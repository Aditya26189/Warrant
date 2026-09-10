"""The frontier: the whole curve, in quantities that need no interval.

The design decision under test is the one that makes it usable at all. Every
rate this project publishes carries a bootstrap interval, and bootstrapping
twenty grid points takes about two minutes on a small file. Rather than narrow
the intervals for one view -- which would make a frontier disagree with the
warrant beside it -- the frontier reports only what is **exact**: counts of this
file, and Clopper-Pearson bounds.

That is `CLAUDE.md`'s central distinction used as a feature: yield is exact,
rate is estimated.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.intake import frontier, load_scored_items, render_frontier

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _csv(tmp_path: Path, n=600, separation=1.9, base=0.25, seed=7, name="f.csv") -> Path:
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < base).astype(int)
    scores = 1 / (1 + np.exp(-(rng.normal(0, 1, n) + separation * labels)))
    path = tmp_path / name
    path.write_text(
        "id,label,score\n"
        + "\n".join(f"i{i},{int(l)},{s:.6f}" for i, (s, l) in enumerate(zip(scores, labels)))
        + "\n",
        encoding="utf-8",
    )
    return path


def test_the_frontier_reports_only_exact_quantities(tmp_path, config) -> None:
    """No field may be an estimate, because none of them carries an interval."""
    items = load_scored_items(_csv(tmp_path))
    points = frontier(config, items)
    for point in points:
        payload = point.to_payload()
        assert "recall" not in payload and "precision" not in payload, (
            "a rate reached the frontier. Rates are estimated and would need an "
            "interval; the frontier exists precisely to avoid paying for twenty "
            "bootstraps"
        )
        if point.certified:
            counts = payload["counts_exact"]
            assert all(isinstance(v, int) for v in counts.values())


def test_the_counts_are_internally_consistent(tmp_path, config) -> None:
    """caught + missed is the positive total; caught + false+ is the flagged total."""
    items = load_scored_items(_csv(tmp_path))
    points = frontier(config, items)
    certified = [p for p in points if p.certified]
    assert certified, "the fixture certified nothing; the test would prove nothing"
    for p in certified:
        assert p.true_positives + p.missed == items.n_positive
        assert p.true_positives + p.false_positives == p.n_flagged


def test_a_looser_budget_never_catches_less(tmp_path, config) -> None:
    """The curve must be monotone, or the certification is not ordering thresholds."""
    items = load_scored_items(_csv(tmp_path))
    certified = [p for p in frontier(config, items) if p.certified]
    caught = [p.true_positives for p in certified]
    flagged = [p.n_flagged for p in certified]
    assert caught == sorted(caught), f"catching fell as the budget loosened: {caught}"
    assert flagged == sorted(flagged), f"flagging fell as the budget loosened: {flagged}"


def test_a_refused_budget_keeps_its_row_and_says_what_it_needs(tmp_path, config) -> None:
    """Dropping it turns a fact about the evidence into an apparent oversight."""
    items = load_scored_items(_csv(tmp_path, n=120))
    points = frontier(config, items)
    refused = [p for p in points if not p.certified]
    assert refused, "a 120-row file should refuse the tightest budgets"
    for p in refused:
        assert p.min_negatives_required > items.n_negative
        assert p.threshold is None and p.n_flagged is None

    text = render_frontier(points, n_positive=items.n_positive, n_negative=items.n_negative)
    assert "REFUSED" in text and "clean negatives" in text


def test_the_rendering_says_where_rates_come_from(tmp_path, config) -> None:
    """A table with no intervals must explain that none is missing."""
    items = load_scored_items(_csv(tmp_path))
    text = render_frontier(
        frontier(config, items), n_positive=items.n_positive, n_negative=items.n_negative
    )
    assert "EXACT" in text
    assert "--budget" in text, "the reader is not told how to get rates"
    text.encode("ascii")


def test_the_frontier_is_fast_enough_to_wait_for(tmp_path, config) -> None:
    """The whole reason it reports counts.

    Twenty bootstrapped grid points take about two minutes on a file this size.
    If the frontier ever starts bootstrapping, this fails.
    """
    import time

    items = load_scored_items(_csv(tmp_path))
    start = time.time()
    frontier(config, items)
    assert time.time() - start < 20, (
        "the frontier got slow, which usually means it started estimating rates"
    )


def test_the_cli_frontier_runs_and_writes_a_record(tmp_path) -> None:
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), "certify",
         "-i", str(_csv(tmp_path)), "--frontier", "-o", str(tmp_path / "f.json")],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stderr
    assert "THE FRONTIER" in result.stdout
    payload = json.loads((tmp_path / "f.json").read_text(encoding="utf-8"))
    assert payload["frontier"] and payload["input"]["n"] == 600


def test_certify_without_a_budget_or_frontier_says_which_to_use(tmp_path) -> None:
    """--budget stopped being required, so the error has to be actionable."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), "certify",
         "-i", str(_csv(tmp_path))],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900,
    )
    assert result.returncode == 2
    assert "--frontier" in result.stderr
