"""The frontier-selection study measures what it says it measures. DECISIONS.md 192.

The study's shortcuts -- a certified threshold as a fixed order statistic,
per-row error as a binomial tail, joint error from multinomial counts, order
statistics from beta increments -- are each checked here against the direct
computation they replace, so the registered result rests on checked arithmetic
rather than on the derivation in the module docstring.
"""

from __future__ import annotations

import numpy as np
import pytest

from controlplane.intake.selection import (
    REGISTERED,
    _order_statistics,
    certified_order_statistics,
    joint_miscoverage,
    row_miscoverage,
    run_study,
)
from controlplane.validation.warrant_stats import certify_fpr


@pytest.mark.parametrize("n", [150, 300, 1200])
def test_the_certified_threshold_is_the_order_statistic_the_study_uses(n: int) -> None:
    rng = np.random.default_rng(n)
    scores = rng.random(n)
    ordered = np.sort(scores)
    for budget, index in certified_order_statistics(n, REGISTERED.grid, 0.05).items():
        certification = certify_fpr(scores, budget, alpha=0.05)
        if index is None:
            assert not certification.fpr_certified, budget
        else:
            assert certification.fpr_certified, budget
            assert certification.threshold == np.nextafter(ordered[index - 1], np.inf)
            assert certification.k == n - index


def test_every_row_meets_its_level_alone() -> None:
    """M3 in exact arithmetic: if a row failed this, nothing downstream stands."""
    for n in REGISTERED.ns:
        for budget, index in certified_order_statistics(n, REGISTERED.grid, 0.05).items():
            if index is not None:
                assert row_miscoverage(n, budget, index) <= 0.05, (n, budget)


def test_the_joint_level_is_at_least_every_row_and_at_most_their_sum() -> None:
    n = 600
    rows = [row_miscoverage(n, b, m)
            for b, m in certified_order_statistics(n, REGISTERED.grid, 0.05).items() if m is not None]
    joint = joint_miscoverage(n, REGISTERED.grid, 0.05, 20_000, np.random.default_rng(3))
    slack = 3 * joint["mc_se"]
    assert joint["value"] >= max(rows) - slack
    assert joint["value"] <= sum(rows) + slack


def test_joint_counts_agree_with_sorting_real_samples() -> None:
    """The multinomial shortcut against the obvious computation, at a small n."""
    n, reps = 300, 4_000
    stats = certified_order_statistics(n, REGISTERED.grid, 0.05)
    rng = np.random.default_rng(11)
    samples = np.sort(rng.random((reps, n)), axis=1)
    wrong = np.zeros(reps, dtype=bool)
    for budget, index in stats.items():
        if index is not None:
            wrong |= (1.0 - samples[:, index - 1]) > budget
    direct = wrong.mean()
    shortcut = joint_miscoverage(n, REGISTERED.grid, 0.05, reps, np.random.default_rng(12))
    se = np.sqrt(direct * (1 - direct) / reps) * np.sqrt(2)
    assert abs(shortcut["value"] - direct) <= 3 * se


def test_beta_increments_draw_the_right_order_statistics() -> None:
    n, reps = 200, 20_000
    indices = np.array([20, 100, 180])
    draws = _order_statistics(n, indices, reps, np.random.default_rng(5))
    expected = indices / (n + 1)
    assert np.allclose(draws.mean(axis=0), expected, atol=0.003)
    assert (np.diff(draws, axis=1) > 0).all(), "order statistics must be increasing"


def test_budgets_sharing_an_order_statistic_share_a_threshold() -> None:
    """Found by the first smoke run: equal indices made Beta(0, .) and raised."""
    draws = _order_statistics(50, np.array([10, 10, 40]), 100, np.random.default_rng(2))
    assert (draws[:, 0] == draws[:, 1]).all()
    assert (draws[:, 2] > draws[:, 1]).all()


def test_a_smoke_sized_study_is_marked_as_one() -> None:
    study = run_study(REGISTERED, seed=1, replicates=200, crosscheck_replicates=3)
    assert study["registered_run"] is False
    assert {cell["n"] for cell in study["cells"]} == set(REGISTERED.ns)
    assert study["criteria"]["M2_bonferroni_alpha"] == pytest.approx(0.05 / 8)
    assert "Not a measurement" in study["what_these_are"]
