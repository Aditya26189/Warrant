"""A year of rechecks, compared as sequential change detection.

``DECISIONS.md`` 187, pre-registered. ``warrant recheck`` tests each recheck on
its own sample. A monitoring programme runs dozens of them a year, and the
question it actually has is **how soon a breach that starts mid-year is caught,
at a bounded chance of revoking a detector that never breached**. That is
sequential change detection, and this module measures how five revocation rules
answer it when every rule reads the same labelled negatives in the same order.

=====================  =====================================================
``fixed``              the shipped rule: one-sided Clopper-Pearson lower bound
                       on the recheck's own sample, at ``alpha``
``split``              the same bound at ``alpha / K``
``monitor``            :class:`~controlplane.validation.warrant_stats.FPRMonitor`
                       as shipped, over every label, checked at each recheck
``monitor_uncapped``   the same mixture without its cap -- a reference for the
                       suspected defect 187 records, not a candidate
``e_detector``         the mean over the monitor's betting grid of one
                       Shiryaev-Roberts e-detector per bet, threshold N/alpha
=====================  =====================================================

**What the numbers are.** Operating characteristics of decision rules under a
known truth, exact up to Monte Carlo error. They describe the rules, not any
detector, and every figure travels with its scenario.

**Why the e-detector's threshold is N / alpha.** For one bet ``lam`` the
statistic is ``R_t = (R_{t-1} + 1) * (1 + lam (x_t - p0))``, and under any
true rate ``p <= p0`` the conditional mean of the second factor is at most one.
So ``V_t = R_t + (N - t)`` is a nonnegative supermartingale from ``V_0 = N``
that dominates ``R_t`` for ``t <= N``, and Ville's inequality gives
``P(max_{t<=N} R_t >= N / alpha) <= alpha``. A mean of such statistics inherits
the bound. Construction: Shin, Ramdas and Rinaldo (2023), *E-detectors: a
nonparametric framework for sequential change detection*, NEJSDS.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

__all__ = [
    "RULES",
    "REGISTERED",
    "RuleSummary",
    "Scenario",
    "StudyDesign",
    "critical_count",
    "monitor_revokes",
    "run_study",
    "simulate",
]

#: The five rules, in the order 187 lists them.
RULES: tuple[str, ...] = ("fixed", "split", "monitor", "monitor_uncapped", "e_detector")

#: The rules eligible under 187's primary criterion. ``monitor_uncapped`` is a
#: reference for the cap's effect and is not shipped code.
CANDIDATES: tuple[str, ...] = ("split", "monitor", "e_detector")


@dataclass(frozen=True)
class Scenario:
    """The true false-positive rate across one simulated year."""

    name: str
    rate_before: float
    rate_after: float
    #: Rechecks at ``rate_before`` before the rate changes; ``None`` for a year
    #: with no change.
    change_after: Optional[int] = None

    def rate_at(self, recheck: int) -> float:
        if self.change_after is None or recheck < self.change_after:
            return self.rate_before
        return self.rate_after


@dataclass(frozen=True)
class Cadence:
    """A schedule: how many rechecks a year, and the catch window after a change."""

    name: str
    rechecks: int
    change_after: int
    window: int


@dataclass(frozen=True)
class StudyDesign:
    """The setting 187 registered. Not a config knob: changing it is a new study."""

    budget: float
    alpha: float
    breach: float
    negatives_per_recheck: int
    years: int
    cadences: tuple[Cadence, ...]
    certified_rate: float

    def scenarios(self, cadence: Cadence) -> tuple[Scenario, ...]:
        half = cadence.change_after
        return (
            Scenario("S0", self.budget, self.budget),
            Scenario("S1", self.certified_rate, self.certified_rate),
            Scenario("S2", self.budget, self.breach, half),
            Scenario("S3", self.certified_rate, self.breach, half),
        )


#: ``DECISIONS.md`` 187. ``negatives_per_recheck`` is 183's 0.80-power size at
#: this budget, breach and alpha; ``certified_rate`` is the measured true rate
#: of the certified threshold in 143.
REGISTERED = StudyDesign(
    budget=0.05,
    alpha=0.05,
    breach=0.075,
    negatives_per_recheck=628,
    years=4000,
    cadences=(
        Cadence("weekly", rechecks=52, change_after=26, window=13),
        Cadence("monthly", rechecks=12, change_after=6, window=3),
    ),
    certified_rate=0.0371,
)


def critical_count(n: int, budget: float, alpha: float) -> int:
    """Fewest false positives in ``n`` whose lower bound revokes; ``n + 1`` if none.

    Uses :func:`controlplane.intake.recheck._lower_bound_at`, the function a
    recheck decides with, so the simulated rule and the shipped one cannot
    differ. Scalar, because each rule has one ``n``.
    """
    from ..intake.recheck import _lower_bound_at

    for k in range(1, n + 1):
        if _lower_bound_at(n, k, alpha) > budget:
            return k
    return n + 1


def _grid(p0: float, alpha: float) -> np.ndarray:
    """The betting grid, taken from the shipped monitor rather than restated."""
    from ..validation.warrant_stats import FPRMonitor

    return np.asarray(FPRMonitor(p0=p0, alpha=alpha).lams, dtype=float)


def monitor_revokes(
    labels_seen: np.ndarray, false_positives: np.ndarray, p0: float, alpha: float,
    *, capped: bool = True,
) -> np.ndarray:
    """``FPRMonitor.revoked`` after these counts, for many streams at once.

    Each bet's log-wealth depends only on how many labels were seen and how many
    fired, because its per-label factors commute:
    ``k log(1 + lam (1 - p0)) + (t - k) log(1 - lam p0)``. With ``capped`` this
    reproduces the shipped ``wealth`` exactly, cap included -- revoked when the
    largest bet exceeds ``log(1/alpha) + 1`` or the mixture mean reaches
    ``1/alpha``. Without it, only the mixture mean decides. Pinned against the
    monitor fed label by label in ``tests/test_recheck_schedules.py``.
    """
    lams = _grid(p0, alpha)
    t = np.asarray(labels_seen, dtype=float)[..., None]
    k = np.asarray(false_positives, dtype=float)[..., None]
    logw = k * np.log1p(lams * (1.0 - p0)) + (t - k) * np.log1p(-lams * p0)
    top = logw.max(axis=-1)
    mixture = top + np.log(np.mean(np.exp(logw - top[..., None]), axis=-1))
    threshold = math.log(1.0 / alpha)
    by_mixture = mixture >= threshold
    if not capped:
        return by_mixture
    return by_mixture | (top > threshold + 1.0)


@dataclass(frozen=True)
class RuleSummary:
    """One rule, one cadence, one scenario: what a year of it does."""

    rule: str
    cadence: str
    scenario: str
    years: int
    rechecks: int
    negatives_per_recheck: int
    #: Share of years with at least one revocation.
    revoked_in_year: float
    #: Share of years revoked before the rate changed. For a year with no change
    #: this equals ``revoked_in_year``.
    revoked_before_change: float
    #: Share of years whose FIRST revocation lands within the window after the
    #: change. A year revoked earlier did not catch the breach, it cried wolf.
    caught_in_window: Optional[float]
    #: Median rechecks from the change to the first revocation, over years whose
    #: first revocation is at or after the change; ``None`` if under half are.
    median_delay: Optional[float]
    extra: dict[str, Any] = field(default_factory=dict)

    def mc_se(self, share: float) -> float:
        """Monte Carlo standard error of a share of ``years``."""
        return math.sqrt(max(share * (1.0 - share), 1e-12) / self.years)

    def to_payload(self) -> dict[str, Any]:
        def with_se(value: Optional[float]) -> Optional[dict[str, float]]:
            if value is None:
                return None
            return {"value": value, "mc_se": self.mc_se(value)}

        return {
            "rule": self.rule,
            "cadence": self.cadence,
            "scenario": self.scenario,
            "years": self.years,
            "rechecks": self.rechecks,
            "negatives_per_recheck": self.negatives_per_recheck,
            "labels_per_year": self.rechecks * self.negatives_per_recheck,
            "revoked_in_year": with_se(self.revoked_in_year),
            "revoked_before_change": with_se(self.revoked_before_change),
            "caught_in_window": with_se(self.caught_in_window),
            "median_delay_rechecks": self.median_delay,
            **self.extra,
        }


def simulate(
    design: StudyDesign, cadence: Cadence, scenario: Scenario, *, seed: int,
    years: Optional[int] = None,
) -> dict[str, RuleSummary]:
    """Simulate ``years`` of one cadence under one scenario, for every rule.

    Quantity: per rule, the share of simulated years with any revocation, with
    a revocation before the change, and with the first revocation inside the
    catch window after it -- probabilities of events under a declared true
    false-positive rate. Propagation: Monte Carlo over independent simulated
    years; each share carries the binomial standard error
    ``sqrt(p (1 - p) / years)`` (:meth:`RuleSummary.mc_se`), and 187's criteria
    compare shares against limits stated in those units.

    Every rule reads the same labels: each recheck's Bernoulli draws are made
    once, counted for the per-recheck rules and fed in order to the e-detector.
    """
    years = design.years if years is None else years
    n, K, p0, alpha = design.negatives_per_recheck, cadence.rechecks, design.budget, design.alpha
    rng = np.random.default_rng(seed)
    lams = _grid(p0, alpha)
    up, down = 1.0 + lams * (1.0 - p0), 1.0 - lams * p0
    total = K * n
    e_threshold = total / alpha

    k_fixed = critical_count(n, p0, alpha)
    k_split = critical_count(n, p0, alpha / K)

    first = {rule: np.full(years, -1, dtype=np.int64) for rule in RULES}
    seen_fp = np.zeros(years, dtype=np.int64)
    detector = np.zeros((years, lams.size), dtype=float)

    def mark(rule: str, fired: np.ndarray, recheck: int) -> None:
        fresh = fired & (first[rule] < 0)
        first[rule][fresh] = recheck

    for j in range(K):
        draws = rng.random((years, n)) < scenario.rate_at(j)
        counts = draws.sum(axis=1)
        seen_fp += counts
        labels_seen = np.full(years, (j + 1) * n)

        mark("fixed", counts >= k_fixed, j)
        mark("split", counts >= k_split, j)
        mark("monitor", monitor_revokes(labels_seen, seen_fp, p0, alpha), j)
        mark("monitor_uncapped", monitor_revokes(labels_seen, seen_fp, p0, alpha, capped=False), j)

        for i in range(n):
            factor = np.where(draws[:, i : i + 1], up, down)
            detector = np.minimum((detector + 1.0) * factor, 1e300)
        mark("e_detector", detector.mean(axis=1) >= e_threshold, j)

    change = scenario.change_after
    summaries: dict[str, RuleSummary] = {}
    for rule in RULES:
        f = first[rule]
        revoked = f >= 0
        if change is None:
            before = revoked
            caught = None
            delay = None
        else:
            before = revoked & (f < change)
            caught = float((revoked & (f >= change) & (f < change + cadence.window)).mean())
            after = f[revoked & (f >= change)] - change
            delay = float(np.median(after)) if after.size * 2 >= years else None
        summaries[rule] = RuleSummary(
            rule=rule, cadence=cadence.name, scenario=scenario.name, years=years,
            rechecks=K, negatives_per_recheck=n,
            revoked_in_year=float(revoked.mean()),
            revoked_before_change=float(before.mean()),
            caught_in_window=caught, median_delay=delay,
            extra={"critical_count": k_fixed if rule == "fixed" else (
                k_split if rule == "split" else None)},
        )
    return summaries


def run_study(design: StudyDesign = REGISTERED, *, seed: int, years: Optional[int] = None) -> dict[str, Any]:
    """Every cadence and scenario, then 187's criteria applied to the result.

    Seeds differ per (cadence, scenario) so no two cells share draws, and are
    derived from ``seed`` so the whole study reproduces from one number.
    """
    cells: list[RuleSummary] = []
    for c_index, cadence in enumerate(design.cadences):
        for s_index, scenario in enumerate(design.scenarios(cadence)):
            cell_seed = seed + 1000 * c_index + s_index
            cells.extend(simulate(design, cadence, scenario, seed=cell_seed, years=years).values())
    return {
        "design": {
            "decision": "DECISIONS.md 187",
            "budget": design.budget, "alpha": design.alpha, "breach": design.breach,
            "negatives_per_recheck": design.negatives_per_recheck,
            "years": design.years if years is None else years,
            "certified_rate": design.certified_rate,
            "cadences": [vars(c) for c in design.cadences],
            "seed": seed,
        },
        "what_these_are": (
            "Simulated operating characteristics of revocation rules under a known "
            "true false-positive rate, exact up to Monte Carlo error. They describe "
            "the rules, not any detector."
        ),
        "cells": [cell.to_payload() for cell in cells],
        "criteria": apply_criteria(cells, design),
    }


def apply_criteria(cells: list[RuleSummary], design: StudyDesign) -> dict[str, Any]:
    """187's V, P and floor, applied mechanically to the simulated cells."""
    by_key = {(c.rule, c.cadence, c.scenario): c for c in cells}
    validity = {}
    for cadence in design.cadences:
        for rule in RULES:
            cell = by_key[(rule, cadence.name, "S0")]
            limit = design.alpha + 3 * cell.mc_se(design.alpha)
            validity[f"{rule}/{cadence.name}"] = {
                "revoked_in_year": cell.revoked_in_year,
                "limit": limit,
                "passes": cell.revoked_in_year <= limit,
            }

    primary_cadence = design.cadences[0].name
    eligible = [
        by_key[(rule, primary_cadence, "S2")]
        for rule in CANDIDATES
        if validity[f"{rule}/{primary_cadence}"]["passes"]
    ]
    chosen: Optional[str] = None
    floor_met = False
    if eligible:
        best = max(eligible, key=lambda c: c.caught_in_window or 0.0)
        tied = [
            c for c in eligible
            if (best.caught_in_window or 0.0) - (c.caught_in_window or 0.0)
            <= 2 * best.mc_se(best.caught_in_window or 0.0)
        ]
        best = min(tied, key=lambda c: (math.inf if c.median_delay is None else c.median_delay))
        floor_met = (best.caught_in_window or 0.0) >= 0.50
        chosen = best.rule if floor_met else None
    return {
        "validity": validity,
        "primary": {
            "cadence": primary_cadence,
            "scenario": "S2",
            "eligible": [c.rule for c in eligible],
            "chosen": chosen,
            "floor_met": floor_met,
            "note": (
                "Chosen among rules passing validity, by the share of years whose "
                "first revocation lands within the window after the change; ties "
                "within 2 MC SE go to the lower median delay. No rule is chosen when "
                "the best catches under 0.50, and the shipped rule then stays."
            ),
        },
    }
