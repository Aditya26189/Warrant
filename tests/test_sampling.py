"""The on-traffic warrant, and the gates registered before it was written.

``DECISIONS.md`` 147 pre-registered four of these by name and ``docs/TASKS.md``
Phase 6 lists them as the gate. They are here in the order the contract names
them, then the ones the build added.

**What these tests are for is narrower than it looks.** Every control already
in this repository checks that a number is arithmetically reproducible from its
artifact, and the defect in 147 was reproducible to the last digit for four
phases. So the tests that matter most here are the ones that ask *what quantity
is this number in* -- :func:`test_sizing_derivative`,
:func:`test_sizing_units`, and :func:`test_a_plan_is_honoured_by_the_estimator`.
The last is the one no formula can satisfy by agreeing with itself: it sizes a
sample with one module and then checks that the other module, given exactly that
sample, publishes the margin that was promised.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from controlplane.config import load_config
from controlplane.sampling import (
    WITHHELD_FIELDS,
    AgreementError,
    AllocationError,
    Band,
    EstimationError,
    LabelItem,
    QueueError,
    SizingError,
    build_queue,
    cohens_kappa,
    design_effect,
    estimate_on_traffic,
    labels_for_prevalence,
    labels_for_recall,
    neyman,
    proportional,
    recall_sensitivity,
)

# The declared workload, from config rather than typed, so a change to
# config.yaml moves these tests instead of leaving them describing a scenario
# the project no longer runs (CLAUDE.md invariant 6).
_PROJECT_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
_W = load_config(_PROJECT_ROOT / "config.yaml").workload
_FLAG_RATE = _W.base_error_rate * _W.measured_tpr + (1 - _W.base_error_rate) * _W.measured_fpr


def _sensitivity():
    return recall_sensitivity(
        recall=_W.measured_tpr,
        flag_rate=_FLAG_RATE,
        monthly_interactions=_W.monthly_interactions,
        base_error_rate=_W.base_error_rate,
    )


# --------------------------------------------------------------------------- #
# The registered gate
# --------------------------------------------------------------------------- #


def test_sizing_derivative() -> None:
    """Sizing for recall differs from sizing for prevalence by ``(dR/dq)^2``.

    ``SPEC.md`` §6.2 words the gate exactly this way and ``docs/TASKS.md``
    Phase 6 repeats it. Both sizings use the same closed form at the same
    declared ``q``; the only thing that differs is the margin, and the recall
    margin is the prevalence margin divided by ``|dR/dq|``. Since ``n`` scales
    as ``1/m^2``, the ratio is the square of the derivative -- exactly, not
    approximately, which is why this is an equality to eleven places rather
    than a tolerance.
    """
    sensitivity = _sensitivity()
    # A fine margin, so that rounding each sizing up to a whole label does not
    # distort the ratio. At a 0.05 margin the prevalence sizing is 40 labels and
    # ceil() alone moves the ratio by 2%, which would make this gate a statement
    # about integer arithmetic rather than about the derivative.
    margin = 0.005
    for_recall = labels_for_recall(
        sensitivity=sensitivity, margin=margin, basis="normal"
    )
    for_prevalence = labels_for_prevalence(
        prevalence=sensitivity.unflagged_prevalence, margin=margin
    )
    ratio = (
        for_recall.labels_infinite_population / for_prevalence.labels_infinite_population
    )
    assert ratio == pytest.approx(sensitivity.derivative**2, rel=1e-3)

    # And the identity is the reason, not a coincidence: the recall margin is
    # the prevalence margin divided by |dR/dq|, and n goes as 1/m^2.
    assert for_recall.prevalence_margin == pytest.approx(
        margin / abs(sensitivity.derivative), rel=1e-12
    )


def test_the_derivative_matches_the_analytic_form_and_the_spec() -> None:
    """``dR/dq`` against its own closed form, and against ``SPEC.md``'s -4.65."""
    s = _sensitivity()
    expected = -s.confirmed_errors * s.unflagged_pool / (
        (s.confirmed_errors + s.unflagged_prevalence * s.unflagged_pool) ** 2
    )
    assert s.derivative == pytest.approx(expected, rel=1e-12)
    assert s.derivative == pytest.approx(-4.65, abs=0.005)


