"""Offline verification of the consolidated, restricted source-evidence transfer."""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

FILES = {"BASE_EVIDENCE_SUPPLEMENT.zip", "SEMANTIC_METHOD_FACTS.json", "SEMANTIC_EVIDENCE_RECEIPTS.json",
         "SEMANTIC_COVERAGE.json", "RESTRICTION_EXCEPTIONS.json", "CHECKER_ROLE_RECEIPTS.json",
         "README.md", "verify_semantic.py"}
OUTCOME = re.compile('\\b(?:FPR|FNR|TPR|ASR|AUC|ROC|accuracy|precision|recall|F1|true.positive|false.positive|false.negative|confidence|guarantee\\w*|assur\\w*|statistic\\w*|significan\\w*|outperform\\w*|surpass\\w*|achiev\\w*|improv\\w*|degrad\\w*|superior|inferior|best|worst|better|worse|highest|lowest|effective\\w*|success\\w*|failure\\w*|robust\\w*|stronger|weaker|negligible|near.zero|competitive|performance|empirically|findings?|results?|observed|demonstrate\\w*|show(?:s|ed)?|reveal\\w*|hundred\\w*|thousand\\w*|million\\w*|percent\\w*)\\b|[%=<>\\d]', re.I)
SAFE_LIMITATION = 'Bounded method context only; no full-work eligibility or statistical review. Evaluation language, timing, and uninspected baseline methods remain unresolved unless separately established.'
SPELLED_COUNTS = re.compile('\\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|hundred|thousand)\\s+(?:(?:benign|malicious|clean|negative|positive|test|evaluation|training)\\s+)?(?:samples?|examples?|prompts?|instances?|records?|items?)\\b', re.I)
FACT_FIELDS = {"evidence_id", "work_id", "review_id", "member_id", "fact_kind", "method_fact",
               "source_url", "version", "raw_source_sha256", "locator", "restriction_checked_by",
               "checked_utc", "limitation", "source_checker_record_sha256", "eligibility_decision"}
KINDS = {"INPUT_TASK", "EVALUATION_UNIT", "BINARY_PROCEDURE", "PRE_TARGET_TIMING", "ENGLISH_EVALUATION",
         "DATASET_PROVENANCE", "METHOD_BOUNDARY"}
ACTORS = {"/root/a04_semantic_restriction", "/root/a04_semantic_restriction_02", "/root/a04_semantic_restriction_03"}
COVERAGE_FIELDS = {"work_id", "review_id", "member_ids", "source_restriction_checker",
                   "context_checked_member_ids", "restricted_method_evidence_ids",
                   "additional_restriction_correction_needed", "remaining_eligibility_facts_require_review",
                   "final_preferred_version_independently_verified", "delivered_to_reviewer",
                   "independent_eligibility_review_completed", "eligibility_decision"}
RECEIPT_FIELDS = {"evidence_id", "work_ids", "requested_method_or_bibliographic_fact", "provider_id",
                  "source_url", "version", "method_dataset_or_bibliographic_locator", "retrieved_utc",
                  "http_or_access_status", "raw_source_sha256", "restricted_evidence_sha256",
                  "restriction_checked_by", "restriction_checked_utc", "mechanical_release_checked_by",
                  "qualitative_and_quantitative_findings_absent", "reviewer_received_utc", "limitations"}
ROLE_FIELDS = {"actor_id", "role", "separate_task_context_fork_turns", "shared_filesystem",
               "os_isolation_claimed", "eligibility_review_claimed", "actual_completion_report_received"}
EXCEPTION_FIELDS = {"work_id", "review_id", "checker", "fact_id", "source_checker_record_sha256", "codes"}


