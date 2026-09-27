"""The two findings still open in read-only code, as tests that run.

`reports/PROJECT-REVIEW-2026-09-23.md` left ten findings. Eight are closed. The
two that remain are in zones `CLAUDE.md` marks read-only -- ``validation/stats.py``
and ``validation/warrant_stats.py`` -- where the rule is *read and call, do not
modify, report suspected bugs as OPEN items*.

A defect described in prose is checked by nobody. These are that report, executed:
each one states the property the code is supposed to have, is reproduced here, and
is marked **strict** xfail. Strict means that the day an owner repairs the
behaviour, the suite fails on the unexpected pass and whoever fixed it has to come
here, delete the marker and close the finding. That is the intended way out.

**These are not a repair and they are not a design.** R2 in particular must not be
closed by replacing a row count with a group count: the review is explicit that the
estimand has to be defined first, by an owner who is not the implementer. What is
asserted below is only the weaker property both the review and `CLAUDE.md` already
commit to -- that copying rows cannot buy evidence.
"""

from __future__ import annotations

import numpy as np
import pytest

from controlplane.config import load_config
from controlplane.validation.metrics_builder import build_warrant_metrics
from controlplane.validation.warrant_stats import FPRMonitor

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return load_config(str(PROJECT_ROOT / "config.yaml"))


def _homogeneous_groups(rows_per_group: int):
    """60 negative groups and 4 positive groups, perfectly separated.

    Homogeneous within a group, so duplicating rows changes no group's label and
    adds no independent unit -- the construction the review specifies.
    """
    labels, scores, groups = [], [], []
    for index in range(60):
        labels += [0] * rows_per_group
        scores += [0.1] * rows_per_group
        groups += [f"neg-{index}"] * rows_per_group
    for index in range(4):
        labels += [1] * rows_per_group
        scores += [0.9] * rows_per_group
        groups += [f"pos-{index}"] * rows_per_group
    return np.array(labels), np.array(scores), np.array(groups)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "R2 of reports/PROJECT-REVIEW-2026-09-23.md: validation/stats.py falls back "
        "from a degenerate grouped bootstrap to a row-level Clopper-Pearson "
        "interval, and metrics_builder supplies a row denominator, so repeating "
        "every row tightens the bound. Measured here: 0.3976353644 at one row per "
        "group, 0.9908201954 at a hundred, from the same four positive groups. "
        "validation/stats.py is read-only; this needs an owner and a defined "
        "estimand, not a row count swapped for a group count. When this passes, "
        "strict mode fails it: close R2 and delete the marker."
    ),
)
def test_duplicating_rows_does_not_tighten_a_grouped_bound(config) -> None:
    """The property: evidence comes from independent units, not from copies."""
    single = build_warrant_metrics(config, *_homogeneous_groups(1), threshold=0.5)
    duplicated = build_warrant_metrics(config, *_homogeneous_groups(100), threshold=0.5)

    for quantity in ("recall", "precision"):
        once = getattr(single, quantity)
        many = getattr(duplicated, quantity)
        assert many.ci_low == pytest.approx(once.ci_low, abs=1e-9), (
            f"{quantity}'s lower limit moved from {once.ci_low} to {many.ci_low} "
            "by copying rows inside the same groups"
        )
        assert many.n == once.n, (
            f"{quantity}'s n went {once.n} -> {many.n}: the denominator is rows, "
            "and the file declared 64 independent groups"
        )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "R10 of reports/PROJECT-REVIEW-2026-09-23.md, first reported in PHASE-12 "
        "1.5: FPRMonitor.wealth caps on a component maximum, so after two false "
        "positives it reports 20.0 and revokes while the mean of its component "
        "wealths -- the mixture its docstring states Ville's inequality over -- is "
        "14.205850. validation/warrant_stats.py is read-only; this needs an owner "
        "and an independent stopping-rule review. When this passes, strict mode "
        "fails it: close R10 and delete the marker."
    ),
)
def test_the_monitor_revokes_on_the_mixture_it_documents() -> None:
    """The property: the statistic that stops is the statistic that is bounded."""
    monitor = FPRMonitor(p0=0.05, alpha=0.05)
    for _ in range(2):
        monitor.update(1)

    mixture_mean = float(np.mean(np.exp(np.asarray(monitor._logw))))  # noqa: SLF001
    boundary = 1.0 / 0.05
    assert not monitor.revoked or mixture_mean >= boundary, (
        f"revoked with the documented mixture at {mixture_mean:.6f}, below the "
        f"{boundary} boundary the guarantee is stated for"
    )
