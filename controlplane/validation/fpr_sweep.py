"""Sweeping the FPR budget: is recall 0.079 a ceiling, or a policy choice?

The shipped operating point warrants recall 0.0794 at a 4.2% flag rate, with
AUROC 0.8256 and precision 0.88. Recall that low reads as a weak detector. But
AUROC 0.826 with precision 0.88 is not the signature of a detector that cannot
separate the classes — it is the signature of one held at a very tight
false-positive budget. Those two readings imply different products, and nothing
in ``results/`` currently distinguishes them.

This module re-analyses **frozen scores**. It runs no inference, fits no probe
and touches no model: every number below is a function of the four arrays in a
``results/scores/*.json`` file, which is the same footing ``make verify``'s
second tier stands on.

**What one grid point is.** For a target FPR ``t``,
:func:`~controlplane.validation.warrant_stats.certify_fpr` picks the lowest
threshold whose Clopper-Pearson upper bound on the negatives clears ``t``, or
refuses when no threshold on this many negatives can. The threshold that comes
back is then scored through
:func:`~controlplane.validation.metrics_builder.build_warrant_metrics` — the
same builder every runner calls, at the config's bootstrap count, coverage and
seed. No bound and no estimator is reimplemented here.

**The selection caveat, stated once and carried into the artifact.** The
threshold at each grid point is chosen on the same 600-item frozen test split
the recall is then measured on. This is weaker than the pipeline's discipline,
where selection happens on validation and test is scored once, and it is a
consequence of what is frozen: only test-split scores were committed, and
re-deriving validation-split scores would mean refitting the probe. The bias is
narrower than "selected on test" usually implies — ``certify_fpr`` reads the
**negatives only**, so the positives that determine recall play no part in
choosing the threshold — but the threshold still tracks this sample's negative
tail rather than the population's, so each point's recall is an in-sample
figure. ``DECISIONS.md`` 124.
"""

from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np

from ..config import Config
from ..model import Metric, MetricError, WarrantMetrics, to_jsonable
from .metrics_builder import build_warrant_metrics
from .scores import ScoreSet
from .warrant_stats import certify_fpr, min_n_for

__all__ = [
    "LIFT_HOLDS_LOWER_BOUND",
    "MEASURED",
    "FprSweep",
    "SweepPoint",
    "fpr_grid",
    "resolve_data_source",
    "sweep_fpr",
]

_LOG = logging.getLogger(__name__)

#: The pre-registered bar for "lift holds" (Phase 0 brief, D6): the lower bound
#: of lift's 95% interval must be **strictly** greater than this. Registered
#: before any sweep output was seen and not adjustable afterwards — a criterion
#: moved after the fact is the exact failure this project exists to prevent.
LIFT_HOLDS_LOWER_BOUND = 1.0

#: The only ``data_source`` whose numbers may be printed as results.
MEASURED = "measured"


def fpr_grid(start: float, stop: float, step: float) -> tuple[float, ...]:
    """Build the target-FPR grid, inclusive of both ends.

    Constructed on integer multiples of ``step`` rather than by accumulating
    floats: ``0.01 + 0.01 + …`` reaches ``0.060000000000000005``, which is not
    the target anybody registered and renders as ``0.06`` while comparing
    unequal to it.

    Args:
        start: First target FPR.
        stop: Last target FPR, included when it lands on the grid.
        step: Spacing.

    Returns:
        Ascending target FPRs.

    Raises:
        ValueError: If the grid is empty or the step is not positive.
    """
    if step <= 0:
        raise ValueError(f"step must be positive; got {step}")
    if stop < start:
        raise ValueError(f"stop {stop} is below start {start}")
    scale = round(1.0 / step)
    if abs(scale * step - 1.0) > 1e-9:
        raise ValueError(
            f"step {step} does not divide 1.0; the grid would not land on the "
            "targets it names"
        )
    first, last = round(start * scale), round(stop * scale)
    grid = tuple(round(i / scale, 10) for i in range(first, last + 1))
    if not grid:
        raise ValueError(f"empty grid from start={start} stop={stop} step={step}")
    return grid


