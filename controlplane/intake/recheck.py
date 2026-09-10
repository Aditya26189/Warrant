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

__all__ = ["RecheckResult", "recheck_items", "score_distribution"]

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
    psi: Optional[float] = None
    psi_null_p95: Optional[float] = None
    psi_beyond_noise: Optional[bool] = None
    drift_assessed: bool = False
    drift_not_assessed_reason: str = ""

    @property
    def still_valid(self) -> bool:
        return self.status is WarrantStatus.VALID

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "prior_warrant": {"budget_fpr": self.budget, "threshold": self.threshold},
            "now": {
                "n": self.n_now,
                "n_negative": self.n_negative_now,
                "achieved_fpr": self.achieved_fpr_now,
                "fpr_upper_bound": self.fpr_upper_bound_now,
                "fpr_lower_bound": self.fpr_lower_bound_now,
                "bound_still_holds": self.bound_still_holds,
            },
            "drift": {
                "assessed": self.drift_assessed,
                "not_assessed_reason": self.drift_not_assessed_reason,
                "psi": self.psi,
                "psi_null_p95": self.psi_null_p95,
                "beyond_noise": self.psi_beyond_noise,
                "note": (
                    "PSI is compared against a null simulated at this file's own "
                    "sample size, not against the 0.10/0.25 folklore bands, which "
                    "are not scale-free (DECISIONS 070)."
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
        alpha: Certification level; defaults to ``1 - config.validation.ci``.

    Returns:
        The verdict, with both failure modes reported separately.
    """
    alpha = (1.0 - config.validation.ci) if alpha is None else alpha
    labels, scores, _ = items.as_arrays()
    negatives = scores[labels == 0]

    # --- has the bound broken? ------------------------------------------
    bound_holds: Optional[bool] = None
    achieved: Optional[float] = None
    upper: Optional[float] = None
    lower: Optional[float] = None
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

    # --- has the ground moved? ------------------------------------------
    psi = null_p95 = None
    beyond_noise: Optional[bool] = None
    assessed = False
    skip_reason = ""
    if reference is None:
        skip_reason = (
            "the prior warrant carries no score distribution, so there is "
            "nothing to compare against"
        )
    elif items.n < MIN_ITEMS_FOR_DRIFT:
        skip_reason = (
            f"{items.n} items is below the {MIN_ITEMS_FOR_DRIFT} needed before a "
            "drift verdict means anything; a shift indistinguishable from "
            "resampling is not a finding"
        )
    else:
        from ..drift import population_stability_index, simulate_null_psi

        psi = float(population_stability_index(reference, scores.tolist()).psi)
        band = simulate_null_psi(
            reference.bin_probabilities,
            n=items.n,
            n_reference=items.n,
            stable_band=config.drift.psi_stable,
        )
        null_p95 = float(band.p95)
        beyond_noise = psi > null_p95
        assessed = True

    return _verdict(
        config, budget, threshold, items, achieved, upper, lower, bound_holds,
        psi, null_p95, beyond_noise, assessed, skip_reason,
    )


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


def _verdict(
    config: Config,
    budget: float,
    threshold: float,
    items: ScoredItems,
    achieved: Optional[float],
    upper: Optional[float],
    lower: Optional[float],
    bound_holds: Optional[bool],
    psi: Optional[float],
    null_p95: Optional[float],
    beyond_noise: Optional[bool],
    assessed: bool,
    skip_reason: str,
) -> RecheckResult:
    """Decide, worst finding first.

    A broken bound outranks a moved distribution: the first is the promise being
    measurably false today, the second is a reason to doubt that it will hold
    tomorrow.
    """
    common = dict(
        budget=budget, threshold=threshold, n_now=items.n,
        n_negative_now=items.n_negative, achieved_fpr_now=achieved,
        fpr_upper_bound_now=upper, fpr_lower_bound_now=lower,
        bound_still_holds=bound_holds,
        psi=psi, psi_null_p95=null_p95, psi_beyond_noise=beyond_noise,
        drift_assessed=assessed, drift_not_assessed_reason=skip_reason,
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
    if assessed and psi is not None and psi >= config.drift.psi_significant and beyond_noise:
        return RecheckResult(
            status=WarrantStatus.REVOKED,
            reason=(
                f"the bound still holds, but the score distribution has moved "
                f"(PSI {psi:.4f}, beyond both the {config.drift.psi_significant} "
                f"band and this sample's own noise level of {null_p95:.4f}). The "
                f"warrant describes traffic you no longer have."
            ),
            **common,
        )
    if assessed and psi is not None and psi >= config.drift.psi_stable and beyond_noise:
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
