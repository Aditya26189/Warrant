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
    if path in {"method_summary", "english_evaluation_support", "coverage"}:
        return packet[path]
    match = re.fullmatch(r"arm_inventory\[(\d+)\]", path)
    if match:
        return packet["arm_inventory"][int(match[1])]
    match = re.fullmatch(r"coverage\.([a-z_]+)", path)
    if match:
        return packet["coverage"][match[1]]
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
    if (not mechanical.get("raw_hash_verified") or not mechanical.get("acquisition_hash_verified")
            or mechanical.get("provider_locator_mismatches")):
        raise ValueError("SOURCE_BINDING_NOT_VERIFIED")
    if check["restriction_check"]["outcomes_transferred"] or check["restriction_check"]["eligibility_judgments_transferred"]:
        raise ValueError("RESTRICTION_FAILURE")
    result = []
    seen = set()
    for row in check["per_fact"]:
        if row["decision"] != "APPROVE":
            continue
        path = row["field_path"]
        if path in seen:
            raise ValueError("DUPLICATE_APPROVAL")
        seen.add(path)
        value = field(packet, path)
        result.append({"field_path": path, "value": value, "value_sha256": sha(encoded(value)),
                       "semantic_check": row["semantic_fidelity"],
                       "restriction_check": row["restriction_rationale"],
                       "provider_actor": provider, "checker_actor": check["actor"]})
    return result


def build(checkpoint_path: Path) -> tuple[dict, dict[str, bytes]]:
    """Freeze a sealed checker checkpoint without reading unapproved method values."""
    checkpoint_raw = checkpoint_path.read_bytes()
    checkpoint = json.loads(checkpoint_raw)
    requests_raw = (HERE / "SOURCE_REQUESTS.json").read_bytes()
    requests = json.loads(requests_raw)
    if isinstance(requests, dict):
        requests = requests["requests"]
    inventory = {r["review_id"]: r for r in requests}
    pins = {r["path"]: r["sha256"] for r in checkpoint["files"]}
    files = {"CHECKER_CHECKPOINT.json": checkpoint_raw}
    facts = []
    for rid, relative in sorted(checkpoint["latest_receipts"].items()):
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
        for n, item in enumerate(released, 1):
            facts.append({"evidence_id": "A05-DEEP-" + rid + "-" + sha(raw)[:12] + "-F" + str(n).zfill(2),
                          "review_id": rid, "work_id": request["work_id"],
                          "version": check["requested_preferred_version"],
                          "source_identity": check["source_identity"],
                          "provider_packet_sha256": sha(packet_raw),
                          "checker_receipt": receipt_name, "checker_receipt_sha256": sha(raw),
                          "coverage_disposition": check["actual_context_check"]["coverage_disposition"],
                          "release_status": "CHECKED_METHOD_FIELD_NOT_ELIGIBILITY", **item})
    return {"schema": "A05_DEEP_CHECKED_METHOD_RELEASE_v1",
            "request_sha256": sha(requests_raw), "checkpoint_sha256": sha(checkpoint_raw),
            "released_by": "EXPOSED_CUSTODIAN_ROOT", "facts": facts,
            "source_files": {name: sha(raw) for name, raw in files.items()},
            "limits": ["Only individually approved fields are released. Held fields and unapproved coverage are not evidence.",
                       "Requested version is retained; source identity/binding limits must be assessed separately.",
                       "Actual source-role separation on shared filesystem; no fresh independent final eligibility review.",
                       "No outcomes, sample/false-positive counts, assurance classes, draw, assignment or B2."]}, files


def main() -> None:
    """Create one append-only release from a clean committed generator."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{3}", args.run):
        raise ValueError("BAD_RUN_NAME")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=HERE, text=True).strip():
        raise ValueError("DIRTY_TREE")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    release, files = build(args.checkpoint)
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
