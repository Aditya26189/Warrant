"""A year of rechecks, compared as change detection (DECISIONS.md 187).

The comparison is only worth its numbers if each simulated rule IS the rule it
names. So most of this file pins the simulation to shipped code: the critical
count to `recheck`'s own floor, the closed-form monitor to `FPRMonitor` fed one
label at a time, and the e-detector to an explicit loop.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest

from controlplane.economics.schedules import (
    REGISTERED,
    RULES,
    Cadence,
    RuleSummary,
    Scenario,
    StudyDesign,
    apply_criteria,
    critical_count,
    monitor_revokes,
    simulate,
)
from controlplane.intake.recheck import smallest_detectable_breach
from controlplane.validation.warrant_stats import FPRMonitor

ALPHA = 0.05


@pytest.mark.parametrize("n,budget", [(100, 0.05), (628, 0.05), (400, 0.01), (50, 0.2)])
def test_the_critical_count_is_the_one_recheck_revokes_at(n: int, budget: float) -> None:
    k = critical_count(n, budget, ALPHA)
    floor = smallest_detectable_breach(n, budget, ALPHA)
    if floor is None:
        assert k == n + 1
    else:
        assert k == round(floor * n)


def test_splitting_alpha_raises_the_critical_count() -> None:
    assert critical_count(628, 0.05, ALPHA / 52) > critical_count(628, 0.05, ALPHA)


def _streams(seed: int):
    rng = np.random.default_rng(seed)
    yield "null", (rng.random(900) < 0.05).astype(int)
    yield "breach", (rng.random(900) < 0.12).astype(int)
    # Early burst: drives the most aggressive bets high while the mixture stays
    # low, which is the region where the cap and the mixture disagree.
    burst = np.zeros(900, dtype=int)
    burst[:2] = 1
    yield "burst", burst


@pytest.mark.parametrize("p0", [0.05, 0.02])
def test_the_closed_form_monitor_is_fprmonitor(p0: float) -> None:
    """Counts in, `revoked` out, equal to feeding the monitor label by label."""
    for name, stream in _streams(7):
        monitor = FPRMonitor(p0=p0, alpha=ALPHA)
        for t, x in enumerate(stream, start=1):
            monitor.update(int(x))
            if t > 30 and t % 25:  # every label early, where the cap bites
                continue
            k = int(stream[:t].sum())
            ours = bool(monitor_revokes(np.array([t]), np.array([k]), p0, ALPHA)[0])
            assert ours == monitor.revoked, f"{name} p0={p0} t={t} k={k}"
            mixture = float(np.mean(np.exp(monitor._logw)))
            uncapped = bool(monitor_revokes(np.array([t]), np.array([k]), p0, ALPHA, capped=False)[0])
            assert uncapped == (mixture >= 1.0 / ALPHA), f"{name} p0={p0} t={t}"


def test_the_cap_revokes_where_the_mixture_does_not() -> None:
    """The suspected defect 187 records, shown to exist rather than argued.

    Two false positives in the first two labels at p0 = 0.05: the largest bet's
    wealth is 110 (above e/alpha = 54.4) while the mean over the grid is 14.2,
    under 1/alpha = 20. The shipped monitor revokes; the e-process has not.
    """
    p0 = 0.05
    capped = monitor_revokes(np.array([2]), np.array([2]), p0, ALPHA)[0]
    uncapped = monitor_revokes(np.array([2]), np.array([2]), p0, ALPHA, capped=False)[0]
    monitor = FPRMonitor(p0=p0, alpha=ALPHA)
    for _ in range(2):
        monitor.update(1)
    mixture = float(np.mean(np.exp(monitor._logw)))
    assert monitor.revoked and capped
    assert not uncapped and mixture < 1.0 / ALPHA, (
        "the burst no longer separates the cap from the mixture; pick a stream that does"
    )


def _small(**overrides) -> StudyDesign:
    base = dict(
        budget=0.05, alpha=ALPHA, breach=0.15, negatives_per_recheck=60, years=600,
        cadences=(Cadence("short", rechecks=10, change_after=5, window=3),),
        certified_rate=0.03,
    )
    base.update(overrides)
    return StudyDesign(**base)


def test_the_e_detector_is_the_recursion_it_claims() -> None:
    """One stream, explicit loop, same first alarm as the vectorised simulation."""
    design = _small(years=1)
    cadence = design.cadences[0]
    scenario = Scenario("S2", 0.05, 0.3, 5)
    result = simulate(design, cadence, scenario, seed=3)

    rng = np.random.default_rng(3)
    lams = FPRMonitor(p0=0.05, alpha=ALPHA).lams
    stats = np.zeros(lams.size)
    threshold = cadence.rechecks * design.negatives_per_recheck / ALPHA
    first = -1
    for j in range(cadence.rechecks):
        draws = rng.random((1, design.negatives_per_recheck)) < scenario.rate_at(j)
        for x in draws[0]:
            stats = (stats + 1.0) * (1.0 + lams * (float(x) - 0.05))
        if first < 0 and stats.mean() >= threshold:
            first = j
    summary = result["e_detector"]
    assert summary.revoked_in_year == (1.0 if first >= 0 else 0.0)


def test_rules_that_promise_the_year_keep_it_on_a_small_null() -> None:
    """Under S0 the split, the uncapped mixture and the e-detector stay near alpha.

    600 simulated years: the limit is alpha plus 3 Monte Carlo standard errors,
    as 187's criterion V is written.
    """
    design = _small()
    out = simulate(design, design.cadences[0], Scenario("S0", 0.05, 0.05), seed=11)
    se = math.sqrt(ALPHA * (1 - ALPHA) / design.years)
    for rule in ("split", "monitor_uncapped", "e_detector"):
        assert out[rule].revoked_in_year <= ALPHA + 3 * se, (rule, out[rule].revoked_in_year)


def test_a_large_breach_is_caught_by_the_sequential_rules() -> None:
    design = _small()
    out = simulate(design, design.cadences[0], Scenario("S2", 0.05, 0.25, 5), seed=12)
    for rule in ("fixed", "e_detector"):
        assert out[rule].caught_in_window > 0.5, (rule, out[rule].caught_in_window)


def test_a_year_revoked_before_the_change_did_not_catch_it() -> None:
    """Crying wolf early is not detection, so it never counts as a catch."""
    design = _small()
    out = simulate(design, design.cadences[0], Scenario("S2", 0.05, 0.25, 5), seed=13)
    for rule in RULES:
        s = out[rule]
        assert s.caught_in_window + s.revoked_before_change <= s.revoked_in_year + 1e-12


def _cell(rule, *, s0, s2=None, delay=None, cadence="weekly", years=4000):
    common = dict(rule=rule, cadence=cadence, years=years, rechecks=52,
                  negatives_per_recheck=628, extra={})
    return [
        RuleSummary(scenario="S0", revoked_in_year=s0, revoked_before_change=s0,
                    caught_in_window=None, median_delay=None, **common),
        RuleSummary(scenario="S2", revoked_in_year=0.9, revoked_before_change=0.01,
                    caught_in_window=s2, median_delay=delay, **common),
    ]


def _design_one_cadence() -> StudyDesign:
    return dataclasses.replace(REGISTERED, cadences=(REGISTERED.cadences[0],))


def test_the_criteria_exclude_an_invalid_rule_however_fast() -> None:
    cells = (
        _cell("fixed", s0=0.86, s2=0.99, delay=0)
        + _cell("split", s0=0.03, s2=0.60, delay=4)
        + _cell("monitor", s0=0.20, s2=0.95, delay=1)
        + _cell("monitor_uncapped", s0=0.01, s2=0.99, delay=1)
        + _cell("e_detector", s0=0.02, s2=0.70, delay=3)
    )
    verdict = apply_criteria(cells, _design_one_cadence())
    assert verdict["primary"]["eligible"] == ["split", "e_detector"]
    assert verdict["primary"]["chosen"] == "e_detector"


def test_a_tie_goes_to_the_lower_delay() -> None:
    cells = (
        _cell("fixed", s0=0.86, s2=0.99)
        + _cell("split", s0=0.03, s2=0.700, delay=2)
        + _cell("monitor", s0=0.03, s2=0.704, delay=6)
        + _cell("monitor_uncapped", s0=0.01, s2=0.9)
        + _cell("e_detector", s0=0.02, s2=0.60, delay=1)
    )
    verdict = apply_criteria(cells, _design_one_cadence())
    assert verdict["primary"]["chosen"] == "split"


def test_nothing_is_chosen_below_the_floor() -> None:
    cells = (
        _cell("fixed", s0=0.86, s2=0.99)
        + _cell("split", s0=0.03, s2=0.30, delay=9)
        + _cell("monitor", s0=0.03, s2=0.20, delay=12)
        + _cell("monitor_uncapped", s0=0.01, s2=0.9)
        + _cell("e_detector", s0=0.02, s2=0.45, delay=8)
    )
    verdict = apply_criteria(cells, _design_one_cadence())
    assert verdict["primary"]["chosen"] is None
    assert verdict["primary"]["floor_met"] is False


def test_the_registered_design_is_the_one_187_wrote_down() -> None:
    assert (REGISTERED.budget, REGISTERED.alpha, REGISTERED.breach) == (0.05, 0.05, 0.075)
    assert REGISTERED.negatives_per_recheck == 628
    assert REGISTERED.years == 4000
    assert [(c.name, c.rechecks, c.change_after, c.window) for c in REGISTERED.cadences] == [
        ("weekly", 52, 26, 13), ("monthly", 12, 6, 3),
    ]
