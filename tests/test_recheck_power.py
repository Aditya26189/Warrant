"""A recheck's sample size is a probability of catching a breach. DECISIONS.md 183.

146 sized a recheck so that an *observed* rate equal to the breach would revoke.
At a *true* breach the count is binomial and reaches the critical count about
half the time, so every size it quoted caught its breach with probability near
0.49, and the plan never said so. It also priced 52 rechecks a year without
saying what 52 tests do to a detector that kept its promise.

These tests are 183's pre-registered criteria, C1 to C4, in executable form.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import beta

from controlplane.config import ConfigError, ValidationConfig
from controlplane.economics.sizing import (
    DEFAULT_CADENCES,
    critical_counts,
    false_revocation_in_year,
    monitoring_plan,
    negatives_for_detection,
    negatives_for_power,
    revocation_probability,
)
from controlplane.intake.render import render_plan

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALPHA = 0.05
POWER = 0.80

#: (budget, breach, 146's size, its power, 183's size at 0.80, scratch estimate).
#: The scratch column is what 183 recorded before the implementation existed;
#: C3 required the implementation to land within 5% of it.
ROWS = (
    (0.05, 0.075, 287, 0.489, 628, 638),
    (0.05, 0.100, 86, 0.495, 191, 192),
    (0.01, 0.015, 1501, 0.488, 3295, 3350),
)


def _power(n: int, breach: float, budget: float) -> float:
    return float(revocation_probability(np.array([n]), breach, budget, ALPHA)[0])


def test_critical_counts_are_the_rule_recheck_applies() -> None:
    """The planned test and the executed test must be one test.

    Brute force against `beta.ppf` directly -- the bound `recheck` computes --
    rather than against the binomial-tail shortcut the fast path starts from.
    """
    for budget in (0.01, 0.05, 0.2):
        ns = np.arange(1, 400)
        fast = critical_counts(ns, budget, ALPHA)
        for n, k in zip(ns, fast, strict=True):
            brute = next(
                (j for j in range(1, n + 1) if beta.ppf(ALPHA, j, n - j + 1) > budget),
                n + 1,
            )
            assert k == brute, f"n={n} budget={budget}: {k} != {brute}"


@pytest.mark.parametrize("budget,breach,old,old_power,size,scratch", ROWS)
def test_the_sizes_146_quoted_catch_their_breach_half_the_time(
    budget, breach, old, old_power, size, scratch
) -> None:
    """The defect, pinned by the numbers 183 recorded before the fix."""
    assert negatives_for_detection(breach, budget, ALPHA) == old
    assert _power(old, breach, budget) == pytest.approx(old_power, abs=5e-4)


@pytest.mark.parametrize("budget,breach,old,old_power,size,scratch", ROWS)
def test_c1_power_holds_from_the_quoted_size_and_not_one_below(
    budget, breach, old, old_power, size, scratch
) -> None:
    assert negatives_for_power(breach, budget, ALPHA, POWER) == size
    ns = np.arange(size, size * 12 + 1)
    powers = revocation_probability(ns, breach, budget, ALPHA)
    assert (powers >= POWER).all(), (
        f"power falls below {POWER} at n={ns[powers < POWER][:5]} above the quoted {size}"
    )
    assert _power(size - 1, breach, budget) < POWER, (
        f"{size - 1} negatives already reach {POWER}; {size} overcharges by a sample"
    )


@pytest.mark.parametrize("budget,breach,old,old_power,size,scratch", ROWS)
def test_c2_the_planned_power_is_what_recheck_actually_delivers(
    budget, breach, old, old_power, size, scratch
) -> None:
    """Seeded draws decided by the lower bound `recheck` itself computes."""
    from controlplane.intake.recheck import _lower_bound_at

    reps = 20_000
    rng = np.random.default_rng(183)
    for true_rate, exact in (
        (breach, _power(size, breach, budget)),
        (budget, _power(size, budget, budget)),
    ):
        counts = rng.binomial(size, true_rate, reps)
        # Decide each distinct count once; the decision depends on nothing else.
        revokes = {int(k): _lower_bound_at(size, int(k), ALPHA) > budget for k in np.unique(counts)}
        observed = float(np.mean([revokes[int(k)] for k in counts]))
        se = (exact * (1 - exact) / reps) ** 0.5
        assert abs(observed - exact) <= 3 * se + 1e-9, (
            f"true rate {true_rate}: simulated {observed:.4f}, exact {exact:.4f}"
        )
        if true_rate == budget:
            assert observed <= ALPHA + 3 * (ALPHA * (1 - ALPHA) / reps) ** 0.5


@pytest.mark.parametrize("budget,breach,old,old_power,size,scratch", ROWS)
def test_c3_the_implementation_landed_where_the_preregistration_said(
    budget, breach, old, old_power, size, scratch
) -> None:
    assert abs(size - scratch) / scratch <= 0.05


def test_c4_a_year_of_rechecks_is_bounded_by_alpha_per_recheck() -> None:
    plan = monitoring_plan(
        budget=0.05, breach_rate=0.075, alpha=ALPHA, power=POWER, negative_share=0.9
    )
    assert plan.false_revocation_per_recheck <= ALPHA
    for option, (_name, per_year) in zip(plan.cadences, DEFAULT_CADENCES, strict=True):
        assert option.false_revocation_in_year == pytest.approx(
            false_revocation_in_year(plan.false_revocation_per_recheck, per_year)
        )
        assert option.false_revocation_in_year <= 1 - (1 - ALPHA) ** per_year


def test_more_rechecks_revoke_a_sound_detector_more_often() -> None:
    plan = monitoring_plan(
        budget=0.05, breach_rate=0.075, alpha=ALPHA, power=POWER, negative_share=0.9
    )
    by_count = sorted(plan.cadences, key=lambda option: option.rechecks_per_year)
    chances = [option.false_revocation_in_year for option in by_count]
    assert chances == sorted(chances)
    assert chances[-1] > 0.5, (
        "a weekly programme at the boundary should be likelier than not to revoke "
        "a sound detector at least once in a year; if it is not, 183's arithmetic "
        "has changed and the rendered warning needs rereading"
    )


def test_the_plan_quotes_the_power_it_achieves_and_the_ladder() -> None:
    plan = monitoring_plan(
        budget=0.05, breach_rate=0.075, alpha=ALPHA, power=POWER, negative_share=0.9
    )
    assert plan.negatives_per_recheck == 628
    assert plan.power_at_breach >= POWER
    ladder = dict(plan.sizes_by_power)
    assert ladder[0.8] == 628
    assert ladder[0.5] < ladder[0.8] < ladder[0.9]
    text = render_plan(plan)
    assert "revokes" in text and f"{plan.power_at_breach:.3f}" in text
    assert "misses a real breach as often as it catches one" in text
    assert "false revocation" in text
    assert "power = 0.8" in text, "the declared power must be listed with the other premises"
    payload = plan.to_payload()
    assert payload["power"] == POWER
    assert payload["cadences"][0]["false_revocation_in_year"] is not None


def test_a_power_outside_the_unit_interval_is_refused() -> None:
    for bad in (0.0, 1.0, 1.2):
        with pytest.raises(ValueError, match="power"):
            negatives_for_power(0.075, 0.05, ALPHA, bad)


def test_config_refuses_a_default_power_below_a_coin_flip() -> None:
    import dataclasses

    from controlplane.config import load_config

    validation = load_config(PROJECT_ROOT / "config.yaml").validation
    assert validation.recheck_power == POWER
    with pytest.raises(ConfigError, match="recheck_power"):
        dataclasses.replace(validation, recheck_power=0.4)
    assert isinstance(validation, ValidationConfig)


def test_recheck_says_how_often_this_file_catches_a_real_breach(tmp_path, config) -> None:
    from controlplane.intake import load_scored_items, recheck_items, render_recheck

    rng = np.random.default_rng(3)
    labels = (rng.random(800) < 0.25).astype(int)
    scores = 1 / (1 + np.exp(-(rng.normal(0, 1, 800) + 1.9 * labels)))
    path = tmp_path / "f.csv"
    path.write_text(
        "id,label,score\n"
        + "".join(f"i{i},{l},{s:.6f}\n" for i, (l, s) in enumerate(zip(labels, scores, strict=True))),
        encoding="utf-8",
    )
    result = recheck_items(config, load_scored_items(path), budget=0.05, threshold=0.85)
    n_neg = result.n_negative_now
    assert result.power_against_1_5x_budget == pytest.approx(_power(n_neg, 0.075, 0.05))
    assert result.negatives_for_tighter_floor == 628
    assert result.recheck_power == config.validation.recheck_power
    assert "would be revoked by this file with probability" in render_recheck(result)
    detection = result.to_payload()["detection"]
    assert detection["power_against_1_5x_budget"] == result.power_against_1_5x_budget


def test_recheck_of_a_budget_with_no_1_5x_rate_does_not_raise(tmp_path, config) -> None:
    """1.5 x 0.7 is not a rate. The first version would have raised on it."""
    from controlplane.intake import load_scored_items, recheck_items

    path = tmp_path / "f.csv"
    path.write_text("id,label,score\n" + "".join(
        f"i{i},{i % 2},{(i % 10) / 10:.2f}\n" for i in range(300)
    ), encoding="utf-8")
    result = recheck_items(config, load_scored_items(path), budget=0.7, threshold=0.5)
    assert result.negatives_for_tighter_floor is None
    assert result.power_against_1_5x_budget is None


def test_plan_power_flag_overrides_the_config(tmp_path) -> None:
    outs = {}
    for power in (None, "0.9"):
        out = tmp_path / f"plan-{power}.json"
        args = [sys.executable, str(PROJECT_ROOT / "warrant.py"), "plan", "-b", "0.05",
                "--negative-share", "0.9", "-q", "-o", str(out)]
        if power:
            args += ["--power", power]
        result = subprocess.run(args, capture_output=True, text=True, cwd=str(PROJECT_ROOT),
                                timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        assert result.returncode == 0, result.stderr
        outs[power] = json.loads(out.read_text(encoding="utf-8"))
    assert outs[None]["power"] == POWER and outs[None]["negatives_per_recheck"] == 628
    assert outs["0.9"]["power"] == 0.9 and outs["0.9"]["negatives_per_recheck"] == 858
