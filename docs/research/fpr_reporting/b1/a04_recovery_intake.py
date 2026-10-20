"""Preserve provisional returns and restore original archive authentication.

This is custodian mechanics only. No historical screening ledger is imported,
no independent scientific review is certified, and no sampling is implemented.
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import a04_evidence as e

RUN = "a04-provisional-recovery-v1-20261021"
CACHE = Path(e.read(e.CONFIG)["cache_root"]).parent / "fpr-a04-recovery-20261021"
ORIGINAL_NAMES = ("B1_ELIGIBILITY_REVIEW_PROVISIONAL.json", "B1_VALIDATION_RESULTS.json",
                  "B1_CONSOLIDATED_REPORT.md", "B1_CONTROLLED_EVIDENCE_REQUESTS.json")
ARCHIVES = {
    "FRESH_REVIEWER_INTAKE.zip": ("a04-handoff/FRESH_REVIEWER_INTAKE.zip",
        "48c903779bda205c2af6231da92cca8b70e6ba9755cfa175f526c107e23e7290", "verify_package.py"),
    "RESTRICTED_EVIDENCE_SUPPLEMENT.zip": ("a04-evidence-v1-20261019/RESTRICTED_EVIDENCE_SUPPLEMENT.zip",
        "066c27ae28ad941ea9ebf963f3fc5d854b2bcd39d1fb060a16b52b5cc4294c08", "verify_evidence.py"),
    "CONSOLIDATED_RESTRICTED_EVIDENCE.zip": ("a04-semantic-evidence-v1-20261020/CONSOLIDATED_RESTRICTED_EVIDENCE.zip",
        "8158e43ee8ad8c55854aab59c526b979b7e5a89b23f804eb65b408b384621a71", "verify_semantic.py"),
}
CRITERIA = {"input_injection_task", "binary_evaluation", "before_target_answer", "english_evaluation", "version", "identity"}
BASE_CRITERIA = CRITERIA - {"identity"}


def authenticated_payloads(raw: bytes, expected_sha256: str) -> dict[str, bytes]:
    """Authenticate original bytes before parsing or executing their verifier."""
    import io
    if e.sha(raw) != expected_sha256:
        raise ValueError("ORIGINAL_ARCHIVE_DIGEST_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
        names = zipped.namelist()
        if len(names) != len(set(names)) or any(Path(n).name != n for n in names):
            raise ValueError("ARCHIVE_NOT_FLAT_OR_DUPLICATED")
        if zipped.testzip() is not None:
            raise ValueError("ARCHIVE_CRC_FAILED")
        files = {name: zipped.read(name) for name in names}
    manifest = json.loads(files["MANIFEST.json"])
    if set(files) != set(manifest["files"]) | {"MANIFEST.json"}:
        raise ValueError("ARCHIVE_MANIFEST_MEMBERSHIP_MISMATCH")
    if any(e.sha(files[name]) != digest for name, digest in manifest["files"].items()):
        raise ValueError("ARCHIVE_MANIFEST_DIGEST_MISMATCH")
    return files


def original_archives() -> dict[str, dict[str, bytes]]:
    """Load only the three hash-pinned authentic original archives."""
    result = {name: authenticated_payloads((e.BASE / path).read_bytes(), digest)
              for name, (path, digest, _) in ARCHIVES.items()}
    actual = result["CONSOLIDATED_RESTRICTED_EVIDENCE.zip"]["BASE_EVIDENCE_SUPPLEMENT.zip"]
    if actual != (e.BASE / ARCHIVES["RESTRICTED_EVIDENCE_SUPPLEMENT.zip"][0]).read_bytes():
        raise ValueError("ORIGINAL_NESTED_BASE_NOT_BYTE_IDENTICAL")
    return result


def frozen_inputs() -> tuple[list, dict, dict, list]:
    """Read the frozen inventory and released evidence without prior decisions."""
    archives = original_archives()
    intake = archives["FRESH_REVIEWER_INTAKE.zip"]
    base = archives["RESTRICTED_EVIDENCE_SUPPLEMENT.zip"]
    semantic = archives["CONSOLIDATED_RESTRICTED_EVIDENCE.zip"]
    inventory = json.loads(intake["CANDIDATE_INVENTORY.json"])
    evidence = {}
    for data, name in ((base, "BIBLIOGRAPHIC_EVIDENCE.json"), (base, "METHOD_EVIDENCE.json"),
                       (semantic, "SEMANTIC_METHOD_FACTS.json")):
        for row in json.loads(data[name]):
            if row["evidence_id"] in evidence:
                raise ValueError("DUPLICATE_FROZEN_EVIDENCE_ID")
            evidence[row["evidence_id"]] = row
    receipts = {}
    for data, name in ((base, "EVIDENCE_RECEIPTS.json"), (semantic, "SEMANTIC_EVIDENCE_RECEIPTS.json")):
        for row in json.loads(data[name]):
            receipts[row["evidence_id"]] = row
    return inventory, evidence, receipts, json.loads(base["SENTINEL_IDENTIFIER_CROSSWALK.json"])


def validate_return(rows: list, requests: list, declared: dict) -> dict:
    """Validate provisional mechanics; never promote dispositions into scientific review."""
    inventory, evidence, receipts, sentinels = frozen_inputs()
    by_id = {r["review_id"]: r for r in inventory}
    if (len(rows) != 372 or len({r["review_id"] for r in rows}) != 372
            or {r["review_id"] for r in rows} != set(by_id)):
        raise ValueError("PROVISIONAL_WORK_COVERAGE_MISMATCH")
    exact_all = {r["review_id"] for r in sentinels
                 if any(x["exclude_versions"] == "ALL" for x in r["exact_identifier_matches"])}
    decisions = collections.Counter()
    mentioned = set()
    for row in rows:
        rid = row["review_id"]
        if row["work_id"] != by_id[rid]["work_id"]:
            raise ValueError("PROVISIONAL_WORK_ID_MISMATCH")
        if row["decision"] not in {"UNCLEAR", "EXCLUDE"}:
            raise ValueError("UNEXPECTED_PROVISIONAL_DECISION")
        if (row["decision"] == "EXCLUDE") != (rid in exact_all):
            raise ValueError("EXCLUSION_NOT_EXACT_ALL_VERSION_SENTINEL")
        decisions[row["decision"]] += 1
        for eid in row["evidence_ids"]:
            if eid not in evidence or eid not in receipts or evidence[eid]["work_id"] != row["work_id"]:
                raise ValueError("PROVISIONAL_EVIDENCE_FOREIGN_KEY")
            if receipts[eid]["restricted_evidence_sha256"] != e.sha(e.encoded(evidence[eid])):
                raise ValueError("PROVISIONAL_EVIDENCE_RECEIPT_HASH")
            mentioned.add(eid)
        for locator in row["method_bibliographic_locators"]:
            if locator["evidence_id"] not in row["evidence_ids"]:
                raise ValueError("PROVISIONAL_LOCATOR_NOT_LINKED")
            source = evidence[locator["evidence_id"]]
            for key in ("source_url", "version", "raw_source_sha256", "locator"):
                if source.get(key) != locator.get(key):
                    raise ValueError("PROVISIONAL_SOURCE_LOCATOR_CHANGED")
    unclear = {r["review_id"] for r in rows if r["decision"] == "UNCLEAR"}
    if len(requests) != 367 or len({r["review_id"] for r in requests}) != 367 or {r["review_id"] for r in requests} != unclear:
        raise ValueError("CONTROLLED_REQUEST_WORK_COVERAGE")
    if len({r["request_id"] for r in requests}) != 367:
        raise ValueError("CONTROLLED_REQUEST_ID_DUPLICATED")
    for request in requests:
        work = by_id[request["review_id"]]
        mids = [m["member_id"] for m in work["members"]]
        if (request["work_id"] != work["work_id"] or request["current_decision"] != "UNCLEAR"
                or sorted(request["member_ids"]) != sorted(mids)):
            raise ValueError("CONTROLLED_REQUEST_IDENTITY_MISMATCH")
        criteria = [r["criterion"] for r in request["controlled_requests"]]
        if (len(criteria) != len(set(criteria)) or not BASE_CRITERIA.issubset(criteria)
                or not set(criteria).issubset(CRITERIA)):
            raise ValueError("CONTROLLED_REQUEST_CRITERIA_MISMATCH")
        for gap in request["controlled_requests"]:
            for eid in gap["existing_restricted_evidence_ids"]:
                if eid not in evidence or evidence[eid]["work_id"] != work["work_id"]:
                    raise ValueError("CONTROLLED_REQUEST_EVIDENCE_FOREIGN_KEY")
    if decisions != {"UNCLEAR": 367, "EXCLUDE": 5} or len(exact_all) != 5:
        raise ValueError("PROVISIONAL_REPORTED_COUNT_MISMATCH")
    return {"mechanical_validation": "PASS", "works": 372,
            "memberships": sum(len(r["members"]) for r in inventory),
            "decisions_reported": dict(decisions), "controlled_request_works": 367,
            "controlled_request_items": sum(len(r["controlled_requests"]) for r in requests),
            "semantic_facts_linked": sum(eid.startswith("SEM-") for eid in mentioned),
            "exact_all_version_sentinel_review_ids": sorted(exact_all),
            "return_status": "PROVISIONAL_UNAUTHENTICATED",
            "reported_all_rows_explicitly_adjudicated": declared.get("all_rows_explicitly_adjudicated"),
            "interpretation": "MECHANICAL_DISPOSITIONS_NOT_COMPLETED_INDEPENDENT_SCIENTIFIC_ELIGIBILITY_ADJUDICATION",
            "reported_synthetic_content_check": declared.get("semantic_content_check"),
            "synthetic_or_overridden_checks_used_for_authentication": False,
            "authentic_transfer_recorded": False, "fresh_intake_attested_locally": False,
            "completed_independent_eligibility_return": False, "historical_judgment_comparison": "NOT_PERFORMED",
            "gate": "FRAME_BLOCKED", "draw_executed": False, "B2_executed": False}


def source_requests(requests: list) -> list:
    """Remove provisional decisions/statuses from the neutral source-role worklist."""
    return [{"request_id": r["request_id"], "review_id": r["review_id"], "work_id": r["work_id"],
             "member_ids": r["member_ids"], "primary_source_urls": r["primary_source_urls"],
             "controlled_requests": [{k: gap[k] for k in ("criterion", "request", "existing_restricted_evidence_ids")}
                                     for gap in r["controlled_requests"]]} for r in requests]


def import_return(source: Path, head: str) -> None:
    """Preserve the four original byte streams before publishing validation addenda."""
    root = e.BASE / RUN
    files = {name: (source / name).read_bytes() for name in ORIGINAL_NAMES}
    for name, raw in files.items():
        path = root / "original-return" / name
        if path.exists():
            if path.read_bytes() != raw:
                raise ValueError("ORIGINAL_RETURN_OVERWRITE_FORBIDDEN")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    rows = json.loads(files[ORIGINAL_NAMES[0]])
    requests = json.loads(files[ORIGINAL_NAMES[3]])
    result = validate_return(rows, requests, json.loads(files[ORIGINAL_NAMES[1]]))
    result.update(source_git_commit=head, imported_utc=e.now(), original_file_sha256={n: e.sha(raw) for n, raw in files.items()})
    referenced = source / "B1_EVIDENCE_REFERENCES_AND_LIMITATIONS.json"
    result["separately_referenced_artifact"] = {"filename": referenced.name, "available_at_source": referenced.exists(),
        "core_validation_requires_it": False, "basis": "All original provisional rows embed their evidence IDs, locators and limitations; no separate original artifact is fabricated."}
    e.write_new(root / "PROVISIONAL_RETURN_VALIDATION.json", result)
    e.write_new(root / "SOURCE_GAP_REQUESTS.json", source_requests(requests))
    projection = [{k: row[k] for k in ("review_id", "work_id", "evidence_ids", "method_bibliographic_locators", "limitations")} for row in rows]
    e.write_new(root / "RECONSTRUCTED_REFERENCE_INDEX_CUSTODIAN_ONLY.json", {
        "status": "DERIVED_FROM_EMBEDDED_PROVISIONAL_FIELDS_NOT_THE_MISSING_ORIGINAL_ARTIFACT", "rows": projection})
    print(json.dumps(result, sort_keys=True))


def authenticate(head: str) -> None:
    """Execute unmodified original verifiers only after pinned-byte authentication."""
    payloads = original_archives()
    outputs = []
    for name, files in payloads.items():
        folder = CACHE / "authentic-originals" / name.removesuffix(".zip")
        if folder.exists() and {p.name for p in folder.iterdir()} != set(files):
            raise ValueError("AUTHENTIC_EXTRACTION_DIRECTORY_CHANGED")
        folder.mkdir(parents=True, exist_ok=True)
        for filename, raw in files.items():
            path = folder / filename
            if path.exists() and path.read_bytes() != raw:
                raise ValueError("AUTHENTIC_EXTRACTED_BYTES_CHANGED")
            path.write_bytes(raw)
        process = subprocess.run([sys.executable, "-I", str(folder / ARCHIVES[name][2])], capture_output=True, text=True)
        if process.returncode:
            raise ValueError(f"ORIGINAL_OFFLINE_VERIFIER_FAILED:{name}:{process.stderr}")
        outputs.append({"filename": name, "path": ARCHIVES[name][0], "original_sha256": ARCHIVES[name][1],
                        "original_bytes": (e.BASE / ARCHIVES[name][0]).stat().st_size,
                        "manifest_sha256": e.sha(files["MANIFEST.json"]), "offline_verifier": ARCHIVES[name][2],
                        "unmodified_offline_verifier_returncode": process.returncode,
                        "unmodified_offline_verifier_stdout": process.stdout.strip(),
                        "synthetic_substitute_used": False, "hash_override_used": False})
    record = {"source_git_commit": head, "checked_utc": e.now(), "archives": outputs,
              "nested_base_byte_identical_to_original": True, "actual_delivery_recorded": False,
              "reviewer_intake_attested_locally": False, "completed_independent_eligibility_return": False,
              "historical_protocols": e.baseline(e.read(e.CONFIG)), "gate": "FRAME_BLOCKED"}
    e.write_new(e.BASE / RUN / "AUTHENTIC_ORIGINAL_ARCHIVE_CHECKS.json", record)
    print(json.dumps(record, sort_keys=True))


def main() -> None:
    """Run separate clean-tree recovery milestones without deciding eligibility."""
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["import", "authenticate"])
    parser.add_argument("--source", type=Path, default=Path("C:/Users/LawLight/Downloads"))
    args = parser.parse_args()
    head = e.clean_head()
    e.baseline(e.read(e.CONFIG))
    if args.phase == "import":
        import_return(args.source, head)
    else:
        authenticate(head)


if __name__ == "__main__":
    main()
