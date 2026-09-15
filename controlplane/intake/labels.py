"""How far a certificate depends on its labels being right (``DECISIONS.md`` 197).

``certify`` treats the ``label`` column as truth. It picks the **lowest** threshold
whose Clopper-Pearson bound clears the budget, so the next lower cut fails and the
certificate sits at the edge by construction. Two label errors flatter it:

* **a flagged item labelled positive that is really clean** -- a false positive
  counted as a hit: ``(k, n) -> (k+1, n+1)``;
* **an unflagged item labelled negative that is really positive** -- a clean
  negative that did not fire, which the truth does not have: ``(k, n) -> (k, n-1)``.

The other two errors (a flagged negative that is really positive, an unflagged
positive that is really clean) make the bound conservative and are never used to
tighten it. With ``k`` false positives on ``n`` negative units at budget ``B`` the
bound clears ``B`` at level ``alpha`` iff ``P(Bin(n, B) <= k) <= alpha``, so with
``a`` errors of the first kind and ``b`` of the second the certificate holds only
at confidence::

    c(a, b) = 1 - P(Bin(n+a-b, B) <= k+a)

non-increasing in each (one more trial adds at most one to the count; one fewer
trial cannot raise it). The first costs more per error; the second is the one
realistic noise makes material on a large file, because the unflagged negatives
are the large pool (197 review, F1).

A second reviewer's ``label_2`` is measured beside it: kappa over the pairs, and at
the certified threshold the disputed counts in both flattering directions. **Nothing
here changes a status, a threshold or a bound.** A disagreement is not an error,
and counting every dispute against the primary label is a worst case over the
pairs, not a bound on the truth.
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
    "Ladder",
    "SecondReview",
    "confidence_after",
    "disputes_upper_bound",
    "errors_below",
    "label_sensitivity",
    "second_review",
    "single_label_groups",
]

#: The confidence levels a certificate's label-error sensitivity is read against.
#: A presentation ladder, like ``sizing.POWER_LADDER``: it selects nothing.
CONFIDENCE_LADDER: tuple[float, ...] = (0.90, 0.80, 0.50)

FLAGGED_CLEAN = "flagged_clean"
UNFLAGGED_POSITIVE = "unflagged_positive"

_MEANING = (
    "The confidence at which this certificate's budget still clears if that many "
    "labels are wrong in the named direction. It is not a probability that the "
    "detector is within budget."
)

_DIRECTION = (
    "Two label errors flatter the bound: a flagged item labelled positive that is "
    "really clean (one more false positive and one more negative), and an unflagged "
    "item labelled negative that is really positive (one fewer negative). The other "
    "two -- a flagged negative that is really positive, an unflagged positive that is "
    "really clean -- make the bound conservative and are never used to tighten it. "
    "Errors of both kinds together cost more than either ladder shows alone."
)


def confidence_after(
    k: int, n: int, budget: float, *, flagged_clean: int = 0, unflagged_positive: int = 0,
) -> float:
    """The level the certificate holds at when the labels are corrected.

    Quantity: ``1 - P(Bin(n', B) <= k')`` with ``k' = k + flagged_clean`` and
    ``n' = n + flagged_clean - unflagged_positive``. Propagation: exact, through the
    Clopper-Pearson duality -- the one-sided bound at ``(k', n')`` equals ``B`` at
    exactly this level.
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
    k: int,
    n: int,
    budget: float,
    limit: int,
    *,
    kind: str = FLAGGED_CLEAN,
    levels: Sequence[float] = CONFIDENCE_LADDER,
) -> dict[float, Optional[int]]:
    """The fewest errors of one kind that take the confidence below each level.

    ``None`` for a level not reached within ``limit`` errors -- there are only so
    many flagged positives, or unflagged negatives, to be wrong about. Exact;
    ``c`` is evaluated at every count up to ``limit``, so monotonicity is used only
    to read the first crossing, not to skip any value.
    """
    if kind == FLAGGED_CLEAN:
        e = np.arange(0, limit + 1)
        confidence = 1.0 - stats.binom.cdf(k + e, n + e, budget)
    elif kind == UNFLAGGED_POSITIVE:
        if limit > n - k:
            raise ValueError(f"only {n - k} unflagged negatives can be relabelled, not {limit}")
        e = np.arange(0, limit + 1)
        trials = n - e
        confidence = np.where(trials > 0, 1.0 - stats.binom.cdf(k, np.maximum(trials, 1), budget), 0.0)
    else:
        raise ValueError(f"unknown error kind {kind!r}")
    found: dict[float, Optional[int]] = {}
    for level in levels:
        below = np.flatnonzero(confidence < level)
        found[level] = int(e[below[0]]) if below.size else None
    return found


