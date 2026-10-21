"""Release recovery evidence only after source-role provenance validation.

No eligibility classification or preferred-version choice is implemented here.
Missing/uncertain evidence stays explicit and cannot exclude a candidate.
"""
from __future__ import annotations

import argparse
import json
import re
import io
import subprocess
import sys
import zipfile
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


def pdf_locator(locator: dict, body: dict, member_id: str | None = None, actor_id: str | None = None) -> list[str]:
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
            required = {"page_number_1based", "rendered_page_sha256", "rendered_page_path", "page_text_sha256"}
            optional = {"render_tool", "visual_review_receipt_sha256", "visual_checked_utc"}
            if not required.issubset(place) or set(place) - required - optional:
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
            if optional.intersection(place):
                if not optional.issubset(place) or member_id is None or actor_id is None:
                    return ["PDF_VISUAL_RECEIPT_SCHEMA_UNSUPPORTED"]
                receipt_path = r.CACHE / "checker-01/pdf-renders" / f"{member_id}-p{number_for_receipt(n)}.view.0001.json"
                render_path = receipt_path.with_name(f"{member_id}-p{number_for_receipt(n)}.render.json")
                if not receipt_path.exists() or not render_path.exists():
                    return ["PDF_VISUAL_RECEIPT_MISSING"]
                receipt = e.read(receipt_path)
                rendered = e.read(render_path)
                if (e.sha(receipt_path.read_bytes()) != place["visual_review_receipt_sha256"]
                        or receipt["actor_id"] != actor_id or receipt["member_id"] != member_id
                        or receipt["page_number_1based"] != n or receipt["visual_review_completed"] is not True
                        or receipt["checked_utc"] != place["visual_checked_utc"] or not utc(receipt["checked_utc"])
                        or receipt["rendered_page_sha256"] != e.sha(png)
                        or receipt["render_receipt_sha256"] != e.sha(render_path.read_bytes())
                        or rendered["raw_source_sha256"] != body["sha256"] or rendered["member_id"] != member_id
                        or rendered["actor_id"] != actor_id or rendered["page_number_1based"] != n
                        or rendered["page_text_sha256"] != place["page_text_sha256"]
                        or rendered["rendered_page_sha256"] != place["rendered_page_sha256"]
                        or place["render_tool"] != "PyMuPDF fitz Page.get_pixmap with Matrix(2,2), csRGB, alpha=False"):
                    return ["PDF_VISUAL_RECEIPT_COMMITMENT_CHANGED"]
    return []


def number_for_receipt(number: int) -> str:
    """Use the actual documented immutable page-receipt convention."""
    return f"{number:03d}"


def public_locator(locator: dict) -> dict:
    """Withhold working render/view receipt metadata after validating its bytes."""
    if locator["format"] == "HTML":
        return s.transfer_locator(locator)
    return {"format": "PDF", "method_section_locator": locator["method_section_locator"],
            "evidence_pages": [{k: p[k] for k in ("page_number_1based", "page_text_sha256", "rendered_page_sha256")}
                               for p in locator["evidence_pages"]]}


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
    geometry = (pdf_locator(fact["locator"], body, fact["member_id"], record["actor_id"])
                if body["kind"] == "PDF" else html_locator(fact["locator"], body))
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
    path = r.CACHE / "checker-03/M0326.IDENTITY_NOTE.0001.json"
    if path.exists():
        note = e.read(path)
        row = bindings["M0326"]
        if (note["actor_id"] != s.ACTORS["03"] or note["member_id"] != row["member_id"]
                or note["raw_source_sha256"] != row["body"]["sha256"] or note["source_url"] != row["body"]["url"]
                or not note["visual_bibliographic_region_inspected"] or note["method_release_supported"]
                or note["eligibility_decision"] is not None or not utc(note["checked_utc"])
                or e.sha(sources.identity_text(note["controlled_frozen_title"]).encode()) != row["captured_title_identity_sha256"]):
            raise ValueError("UNRESOLVED_IDENTITY_NOTE_COMMITMENT_CHANGED")
        locator = {"format": "PDF", "method_section_locator": "First page bibliography",
                   "evidence_pages": [{k: note[k] for k in ("page_number_1based", "rendered_page_sha256", "rendered_page_path", "page_text_sha256")}]}
        if pdf_locator(locator, row["body"]):
            raise ValueError("UNRESOLVED_IDENTITY_PAGE_PROOF_FAILED")
        notes.append({"evidence_id": "R01-IDENTITY-M0326", "member_id": row["member_id"], "review_id": row["review_id"],
                      "source_url": row["body"]["url"], "raw_source_sha256": row["body"]["sha256"],
                      "actor_id": note["actor_id"], "checked_utc": note["checked_utc"], "locator": s.transfer_locator(locator),
                      "frozen_title_identity_sha256": row["captured_title_identity_sha256"],
                      "observed_title_identity_sha256": e.sha(sources.identity_text(note["primary_pdf_title"]).encode()),
                      "author_names_visually_match": note["all_controlled_author_names_present_in_primary_header"],
                      "source_checker_record_sha256": e.sha(path.read_bytes()), "method_release_supported": False,
                      "eligibility_decision": None, "limitation_codes": ["TITLE_DISCREPANCY_REQUIRES_PRIMARY_IDENTITY_LINK", "NO_ALIAS_MAPPING_ASSERTED"]})
    return bindings, notes


