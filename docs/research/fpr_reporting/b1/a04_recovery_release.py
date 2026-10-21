"""Release recovery evidence only after source-role provenance validation.

No eligibility classification or preferred-version choice is implemented here.
Missing/uncertain evidence stays explicit and cannot exclude a candidate.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import fitz

import a04_evidence as e
import a04_recovery_intake as r
import a04_recovery_sources as sources
import a04_semantic_release as s

METHOD_CRITERIA = {"input_injection_task", "binary_evaluation", "before_target_answer", "english_evaluation"}
EXTRA_FACT_FIELDS = {"addresses_criteria", "experiment_scope", "source_binding_basis"}
PROOF_FIELDS = {"source_binding_receipt_sha256", "source_binding_limitation_codes", "acquisition_receipt_sha256", "source_binding_receipt"}


def utc(value: str) -> bool:
    """Require a real UTC timestamp, without substituting local file dates."""
    try:
        return datetime.fromisoformat(value).utcoffset() == timedelta(0)
    except (TypeError, ValueError):
        return False


def supports(row: dict) -> dict:
    """Normalize explicit criterion maps/lists without inferring satisfaction."""
    values = row["criterion_support"]
    if isinstance(values, list):
        if len(values) != len({x["criterion"] for x in values}):
            raise ValueError("DUPLICATE_CRITERION_SUPPORT")
        values = {x["criterion"]: {k: v for k, v in x.items() if k != "criterion"} for x in values}
    if not isinstance(values, dict) or set(values) != METHOD_CRITERIA:
        raise ValueError("INCOMPLETE_CRITERION_SUPPORT")
    expected = {"reused_evidence_ids", "new_fact_ids", "further_controlled_evidence_needed", "limitation_codes"}
    for value in values.values():
        if (set(value) != expected or type(value["further_controlled_evidence_needed"]) is not bool
                or not all(isinstance(value[k], list) for k in expected - {"further_controlled_evidence_needed"})):
            raise ValueError("UNEXPECTED_CRITERION_SUPPORT_FIELDS")
        codes(value["limitation_codes"])
    return values


def codes(values: list) -> None:
    """Allow neutral machine codes, never arbitrary narrative findings."""
    if not isinstance(values, list) or any(not isinstance(x, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", x) for x in values):
        raise ValueError("UNSAFE_LIMITATION_CODE")


def pdf_locator(locator: dict, body: dict) -> list[str]:
    """Reproduce actual rendered method pages in approved ignored caches."""
    if (not isinstance(locator, dict) or set(locator) != {"format", "evidence_pages", "method_section_locator"}
            or locator["format"] != "PDF" or not locator["evidence_pages"]):
        return ["PDF_LOCATOR_SCHEMA_UNSUPPORTED"]
    if e.OUTCOME.search(re.sub(r"\d", "", locator["method_section_locator"])):
        return ["PDF_SECTION_REQUIRES_RESTRICTION_CHECK"]
    raw = Path(body["raw_path"]).read_bytes()
    if e.sha(raw) != body["sha256"]:
        return ["PRIMARY_BODY_HASH_CHANGED"]
    roots = [r.CACHE.resolve(), Path(e.read(e.CONFIG)["cache_root"]).resolve()]
    with fitz.open(stream=raw, filetype="pdf") as pdf:
        for place in locator["evidence_pages"]:
            if set(place) != {"page_number_1based", "rendered_page_sha256", "rendered_page_path", "page_text_sha256"}:
                return ["PDF_PAGE_SCHEMA_UNSUPPORTED"]
            n = place["page_number_1based"]
            if type(n) is not int or not 1 <= n <= len(pdf):
                return ["PDF_PAGE_NOT_FOUND"]
            page = pdf[n - 1]
            if e.sha(page.get_text().encode()) != place["page_text_sha256"]:
                return ["PDF_PAGE_TEXT_HASH_CHANGED"]
            image = Path(place["rendered_page_path"]).resolve()
            if not any(image.is_relative_to(root) for root in roots):
                return ["PDF_RENDER_OUTSIDE_APPROVED_CACHE"]
            png = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes("png")
            if e.sha(png) != place["rendered_page_sha256"] or image.read_bytes() != png:
                return ["PDF_RENDER_HASH_CHANGED"]
    return []


def html_locator(locator: dict, body: dict) -> list[str]:
    """Reconstruct original global paragraph ordinals and section ancestry."""
    if not isinstance(locator, dict) or locator.get("format") != "HTML" or not locator.get("evidence_paragraphs"):
        return ["HTML_LOCATOR_SCHEMA_UNSUPPORTED"]
    metadata = {"parser": "html.parser", "source_view": "ORIGINAL_UNMODIFIED_RAW_BODY", "index_base": 0,
                "ordinal_base": 0, "paragraph_text_hash_method": "BeautifulSoup p.get_text(' ',strip=True).encode('utf-8')"}
    if any(k not in metadata or v != metadata[k] for k, v in locator.items() if k not in {"format", "evidence_paragraphs"}):
        return ["HTML_LOCATOR_METADATA_UNSUPPORTED"]
    paragraphs = s.paragraph_index(body["raw_path"], body["sha256"])
    for place in locator["evidence_paragraphs"]:
        needed = {"global_p_ltx_p_ordinal", "section_id", "paragraph_text_sha256"}
        if not needed.issubset(place) or set(place) - needed - {"global_p_ltx_p_index_zero_based", "index_base"}:
            return ["HTML_PARAGRAPH_SCHEMA_UNSUPPORTED"]
        n = place["global_p_ltx_p_ordinal"]
        if (type(n) is not int or n not in paragraphs or place.get("index_base", 0) != 0
                or place.get("global_p_ltx_p_index_zero_based", n) != n):
            return ["HTML_PARAGRAPH_ORDINAL_INVALID"]
        p = paragraphs[n]
        if p["protected_container"]:
            return ["HTML_PROTECTED_SOURCE_CONTAINER"]
        if place["section_id"] != p["section_id"] or place["paragraph_text_sha256"] not in p["hashes"]:
            return ["HTML_PARAGRAPH_HASH_OR_SECTION_CHANGED"]
    return []


def validate_fact(fact: dict, record: dict, binding: dict) -> list[str]:
    """Use new source proof directly; never override an old acquisition state."""
    optional = {"source_context_original_checked_utc", "locator_checked_utc", "literal_quotation_words"}
    if not (s.FACT_FIELDS | EXTRA_FACT_FIELDS).issubset(fact) or set(fact) - s.FACT_FIELDS - EXTRA_FACT_FIELDS - optional - PROOF_FIELDS:
        return ["UNEXPECTED_RECOVERY_FACT_FIELDS"]
    if (not binding["method_release_supported"] or not binding.get("body")
            or fact["member_id"] != binding["member_id"] or fact["member_id"] not in record["context_checked_member_ids"]):
        return ["SOURCE_METHOD_CONTEXT_OR_IDENTITY_UNSUPPORTED"]
    body = binding["body"]
    version = binding["captured_version_id"]
    if version is None:
        version = "acl:" + body["url"].rsplit("/", 1)[-1].removesuffix(".pdf") + ":publication"
    if (fact["source_url"] != body["url"] or fact["raw_source_sha256"] != body["sha256"]
            or fact["version"].removeprefix("arxiv:") != version.removeprefix("arxiv:")
            or fact["fact_kind"] not in s.KINDS or fact["restriction_checked_by"] != record["actor_id"]):
        return ["RECOVERY_FACT_SOURCE_OR_ACTOR_MISMATCH"]
    criteria = fact["addresses_criteria"]
    if not isinstance(criteria, list) or not criteria or len(set(criteria)) != len(criteria) or not set(criteria).issubset(METHOD_CRITERIA):
        return ["RECOVERY_FACT_CRITERION_LINK_INVALID"]
    if (not isinstance(fact["experiment_scope"], str) or not fact["experiment_scope"]
            or e.OUTCOME.search(fact["experiment_scope"]) or s.SPELLED_COUNTS.search(fact["experiment_scope"])):
        return ["EXPERIMENT_SCOPE_REQUIRES_RESTRICTION_CHECK"]
    if not fact["source_binding_basis"]:
        return ["SOURCE_BINDING_BASIS_MISSING"]
    proof_errors = validate_optional_proofs(fact, binding)
    if proof_errors:
        return proof_errors
    check = fact["second_local_semantic_pass"]
    if (not isinstance(check, dict) or check.get("actor_id", check.get("checked_by")) != record["actor_id"]
            or check.get("literal_quotation_words", 0) != 0 or fact.get("literal_quotation_words", 0) != 0
            or not (check.get("status") or check.get("performed") is True)
            or not utc(fact["checked_utc"]) or not utc(check.get("checked_utc"))):
        return ["RECOVERY_SECOND_PASS_UNATTESTED"]
    geometry = pdf_locator(fact["locator"], body) if body["kind"] == "PDF" else html_locator(fact["locator"], body)
    return geometry + s.leakage_codes(fact)


def validate_optional_proofs(fact: dict, binding: dict) -> list[str]:
    """Accept only explicitly hash-checked optional receipt metadata."""
    if not PROOF_FIELDS.intersection(fact):
        return []
    path = e.BASE / r.RUN / "SOURCE_BINDINGS.json"
    original = next(x for x in e.read(path) if x["member_id"] == binding["member_id"])
    if ("source_binding_receipt_sha256" in fact and fact["source_binding_receipt_sha256"] != e.sha(path.read_bytes())
            or "acquisition_receipt_sha256" in fact and fact["acquisition_receipt_sha256"] != original["original_acquisition_receipt_sha256"]
            or "source_binding_limitation_codes" in fact and fact["source_binding_limitation_codes"] != original["limitation_codes"]):
        return ["OPTIONAL_SOURCE_PROOF_COMMITMENT_CHANGED"]
    if "source_binding_receipt" in fact:
        proof = fact["source_binding_receipt"]
        fields = {"path", "sha256", "member_id", "body_exact_revision_self_identified", "protocol_preferred_version", "limitation_codes"}
        if (not isinstance(proof, dict) or set(proof) != fields or Path(proof["path"]).resolve() != path.resolve()
                or proof["sha256"] != e.sha(path.read_bytes()) or proof["member_id"] != original["member_id"]
                or any(proof[k] != original[k] for k in fields - {"path", "sha256", "member_id"})):
            return ["OPTIONAL_SOURCE_PROOF_COMMITMENT_CHANGED"]
    return []


def public_binding(row: dict) -> dict:
    """Withhold local raw-cache paths while preserving source proof limitations."""
    out = {k: v for k, v in row.items() if k != "body"}
    if row.get("body"):
        out["body"] = {k: v for k, v in row["body"].items() if k != "raw_path"}
    out["evidence_id"] = "R01-SOURCE-" + row["member_id"]
    return out


def public_bibliography(row: dict) -> dict:
    """Allowlist transport metadata, keeping raw sources custodian-side."""
    out = dict(row)
    out["provenance"] = {k: v for k, v in row["provenance"].items() if k != "attempts"}
    out["provenance"]["attempts"] = [{k: v for k, v in item.items() if k != "raw_path"} for item in row["provenance"]["attempts"]]
    return out


def effective_bindings() -> tuple[dict, list]:
    """Append a checked visual identity receipt without rewriting original proofs."""
    bindings_path = e.BASE / r.RUN / "SOURCE_BINDINGS.json"
    bindings = {x["member_id"]: x for x in e.read(bindings_path)}
    path = r.CACHE / "checker-02/W0221.IDENTITY_CHECK.0001.json"
    notes = []
    if path.exists():
        note = e.read(path)
        row = bindings["M0272"]
        if (note["actor_id"] != s.ACTORS["02"] or note["review_id"] != row["review_id"]
                or note["member_id"] != row["member_id"] or note["raw_source_sha256"] != row["body"]["sha256"]
                or note["source_binding_sha256"] != e.sha(bindings_path.read_bytes())
                or note["captured_version_id"] != row["captured_version_id"]
                or note["recorded_official_exact_version_url"] != row["body"]["url"]
                or not note["visual_check_performed"] or not note["title_identity_match"]
                or not note["authors_visually_match_controlled_metadata"]
                or note["frozen_title_identity_sha256"] != row["captured_title_identity_sha256"]
                or sources.identity_text(note["observed_first_page_title"]) == ""
                or e.sha(sources.identity_text(note["observed_first_page_title"]).encode()) != row["captured_title_identity_sha256"]
                or note["observed_title_identity_sha256"] != row["captured_title_identity_sha256"]
                or note["eligibility_decision"] is not None or note["protocol_preferred_version"] is not None
                or note["body_exact_revision_self_identified"] is not False or not utc(note["checked_utc"])):
            raise ValueError("VISUAL_IDENTITY_RECEIPT_COMMITMENT_CHANGED")
        if "CAPTURED_SOURCE_DATE_CUTOFF_UNRESOLVED" in row["limitation_codes"]:
            raise ValueError("VISUAL_IDENTITY_CANNOT_REPAIR_UNKNOWN_DATE")
        locator = {"format": "PDF", "method_section_locator": "First page bibliography",
                   "evidence_pages": [{k: note[k] for k in ("page_number_1based", "rendered_page_sha256", "rendered_page_path", "page_text_sha256")}]}
        if pdf_locator(locator, row["body"]):
            raise ValueError("VISUAL_IDENTITY_PAGE_PROOF_FAILED")
        proof = {k: note[k] for k in ("actor_id", "member_id", "review_id", "checked_utc", "raw_source_sha256",
                 "captured_version_id", "frozen_title_identity_sha256", "observed_title_identity_sha256",
                 "body_exact_revision_self_identified", "title_identity_match", "authors_visually_match_controlled_metadata",
                 "source_binding_basis", "source_binding_sha256")}
        proof.update({"evidence_id": "R01-IDENTITY-M0272", "source_checker_record_sha256": e.sha(path.read_bytes()),
                      "locator": s.transfer_locator(locator), "eligibility_decision": None,
                      "limitation_codes": ["PDF_FONT_MAPPING_CORRUPTS_EXTRACTED_TITLE", "IN_BODY_REVISION_IDENTIFIER_NOT_FOUND",
                                           "PROTOCOL_PREFERRED_VERSION_NOT_ADJUDICATED"]})
        notes.append(proof)
        row.update({"source_binding_basis": note["source_binding_basis"], "method_release_supported": True,
                    "visual_identity_evidence_id": proof["evidence_id"], "body_title_matches_frozen_work": True,
                    "previous_source_binding_basis": row["source_binding_basis"],
                    "limitation_codes": [x for x in row["limitation_codes"] if x != "WORK_TITLE_IDENTITY_NOT_ESTABLISHED"]
                        + proof["limitation_codes"]})
    return bindings, notes


def collect(allow_partial: bool = False) -> tuple[dict, dict]:
    """Validate actual immutable role returns; never turn gaps into exclusions."""
    inventory, old, _, _ = r.frozen_inputs()
    _ = inventory
    gap_path = e.BASE / r.RUN / "SOURCE_GAP_REQUESTS.json"
    gap_raw = gap_path.read_bytes()
    gaps = json.loads(gap_raw)
    bindings, identity_notes = effective_bindings()
    bibliographic_path = e.BASE / r.RUN / "OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json"
    bibliography = e.read(bibliographic_path) if bibliographic_path.exists() else []
    bib = {x["member_id"]: x for x in bibliography}
    facts, receipts, responses, quarantine, snapshots, missing = [], [], [], [], [], []
    used = set()
    for req in gaps:
        rid = req["review_id"]
        owner = s.owner(rid)
        directory = r.CACHE / ("checker-" + owner)
        try:
            row, path = s.latest_record(directory, rid)
        except (FileNotFoundError, ValueError) as exc:
            if not allow_partial or isinstance(exc, ValueError) and str(exc) != "CHECKER_RETURN_MISSING":
                raise
            missing.append(rid)
            continue
        if (row["actor_id"] != s.ACTORS[owner] or row["work_id"] != req["work_id"]
                or row["request_id"] != req["request_id"] or set(row["member_ids"]) != set(req["member_ids"])
                or row["eligibility_decision"] is not None or row["input_request_sha256"] != e.sha(gap_raw)
                or not utc(row["checked_utc"])):
            raise ValueError("RECOVERY_WORK_ROLE_OR_INPUT_CHANGED:" + rid)
        checked = row["context_checked_member_ids"]
        if len(set(checked)) != len(checked) or not set(checked).issubset(req["member_ids"]):
            raise ValueError("RECOVERY_CONTEXT_MEMBERSHIP_CHANGED:" + rid)
        support = supports(row)
        codes(row["remaining_fact_codes"])
        reused = row["reused_evidence_ids"]
        if (len(set(reused)) != len(reused) or any(x not in old or old[x]["work_id"] != req["work_id"] for x in reused)):
            raise ValueError("RECOVERY_REUSED_EVIDENCE_FOREIGN_KEY:" + rid)
        snapshot = {"review_id": rid, "actor_id": row["actor_id"], "record_revision": row["record_revision"],
                    "path": str(path), "sha256": e.sha(path.read_bytes())}
        snapshots.append(snapshot)
        released = {}
        words = 0
        for fact in row["new_method_facts"]:
            if fact.get("member_id") not in req["member_ids"]:
                raise ValueError("RECOVERY_FACT_OUTSIDE_WORK:" + rid)
            errors = validate_fact(fact, row, bindings[fact["member_id"]])
            words += len(fact["method_fact"].split())
            if words > 180:
                errors.append("METHOD_PARAPHRASE_DISPLAY_BOUND")
            if errors:
                quarantine.append({"review_id": rid, "fact_id": fact["fact_id"], "codes": errors, "source_checker_record_sha256": snapshot["sha256"]})
                continue
            eid = "REC-" + fact["fact_id"]
            if eid in used:
                raise ValueError("DUPLICATE_RECOVERY_FACT_ID")
            used.add(eid)
            released[fact["fact_id"]] = eid
            projected = {"evidence_id": eid, "review_id": rid, "work_id": req["work_id"],
                         **{k: fact[k] for k in ("member_id", "fact_kind", "method_fact", "source_url", "version",
                             "raw_source_sha256", "restriction_checked_by", "checked_utc", "limitation", "addresses_criteria", "experiment_scope")},
                         "locator": s.transfer_locator(fact["locator"]),
                         "source_binding_evidence_id": "R01-SOURCE-" + fact["member_id"],
                         "source_binding_basis": bindings[fact["member_id"]]["source_binding_basis"],
                         "source_checker_record_sha256": snapshot["sha256"], "eligibility_decision": None}
            facts.append(projected)
            receipts.append({"evidence_id": eid, "work_ids": [req["work_id"]], "source_url": projected["source_url"],
                             "version": projected["version"], "raw_source_sha256": projected["raw_source_sha256"],
                             "method_dataset_or_bibliographic_locator": projected["locator"],
                             "restricted_evidence_sha256": e.sha(e.encoded(projected)),
                             "retrieved_utc": bindings[fact["member_id"]]["body"]["finished_utc"],
                             "restriction_checked_by": row["actor_id"], "restriction_checked_utc": fact["checked_utc"],
                             "second_local_semantic_pass": fact["second_local_semantic_pass"],
                             "reviewer_received_utc": None})
        criterion_rows = []
        for criterion, value in sorted(support.items()):
            if (any(x not in reused for x in value["reused_evidence_ids"])
                    or any(x not in {f["fact_id"] for f in row["new_method_facts"]} for x in value["new_fact_ids"])):
                raise ValueError("RECOVERY_CRITERION_REFERENCE_OUTSIDE_WORK:" + rid)
            dropped = [x for x in value["new_fact_ids"] if x not in released]
            criterion_rows.append({"criterion": criterion, "reused_evidence_ids": value["reused_evidence_ids"],
                                   "new_evidence_ids": [released[x] for x in value["new_fact_ids"] if x in released],
                                   "further_controlled_evidence_needed": bool(value["further_controlled_evidence_needed"] or dropped),
                                   "limitation_codes": value["limitation_codes"] + (["FACT_RESTRICTION_CORRECTION_PENDING"] if dropped else []),
                                   "criterion_satisfaction_decision": None})
        bibliography_ids = [bib[m]["evidence_id"] for m in req["member_ids"] if m in bib]
        for criterion in [x["criterion"] for x in req["controlled_requests"] if x["criterion"] in {"version", "identity"}]:
            criterion_rows.append({"criterion": criterion, "bibliographic_evidence_ids": bibliography_ids,
                                   "source_binding_evidence_ids": ["R01-SOURCE-" + m for m in req["member_ids"]],
                                   "frozen_bibliographic_evidence_ids": ["BIB-" + m for m in req["member_ids"]],
                                   "further_controlled_evidence_needed": None,
                                   "independent_bibliographic_judgment_required": True,
                                   "limitation_codes": ["PROTOCOL_PREFERRED_VERSION_AND_SENTINEL_SCOPE_REQUIRE_INDEPENDENT_REVIEW"]
                                       + (["CROSS_MEMBER_IDENTITY_REQUIRES_INDEPENDENT_REVIEW"] if criterion == "identity" else []),
                                   "criterion_satisfaction_decision": None})
        responses.append({"request_id": req["request_id"], "review_id": rid, "work_id": req["work_id"],
                          "member_ids": req["member_ids"], "source_restriction_checker": row["actor_id"],
                          "context_checked_member_ids": checked, "reused_evidence_ids": reused,
                          "new_evidence_ids": list(released.values()), "criterion_evidence": criterion_rows,
                          "remaining_fact_codes": row["remaining_fact_codes"], "eligibility_decision": None,
                          "source_checker_record_sha256": snapshot["sha256"],
                          "evidence_delivered": False, "independent_review_completed": False})
    audit = {"actual_role_records": len(responses), "requested_works": 367, "requested_memberships": 384,
             "missing_role_records": missing, "released_new_method_facts": len(facts),
             "context_checked_memberships": sum(len(x["context_checked_member_ids"]) for x in responses),
             "quarantine_count": len(quarantine), "quarantined_facts": quarantine,
             "checker_record_inputs": snapshots, "official_bibliographic_memberships": len(bibliography),
             "criteria_responses": sum(len(x["criterion_evidence"]) for x in responses),
             "independent_eligibility_decisions": 0, "actual_delivery_recorded": False, "gate": "FRAME_BLOCKED"}
    payloads = {"RECOVERY_METHOD_FACTS.json": facts, "RECOVERY_EVIDENCE_RECEIPTS.json": receipts,
                "CONTROLLED_REQUEST_RESPONSES.json": responses,
                "RECOVERY_SOURCE_BINDINGS.json": [public_binding(x) for x in bindings.values()],
                "RECOVERY_IDENTITY_EVIDENCE.json": identity_notes,
                "OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json": [public_bibliography(x) for x in bibliography]}
    return payloads, audit


def main() -> None:
    """Audit while roles run; freezing is a separate complete-role milestone."""
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["audit"])
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    _, audit = collect(args.partial)
    print(json.dumps({k: v for k, v in audit.items() if k != "checker_record_inputs"}, sort_keys=True))


if __name__ == "__main__":
    main()
