"""The lift interval's lower bound is conservative on every shipped artifact.

``WarrantMetrics.lift`` divides recall's interval by the measured flag rate,
holding the flag rate fixed. Its docstring once justified that by calling the
flag rate's uncertainty an order of magnitude smaller, which the artifacts
contradict (relative half-widths 0.36-0.40 against recall's 0.38-0.40). The
lower bound is still safe, for a different reason: recall and flag rate move
together, so the ratio varies less than recall. ``issuance.py`` refuses on that
lower bound, which makes this the property the refusal bar rests on, and a
docstring is not a control (``DECISIONS.md`` 169).

The joint bootstrap resamples items as a multinomial over the four cells of the
confusion table the artifact's counts define: positives from ``base_rate``,
flagged items and true positives from ``confirmed_errors``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from controlplane.config import load_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = sorted((PROJECT_ROOT / "results").glob("validation-T1-*.json"))
DRAWS = 2000


def _joint_lift_interval(n: int, positives: int, flagged: int, tp: int, seed: int) -> tuple[float, float]:
    fn, fp = positives - tp, flagged - tp
    tn = n - tp - fn - fp
    assert min(tp, fn, fp, tn) >= 0, "artifact counts do not form a confusion table"
    rng = np.random.default_rng(seed)
    cells = rng.multinomial(n, np.array([tp, fn, fp, tn]) / n, size=DRAWS)
    tp_b, fn_b, fp_b = cells[:, 0], cells[:, 1], cells[:, 2]
    ok = (tp_b + fn_b > 0) & (tp_b + fp_b > 0)
    lift = (tp_b[ok] / (tp_b[ok] + fn_b[ok])) / ((tp_b[ok] + fp_b[ok]) / n)
    low, high = np.percentile(lift, [2.5, 97.5])
    return float(low), float(high)


def test_there_are_artifacts_to_check() -> None:
    assert ARTIFACTS, "no results/validation-T1-*.json; the property below checks nothing"


@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.stem)
def test_the_shipped_lift_lower_bound_does_not_exceed_the_joint_one(path: Path) -> None:
    seed = load_config(str(PROJECT_ROOT / "config.yaml")).seed
    metrics = json.loads(path.read_text(encoding="utf-8"))["metrics"]
    base_rate = json.loads(path.read_text(encoding="utf-8"))["base_rate"]
    recall, flag = metrics["recall"], metrics["flag_rate"]
    n = int(recall["n"])
    positives = int(round(base_rate * n))
    flagged = int(metrics["confirmed_errors"]["n"])
    tp = int(metrics["confirmed_errors"]["value"])

    # The artifact's own recall and flag rate must be what the counts say, or
    # the reconstruction below is checking a different table.
    assert tp / positives == pytest.approx(recall["value"], abs=1e-9)
    assert flagged / n == pytest.approx(flag["value"], abs=1e-9)

    shipped_low = recall["ci_low"] / flag["value"]
    joint_low, _ = _joint_lift_interval(n, positives, flagged, tp, seed)
    assert shipped_low <= joint_low, (
        f"{path.name}: the shipped lift lower bound {shipped_low:.3f} is above a "
        f"joint bootstrap's {joint_low:.3f}, so holding the flag rate fixed is no "
        "longer conservative and the refusal bar can issue a warrant it should not"
    )
