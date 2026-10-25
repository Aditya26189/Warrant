"""Replay exposed-custodian judgments over the immutable unsampled A05 proposal."""
from __future__ import annotations

import argparse
import collections
import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import release_deep as r

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "a05-custodian-adjudication-20261023"
sys.path.insert(0, str(OLD))
spec = importlib.util.spec_from_file_location("prior_a05_compiler", OLD / "compile_proposal.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
CRITERIA = set(prior.CRITERIA)
BASELINE = "e073ce2cb94c240e5570a51446a4d0a36fda51e5"


def validate_fact_receipt(fact: dict, checker: dict, release_request_sha256: str) -> None:
    """Prevent relabeling an approved field as another work or edition."""
    if (checker["review_id"] != fact["review_id"]
            or checker["requested_preferred_version"] != fact["version"]
            or checker["request_sha256"] != release_request_sha256):
        raise ValueError("FACT_CHECKER_WORK_VERSION_OR_REQUEST_CHANGED")


def load_evidence() -> dict:
    """Verify source/checker payloads before using any new scientific assertion."""
    book = json.loads((OLD / "SOURCE_CASEBOOK.json").read_bytes())
    evidence = {f["evidence_id"]: f for c in book["cases"] for f in c["evidence"]}
    for release_path in [*sorted(OLD.glob("RELEASED_FACTS_*.json")),
                         *sorted(HERE.glob("releases/*/FACTS.json"))]:
        release = json.loads(release_path.read_bytes())
        root = release_path.parent if release_path.name == "FACTS.json" else OLD / "checked-source-receipts"
        if any(r.sha((root / name).read_bytes()) != digest for name, digest in release["source_files"].items()):
            raise ValueError("RELEASE_RECEIPT_CHANGED")
        for fact in release["facts"]:
            eid = fact["evidence_id"]
            if eid in evidence:
                if evidence[eid] != fact:
                    raise ValueError("EVIDENCE_ID_COLLISION")
                continue
            if "value" in fact:
                if r.sha(r.encoded(fact["value"])) != fact["value_sha256"]:
                    raise ValueError("RELEASED_VALUE_CHANGED")
                checker_raw = (root / fact["checker_receipt"]).read_bytes()
                checker = json.loads(checker_raw)
                validate_fact_receipt(fact, checker, release["request_sha256"])
                if r.sha(checker_raw) != fact["checker_receipt_sha256"]:
                    raise ValueError("FACT_CHECKER_CHANGED")
                checks = [x for x in checker["per_fact"] if x["field_path"] == fact["field_path"]]
                if (len(checks) != 1 or checks[0]["decision"] != "APPROVE"
                        or checker["provider_packet_sha256"] != fact["provider_packet_sha256"]
                        or checker["actor"] != fact["checker_actor"]
                        or fact["checker_actor"] == fact["provider_actor"]):
                    raise ValueError("FACT_NOT_SEPARATELY_APPROVED")
                provider_raw = Path(checker["provider_packet"]).read_bytes()
                if (r.sha(provider_raw) != fact["provider_packet_sha256"]
                        or r.field(json.loads(provider_raw), fact["field_path"]) != fact["value"]
                        or fact.get("clarification_scope") != json.loads(provider_raw).get("clarification_scope")):
                    raise ValueError("VALUE_NOT_EXACT_APPROVED_PROVIDER_FIELD")
            evidence[eid] = fact
    for release_path in sorted(HERE.glob("bibliography/*/FACTS.json")):
        release = json.loads(release_path.read_bytes())
        root = release_path.parent
        if any(r.sha((root / name).read_bytes()) != digest for name, digest in release["source_files"].items()):
            raise ValueError("BIBLIOGRAPHY_RECEIPT_CHANGED")
        for fact in release["facts"]:
            check_raw = (root / fact["checker_receipt"]).read_bytes()
            check = json.loads(check_raw)
            n = int(fact["evidence_id"].rsplit("-F", 1)[1]) - 1
            approval = check["per_fact"][n]
            source_raw = (root / fact["source_receipt"]).read_bytes()
            source = json.loads(source_raw)
            if (r.sha(check_raw) != fact["checker_receipt_sha256"] or approval["decision"] != "APPROVE"
                    or fact["provider_actor"] == fact["checker_actor"] or check["actor"] != fact["checker_actor"]
                    or source["review_id"] != fact["review_id"]):
                raise ValueError("BIBLIOGRAPHY_NOT_APPROVED")
            binding = [x for x in check["sources"] if Path(x["receipt"]).name == Path(fact["source_receipt"]).name]
            if len(binding) != 1 or binding[0]["receipt_sha256"] != r.sha(source_raw):
                raise ValueError("BIBLIOGRAPHY_PROVIDER_CHANGED")
            match = re.fullmatch(r"records\[\d+\]\.metadata_fields\[(\d+)\]", approval["field_path"])
            if match:
                item = source["metadata_fields"][int(match[1])]
                value = item["value"]
                digest = r.sha(value.encode())
                if item["field"] != fact["field"] or item["locator"] != fact["source_locator"]:
                    raise ValueError("BIBLIOGRAPHY_FIELD_CHANGED")
            else:
                field = approval["field_path"].removeprefix("receipt.bibliographic_fields.")
                value = source["bibliographic_fields"][field]
                digest = r.sha(json.dumps(value, sort_keys=True).encode())
            if value != fact["value"] or digest != approval["value_sha256"]:
                raise ValueError("BIBLIOGRAPHY_VALUE_CHANGED")
            if fact["evidence_id"] in evidence and evidence[fact["evidence_id"]] != fact:
                raise ValueError("BIBLIOGRAPHY_EVIDENCE_COLLISION")
            evidence[fact["evidence_id"]] = fact
    return evidence


def validate_refs(refs: list, rid: str, evidence: dict, version: str | None = None) -> None:
    """A selected-edition judgment cannot borrow another work's/version's facts."""
    if not refs:
        raise ValueError("EMPTY_SCIENTIFIC_EVIDENCE")
    for eid in refs:
        fact = evidence.get(eid)
        if not fact or fact["review_id"] != rid:
            raise ValueError("FOREIGN_OR_UNKNOWN_EVIDENCE")
        if version and fact.get("version") != version:
            raise ValueError("MIXED_VERSION_EVIDENCE")


def apply_domain(row: dict, change: dict, evidence: dict) -> None:
    """Validate source-bound authored judgments, never infer labels from keywords."""
    if r.sha(r.encoded(row)) != change["before_row_sha256"] or row["work_id"] != change["work_id"]:
        raise ValueError("PRIOR_ROW_CHANGED")
    criteria = change["criteria"]
    if set(criteria) != CRITERIA or set(criteria.values()) - {"MET", "NOT_MET", "UNCLEAR"}:
        raise ValueError("BAD_CRITERIA")
    rid = row["review_id"]
    validate_refs(change["new_evidence_ids"], rid, evidence, row["selected_version_id"])
    if any(evidence[eid].get("release_status") == "CHECKED_BIBLIOGRAPHIC_SCOPE_NOT_ELIGIBILITY"
           for eid in change["new_evidence_ids"]):
        raise ValueError("BIBLIOGRAPHY_IS_NOT_DOMAIN_PROOF")
    ground = change["whole_work_exclusion_ground"]
    if ground:
        if "NOT_MET" not in criteria.values():
            raise ValueError("EXCLUSION_WITHOUT_ESTABLISHED_FAILURE")
        scope = change["exclusion_basis"]
        if scope in {"COMPLETE_EVALUATED_ARM_SCOPE", "COMPLETE_NONEMPIRICAL_SCOPE"}:
            if not any(evidence[eid].get("field_path") == "coverage.scope_completeness"
                       and evidence[eid]["value"] is True and not evidence[eid].get("clarification_scope")
                       for eid in change["new_evidence_ids"]):
                raise ValueError("EXCLUSION_FROM_PARTIAL_SCOPE")
        elif scope == "EXPLICIT_WHOLE_STUDY_TASK_SCOPE":
            if criteria["input_injection_task"] != "NOT_MET" or not any(
                    evidence[eid].get("field_path") == "study_scope_statement" and evidence[eid].get("value")
                    for eid in change["new_evidence_ids"]):
                raise ValueError("NO_AFFIRMATIVE_WHOLE_STUDY_TASK_PROOF")
        elif scope != "EXPLICIT_NONEMPIRICAL_DESIGN":
            raise ValueError("UNKNOWN_EXCLUSION_BASIS")
    proof = change["positive_criterion_evidence_ids"]
    if set(criteria.values()) == {"MET"}:
        if not proof or set(proof) != CRITERIA:
            raise ValueError("POSITIVE_PROOF_MISSING")
        for refs in proof.values():
            validate_refs(refs, rid, evidence, row["selected_version_id"])
            if any(evidence[eid].get("release_status") == "CHECKED_BIBLIOGRAPHIC_SCOPE_NOT_ELIGIBILITY"
                   for eid in refs):
                raise ValueError("BIBLIOGRAPHY_IS_NOT_DOMAIN_PROOF")
        row["positive_experiment_binding"] = {"review_id": rid, "criterion_evidence_ids": proof,
            "experiment_and_inference_rationale": change["scientific_rationale"]}
    row.update({"criteria": criteria, "whole_work_exclusion_ground": ground,
                "scientific_rationale": change["scientific_rationale"],
                "considered_method_evidence_ids": sorted(set(row["considered_method_evidence_ids"] + change["new_evidence_ids"])),
                "deep_exclusion_basis": change["exclusion_basis"]})


def apply_version(row: dict, correction: dict, evidence: dict | None = None) -> None:
    """Remove only the disclosed, extra timestamp condition; retain its evidence."""
    if r.sha(r.encoded(row)) != correction["before_row_sha256"]:
        raise ValueError("VERSION_PRIOR_CHANGED")
    if correction["action"] == "RECLASSIFY_REPOSITORY_DOI_AS_PREPRINT":
        if row["review_id"] != "W0368" or correction["selected_version_id"] != row["selected_version_id"] or evidence is None:
            raise ValueError("UNSUPPORTED_REPOSITORY_CORRECTION")
        if r.sha((HERE / correction["rule_document"]).read_bytes()) != correction["rule_document_sha256"]:
            raise ValueError("VERSION_REASONING_CHANGED")
        validate_refs(correction["evidence_ids"], row["review_id"], evidence)
        facts = {evidence[eid]["field"]: evidence[eid]["value"] for eid in correction["evidence_ids"]}
        if (facts.get("resource_type", {}).get("subtype") != "preprint"
                or "doi:" + facts.get("doi", "") != row["work_id"]
                or facts.get("version") != "1.0.0" or facts.get("publication_date") != "2026-04-18"
                or row["selected_version_id"] != "arxiv:2604.18248v4"
                or row["bibliography"]["selected"]["date_interval"] != ["2026-07-30", "2026-07-30"]):
            raise ValueError("REPOSITORY_PRIMARY_TYPE_OR_CHRONOLOGY_CHANGED")
        bib = row["bibliography"]
        expected = "KNOWN_PUBLISHER_VOR_AVAILABILITY_OR_EXACT_VERSION_UNRESOLVED"
        if bib["version_issues"] != [expected]:
            raise ValueError("DIFFERENT_REPOSITORY_VERSION_PROBLEM")
        bib["superseded_version_issues"] = bib["version_issues"]
        bib["version_issues"] = []
        bib["status"] = "MET"
        bib["first_public_date_interval"] = [facts["publication_date"]] * 2
        bib["first_public_evidence_ids"] = [eid for eid in correction["evidence_ids"]
                                           if evidence[eid]["field"] == "publication_date"]
        bib["repository_preprint_metadata_evidence_ids"] = correction["evidence_ids"]
        bib["retained_limitations"] = correction["retained_limitations"]
        row["version_correction_rationale"] = correction["rationale"]
        return
    if (row["review_id"] != "W0339" or correction["action"] !=
            "RETAIN_DECLARED_PUBLISHER_EDITION_REMOVE_ADDED_BYTE_TIMESTAMP_REQUIREMENT"
            or correction["selected_version_id"] != row["selected_version_id"]):
        raise ValueError("UNSUPPORTED_VERSION_CORRECTION")
    if r.sha((HERE / correction["rule_document"]).read_bytes()) != correction["rule_document_sha256"]:
        raise ValueError("VERSION_REASONING_CHANGED")
    bib = row["bibliography"]
    expected = "PUBLISHER_HEADER_DATES_ONLY_EXACT_CUTOFF_VOR_BYTES_UNAUTHENTICATED_POSTCUTOFF_LAST_MODIFIED"
    if bib["version_issues"] != [expected] or not bib["selected_method_body_supported"]:
        raise ValueError("DIFFERENT_VERSION_PROBLEM")
    if bib["selected"]["date_interval"] != ["2026-09-03", "2026-09-03"]:
        raise ValueError("PUBLISHER_EDITION_DATE_CHANGED")
    metadata = json.loads((OLD / bib["selected"]["metadata_receipt"]).read_bytes())
    if (metadata["pdf_identity"]["header_dates"]["date_of_publication"] != "2026-08-28"
            or metadata["pdf_identity"]["header_dates"]["date_of_current_version"] != "2026-09-03"):
        raise ValueError("PRIMARY_DATE_CHANGED")
    bib["superseded_version_issues"] = bib["version_issues"]
    bib["version_issues"] = []
    bib["status"] = "MET"
    bib["selected"]["unresolved_reasons"] = []
    bib["historical_byte_authentication"] = "NOT_ESTABLISHED_NOT_A_LOCKED_UNIVERSAL_REQUIREMENT"
    bib["retained_limitations"] = correction["retained_limitations"]
    row["version_correction_rationale"] = correction["rationale"]


def apply_identity(rows: dict, correction: dict, evidence: dict) -> set[str]:
    """Record distinct whole documents with reuse, without transferring methods."""
    expected = {"W0069": ("arxiv:2508.04281", "arxiv:2508.04281v5"),
                "W0325": ("arxiv:2610.04412", "arxiv:2610.04412v1")}
    if (correction["action"] != "KEEP_DISTINCT_WORKS_SHARED_STUDY"
            or set(correction["works"]) != set(expected)
            or correction["referenced_paper_version"] != "UNSPECIFIED_IN_THESIS"
            or not correction["rationale"] or not correction["limitations"]):
        raise ValueError("UNSUPPORTED_IDENTITY_CORRECTION")
    name = correction["rule_document"]
    if (name != "WORK_UNIT_RULE_APPLICATION.md"
            or r.sha((HERE / name).read_bytes()) != correction["rule_document_sha256"]):
        raise ValueError("IDENTITY_RULE_CHANGED")
    # Validate the entire pair before mutating either member.
    for rid, (work, version) in expected.items():
        row, pin = rows[rid], correction["works"][rid]
        if (row["work_id"] != work or row["selected_version_id"] != version
                or r.sha(r.encoded(row)) != pin["before_row_sha256"]):
            raise ValueError("IDENTITY_PRIOR_CHANGED")
        if row["identity_issues"] != ["REPRODUCED_STUDY_UNIT_UNRESOLVED"]:
            raise ValueError("DIFFERENT_IDENTITY_PROBLEM")
        validate_refs(pin["evidence_ids"], rid, evidence, version)
        fields = set()
        for eid in pin["evidence_ids"]:
            fact = evidence[eid]
            if fact.get("release_status") != "CHECKED_BIBLIOGRAPHIC_SCOPE_NOT_ELIGIBILITY":
                raise ValueError("IDENTITY_REQUIRES_CHECKED_BIBLIOGRAPHIC_SCOPE")
            fields.add(fact["field_path"].removeprefix("bibliographic_scope_facts."))
        if (not {"title", "whole_document_scope", "edition", "source_declared_relationship"} <= fields
                or not fields.intersection({"author", "authors"})
                or (rid == "W0325" and "document_type" not in fields)):
            raise ValueError("IDENTITY_SCOPE_PROOF_INCOMPLETE")
    for rid in expected:
        row = rows[rid]
        row["superseded_identity_issues"] = row["identity_issues"]
        row["identity_issues"] = []
        row["shared_study_relationship"] = {
            "other_review_id": next(x for x in expected if x != rid),
            "relation": "THESIS_CHAPTER_BASED_ON_PAPER_DISTINCT_WHOLE_DOCUMENTS",
            "referenced_paper_version": correction["referenced_paper_version"],
            "evidence_by_work": {k: v["evidence_ids"] for k, v in correction["works"].items()},
            "rationale": correction["rationale"], "limitations": correction["limitations"],
            "method_evidence_transferred": False, "independent_replication": False}
    return set(expected)


def recompute(row: dict) -> None:
    """Preserve unresolved facts while applying the already locked pointwise gate."""
    bib = row["bibliography"]
    sentinel = any(x["exclude_versions"] == "ALL" for x in row["sentinel_exact_matches"])
    positive = set(row["criteria"].values()) == {"MET"}
    proof = row.get("positive_experiment_binding")
    if sentinel or row["whole_work_exclusion_ground"]:
        row["decision"] = "EXCLUDE"
    elif (positive and proof and bib["status"] == "MET"
          and bib["selected_method_body_supported"] and not row["identity_issues"]):
        row["decision"] = "POINTWISE_SUPPORTED_PENDING_FRAME"
    else:
        row["decision"] = "UNCLEAR"
    unresolved = [k for k in sorted(CRITERIA) if row["criteria"][k] != "MET"]
    if bib["status"] != "MET":
        unresolved.append("preferred_version_or_date")
    if not bib["selected_method_body_supported"]:
        unresolved.append("selected_body_source_binding")
    if positive and not proof:
        unresolved.append("same_preferred_version_criterion_evidence")
    row["unresolved_components"] = unresolved + row["identity_issues"]


def assemble(head: str) -> dict[str, object]:
    """Produce a full unsampled proposal with append-only before-hash corrections."""
    evidence = load_evidence()
    baseline_raw = (OLD / "CUSTODIAN_FRAME_PROPOSAL.json").read_bytes()
    original = json.loads(baseline_raw)
    rows = {x["review_id"]: copy.deepcopy(x) for x in original["rows"]}
    history = []
    for path in sorted(HERE.glob("AUTHOR_JUDGMENTS_*.json")):
        judgments = json.loads(path.read_bytes())
        if (judgments["actor"] != "EXPOSED_CUSTODIAN_ROOT" or not judgments["not_fresh_independent"]
                or judgments["baseline_proposal_sha256"] != r.sha(baseline_raw)):
            raise ValueError("JUDGMENT_AUTHORITY_OR_BASE_CHANGED")
        release_pins = {r.sha(p.read_bytes()) for p in HERE.glob("releases/*/FACTS.json")}
        if judgments["release_sha256"] not in release_pins:
            raise ValueError("AUTHOR_RELEASE_CHANGED")
        if set(judgments.get("additional_release_sha256", [])) - release_pins:
            raise ValueError("AUTHOR_ADDITIONAL_RELEASE_CHANGED")
        if judgments.get("bibliography_release_sha256") and judgments["bibliography_release_sha256"] not in {
                r.sha(p.read_bytes()) for p in HERE.glob("bibliography/*/FACTS.json")}:
            raise ValueError("AUTHOR_BIBLIOGRAPHY_RELEASE_CHANGED")
        for name, digest in judgments.get("interpretation_documents", {}).items():
            if Path(name).name != name or r.sha((HERE / name).read_bytes()) != digest:
                raise ValueError("AUTHOR_INTERPRETATION_DOCUMENT_CHANGED")
        touched = set()
        for change in judgments["changes"]:
            rid = change["review_id"]
            if rid in touched:
                raise ValueError("DUPLICATE_DOMAIN_CORRECTION")
            apply_domain(rows[rid], change, evidence)
            touched.add(rid)
        for correction in judgments["version_corrections"]:
            apply_version(rows[correction["review_id"]], correction, evidence)
            touched.add(correction["review_id"])
        for correction in judgments.get("identity_corrections", []):
            if touched.intersection(correction["works"]):
                raise ValueError("OVERLAPPING_IDENTITY_CORRECTION")
            touched.update(apply_identity(rows, correction, evidence))
        for note in judgments["reviewed_unchanged"]:
            row = rows[note["review_id"]]
            if r.sha(r.encoded(row)) != note["before_row_sha256"]:
                raise ValueError("UNCHANGED_REVIEW_PRIOR_CHANGED")
            validate_refs(note["checked_evidence_ids"], row["review_id"], evidence, row["selected_version_id"])
            row["deep_review_notes"] = note
            touched.add(row["review_id"])
        for rid in touched:
            recompute(rows[rid])
        history.append({"file": path.name, "sha256": r.sha(path.read_bytes()), "reviewed_works": sorted(touched)})
    for row in rows.values():
        if row["positive_experiment_binding"] and set(row["criteria"].values()) == {"MET"}:
            for refs in row["positive_experiment_binding"]["criterion_evidence_ids"].values():
                validate_refs(refs, row["review_id"], evidence, row["selected_version_id"])
    out = [rows[k] for k in sorted(rows)]
    if {x["work_id"] for x in out} != {x["work_id"] for x in original["rows"]}:
        raise ValueError("FROZEN_UNIVERSE_CHANGED")
    for before, after in zip(original["rows"], out, strict=True):
        if before["memberships"] != after["memberships"] or before["sentinel_exact_matches"] != after["sentinel_exact_matches"]:
            raise ValueError("MEMBERSHIP_OR_SENTINEL_CHANGED")
    counts = dict(collections.Counter(x["decision"] for x in out))
    unresolved = [x for x in out if x["decision"] == "UNCLEAR"]
    summary = {"status": "FRAME_BLOCKED" if unresolved else "COMPLETE_PROPOSAL_AWAITING_APPROVAL",
               "source_git_commit": head, "works": len(out),
               "memberships": sum(len(x["memberships"]) for x in out), "decisions": counts,
               "all_domain_criteria_met": sum(set(x["criteria"].values()) == {"MET"} for x in out),
               "new_scientific_judgment_files": history, "no_sampling": True, "b2_authorized": False,
               "role": "REVIEWER_INFORMED_EXPOSED_CUSTODIAN_NOT_FRESH_FINAL_REVIEW",
               "baseline_proposal_sha256": r.sha(baseline_raw)}
    report = ("# Deeper B1 scientific continuation\n\n"
              f"Generated from clean committed source `{head}`. Status: **{summary['status']}**.\n\n"
              f"All {len(out)} frozen works and {summary['memberships']} memberships are preserved. "
              f"Pointwise supported pending complete-frame approval: {counts.get('POINTWISE_SUPPORTED_PENDING_FRAME', 0)}; "
              f"excluded: {counts.get('EXCLUDE', 0)}; unresolved: {counts.get('UNCLEAR', 0)}. "
              f"All four domain criteria supported in a documented edition: {summary['all_domain_criteria_met']}.\n\n"
              "New source evidence inventories secondary arms and separates protected-answer dependence from auxiliary detection. "
              "Complete declared method scope or an explicit nonempirical design supports a scope exclusion; a partial inventory does not. "
              "Exact-edition English construction can establish an English component without asserting every item is English.\n\n"
              "W0339 retains its checked publisher edition and transport caveat. The added requirement to authenticate historical PDF bytes "
              "is removed under VERSION_RULE_APPLICATION.md; no dates or source checks are rewritten.\n\n"
              "The W0368 repository DOI is explicitly a preprint, so it receives no publisher-edition preference. "
              "Its earlier repository-declared publication date is retained separately from the selected later arXiv revision. "
              "Prior task assumptions for W0018 and W0061 were narrowed: binary jailbreak/adversarial-query labels alone do not establish injected-instruction detection.\n\n"
              "These are exposed-custodian judgments informed by preserved reviewer returns, not a fresh independent final review. "
              "Unresolved works are not exclusions. No literature prevalence, performance, assurance or publication-readiness claim follows. "
              "No draw, human assignment or B2 is authorized. Original packages and prior proposals remain unchanged.\n")
    return {"FRAME_PROPOSAL.json": {"summary": summary, "rows": out},
            "VALIDATION.json": {**summary, "inventory_preserved": True, "memberships_preserved": True,
                                "sentinel_matches_preserved": True, "positive_exact_version_refs_checked": True},
            "REMAINING_QUESTIONS.json": {"status": summary["status"], "requests": [
                {"review_id": x["review_id"], "work_id": x["work_id"], "selected_version_id": x["selected_version_id"],
                 "missing_components": x["unresolved_components"], "deep_review": x.get("deep_review_notes"),
                 "scope": "Primary methods/data/bibliography only; no results/counts/assurance classes."} for x in unresolved]},
            "REPORT.md": report}


def main() -> None:
    """Create a new checkpoint without replacing any prior research artifact."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    if len(args.run) != 3 or not args.run.isdigit():
        raise ValueError("BAD_RUN")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=HERE, text=True).strip():
        raise ValueError("DIRTY_TREE")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    outputs = assemble(head)
    destination = HERE / "checkpoints" / args.run
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in outputs.items():
        (destination / name).write_bytes(value.encode() if isinstance(value, str) else r.encoded(value))
    print(json.dumps(outputs["VALIDATION.json"], sort_keys=True))


if __name__ == "__main__":
    main()
