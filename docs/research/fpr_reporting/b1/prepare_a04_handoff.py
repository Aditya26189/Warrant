"""Project frozen bibliography into a restricted fresh-reviewer intake.

This custodian utility performs no eligibility decisions, research retrieval or
sampling. Its explicit field/file allowlists prevent historical judgments and
source prose from being propagated into the reviewer package.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
CHECKPOINT = "03834a066981d5d01869d959aa4e0aacace125d4"
AMENDMENT_COMMIT = "651dd24"
WORKS = "a02-human-batch001/WORK_RECORDS.json"
METADATA = "a02-metadata/metadata_union.jsonl"
SENTINELS = "SENTINEL_INVENTORY_AMENDED.json"
PINNED = {
    WORKS: "dce32691f348356c587f3cbd4ea03637a0af59974b87ae24cf238e6d72cdf34c",
    METADATA: "dea23a8f9198e3ecefd71ab92c91b0680a7b0cfe97f59119880997cfba69b808",
    SENTINELS: "dafd88a2eb9e904054dd4dd0eeb579e9e8acabae8bc7062d49ca0355855ed69f",
    "PROTOCOL_LOCK_A03.json": "0c11c681b6f08fdf3a1e34a26675f157be79e757ba6d9f55cd7f7cc85689f4f0",
}
PROTOCOL = (
    "APPROVED_FRAME_SOURCE.md", "AMENDMENT_A01_SENTINEL_EXCLUSIONS.md",
    "AMENDMENT_A02_RETRIEVAL_SCOPE.md", "AMENDMENT_A03_ASSISTANT_METHOD_REVIEW.md",
    "AMENDMENT_A04_FRESH_REVIEWER_PATH.md", "PROTOCOL_LOCK_A02.json",
    "PROTOCOL_LOCK_A03.json", SENTINELS,
)
STATIC = (
    "READ_FIRST.md", "ELIGIBILITY_RULES.md", "BIBLIOGRAPHIC_CONSTRAINTS.json",
    "REVIEWER_INTAKE_BLANK.json", "EVIDENCE_RECEIPT_BLANK.json", "verify_package.py",
)
REVIEW_FIELDS = (
    "decision", "input_injection_task", "binary_evaluation", "before_target_answer",
    "english_evaluation", "first_public_date", "selected_version_id", "version_date",
    "version_preference_basis", "sentinel_check", "identity_reconciliation",
    "access_status", "evidence_ids", "method_bibliographic_locators", "limitations",
    "reviewer_id", "reviewed_utc",
)


def canonical(value: object) -> bytes:
    """Serialize commitments reproducibly without carrying source prose."""
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode()


def digest(value: bytes) -> str:
    """Compute the exact-byte SHA-256 commitment."""
    return hashlib.sha256(value).hexdigest()


def project(works: list, metadata: list, sentinels: list) -> tuple[list, list, list, list]:
    """Allowlist bibliography only, retaining every original work/member."""
    indexed = {}
    member_ids = {}
    crosswalk = []
    for number, row in enumerate(metadata, 1):
        key = (row["source"], row["source_id"])
        if key in indexed or row["source"] not in {"arxiv", "acl"}:
            raise ValueError("Repeated or out-of-frame source record")
        indexed[key] = row
        member_ids[key] = f"M{number:04d}"
    inventory, reviews, used = [], [], []
    for number, work in enumerate(sorted(works, key=lambda w: w["work_id"]), 1):
        members = []
        for member in work["members"]:
            key = (member["source"], member["source_id"])
            row = indexed[key]
            used.append(key)
            version = re.fullmatch(r"https?://arxiv.org/abs/(\d{4}\.\d{4,5}v\d+)", key[1])
            members.append({
                "member_id": member_ids[key], "source": key[0],
                "captured_version_id": f"arxiv:{version[1]}" if version else None,
                **{field: row.get(field) for field in ("doi", "published", "updated", "year", "month")},
                "metadata_record_sha256": digest(canonical(row)),
                "title_sha256": digest(row["title"].encode("utf-8")),
                "normalized_title_sha256": digest(row["normalized_title"].encode("utf-8")),
            })
        identity = {"review_id": f"W{number:04d}", "work_id": work["work_id"]}
        inventory.append({**identity, "identifiers": work["identifiers"], "members": members})
        reviews.append({**identity, **dict.fromkeys(REVIEW_FIELDS)})
        crosswalk.append({**identity, "source_members": work["members"]})
    if len(used) != len(set(used)) or set(used) != set(indexed):
        raise ValueError("Incomplete or repeated source-to-work membership")
    restricted_sentinels = [{
        "work_id": s["work_id"], "exclude_versions": s["exclude_versions"],
        "frozen_label_sha256": digest(s["title_or_context_label"].encode("utf-8")),
        "source_urls_sha256": digest(canonical(s["source_urls"])),
    } for s in sentinels]
    return inventory, reviews, restricted_sentinels, crosswalk


def git(*args: str) -> str:
    """Run read-only Git provenance checks in the research worktree."""
    return subprocess.check_output(["git", *args], cwd=BASE, text=True).strip()


def prepare() -> None:
    """Build once on a clean committed tree; retain old evidence unchanged."""
    if git("status", "--porcelain"):
        raise RuntimeError("Commit preparation sources before generating handoff artifacts")
    for name, expected in PINNED.items():
        if digest((BASE / name).read_bytes()) != expected:
            raise ValueError(f"Frozen input mismatch: {name}")
    for lock_name in ("PROTOCOL_LOCK_A02.json", "PROTOCOL_LOCK_A03.json"):
        lock = json.loads((BASE / lock_name).read_text(encoding="utf-8"))
        for name, expected in lock["files"].items():
            if digest((BASE / name).read_bytes()) != expected:
                raise ValueError(f"Historical lock mismatch: {name}")
    historical_names = git("ls-tree", "-r", "--name-only", CHECKPOINT, "--", ".").splitlines()
    historical_changes = git("diff", "--name-status", "--diff-filter=DMRTUXB", CHECKPOINT, "--", ".")
    if historical_changes:
        raise ValueError("Historical B1 artifact changed: " + historical_changes)
    source = BASE / "a04-handoff-source"
    output = BASE / "a04-handoff"
    if output.exists() or (BASE / "PROTOCOL_LOCK_A04.json").exists():
        raise FileExistsError("Do not overwrite a generated/frozen handoff")
    works = json.loads((BASE / WORKS).read_text(encoding="utf-8"))
    metadata = [json.loads(line) for line in (BASE / METADATA).read_text(encoding="utf-8").splitlines()]
    sentinels = json.loads((BASE / SENTINELS).read_text(encoding="utf-8"))["work_exclusions"]
    inventory, reviews, restricted_sentinels, crosswalk = project(works, metadata, sentinels)
    historical_ledger = json.loads((BASE / "a03-review-stop/SCREENING_LEDGER.json").read_text(encoding="utf-8"))
    if {w["work_id"] for w in works} != {w["work_id"] for w in historical_ledger}:
        raise ValueError("Independent inventory does not cover the entire historical ledger")
    head = git("rev-parse", "HEAD")
    created = datetime.now(timezone.utc).isoformat()
    protocol_hashes = {name: digest((BASE / name).read_bytes()) for name in PROTOCOL}
    files = {name: (source / name).read_bytes() for name in STATIC}
    files.update({
        "CANDIDATE_INVENTORY.json": canonical(inventory),
        "ELIGIBILITY_REVIEW_BLANK.json": canonical(reviews),
        "SENTINEL_IDENTIFIERS.json": canonical(restricted_sentinels),
    })
    manifest = {
        "created_utc": created, "source_git_commit": head, "source_tree_clean_at_start": True,
        "protocol_sha256": protocol_hashes, "files": {k: digest(v) for k, v in sorted(files.items())},
        "independent_review": "NOT_STARTED", "reviewer_assignment": "UNASSIGNED", "draw": "BLOCKED",
        "work_count": len(inventory), "source_member_count": len(metadata), "sentinel_count": len(sentinels),
        "restrictions": "BIBLIOGRAPHY_ONLY_NO_PRIOR_JUDGMENTS_NO_PRIMARY_PROSE",
    }
    files["MANIFEST.json"] = canonical(manifest)
    restricted = output / "restricted"
    restricted.mkdir(parents=True)
    for name, content in files.items():
        (restricted / name).write_bytes(content)
    checked = subprocess.check_output([sys.executable, str(restricted / "verify_package.py")], text=True)
    archive = output / "FRESH_REVIEWER_INTAKE.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as target:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(info, content)
    with zipfile.ZipFile(archive) as packaged:
        if set(packaged.namelist()) != set(files) or len(packaged.namelist()) != len(files):
            raise ValueError("Archive member allowlist mismatch")
        for name, content in files.items():
            if packaged.read(name) != content:
                raise ValueError("Archive byte mismatch")
    if archive.stat().st_size >= 10_000_000:
        raise ValueError("Archive exceeds repository staging limit")
    receipt = {
        "created_utc": created, "source_git_commit": head,
        "amendment_commit": git("rev-parse", AMENDMENT_COMMIT),
        "historical_checkpoint": CHECKPOINT, "historical_b1_files_preserved": len(historical_names),
        "historical_modified_deleted_or_renamed_files": [], "frozen_locks_checked": ["A02", "A03"],
        "raw_input_sha256": PINNED, "protocol_sha256": protocol_hashes,
        "package_sha256": digest(archive.read_bytes()), "package_bytes": archive.stat().st_size,
        "package_manifest_sha256": digest(files["MANIFEST.json"]),
        "standalone_integrity_check": json.loads(checked),
        "all_372_previous_ledger_ids_covered": True,
        "previous_assistant_events_preserved": 42, "previous_assistant_works_to_reassess": 41,
        "previous_unresolved_domain_questions_to_adjudicate": 115,
        "reviewer_assignment": "UNASSIGNED", "independent_review": "NOT_STARTED",
        "evidence_intake_provider": "UNASSIGNED", "gate": "FRAME_BLOCKED",
        "draw_executed": False, "B2": "NOT_AUTHORIZED", "source_refresh": False,
        "title_and_abstract_display": "UNIFORMLY_WITHHELD_NOT_AN_ELIGIBILITY_CHANGE",
        "custodian_only_crosswalk": crosswalk,
        "preparation_source_sha256": {"prepare_a04_handoff.py": digest(Path(__file__).read_bytes()),
                                      "check_a04_handoff.py": digest((BASE / "check_a04_handoff.py").read_bytes()),
                                      **{f"a04-handoff-source/{n}": digest((source / n).read_bytes()) for n in STATIC}},
    }
    (output / "CUSTODIAN_RECEIPT.json").write_bytes(canonical(receipt))
    lock = {
        "amendment": "A04_FRESH_REVIEWER_PATH", "created_utc": created,
        "source_git_commit": head, "source_tree_clean_at_start": True,
        "amendment_commit": receipt["amendment_commit"], "historical_checkpoint": CHECKPOINT,
        "gate": "FRAME_BLOCKED", "draw_authorized": False, "independent_review": "NOT_STARTED",
        "files": {**protocol_hashes, **PINNED,
                  "a04-handoff/CUSTODIAN_RECEIPT.json": digest(canonical(receipt)),
                  "a04-handoff/FRESH_REVIEWER_INTAKE.zip": receipt["package_sha256"],
                  **receipt["preparation_source_sha256"]},
    }
    (BASE / "PROTOCOL_LOCK_A04.json").write_bytes(canonical(lock))
    print(json.dumps({k: receipt[k] for k in ("package_sha256", "package_bytes", "gate", "independent_review")}, sort_keys=True))


if __name__ == "__main__":
    prepare()
