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

import numpy as np

from ..config import Config
from ..model import Metric, MetricError, WarrantMetrics, WarrantStatus, to_jsonable
from ..validation.metrics_builder import build_warrant_metrics
from ..validation.warrant_stats import certify_fpr, min_n_for
from .contract import ScoredItems

__all__ = ["CertificationResult", "certify_items"]


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

    @property
    def certified(self) -> bool:
        return self.status is WarrantStatus.VALID

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "budget_fpr": self.budget,
            "alpha": self.alpha,
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
            },
            "certification": {
                "threshold": self.threshold,
                "fpr_upper_bound": self.fpr_upper_bound,
                "false_positives_at_threshold": self.false_positives_at_threshold,
                "min_units_required": self.min_units_required,
                "estimator": (
                    "Clopper-Pearson one-sided upper bound on the negatives; "
                    "the lowest threshold whose bound clears the budget"
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


def certify_items(
    config: Config,
    items: ScoredItems,
    *,
    budget: float,
    alpha: Optional[float] = None,
) -> CertificationResult:
    """Certify ``items``' detector at ``budget``, or refuse with the shortfall.

    Args:
        config: Supplies the bootstrap count, coverage and seed, so a customer's
            intervals are the same object every published number here uses.
        items: The parsed input.
        budget: Target false-positive rate, in (0, 1).
        alpha: Certification level. Defaults to ``1 - config.validation.ci``.

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

    negatives = scores[labels == 0]
    floor = min_n_for(budget, alpha)
    certification = certify_fpr(
        negatives, budget, alpha=alpha, cluster_ids=(
            None if groups is None else groups[labels == 0]
        ),
    )

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
    }

    if not certification.fpr_certified:
        # A refusal, not an error. The evidence was insufficient; the tool did
        # its job. DECISIONS 138.
        return CertificationResult(
            status=WarrantStatus.REFUSED, reason=certification.reason, **common
        )

    threshold = float(certification.threshold)
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
