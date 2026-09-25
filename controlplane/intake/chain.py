"""A year of rechecks as one change detector, carried in the recheck records.

``DECISIONS.md`` 193, from 187. A single ``warrant recheck`` tests one file on its
own, so a year of weekly rechecks is 52 tests and revokes a detector that kept its
promise in most years (0.8515, 187). A **chain** feeds every recheck's clean
negatives, one unit at a time, into one Shiryaev-Roberts e-detector -- the mean
over :class:`~controlplane.validation.warrant_stats.FPRMonitor`'s betting grid of
one detector per bet -- and revokes when that mean reaches ``N / alpha``.

**The guarantee, and its conditions.** For any true false-positive rate at or
below the certified budget, the probability that the chain's sequential statistic
revokes at any point in its first ``N`` units is at most ``alpha``: ``R_t + (N - t)``
is a nonnegative supermartingale from ``N`` that dominates the statistic, so
Ville's inequality applies (187). The bound covers that statistic only: a recheck
REVOKED because the score distribution moved is a separate check, outside it
(addendum 2026-09-16). It holds for the chain **as kept** -- a user who discards an
unfavourable record and starts again has a new chain and a spent guarantee, and
nothing on one machine can stop that. What the records do is make it visible:
each carries the digest of the warrant and of the record before it.

**What is not the user's to choose.** ``N``, alpha and the grid are frozen when a
chain starts. Within a file, units are fed in the order of
``sha256(warrant digest, unit id)``, fixed before any score is read, so sorting or
shuffling a file changes nothing. A unit **id** already consumed cannot be fed
again: ids must be unique and stable across every file of a chain -- an item's own
id, not a row number that restarts in each file. The check is on ids, not items;
the same labelled items resubmitted under new ids are not recognised, and nothing
local could recognise them (DECISIONS 194).

**Forks are made visible, not prevented.** A sidecar ``<warrant>.chain-head``
holds the digest of the chain's latest record. Continuing from any other record,
or starting a chain while a head exists, is refused unless ``--fork`` is given,
and a forked link records the head it left. Deleting the sidecar defeats the
check, and each record says which check applied (194). Starting a chain from a
**copy** of the warrant, which has no sidecar of its own, is not refused; it is
visible to ``warrant chain verify`` only when both chains' records are kept.

**The digests are checksums, not signatures.** Anyone who can write the records
can produce a consistent set: a record edited and re-digested passes every check
here, and one with ``head_check`` cleared cannot be told from a record written
before 194. Tamper-evidence would need a key or an anchor outside the user's
control, which a local tool does not have (194). Since the addendum of 2026-09-17
every chained record is also sealed whole (``record_sha256``), so an edit to any
stored field is caught unless the editor recomputes the seal. Missing seals
are unknown integrity, not established legacy age; verification cannot call them
clean and continuation refuses them (207).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from typing import Any, Mapping, Optional, Sequence

import numpy as np

__all__ = [
    "HEAD_SUFFIX",
    "METHOD",
    "ChainError",
    "ChainState",
    "FeedResult",
    "canonical_sha256",
    "continue_chain",
    "feed",
    "head_document",
    "head_path",
    "read_head",
    "record_has_drift_revocation",
    "start_chain",
    "unit_digest",
    "write_head",
]

#: Appended to the warrant record's path to name its chain-head sidecar (194).
HEAD_SUFFIX = ".chain-head"

METHOD = "mean_of_shiryaev_roberts_e_detectors_over_fprmonitor_grid"

#: Hex characters kept per consumed-unit digest. 96 bits: a collision among a
#: year's units is not a practical event, and a full-year chain stays well under
#: a megabyte.
DIGEST_HEX = 24


class ChainError(ValueError):
    """A chain cannot be started, continued or fed as asked. The CLI exits 2."""


class MalformedChainError(ChainError):
    """A chain block whose values are the wrong type or out of their domain.

    Distinct from an edit the digest catches: an ``alpha`` of 0 or a NaN statistic
    is not evidence that someone changed a record, and the verifier reports it as
    ``malformed`` rather than ``digest``. Raised before any arithmetic, so a bad
    value never reaches a division or the digest's encoder (194, defect 3).
    """


#: The field a chained recheck record is sealed under (addendum 2026-09-17).
SEAL_FIELD = "record_sha256"


def seal_record(document: dict[str, Any]) -> dict[str, Any]:
    """The document with ``record_sha256`` over everything else in it.

    Covers the whole record -- status, reason, bounds, drift, labels, provenance,
    the chain block -- not only the chain state. A schema audit found 197 fields of
    the latest record that could be edited without the verifier noticing, because
    only the chain state carried a digest and only a successor covered the rest.
    A checksum, not a signature: rewriting a record and recomputing this passes.
    """
    body = {key: value for key, value in document.items() if key != SEAL_FIELD}
    return {**body, SEAL_FIELD: record_sha256(body, "record being sealed")}


def seal_reproduces(record: dict[str, Any]) -> Optional[bool]:
    """``True`` if the record's seal reproduces, ``False`` if not, ``None`` if unsealed.

    ``None`` means unknown integrity, not an established legacy creation date.
    A genuine legacy record and a stripped modern seal cannot be distinguished
    from this absence. Decision 207 preserves inspection but bars continuation.
    """
    if SEAL_FIELD not in record:
        return None
    body = {key: value for key, value in record.items() if key != SEAL_FIELD}
    return record.get(SEAL_FIELD) == record_sha256(body, "record")


def record_sha256(record: Any, what: str) -> str:
    """:func:`canonical_sha256` of a whole record, or a :class:`MalformedChainError`.

    The digest's encoder refuses NaN and infinity, and a record can carry one
    anywhere, not only in its chain block. Unguarded, that refusal surfaced as a
    traceback before any validation ran (194, defect 3, found by the harness
    after the first fix).
    """
    try:
        return canonical_sha256(record)
    except ValueError as exc:
        raise MalformedChainError(
            f"the {what} holds a value no JSON record can carry -- NaN or infinity ({exc})"
        ) from exc


def _real(block: dict[str, Any], key: str, *, low: float, high: float, closed: bool = False) -> float:
    """A finite real in ``(low, high)`` (or ``[low, high]``), never a boolean."""
    import math

    value = block.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MalformedChainError(f"the chain's {key} is {value!r}, not a number")
    if not math.isfinite(value):
        raise MalformedChainError(f"the chain's {key} is {value!r}, not a finite number")
    inside = low <= value <= high if closed else low < value < high
    if not inside:
        bounds = f"[{low:g}, {high:g}]" if closed else f"({low:g}, {high:g})"
        raise MalformedChainError(f"the chain's {key} is {value!r}, outside {bounds}")
    return float(value)


def _count(block: dict[str, Any], key: str, *, minimum: int) -> int:
    """A non-negative integer at least ``minimum``, never a boolean."""
    value = block.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise MalformedChainError(f"the chain's {key} is {value!r}, not an integer")
    if value < minimum:
        raise MalformedChainError(f"the chain's {key} is {value}, below {minimum}")
    return value


def _validate_block(block: dict[str, Any]) -> None:
    """Every field the state is rebuilt from: its type and its domain.

    Raises :class:`MalformedChainError` naming the first field that fails.
    """
    import math

    if not isinstance(block, dict):
        raise MalformedChainError("the chain block is not an object")
    for key in ("warrant_sha256",):
        if not isinstance(block.get(key), str):
            raise MalformedChainError(f"the chain's {key} is {block.get(key)!r}, not a digest")
    _real(block, "p0", low=0.0, high=1.0)
    _real(block, "alpha", low=0.0, high=1.0)
    grid = block.get("grid")
    if not isinstance(grid, dict):
        raise MalformedChainError(f"the chain's grid is {grid!r}, not an object")
    _real(grid, "lam_lo", low=0.0, high=math.inf)
    _real(grid, "lam_hi", low=0.0, high=math.inf)
    n_lam = _count(grid, "n_lam", minimum=1)
    _count(block, "horizon_units", minimum=1)
    units = _count(block, "units_consumed", minimum=0)
    _count(block, "sequence", minimum=1)
    statistics = block.get("statistics")
    if not isinstance(statistics, list) or len(statistics) != n_lam:
        raise MalformedChainError(
            f"the chain's statistics are not a list of {n_lam} values, one per bet")
    for index, value in enumerate(statistics):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise MalformedChainError(f"the chain's statistic {index} is {value!r}, not a finite number")
    digests = block.get("consumed_unit_digests")
    if not isinstance(digests, list) or not all(isinstance(d, str) for d in digests):
        raise MalformedChainError("the chain's consumed_unit_digests are not a list of digests")
    previous = block.get("previous_record_sha256")
    if previous is not None and not isinstance(previous, str):
        raise MalformedChainError(f"the chain's previous_record_sha256 is {previous!r}, not a digest")
    revoked = block.get("revoked_at_unit")
    if revoked is not None:
        if isinstance(revoked, bool) or not isinstance(revoked, int) or not 1 <= revoked <= units:
            raise MalformedChainError(
                f"the chain's revoked_at_unit is {revoked!r}, not a unit between 1 and {units}")


def canonical_sha256(value: Any) -> str:
    """SHA-256 of one deterministic JSON encoding, so a digest names content."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                         allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def unit_digest(warrant_sha256: str, unit_id: str) -> str:
    """The digest a unit is ordered by and remembered as, bound to its warrant."""
    return hashlib.sha256(f"{warrant_sha256}\x00{unit_id}".encode("utf-8")).hexdigest()