def crosslinks(bibliography: list, registration: list) -> list:
    """Expose identifier links and exact sentinel collisions without new mappings."""
    intake = r.original_archives()["FRESH_REVIEWER_INTAKE.zip"]
    inventory = json.loads(intake["CANDIDATE_INVENTORY.json"])
    sentinels = json.loads(intake["SENTINEL_IDENTIFIERS.json"])
    members = {row["member_id"]: row for row in bibliography}
    results = []
    for work in inventory:
        if not any(m["member_id"] in members for m in work["members"]):
            continue
        linked = [{"identifier": identifier, "evidence_id": members[m["member_id"]]["evidence_id"], "member_id": m["member_id"]}
                  for m in work["members"] for identifier in members[m["member_id"]]["official_fields"]["linked_identifiers"]]
        identifiers = set(work["identifiers"]) | {x["identifier"] for x in linked}
        related = [{"registration_evidence_id": item["evidence_id"], **relation}
                   for item in registration if set(item["member_ids"]) & {m["member_id"] for m in work["members"]}
                   for relation in (item["registered_fields"] or {}).get("related_doi_identifiers", [])]
        results.append({"review_id": work["review_id"], "work_id": work["work_id"],
                        "member_ids": [m["member_id"] for m in work["members"]],
                        "frozen_identifiers": work["identifiers"], "official_linked_identifiers": linked,
                        "registered_relations_not_new_candidates": related,
                        "exact_sentinel_identifier_collisions": [{"sentinel_work_id": x["work_id"], "exclude_versions": x["exclude_versions"]}
                                                                 for x in sentinels if x["work_id"] in identifiers],
                        "alias_mapping_decision": None, "selected_protocol_preferred_version": None,
                        "limitation_codes": ["EXACT_IDENTIFIER_CHECK_ONLY_RENAMED_AND_VERSION_SCOPE_REQUIRE_REVIEW"],
                        "eligibility_decision": None})
    return results


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
    registration_path = e.BASE / r.RUN / "REGISTERED_DOI_EVIDENCE_CUSTODIAN.json"
    registration = e.read(registration_path) if registration_path.exists() else []
    followup_path = e.BASE / r.RUN / "REGISTRATION_FOLLOWUP_CUSTODIAN.json"
    followup = e.read(followup_path) if followup_path.exists() else []
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
                         "locator": public_locator(fact["locator"]),
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
            linked_facts = {f["fact_id"]: f for f in row["new_method_facts"]}
            if any(criterion not in linked_facts[x]["addresses_criteria"] for x in value["new_fact_ids"]):
                raise ValueError("RECOVERY_CRITERION_LINK_NOT_ATTESTED:" + rid)
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
                "OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json": [public_bibliography(x) for x in bibliography],
                "REGISTERED_DOI_EVIDENCE.json": [{**x, "provenance": {k: v for k, v in x["provenance"].items() if k != "raw_path"}} for x in registration],
                "REGISTRATION_FOLLOWUP_EVIDENCE.json": [{k: v for k, v in x.items() if k != "raw_path"} for x in followup],
                "BIBLIOGRAPHIC_CROSSLINKS.json": crosslinks(bibliography, registration),
                "SOURCE_GAP_REQUESTS.json": gaps}
    return payloads, audit


def main() -> None:
    """Audit while roles run; freezing is a separate complete-role milestone."""
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["audit", "freeze"])
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    if args.phase == "freeze":
        if args.partial:
            raise ValueError("PARTIAL_RELEASE_NOT_AUTHORIZED")
        freeze(e.clean_head())
    else:
        _, audit = collect(args.partial)
        print(json.dumps({k: v for k, v in audit.items() if k != "checker_record_inputs"}, sort_keys=True))


