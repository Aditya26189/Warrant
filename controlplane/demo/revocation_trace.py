"""A revocation, replayed on real token lengths against a real warrant.

``DECISIONS.md`` 178. ``CLAUDE.md``'s definition of done asks ``RESULTS.md`` for
*drift/revocation traces*, and until this module no drift run in ``results/``
had revoked a warrant a model produced. This replays one.

**Nothing here decides.** The monitor is :class:`~controlplane.drift.DriftMonitor`,
the ladder is :func:`~controlplane.drift.ladder.apply_ladder`, routing is
:func:`~controlplane.drift.response.respond_to_drift` and the record is
:func:`~controlplane.drift.certify.certify_drift_response` -- the same paths the
demo and the gateway use. This module builds the stream, feeds it, and writes
down what those paths did, including against criteria registered before it ran.

**What the stream is.** Token lengths from the GPU extraction caches: the
``triviaqa-600`` test split for the normal segment and ``triviaqa-longctx-600``
for the shift, each drawn without replacement at a declared seed. Every event
names the cache row it came from. It is a replay of committed measurements, not
production traffic, and the artifact says so.
"""

from __future__ import annotations

import dataclasses
import inspect
from datetime import datetime
from typing import Any, Optional, Sequence

import numpy as np

from ..config import Config
from ..drift import DriftMonitor
from ..drift.certify import certify_drift_response, ladder_policy_hash
from ..drift.ladder import apply_ladder
from ..drift.response import respond_to_drift
from ..matrix import Profile
from ..model import Warrant, WarrantStatus
from ..model.serde import to_jsonable
from ..store import Ledger, RecordKind
from ..validation.evalsets import EvalSet, ExtractionCache

__all__ = [
    "ReplayEvent",
    "TraceError",
    "build_replay",
    "latest_warrant",
    "run_revocation_trace",
]

#: The ladder's own widening factor, read off its signature rather than
#: restated, so the policy hash on each certificate describes the ladder that
#: actually ran (``DECISIONS.md`` 172: it is a default argument, not config).
LADDER_WIDEN_FACTOR: float = inspect.signature(apply_ladder).parameters["widen_factor"].default


class TraceError(RuntimeError):
    """Raised when the trace cannot be run honestly."""


@dataclasses.dataclass(frozen=True)
class ReplayEvent:
    """One replayed request.

    Args:
        index: Position in the stream, from 0.
        segment: ``"normal"`` or ``"shift"``.
        eval_set_id: The set whose cache supplied the length.
        cache_row: The row in that cache, so the event can be checked.
        token_length: The prompt length the model saw, as recorded at extraction.
    """

    index: int
    segment: str
    eval_set_id: str
    cache_row: int
    token_length: int


def latest_warrant(ledger: Ledger, *, detector_id: str, eval_set_id: str) -> Warrant:
    """The newest warrant for a detector on an envelope, from the audit ledger."""
    found: Optional[Warrant] = None
    for record in ledger.query(kind=RecordKind.WARRANT):
        warrant = ledger.get_warrant(record.record_id)
        if warrant.detector_id == detector_id and warrant.eval_set_id == eval_set_id:
            found = warrant
    if found is None:
        raise TraceError(
            f"no warrant for {detector_id} on {eval_set_id} in the ledger. The trace "
            "observes a measured warrant; rebuild the chain first (DECISIONS.md 157)."
        )
    return found


def build_replay(
    *,
    normal_evalset: EvalSet,
    normal_cache: ExtractionCache,
    shift_cache: ExtractionCache,
    n_normal: int,
    n_shift: int,
    seed: int,
) -> tuple[ReplayEvent, ...]:
    """Assemble the stream: held-out normal traffic, then the shifted envelope.

    The normal segment draws only from the **test** split. The reference envelope
    was built over the whole set, and test rows are the ones no fit or threshold
    ever saw, which is the closest a replay gets to traffic arriving later.

    Raises:
        TraceError: If either segment asks for more rows than exist, or the cache
            and its eval set disagree about how many items there are.
    """
    if len(normal_evalset.items) != normal_cache.n_items:
        raise TraceError(
            f"{normal_evalset.eval_set_id} has {len(normal_evalset.items)} items and "
            f"its cache {normal_cache.n_items}; the split cannot be read off the rows"
        )
    test_rows = np.array(
        [i for i, item in enumerate(normal_evalset.items) if item.split == "test"]
    )
    if n_normal > test_rows.size or n_shift > shift_cache.n_items:
        raise TraceError(
            f"asked for {n_normal} normal and {n_shift} shifted requests; "
            f"{test_rows.size} test rows and {shift_cache.n_items} long-context rows exist"
        )
    normal_rows = np.random.default_rng(seed).choice(test_rows, size=n_normal, replace=False)
    shift_rows = np.random.default_rng(seed + 1).choice(
        shift_cache.n_items, size=n_shift, replace=False
    )
    events: list[ReplayEvent] = []
    for row in normal_rows:
        events.append(
            ReplayEvent(len(events), "normal", normal_cache.eval_set_id, int(row),
                        int(normal_cache.token_lengths[int(row)]))
        )
    for row in shift_rows:
        events.append(
            ReplayEvent(len(events), "shift", shift_cache.eval_set_id, int(row),
                        int(shift_cache.token_lengths[int(row)]))
        )
    return tuple(events)


