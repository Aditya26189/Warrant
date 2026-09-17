"""A budget picked off the frontier, certified at the frontier's level. DECISIONS.md 195.

192 made the frontier certify every row at ``alpha / len(grid)`` so a row chosen
after reading them all still holds. `certify --budget` on the same file did not
follow, so the warrant a customer took away was at the unadjusted level.
`--from-frontier` closes that, and these tests hold it to 195's criteria: the
warrant's threshold is the frontier row's, a pick that is not a pick is refused,
later tests run at the family level, and the input digest is the release path's.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.intake import certify_items, frontier, load_scored_items
from controlplane.intake.certify import input_sha256

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _ungrouped(path: Path, n: int = 800, seed: int = 7) -> Path:
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < 0.25).astype(int)
    scores = 1 / (1 + np.exp(-(rng.normal(0, 1, n) + 1.9 * labels)))
    path.write_text("id,label,score\n" + "".join(
        f"i{i},{l},{s:.6f}\n" for i, (l, s) in enumerate(zip(labels, scores, strict=True))),
        encoding="utf-8")
    return path


def _grouped(path: Path, groups: int = 300, size: int = 2, seed: int = 7) -> Path:
    rng = np.random.default_rng(seed)
    rows = ["id,label,score,group"]
    item = 0
    for g in range(groups):
        label = int(rng.random() < 0.3)
        level = rng.normal(1.9 * label, 1)
        for _ in range(size):
            rows.append(f"i{item},{label},{1 / (1 + np.exp(-(level + rng.normal(0, 0.2)))):.6f},g{g}")
            item += 1
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


# --------------------------------------------------------------------------- #
# The warrant is the frontier's row
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("shape", ["ungrouped", "grouped"])
def test_the_picked_warrant_carries_the_frontier_rows_threshold(tmp_path, config, shape) -> None:
    """Every certified row, through certify_items at the row level, in-process."""
    path = (_ungrouped if shape == "ungrouped" else _grouped)(tmp_path / f"{shape}.csv")
    items = load_scored_items(path)
    rows = [row for row in frontier(config, items) if row.certified]
    assert rows, f"the {shape} fixture certified nothing; the test would prove nothing"
    grid = [row.budget for row in frontier(config, items)]
    for row in rows[:3]:  # certify_items bootstraps; three rows keep this under a minute
        selection = {"from_frontier": "x", "grid": grid, "row_alpha": row.row_alpha,
                     "family_alpha": row.family_alpha}
        warrant = certify_items(config, items, budget=row.budget, alpha=row.row_alpha,
                                selection=selection)
        assert warrant.certified
        assert warrant.threshold == row.threshold, (shape, row.budget)
        payload = warrant.to_payload()
        assert payload["certification"]["alpha"] == row.row_alpha
        assert payload["alpha"] == row.family_alpha


def test_a_selection_at_the_wrong_level_is_refused(tmp_path, config) -> None:
    items = load_scored_items(_ungrouped(tmp_path / "f.csv"))
    with pytest.raises(ValueError, match="row_alpha"):
        certify_items(config, items, budget=0.05, alpha=0.05,
                      selection={"from_frontier": "x", "grid": [0.05], "row_alpha": 0.00625,
                                 "family_alpha": 0.05})


# --------------------------------------------------------------------------- #
# The command
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def picked(tmp_path_factory):
    """A frontier, a --from-frontier warrant and a plain one, through the CLI."""
    root = tmp_path_factory.mktemp("picked")
    data = _ungrouped(root / "f.csv")
    assert _run("certify", "-i", str(data), "--frontier", "-q").returncode == 0
    record = root / "f.csv.frontier.json"
    result = _run("certify", "-i", str(data), "-b", "0.05", "--from-frontier", str(record),
                  "-o", str(root / "picked.json"))
    assert result.returncode == 0, result.stderr
    plain = _run("certify", "-i", str(data), "-b", "0.05", "-o", str(root / "plain.json"))
    assert plain.returncode == 0, plain.stderr
    return root, result.stdout, plain.stdout


def test_the_cli_warrant_matches_the_frontier_row_and_names_its_levels(picked) -> None:
    root, stdout, _ = picked
    row = next(r for r in json.loads((root / "f.csv.frontier.json").read_text(encoding="utf-8"))["frontier"]
               if r["budget_fpr"] == 0.05)
    warrant = json.loads((root / "picked.json").read_text(encoding="utf-8"))
    assert warrant["certification"]["threshold"] == row["threshold"]
    assert warrant["certification"]["alpha"] == row["row_alpha"]
    assert warrant["alpha"] == row["family_alpha"]
    assert warrant["selection"]["grid"] and warrant["selection"]["from_frontier"]
    assert "only the false-positive bound is adjusted" in warrant["selection"]["metrics_note"].lower()
    assert "carry that pick's optimism" in warrant["reason"]
    assert "this certificate is at alpha" in stdout and "rechecks, plans and chains run at" in stdout


def test_the_default_is_unchanged_but_notices_the_frontier(picked) -> None:
    root, _, plain_stdout = picked
    plain = json.loads((root / "plain.json").read_text(encoding="utf-8"))
    picked_warrant = json.loads((root / "picked.json").read_text(encoding="utf-8"))
    assert plain["selection"] is None
    assert plain["alpha"] == plain["certification"]["alpha"]
    assert plain["frontier_record_present"] is True
    assert "--from-frontier f.csv.frontier.json" in plain_stdout
    assert plain["certification"]["threshold"] <= picked_warrant["certification"]["threshold"], (
        "the unadjusted threshold can only be as strict or laxer than the frontier row's"
    )


def test_no_sibling_frontier_means_no_notice(tmp_path) -> None:
    data = _ungrouped(tmp_path / "alone.csv", n=600, seed=3)
    result = _run("certify", "-i", str(data), "-b", "0.05", "-o", str(tmp_path / "w.json"))
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / "w.json").read_text(encoding="utf-8"))["frontier_record_present"] is False
    assert "notice" not in result.stdout


def test_a_recheck_of_a_picked_warrant_runs_at_the_family_level(picked, tmp_path, config) -> None:
    """Nothing is selected in a recheck, so it is not held to the row level."""
    from controlplane.intake import recheck_items

    root, _, _ = picked
    fresh = _ungrouped(tmp_path / "later.csv", n=800, seed=12)
    out = tmp_path / "r.json"
    result = _run("recheck", "-w", str(root / "picked.json"), "-i", str(fresh), "-q", "-o", str(out))
    assert result.returncode == 0, result.stderr
    warrant = json.loads((root / "picked.json").read_text(encoding="utf-8"))
    expected = recheck_items(config, load_scored_items(fresh), budget=0.05,
                             threshold=warrant["certification"]["threshold"],
                             alpha=warrant["alpha"])
    assert json.loads(out.read_text(encoding="utf-8"))["now"]["fpr_lower_bound"] == pytest.approx(
        expected.fpr_lower_bound_now)


@pytest.mark.parametrize("case", ["other_file", "off_grid", "no_digest", "with_frontier",
                                  "edited_row_alpha", "cut_to_one_row", "edited_threshold"])
def test_a_pick_that_is_not_a_pick_is_refused(picked, tmp_path, case) -> None:
    root, _, _ = picked
    record = root / "f.csv.frontier.json"
    data = root / "f.csv"
    args = ["-b", "0.05", "--from-frontier", str(record)]
    if case == "other_file":
        data = _ungrouped(tmp_path / "other.csv", seed=99)
    elif case == "off_grid":
        args = ["-b", "0.04", "--from-frontier", str(record)]
    elif case == "no_digest":
        stale = json.loads(record.read_text(encoding="utf-8"))
        del stale["input"]["input_sha256"]
        record = tmp_path / "stale.frontier.json"
        record.write_text(json.dumps(stale), encoding="utf-8")
        args = ["-b", "0.05", "--from-frontier", str(record)]
    elif case == "with_frontier":
        args = ["--frontier", "--from-frontier", str(record)]
    elif case in ("edited_row_alpha", "cut_to_one_row", "edited_threshold"):
        # The 195 review: the digest binds the record to the file, not its numbers.
        forged = json.loads(record.read_text(encoding="utf-8"))
        if case == "edited_row_alpha":
            for row in forged["frontier"]:
                row["row_alpha"] = row["family_alpha"]
        elif case == "cut_to_one_row":
            forged["frontier"] = [r for r in forged["frontier"] if r["budget_fpr"] == 0.05]
            forged["frontier"][0]["row_alpha"] = forged["frontier"][0]["family_alpha"]
        else:
            row = next(r for r in forged["frontier"] if r["budget_fpr"] == 0.05)
            row["threshold"] = row["threshold"] - 0.01
        record = tmp_path / f"{case}.frontier.json"
        record.write_bytes(json.dumps(forged).encode("utf-8"))
        args = ["-b", "0.05", "--from-frontier", str(record)]
    out = tmp_path / "w.json"
    result = _run("certify", "-i", str(data), *args, "-q", "-o", str(out))
    assert result.returncode == 2, (case, result.stdout, result.stderr)
    assert not out.exists(), f"{case}: a refused pick must write nothing"


# --------------------------------------------------------------------------- #
# One digest convention
# --------------------------------------------------------------------------- #


def test_input_sha256_is_the_release_paths_data_sha256(tmp_path) -> None:
    """The expression at release/evaluate.py, `data_sha256`, computed here directly."""
    from controlplane.release.contract import digest

    items = load_scored_items(_ungrouped(tmp_path / "f.csv"))
    labels, scores, _ = items.as_arrays()
    semantic_rows = sorted((digest({"item_id": i}), int(y), float(s))
                           for i, y, s in zip(items.ids, labels, scores, strict=True))
    assert input_sha256(items) == digest(semantic_rows)
    source = (PROJECT_ROOT / "controlplane" / "release" / "evaluate.py").read_text(encoding="utf-8")
    assert 'digest({"item_id": i}), int(y), float(s)' in source, (
        "release/evaluate.py changed its data digest; 195 requires one convention"
    )


def test_input_sha256_ignores_row_order_and_sees_groups(tmp_path) -> None:
    path = _grouped(tmp_path / "g.csv")
    items = load_scored_items(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    shuffled = tmp_path / "shuffled.csv"
    shuffled.write_text("\n".join([lines[0], *reversed(lines[1:])]) + "\n", encoding="utf-8")
    assert input_sha256(load_scored_items(shuffled)) == input_sha256(items)
    ungrouped = tmp_path / "nogroups.csv"
    ungrouped.write_text("\n".join(",".join(l.split(",")[:3]) for l in lines) + "\n", encoding="utf-8")
    assert input_sha256(load_scored_items(ungrouped)) != input_sha256(items)
