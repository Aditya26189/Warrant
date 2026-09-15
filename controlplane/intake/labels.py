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
    "RecheckDisputes",
    "RecheckSensitivity",
    "chained_sensitivity",
    "errors_to_revoke",
    "lower_bound",
    "recheck_label_sensitivity",
    "recheck_second_review",
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
    agreement_part, warnings, reviewed = _agreement(labels, second, seed=seed, resamples=resamples, ci=ci)
    common = dict(**agreement_part, alpha=alpha)
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

    pools = _pools(labels, second, scores, reviewed, threshold=threshold, k=k, n=n,
                   alpha=alpha, subject="certificate")
    at_pairs = confidence_after(
        k, n, budget, flagged_clean=pools["d1"], unflagged_positive=pools["d2"])
    at_upper = (
        confidence_after(k, n, budget, flagged_clean=pools["f_upper"],
                         unflagged_positive=pools["u_upper"])
        if pools["f_upper"] is not None and pools["u_upper"] is not None else None
    )
    return SecondReview(
        **common, warnings=warnings + pools["warnings"],
        disputes=Disputes(
            flagged_positives=pools["f_population"],
            reviewed_flagged_positives=pools["f_reviewed"],
            flagged_positives_disputed=pools["d1"],
            unflagged_negatives=pools["u_population"],
            reviewed_unflagged_negatives=pools["u_reviewed"],
            unflagged_negatives_disputed=pools["d2"],
            confidence_if_disputes_are_errors=at_pairs,
            flagged_upper_bound=pools["f_upper"],
            unflagged_upper_bound=pools["u_upper"],
            confidence_at_upper_bounds=at_upper,
            upper_bound_reason=pools["reason"],
        ),
    )


def _agreement(
    labels: np.ndarray, second: Sequence[Optional[int]], *, seed: int, resamples: int, ci: float,
) -> tuple[dict[str, Any], tuple[str, ...], np.ndarray]:
    """Kappa, the 2x2 table and the per-class pair counts, shared by certify and recheck."""
    labels = np.asarray(labels)
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
    part = dict(
        n_pairs=int(reviewed.sum()), pairs_by_label=pairs_by_label, table=table,
        agreement=agreement,
    )
    return part, warnings, reviewed


def _pools(
    labels: np.ndarray,
    second: Sequence[Optional[int]],
    scores: np.ndarray,
    reviewed: np.ndarray,
    *,
    threshold: float,
    k: int,
    n: int,
    alpha: float,
    subject: str,
) -> dict[str, Any]:
    """The two flattering pools at ``threshold``: sizes, reviewed, disputed, and bounds.

    Items only. ``k`` and ``n`` must be the same file's item counts, which is
    checked, so a caller cannot pair these disputes with another unit's bound.
    """
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
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

    reasons: list[str] = []
    warnings: tuple[str, ...] = ()
    f_upper: Optional[int] = None
    if f_population == 0:
        f_upper = 0
    elif f_reviewed == 0:
        reasons.append(
            "no flagged positive was double-labelled, so the error that costs most per "
            "item went unreviewed"
        )
        warnings += (
            f"none of the {f_population} flagged positives was double-labelled: the "
            f"label error that costs this {subject} most per item was not reviewed",
        )
    else:
        f_upper = disputes_upper_bound(d1, f_reviewed, f_population, alpha)
    u_upper: Optional[int] = None
    if u_reviewed == 0:
        reasons.append(
            "no unflagged negative was double-labelled, so the error that realistic "
            "noise makes material on a large file went unreviewed"
        )
        warnings += (
            f"none of the {u_population} unflagged negatives was double-labelled: an "
            f"unflagged negative that is really positive also flatters this {subject}",
        )
    else:
        u_upper = disputes_upper_bound(d2, u_reviewed, u_population, alpha)
    return dict(
        f_population=f_population, u_population=u_population,
        f_reviewed=f_reviewed, u_reviewed=u_reviewed, d1=d1, d2=d2,
        f_upper=f_upper, u_upper=u_upper, warnings=warnings, reason="; ".join(reasons),
    )


# ------------------------------------------------------------------ recheck (198)

