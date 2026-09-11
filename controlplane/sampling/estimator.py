"""The on-traffic warrant: recall estimated on your traffic, not on a benchmark.

This is clause one of the three in ``CLAUDE.md`` -- *"we tell you what your
error rate is on your traffic"* -- and until now it had no implementation.

**The design is two strata and they are not symmetric.**

* **Stratum A, flagged.** Reviewed in full, because an escalated item is
  reviewed anyway. Those reviews are labels the operator already paid for and
  currently discards. A census, so every count over it is **exact** and free.
* **Stratum B, unflagged.** Sampled, because reviewing it all is the cost the
  detector exists to avoid. Everything over it is **estimated** and carries an
  interval.

That asymmetry produces the project's central distinction as a structural fact
rather than as a convention anybody has to remember:

    precision = TP / N_A                       EXACT   -- a census, free
    recall    = TP / (TP + q * N_B)            ESTIMATED -- q costs labels

Precision needs no sampling at all. Recall needs the whole sampling apparatus.
It is the same reason ``CLAUDE.md`` insists the two travel together: they are
not two views of one measurement, they are a free claim and an expensive one.

**The estimand is finite-population.** What is claimed is recall *on the month's
realised traffic*, not on the distribution the traffic was drawn from. That is
what makes ``TP`` exact: conditional on the realised month, the flagged stratum
is enumerated, not sampled. A superpopulation estimand would put an interval on
``TP`` as well and would be answering a question nobody asked -- an operator
wants to know what this month's reviewers missed, not what a hypothetical
replication of this month would have missed.

**The interval is propagated by monotone transformation, not by the delta
method.** ``R = TP/(TP + q*N_B)`` is strictly decreasing in ``q``, so if
``[q_lo, q_hi]`` covers ``q`` with probability at least ``1-alpha``, then
``[g(q_hi), g(q_lo)]`` covers ``R`` with *exactly the same* probability. The
delta method is an approximation that degrades precisely where this project
operates -- small event counts in a large pool -- and it can put a recall bound
above 1 or below 0, which the transformation cannot.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

from ..model import Metric, MetricKind
from ..validation.stats import clopper_pearson

#: Two-sided normal quantile at 95%, matching planning.py.
_Z_95 = 1.959963984540054

__all__ = [
    "Band",
    "EstimationError",
    "OnTrafficEstimate",
    "estimate_on_traffic",
]


class EstimationError(ValueError):
    """An on-traffic estimate was requested that the evidence cannot support."""


@dataclass(frozen=True)
class Band:
    """One score band of the unflagged stratum, and what was labelled in it.

    Bands exist so that labels can be concentrated where the variance is
    (``SPEC.md`` §6.3). With a single band the design is simple random sampling
    of the unflagged pool, which is what month one runs.

    Attributes:
        name: Band identifier, for reporting only.
        population: ``N_h``, unflagged items in this band this month.
        sampled: ``n_h``, items drawn and labelled.
        errors: ``k_h``, of those, confirmed incorrect.
    """

    name: str
    population: int
    sampled: int
    errors: int

    def __post_init__(self) -> None:
        if self.population < 0:
            raise EstimationError(f"{self.name}: population must be non-negative")
        if self.sampled < 0:
            raise EstimationError(f"{self.name}: sampled must be non-negative")
        if self.sampled > self.population:
            raise EstimationError(
                f"{self.name}: sampled {self.sampled} from a population of "
                f"{self.population}. A sample cannot exceed its pool."
            )
        if not 0 <= self.errors <= self.sampled:
            raise EstimationError(
                f"{self.name}: {self.errors} errors in {self.sampled} labelled "
                "items is impossible."
            )

    @property
    def rate(self) -> float:
        """Observed error rate in this band, or 0.0 if nothing was labelled."""
        return self.errors / self.sampled if self.sampled else 0.0

    @property
    def fraction_sampled(self) -> float:
        """``n_h / N_h``, the band's sampling fraction."""
        return self.sampled / self.population if self.population else 0.0


