"""Release exact, separately checked method fields without promoting held prose."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parents[5] / "fpr-a05-deep-20261024"


def encoded(value: object) -> bytes:
    """Use deterministic, reviewable bytes for facts and receipts."""
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode()


def sha(raw: bytes) -> str:
    """Bind each approval to the precise provider/checker bytes."""
    return hashlib.sha256(raw).hexdigest()


def field(packet: dict, path: str) -> object:
    """Resolve only declared method fields; never evaluate a supplied expression."""
    if path in {"method_summary", "english_evaluation_support", "study_scope_statement", "coverage",
                "clarification_scope", "input_unit_and_dependency"}:
        return packet[path]
    match = re.fullmatch(r"bounded_method_data_facts\[(\d+)\]", path)
    if match:
        return packet["bounded_method_data_facts"][int(match[1])]
    if path in {"source_receipts.locators", "source_receipts.additional_table_locators"}:
        return packet["source_receipts"][path.rsplit(".", 1)[1]]
    if path in {"architecture_clarification.verdict_context", "architecture_clarification.call_boundary_limit"}:
        return packet["architecture_clarification"][path.rsplit(".", 1)[1]]
    match = re.fullmatch(r"additional_primary_method_images\[(\d+)\]", path)
    if match:
        return packet["additional_primary_method_images"][int(match[1])]
    match = re.fullmatch(r"arm_inventory\[(\d+)\]", path)
    if match:
        return packet["arm_inventory"][int(match[1])]
    match = re.fullmatch(r"coverage\.([a-z_]+)", path)
    if match:
        return packet["coverage"][match[1]]
    match = re.fullmatch(r"bibliographic_scope_facts\.(title|author|authors|document_type|whole_document_scope|edition|source_declared_relationship)", path)
    if match:
        return packet["bibliographic_scope_facts"][match[1]]
    raise ValueError("UNRELEASEABLE_FIELD:" + path)


def checked_fields(check: dict, packet: dict, packet_raw: bytes) -> list[dict]:
    """Reject changed drafts, self-checks and mismatched identities before release."""
    provider = packet.get("provider_actor") or packet.get("provider", {}).get("actor")
    if not provider or not check.get("actor") or provider == check["actor"]:
        raise ValueError("SEPARATE_ACTUAL_ACTORS_REQUIRED")
    if sha(packet_raw) != check["provider_packet_sha256"]:
        raise ValueError("PROVIDER_CHANGED_AFTER_CHECK")
    if packet["review_id"] != check["review_id"]:
        raise ValueError("FOREIGN_WORK")
    mechanical = check["mechanical_check"]
    restriction = check["restriction_check"]
    eligibility = restriction.get("eligibility_judgments_transferred", restriction.get("eligibility_or_canonical_merge_transferred"))
    if restriction.get("outcomes_transferred") is not False or eligibility is not False:
        raise ValueError("RESTRICTION_FAILURE")
    if mechanical.get("raw_body_available") is False and mechanical.get("acquisition_hash_verified"):
        # An authenticated access gap must not become a scientific method fact.
        return []
    if (not mechanical.get("raw_hash_verified") or not mechanical.get("acquisition_hash_verified")
            or mechanical.get("provider_locator_mismatches")):
        raise ValueError("SOURCE_BINDING_NOT_VERIFIED")
    result = []
    seen = set()
    for row in check["per_fact"]:
        if row["decision"] != "APPROVE":
            continue
        path = row["field_path"]
        if path in {"request_provenance", "exact_version_validation"}:
            continue  # Retained in the exact checker receipt, not method prose.
        if path in seen:
            raise ValueError("DUPLICATE_APPROVAL")
        seen.add(path)
        value = field(packet, path)
        result.append({"field_path": path, "value": value, "value_sha256": sha(encoded(value)),
                       "semantic_check": row["semantic_fidelity"],
                       "restriction_check": row["restriction_rationale"],
                       "provider_actor": provider, "checker_actor": check["actor"]})
    return result


def build(checkpoint_path: Path, requests_path: Path | None = None) -> tuple[dict, dict[str, bytes]]:
    """Freeze a sealed checker checkpoint without reading unapproved method values."""
    checkpoint_raw = checkpoint_path.read_bytes()
    checkpoint = json.loads(checkpoint_raw)
    requests_raw = (requests_path or HERE / "SOURCE_REQUESTS.json").read_bytes()
    requests = json.loads(requests_raw)
    if isinstance(requests, dict):
        requests = requests["requests"]
    inventory = {r["review_id"]: r for r in requests}
    pins = {r["path"]: r["sha256"] for r in checkpoint["files"]}
    files = {"CHECKER_CHECKPOINT.json": checkpoint_raw}
    facts = []
    access_only = []
    latest = checkpoint.get("latest_receipts")
    if latest is None:
        latest = {}
        for relative, pin in pins.items():
            raw = (checkpoint_path.parent / relative).read_bytes()
            if sha(raw) != pin:
                raise ValueError("CHECKPOINT_FILE_CHANGED")
            rid = json.loads(raw)["review_id"]
            if rid in latest:
                raise ValueError("AMBIGUOUS_LATEST_CHECKER_RECEIPT")
            latest[rid] = relative
    for rid, relative in sorted(latest.items()):
        raw = (checkpoint_path.parent / relative).read_bytes()
        if sha(raw) != pins[relative]:
            raise ValueError("CHECKPOINT_FILE_CHANGED")
        check = json.loads(raw)
        if rid != check["review_id"] or check["request_sha256"] != sha(requests_raw):
            raise ValueError("REQUEST_OR_ID_CHANGED")
        request = inventory[rid]
        if check["requested_preferred_version"] != request["requested_preferred_version"]:
            raise ValueError("REQUESTED_VERSION_CHANGED")
        packet_raw = Path(check["provider_packet"]).read_bytes()
        packet = json.loads(packet_raw)
        if packet["work_id"] != request["work_id"]:
            raise ValueError("WORK_ID_CHANGED")
        released = checked_fields(check, packet, packet_raw)
        receipt_name = "checker/" + Path(relative).name
        files[receipt_name] = raw
        if not released:
            access_only.append({"review_id": rid, "checker_receipt": receipt_name,
                                "checker_receipt_sha256": sha(raw), "source_identity": check["source_identity"],
                                "status": "ACCESS_RECORD_ONLY_NO_METHOD_EVIDENCE"})
        for n, item in enumerate(released, 1):
            facts.append({"evidence_id": "A05-DEEP-" + rid + "-" + sha(raw)[:12] + "-F" + str(n).zfill(2),
                          "review_id": rid, "work_id": request["work_id"],
                          "version": check["requested_preferred_version"],
                          "source_identity": check["source_identity"],
                          "provider_packet_sha256": sha(packet_raw),
                          "checker_receipt": receipt_name, "checker_receipt_sha256": sha(raw),
                          "coverage_disposition": check["actual_context_check"].get("coverage_disposition", "BIBLIOGRAPHIC_SCOPE_ONLY"),
                          "release_status": ("CHECKED_BIBLIOGRAPHIC_SCOPE_NOT_ELIGIBILITY" if item["field_path"].startswith("bibliographic_scope_facts.")
                                             else "CHECKED_METHOD_FIELD_NOT_ELIGIBILITY"),
                          **({"clarification_scope": packet["clarification_scope"]} if "clarification_scope" in packet else {}), **item})
    return {"schema": "A05_DEEP_CHECKED_METHOD_RELEASE_v1",
            "request_sha256": sha(requests_raw), "checkpoint_sha256": sha(checkpoint_raw),
            "released_by": "EXPOSED_CUSTODIAN_ROOT", "facts": facts, "access_only_records": access_only,
            "source_files": {name: sha(raw) for name, raw in files.items()},
            "limits": ["Only individually approved fields are released. Held fields and unapproved coverage are not evidence.",
                       "Requested version is retained; source identity/binding limits must be assessed separately.",
                       "Actual source-role separation on shared filesystem; no fresh independent final eligibility review.",
                       "No outcomes, sample/false-positive counts, assurance classes, draw, assignment or B2."]}, files


def main() -> None:
    """Create one append-only release from a clean committed generator."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--requests", type=Path)
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{3}", args.run):
        raise ValueError("BAD_RUN_NAME")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=HERE, text=True).strip():
        raise ValueError("DIRTY_TREE")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    release, files = build(args.checkpoint, args.requests)
    release["source_git_commit"] = head
    destination = HERE / "releases" / args.run
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (destination / "FACTS.json").write_bytes(encoded(release))
    print(json.dumps({"run": args.run, "facts": len(release["facts"]),
                      "works": len({r["review_id"] for r in release["facts"]}), "source_git_commit": head}))


if __name__ == "__main__":
    main()
