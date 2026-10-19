"""Offline allowlist, schema, completeness and finite-language restriction checks."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

FILES = {
    "README.md", "verify_evidence.py", "WORK_EVIDENCE_CROSSWALK.json",
    "BIBLIOGRAPHIC_EVIDENCE.json", "METHOD_EVIDENCE.json", "EVIDENCE_RECEIPTS.json",
    "EXCEPTIONS.json", "MEMBER_COVERAGE.json", "PRIMARY_ACCESS_FOLLOWUPS.json",
    "SENTINEL_IDENTIFIER_CROSSWALK.json",
    "REVIEWER_INTAKE_BLANK.json", "ELIGIBILITY_REVIEW_BLANK.json",
    "EVIDENCE_RECEIPT_BLANK.json", "finite_language.json",
}
FINITE_LANGUAGE_SHA256 = "__FINITE_LANGUAGE_SHA256__"
METHOD_FIELDS = {
    "work_id", "member_id", "review_id", "quote", "grammar_rule", "ruleset",
    "locator", "section_id", "section_role", "paragraph_ordinal", "span_start", "span_end",
    "paragraph_sha256", "limitation", "evidence_id", "source_url", "version",
    "retrieved_utc", "http_or_access_status", "raw_source_sha256", "eligibility_inference",
}
BIB_FIELDS = {
    "work_id", "member_id", "review_id", "evidence_id", "captured_bibliography",
    "metadata_record_sha256", "date_fields_origin", "captured_version_id",
    "captured_updated_before_cutoff", "retrieved_body_version_evidence", "selected_protocol_version",
    "preferred_version_status", "access_attempts", "source_url", "version", "retrieved_utc",
    "http_or_access_status", "raw_source_sha256",
}
WORK_FIELDS = {
    "work_id", "review_id", "member_ids", "evidence_ids", "source_available",
    "exact_captured_version_body_verified", "final_preferred_version_verified",
    "has_verified_method_clause", "complete_method_evidence_ready", "decision",
}
COVERAGE_FIELDS = {
    "work_id", "member_id", "review_id", "acquisition_attempted", "source_available",
    "captured_source_version_body_verified", "final_preferred_version_verified",
    "relevant_method_regions_found", "quarantined_method_proposal_count",
    "closed_language_method_proposals_generated", "verified_method_evidence_ids",
    "restricted_bibliographic_packet_ready", "complete_method_evidence_ready",
    "delivered_to_reviewer", "independent_review_completed", "decision",
}
RECEIPT_FIELDS = {
    "work_id", "member_id", "review_id", "evidence_id", "source_url", "version",
    "retrieved_utc", "http_or_access_status", "raw_source_sha256", "provider_id",
    "requested_method_or_bibliographic_fact", "method_dataset_or_bibliographic_locator",
    "restricted_evidence_sha256", "restriction_checked_by",
    "qualitative_and_quantitative_findings_absent", "reviewer_received_utc", "limitations",
}
FOLLOWUP_FIELDS = {
    "work_id", "member_id", "captured_version_id", "metadata_provenance", "revision_history",
    "official_mirror_attempts", "exact_revision_mirror_body_available", "earlier_version_substituted",
    "eligibility_decision", "started_utc", "source_git_commit",
}
EXCEPTION_CODES = {
    "FINAL_PREFERRED_VERSION_REVIEW_REQUIRED", "MATERIAL_ELIGIBILITY_FACTS_NOT_ESTABLISHED",
    "PRIMARY_FULL_TEXT_UNAVAILABLE_NOT_AN_EXCLUSION", "PDF_LAYOUT_AND_SEMANTIC_RESTRICTION_CHECK_REQUIRED",
    "BROADER_METHOD_PROPOSALS_QUARANTINED_SEMANTIC_CHECKER_REQUIRED",
    "NO_METHOD_CLAUSE_ADMITTED_BY_CLOSED_LANGUAGE",
}


def load(root: Path, name: str) -> object:
    """Read explicit UTF-8 JSON."""
    return json.loads((root / name).read_text(encoding="utf-8"))


def digest(raw: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    """Reproduce custody commitments."""
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode()


def verify(root: Path) -> dict:
    """Reject overinclusive, altered, incomplete or result-bearing method payloads."""
    if {p.name for p in root.iterdir()} != FILES | {"MANIFEST.json"}:
        raise ValueError("UNEXPECTED_OR_MISSING_TRANSFER_FILES")
    if any(p.is_symlink() or not p.is_file() for p in root.iterdir()):
        raise ValueError("TRANSFER_MUST_BE_FLAT_REGULAR_FILES")
    manifest = load(root, "MANIFEST.json")
    if set(manifest["files"]) != FILES:
        raise ValueError("MANIFEST_ALLOWLIST_MISMATCH")
    for name, expected in manifest["files"].items():
        if digest((root / name).read_bytes()) != expected:
            raise ValueError("TRANSFER_HASH_MISMATCH:" + name)
    if digest((root / "finite_language.json").read_bytes()) != FINITE_LANGUAGE_SHA256:
        raise ValueError("FINITE_LANGUAGE_CHANGED")
    patterns = {name: re.compile(pattern, re.I) for name, pattern in load(root, "finite_language.json")["patterns"].items()}
    works = load(root, "WORK_EVIDENCE_CROSSWALK.json")
    bibliography = load(root, "BIBLIOGRAPHIC_EVIDENCE.json")
    methods = load(root, "METHOD_EVIDENCE.json")
    receipts = load(root, "EVIDENCE_RECEIPTS.json")
    coverage = load(root, "MEMBER_COVERAGE.json")
    exceptions = load(root, "EXCEPTIONS.json")
    for rows, fields in ((works, WORK_FIELDS), (coverage, COVERAGE_FIELDS), (receipts, RECEIPT_FIELDS),
                         (exceptions, {"work_id", "member_id", "review_id", "codes"})):
        if any(set(row) != fields for row in rows):
            raise ValueError("UNEXPECTED_TRANSFER_RECORD_FIELDS")
    if any(not set(row["codes"]).issubset(EXCEPTION_CODES) for row in exceptions):
        raise ValueError("UNCONTROLLED_EXCEPTION_PROSE")
    if len(works) != 372 or len({w["work_id"] for w in works}) != 372:
        raise ValueError("WORK_FRAME_MISMATCH")
    mids = [mid for w in works for mid in w["member_ids"]]
    if len(mids) != 389 or len(set(mids)) != 389:
        raise ValueError("SOURCE_MEMBERSHIP_MISMATCH")
    for rows in (bibliography, coverage, exceptions):
        if len(rows) != 389 or {r["member_id"] for r in rows} != set(mids):
            raise ValueError("INCOMPLETE_MEMBER_RECORDS")
    by_member = {r["member_id"]: r["work_id"] for r in bibliography}
    for work in works:
        if work["decision"] is not None or any(by_member[mid] != work["work_id"] for mid in work["member_ids"]):
            raise ValueError("FRAME_IDENTITY_OR_DECISION_MISMATCH")
    for b in bibliography:
        if set(b) != BIB_FIELDS or set(b["captured_bibliography"]) != {"doi", "published", "updated", "year", "month"}:
            raise ValueError("UNEXPECTED_BIBLIOGRAPHIC_FIELDS")
        if b["selected_protocol_version"] is not None:
            raise ValueError("FINAL_VERSION_NOT_INDEPENDENTLY_ESTABLISHED")
        if any(set(a) != {"url", "status", "started_utc", "finished_utc"} for a in b["access_attempts"]):
            raise ValueError("UNEXPECTED_ACCESS_PROSE")
        data = b["captured_bibliography"]
        if (data["year"] and not re.fullmatch(r"\d{4}", data["year"])):
            raise ValueError("INVALID_BIBLIOGRAPHIC_YEAR")
        if data["month"] not in {"", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"}:
            raise ValueError("INVALID_BIBLIOGRAPHIC_MONTH")
    total_words = {}
    for m in methods:
        if set(m) != METHOD_FIELDS or m["grammar_rule"] not in patterns:
            raise ValueError("UNEXPECTED_METHOD_SCHEMA")
        if not patterns[m["grammar_rule"]].fullmatch(m["quote"]):
            raise ValueError("METHOD_QUOTE_OUTSIDE_FINITE_LANGUAGE")
        if m["member_id"] not in by_member or m["work_id"] != by_member[m["member_id"]]:
            raise ValueError("METHOD_IDENTITY_MISMATCH")
        if m["eligibility_inference"] != "NOT_PERFORMED":
            raise ValueError("ELIGIBILITY_INFERENCE_NOT_AUTHORIZED")
        total_words[m["work_id"]] = total_words.get(m["work_id"], 0) + len(m["quote"].split())
    if any(n > 25 for n in total_words.values()):
        raise ValueError("LITERAL_QUOTE_DISPLAY_BOUND_EXCEEDED")
    evidence = {r["evidence_id"]: r for r in [*bibliography, *methods]}
    if len(evidence) != len(bibliography) + len(methods):
        raise ValueError("DUPLICATE_EVIDENCE")
    if len(receipts) != len(evidence) or {r["evidence_id"] for r in receipts} != set(evidence):
        raise ValueError("MISSING_OR_DUPLICATE_EVIDENCE_RECEIPTS")
    for r in receipts:
        if r["restricted_evidence_sha256"] != digest(canonical(evidence[r["evidence_id"]])):
            raise ValueError("EVIDENCE_RECEIPT_HASH_MISMATCH")
        if r["reviewer_received_utc"] is not None:
            raise ValueError("ACTUAL_REVIEWER_DELIVERY_NOT_ESTABLISHED")
    for f in load(root, "PRIMARY_ACCESS_FOLLOWUPS.json"):
        if set(f) != FOLLOWUP_FIELDS or f["eligibility_decision"] is not None or f["earlier_version_substituted"]:
            raise ValueError("FOLLOWUP_SCHEMA_OR_VERSION_SUBSTITUTION")
        if set(f["metadata_provenance"]) != {"source_url", "retrieved_utc", "http_or_access_status", "raw_source_sha256", "locator", "mode"}:
            raise ValueError("UNEXPECTED_FOLLOWUP_METADATA_PROSE")
        if any(set(r) != {"revision", "public_utc", "withdrawn_in_history"} for r in f["revision_history"]):
            raise ValueError("UNEXPECTED_REVISION_HISTORY_PROSE")
        if any(set(a) != {"url", "status", "started_utc", "finished_utc"} for a in f["official_mirror_attempts"]):
            raise ValueError("UNEXPECTED_MIRROR_PROSE")
    sentinel_rows = load(root, "SENTINEL_IDENTIFIER_CROSSWALK.json")
    if (len(sentinel_rows) != 372
            or {r["work_id"] for r in sentinel_rows} != {w["work_id"] for w in works}
            or any(set(r) != {"work_id", "review_id", "exact_identifier_matches", "matching_scope", "decision"}
                   or r["decision"] is not None for r in sentinel_rows)):
        raise ValueError("SENTINEL_CROSSWALK_MISMATCH")
    if any(set(m) != {"sentinel_id", "exclude_versions"} for r in sentinel_rows for m in r["exact_identifier_matches"]):
        raise ValueError("UNEXPECTED_SENTINEL_EXPOSURE_PROSE")
    if {eid for w in works for eid in w["evidence_ids"]} != set(evidence):
        raise ValueError("WORK_EVIDENCE_CROSSWALK_MISMATCH")
    blank = load(root, "ELIGIBILITY_REVIEW_BLANK.json")
    if len(blank) != 372 or {r["work_id"] for r in blank} != {w["work_id"] for w in works}:
        raise ValueError("BLANK_REVIEW_FRAME_MISMATCH")
    if any(value is not None for row in blank for key, value in row.items() if key not in {"review_id", "work_id"}):
        raise ValueError("REVIEW_NOT_BLANK")
    for name in ("REVIEWER_INTAKE_BLANK.json", "EVIDENCE_RECEIPT_BLANK.json"):
        if any(v is not None for v in load(root, name).values()):
            raise ValueError("ATTESTATION_TEMPLATE_NOT_BLANK")
    if (manifest["gate"] != "FRAME_BLOCKED" or manifest["draw_executed"]
            or manifest["delivered_to_reviewer"] or manifest["separate_semantic_checker_established"]):
        raise ValueError("GATE_OR_ROLE_STATUS_INVALID")
    return {"integrity": "PASS", "works": 372, "members": 389, "method_clauses": len(methods),
            "independent_review": "NOT_COMPLETED", "gate": "FRAME_BLOCKED"}


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
