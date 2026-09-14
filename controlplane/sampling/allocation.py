"""Where to spend the labels: proportional in month one, Neyman after.

``SPEC.md`` §6.3. Two allocation rules over the score bands of the unflagged
stratum, and one measurement that decides whether the second was worth it.

    proportional   n_h  ~  W_h
    Neyman         n_h  ~  W_h * sqrt(q_h (1 - q_h))

**Month one cannot run Neyman**, and this is not a scheduling detail. Neyman
needs the per-band prevalences ``q_h``, which are exactly what the first month's
labels are bought to discover. Any ``q_h`` available before that month is an
assumption, and an allocation built on assumed variances concentrates labels
wherever the assumption said to -- which is the one place the resulting estimate
cannot correct. So the first warrant is paid for at full simple-random-sampling
price, and :func:`neyman` refuses to run without measured inputs.

**Expect about 1.5x, and treat 2x as a good outcome.** Neyman's variance goes as
``[sum_h W_h sqrt(q_h(1-q_h))]^2``, and the square root is concave, so a large
band with a small but non-zero prevalence dominates the sum *because* it is
large. The design effect is measured here from the observed band structure
rather than declared, because ``config.yaml`` carries 0.67 as an expectation and
an expectation quoted as a measurement is the thing this project exists to stop.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence

__all__ = [
    "Allocation",
    "AllocationError",
    "design_effect",
    "neyman",
    "proportional",
]


class AllocationError(ValueError):
    """An allocation was requested that the available evidence cannot support."""


@dataclass(frozen=True)
class Allocation:
    """How many labels each band gets, and what the split is expected to buy.

    Attributes:
        rule: ``"proportional"`` or ``"neyman"``.
        total: Labels allocated in total.
        per_band: Band name to label count. Sums to ``total``.
        weights: Band name to ``W_h``, the band's share of the unflagged pool.
        design_effect: ``Var(this design) / Var(SRS at the same total)``, when
            it can be computed. Below 1 means the design buys precision.
            ``None`` for proportional without measured prevalences, where there
            is nothing yet to compute it from.
        measured_inputs: Per-band prevalences used, when the rule needed them.
        note: What the allocation assumes.
    """

    rule: str
    total: int
    per_band: dict[str, int]
    weights: dict[str, float]
    design_effect: Optional[float] = None
    measured_inputs: dict[str, float] = field(default_factory=dict)
    note: str = ""

    def render(self) -> str:
        """The split, one band per line, largest first."""
        lines = [f"{self.rule} allocation of {self.total:,} labels"]
        for name, count in sorted(
            self.per_band.items(), key=lambda kv: -kv[1]
        ):
            share = self.weights.get(name, 0.0)
            lines.append(
                f"    {name:<16} {count:>8,}  (W_h={share:.4f})"
            )
        if self.design_effect is not None:
            lines.append(f"    design effect    {self.design_effect:>8.4f}")
        return "\n".join(lines)


def _largest_remainder(shares: Sequence[float], total: int) -> list[int]:
    """Apportion ``total`` across ``shares`` so the counts sum to ``total``.

    Rounding each share independently loses or gains items against the total,
    and a sampling plan whose parts do not sum to its whole is a plan somebody
    will reconcile by hand at the worst moment. Largest-remainder is the
    standard apportionment for this and is deterministic, which matters because
    every artifact in this project has to be reproducible bit for bit.
    """
    if total <= 0:
        return [0] * len(shares)
    raw = [s * total for s in shares]
    floors = [int(math.floor(x)) for x in raw]
    shortfall = total - sum(floors)
    if shortfall:
        order = sorted(
            range(len(raw)), key=lambda i: (-(raw[i] - floors[i]), i)
        )
        for i in order[:shortfall]:
            floors[i] += 1
    return floors


def _weights(populations: Mapping[str, int]) -> dict[str, float]:
    total = sum(populations.values())
    if total <= 0:
        raise AllocationError("the unflagged pool is empty; there is nothing to allocate")
    return {name: pop / total for name, pop in populations.items()}


def proportional(*, populations: Mapping[str, int], total: int) -> Allocation:
    """Split ``total`` labels in proportion to each band's share of the pool.

    The month-one rule. It needs nothing but the band sizes, which are known
    from the traffic itself, and it has one property Neyman does not: under
    equal sampling fractions the stratified estimator collapses to the pooled
    proportion, so :mod:`~controlplane.sampling.estimator` can give it an
    **exact** Clopper-Pearson interval. Neyman buys precision by giving that up.

    Args:
        populations: Band name to unflagged items in that band this month.
        total: Labels to allocate.

    Returns:
        The allocation. ``design_effect`` is ``None``: with no measured ``q_h``
        there is nothing to compare against, and returning 1.0 would assert a
        measurement that was not made.

    Raises:
        AllocationError: If the pool is empty or ``total`` is negative.
    """
    if total < 0:
        raise AllocationError(f"total={total!r} cannot be negative")
    weights = _weights(populations)
    names = list(populations)
    counts = _largest_remainder([weights[n] for n in names], total)
    return Allocation(
        rule="proportional",
        total=total,
        per_band={n: c for n, c in zip(names, counts, strict=True)},
        weights=weights,
        design_effect=None,
        note=(
            "Month one. Needs no measured prevalence, costs full SRS price, and "
            "is the only allocation for which this project can report an exact "
            "interval. SPEC.md 6.3."
        ),
    )


def neyman(
    *,
    populations: Mapping[str, int],
    prevalences: Mapping[str, float],
    total: int,
) -> Allocation:
    """Split ``total`` labels toward the bands carrying the variance.

    Args:
        populations: Band name to unflagged items in that band this month.
        prevalences: Band name to **measured** ``q_h`` from a previous month's
            labels. Not declared, not assumed, not borrowed from another
            workload.
        total: Labels to allocate.

    Returns:
        The allocation, with the design effect measured against simple random
        sampling at the same total.

    Raises:
        AllocationError: If a band has no measured prevalence, if a prevalence
            is not a rate, or if every band has prevalence 0 or 1 -- in which
            case there is no variance to chase and proportional is the answer.
    """
    if total < 0:
        raise AllocationError(f"total={total!r} cannot be negative")
    weights = _weights(populations)
    missing = sorted(set(populations) - set(prevalences))
    if missing:
        raise AllocationError(
            f"no measured prevalence for band(s) {', '.join(missing)}. Neyman "
            "allocation is a function of the per-band prevalences, and assuming "
            "one concentrates labels wherever the assumption pointed -- which is "
            "the one place the resulting estimate cannot correct it. Run "
            "proportional() for the first month and Neyman once these are "
            "measured (SPEC.md 6.3)."
        )
    for name, q in prevalences.items():
        if not 0.0 <= q <= 1.0:
            raise AllocationError(f"prevalence for {name} is {q!r}, not a rate")

    names = list(populations)
    spread = {n: math.sqrt(prevalences[n] * (1.0 - prevalences[n])) for n in names}
    denominator = sum(weights[n] * spread[n] for n in names)
    if denominator <= 0.0:
        raise AllocationError(
            "every band has a measured prevalence of 0 or 1, so no band carries "
            "any variance and Neyman has nothing to allocate toward. Use "
            "proportional()."
        )
    shares = [weights[n] * spread[n] / denominator for n in names]
    counts = _largest_remainder(shares, total)

    return Allocation(
        rule="neyman",
        total=total,
        per_band={n: c for n, c in zip(names, counts, strict=True)},
        weights=weights,
        design_effect=design_effect(
            populations=populations, prevalences=prevalences, total=total
        ),
        measured_inputs=dict(prevalences),
        note=(
            "Concentrates labels where the variance is. Unequal sampling "
            "fractions, so the estimator's q interval becomes approximate -- "
            "that is what this precision costs."
        ),
    )


def design_effect(
    *,
    populations: Mapping[str, int],
    prevalences: Mapping[str, float],
    total: int,
) -> float:
    """Neyman's variance against simple random sampling, at the same total.

    Quantity: ``Var(q_hat | Neyman) / Var(q_hat | SRS)``, both at sample size
    ``total``, ignoring the finite-population correction so the ratio is a
    property of the band structure rather than of one month's volume.
    Propagation: closed form. With ``S_h = sqrt(q_h(1-q_h))`` and ``q_bar`` the
    pooled prevalence,

        Var_Neyman = [sum_h W_h S_h]^2 / n
        Var_SRS    = q_bar (1 - q_bar) / n

    so the ratio is ``[sum_h W_h S_h]^2 / (q_bar (1 - q_bar))``, and ``n``
    cancels. It is at most 1 by Cauchy-Schwarz, which is why Neyman never costs
    precision -- and it is rarely far below 1, because the square root is
    concave and a large band with small non-zero prevalence dominates the sum
    **because** it is large. ``SPEC.md`` §6.3 expects ~0.67 and says to measure
    rather than assume; this measures it.

    Args:
        populations: Band name to unflagged items in that band.
        prevalences: Band name to measured ``q_h``.
        total: Unused by the ratio -- both variances carry ``1/n`` -- and taken
            only so callers cannot reach this with an allocation it does not
            describe.

    Returns:
        The ratio. Below 1 means the design buys precision.

    Raises:
        AllocationError: If a band lacks a prevalence, or the pooled prevalence
            is degenerate.
    """
    weights = _weights(populations)
    missing = sorted(set(populations) - set(prevalences))
    if missing:
        raise AllocationError(
            f"no measured prevalence for band(s) {', '.join(missing)}"
        )
    pooled = sum(weights[n] * prevalences[n] for n in populations)
    if not 0.0 < pooled < 1.0:
        raise AllocationError(
            f"pooled prevalence is {pooled:g}; a design effect against simple "
            "random sampling is undefined when there is no variance to compare."
        )
    numerator = sum(
        weights[n] * math.sqrt(prevalences[n] * (1.0 - prevalences[n]))
        for n in populations
    ) ** 2
    return numerator / (pooled * (1.0 - pooled))
