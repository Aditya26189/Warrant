"""Review volume, and how many reviewed items a recall claim needs.

Two quantities, both arithmetic over numbers that already exist. Neither needs
a new measurement, and neither is a cost figure — the price list is still not
built (``DECISIONS.md`` 096, 099).

**Review volume** is what a profile's operating point costs in items per month:
the measured flag rate applied to one declared workload, decomposed into true
and false positives so the composition is visible rather than a single total.

**Recall sample size** is the opposite direction: given a measured recall, how
many *flagged* items must be reviewed for the interval around it to reach a
declared margin. This is what makes a recall claim maintainable in production
rather than a one-off from a frozen eval set.

Every function separates its **measured** inputs (from ``results/``) from its
**declared** ones (from ``config.yaml``), and every result carries both lists.
A number derived from a declared workload is not a measurement of anything, and
the only defence against that being forgotten is for the object to say so.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

__all__ = ["ReviewSizing", "recall_sample_size", "review_volume"]

#: Two-sided normal quantile at 95%. The same coverage the warrants use, so a
#: sample size computed here and an interval reported there mean the same thing.
_Z_95 = 1.959963984540054


@dataclass(frozen=True)
class ReviewSizing:
    """A derived review quantity, with its inputs labelled by origin."""

    name: str
    value: float
    unit: str
    measured_inputs: dict[str, float] = field(default_factory=dict)
    declared_inputs: dict[str, float] = field(default_factory=dict)
    note: str = ""

    def render(self) -> str:
        measured = ", ".join(f"{k}={v:g}" for k, v in self.measured_inputs.items())
        declared = ", ".join(f"{k}={v:g}" for k, v in self.declared_inputs.items())
        return (
            f"{self.name}: {self.value:,.0f} {self.unit}\n"
            f"    measured: {measured or 'none'}\n"
            f"    declared: {declared or 'none'}"
        )


def review_volume(
    *,
    flag_rate: float,
    recall: float,
    base_error_rate: float,
    monthly_interactions: int,
    operating_point_id: str = "",
) -> dict[str, ReviewSizing]:
    """Items sent to review per month, split into true and false positives.

    Args:
        flag_rate: **Measured** flag rate at this operating point.
        recall: **Measured** recall at this operating point.
        base_error_rate: **Declared** error rate of the production traffic. Not
            the eval set's base rate — that describes TriviaQA, and quoting it
            as production would be the scenario-mixing error ``CLAUDE.md`` names.
        monthly_interactions: **Declared** traffic volume.
        operating_point_id: For labelling only.

    Returns:
        ``flagged``, ``true_positives``, ``false_positives`` and
        ``errors_missed``, each as a :class:`ReviewSizing`.

    Raises:
        ValueError: If a rate is outside ``[0, 1]`` or the volume is negative.
    """
    for name, value in (
        ("flag_rate", flag_rate),
        ("recall", recall),
        ("base_error_rate", base_error_rate),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name}={value!r} is not a rate in [0, 1]")
    if monthly_interactions < 0:
        raise ValueError(f"monthly_interactions={monthly_interactions!r} is negative")

    measured = {"flag_rate": flag_rate, "recall": recall}
    declared = {
        "monthly_interactions": monthly_interactions,
        "base_error_rate": base_error_rate,
    }
    errors = monthly_interactions * base_error_rate
    flagged = monthly_interactions * flag_rate
    true_positives = errors * recall
    # Clamped at zero: a measured flag rate and a measured recall come from one
    # envelope, and applying both to a *different* declared base rate can make
    # the implied true positives exceed the flagged total. That is a sign the
    # two rates are being quoted against traffic they were not measured on, so
    # it is surfaced in the note rather than allowed to produce a negative.
    false_positives = max(0.0, flagged - true_positives)
    inconsistent = flagged < true_positives

    note = (
        "Derived from ONE declared workload. The flag rate and recall are "
        "measured on an eval set; the volume and production error rate are "
        "declared. Mixing rates from two workloads is the error CLAUDE.md names."
    )
    if inconsistent:
        note += (
            " WARNING: implied true positives exceed the flagged total, which "
            "means this operating point's rates do not describe traffic at this "
            "declared base error rate."
        )

    def sizing(name: str, value: float) -> ReviewSizing:
        return ReviewSizing(
            name=f"{name}{f' @ {operating_point_id}' if operating_point_id else ''}",
            value=value,
            unit="items/month",
            measured_inputs=measured,
            declared_inputs=declared,
            note=note,
        )

    return {
        "flagged": sizing("flagged", flagged),
        "true_positives": sizing("true positives", true_positives),
        "false_positives": sizing("false positives", false_positives),
        "errors_missed": sizing("errors missed", errors - true_positives),
    }


def recall_sample_size(
    *,
    recall: float,
    margin: float,
    design_effect: float = 1.0,
    operating_point_id: str = "",
) -> ReviewSizing:
    """**Superseded.** Confirmed *errors* a recall interval needs, not items.

    Quantity: confirmed errors a sample must contain for a recall interval
    of half-width ``margin`` -- **not** reviewed items, which is the defect.
    Propagation: normal approximation for a proportion at ``p = recall``,
    ``n = z^2 p(1-p)/m^2``, inflated by the declared design effect. It
    propagates through **no derivative at all**, which is why it is wrong
    for the design this project runs -- see the warning below and
    ``DECISIONS.md`` 147.

    .. warning::

       ``DECISIONS.md`` 147. This function shipped for four phases labelled
       ``unit="reviewed items"``, and it never returned reviewed items. Use
       :func:`controlplane.sampling.planning.labels_for_recall`, which
       propagates through ``dR/dq`` and sizes against the interval
       :mod:`controlplane.sampling.estimator` actually publishes. At the three
       shipped operating points this figure was low by 6x to 13x.

    It is kept, with its arithmetic unchanged and its unit corrected, because a
    function renamed away leaves nothing for a reader who still has the old
    number to find.

    What the formula is right for: ``n = z^2 p(1-p)/m^2`` at ``p = recall`` is
    the sample size for estimating recall by drawing ``n`` items **from the
    population of true errors** and checking whether each was flagged. That is a
    real design and it is the one design nobody can run, because the error
    population is not enumerable without the labels the sample exists to buy.
    Reaching ``n`` confirmed errors costs roughly ``n / base_error_rate``
    reviewed items -- another factor of 33 at a declared 3% base rate.

    Args:
        recall: **Measured** recall at the operating point.
        margin: **Declared** half-width wanted on the interval.
        design_effect: **Declared** variance inflation from stratified sampling
            relative to simple random sampling. Values above 1 mean the design
            costs precision; below 1, that stratification buys some back.
        operating_point_id: For labelling only.

    Returns:
        The required number of **confirmed errors**, rounded up. Not items, and
        not labels.

    Raises:
        ValueError: If ``recall`` is not a rate, ``margin`` is not positive, or
            ``design_effect`` is not positive.
    """
    if not 0.0 <= recall <= 1.0:
        raise ValueError(f"recall={recall!r} is not a rate in [0, 1]")
    if margin <= 0.0:
        raise ValueError(f"margin={margin!r} must be positive")
    if design_effect <= 0.0:
        raise ValueError(f"design_effect={design_effect!r} must be positive")

    n = (_Z_95**2) * recall * (1.0 - recall) / (margin**2) * design_effect
    return ReviewSizing(
        name=(
            "SUPERSEDED: confirmed errors for recall +/- "
            f"{margin:g}{f' @ {operating_point_id}' if operating_point_id else ''}"
        ),
        value=float(math.ceil(n)),
        unit="confirmed errors (NOT reviewed items)",
        measured_inputs={"recall": recall},
        declared_inputs={
            "margin": margin,
            "design_effect": design_effect,
            "confidence": 0.95,
        },
        note=(
            "SUPERSEDED by sampling.planning.labels_for_recall -- DECISIONS.md "
            "147. This is a count of confirmed errors the sample must contain, "
            "under a design that draws from the error population and which "
            "nobody can run. It was published as 'reviewed items' for four "
            "phases and was low by 6x to 13x as a label budget. Normal "
            "approximation, sized at the measured recall rather than at p=0.5. "
            "The design effect is declared, not measured."
        ),
    )
