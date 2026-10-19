"""Validate separate restriction-checker returns without deciding eligibility.

Root remains the exposed custodian. Separate checker contexts share a filesystem;
neither this module nor their source checks constitute A04 eligibility review.
"""
from __future__ import annotations

import argparse
import functools
import json
import re
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from bs4 import BeautifulSoup
import fitz

import a04_evidence as e

RUN = "a04-semantic-evidence-v1-20261020"
ACTORS = {
    "01": "/root/a04_semantic_restriction",
    "02": "/root/a04_semantic_restriction_02",
    "03": "/root/a04_semantic_restriction_03",
}
EXTRA_FIRST = {341, 348, 352, 354, 356}
KINDS = {"INPUT_TASK", "EVALUATION_UNIT", "BINARY_PROCEDURE", "PRE_TARGET_TIMING",
         "ENGLISH_EVALUATION", "DATASET_PROVENANCE", "METHOD_BOUNDARY"}
FACT_FIELDS = {
    "fact_id", "member_id", "fact_kind", "method_fact", "source_url", "version",
    "raw_source_sha256", "locator", "restriction_checked_by", "checked_utc",
    "limitation", "second_local_semantic_pass",
}
SAFE_LIMITATION = (
    "Bounded method context only; no full-work eligibility or statistical review. "
    "Evaluation language, timing, and uninspected baseline methods remain unresolved unless separately established."
)
SPELLED_COUNTS = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|hundred|thousand)\s+"
    r"(?:(?:benign|malicious|clean|negative|positive|test|evaluation|training)\s+)?"
    r"(?:samples?|examples?|prompts?|instances?|records?|items?)\b", re.I)


def owner(review_id: str) -> str:
    """Apply the operational partition; this does not sample or change the frame."""
    if not re.fullmatch(r"W\d{4}", review_id):
        raise ValueError("INVALID_REVIEW_ID")
    number = int(review_id[1:])
    if not 1 <= number <= 372:
        raise ValueError("OUT_OF_FRAME_REVIEW_ID")
    return "01" if number <= 124 or number in EXTRA_FIRST else "02" if number <= 248 else "03"


def latest_record(directory: Path, review_id: str) -> tuple[dict, Path]:
    """Validate immutable revision history before selecting the current return."""
    candidates = [p for p in directory.glob(review_id + "*.json")
                  if re.fullmatch(re.escape(review_id) + r"(?:\.\d{4})?\.json", p.name)]
    by_revision = {}
    for path in candidates:
        row = e.read(path)
        revision = row["record_revision"]
        if type(revision) is not int or revision < 1 or row["review_id"] != review_id:
            raise ValueError("INVALID_RECORD_REVISION")
        if revision in by_revision and e.encoded(by_revision[revision][0]) != e.encoded(row):
            raise ValueError("CONFLICTING_SAME_REVISION")
        by_revision[revision] = (row, path)
    if not by_revision:
        raise ValueError("CHECKER_RETURN_MISSING")
    if set(by_revision) != set(range(1, max(by_revision) + 1)):
        raise ValueError("CHECKER_REVISION_GAP")
    for revision, (row, _) in by_revision.items():
        parent = row["supersedes"]
        if revision == 1:
            if parent is not None:
                raise ValueError("INITIAL_REVISION_HAS_PARENT")
        else:
            if not isinstance(parent, str) or Path(parent).name != parent:
                raise ValueError("UNSAFE_SUPERSESSION_PATH")
            if not re.fullmatch(re.escape(review_id) + r"(?:\.\d{4})?\.json", parent):
                raise ValueError("UNSAFE_SUPERSESSION_NAME")
            prior = e.read(directory / parent)
            if e.encoded(prior) != e.encoded(by_revision[revision - 1][0]):
                raise ValueError("SUPERSESSION_CHAIN_MISMATCH")
    return by_revision[max(by_revision)]