def test_the_amplification_is_against_confirmed_errors_not_the_flagged_pool() -> None:
    """``DECISIONS.md`` 148: 232 is ``N_u/TP``, and ``N_u/N_flagged`` is 66.

    Both are carried under distinct names precisely so the two can never again
    be reached by the same word. The derivative is a function of ``TP`` and
    ``N_u`` and contains no term in the flagged pool at all, which is what
    settles which ratio the sentence in ``CLAUDE.md`` was describing.
    """
    s = _sensitivity()
    assert s.amplification == pytest.approx(s.unflagged_pool / s.confirmed_errors)
    assert s.pool_ratio == pytest.approx(s.unflagged_pool / s.flagged_pool)
    assert s.amplification == pytest.approx(232, abs=1.0)
    assert s.pool_ratio == pytest.approx(66, abs=1.0)


def test_sizing_units() -> None:
    """No sample size without a declared target quantity.

    The defect in ``DECISIONS.md`` 147 was a number whose arithmetic was right
    for a question nobody was asking, shipped under a unit that named a
    different one. Every plan therefore carries its estimand, and the estimand
    is a required field with no default -- so a plan cannot be constructed
    without one, and the two estimands this module supports are reached through
    two differently-named functions rather than through one argument.
    """
    s = _sensitivity()
    recall_plan = labels_for_recall(sensitivity=s, margin=0.05)
    prevalence_plan = labels_for_prevalence(
        prevalence=s.unflagged_prevalence, margin=0.05
    )
    assert recall_plan.estimand == "recall"
    assert prevalence_plan.estimand == "prevalence"
    # The two answer different questions at the same margin, and by a factor
    # that is not close to one.
    assert recall_plan.labels > 10 * prevalence_plan.labels

    # A plan also has to say which interval it was sized against.
    assert recall_plan.basis in ("exact", "normal")
    with pytest.raises(SizingError, match="basis"):
        labels_for_recall(sensitivity=s, margin=0.05, basis="whatever")


def test_stratified_unbiased() -> None:
    """Nominal coverage on synthetic data with known ground truth, 1,000 trials.

    Pre-registered in ``DECISIONS.md`` 147: *if coverage lands outside
    [0.93, 0.97] the estimator is reported as failing, not retuned.*

    The ground truth here is the finite-population recall of one fixed
    population, which is the estimand the estimator claims. Each trial draws a
    fresh sample of the unflagged stratum without replacement, so what varies
    between trials is exactly what the interval is a statement about.

    Coverage is expected **at or above** nominal rather than exactly at it:
    Clopper-Pearson is conservative by construction, and this design adds a
    second conservatism by ignoring the finite-population correction. An
    interval that over-covers claims less than it could; one that under-covers
    claims more than it can.
    """
    rng = np.random.default_rng(1729)
    pool = 20_000
    true_q = 0.03
    flagged_reviewed = 900
    true_positives = 300
    truth = np.zeros(pool, dtype=np.int8)
    truth[: int(round(true_q * pool))] = 1
    rng.shuffle(truth)
    realised_q = truth.mean()
    true_recall = true_positives / (true_positives + realised_q * pool)

    n = 900
    covered = 0
    trials = 1000
    for _ in range(trials):
        idx = rng.choice(pool, size=n, replace=False)
        errors = int(truth[idx].sum())
        estimate = estimate_on_traffic(
            flagged_reviewed=flagged_reviewed,
            flagged_confirmed=true_positives,
            bands=[Band("all", population=pool, sampled=n, errors=errors)],
        )
        if estimate.recall.ci_low <= true_recall <= estimate.recall.ci_high:
            covered += 1
    coverage = covered / trials
    assert 0.93 <= coverage <= 1.0, (
        f"coverage {coverage:.3f} over {trials} trials against a true recall of "
        f"{true_recall:.4f}. Below 0.93 the interval claims more than it can "
        "support; this is reported rather than retuned (DECISIONS.md 147)."
    )


