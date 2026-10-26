"""Create a flat restricted supplement; never transfer quarantine/source displays."""
from __future__ import annotations

import importlib.metadata
import json
import zipfile
from pathlib import Path

import a04_evidence as e
import a04_method_clauses as clauses


def build(config: dict) -> tuple[dict, dict]:
    """Reconcile all members, recheck released evidence and keep all decisions null."""
    frozen = e.read(e.BASE / config["run_id"] / "EVIDENCE_REQUESTS.json")
    if e.encoded(e.make_requests(config)) != e.encoded(frozen):
        raise ValueError("REQUEST_FRAME_CHANGED")
    cache = Path(config["cache_root"])
    bibliographic, methods, receipts, exceptions, ledger = [], [], [], [], []
    used_words = {}
    custodian = {"source_receipts": [], "processing_receipts": [], "source_bodies": []}
    for request in frozen["source_requests"]:
        mid = request["member_id"]
        acquired_path = cache / "acquisition" / f"{mid}.json"
        processed_path = cache / "processed" / f"{mid}.json"
        acquired, processed = e.read(acquired_path), e.read(processed_path)
        if (acquired["member_id"] != mid or processed["member_id"] != mid
                or acquired["work_id"] != request["work_id"] or processed["work_id"] != request["work_id"]
                or acquired["request_sha256"] != e.sha(e.encoded(request))
                or processed["acquisition_receipt_sha256"] != e.sha(e.encoded(acquired))):
            raise ValueError(f"MEMBER_RECEIPT_MISMATCH:{mid}")
        body = acquired["body"]
        followup_path = cache / "official-mirror-followup/acquisition" / f"{mid}.json"
        if not body and followup_path.exists():
            followup = e.read(followup_path)
            if followup["work_id"] != request["work_id"]:
                raise ValueError("FOLLOWUP_WORK_ID_MISMATCH")
            body = followup["body"]
            if body:
                if request["captured_version_id"].removeprefix("arxiv:") not in body["url"]:
                    raise ValueError("FOLLOWUP_VERSION_MISMATCH")
                acquired = {**acquired, "attempts": [*acquired["attempts"], *followup["attempts"]]}
        source_items = []
        if body:
            raw = Path(body["raw_path"]).read_bytes()
            if (e.sha(raw) != body["sha256"]
                    or processed["raw_source_sha256"] not in {None, body["sha256"]}):
                raise ValueError(f"SOURCE_HASH_MISMATCH:{mid}")
            if body["kind"] == "HTML":
                e.validate_body(raw, body["url"])
                source_items = clauses.extract(raw)
            for item in source_items:
                clauses.verify(raw, item)
            custodian["source_bodies"].append({"member_id": mid, "sha256": body["sha256"], "raw_path": body["raw_path"]})
        e.write_new(cache / "finite-clauses-v2" / f"{mid}.json", {
            "member_id": mid, "source_sha256": body["sha256"] if body else None,
            "ruleset": clauses.RULESET, "source_items": source_items,
            "provider": config["provider_id"], "independent_eligibility_review": "NOT_PERFORMED"})
        date = request["bibliography"]["updated"]
        captured_before_cutoff = bool(date and date < config["bibliographic_cutoff"])
        base = {"work_id": request["work_id"], "member_id": mid, "review_id": request["review_id"]}
        provenance = {
            "source_url": body["url"] if body else request["urls"][0],
            "version": request["captured_version_id"] or "UNVERSIONED_ANTHOLOGY_PDF_NOT_CUTOFF_VERIFIED",
            "retrieved_utc": body["finished_utc"] if body else acquired["completed_utc"],
            "http_or_access_status": body["status"] if body else "UNAVAILABLE_RECORDED_ATTEMPTS",
            "raw_source_sha256": body["sha256"] if body else None,
        }
        bibliography = {
            **base, "evidence_id": f"BIB-{mid}", "captured_bibliography": request["bibliography"],
            "metadata_record_sha256": request["metadata_record_sha256"],
            "date_fields_origin": "FROZEN_DISCOVERY_METADATA_NOT_INFERRED_FROM_NEW_PDF",
            "captured_version_id": request["captured_version_id"],
            "captured_updated_before_cutoff": captured_before_cutoff,
            "retrieved_body_version_evidence": body["version_state"] if body else "UNAVAILABLE",
            "selected_protocol_version": None,
            "preferred_version_status": "INDEPENDENT_ADJUDICATION_REQUIRED",
            "access_attempts": [{k: a.get(k) for k in ("url", "status", "started_utc", "finished_utc")} for a in acquired["attempts"]],
            **provenance,
        }
        bibliographic.append(bibliography)
        receipts.append({**base, "evidence_id": f"BIB-{mid}",
                         "requested_method_or_bibliographic_fact": "FROZEN_BIBLIOGRAPHY_AND_PRIMARY_ACCESS",
                         **provenance, "provider_id": config["provider_id"],
                         "method_dataset_or_bibliographic_locator": "FROZEN_METADATA_MEMBER_AND_PINNED_PRIMARY_RESPONSE",
                         "restricted_evidence_sha256": e.sha(e.encoded(bibliography)),
                         "restriction_checked_by": "AUTOMATED_ALLOWLIST_AND_HASH_CHECK_NO_INDEPENDENT_ATTESTATION",
                         "qualitative_and_quantitative_findings_absent": True,
                         "reviewer_received_utc": None,
                         "limitations": "FINAL_PROTOCOL_VERSION_AND_ELIGIBILITY_NOT_DETERMINED"})
        released = []
        for item in source_items:
            # Keep literal quotes short across every version of a work. This is
            # a transfer-display bound, never an eligibility or sampling limit.
            words = len(item["quote"].split())
            work = request["work_id"]
            if used_words.get(work, 0) + words > 25:
                continue
            used_words[work] = used_words.get(work, 0) + words
            eid = f"METHOD-{mid}-{len(released) + 1:02d}"
            method = {**base, **item, "evidence_id": eid, **provenance,
                      "eligibility_inference": "NOT_PERFORMED"}
            methods.append(method)
            receipts.append({**base, "evidence_id": eid, **provenance,
                             "requested_method_or_bibliographic_fact": item["grammar_rule"],
                             "provider_id": config["provider_id"],
                             "method_dataset_or_bibliographic_locator": item["locator"],
                             "restricted_evidence_sha256": e.sha(e.encoded(method)),
                             "restriction_checked_by": "AUTOMATED_STRUCTURE_SPAN_AND_FINITE_GRAMMAR_V2",
                             "qualitative_and_quantitative_findings_absent": True,
                             "reviewer_received_utc": None,
                             "limitations": item["limitation"]})
            released.append(eid)
        codes = ["FINAL_PREFERRED_VERSION_REVIEW_REQUIRED", "MATERIAL_ELIGIBILITY_FACTS_NOT_ESTABLISHED"]
        if not body:
            codes.append("PRIMARY_FULL_TEXT_UNAVAILABLE_NOT_AN_EXCLUSION")
        if body and body["kind"] == "PDF":
            codes.append("PDF_LAYOUT_AND_SEMANTIC_RESTRICTION_CHECK_REQUIRED")
        if processed["method_proposal_count"]:
            codes.append("BROADER_METHOD_PROPOSALS_QUARANTINED_SEMANTIC_CHECKER_REQUIRED")
        if not released:
            codes.append("NO_METHOD_CLAUSE_ADMITTED_BY_CLOSED_LANGUAGE")
        exceptions.append({**base, "codes": codes})
        ledger.append({**base, "acquisition_attempted": True, "source_available": bool(body),
                       "captured_source_version_body_verified": bool(body and body["version_state"] in {"EXACT_VERSION_SELF_LINK", "EXACT_VERSION_IN_BODY"}),
                       "final_preferred_version_verified": False,
                       "relevant_method_regions_found": bool(processed["method_structure"].get("method_terms_found")),
                       "quarantined_method_proposal_count": processed["method_proposal_count"],
                       "closed_language_method_proposals_generated": len(source_items),
                       "verified_method_evidence_ids": released,
                       "restricted_bibliographic_packet_ready": True,
                       "complete_method_evidence_ready": False,
                       "delivered_to_reviewer": False, "independent_review_completed": False,
                       "decision": None})
        custodian["source_receipts"].append({"member_id": mid, "path": str(acquired_path), "sha256": e.sha(acquired_path.read_bytes())})
        custodian["processing_receipts"].append({"member_id": mid, "path": str(processed_path), "sha256": e.sha(processed_path.read_bytes())})
    crosswalk = []
    for work in frozen["works"]:
        member_rows = [row for row in ledger if row["work_id"] == work["work_id"]]
        ids = [f"BIB-{mid}" for mid in work["member_ids"]]
        ids.extend(eid for row in member_rows for eid in row["verified_method_evidence_ids"])
        crosswalk.append({"work_id": work["work_id"], "review_id": work["review_id"],
                          "member_ids": work["member_ids"], "evidence_ids": ids,
                          "source_available": any(r["source_available"] for r in member_rows),
                          "exact_captured_version_body_verified": any(r["captured_source_version_body_verified"] for r in member_rows),
                          "final_preferred_version_verified": False,
                          "has_verified_method_clause": any(r["verified_method_evidence_ids"] for r in member_rows),
                          "complete_method_evidence_ready": False, "decision": None})
    if len(crosswalk) != 372 or len(ledger) != 389:
        raise ValueError("INCOMPLETE_FRAME")
    inventory = e.read(e.BASE / "a04-handoff/restricted/CANDIDATE_INVENTORY.json")
    sentinels = e.read(e.BASE / "SENTINEL_INVENTORY_AMENDED.json")["work_exclusions"]
    sentinel_by_id = {s["work_id"]: s["exclude_versions"] for s in sentinels}
    sentinel_crosswalk = [{"work_id": w["work_id"], "review_id": w["review_id"],
                           "exact_identifier_matches": [{"sentinel_id": i, "exclude_versions": sentinel_by_id[i]}
                                                        for i in w["identifiers"] if i in sentinel_by_id],
                           "matching_scope": "IDENTIFIER_ONLY_RENAMED_OR_OTHER_VERSION_MATCHES_REQUIRE_BIBLIOGRAPHIC_REVIEW",
                           "decision": None} for w in inventory]
    payloads = {"WORK_EVIDENCE_CROSSWALK.json": crosswalk, "BIBLIOGRAPHIC_EVIDENCE.json": bibliographic,
                "METHOD_EVIDENCE.json": methods, "EVIDENCE_RECEIPTS.json": receipts,
                "EXCEPTIONS.json": exceptions, "MEMBER_COVERAGE.json": ledger,
                "SENTINEL_IDENTIFIER_CROSSWALK.json": sentinel_crosswalk}
    followups = e.read(e.BASE / config["run_id"] / "PRIMARY_ACCESS_FOLLOWUPS.json")
    payloads["PRIMARY_ACCESS_FOLLOWUPS.json"] = followups
    custodian["coverage"] = {
        "works": 372, "members": 389,
        "works_with_primary_source": sum(w["source_available"] for w in crosswalk),
        "members_with_primary_source": sum(w["source_available"] for w in ledger),
        "works_with_exact_captured_version_in_body": sum(w["exact_captured_version_body_verified"] for w in crosswalk),
        "members_with_exact_captured_version_in_body": sum(w["captured_source_version_body_verified"] for w in ledger),
        "final_preferred_versions_independently_verified": 0,
        "works_with_quarantined_method_proposals": len({r["work_id"] for r in ledger if r["quarantined_method_proposal_count"]}),
        "quarantined_method_proposals": sum(r["quarantined_method_proposal_count"] for r in ledger),
        "works_with_verified_method_clauses": sum(w["has_verified_method_clause"] for w in crosswalk),
        "verified_method_clauses": len(methods), "works_with_restricted_bibliographic_packets": 372,
        "works_with_complete_method_evidence": 0, "delivered_to_actual_reviewer": 0,
        "independent_eligibility_judgments": 0,
    }
    return payloads, custodian