def replay_bibliography() -> dict:
    """Reparse exact captured bytes from a clean committed release tool."""
    import a04_recovery_bibliography as registered
    import a04_recovery_registration_followup as followup
    requests, metadata = sources.inputs()
    by_mid = {x["member_id"]: x for x in requests}
    official = e.read(e.BASE / r.RUN / "OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json")
    if len(official) != 384 or {x["member_id"] for x in official} != set(by_mid):
        raise ValueError("BIBLIOGRAPHY_REPLAY_MEMBERSHIP_CHANGED")
    for row in official:
        if row["metadata_record_sha256"] != by_mid[row["member_id"]]["metadata_record_sha256"]:
            raise ValueError("BIBLIOGRAPHY_REPLAY_METADATA_CHANGED")
        successful = [x for x in row["provenance"]["attempts"] if x.get("raw_path")]
        if len(successful) != 1:
            raise ValueError("BIBLIOGRAPHY_REPLAY_EXPECTED_CAPTURE_MISSING")
        raw = Path(successful[0]["raw_path"]).read_bytes()
        if e.sha(raw) != row["provenance"]["raw_source_sha256"]:
            raise ValueError("BIBLIOGRAPHY_REPLAY_RAW_HASH_CHANGED")
        if sources.bibliographic_fields(raw, metadata[row["member_id"]]["source"]) != row["official_fields"]:
            raise ValueError("BIBLIOGRAPHY_REPLAY_FIELDS_CHANGED")
    registration = e.read(e.BASE / r.RUN / "REGISTERED_DOI_EVIDENCE_CUSTODIAN.json")
    for row in registration:
        if row["registered_fields"] is None:
            continue
        raw = Path(row["provenance"]["raw_path"]).read_bytes()
        if (e.sha(raw) != row["provenance"]["raw_source_sha256"]
                or registered.registered_fields(json.loads(raw)["message"], row["doi"]) != row["registered_fields"]):
            raise ValueError("REGISTRATION_REPLAY_CHANGED")
    followups = e.read(e.BASE / r.RUN / "REGISTRATION_FOLLOWUP_CUSTODIAN.json")
    for row in followups:
        if row["official_fields"] is None:
            continue
        raw = Path(row["raw_path"]).read_bytes()
        fields = (followup.datacite_fields(json.loads(raw)["data"]["attributes"], row["doi"])
                  if row["source_kind"] == "DATACITE" else sources.bibliographic_fields(raw, "acl"))
        if e.sha(raw) != row["raw_source_sha256"] or fields != row["official_fields"]:
            raise ValueError("REGISTRATION_FOLLOWUP_REPLAY_CHANGED")
    return {"official_memberships_replayed": len(official), "registration_receipts": len(registration),
            "registration_followups": len(followups), "capture_refreshed": False, "replay": "BYTE_IDENTICAL_FIELDS"}