def resolve_data_source(
    artifact: Path, *, eval_set_id: str, envelope_id: str
) -> tuple[str, str]:
    """Read the ``data_source`` of the run a score set reproduces. Fail-closed.

    A score set records the arrays but not whether they came from a language
    model or from the synthetic generator, so the declaration is read from the
    run artifact the score set names as its target. Anything that is not an
    explicit ``measured`` on a block matching this eval set and envelope comes
    back unverified, because the failure mode is a new artifact shape that
    nobody taught this function to read — not one that lies.

    Args:
        artifact: The run artifact named in the score set's target.
        eval_set_id: The score set's eval set, which the block must match.
        envelope_id: The score set's envelope, which the block must match.

    Returns:
        ``(data_source, reason)``. ``reason`` is empty when measured.
    """
    if not artifact.is_file():
        return "unverified", f"{artifact.name} is absent; cannot check data_source"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    # Run artifacts declare at the top level; a transfer artifact carries a
    # source and a target block, each with its own declaration.
    blocks = [payload] + [
        payload[key] for key in ("source", "target") if isinstance(payload.get(key), dict)
    ]
    for block in blocks:
        if (
            block.get("eval_set_id") == eval_set_id
            and block.get("envelope_id") == envelope_id
        ):
            source = block.get("data_source")
            if source == MEASURED:
                return MEASURED, ""
            if source is None:
                return "unverified", (
                    f"{artifact.name} declares no data_source for {eval_set_id}"
                )
            return source, (
                f"{eval_set_id} is declared {source!r}, not measured; its numbers "
                "describe a generator we wrote rather than a language model"
            )
    return "unverified", (
        f"{artifact.name} carries no block for {eval_set_id} at envelope "
        f"{envelope_id}, so its data_source cannot be established"
    )


@dataclasses.dataclass(frozen=True)
class SweepPoint:
    """One target FPR: what it certified, and what that threshold bought.

    A refused point keeps its row. Dropping it would turn "no threshold on this
    many negatives can certify a 1% budget" — a fact about the sample size,
    which is the answer to a question a reader will ask — into a gap in a table
    that reads as an oversight.
    """

    target_fpr: float
    certified: bool
    reason: str
    n_units: int
    min_units_required: int
    threshold: Optional[float] = None
    ucb: Optional[float] = None
    k_false_positives: Optional[int] = None
    achieved_fpr: Optional[float] = None
    recall: Optional[Metric] = None
    precision: Optional[Metric] = None
    flag_rate: Optional[Metric] = None
    lift: Optional[Metric] = None
    lift_ceiling: Optional[float] = None
    lift_fraction_of_ceiling: Optional[float] = None
    lift_holds: Optional[bool] = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "target_fpr": self.target_fpr,
            "certified": self.certified,
            "reason": self.reason,
            "n_units": self.n_units,
            "min_units_required": self.min_units_required,
            "threshold": self.threshold,
            "ucb": self.ucb,
            "k_false_positives": self.k_false_positives,
            "achieved_fpr": self.achieved_fpr,
            "recall": to_jsonable(self.recall) if self.recall else None,
            "precision": to_jsonable(self.precision) if self.precision else None,
            "flag_rate": to_jsonable(self.flag_rate) if self.flag_rate else None,
            "lift": to_jsonable(self.lift) if self.lift else None,
            "lift_ceiling": self.lift_ceiling,
            "lift_fraction_of_ceiling": self.lift_fraction_of_ceiling,
            "lift_holds": self.lift_holds,
        }


