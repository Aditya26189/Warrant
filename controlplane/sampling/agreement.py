"""Cohen's kappa, published next to every warrant it qualifies.

``CLAUDE.md``: *a +/-5pp recall interval is meaningless at inter-rater
kappa = 0.5.*

The reason is that every interval this project publishes is a statement about
**sampling** error and nothing else. It answers "how much would this number move
if I drew a different sample?" It is silent on "how much would it move if a
different person reviewed the same sample?" -- and at kappa 0.5 the second
question has the larger answer. A narrow interval over labels two reviewers
disagree about is a precise measurement of one reviewer's opinion.

**Kappa is reported with an interval of its own**, because it is estimated from
a handful of doubly-labelled items and a point estimate of an agreement
statistic is exactly the kind of unbacked number this repository refuses
elsewhere. The interval is a percentile bootstrap over the paired items, which
is the resampling unit: the pair is what was observed, and resampling labels
independently would break the pairing that kappa is about.

**Kappa is undefined, not 1.0, when both reviewers agree on everything and the
category is constant.** With one category used, expected agreement is 1, so
``(p_o - p_e)/(1 - p_e)`` is ``0/0``. Returning 1.0 there reports perfect
agreement from evidence that contains no disagreement to detect, which is the
same error as a bootstrap interval of ``[0, 0]`` from 200 clean negatives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

__all__ = ["Agreement", "AgreementError", "cohens_kappa"]


class AgreementError(ValueError):
    """Agreement was requested from evidence that cannot support it."""


@dataclass(frozen=True)
class Agreement:
    """Inter-rater agreement over the doubly-labelled subset.

    Attributes:
        kappa: Cohen's kappa, or ``None`` when it is undefined.
        ci_low: Lower percentile-bootstrap bound. ``None`` when kappa is.
        ci_high: Upper bound.
        n_pairs: Items labelled by both reviewers.
        observed_agreement: ``p_o``, the raw share the reviewers agreed on.
            Reported because it is what people mean by "agreement" and kappa is
            routinely mistaken for it.
        expected_agreement: ``p_e``, the share chance alone would produce given
            each reviewer's marginal rate.
        undefined_reason: Why kappa is ``None``, when it is.
        interpretation: A plain-language band, with the caveat that the bands
            are conventional rather than derived.
    """

    kappa: Optional[float]
    ci_low: Optional[float]
    ci_high: Optional[float]
    n_pairs: int
    observed_agreement: float
    expected_agreement: float
    undefined_reason: str = ""
    interpretation: str = ""

    def render(self) -> str:
        """One block, with the raw agreement beside kappa so neither is read as the other."""
        if self.kappa is None:
            return (
                f"Cohen's kappa: UNDEFINED over {self.n_pairs} pairs\n"
                f"    {self.undefined_reason}\n"
                f"    raw agreement {self.observed_agreement:.4f}"
            )
        return (
            f"Cohen's kappa: {self.kappa:.4f} "
            f"[{self.ci_low:.4f}, {self.ci_high:.4f}] "
            f"(95% CI, {self.n_pairs} pairs) -- {self.interpretation}\n"
            f"    raw agreement {self.observed_agreement:.4f}, "
            f"chance agreement {self.expected_agreement:.4f}"
        )


def _kappa(first: Sequence[int], second: Sequence[int]) -> tuple[float, float, Optional[float]]:
    """``(p_o, p_e, kappa)`` for two binary label vectors, kappa ``None`` if undefined."""
    n = len(first)
    agree = sum(1 for a, b in zip(first, second, strict=True) if a == b)
    p_o = agree / n
    p1 = sum(first) / n
    p2 = sum(second) / n
    p_e = p1 * p2 + (1.0 - p1) * (1.0 - p2)
    if abs(1.0 - p_e) < 1e-12:
        return p_o, p_e, None
    return p_o, p_e, (p_o - p_e) / (1.0 - p_e)


def _band(kappa: float) -> str:
    """Landis and Koch's conventional bands, named as conventions.

    These are a 1977 convention with no derivation behind them, widely quoted
    as though they were a result. The label is useful shorthand and it is said
    here to be shorthand.
    """
    if kappa < 0.0:
        return "worse than chance (Landis-Koch convention)"
    if kappa < 0.20:
        return "slight (Landis-Koch convention)"
    if kappa < 0.40:
        return "fair (Landis-Koch convention)"
    if kappa < 0.60:
        return "moderate (Landis-Koch convention)"
    if kappa < 0.80:
        return "substantial (Landis-Koch convention)"
    return "almost perfect (Landis-Koch convention)"


def cohens_kappa(
    first: Sequence[int],
    second: Sequence[int],
    *,
    seed: int = 1729,
    resamples: int = 2000,
    ci: float = 0.95,
) -> Agreement:
    """Agreement between two reviewers on the same items, with an interval.

    Quantity: Cohen's kappa on binary labels, where 1 means *incorrect* --
    ``config.yaml`` sets the positive class to ``incorrect`` and an inverted
    convention here would report agreement about a different question.
    Propagation: percentile bootstrap resampling **pairs**, 95% by default.

    Args:
        first: Reviewer one's labels, 0 or 1.
        second: Reviewer two's labels on the same items, in the same order.
        seed: Bootstrap seed, so the interval reproduces.
        resamples: Bootstrap resamples.
        ci: Coverage.

    Returns:
        The agreement, with kappa ``None`` where it is undefined.

    Raises:
        AgreementError: If the vectors differ in length, are empty, or contain
            anything but 0 and 1.
    """
    import numpy as np

    if len(first) != len(second):
        raise AgreementError(
            f"{len(first)} labels against {len(second)}. Kappa is computed over "
            "pairs, so the two reviewers must have labelled the same items."
        )
    if not first:
        raise AgreementError(
            "no doubly-labelled items. Agreement cannot be reported, and a "
            "warrant published without it carries a sampling interval that is "
            "silent about reviewer disagreement."
        )
    for name, labels in (("first", first), ("second", second)):
        bad = sorted({v for v in labels if v not in (0, 1)})
        if bad:
            raise AgreementError(
                f"{name} reviewer's labels contain {bad}; expected 0 or 1, "
                "where 1 is the positive class 'incorrect'."
            )

    p_o, p_e, kappa = _kappa(first, second)
    if kappa is None:
        return Agreement(
            kappa=None,
            ci_low=None,
            ci_high=None,
            n_pairs=len(first),
            observed_agreement=p_o,
            expected_agreement=p_e,
            undefined_reason=(
                "both reviewers used one category, so chance agreement is 1 and "
                "kappa is 0/0. This is not perfect agreement -- it is a set of "
                "items with no disagreement available to detect."
            ),
        )

    rng = np.random.default_rng(seed)
    a = np.asarray(first, dtype=np.int64)
    b = np.asarray(second, dtype=np.int64)
    n = a.size
    draws: list[float] = []
    for _ in range(resamples):
        idx = rng.integers(0, n, size=n)
        _, _, k = _kappa(a[idx].tolist(), b[idx].tolist())
        if k is not None:
            draws.append(k)
    if not draws:  # pragma: no cover - needs every resample degenerate
        raise AgreementError(
            "every bootstrap resample was degenerate, so kappa has no interval. "
            "This means the doubly-labelled subset is too small or too "
            "one-sided to support an agreement claim."
        )
    alpha = 1.0 - ci
    low = float(np.percentile(draws, 100 * alpha / 2))
    high = float(np.percentile(draws, 100 * (1 - alpha / 2)))
    return Agreement(
        kappa=kappa,
        ci_low=low,
        ci_high=high,
        n_pairs=n,
        observed_agreement=p_o,
        expected_agreement=p_e,
        interpretation=_band(kappa),
    )
