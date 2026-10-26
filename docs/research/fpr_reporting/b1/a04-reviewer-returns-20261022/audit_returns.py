"""Audit received B1 review mechanics against locked released evidence only.

This never reads historical custodian judgments or adjudicates eligibility.
Run on a clean research checkout with --output to freeze a new assessment.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import io
import json
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
WRAPPER = HERE.parent / "a04-provisional-recovery-v1-20261021/REVIEWER_RECOVERY_TRANSFER.zip"
PINS = {
    "B1_SUBSTANTIVE_REVIEW.zip": "b2f0d658ebc0bf7e27d214029e1007327c363f4fd73a4c480833103e1eb8bcbb",
    "ELIGIBILITY_REVIEWS.zip": "b8d9352eb67b69765497b09818184f022127ffc79216495cea61cc096ef54fe7",
}
WRAPPER_PIN = "d105eed48c37e6532776060b3aec4ab70ece3cad885d1555ce08d54c89cf5142"
CRITERIA = ("input_injection_task", "binary_evaluation", "before_target_answer", "english_evaluation")


def encoded(value: object) -> bytes:
    """Keep audit outputs deterministic apart from explicit execution provenance."""
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode()


def archive(raw: bytes, expected: str | None = None) -> dict[str, bytes]:
    """Check committed receipt pins and reject unsafe ZIPs before extraction."""
    if expected and hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("ARCHIVE_HASH_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
        entries = zipped.infolist()
        names = [x.filename for x in entries]
        if len(names) != len(set(names)):
            raise ValueError("DUPLICATE_ARCHIVE_ENTRY")
        for item in entries:
            name = item.filename.replace("\\", "/")
            if (name.startswith("/") or ":" in name or ".." in PurePosixPath(name).parts
                    or stat.S_ISLNK(item.external_attr >> 16) or item.is_dir()
                    or item.file_size > 10_000_000):
                raise ValueError("UNSAFE_ARCHIVE_ENTRY")
        if sum(x.file_size for x in entries) > 30_000_000 or zipped.testzip():
            raise ValueError("ARCHIVE_SIZE_OR_CRC_FAILURE")
        return {name: zipped.read(name) for name in names}


def manifest_check(files: dict[str, bytes], name: str) -> None:
    """Check exact payload coverage, including the original return verifier."""
    manifest = json.loads(files[name])["files"]
    if set(manifest) != set(files) - {name}:
        raise ValueError("MANIFEST_COVERAGE")
    if any(hashlib.sha256(files[n]).hexdigest() != pin for n, pin in manifest.items()):
        raise ValueError("MANIFEST_HASH")


def reference_issues(rows: list[dict], evidence: dict[str, dict]) -> list[dict]:
    """Check citations without converting their presence into criterion support."""
    issues = []
    for row in rows:
        for eid in row["evidence_ids"]:
            source = evidence.get(eid)
            if source is None or source.get("work_id") != row["work_id"]:
                issues.append({"review_id": row["review_id"], "evidence_id": eid,
                               "issue": "UNKNOWN_OR_OTHER_WORK_REFERENCE"})
        for locator in row["method_bibliographic_locators"]:
            if isinstance(locator, dict) and "evidence_id" in locator:
                source = evidence.get(locator["evidence_id"], {})
                if locator["evidence_id"] not in row["evidence_ids"] or any(
                        locator[k] != source.get(k) for k in ("source_url", "version", "locator") if k in locator):
                    issues.append({"review_id": row["review_id"], "issue": "SOURCE_LOCATOR_MISMATCH"})
            elif not any(locator == evidence.get(eid, {}).get("locator") for eid in row["evidence_ids"]):
                issues.append({"review_id": row["review_id"], "issue": "UNLINKED_BARE_LOCATOR"})
    return issues


def projection_comparison(rows: list[dict], responses: list[dict]) -> dict:
    """Measure label agreement with provider flags; do not infer authorship."""
    by_id = {x["review_id"]: x for x in rows}
    pairs: collections.Counter = collections.Counter()
    differences = []
    for response in responses:
        row = by_id[response["review_id"]]
        for criterion in response["criterion_evidence"]:
            name = criterion["criterion"]
            if name not in CRITERIA:
                continue
            projected = "UNCLEAR" if criterion["further_controlled_evidence_needed"] else "MET"
            pairs[(projected, row[name])] += 1
            if projected != row[name]:
                differences.append({"review_id": row["review_id"], "criterion": name,
                                    "provider_projection": projected, "review_B": row[name]})
    return {"cells": sum(pairs.values()), "matching_cells": sum(v for (a, b), v in pairs.items() if a == b),
            "pairs": [{"provider_projection": a, "review_B": b, "cells": n} for (a, b), n in sorted(pairs.items())],
            "differences": differences,
            "interpretation": "Exact agreement is observable; it does not prove how the review was produced or establish scientific independence."}


def date_issues(rows: list[dict], official: list[dict]) -> list[dict]:
    """Flag unsupported date precision and revision-date disagreements only."""
    issues = []
    for row in rows:
        selected = row["selected_version_id"] or ""
        given = (row["version_date"] or "").replace("/", "-")
        records = [x for x in official if x["review_id"] == row["review_id"]]
        if selected.startswith("arxiv:") and re.search(r"v\d+$", selected):
            revision = re.search(r"v\d+$", selected).group()
            dates = {x["public_utc"][:10] for record in records
                     for x in record["official_fields"]["revision_history"] if x["revision"] == revision}
            if dates and given not in dates:
                issues.append({"review_id": row["review_id"], "selected_version_id": selected,
                               "reported_version_date": row["version_date"], "official_revision_dates": sorted(dates),
                               "issue": "SELECTED_REVISION_DATE_MISMATCH"})
        if selected.startswith("acl:") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", given):
            identifier = selected.removeprefix("acl:").removesuffix(":publication")
            literals = [x["value"] for record in records
                        if record["provenance"]["source_url"].rstrip("/").endswith(identifier)
                        for x in record["official_fields"]["publication_date_literals"]]
            if literals and not any(re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", x) for x in literals):
                issues.append({"review_id": row["review_id"], "selected_version_id": selected,
                               "reported_version_date": row["version_date"], "official_publication_literals": literals,
                               "issue": "DAY_PRECISION_NOT_SUPPORTED_BY_MONTH_ONLY_RECORD"})
    return issues


def audit() -> dict:
    """Reconcile two received packages against the same unchanged source inputs."""
    packages = {name: archive((HERE / name).read_bytes(), pin) for name, pin in PINS.items()}
    a = packages["B1_SUBSTANTIVE_REVIEW.zip"]
    b = packages["ELIGIBILITY_REVIEWS.zip"]
    manifest_check(a, "B1_SHA256_MANIFEST.json")
    wrapper = archive(WRAPPER.read_bytes(), WRAPPER_PIN)
    manifest_check(wrapper, "MANIFEST.json")
    originals = {name: archive(wrapper[name]) for name in (
        "FRESH_REVIEWER_INTAKE.zip", "RESTRICTED_EVIDENCE_SUPPLEMENT.zip", "CONSOLIDATED_RESTRICTED_EVIDENCE.zip",
        "RECOVERY_CONTROLLED_EVIDENCE.zip")}
    for files in originals.values():
        manifest_check(files, "MANIFEST.json")
    intake = originals["FRESH_REVIEWER_INTAKE.zip"]
    base = originals["RESTRICTED_EVIDENCE_SUPPLEMENT.zip"]
    semantic = originals["CONSOLIDATED_RESTRICTED_EVIDENCE.zip"]
    recovery = originals["RECOVERY_CONTROLLED_EVIDENCE.zip"]
    inventory = json.loads(intake["CANDIDATE_INVENTORY.json"])
    inventory_by_id = {x["review_id"]: x for x in inventory}
    method_rows = json.loads(base["METHOD_EVIDENCE.json"]) + json.loads(semantic["SEMANTIC_METHOD_FACTS.json"]) + json.loads(recovery["RECOVERY_METHOD_FACTS.json"])
    methods = {x["evidence_id"]: x for x in method_rows}
    evidence = dict(methods)
    for row in json.loads(base["BIBLIOGRAPHIC_EVIDENCE.json"]):
        evidence[row["evidence_id"]] = row
    for name, raw in recovery.items():
        if name.endswith(".json") and name != "MANIFEST.json":
            value = json.loads(raw)
            if isinstance(value, list):
                for row in value:
                    if isinstance(row, dict) and "evidence_id" in row and row["evidence_id"] not in evidence:
                        item = dict(row)
                        if "work_id" not in item and item.get("review_id") in inventory_by_id:
                            item["work_id"] = inventory_by_id[item["review_id"]]["work_id"]
                        evidence[item["evidence_id"]] = item
    rows_a = json.loads(a["B1_ELIGIBILITY_REVIEW_372.json"])
    rows_b = json.loads(b["ELIGIBILITY_REVIEW.json"])
    rationales = json.loads(a["B1_SCIENTIFIC_WORK_RATIONALES.json"])
    assessments = json.loads(a["B1_ALL_METHOD_FACT_ASSESSMENTS.json"])
    requests = json.loads(a["B1_PRECISION_CONTROLLED_REQUESTS.json"])
    index = json.loads(b["INDEX.json"])
    by_a, by_b = ({x["review_id"]: x for x in rows} for rows in (rows_a, rows_b))
    for rows, by_id in ((rows_a, by_a), (rows_b, by_b)):
        if len(rows) != 372 or len(by_id) != 372 or set(by_id) != set(inventory_by_id):
            raise ValueError("WORK_COVERAGE_CHANGED")
        if any(row["work_id"] != inventory_by_id[row["review_id"]]["work_id"] for row in rows):
            raise ValueError("WORK_ID_CHANGED")
    expected_b = {"ELIGIBILITY_REVIEW.json", "INDEX.json", "README.md"} | {f"reviews/{rid}.json" for rid in by_b}
    if set(b) != expected_b or len(index["reviews"]) != 372:
        raise ValueError("REVIEW_B_FILE_COVERAGE")
    for item in index["reviews"]:
        row = by_b[item["review_id"]]
        if json.loads(b[item["file"]]) != row or any(item[k] != row[k] for k in ("decision", "work_id", "selected_version_id")):
            raise ValueError("REVIEW_B_INDIVIDUAL_OR_INDEX_MISMATCH")
    exact_all = {x["review_id"] for x in json.loads(base["SENTINEL_IDENTIFIER_CROSSWALK.json"])
                 if any(y["exclude_versions"] == "ALL" for y in x["exact_identifier_matches"])}
    for by_id in (by_a, by_b):
        if any(by_id[rid]["decision"] not in {"EXCLUDE", "EXCLUDED"} for rid in exact_all):
            raise ValueError("LOCKED_SENTINEL_NOT_EXCLUDED")
    fact_issues = []
    if len(assessments) != 828 or {x["evidence_id"] for x in assessments} != set(methods):
        raise ValueError("METHOD_ASSESSMENT_COVERAGE")
    for row in assessments:
        source = methods[row["evidence_id"]]
        if any(row[k] != source[k] for k in ("work_id", "review_id", "version")) or row["fact"] != source.get("method_fact", source.get("quote")):
            fact_issues.append(row["evidence_id"])
    rationale_issues = []
    for row in rationales:
        rid = row["review_id"]
        if set(row["memberships"]) != {x["member_id"] for x in inventory_by_id[rid]["members"]}:
            rationale_issues.append({"review_id": rid, "issue": "MEMBERSHIP_MISMATCH"})
        for item in row["method_evidence_considered"]:
            source = methods.get(item["evidence_id"], {})
            if (source.get("work_id") != row["work_id"] or item["bounded_method_fact"] != source.get("method_fact", source.get("quote"))
                    or item["source_version"] != source.get("version") or item["locator"] != source.get("locator")):
                rationale_issues.append({"review_id": rid, "issue": "RATIONALE_SOURCE_MISMATCH", "evidence_id": item["evidence_id"]})
    norm = {"ELIGIBLE": "INCLUDE", "EXCLUDED": "EXCLUDE"}
    disagreements = [{"review_id": rid, "work_id": by_a[rid]["work_id"], "A": by_a[rid]["decision"], "B": by_b[rid]["decision"]}
                     for rid in by_a if by_a[rid]["decision"] != norm.get(by_b[rid]["decision"], by_b[rid]["decision"])]
    includes_a = {rid for rid, row in by_a.items() if row["decision"] == "INCLUDE"}
    includes_b = {rid for rid, row in by_b.items() if row["decision"] == "ELIGIBLE"}
    mixed = {}
    for label, by_id, accepted in (("A", by_a, includes_a), ("B", by_b, includes_b)):
        mixed[label] = [{"review_id": rid, "selected_version_id": by_id[rid]["selected_version_id"],
                         "method_source_versions": sorted({methods[eid]["version"] for eid in by_id[rid]["evidence_ids"] if eid in methods})}
                        for rid in sorted(accepted) if any(methods[eid]["version"] != by_id[rid]["selected_version_id"]
                                                          for eid in by_id[rid]["evidence_ids"] if eid in methods)]
    receipt_comparisons = []
    for row in json.loads(a["B1_SOURCE_RECEIPT_RECORD.json"]):
        name = {"intake": "FRESH_REVIEWER_INTAKE.zip", "base": "RESTRICTED_EVIDENCE_SUPPLEMENT.zip",
                "semantic": "CONSOLIDATED_RESTRICTED_EVIDENCE.zip", "recovery": "RECOVERY_CONTROLLED_EVIDENCE.zip"}[row["component"]]
        files = originals[name]
        expected = {n: hashlib.sha256(raw).hexdigest() for n, raw in files.items() if n != "MANIFEST.json"}
        receipt_comparisons.append({"component": row["component"], "payload_hashes_match_original": row["manifest_file_sha256"] == expected,
                                    "manifest_hash_matches_original": row["manifest_sha256"] == hashlib.sha256(files["MANIFEST.json"]).hexdigest()})
    with tempfile.TemporaryDirectory(prefix="warrant-return-verifier-") as directory:
        target = Path(directory)
        for name, raw in a.items():
            (target / name).write_bytes(raw)
        process = subprocess.run([sys.executable, "-I", str(target / "B1_VERIFY_RETURN.py")], cwd=target,
                                 capture_output=True, text=True, timeout=60)
        original_verifier = {"exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr}
    official = json.loads(recovery["OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json"])
    return {"scope": "MECHANICAL_AND_EVIDENCE_PROVENANCE_REVIEW_ONLY_NO_ELIGIBILITY_ADJUDICATION",
            "archive_pins": PINS, "inventory": {"works": len(inventory), "memberships": sum(len(x["members"]) for x in inventory)},
            "review_A_manifest": "PASS", "review_B_individual_files_and_index": "PASS", "review_A_original_verifier": original_verifier,
            "review_A_source_receipt_commitments": receipt_comparisons, "locked_all_version_sentinel_ids": sorted(exact_all),
            "counts": {"A": dict(collections.Counter(x["decision"] for x in rows_a)), "B": dict(collections.Counter(x["decision"] for x in rows_b))},
            "included_ids": {"A": sorted(includes_a), "B": sorted(includes_b), "common": sorted(includes_a & includes_b), "union_not_a_frame": sorted(includes_a | includes_b)},
            "decision_disagreements": disagreements,
            "reference_issues": {"A": reference_issues(rows_a, evidence), "B": reference_issues(rows_b, evidence)},
            "review_A_fact_text_issues": fact_issues, "review_A_rationale_source_issues": rationale_issues,
            "review_A_requests": {"items": len(requests), "work_ids": len({x["review_id"] for x in requests}), "by_criterion": dict(collections.Counter(x["criterion"] for x in requests))},
            "date_issues": {"A": date_issues(rows_a, official), "B": date_issues(rows_b, official)},
            "accepted_rows_citing_other_versions": mixed,
            "provider_flag_comparison_B": projection_comparison(rows_b, json.loads(recovery["CONTROLLED_REQUEST_RESPONSES.json"])),
            "independence": {"user_states_fresh_reviewer_provenance": True, "A_declares_freshness": json.loads(a["B1_VALIDATION.json"])["A04_freshness_attested"],
                             "B_claims_independent_in_README": True, "B_has_separate_intake_or_delivery_receipt": False,
                             "custodian_does_not_fabricate_or_resolve_conflicting_attestations": True},
            "gate": "FRAME_BLOCKED", "draw_performed": False, "B2_authorized": False,
            "historical_custodian_judgments_read_or_compared": False}


def main() -> None:
    """Print checks, or freeze a new append-only receipt from a clean checkout."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip())
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    if args.output and subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True):
        raise SystemExit("CLEAN_WORKTREE_REQUIRED_BEFORE_FREEZING_AUDIT")
    result = audit()
    result["source_head"] = head
    result["performed_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    if args.output:
        if args.output.exists():
            raise SystemExit("APPEND_ONLY_OUTPUT_ALREADY_EXISTS")
        args.output.write_bytes(encoded(result))
    print(json.dumps({"counts": result["counts"], "disagreements": len(result["decision_disagreements"]),
                      "common_eligible_ids": result["included_ids"]["common"],
                      "reference_issues": {k: len(v) for k, v in result["reference_issues"].items()},
                      "date_issues": {k: len(v) for k, v in result["date_issues"].items()},
                      "original_verifier_exit": result["review_A_original_verifier"]["exit_code"], "gate": result["gate"]}, sort_keys=True))


if __name__ == "__main__":
    main()