@dataclasses.dataclass(frozen=True)
class FprSweep:
    """A whole sweep over one score set, plus the shipped point for reference."""

    score_set_id: str
    detector_id: str
    variant: str
    eval_set_id: str
    envelope_id: str
    data_source: str
    data_source_reason: str
    n: int
    n_positive: int
    n_negative: int
    base_rate: float
    alpha: float
    bootstrap_samples: int
    seed: int
    grid: tuple[float, ...]
    points: tuple[SweepPoint, ...]
    shipped_threshold: float
    shipped_operating_point_id: Optional[str]
    shipped_recall: Optional[Metric]
    shipped_precision: Optional[Metric]
    shipped_flag_rate: Optional[Metric]
    shipped_lift: Optional[Metric]

    @property
    def is_measured(self) -> bool:
        """Whether this sweep's numbers may be printed at all (D9)."""
        return self.data_source == MEASURED

    @property
    def holding_points(self) -> tuple[SweepPoint, ...]:
        """Grid points clearing the pre-registered bar, ascending in target."""
        return tuple(p for p in self.points if p.lift_holds)

    @property
    def headline(self) -> Optional[SweepPoint]:
        """The largest target FPR at which lift holds. The D6 output.

        None when no point on the grid holds, which is a result rather than a
        missing value: it says the probe does not clear the bar anywhere in the
        swept range.
        """
        holding = self.holding_points
        return holding[-1] if holding else None

    @property
    def recall_is_a_dial(self) -> Optional[bool]:
        """Whether loosening the budget moves recall beyond sampling noise.

        The rule, registered before the sweep was run (``DECISIONS.md`` 126):
        recall is a **dial** if recall at the headline point lies strictly above
        the *upper* bound of the shipped operating point's 95% recall interval,
        and a **ceiling** otherwise. Comparing against the interval rather than
        the point estimate is what stops a difference the sample cannot resolve
        from being reported as a gain.

        Returns:
            None when nothing holds or the shipped recall is unavailable, in
            which case there is no comparison to make and inventing one would be
            worse than saying so.
        """
        headline = self.headline
        if headline is None or headline.recall is None:
            return None
        if self.shipped_recall is None or self.shipped_recall.ci_high is None:
            return None
        return bool(headline.recall.value > self.shipped_recall.ci_high)

    def to_payload(self) -> dict[str, Any]:
        headline = self.headline
        return {
            "score_set_id": self.score_set_id,
            "detector_id": self.detector_id,
            "variant": self.variant,
            "eval_set_id": self.eval_set_id,
            "envelope_id": self.envelope_id,
            "data_source": self.data_source,
            "data_source_reason": self.data_source_reason,
            "is_measured": self.is_measured,
            "n": self.n,
            "n_positive": self.n_positive,
            "n_negative": self.n_negative,
            "base_rate": self.base_rate,
            "estimator": {
                "alpha": self.alpha,
                "bootstrap_samples": self.bootstrap_samples,
                "seed": self.seed,
                "certification": "Clopper-Pearson one-sided upper bound via certify_fpr",
                "interval": (
                    "percentile bootstrap over questions; lift inherits recall's "
                    "interval divided by the measured flag rate"
                ),
            },
            "grid_spec": {
                "targets": list(self.grid),
                "n_points": len(self.grid),
            },
            "criterion": {
                "name": "lift_holds",
                "rule": "lift ci_low > 1.0, strictly",
                "lower_bound": LIFT_HOLDS_LOWER_BOUND,
                "registered": "Phase 0 brief D6, before any sweep output was seen",
            },
            "shipped_operating_point": {
                "operating_point_id": self.shipped_operating_point_id,
                "threshold": self.shipped_threshold,
                "recall": to_jsonable(self.shipped_recall) if self.shipped_recall else None,
                "precision": (
                    to_jsonable(self.shipped_precision) if self.shipped_precision else None
                ),
                "flag_rate": (
                    to_jsonable(self.shipped_flag_rate) if self.shipped_flag_rate else None
                ),
                "lift": to_jsonable(self.shipped_lift) if self.shipped_lift else None,
            },
            "headline": {
                "largest_target_fpr_where_lift_holds": (
                    headline.target_fpr if headline else None
                ),
                "recall_there": (
                    headline.recall.value if headline and headline.recall else None
                ),
                "recall_ci_there": (
                    [headline.recall.ci_low, headline.recall.ci_high]
                    if headline and headline.recall
                    else None
                ),
                "n_points_holding": len(self.holding_points),
                "recall_is_a_dial": self.recall_is_a_dial,
            },
            "points": [p.to_payload() for p in self.points],
        }


def _metrics_at(
    config: Config, score_set: ScoreSet, threshold: float
) -> WarrantMetrics:
    """Score one threshold through the builder every runner calls."""
    return build_warrant_metrics(
        config,
        np.asarray(score_set.labels),
        np.asarray(score_set.scores, dtype=float),
        threshold,
        groups=np.asarray(score_set.question_ids),
        is_hard_negative_set=score_set.is_hard_negative_set,
    )


def _lift_of(metrics: WarrantMetrics) -> tuple[Optional[Metric], Optional[float], Optional[float], str]:
    """Lift, its ceiling and its fraction — or why there is none.

    ``WarrantMetrics.lift`` raises when nothing was flagged or recall is
    undefined. Both are real outcomes at a tight budget rather than errors, so
    they are recorded as an absent lift with the reason attached instead of
    ending the sweep.
    """
    try:
        return metrics.lift, metrics.lift_ceiling, metrics.lift_fraction_of_ceiling, ""
    except MetricError as exc:
        return None, metrics.lift_ceiling, None, str(exc)