def leakage_codes(fact: dict) -> list[str]:
    """Supplement genuine source-context checking with conservative content gates."""
    codes = []
    if e.OUTCOME.search(fact["method_fact"]) or SPELLED_COUNTS.search(fact["method_fact"]):
        codes.append("METHOD_TEXT_REQUIRES_RESTRICTION_CORRECTION")
    limitation = fact["limitation"]
    if limitation != SAFE_LIMITATION and (e.OUTCOME.search(limitation) or SPELLED_COUNTS.search(limitation)):
        codes.append("LIMITATION_TEXT_REQUIRES_RESTRICTION_CORRECTION")
    return codes


@functools.lru_cache(maxsize=8)
def paragraph_index(raw_path: str, digest: str) -> dict:
    """Reconstruct paragraph hashes and section ancestry without displaying text."""
    raw = Path(raw_path).read_bytes()
    if e.sha(raw) != digest:
        raise ValueError("SEMANTIC_PRIMARY_BODY_HASH_MISMATCH")
    soup = BeautifulSoup(raw, "html.parser")
    result = {}
    for ordinal, paragraph in enumerate(soup.select("p.ltx_p")):
        text = paragraph.get_text(" ", strip=True)
        section = paragraph.find_parent("section")
        forbidden = bool(paragraph.find_parent(["table", "figure", "figcaption", "blockquote"]))
        if any("abstract" in " ".join(p.get("class", [])) for p in paragraph.parents if p.name):
            forbidden = True
        result[ordinal] = {"section_id": section.get("id") if section else None,
                           "hashes": {e.sha(text.encode()), e.sha(e.normalized(text).encode())},
                           "protected_container": forbidden}
    return result


def validate_fact(fact: dict, record: dict, request: dict, body: dict) -> list[str]:
    """Require a real separate checker, exact version/body and reconstructable locators."""
    optional = {"source_context_original_checked_utc", "locator_checked_utc", "literal_quotation_words"}
    if not FACT_FIELDS.issubset(fact) or set(fact) - FACT_FIELDS - optional:
        return ["UNEXPECTED_SEMANTIC_FACT_FIELDS"]
    if fact.get("literal_quotation_words", 0) != 0:
        return ["SEMANTIC_LITERAL_QUOTATION_NOT_ALLOWED"]
    if (fact["member_id"] != request["member_id"] or fact["fact_kind"] not in KINDS
            or fact["restriction_checked_by"] != record["actor_id"]):
        return ["SEMANTIC_FACT_IDENTITY_MISMATCH"]
    if (not body or (body["kind"], body["version_state"]) not in {
            ("HTML", "EXACT_VERSION_SELF_LINK"), ("PDF", "EXACT_VERSION_IN_BODY")}
            or fact["raw_source_sha256"] != body["sha256"] or fact["source_url"] != body["url"]
            or fact["version"].removeprefix("arxiv:") != request["captured_version_id"].removeprefix("arxiv:")):
        return ["SEMANTIC_FACT_SOURCE_VERSION_UNVERIFIED"]
    check = fact["second_local_semantic_pass"]
    if (not isinstance(check, dict) or check.get("actor_id", check.get("checked_by")) != record["actor_id"]
            or check.get("literal_quotation_words", 0) != 0
            or not (check.get("status") or (check.get("performed") is True and check.get("scope")))):
        return ["SEMANTIC_RESTRICTION_PASS_UNATTESTED"]
    for stamp in (fact["checked_utc"], check.get("checked_utc")):
        try:
            if datetime.fromisoformat(stamp).utcoffset() != timedelta(0):
                return ["SEMANTIC_CHECK_TIMESTAMP_NOT_UTC"]
        except (TypeError, ValueError):
            return ["SEMANTIC_CHECK_TIMESTAMP_INVALID"]
    locator = fact["locator"]
    if body["kind"] == "PDF":
        return validate_pdf_locator(locator, body) + leakage_codes(fact)
    if not isinstance(locator, dict) or not {"format", "evidence_paragraphs"}.issubset(locator) or locator["format"] != "HTML":
        return ["SEMANTIC_LOCATOR_SCHEMA_UNSUPPORTED"]
    allowed_metadata = {"parser": "html.parser", "source_view": "ORIGINAL_UNMODIFIED_RAW_BODY",
                        "index_base": 0, "ordinal_base": 0,
                        "paragraph_text_hash_method": "BeautifulSoup p.get_text(' ',strip=True).encode('utf-8')"}
    if any(key not in allowed_metadata or value != allowed_metadata[key]
           for key, value in locator.items() if key not in {"format", "evidence_paragraphs"}):
        return ["SEMANTIC_LOCATOR_METADATA_UNSUPPORTED"]
    if not locator["evidence_paragraphs"]:
        return ["SEMANTIC_LOCATOR_EMPTY"]
    paragraphs = paragraph_index(body["raw_path"], body["sha256"])
    for place in locator["evidence_paragraphs"]:
        needed = {"global_p_ltx_p_ordinal", "section_id", "paragraph_text_sha256"}
        if not needed.issubset(place) or set(place) - needed - {"global_p_ltx_p_index_zero_based", "index_base"}:
            return ["SEMANTIC_PARAGRAPH_SCHEMA_UNSUPPORTED"]
        ordinal = place["global_p_ltx_p_ordinal"]
        if place.get("index_base", 0) != 0 or place.get("global_p_ltx_p_index_zero_based", ordinal) != ordinal:
            return ["SEMANTIC_PARAGRAPH_INDEX_CONVENTION_MISMATCH"]
        if type(ordinal) is not int or ordinal not in paragraphs:
            return ["SEMANTIC_PARAGRAPH_NOT_FOUND"]
        primary = paragraphs[ordinal]
        if primary["protected_container"]:
            return ["SEMANTIC_SOURCE_CONTAINER_REQUIRES_REVIEW"]
        if primary["section_id"] != place["section_id"] or place["paragraph_text_sha256"] not in primary["hashes"]:
            return ["SEMANTIC_PARAGRAPH_HASH_OR_SECTION_MISMATCH"]
    return leakage_codes(fact)


