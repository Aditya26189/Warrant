"""How many labels a recall claim costs, propagated through ``dR/dq``.

**This module exists because the repository got this wrong.** ``DECISIONS.md``
147 records the defect and its magnitude; the short version is that
``economics/review.py`` sized a binomial on recall directly and called the
result "reviewed items", understating the bill by 9x to 19x at the three
shipped operating points. ``CLAUDE.md`` names that error first in its
silent-failure list and ``SPEC.md`` section 6.2 calls it "the error the spec
exists to prevent".

The reason it is worth a module rather than a line is structural. Recall is not
measured; it is *computed* from a measured prevalence::

    R      = TP / (TP + q*N_u)
    dR/dq  = -TP*N_u / (TP + q*N_u)^2

``TP`` is an exact census of the flagged stratum, which is reviewed in full and
therefore free. ``q`` is the prevalence of errors in the unflagged pool, which
is what labels buy. Because the unflagged pool is two orders of magnitude larger
than the flagged one, a small error in ``q`` arrives at ``R`` multiplied by that
ratio -- and sample size scales as ``1/margin^2``, so the cost is the *square*
of the derivative.

Every figure here is a **planning** figure over **declared** inputs. A sample
size is computed before the measurement it sizes, so it is always conditioned on
an assumed value of the quantity being measured. The dishonesty is never in
declaring ``q``; it is in not saying that you did. Each result carries its
``declared_inputs`` and :mod:`controlplane.sampling.estimator` reports the
realised margin against the planned one once the labels land.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    "LabelPlan",
    "RecallSensitivity",
    "SizingError",
    "labels_for_prevalence",
    "labels_for_recall",
    "recall_sensitivity",
]

#: Two-sided normal quantile at 95%, matching ``economics/review.py`` so a
#: sample size computed here and an interval reported by a warrant mean the
#: same thing.
_Z_95 = 1.959963984540054


class SizingError(ValueError):
    """A sample size was requested that cannot be honestly returned."""


@dataclass(frozen=True)
class RecallSensitivity:
    """``dR/dq`` at one declared operating point, with everything behind it.

    Attributes:
        recall: Declared recall at the operating point. Measured on an eval set;
            declared for this workload, because the workload is not that eval
            set.
        flag_rate: Declared flag rate at the operating point.
        monthly_interactions: Declared traffic volume, ``N``.
        base_error_rate: Declared error rate of that traffic.
        errors: ``N * base_error_rate``. Errors present in the month.
        flagged_pool: ``N * flag_rate``, ``N_f``. Reviewed in full.
        unflagged_pool: ``N * (1 - flag_rate)``, ``N_u``. Sampled.
        confirmed_errors: ``errors * recall``, ``TP``. Exact once reviewed.
        unflagged_prevalence: ``(errors - TP) / N_u``, ``q``.
        derivative: ``dR/dq``, negative by construction.
        amplification: ``N_u / TP``. **This is the ratio that multiplies.** An
            error of ``dq`` in the prevalence moves the denominator of
            ``R = TP/(TP + q*N_u)`` by ``dq*N_u``, which measured against ``TP``
            is ``dq`` times this. ``CLAUDE.md`` and ``SPEC.md`` §6.2 both quote
            its value correctly and both name it "the unflagged pool is ~232x
            the flagged one", which is a different ratio with a different value
            -- see ``DECISIONS.md`` 148.
        pool_ratio: ``N_u / N_f``, the unflagged pool against the flagged one.
            Reported alongside precisely so the two can never be conflated
            again. At the declared workload this is 66, not 232.
    """

    recall: float
    flag_rate: float
    monthly_interactions: int
    base_error_rate: float
    errors: float
    flagged_pool: float
    unflagged_pool: float
    confirmed_errors: float
    unflagged_prevalence: float
    derivative: float
    amplification: float
    pool_ratio: float

    def render(self) -> str:
        """One line naming the derivative and the quantities behind it."""
        return (
            f"dR/dq = {self.derivative:.3f}  "
            f"(TP={self.confirmed_errors:,.0f}, N_u={self.unflagged_pool:,.0f}, "
            f"q={self.unflagged_prevalence:.5f}, "
            f"N_u is {self.amplification:,.0f}x the confirmed true positives "
            f"and {self.pool_ratio:,.0f}x the flagged pool)"
        )


def recall_sensitivity(
    *,
    recall: float,
    flag_rate: float,
    monthly_interactions: int,
    base_error_rate: float,
) -> RecallSensitivity:
    """Close the loop from a declared workload to ``dR/dq``.

    Quantity: the partial derivative of recall with respect to the prevalence of
    errors in the unflagged pool. Propagation: closed form, exact --
    ``dR/dq = -TP*N_u / (TP + q*N_u)^2``, obtained by differentiating
    ``R = TP/(TP + q*N_u)`` holding ``TP`` and ``N_u`` fixed, which is what the
    census of stratum A and the month's realised volume respectively do.

    Args:
        recall: Declared recall at the operating point, in ``(0, 1]``.
        flag_rate: Declared flag rate, in ``[0, 1)``.
        monthly_interactions: Declared volume, positive.
        base_error_rate: Declared error rate of the traffic, in ``(0, 1)``.

    Returns:
        The sensitivity and every intermediate it was built from.

    Raises:
        SizingError: If an input is out of range, or if the declared recall and
            flag rate are inconsistent with the declared base rate -- that is,
            if they imply more true positives than the operating point flags.
            Those are three numbers from three different places and there is no
            reason they must agree; when they do not, the cause is the
            scenario-mixing error ``CLAUDE.md`` invariant 6 names, and a
            derivative computed through it would be fiction.
    """
    if not 0.0 < recall <= 1.0:
        raise SizingError(f"recall={recall!r} must be in (0, 1]")
    if not 0.0 <= flag_rate < 1.0:
        raise SizingError(f"flag_rate={flag_rate!r} must be in [0, 1)")
    if monthly_interactions <= 0:
        raise SizingError(
            f"monthly_interactions={monthly_interactions!r} must be positive"
        )
    if not 0.0 < base_error_rate < 1.0:
        raise SizingError(f"base_error_rate={base_error_rate!r} must be in (0, 1)")

    n = float(monthly_interactions)
    errors = n * base_error_rate
    flagged = n * flag_rate
    unflagged = n * (1.0 - flag_rate)
    true_positives = errors * recall

    if true_positives > flagged:
        raise SizingError(
            f"recall={recall:g} at flag_rate={flag_rate:g} implies "
            f"{true_positives:,.0f} true positives inside a flagged pool of "
            f"{flagged:,.0f}. These rates were not measured on traffic at "
            f"base_error_rate={base_error_rate:g}. Quoting them together is the "
            "scenario mixing CLAUDE.md invariant 6 forbids."
        )

    missed = errors - true_positives
    q = missed / unflagged
    denominator = true_positives + q * unflagged
    derivative = -true_positives * unflagged / (denominator**2)

    return RecallSensitivity(
        recall=recall,
        flag_rate=flag_rate,
        monthly_interactions=int(monthly_interactions),
        base_error_rate=base_error_rate,
        errors=errors,
        flagged_pool=flagged,
        unflagged_pool=unflagged,
        confirmed_errors=true_positives,
        unflagged_prevalence=q,
        derivative=derivative,
        amplification=(unflagged / true_positives) if true_positives > 0 else math.inf,
        pool_ratio=(unflagged / flagged) if flagged > 0 else math.inf,
    )


@dataclass(frozen=True)
class LabelPlan:
    """Labels to draw from the unflagged stratum, and what they buy.

    Attributes:
        estimand: ``"recall"`` or ``"prevalence"``. **Required and never
            defaulted.** A sample size with no estimand is a number in no units,
            which is the defect this module was written to close.
        margin: Declared half-width wanted, in the units of ``estimand``.
        confidence: Coverage the margin is quoted at.
        labels: Labels to draw, under ``basis``. This is the number to budget
            from.
        basis: ``"exact"`` or ``"normal"`` -- which interval ``labels`` was
            sized against.
        labels_normal: The normal-approximation figure, finite-population
            corrected. ``SPEC.md`` section 6.2's answer, and what a reader
            recomputes by hand.
        labels_exact: The smallest ``n`` from which the Clopper-Pearson
            interval the estimator reports holds the margin and keeps holding
            it. ``None`` if no achievable sample reaches it.
        labels_infinite_population: The uncorrected normal figure,
            ``z^2 p(1-p)/m^2`` inflated by the design effect, with no
            finite-population correction. Reported because it is the closed
            form the spec writes down.
        prevalence_margin: For ``estimand="recall"``, the ``m_q`` the recall
            margin was translated into. Equal to ``margin`` for a prevalence
            plan.
        derivative: ``dR/dq`` used, when sizing for recall; ``None`` otherwise.
        naive_labels: What sizing this margin *directly* as a binomial on the
            estimand would have returned -- the wrong answer, kept so the gap is
            visible rather than asserted.
        understatement: ``labels`` divided by ``naive_labels``. For recall this
            is ``(dR/dq)^2`` before the finite-population correction.
        feasible: Whether the plan can be executed at all.
        refusal_reason: Why not, when ``feasible`` is ``False``.
        declared_inputs: Every input that was chosen rather than measured.
        note: What the plan is and is not.
        assurance: Declared probability that the realised margin meets
            ``margin`` (``DECISIONS.md`` 191). ``labels_exact`` is sized to it.
        assurance_at_labels: Exact assurance of ``labels`` -- at least
            ``assurance`` on the exact basis, and printed on the normal basis so
            its shortfall is visible.
        labels_at_expected_count: The exact-interval size at the *expected*
            error count, which is what the exact basis quoted before 191.
        assurance_at_expected_count: That size's assurance, about one half.
        sizes_by_assurance: ``(assurance, labels)`` for each rung of
            :data:`ASSURANCE_LADDER`; ``None`` where no sample reaches it.
    """

    estimand: str
    margin: float
    confidence: float
    labels: int
    basis: str
    labels_normal: int
    labels_exact: Optional[int]
    labels_infinite_population: int
    prevalence_margin: Optional[float]
    derivative: Optional[float]
    naive_labels: int
    understatement: float
    feasible: bool
    refusal_reason: str = ""
    declared_inputs: dict[str, float] = field(default_factory=dict)
    note: str = ""
    assurance: Optional[float] = None
    assurance_at_labels: Optional[float] = None
    labels_at_expected_count: Optional[int] = None
    assurance_at_expected_count: Optional[float] = None
    sizes_by_assurance: tuple[tuple[float, Optional[int]], ...] = ()

    def render(self) -> str:
        """A human-readable plan, or the refusal and what would lift it."""
        if not self.feasible:
            return (
                f"REFUSED: {self.estimand} to +/-{self.margin:g} at "
                f"{self.confidence:.0%}\n    {self.refusal_reason}"
            )
        head = (
            f"{self.estimand} to +/-{self.margin:g} at {self.confidence:.0%}: "
            f"{self.labels:,} labels from the unflagged pool "
            f"({self.basis} basis)"
        )
        if self.assurance_at_labels is not None:
            head += (
                f"\n    realises the margin with probability "
                f"{self.assurance_at_labels:.3f} (declared assurance {self.assurance:g})"
            )
        if self.labels_at_expected_count is not None:
            head += (
                f"\n    sized at the expected error count it would be "
                f"{self.labels_at_expected_count:,}, which realises the margin with "
                f"probability {self.assurance_at_expected_count:.3f}"
            )
        if self.labels_exact is not None and self.labels_exact != self.labels_normal:
            head += (
                f"\n    exact interval needs {self.labels_exact:,}; the "
                f"normal approximation says {self.labels_normal:,}"
            )
        if self.derivative is not None and self.prevalence_margin is not None:
            head += (
                f"\n    via prevalence to +/-{self.prevalence_margin:.6f}, "
                f"dR/dq={self.derivative:.3f}"
            )
            head += (
                f"\n    sizing the margin directly would have said "
                f"{self.naive_labels:,} -- understated "
                f"{self.understatement:.1f}x"
            )
        return head


def _binomial_n(p: float, margin: float, z: float, design_effect: float) -> float:
    """Normal-approximation sample size for a proportion, infinite population."""
    return (z**2) * p * (1.0 - p) / (margin**2) * design_effect


def _finite_population(n: float, pool: Optional[float]) -> float:
    """Cochran's finite-population correction.

    ``n_fpc = n / (1 + (n - 1)/N)``. Sampling without replacement from a pool of
    ``N`` removes variance the infinite-population formula charges for, and at
    the margins this project quotes ``n/N`` reaches a fifth of the pool, where
    ignoring it over-sizes materially. Omitting it errs toward a larger bill,
    which is the safe direction, but a price list that is wrong in the safe
    direction is still wrong and a reviewer with Cochran open will say so.
    """
    if pool is None or pool <= 1.0:
        return n
    return n / (1.0 + (n - 1.0) / pool)


#: How far past a candidate ``n`` the margin must keep holding before that ``n``
#: is quoted. The same horizon and the same reason as
#: :data:`controlplane.economics.sizing.STABILITY_HORIZON`: the achieved margin
#: is not monotone in ``n``, because the observed count is ``round(q*n)`` and the
#: integer jumps.
STABILITY_HORIZON = 12

#: Past this, the honest answer is "not by labelling".
MAX_LABELS = 2_000_000

#: Assurances every recall plan prints a sample size for, so the declared one is
#: read beside its neighbours (``DECISIONS.md`` 191). Presentation, like
#: :data:`controlplane.economics.sizing.POWER_LADDER`; 0.5 is on it because it is
#: roughly what sizing at the expected count delivered.
ASSURANCE_LADDER: tuple[float, ...] = (0.5, 0.8, 0.9)



def _effective_n(ns, *, pool: float, design_effect: float, finite_population: bool):
    """Sample size of an SRS whose binomial variance matches this design's.

    Two corrections, both of which change how much information ``n`` labels
    carry rather than how many labels are drawn:

    * the **design effect** is ``Var_design / Var_SRS``, so a design with
      ``deff`` behaves like an SRS of ``n/deff``;
    * the **finite-population correction** multiplies variance by
      ``1 - n/N``, so drawing ``n`` without replacement from ``N`` behaves like
      an SRS of ``n / (1 - n/N)``.

    Both are applied to the *information*, then Clopper-Pearson is evaluated at
    that effective size. Applying them to the interval afterwards would scale a
    bound that is not symmetric about the estimate, which is the whole reason
    the exact interval was chosen over the normal one.
    """
    import numpy as np

    ns = np.asarray(ns, dtype=np.float64)
    if finite_population and pool > 0:
        fraction = np.minimum(ns / pool, 0.999999)
    else:
        fraction = np.zeros_like(ns)
    effective = ns / design_effect / (1.0 - fraction)
    if pool > 0:
        effective = np.minimum(effective, pool)
    return np.maximum(np.rint(effective), 1.0).astype(np.int64)


def _margin_mask(
    lo: int,
    hi: int,
    *,
    prevalence: float,
    true_positives: float,
    pool: float,
    margin: float,
    design_effect: float,
    finite_population: bool,
    confidence: float,
):
    """Does the *exact* recall interval reach ``margin``, for every ``n`` in range?

    This is the predicate the estimator will actually satisfy or fail.
    :func:`labels_for_recall` with ``basis="normal"`` sizes against the normal
    approximation, which is what ``SPEC.md`` §6.2 writes down and what
    under-delivers: at the declared workload its 843 labels realise a half-width
    of 0.0545 against a 0.05 target. Vectorised for the same reason
    :func:`controlplane.economics.sizing._detect_mask` is -- the search asks this
    tens of thousands of times.
    """
    import numpy as np
    from scipy.stats import beta

    ns = np.arange(lo, hi + 1, dtype=np.int64)
    effective = _effective_n(
        ns, pool=pool, design_effect=design_effect, finite_population=finite_population
    )
    counts = np.rint(prevalence * effective).astype(np.int64)
    alpha = 1.0 - confidence

    q_lo = np.zeros(ns.shape, dtype=float)
    live = counts > 0
    if live.any():
        q_lo[live] = beta.ppf(
            alpha / 2.0, counts[live], effective[live] - counts[live] + 1
        )
    q_hi = np.ones(ns.shape, dtype=float)
    below = counts < effective
    if below.any():
        q_hi[below] = beta.ppf(
            1.0 - alpha / 2.0, counts[below] + 1, effective[below] - counts[below]
        )

    recall_lo = true_positives / (true_positives + q_hi * pool)
    recall_hi = true_positives / (true_positives + q_lo * pool)
    return ((recall_hi - recall_lo) / 2.0) <= margin


def _recall_half_width(ks, effective, *, true_positives: float, pool: float, confidence: float):
    """The recall half-width the estimator reports for ``k`` errors in ``n_eff``.

    Clopper-Pearson on the prevalence, pushed through ``R = TP / (TP + q N_u)``,
    exactly as :func:`_margin_mask` evaluates it at one count.
    """
    import numpy as np
    from scipy.stats import beta

    ks = np.asarray(ks, dtype=np.int64)
    effective = np.asarray(effective, dtype=np.int64)
    alpha = 1.0 - confidence
    q_lo = np.zeros(ks.shape, dtype=float)
    live = ks > 0
    if live.any():
        q_lo[live] = beta.ppf(alpha / 2.0, ks[live], effective[live] - ks[live] + 1)
    q_hi = np.ones(ks.shape, dtype=float)
    below = ks < effective
    if below.any():
        q_hi[below] = beta.ppf(1.0 - alpha / 2.0, ks[below] + 1, effective[below] - ks[below])
    recall_lo = true_positives / (true_positives + q_hi * pool)
    recall_hi = true_positives / (true_positives + q_lo * pool)
    return (recall_hi - recall_lo) / 2.0


def _assurance(
    ns,
    *,
    prevalence: float,
    true_positives: float,
    pool: float,
    margin: float,
    design_effect: float,
    finite_population: bool,
    confidence: float,
):
    """Chance that a sample of each ``n`` realises the recall margin.

    Quantity: ``P(half-width(K, n_eff) <= margin)`` with ``K ~ Bin(n_eff, q)``,
    the probability that the interval the estimator reports is as narrow as the
    plan promised. Propagation: exact binomial weights over the counts that meet
    the margin. With a design effect the count is not one binomial, and this is
    the planner's existing effective-``n`` approximation.

    **The shape it relies on, and the one it first assumed wrongly.** The
    half-width in ``k`` is roughly ``sqrt(k) * |dR/dq|``: the prevalence interval
    widens as ``sqrt(k)`` while ``|dR/dq| = TP N_u / (TP + q N_u)^2`` stays near
    ``N_u / TP`` until ``q N_u`` approaches ``TP`` and then falls as ``1/k^2``. So
    it rises to one peak, near ``k = n TP / (3 N_u)``, and falls after. The
    counts that meet a margin are therefore a low tail ``k <= a`` and a high tail
    ``k >= b``. The first implementation assumed only the high tail, which holds
    where the peak sits far below the expected count (the declared workload) and
    fails where it does not: at ``decision_support`` it returned 1.0 where brute
    force gives 0.0000 (``DECISIONS.md`` 191). ``tests/test_sampling_assurance.py``
    checks the single peak at every shipped operating point and the result
    against brute-force enumeration there.

    Counts are searched within the expected count +/- 12 standard deviations,
    outside which the binomial mass is below 1e-30; the tails' probabilities are
    still taken over every count, so nothing inside the bracket is dropped.
    """
    import numpy as np
    from scipy.stats import binom

    ns = np.asarray(ns, dtype=np.int64)
    effective = _effective_n(
        ns, pool=pool, design_effect=design_effect, finite_population=finite_population
    )

    def width(ks):
        return _recall_half_width(
            ks, effective, true_positives=true_positives, pool=pool, confidence=confidence
        )

    mean = effective * prevalence
    spread = np.sqrt(np.maximum(effective * prevalence * (1.0 - prevalence), 1.0))
    lo = np.clip(np.floor(mean - 12.0 * spread).astype(np.int64), 0, effective)
    hi = np.clip(np.ceil(mean + 12.0 * spread).astype(np.int64), 0, effective)

    # 1. The peak within the bracket, by integer ternary search. On a function
    #    with one peak this converges to it, or to the bracket's end nearer it
    #    when the peak lies outside.
    a, b = lo.copy(), hi.copy()
    while True:
        open_ = b - a > 2
        if not open_.any():
            break
        third = (b - a) // 3
        m1, m2 = a + third, b - third
        rising = width(m1) < width(m2)
        a = np.where(open_ & rising, m1 + 1, a)
        b = np.where(open_ & ~rising, m2, b)
    candidates = np.stack([a, np.minimum(a + 1, b), b])
    widths = np.stack([width(c) for c in candidates])
    peak = candidates[np.argmax(widths, axis=0), np.arange(ns.size)]
    peak_width = widths.max(axis=0)

    total = np.zeros(ns.shape, dtype=float)
    everywhere = peak_width <= margin
    total[everywhere] = 1.0

    # 2. Rising side [lo, peak]: the last count still meeting the margin.
    left_meets = ~everywhere & (width(lo) <= margin)
    if left_meets.any():
        l, r = lo.copy(), peak.copy()  # width(l) <= margin < width(r)
        while True:
            open_ = left_meets & (r - l > 1)
            if not open_.any():
                break
            mid = (l + r) // 2
            ok = width(mid) <= margin
            l = np.where(open_ & ok, mid, l)
            r = np.where(open_ & ~ok, mid, r)
        total[left_meets] += binom.cdf(l[left_meets], effective[left_meets], prevalence)

    # 3. Falling side [peak, hi]: the first count meeting the margin again.
    right_meets = ~everywhere & (width(hi) <= margin)
    if right_meets.any():
        l, r = peak.copy(), hi.copy()  # width(l) > margin >= width(r)
        while True:
            open_ = right_meets & (r - l > 1)
            if not open_.any():
                break
            mid = (l + r) // 2
            ok = width(mid) <= margin
            r = np.where(open_ & ok, mid, r)
            l = np.where(open_ & ~ok, mid, l)
        total[right_meets] += binom.sf(r[right_meets] - 1, effective[right_meets], prevalence)
    return np.clip(total, 0.0, 1.0)


def _labels_for_exact_margin(
    *,
    prevalence: float,
    true_positives: float,
    pool: float,
    margin: float,
    design_effect: float,
    finite_population: bool,
    confidence: float,
    horizon: int = STABILITY_HORIZON,
    assurance: Optional[float] = None,
) -> Optional[int]:
    """Smallest ``n`` from which the exact recall margin holds, and keeps holding.

    With ``assurance``, "holds" means the margin is realised with at least that
    probability over the binomial count (:func:`_assurance`); without it, at the
    expected count -- which ``DECISIONS.md`` 191 found delivers about half.

    Follows :func:`controlplane.economics.sizing.negatives_for_detection` step
    for step, and for the identical reason: the predicate is not monotone in
    ``n``, so the first crossing is not a number anyone can budget from.
    ``DECISIONS.md`` 146 established that the stable threshold is the quotable
    one; this applies the same rule to a different predicate.

    Returns:
        The count, or ``None`` when no achievable sample reaches the margin.
    """
    cap = int(min(MAX_LABELS, max(pool, 1)))

    def mask(lo: int, hi: int):
        if assurance is not None:
            import numpy as np

            return _assurance(
                np.arange(lo, hi + 1, dtype=np.int64),
                prevalence=prevalence,
                true_positives=true_positives,
                pool=pool,
                margin=margin,
                design_effect=design_effect,
                finite_population=finite_population,
                confidence=confidence,
            ) >= assurance
        return _margin_mask(
            lo,
            hi,
            prevalence=prevalence,
            true_positives=true_positives,
            pool=pool,
            margin=margin,
            design_effect=design_effect,
            finite_population=finite_population,
            confidence=confidence,
        )

    if cap < 2 or not mask(max(1, cap - 200), cap).all():
        return None

    upper = 10
    while upper <= cap:
        span = max(50, upper // 4)
        if mask(upper, min(upper + span, cap)).all():
            break
        upper = int(upper * 1.2) + 1
    else:
        return None

    below = mask(1, upper)
    failures = (~below).nonzero()[0]
    stable = int(failures[-1]) + 2 if failures.size else 1
    ceiling = min(stable * horizon, cap)
    if not mask(stable, ceiling).all():  # pragma: no cover - convergence failure
        return None
    return stable


def _certified(
    ns,
    target: float,
    *,
    prevalence: float,
    true_positives: float,
    pool: float,
    margin: float,
    design_effect: float,
    finite_population: bool,
    confidence: float,
):
    """Sample sizes whose assurance is *proven* to reach ``target`` in four evaluations.

    A central count interval ``[k1, k2]`` holding at least ``target`` of the
    binomial mass certifies ``assurance >= target`` when the half-width is at
    most ``margin`` everywhere on it. The half-width has one peak
    (:func:`_assurance`), so its maximum over the interval is an endpoint whenever
    it is falling at ``k1`` or rising at ``k2`` -- four evaluations. ``False``
    means *not certified*, not *below target*; the caller computes those exactly.
    This exists because confirming a size over its 12x horizon asks the question
    for hundreds of thousands of sizes, nearly all far above target.
    """
    import numpy as np
    from scipy.stats import binom

    ns = np.asarray(ns, dtype=np.int64)
    effective = _effective_n(
        ns, pool=pool, design_effect=design_effect, finite_population=finite_population
    )
    tail = (1.0 - target) / 2.0
    k1 = np.asarray(binom.ppf(tail, effective, prevalence), dtype=np.int64)
    k2 = np.asarray(binom.isf(tail, effective, prevalence), dtype=np.int64)
    k1 = np.clip(k1, 0, effective)
    k2 = np.clip(k2, k1, effective)
    mass = binom.cdf(k2, effective, prevalence) - binom.cdf(k1 - 1, effective, prevalence)

    def width(ks):
        return _recall_half_width(
            ks, effective, true_positives=true_positives, pool=pool, confidence=confidence
        )

    w1, w2 = width(k1), width(k2)
    # Strict: an exactly flat step is not evidence of which side of the peak
    # an endpoint sits on (DECISIONS 194).
    falling_at_k1 = width(np.minimum(k1 + 1, effective)) < w1
    rising_at_k2 = width(np.maximum(k2 - 1, 0)) < w2
    endpoint_max = (falling_at_k1 | rising_at_k2) & (k2 > k1)
    return (mass >= target) & endpoint_max & (w1 <= margin) & (w2 <= margin)


def _labels_at_assurances(
    targets,
    *,
    prevalence: float,
    true_positives: float,
    pool: float,
    margin: float,
    design_effect: float,
    finite_population: bool,
    confidence: float,
    horizon: int = STABILITY_HORIZON,
) -> dict[float, Optional[int]]:
    """Stable sizes for several assurances from one exact evaluation.

    The stable-threshold rule of ``DECISIONS.md`` 146 for each target -- the
    smallest ``n`` from which assurance holds at ``n`` and every ``n`` up to
    ``horizon`` times it -- but read off a single array of exact assurances over
    ``[1, horizon x n_max]``, where ``n_max`` is the largest target's size. Each
    target's own horizon lies inside that range, so every size is confirmed
    exactly as a separate search would confirm it; the saving is that the
    binomial sums are computed once instead of once per target (about 4x on a
    plan's ladder).
    """
    import numpy as np

    common = dict(
        prevalence=prevalence, true_positives=true_positives, pool=pool, margin=margin,
        design_effect=design_effect, finite_population=finite_population,
        confidence=confidence,
    )
    cap = int(min(MAX_LABELS, max(pool, 1)))
    ordered = sorted(set(targets))
    result: dict[float, Optional[int]] = {target: None for target in ordered}
    if cap < 2:
        return result

    def at_least(values_ns, target):
        """``assurance >= target`` per size: certified cheaply, else computed."""
        ok = _certified(values_ns, target, **common)
        rest = ~ok
        if rest.any():
            ok[rest] = _assurance(values_ns[rest], **common) >= target
        return ok

    def last_failure(lo_n: int, hi_n: int, target: float) -> int:
        """The largest ``n`` in ``[lo_n, hi_n]`` whose assurance is below ``target``, or 0.

        Scanned from the top in chunks, stopping at the first chunk holding a
        failure: sizes below the last failure cannot change a stable threshold,
        so they are never computed. Within a chunk every size is decided --
        certified cheaply, or computed exactly.
        """
        chunk = 4096
        top_n = hi_n
        while top_n >= lo_n:
            bottom = max(lo_n, top_n - chunk + 1)
            window = np.arange(bottom, top_n + 1)
            ok = at_least(window, target)
            if not ok.all():
                return int(window[~ok][-1])
            top_n = bottom - 1
        return 0

    top_ns = np.arange(max(1, cap - 200), cap + 1)
    reachable = [target for target in ordered if at_least(top_ns, target).all()]
    if not reachable:
        return result
    hardest = reachable[-1]

    # Grow until a stretch holds for the hardest target, as the single-target
    # search does.
    upper = 10
    while upper <= cap:
        span = max(50, upper // 4)
        if at_least(np.arange(upper, min(upper + span, cap) + 1), hardest).all():
            break
        upper = int(upper * 1.2) + 1
    else:
        return result

    # The hardest target's stable size, confirmed over its whole horizon; a
    # failure found above moves the size up and the horizon with it.
    stable = last_failure(1, upper, hardest) + 1
    confirmed_to = upper
    while True:
        ceiling = min(stable * horizon, cap)
        if ceiling <= confirmed_to:
            break
        failure = last_failure(confirmed_to + 1, ceiling, hardest)
        confirmed_to = ceiling
        if failure:
            stable = failure + 1
    result[hardest] = max(stable, 1)

    # Easier targets hold wherever the hardest does, so only sizes below the
    # hardest's stable size can fail them; each horizon lies inside the range
    # already confirmed for the hardest.
    for target in reachable[:-1]:
        result[target] = max(last_failure(1, result[hardest] - 1, target) + 1, 1)
    return result


def _assurance_by_enumeration(
    n: int,
    *,
    prevalence: float,
    true_positives: float,
    pool: float,
    margin: float,
    design_effect: float,
    finite_population: bool,
    confidence: float,
) -> float:
    """Assurance at one size over every count, assuming nothing about the shape.

    The reference :func:`_assurance` is checked against at every quoted size
    (DECISIONS 194): the fast path rests on the half-width having one peak, and
    this does not.
    """
    import numpy as np
    from scipy.stats import binom

    effective = int(_effective_n(
        np.array([n]), pool=pool, design_effect=design_effect,
        finite_population=finite_population,
    )[0])
    ks = np.arange(0, effective + 1)
    widths = _recall_half_width(ks, np.full(ks.shape, effective), true_positives=true_positives,
                                pool=pool, confidence=confidence)
    return float(binom.pmf(ks, effective, prevalence)[widths <= margin].sum())


def _confirm_quoted_sizes(sizes: dict, **common) -> None:
    """Refuse to return a size the brute-force reference does not confirm.

    At each quoted size, assurance by enumeration must reach the target and agree
    with the fast computation within 1e-9; one size below, it must fall short --
    the size is where the last failure ends. A published label budget crosses
    this boundary, so it is asserted here rather than trusted (DECISIONS 194).

    Raises:
        SizingError: If any quoted size is not confirmed.
    """
    for target, size in sizes.items():
        if size is None:
            continue
        exact = _assurance_by_enumeration(size, **common)
        fast = float(_assurance([size], **common)[0])
        below = _assurance_by_enumeration(size - 1, **common) if size > 1 else 0.0
        if exact < target or abs(exact - fast) > 1e-9 or below >= target:
            raise SizingError(
                f"the size quoted for assurance {target:g} ({size:,}) is not confirmed by "
                f"enumeration: {exact:.6f} at it, {below:.6f} one below, {fast:.6f} from "
                "the fast path. The single-peak shape the fast path relies on may not "
                "hold for these inputs; no size is returned rather than an unconfirmed one."
            )


def _check_common(*, margin: float, confidence: float, design_effect: float) -> None:
    """Range checks shared by both sizings, so they cannot drift apart."""
    if not 0.0 < margin < 1.0:
        raise SizingError(f"margin={margin!r} must be in (0, 1)")
    if confidence != 0.95:
        raise SizingError(
            f"confidence={confidence!r}: only 0.95 is supported, so that a "
            "sample size and the interval it sizes cannot differ in coverage "
            "without anyone noticing."
        )
    if design_effect <= 0.0:
        raise SizingError(f"design_effect={design_effect!r} must be positive")


def labels_for_prevalence(
    *,
    prevalence: float,
    margin: float,
    confidence: float = 0.95,
    design_effect: float = 1.0,
    pool: Optional[float] = None,
) -> LabelPlan:
    """Labels to estimate the unflagged pool's error prevalence to ``+/- margin``.

    Quantity: ``q``, a binomial proportion over the unflagged stratum.
    Propagation: normal approximation at the declared ``q``, inflated by the
    declared design effect, then finite-population corrected against ``pool``.

    Args:
        prevalence: Declared ``q`` to size around.
        margin: Declared half-width, in prevalence units.
        confidence: Coverage. Only 0.95 is supported, so that a sample size and
            a warrant interval cannot silently differ in coverage.
        design_effect: Declared variance inflation of the sampling design
            relative to simple random sampling.
        pool: Unflagged pool size, for the finite-population correction.

    Returns:
        The plan. ``understatement`` is 1.0 by construction: sizing a prevalence
        margin as a prevalence is the question being asked.

    Raises:
        SizingError: On an out-of-range input or an unsupported confidence.
    """
    _check_common(margin=margin, confidence=confidence, design_effect=design_effect)
    if not 0.0 < prevalence < 1.0:
        raise SizingError(f"prevalence={prevalence!r} must be in (0, 1)")

    raw = _binomial_n(prevalence, margin, _Z_95, design_effect)
    corrected = _finite_population(raw, pool)
    declared: dict[str, float] = {
        "prevalence": prevalence,
        "margin": margin,
        "confidence": confidence,
        "design_effect": design_effect,
    }
    if pool is not None:
        declared["pool"] = pool
    return LabelPlan(
        estimand="prevalence",
        margin=margin,
        confidence=confidence,
        labels=int(math.ceil(corrected)),
        basis="normal",
        labels_normal=int(math.ceil(corrected)),
        labels_exact=None,
        labels_infinite_population=int(math.ceil(raw)),
        prevalence_margin=margin,
        derivative=None,
        naive_labels=int(math.ceil(raw)),
        understatement=1.0,
        feasible=True,
        declared_inputs=declared,
        note=(
            "A prevalence sizing, in prevalence units. This is the correct "
            "answer to the question it names and the wrong answer to any "
            "question about recall -- see DECISIONS.md 147."
        ),
    )


def labels_for_recall(
    *,
    sensitivity: RecallSensitivity,
    margin: float,
    confidence: float = 0.95,
    design_effect: float = 1.0,
    finite_population: bool = False,
    basis: str = "exact",
    assurance: float,
) -> LabelPlan:
    """Labels to estimate recall to ``+/- margin``, through ``dR/dq``.

    Quantity: recall on the month's realised traffic. Propagation: the recall
    margin is divided by ``|dR/dq|`` to give the prevalence margin that induces
    it, the prevalence estimate is sized at that margin, and the result is
    finite-population corrected against the unflagged pool. The ratio to a
    direct binomial sizing on recall is therefore ``(dR/dq)^2`` before the
    correction -- the identity ``SPEC.md`` section 6.2 demands a test for, and
    which ``test_sizing_derivative`` asserts.

    **This refuses.** A recall margin can demand more labels than the unflagged
    pool contains, and at that point the honest answer is that the margin is
    unreachable on this traffic, not a number nobody can act on.

    **Sized with assurance** (``DECISIONS.md`` 191). The exact basis returns the
    smallest stable ``n`` at which the margin is *realised* with probability at
    least ``assurance`` over the binomial count of errors in the sample. Before
    191 it sized at the expected count, and the published 1,014-label figure
    realised its margin with probability 0.4882.

    Args:
        sensitivity: From :func:`recall_sensitivity`. Carries ``q``, ``N_u`` and
            the derivative, all from one declared workload.
        margin: Declared half-width wanted on recall.
        assurance: **Declared.** Probability the realised margin meets
            ``margin``; ``sampling.margin_assurance`` unless overridden. Required
            and never defaulted, so no caller inherits one it did not choose.
        confidence: Coverage. Only 0.95 is supported.
        design_effect: Declared variance inflation of the design.
        finite_population: Apply Cochran's correction against the unflagged
            pool. **Off by default, deliberately.**
            :mod:`~controlplane.sampling.estimator` publishes a plain
            Clopper-Pearson interval over the observed ``(k, n)``, which a
            reader can recompute from two integers. A correction inside the
            published bound would narrow it on an argument the reader has to
            take on trust, and -- worse here -- a plan sized *with* the
            correction against an estimate reported *without* it promises a
            margin the estimator will not deliver. That is the defect in
            ``DECISIONS.md`` 147 in miniature: two quantities compared under
            different conventions. Leaving it off also reproduces ``SPEC.md``
            section 6.2's worked figures exactly, which is how the spec's
            arithmetic is regression-tested.
        basis: ``"exact"`` (default) sizes against the Clopper-Pearson interval
            :mod:`~controlplane.sampling.estimator` will actually report, and
            returns the smallest ``n`` from which the margin holds *and keeps
            holding*. ``"normal"`` returns ``SPEC.md`` section 6.2's
            normal-approximation figure, which is what a reader recomputes by
            hand and which **under-delivers**: at the declared workload its 843
            labels realise a half-width of 0.0545 against a 0.05 target. Both
            are reported on every plan, so the gap is visible either way.

    Returns:
        The plan, feasible or refused.

    Raises:
        SizingError: On an out-of-range input, an unsupported confidence, or an
            unknown ``basis``.
    """
    if not 0.0 < assurance < 1.0:
        raise SizingError(f"assurance={assurance!r} must be a probability in (0, 1)")
    if basis not in ("exact", "normal"):
        raise SizingError(
            f"basis={basis!r} is not one of 'exact' or 'normal'. A sample size "
            "has to say which interval it was sized against, because the two "
            "differ by up to 20% at the margins this project quotes."
        )
    _check_common(margin=margin, confidence=confidence, design_effect=design_effect)

    q = sensitivity.unflagged_prevalence
    pool = sensitivity.unflagged_pool
    derivative = abs(sensitivity.derivative)
    declared: dict[str, float] = {
        "margin_recall": margin,
        "confidence": confidence,
        "design_effect": design_effect,
        "recall": sensitivity.recall,
        "flag_rate": sensitivity.flag_rate,
        "monthly_interactions": float(sensitivity.monthly_interactions),
        "base_error_rate": sensitivity.base_error_rate,
        "unflagged_prevalence": q,
        "unflagged_pool": pool,
        "derivative": sensitivity.derivative,
        "assurance": assurance,
    }

    if derivative == 0.0 or q <= 0.0 or q >= 1.0:
        return LabelPlan(
            estimand="recall",
            margin=margin,
            confidence=confidence,
            labels=0,
            basis=basis,
            labels_normal=0,
            labels_exact=None,
            labels_infinite_population=0,
            prevalence_margin=None,
            derivative=sensitivity.derivative,
            naive_labels=0,
            understatement=math.inf,
            feasible=False,
            refusal_reason=(
                "no prevalence margin induces a recall margin at this "
                "operating point: dR/dq is zero, or the unflagged pool holds "
                "either no errors or nothing else. Recall is not estimable "
                "from any number of labels here."
            ),
            declared_inputs=declared,
        )

    prevalence_margin = margin / derivative
    raw = _binomial_n(q, prevalence_margin, _Z_95, design_effect)
    corrected = _finite_population(raw, pool if finite_population else None)
    naive = _binomial_n(sensitivity.recall, margin, _Z_95, design_effect)
    normal_labels = int(math.ceil(corrected))

    common = dict(
        prevalence=q,
        true_positives=sensitivity.confirmed_errors,
        pool=pool,
        margin=margin,
        design_effect=design_effect,
        finite_population=finite_population,
        confidence=confidence,
    )
    sizes = _labels_at_assurances((*ASSURANCE_LADDER, assurance), **common)
    _confirm_quoted_sizes(sizes, **common)
    exact_labels = sizes[assurance]
    at_expected = _labels_for_exact_margin(**common)
    ladder = tuple((rung, sizes[rung]) for rung in ASSURANCE_LADDER)
    chosen = exact_labels if basis == "exact" else normal_labels

    def assurance_of(n: Optional[int]) -> Optional[float]:
        if not n:
            return None
        return float(_assurance([n], **common)[0])
    understatement = (chosen / naive) if (naive > 0 and chosen) else math.inf

    def build(feasible: bool, reason: str = "", note: str = "") -> LabelPlan:
        return LabelPlan(
            estimand="recall",
            margin=margin,
            confidence=confidence,
            labels=int(chosen or 0),
            basis=basis,
            labels_normal=normal_labels,
            labels_exact=exact_labels,
            labels_infinite_population=int(math.ceil(raw)),
            prevalence_margin=prevalence_margin,
            derivative=sensitivity.derivative,
            naive_labels=int(math.ceil(naive)),
            understatement=understatement,
            feasible=feasible,
            refusal_reason=reason,
            declared_inputs=declared,
            note=note,
            assurance=assurance,
            assurance_at_labels=assurance_of(chosen),
            labels_at_expected_count=at_expected,
            assurance_at_expected_count=assurance_of(at_expected),
            sizes_by_assurance=ladder,
        )

    if basis == "exact" and exact_labels is None:
        return build(
            False,
            reason=(
                f"no sample of the {pool:,.0f}-item unflagged pool holds recall "
                f"to +/-{margin:g} with probability {assurance:g} under the exact "
                f"interval the estimator reports. The normal approximation would "
                f"have quoted "
                f"{normal_labels:,}, which is what makes this worth refusing "
                f"rather than rounding up: the closed form returns a number for "
                f"a margin no sample achieves."
            ),
        )

    if chosen and chosen > pool:
        return build(
            False,
            reason=(
                f"recall to +/-{margin:g} needs {chosen:,} labels from an "
                f"unflagged pool of {pool:,.0f}. The margin is not reachable on "
                f"this traffic at this operating point. Reaching it requires a "
                f"wider margin, more traffic, or an operating point whose "
                f"|dR/dq| is smaller than {derivative:.2f}."
            ),
        )

    return build(
        True,
        note=(
            "A planning figure over declared inputs. q is assumed, not "
            "measured -- every sample size is, because it is computed before "
            "the measurement it sizes. estimator.py reports the realised "
            "margin against this one once the labels land."
        ),
    )
