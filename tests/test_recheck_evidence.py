"""A recheck identifies and can replay the exact certificate it consumed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from controlplane.intake.chain import canonical_sha256
from controlplane.intake.certify import evidence_sha256
from controlplane.intake.contract import load_scored_items

ROOT = Path(__file__).resolve().parents[1]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "warrant.py"), *args], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )


@pytest.fixture(scope="module")
def issued(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    directory = tmp_path_factory.mktemp("recheck-evidence")
    scores = directory / "scores.csv"
    scores.write_bytes((ROOT / "examples" / "certifies.csv").read_bytes())
    warrant = directory / "issued.json"
    made = _run("certify", "-i", str(scores), "-b", ".05", "-o", str(warrant), "-q")
    assert made.returncode == 0, made.stderr
    return scores, warrant


def test_ordinary_recheck_links_exact_warrant_without_claiming_replay(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, warrant = issued
    out = tmp_path / "ordinary.json"
    result = _run("recheck", "-w", str(warrant), "-i", str(scores), "-o", str(out), "-q")
    assert result.returncode == 0, result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    original = json.loads(warrant.read_text(encoding="utf-8"))
    assert payload["prior_warrant"]["warrant_sha256"] == canonical_sha256(original)
    assert payload["prior_warrant"]["certificate_verification"] == "NOT_CHECKED"
    assert payload["now"]["evidence_sha256"] == evidence_sha256(load_scored_items(scores))

    replay = _run("verify-recheck", "--record", str(out), "--warrant", str(warrant),
                  "--input", str(scores))
    assert replay.returncode == 0, replay.stderr
    assert "VERIFIED" in replay.stdout and "NOT_CHECKED" in replay.stdout


def test_recheck_replay_detects_changed_batch_and_statistic(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, warrant = issued
    out = tmp_path / "ordinary.json"
    assert _run("recheck", "-w", str(warrant), "-i", str(scores),
                "-o", str(out), "-q").returncode == 0
    changed = tmp_path / "changed.csv"
    lines = scores.read_text(encoding="utf-8").splitlines()
    row = lines[1].split(",")
    row[2] = str(float(row[2]) + 0.01)
    lines[1] = ",".join(row)
    changed.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mismatch = _run("verify-recheck", "--record", str(out), "-w", str(warrant),
                    "-i", str(changed))
    assert mismatch.returncode == 1 and "MISMATCH" in mismatch.stdout

    payload = json.loads(out.read_text(encoding="utf-8"))
    payload["now"]["achieved_fpr"] = 0.99
    out.write_text(json.dumps(payload), encoding="utf-8")
    mismatch = _run("verify-recheck", "--record", str(out), "-w", str(warrant),
                    "-i", str(scores))
    assert mismatch.returncode == 1 and "MISMATCH" in mismatch.stdout


def test_checked_source_must_be_replayed_again(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, warrant = issued
    out = tmp_path / "checked.json"
    assert _run("recheck", "-w", str(warrant), "-i", str(scores),
                "--certificate-input", str(scores), "-o", str(out), "-q").returncode == 0
    missing = _run("verify-recheck", "--record", str(out), "-w", str(warrant),
                   "-i", str(scores))
    assert missing.returncode == 1 and "UNVERIFIED" in missing.stdout
    replay = _run("verify-recheck", "--record", str(out), "-w", str(warrant),
                  "-i", str(scores), "--certificate-input", str(scores))
    assert replay.returncode == 0 and "VERIFIED" in replay.stdout

    payload = json.loads(out.read_text(encoding="utf-8"))
    del payload["now"]["evidence_sha256"]
    out.write_text(json.dumps(payload), encoding="utf-8")
    legacy = _run("verify-recheck", "--record", str(out), "-w", str(warrant),
                  "-i", str(scores), "--certificate-input", str(scores))
    assert legacy.returncode == 1 and "UNVERIFIED" in legacy.stdout


def test_replay_rejects_changed_source_certificate_and_configuration(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, warrant = issued
    out = tmp_path / "ordinary.json"
    assert _run("recheck", "-w", str(warrant), "-i", str(scores),
                "-o", str(out), "-q").returncode == 0
    edited_warrant = json.loads(warrant.read_text(encoding="utf-8"))
    edited_warrant["certification"]["threshold"] = 0.0
    changed = tmp_path / "changed-warrant.json"
    changed.write_text(json.dumps(edited_warrant), encoding="utf-8")
    mismatch = _run("verify-recheck", "--record", str(out), "-w", str(changed),
                    "-i", str(scores))
    assert mismatch.returncode == 1 and "MISMATCH" in mismatch.stdout

    edited_record = json.loads(out.read_text(encoding="utf-8"))
    edited_record["provenance"]["config_hash"] = "0" * 64
    out.write_text(json.dumps(edited_record), encoding="utf-8")
    mismatch = _run("verify-recheck", "--record", str(out), "-w", str(warrant),
                    "-i", str(scores))
    assert mismatch.returncode == 1 and "MISMATCH" in mismatch.stdout


def test_chained_recheck_digest_does_not_claim_sequential_replay(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, original_warrant = issued
    warrant = tmp_path / "isolated-warrant.json"
    warrant.write_bytes(original_warrant.read_bytes())
    out = tmp_path / "chain.json"
    assert _run("recheck", "-w", str(warrant), "-i", str(scores),
                "--horizon-labels", "10000", "-o", str(out), "-q").returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["now"]["evidence_sha256"] == evidence_sha256(load_scored_items(scores))
    result = _run("verify-recheck", "--record", str(out), "-w", str(warrant),
                  "-i", str(scores))
    assert result.returncode == 1 and "UNVERIFIED" in result.stdout


def test_checked_recheck_rejects_an_edited_certificate_before_writing(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, warrant = issued
    good = tmp_path / "checked.json"
    checked = _run("recheck", "-w", str(warrant), "-i", str(scores),
                   "--certificate-input", str(scores), "-o", str(good), "-q")
    assert checked.returncode == 0, checked.stderr
    payload = json.loads(good.read_text(encoding="utf-8"))
    assert payload["prior_warrant"]["certificate_verification"] == "VERIFIED"

    edited = json.loads(warrant.read_text(encoding="utf-8"))
    edited["certification"]["threshold"] = 0.0
    bad_warrant = tmp_path / "edited.json"
    bad_warrant.write_text(json.dumps(edited), encoding="utf-8")
    refused = tmp_path / "must-not-exist.json"
    result = _run("recheck", "-w", str(bad_warrant), "-i", str(scores),
                  "--certificate-input", str(scores), "-o", str(refused))
    assert result.returncode == 2
    assert "MISMATCH" in result.stderr
    assert "Traceback" not in result.stderr
    assert not refused.exists()

    altered_scores = tmp_path / "altered-scores.csv"
    lines = scores.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[2] = str(float(cells[2]) + 0.01)
    lines[1] = ",".join(cells)
    altered_scores.write_text("\n".join(lines) + "\n", encoding="utf-8")
    changed_input = _run("recheck", "-w", str(warrant), "-i", str(scores),
                         "--certificate-input", str(altered_scores), "-o", str(refused))
    assert changed_input.returncode == 2
    assert "MISMATCH" in changed_input.stderr
    assert not refused.exists()

    legacy = json.loads(warrant.read_text(encoding="utf-8"))
    del legacy["input"]["evidence_sha256"]
    old_warrant = tmp_path / "legacy.json"
    old_warrant.write_text(json.dumps(legacy), encoding="utf-8")
    unverified = _run("recheck", "-w", str(old_warrant), "-i", str(scores),
                      "--certificate-input", str(scores), "-o", str(refused))
    assert unverified.returncode == 2
    assert "UNVERIFIED" in unverified.stderr
    assert not refused.exists()


def test_selected_certificate_requires_retained_frontier(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, _ = issued
    frontier = tmp_path / "frontier.json"
    assert _run("certify", "-i", str(scores), "--frontier", "-o", str(frontier), "-q").returncode == 0
    warrant = tmp_path / "selected.json"
    made = _run("certify", "-i", str(scores), "-b", ".05", "--from-frontier",
                str(frontier), "-o", str(warrant), "-q")
    assert made.returncode == 0, made.stderr
    out = tmp_path / "selected-recheck.json"
    missing = _run("recheck", "-w", str(warrant), "-i", str(scores),
                   "--certificate-input", str(scores), "-o", str(out))
    assert missing.returncode == 2
    assert "UNVERIFIED" in missing.stderr
    assert not out.exists()
    good = _run("recheck", "-w", str(warrant), "-i", str(scores),
                "--certificate-input", str(scores), "--certificate-frontier",
                str(frontier), "-o", str(out), "-q")
    assert good.returncode == 0, good.stderr
    assert json.loads(out.read_text(encoding="utf-8"))["prior_warrant"]["certificate_verification"] == "VERIFIED"
    missing_replay = _run("verify-recheck", "--record", str(out), "-w", str(warrant),
                          "-i", str(scores), "--certificate-input", str(scores))
    assert missing_replay.returncode == 1 and "UNVERIFIED" in missing_replay.stdout
    replay = _run("verify-recheck", "--record", str(out), "-w", str(warrant),
                  "-i", str(scores), "--certificate-input", str(scores),
                  "--certificate-frontier", str(frontier))
    assert replay.returncode == 0 and "VERIFIED" in replay.stdout

    alone = _run("recheck", "-w", str(warrant), "-i", str(scores),
                 "--certificate-frontier", str(frontier), "-o", str(tmp_path / "alone.json"))
    assert alone.returncode == 2
    assert "needs --certificate-input" in alone.stderr
    assert not (tmp_path / "alone.json").exists()


@pytest.mark.parametrize("raw,reason", [
    ('{"input": {}, "input": {}}', "duplicate JSON key"),
    ('{"budget_fpr": NaN}', "non-finite JSON number"),
])
def test_ambiguous_certificate_is_bad_input(
    issued: tuple[Path, Path], tmp_path: Path, raw: str, reason: str,
) -> None:
    scores, _ = issued
    warrant = tmp_path / "ambiguous.json"
    warrant.write_text(raw, encoding="utf-8")
    out = tmp_path / "must-not-exist.json"
    result = _run("recheck", "-w", str(warrant), "-i", str(scores), "-o", str(out))
    assert result.returncode == 2
    assert reason in result.stderr
    assert "Traceback" not in result.stderr
    assert not out.exists()


def test_chained_recheck_repeats_its_existing_warrant_digest(
    issued: tuple[Path, Path], tmp_path: Path,
) -> None:
    scores, warrant = issued
    out = tmp_path / "chained.json"
    result = _run("recheck", "-w", str(warrant), "-i", str(scores),
                  "--certificate-input", str(scores), "--horizon-labels", "10000",
                  "-o", str(out), "-q")
    assert result.returncode == 0, result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["prior_warrant"]["warrant_sha256"] == payload["chain"]["warrant_sha256"]
    assert payload["prior_warrant"]["certificate_verification"] == "VERIFIED"


@pytest.mark.parametrize("field", ["certification", "input", "score_distribution"])
def test_wrong_shaped_warrant_blocks_are_bad_input_without_a_partial_record(
    issued: tuple[Path, Path], tmp_path: Path, field: str,
) -> None:
    scores, warrant = issued
    malformed = json.loads(warrant.read_text(encoding="utf-8"))
    malformed[field] = ["not an object"]
    bad_warrant = tmp_path / "wrong-shape.json"
    bad_warrant.write_text(json.dumps(malformed), encoding="utf-8")
    out = tmp_path / "must-not-exist.json"
    result = _run("recheck", "-w", str(bad_warrant), "-i", str(scores), "-o", str(out))
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert not out.exists()