def validate_pdf_locator(locator: dict, body: dict) -> list[str]:
    """Reproduce the exact pages rendered and visually checked by the separate actor."""
    if (not isinstance(locator, dict) or set(locator) != {"format", "evidence_pages", "method_section_locator"}
            or locator["format"] != "PDF" or not locator["evidence_pages"]):
        return ["SEMANTIC_PDF_LOCATOR_SCHEMA_UNSUPPORTED"]
    if e.OUTCOME.search(re.sub(r"\d", "", locator["method_section_locator"])):
        return ["SEMANTIC_PDF_SECTION_REQUIRES_REVIEW"]
    raw = Path(body["raw_path"]).read_bytes()
    if e.sha(raw) != body["sha256"]:
        return ["SEMANTIC_PRIMARY_BODY_HASH_MISMATCH"]
    with fitz.open(stream=raw, filetype="pdf") as pdf:
        for place in locator["evidence_pages"]:
            if set(place) != {"page_number_1based", "rendered_page_sha256", "rendered_page_path", "page_text_sha256"}:
                return ["SEMANTIC_PDF_PAGE_SCHEMA_UNSUPPORTED"]
            number = place["page_number_1based"]
            if type(number) is not int or not 1 <= number <= len(pdf):
                return ["SEMANTIC_PDF_PAGE_NOT_FOUND"]
            page = pdf[number - 1]
            if e.sha(page.get_text().encode()) != place["page_text_sha256"]:
                return ["SEMANTIC_PDF_PAGE_TEXT_MISMATCH"]
            png = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes("png")
            render = Path(place["rendered_page_path"])
            if not render.resolve().is_relative_to(Path(e.read(e.CONFIG)["cache_root"]).resolve()):
                return ["SEMANTIC_PDF_RENDER_OUTSIDE_CACHE"]
            if e.sha(png) != place["rendered_page_sha256"] or e.sha(render.read_bytes()) != e.sha(png):
                return ["SEMANTIC_PDF_RENDER_MISMATCH"]
    return []


