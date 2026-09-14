"""The frontier certifies what `certify` certifies, on grouped files too. DECISIONS.md 190.

`frontier` dropped the `group` column and certified at item level. On a grouped
file it reported budgets as certified that `certify --budget` refuses, and at a
budget both certified it quoted a lower threshold than the warrant `certify`
issues. The frontier is what a customer chooses a budget from, so a row there
reading "certified" is a promise; these tests hold it to the command that makes
the promise.

They compare against `certify_items` end to end, not against the shared step
both now call, so a future second copy of that step would still be caught.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.intake import certify_items, frontier, load_scored_items, render_frontier
from controlplane.validation.warrant_stats import certify_fpr

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: Budgets where the grouped file below separates item-level from cluster-level
#: certification (0.01, 0.02) and where both certify (0.03).
BUDGETS = (0.01, 0.02, 0.03)


def _grouped_csv(path: Path, *, groups: int = 150, size: int = 4, seed: int = 7,
                 unequal: bool = False) -> Path:
    """Clustered scores: members of a group share a level, so they are not independent."""
    rng = np.random.default_rng(seed)
    rows = ["id,label,score,group"]
    item = 0
    for g in range(groups):
        label = int(rng.random() < 0.3)
        level = rng.normal(1.9 * label, 1)
        members = size + (size if unequal and g == 0 else 0)
        for _ in range(members):
            score = 1 / (1 + np.exp(-(level + rng.normal(0, 0.2))))
            rows.append(f"i{item},{label},{score:.6f},g{g}")
            item += 1
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _ungrouped_csv(path: Path, n: int = 600, seed: int = 7) -> Path:
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < 0.25).astype(int)
    scores = 1 / (1 + np.exp(-(rng.normal(0, 1, n) + 1.9 * labels)))
    path.write_text(
        "id,label,score\n"
        + "".join(f"i{i},{l},{s:.6f}\n" for i, (l, s) in enumerate(zip(labels, scores, strict=True))),
        encoding="utf-8",
    )
    return path


def test_the_grouped_file_really_separates_the_two_units(tmp_path) -> None:
    """Without this, agreement below could hold on a file where the unit never mattered."""
    items = load_scored_items(_grouped_csv(tmp_path / "g.csv"))
    labels, scores, groups = items.as_arrays()
    negatives = scores[labels == 0]
    item_level = certify_fpr(negatives, 0.02, alpha=0.05)
    cluster_level = certify_fpr(negatives, 0.02, alpha=0.05, cluster_ids=groups[labels == 0])
    assert item_level.fpr_certified and not cluster_level.fpr_certified


@pytest.mark.parametrize("kind", ["grouped", "ungrouped"])
def test_every_frontier_row_matches_certify(tmp_path, config, kind) -> None:
    path = (_grouped_csv if kind == "grouped" else _ungrouped_csv)(tmp_path / f"{kind}.csv")
    items = load_scored_items(path)
    rows = {point.budget: point for point in frontier(config, items, grid=BUDGETS)}
    # The frontier certifies each row at the family level split across its grid
    # (DECISIONS 192), so it agrees with certify at that level.
    row_alpha = (1 - config.validation.ci) / len(BUDGETS)
    for budget in BUDGETS:
        warrant = certify_items(config, items, budget=budget, alpha=row_alpha)
        row = rows[budget]
        assert row.certified == warrant.certified, (
            f"{kind} budget {budget}: frontier says certified={row.certified}, "
            f"certify says {warrant.status.value}"
        )
        assert row.threshold == warrant.threshold, (
            f"{kind} budget {budget}: frontier threshold {row.threshold}, "
            f"certify threshold {warrant.threshold}"
        )
        assert row.negative_units == warrant.negative_units
        assert row.min_negatives_required == warrant.min_units_required


def test_unequal_groups_are_refused_by_the_frontier_as_by_certify(tmp_path, config) -> None:
    items = load_scored_items(_grouped_csv(tmp_path / "u.csv", unequal=True))
    with pytest.raises(ValueError, match="unequal group sizes"):
        certify_items(config, items, budget=0.05)
    with pytest.raises(ValueError, match="unequal group sizes"):
        frontier(config, items)


def test_the_cli_frontier_exits_two_on_unequal_groups(tmp_path) -> None:
    path = _grouped_csv(tmp_path / "u.csv", unequal=True)
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), "certify", "-i", str(path),
         "--frontier", "-q", "-o", str(tmp_path / "f.json")],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 2, result.stderr
    assert "unequal group sizes" in result.stderr
    assert not (tmp_path / "f.json").exists()


def test_a_refused_grouped_row_names_clusters_not_items(tmp_path, config) -> None:
    items = load_scored_items(_grouped_csv(tmp_path / "g.csv"))
    points = frontier(config, items, grid=(0.02,))
    assert not points[0].certified
    text = render_frontier(points, n_positive=items.n_positive, n_negative=items.n_negative)
    assert f"independent negative clusters, this file has {points[0].negative_units}" in text
    assert f"this file has {items.n_negative}" not in text, (
        "the item count is the number that made the old frontier certify; printing "
        "it beside a cluster requirement invites the same misreading"
    )
    assert points[0].to_payload()["unit"] == "negative cluster"