def lower_bound(k: int, n: int, alpha: float) -> float:
    """One-sided Clopper-Pearson lower bound for ``k`` of ``n``, the bound a recheck revokes on.

    The same formula as ``intake.recheck._lower_bound_at``, kept here so this
    module does not import the recheck it annotates; a test holds them equal.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if k <= 0:
        return 0.0
    return float(stats.beta.ppf(alpha, k, n - k + 1))


def errors_to_revoke(
    k: int, n: int, budget: float, alpha: float, limit: int, *, kind: str,
) -> Optional[int]:
    """The fewest errors of one kind at which this recheck's counts would revoke.

    Quantity: the smallest ``a`` in ``1..limit`` with ``lower(k+a, n+a) > budget``
    (``kind="flagged_clean"``), or the smallest ``b`` in ``1..limit`` with
    ``lower(k, n-b) > budget`` (``kind="unflagged_positive"``). Propagation: exact;
    every count up to ``limit`` is evaluated, so no monotonicity is assumed.
    ``None`` when none revokes.
    """
    if limit <= 0:
        return None
    e = np.arange(1, limit + 1)
    if kind == FLAGGED_CLEAN:
        lows = stats.beta.ppf(alpha, k + e, n - k + 1)
    elif kind == UNFLAGGED_POSITIVE:
        if limit > n - k:
            raise ValueError(f"only {n - k} unflagged negatives can be relabelled, not {limit}")
        remaining = n - e
        if k <= 0:
            return None
        lows = np.where(remaining >= k, stats.beta.ppf(alpha, k, np.maximum(remaining - k + 1, 1)), 1.0)
    else:
        raise ValueError(f"unknown error kind {kind!r}")
    hit = np.flatnonzero(lows > budget)
    return int(e[hit[0]]) if hit.size else None


_RECHECK_MEANING = (
    "How many labels of each kind would have to be wrong for this file's own bound "
    "test to have revoked. A VALID recheck remains an absence of evidence of breach, "
    "not evidence that the promise holds, whatever the verdict; these counts do not "
    "change that."
)


@dataclasses.dataclass(frozen=True)
class RecheckSensitivity:
    """How many wrong labels would have turned this recheck into a revocation."""

    computed: bool
    reason: str = ""
    unit: str = "items"
    k: Optional[int] = None
    n: Optional[int] = None
    revokes_at_count: Optional[int] = None
    flagged_positives: Optional[int] = None
    flagged_clean_to_revoke: Optional[int] = None
    unflagged_positive_to_revoke: Optional[int] = None

    def to_payload(self) -> dict[str, Any]:
        if not self.computed:
            return {"computed": False, "reason": self.reason}
        return {
            "computed": True,
            "kind": MetricKind.EXACT.value,
            "meaning": _RECHECK_MEANING,
            "direction": _DIRECTION,
            "unit": self.unit,
            "false_positives": self.k,
            "negatives": self.n,
            "revokes_at_false_positives": self.revokes_at_count,
            "flagged_positive_really_clean": {
                f"flagged_positive_{self.unit}": self.flagged_positives,
                "errors_to_revoke": self.flagged_clean_to_revoke,
            },
            "unflagged_negative_really_positive": {
                f"unflagged_negative_{self.unit}": (
                    None if self.n is None or self.k is None else self.n - self.k
                ),
                "errors_to_revoke": self.unflagged_positive_to_revoke,
            },
        }


def recheck_label_sensitivity(
    *,
    bound_holds: Optional[bool],
    grouped: bool,
    single_label: bool,
    k: Optional[int],
    n: int,
    flagged_positives: Optional[int],
    budget: float,
    alpha: float,
) -> RecheckSensitivity:
    """The recheck's label-error counts, or why there are none (``DECISIONS.md`` 198)."""
    if bound_holds is None:
        return RecheckSensitivity(
            computed=False,
            reason="not computed: the file has no negatives, so nothing was tested (DECISIONS 198)",
        )
    if bound_holds is False:
        return RecheckSensitivity(
            computed=False,
            reason=(
                "not computed: the bound has already broken. The errors that flatter it "
                "only deepen a breach, and the ones that would clear a revocation are "
                "never counted -- that count would be a recipe (DECISIONS 198)"
            ),
        )
    if grouped and not single_label:
        return RecheckSensitivity(
            computed=False,
            reason=(
                "not computed: a group holds both labels, so relabelling an item "
                "changes its group's negative size and no corrected count is defined "
                "(DECISIONS 197, 198)"
            ),
        )
    if k is None or flagged_positives is None:
        raise ValueError("a tested recheck carries k and its flagged positives")
    revokes_at = next((c for c in range(1, n + 1) if lower_bound(c, n, alpha) > budget), None)
    return RecheckSensitivity(
        computed=True,
        unit="groups" if grouped else "items",
        k=k, n=n, revokes_at_count=revokes_at,
        flagged_positives=flagged_positives,
        flagged_clean_to_revoke=errors_to_revoke(
            k, n, budget, alpha, flagged_positives, kind=FLAGGED_CLEAN),
        unflagged_positive_to_revoke=errors_to_revoke(
            k, n, budget, alpha, n - k, kind=UNFLAGGED_POSITIVE),
    )


def chained_sensitivity() -> RecheckSensitivity:
    """What a chained recheck carries instead of the counts (198)."""
    return RecheckSensitivity(
        computed=False,
        reason=(
            "not computed on a chained recheck: one file's bound is evidence, the "
            "chain's statistic decides, and what an error does to that statistic "
            "depends on where the unit sits in the chain (DECISIONS 198)"
        ),
    )