@dataclass(frozen=True)
class OnTrafficEstimate:
    """What this month's traffic says, with the exact half separated from the
    estimated half.

    Attributes:
        recall: ESTIMATED. The claim the labels were bought for.
        precision: EXACT. A census of the flagged stratum, free.
        confirmed_errors: EXACT. ``TP`` -- the yield. *"We surfaced this many
            real errors"*, with no sampling and no interval.
        errors_missed: ESTIMATED. ``q * N_B``, the errors in the pool nobody
            reviewed.
        unflagged_prevalence: ESTIMATED. ``q`` itself, reported because it is
            what was actually measured and everything else is a transform of it.
        labels_spent: Items labelled in the unflagged stratum.
        realised_margin: Half-width actually achieved on recall, against which
            a plan's declared margin can be checked.
        planned_margin: What was planned, when a plan was supplied.
        margin_met: Whether the realised half-width reached the planned one.
        proportional: Whether every band was sampled at the same fraction, which
            decides whether the interval is exact-conservative or approximate.
        interval_basis: Which of the two was used, in words.
        bands: The unflagged strata as supplied.
        notes: Anything a reader must know before quoting these numbers.
    """

    recall: Metric
    precision: Metric
    confirmed_errors: Metric
    errors_missed: Metric
    unflagged_prevalence: Metric
    labels_spent: int
    realised_margin: float
    planned_margin: Optional[float]
    margin_met: Optional[bool]
    proportional: bool
    interval_basis: str
    bands: tuple[Band, ...] = ()
    notes: tuple[str, ...] = ()

    def render(self) -> str:
        """The estimate, with EXACT and ESTIMATED visibly separated."""
        lines = [
            "EXACT      (census of the flagged stratum, no sampling, free)",
            f"    confirmed errors surfaced : {self.confirmed_errors.value:,.0f}",
            f"    precision                 : {self.precision.value:.4f} "
            f"(n={self.precision.n:,})",
            "",
            f"ESTIMATED  ({self.labels_spent:,} labels from the unflagged pool)",
            f"    recall                    : {self.recall.value:.4f} "
            f"[{self.recall.ci_low:.4f}, {self.recall.ci_high:.4f}] "
            f"(95% CI, n={self.recall.n:,})",
            f"    unflagged prevalence q    : {self.unflagged_prevalence.value:.5f} "
            f"[{self.unflagged_prevalence.ci_low:.5f}, "
            f"{self.unflagged_prevalence.ci_high:.5f}]",
            f"    errors missed             : {self.errors_missed.value:,.0f} "
            f"[{self.errors_missed.ci_low:,.0f}, {self.errors_missed.ci_high:,.0f}]",
            "",
            f"    interval basis            : {self.interval_basis}",
            f"    realised recall margin    : +/-{self.realised_margin:.4f}",
        ]
        if self.planned_margin is not None:
            verdict = "MET" if self.margin_met else "NOT MET"
            lines.append(
                f"    planned                   : +/-{self.planned_margin:.4f} "
                f"-- {verdict}"
            )
        for note in self.notes:
            lines.append(f"    note: {note}")
        return "\n".join(lines)


def _stratified_prevalence(
    bands: Sequence[Band], ci: float
) -> tuple[float, float, float, bool, str]:
    """Estimate ``q`` over the unflagged strata and bound it.

    Returns ``(q_hat, q_lo, q_hi, proportional, basis)``.

    Two regimes, and which one applies is decided by the data rather than
    declared:

    * **Every band sampled at the same fraction** (proportional allocation, what
      month one runs). The stratified estimator
      ``q_hat = sum_h W_h * k_h/n_h`` collapses *algebraically* to the pooled
      proportion ``K/n``: substituting ``n_h = n*W_h`` gives
      ``sum_h W_h * k_h/(n*W_h) = K/n``. Clopper-Pearson on ``(K, n)`` is
      therefore a valid interval for it, and a **conservative** one, because
      stratification cannot raise the variance of the proportional estimator
      above the simple-random-sampling variance the binomial charges for. Exact
      coverage in the direction that is safe to be wrong in.

    * **Unequal fractions** (Neyman allocation). The collapse does not hold and
      no exact interval is available, so the estimate carries the standard
      stratified variance with a finite-population correction per band and a
      normal interval over it. **Neyman buys precision by giving up
      exactness**, and that trade is stated rather than hidden.
    """
    population = sum(b.population for b in bands)
    sampled = sum(b.sampled for b in bands)
    errors = sum(b.errors for b in bands)
    if population <= 0:
        raise EstimationError("the unflagged pool is empty; there is nothing to sample")
    if sampled <= 0:
        raise EstimationError(
            "no labels were drawn from the unflagged pool. Recall on traffic is "
            "not estimable without them, and reporting it from the flagged "
            "stratum alone would assume the detector missed nothing -- which is "
            "the claim being tested."
        )

    unsampled = [b.name for b in bands if b.population > 0 and b.sampled == 0]
    if unsampled:
        raise EstimationError(
            "these unflagged bands hold traffic but were never labelled: "
            f"{', '.join(unsampled)}. A stratified mean over the sampled bands "
            "alone silently drops their weight and understates q in proportion "
            "to how much of the pool they hold. Either label them or merge them "
            "into a band that was labelled; there is no third option that is "
            "not an assumption about traffic nobody looked at."
        )

    fractions = {round(b.fraction_sampled, 12) for b in bands if b.population > 0}
    proportional = len(fractions) <= 1

    if proportional:
        q_hat = errors / sampled
        q_lo, q_hi = clopper_pearson(errors, sampled, ci)
        basis = (
            "Clopper-Pearson on the pooled count; exact and conservative, "
            "because under equal sampling fractions the stratified estimator "
            "equals the pooled proportion and its variance cannot exceed the "
            "binomial"
        )
        return q_hat, q_lo, q_hi, True, basis

    q_hat = 0.0
    variance = 0.0
    for band in bands:
        if band.population == 0 or band.sampled == 0:
            continue
        weight = band.population / population
        rate = band.rate
        q_hat += weight * rate
        fpc = 1.0 - band.sampled / band.population
        if band.sampled > 1:
            # Unbiased sample variance of a Bernoulli: n/(n-1) * p(1-p).
            var_h = rate * (1.0 - rate) * band.sampled / (band.sampled - 1)
        else:
            var_h = rate * (1.0 - rate)
        variance += (weight**2) * fpc * var_h / band.sampled

    se = math.sqrt(max(variance, 0.0))
    z = _Z_95
    q_lo = max(0.0, q_hat - z * se)
    q_hi = min(1.0, q_hat + z * se)
    basis = (
        "stratified variance with a per-band finite-population correction, "
        "normal interval; APPROXIMATE -- unequal sampling fractions admit no "
        "exact interval, which is what Neyman allocation costs"
    )
    return q_hat, q_lo, q_hi, False, basis