def transfer_locator(locator: dict) -> dict:
    """Keep source locators while withholding custodian-only render paths."""
    if locator["format"] == "HTML":
        return {"format": "HTML", "evidence_paragraphs": [
            {key: place[key] for key in ("global_p_ltx_p_ordinal", "section_id", "paragraph_text_sha256")}
            for place in locator["evidence_paragraphs"]]}
    return {"format": "PDF", "method_section_locator": locator["method_section_locator"],
            "evidence_pages": [{key: value for key, value in page.items() if key != "rendered_page_path"}
                               for page in locator["evidence_pages"]]}


def verifier_bytes() -> bytes:
    """Bind the same conservative guards into the standalone, dependency-free verifier."""
    return (e.BASE / "a04-semantic-source/verify_semantic.py").read_bytes().replace(
        b"'__OUTCOME_PATTERN__'", repr(e.OUTCOME.pattern).encode()).replace(
        b"'__SAFE_LIMITATION__'", repr(SAFE_LIMITATION).encode()).replace(
        b"'__SPELLED_COUNT_PATTERN__'", repr(SPELLED_COUNTS.pattern).encode())


def collect(config: dict) -> tuple[dict, dict]:
    """Project all 372 assigned returns; rejected evidence never excludes a paper."""
    frozen = e.read(e.BASE / config["run_id"] / "EVIDENCE_REQUESTS.json")
    source_requests = {r["member_id"]: r for r in frozen["source_requests"]}
    cache = Path(config["cache_root"])
    facts, receipts, coverage, quarantine, record_inputs = [], [], [], [], []
    used_ids = set()
    word_totals = {}
    for work in frozen["works"]:
        checker = owner(work["review_id"])
        row, path = latest_record(cache / f"semantic-check-{checker}", work["review_id"])
        if (row["actor_id"] != ACTORS[checker] or row["work_id"] != work["work_id"]
                or set(row["member_ids"]) != set(work["member_ids"]) or row["eligibility_decision"] is not None
                or row["input_requests_sha256"] != e.sha(e.encoded(frozen))):
            raise ValueError("CHECKER_WORK_OR_INPUT_MISMATCH")
        if (len(row["checked_member_ids"]) != len(set(row["checked_member_ids"]))
                or not set(row["checked_member_ids"]).issubset(set(work["member_ids"]))):
            raise ValueError("CHECKER_MEMBER_MISMATCH")
        digest = e.sha(path.read_bytes())
        released = []
        for fact in row["restricted_method_facts"]:
            mid = fact.get("member_id")
            if mid not in work["member_ids"]:
                raise ValueError("FACT_SOURCE_OUTSIDE_WORK")
            acquisition = e.read(cache / "acquisition" / f"{mid}.json")
            codes = validate_fact(fact, row, source_requests[mid], acquisition["body"])
            if mid not in row["checked_member_ids"]:
                codes.append("FACT_SOURCE_CONTEXT_NOT_ATTESTED")
            words = len(fact.get("method_fact", "").split())
            if word_totals.get(work["work_id"], 0) + words > 180:
                codes.append("METHOD_PARAPHRASE_DISPLAY_BOUND")
            if codes:
                quarantine.append({"work_id": work["work_id"], "review_id": work["review_id"],
                                   "checker": checker, "fact_id": fact.get("fact_id"),
                                   "source_checker_record_sha256": digest, "codes": codes})
                continue
            eid = f"SEM-{checker}-{fact['fact_id']}"
            if eid in used_ids:
                raise ValueError("DUPLICATE_SEMANTIC_EVIDENCE_ID")
            used_ids.add(eid)
            word_totals[work["work_id"]] = word_totals.get(work["work_id"], 0) + words
            projected = {"evidence_id": eid, "work_id": work["work_id"], "review_id": work["review_id"],
                         **{k: fact[k] for k in ("member_id", "fact_kind", "method_fact", "source_url", "version",
                                                "raw_source_sha256", "locator", "restriction_checked_by", "checked_utc", "limitation")},
                         "source_checker_record_sha256": digest, "eligibility_decision": None}
            projected["locator"] = transfer_locator(fact["locator"])
            facts.append(projected)
            body = acquisition["body"]
            receipts.append({"evidence_id": eid, "work_ids": [work["work_id"]],
                             "requested_method_or_bibliographic_fact": fact["fact_kind"],
                             "provider_id": config["provider_id"], "source_url": fact["source_url"],
                             "version": fact["version"], "method_dataset_or_bibliographic_locator": projected["locator"],
                             "retrieved_utc": body["finished_utc"], "http_or_access_status": body["status"],
                             "raw_source_sha256": fact["raw_source_sha256"],
                             "restricted_evidence_sha256": e.sha(e.encoded(projected)),
                             "restriction_checked_by": fact["restriction_checked_by"],
                             "restriction_checked_utc": fact["checked_utc"],
                             "mechanical_release_checked_by": config["provider_id"],
                             "qualitative_and_quantitative_findings_absent": True,
                             "reviewer_received_utc": None, "limitations": fact["limitation"]})
            released.append(eid)
        coverage.append({"work_id": work["work_id"], "review_id": work["review_id"],
                         "member_ids": work["member_ids"], "source_restriction_checker": row["actor_id"],
                         "context_checked_member_ids": row["checked_member_ids"],
                         "restricted_method_evidence_ids": released,
                         "additional_restriction_correction_needed": any(q["work_id"] == work["work_id"] for q in quarantine),
                         "remaining_eligibility_facts_require_review": True,
                         "final_preferred_version_independently_verified": False,
                         "delivered_to_reviewer": False, "independent_eligibility_review_completed": False,
                         "eligibility_decision": None})
        record_inputs.append({"review_id": work["review_id"], "path": str(path), "sha256": digest,
                              "record_revision": row["record_revision"], "actor": row["actor_id"]})
    if len(coverage) != 372 or len({m for r in coverage for m in r["member_ids"]}) != 389:
        raise ValueError("SEMANTIC_TRANSFER_FRAME_CHANGED")
    return {"SEMANTIC_METHOD_FACTS.json": facts, "SEMANTIC_EVIDENCE_RECEIPTS.json": receipts,
            "SEMANTIC_COVERAGE.json": coverage, "RESTRICTION_EXCEPTIONS.json": quarantine}, {
                "checker_record_inputs": record_inputs, "quarantined_facts": quarantine,
                "works_with_method_facts": sum(bool(r["restricted_method_evidence_ids"]) for r in coverage),
                "released_method_facts": len(facts), "works": 372, "members": 389,
                "context_checked_works": sum(bool(r["context_checked_member_ids"]) for r in coverage),
                "context_checked_memberships": sum(len(r["context_checked_member_ids"]) for r in coverage),
                "quarantined_fact_count": len(quarantine), "delivered_to_reviewer": 0,
                "independent_eligibility_judgments": 0,
            }