def run_revocation_trace(
    config: Config,
    *,
    warrant: Warrant,
    replay: Sequence[ReplayEvent],
    matrix,
    profile_names: Sequence[str],
    live_eval_set_id: str,
    now: datetime,
    ledger: Ledger,
    checkpoint_every: int = 50,
) -> dict[str, Any]:
    """Feed the stream to the monitor, checkpoint the ladder, act at revocation.

    Args:
        config: Supplies the drift window, bands, features and false-alarm ceiling.
        warrant: The warrant under observation.
        replay: From :func:`build_replay`.
        matrix: The warrant matrix, for the revocation consultation.
        profile_names: Each profile gets its own routing decision and certificate.
        live_eval_set_id: The envelope the shifted traffic is in.
        now: Decision time. Must be inside the warrant's lifetime.
        ledger: Where the certificates are sealed. A separate file from the
            matrix's audit store, so replaying does not change the record count
            ``RESULTS.md`` reports.
        checkpoint_every: Requests between verdicts once the window is full.

    Returns:
        The artifact payload: stream, checkpoints, the revocation, and the
        pre-registered criteria evaluated.

    Raises:
        TraceError: If the warrant is not VALID or has expired. A trace of an
            expired warrant would report age, not drift (``DECISIONS.md`` 177).
    """
    if warrant.status is not WarrantStatus.VALID:
        raise TraceError(f"warrant {warrant.warrant_id} is {warrant.status.value}, not VALID")
    if warrant.is_expired(now):
        raise TraceError(
            f"warrant {warrant.warrant_id} expired at {warrant.expires_at.isoformat()}. "
            "A revocation trace of an expired warrant reports its age, not the drift. "
            "Rebuild the chain to re-issue it (DECISIONS.md 177)."
        )

    drift = config.drift
    monitor = DriftMonitor(
        warrant.envelope,
        window_size=drift.window_size,
        psi_stable=drift.psi_stable,
        psi_significant=drift.psi_significant,
        features=drift.features,
        max_false_alarm_rate=drift.max_false_alarm_rate,
    )
    shift_start = next((e.index for e in replay if e.segment == "shift"), None)

    checkpoints: list[dict[str, Any]] = []
    revocation: Optional[dict[str, Any]] = None
    window_segments: list[str] = []
    for event in replay:
        monitor.observe({"token_length": float(event.token_length)})
        window_segments.append(event.segment)
        window_segments = window_segments[-drift.window_size:]
        n = event.index + 1
        if n < drift.window_size or n % checkpoint_every:
            continue
        verdict = monitor.verdict()
        transition = apply_ladder(warrant, verdict)
        driver = verdict.per_feature.get(verdict.driver) if verdict.driver else None
        checkpoints.append(
            {
                "after_request": n,
                "window_normal": window_segments.count("normal"),
                "window_shift": window_segments.count("shift"),
                "envelope_state": verdict.state.value,
                "psi": None if driver is None else driver.psi,
                "driven_by_smoothing": None if driver is None else driver.driven_by_smoothing,
                "to_status": transition.to_status.value,
                "reason": transition.reason,
            }
        )
        if transition.needs_routing and revocation is None:
            revocation = _act_on_revocation(
                config, warrant=warrant, monitor=monitor, matrix=matrix,
                profile_names=profile_names, live_eval_set_id=live_eval_set_id,
                now=now, ledger=ledger, request_index=n,
            )

    criteria = _criteria(checkpoints, revocation, shift_start, drift.window_size, live_eval_set_id, warrant)
    return {
        "what_this_is": (
            "a replay of committed token lengths through the shipped drift, ladder, "
            "routing and certification code -- not production traffic"
        ),
        "warrant": {
            "warrant_id": warrant.warrant_id,
            "detector_id": warrant.detector_id,
            "operating_point_id": warrant.operating_point.operating_point_id,
            "eval_set_id": warrant.eval_set_id,
            "envelope_id": warrant.envelope.envelope_id,
            "issued_at": warrant.issued_at.isoformat(),
            "expires_at": warrant.expires_at.isoformat(),
        },
        "monitor": {
            "window_size": drift.window_size,
            "psi_stable": drift.psi_stable,
            "psi_significant": drift.psi_significant,
            "features_configured": list(drift.features),
            "features_with_a_reference": [f.name for f in warrant.envelope.features],
            "null_bands": {
                name: {"false_alarm_rate": band.false_alarm_rate, "p95": band.p95}
                for name, band in monitor.null_bands.items()
            },
            "checkpoint_every": checkpoint_every,
            "ladder_widen_factor": LADDER_WIDEN_FACTOR,
        },
        "stream": {
            "n_normal": sum(1 for e in replay if e.segment == "normal"),
            "n_shift": sum(1 for e in replay if e.segment == "shift"),
            "shift_starts_at_request": None if shift_start is None else shift_start + 1,
            "token_length_median": {
                segment: float(np.median([e.token_length for e in replay if e.segment == segment]))
                for segment in ("normal", "shift")
            },
            "events": [dataclasses.asdict(e) for e in replay],
        },
        "checkpoints": checkpoints,
        "revocation": revocation,
        "criteria": criteria,
        "decided_at": now.isoformat(),
    }


