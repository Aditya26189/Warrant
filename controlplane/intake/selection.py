"""The frontier as a selection device: how wrong is the row a customer picks? DECISIONS.md 192.

``warrant certify --frontier`` certifies every budget on its grid off one file's
negatives and invites the reader to pick a row. Each row's claim -- the true
false-positive rate at its threshold is at most its budget -- holds with
probability at least ``1 - alpha`` alone. A row chosen by looking at the others
is wrong at most as often as *any* certified row is, and this module measures
both, pre-registered, before the frontier changes or does not.

**Why most of it needs no model of the detector.** Item-level certification
depends only on the ranks of the negative scores. With continuous scores the
threshold certified at budget ``b`` sits just above the ``m``-th smallest
negative score, ``m = n - k*``, where ``k*`` is the largest count whose one-sided
Clopper-Pearson upper bound on ``n`` is at most ``b``. Mapping scores through the
true survival function makes negatives Uniform(0, 1) with ``FPR(t) = 1 - t``, so:

* which rows certify, and how many false positives each shows, depend on ``n``
  alone;
* a row is wrong exactly when at least ``m`` negatives fall below ``1 - b``:
  an exact binomial tail per row, and multinomial counts for all rows at once.

The pick rule is the one place a detector shape enters, because the *caught*
column is what makes a wrongly low threshold look attractive.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any, Optional, Sequence

import numpy as np

from .frontier import DEFAULT_GRID

__all__ = [
    "REGISTERED",
    "SelectionDesign",
    "certified_order_statistics",
    "crosscheck_against_certify",
    "joint_miscoverage",
    "pick_rule_miscoverage",
    "row_miscoverage",
    "run_study",
]


@dataclasses.dataclass(frozen=True)
class SelectionDesign:
    """The design ``DECISIONS.md`` 192 registered. Change it and it is a new study."""

    ns: tuple[int, ...] = (150, 300, 600, 1200, 5000)
    grid: tuple[float, ...] = tuple(DEFAULT_GRID)
    alpha: float = 0.05
    replicates: int = 20_000
    separations: tuple[float, ...] = (1.0, 2.0)
    positives_per_negative: float = 1.0 / 3.0
    recall_target: float = 0.5
    crosscheck_n: int = 300
    crosscheck_replicates: int = 2_000
    material: float = 0.10


REGISTERED = SelectionDesign()


def certified_order_statistics(n: int, grid: Sequence[float], alpha: float) -> dict[float, Optional[int]]:
    """For each budget, the 1-based order statistic its threshold sits above.

    ``None`` when the budget cannot certify at this ``n`` at all. Mirrors
    :func:`controlplane.validation.warrant_stats.certify_fpr`: candidates sit
    just above each negative score, lowest first, and the first whose bound
    clears the budget is taken -- above the ``i``-th smallest score ``n - i``
    negatives remain, so the first clearing ``i`` is ``n - k*``.
    """
    from ..validation.warrant_stats import cp_upper, min_n_for

    out: dict[float, Optional[int]] = {}
    for budget in grid:
        if n < min_n_for(float(budget), alpha):  # certify_fpr's own refusal rule
            out[float(budget)] = None
            continue
        if cp_upper(0, n, alpha) > budget:  # pragma: no cover - certify_fpr asserts this away
            raise AssertionError(f"n={n} clears min_n_for({budget}) but k=0 does not certify")
        # cp_upper is increasing in k, so the largest clearing k is found by bisection.
        low, high = 0, n - 1
        while low < high:
            mid = (low + high + 1) // 2
            if cp_upper(mid, n, alpha) <= budget:
                low = mid
            else:
                high = mid - 1
        out[float(budget)] = n - low
    return out


def row_miscoverage(n: int, budget: float, order_statistic: int) -> float:
    """Exact ``P(FPR(threshold) > budget)`` for one certified row.

    Quantity: the probability the certified threshold's true false-positive
    rate exceeds the budget. Propagation: exact -- the row is wrong when at
    least ``m`` of ``n`` uniform negatives fall below ``1 - budget``, a binomial
    upper tail, with no simulation and no assumption about the detector beyond
    continuous scores.
    """
    from scipy.stats import binom

    return float(binom.sf(order_statistic - 1, n, 1.0 - budget))


def joint_miscoverage(n: int, grid: Sequence[float], alpha: float, replicates: int,
                      rng: np.random.Generator) -> dict[str, float]:
    """``P(any certified row is wrong)``: the worst case over every pick rule.

    Quantity: the probability that at least one certified row's threshold has a
    true false-positive rate above its budget. Propagation: Monte Carlo over
    multinomial counts of ``n`` uniforms in the intervals cut at ``1 - b_j`` --
    exact in distribution for any continuous detector -- with the binomial
    standard error of the proportion reported beside it.
    """
    stats = certified_order_statistics(n, grid, alpha)
    live = sorted((1.0 - b, m) for b, m in stats.items() if m is not None)
    if not live:
        return {"value": 0.0, "mc_se": 0.0, "rows_certified": 0}
    cuts = np.array([c for c, _ in live])
    needed = np.array([m for _, m in live])
    edges = np.concatenate([[0.0], cuts, [1.0]])
    counts = rng.multinomial(n, np.diff(edges), size=replicates)
    below = np.cumsum(counts, axis=1)[:, :-1]  # negatives below each cut
    wrong = (below >= needed).any(axis=1)
    value = float(wrong.mean())
    return {"value": value, "mc_se": math.sqrt(value * (1 - value) / replicates),
            "rows_certified": int(len(live))}


def _order_statistics(n: int, indices: np.ndarray, replicates: int, rng: np.random.Generator) -> np.ndarray:
    """Joint draws of the ``indices``-th smallest of ``n`` uniforms, one row per replicate.

    Sequential beta increments: given the ``a``-th order statistic ``x``, the
    ``b``-th is ``x + (1 - x) * Beta(b - a, n - b + 1)``. Exact, and it avoids
    sorting ``n`` values per replicate.
    """
    out = np.empty((replicates, indices.size))
    previous_index, previous = 0, np.zeros(replicates)
    for column, index in enumerate(indices):
        if index == previous_index:
            # Two budgets certifying at the same order statistic share one
            # threshold; Beta(0, .) is undefined, and the value is the same draw.
            out[:, column] = previous
            continue
        step = rng.beta(index - previous_index, n - index + 1, size=replicates)
        previous = previous + (1.0 - previous) * step
        out[:, column] = previous
        previous_index = index
    return out


def pick_rule_miscoverage(n: int, grid: Sequence[float], alpha: float, separation: float,
                          design: SelectionDesign, replicates: int,
                          rng: np.random.Generator) -> dict[str, float]:
    """Rule R1: the tightest budget whose caught count reaches the recall target.

    Quantity: the probability the row R1 picks is wrong, unconditionally and
    given that it picks one. Propagation: Monte Carlo under a binormal ROC with
    separation ``separation`` -- negatives N(0, 1), positives N(d', 1), mapped to
    the negatives' uniform scale -- with thresholds drawn as joint order
    statistics and caught counts as sequential conditional binomials; the
    binomial standard error of each proportion is reported.
    """
    from scipy.stats import norm

    stats = certified_order_statistics(n, grid, alpha)
    rows = sorted((b, m) for b, m in stats.items() if m is not None)  # tightest budget first
    if not rows:
        return {"miscoverage": 0.0, "miscoverage_given_pick": 0.0, "pick_rate": 0.0, "mc_se": 0.0}
    budgets = np.array([b for b, _ in rows])
    indices = np.array([m for _, m in rows])
    n_pos = int(round(n * design.positives_per_negative))
    target = math.ceil(design.recall_target * n_pos)

    # Thresholds rise as budgets tighten; draw the order statistics ascending.
    ascending = np.argsort(indices)
    thresholds = np.empty((replicates, indices.size))
    thresholds[:, ascending] = _order_statistics(n, indices[ascending], replicates, rng)

    # Positives above each threshold: walk thresholds from highest to lowest,
    # adding the positives that fall between consecutive thresholds.
    def above(t: np.ndarray) -> np.ndarray:
        return norm.sf(norm.ppf(np.clip(t, 1e-300, 1 - 1e-16)) - separation)

    order = np.argsort(-indices)  # highest threshold first; the order is fixed by the indices
    caught = np.empty_like(thresholds, dtype=np.int64)
    remaining = np.full(replicates, n_pos)
    taken = np.zeros(replicates, dtype=np.int64)
    p_prev = np.zeros(replicates)
    for column in order:
        p_now = above(thresholds[:, column])
        # Conditional probability of landing in the new band among those not yet above.
        band = np.clip((p_now - p_prev) / np.clip(1 - p_prev, 1e-300, None), 0.0, 1.0)
        newly = rng.binomial(remaining, band)
        taken = taken + newly
        remaining = remaining - newly
        caught[:, column] = taken
        p_prev = np.maximum(p_prev, p_now)

    reaches = caught >= target
    picked = np.where(reaches.any(axis=1), reaches.argmax(axis=1), -1)
    has_pick = picked >= 0
    chosen_threshold = thresholds[np.arange(replicates), np.clip(picked, 0, None)]
    chosen_budget = budgets[np.clip(picked, 0, None)]
    wrong = has_pick & ((1.0 - chosen_threshold) > chosen_budget)
    miscoverage = float(wrong.mean())
    pick_rate = float(has_pick.mean())
    given = float(wrong[has_pick].mean()) if has_pick.any() else 0.0
    return {"miscoverage": miscoverage, "miscoverage_given_pick": given, "pick_rate": pick_rate,
            "mc_se": math.sqrt(max(given * (1 - given), 1e-12) / max(int(has_pick.sum()), 1))}


def crosscheck_against_certify(n: int, grid: Sequence[float], alpha: float, replicates: int,
                               rng: np.random.Generator) -> list[dict[str, Any]]:
    """Per-row miscoverage through the shipped function, beside the exact tail.

    Builds real files of uniform negative scores and certifies them with
    :func:`controlplane.intake.certify.certify_budget`, the step the frontier
    calls, so the analytic shortcut above and the code a customer runs are held
    to one answer.
    """
    from .certify import certify_budget
    from .contract import ScoredItems

    stats = certified_order_statistics(n, grid, alpha)
    wrong = {float(b): 0 for b in grid}
    ids = tuple(f"i{i}" for i in range(n))
    labels = tuple([0] * n)
    for _ in range(replicates):
        scores = rng.random(n)
        items = ScoredItems(ids=ids, labels=labels, scores=tuple(scores.tolist()),
                            groups=None, passthrough_columns=(), source="crosscheck")
        for budget in grid:
            certification = certify_budget(items, float(budget), alpha)
            if certification.fpr_certified and (1.0 - certification.threshold) > budget:
                wrong[float(budget)] += 1
    rows = []
    for budget in grid:
        m = stats[float(budget)]
        exact = row_miscoverage(n, float(budget), m) if m is not None else 0.0
        simulated = wrong[float(budget)] / replicates
        se = math.sqrt(max(exact * (1 - exact), 1e-12) / replicates)
        rows.append({"budget": float(budget), "exact": exact, "simulated": simulated,
                     "z": (simulated - exact) / se, "agrees": abs(simulated - exact) <= 3 * se + 1e-12})
    return rows


def run_study(design: SelectionDesign = REGISTERED, *, seed: int,
              replicates: Optional[int] = None,
              crosscheck_replicates: Optional[int] = None) -> dict[str, Any]:
    """Every registered cell, the cross-check and the three criteria.

    ``replicates`` and ``crosscheck_replicates`` other than the design's are
    smoke runs; the caller must not write them where the registered result
    lives.
    """
    reps = design.replicates if replicates is None else replicates
    cross_reps = design.crosscheck_replicates if crosscheck_replicates is None else crosscheck_replicates
    rng = np.random.default_rng(seed)
    bonferroni = design.alpha / len(design.grid)

    cells = []
    for n in design.ns:
        stats = certified_order_statistics(n, design.grid, design.alpha)
        strict = certified_order_statistics(n, design.grid, bonferroni)
        rows = []
        for budget in design.grid:
            m, m_strict = stats[float(budget)], strict[float(budget)]
            rows.append({
                "budget": float(budget),
                "certified": m is not None,
                "order_statistic": m,
                "exact_miscoverage": row_miscoverage(n, float(budget), m) if m is not None else None,
                "bonferroni_certified": m_strict is not None,
                "bonferroni_order_statistic": m_strict,
                # How far the threshold moves under the joint level, as a share of
                # negatives: the expected true FPR at the threshold falls by this.
                "bonferroni_threshold_shift": (
                    (m_strict - m) / (n + 1) if m is not None and m_strict is not None else None
                ),
            })
        cells.append({
            "n": n,
            "rows": rows,
            "joint": joint_miscoverage(n, design.grid, design.alpha, reps, rng),
            "r1": {f"d'={s:g}": pick_rule_miscoverage(n, design.grid, design.alpha, s, design, reps, rng)
                   for s in design.separations},
        })

    crosscheck = crosscheck_against_certify(design.crosscheck_n, design.grid, design.alpha, cross_reps, rng)

    worst_row = max((r["exact_miscoverage"] for c in cells for r in c["rows"] if r["exact_miscoverage"] is not None), default=0.0)
    worst_r1 = max(v["miscoverage_given_pick"] for c in cells for v in c["r1"].values())
    return {
        "kind": "frontier_selection_study",
        "decision": "DECISIONS.md 192",
        "design": dataclasses.asdict(design),
        "replicates": reps,
        "crosscheck_replicates": cross_reps,
        "registered_run": reps == design.replicates and cross_reps == design.crosscheck_replicates,
        "cells": cells,
        "crosscheck": crosscheck,
        "criteria": {
            "M3_sanity": {"worst_row_miscoverage": worst_row, "passes": worst_row <= design.alpha,
                          "crosscheck_agrees": all(r["agrees"] for r in crosscheck)},
            "M1_material": {"worst_r1_miscoverage_given_pick": worst_r1, "threshold": design.material,
                            "material": worst_r1 > design.material},
            "M2_bonferroni_alpha": bonferroni,
        },
        "what_these_are": (
            "Simulated operating characteristics of the frontier used as a selection "
            "device, under uniform negatives and binormal positives. Not a measurement "
            "of any detector. Per-row and joint figures hold for any continuous-score "
            "detector at item level; R1 depends on the stated ROC shape."
        ),
    }
