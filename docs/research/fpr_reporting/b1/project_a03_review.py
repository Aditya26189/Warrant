"""Project preserved method annotations at a blocked B1 gate, without sampling."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "a03-review-stop"
EVENT_FILES = (
    "a03-method-batch001/DOMAIN_DECISIONS.jsonl",
    "a03-method-events002/DOMAIN_DECISION_EVENTS.jsonl",
)
INPUT_FILES = (
    *EVENT_FILES,
    "PROTOCOL_LOCK_A03.json",
    "a02-human-batch002/SCREENING_LEDGER.json",
    "a02-human-batch002/PENDING_METADATA_ANSWERS_BLANK.json",
    "a02-human-batch001/WORK_ID_CROSSWALK.json",
    "a03-method-batch001/SOURCE_PROVENANCE.json",
    "a03-method-events002/SUPPLEMENTAL_SOURCE_PROVENANCE.json",
    "a03-method-events002/EXPOSURE_DEVIATION.json",
    "a03-method-events002/REVIEW_OVERLAP_NOTE.json",
    "project_a03_review.py",
)


def read_json(path: Path) -> Any:
    """Read historical Windows or LF JSON without changing its bytes."""
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    """Bind a record to original bytes rather than normalized line endings."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Write new artifacts with LF while preserving historical snapshots."""
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def project() -> tuple[list[dict], list[dict], list[dict]]:
    """Replay domain events only; INCLUDE never means fully eligible here."""
    lock = read_json(BASE / "PROTOCOL_LOCK_A03.json")
    for name, expected in lock["files"].items():
        if digest(BASE / name) != expected:
            raise AssertionError(f"Locked input changed: {name}")
    original_manifest = read_json(BASE / "a03-method-batch001/MANIFEST.json")
    for name, expected in original_manifest["files"].items():
        assert digest(BASE / "a03-method-batch001" / name) == expected

    baseline = read_json(BASE / "a02-human-batch002/SCREENING_LEDGER.json")
    questions = read_json(BASE / "a02-human-batch002/PENDING_METADATA_ANSWERS_BLANK.json")["questions"]
    question_by_id = {q["review_id"]: q for q in questions}
    aliases = read_json(BASE / "a02-human-batch001/WORK_ID_CROSSWALK.json")["old_to_current_work_id"]
    receipts = read_json(BASE / "a03-method-batch001/SOURCE_PROVENANCE.json")["work_sources"]
    receipt_by_id = {r["review_id"]: r for r in receipts}
    assert len(baseline) == lock["current_work_records"] == 372
    assert len(questions) == len(receipts) == lock["unresolved_domain_records"] == 156
    normalized = []
    latest = {}
    for filename in EVENT_FILES:
        for line_number, line in enumerate((BASE / filename).read_text(encoding="utf-8").splitlines(), 1):
            event = json.loads(line)
            rid = event["review_id"]
            question = question_by_id[rid]
            source_id = question["work_id"]
            assert receipt_by_id[rid]["work_id"] == source_id
            if "work_id" in event:
                assert event["work_id"] == source_id
            else:
                assert rid in {"Q003", "Q005", "Q007"}
            assert event["decision"] in {"INCLUDE", "EXCLUDE"}
            assert event["scope"] == "DOMAIN_ONLY"
            assert event["outcome_use"] == "NONE"
            if rid in latest:
                assert rid == "Q007" and "supersedes" in event
            locators = event.get("method_locators", [event.get("method_dataset_locator")])
            assert locators and all(locators)
            record = {
                "event_sequence": len(normalized) + 1,
                "review_id": rid,
                "work_id": aliases.get(source_id, source_id),
                "title": question["title"],
                "decision": event["decision"],
                "adjudicator": "CODEX_METHOD_ADJUDICATION",
                "method_dataset_locators": locators,
                "method_only_rationale": event.get("method_only_rationale", event.get("rationale")),
                "language_evidence": event.get("language_evidence", event.get("english_support")),
                "limitations": event["limitations"],
                "recorded_utc": event["recorded_utc"],
                "source_git_commit": event["source_git_commit"],
                "historical_record": {"file": filename, "line": line_number, "sha256": digest(BASE / filename)},
                "correction_of": event.get("supersedes"),
                "source_receipt_file": "a03-method-batch001/SOURCE_PROVENANCE.json",
                "source_receipt_review_id": rid,
                "exposure_status": "INCIDENTAL_EXPOSURE_DISCLOSED_PROCESS_REVIEW_REQUIRED",
                "scope": "DOMAIN_ONLY_NOT_ELIGIBLE_FRAME",
                "version_eligibility": "NOT_RUN",
            }
            assert record["method_only_rationale"] and record["language_evidence"]
            normalized.append(record)
            latest[rid] = record

    assert len(normalized) == 42 and len(latest) == 41
    rows = copy.deepcopy(baseline)
    row_by_id = {r["work_id"]: r for r in rows}
    for event in latest.values():
        row = row_by_id[event["work_id"]]
        assert row["decision"] == "UNCLEAR"
        row["prior_domain_decision"] = row["decision"]
        row["decision"] = event["decision"]
        row["rationale"] = event["method_only_rationale"]
        row["reason"] = "CODEX_METHOD_ADJUDICATION_PROCESS_REVIEW_PENDING"
        row["assistant_event_sequence"] = event["event_sequence"]
        row["paper_outcome_use"] = "METHOD_BASIS_REPORTED_INCIDENTAL_EXPOSURE_DISCLOSED"
        row["version_selection"] = "NOT_RUN"
    pending = [q for q in questions if q["review_id"] not in latest]
    assert len(pending) == 115
    assert Counter(r["decision"] for r in rows)["UNCLEAR"] == len(pending)
    assert [r["work_id"] for r in rows] == [r["work_id"] for r in baseline]
    assert all(new == old for new, old in zip(rows, baseline, strict=True)
               if old["decision"] != "UNCLEAR")
    return normalized, rows, pending