def _act_on_revocation(
    config: Config,
    *,
    warrant: Warrant,
    monitor: DriftMonitor,
    matrix,
    profile_names: Sequence[str],
    live_eval_set_id: str,
    now: datetime,
    ledger: Ledger,
    request_index: int,
) -> dict[str, Any]:
    """Route and certify once per profile, at the first REVOKED verdict."""
    policy_hash = ladder_policy_hash(
        psi_stable=config.drift.psi_stable,
        psi_significant=config.drift.psi_significant,
        window_size=config.drift.window_size,
        widen_factor=LADDER_WIDEN_FACTOR,
    )
    decisions = []
    for name in profile_names:
        response = respond_to_drift(
            warrant, monitor, matrix=matrix,
            profile=Profile.from_config(config, name),
            live_eval_set_id=live_eval_set_id,
        )
        certificate = certify_drift_response(
            response, warrant,
            certificate_id=f"cert-revocation-{name}-{request_index:04d}",
            request_id=f"R-replay-{request_index:04d}",
            session_id="S-revocation-replay",
            live_envelope_id=live_eval_set_id,
            timestamp=now,
            policy_hash=policy_hash,
        )
        sealed = ledger.append_certificate(certificate)
        decisions.append(
            {
                "profile": name,
                "response": response.to_payload(),
                "certificate": to_jsonable(sealed),
            }
        )
    chain = ledger.verify_chain()
    return {
        "at_request": request_index,
        "live_eval_set_id": live_eval_set_id,
        "policy_hash": policy_hash,
        "decisions": decisions,
        "certificate_chain": {"ok": chain.ok, "n_records": chain.n_records, "head_hash": chain.head_hash},
    }


def _criteria(
    checkpoints: Sequence[dict[str, Any]],
    revocation: Optional[dict[str, Any]],
    shift_start: Optional[int],
    window_size: int,
    live_eval_set_id: str,
    warrant: Warrant,
) -> dict[str, dict[str, Any]]:
    """The four criteria ``DECISIONS.md`` 178 registered before the run."""
    pure_normal = [c for c in checkpoints if c["window_shift"] == 0]
    false_alarms = [
        c["after_request"] for c in pure_normal
        if c["to_status"] in (WarrantStatus.STALE.value, WarrantStatus.REVOKED.value)
    ]
    first_revoked = next(
        (c["after_request"] for c in checkpoints if c["to_status"] == WarrantStatus.REVOKED.value),
        None,
    )
    delay = None if first_revoked is None or shift_start is None else first_revoked - shift_start
    decisions = [] if revocation is None else revocation["decisions"]
    routed_envelopes = {
        d["response"]["routing"]["envelope_id"] for d in decisions if d["response"]["routing"]
    }
    certificates_honest = bool(decisions) and all(
        any(repr(live_eval_set_id) in note for note in d["certificate"]["unchecked"])
        and any(repr(warrant.eval_set_id) in note for note in d["certificate"]["unchecked"])
        and any("MMD" in note for note in d["certificate"]["unchecked"])
        for d in decisions
    )
    return {
        "1_no_false_alarm": {
            "passed": bool(pure_normal) and not false_alarms,
            "checkpoints_entirely_normal": len(pure_normal),
            "false_alarms_at": false_alarms,
        },
        "2_revoked_within_one_window": {
            "passed": delay is not None and delay <= window_size,
            "first_revoked_after_request": first_revoked,
            "requests_after_shift_began": delay,
            "window_size": window_size,
        },
        "3_routing_on_the_live_envelope": {
            "passed": bool(decisions) and routed_envelopes == {live_eval_set_id},
            "envelopes_routed_on": sorted(routed_envelopes),
        },
        "4_certificate_says_what_was_not_checked": {"passed": certificates_honest},
    }

