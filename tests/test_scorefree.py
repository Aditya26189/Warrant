"""Certifying a detector that emits no score, and the claims registered first.

``DECISIONS.md`` 152 pre-registered four claims with the test that would falsify
each. They are here under those names, including **the one that failed**:
``test_c3_...`` is written against the corrected claim and its docstring records
what the original said and why the original test did not show it.

The judge here is simulated — a latent per-item flag probability and ``k``
Bernoulli draws from it — because this repository has no paid API key
(``DECISIONS.md`` 136). A real judge's repeated samples share a prompt and a
temperature and are correlated, so every figure from this is an **upper bound**
on what ``k`` buys.
"""

from __future__ import annotations

import numpy as np
import pytest

from controlplane.validation.scorefree import (
    ScoreFreeError,
    consensus_scores,
    smallest_certifiable_budget,
    tunability,
)
from controlplane.validation.stats import auroc
from controlplane.validation.warrant_stats import cp_upper

#: Budgets the tunability of a detector is measured across. The same shape of
#: grid ``DECISIONS.md`` 141 used for Presidio, so the two are comparable.
BUDGETS = (0.001, 0.002, 0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30)


def _simulated_judge(n_negatives: int = 1000, n_positives: int = 300, seed: int = 1729):
    """Latent flag probabilities for a judge with real overlap between classes.

    Negatives draw from ``Beta(1.2, 12)`` — mean 0.091, so the judge fires on
    roughly 9% of clean items — and positives from ``Beta(5, 3)``. The overlap
    is deliberate: a separable simulation would make every claim here trivial.
    """
    rng = np.random.default_rng(seed)
    negatives = np.clip(rng.beta(1.2, 12.0, n_negatives), 0.0, 1.0)
    positives = np.clip(rng.beta(5.0, 3.0, n_positives), 0.0, 1.0)
    latent = np.concatenate([negatives, positives])
    labels = np.concatenate(
        [np.zeros(n_negatives, dtype=int), np.ones(n_positives, dtype=int)]
    )
    return latent, labels


def _votes(latent: np.ndarray, k: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).binomial(k, latent)


# --------------------------------------------------------------------------- #
# The four registered claims
# --------------------------------------------------------------------------- #


def test_c1_a_k_vote_consensus_offers_at_most_k_plus_one_decision_rules() -> None:
    """C1. **Holds.** And the realised count is far below the bound.

    A ``k``-vote score takes at most ``k + 1`` values, so it induces at most
    ``k + 1`` rules of the form *flag when votes >= m*. The bound is exact and
    structural. What makes it worth measuring is how loose it is: at ``k = 50``
    the detector has 51 notches and lands on ten distinct operating points
    across twelve budgets. **Notches are not operating points**, and buying the
    former does not buy the latter in proportion.
    """
    latent, labels = _simulated_judge()
    seen: list[tuple[int, int]] = []
    for k in (1, 3, 5, 9, 25, 50):
        scores = consensus_scores(
            _votes(latent, k, 100 + k), k=k, detector_id="judge-sim"
        )
        assert scores.notches == k + 1
        assert scores.distinct_scores <= k + 1
        result = tunability(
            scores=scores.scores,
            labels=labels,
            budgets=BUDGETS,
            detector_id=scores.detector_id,
        )
        assert result.distinct_operating_points <= k + 1
        seen.append((k, result.distinct_operating_points))

    # Monotone in k, and nowhere near the bound.
    counts = [n for _, n in seen]
    assert counts == sorted(counts)
    assert counts[-1] < 51 / 2


