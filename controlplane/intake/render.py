"""The summary a person reads in a terminal.

Written to make a **refusal legible as a result**. A tool that prints a warrant
in confident green and a refusal in the same shape as a stack trace teaches its
user that refusals are malfunctions, and the entire proposition here is that
they are not. So both outcomes get the same layout, the same amount of detail,
and a refusal additionally gets the one thing a user actually wants next: what
it would take.
"""

from __future__ import annotations

from typing import Optional

from ..model import Metric, WarrantStatus
from .certify import CertificationResult

__all__ = ["render_summary"]

# ASCII only, deliberately. The first run of this on Windows died with
# UnicodeEncodeError: the console's cp1252 codepage cannot encode a box-drawing
# character, and a stranger following the quickstart would have hit a traceback
# instead of a warrant. Output that cannot be printed is output that does not
# work, whatever it looks like on the machine it was written on.
_RULE = "-" * 66


def _metric_line(label: str, metric: Optional[Metric], digits: int = 4) -> str:
    if metric is None:
        return f"  {label:<14} n/a"
    return f"  {label:<14} {metric.render(digits)}"


def render_summary(result: CertificationResult) -> str:
    """Render one certification for a terminal."""
    lines = [
        _RULE,
        f"  WARRANT: {result.status.value}",
        _RULE,
        "",
        f"  input          {result.source}",
        f"  items          {result.n}  ({result.n_positive} positive, "
        f"{result.n_negative} negative)",
    ]
    if result.grouped:
        lines.append(
            f"  units          {result.n_units} groups - certification and "
            "resampling both happen at group level"
        )
    lines += [
        f"  base rate      {result.base_rate:.4f}",
        f"  budget         FPR <= {result.budget:.4f} at "
        f"{(1 - result.alpha) * 100:.0f}% confidence",
        "",
    ]

    if result.status is WarrantStatus.REFUSED:
        lines += [
            "  REFUSED. The evidence does not support a warrant at this budget.",
            "",
            f"  {result.reason}",
            "",
            "  What would change it:",
            f"    * {result.min_units_required} clean negative units are needed "
            f"to certify FPR <= {result.budget:.4f}; this file has "
            f"{result.negative_units}.",
            "    * A looser budget needs fewer: the requirement scales as "
            "log(alpha)/log(1-budget).",
            "",
            "  This is the tool working. A detector that cannot be certified on",
            "  the evidence provided is a fact worth having before it ships, not",
            "  an error in the measurement.",
            _RULE,
            "",
        ]
        return "\n".join(lines)

    lines += [
        "  CERTIFIED.",
        "",
        f"  {result.reason}",
        "",
        f"  threshold      {result.threshold:.6f}",
        f"  FPR bound      {result.fpr_upper_bound:.4f}  "
        f"({result.false_positives_at_threshold} false positive(s) on "
        f"{result.negative_units} negative units)",
        f"  flagged        {result.n_flagged} of {result.n} items",
        "",
        "  What the detector does at that threshold:",
        _metric_line("recall", result.recall),
        _metric_line("precision", result.precision),
        _metric_line("flag rate", result.flag_rate),
        _metric_line("lift", result.lift, 3),
    ]
    if result.lift is not None and result.lift_ceiling:
        share = result.lift.value / result.lift_ceiling
        lines.append(
            f"                 ceiling {result.lift_ceiling:.2f} at this base "
            f"rate - the detector reaches {share * 100:.0f}% of it"
        )
    if result.metrics_absent_reason:
        lines += ["", f"  note: {result.metrics_absent_reason}"]

    lines += [
        "",
        "  Every rate carries a 95% interval. Recall and precision are reported",
        "  together and neither is quotable alone.",
        _RULE,
        "",
    ]
    return "\n".join(lines)