@dataclasses.dataclass(frozen=True)
class RecheckDisputes:
    """At the warrant's threshold on the fresh file, the disputes that could hide a breach."""

    flagged_positives: int
    reviewed_flagged_positives: int
    flagged_positives_disputed: int
    unflagged_negatives: int
    reviewed_unflagged_negatives: int
    unflagged_negatives_disputed: int
    lower_bound_if_disputes_are_errors: float
    revokes_if_disputes_are_errors: bool
    flagged_upper_bound: Optional[int]
    unflagged_upper_bound: Optional[int]
    lower_bound_at_upper_bounds: Optional[float]
    revokes_at_upper_bounds: Optional[bool]
    upper_bound_reason: str = ""

    def to_payload(self, alpha: float) -> dict[str, Any]:
        whole: dict[str, Any]
        if self.lower_bound_at_upper_bounds is None:
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
                "assumes": (
                    "the double-labelled items in each pool are a simple random sample "
                    "of that pool; Warrant cannot see how they were chosen"
                ),
                "lower_bound_if_all_are_errors": self.lower_bound_at_upper_bounds,
                "would_revoke": self.revokes_at_upper_bounds,
                "meaning": (
                    "This file's lower bound if the disputes are at those bounds and "
                    "every one is a primary error: a sensitivity at upper confidence "
                    "bounds, not a joint confidence, and it changes no verdict."
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
            "lower_bound_if_every_dispute_is_a_primary_error": (
                self.lower_bound_if_disputes_are_errors
            ),
            "would_revoke_if_every_dispute_is_a_primary_error": (
                self.revokes_if_disputes_are_errors
            ),
            "worst_case_meaning": (
                "Every disagreement among the pairs counted against the primary label: "
                "a worst case over the pairs, not a bound on the truth."
            ),
            "whole_file": whole,
        }


def recheck_second_review(
    labels: np.ndarray,
    second: Sequence[Optional[int]],
    scores: np.ndarray,
    *,
    threshold: float,
    k: Optional[int],
    n: int,
    budget: float,
    alpha: float,
    bound_holds: Optional[bool],
    grouped: bool,
    seed: int,
    resamples: int,
    ci: float,
) -> SecondReview:
    """Kappa on a recheck file, and the disputes that could hide a breach (198).

    Quantity: as :func:`second_review`, with the recheck's decision in place of the
    certificate's confidence: this file's one-sided lower bound with the disputes
    counted as errors, and whether it clears the budget. Propagation: exact
    Clopper-Pearson lower bound; each pool's dispute bound by
    :func:`disputes_upper_bound` at ``alpha``, jointly ``>= 1 - 2 alpha``.
    """
    agreement_part, warnings, reviewed = _agreement(labels, second, seed=seed, resamples=resamples, ci=ci)
    common = dict(**agreement_part, alpha=alpha)
    reason = ""
    if bound_holds is None:
        reason = "not computed: the file has no negatives (DECISIONS 198)"
    elif bound_holds is False:
        reason = "not computed: the bound has already broken (DECISIONS 198)"
    elif grouped:
        reason = (
            "not computed on a grouped file: label_2 is per item, and a dispute inside "
            "a group is not a whole-group relabelling (DECISIONS 197, 198)"
        )
    if reason:
        return SecondReview(**common, warnings=warnings, disputes_reason=reason)
    if k is None:
        raise ValueError("a tested recheck carries k")

    pools = _pools(labels, second, scores, reviewed, threshold=threshold, k=k, n=n,
                   alpha=alpha, subject="recheck")
    low_pairs = lower_bound(k + pools["d1"], n + pools["d1"] - pools["d2"], alpha)
    low_upper: Optional[float] = None
    if pools["f_upper"] is not None and pools["u_upper"] is not None:
        low_upper = lower_bound(k + pools["f_upper"], n + pools["f_upper"] - pools["u_upper"], alpha)
    return SecondReview(
        **common, warnings=warnings + pools["warnings"],
        disputes=RecheckDisputes(
            flagged_positives=pools["f_population"],
            reviewed_flagged_positives=pools["f_reviewed"],
            flagged_positives_disputed=pools["d1"],
            unflagged_negatives=pools["u_population"],
            reviewed_unflagged_negatives=pools["u_reviewed"],
            unflagged_negatives_disputed=pools["d2"],
            lower_bound_if_disputes_are_errors=low_pairs,
            revokes_if_disputes_are_errors=low_pairs > budget,
            flagged_upper_bound=pools["f_upper"],
            unflagged_upper_bound=pools["u_upper"],
            lower_bound_at_upper_bounds=low_upper,
            revokes_at_upper_bounds=None if low_upper is None else low_upper > budget,
            upper_bound_reason=pools["reason"],
        ),
    )
