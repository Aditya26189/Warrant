"""How far a certificate depends on its labels being right (``DECISIONS.md`` 197).

``certify`` treats the ``label`` column as truth. It picks the **lowest** threshold
whose Clopper-Pearson bound clears the budget, so the next lower cut fails and the
certificate sits at the edge by construction. The error that flatters it is a
clean item labelled positive and flagged: a false positive counted as a true
positive. Its effect is exact arithmetic on the counts, and every VALID
certificate on an ungrouped file carries it.

With ``k`` false positives on ``n`` negative units at budget ``B``, the bound clears
``B`` at level ``alpha`` iff ``P(Bin(n, B) <= k) <= alpha``. With ``e`` such items the
counts are ``(k+e, n+e)`` and the certificate holds only at confidence::

    c(e) = 1 - P(Bin(n+e, B) <= k+e)

which is non-increasing in ``e`` (one more trial adds at most one to the count).

A second reviewer's ``label_2`` is measured beside it: kappa over the pairs, and at
the certified threshold the disputed counts in the directions that flatter the
bound. **Nothing here changes a status, a threshold or a bound.** A disagreement is
not an error, and counting every dispute against the primary label is a worst case
over the pairs, not a bound on the truth.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional, Sequence

import numpy as np
from scipy import stats

from ..model import MetricKind
from ..sampling.agreement import Agreement, cohens_kappa
from ..validation.warrant_stats import cp_upper

__all__ = [
    "CONFIDENCE_LADDER",
    "Disputes",
    "LabelSensitivity",
    "SecondReview",
    "confidence_after",
    "disputes_upper_bound",
    "errors_below",
    "label_sensitivity",
    "second_review",
]

#: The confidence levels a certificate's label-error sensitivity is read against.
#: A presentation ladder, like ``sizing.POWER_LADDER``: it selects nothing.
CONFIDENCE_LADDER: tuple[float, ...] = (0.90, 0.80, 0.50)

_MEANING = (
    "The confidence at which this certificate's budget still clears if that many "
    "flagged positives are really clean items. It is not a probability that the "
    "detector is within budget."
)


def confidence_after(
    k: int, n: int, budget: float, *, flagged_clean: int = 0, unflagged_positive: int = 0,
) -> float:
    """The level the certificate holds at when the labels are corrected.

    Quantity: ``1 - P(Bin(n', B) <= k')`` with ``k' = k + flagged_clean`` and
    ``n' = n + flagged_clean - unflagged_positive``. ``flagged_clean`` flagged
    positives that are really clean each add a false positive and a negative
    unit; ``unflagged_positive`` unflagged negatives that are really positive each
    remove a negative unit. Propagation: exact, through the Clopper-Pearson
    duality -- the one-sided bound at ``(k', n')`` equals ``B`` at exactly this
    level.
    """
    if min(k, n, flagged_clean, unflagged_positive) < 0:
        raise ValueError("counts must be non-negative")
    if unflagged_positive > n - k:
        raise ValueError(
            f"{unflagged_positive} unflagged negatives cannot be relabelled: only "
            f"{n - k} of the {n} negatives are unflagged"
        )
    k_new = k + flagged_clean
    n_new = n + flagged_clean - unflagged_positive
    if n_new == 0:
        return 0.0
    return float(1.0 - stats.binom.cdf(k_new, n_new, budget))


def errors_below(
    k: int, n: int, budget: float, limit: int, levels: Sequence[float] = CONFIDENCE_LADDER,
) -> dict[float, Optional[int]]:
    """The fewest flagged-clean errors that take the confidence below each level.

    ``None`` for a level not reached within ``limit`` errors -- there are only
    ``limit`` flagged positives to be wrong about. Exact; ``c(e)`` is evaluated at
    every ``e`` up to ``limit``, so monotonicity is used only to read the first
    crossing, not to skip any value.
    """
    e = np.arange(0, limit + 1)
    confidence = 1.0 - stats.binom.cdf(k + e, n + e, budget)
    found: dict[float, Optional[int]] = {}
    for level in levels:
        below = np.flatnonzero(confidence < level)
        found[level] = int(e[below[0]]) if below.size else None
    return found


def disputes_upper_bound(disputed: int, reviewed: int, population: int, alpha: float) -> int:
    """An exact upper bound on disputed items in a population, from a reviewed sample.

    Quantity: ``D``, the number of the ``population`` flagged positives a second
    reviewer would dispute, given ``disputed`` of ``reviewed`` sampled without
    replacement. Propagation: the exact hypergeometric bound
    ``max{D : P(X <= disputed | population, D, reviewed) >= alpha}``. Equal to
    ``disputed`` when every item was reviewed. Assumes the reviewed items are a
    simple random sample of the population, which nothing here can check.
    """
    if not 0 <= disputed <= reviewed <= population:
        raise ValueError(
            f"need 0 <= disputed ({disputed}) <= reviewed ({reviewed}) <= "
            f"population ({population})"
        )
    if reviewed == population:
        return disputed
    candidates = np.arange(disputed, population - (reviewed - disputed) + 1)
    cdf = stats.hypergeom.cdf(disputed, population, candidates, reviewed)
    return int(candidates[cdf >= alpha].max())


@dataclasses.dataclass(frozen=True)
class LabelSensitivity:
    """What one wrong label at the certified threshold does to the certificate."""

    computed: bool
    reason: str = ""
    flagged_positives: Optional[int] = None
    confidence_as_labelled: Optional[float] = None
    confidence_if_one_is_clean: Optional[float] = None
    bound_if_one_is_clean: Optional[float] = None
    errors_below: Optional[dict[float, Optional[int]]] = None

    def to_payload(self) -> dict[str, Any]:
        if not self.computed:
            return {"computed": False, "reason": self.reason}
        return {
            "computed": True,
            "kind": MetricKind.EXACT.value,
            "meaning": _MEANING,
            "direction": (
                "A flagged item labelled positive that is really clean. A flagged "
                "negative that is really positive, or an unflagged positive that is "
                "really clean, makes the bound conservative and is never used to "
                "tighten it."
            ),
            "flagged_positives": self.flagged_positives,
            "confidence_as_labelled": self.confidence_as_labelled,
            "confidence_if_one_flagged_positive_is_clean": self.confidence_if_one_is_clean,
            "fpr_upper_bound_if_one_flagged_positive_is_clean": self.bound_if_one_is_clean,
            "flagged_clean_errors_to_fall_below": {
                f"{level:.2f}": count for level, count in (self.errors_below or {}).items()
            },
        }


def label_sensitivity(
    *,
    certified: bool,
    grouped: bool,
    k: Optional[int],
    n: int,
    flagged_positives: Optional[int],
    budget: float,
    alpha: float,
) -> LabelSensitivity:
    """The label-error sensitivity of one certificate, or why there is none.

    Not computed on a refusal: a count of relabellings that would turn a refusal
    into a warrant is a recipe, and refusal has no override (invariant 3). Not
    computed on a grouped file: relabelling one item changes its cluster's size,
    ``certify`` requires equal sizes, so no corrected count is defined.
    """
    if not certified:
        return LabelSensitivity(
            computed=False,
            reason=(
                "not computed on a refusal: how many relabellings would turn it into "
                "a warrant is a recipe, and a refusal has no override (DECISIONS 197)"
            ),
        )
    if grouped:
        return LabelSensitivity(
            computed=False,
            reason=(
                "not computed on a grouped file: relabelling one item changes its "
                "group's size, and certification needs equal-sized groups, so no "
                "corrected count is defined (DECISIONS 197)"
            ),
        )
    if k is None or flagged_positives is None:
        raise ValueError("a certified, ungrouped result carries k and its flagged positives")
    return LabelSensitivity(
        computed=True,
        flagged_positives=flagged_positives,
        confidence_as_labelled=confidence_after(k, n, budget),
        confidence_if_one_is_clean=(
            confidence_after(k, n, budget, flagged_clean=1) if flagged_positives else None
        ),
        bound_if_one_is_clean=cp_upper(k + 1, n + 1, alpha) if flagged_positives else None,
        errors_below=errors_below(k, n, budget, flagged_positives),
    )


@dataclasses.dataclass(frozen=True)
class Disputes:
    """At the certified threshold, the pairs that disagree in the flattering directions."""

    flagged_positives: int
    reviewed_flagged_positives: int
    flagged_positives_disputed: int
    unflagged_negatives_disputed: int
    confidence_if_disputes_are_errors: float
    disputes_upper_bound: Optional[int]
    confidence_at_upper_bound: Optional[float]
    upper_bound_reason: str = ""

    def to_payload(self, alpha: float) -> dict[str, Any]:
        upper: dict[str, Any]
        if self.disputes_upper_bound is None:
            upper = {"computed": False, "reason": self.upper_bound_reason}
        else:
            upper = {
                "computed": True,
                "kind": MetricKind.ESTIMATED.value,
                "flagged_positive_disputes_in_file_at_most": self.disputes_upper_bound,
                "alpha": alpha,
                "n": self.reviewed_flagged_positives,
                "estimator": (
                    "exact hypergeometric upper bound over the flagged positives, "
                    "from the double-labelled ones"
                ),
                "assumes": (
                    "the double-labelled flagged positives are a simple random sample "
                    "of the flagged positives; Warrant cannot see how they were chosen"
                ),
                "confidence_if_that_many_are_errors": self.confidence_at_upper_bound,
            }
        return {
            "kind": MetricKind.EXACT.value,
            "flagged_positives": self.flagged_positives,
            "reviewed_flagged_positives": self.reviewed_flagged_positives,
            "flagged_positives_label_2_calls_clean": self.flagged_positives_disputed,
            "unflagged_negatives_label_2_calls_positive": self.unflagged_negatives_disputed,
            "confidence_if_every_dispute_is_a_primary_error": (
                self.confidence_if_disputes_are_errors
            ),
            "worst_case_meaning": (
                "Every disagreement counted against the primary label: a worst case "
                "over the pairs, not a bound on the truth."
            ),
            "whole_file": upper,
        }


@dataclasses.dataclass(frozen=True)
class SecondReview:
    """A second reviewer's labels, measured beside the certificate."""

    n_pairs: int
    pairs_by_label: dict[int, int]
    table: dict[tuple[int, int], int]
    agreement: Agreement
    warnings: tuple[str, ...]
    alpha: float
    disputes: Optional[Disputes] = None
    disputes_reason: str = ""

    def to_payload(self) -> dict[str, Any]:
        agreement = self.agreement
        return {
            "column": "label_2",
            "changes_the_verdict": False,
            "n_pairs": self.n_pairs,
            "pairs_by_primary_label": {str(y): count for y, count in self.pairs_by_label.items()},
            "table": {
                f"label={y},label_2={z}": count for (y, z), count in self.table.items()
            },
            "kappa": {
                "kind": MetricKind.ESTIMATED.value,
                "value": agreement.kappa,
                "ci_low": agreement.ci_low,
                "ci_high": agreement.ci_high,
                "n": agreement.n_pairs,
                "estimator": "Cohen's kappa, percentile bootstrap over pairs",
                "observed_agreement": agreement.observed_agreement,
                "expected_agreement": agreement.expected_agreement,
                "interpretation": agreement.interpretation,
                "undefined_reason": agreement.undefined_reason,
            },
            "warnings": list(self.warnings),
            "disputes": (
                self.disputes.to_payload(self.alpha) if self.disputes is not None
                else {"computed": False, "reason": self.disputes_reason}
            ),
            "cannot_check": (
                "A disagreement is not an error, and an agreement is not a correct "
                "label: two reviewers who were both wrong, or who both saw the score, "
                "agree and are counted clean. Warrant cannot see whether reviewers "
                "were blind to the score or how the double-labelled items were chosen."
            ),
        }


def second_review(
    labels: np.ndarray,
    second: Sequence[Optional[int]],
    scores: np.ndarray,
    *,
    threshold: Optional[float],
    k: Optional[int],
    n: int,
    budget: float,
    alpha: float,
    certified: bool,
    grouped: bool,
    seed: int,
    resamples: int,
    ci: float,
) -> SecondReview:
    """Kappa over the double-labelled items, and the disputes at the threshold.

    Quantity: Cohen's kappa between ``label`` and ``label_2`` over the items that
    carry both; and, on a certified ungrouped file, the exact disputed counts at
    ``threshold`` with the confidence ``c`` if each is a primary error.
    Propagation: kappa by percentile bootstrap over pairs
    (:func:`controlplane.sampling.agreement.cohens_kappa`); ``c`` exactly, as in
    :func:`confidence_after`; the whole-file dispute bound by
    :func:`disputes_upper_bound` at ``alpha``.
    """
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
    reviewed = np.array([value is not None for value in second], dtype=bool)
    if reviewed.shape != labels.shape:
        raise ValueError("label_2 must have one entry per item")
    if not reviewed.any():
        raise ValueError("no item carries label_2")
    first = labels[reviewed].astype(int)
    other = np.array([value for value in second if value is not None], dtype=int)
    agreement = cohens_kappa(
        first.tolist(), other.tolist(), seed=seed, resamples=resamples, ci=ci,
    )
    pairs_by_label = {y: int((first == y).sum()) for y in (0, 1)}
    table = {(y, z): int(((first == y) & (other == z)).sum()) for y in (0, 1) for z in (0, 1)}
    warnings = tuple(
        f"no item labelled {y} was double-labelled; double-label both classes, or "
        f"disagreement about {'clean items' if y == 0 else 'positives'} goes unmeasured"
        for y in (0, 1) if pairs_by_label[y] == 0
    )
    common = dict(
        n_pairs=int(reviewed.sum()), pairs_by_label=pairs_by_label, table=table,
        agreement=agreement, alpha=alpha,
    )

    if not certified or grouped:
        return SecondReview(
            **common, warnings=warnings,
            disputes_reason=(
                "not computed on a refusal (DECISIONS 197)" if not certified else
                "not computed on a grouped file (DECISIONS 197)"
            ),
        )
    if threshold is None or k is None:
        raise ValueError("a certified result carries its threshold and k")

    second_full = np.array([-1 if value is None else value for value in second], dtype=int)
    flagged = scores >= threshold
    flagged_positive = flagged & (labels == 1)
    population = int(flagged_positive.sum())
    reviewed_fp = int((flagged_positive & reviewed).sum())
    d1 = int((flagged_positive & (second_full == 0)).sum())
    d2 = int((~flagged & (labels == 0) & (second_full == 1)).sum())
    at_pairs = confidence_after(k, n, budget, flagged_clean=d1, unflagged_positive=d2)

    upper: Optional[int] = None
    at_upper: Optional[float] = None
    reason = ""
    if population == 0:
        reason = "nothing labelled positive is flagged, so there is nothing to dispute"
    elif reviewed_fp == 0:
        reason = (
            "no flagged positive was double-labelled, so the direction that flatters "
            "the bound went unreviewed"
        )
        warnings = warnings + (
            f"none of the {population} flagged positives was double-labelled: the "
            "label error that flatters this certificate was not reviewed",
        )
    else:
        upper = disputes_upper_bound(d1, reviewed_fp, population, alpha)
        at_upper = confidence_after(k, n, budget, flagged_clean=upper, unflagged_positive=d2)

    return SecondReview(
        **common, warnings=warnings,
        disputes=Disputes(
            flagged_positives=population,
            reviewed_flagged_positives=reviewed_fp,
            flagged_positives_disputed=d1,
            unflagged_negatives_disputed=d2,
            confidence_if_disputes_are_errors=at_pairs,
            disputes_upper_bound=upper,
            confidence_at_upper_bound=at_upper,
            upper_bound_reason=reason,
        ),
    )