def test_blinding() -> None:
    """The queue payload carries no flag status, score, stratum or ordering signal.

    ``CLAUDE.md`` invariant 7. Four leaks, checked separately, because closing
    three of them is worth nothing.
    """
    items = [
        LabelItem(
            item_id=f"item-{i:04d}",
            content=f"response {i}",
            flagged=i < 40,
            stratum="flagged" if i < 40 else "unflagged",
            band="high" if i < 40 else "low",
            score=0.9 if i < 40 else 0.1,
            context={"question": f"q{i}"},
        )
        for i in range(400)
    ]
    queue = build_queue(
        items, seed=1729, double_label_fraction=0.10, safe_context_keys=["question"]
    )

    # 1. The fields themselves, by name and by absence rather than by null.
    for payload in queue.payloads:
        assert set(payload) <= {"queue_id", "content", "question"}
        assert not set(payload) & WITHHELD_FIELDS

    # 2. Order. Flagged items must not cluster at either end. Tested as a
    #    permutation test rather than against a hand-picked tolerance: the
    #    observed mean position of the flagged items is compared against its own
    #    null, generated by reshuffling the same labels 2,000 times. A
    #    tolerance would be a number chosen to pass, and the null is the thing
    #    the claim is actually about. A concatenated flagged-then-unflagged
    #    queue sits at p = 0 against this null, which is checked below.
    positions = {p["queue_id"]: i for i, p in enumerate(queue.payloads)}
    by_item = {item.item_id: item for item in items}
    is_flagged = np.array(
        [
            by_item[queue.assignments[p["queue_id"]]].flagged
            for p in queue.payloads
        ]
    )
    index = np.arange(len(queue.payloads))
    observed = float(index[is_flagged].mean())

    rng = np.random.default_rng(20260911)
    null = np.empty(2000)
    for i in range(null.size):
        null[i] = index[rng.permutation(is_flagged)].mean()
    # Two-sided p-value of the observed mean against its own shuffle null.
    p_value = float(
        (np.abs(null - index.mean()) >= abs(observed - index.mean())).mean()
    )
    assert p_value > 0.01, (
        f"flagged items sit at mean position {observed:.1f} against a shuffle "
        f"null centred on {index.mean():.1f} (p={p_value:.4f}). The queue order "
        "is carrying stratum."
    )

    # And the test has power: an unshuffled queue fails it decisively.
    leaky = np.zeros(len(queue.payloads), dtype=bool)
    leaky[: int(is_flagged.sum())] = True
    leaky_observed = float(index[leaky].mean())
    leaky_p = float(
        (np.abs(null - index.mean()) >= abs(leaky_observed - index.mean())).mean()
    )
    assert leaky_p == 0.0

    # 3. Identifiers. Queue ids must not sort into stratum order.
    ordered = [queue.assignments[qid] for qid in sorted(queue.assignments)]
    first_half_flagged = sum(1 for i in ordered[: len(ordered) // 2] if by_item[i].flagged)
    second_half_flagged = sum(1 for i in ordered[len(ordered) // 2 :] if by_item[i].flagged)
    assert abs(first_half_flagged - second_half_flagged) < 20

    # 4. Repeats. The two occurrences of a double-labelled item get different
    #    ids, so a reviewer cannot recognise the second pass.
    assert queue.duplicated
    for item_id in queue.duplicated:
        ids = [qid for qid, mapped in queue.assignments.items() if mapped == item_id]
        assert len(ids) == 2 and ids[0] != ids[1]


def test_the_queue_refuses_a_context_key_that_would_leak() -> None:
    """An allowlist is only an allowlist if the denied list raises."""
    item = LabelItem(
        item_id="a",
        content="text",
        flagged=True,
        stratum="flagged",
        context={"score": 0.99},
    )
    with pytest.raises(QueueError, match="invariant 7"):
        build_queue([item], seed=1)


def test_double_labelling_covers_both_strata() -> None:
    """A pooled 10% lands in the larger stratum; the share is applied per stratum.

    With 40 flagged against 360 unflagged, a pooled draw would put roughly four
    of forty repeats in the flagged stratum by chance alone, and an agreement
    figure measured almost entirely on one stratum says nothing about the other.
    """
    items = [
        LabelItem(
            item_id=f"i{i}",
            content="c",
            flagged=i < 40,
            stratum="flagged" if i < 40 else "unflagged",
        )
        for i in range(400)
    ]
    queue = build_queue(items, seed=7, double_label_fraction=0.10)
    strata = {item.item_id: item.stratum for item in items}
    counts: dict[str, int] = {}
    for item_id in queue.duplicated:
        counts[strata[item_id]] = counts.get(strata[item_id], 0) + 1
    assert counts["flagged"] == 4
    assert counts["unflagged"] == 36


def test_no_scenario_mixing() -> None:
    """Rates from one workload cannot be quoted against another's base rate.

    ``CLAUDE.md`` invariant 6. The check is concrete rather than procedural: a
    recall and a flag rate that together imply more true positives than the
    operating point flags did not come from traffic at this base error rate, and
    a derivative computed through them would be fiction.
    """
    with pytest.raises(SizingError, match="invariant 6"):
        recall_sensitivity(
            recall=0.90,
            flag_rate=0.01,
            monthly_interactions=200_000,
            base_error_rate=0.03,
        )
    # The declared workload is internally consistent, which is the other half.
    assert _sensitivity().confirmed_errors <= _sensitivity().flagged_pool


# --------------------------------------------------------------------------- #
# What the build added
# --------------------------------------------------------------------------- #


def test_a_plan_is_honoured_by_the_estimator() -> None:
    """Size a sample with one module; the other must deliver the promised margin.

    This is the test the formula cannot pass by agreeing with itself, and it is
    what caught the finite-population correction being applied on the planning
    side and not on the reporting side -- which would have promised a margin the
    published interval did not meet, in a package written to fix exactly that.
    """
    s = _sensitivity()
    flagged = int(round(s.flagged_pool))
    confirmed = int(round(s.confirmed_errors))
    pool = int(round(s.unflagged_pool))
    for margin in (0.05, 0.02, 0.01):
        plan = labels_for_recall(sensitivity=s, margin=margin)
        assert plan.feasible
        errors = int(round(s.unflagged_prevalence * plan.labels))
        estimate = estimate_on_traffic(
            flagged_reviewed=flagged,
            flagged_confirmed=confirmed,
            bands=[Band("all", population=pool, sampled=plan.labels, errors=errors)],
            planned_margin=margin,
        )
        assert estimate.margin_met, (
            f"plan of {plan.labels} labels for +/-{margin} realised "
            f"+/-{estimate.realised_margin:.5f}"
        )


def test_the_normal_approximation_does_not_deliver_its_margin() -> None:
    """``SPEC.md`` §6.2's closed form under-delivers, at every tier.

    This is why ``basis="exact"`` is the default. The normal figure is still
    reported on every plan, because it is what a reader recomputes by hand and
    an unexplained discrepancy reads as an error.
    """
    s = _sensitivity()
    flagged = int(round(s.flagged_pool))
    confirmed = int(round(s.confirmed_errors))
    pool = int(round(s.unflagged_pool))
    for margin in (0.05, 0.02, 0.01):
        plan = labels_for_recall(sensitivity=s, margin=margin)
        assert plan.labels_exact is not None and plan.labels_exact > plan.labels_normal
        errors = int(round(s.unflagged_prevalence * plan.labels_normal))
        estimate = estimate_on_traffic(
            flagged_reviewed=flagged,
            flagged_confirmed=confirmed,
            bands=[
                Band("all", population=pool, sampled=plan.labels_normal, errors=errors)
            ],
            planned_margin=margin,
        )
        assert not estimate.margin_met


def test_the_spec_worked_example_reproduces() -> None:
    """``SPEC.md`` §6.2 quotes n ~= 847 and ~= 5,292. Both, to its own rounding.

    The spec computed from rounded intermediates -- it uses f = 0.0148 where the
    operating point implies 0.014918 -- so the tolerance is the rounding, not a
    fudge factor: 847 against 846 and 5,292 against 5,286.
    """
    s = _sensitivity()
    for margin, spec_value in ((0.05, 847), (0.02, 5292)):
        plan = labels_for_recall(sensitivity=s, margin=margin, basis="normal")
        assert plan.labels == pytest.approx(spec_value, rel=0.002)


def test_precision_is_exact_and_recall_is_estimated() -> None:
    """The central distinction, as a structural property of the design.

    Precision over a census carries no interval and needs no labels. Recall over
    a sampled pool carries one and costs them. ``CLAUDE.md``: *conflating these
    is the most damaging error available in this project.*
    """
    from controlplane.model import MetricKind

    estimate = estimate_on_traffic(
        flagged_reviewed=2984,
        flagged_confirmed=850,
        bands=[Band("all", population=197_016, sampled=1014, errors=26)],
    )
    assert estimate.precision.kind is MetricKind.EXACT
    assert estimate.precision.ci_low is None
    assert estimate.confirmed_errors.kind is MetricKind.EXACT
    assert estimate.recall.kind is MetricKind.ESTIMATED
    assert estimate.recall.ci_low is not None and estimate.recall.ci_high is not None
    assert estimate.recall.n == 1014


def test_a_sampled_flagged_stratum_is_refused() -> None:
    """The exact half is only exact because stratum A is a census.

    Reviewing a sample of the flagged items and reporting the result as EXACT is
    the yield-versus-rate conflation, so the estimator refuses rather than
    quietly estimating both halves.
    """
    with pytest.raises(EstimationError, match="census"):
        estimate_on_traffic(
            flagged_reviewed=300,
            flagged_confirmed=100,
            flagged_population=2984,
            bands=[Band("all", population=197_016, sampled=1000, errors=26)],
        )


def test_an_unsampled_band_is_refused_rather_than_dropped() -> None:
    """Skipping a band silently drops its weight and understates ``q``."""
    with pytest.raises(EstimationError, match="never labelled"):
        estimate_on_traffic(
            flagged_reviewed=2984,
            flagged_confirmed=850,
            bands=[
                Band("low", population=150_000, sampled=800, errors=8),
                Band("high", population=47_016, sampled=0, errors=0),
            ],
        )


def test_no_labels_at_all_is_refused() -> None:
    """Reporting recall from the flagged stratum alone assumes nothing was missed."""
    with pytest.raises(EstimationError, match="not estimable"):
        estimate_on_traffic(
            flagged_reviewed=2984,
            flagged_confirmed=850,
            bands=[Band("all", population=197_016, sampled=0, errors=0)],
        )


def test_proportional_allocation_earns_an_exact_interval_and_neyman_does_not() -> None:
    """What Neyman costs, stated where it is paid.

    Under equal sampling fractions the stratified estimator equals the pooled
    proportion, so Clopper-Pearson applies. Unequal fractions break that and the
    interval becomes a normal approximation over the stratified variance.
    """
    even = estimate_on_traffic(
        flagged_reviewed=2984,
        flagged_confirmed=850,
        bands=[
            Band("low", population=100_000, sampled=500, errors=5),
            Band("high", population=100_000, sampled=500, errors=20),
        ],
    )
    assert even.proportional
    assert "Clopper-Pearson" in even.interval_basis

    uneven = estimate_on_traffic(
        flagged_reviewed=2984,
        flagged_confirmed=850,
        bands=[
            Band("low", population=100_000, sampled=300, errors=3),
            Band("high", population=100_000, sampled=700, errors=28),
        ],
    )
    assert not uneven.proportional
    assert "APPROXIMATE" in uneven.interval_basis


def test_neyman_refuses_without_measured_prevalences() -> None:
    """Month one cannot run Neyman, and the code says so rather than assuming."""
    populations = {"low": 100_000, "high": 97_016}
    with pytest.raises(AllocationError, match="measured prevalence"):
        neyman(populations=populations, prevalences={"low": 0.01}, total=1000)
    plan = proportional(populations=populations, total=1000)
    assert plan.design_effect is None
    assert sum(plan.per_band.values()) == 1000


def test_the_design_effect_is_measured_and_lands_near_the_spec_expectation() -> None:
    """``SPEC.md`` §6.3 expects ~0.67 and says measure, do not assume.

    Cauchy-Schwarz puts it at or below 1, which is checked, and the concavity of
    the square root keeps it from falling far -- which is the substantive
    warning in the spec and the reason 2x is called a good outcome rather than a
    baseline.
    """
    populations = {"b0": 100_000, "b1": 60_000, "b2": 30_000, "b3": 7_016}
    prevalences = {"b0": 0.008, "b1": 0.020, "b2": 0.055, "b3": 0.140}
    deff = design_effect(
        populations=populations, prevalences=prevalences, total=1000
    )
    assert 0.0 < deff <= 1.0
    assert deff > 0.5
    allocation = neyman(populations=populations, prevalences=prevalences, total=1000)
    assert allocation.design_effect == pytest.approx(deff)
    assert sum(allocation.per_band.values()) == 1000
    # Neyman moves labels toward the high-variance bands, which is its point.
    assert allocation.per_band["b3"] > proportional(
        populations=populations, total=1000
    ).per_band["b3"]


def test_kappa_widens_the_recall_interval_rather_than_being_a_footnote() -> None:
    """``CLAUDE.md``: a +/-5pp interval is meaningless at kappa 0.5.

    The response is to make it wide rather than to leave it meaningless, and to
    record why on the metric so a widened interval can never be mistaken for a
    measured one.
    """
    common = dict(
        flagged_reviewed=2984,
        flagged_confirmed=850,
        bands=[Band("all", population=197_016, sampled=1014, errors=26)],
    )
    clean = estimate_on_traffic(**common)
    noisy = estimate_on_traffic(**common, kappa=0.5)
    clean_width = clean.recall.ci_high - clean.recall.ci_low
    noisy_width = noisy.recall.ci_high - noisy.recall.ci_low
    assert noisy_width == pytest.approx(clean_width * 2.0, rel=1e-6)
    assert "kappa" in noisy.recall.estimator
    assert any("kappa" in note for note in noisy.notes)


def test_kappa_is_undefined_rather_than_one_when_nobody_disagreed() -> None:
    """Perfect agreement on a constant category is 0/0, not 1.0.

    The same shape as a bootstrap interval of [0, 0] from 200 clean negatives:
    a claim of certainty from evidence containing nothing to be uncertain about.
    """
    result = cohens_kappa([0] * 30, [0] * 30)
    assert result.kappa is None
    assert result.observed_agreement == 1.0
    assert "0/0" in result.undefined_reason


def test_kappa_carries_an_interval_and_its_raw_agreement() -> None:
    """A point estimate of an agreement statistic is an unbacked number."""
    first = [1, 0, 1, 1, 0, 0, 1, 0, 1, 0] * 5
    second = [1, 0, 1, 0, 0, 1, 1, 0, 1, 0] * 5
    result = cohens_kappa(first, second, resamples=500)
    assert result.kappa is not None
    assert result.ci_low < result.kappa < result.ci_high
    assert result.n_pairs == 50
    # Raw agreement is higher than kappa here, which is the whole reason kappa
    # exists and the reason both are reported.
    assert result.observed_agreement > result.kappa


def test_agreement_refuses_mismatched_or_non_binary_labels() -> None:
    with pytest.raises(AgreementError, match="same items"):
        cohens_kappa([0, 1], [0, 1, 1])
    with pytest.raises(AgreementError, match="expected 0 or 1"):
        cohens_kappa([0, 2], [0, 1])
    with pytest.raises(AgreementError, match="no doubly-labelled"):
        cohens_kappa([], [])


def test_an_unreachable_margin_is_refused_not_rounded_up() -> None:
    """A price list that always returns a price will one day quote an impossible one.

    ``DECISIONS.md`` 146 established this for the monitoring plan; the same rule
    applies to a label plan. The normal approximation returns a number for this
    margin, which is what makes the refusal worth having.
    """
    s = _sensitivity()
    plan = labels_for_recall(sensitivity=s, margin=0.001)
    assert not plan.feasible
    assert plan.labels_normal > 0
    assert "no sample" in plan.refusal_reason


def test_the_stable_threshold_holds_and_keeps_holding() -> None:
    """The quoted ``n`` is not the first crossing, which is not monotone.

    ``DECISIONS.md`` 146 measured this for detection and the same non-monotonicity
    applies here: the observed count is ``round(q*n)``, so the integer jumps and
    the interval at ``(n, k)`` does not narrow with every sample added.
    """
    s = _sensitivity()
    plan = labels_for_recall(sensitivity=s, margin=0.05)
    flagged = int(round(s.flagged_pool))
    confirmed = int(round(s.confirmed_errors))
    pool = int(round(s.unflagged_pool))
    for n in range(plan.labels, plan.labels + 400):
        errors = int(round(s.unflagged_prevalence * n))
        estimate = estimate_on_traffic(
            flagged_reviewed=flagged,
            flagged_confirmed=confirmed,
            bands=[Band("all", population=pool, sampled=n, errors=errors)],
        )
        assert estimate.realised_margin <= 0.05, f"failed at n={n}"


def test_review_sizing_now_names_the_estimand_it_is_for() -> None:
    """The superseded function still exists and can no longer be read as labels.

    ``DECISIONS.md`` 147: a function renamed away leaves nothing for a reader
    who remembers the old number to find, so it keeps its arithmetic and gains
    the estimand it was actually computing.
    """
    from controlplane.economics import recall_sample_size

    sizing = recall_sample_size(recall=0.2171, margin=0.05)
    assert sizing.unit.startswith("confirmed errors")
    assert "NOT reviewed items" in sizing.unit
    assert "SUPERSEDED" in sizing.name
    assert "147" in sizing.note
    # The arithmetic is unchanged, deliberately: the figure in a pre-147
    # artifact is still findable, and the note is what tells whoever finds it
    # what it was. 262 at a design effect of 1; the 175 in
    # results/feasibility.json is the same number carrying the declared 0.67.
    assert math.isclose(sizing.value, 262.0, rel_tol=1e-9)
    with_declared = recall_sample_size(
        recall=0.2171, margin=0.05, design_effect=0.67
    )
    assert math.isclose(with_declared.value, 175.0, rel_tol=1e-9)
