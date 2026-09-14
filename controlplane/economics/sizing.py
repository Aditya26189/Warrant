"""The price list: what it costs to keep a warrant true.

The third clause of this project's pitch, and the last one without code. Line 9
of ``config.yaml`` has read *"Every economic figure in every document is
computed from this block by controlplane/economics/sizing.py. Nothing is typed
by hand"* since the first commit, and this module did not exist
(``DECISIONS.md`` 096, 099, now 146).

Two questions, and they face opposite directions.

**:func:`monitoring_plan` is the customer one.** You certified a detector at a
false-positive budget. Keeping that claim true means re-testing it, and
re-testing costs labels. Given the breach you want to be able to catch and the
probability of catching it, this says how many clean negatives one recheck
needs, how many items you must label to get them, and what a year of rechecks
costs at each of several cadences -- in labels, and in the chance that the year
revokes a detector that kept its promise (``DECISIONS.md`` 183).

**:func:`workload_price_list` is ours.** The declared workload in
``config.yaml`` is one scenario — invariant 6 — and every economic figure this
project publishes has to come from that block rather than from whichever
numbers were to hand.

Three properties hold throughout, and each exists because its absence is a way
to be confidently wrong:

**Arithmetic is exact; its premises are declared.** Nothing here is a sample
estimate, so nothing here carries an interval. But a plan built on a negative
share of 0.9 when the truth is 0.6 is wrong by half, so every figure names the
inputs it was handed. This is *yield is exact, rate is estimated* one level up,
and it reuses the idiom :mod:`controlplane.economics.review` already set.

**No cadence is invented.** How often to recheck depends on how fast your input
distribution moves, which is exactly what you do not know — it is why the drift
machinery exists at all. A default of "monthly" would be a hardcoded constant
with no evidence behind it. So this prices a ladder and the person chooses.

**It refuses.** When no achievable sample detects the breach at the budget and
confidence asked for, that is the answer. A price list that always returns a
price will one day quote an impossible one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Optional

__all__ = [
    "CadenceOption",
    "MonitoringPlan",
    "DEFAULT_CADENCES",
    "POWER_LADDER",
    "critical_counts",
    "false_revocation_in_year",
    "negatives_for_detection",
    "negatives_for_power",
    "monitoring_plan",
    "revocation_probability",
    "workload_price_list",
]

#: Cadences priced by default. A presentation choice, not a measurement knob:
#: the four intervals a monitoring programme is actually scheduled on. None is
#: recommended over another, and the module deliberately declines to.
DEFAULT_CADENCES: tuple[tuple[str, int], ...] = (
    ("weekly", 52),
    ("fortnightly", 26),
    ("monthly", 12),
    ("quarterly", 4),
)

#: Above this the answer is "not with labelling", and saying so beats returning
#: a number nobody will ever collect.
MAX_NEGATIVES = 2_000_000

#: How far past a candidate ``n`` detection must keep holding before that ``n``
#: is quoted. Measured, not guessed: from each stable threshold up to twelve
#: times it, there is no ``n`` at which detection fails (``DECISIONS.md`` 146).
STABILITY_HORIZON = 12

#: Powers the plan always prints a sample size for, so the declared power is read
#: beside its neighbours rather than alone (``DECISIONS.md`` 183). Presentation,
#: like :data:`DEFAULT_CADENCES`: the year is priced at the declared power, and
#: 0.5 is on the ladder because it is what this module quoted before 183.
POWER_LADDER: tuple[float, ...] = (0.5, 0.8, 0.9)


def _lower_bound_at(n: int, k: int, alpha: float) -> float:
    """One-sided Clopper-Pearson lower bound for ``k`` of ``n``.

    The same bound revocation turns on in
    :mod:`controlplane.intake.recheck`, so a sample size computed here and a
    verdict reached there mean the same thing.
    """
    from scipy.stats import beta

    if k <= 0:
        return 0.0
    if k >= n:
        return float(beta.ppf(alpha, k, 1))
    return float(beta.ppf(alpha, k, n - k + 1))


def _detects(n: int, breach_rate: float, budget: float, alpha: float) -> bool:
    """Would an observed ``breach_rate`` on ``n`` negatives establish a breach?"""
    k = int(round(breach_rate * n))
    return bool(k) and _lower_bound_at(n, k, alpha) > budget


def _detect_mask(lo: int, hi: int, breach_rate: float, budget: float, alpha: float):
    """:func:`_detects` for every ``n`` in ``[lo, hi]``, in one call.

    The search below asks this question tens of thousands of times, and one
    ``beta.ppf`` per question took 1.6 seconds per sample size — enough to make
    a CLI feel broken and a test suite slower than the thing it tests. The
    vectorised form answers the same question in milliseconds. ``np.rint``
    rounds half to even, which is what :func:`round` does, so the two agree
    element for element rather than only usually.
    """
    import numpy as np
    from scipy.stats import beta

    ns = np.arange(lo, hi + 1, dtype=np.int64)
    ks = np.rint(breach_rate * ns).astype(np.int64)
    live = ks > 0
    bounds = np.zeros(ns.shape, dtype=float)
    if live.any():
        bounds[live] = beta.ppf(alpha, ks[live], ns[live] - ks[live] + 1)
    return live & (bounds > budget)


def negatives_for_detection(
    breach_rate: float,
    budget: float,
    alpha: float,
    *,
    horizon: int = STABILITY_HORIZON,
    cap: int = MAX_NEGATIVES,
) -> Optional[int]:
    """Clean negatives needed before ``breach_rate`` establishes a breach.

    Quantity: the clean negatives needed before an observed ``breach_rate``
    **establishes** that the true rate exceeds ``budget``.
    Propagation: one-sided Clopper-Pearson lower bound at each achievable
    integer count, searched exactly rather than inverted in closed form --
    the predicate is not monotone in ``n`` because the count is
    ``round(breach_rate * n)``, so a closed form would return a value at
    which detection does not hold.

    **Not a sample size to plan from** (``DECISIONS.md`` 183). "Detects" here
    means an observed rate *equal to* the breach revokes, and at a true breach
    the observed rate falls short about half the time: the sizes this returns
    have power near 0.49. :func:`monitoring_plan` and ``recheck``'s hint size
    at a declared power with :func:`negatives_for_power`. This stays because
    the stable-threshold search below is the one that function reuses, and its
    tests pin the sawtooth that makes that search necessary.

    **The smallest ``n`` from which detection holds at ``n`` and at every larger
    ``n``** — not the first ``n`` at which it happens to hold. The distinction is
    the whole point of this function and it is worth 20% of the answer.

    Detection is *not* monotone in ``n``. The observed count is
    ``round(breach_rate * n)``, so the integer jumps and the bound at ``(n, k)``
    does not improve with every sample added. At a 0.05 budget catching 0.075,
    detection first holds at ``n = 234`` and then fails again at 236 through 246
    and at 252. Quoting 234 to somebody who then collects 240 negatives tells
    them they are covered when they are not. The stable answer is 287.

    Args:
        breach_rate: The false-positive rate you want to be able to catch.
            Must exceed ``budget`` — catching a rate at or below the promise is
            not a thing that can be established.
        budget: The certified false-positive budget.
        alpha: One-sided confidence level, the same one certification used.
        horizon: How far past a candidate detection must keep holding. See
            :data:`STABILITY_HORIZON`.
        cap: Give up past this many negatives.

    Returns:
        The count, or ``None`` when no sample up to ``cap`` detects it — which
        is an answer and is reported as one.

    Raises:
        ValueError: If the rates are not ordered, or are outside ``(0, 1)``.
    """
    if not 0.0 < budget < 1.0:
        raise ValueError(f"budget={budget!r} is not a rate in (0, 1)")
    if not 0.0 < breach_rate < 1.0:
        raise ValueError(f"breach_rate={breach_rate!r} is not a rate in (0, 1)")
    if breach_rate <= budget:
        raise ValueError(
            f"breach_rate={breach_rate} does not exceed budget={budget}. No "
            "sample can establish that a rate at or below the promise breaks it."
        )
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha={alpha!r} is not in (0, 1)")

    # 0. Ask the top of the range first. Detection at large n is all-or-nothing
    #    -- once the bound converges it holds for every larger n, which
    #    DECISIONS 146 checked rather than assumed -- so a window just below the
    #    cap failing means no achievable sample detects this. One vectorised
    #    call, and it turns the refusal path from 13.8 seconds of fruitless
    #    climbing into milliseconds. A tool that takes fourteen seconds to say
    #    no reads as a tool that is broken.
    if not _detect_mask(max(1, cap - 1000), cap, breach_rate, budget, alpha).all():
        return None

    # 1. Grow until detection holds across a stretch, which puts us at or above
    #    the stable threshold rather than inside one of the holes below it.
    upper = 10
    while upper <= cap:
        span = max(50, upper // 4)
        if _detect_mask(
            upper, min(upper + span, cap), breach_rate, budget, alpha
        ).all():
            break
        upper = int(upper * 1.2) + 1
    else:
        return None

    # 2. Walk back down to the last n that fails. Everything above it holds, so
    #    that failure plus one is the smallest n worth quoting.
    below = _detect_mask(1, upper, breach_rate, budget, alpha)
    failures = (~below).nonzero()[0]
    stable = int(failures[-1]) + 2 if failures.size else 1

    # 3. Confirm across the horizon. Cheap now, and it is the property being
    #    sold: not "detection happens here" but "detection happens from here on".
    ceiling = min(stable * horizon, cap)
    if not _detect_mask(stable, ceiling, breach_rate, budget, alpha).all():
        # pragma: no cover - would mean the convergence measured in 146 is wrong
        return None
    return stable


def critical_counts(ns, budget: float, alpha: float):
    """The fewest false positives that revoke, for every sample size in ``ns``.

    ``k*(n)`` is the smallest count whose one-sided Clopper-Pearson lower bound
    at ``alpha`` exceeds ``budget`` -- the rule
    :func:`controlplane.intake.recheck.recheck_items` revokes on. Where no count
    up to ``n`` clears, ``k*(n)`` is ``n + 1``, so every probability computed
    from it is zero rather than undefined.

    The candidate comes from the binomial tail (the bound clears the budget
    exactly when ``P(Bin(n, budget) >= k) < alpha``), then is corrected against
    ``beta.ppf`` itself, so a disagreement between the two at a floating-point
    boundary is settled in favour of the function a recheck actually calls.
    """
    import numpy as np
    from scipy.stats import beta, binom

    ns = np.asarray(ns, dtype=np.int64)
    ks = np.asarray(binom.isf(alpha, ns, budget), dtype=np.int64) + 1
    ks = np.clip(ks, 1, ns + 1)

    def clears(k):
        live = (k >= 1) & (k <= ns)
        out = np.zeros(ns.shape, dtype=bool)
        if live.any():
            out[live] = beta.ppf(alpha, k[live], ns[live] - k[live] + 1) > budget
        return out

    for _ in range(16):
        up = (ks <= ns) & ~clears(ks)
        down = (ks > 1) & clears(ks - 1)
        if not (up.any() or down.any()):
            return ks
        ks = ks + up.astype(np.int64) - down.astype(np.int64)
    raise AssertionError(  # pragma: no cover - the tail and the bound are duals
        "critical counts did not settle; the binomial tail and the Clopper-Pearson "
        "bound disagree by more than a floating-point boundary"
    )


def revocation_probability(ns, true_rate: float, budget: float, alpha: float):
    """Chance one recheck of ``n`` clean negatives revokes, at a true rate.

    Quantity: ``P(Bin(n, true_rate) >= k*(n))``, the probability that a recheck
    revokes. At ``true_rate`` above the budget it is the **power**; at the
    budget it is the **false-revocation rate**, and since the tail increases
    with the rate, that is the worst case over every rate the warrant promised.
    Propagation: exact binomial tail at the exact critical count of
    :func:`critical_counts`; no normal approximation (``DECISIONS.md`` 183).
    """
    import numpy as np
    from scipy.stats import binom

    ns = np.asarray(ns, dtype=np.int64)
    return binom.sf(critical_counts(ns, budget, alpha) - 1, ns, true_rate)


def _power_mask(lo: int, hi: int, breach_rate: float, budget: float, alpha: float, power: float):
    """Whether each ``n`` in ``[lo, hi]`` reaches ``power`` against the breach."""
    import numpy as np

    ns = np.arange(lo, hi + 1, dtype=np.int64)
    return revocation_probability(ns, breach_rate, budget, alpha) >= power


def negatives_for_power(
    breach_rate: float,
    budget: float,
    alpha: float,
    power: float,
    *,
    horizon: int = STABILITY_HORIZON,
    cap: int = MAX_NEGATIVES,
) -> Optional[int]:
    """Clean negatives one recheck needs to catch a true breach with ``power``.

    Quantity: the smallest ``n`` from which a recheck revokes, with probability
    at least ``power``, a detector whose true false-positive rate is
    ``breach_rate``, at that ``n`` and every larger one up to ``horizon`` times
    it. Propagation: exact binomial power at the exact critical count, searched
    over integer ``n`` -- power is a sawtooth in ``n`` for the same reason
    detection is (:func:`negatives_for_detection`), so the stable-threshold
    rule of ``DECISIONS.md`` 146 applies unchanged.

    **Why this and not** :func:`negatives_for_detection`. That function asks
    whether an *observed* rate equal to the breach would revoke. At a *true*
    breach the observed count is binomial and clears the critical count about
    half the time: the sizes it quotes (287, 86, 1501 in 146's table) have power
    0.489, 0.495 and 0.488 (``DECISIONS.md`` 183).

    Args:
        breach_rate: The true false-positive rate to catch. Must exceed ``budget``.
        budget: The certified false-positive budget.
        alpha: One-sided level, the same one certification and recheck use.
        power: Probability of revoking at ``breach_rate``, in ``(0, 1)``.
        horizon: How far past a candidate power must keep holding.
        cap: Give up past this many negatives.

    Returns:
        The count, or ``None`` when no sample up to ``cap`` reaches the power.

    Raises:
        ValueError: If the rates are not ordered or not in ``(0, 1)``, or
            ``power`` is not in ``(0, 1)``.
    """
    if not 0.0 < power < 1.0:
        raise ValueError(f"power={power!r} is not a probability in (0, 1)")
    # The rate checks are the same questions as detection's; ask them once.
    if not 0.0 < budget < 1.0:
        raise ValueError(f"budget={budget!r} is not a rate in (0, 1)")
    if not 0.0 < breach_rate < 1.0:
        raise ValueError(f"breach_rate={breach_rate!r} is not a rate in (0, 1)")
    if breach_rate <= budget:
        raise ValueError(
            f"breach_rate={breach_rate} does not exceed budget={budget}. No "
            "sample can establish that a rate at or below the promise breaks it."
        )
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha={alpha!r} is not in (0, 1)")

    # Same three steps as negatives_for_detection, on power instead of on one
    # observed count: ask the top of the range, grow until a stretch holds,
    # walk back to the last failure, then confirm across the horizon.
    if not _power_mask(max(1, cap - 1000), cap, breach_rate, budget, alpha, power).all():
        return None

    upper = 10
    while upper <= cap:
        span = max(50, upper // 4)
        if _power_mask(upper, min(upper + span, cap), breach_rate, budget, alpha, power).all():
            break
        upper = int(upper * 1.2) + 1
    else:
        return None

    below = _power_mask(1, upper, breach_rate, budget, alpha, power)
    failures = (~below).nonzero()[0]
    stable = int(failures[-1]) + 2 if failures.size else 1

    ceiling = min(stable * horizon, cap)
    if not _power_mask(stable, ceiling, breach_rate, budget, alpha, power).all():
        # pragma: no cover - power converges to 1 above the budget
        return None
    return stable


def false_revocation_in_year(per_recheck: float, rechecks: int) -> float:
    """Chance at least one of a year's rechecks revokes a warrant that held.

    Quantity: ``1 - (1 - f)^K`` for ``K`` rechecks each revoking a detector
    exactly at its budget with probability ``f``. Propagation: exact under
    independent samples per recheck; a programme that re-labels overlapping
    items has correlated rechecks and a smaller figure, which this does not
    model. It is a statement about the schedule, not about any one recheck,
    and it is what 143's cry-wolf argument looks like at a cadence.
    """
    if not 0.0 <= per_recheck <= 1.0:
        raise ValueError(f"per_recheck={per_recheck!r} is not a probability")
    if rechecks < 0:
        raise ValueError(f"rechecks={rechecks!r} is negative")
    return 1.0 - (1.0 - per_recheck) ** rechecks


def smallest_detectable_at(n_negatives: int, budget: float, alpha: float) -> Optional[float]:
    """The smallest observed rate that would revoke, at this ``n``.

    Quantity: the least observed false-positive rate whose one-sided
    Clopper-Pearson lower bound exceeds the budget at this ``n``.
    Propagation: exact, by search -- the bound is evaluated at each
    achievable integer count and the first crossing returned. No normal
    approximation is involved, which matters because the counts here are
    small enough that one would be wrong in the unsafe direction.

    The plan's own sanity check: having quoted a sample size for a breach of a
    given size, this says what that sample would *actually* catch, which is at
    least as good and usually better. Mirrors
    :func:`controlplane.intake.recheck.smallest_detectable_breach` so that a
    planned floor and a measured floor are the same quantity.
    """
    import numpy as np
    from scipy.stats import beta

    ks = np.arange(1, n_negatives + 1, dtype=np.int64)
    bounds = beta.ppf(alpha, ks, n_negatives - ks + 1)
    clears = (bounds > budget).nonzero()[0]
    return float(ks[clears[0]]) / n_negatives if clears.size else None


@dataclass(frozen=True)
class CadenceOption:
    """One row of the ladder: a schedule, and what a year of it costs."""

    name: str
    rechecks_per_year: int
    labels_per_year: int
    #: ``None`` when no labelling rate was declared. Not zero, and not a guess.
    reviewer_hours_per_year: Optional[float] = None
    cost_per_year: Optional[float] = None
    currency: str = ""
    #: Chance at least one of the year's rechecks revokes a detector sitting
    #: exactly at its budget (:func:`false_revocation_in_year`, DECISIONS 183).
    false_revocation_in_year: Optional[float] = None

    def render(self) -> str:
        money = (
            f"  {self.currency}{self.cost_per_year:,.0f}"
            if self.cost_per_year is not None
            else ""
        )
        hours = (
            f"  {self.reviewer_hours_per_year:,.0f} h"
            if self.reviewer_hours_per_year is not None
            else ""
        )
        false_alarm = (
            f"   false revocation {self.false_revocation_in_year:.2f}"
            if self.false_revocation_in_year is not None
            else ""
        )
        return (
            f"  {self.name:<13} {self.rechecks_per_year:>3} rechecks   "
            f"{self.labels_per_year:>9,} labels{false_alarm}{hours}{money}"
        )


@dataclass(frozen=True)
class MonitoringPlan:
    """What keeping one warrant true costs, and on what premises.

    Every figure is exact arithmetic. None of it is measured, so
    ``declared_inputs`` is not decoration: it is the list of things that have to
    be right for the arithmetic to mean anything.
    """

    budget: float
    alpha: float
    breach_rate: float
    feasible: bool
    #: The declared probability of catching a true breach, which sizes the plan.
    power: Optional[float] = None
    negatives_per_recheck: Optional[int] = None
    items_per_recheck: Optional[int] = None
    detection_floor: Optional[float] = None
    #: Exact power at the quoted size. At least ``power``, and usually a little
    #: above it, because sizes are integers.
    power_at_breach: Optional[float] = None
    #: Chance one recheck of the quoted size revokes a detector exactly at its
    #: budget. At most ``alpha``, and below it, because counts are integers.
    false_revocation_per_recheck: Optional[float] = None
    #: ``(power, negatives)`` for each rung of :data:`POWER_LADDER`; ``None``
    #: where no sample up to the cap reaches that power.
    sizes_by_power: tuple[tuple[float, Optional[int]], ...] = ()
    cadences: tuple[CadenceOption, ...] = ()
    declared_inputs: Mapping[str, float] = field(default_factory=dict)
    refusal_reason: str = ""

    def to_payload(self) -> dict:
        """The record. Flat, so a spreadsheet can read it."""
        return {
            "kind": "monitoring_plan",
            "feasible": self.feasible,
            "budget": self.budget,
            "alpha": self.alpha,
            "breach_rate": self.breach_rate,
            "power": self.power,
            "negatives_per_recheck": self.negatives_per_recheck,
            "items_per_recheck": self.items_per_recheck,
            "detection_floor": self.detection_floor,
            "power_at_breach": self.power_at_breach,
            "false_revocation_per_recheck": self.false_revocation_per_recheck,
            "sizes_by_power": [
                {"power": rung, "negatives_per_recheck": size}
                for rung, size in self.sizes_by_power
            ],
            "declared_inputs": dict(self.declared_inputs),
            "refusal_reason": self.refusal_reason,
            "cadences": [
                {
                    "name": option.name,
                    "rechecks_per_year": option.rechecks_per_year,
                    "labels_per_year": option.labels_per_year,
                    "false_revocation_in_year": option.false_revocation_in_year,
                    "reviewer_hours_per_year": option.reviewer_hours_per_year,
                    "cost_per_year": option.cost_per_year,
                    "currency": option.currency,
                }
                for option in self.cadences
            ],
            "exactness": (
                "EXACT arithmetic over DECLARED inputs. Not a measurement and "
                "not an estimate: no interval is carried because none is owed. "
                "Wrong declared inputs make every figure here wrong in "
                "proportion, which is why they are listed."
            ),
        }


def monitoring_plan(
    *,
    budget: float,
    breach_rate: float,
    alpha: float,
    power: float,
    negative_share: float,
    minutes_per_label: Optional[float] = None,
    cost_per_hour: Optional[float] = None,
    currency: str = "",
    cadences: tuple[tuple[str, int], ...] = DEFAULT_CADENCES,
) -> MonitoringPlan:
    """Price keeping one warrant true.

    Quantity: the clean negatives one recheck needs to revoke, with probability
    ``power``, a detector whose true false-positive rate is ``breach_rate``;
    the items that must be labelled to get them; and, per cadence, the chance a
    year of rechecks revokes a detector that kept its promise. Propagation:
    exact binomial power at the exact Clopper-Pearson critical count
    (:func:`negatives_for_power`), divided by the declared negative share; the
    year figure is :func:`false_revocation_in_year` under independent samples.

    Args:
        budget: **Declared.** The false-positive budget the detector was
            certified at.
        breach_rate: **Declared.** The true rate you want to be able to catch.
            Must exceed ``budget``.
        alpha: **Declared.** One-sided confidence, matching certification.
        power: **Declared.** Probability one recheck catches a true
            ``breach_rate``. ``validation.recheck_power`` unless overridden;
            required here so no caller inherits a power it did not choose.
        negative_share: **Declared.** The fraction of your traffic that is
            truly negative. It converts "negatives needed" into "items to
            label", and it is the input most often wrong: a plan built on 0.9
            when the truth is 0.6 understates the labelling by half.
        minutes_per_label: **Declared**, optional. Omit and the plan returns
            counts without hours or money rather than inventing a rate.
        cost_per_hour: **Declared**, optional. Same.
        currency: Label only, for rendering.
        cadences: The ladder to price.

    Returns:
        A plan, or a refusal carrying the reason and what would change it.

    Raises:
        ValueError: If ``negative_share`` is not in ``(0, 1]``, or the rates
            are malformed. The rate checks happen in
            :func:`negatives_for_detection`.
    """
    if not 0.0 < negative_share <= 1.0:
        raise ValueError(
            f"negative_share={negative_share!r} is not in (0, 1]. It is the "
            "fraction of traffic that is truly negative; a detector with no "
            "negatives in its traffic has no false-positive rate to keep."
        )

    declared: dict[str, float] = {
        "budget": budget,
        "breach_rate": breach_rate,
        "alpha": alpha,
        "power": power,
        "negative_share": negative_share,
    }
    if minutes_per_label is not None:
        declared["minutes_per_label"] = minutes_per_label
    if cost_per_hour is not None:
        declared["cost_per_hour"] = cost_per_hour

    negatives = negatives_for_power(breach_rate, budget, alpha, power)
    ladder = tuple(
        (rung, negatives if rung == power else negatives_for_power(breach_rate, budget, alpha, rung))
        for rung in POWER_LADDER
    )
    if negatives is None:
        return MonitoringPlan(
            budget=budget,
            alpha=alpha,
            breach_rate=breach_rate,
            feasible=False,
            power=power,
            sizes_by_power=ladder,
            declared_inputs=declared,
            refusal_reason=(
                f"no sample up to {MAX_NEGATIVES:,} clean negatives catches a "
                f"true rate of {breach_rate:.4g} against a {budget:.4g} budget "
                f"with probability {power:.2g} at alpha={alpha:.3g}. The gap "
                "between the breach and the budget is too small to resolve by "
                "labelling. Widen the breach you are willing to catch, loosen "
                "alpha, lower the power, or certify at a tighter budget so that "
                "the same absolute drift is a larger relative one."
            ),
        )

    import numpy as np

    items = math.ceil(negatives / negative_share)
    floor = smallest_detectable_at(negatives, budget, alpha)
    at_n = np.array([negatives])
    achieved_power = float(revocation_probability(at_n, breach_rate, budget, alpha)[0])
    per_recheck_false = float(revocation_probability(at_n, budget, budget, alpha)[0])

    priced: list[CadenceOption] = []
    for name, per_year in cadences:
        labels = items * per_year
        hours = (
            labels * minutes_per_label / 60.0 if minutes_per_label is not None else None
        )
        cost = hours * cost_per_hour if hours is not None and cost_per_hour is not None else None
        priced.append(
            CadenceOption(
                name=name,
                rechecks_per_year=per_year,
                labels_per_year=labels,
                reviewer_hours_per_year=hours,
                cost_per_year=cost,
                currency=currency,
                false_revocation_in_year=false_revocation_in_year(per_recheck_false, per_year),
            )
        )

    return MonitoringPlan(
        budget=budget,
        alpha=alpha,
        breach_rate=breach_rate,
        feasible=True,
        power=power,
        negatives_per_recheck=negatives,
        items_per_recheck=items,
        detection_floor=floor,
        power_at_breach=achieved_power,
        false_revocation_per_recheck=per_recheck_false,
        sizes_by_power=ladder,
        cadences=tuple(priced),
        declared_inputs=declared,
    )


def workload_price_list(workload: Mapping[str, float]) -> dict[str, object]:
    """The declared workload's economics, from the one block in ``config.yaml``.

    Invariant 6: every economic figure this project publishes comes from a
    single declared scenario. Taking a flag rate from one and a base rate from
    another is silently wrong and survives a reviewer with a calculator only
    until they use it.

    **``q`` and ``dR/dq`` are absent here and live in**
    :func:`controlplane.sampling.planning.recall_sensitivity`. ``q`` is the
    prevalence of errors in the *unflagged* pool: an estimand, measured with
    labels, not a property of a workload block. It is still *declared* for
    planning purposes -- every sample size is computed before the measurement
    it sizes, so it is always conditioned on an assumed value -- but it is
    declared there, labelled as declared, and reported against the realised
    value once labels land.

    An earlier version of this docstring named
    :func:`controlplane.economics.review.recall_sample_size` as what
    operationalises it honestly. That was wrong: the function propagated
    through no derivative at all and was low by 6x to 13x as a label budget.
    ``DECISIONS.md`` 147.

    Args:
        workload: The ``workload`` block: ``monthly_interactions``,
            ``base_error_rate``, ``measured_tpr``, ``measured_fpr``,
            ``review_minutes_per_item``, ``reviewer_monthly_cost_inr``,
            ``reviewer_productive_hours``.

    Returns:
        ``cost_per_review``, ``flag_rate`` and the review-volume decomposition
        from :func:`controlplane.economics.review.review_volume`.

    Raises:
        KeyError: If the block is missing a field, rather than defaulting one.
            A workload with a guessed volume is not the declared workload.
    """
    from .review import review_volume

    base = float(workload["base_error_rate"])
    tpr = float(workload["measured_tpr"])
    fpr = float(workload["measured_fpr"])

    # The flag rate implied by the measured operating point *at this declared
    # base rate*. Not the flag rate measured on the eval set, which describes
    # the eval set's class balance and not production traffic.
    flag_rate = base * tpr + (1.0 - base) * fpr

    hourly = float(workload["reviewer_monthly_cost_inr"]) / float(
        workload["reviewer_productive_hours"]
    )
    cost_per_review = hourly * float(workload["review_minutes_per_item"]) / 60.0

    volume = review_volume(
        flag_rate=flag_rate,
        recall=tpr,
        base_error_rate=base,
        monthly_interactions=int(workload["monthly_interactions"]),
        operating_point_id=str(workload.get("name", "")),
    )
    return {
        "flag_rate": flag_rate,
        "cost_per_review": cost_per_review,
        "reviewer_cost_per_hour": hourly,
        "monthly_review_cost": volume["flagged"].value * cost_per_review,
        "volume": volume,
    }
