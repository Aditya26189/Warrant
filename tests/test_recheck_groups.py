"""A grouped warrant is rechecked in the unit it was certified in (DECISIONS.md 188).

`certify` on a file with a `group` column bounds the false-positive rate over
negative clusters. `recheck` used to discard the column and re-test item by item
-- a different rate, at an inflated sample size. These tests hold the recheck to
certify's unit, and show the verdict the old behaviour got wrong.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.economics.sizing import revocation_probability
from controlplane.intake import load_scored_items, recheck_items
from controlplane.intake.recheck import negative_cluster_maxima, smallest_detectable_breach
from controlplane.model import WarrantStatus

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUDGET, THRESHOLD = 0.05, 0.5


def _grouped_csv(path: Path, *, firing_clusters: int, clusters: int = 40, size: int = 10,
                 positive_clusters: int = 10, sizes: list[int] | None = None) -> Path:
    """Negative clusters whose members share a fate: all fire or none do.

    That is the dependence a `group` column declares -- several items from one
    source document, which a detector gets right or wrong together.
    """
    rows = ["id,label,score,group"]
    item = 0
    sizes = sizes or [size] * clusters
    for c, n in enumerate(sizes):
        score = 0.9 if c < firing_clusters else 0.1
        for _ in range(n):
            rows.append(f"i{item},0,{score},neg{c}")
            item += 1
    for c in range(positive_clusters):
        for _ in range(size):
            rows.append(f"i{item},1,0.95,pos{c}")
            item += 1
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_the_recheck_counts_clusters_not_items(tmp_path, config) -> None:
    items = load_scored_items(_grouped_csv(tmp_path / "g.csv", firing_clusters=4))
    result = recheck_items(config, items, budget=BUDGET, threshold=THRESHOLD)
    assert result.unit == "cluster"
    assert result.n_negative_now == 40
    assert result.achieved_fpr_now == pytest.approx(4 / 40)
    assert result.to_payload()["now"]["unit"] == "cluster"


def test_correlated_false_positives_no_longer_revoke_on_an_inflated_n(tmp_path, config) -> None:
    """The verdict the defect got wrong, pinned in both units.

    Four whole clusters fire: 40 false positives in 400 negative items, or 4 in
    40 clusters. Per item, the lower bound clears the budget and the warrant is
    revoked. Per cluster -- the unit the promise was made in -- 4 of 40 does not
    establish a breach, and the right answer is STALE, not REVOKED.
    """
    from controlplane.intake.recheck import _lower_bound_at

    alpha = 1.0 - config.validation.ci
    assert _lower_bound_at(400, 40, alpha) > BUDGET, "the item-level test would revoke"
    assert _lower_bound_at(40, 4, alpha) <= BUDGET

    items = load_scored_items(_grouped_csv(tmp_path / "g.csv", firing_clusters=4))
    result = recheck_items(config, items, budget=BUDGET, threshold=THRESHOLD)
    assert result.status is WarrantStatus.STALE
    assert result.bound_still_holds is True


def test_floor_and_power_are_quoted_at_the_cluster_count(tmp_path, config) -> None:
    """Quoting power at the item count would overstate what the file can catch."""
    alpha = 1.0 - config.validation.ci
    items = load_scored_items(_grouped_csv(tmp_path / "g.csv", firing_clusters=0, clusters=120))
    result = recheck_items(config, items, budget=BUDGET, threshold=THRESHOLD)
    assert result.detectable_floor == smallest_detectable_breach(120, BUDGET, alpha)
    expected = float(revocation_probability(np.array([120]), BUDGET * 1.5, BUDGET, alpha)[0])
    assert result.power_against_1_5x_budget == pytest.approx(expected)
    at_items = float(revocation_probability(np.array([1200]), BUDGET * 1.5, BUDGET, alpha)[0])
    assert result.power_against_1_5x_budget < at_items


def test_drift_is_not_assessed_on_a_grouped_file(tmp_path, config) -> None:
    from controlplane.intake import score_distribution

    items = load_scored_items(_grouped_csv(tmp_path / "g.csv", firing_clusters=2, clusters=60))
    _, scores, _ = items.as_arrays()
    result = recheck_items(config, items, budget=BUDGET, threshold=THRESHOLD,
                           reference=score_distribution(scores))
    assert result.drift_assessed is False
    assert "declares groups" in result.drift_not_assessed_reason


def test_unequal_negative_clusters_are_refused() -> None:
    scores = np.array([0.1, 0.2, 0.9, 0.3])
    labels = np.array([0, 0, 0, 0])
    groups = np.array(["a", "a", "b", "c"])
    with pytest.raises(ValueError, match="unequal negative cluster sizes"):
        negative_cluster_maxima(scores, labels, groups, source="f.csv")


def test_a_cluster_fires_on_its_maximum() -> None:
    scores = np.array([0.1, 0.8, 0.2, 0.3, 0.99, 0.0])
    labels = np.array([0, 0, 0, 0, 1, 1])
    groups = np.array(["a", "a", "b", "b", "a", "b"])
    assert sorted(negative_cluster_maxima(scores, labels, groups, source="f").tolist()) == [0.3, 0.8]


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=600,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def _record(path: Path, *, grouped: bool) -> Path:
    path.write_text(json.dumps({
        "status": "VALID", "budget_fpr": BUDGET, "alpha": 0.05,
        "input": {"grouped": grouped},
        "certification": {"threshold": THRESHOLD}, "score_distribution": None,
    }), encoding="utf-8")
    return path


def test_a_grouped_warrant_rechecked_without_groups_is_refused(tmp_path) -> None:
    flat = tmp_path / "flat.csv"
    flat.write_text("id,label,score\n" + "\n".join(
        f"i{i},{int(i % 4 == 0)},{0.1 + 0.8 * (i % 4 == 0)}" for i in range(80)
    ) + "\n", encoding="utf-8")
    result = _run("recheck", "-w", str(_record(tmp_path / "g.warrant.json", grouped=True)),
                  "-i", str(flat), "-q", "-o", str(tmp_path / "r.json"))
    assert result.returncode == 2
    assert "certified on clusters" in result.stderr
    assert not (tmp_path / "r.json").exists()


def test_an_ungrouped_warrant_rechecked_with_groups_is_refused(tmp_path) -> None:
    grouped = _grouped_csv(tmp_path / "g.csv", firing_clusters=1)
    result = _run("recheck", "-w", str(_record(tmp_path / "f.warrant.json", grouped=False)),
                  "-i", str(grouped), "-q", "-o", str(tmp_path / "r.json"))
    assert result.returncode == 2
    assert "certified on independent items" in result.stderr


def test_unequal_clusters_exit_2_from_the_command_line(tmp_path) -> None:
    uneven = _grouped_csv(tmp_path / "u.csv", firing_clusters=1, clusters=3, sizes=[10, 10, 9])
    result = _run("recheck", "-w", str(_record(tmp_path / "g.warrant.json", grouped=True)),
                  "-i", str(uneven), "-q", "-o", str(tmp_path / "r.json"))
    assert result.returncode == 2
    assert "unequal negative cluster sizes" in result.stderr
