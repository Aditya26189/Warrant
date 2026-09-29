"""Verify a retained certify record against the scored rows that produced it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "warrant.py"), *args], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def issued(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    directory = tmp_path_factory.mktemp("certify-verify")
    scores = directory / "scores.csv"
    scores.write_bytes((ROOT / "examples" / "certifies.csv").read_bytes())
    record = directory / "issued.json"
    result = _run("certify", "--input", str(scores), "--budget", "0.05",
                  "--out", str(record), "--quiet")
    assert result.returncode == 0, result.stderr
    return scores, record


def test_replay_accepts_a_copy_and_refuses_changed_rows_or_metrics(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, record = issued
    copy = tmp_path / "copy.csv"
    copy.write_bytes(scores.read_bytes())
    before = record.read_bytes()
    good = _run("verify", "--warrant", str(record), "--input", str(copy))
    assert good.returncode == 0, good.stderr
    assert "VERIFIED" in good.stdout
    assert record.read_bytes() == before, "verification must not rewrite evidence"

    altered = tmp_path / "altered.csv"
    lines = copy.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[2] = str(float(cells[2]) + 0.01)
    lines[1] = ",".join(cells)
    altered.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert altered.read_bytes() != copy.read_bytes()
    wrong_rows = _run("verify", "--warrant", str(record), "--input", str(altered))
    assert wrong_rows.returncode == 1
    assert "MISMATCH" in wrong_rows.stdout

    payload = json.loads(record.read_text(encoding="utf-8"))
    payload["certification"]["fpr_upper_bound"] = 0.0
    edited = _write(tmp_path / "edited.json", payload)
    wrong_bound = _run("verify", "--warrant", str(edited), "--input", str(copy))
    assert wrong_bound.returncode == 1
    assert "certification" in wrong_bound.stdout


def test_legacy_and_malformed_records_never_verify(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, record = issued
    legacy = json.loads(record.read_text(encoding="utf-8"))
    del legacy["input"]["evidence_sha256"]
    old = _write(tmp_path / "old.json", legacy)
    result = _run("verify", "--warrant", str(old), "--input", str(scores))
    assert result.returncode == 1
    assert "UNVERIFIED" in result.stdout

    bad = tmp_path / "bad.json"
    bad.write_text('{"input": {}, "input": {}}', encoding="utf-8")
    result = _run("verify", "--warrant", str(bad), "--input", str(scores))
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_a_refusal_can_be_reproduced(tmp_path: Path) -> None:
    scores = ROOT / "examples" / "refuses.csv"
    record = tmp_path / "refused.json"
    made = _run("certify", "--input", str(scores), "--budget", "0.01",
                "--out", str(record), "--quiet")
    assert made.returncode == 0, made.stderr
    replay = _run("verify", "--warrant", str(record), "--input", str(scores))
    assert replay.returncode == 0, replay.stderr


def test_frontier_selected_record_needs_and_checks_its_frontier(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, _ = issued
    frontier = tmp_path / "grid.json"
    made = _run("certify", "--input", str(scores), "--frontier",
                "--out", str(frontier), "--quiet")
    assert made.returncode == 0, made.stderr
    record = tmp_path / "selected.json"
    made = _run("certify", "--input", str(scores), "--budget", "0.05",
                "--from-frontier", str(frontier), "--out", str(record), "--quiet")
    assert made.returncode == 0, made.stderr

    no_frontier = _run("verify", "--warrant", str(record), "--input", str(scores))
    assert no_frontier.returncode == 1
    assert "UNVERIFIED" in no_frontier.stdout
    good = _run("verify", "--warrant", str(record), "--input", str(scores),
                "--frontier", str(frontier))
    assert good.returncode == 0, good.stderr

    altered = json.loads(frontier.read_text(encoding="utf-8"))
    altered["frontier"][0]["row_alpha"] = 0.05
    changed = _write(tmp_path / "changed-grid.json", altered)
    bad = _run("verify", "--warrant", str(record), "--input", str(scores),
               "--frontier", str(changed))
    assert bad.returncode == 1