def main() -> None:
    """Audit completed role returns or freeze a consolidated, verified transfer."""
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["audit", "freeze"])
    args = parser.parse_args()
    head = e.clean_head()
    config = e.read(e.CONFIG)
    e.baseline(config)
    payloads, audit = collect(config)
    if args.phase == "audit":
        print(json.dumps({k: value for k, value in audit.items() if k not in {"checker_record_inputs", "quarantined_facts"}}, sort_keys=True))
        return
    freeze(payloads, audit, config, head)


def freeze(payloads: dict, audit: dict, config: dict, head: str) -> None:
    """Release only validated facts, with the unchanged base archive nested separately."""
    root = e.BASE / RUN
    completion = e.read(root / "CHECKER_COMPLETION_RECEIPT.json")
    if (set(completion["actors"]) != set(ACTORS.values())
            or not completion["actual_agent_completion_reports_received"]
            or completion["independent_eligibility_review_completed"]):
        raise ValueError("ACTUAL_SOURCE_CHECKER_COMPLETION_NOT_RECORDED")
    for item in completion["manifest_inputs"]:
        if e.sha(Path(item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError("CHECKER_COMPLETION_MANIFEST_CHANGED")
    for item in audit["checker_record_inputs"]:
        if e.sha(Path(item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError("CHECKER_SNAPSHOT_CHANGED_DURING_RELEASE")
    roles = [{"actor_id": actor, "role": "SOURCE_RESTRICTION_CHECKER_NOT_ELIGIBILITY_REVIEWER",
              "separate_task_context_fork_turns": "none", "shared_filesystem": True,
              "os_isolation_claimed": False, "eligibility_review_claimed": False,
              "actual_completion_report_received": True} for actor in ACTORS.values()]
    payloads["CHECKER_ROLE_RECEIPTS.json"] = roles
    base = e.BASE / config["run_id"] / "RESTRICTED_EVIDENCE_SUPPLEMENT.zip"
    if e.sha(base.read_bytes()) != "066c27ae28ad941ea9ebf963f3fc5d854b2bcd39d1fb060a16b52b5cc4294c08":
        raise ValueError("FROZEN_BASE_SUPPLEMENT_CHANGED")
    files = {name: e.encoded(value) for name, value in payloads.items()}
    files["BASE_EVIDENCE_SUPPLEMENT.zip"] = base.read_bytes()
    for name in ("README.md", "verify_semantic.py"):
        files[name] = (e.BASE / "a04-semantic-source" / name).read_bytes()
    files["verify_semantic.py"] = verifier_bytes()
    coverage = {k: v for k, v in audit.items() if k not in {"checker_record_inputs", "quarantined_facts"}}
    manifest = {"created_utc": e.now(), "source_git_commit": head, "source_tree_clean_at_start": True,
                "files": {name: e.sha(raw) for name, raw in files.items()},
                "original_intake_sha256": config["intake_archive_sha256"],
                "base_supplement_sha256": e.sha(base.read_bytes()), "coverage": coverage,
                "gate": "FRAME_BLOCKED", "draw_executed": False, "B2": "NOT_AUTHORIZED",
                "actual_independent_eligibility_review": "NOT_RECEIVED", "actual_delivery": "NOT_PERFORMED"}
    files["MANIFEST.json"] = e.encoded(manifest)
    output = root / "restricted"
    archive = root / "CONSOLIDATED_RESTRICTED_EVIDENCE.zip"
    if output.exists() or archive.exists():
        raise FileExistsError("Do not overwrite a frozen semantic transfer")
    output.mkdir()
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    with zipfile.ZipFile(archive, "x") as zipped:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(info, raw)
    with zipfile.ZipFile(archive) as zipped:
        if len(zipped.namelist()) != len(files) or set(zipped.namelist()) != set(files):
            raise ValueError("SEMANTIC_ARCHIVE_ALLOWLIST_MISMATCH")
        if any(zipped.read(name) != raw for name, raw in files.items()):
            raise ValueError("SEMANTIC_ARCHIVE_BYTES_CHANGED")
    if archive.stat().st_size >= 10_000_000:
        raise ValueError("STAGING_SIZE_LIMIT")
    audit.update({"source_git_commit": head, "created_utc": manifest["created_utc"],
                  "package_sha256": e.sha(archive.read_bytes()), "package_bytes": archive.stat().st_size,
                  "package_manifest_sha256": e.sha(files["MANIFEST.json"]),
                  "completion_receipt_sha256": e.sha(e.encoded(completion)),
                  "historical_lock_sha256": e.baseline(config)["historical_locks"],
                  "source_code_sha256": {p.name: e.sha(p.read_bytes()) for p in (Path(__file__), Path(e.__file__))},
                  "gate": "FRAME_BLOCKED", "actual_delivery": "NOT_PERFORMED"})
    e.write_new(root / "CUSTODIAN_RELEASE_AUDIT.json", audit)
    print(json.dumps({"coverage": coverage, "package_sha256": audit["package_sha256"],
                      "package_bytes": audit["package_bytes"], "gate": "FRAME_BLOCKED"}, sort_keys=True))


if __name__ == "__main__":
    main()