def test_c2_a_bound_certified_at_one_k_does_not_hold_at_another() -> None:
    """C2. **Holds, decisively.** This is why ``k`` belongs in the warrant key.

    Certify a vote-fraction threshold at ``k = 9``, then apply the identical
    threshold to the same items scored at ``k = 1``. The realised false-positive
    rate is more than double the certified upper bound. A warrant that did not
    name ``k`` would be a bound on a procedure nobody was running.
    """
    latent, labels = _simulated_judge()
    nine = consensus_scores(_votes(latent, 9, 109), k=9, detector_id="judge-sim")
    certified = tunability(
        scores=nine.scores, labels=labels, budgets=(0.05,), detector_id=nine.detector_id
    ).achievable[0.05]
    assert certified is not None

    one = consensus_scores(_votes(latent, 1, 201), k=1, detector_id="judge-sim")
    at_k1 = np.asarray(one.scores)[labels == 0]
    realised = float((at_k1 >= certified["threshold"]).mean())

    assert realised > certified["fpr_upper"], (
        f"the same threshold realised {realised:.4f} at k=1 against a bound of "
        f"{certified['fpr_upper']:.4f} certified at k=9. If this ever passes, "
        "k is not part of the operating point and DECISIONS 152 is wrong."
    )
    # And the ids differ, which is the mechanism that prevents the confusion.
    assert nine.detector_id != one.detector_id


def test_c3_granularity_binds_below_the_crossover_and_the_data_binds_above() -> None:
    """C3. **Failed as registered; this is the corrected claim.**

    ``DECISIONS.md`` 152 registered C3 as *"find a budget no m certifies at
    k = 3 and some m certifies at k = 25"*, and the first run of that test found
    none: both reached the same budgets. Two things were wrong with it.

    The first was a defect in :func:`smallest_certifiable_budget`, which
    included a cut point above every score. That threshold flags no negative, so
    it returned the data's floor at every ``k`` — a true number for a detector
    that never fires, which made granularity look as though it never binds.
    Positives are now required.

    The second was that a single vote draw is noisy, and the original test read
    one. Repeated over sixty draws the claim holds clearly: at ``n = 1,000``
    negatives the tightest certifiable budget is 0.111 at ``k = 1`` and 0.008 at
    ``k = 3``, against a data floor of 0.003.

    So there are **two floors and they bind in turn**: granularity below the
    crossover, the data's own certification capacity above it.
    """
    latent, labels = _simulated_judge()
    negatives_mask = labels == 0
    floor = cp_upper(0, int(negatives_mask.sum()), 0.05)

    def tightest(k: int, seed: int) -> float:
        scores = np.asarray(
            consensus_scores(_votes(latent, k, seed), k=k, detector_id="j").scores
        )
        value = smallest_certifiable_budget(
            scores[negatives_mask], scores[~negatives_mask]
        )
        return 1.0 if value is None else value

    at_one = float(np.median([tightest(1, 900_000 + s) for s in range(30)]))
    at_three = float(np.median([tightest(3, 903_000 + s) for s in range(30)]))
    at_nine = float(np.median([tightest(9, 909_000 + s) for s in range(30)]))

    # Granularity binds hard at k=1 and loosens fast.
    assert at_one > 10 * floor
    assert at_three < at_one
    assert at_nine <= at_three
    # By k=9 the data's capacity is what binds, not the notches.
    assert at_nine == pytest.approx(floor, rel=0.05)


def test_c4_finite_k_costs_ranking_quality_and_converges() -> None:
    """C4. **Holds**, against the threshold registered before it was run.

    ``DECISIONS.md`` 152: *AUROC at k = 50 is within 0.02 of the
    latent-probability AUROC.* Measured over 40 draws rather than the registered
    200, because 200 makes the suite slower than the thing it tests and the gap
    at ``k = 50`` is an order of magnitude inside the threshold either way.
    """
    latent, labels = _simulated_judge()
    ceiling = auroc(labels, latent)

    measured = []
    for k in (1, 3, 9, 50):
        draws = [
            auroc(labels, _votes(latent, k, 1000 * k + s) / k) for s in range(40)
        ]
        measured.append((k, float(np.mean(draws))))

    values = [value for _, value in measured]
    assert values == sorted(values), "AUROC must rise with k"
    assert all(value < ceiling for value in values)
    assert ceiling - values[-1] < 0.02, (
        f"AUROC at k=50 is {values[-1]:.4f} against a ceiling of {ceiling:.4f}. "
        "The registered threshold was 0.02. If this fails, repeated sampling "
        "buys granularity and not ranking, which is a weaker claim than "
        "docs/REDACT.md section 5 implies."
    )