def _grid(p0: float, alpha: float) -> tuple[float, float, int, np.ndarray]:
    """The shipped monitor's betting grid, with the bounds that rebuild it."""
    from ..validation.warrant_stats import FPRMonitor

    monitor = FPRMonitor(p0=p0, alpha=alpha)
    return monitor.lam_lo, monitor.lam_hi, monitor.n_lam, np.asarray(monitor.lams, dtype=float)


@dataclasses.dataclass(frozen=True)
class ChainState:
    """Everything a chain needs to continue, and nothing about anyone's data."""

    warrant_sha256: str
    p0: float
    alpha: float
    lam_lo: float
    lam_hi: float
    n_lam: int
    horizon_units: int
    units_consumed: int
    statistics: tuple[float, ...]
    sequence: int
    previous_record_sha256: Optional[str]
    consumed_unit_digests: tuple[str, ...]
    revoked_at_unit: Optional[int] = None
    #: ``"matched"``, ``"forked"`` or ``"no_sidecar"``: which head check this link
    #: passed (194). ``None`` only in records written before the check existed.
    head_check: Optional[str] = None
    #: The head digest a ``--fork`` left behind.
    forked_from_head: Optional[str] = None

    @property
    def threshold(self) -> float:
        return self.horizon_units / self.alpha

    @property
    def ended(self) -> bool:
        return self.units_consumed >= self.horizon_units

    @property
    def mean_statistic(self) -> float:
        return float(np.mean(self.statistics))

    def _body(self) -> dict[str, Any]:
        body = {
            "method": METHOD,
            "warrant_sha256": self.warrant_sha256,
            "p0": self.p0,
            "alpha": self.alpha,
            "grid": {"lam_lo": self.lam_lo, "lam_hi": self.lam_hi, "n_lam": self.n_lam},
            "horizon_units": self.horizon_units,
            "threshold": self.threshold,
            "units_consumed": self.units_consumed,
            "statistics": list(self.statistics),
            "mean_statistic": self.mean_statistic,
            "sequence": self.sequence,
            "previous_record_sha256": self.previous_record_sha256,
            "consumed_unit_digests": list(self.consumed_unit_digests),
            "revoked_at_unit": self.revoked_at_unit,
            "ended": self.ended,
        }
        # Added by 194. Omitted when unset, so a record written before it still
        # reproduces its own digest.
        if self.head_check is not None:
            body["head_check"] = self.head_check
            body["forked_from_head"] = self.forked_from_head
        return body

    def to_payload(self) -> dict[str, Any]:
        body = self._body()
        return {
            **body,
            "state_sha256": canonical_sha256(body),
            "guarantee": (
                f"P(this chain's sequential false-positive statistic revokes, within the "
                f"first {self.horizon_units} units, a detector whose true false-positive "
                f"rate is at or below {self.p0:g}) <= {self.alpha:g} -- for this chain as "
                "kept. The bound covers that statistic only: a recheck REVOKED because the "
                "score distribution moved is a separate check, outside it. Starting a "
                "fresh chain after an unfavourable record spends the guarantee; keep "
                "every record. "
                "The chain-head sidecar makes an accidental fork declare itself; it "
                "does not prevent a deliberate one. The digests here are checksums, "
                "not signatures: anyone who can write these records can produce a "
                "consistent set."
            ),
            "head_check_meaning": (
                "'matched' means this link's --since record matched the chain-head "
                "sidecar present when it ran. The sidecar is an ordinary file the user "
                "can edit, copy or delete, so 'matched' is not proof that this link is "
                "not a fork; only the kept records, checked together, can show that -- "
                "and only if they were not rewritten with recomputed digests "
                "(DECISIONS 194)."
            ),
        }

    @classmethod
    def from_payload(cls, block: dict[str, Any]) -> "ChainState":
        """Rebuild a state, refusing one that is malformed or does not reproduce.

        Three checks, in order. The values are validated before any arithmetic
        (:class:`MalformedChainError`). The digest of the rebuilt body must match.
        Then every serialized derived field must equal its reconstruction: the
        digest is computed over the rebuilt body, so a derived field edited in the
        record would otherwise never be read (194, defect 2).
        """
        _validate_block(block)
        try:
            state = cls(
                warrant_sha256=block["warrant_sha256"], p0=float(block["p0"]),
                alpha=float(block["alpha"]), lam_lo=float(block["grid"]["lam_lo"]),
                lam_hi=float(block["grid"]["lam_hi"]), n_lam=int(block["grid"]["n_lam"]),
                horizon_units=int(block["horizon_units"]),
                units_consumed=int(block["units_consumed"]),
                statistics=tuple(float(v) for v in block["statistics"]),
                sequence=int(block["sequence"]),
                previous_record_sha256=block["previous_record_sha256"],
                consumed_unit_digests=tuple(block["consumed_unit_digests"]),
                revoked_at_unit=block["revoked_at_unit"],
                head_check=block.get("head_check"),
                forked_from_head=block.get("forked_from_head"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ChainError(f"the chain block is incomplete or malformed ({exc})") from exc
        if block.get("method") != METHOD:
            raise ChainError(f"the chain was built by {block.get('method')!r}, not {METHOD!r}")
        if canonical_sha256(state._body()) != block.get("state_sha256"):
            raise ChainError(
                "the chain state does not reproduce its digest: it was edited without "
                "its digest being recomputed, and a statistic that has been edited "
                "carries no guarantee. The digest is a checksum, not a signature: an "
                "edit that recomputes it is not caught here (DECISIONS 194)"
            )
        if len(state.statistics) != state.n_lam:
            raise ChainError("the chain's statistics do not match its betting grid")
        for key in ("threshold", "mean_statistic", "ended"):
            if key not in block:
                raise ChainError(f"the chain record has no {key}, which it always carries")
            written, rebuilt = block[key], getattr(state, key)
            same_type = (type(written) is bool) if key == "ended" else not isinstance(written, bool)
            if not same_type or written != rebuilt:
                raise ChainError(
                    f"the chain record's {key} reads {written!r} but its state rebuilds "
                    f"{rebuilt!r}: the field was edited without its digest being "
                    "recomputed, and a record whose fields disagree with its own state "
                    "carries no guarantee (DECISIONS 194)"
                )
        return state


def head_path(warrant_path: Any) -> Any:
    """Where a warrant's chain-head sidecar lives: beside the warrant record."""
    from pathlib import Path

    return Path(str(warrant_path) + HEAD_SUFFIX)


def read_head(warrant_path: Any) -> Optional[str]:
    """The digest of the chain's latest record, or ``None`` with no sidecar."""
    path = head_path(warrant_path)
    if not path.is_file():
        return None
    try:
        return str(json.loads(path.read_text(encoding="utf-8"))["head_record_sha256"])
    except (ValueError, KeyError, TypeError) as exc:
        raise ChainError(f"{path.name} is not a chain-head sidecar ({exc})") from exc


def read_head_status(warrant_path: Any) -> Optional[str]:
    """The latest record's status as the sidecar recorded it, or ``None``.

    ``None`` with no sidecar, and for a sidecar written before the status was
    recorded -- read as before, not as a refusal.
    """
    path = head_path(warrant_path)
    if not path.is_file():
        return None
    try:
        status = json.loads(path.read_text(encoding="utf-8")).get("status")
    except (ValueError, AttributeError) as exc:
        raise ChainError(f"{path.name} is not a chain-head sidecar ({exc})") from exc
    return status if isinstance(status, str) else None


def _refuse_revoked_head(head_status: Optional[str]) -> None:
    """A warrant whose chain's latest record REVOKED it takes no new or forked link.

    ``--fork`` declares a branch; it does not reopen a revocation. Without this, a
    new chain on the same warrant -- or a fork from a link before the revocation --
    started cleanly and could return VALID (DECISIONS addendum 2026-09-16).
    """
    if head_status == "REVOKED":
        raise ChainError(
            "this warrant's chain REVOKED it at its latest record, so no new chain and "
            "no fork may continue it, with or without --fork. Re-certify, and start a "
            "new chain on the new warrant."
        )


def head_document(record_sha256: str, sequence: int, *,
                  status: Optional[str] = None) -> dict[str, Any]:
    """Use one head schema for ordinary writes and interrupted-publication recovery."""
    note = (
        "The digest and status of this warrant's latest chained recheck record. A "
        "recheck --since any other record, or a new chain while this exists, is "
        "refused without --fork; if the status is REVOKED, both are refused even "
        "with --fork. Deleting this file defeats these checks (DECISIONS 194)."
    )
    payload = {"head_record_sha256": record_sha256, "sequence": sequence, "note": note}
    if status is not None:
        payload["status"] = status
    return payload


def write_head(warrant_path: Any, record_sha256: str, sequence: int, *,
               status: Optional[str] = None) -> None:
    """Atomically replace the mutable pointer; callers serialize the whole transaction."""
    from ._atomic_files import write_json_atomic

    write_json_atomic(head_path(warrant_path),
                      head_document(record_sha256, sequence, status=status), replace=True)


def _head_check(head: Optional[str], continuing_from: Optional[str], fork: bool) -> tuple[str, Optional[str]]:
    """Which head check applies, refusing an undeclared fork."""
    if head is None:
        return "no_sidecar", None
    if continuing_from is not None and continuing_from == head:
        return "matched", None
    if not fork:
        if continuing_from is None:
            raise ChainError(
                "a chain already exists for this warrant (its head sidecar is present). "
                "Continue it with --since on its latest record, or pass --fork to "
                "start another; a fork is recorded and visible."
            )
        raise ChainError(
            "the --since record is not the chain's latest record, so continuing from "
            "it would drop every link after it. Use the latest record, or pass --fork "
            "to branch deliberately; a fork is recorded and visible."
        )
    return "forked", head


def start_chain(warrant_record: dict[str, Any], *, horizon_units: int, alpha: float,
                head: Optional[str] = None, fork: bool = False,
                head_status: Optional[str] = None) -> ChainState:
    """A new chain for this warrant, with ``N`` declared now and frozen."""
    _refuse_revoked_head(head_status)
    if horizon_units < 1:
        raise ChainError(f"--horizon-labels must be a positive number of units, got {horizon_units}")
    budget = warrant_record.get("budget_fpr")
    if budget is None:
        raise ChainError("the warrant record carries no budget_fpr to monitor against")
    check, left = _head_check(head, None, fork)
    lam_lo, lam_hi, n_lam, _ = _grid(float(budget), alpha)
    return ChainState(
        warrant_sha256=canonical_sha256(warrant_record), p0=float(budget), alpha=alpha,
        lam_lo=lam_lo, lam_hi=lam_hi, n_lam=n_lam, horizon_units=int(horizon_units),
        units_consumed=0, statistics=tuple(0.0 for _ in range(n_lam)), sequence=1,
        previous_record_sha256=None, consumed_unit_digests=(),
        head_check=check, forked_from_head=left,
    )


def record_has_drift_revocation(record: Mapping[str, Any]) -> bool:
    """Read the independent drift finding, including old inconsistent records.

    Decision 205: an aggregate STALE status once hid a drift REVOKED finding.
    The retained finding still bars continuation. This does not recompute its
    statistics or authenticate the record; sealing is checked separately.
    """
    drift = record.get("drift")
    return isinstance(drift, Mapping) and drift.get("verdict") == "REVOKED"


def continue_chain(
    previous_record: dict[str, Any], warrant_record: dict[str, Any], *, alpha: float,
    head: Optional[str] = None, fork: bool = False, head_status: Optional[str] = None,
) -> ChainState:
    """The next link, refused unless it continues this warrant's live chain."""
    _refuse_revoked_head(head_status)
    block = previous_record.get("chain")
    if not block:
        raise ChainError(
            "the --since record is not part of a chain. Start one with "
            "--horizon-labels on a recheck, then continue it with --since."
        )
    state = ChainState.from_payload(block)
    sealed = seal_reproduces(previous_record)
    if sealed is False:
        # Without this, an edited latest record -- a REVOKED status set to VALID,
        # the sidecar deleted -- could be continued (addendum 2026-09-17).
        raise ChainError(
            "the --since record's seal does not reproduce: a field was edited after "
            "the record was written, so it cannot be continued. The seal is a "
            "checksum, not a signature."
        )
    if state.warrant_sha256 != record_sha256(warrant_record, "warrant record"):
        raise ChainError(
            "the --since record's chain belongs to a different warrant record; a chain "
            "cannot be moved between warrants"
        )
    if abs(state.alpha - alpha) > 1e-12:
        raise ChainError(f"the chain runs at alpha={state.alpha:g}, the warrant at {alpha:g}")
    if previous_record.get("status") == "REVOKED" or record_has_drift_revocation(previous_record):
        # The chain state records only the chain's own revocation. A recheck
        # revoked by drift, with the bound holding and the chain live, carries
        # status REVOKED and no revoked_at_unit -- and was continued until 194's
        # review found it. A claim that stands is not continued (194, defect 1).
        # Old STALE records can hide that drift revocation; read it directly (205).
        raise ChainError(
            "the --since record REVOKED this warrant"
            + ("" if state.revoked_at_unit is not None else
               ", on its score distribution rather than the chain's statistic")
            + ". A revoked warrant is not continued: re-certify, and start a new "
            "chain on the new warrant."
        )
    lam_lo, lam_hi, n_lam, _ = _grid(state.p0, state.alpha)
    if (state.lam_lo, state.lam_hi, state.n_lam) != (lam_lo, lam_hi, n_lam):
        raise ChainError("the betting grid has changed since the chain started")
    if state.revoked_at_unit is not None:
        raise ChainError(
            f"this chain revoked the warrant at unit {state.revoked_at_unit}. Re-certify, "
            "and start a new chain on the new warrant."
        )
    if state.ended:
        raise ChainError(
            f"this chain has consumed its {state.horizon_units} units; its guarantee "
            "does not extend past them. Re-certify and start a new chain."
        )
    # Preserve malformed-JSON diagnostics before the missing-assurance refusal.
    previous_sha = record_sha256(previous_record, "--since record")
    if sealed is None:
        raise ChainError(
            "the --since record is unsealed; its record integrity is unknown. "
            "Inspect it with warrant chain verify, but do not continue it, even "
            "with --fork. Recover a verified retained copy or re-certify and "
            "start a new chain. A missing seal does not establish legacy age."
        )
    if head is None and state.head_check in ("matched", "forked"):
        # The last link was written under a head and there is none now: the
        # sidecar was deleted, or the warrant was moved or copied, which starts a
        # fresh path and so a fresh head (DECISIONS 194, A).
        if not fork:
            raise ChainError(
                "this chain had a head when its last record was written and none is "
                "present now: the sidecar was deleted, or the warrant record was moved "
                "or copied. Continue from the warrant's original location, or pass "
                "--fork to continue here; the fork is recorded."
            )
        check, left = "forked", None
    else:
        check, left = _head_check(head, previous_sha, fork)
    return dataclasses.replace(
        state, sequence=state.sequence + 1, previous_record_sha256=previous_sha,
        head_check=check, forked_from_head=left,
    )


@dataclasses.dataclass(frozen=True)
class FeedResult:
    """One recheck's effect on its chain."""

    state: ChainState
    units_in_file: int
    units_fed: int
    #: Units in the file past the horizon or after a revocation, not consumed.
    units_not_consumed: int
    revoked_here: bool
    max_mean_here: float

    def to_payload(self) -> dict[str, Any]:
        return {
            **self.state.to_payload(),
            "this_recheck": {
                "units_in_file": self.units_in_file,
                "units_fed": self.units_fed,
                "units_not_consumed": self.units_not_consumed,
                "revoked_here": self.revoked_here,
                "max_mean_statistic_here": self.max_mean_here,
            },
        }


def feed(state: ChainState, unit_ids: Sequence[str], fired: np.ndarray, *,
         in_given_order: bool = False) -> FeedResult:
    """Feed one recheck's clean-negative units into the chain.

    Quantity: whether the chain's evidence has established that the true
    false-positive rate exceeds the certified budget, at any unit so far.
    Propagation: a Shiryaev-Roberts e-detector per bet on the monitor's grid,
    averaged; revocation at ``N / alpha``, where ``R_t + (N - t)`` is a
    nonnegative supermartingale under any rate at or below the budget, so
    Ville's inequality bounds this statistic's false revocation over the first
    ``N`` units by alpha (DECISIONS 187, 193). A revocation for a moved score
    distribution is a separate check, outside that bound. Checked after every unit.

    Args:
        state: The chain before this recheck.
        unit_ids: One id per clean-negative unit -- item ids, or cluster ids
            when the warrant is grouped.
        fired: Whether each unit reached the certified threshold.
        in_given_order: Feed in the order given instead of the digest order.
            For reproducing a simulated stream; the CLI never sets it.

    Raises:
        ChainError: If a unit repeats within the file or was consumed earlier.
    """
    ids = [str(u) for u in unit_ids]
    fired = np.asarray(fired, dtype=bool)
    if fired.shape != (len(ids),):
        raise ChainError("unit ids and outcomes differ in length")
    digests = [unit_digest(state.warrant_sha256, u) for u in ids]
    short = [d[:DIGEST_HEX] for d in digests]
    if len(set(short)) != len(short):
        raise ChainError("a unit id appears twice in this file; each unit is one observation")
    seen = set(state.consumed_unit_digests)
    reused = sum(1 for d in short if d in seen)
    if reused:
        raise ChainError(
            f"{reused} unit(s) in this file were already consumed by this chain. A label "
            "the detector has already passed cannot be counted as evidence twice. Unit "
            "ids must be unique across every file of a chain: use each item's own "
            "stable id, not a row number that restarts per file."
        )

    order = range(len(ids)) if in_given_order else sorted(range(len(ids)), key=digests.__getitem__)
    _, _, _, lams = _grid(state.p0, state.alpha)
    up, down = 1.0 + lams * (1.0 - state.p0), 1.0 - lams * state.p0
    statistics = np.asarray(state.statistics, dtype=float)
    threshold = state.threshold
    consumed = list(state.consumed_unit_digests)
    t = state.units_consumed
    revoked_at = state.revoked_at_unit
    fed = 0
    max_mean = 0.0
    for index in order:
        if t >= state.horizon_units or revoked_at is not None:
            break
        statistics = (statistics + 1.0) * (up if fired[index] else down)
        t += 1
        fed += 1
        consumed.append(short[index])
        mean = float(statistics.mean())
        max_mean = max(max_mean, mean)
        if mean >= threshold:
            revoked_at = t
    new_state = dataclasses.replace(
        state, units_consumed=t, statistics=tuple(float(v) for v in statistics),
        consumed_unit_digests=tuple(consumed), revoked_at_unit=revoked_at,
    )
    return FeedResult(
        state=new_state, units_in_file=len(ids), units_fed=fed,
        units_not_consumed=len(ids) - fed,
        revoked_here=revoked_at is not None and state.revoked_at_unit is None,
        max_mean_here=max_mean,
    )
