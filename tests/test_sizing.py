"""The price list. ``DECISIONS.md`` 146.

The tests that matter here are about one number: how many clean negatives a
recheck needs. It is the figure somebody budgets a labelling programme from, so
being 20% out is money, and being *subtly* out is worse than being obviously
out.

The subtle way to be wrong is the reason this file exists. Detection is not
monotone in ``n``. The observed count is ``round(rate * n)``, so the integer
jumps and the Clopper-Pearson bound at ``(n, k)`` does not improve with every
sample added. Quote the first ``n`` that works and you hand someone a number
that fails at several larger ones.
"""

from __future__ import annotations

import math

import pytest

from controlplane.economics.sizing import (
    DEFAULT_CADENCES,
    MAX_NEGATIVES,
    _detects,
    monitoring_plan,
    negatives_for_detection,
    smallest_detectable_at,
    workload_price_list,
)
from controlplane.intake.render import render_plan

ALPHA = 0.05

#: (budget, breach, first crossing, stable threshold). Measured, and the gap
#: between the last two columns is the whole point of the module.
PAIRS = (
    (0.05, 0.075, 234, 287),
    (0.05, 0.100, 66, 86),
    (0.01, 0.015, 1234, 1501),
)


@pytest.mark.parametrize("budget,breach,first,stable", PAIRS)
def test_the_quoted_size_is_the_stable_one_not_the_first_that_works(
    budget: float, breach: float, first: int, stable: int
) -> None:
    """The defect this module was written to avoid, pinned by its own numbers.

    Both columns are real: detection genuinely does hold at ``first``. It then
    stops holding again further up, which is what makes quoting it dangerous
    rather than merely imprecise.
    """
    assert _detects(first, breach, budget, ALPHA), (
        f"the recorded first crossing {first} does not detect {breach} at "
        f"budget {budget}; the table in DECISIONS 146 is wrong"
    )
    assert negatives_for_detection(breach, budget, ALPHA) == stable
    assert stable > first, "a stable threshold below the first crossing is nonsense"


@pytest.mark.parametrize("budget,breach,first,stable", PAIRS)
def test_there_are_sample_sizes_above_the_first_crossing_that_do_not_detect(
    budget: float, breach: float, first: int, stable: int
) -> None:
    """The failure quoting the first crossing would cause, made concrete.

    Without this the previous test could pass on an implementation that simply
    returned a larger number for no reason.
    """
    holes = [
        n for n in range(first, stable) if not _detects(n, breach, budget, ALPHA)
    ]
    assert holes, (
        f"no n between {first} and {stable} fails to detect, so the stable "
        "threshold and the first crossing should have been equal"
    )


@pytest.mark.parametrize("budget,breach,first,stable", PAIRS)
def test_detection_holds_at_every_size_from_the_quoted_one_upward(
    budget: float, breach: float, first: int, stable: int
) -> None:
    """The property being sold: not "it works here" but "it works from here"."""
    failures = [
        n
        for n in range(stable, stable * 3)
        if not _detects(n, breach, budget, ALPHA)
    ]
    assert not failures, (
        f"quoted {stable} negatives, but detection fails at {failures[:8]}"
    )


@pytest.mark.parametrize("budget,breach,first,stable", PAIRS)
def test_the_quoted_size_is_minimal(
    budget: float, breach: float, first: int, stable: int
) -> None:
    """One fewer must not have the same guarantee, or the quote is padded."""
    below = stable - 1
    holds_from_below = all(
        _detects(n, breach, budget, ALPHA) for n in range(below, stable * 3)
    )
    assert not holds_from_below, (
        f"{below} negatives would have done, so {stable} overcharges the user "
        "by a sample"
    )


def test_a_breach_at_or_below_the_budget_is_refused_as_a_question() -> None:
    """No sample establishes that a rate inside the promise breaks it."""
    with pytest.raises(ValueError, match="does not exceed budget"):
        negatives_for_detection(0.05, 0.05, ALPHA)
    with pytest.raises(ValueError, match="does not exceed budget"):
        negatives_for_detection(0.04, 0.05, ALPHA)


def test_an_unresolvable_gap_returns_no_number_rather_than_a_huge_one() -> None:
    """A price list that always quotes a price will quote an impossible one."""
    assert negatives_for_detection(0.0501, 0.05, ALPHA) is None


