"""Is the warrant still true? The second clause, on the customer path.

The product claims three things: what your error rate is, **when that number
stops being true**, and what it costs to keep it true. The second was built for
the research pipeline — PSI, a simulated null band, a revocation ladder — and had
no route a customer could reach. This is that route.

``warrant recheck`` takes a warrant issued earlier and a fresh file of the same
shape, and answers one question: **does the promise still hold?** Two ways it can
fail, and they are different failures:

* **The bound broke.** The threshold that was certified at a 5% false-positive
  budget now exceeds it on new data. The promise is measurably false.
* **The ground moved.** The score distribution has shifted far enough that the
  old measurement no longer describes the traffic, even if today's sample happens
  to satisfy the bound.

**Why drift alone is not enough, and why a small file cannot cry wolf.** PSI's
0.10 and 0.25 bands are credit-scoring rules of thumb quoted without their sample
size, and they are not scale-free: the null grows roughly as ``(k-1)/n``. On two
hundred rows a PSI of 0.12 is unremarkable noise; on twenty thousand it is a real
shift. So the observed PSI is compared against a **null band simulated at this
file's own sample size** (``DECISIONS.md`` 070) rather than against the folklore
number. A verdict that would be indistinguishable from resampling the same
distribution is reported as exactly that.

**Nothing personal is retained.** A warrant stores the score distribution as bin
edges and probabilities, never as values, so a record that lives for a year
carries no one's data — the reasoning already written into
:class:`~controlplane.model.EnvelopeFeature`.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional

import numpy as np

from ..config import Config
from ..model import EnvelopeFeature, WarrantStatus
from .contract import ScoredItems

__all__ = [
    "RecheckResult",
    "negatives_needed_to_detect",
    "apply_revoked_chain_head",
    "recheck_items",
    "score_distribution",
    "smallest_detectable_breach",
]

#: Bins for the score histogram a warrant carries. Ten is the credit-scoring
#: convention PSI grew up with, and it keeps the null band narrow enough to be
#: informative at the file sizes a customer actually has.
N_BINS = 10

#: Below this many items, drift is not assessed at all. Two hundred is
#: `config.drift.window_size`, the minimum the research monitor accepts before
#: any verdict, and the same restraint applies here: a shift that cannot be
#: distinguished from resampling is not a finding.
MIN_ITEMS_FOR_DRIFT = 200


def score_distribution(scores: np.ndarray, *, name: str = "detector_score") -> EnvelopeFeature:
    """Summarise scores as a binned reference, retaining no values.

    Args:
        scores: The detector's scores over the certified set.
        name: Feature name recorded in the warrant.

    Returns:
        The reference distribution a later recheck compares against.
    """
    values = np.asarray(scores, dtype=float)
    edges = np.histogram_bin_edges(values, bins=N_BINS)
    counts, _ = np.histogram(values, bins=edges)
    probabilities = counts / max(counts.sum(), 1)
    # PSI divides by the reference proportion, so an empty reference bin makes it
    # infinite. Flooring keeps the statistic finite while still registering a
    # large divergence -- the standard treatment, and the same one the research
    # path uses.
    probabilities = np.maximum(probabilities, 1e-6)
    probabilities = probabilities / probabilities.sum()
    return EnvelopeFeature(
        name=name,
        bin_edges=tuple(float(e) for e in edges),
        bin_probabilities=tuple(float(p) for p in probabilities),
        mean=float(values.mean()),
        std=float(values.std()),
    )


@dataclasses.dataclass(frozen=True)
class RecheckResult:
    """Whether a warrant still holds, and which way it failed if not."""

    status: WarrantStatus
    reason: str
    budget: float
    threshold: float
    n_now: int
    n_negative_now: int
    achieved_fpr_now: Optional[float]
    fpr_upper_bound_now: Optional[float]
    fpr_lower_bound_now: Optional[float]
    bound_still_holds: Optional[bool]
    #: Smallest observed rate that would have revoked at this sample size.
    #: Printed with every verdict, because the dead zone the asymmetric test
    #: buys is invisible otherwise.
    detectable_floor: Optional[float] = None
    #: Negatives that would be needed to catch a true breach at 1.5x the budget
    #: with probability ``recheck_power`` (DECISIONS 183).
    negatives_for_tighter_floor: Optional[int] = None
    #: This file's own chance of revoking a detector truly at 1.5x the budget.
    #: The floor above says which observed rate revokes; this says how often a
    #: real breach of that size produces one.
    power_against_1_5x_budget: Optional[float] = None
    recheck_power: Optional[float] = None
    #: ``"item"``, or ``"cluster"`` when the file declares groups. Every count
    #: and rate in the record is in this unit (DECISIONS 188).
    unit: str = "item"
    #: What drift alone concludes -- ``"REVOKED"``, ``"STALE"``, ``"STABLE"``, or
    #: ``None`` when not assessed -- by the rule :func:`_verdict` applies. Carried
    #: separately because the verdict is bound-first, and a chain that reinterprets
    #: the bound must not lose a drift revocation behind it (DECISIONS 194).
    drift_verdict: Optional[str] = None
    psi: Optional[float] = None
    psi_null_p95: Optional[float] = None
    psi_beyond_noise: Optional[bool] = None
    #: Where this warrant's chain revoked it, when an unchained recheck found a
    #: sidecar saying so: ``"record NNNN"`` (``DECISIONS.md`` 210). ``None`` when
    #: there is no sidecar, or its latest record did not revoke.
    chain_revoked_at: Optional[str] = None
    #: Canonical digest of the exact retained certificate the CLI read (213).
    #: Direct statistical callers have no source record and leave this absent.
    warrant_sha256: Optional[str] = None
    #: VERIFIED only after replay against retained certificate input; otherwise
    #: NOT_CHECKED. This is arithmetic consistency, never authenticated custody.
    certificate_verification: str = "NOT_CHECKED"
    #: Items the reference bins were built from, which is what the null band is
    #: simulated at. ``None`` when the warrant does not say, in which case the
    #: band falls back to this file's size and the record says so (209).
    psi_reference_n: Optional[int] = None
    drift_assessed: bool = False
    drift_not_assessed_reason: str = ""
    #: Live bins that were empty where the reference had mass, and were
    #: therefore floored at the configured epsilon.
    psi_bins_smoothed: int = 0
    #: True when those floored bins contribute most of the index. Such a PSI
    #: is a statement about **absence of data in a region**, not about a
    #: measured shift there, and must not revoke a warrant on its own.
    psi_driven_by_smoothing: bool = False
    psi_epsilon: Optional[float] = None
    #: How many wrong labels would have made this file revoke, or why that is not
    #: computed (:class:`controlplane.intake.labels.RecheckSensitivity`, DECISIONS 198).
    label_sensitivity: Optional[Any] = None
    #: ``label_2`` measured beside the recheck, when the file has the column (198).
    second_review: Optional[Any] = None

    @property
    def still_valid(self) -> bool:
        return self.status is WarrantStatus.VALID

    def to_payload(self) -> dict[str, Any]:
        prior_warrant: dict[str, Any] = {
            "budget_fpr": self.budget,
            "threshold": self.threshold,
            # Where the chain revoked it, so the record says so rather than
            # leaving the reader to find the sidecar (DECISIONS 210).
            "chain_revoked_at": self.chain_revoked_at,
        }
        if self.warrant_sha256 is not None:
            prior_warrant["warrant_sha256"] = self.warrant_sha256
            prior_warrant["certificate_verification"] = self.certificate_verification
        return {
            "status": self.status.value,
            "reason": self.reason,
            "prior_warrant": prior_warrant,
            "detection": {
                "smallest_detectable_rate": self.detectable_floor,
                "negatives_here": self.n_negative_now,
                "power_against_1_5x_budget": self.power_against_1_5x_budget,
                "negatives_to_detect_1_5x_budget": self.negatives_for_tighter_floor,
                "recheck_power": self.recheck_power,
                "note": (
                    "Revocation requires the one-sided lower bound to exceed the "
                    "budget, which leaves a dead zone between the budget and this "
                    "floor. A rate inside it returns VALID and is not evidence "
                    "the promise holds -- only an absence of evidence it broke. "
                    "negatives_to_detect_1_5x_budget is sized to catch a TRUE "
                    "rate of 1.5x the budget with probability recheck_power "
                    "(DECISIONS 183)."
                ),
            },
            "now": {
                "unit": self.unit,
                "n": self.n_now,
                "n_negative": self.n_negative_now,
                "achieved_fpr": self.achieved_fpr_now,
                "fpr_upper_bound": self.fpr_upper_bound_now,
                "fpr_lower_bound": self.fpr_lower_bound_now,
                "bound_still_holds": self.bound_still_holds,
            },
            "drift": {
                "verdict": self.drift_verdict,
                "assessed": self.drift_assessed,
                "not_assessed_reason": self.drift_not_assessed_reason,
                "psi": self.psi,
                "psi_null_p95": self.psi_null_p95,
                "psi_reference_n": self.psi_reference_n,
                "psi_reference_n_known": self.psi_reference_n is not None,
                "beyond_noise": self.psi_beyond_noise,
                "bins_smoothed": self.psi_bins_smoothed,
                "driven_by_smoothing": self.psi_driven_by_smoothing,
                "epsilon": self.psi_epsilon,
                "note": (
                    "PSI is compared against a null simulated at this file's own "
                    "sample size and at the reference's, not against the 0.10/0.25 "
                    "folklore bands, which are not scale-free (DECISIONS 070, 209)."
                    + (
                        ""
                        if self.psi_reference_n is not None
                        else " This warrant does not record how many items its "
                        "reference was built from, so the band assumed it was as "
                        "large as this file. A reference smaller than that has a "
                        "wider null than the one used here."
                    )
                ),
            },
            "labels": {
                "decision": "DECISIONS.md 198",
                "tested_on": "the label column; label_2 changes no verdict",
                "sensitivity": (
                    self.label_sensitivity.to_payload()
                    if self.label_sensitivity is not None else None
                ),
                "second_review": (
                    self.second_review.to_payload() if self.second_review is not None
                    else {"present": False, "note": (
                        "no label_2 column: agreement between reviewers is not measured"
                    )}
                ),
            },
        }


def recheck_items(
    config: Config,
    items: ScoredItems,
    *,
    budget: float,
    threshold: float,
    reference: Optional[EnvelopeFeature] = None,
    reference_n: Optional[int] = None,
    alpha: Optional[float] = None,
) -> RecheckResult:
    """Re-test a warrant's promise against fresh data.

    Args:
        config: Supplies the confidence level and the PSI bands.
        items: The new file, same contract as certification.
        budget: The false-positive budget the warrant promised.
        threshold: The threshold the warrant certified.
        reference: The score distribution recorded at certification. Absent for
            warrants issued before records carried one; drift is then skipped
            and said to be skipped rather than silently reported as stable.
        reference_n: Items that reference was built from, which the PSI null is
            simulated at (``DECISIONS.md`` 209). The certify record's ``input.n``,
            since the reference is built from every score in that file. ``None``
            for a record that does not say: the band then falls back to this
            file's size, as before, and the record discloses it.
        alpha: Certification level; defaults to ``1 - config.validation.ci``.

    Returns:
        The verdict, with both failure modes reported separately.
    """
    alpha = (1.0 - config.validation.ci) if alpha is None else alpha
    labels, scores, groups = items.as_arrays()
    # A grouped file is re-tested in the unit it was certified in: one maximum
    # per negative cluster, so `negatives.size` below is the cluster count and
    # every bound, floor and power is computed at it. Discarding the groups
    # re-tested a cluster promise per item, at an inflated n (DECISIONS 188).
    unit = "item" if groups is None else "cluster"
    negatives = (
        scores[labels == 0]
        if groups is None
        else negative_cluster_maxima(scores, labels, groups, source=items.source)
    )

    # --- has the bound broken? ------------------------------------------
    bound_holds: Optional[bool] = None
    achieved: Optional[float] = None
    upper: Optional[float] = None
    lower: Optional[float] = None
    floor: Optional[float] = None
    needed: Optional[int] = None
    power_here: Optional[float] = None
    power = config.validation.recheck_power
    if negatives.size:
        achieved = float((negatives >= threshold).mean())
        k = int((negatives >= threshold).sum())
        upper = _upper_bound_at(negatives.size, k, alpha)
        lower = _lower_bound_at(negatives.size, k, alpha)
        # THE DIRECTION OF THIS TEST IS THE WHOLE DESIGN, and the first version
        # had it backwards.
        #
        # Asking "does the new upper bound still clear the budget?" makes
        # revocation nearly automatic. Certification picks the lowest threshold
        # whose upper bound clears the budget, which deliberately pushes the true
        # rate up close to it -- measured here: certified at upper bound 0.0493
        # against a 0.05 budget, true rate 0.0371. A fresh sample from the SAME
        # distribution then measured 0.0491 with an upper bound of 0.0663,
        # failing re-certification, while its lower bound of 0.0353 showed no
        # evidence whatever that the promise had been broken.
        #
        # A recheck built that way cries wolf on stable traffic, which is worse
        # than useless: it teaches its user to ignore revocations.
        #
        # So the test is asymmetric, as it should be. Revoke only on evidence
        # that the rate EXCEEDS the promise -- the one-sided lower bound above
        # the budget. Failing to re-prove a claim is not the same as disproving
        # it, and that distinction is what this whole project rests on.
        bound_holds = lower <= budget
        floor = smallest_detectable_breach(int(negatives.size), budget, alpha)
        # A 1.5x breach is only a rate while it is below 1; a budget above 2/3
        # has no such breach to size, and asking would raise.
        if budget * 1.5 < 1.0:
            from ..economics.sizing import revocation_probability

            needed = negatives_needed_to_detect(budget * 1.5, budget, alpha, power)
            power_here = float(revocation_probability(
                np.array([negatives.size]), budget * 1.5, budget, alpha
            )[0])

    # --- has the ground moved? ------------------------------------------
    psi = null_p95 = epsilon = None
    smoothed = 0
    by_smoothing = False
    beyond_noise: Optional[bool] = None
    assessed = False
    skip_reason = ""
    if reference is None:
        skip_reason = (
            "the prior warrant carries no score distribution, so there is "
            "nothing to compare against"
        )
    elif groups is not None:
        skip_reason = (
            "the file declares groups, and the PSI noise level is simulated for "
            "independent items; a clustered file's noise is wider than that, so "
            "a drift verdict here would overstate the evidence"
        )
    elif items.n < MIN_ITEMS_FOR_DRIFT:
        skip_reason = (
            f"{items.n} items is below the {MIN_ITEMS_FOR_DRIFT} needed before a "
            "drift verdict means anything; a shift indistinguishable from "
            "resampling is not a finding"
        )
    else:
        from ..drift import population_stability_index, simulate_null_psi

        measured = population_stability_index(reference, scores.tolist())
        psi = float(measured.psi)
        smoothed = int(measured.bins_smoothed)
        by_smoothing = bool(measured.driven_by_smoothing)
        epsilon = float(measured.epsilon)
        # The reference's own estimation error is part of the null, so the
        # simulator is told how big the reference actually was. Passing this
        # file's size for it made a noisy hundred-item reference look as precise
        # as the new file (``DECISIONS.md`` 209).
        band = simulate_null_psi(
            reference.bin_probabilities,
            n=items.n,
            n_reference=items.n if reference_n is None else int(reference_n),
            stable_band=config.drift.psi_stable,
        )
        null_p95 = float(band.p95)
        beyond_noise = psi > null_p95
        assessed = True

    verdict = _verdict(
        config, budget, threshold, items, achieved, upper, lower, floor, needed,
        bound_holds,
        psi, null_p95, beyond_noise, assessed, skip_reason,
        smoothed, by_smoothing, epsilon, reference_n,
    )

    # --- how far does it depend on its labels? (DECISIONS 198) ----------
    # Computed from the counts above and fed back into nothing.
    from .labels import recheck_label_sensitivity, recheck_second_review, single_label_groups

    grouped = groups is not None
    single_label = not grouped or single_label_groups(labels, groups)
    k_now = int((negatives >= threshold).sum()) if negatives.size else None
    flagged_positives: Optional[int] = None
    if bound_holds and not grouped:
        flagged_positives = int(((scores >= threshold) & (labels == 1)).sum())
    elif bound_holds and single_label:
        flagged_positives = len({
            g for g, y, s in zip(groups, labels, scores, strict=True)
            if y == 1 and s >= threshold
        })
    sensitivity = recheck_label_sensitivity(
        bound_holds=bound_holds, grouped=grouped, single_label=single_label,
        k=k_now, n=int(negatives.size), flagged_positives=flagged_positives,
        budget=budget, alpha=alpha,
    )
    review = None
    if items.second_labels is not None:
        review = recheck_second_review(
            labels, items.second_labels, scores,
            threshold=threshold, k=k_now, n=int(negatives.size), budget=budget,
            alpha=alpha, bound_holds=bound_holds, grouped=grouped,
            groups=groups,
            seed=config.seed, resamples=config.validation.bootstrap_samples,
            ci=config.validation.ci,
        )
    return dataclasses.replace(
        verdict, power_against_1_5x_budget=power_here, recheck_power=power,
        unit=unit, n_negative_now=int(negatives.size),
        drift_verdict=drift_verdict(
            config, assessed=assessed, psi=psi, beyond_noise=beyond_noise,
            by_smoothing=by_smoothing,
        ),
        label_sensitivity=sensitivity, second_review=review,
    )


def negative_cluster_maxima(
    scores: np.ndarray, labels: np.ndarray, groups: np.ndarray, *, source: str
) -> np.ndarray:
    """One score per negative cluster: its maximum. See :func:`negative_cluster_units`."""
    return negative_cluster_units(scores, labels, groups, source=source)[1]


def negative_cluster_units(
    scores: np.ndarray, labels: np.ndarray, groups: np.ndarray, *, source: str
) -> tuple[np.ndarray, np.ndarray]:
    """Each negative cluster's id and maximum score, the unit certify counted.

    The ids are what a recheck chain orders and remembers (DECISIONS 193); the
    maxima are what decides whether each cluster is a false positive.

    A cluster is a false positive when any member reaches the threshold, so its
    maximum decides it -- the rule in
    :func:`controlplane.validation.warrant_stats.certify_fpr`. Unequal cluster
    sizes are refused for certify's reason: the cluster bound then no longer
    dominates the per-item rate the warrant promises.

    Raises:
        ValueError: If the negative clusters are not all the same size.
    """
    negative_scores = scores[labels == 0]
    negative_groups = groups[labels == 0]
    keys, inverse, sizes = np.unique(negative_groups, return_inverse=True, return_counts=True)
    if keys.size and len(set(sizes.tolist())) != 1:
        raise ValueError(
            f"{source}: the 'group' column has unequal negative cluster sizes "
            f"({int(sizes.min())} to {int(sizes.max())} items), so a cluster-level "
            "recheck would be anticonservative, for the same reason certify "
            "refuses one. See docs/INPUT.md."
        )
    maxima = np.full(keys.size, -np.inf)
    np.maximum.at(maxima, inverse, negative_scores)
    return keys, maxima


def _upper_bound_at(n: int, k: int, alpha: float) -> float:
    """One-sided Clopper-Pearson upper bound for ``k`` of ``n``."""
    from scipy.stats import beta

    if k >= n:
        return 1.0
    return float(beta.ppf(1.0 - alpha, k + 1, n - k))


def _lower_bound_at(n: int, k: int, alpha: float) -> float:
    """One-sided Clopper-Pearson lower bound for ``k`` of ``n``.

    The bound revocation turns on. It answers "how low could the true rate
    plausibly be", so exceeding the budget here means the data has *established*
    that the promise is broken, rather than merely failed to re-establish it.
    """
    from scipy.stats import beta

    if k <= 0:
        return 0.0
    return float(beta.ppf(alpha, k, n - k + 1))

def smallest_detectable_breach(
    n_negatives: int, budget: float, alpha: float
) -> Optional[float]:
    """The smallest observed false-positive rate that would revoke, at this ``n``.

    Quantity: the least observed false-positive rate that **establishes** a
    breach -- one whose one-sided Clopper-Pearson lower bound clears the
    budget. Propagation: exact, by search over achievable integer counts.
    Revocation turns on evidence of breach rather than failure to re-prove
    (``DECISIONS.md`` 143), so the lower bound is the right tail and the
    gap between it and the budget is the dead zone stated below.

    Revoking only on the lower bound buys a low false-alarm rate with a **dead
    zone**, and the zone has to be stated or "no evidence of breach" becomes the
    same kind of overclaim the asymmetric test was introduced to remove.

    Worked at the sizes this tool actually sees: 591 negatives against a 5%
    budget, the lower bound first clears 0.05 at k = 40, an observed rate of
    **6.8%**. A detector that has genuinely drifted from 3.7% to 6.0% sits
    inside that zone and returns VALID -- correctly, since 6% on 591 negatives
    does not establish a breach, and misleadingly if the floor is not printed
    beside the verdict.

    Returns:
        The rate, or None when no observed count at this ``n`` could establish a
        breach at all -- which is itself worth saying.
    """
    for k in range(1, n_negatives + 1):
        if _lower_bound_at(n_negatives, k, alpha) > budget:
            return k / n_negatives
    return None


def negatives_needed_to_detect(
    rate: float, budget: float, alpha: float, power: float
) -> Optional[int]:
    """Clean negatives needed to catch a true ``rate`` with probability ``power``.

    Quantity: the smallest stable ``n`` at which a recheck revokes a detector
    whose true false-positive rate is ``rate`` with probability at least
    ``power``. Propagation: exact binomial power at the exact Clopper-Pearson
    critical count, via
    :func:`controlplane.economics.sizing.negatives_for_power`.

    The companion to the floor: it turns "this file could not have caught a 6%
    rate" into "and here is what would have". Mirrors the answer `certify` gives
    a refusal -- the requirement, not just the shortfall.

    **Corrected again in DECISIONS 183, and the number went up again.** 146's
    size made an observed rate at the breach revoke, which catches a true
    breach about half the time; 287 became 628 at power 0.80.

    **Corrected in DECISIONS 146, and the number went up.** The first version
    walked ``n`` in steps of 1.2x and returned the first ``n`` at which the
    bound cleared. Both halves were wrong for a number somebody plans against.
    The step overshot by up to 20%; worse, detection is *not monotone in n* --
    at a 0.05 budget catching 0.075 it first holds at 234 and then fails again
    at 236 through 246 and at 252. The honest quantity is the smallest ``n``
    from which it holds at ``n`` and at every larger ``n``: 287 here, against
    the 249 this used to print.

    Delegates so that a planned sample size and a recheck's own hint cannot
    drift apart.

    Returns:
        The count, or ``None`` when no achievable sample detects it.
    """
    from ..economics.sizing import negatives_for_power

    return negatives_for_power(rate, budget, alpha, power)


def drift_verdict(
    config: Config,
    *,
    assessed: bool,
    psi: Optional[float],
    beyond_noise: Optional[bool],
    by_smoothing: bool,
) -> Optional[str]:
    """What the distribution check alone concludes, by the one rule `_verdict` uses.

    PSI driven by empty bins is a statement about missing data, never a
    revocation (STALE); beyond both the significant band and this sample's noise
    is REVOKED; beyond the stable band and the noise is STALE.
    """
    if not assessed or psi is None:
        return None
    if by_smoothing:
        return "STALE"
    if psi >= config.drift.psi_significant and beyond_noise:
        return "REVOKED"
    if psi >= config.drift.psi_stable and beyond_noise:
        return "STALE"
    return "STABLE"


def _verdict(
    config: Config,
    budget: float,
    threshold: float,
    items: ScoredItems,
    achieved: Optional[float],
    upper: Optional[float],
    lower: Optional[float],
    floor: Optional[float],
    needed: Optional[int],
    bound_holds: Optional[bool],
    psi: Optional[float],
    null_p95: Optional[float],
    beyond_noise: Optional[bool],
    assessed: bool,
    skip_reason: str,
    smoothed: int = 0,
    by_smoothing: bool = False,
    epsilon: Optional[float] = None,
    reference_n: Optional[int] = None,
) -> RecheckResult:
    """Decide, worst finding first.

    A broken bound outranks a moved distribution: the first is the promise being
    measurably false today, the second is a reason to doubt that it will hold
    tomorrow. Either revocation outranks a weaker warning or absent FPR
    evidence; an early STALE return must not hide drift revocation (205).
    """
    common = dict(
        budget=budget, threshold=threshold, n_now=items.n,
        n_negative_now=items.n_negative, achieved_fpr_now=achieved,
        fpr_upper_bound_now=upper, fpr_lower_bound_now=lower,
        bound_still_holds=bound_holds, detectable_floor=floor,
        negatives_for_tighter_floor=needed,
        psi=psi, psi_null_p95=null_p95, psi_beyond_noise=beyond_noise,
        psi_reference_n=reference_n,
        drift_assessed=assessed, drift_not_assessed_reason=skip_reason,
        psi_bins_smoothed=smoothed, psi_driven_by_smoothing=by_smoothing,
        psi_epsilon=epsilon,
    )

    if bound_holds is False:
        return RecheckResult(
            status=WarrantStatus.REVOKED,
            reason=(
                f"the false-positive rate is now measurably above the promise: "
                f"{achieved:.4f} measured, and even its lower bound of "
                f"{lower:.4f} exceeds the {budget:.4f} it was warranted at. That "
                f"is evidence the promise is broken, not merely an absence of "
                f"evidence that it holds."
            ),
            **common,
        )
    drift = drift_verdict(
        config, assessed=assessed, psi=psi, beyond_noise=beyond_noise, by_smoothing=by_smoothing
    )
    if drift == "REVOKED":
        return RecheckResult(
            status=WarrantStatus.REVOKED,
            reason=(
                f"the score distribution has moved "
                f"(PSI {psi:.4f}, beyond both the {config.drift.psi_significant} "
                f"band and this sample's own noise level of {null_p95:.4f}). The "
                f"warrant describes traffic you no longer have."
            ),
            **common,
        )
    if bound_holds is None:
        return RecheckResult(
            status=WarrantStatus.UNVALIDATED,
            reason=(
                "the new file has no negatives, so the false-positive bound "
                "cannot be re-tested. This is not evidence that it holds."
            ),
            **common,
        )
    if achieved is not None and achieved > budget:
        return RecheckResult(
            status=WarrantStatus.STALE,
            reason=(
                f"the measured false-positive rate {achieved:.4f} is above the "
                f"{budget:.4f} promised, but its lower bound of {lower:.4f} does "
                f"not establish that the true rate exceeds it. Not proof, and not "
                f"nothing: re-certify on more data before relying on this."
            ),
            **common,
        )
    if drift == "STALE" and by_smoothing:
        # The index is dominated by bins the live file left empty where the
        # reference had mass. That is a claim about missing data in a region,
        # not a measured shift of that size, and the smoothing constant sets its
        # magnitude: at eps=1e-6 one empty bin contributes ~13, at 1e-4 about 9.
        # Revoking on it would be revoking on a configuration choice.
        return RecheckResult(
            status=WarrantStatus.STALE,
            reason=(
                f"the bound holds, and PSI is {psi:.4f} but {smoothed} live "
                f"bin(s) are empty where the reference had mass, contributing "
                f"most of that number. This says your new file has no data in a "
                f"region the warrant was measured over -- not that the "
                f"distribution shifted by that much. Widen the sample or check "
                f"the file is complete before treating it as drift."
            ),
            **common,
        )
    if drift == "STALE":
        return RecheckResult(
            status=WarrantStatus.STALE,
            reason=(
                f"the bound holds and the distribution has shifted detectably "
                f"but not decisively (PSI {psi:.4f} against a noise level of "
                f"{null_p95:.4f}). Re-certify sooner than you planned."
            ),
            **common,
        )
    if not assessed:
        return RecheckResult(
            status=WarrantStatus.VALID,
            reason=(
                f"the measured false-positive rate is {achieved:.4f} against a "
                f"{budget:.4f} promise, with nothing in the data establishing a "
                f"breach. Drift was not assessed: {skip_reason}."
            ),
            **common,
        )
    return RecheckResult(
        status=WarrantStatus.VALID,
        reason=(
            f"the measured false-positive rate is {achieved:.4f} against a "
            f"{budget:.4f} promise, and the score distribution has not moved "
            f"beyond this sample's own noise level (PSI {psi:.4f} against "
            f"{null_p95:.4f})."
        ),
        **common,
    )


def chain_units(items: ScoredItems, threshold: float) -> tuple[list[str], np.ndarray]:
    """The clean-negative units a chain consumes from one file, and which fired.

    Items when the file is ungrouped; negative clusters, decided by their
    maximum, when it declares groups -- the unit certify counted (188).
    """
    labels, scores, groups = items.as_arrays()
    if groups is None:
        negative = labels == 0
        ids = [items.ids[i] for i in np.flatnonzero(negative)]
        return ids, scores[negative] >= threshold
    keys, maxima = negative_cluster_units(scores, labels, groups, source=items.source)
    return [str(k) for k in keys], maxima >= threshold


def require_chain_replaced(result: RecheckResult) -> None:
    """Raise if a chained result still carries one file's label-error counts (198 review, c).

    :func:`apply_chain` replaces them; this makes that structural, so a path that
    builds a chained result some other way fails before a record is written
    rather than publishing a per-file count that reads as the chain's.
    """
    sensitivity = result.label_sensitivity
    if sensitivity is not None and sensitivity.computed:
        raise RuntimeError(
            "a chained recheck carries per-file label-error counts; apply_chain must "
            "replace them (DECISIONS 198)"
        )
    if result.second_review is not None and result.second_review.disputes is not None:
        raise RuntimeError(
            "a chained recheck carries per-file label_2 disputes; apply_chain must "
            "replace them (DECISIONS 198)"
        )


def apply_revoked_chain_head(result: RecheckResult, revoked_at: str) -> RecheckResult:
    """What an unchained recheck reports when the chain already revoked (210).

    The measurement is kept in full -- the bound, the floor, the drift verdict,
    the label evidence are why the command was run -- and the status becomes the
    warrant's recorded lifecycle, because a ``VALID`` here would be read by
    anything that reads a status field and does not read a note.

    Args:
        result: The verdict computed from this file alone.
        revoked_at: How to name the revoking record, e.g. ``"record 0002"``.

    Returns:
        The same measurement, reported as REVOKED and saying where from.
    """
    return dataclasses.replace(
        result,
        status=WarrantStatus.REVOKED,
        chain_revoked_at=revoked_at,
        reason=(
            f"this warrant's chain REVOKED it at {revoked_at}, so the warrant is "
            f"not live and this file cannot restore it: re-certify. The "
            f"measurement below is what this file says on its own, and it is "
            f"reported in full -- the original verdict here was "
            f"{result.status.value}: {result.reason}"
        ),
    )


def apply_chain(result: RecheckResult, fed: Any) -> RecheckResult:
    """The verdict a recheck carries when it is one link of a chain (DECISIONS 193, 194).

    The chain's statistic is what can revoke on the bound: one file's lower
    bound clearing the budget is one test of many in a year, and in a chain it
    is reported as evidence -- STALE -- not as a revocation. **A drift revocation
    is a different claim and stands**, whatever the bound did: it is read from
    the result's separate drift verdict, because the bound-first verdict hides it
    when both fire (194, F1) or an inconclusive FPR warning fires first (205).
    Every reason says where the chain is, whether this
    file's units all reached it, and whether it has ended (194, F2).
    """
    from .labels import chained_sensitivity

    # 198: a per-file count would read as the chain's, which it is not.
    result = dataclasses.replace(
        result,
        label_sensitivity=chained_sensitivity(),
        second_review=(
            dataclasses.replace(
                result.second_review, disputes=None,
                disputes_reason=chained_sensitivity().reason,
            )
            if result.second_review is not None else None
        ),
    )
    state = fed.state
    notes = [
        f"In the chain: statistic {state.mean_statistic:,.1f} against a revocation "
        f"threshold of {state.threshold:,.0f}, after {state.units_consumed:,} of "
        f"{state.horizon_units:,} units."
    ]
    if fed.units_not_consumed:
        notes.append(
            f"{fed.units_not_consumed:,} of this file's {fed.units_in_file:,} units were "
            "not consumed -- past the horizon, or after the chain revoked -- and the "
            "chain has not seen them."
        )
    if state.ended and state.revoked_at_unit is None:
        notes.append("The chain has consumed its units; re-certify before relying on it further.")
    suffix = " " + " ".join(notes)

    if state.revoked_at_unit is not None:
        return dataclasses.replace(
            result,
            status=WarrantStatus.REVOKED,
            reason=(
                f"the chain of rechecks has established a breach: its statistic "
                f"reached {state.threshold:,.0f} at unit {state.revoked_at_unit:,} of "
                f"{state.horizon_units:,}. Across the whole chain, a detector keeping "
                f"its promise is revoked this way with probability at most "
                f"{state.alpha:g}." + suffix
            ),
        )
    if result.drift_verdict == "REVOKED":
        bound_note = (
            " This file's bound also breaks, which in a chain is evidence rather "
            "than a revocation." if result.bound_still_holds is False else ""
        )
        return dataclasses.replace(
            result,
            status=WarrantStatus.REVOKED,
            reason=(
                f"the score distribution has moved (PSI {result.psi:.4f}, beyond "
                f"both the significant band and this sample's noise level of "
                f"{result.psi_null_p95:.4f}): the warrant describes traffic you no "
                f"longer have. That is a separate claim from the chain's, and it "
                f"stands." + bound_note + suffix
            ),
        )
    if result.bound_still_holds is False:
        return dataclasses.replace(
            result,
            status=WarrantStatus.STALE,
            reason=(
                f"this file alone would revoke -- its lower bound "
                f"{result.fpr_lower_bound_now:.4f} exceeds the {result.budget:.4f} "
                f"budget -- but in a chain one file is one test of many, and the "
                f"chain has not established a breach. Evidence, not a revocation."
                + suffix
            ),
        )
    return dataclasses.replace(result, reason=result.reason + suffix)