def freeze(config: dict, head: str) -> None:
    """Freeze a verified partial supplement and a separate custodian-only audit."""
    e.baseline(config)
    payloads, custodian = build(config)
    root = e.BASE / config["run_id"]
    output = root / "restricted-supplement"
    if output.exists() or (root / "RESTRICTED_EVIDENCE_SUPPLEMENT.zip").exists():
        raise FileExistsError("Do not overwrite a frozen evidence supplement")
    files = {name: e.encoded(value) for name, value in payloads.items()}
    for name in ("README.md", "verify_evidence.py"):
        files[name] = (e.SOURCE / name).read_bytes()
    for name in ("REVIEWER_INTAKE_BLANK.json", "ELIGIBILITY_REVIEW_BLANK.json", "EVIDENCE_RECEIPT_BLANK.json"):
        files[name] = (e.BASE / "a04-handoff/restricted" / name).read_bytes()
    # Include the finite grammar as code, without access to repository/caches.
    files["finite_language.json"] = e.encoded({"ruleset": clauses.RULESET,
        "patterns": {name: pattern.pattern for name, pattern in clauses.PATTERNS.items()}})
    files["verify_evidence.py"] = files["verify_evidence.py"].replace(
        b"__FINITE_LANGUAGE_SHA256__", e.sha(files["finite_language.json"]).encode())
    manifest = {"created_utc": e.now(), "source_git_commit": head, "source_tree_clean_at_start": True,
                "intake_sha256": config["intake_archive_sha256"] ,
                "files": {name: e.sha(raw) for name, raw in files.items()},
                "scope": "A04_PARTIAL_EVIDENCE_SUPPLEMENT_NOT_FRAME_APPROVAL",
                "coverage": custodian["coverage"], "gate": "FRAME_BLOCKED",
                "provider": config["provider_id"], "independent_reviewer_attested_locally": False,
                "separate_semantic_checker_established": False, "delivered_to_reviewer": False,
                "draw_executed": False, "B2": "NOT_AUTHORIZED"}
    files["MANIFEST.json"] = e.encoded(manifest)
    output.mkdir()
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    archive = root / "RESTRICTED_EVIDENCE_SUPPLEMENT.zip"
    with zipfile.ZipFile(archive, "x") as packaged:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            packaged.writestr(info, raw)
    with zipfile.ZipFile(archive) as packaged:
        if len(packaged.namelist()) != len(files) or set(packaged.namelist()) != set(files):
            raise ValueError("ARCHIVE_ALLOWLIST_MISMATCH")
        for name, raw in files.items():
            if packaged.read(name) != raw:
                raise ValueError("ARCHIVE_BYTE_MISMATCH")
    if archive.stat().st_size >= 10_000_000:
        raise ValueError("STAGING_SIZE_LIMIT")
    custodian.update({"source_git_commit": head, "package_sha256": e.sha(archive.read_bytes()),
                      "package_bytes": archive.stat().st_size, "manifest_sha256": e.sha(files["MANIFEST.json"]),
                      "gate": "FRAME_BLOCKED", "actual_delivery": "NOT_PERFORMED",
                      "protocol_hashes": e.baseline(config)["historical_locks"],
                      "source_code_sha256": {p.name: e.sha(p.read_bytes()) for p in (
                          Path(__file__), Path(e.__file__), Path(clauses.__file__), e.CONFIG)},
                      "parser_versions": {n: importlib.metadata.version(n) for n in ("beautifulsoup4", "pypdf")},
                      "restriction_check_type": "AUTOMATED_FINITE_LANGUAGE_NOT_INDEPENDENT_SEMANTIC_ATTESTATION"})
    e.write_new(root / "CUSTODIAN_EVIDENCE_MANIFEST.json", custodian)
    print(json.dumps({"coverage": custodian["coverage"], "package_sha256": custodian["package_sha256"],
                      "package_bytes": custodian["package_bytes"], "gate": "FRAME_BLOCKED"}), flush=True)
