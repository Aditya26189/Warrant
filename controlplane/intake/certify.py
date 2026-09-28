"""Certify a customer's detector against a false-positive budget, or refuse.

Calls the same :func:`~controlplane.validation.warrant_stats.certify_fpr` and
:func:`~controlplane.validation.metrics_builder.build_warrant_metrics` the
research pipeline calls. There is no simplified variant for the customer path:
a second implementation is how the two drift, and the number a customer gets has
to be the number this project defends.

**Refusal is a result.** Too few independent negatives to bound the requested
budget is not a failure of the tool — it is the tool working, and it carries the
n required and the n observed so the answer to *"what would it take?"* is in the
artifact rather than in someone's head.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional


from ..config import Config
from ..model import Metric, MetricError, WarrantMetrics, WarrantStatus, to_jsonable
from ..validation.metrics_builder import build_warrant_metrics
from ..validation.warrant_stats import Certification, certify_fpr, min_n_for
from .contract import ScoredItems

__all__ = [
    "CertificationResult", "certify_budget", "certify_items", "evidence_sha256",
    "input_sha256",
]


@dataclasses.dataclass(frozen=True)
class CertificationResult:
    """A warrant or a refusal, with everything needed to act on either."""

    status: WarrantStatus
    budget: float
    alpha: float
    reason: str
    source: str
    n: int
    n_positive: int
    n_negative: int
    n_units: int
    #: Independent NEGATIVE units -- what the budget is actually certified
    #: against. Distinct from n_units: the requirement is for clean negatives,
    #: and reporting the item count beside it invites the reader to think a file
    #: of 60 items has 60 units of evidence for a false-positive bound.
    negative_units: int
    base_rate: float
    grouped: bool
    min_units_required: int
    evidence_sha256: str
    threshold: Optional[float] = None
    fpr_upper_bound: Optional[float] = None
    false_positives_at_threshold: Optional[int] = None
    n_flagged: Optional[int] = None
    recall: Optional[Metric] = None
    precision: Optional[Metric] = None
    flag_rate: Optional[Metric] = None
    lift: Optional[Metric] = None
    lift_ceiling: Optional[float] = None
    metrics_absent_reason: str = ""
    #: The score distribution, as bin edges and probabilities. Carried so a later
    #: `warrant recheck` can tell whether the traffic has moved, and stored as a
    #: histogram rather than values so a record living for a year holds nobody's
    #: data.
    score_distribution: Optional[Any] = None
    #: Set when the budget was picked off a frontier (``--from-frontier``,
    #: DECISIONS 195): the frontier record's digest, its grid, and the two levels.
    #: The certificate is at ``row_alpha``; ``alpha`` above is then that level.
    selection: Optional[dict[str, Any]] = None
    #: A frontier record for this same input sat beside it when this warrant was
    #: issued without ``--from-frontier``. Not proof of a pick; a flag for audit.
    frontier_record_present: bool = False
    #: What one wrong label at the threshold does to the certificate, or why that
    #: is not computed (:class:`controlplane.intake.labels.LabelSensitivity`, 197).
    label_sensitivity: Optional[Any] = None
    #: ``label_2`` measured beside the certificate, when the file has the column
    #: (:class:`controlplane.intake.labels.SecondReview`, 197). Changes nothing above.
    second_review: Optional[Any] = None

    @property
    def certified(self) -> bool:
        return self.status is WarrantStatus.VALID

    @property
    def recheck_alpha(self) -> float:
        """The level later tests on fresh labels run at (DECISIONS 195).

        A pick off a frontier is a selection made once, paid for by certifying
        at ``row_alpha``. A recheck, a plan and a chain select nothing, so they
        run at the family level the frontier split.
        """
        return self.selection["family_alpha"] if self.selection else self.alpha

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "budget_fpr": self.budget,
            # Read by recheck, plan and a chain. Deliberately the family level
            # when the budget was picked off a frontier; see `certification.alpha`.
            "alpha": self.recheck_alpha,
            "selection": self.selection,
            "frontier_record_present": self.frontier_record_present,
            "reason": self.reason,
            "input": {
                "source": self.source,
                "n": self.n,
                "n_positive": self.n_positive,
                "n_negative": self.n_negative,
                "independent_units": self.n_units,
                "independent_negative_units": self.negative_units,
                "grouped": self.grouped,
                "base_rate": self.base_rate,
                "evidence_sha256": self.evidence_sha256,
            },
            "certification": {
                # The level this certificate's bound was computed at. Equal to
                # the top-level alpha unless the budget was picked off a
                # frontier, when it is that frontier's row_alpha (195).
                "alpha": self.alpha,
                "alpha_governs": (
                    "this certificate; later rechecks, plans and chains run at the "
                    "top-level alpha"
                ),
                "threshold": self.threshold,
                "fpr_upper_bound": self.fpr_upper_bound,
                "false_positives_at_threshold": self.false_positives_at_threshold,
                "min_units_required": self.min_units_required,
                "estimator": (
                    "Clopper-Pearson one-sided upper bound on the negatives; "
                    "the lowest threshold whose bound clears the budget"
                ),
            },
            "score_distribution": (
                to_jsonable(self.score_distribution)
                if self.score_distribution is not None
                else None
            ),
            "labels": {
                "decision": "DECISIONS.md 197",
                "certified_on": "the label column; label_2 changes no status, threshold or bound",
                "sensitivity": (
                    self.label_sensitivity.to_payload()
                    if self.label_sensitivity is not None else None
                ),
                "second_review": (
                    self.second_review.to_payload() if self.second_review is not None
                    else {"present": False, "note": (
                        "no label_2 column: agreement between reviewers is not measured, "
                        "and the certificate is exact about these labels and silent about "
                        "whether they are right"
                    )}
                ),
            },
            "metrics": {
                "n_flagged": self.n_flagged,
                "recall": to_jsonable(self.recall) if self.recall else None,
                "precision": to_jsonable(self.precision) if self.precision else None,
                "flag_rate": to_jsonable(self.flag_rate) if self.flag_rate else None,
                "lift": to_jsonable(self.lift) if self.lift else None,
                "lift_ceiling": self.lift_ceiling,
                "absent_reason": self.metrics_absent_reason,
            },
        }


def _lift_of(metrics: WarrantMetrics) -> tuple[Optional[Metric], Optional[float], str]:
    """Lift and its ceiling, or why there is none.

    Nothing flagged means lift is ``recall / 0``. That is an absence with a
    reason, not a zero.
    """
    try:
        return metrics.lift, metrics.lift_ceiling, ""
    except MetricError as exc:
        return None, metrics.lift_ceiling, str(exc)


def certify_budget(items: ScoredItems, budget: float, alpha: float) -> Certification:
    """The certification step itself, and the only copy of it.

    ``certify --budget`` and ``certify --frontier`` both call this, so the two
    cannot disagree about a status, a threshold or the unit of inference. They
    did until ``DECISIONS.md`` 190: the frontier dropped the ``group`` column and
    certified grouped files at item level, reporting budgets as certified that
    this function refuses.

    Quantity: the lowest threshold whose one-sided Clopper-Pearson upper bound
    on the false-positive rate clears ``budget``. Propagation: exact binomial
    bound over independent negative units -- items, or equal-sized clusters
    when the file is grouped, a cluster counting as a false positive when any
    member fires (:func:`controlplane.validation.warrant_stats.certify_fpr`).

    Raises:
        ValueError: If the file is grouped with unequal group sizes.
    """
    labels, scores, groups = items.as_arrays()
    # Unequal clusters make the cluster-level bound ANTICONSERVATIVE -- it would
    # promise a tighter FPR than the data supports. Raised rather than silently
    # certified at item level, because item-level certification on grouped data
    # assumes an independence the group column explicitly denies. This is the
    # one shape of input the tool tells you to change rather than judging.
    if groups is not None and not items.equal_group_sizes:
        raise ValueError(
            f"{items.source}: the 'group' column has unequal group sizes, so a "
            "cluster-level false-positive bound would be anticonservative — it "
            "would promise a tighter rate than the data supports. Either make "
            "the groups equal-sized, or drop the column and accept that items "
            "are being treated as independent. See docs/INPUT.md."
        )
    return certify_fpr(
        scores[labels == 0], budget, alpha=alpha,
        cluster_ids=None if groups is None else groups[labels == 0],
    )


def certify_items(
    config: Config,
    items: ScoredItems,
    *,
    budget: float,
    alpha: Optional[float] = None,
    selection: Optional[dict[str, Any]] = None,
) -> CertificationResult:
    """Certify ``items``' detector at ``budget``, or refuse with the shortfall.

    Quantity: the detector's false-positive rate on the supplied negatives,
    bounded above, and the lowest threshold whose bound clears ``budget``.
    Propagation: one-sided Clopper-Pearson upper bound at ``alpha``, the
    same bound :func:`controlplane.validation.warrant_stats.certify_fpr`
    uses, so a customer's certificate and a published warrant mean the
    same thing. Recall at the chosen threshold is reported with a
    percentile bootstrap over items.

    Args:
        config: Supplies the bootstrap count, coverage and seed, so a customer's
            intervals are the same object every published number here uses.
        items: The parsed input.
        budget: Target false-positive rate, in (0, 1).
        alpha: Certification level. Defaults to ``1 - config.validation.ci``.
        selection: When the budget was picked off a frontier, that frontier's
            digest, grid, ``row_alpha`` and ``family_alpha`` (``DECISIONS.md``
            195). ``alpha`` must then be its ``row_alpha``; the record keeps
            ``family_alpha`` for every later test on fresh labels.

    Returns:
        A :class:`CertificationResult`, VALID or REFUSED.

    Raises:
        ValueError: If the budget is out of range, or the file is grouped with
            unequal group sizes — see below.
    """
    if not 0.0 < budget < 1.0:
        raise ValueError(
            f"budget must be a false-positive rate in (0, 1); got {budget}. "
            "0.05 means 'at most 5% of clean items may be flagged'."
        )
    alpha = (1.0 - config.validation.ci) if alpha is None else alpha
    if selection is not None and abs(selection["row_alpha"] - alpha) > 1e-15:
        raise ValueError(
            f"a budget picked off a frontier is certified at its row_alpha "
            f"{selection['row_alpha']:g}, not {alpha:g}"
        )
    labels, scores, groups = items.as_arrays()

    from .recheck import score_distribution

    certification = certify_budget(items, budget, alpha)
    distribution = score_distribution(scores)
    floor = min_n_for(budget, alpha)

    common = {
        "budget": budget,
        "alpha": alpha,
        "source": items.source,
        "n": items.n,
        "n_positive": items.n_positive,
        "n_negative": items.n_negative,
        "n_units": items.n_units,
        "negative_units": certification.n_eff,
        "base_rate": items.base_rate,
        "grouped": groups is not None,
        "min_units_required": floor,
        "evidence_sha256": evidence_sha256(items),
        "score_distribution": distribution,
        "selection": selection,
    }

    from .labels import label_sensitivity, second_review, single_label_groups

    grouped = groups is not None
    certified = bool(certification.fpr_certified)
    threshold = float(certification.threshold) if certified else None
    single_label = not grouped or single_label_groups(labels, groups)
    flagged_positives: Optional[int] = None
    if certified and not grouped:
        flagged_positives = int(((scores >= threshold) & (labels == 1)).sum())
    elif certified and single_label:
        # Whole-group units, as the certificate counts them: a positive group is
        # flagged when any member is (197 review, F4).
        flagged_positives = len({
            g for g, y, s in zip(groups, labels, scores, strict=True)
            if y == 1 and s >= threshold
        })
    # DECISIONS 197: both are computed from the certification above and feed
    # nothing back into it.
    common["label_sensitivity"] = label_sensitivity(
        certified=certified, grouped=grouped, single_label=single_label,
        k=certification.k, n=certification.n_eff,
        flagged_positives=flagged_positives, budget=budget, alpha=alpha,
    )
    if items.second_labels is not None:
        common["second_review"] = second_review(
            labels, items.second_labels, scores,
            threshold=threshold, k=certification.k, n=certification.n_eff,
            budget=budget, alpha=alpha, certified=certified, grouped=grouped,
            groups=groups,
            seed=config.seed, resamples=config.validation.bootstrap_samples,
            ci=config.validation.ci,
        )

    if not certified:
        # A refusal, not an error. The evidence was insufficient; the tool did
        # its job. DECISIONS 138.
        return CertificationResult(
            status=WarrantStatus.REFUSED, reason=certification.reason, **common
        )

    metrics = build_warrant_metrics(
        config, labels, scores, threshold, groups=groups
    )
    lift, ceiling, lift_absent = _lift_of(metrics)
    return CertificationResult(
        status=WarrantStatus.VALID,
        reason=(
            f"certified: FPR <= {budget:.4f} at {int(100 * config.validation.ci)}% "
            f"confidence, upper bound {certification.ucb:.4f} on "
            f"{certification.n_eff} independent negative units"
            if selection is None else
            f"certified: FPR <= {budget:.4f}, upper bound {certification.ucb:.4f} on "
            f"{certification.n_eff} independent negative units, at alpha {alpha:.4g} -- "
            f"this budget was picked off a frontier of {len(selection['grid'])} budgets, "
            f"whose rows hold together at alpha {selection['family_alpha']:g}. Only "
            f"the FPR bound is adjusted: recall and precision are measured on the "
            f"file the budget was picked from and carry that pick's optimism"
        ),
        threshold=threshold,
        fpr_upper_bound=certification.ucb,
        false_positives_at_threshold=certification.k,
        n_flagged=int((scores >= threshold).sum()),
        recall=metrics.recall,
        precision=metrics.precision,
        flag_rate=metrics.flag_rate,
        lift=lift,
        lift_ceiling=ceiling,
        metrics_absent_reason=lift_absent,
        **common,
    )


def input_sha256(items: ScoredItems) -> str:
    """One digest for one scored file, whatever order its rows are in (195).

    The release path's convention (``release/evaluate.py``, ``data_sha256``):
    the canonical digest of the sorted ``(sha256 of item id, label, score)``
    rows, so two commands name one file by one digest. A grouped file -- which
    the release path refuses -- appends each row's group digest.
    """
    from ..release.contract import digest

    labels, scores, groups = items.as_arrays()
    if groups is None:
        rows = sorted(
            (digest({"item_id": i}), int(y), float(s))
            for i, y, s in zip(items.ids, labels, scores, strict=True)
        )
    else:
        rows = sorted(
            (digest({"item_id": i}), int(y), float(s), digest({"group": str(g)}))
            for i, y, s, g in zip(items.ids, labels, scores, groups, strict=True)
        )
    return digest(rows)


def evidence_sha256(items: ScoredItems) -> str:
    """Bind every scored-file field that can affect certification (211).

    The existing frontier digest intentionally excludes ``label_2`` because
    second review changes no frontier row. A certify record also reports second
    review, so its own binding must include that column. Order, source path and
    ignored passthrough columns cannot alter the estimator and are excluded.
    """
    from ..release.contract import digest

    groups = items.groups or (None,) * items.n
    second_labels = items.second_labels or (None,) * items.n
    rows = [
        {
            "item_id_sha256": digest({"item_id": item_id}),
            "label": int(label),
            "score": float(score),
            "group_sha256": digest({"group": group}) if group is not None else None,
            "label_2": second_label,
        }
        for item_id, label, score, group, second_label in zip(
            items.ids, items.labels, items.scores, groups, second_labels, strict=True
        )
    ]
    rows.sort(key=lambda row: row["item_id_sha256"])
    return digest({
        "schema": "certify-effective-rows-v1",
        "has_second_review": items.second_labels is not None,
        "rows": rows,
    })
