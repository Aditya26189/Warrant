"""Certifying a detector that emits no score, and what the score costs.

``docs/REDACT.md`` §5 states this repository's largest methodological limit: a
warrant is a statement about a threshold, and the detector family that wins on
REDACT — GPT-4.1, Claude Sonnet — emits spans and types with no confidence
attached. There is nothing to threshold, so the method cannot certify the
detectors that perform best.

**The route out is repeated sampling.** Run the judge ``k`` times at
temperature; score item ``i`` as ``votes_i / k``. A set-valued extractor becomes
rankable.

**And the consequence is the interesting half.** That score takes at most
``k + 1`` values, so it induces at most ``k + 1`` distinct decision rules: flag
when ``votes >= m``, for ``m`` in ``0..k``. A judge wrapped this way has no
continuous dial. It has ``k + 1`` notches, and buying more notches costs ``k``
times the inference bill.

That is the same finding as ``DECISIONS.md`` 141 arriving from the other
direction. There, Presidio's rule-fired confidence was found to yield one to
three operating points across twenty budgets, so a false-positive budget is not
a dial you can set on it. Here the notches are countable in advance and **their
number is a purchase decision**.

:func:`tunability` is deliberately written against *any* score vector rather
than only against consensus scores, because the question — *how many operating
points does this detector actually offer?* — is the same one for a rule engine,
and it had been observed for Presidio and written up without ever being
implemented.

``DECISIONS.md`` 152 registers the four claims this module exists to test, and
the scope: everything here is exercised against a **simulated** judge whose
draws are Bernoulli by construction. A real judge's repeated samples share a
prompt and a temperature and are correlated, which makes the vote fraction a
worse estimate than the simulation says. Every figure derived here is therefore
an **upper bound** on what ``k`` buys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

from .warrant_stats import cp_upper

__all__ = [
    "ConsensusScores",
    "ScoreFreeError",
    "Tunability",
    "consensus_scores",
    "smallest_certifiable_budget",
    "tunability",
]


class ScoreFreeError(ValueError):
    """A score-free detector was asked for something it cannot provide."""


@dataclass(frozen=True)
class ConsensusScores:
    """Scores derived from ``k`` repeated binary verdicts per item.

    Attributes:
        k: Samples drawn per item. **Part of the operating point**, not a
            runtime detail: a bound certified at this ``k`` says nothing about
            any other (``DECISIONS.md`` 152).
        votes: Per item, how many of the ``k`` runs flagged it.
        scores: ``votes / k``. The rankable quantity.
        detector_id: The wrapped detector's id with ``k`` appended, which is
            how ``k`` enters the warrant key without a schema change.
        notches: Distinct decision rules available, ``k + 1`` by construction.
        distinct_scores: Score values actually realised on this data. At most
            ``k + 1`` and usually fewer, which is the number that bounds the
            operating points reachable *here*.
    """

    k: int
    votes: tuple[int, ...]
    scores: tuple[float, ...]
    detector_id: str
    notches: int
    distinct_scores: int

    def render(self) -> str:
        """One line: the id that carries ``k``, and what it bought."""
        return (
            f"{self.detector_id}: {self.notches} notches available, "
            f"{self.distinct_scores} score values realised over "
            f"{len(self.votes):,} items"
        )


def consensus_scores(
    votes: Sequence[int], *, k: int, detector_id: str
) -> ConsensusScores:
    """Wrap ``k`` repeated binary verdicts into a rankable score.

    Args:
        votes: Per item, how many of the ``k`` runs flagged it.
        k: Samples per item. Must be positive.
        detector_id: The underlying detector's id. ``k`` is appended, because
            ``CLAUDE.md`` invariant 1 keys a warrant by its detector and a
            nine-sample consensus is not the same detector as a one-sample one.

    Returns:
        The scores, the id that carries ``k``, and the notch count.

    Raises:
        ScoreFreeError: If ``k`` is not positive, a vote count is outside
            ``[0, k]``, or no items were supplied.
    """
    if k <= 0:
        raise ScoreFreeError(f"k={k!r} must be positive")
    if "@k=" in detector_id:
        raise ScoreFreeError(
            f"detector_id={detector_id!r} already carries a k. Wrapping a "
            "consensus in a consensus would produce an id that names two "
            "sample counts and a warrant nobody can resolve."
        )
    counts = list(votes)
    if not counts:
        raise ScoreFreeError("no items: there is nothing to score")
    for i, value in enumerate(counts):
        if not 0 <= value <= k:
            raise ScoreFreeError(
                f"item {i} has {value} votes out of k={k}, which is impossible"
            )
    scores = tuple(v / k for v in counts)
    return ConsensusScores(
        k=k,
        votes=tuple(int(v) for v in counts),
        scores=scores,
        detector_id=f"{detector_id}@k={k}",
        notches=k + 1,
        distinct_scores=len(set(scores)),
    )


@dataclass(frozen=True)
class Tunability:
    """How many operating points a detector actually offers, and which budgets.

    Attributes:
        detector_id: What was measured.
        n_negatives: Negatives the budgets were certified against.
        n_positives: Positives recall was measured on.
        distinct_scores: Score values realised. An upper bound on everything
            below: you cannot have more decision rules than score cut points.
        distinct_operating_points: Distinct realised ``(FPR, recall)`` pairs
            across the requested budgets. **This is the tunability**, and it is
            what an F1 table structurally cannot show, because F1 is computed
            wherever the detector already sits and never varies the threshold.
        budgets_requested: How many budgets were asked for.
        budgets_certifiable: How many of them some threshold can actually meet,
            with a Clopper-Pearson upper bound clearing the budget.
        tightest_certifiable: The smallest budget any threshold underwrites, or
            ``None`` when none does.
        achievable: Per requested budget, the realised ``(threshold, fpr,
            fpr_upper, recall)`` or ``None`` where the budget is unreachable.
        note: What the numbers are and are not.
    """

    detector_id: str
    n_negatives: int
    n_positives: int
    distinct_scores: int
    distinct_operating_points: int
    budgets_requested: int
    budgets_certifiable: int
    tightest_certifiable: Optional[float]
    achievable: dict[float, Optional[dict[str, float]]] = field(default_factory=dict)
    note: str = ""

    def render(self) -> str:
        """The tunability, and the budgets that are simply out of reach."""
        lines = [
            f"{self.detector_id}: {self.distinct_operating_points} distinct "
            f"operating points across {self.budgets_requested} budgets "
            f"({self.distinct_scores} distinct scores, n={self.n_negatives:,} "
            "negatives)"
        ]
        if self.tightest_certifiable is None:
            lines.append("    no budget in the grid is certifiable at any threshold")
        else:
            lines.append(
                f"    tightest certifiable budget {self.tightest_certifiable:g}; "
                f"{self.budgets_certifiable} of {self.budgets_requested} reachable"
            )
        return "\n".join(lines)


def tunability(
    *,
    scores: Sequence[float],
    labels: Sequence[int],
    budgets: Sequence[float],
    alpha: float = 0.05,
    detector_id: str = "",
) -> Tunability:
    """How many operating points this detector offers across a budget grid.

    Quantity: the count of distinct realised ``(FPR, recall)`` pairs a detector
    can be moved to. Propagation: for each budget, the lowest threshold whose
    one-sided Clopper-Pearson **upper** bound on the negative-class flag rate
    clears the budget — the same rule
    :func:`controlplane.validation.warrant_stats.certify_fpr` uses, so a
    tunability count and a warrant mean the same thing by construction.

    A detector with one operating point across twenty budgets cannot be tuned to
    your budget at all. That is a procurement fact and an F1 table cannot show
    it, because F1 is computed wherever the detector already sits.

    Args:
        scores: Detector scores. Higher means more suspicious.
        labels: 1 for the positive class (*incorrect*, per ``config.yaml``),
            0 for negatives.
        budgets: False-positive budgets to try.
        alpha: One-sided confidence level.
        detector_id: For labelling only.

    Returns:
        The tunability and the per-budget outcome.

    Raises:
        ScoreFreeError: If the inputs disagree in length, are empty, hold
            anything but 0 and 1 as labels, or contain no negatives.
    """
    score_array = np.asarray(scores, dtype=float)
    label_array = np.asarray(labels, dtype=int)
    if score_array.size != label_array.size:
        raise ScoreFreeError(
            f"{score_array.size} scores against {label_array.size} labels"
        )
    if score_array.size == 0:
        raise ScoreFreeError("no items to measure tunability on")
    if set(np.unique(label_array).tolist()) - {0, 1}:
        raise ScoreFreeError(
            "labels must be 0 or 1, where 1 is the positive class 'incorrect'"
        )

    negatives = score_array[label_array == 0]
    positives = score_array[label_array == 1]
    if negatives.size == 0:
        raise ScoreFreeError(
            "no negatives. A false-positive budget cannot be certified against "
            "a set with nothing to be falsely positive about."
        )

    # Candidate thresholds are the realised score values and nothing else.
    # A threshold between two realised values produces the identical partition,
    # so a grid finer than the data is a grid of duplicates -- which is exactly
    # how a detector with three notches gets reported as having twenty.
    candidates = np.unique(score_array)

    achievable: dict[float, Optional[dict[str, float]]] = {}
    realised: set[tuple[float, float]] = set()
    certifiable: list[float] = []
    for budget in budgets:
        chosen: Optional[dict[str, float]] = None
        for threshold in candidates:
            false_positives = int((negatives >= threshold).sum())
            upper = cp_upper(false_positives, int(negatives.size), alpha)
            if upper <= budget:
                fpr = false_positives / negatives.size
                recall = (
                    float((positives >= threshold).mean()) if positives.size else 0.0
                )
                chosen = {
                    "threshold": float(threshold),
                    "fpr": fpr,
                    "fpr_upper": upper,
                    "recall": recall,
                }
                realised.add((round(fpr, 12), round(recall, 12)))
                certifiable.append(float(budget))
                break
        achievable[float(budget)] = chosen

    return Tunability(
        detector_id=detector_id,
        n_negatives=int(negatives.size),
        n_positives=int(positives.size),
        distinct_scores=int(candidates.size),
        distinct_operating_points=len(realised),
        budgets_requested=len(list(budgets)),
        budgets_certifiable=len(certifiable),
        tightest_certifiable=min(certifiable) if certifiable else None,
        achievable=achievable,
        note=(
            "Thresholds are the realised score values, not a grid. A grid finer "
            "than the data counts duplicates and reports a detector with three "
            "notches as having twenty. Certification uses the one-sided "
            "Clopper-Pearson upper bound, the same rule certify_fpr uses."
        ),
    )


def smallest_certifiable_budget(
    negative_scores: Sequence[float],
    positive_scores: Sequence[float],
    alpha: float = 0.05,
) -> Optional[float]:
    """The tightest false-positive budget a **useful** threshold underwrites.

    Two floors bind on a false-positive budget and they are different
    constraints:

    * **The data's capacity.** ``cp_upper(0, n, alpha)`` is the tightest bound
      any threshold can reach, because a Clopper-Pearson upper bound from zero
      failures in ``n`` negatives is still positive. This is the same quantity
      as ``docs/REDACT.md`` §1's certification capacity, one level down.
    * **Granularity.** A detector that emits ``d`` distinct scores offers ``d``
      cut points, so it can only land on ``d`` false-positive rates. A
      ``k``-vote consensus has at most ``k + 1``.

    **Positives are required, and that is the fix for a real defect in the
    first version of this function.** Without them the threshold set included a
    cut point above every score, which flags no negative, returns the data floor
    at every ``k``, and is reached only by a detector that never fires. It was a
    true number for a useless operating point, which made granularity look as if
    it never binds. A threshold is only counted here if it flags at least one
    positive.

    Args:
        negative_scores: Scores of the negative class.
        positive_scores: Scores of the positive class. A candidate threshold
            that flags none of these is a detector that does nothing.
        alpha: One-sided confidence level.

    Returns:
        The bound, or ``None`` if there are no negatives, or no threshold flags
        a positive.
    """
    negatives = np.asarray(negative_scores, dtype=float)
    positives = np.asarray(positive_scores, dtype=float)
    if negatives.size == 0 or positives.size == 0:
        return None
    best: Optional[float] = None
    for threshold in np.unique(np.concatenate([negatives, positives])):
        if not (positives >= threshold).any():
            continue
        false_positives = int((negatives >= threshold).sum())
        bound = cp_upper(false_positives, int(negatives.size), alpha)
        best = bound if best is None else min(best, bound)
    return best
