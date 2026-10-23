"""Validate attributed judgments and compile an unsampled A05 frame proposal.

Scientific states come only from signed custodian records, never availability
flags. Bibliographic chronology implements the locked preference and cutoff.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adjudicate as a  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "a05_administrative_dates", HERE.parent / "a04-custodian-repair-20261023/repair_review.py")
dates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dates)
CRITERIA = ("input_injection_task", "binary_evaluation", "before_target_answer", "english_evaluation")
CUTOFF = dt.datetime.fromisoformat("2026-10-17T00:00:00+00:00")


def bibliography(case: dict, override: dict | None = None) -> dict:
    """Separate preferred-version support, historical dates and actual body access."""
    official = [x for x in case["evidence"] if x["evidence_id"].startswith("R01-BIB-")]
    bindings = [x for x in case["evidence"] if x["evidence_id"].startswith("R01-SOURCE-")]
    registrations = [x for x in case["evidence"] if x["evidence_id"].startswith("R01-DOI-")]
    candidates = []
    issues = []
    for record in official:
        url = record["provenance"]["source_url"]
        identifier = dates.arxiv_id(url)
        if identifier:
            for revision in record["official_fields"]["revision_history"]:
                instant = dt.datetime.fromisoformat(revision["public_utc"].replace("Z", "+00:00"))
                if instant <= CUTOFF:
                    candidates.append({"version": "arxiv:" + identifier + revision["revision"],
                        "priority": 1, "date_interval": [instant.date().isoformat()] * 2,
                        "public_utc": revision["public_utc"], "member_id": record["member_id"],
                        "withdrawn": revision.get("withdrawn_in_history", False),
                        "evidence_ids": [record["evidence_id"]]})
        elif "aclanthology.org/" in url:
            identifier = url.rstrip("/").rsplit("/", 1)[-1]
            for literal in record["official_fields"]["publication_date_literals"]:
                bounds = dates.interval(literal["value"])
                if bounds and bounds[0] <= "2026-10-16" < bounds[1]:
                    issues.append("PUBLICATION_INTERVAL_STRADDLES_CUTOFF")
                elif bounds and bounds[1] <= "2026-10-16":
                    candidates.append({"version": "acl:" + identifier + ":publication",
                        "priority": 3, "date_interval": list(bounds), "member_id": record["member_id"],
                        "withdrawn": False, "evidence_ids": [record["evidence_id"]]})
    if override:
        candidates.append(override)
        issues.extend(override.get("unresolved_reasons", []))
    candidates.sort(key=lambda r: (r["priority"], r["date_interval"][1], r["version"]))
    selected = candidates[-1] if candidates else None
    known_other_dois = sorted({r.get("doi", "").lower() for r in registrations
        if r.get("doi") and not r["doi"].lower().startswith(("10.18653/", "10.48550/"))})
    if known_other_dois and not (selected and selected["priority"] == 3):
        issues.append("KNOWN_PUBLISHER_VOR_AVAILABILITY_OR_EXACT_VERSION_UNRESOLVED")
    if not selected:
        issues.append("NO_SUPPORTED_PREFERRED_VERSION")
    first = dates.first_public_basis(official)
    first_interval = list(first[0]) if first else None
    first_refs = first[1] if first else []
    if override and override.get("first_public_date_interval"):
        bounds = override["first_public_date_interval"]
        if first_interval is None or bounds[0] < first_interval[0]:
            first_interval, first_refs = bounds, override["evidence_ids"]
    if not first_interval or first_interval[0] < "2024-01-01" or first_interval[1] > "2026-10-16":
        issues.append("FIRST_PUBLIC_WINDOW_NOT_ESTABLISHED")
    selected_bindings = [x for x in bindings if selected and (
        x.get("captured_version_id") == selected["version"] or
        (selected["version"].startswith("acl:") and x["member_id"] == selected["member_id"]))]
    supported_body = bool(selected_bindings and all(x["method_release_supported"] for x in selected_bindings))
    if override and selected is override:
        supported_body = bool(override.get("source_body_supported"))
    return {"status": "MET" if selected and not issues else "UNCLEAR", "selected": selected,
            "first_public_date_interval": first_interval, "first_public_evidence_ids": first_refs,
            "version_issues": sorted(set(issues)), "selected_method_body_supported": supported_body,
            "access_records": [{"member_id": x["member_id"], "evidence_id": x["evidence_id"],
                "body": x.get("body"), "source_binding_basis": x["source_binding_basis"],
                "method_release_supported": x["method_release_supported"]} for x in bindings],
            "original_access_attempts": [{"member_id": x["member_id"], "evidence_id": x["evidence_id"],
                "attempts": x["access_attempts"], "source_url": x["source_url"],
                "http_or_access_status": x["http_or_access_status"]} for x in case["evidence"]
                if x["evidence_id"].startswith("BIB-M")],
            "known_registered_dois": known_other_dois,
            "scope_limit": "Preference among documented captured/public verification versions; no index refresh or claim of exhaustive publisher search."}


def validate_domain_rows(cases: list, rows: list, evidence: dict) -> None:
    """Reject dropped works, unsupported references and anonymous scientific states."""
    inventory = {c["review_id"]: c for c in cases}
    if len(rows) != len(inventory) or {r["review_id"] for r in rows} != set(inventory):
        raise ValueError("DOMAIN_WORK_COVERAGE")
    for row in rows:
        rid = row["review_id"]
        if row["work_id"] != inventory[rid]["inventory"]["work_id"] or set(row["criteria"]) != set(CRITERIA):
            raise ValueError("DOMAIN_ID_OR_CRITERIA")
        if set(row["criteria"].values()) - {"MET", "NOT_MET", "UNCLEAR"} or not row["scientific_rationale"]:
            raise ValueError("DOMAIN_SCIENTIFIC_RECORD")
        for eid in row["considered_method_evidence_ids"]:
            if eid not in evidence or evidence[eid]["review_id"] != rid:
                raise ValueError("DOMAIN_FOREIGN_EVIDENCE")


def validate_positive_binding(row: dict, binding: dict, evidence: dict, selected: str) -> None:
    """Require explicit same-version source proofs for every positive criterion."""
    if set(binding["criterion_evidence_ids"]) != set(CRITERIA):
        raise ValueError("POSITIVE_CRITERION_COVERAGE")
    for key, refs in binding["criterion_evidence_ids"].items():
        if not refs or row["criteria"][key] != "MET":
            raise ValueError("POSITIVE_NOT_ESTABLISHED")
        for eid in refs:
            fact = evidence.get(eid)
            if not fact or fact["review_id"] != row["review_id"] or fact.get("version") != selected:
                raise ValueError("POSITIVE_MIXED_VERSION_OR_FOREIGN_SOURCE")
    if not binding.get("experiment_and_inference_rationale"):
        raise ValueError("POSITIVE_NO_RATIONALE")


def assemble(source_head: str) -> dict[str, object]:
    """Compile separate original-review comparisons and new custodian proposal."""
    book = json.loads((HERE / "SOURCE_CASEBOOK.json").read_bytes())
    cases = book["cases"]
    evidence = {x["evidence_id"]: x for c in cases for x in c["evidence"]}
    for path in sorted(HERE.glob("RELEASED_FACTS_*.json")):
        for fact in json.loads(path.read_bytes())["facts"]:
            if fact["evidence_id"] in evidence:
                raise ValueError("NEW_EVIDENCE_COLLISION")
            evidence[fact["evidence_id"]] = fact
    rows = []
    for path in sorted(HERE.glob("DOMAIN_BATCH_*.json")):
        batch = json.loads(path.read_bytes())
        if batch["actor"] != "EXPOSED_CUSTODIAN_ROOT" or batch["casebook_sha256"] != a.sha((HERE / "SOURCE_CASEBOOK.json").read_bytes()):
            raise ValueError("DOMAIN_AUTHORITY_OR_INPUT_COMMITMENT")
        rows.extend(batch["rows"])
    validate_domain_rows(cases, rows, evidence)
    domain = {r["review_id"]: r for r in rows}
    revisions = json.loads((HERE / "SCIENTIFIC_RECONCILIATION.json").read_bytes())
    for correction in revisions["corrections"]:
        target = domain[correction["review_id"]]
        if a.sha(a.encoded(target)) != correction["before_sha256"]:
            raise ValueError("RECONCILIATION_BEFORE_CHANGED")
        target.update(correction["after_fields"])
    validate_domain_rows(cases, list(domain.values()), evidence)
    bindings = {r["review_id"]: r for r in json.loads((HERE / "POSITIVE_EXPERIMENT_BINDINGS.json").read_bytes())["rows"]}
    override_rows = json.loads((HERE / "BIBLIOGRAPHIC_OVERRIDES.json").read_bytes())["rows"]
    overrides = {r["review_id"]: r["candidate"] for r in override_rows}
    out = []
    changes = []
    requests = []
    for case in cases:
        rid = case["review_id"]
        row = domain[rid]
        bib = bibliography(case, overrides.get(rid))
        sentinel = case["sentinel_crosswalk"]["exact_identifier_matches"]
        excluded = any(x["exclude_versions"] == "ALL" for x in sentinel)
        identity_issues = (["REPRODUCED_STUDY_UNIT_UNRESOLVED"] if rid in {"W0069", "W0325"} else [])
        if rid == "W0274":
            identity_issues.append("RETRIEVED_BODY_IDENTITY_MISMATCH")
        version = bib["selected"]["version"] if bib["selected"] else None
        positive = set(row["criteria"].values()) == {"MET"}
        proof = bindings.get(rid)
        proof_ok = False
        if proof and positive and version:
            validate_positive_binding(row, proof, evidence, version)
            proof_ok = True
        if excluded or row["whole_work_exclusion_ground"]:
            decision = "EXCLUDE"
        elif positive and proof_ok and bib["status"] == "MET" and bib["selected_method_body_supported"] and not identity_issues:
            decision = "POINTWISE_SUPPORTED_PENDING_FRAME"
        else:
            decision = "UNCLEAR"
        unresolved = [k for k in CRITERIA if row["criteria"][k] != "MET"]
        if bib["status"] != "MET":
            unresolved.append("preferred_version_or_date")
        if not bib["selected_method_body_supported"]:
            unresolved.append("selected_body_source_binding")
        if positive and not proof_ok:
            unresolved.append("same_preferred_version_criterion_evidence")
        unresolved += identity_issues
        current = {**row, "decision": decision, "bibliography": bib,
            "selected_version_id": version, "positive_experiment_binding": proof,
            "memberships": case["inventory"]["members"], "sentinel_exact_matches": sentinel,
            "sentinel_limit": "Exact identifiers and documented crosslinks checked; global renamed/version-scope clearance is a frame requirement, not inferred from an empty exact match.",
            "identity_issues": identity_issues, "unresolved_components": unresolved,
            "actor": "EXPOSED_CUSTODIAN_ROOT", "not_fresh_independent": True}
        out.append(current)
        old = case["prior_b_administrative"]
        changes.append({"review_id": rid, "original_b_decision": old["decision"],
            "original_b_criteria": {k: old[k] for k in CRITERIA},
            "original_b_selected_version": old["selected_version_id"],
            "custodian_decision": decision, "custodian_criteria": row["criteria"],
            "custodian_selected_version": version, "rationale": row["scientific_rationale"],
            "original_b_unchanged": True})
        if decision == "UNCLEAR":
            requests.append({"review_id": rid, "work_id": row["work_id"],
                "selected_version_id": version, "specific_missing_components": unresolved,
                "existing_method_evidence_ids": row["considered_method_evidence_ids"],
                "request_boundary": "Primary method/dataset/bibliography only; no outcomes, counts or assurance classification. Missing evidence is not exclusion.",
                "context": row["scientific_rationale"]})
    counts = collections.Counter(r["decision"] for r in out)
    summary = {"status": "FRAME_BLOCKED", "deliverable": "CUSTODIAN_ADJUDICATED_PROPOSAL_WITH_UNCERTAINTIES",
        "source_git_commit": source_head, "works": len(out), "memberships": sum(len(r["memberships"]) for r in out),
        "counts": dict(counts), "all_four_domain_supported": sum(set(r["criteria"].values()) == {"MET"} for r in out),
        "global_frame_clearance": False, "sampling_authorized": False, "b2_authorized": False,
        "independent_final_review_claimed": False, "assurance_outcomes_extracted": False,
        "not_frame_insufficient": "Unresolved works are not exclusions; the ultimate eligible count has not been determined.",
        "unresolved_component_counts": dict(collections.Counter(k for r in requests for k in r["specific_missing_components"]))}
    return {"CUSTODIAN_FRAME_PROPOSAL.json": {"summary": summary, "rows": out},
            "REVIEWER_B_RECONCILIATION.json": {"rows": changes},
            "REMAINING_CONTROLLED_QUESTIONS.json": {"requests": requests},
            "PROPOSAL_VALIDATION.json": summary}


def main() -> None:
    """Write a new proposal once or verify exact deterministic replay."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        head = a.clean_head()
    else:
        head = json.loads((HERE / "PROPOSAL_VALIDATION.json").read_bytes())["source_git_commit"]
    outputs = assemble(head)
    for name, value in outputs.items():
        raw = a.encoded(value)
        if args.write:
            with (HERE / name).open("xb") as stream:
                stream.write(raw)
        elif (HERE / name).read_bytes() != raw:
            raise ValueError("PROPOSAL_REPLAY_CHANGED:" + name)
    print(json.dumps(outputs["PROPOSAL_VALIDATION.json"], sort_keys=True))


if __name__ == "__main__":
    main()