def estimate_on_traffic(
    *,
    flagged_reviewed: int,
    flagged_confirmed: int,
    bands: Sequence[Band],
    flagged_population: Optional[int] = None,
    ci: float = 0.95,
    planned_margin: Optional[float] = None,
    kappa: Optional[float] = None,
    kappa_floor: float = 0.6,
) -> OnTrafficEstimate:
    """Recall and precision on one month of real traffic.

    Quantity: finite-population recall and precision on the realised month.
    Propagation: Clopper-Pearson (or stratified-normal under Neyman) on ``q``,
    carried into recall by the exact monotone transform
    ``R = TP/(TP + q*N_B)``, which preserves coverage because ``R`` is strictly
    decreasing in ``q``.

    Args:
        flagged_reviewed: ``N_A``. Items the detector flagged, all reviewed.
        flagged_confirmed: ``TP``. Of those, confirmed incorrect. Exact.
        bands: The unflagged stratum, one :class:`Band` per score band. A single
            band is simple random sampling, which is what month one runs.
        flagged_population: Items the detector flagged this month, when that
            differs from the number reviewed. Supplying a larger value is
            refused: the whole reason ``TP`` and precision are free of intervals
            is that stratum A is a census, and a sampled stratum A makes both of
            them estimates. Left ``None``, the reviewed count is taken as the
            census.
        ci: Coverage for every interval returned. Only 0.95 is supported.
        planned_margin: The recall half-width a :class:`~.planning.LabelPlan`
            promised, so the realised one can be reported against it.
        kappa: Measured inter-rater agreement on the double-labelled subset. An
            interval computed from labels that two reviewers disagree about is
            narrower than the evidence supports, so a low value widens it.
        kappa_floor: Below this, the recall interval is widened by ``1/kappa``
            and the reason recorded on the metric. ``CLAUDE.md`` names a +/-5pp
            recall interval at kappa 0.5 as meaningless; this makes it wide
            instead of meaningless.

    Returns:
        The estimate, with exact and estimated quantities in separate fields.

    Raises:
        EstimationError: If the flagged census is inconsistent, if no labels
            were drawn from the unflagged pool, or if the confirmed count
            exceeds the reviewed one.
    """
    if abs(ci - 0.95) > 1e-12:
        raise EstimationError(
            f"ci={ci!r}: only 0.95 is supported. Every interval this project "
            "publishes is two-sided 95%, and a metric that carried a different "
            "coverage under the same convention label would be a 23% error "
            "wearing the right words (DECISIONS.md 110)."
        )
    if flagged_reviewed < 0 or flagged_confirmed < 0:
        raise EstimationError("counts cannot be negative")
    if flagged_confirmed > flagged_reviewed:
        raise EstimationError(
            f"{flagged_confirmed} confirmed errors inside {flagged_reviewed} "
            "reviewed items is impossible"
        )
    if flagged_population is not None and flagged_population != flagged_reviewed:
        raise EstimationError(
            f"{flagged_reviewed} of {flagged_population} flagged items were "
            "reviewed. This estimator requires a census of the flagged stratum, "
            "because that census is the only reason the confirmed-error count "
            "and precision carry no interval. Sampling stratum A turns the free "
            "exact half of this design into a second estimate, and reporting it "
            "as EXACT would be the yield-versus-rate conflation CLAUDE.md calls "
            "the most damaging error available here."
        )
    if not bands:
        raise EstimationError("the unflagged stratum must be described by at least one band")

    q_hat, q_lo, q_hi, proportional, basis = _stratified_prevalence(bands, ci)
    pool = sum(b.population for b in bands)
    labels = sum(b.sampled for b in bands)
    true_positives = float(flagged_confirmed)

    if true_positives == 0.0:
        raise EstimationError(
            "the flagged stratum confirmed no true positives, so recall is 0/0 "
            "at every value of q. This operating point has nothing to warrant "
            "on this traffic, and reporting a recall of zero would assert a "
            "measurement that was not made."
        )

    def recall_at(q: float) -> float:
        return true_positives / (true_positives + q * pool)

    # R is strictly decreasing in q, so the bounds cross over.
    recall_hat = recall_at(q_hat)
    recall_lo = recall_at(q_hi)
    recall_hi = recall_at(q_lo)

    notes: list[str] = []
    convention = "two_sided_95"

    prevalence_metric = Metric(
        name="unflagged_prevalence",
        value=q_hat,
        kind=MetricKind.ESTIMATED,
        n=labels,
        ci_low=q_lo,
        ci_high=q_hi,
        ci_level=ci,
        unit="rate",
        estimator=basis,
        convention=convention,
    )
    recall_metric = Metric(
        name="recall_on_traffic",
        value=recall_hat,
        kind=MetricKind.ESTIMATED,
        n=labels,
        ci_low=recall_lo,
        ci_high=recall_hi,
        ci_level=ci,
        unit="rate",
        estimator=(
            f"monotone transform of the q interval through R = TP/(TP + q*N_B); "
            f"q interval by {basis}"
        ),
        convention=convention,
    )
    missed_metric = Metric(
        name="errors_missed",
        value=q_hat * pool,
        kind=MetricKind.ESTIMATED,
        n=labels,
        ci_low=q_lo * pool,
        ci_high=q_hi * pool,
        ci_level=ci,
        unit="count",
        estimator=f"q interval scaled by the unflagged pool of {pool:,}; {basis}",
        convention=convention,
    )

    if kappa is not None and kappa < kappa_floor:
        factor = 1.0 / max(kappa, 1e-6)
        reason = (
            f"inter-rater kappa {kappa:.3f} below the {kappa_floor:g} floor: the "
            "labels this interval rests on are not reproducible between "
            "reviewers"
        )
        recall_metric = recall_metric.widened(factor, reason)
        notes.append(
            f"recall interval widened x{factor:.2f} for kappa={kappa:.3f}. A "
            "narrow interval over labels two reviewers disagree about is a "
            "false claim of precision, not a measurement."
        )
    elif kappa is not None:
        notes.append(f"inter-rater kappa {kappa:.3f}, at or above the {kappa_floor:g} floor")

    realised = (recall_metric.ci_high - recall_metric.ci_low) / 2.0
    margin_met = None if planned_margin is None else realised <= planned_margin
    if planned_margin is not None and not margin_met:
        notes.append(
            f"the realised half-width {realised:.4f} did not reach the planned "
            f"{planned_margin:.4f}. The plan assumed a prevalence; the measured "
            f"one is {q_hat:.5f}. Replan at the measured value rather than "
            "quoting the planned margin."
        )

    precision_metric = Metric(
        name="precision_on_traffic",
        value=(true_positives / flagged_reviewed) if flagged_reviewed else 0.0,
        kind=MetricKind.EXACT,
        n=flagged_reviewed,
        unit="rate",
    )
    if not proportional:
        notes.append(
            "allocation was not proportional, so the q interval is approximate. "
            "Report it as such or fall back to proportional for an exact one."
        )

    return OnTrafficEstimate(
        recall=recall_metric,
        precision=precision_metric,
        confirmed_errors=Metric(
            name="confirmed_errors",
            value=true_positives,
            kind=MetricKind.EXACT,
            n=flagged_reviewed,
            unit="count",
        ),
        errors_missed=missed_metric,
        unflagged_prevalence=prevalence_metric,
        labels_spent=labels,
        realised_margin=realised,
        planned_margin=planned_margin,
        margin_met=margin_met,
        proportional=proportional,
        interval_basis=basis,
        bands=tuple(bands),
        notes=tuple(notes),
    )
