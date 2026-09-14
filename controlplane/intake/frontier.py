"""The whole curve, in exact counts: what each budget would cost you.

``certify`` answers one budget. The question a person actually has before they
pick one is *what does each budget buy me*, and answering it needs the frontier.

**Why this reports counts and not rates**, which is the design decision worth
understanding rather than a limitation:

Every rate this project publishes carries a bootstrap interval, because a point
estimate reaching a user is the failure `CLAUDE.md` invariant 4 exists to stop.
Bootstrapping is not cheap — one metrics block on a 400-row file takes **6.7
seconds**, so twenty grid points would be **134 seconds** of a person waiting at
a terminal. Reducing the resample count for this one view was available and
refused: ``build_warrant_metrics`` takes its count from config precisely so two
paths cannot disagree about how wide an interval is, and a frontier whose
intervals were narrower than the warrant's would be worse than no frontier.

So the frontier reports the half of the answer that is **exact and free**. From
`CLAUDE.md`'s single most important distinction:

    Yield is exact. Rate is estimated.

At each budget the certified threshold, its Clopper-Pearson bound, and the
**counts** — flagged, caught, missed, false positives — are all exact facts about
this file. None needs an interval because none is an estimate. Rates with
intervals come from certifying at a chosen budget, which is one bootstrap rather
than twenty.

The counts are also the more useful answer for choosing an operating point.
*"At a 5% budget you flag 66 items and catch 58 of the 102 you care about"* is
something a person can act on; 0.5686 [0.4672, 0.6705] is something they have to
translate first.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional, Sequence


from ..config import Config
from ..validation.warrant_stats import min_n_for
from .certify import certify_budget
from .contract import ScoredItems

__all__ = ["FrontierPoint", "frontier"]

#: The budgets shown by default: the standard grid this project registers
#: everywhere else, so a customer's curve and a published one are the same shape.
DEFAULT_GRID = (0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20)


@dataclasses.dataclass(frozen=True)
class FrontierPoint:
    """One budget, in exact quantities only."""

    budget: float
    certified: bool
    reason: str
    #: Independent negative units the budget needs: items, or clusters on a
    #: grouped file, the unit certification counts.
    min_negatives_required: int
    #: Independent negative units this file has, in the same unit.
    negative_units: Optional[int] = None
    grouped: bool = False
    threshold: Optional[float] = None
    fpr_upper_bound: Optional[float] = None
    n_flagged: Optional[int] = None
    true_positives: Optional[int] = None
    false_positives: Optional[int] = None
    missed: Optional[int] = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "budget_fpr": self.budget,
            "certified": self.certified,
            "reason": self.reason,
            "min_negatives_required": self.min_negatives_required,
            "independent_negative_units": self.negative_units,
            "unit": "negative cluster" if self.grouped else "negative item",
            "threshold": self.threshold,
            "fpr_upper_bound": self.fpr_upper_bound,
            "counts_exact": {
                "flagged": self.n_flagged,
                "caught": self.true_positives,
                "false_positives": self.false_positives,
                "missed": self.missed,
            },
        }


def frontier(
    config: Config,
    items: ScoredItems,
    *,
    grid: Sequence[float] = DEFAULT_GRID,
    alpha: Optional[float] = None,
) -> tuple[FrontierPoint, ...]:
    """Certify at every budget on the grid and report the exact counts.

    Args:
        config: Supplies the confidence level.
        items: The scored file.
        grid: Budgets to evaluate, ascending.
        alpha: Certification level; defaults to ``1 - config.validation.ci``.

    Raises:
        ValueError: If the file is grouped with unequal group sizes, exactly as
            ``certify --budget`` does.

    Returns:
        One point per budget, refusals kept in place. A refused budget is a fact
        about the evidence and dropping it would turn "you do not have enough
        clean negatives for 1%" into a gap that reads as an oversight.
    """
    alpha = (1.0 - config.validation.ci) if alpha is None else alpha
    labels, scores, groups = items.as_arrays()
    grouped = groups is not None
    positives_total = int((labels == 1).sum())

    points: list[FrontierPoint] = []
    for budget in grid:
        floor = min_n_for(float(budget), alpha)
        # The step `certify --budget` runs, not a second copy of it. The copy
        # that stood here dropped the group column, so a grouped file was
        # certified at item level at budgets `certify` refuses (DECISIONS 190).
        certification = certify_budget(items, float(budget), alpha)
        if not certification.fpr_certified:
            points.append(
                FrontierPoint(
                    budget=float(budget), certified=False,
                    reason=certification.reason, min_negatives_required=floor,
                    negative_units=certification.n_eff, grouped=grouped,
                )
            )
            continue

        threshold = float(certification.threshold)
        flagged = scores >= threshold
        true_positives = int((flagged & (labels == 1)).sum())
        points.append(
            FrontierPoint(
                budget=float(budget),
                certified=True,
                reason="certified",
                min_negatives_required=floor,
                negative_units=certification.n_eff,
                grouped=grouped,
                threshold=threshold,
                fpr_upper_bound=float(certification.ucb),
                n_flagged=int(flagged.sum()),
                true_positives=true_positives,
                false_positives=int((flagged & (labels == 0)).sum()),
                missed=positives_total - true_positives,
            )
        )
    return tuple(points)
