"""The chain's detection grid is the study 196 registered (DECISIONS.md 196).

The simulator is 187's and already pinned to shipped code in
test_recheck_schedules.py. What is pinned here is that the grid is the registered
one and that each criterion is evaluated as written -- P1 strictly, P3 on S2.
"""

from __future__ import annotations

from controlplane.economics.detection_grid import (
    BREACHES,
    CADENCES,
    REGISTERED_YEARS,
    evaluate_criteria,
    registered_designs,
    run_grid,
)
from controlplane.economics.schedules import RULES, RuleSummary


def test_the_grid_is_the_registered_one() -> None:
    designs = registered_designs()
    assert [d.breach for d in designs] == [0.075, 0.10, 0.15]
    assert [d.negatives_per_recheck for d in designs] == [628, 191, 59]
    assert all((d.budget, d.alpha, d.certified_rate, d.years) == (0.05, 0.05, 0.0371, 2000) for d in designs)
    assert [(c.name, c.rechecks, c.change_after, c.window) for c in CADENCES] == [
        ("weekly-13", 52, 13, 13), ("weekly-26", 52, 26, 13),
        ("weekly-39", 52, 39, 13), ("monthly-6", 12, 6, 3),
    ]
    assert REGISTERED_YEARS == 2000


def _cell(*, revoked=0.01, caught=0.9) -> RuleSummary:
    return RuleSummary(rule="e_detector", cadence="x", scenario="x", years=2000, rechecks=52,
                       negatives_per_recheck=100, revoked_in_year=revoked,
                       revoked_before_change=revoked, caught_in_window=caught,
                       median_delay=1.0, extra={})


def _index(overrides=None):
    index = {}
    for breach in BREACHES:
        for cadence in CADENCES:
            for scenario in ("S0", "S1", "S2", "S3"):
                index[(breach, cadence.name, scenario, "e_detector")] = _cell(
                    caught=0.80 + 0.05 * BREACHES.index(breach)
                    - (0.1 if cadence.name == "weekly-39" else 0.0))
    for key, cell in (overrides or {}).items():
        index[key] = cell
    return index


def test_v_fails_on_one_cell_over_the_limit() -> None:
    verdict = evaluate_criteria(_index({(0.10, "monthly-6", "S1", "e_detector"): _cell(revoked=0.07)}), 2000)
    assert verdict["V"]["all_pass"] is False
    failing = [c for c in verdict["V"]["cells"] if not c["passes"]]
    assert failing == [c for c in failing if (c["breach"], c["cadence"], c["scenario"]) == (0.10, "monthly-6", "S1")]


def test_p1_is_strict() -> None:
    lower = _index({(0.15, "weekly-26", "S2", "e_detector"): _cell(caught=0.849)})
    verdict = evaluate_criteria(lower, 2000)
    assert verdict["P1"]["all_hold"] is False


def test_p2_allows_two_standard_errors_and_no_more() -> None:
    base = _index()
    s2 = base[(0.075, "weekly-13", "S2", "e_detector")].caught_in_window
    close = _index({(0.075, "weekly-13", "S3", "e_detector"): _cell(caught=s2 - 0.01)})
    far = _index({(0.075, "weekly-13", "S3", "e_detector"): _cell(caught=s2 - 0.05)})
    assert evaluate_criteria(close, 2000)["P2"]["all_hold"] is True
    assert evaluate_criteria(far, 2000)["P2"]["all_hold"] is False


def test_p3_compares_week_39_with_week_13_on_s2() -> None:
    verdict = evaluate_criteria(_index(), 2000)
    assert verdict["P3"]["all_hold"] is True
    reversed_ = _index({(b, "weekly-39", "S2", "e_detector"): _cell(caught=0.99) for b in BREACHES})
    assert evaluate_criteria(reversed_, 2000)["P3"]["all_hold"] is False


def test_a_tiny_grid_has_every_cell_and_every_criterion() -> None:
    grid = run_grid(seed=3, years=2)
    assert len(grid["cells"]) == len(BREACHES) * len(CADENCES) * 4 * len(RULES)
    assert set(grid["criteria"]) == {"V", "P1", "P2", "P3"}
    assert "not any detector" in grid["what_these_are"]