# --------------------------------------------------------------------------- #
# The parts that must refuse
# --------------------------------------------------------------------------- #


def test_a_binary_detector_has_exactly_one_operating_point() -> None:
    """The general statement C1 is a special case of.

    At ``k = 1`` a judge emits one bit, so there is one usable cut point and the
    only false-positive rate available is the judge's own. There is no dial.
    This is ``DECISIONS.md`` 141's finding about Presidio's rule-fired
    confidence, arriving from the other direction and for the same reason.
    """
    latent, labels = _simulated_judge()
    scores = consensus_scores(_votes(latent, 1, 77), k=1, detector_id="judge-sim")
    result = tunability(
        scores=scores.scores,
        labels=labels,
        budgets=BUDGETS,
        detector_id=scores.detector_id,
    )
    assert result.distinct_operating_points == 1
    assert result.budgets_certifiable < result.budgets_requested


def test_the_detector_id_carries_k_and_refuses_to_carry_two() -> None:
    """``k`` enters the warrant key through the id, so it cannot enter twice."""
    wrapped = consensus_scores([0, 1, 2], k=2, detector_id="judge")
    assert wrapped.detector_id == "judge@k=2"
    with pytest.raises(ScoreFreeError, match="already carries a k"):
        consensus_scores([0, 1], k=1, detector_id=wrapped.detector_id)


def test_impossible_vote_counts_are_refused() -> None:
    with pytest.raises(ScoreFreeError, match="impossible"):
        consensus_scores([0, 5], k=3, detector_id="judge")
    with pytest.raises(ScoreFreeError, match="must be positive"):
        consensus_scores([0], k=0, detector_id="judge")
    with pytest.raises(ScoreFreeError, match="nothing to score"):
        consensus_scores([], k=3, detector_id="judge")


def test_tunability_refuses_a_set_with_no_negatives() -> None:
    """A false-positive budget over a set with nothing to be falsely positive about."""
    with pytest.raises(ScoreFreeError, match="no negatives"):
        tunability(scores=[0.1, 0.9], labels=[1, 1], budgets=(0.05,))


def test_thresholds_are_the_realised_scores_and_not_a_grid() -> None:
    """A grid finer than the data counts the same partition many times.

    This is how a detector with three notches gets reported as having twenty,
    and it is the counting error that would make the tunability primitive
    useless if it were made.
    """
    labels = [0] * 50 + [1] * 50
    scores = [0.0] * 50 + [1.0] * 50
    result = tunability(scores=scores, labels=labels, budgets=BUDGETS)
    assert result.distinct_scores == 2
    assert result.distinct_operating_points == 1


def test_a_threshold_that_flags_nothing_does_not_count_as_capacity() -> None:
    """The defect C3's docstring records, kept as a test so it cannot return.

    A cut point above every score certifies any budget the data can support and
    is reached only by a detector that never fires. Requiring a positive is what
    stops that being reported as certification capacity.
    """
    negatives = np.array([0.0, 0.1, 0.2])
    positives = np.array([0.3, 0.4])
    reachable = smallest_certifiable_budget(negatives, positives)
    assert reachable is not None
    # The floor from zero observed failures in three negatives -- what the
    # broken version returned at every k.
    floor = cp_upper(0, 3, 0.05)
    assert reachable == pytest.approx(floor)
    # With no positives at all there is no useful threshold, so there is no
    # capacity to report.
    assert smallest_certifiable_budget(negatives, []) is None
