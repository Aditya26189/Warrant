"""Apply append-only administrative B1 repairs without eligibility adjudication."""
from __future__ import annotations

import argparse
import calendar
import collections
import copy
import datetime as dt
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "a04-reviewer-returns-20261022"
COMPANION_PIN = "7466fa2253358b24917b93b24a4214e3b42103c7f7d994006a9efaa6ad7a43ed"
WRAPPER_PIN = "d105eed48c37e6532776060b3aec4ab70ece3cad885d1555ce08d54c89cf5142"
REVIEW_B_PIN = "b8d9352eb67b69765497b09818184f022127ffc79216495cea61cc096ef54fe7"
CRITERIA = ("input_injection_task", "binary_evaluation", "before_target_answer", "english_evaluation")
DATE_FIELDS = {"first_public_date", "version_date"}


def encoded(value: object) -> bytes:
    """Preserve the canonical hash convention of the original evidence releases."""
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode()


def sha(raw: bytes) -> str:
    """Return the commitment for original or derived bytes."""
    return hashlib.sha256(raw).hexdigest()


def archive(raw: bytes, pin: str | None = None, manifest: str | None = None) -> dict[str, bytes]:
    """Require pinned custody bytes and safe unique entries before parsing."""
    if pin and sha(raw) != pin:
        raise ValueError("ARCHIVE_PIN_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
        names = zipped.namelist()
        if len(names) != len(set(names)) or any(n.startswith(("/", "\\")) or ":" in n
                or ".." in n.replace("\\", "/").split("/") for n in names):
            raise ValueError("UNSAFE_ARCHIVE_NAMES")
        if zipped.testzip() is not None:
            raise ValueError("ARCHIVE_CRC_FAILURE")
        files = {n: zipped.read(n) for n in names}
    if manifest:
        declared = json.loads(files[manifest])["files"]
        if set(files) != set(declared) | {manifest} or any(sha(files[n]) != digest for n, digest in declared.items()):
            raise ValueError("MANIFEST_MISMATCH")
    return files


def interval(value: str | None) -> tuple[str, str] | None:
    """Keep month uncertainty instead of manufacturing a publication day."""
    if not value:
        return None
    if not re.fullmatch(r"\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?", value):
        return None
    parts = [int(x) for x in re.split(r"[-/]", value)]
    try:
        start = dt.date(*parts) if len(parts) == 3 else dt.date(parts[0], parts[1], 1)
        end = start if len(parts) == 3 else dt.date(parts[0], parts[1], calendar.monthrange(*parts)[1])
    except ValueError:
        return None
    return start.isoformat(), end.isoformat()


def display(bounds: tuple[str, str]) -> str | None:
    """Return a day or a whole month; retain a partial-month interval separately."""
    low, high = bounds
    if low == high:
        return low
    month = low[:7]
    return month if interval(month) == bounds else None


def arxiv_id(value: str) -> str | None:
    """Bind revision histories to the actual selected arXiv identifier."""
    match = re.search(r"(?:arxiv:|arxiv\.org/(?:abs|html|pdf)/)(\d{4}\.\d{4,5})", value)
    return match.group(1) if match else None


def version_basis(selected: str | None, records: list[dict]) -> tuple[tuple[str, str], list[str]] | None:
    """Use only the selected version's unique official date evidence."""
    candidates = []
    for record in records:
        fields = record["official_fields"]
        url = record["provenance"]["source_url"]
        if selected and selected.startswith("arxiv:") and arxiv_id(url) == arxiv_id(selected):
            revision = re.search(r"v\d+$", selected)
            if revision:
                for row in fields["revision_history"]:
                    if row["revision"] == revision.group():
                        candidates.append(((row["public_utc"][:10],) * 2, record["evidence_id"]))
        elif selected and selected.startswith("acl:"):
            identifier = selected.removeprefix("acl:").removesuffix(":publication")
            if url.rstrip("/").endswith("/" + identifier):
                for row in fields["publication_date_literals"]:
                    bounds = interval(row["value"])
                    if bounds:
                        candidates.append((bounds, record["evidence_id"]))
    unique = {bounds for bounds, _ in candidates}
    if len(unique) != 1:
        return None
    return unique.pop(), sorted({eid for _, eid in candidates})


def first_public_basis(records: list[dict]) -> tuple[tuple[str, str], list[str]] | None:
    """Bound earliest documented release; this does not settle unknown earlier VORs."""
    candidates = []
    for record in records:
        fields = record["official_fields"]
        if arxiv_id(record["provenance"]["source_url"]):
            for row in fields["revision_history"]:
                candidates.append(((row["public_utc"][:10],) * 2, record["evidence_id"]))
        else:
            for row in fields["publication_date_literals"]:
                bounds = interval(row["value"])
                if bounds:
                    candidates.append((bounds, record["evidence_id"]))
    if not candidates:
        return None
    bounds = min(x[0][0] for x in candidates), min(x[0][1] for x in candidates)
    return bounds, sorted({eid for _, eid in candidates})


def repair_rows(rows: list[dict], official: list[dict]) -> tuple[list[dict], list[dict]]:
    """Correct source-supported date fields and leave every review decision intact."""
    repaired = copy.deepcopy(rows)
    changes = []
    for old, row in zip(rows, repaired, strict=True):
        records = [x for x in official if x["review_id"] == row["review_id"]]
        bases = {"version_date": version_basis(row["selected_version_id"], records),
                 "first_public_date": first_public_basis(records)}
        for field, basis in bases.items():
            if basis is None:
                continue
            bounds, evidence_ids = basis
            if interval(row[field]) == bounds:
                continue
            value = display(bounds)
            changes.append({"review_id": row["review_id"], "work_id": row["work_id"], "field": field,
                            "before": row[field], "after": value, "supported_interval": list(bounds),
                            "evidence_ids": evidence_ids, "original_row_sha256": sha(encoded(old)),
                            "basis": "SELECTED_VERSION_PRIMARY_DATE" if field == "version_date" else "EARLIEST_DOCUMENTED_PRIMARY_PUBLIC_RELEASE",
                            "not_an_eligibility_or_preferred_version_decision": True})
            row[field] = value
        if {k for k in old if old[k] != row[k]} - DATE_FIELDS:
            raise ValueError("NONADMINISTRATIVE_FIELD_CHANGED")
    return repaired, changes


def validate_intake(intake: dict, freeze: dict, rows: list[dict]) -> dict:
    """Accept original recorded declarations without fabricating personal-history proof."""
    required = ("independent_human_outcome_sheet_unseen", "previous_assistant_judgments_unseen",
                "restricted_evidence_process_confirmed", "result_bearing_source_displays_unseen",
                "separate_empty_workspace_confirmed")
    valid = (intake["status"] == "ATTESTED" and all(intake.get(k) is True for k in required)
             and intake["package_sha256_received_out_of_band"] == WRAPPER_PIN
             and freeze["archive_transfer_sha256_verified"] == WRAPPER_PIN
             and intake["reviewer_id"] == freeze["reviewer_id"]
             and not intake["previously_familiar_work_ids_for_reassignment"]
             and all(dt.datetime.fromisoformat(intake["attested_utc"].replace("Z", "+00:00"))
                     <= dt.datetime.fromisoformat(row["reviewed_utc"].replace("Z", "+00:00")) for row in rows))
    return {"original_recorded_attestation_accepted": valid,
            "recorded_pre_review_attested_utc": intake["attested_utc"],
            "reviewer_id": intake["reviewer_id"], "reviewer_reports_expected_outer_digest_verified": True,
            "personal_history_independently_observable_by_custodian": False,
            "scientific_frame_completion_inferred_from_attestation": False}


def build() -> dict[str, object]:
    """Validate the full companion and generate traceable administrative working data."""
    companion = archive((HERE / "INDEPENDENT_REVIEWER_B1_RETURN.zip").read_bytes(), COMPANION_PIN, "FREEZE_MANIFEST.json")
    exported = archive((PREVIOUS / "ELIGIBILITY_REVIEWS.zip").read_bytes(), REVIEW_B_PIN)
    if companion["ELIGIBILITY_REVIEW.json"] != exported["ELIGIBILITY_REVIEW.json"]:
        raise ValueError("COMPANION_NOT_REVIEW_B")
    wrapper_path = HERE.parent / "a04-provisional-recovery-v1-20261021/REVIEWER_RECOVERY_TRANSFER.zip"
    wrapper = archive(wrapper_path.read_bytes(), WRAPPER_PIN, "MANIFEST.json")
    sources = {name: archive(wrapper[name], manifest="MANIFEST.json") for name in (
        "FRESH_REVIEWER_INTAKE.zip", "CONSOLIDATED_RESTRICTED_EVIDENCE.zip", "RECOVERY_CONTROLLED_EVIDENCE.zip")}
    intake_files = sources["FRESH_REVIEWER_INTAKE.zip"]
    inventory = json.loads(intake_files["CANDIDATE_INVENTORY.json"])
    recovery = sources["RECOVERY_CONTROLLED_EVIDENCE.zip"]
    official = json.loads(recovery["OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json"])
    facts = (json.loads(sources["CONSOLIDATED_RESTRICTED_EVIDENCE.zip"]["SEMANTIC_METHOD_FACTS.json"])
             + json.loads(recovery["RECOVERY_METHOD_FACTS.json"]))
    facts_by_id = {x["evidence_id"]: x for x in facts}
    rows = json.loads(companion["ELIGIBILITY_REVIEW.json"])
    by_id = {x["review_id"]: x for x in rows}
    if len(rows) != 372 or len(by_id) != 372 or any(by_id[x["review_id"]]["work_id"] != x["work_id"] for x in inventory):
        raise ValueError("ORIGINAL_INVENTORY_MISMATCH")
    receipts = json.loads(companion["EVIDENCE_RECEIPTS.json"])
    if len(receipts) != len(facts) or {x["evidence_id"] for x in receipts} != set(facts_by_id):
        raise ValueError("COMPANION_RECEIPT_COVERAGE")
    for receipt in receipts:
        source = facts_by_id[receipt["evidence_id"]]
        if (receipt["restricted_evidence_sha256"] != sha(encoded(source))
                or any(receipt[k] != source[k] for k in ("source_url", "version", "raw_source_sha256"))
                or receipt["method_dataset_or_bibliographic_locator"] != source["locator"]
                or source["work_id"] not in receipt["work_ids"] or not receipt["reviewer_received_utc"]):
            raise ValueError("COMPANION_RECEIPT_SOURCE_MISMATCH")
    if {eid for row in rows for eid in row["evidence_ids"]} - set(facts_by_id):
        raise ValueError("REVIEW_B_UNRECEIPTED_CITATION")
    requests = json.loads(companion["CONTROLLED_REQUESTS_RETURN.json"])
    unclear = {x["review_id"] for x in rows if x["decision"] == "UNCLEAR"}
    if len(requests) != len(unclear) or {x["review_id"] for x in requests} != unclear:
        raise ValueError("COMPANION_REQUEST_WORK_COVERAGE")
    for request in requests:
        row = by_id[request["review_id"]]
        criteria = {k for k in CRITERIA if row[k] == "UNCLEAR"}
        if (request["work_id"] != row["work_id"] or set(request["unresolved_criteria"]) != criteria
                or {x["criterion"] for x in request["specific_evidence_needed"]} != criteria):
            raise ValueError("COMPANION_REQUEST_CRITERION_COVERAGE")
    intake = json.loads(companion["REVIEWER_INTAKE.json"])
    attestation = validate_intake(intake, json.loads(companion["FREEZE_MANIFEST.json"]), rows)
    repaired, changes = repair_rows(rows, official)
    working = {"status": "ADMINISTRATIVELY_REPAIRED_NOT_A_FROZEN_ELIGIBILITY_FRAME", "sampling_authorized": False,
               "original_reviewer_decisions_preserved": True, "rows": repaired,
               "date_interpretation": "Primary-source administrative dates; first_public_date means earliest documented release, without ruling out unknown earlier VORs. Partial-month bounds are in the change log.",
               "original_work_memberships": [{"review_id": x["review_id"], "work_id": x["work_id"],
                                               "member_ids": [m["member_id"] for m in x["members"]]} for x in inventory]}
    routed = []
    request_by_id = {x["review_id"]: x for x in requests}
    for row in rows:
        if row["review_id"] not in request_by_id:
            continue
        released = [x for x in facts if x["work_id"] == row["work_id"]]
        routed.append({"review_id": row["review_id"], "work_id": row["work_id"],
                       "original_reviewer_request": request_by_id[row["review_id"]],
                       "already_released_method_references": [{"evidence_id": x["evidence_id"], "fact_kind": x["fact_kind"],
                                                               "source_url": x["source_url"], "version": x["version"]} for x in released],
                       "routing_is_not_evidence_of_criterion_satisfaction_or_absence": True})
    validation = {"status": "PASS", "companion_manifest": "PASS", "review_B_array_byte_identical": True,
                  "intake": attestation, "receipt_count": len(receipts), "receipts_match_released_facts": True,
                  "cited_method_ids_without_receipts": [], "request_works": len(requests),
                  "request_criterion_items": sum(len(x["specific_evidence_needed"]) for x in requests),
                  "original_reviewer_frame_completed_claim": json.loads(companion["FREEZE_MANIFEST.json"])["independent_review_completed"],
                  "validated_final_eligibility_frame": False}
    checks = {"works": len(rows), "memberships": sum(len(x["members"]) for x in inventory),
              "original_decision_counts": dict(collections.Counter(x["decision"] for x in rows)),
              "repaired_decision_counts": dict(collections.Counter(x["decision"] for x in repaired)),
              "date_field_changes": len(changes), "changed_works": len({x["review_id"] for x in changes}),
              "changes_by_field": dict(collections.Counter(x["field"] for x in changes)),
              "only_allowed_date_fields_changed": all({k for k in old if old[k] != new[k]} <= DATE_FIELDS
                                                      for old, new in zip(rows, repaired, strict=True)),
              "selected_versions_criteria_and_eligibility_unchanged": True, "gate": "FRAME_BLOCKED",
              "draw_performed": False, "B2_authorized": False, "historical_custodian_judgments_accessed": False}
    return {"COMPANION_VALIDATION.json": validation, "REPAIRED_B_WORKING_COPY.json": working,
            "ADMINISTRATIVE_CHANGE_LOG.json": changes, "REMAINING_REVIEW_WORKLIST.json": routed,
            "REPAIR_CHECKS.json": checks}


def main() -> None:
    """Freeze derived working files only from committed, clean repair code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    if args.write and subprocess.check_output(["git", "status", "--porcelain"], cwd=HERE, text=True):
        raise SystemExit("CLEAN_TREE_REQUIRED")
    outputs = build()
    if args.write:
        if any((HERE / name).exists() for name in outputs) or (HERE / "REPAIR_MANIFEST.json").exists():
            raise SystemExit("APPEND_ONLY_OUTPUT_ALREADY_EXISTS")
        raw = {name: encoded(value) for name, value in outputs.items()}
        manifest = {"source_head": head, "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "files": {name: sha(data) for name, data in raw.items()}, "gate": "FRAME_BLOCKED"}
        for name, data in raw.items():
            (HERE / name).write_bytes(data)
        (HERE / "REPAIR_MANIFEST.json").write_bytes(encoded(manifest))
    print(json.dumps({"companion": outputs["COMPANION_VALIDATION.json"], "checks": outputs["REPAIR_CHECKS.json"]}, sort_keys=True))


if __name__ == "__main__":
    main()