def verify() -> None:
    """Check replay, locked hashes and the explicit absence of a draw."""
    events, rows, pending = project()
    assert read_json(OUTPUT / "DOMAIN_EVENTS_NORMALIZED.json") == events
    assert read_json(OUTPUT / "SCREENING_LEDGER.json") == rows
    assert read_json(OUTPUT / "PENDING_DOMAIN_QUESTIONS.json") == pending
    manifest = read_json(OUTPUT / "MANIFEST.json")
    assert manifest["status"] == "FRAME_BLOCKED"
    for name, expected in manifest["files"].items():
        assert digest(OUTPUT / name) == expected
    for name, expected in manifest["input_sha256"].items():
        assert digest(BASE / name) == expected
    assert manifest["ten_paper_draw"] == manifest["human_six_assignment"] == "NOT_RUN"
    assert all(p.stat().st_size < 10_000_000 for p in OUTPUT.iterdir())
    assert all(b"\r\n" not in p.read_bytes() for p in OUTPUT.iterdir())
    print("PASS:42 events/41 works;372-ID projection;115 unresolved; locked/source hashes; no draw; LF/size checks")


def main() -> None:
    """Freeze a blocked metadata checkpoint from clean committed inputs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        verify()
        return
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=BASE):
        raise RuntimeError("Refusing dirty-tree research projection")
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    events, rows, pending = project()
    OUTPUT.mkdir()
    write_json(OUTPUT / "DOMAIN_EVENTS_NORMALIZED.json", events)
    write_json(OUTPUT / "SCREENING_LEDGER.json", rows)
    write_json(OUTPUT / "PENDING_DOMAIN_QUESTIONS.json", pending)
    write_json(OUTPUT / "MANIFEST.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE, text=True).strip(),
        "source_tree_clean_at_start": True,
        "status": "FRAME_BLOCKED",
        "reason": "UNPLANNED_RESULT_EXPOSURE_REQUIRES_PROCESS_DECISION",
        "scope": "DOMAIN_PROGRESS_ONLY_NOT_ELIGIBLE_FRAME",
        "events": len(events),
        "newly_adjudicated_works": 41,
        "counts": dict(Counter(r["decision"] for r in rows)),
        "unresolved_domain_records": len(pending),
        "original_work_cap": 500,
        "current_works_to_screen": len(rows),
        "input_sha256": {name: digest(BASE / name) for name in INPUT_FILES},
        "files": {p.name: digest(p) for p in sorted(OUTPUT.iterdir())},
        "ten_paper_draw": "NOT_RUN",
        "human_six_assignment": "NOT_RUN",
        "eligible_version_freeze": "NOT_RUN",
        "structured_FPR_extraction": "NOT_RUN",
        "incidental_result_exposure": "OCCURRED",
        "B2": "NOT_AUTHORIZED",
    })
    verify()


if __name__ == "__main__":
    main()
