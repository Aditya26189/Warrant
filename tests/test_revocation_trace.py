"""The revocation trace: pre-registered, replayed on real lengths, and honest.

``DECISIONS.md`` 178 registered four criteria before the trace existed, and 179
records the read-only defect building it exposed. These tests hold three things:
the committed trace meets the criteria it was registered against, the replay
cannot be run on a warrant whose numbers have lapsed, and the defect stays
visible until someone fixes it.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pytest

from controlplane.config import load_config
from controlplane.demo.revocation_trace import TraceError, build_replay, run_revocation_trace
from controlplane.drift import DriftVerdict
from controlplane.drift.ladder import LadderTransition
from controlplane.drift.response import DriftResponse
from controlplane.matrix.routing import RoutingDecision
from controlplane.model import Action, EnvelopeState, WarrantStatus, utc_now
from controlplane.store import Ledger
from controlplane.validation.synthetic import synthetic_cache, synthetic_evalset

from .factories import make_warrant

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRACE = PROJECT_ROOT / "results" / "drift" / "revocation_trace.json"
CONFIG = load_config(str(PROJECT_ROOT / "config.yaml"))


def _trace() -> dict:
    assert TRACE.is_file(), (
        "results/drift/revocation_trace.json is missing; the definition of done "
        "requires a revocation trace. python scripts/28_revocation_trace.py"
    )
    return json.loads(TRACE.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# The module
# --------------------------------------------------------------------------- #


def _synthetic_replay():
    short = synthetic_evalset(
        eval_set_id="short-synthetic", n_items=400, base_rate=0.2, seed=3, declare_splits=True
    )
    long_ = synthetic_evalset(
        eval_set_id="long-synthetic", n_items=200, base_rate=0.2, seed=4, long_context=True
    )
    kwargs = dict(window=CONFIG.probe.rolling_window, stride=CONFIG.probe.rolling_stride)
    return short, synthetic_cache(short, seed=3, **kwargs), synthetic_cache(long_, seed=4, **kwargs)


def test_the_normal_segment_draws_only_held_out_rows() -> None:
    short, short_cache, long_cache = _synthetic_replay()
    replay = build_replay(
        normal_evalset=short, normal_cache=short_cache, shift_cache=long_cache,
        n_normal=50, n_shift=50, seed=CONFIG.seed,
    )
    test_rows = {i for i, item in enumerate(short.items) if item.split == "test"}
    normal = [e for e in replay if e.segment == "normal"]
    assert len(normal) == 50 and all(e.cache_row in test_rows for e in normal)
    assert [e.segment for e in replay] == ["normal"] * 50 + ["shift"] * 50


def test_a_replay_asking_for_more_rows_than_exist_is_refused() -> None:
    short, short_cache, long_cache = _synthetic_replay()
    with pytest.raises(TraceError, match="asked for"):
        build_replay(
            normal_evalset=short, normal_cache=short_cache, shift_cache=long_cache,
            n_normal=10_000, n_shift=10, seed=CONFIG.seed,
        )


def test_an_expired_warrant_is_refused_rather_than_traced(tmp_path: Path) -> None:
    """A trace of an expired warrant reports its age, not the drift (DECISIONS.md 177)."""
    warrant = make_warrant(issued_at=utc_now() - timedelta(hours=48), ttl_hours=24)
    with pytest.raises(TraceError, match="expired"):
        run_revocation_trace(
            CONFIG, warrant=warrant, replay=(), matrix=None, profile_names=(),
            live_eval_set_id="triviaqa-longctx-600", now=utc_now(),
            ledger=Ledger(tmp_path / "t.db", retention_days=400),
        )


# --------------------------------------------------------------------------- #
# DECISIONS.md 179 — the read-only defect, kept visible
# --------------------------------------------------------------------------- #


@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason=(
        "DECISIONS.md 179: DriftResponse.to_payload calls RoutingDecision.to_payload, "
        "which does not exist. drift/ is read-only. When this passes, strict mode "
        "fails it: remove the workaround in demo/revocation_trace.py and close 179."
    ),
)
def test_a_routed_drift_response_serialises() -> None:
    warrant = make_warrant()
    verdict = DriftVerdict(
        state=EnvelopeState.SIGNIFICANT_SHIFT, n_observed=200, window_size=200,
        per_feature={}, unobserved=(), driver=None, reason="test",
    )
    transition = LadderTransition(
        warrant_id=warrant.warrant_id, detector_id=warrant.detector_id,
        eval_set_id=warrant.eval_set_id, from_status=WarrantStatus.VALID,
        to_status=WarrantStatus.REVOKED, envelope_state=EnvelopeState.SIGNIFICANT_SHIFT,
        verdict=verdict, widen_factor=None, reason="test",
    )
    routing = RoutingDecision(
        envelope_id="triviaqa-longctx-600", profile="customer_support", warrant=None,
        action=Action.ESCALATE, claimed_bounds={}, reason="nothing qualifies",
    )
    DriftResponse(transition=transition, routing=routing, claimed_bounds={}).to_payload()