def test_the_refusal_is_fast_enough_to_be_a_usable_answer() -> None:
    """Saying no must not take longer than saying yes.

    The first implementation climbed to the cap before refusing and took nearly
    fourteen seconds. Asking the top of the range first makes it one call, and
    a tool that hangs for fourteen seconds reads as broken rather than decisive.
    """
    import time

    negatives_for_detection(0.075, 0.05, ALPHA)  # warm the scipy import
    start = time.time()
    assert negatives_for_detection(0.0501, 0.05, ALPHA) is None
    assert time.time() - start < 2.0


def test_the_floor_at_the_quoted_size_is_at_least_the_rate_asked_for() -> None:
    """What the sample actually catches, which integer counts make a little worse.

    Asking to catch 0.075 and being told the sample revokes at 0.0767 is not a
    discrepancy: counts are integers, so the achievable observed rates are a
    lattice and the floor lands on the first lattice point that clears.
    """
    for budget, breach, _first, stable in PAIRS:
        floor = smallest_detectable_at(stable, budget, ALPHA)
        assert floor is not None
        assert floor >= breach - 1e-12
        assert floor < breach * 1.1, (
            f"floor {floor} is far above the requested {breach}, which means "
            "the quoted sample size is larger than the question needed"
        )


# --------------------------------------------------------------------------- #
# The plan
# --------------------------------------------------------------------------- #


def a_plan(**overrides):
    kwargs = dict(
        budget=0.05, breach_rate=0.075, alpha=ALPHA, power=0.80, negative_share=0.85
    )
    kwargs.update(overrides)
    return monitoring_plan(**kwargs)


def test_items_to_label_follow_from_the_negative_share() -> None:
    plan = a_plan(negative_share=0.5)
    assert plan.feasible
    assert plan.items_per_recheck == math.ceil(plan.negatives_per_recheck / 0.5)


def test_a_wrong_negative_share_moves_the_plan_in_proportion() -> None:
    """The claim the renderer makes to the user, checked rather than asserted."""
    optimistic = a_plan(negative_share=0.9)
    realistic = a_plan(negative_share=0.6)
    assert optimistic.negatives_per_recheck == realistic.negatives_per_recheck
    ratio = realistic.items_per_recheck / optimistic.items_per_recheck
    assert 1.4 < ratio < 1.6, (
        "the renderer tells users a 0.9-vs-0.6 error understates labelling by "
        f"about half; the measured ratio is {ratio:.3f}"
    )


def test_a_share_outside_the_unit_interval_is_refused() -> None:
    for bad in (0.0, -0.1, 1.5):
        with pytest.raises(ValueError, match="negative_share"):
            a_plan(negative_share=bad)


def test_no_labelling_rate_means_no_hours_and_no_money_rather_than_zero() -> None:
    """The don't-invent rule, where it is easiest to break.

    Zero hours is a claim that the work is free. ``None`` is the truth: nobody
    said how long a label takes.
    """
    plan = a_plan()
    assert plan.cadences
    for option in plan.cadences:
        assert option.reviewer_hours_per_year is None
        assert option.cost_per_year is None


def test_minutes_without_a_rate_price_the_hours_and_not_the_money() -> None:
    plan = a_plan(minutes_per_label=2.0)
    for option in plan.cadences:
        assert option.reviewer_hours_per_year is not None
        assert option.cost_per_year is None


def test_a_year_of_labels_is_the_cadence_times_one_recheck() -> None:
    plan = a_plan(minutes_per_label=3.0, cost_per_hour=600.0)
    for option, (name, per_year) in zip(plan.cadences, DEFAULT_CADENCES, strict=True):
        assert option.name == name
        assert option.labels_per_year == plan.items_per_recheck * per_year
        assert option.reviewer_hours_per_year == pytest.approx(
            option.labels_per_year * 3.0 / 60.0
        )
        assert option.cost_per_year == pytest.approx(
            option.reviewer_hours_per_year * 600.0
        )


def test_an_infeasible_plan_names_what_would_change_it() -> None:
    """A refusal whose only content is 'no' sends the user nowhere."""
    plan = a_plan(breach_rate=0.0501)
    assert not plan.feasible
    assert plan.negatives_per_recheck is None
    for remedy in ("Widen the breach", "loosen alpha", "lower the power", "tighter budget"):
        assert remedy in plan.refusal_reason
    assert f"{MAX_NEGATIVES:,}" in plan.refusal_reason


