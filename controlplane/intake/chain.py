"""A year of rechecks as one change detector, carried in the recheck records.

``DECISIONS.md`` 193, from 187. A single ``warrant recheck`` tests one file on its
own, so a year of weekly rechecks is 52 tests and revokes a detector that kept its
promise in most years (0.8515, 187). A **chain** feeds every recheck's clean
negatives, one unit at a time, into one Shiryaev-Roberts e-detector -- the mean
over :class:`~controlplane.validation.warrant_stats.FPRMonitor`'s betting grid of
one detector per bet -- and revokes when that mean reaches ``N / alpha``.

**The guarantee, and its conditions.** For any true false-positive rate at or
below the certified budget, the probability that the chain revokes at any point
in its first ``N`` units is at most ``alpha``: ``R_t + (N - t)`` is a nonnegative
supermartingale from ``N`` that dominates the statistic, so Ville's inequality
applies (187). It holds for the chain **as kept** -- a user who discards an
unfavourable record and starts again has a new chain and a spent guarantee, and
nothing on one machine can stop that. What the records do is make it visible:
each carries the digest of the warrant and of the record before it.

**What is not the user's to choose.** ``N``, alpha and the grid are frozen when a
chain starts. Within a file, units are fed in the order of
``sha256(warrant digest, unit id)``, fixed before any score is read, so sorting or
shuffling a file changes nothing. A unit already consumed cannot be fed again.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from typing import Any, Optional, Sequence

import numpy as np

__all__ = [
    "METHOD",
    "ChainError",
    "ChainState",
    "FeedResult",
    "canonical_sha256",
    "continue_chain",
    "feed",
    "start_chain",
    "unit_digest",
]

METHOD = "mean_of_shiryaev_roberts_e_detectors_over_fprmonitor_grid"

#: Hex characters kept per consumed-unit digest. 96 bits: a collision among a
#: year's units is not a practical event, and a full-year chain stays well under
#: a megabyte.
DIGEST_HEX = 24


class ChainError(ValueError):
    """A chain cannot be started, continued or fed as asked. The CLI exits 2."""


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
        return {
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

    def to_payload(self) -> dict[str, Any]:
        body = self._body()
        return {
            **body,
            "state_sha256": canonical_sha256(body),
            "guarantee": (
                f"P(any false revocation in the first {self.horizon_units} units) <= "
                f"{self.alpha:g} for any true false-positive rate at or below "
                f"{self.p0:g} -- for this chain as kept. Starting a fresh chain after "
                "an unfavourable record spends the guarantee; keep every record."
            ),
        }

    @classmethod
    def from_payload(cls, block: dict[str, Any]) -> "ChainState":
        """Rebuild a state, refusing one whose digest does not reproduce."""
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
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ChainError(f"the chain block is incomplete or malformed ({exc})") from exc
        if block.get("method") != METHOD:
            raise ChainError(f"the chain was built by {block.get('method')!r}, not {METHOD!r}")
        if canonical_sha256(state._body()) != block.get("state_sha256"):
            raise ChainError(
                "the chain state does not reproduce its digest: it was edited after it "
                "was written, and a statistic that has been edited carries no guarantee"
            )
        if len(state.statistics) != state.n_lam:
            raise ChainError("the chain's statistics do not match its betting grid")
        return state


def start_chain(warrant_record: dict[str, Any], *, horizon_units: int, alpha: float) -> ChainState:
    """A new chain for this warrant, with ``N`` declared now and frozen."""
    if horizon_units < 1:
        raise ChainError(f"--horizon-labels must be a positive number of units, got {horizon_units}")
    budget = warrant_record.get("budget_fpr")
    if budget is None:
        raise ChainError("the warrant record carries no budget_fpr to monitor against")
    lam_lo, lam_hi, n_lam, _ = _grid(float(budget), alpha)
    return ChainState(
        warrant_sha256=canonical_sha256(warrant_record), p0=float(budget), alpha=alpha,
        lam_lo=lam_lo, lam_hi=lam_hi, n_lam=n_lam, horizon_units=int(horizon_units),
        units_consumed=0, statistics=tuple(0.0 for _ in range(n_lam)), sequence=1,
        previous_record_sha256=None, consumed_unit_digests=(),
    )


def continue_chain(
    previous_record: dict[str, Any], warrant_record: dict[str, Any], *, alpha: float
) -> ChainState:
    """The next link, refused unless it continues this warrant's live chain."""
    block = previous_record.get("chain")
    if not block:
        raise ChainError(
            "the --since record is not part of a chain. Start one with "
            "--horizon-labels on a recheck, then continue it with --since."
        )
    state = ChainState.from_payload(block)
    if state.warrant_sha256 != canonical_sha256(warrant_record):
        raise ChainError(
            "the --since record's chain belongs to a different warrant record; a chain "
            "cannot be moved between warrants"
        )
    if abs(state.alpha - alpha) > 1e-12:
        raise ChainError(f"the chain runs at alpha={state.alpha:g}, the warrant at {alpha:g}")
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
    return dataclasses.replace(
        state, sequence=state.sequence + 1,
        previous_record_sha256=canonical_sha256(previous_record),
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
    Ville's inequality bounds false revocation over the first ``N`` units by
    alpha (DECISIONS 187, 193). Checked after every unit.

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
            "the detector has already passed cannot be counted as evidence twice."
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