def sha(raw: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    """Reproduce exact evidence commitments."""
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode()


def valid_locator(locator: dict) -> bool:
    """Accept only public structural locators; no local paths or unbounded fields."""
    digest = lambda x: isinstance(x, str) and re.fullmatch(r"[a-f0-9]{64}", x)
    if locator.get("format") == "HTML":
        return (set(locator) == {"format", "evidence_paragraphs"} and bool(locator["evidence_paragraphs"])
                and all(set(p) == {"global_p_ltx_p_ordinal", "section_id", "paragraph_text_sha256"}
                        and type(p["global_p_ltx_p_ordinal"]) is int and p["global_p_ltx_p_ordinal"] >= 0
                        and digest(p["paragraph_text_sha256"]) for p in locator["evidence_paragraphs"]))
    if locator.get("format") == "PDF":
        return (set(locator) == {"format", "evidence_pages", "method_section_locator"}
                and bool(locator["evidence_pages"])
                and not OUTCOME.search(re.sub(r"\d", "", locator["method_section_locator"]))
                and all(set(p) == {"page_number_1based", "rendered_page_sha256", "page_text_sha256"}
                        and type(p["page_number_1based"]) is int and p["page_number_1based"] >= 1
                        and digest(p["rendered_page_sha256"]) and digest(p["page_text_sha256"])
                        for p in locator["evidence_pages"]))
    return False


def verify(root: Path) -> dict:
    """Reject altered, overinclusive, unbound or nonblank research transfers."""
    if {p.name for p in root.iterdir()} != FILES | {"MANIFEST.json"}:
        raise ValueError("SEMANTIC_TRANSFER_FILE_ALLOWLIST")
    if any(p.is_symlink() or not p.is_file() for p in root.iterdir()):
        raise ValueError("SEMANTIC_TRANSFER_NOT_FLAT")
    load = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    manifest = load("MANIFEST.json")
    if set(manifest["files"]) != FILES:
        raise ValueError("SEMANTIC_MANIFEST_ALLOWLIST")
    for name, digest in manifest["files"].items():
        if sha((root / name).read_bytes()) != digest:
            raise ValueError("SEMANTIC_FILE_HASH_MISMATCH")
    raw = (root / "BASE_EVIDENCE_SUPPLEMENT.zip").read_bytes()
    if sha(raw) != "066c27ae28ad941ea9ebf963f3fc5d854b2bcd39d1fb060a16b52b5cc4294c08":
        raise ValueError("FROZEN_BASE_ARCHIVE_CHANGED")
    with zipfile.ZipFile(io.BytesIO(raw)) as base:
        names = base.namelist()
        if len(names) != len(set(names)) or any(Path(n).name != n for n in names):
            raise ValueError("UNSAFE_BASE_ARCHIVE_MEMBERS")
        inner_manifest = json.loads(base.read("MANIFEST.json"))
        if set(names) != set(inner_manifest["files"]) | {"MANIFEST.json"}:
            raise ValueError("BASE_ARCHIVE_FILE_ALLOWLIST")
        if any(sha(base.read(name)) != digest for name, digest in inner_manifest["files"].items()):
            raise ValueError("BASE_ARCHIVE_INNER_HASH")
        original = json.loads(base.read("WORK_EVIDENCE_CROSSWALK.json"))
        blanks = json.loads(base.read("ELIGIBILITY_REVIEW_BLANK.json"))
    if any(v is not None for row in blanks for k, v in row.items() if k not in {"review_id", "work_id"}):
        raise ValueError("BLANK_REVIEW_CHANGED")
    facts, receipts = load("SEMANTIC_METHOD_FACTS.json"), load("SEMANTIC_EVIDENCE_RECEIPTS.json")
    coverage = load("SEMANTIC_COVERAGE.json")
    by_work = {r["work_id"]: r for r in original}
    if len(coverage) != 372 or {r["work_id"] for r in coverage} != set(by_work):
        raise ValueError("SEMANTIC_FRAME_CHANGED")
    if any(set(r) != COVERAGE_FIELDS or set(r["member_ids"]) != set(by_work[r["work_id"]]["member_ids"])
           or r["review_id"] != by_work[r["work_id"]]["review_id"]
           or r["source_restriction_checker"] not in ACTORS
           or len(r["context_checked_member_ids"]) != len(set(r["context_checked_member_ids"]))
           or not set(r["context_checked_member_ids"]).issubset(r["member_ids"])
           or r["eligibility_decision"] is not None or r["delivered_to_reviewer"] is not False
           or r["final_preferred_version_independently_verified"] is not False
           or r["independent_eligibility_review_completed"] is not False
           or r["remaining_eligibility_facts_require_review"] is not True for r in coverage):
        raise ValueError("SEMANTIC_MEMBERSHIP_OR_DECISION_CHANGED")
    if sum(len(r["member_ids"]) for r in coverage) != 389:
        raise ValueError("SEMANTIC_MEMBER_COUNT_CHANGED")
    by_id = {}
    word_totals = {}
    for f in facts:
        if (set(f) != FACT_FIELDS or f["fact_kind"] not in KINDS
                or f["restriction_checked_by"] not in ACTORS or f["eligibility_decision"] is not None
                or f["work_id"] not in by_work or f["member_id"] not in by_work[f["work_id"]]["member_ids"]
                or f["review_id"] != by_work[f["work_id"]]["review_id"]):
            raise ValueError("UNEXPECTED_SEMANTIC_FACT_SCHEMA")
        if OUTCOME.search(f["method_fact"]) or SPELLED_COUNTS.search(f["method_fact"]):
            raise ValueError("PROHIBITED_METHOD_CONTENT")
        if not valid_locator(f["locator"]):
            raise ValueError("UNEXPECTED_PUBLIC_SOURCE_LOCATOR")
        if f["limitation"] != SAFE_LIMITATION and (OUTCOME.search(f["limitation"]) or SPELLED_COUNTS.search(f["limitation"])):
            raise ValueError("PROHIBITED_LIMITATION_CONTENT")
        if f["evidence_id"] in by_id:
            raise ValueError("DUPLICATE_SEMANTIC_FACT")
        by_id[f["evidence_id"]] = f
        word_totals[f["work_id"]] = word_totals.get(f["work_id"], 0) + len(f["method_fact"].split())
    if any(n > 180 for n in word_totals.values()):
        raise ValueError("SEMANTIC_PARAPHRASE_DISPLAY_BOUND")
    if len(receipts) != len(facts) or {r["evidence_id"] for r in receipts} != set(by_id):
        raise ValueError("SEMANTIC_RECEIPT_COMPLETENESS")
    for r in receipts:
        fact = by_id[r["evidence_id"]]
        if (set(r) != RECEIPT_FIELDS or r["restricted_evidence_sha256"] != sha(canonical(fact))
                or r["reviewer_received_utc"] is not None or r["work_ids"] != [fact["work_id"]]
                or r["source_url"] != fact["source_url"] or r["version"] != fact["version"]
                or r["raw_source_sha256"] != fact["raw_source_sha256"]
                or r["restriction_checked_by"] != fact["restriction_checked_by"]
                or r["restriction_checked_utc"] != fact["checked_utc"]
                or r["limitations"] != fact["limitation"]
                or r["method_dataset_or_bibliographic_locator"] != fact["locator"]
                or r["qualitative_and_quantitative_findings_absent"] is not True):
            raise ValueError("SEMANTIC_RECEIPT_HASH_OR_DELIVERY")
    linked = [eid for r in coverage for eid in r["restricted_method_evidence_ids"]]
    if len(linked) != len(set(linked)) or set(linked) != set(by_id):
        raise ValueError("SEMANTIC_EVIDENCE_CROSSWALK")
    for row in coverage:
        for eid in row["restricted_method_evidence_ids"]:
            if (by_id[eid]["work_id"] != row["work_id"]
                    or by_id[eid]["member_id"] not in row["context_checked_member_ids"]
                    or by_id[eid]["restriction_checked_by"] != row["source_restriction_checker"]):
                raise ValueError("SEMANTIC_CONTEXT_CROSSWALK")
    roles = load("CHECKER_ROLE_RECEIPTS.json")
    if len(roles) != 3 or {r["actor_id"] for r in roles} != ACTORS or any(
            set(r) != ROLE_FIELDS or r["os_isolation_claimed"] is not False
            or r["eligibility_review_claimed"] is not False or r["shared_filesystem"] is not True
            or r["separate_task_context_fork_turns"] != "none"
            or r["role"] != "SOURCE_RESTRICTION_CHECKER_NOT_ELIGIBILITY_REVIEWER"
            or r["actual_completion_report_received"] is not True for r in roles):
        raise ValueError("CHECKER_ROLES_MISREPRESENTED")
    exceptions = load("RESTRICTION_EXCEPTIONS.json")
    if any(set(row) != EXCEPTION_FIELDS or row["work_id"] not in by_work
           or row["review_id"] != by_work[row["work_id"]]["review_id"]
           or any(not re.fullmatch(r"[A-Z_]+", code) for code in row["codes"]) for row in exceptions):
        raise ValueError("UNEXPECTED_EXCEPTION_CONTENT")
    if (manifest["gate"] != "FRAME_BLOCKED" or manifest["draw_executed"]
            or manifest["actual_independent_eligibility_review"] != "NOT_RECEIVED"
            or manifest["actual_delivery"] != "NOT_PERFORMED"):
        raise ValueError("SEMANTIC_GATE_STATUS")
    return {"integrity": "PASS", "works": 372, "members": 389, "method_facts": len(facts),
            "independent_eligibility_review": "NOT_RECEIVED", "gate": "FRAME_BLOCKED"}


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