def disputes_upper_bound(disputed: int, reviewed: int, population: int, alpha: float) -> int:
    """An exact upper bound on disputed items in a population, from a reviewed sample.

    Quantity: ``D``, the number of the ``population`` items a second reviewer would
    dispute, given ``disputed`` of ``reviewed`` sampled without replacement.
    Propagation: the exact hypergeometric bound
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


def single_label_groups(labels: Sequence[int], groups: Sequence[Any]) -> bool:
    """Whether every group carries one label.

    Only then is relabelling a whole group a change of one unit with its size
    unchanged. Certification does not guarantee it: a file whose every group holds
    one positive and one negative has equal negative clusters and certifies (197
    review, F4).
    """
    seen: dict[Any, int] = {}
    for label, group in zip(labels, groups, strict=True):
        if seen.setdefault(group, int(label)) != int(label):
            return False
    return True


@dataclasses.dataclass(frozen=True)
class Ladder:
    """One error kind: the cost of one error, and how many reach each level."""

    limit: int
    confidence_if_one: Optional[float]
    bound_if_one: Optional[float]
    errors_below: dict[float, Optional[int]]

    def to_payload(self, limit_name: str) -> dict[str, Any]:
        return {
            limit_name: self.limit,
            "confidence_if_one": self.confidence_if_one,
            "fpr_upper_bound_if_one": self.bound_if_one,
            "errors_to_fall_below": {
                f"{level:.2f}": count for level, count in self.errors_below.items()
            },
        }


@dataclasses.dataclass(frozen=True)
class LabelSensitivity:
    """What wrong labels at the certified threshold do to the certificate."""

    computed: bool
    reason: str = ""
    unit: str = "items"
    confidence_as_labelled: Optional[float] = None
    flagged_clean: Optional[Ladder] = None
    unflagged_positive: Optional[Ladder] = None

    def to_payload(self) -> dict[str, Any]:
        if not self.computed:
            return {"computed": False, "reason": self.reason}
        payload: dict[str, Any] = {
            "computed": True,
            "kind": MetricKind.EXACT.value,
            "meaning": _MEANING,
            "direction": _DIRECTION,
            "unit": self.unit,
            "confidence_as_labelled": self.confidence_as_labelled,
            "flagged_positive_really_clean": self.flagged_clean.to_payload(
                f"flagged_positive_{self.unit}"
            ),
            "unflagged_negative_really_positive": self.unflagged_positive.to_payload(
                f"unflagged_negative_{self.unit}"
            ),
        }
        if self.unit == "groups":
            payload["unit_note"] = (
                "Every group carries one label, so an error relabels a whole group and "
                "no group changes size. A group is flagged when any member is."
            )
        return payload


def label_sensitivity(
    *,
    certified: bool,
    grouped: bool,
    single_label: bool,
    k: Optional[int],
    n: int,
    flagged_positives: Optional[int],
    budget: float,
    alpha: float,
) -> LabelSensitivity:
    """The label-error sensitivity of one certificate, or why there is none.

    ``n``, ``k`` and ``flagged_positives`` are in the certificate's units: items,
    or whole groups on a grouped file whose groups each carry one label. Not
    computed on a refusal: a count of relabellings that would turn a refusal into a
    warrant is a recipe, and refusal has no override (invariant 3). Not computed on
    a grouped file with a mixed group: relabelling part of a group changes its
    negative cluster's size, certification needs equal sizes, and no corrected
    count is defined.
    """
    if not certified:
        return LabelSensitivity(
            computed=False,
            reason=(
                "not computed on a refusal: how many relabellings would turn it into "
                "a warrant is a recipe, and a refusal has no override (DECISIONS 197)"
            ),
        )
    if grouped and not single_label:
        return LabelSensitivity(
            computed=False,
            reason=(
                "not computed: a group holds both labels, so relabelling an item "
                "changes its group's negative size, certification needs equal sizes, "
                "and no corrected count is defined (DECISIONS 197)"
            ),
        )
    if k is None or flagged_positives is None:
        raise ValueError("a certified result carries k and its flagged positives")
    unflagged = n - k

    def ladder(kind: str, limit: int) -> Ladder:
        if limit == 0:
            return Ladder(limit, None, None, errors_below(k, n, budget, 0, kind=kind))
        if kind == FLAGGED_CLEAN:
            return Ladder(
                limit,
                confidence_after(k, n, budget, flagged_clean=1),
                cp_upper(k + 1, n + 1, alpha),
                errors_below(k, n, budget, limit, kind=kind),
            )
        return Ladder(
            limit,
            confidence_after(k, n, budget, unflagged_positive=1),
            cp_upper(k, n - 1, alpha) if n > 1 else 1.0,
            errors_below(k, n, budget, limit, kind=kind),
        )

    return LabelSensitivity(
        computed=True,
        unit="groups" if grouped else "items",
        confidence_as_labelled=confidence_after(k, n, budget),
        flagged_clean=ladder(FLAGGED_CLEAN, flagged_positives),
        unflagged_positive=ladder(UNFLAGGED_POSITIVE, unflagged),
    )


@dataclasses.dataclass(frozen=True)
class Disputes:
    """At the certified threshold, the pairs that disagree in the flattering directions."""

    flagged_positives: int
    reviewed_flagged_positives: int
    flagged_positives_disputed: int
    unflagged_negatives: int
    reviewed_unflagged_negatives: int
    unflagged_negatives_disputed: int
    confidence_if_disputes_are_errors: float
    flagged_upper_bound: Optional[int]
    unflagged_upper_bound: Optional[int]
    confidence_at_upper_bounds: Optional[float]
    upper_bound_reason: str = ""

    def to_payload(self, alpha: float) -> dict[str, Any]:
        whole: dict[str, Any]
        if self.confidence_at_upper_bounds is None:
            whole = {"computed": False, "reason": self.upper_bound_reason}
        else:
            whole = {
                "computed": True,
                "kind": MetricKind.ESTIMATED.value,
                "flagged_positive_disputes_at_most": self.flagged_upper_bound,
                "flagged_positive_n": self.reviewed_flagged_positives,
                "unflagged_negative_disputes_at_most": self.unflagged_upper_bound,
                "unflagged_negative_n": self.reviewed_unflagged_negatives,
                "alpha_each": alpha,
                "joint_level": (
                    f"each bound holds at 1 - alpha; both hold together at >= "
                    f"{1 - 2 * alpha:.4f}, by the union bound"
                ),
                "estimator": (
                    "exact hypergeometric upper bounds over the flagged positives and "
                    "over the unflagged negatives, each from its double-labelled items"
                ),
                "assumes": (
                    "the double-labelled items in each pool are a simple random sample "
                    "of that pool; Warrant cannot see how they were chosen"
                ),
                "confidence_if_all_are_errors": self.confidence_at_upper_bounds,
                "confidence_meaning": (
                    "The certificate's confidence if the disputes are at those bounds "
                    "and every one is a primary error. A sensitivity evaluated at upper "
                    "confidence bounds: not a joint confidence, and not to be combined "
                    "with the bounds' level into one figure."
                ),
            }
        return {
            "kind": MetricKind.EXACT.value,
            "flagged_positives": self.flagged_positives,
            "reviewed_flagged_positives": self.reviewed_flagged_positives,
            "flagged_positives_label_2_calls_clean": self.flagged_positives_disputed,
            "unflagged_negatives": self.unflagged_negatives,
            "reviewed_unflagged_negatives": self.reviewed_unflagged_negatives,
            "unflagged_negatives_label_2_calls_positive": self.unflagged_negatives_disputed,
            "confidence_if_every_dispute_is_a_primary_error": (
                self.confidence_if_disputes_are_errors
            ),
            "worst_case_meaning": (
                "Every disagreement among the pairs counted against the primary label: "
                "a worst case over the pairs, not a bound on the truth."
            ),
            "whole_file": whole,
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
    carry both; and, on a certified ungrouped file, the exact disputed counts in
    both flattering directions at ``threshold``, with the confidence ``c`` if each
    is a primary error. Propagation: kappa by percentile bootstrap over pairs
    (:func:`controlplane.sampling.agreement.cohens_kappa`); ``c`` exactly, as in
    :func:`confidence_after`; each pool's whole-file dispute bound by
    :func:`disputes_upper_bound` at ``alpha``, the two jointly at ``>= 1 - 2 alpha``.
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
                "not computed on a grouped file: label_2 is per item, and a dispute "
                "inside a group is not a whole-group relabelling (DECISIONS 197)"
            ),
        )
    if threshold is None or k is None:
        raise ValueError("a certified result carries its threshold and k")

    second_full = np.array([-1 if value is None else value for value in second], dtype=int)
    flagged = scores >= threshold
    flagged_positive = flagged & (labels == 1)
    unflagged_negative = ~flagged & (labels == 0)
    f_population = int(flagged_positive.sum())
    u_population = int(unflagged_negative.sum())
    if u_population != n - k:
        raise ValueError(f"{u_population} unflagged negatives against n - k = {n - k}")
    f_reviewed = int((flagged_positive & reviewed).sum())
    u_reviewed = int((unflagged_negative & reviewed).sum())
    d1 = int((flagged_positive & (second_full == 0)).sum())
    d2 = int((unflagged_negative & (second_full == 1)).sum())
    at_pairs = confidence_after(k, n, budget, flagged_clean=d1, unflagged_positive=d2)

    reasons = []
    f_upper: Optional[int] = None
    if f_population == 0:
        f_upper = 0
    elif f_reviewed == 0:
        reasons.append(
            "no flagged positive was double-labelled, so the error that costs most per "
            "item went unreviewed"
        )
        warnings = warnings + (
            f"none of the {f_population} flagged positives was double-labelled: the "
            "label error that costs this certificate most per item was not reviewed",
        )
    else:
        f_upper = disputes_upper_bound(d1, f_reviewed, f_population, alpha)
    u_upper: Optional[int] = None
    if u_reviewed == 0:
        reasons.append(
            "no unflagged negative was double-labelled, so the error that realistic "
            "noise makes material on a large file went unreviewed"
        )
        warnings = warnings + (
            f"none of the {u_population} unflagged negatives was double-labelled: an "
            "unflagged negative that is really positive also flatters this certificate",
        )
    else:
        u_upper = disputes_upper_bound(d2, u_reviewed, u_population, alpha)
    at_upper = (
        confidence_after(k, n, budget, flagged_clean=f_upper, unflagged_positive=u_upper)
        if f_upper is not None and u_upper is not None else None
    )

    return SecondReview(
        **common, warnings=warnings,
        disputes=Disputes(
            flagged_positives=f_population,
            reviewed_flagged_positives=f_reviewed,
            flagged_positives_disputed=d1,
            unflagged_negatives=u_population,
            reviewed_unflagged_negatives=u_reviewed,
            unflagged_negatives_disputed=d2,
            confidence_if_disputes_are_errors=at_pairs,
            flagged_upper_bound=f_upper,
            unflagged_upper_bound=u_upper,
            confidence_at_upper_bounds=at_upper,
            upper_bound_reason="; ".join(reasons),
        ),
    )