def sweep_fpr(
    config: Config,
    score_set: ScoreSet,
    *,
    grid: Sequence[float],
    data_source: str,
    data_source_reason: str = "",
    alpha: Optional[float] = None,
) -> FprSweep:
    """Certify a threshold at each target FPR and score what it bought.

    Args:
        config: Supplies the bootstrap count, coverage and seed, so the sweep's
            intervals are the same object every other artifact reports.
        score_set: Frozen labels, scores and question ids. Nothing is re-scored.
        grid: Target FPRs, ascending.
        data_source: ``measured`` or anything else; carried so the renderer can
            refuse to print numbers that describe a generator (D9).
        data_source_reason: Why, when it is not measured.
        alpha: Certification level. Defaults to ``1 - config.validation.ci``, so
            a 95% coverage setting certifies at alpha 0.05 rather than at a
            second number that could drift away from it.

    Returns:
        A :class:`FprSweep`.

    Raises:
        ValueError: If the set has no negatives to certify against, or if items
            share a question — clustered items are not independent and
            ``certify_fpr`` would need cluster ids this function does not build.
    """
    labels = np.asarray(score_set.labels)
    scores = np.asarray(score_set.scores, dtype=float)
    question_ids = np.asarray(score_set.question_ids)
    alpha = (1.0 - config.validation.ci) if alpha is None else alpha

    negatives = scores[labels == 0]
    if negatives.size == 0:
        raise ValueError(
            f"{score_set.score_set_id} has no negatives; an FPR budget cannot be "
            "certified against a set with nothing to be wrong about"
        )
    # Certification here passes no cluster ids, which is only sound while each
    # item is its own question. Asserted rather than assumed: a set with
    # several items per question would be certified as though correlated items
    # were independent, and the bound would be narrower than the data supports.
    if len(set(question_ids.tolist())) != question_ids.size:
        raise ValueError(
            f"{score_set.score_set_id} has repeated question ids, so its items "
            "are not independent. certify_fpr needs cluster ids for this set; "
            "certifying without them would overstate the effective sample size."
        )

    points: list[SweepPoint] = []
    for target in grid:
        certification = certify_fpr(negatives, float(target), alpha=alpha)
        floor = min_n_for(float(target), alpha)
        if not certification.fpr_certified:
            points.append(
                SweepPoint(
                    target_fpr=float(target),
                    certified=False,
                    reason=certification.reason,
                    n_units=certification.n_eff,
                    min_units_required=floor,
                )
            )
            _LOG.info("target FPR %.2f REFUSED: %s", target, certification.reason)
            continue

        threshold = float(certification.threshold)
        metrics = _metrics_at(config, score_set, threshold)
        lift, ceiling, fraction, lift_absent = _lift_of(metrics)
        achieved_fpr = float((negatives >= threshold).mean())
        holds = None if lift is None else bool(lift.ci_low > LIFT_HOLDS_LOWER_BOUND)
        points.append(
            SweepPoint(
                target_fpr=float(target),
                certified=True,
                reason=lift_absent or certification.reason,
                n_units=certification.n_eff,
                min_units_required=floor,
                threshold=threshold,
                ucb=certification.ucb,
                k_false_positives=certification.k,
                achieved_fpr=achieved_fpr,
                recall=metrics.recall,
                precision=metrics.precision,
                flag_rate=metrics.flag_rate,
                lift=lift,
                lift_ceiling=ceiling,
                lift_fraction_of_ceiling=fraction,
                lift_holds=holds,
            )
        )
        _LOG.info(
            "target FPR %.2f -> tau %.6f  ucb %.4f  achieved FPR %.4f  "
            "recall %.4f  precision %.4f  lift %s",
            target, threshold, certification.ucb, achieved_fpr,
            metrics.recall.value if metrics.recall else float("nan"),
            metrics.precision.value if metrics.precision else float("nan"),
            f"{lift.value:.3f} [{lift.ci_low:.3f}, {lift.ci_high:.3f}]" if lift else "n/a",
        )

    shipped_target = score_set.targets[0]
    shipped = _metrics_at(config, score_set, shipped_target.threshold)
    shipped_lift, _, _, _ = _lift_of(shipped)

    return FprSweep(
        score_set_id=score_set.score_set_id,
        detector_id=score_set.detector_id,
        variant=score_set.variant,
        eval_set_id=score_set.eval_set_id,
        envelope_id=score_set.envelope_id,
        data_source=data_source,
        data_source_reason=data_source_reason,
        n=score_set.n,
        n_positive=int((labels == 1).sum()),
        n_negative=int((labels == 0).sum()),
        base_rate=score_set.base_rate,
        alpha=alpha,
        bootstrap_samples=config.validation.bootstrap_samples,
        seed=config.seed,
        grid=tuple(float(t) for t in grid),
        points=tuple(points),
        shipped_threshold=float(shipped_target.threshold),
        shipped_operating_point_id=shipped_target.operating_point_id,
        shipped_recall=shipped.recall,
        shipped_precision=shipped.precision,
        shipped_flag_rate=shipped.flag_rate,
        shipped_lift=shipped_lift,
    )
