"""A `certify` record, read back by every command that takes one.

`plan --warrant` read `budget` from records that carry `budget_fpr`, so it exited
2 on every record `certify` has ever written, and no test noticed because none
ran `plan` from the command line (DECISIONS.md 182). These tests run the real
commands against a real record, so a key renamed on either side fails here
rather than in a customer's terminal.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: Every path a CLI consumer reads out of a certify record. `recheck` and `plan`
#: in controlplane/cli.py; extend this when a command starts reading another.
CONSUMED_PATHS: tuple[tuple[str, ...], ...] = (
    ("status",),
    ("budget_fpr",),
    ("alpha",),
    ("certification", "threshold"),
    ("score_distribution", "name"),
    ("score_distribution", "bin_edges"),
    ("score_distribution", "bin_probabilities"),
    ("score_distribution", "mean"),
    ("score_distribution", "std"),
)


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def _csv(path: Path, n: int, seed: int) -> Path:
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < 0.25).astype(int)
    scores = 1 / (1 + np.exp(-(rng.normal(0, 1, n) + 1.9 * labels)))
    rows = ["id,label,score"] + [
        f"i{i},{int(label)},{float(score):.6f}"
        for i, (label, score) in enumerate(zip(labels, scores, strict=True))
    ]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def certified(tmp_path_factory) -> Path:
    """One real VALID record; certify costs a bootstrap, so it runs once."""
    root = tmp_path_factory.mktemp("records")
    record = root / "base.warrant.json"
    result = _run("certify", "-i", str(_csv(root / "base.csv", 1200, 11)),
                  "-b", "0.05", "-q", "-o", str(record))
    assert result.returncode == 0, result.stderr
    assert json.loads(record.read_text(encoding="utf-8"))["status"] == "VALID"
    return record


def test_every_key_a_command_reads_is_one_certify_writes(certified) -> None:
    payload = json.loads(certified.read_text(encoding="utf-8"))
    for path in CONSUMED_PATHS:
        node = payload
        for key in path:
            assert isinstance(node, dict) and key in node, (
                f"certify's record has no {'.'.join(path)}, and a command reads it"
            )
            node = node[key]


def test_plan_takes_the_budget_from_the_record(certified, tmp_path) -> None:
    out = tmp_path / "plan.json"
    result = _run("plan", "-w", str(certified), "--negative-share", "0.9",
                  "-q", "-o", str(out))
    assert result.returncode == 0, result.stderr
    record = json.loads(certified.read_text(encoding="utf-8"))
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert plan["budget"] == record["budget_fpr"]
    assert plan["alpha"] == record["alpha"]


def test_plan_accepts_a_budget_that_agrees_with_the_record(certified, tmp_path) -> None:
    result = _run("plan", "-w", str(certified), "-b", "0.05",
                  "--negative-share", "0.9", "-q", "-o", str(tmp_path / "p.json"))
    assert result.returncode == 0, result.stderr


def test_plan_refuses_a_budget_that_disagrees_with_the_record(certified, tmp_path) -> None:
    result = _run("plan", "-w", str(certified), "-b", "0.01",
                  "--negative-share", "0.9", "-q", "-o", str(tmp_path / "p.json"))
    assert result.returncode == 2
    assert "disagrees" in result.stderr
    assert not (tmp_path / "p.json").exists(), "a refused plan must write nothing"


def test_plan_refuses_a_refused_warrant(tmp_path) -> None:
    record = tmp_path / "refused.warrant.json"
    record.write_text(json.dumps({
        "status": "REFUSED", "budget_fpr": 0.01, "alpha": 0.05,
        "certification": {"threshold": None},
    }), encoding="utf-8")
    result = _run("plan", "-w", str(record), "--negative-share", "0.9",
                  "-q", "-o", str(tmp_path / "p.json"))
    assert result.returncode == 2
    assert "REFUSED" in result.stderr
    assert "--budget without" in result.stderr


def test_plan_refuses_a_file_that_is_not_a_certify_record(tmp_path) -> None:
    record = tmp_path / "plan-record.json"
    record.write_text(json.dumps({"kind": "monitoring_plan", "budget": 0.05}),
                      encoding="utf-8")
    result = _run("plan", "-w", str(record), "--negative-share", "0.9",
                  "-q", "-o", str(tmp_path / "p.json"))
    assert result.returncode == 2
    assert "no budget_fpr" in result.stderr


def test_recheck_tests_at_the_alpha_the_record_was_certified_at(tmp_path) -> None:
    """Same data, same threshold, two recorded alphas: two different bounds."""
    fresh = _csv(tmp_path / "later.csv", 800, 12)
    lower = {}
    for alpha in (0.05, 0.2):
        record = tmp_path / f"a{alpha}.warrant.json"
        record.write_text(json.dumps({
            "status": "VALID", "budget_fpr": 0.05, "alpha": alpha,
            "certification": {"threshold": 0.85}, "score_distribution": None,
        }), encoding="utf-8")
        out = tmp_path / f"r{alpha}.json"
        result = _run("recheck", "-w", str(record), "-i", str(fresh),
                      "-q", "-o", str(out))
        assert result.returncode == 0, result.stderr
        lower[alpha] = json.loads(out.read_text(encoding="utf-8"))["now"]["fpr_lower_bound"]
    assert lower[0.2] > lower[0.05], (
        "recheck ignored the record's alpha: a looser level must give a higher "
        "lower bound on the same counts"
    )