def test_the_payload_carries_its_premises_and_says_it_is_not_measured() -> None:
    plan = a_plan(minutes_per_label=1.0, cost_per_hour=100.0)
    payload = plan.to_payload()
    assert payload["declared_inputs"]["negative_share"] == 0.85
    assert payload["declared_inputs"]["minutes_per_label"] == 1.0
    assert "EXACT" in payload["exactness"]
    assert "DECLARED" in payload["exactness"]
    assert len(payload["cadences"]) == len(DEFAULT_CADENCES)


# --------------------------------------------------------------------------- #
# The rendering, where a number becomes a claim
# --------------------------------------------------------------------------- #


def test_the_plan_never_recommends_a_cadence() -> None:
    """The one thing this module refuses to do, enforced on the output.

    A recommendation would be a hardcoded constant wearing the clothes of a
    computed one, printed beside figures that really are computed.
    """
    text = render_plan(a_plan(minutes_per_label=2.0, cost_per_hour=500.0)).lower()
    for word in ("recommend", "we suggest", "should recheck"):
        if word == "recommend":
            # The output says "No cadence is recommended", which is the opposite
            # of recommending one. Any other use of the word is the defect.
            assert text.count("recommend") == 1
            assert "no cadence is recommended" in text
            continue
        assert word not in text


def test_a_refused_plan_renders_in_the_same_shape_as_a_priced_one() -> None:
    """Refusals are results here, as everywhere else in this tool."""
    refused = render_plan(a_plan(breach_rate=0.0501))
    priced = render_plan(a_plan())
    for shared in ("THE PRICE OF KEEPING IT TRUE", "Certified budget"):
        assert shared in refused and shared in priced
    assert "REFUSED" in refused
    assert "REFUSED" not in priced


def test_the_rendered_plan_lists_every_declared_input() -> None:
    """A figure whose premises are off-screen is a figure nobody can check."""
    plan = a_plan(minutes_per_label=2.5, cost_per_hour=750.0)
    text = render_plan(plan)
    for name in plan.declared_inputs:
        assert name in text, f"{name} is used in the arithmetic but not shown"


def test_the_rendered_plan_is_ascii() -> None:
    """cp1252 consoles exist, and a traceback is not a price list.

    The same defect this project already hit once: box-drawing characters in a
    summary that a Windows terminal could not encode.
    """
    text = render_plan(a_plan(minutes_per_label=1.0, cost_per_hour=1.0, currency="INR "))
    text.encode("cp1252")
    assert text.isascii()


# --------------------------------------------------------------------------- #
# The declared workload
# --------------------------------------------------------------------------- #


def _workload() -> dict:
    import yaml
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    return yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))["workload"]


def test_the_workload_price_list_reproduces_the_figures_already_quoted() -> None:
    """The check that makes this module worth having.

    ``CLAUDE.md`` has quoted a 1.48% flag rate and 850 real errors surfaced a
    month since before any of this was computed. Those were hand-derived. If
    the code disagrees with them, one of the two is wrong and it matters which.
    """
    priced = workload_price_list(_workload())
    assert priced["flag_rate"] == pytest.approx(0.0149, abs=5e-4)
    assert priced["volume"]["true_positives"].value == pytest.approx(850, abs=1.0)


def test_the_workload_price_list_refuses_a_block_with_a_field_missing() -> None:
    """A workload with a defaulted volume is not the declared workload."""
    block = _workload()
    del block["monthly_interactions"]
    with pytest.raises(KeyError):
        workload_price_list(block)


def test_every_workload_figure_names_its_measured_and_declared_inputs() -> None:
    priced = workload_price_list(_workload())
    for sizing in priced["volume"].values():
        assert sizing.measured_inputs, f"{sizing.name} claims no measured input"
        assert sizing.declared_inputs, f"{sizing.name} claims no declared input"


def test_the_recheck_hint_and_the_plan_cannot_disagree() -> None:
    """One question, one answer.

    ``recheck`` tells a user how many negatives would have caught a 1.5x
    breach, and ``plan`` sizes the programme that collects them. Two
    implementations of that would drift, and the first one did: it quoted 249
    where 146 quoted 287. Both were later found to catch a true breach about
    half the time (DECISIONS 183); they now agree at a declared power.
    """
    from controlplane.economics.sizing import negatives_for_power
    from controlplane.intake.recheck import negatives_needed_to_detect

    for budget in (0.05, 0.02, 0.01):
        assert negatives_needed_to_detect(budget * 1.5, budget, ALPHA, 0.80) == (
            negatives_for_power(budget * 1.5, budget, ALPHA, 0.80)
        )
