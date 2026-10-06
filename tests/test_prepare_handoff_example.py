"""The public synthetic export traverses both independent replay boundaries.

Decision 234: the four-row mapping example cannot certify. This larger fixture
is derived from the seeded synthetic certificate example, never from a customer.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from controlplane.intake import load_scored_items


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples" / "export_certifies.csv"
MAPPING = ROOT / "examples" / "export_certifies_mapping.json"
ORIGINAL = ROOT / "examples" / "certifies.csv"
SMALL_SOURCE = ROOT / "examples" / "export_sample.csv"
SMALL_MAPPING = ROOT / "examples" / "export_mapping.json"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "warrant.py"), *args],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=300,
    )


def test_public_export_is_exactly_the_seeded_example_with_declared_aliases() -> None:
    with ORIGINAL.open(encoding="utf-8", newline="") as handle:
        original = list(csv.DictReader(handle))
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        exported = list(csv.DictReader(handle))
    assert len(exported) == len(original) == 400
    for base, row in zip(original, exported, strict=True):
        assert row == {
            "item": base["id"],
            "review": "error" if base["label"] == "1" else "ok",
            "risk": base["score"],
            "captured_at": base["captured_at"],
        }


def test_public_handoff_certifies_and_replays_both_boundaries(tmp_path: Path) -> None:
    prepared = tmp_path / "prepared"
    made = _run("prepare", "--input", str(SOURCE), "--mapping", str(MAPPING),
                "--out", str(prepared))
    assert made.returncode == 0, made.stderr
    assert "PREPARED" in made.stdout

    prep_check = _run("verify-prepared", "--input", str(SOURCE),
                      "--mapping", str(MAPPING), "--prepared", str(prepared))
    assert prep_check.returncode == 0, prep_check.stderr
    assert "VERIFIED" in prep_check.stdout

    canonical = prepared / "scored.csv"
    prepared_items = load_scored_items(canonical)
    original_items = load_scored_items(ORIGINAL)
    assert (prepared_items.ids, prepared_items.labels, prepared_items.scores,
            prepared_items.groups, prepared_items.second_labels) == (
                original_items.ids, original_items.labels, original_items.scores,
                original_items.groups, original_items.second_labels,
            )
    manifest = json.loads((prepared / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["excluded_columns"] == ["captured_at"]

    record = tmp_path / "prepared.warrant.json"
    certified = _run("certify", "--input", str(canonical), "--budget", "0.05",
                     "--out", str(record), "--quiet")
    assert certified.returncode == 0, certified.stderr
    warrant = json.loads(record.read_text(encoding="utf-8"))
    assert warrant["status"] == "VALID"
    assert warrant["input"]["evidence_sha256"] == manifest["effective_rows_sha256"]
    checked = _run("verify", "--warrant", str(record), "--input", str(canonical))
    assert checked.returncode == 0, checked.stderr
    assert "VERIFIED" in checked.stdout

    edited_source = tmp_path / "edited-export.csv"
    edited_source.write_bytes(SOURCE.read_bytes().replace(
        b"2026-09-01T12:00:00Z", b"2026-09-01T12:00:01Z", 1,
    ))
    assert edited_source.read_bytes() != SOURCE.read_bytes()
    source_check = _run("verify-prepared", "--input", str(edited_source),
                        "--mapping", str(MAPPING), "--prepared", str(prepared))
    assert source_check.returncode == 1
    assert "MISMATCH" in source_check.stdout
    # Certification binds the scored rows, not excluded source-only columns.
    still_checked = _run("verify", "--warrant", str(record), "--input", str(canonical))
    assert still_checked.returncode == 0, still_checked.stderr
    assert "VERIFIED" in still_checked.stdout


def test_public_grouped_export_refuses_and_replays_both_boundaries(tmp_path: Path) -> None:
    prepared = tmp_path / "prepared-small"
    made = _run("prepare", "--input", str(SMALL_SOURCE), "--mapping",
                str(SMALL_MAPPING), "--out", str(prepared))
    assert made.returncode == 0, made.stderr
    assert "PREPARED" in made.stdout

    prep_check = _run("verify-prepared", "--input", str(SMALL_SOURCE),
                      "--mapping", str(SMALL_MAPPING), "--prepared", str(prepared))
    assert prep_check.returncode == 0, prep_check.stderr
    assert "VERIFIED" in prep_check.stdout

    record = tmp_path / "refused.warrant.json"
    certified = _run("certify", "--input", str(prepared / "scored.csv"),
                     "--budget", "0.05", "--out", str(record), "--quiet")
    assert certified.returncode == 0, certified.stderr
    warrant = json.loads(record.read_text(encoding="utf-8"))
    manifest = json.loads((prepared / "manifest.json").read_text(encoding="utf-8"))
    assert warrant["status"] == "REFUSED"
    assert "only 2 independent units" in warrant["reason"]
    assert "need >= 59 clean units" in warrant["reason"]
    assert warrant["input"]["evidence_sha256"] == manifest["effective_rows_sha256"]
    checked = _run("verify", "--warrant", str(record),
                   "--input", str(prepared / "scored.csv"))
    assert checked.returncode == 0, checked.stderr
    assert "VERIFIED" in checked.stdout

    changed_source = tmp_path / "changed-small.csv"
    changed_source.write_bytes(SMALL_SOURCE.read_bytes().replace(
        b"synthetic example only", b"changed example only", 1,
    ))
    assert changed_source.read_bytes() != SMALL_SOURCE.read_bytes()
    source_check = _run("verify-prepared", "--input", str(changed_source),
                        "--mapping", str(SMALL_MAPPING), "--prepared", str(prepared))
    assert source_check.returncode == 1
    assert "MISMATCH" in source_check.stdout
    still_checked = _run("verify", "--warrant", str(record),
                         "--input", str(prepared / "scored.csv"))
    assert still_checked.returncode == 0, still_checked.stderr
    assert "VERIFIED" in still_checked.stdout