def zipped(files: dict[str, bytes]) -> bytes:
    """Create a new, separately identified transport, never an original substitute."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, raw)
    return stream.getvalue()


def write_raw_new(path: Path, raw: bytes) -> None:
    """Commit exact binary bytes atomically inside the new recovery directory."""
    if not path.resolve().is_relative_to((e.BASE / r.RUN).resolve()):
        raise ValueError("RAW_TRANSFER_PATH_OUTSIDE_NEW_RECOVERY")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise FileExistsError(path)
        return
    partial = path.with_name(path.name + ".partial")
    if partial.exists():
        if partial.read_bytes() == raw:
            partial.rename(path)
            return
        partial.rename(partial.with_name(partial.name + ".interrupted-" + e.sha(partial.read_bytes())[:16]))
    with partial.open("xb") as stream:
        stream.write(raw)
    partial.rename(path)


def freeze(head: str) -> None:
    """Require actual finished restriction roles, then verify the entire handoff."""
    root = e.BASE / r.RUN
    e.baseline(e.read(e.CONFIG))
    completion = e.read(root / "RECOVERY_CHECKER_COMPLETION.json")
    if (set(completion["actors"]) != set(s.ACTORS.values())
            or completion["actual_agent_completion_reports_received"] is not True
            or completion["independent_eligibility_review_completed"] is not False):
        raise ValueError("ACTUAL_RECOVERY_ROLE_COMPLETION_NOT_RECORDED")
    for item in completion["manifest_inputs"]:
        if e.sha(Path(item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError("ACTUAL_RECOVERY_ROLE_MANIFEST_CHANGED")
    replay = replay_bibliography()
    payloads, audit = collect()
    if len(audit["checker_record_inputs"]) != 367 or audit["criteria_responses"] != 1852:
        raise ValueError("RECOVERY_ROLE_COVERAGE_INCOMPLETE")
    if {x["review_id"]: x["sha256"] for x in audit["checker_record_inputs"]} != completion["latest_record_sha256"]:
        raise ValueError("RECOVERY_COMPLETION_SNAPSHOT_CHANGED")
    for row in payloads["CONTROLLED_REQUEST_RESPONSES.json"]:
        if any("PENDING" in code or "NOT_STARTED" in code for code in row["remaining_fact_codes"]):
            raise ValueError("ROUTINE_SOURCE_TASK_STILL_PENDING:" + row["review_id"])
    payloads["CHECKER_ROLE_RECEIPTS.json"] = [{"actor_id": actor,
        "role": "SOURCE_RESTRICTION_CHECKER_NOT_ELIGIBILITY_REVIEWER", "shared_filesystem": True,
        "os_isolation_claimed": False, "eligibility_review_claimed": False,
        "context_history": "RESUMED_EXISTING_SEPARATE_SOURCE_RESTRICTION_CONTEXT_ORIGINALLY_FORKED_WITH_NONE",
        "actual_completion_report_received": True} for actor in s.ACTORS.values()]
    files = {name: e.encoded(value) for name, value in payloads.items()}
    files["README.md"] = (e.BASE / "A04_RECOVERY_REVIEWER_README.md").read_bytes()
    manifest = {"kind": "NEW_CONTROLLED_RECOVERY_EVIDENCE_NOT_ORIGINAL_ARCHIVE_SUBSTITUTE",
                "source_git_commit": head, "prepared_utc": e.now(), "files": {n: e.sha(raw) for n, raw in files.items()},
                "independent_eligibility_review_completed": False, "actual_delivery_recorded": False,
                "gate": "FRAME_BLOCKED"}
    files["MANIFEST.json"] = e.encoded(manifest)
    inner = zipped(files)
    outer = {name: (e.BASE / path).read_bytes() for name, (path, _, _) in r.ARCHIVES.items()}
    # Authenticate exact originals before nesting them in a new transport.
    r.original_archives()
    outer["RECOVERY_CONTROLLED_EVIDENCE.zip"] = inner
    outer["READ_FIRST_RECOVERY.md"] = files["README.md"]
    outer["verify_recovery.py"] = (e.BASE / "verify_a04_recovery_transfer.py").read_bytes().replace(
        b"'__OUTCOME_PATTERN__'", repr(e.OUTCOME.pattern).encode()).replace(
        b"'__SPELLED_COUNT_PATTERN__'", repr(s.SPELLED_COUNTS.pattern).encode()).replace(
        b"'__SAFE_LIMITATION__'", repr(s.SAFE_LIMITATION).encode())
    outer["MANIFEST.json"] = e.encoded({"kind": "NEW_RECOVERY_TRANSPORT_WITH_UNCHANGED_ORIGINAL_ARCHIVES",
        "files": {n: e.sha(raw) for n, raw in outer.items()}, "prepared_utc": e.now(), "source_git_commit": head,
        "actual_delivery_recorded": False, "independent_eligibility_review_completed": False, "gate": "FRAME_BLOCKED"})
    for name, raw in outer.items():
        write_raw_new(root / "transfer" / name, raw)
    process = subprocess.run([sys.executable, "-I", str((root / "transfer/verify_recovery.py").resolve())],
                             capture_output=True, text=True, timeout=300)
    if process.returncode:
        # Preserve failed check evidence; the transport is not called reviewer-ready.
        e.write_new(r.CACHE / ("failed-transfer-check-" + e.now().replace(":", "-") + ".json"),
                    {"exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr})
        raise ValueError("FULL_TRANSFER_VERIFICATION_FAILED:" + process.stderr[-1500:])
    for item in audit["checker_record_inputs"]:
        if e.sha(Path(item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError("CHECKER_RECORD_CHANGED_DURING_FREEZE")
    raw = zipped(outer)
    write_raw_new(root / "REVIEWER_RECOVERY_TRANSFER.zip", raw)
    for name, value in payloads.items():
        e.write_new(root / "released" / name, value)
    e.write_new(root / "RECOVERY_RELEASE_VALIDATION.json", {"source_git_commit": head,
        "checked_utc": e.now(), "bibliography_replay": replay, "actual_full_transfer_verifier": json.loads(process.stdout),
        "audit": audit, "transfer_sha256": e.sha(raw), "transfer_bytes": len(raw),
        "actual_delivery_recorded": False, "independent_eligibility_review_completed": False, "gate": "FRAME_BLOCKED"})
    print(json.dumps({"transfer_sha256": e.sha(raw), "transfer_bytes": len(raw),
                      "new_method_facts": len(payloads["RECOVERY_METHOD_FACTS.json"]), "gate": "FRAME_BLOCKED"}))


if __name__ == "__main__":
    main()
