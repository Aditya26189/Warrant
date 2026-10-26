"""Stage A numerical and adversarial characterization, without runtime changes.

The Decimal oracle inverts a binomial CDF directly; it imports no SciPy oracle.
Finite-population checks concern IID sampling with replacement from the stated
score populations. They are deterministic examples, not a general coverage proof.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from math import comb

import numpy as np
import pytest

from controlplane.config import Config
from controlplane.intake import frontier
from controlplane.intake.certify import certify_budget
from controlplane.intake.contract import ScoredItems, _load_scored_items_bytes
from controlplane.validation.warrant_stats import certify_fpr, cp_upper, min_n_for


def _binomial_cdf(k: int, n: int, p: Decimal) -> Decimal:
    """Sum the finite binomial probabilities, independently of beta quantiles."""
    return sum(
        (Decimal(comb(n, j)) * p**j * (1 - p) ** (n - j)
         for j in range(k + 1)),
        Decimal(0),
    )


def _upper_by_cdf_inversion(k: int, n: int) -> Decimal:
    """Solve P(Binomial(n, p) <= k) = .05 by high-precision bisection."""
    if k == n:
        return Decimal(1)
    with localcontext() as context:
        context.prec = 60
        lower, upper = Decimal(0), Decimal(1)
        for _ in range(160):
            midpoint = (lower + upper) / 2
            if _binomial_cdf(k, n, midpoint) > Decimal("0.05"):
                lower = midpoint
            else:
                upper = midpoint
        return +(lower + upper) / 2


def _max_accepted_k(n: int) -> int:
    """Use the exact-decimal CDF at B=.05 instead of native CP calculations."""
    with localcontext() as context:
        context.prec = 60
        for k in range(n + 1):
            if _binomial_cdf(k, n, Decimal("0.05")) > Decimal("0.05"):
                return k - 1
    raise AssertionError("a budget below one cannot accept all n events")


@pytest.mark.parametrize(
    "budget,n,k,printed,eligible",
    [
        ("0.05", 58, 0, 0.050339338330, False),
        ("0.05", 59, 0, 0.049507609888, True),
        ("0.01", 298, 0, 0.010002432438, False),
        ("0.01", 299, 0, 0.009969146793, True),
        ("0.01", 472, 1, 0.010010788209, False),
        ("0.01", 473, 1, 0.009989707474, True),
        ("0.05", 600, 20, 0.048069909806, True),
        ("0.05", 600, 21, 0.050011443530, False),
    ],
)
def test_cp_vectors_against_independent_binomial_inversion(
    budget: str, n: int, k: int, printed: float, eligible: bool,
) -> None:
    reference = _upper_by_cdf_inversion(k, n)
    native = cp_upper(k, n, 0.05)
    assert float(reference) == pytest.approx(printed, abs=1e-12, rel=0)
    assert native == pytest.approx(float(reference), abs=1e-12, rel=0)
    # Numeric comparison tolerance above is never added to budget eligibility.
    assert (reference <= Decimal(budget)) is eligible
    assert (native <= float(budget)) is eligible


@pytest.mark.parametrize("n,expected", [(100, 1), (300, 8), (600, 20)])
def test_maximum_accepted_count_matches_native_continuous_rank(
    n: int, expected: int,
) -> None:
    assert _max_accepted_k(n) == expected
    scores = np.arange(n, dtype=float)
    result = certify_fpr(scores, target_fpr=0.05, alpha=0.05)
    assert result.fpr_certified and result.k == expected
    assert result.threshold == np.nextafter(scores[n - expected - 1], np.inf)
    assert cp_upper(expected, n) <= 0.05 < cp_upper(expected + 1, n)


def test_budget_equality_passes_but_one_float_below_does_not() -> None:
    scores = np.arange(100, dtype=float)
    boundary = cp_upper(1, 100, 0.05)
    equal = certify_fpr(scores, boundary, alpha=0.05)
    below = certify_fpr(scores, np.nextafter(boundary, -np.inf), alpha=0.05)
    assert equal.k == 1 and equal.ucb == boundary
    assert below.k == 0 and below.ucb < boundary


@pytest.mark.parametrize("n", [1, 600])
def test_log_sample_floor_currently_refuses_an_exact_cp_boundary(n: int) -> None:
    """Rounding in the log/ceil precheck can conservatively refuse eligibility."""
    budget = cp_upper(0, n, 0.05)
    assert cp_upper(0, n, 0.05) <= budget
    assert min_n_for(budget, 0.05) == n + 1
    result = certify_fpr(np.zeros(n), target_fpr=budget, alpha=0.05)
    assert not result.fpr_certified and result.n_eff == n
    assert result.k is None and result.ucb is None


@pytest.mark.parametrize("n", [1, 100, 600])
def test_all_events_has_upper_bound_one(n: int) -> None:
    assert cp_upper(n, n, 0.05) == _upper_by_cdf_inversion(n, n) == 1


def test_zero_trials_has_no_cp_estimate() -> None:
    with pytest.raises(ValueError, match="n must be positive"):
        cp_upper(0, 0)


@pytest.mark.parametrize("scores", [[], [0.5]])
def test_zero_or_one_negative_refuses_without_evaluated_threshold(
    scores: list[float],
) -> None:
    result = certify_fpr(np.asarray(scores), target_fpr=0.05, alpha=0.05)
    assert not result.fpr_certified and result.n_eff == len(scores)
    assert result.threshold is result.ucb is result.k is None


def _uniform_population_bad_pivot_probability(
    levels: int, n: int, rank: int, *, inclusive_pivot: bool,
) -> Fraction:
    """Exact P(FPR > .05) from the pivot CDF and an integer binomial tail.

    The pivot is the ascending, one-indexed ``rank`` order statistic. For the
    shipped successor threshold, firing is strictly above the pivot. The
    inclusive-pivot alternative is only a counterfactual comparator check.
    """
    bad_levels = [
        level for level in range(levels)
        if Fraction(levels - level - int(not inclusive_pivot), levels)
        > Fraction(1, 20)
    ]
    if not bad_levels:
        return Fraction(0)
    below_or_equal = max(bad_levels) + 1
    return Fraction(
        sum(
            comb(n, j) * below_or_equal**j * (levels - below_or_equal) ** (n - j)
            for j in range(rank, n + 1)
        ),
        levels**n,
    )


@pytest.mark.parametrize("levels", [1, 10, 50])
def test_tied_native_cut_and_exact_discrete_population_tail(levels: int) -> None:
    n, accepted_k = 300, 8
    scores = np.resize(np.arange(levels, dtype=float), n)
    pivot = np.sort(scores)[n - accepted_k - 1]
    result = certify_fpr(scores, target_fpr=0.05, alpha=0.05)
    assert result.fpr_certified
    assert result.threshold == np.nextafter(pivot, np.inf)
    assert np.array_equal(scores >= result.threshold, scores > pivot)
    assert result.k == int((scores > pivot).sum()) <= accepted_k
    assert not pivot >= result.threshold
    actual = _uniform_population_bad_pivot_probability(
        levels, n, n - accepted_k, inclusive_pivot=False,
    )
    unshifted_inclusive = _uniform_population_bad_pivot_probability(
        levels, n, n - accepted_k, inclusive_pivot=True,
    )
    assert actual <= Fraction(1, 20)
    assert unshifted_inclusive > Fraction(1, 20)


def test_customer_equality_and_positive_scores_do_not_choose_the_cut(
    config: Config,
) -> None:
    negatives = tuple(float(i) for i in range(100))
    threshold = float(np.nextafter(98.0, np.inf))
    for positive_score in (-1e100, threshold, 1e100):
        items = ScoredItems(
            ids=tuple(f"n{i}" for i in range(100)) + ("p",),
            labels=(0,) * 100 + (1,), scores=negatives + (positive_score,),
            groups=None, passthrough_columns=(), source="stage-a-fixture",
        )
        result = certify_budget(items, budget=0.05, alpha=0.05)
        assert result.threshold == threshold and result.k == 1
        point, = frontier(config, items, grid=(0.05,), alpha=0.05)
        assert point.threshold == threshold
        assert point.true_positives == int(positive_score >= threshold)


def test_returned_adaptive_upper_bound_currently_undercovers_with_ties() -> None:
    """A valid fixed budget does not make the returned adaptive U a 95% bound.

    For this three-atom population, q1=P(S>0) and q2=P(S>1) both lie below B.
    Returned-U noncoverage is {M1<=1} union {M1>=2, M2=0}, where Mj counts
    calibration scores above pivot j-1. Its probability is evaluated directly,
    without simulated draws or treating an adaptively chosen cut as fixed.
    """
    n = 100
    q1, q2 = Decimal("0.04656"), Decimal("0.029514")
    assert _upper_by_cdf_inversion(1, n) < q1 < Decimal("0.05")
    assert _upper_by_cdf_inversion(0, n) < q2 < q1
    assert _max_accepted_k(n) == 1
    cases = [
        ([0.0] * 100, 0.0, 0, q1, True),
        ([0.0] * 99 + [1.0], 0.0, 1, q1, True),
        ([0.0] * 98 + [1.0] * 2, 1.0, 0, q2, True),
        ([0.0] * 98 + [1.0, 2.0], 1.0, 1, q2, False),
        ([0.0] * 98 + [2.0] * 2, 2.0, 0, Decimal(0), False),
    ]
    for scores, pivot, k, population_fpr, noncovered in cases:
        result = certify_fpr(np.asarray(scores), target_fpr=0.05, alpha=0.05)
        assert result.fpr_certified and result.k == k
        assert result.threshold == np.nextafter(pivot, np.inf)
        assert result.ucb == cp_upper(k, n, 0.05)
        assert (population_fpr > Decimal(str(result.ucb))) is noncovered
        assert population_fpr < Decimal("0.05")
    with localcontext() as context:
        context.prec = 60
        noncoverage_probability = n * q2 * (1 - q1) ** (n - 1) + (1 - q2) ** n
    assert float(noncoverage_probability) == pytest.approx(
        0.07630211515886068, abs=1e-15, rel=0,
    )
    assert noncoverage_probability > Decimal("0.05")


def test_equal_negative_clusters_use_their_maxima_not_positive_scores() -> None:
    items = ScoredItems(
        ids=tuple(f"i{i}" for i in range(300)),
        labels=(0, 0, 1) * 100,
        scores=tuple(value for i in range(100) for value in (float(i), -1e6, 1e6)),
        groups=tuple(f"g{i}" for i in range(100) for _ in range(3)),
        passthrough_columns=(), source="stage-a-group-fixture",
    )
    result = certify_budget(items, budget=0.05, alpha=0.05)
    assert result.n_eff == 100 and result.k == 1
    assert result.threshold == np.nextafter(98.0, np.inf)


def test_identical_observations_with_distinct_ids_are_accepted_as_rows() -> None:
    """ID uniqueness cannot establish independent negative observations."""
    raw = (
        "id,label,score\n"
        + "".join(f"n{i},0,0.5\n" for i in range(300)) + "positive,1,0.9\n"
    ).encode("utf-8")
    items = _load_scored_items_bytes(raw, source="distinct-ids.csv")
    result = certify_budget(items, budget=0.05, alpha=0.05)
    assert result.fpr_certified and result.n_eff == 300 and result.k == 0


def test_direct_helper_currently_does_not_reject_nan_scores() -> None:
    """Characterize a lower-level gap; scored-file intake rejects these values."""
    result = certify_fpr(np.full(100, np.nan), target_fpr=0.05, alpha=0.05)
    assert result.fpr_certified and np.isnan(result.threshold) and result.k == 0


def test_largest_finite_pivot_currently_produces_infinite_threshold() -> None:
    """Record successor overflow without changing the native procedure."""
    scores = np.full(100, np.finfo(float).max)
    with pytest.warns(RuntimeWarning, match="overflow encountered in nextafter"):
        result = certify_fpr(scores, target_fpr=0.05, alpha=0.05)
    assert result.fpr_certified and np.isposinf(result.threshold) and result.k == 0
