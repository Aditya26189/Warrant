"""Verify a restricted intake package offline; never adjudicate or sample works."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FILES = {
    "READ_FIRST.md", "ELIGIBILITY_RULES.md", "BIBLIOGRAPHIC_CONSTRAINTS.json",
    "REVIEWER_INTAKE_BLANK.json", "EVIDENCE_RECEIPT_BLANK.json", "verify_package.py",
    "CANDIDATE_INVENTORY.json", "SENTINEL_IDENTIFIERS.json",
    "ELIGIBILITY_REVIEW_BLANK.json",
}
WORK_FIELDS = {"review_id", "work_id", "identifiers", "members"}
MEMBER_FIELDS = {
    "member_id", "source", "captured_version_id", "doi", "published", "updated",
    "year", "month", "metadata_record_sha256", "title_sha256", "normalized_title_sha256",
}
REVIEW_FIELDS = {
    "review_id", "work_id", "decision", "input_injection_task", "binary_evaluation",
    "before_target_answer", "english_evaluation", "first_public_date",
    "selected_version_id", "version_date", "version_preference_basis",
    "sentinel_check", "identity_reconciliation", "access_status",
    "evidence_ids", "method_bibliographic_locators", "limitations", "reviewer_id",
    "reviewed_utc",
}


def verify(root: Path) -> dict:
    """Reject altered, nonblank, incomplete or overinclusive intake artifacts."""
    actual = {p.name for p in root.iterdir()}
    if actual != FILES | {"MANIFEST.json"}:
        raise ValueError("Unexpected or missing intake files")
    if any(p.is_symlink() or not p.is_file() for p in root.iterdir()):
        raise ValueError("Only flat regular files may enter the intake")
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    if set(manifest["files"]) != FILES:
        raise ValueError("Manifest allowlist mismatch")
    for name, digest in manifest["files"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Hash mismatch: {name}")
    works = json.loads((root / "CANDIDATE_INVENTORY.json").read_text(encoding="utf-8"))
    reviews = json.loads((root / "ELIGIBILITY_REVIEW_BLANK.json").read_text(encoding="utf-8"))
    if len(works) != 372 or len(reviews) != 372:
        raise ValueError("Incomplete work inventory")
    if len({w["work_id"] for w in works}) != 372:
        raise ValueError("Duplicate work IDs")
    members = []
    for work, review in zip(works, reviews, strict=True):
        if set(work) != WORK_FIELDS or set(review) != REVIEW_FIELDS:
            raise ValueError("Unexpected work/review fields")
        for key in ("review_id", "work_id"):
            if work[key] != review[key]:
                raise ValueError("Work/review crosswalk mismatch")
        if any(value is not None for key, value in review.items()
               if key not in {"review_id", "work_id"}):
            raise ValueError("Review is not blank")
        for member in work["members"]:
            if set(member) != MEMBER_FIELDS or member["source"] not in {"acl", "arxiv"}:
                raise ValueError("Unexpected member fields/source")
            members.append(member["member_id"])
    if len(members) != 389 or len(set(members)) != 389:
        raise ValueError("Missing or repeated source membership")
    sentinels = json.loads((root / "SENTINEL_IDENTIFIERS.json").read_text(encoding="utf-8"))
    if len(sentinels) != 65 or any(set(s) != {
        "work_id", "exclude_versions", "frozen_label_sha256", "source_urls_sha256"
    } for s in sentinels):
        raise ValueError("Sentinel projection mismatch")
    for name in ("REVIEWER_INTAKE_BLANK.json", "EVIDENCE_RECEIPT_BLANK.json"):
        if any(v is not None for v in json.loads((root / name).read_text(encoding="utf-8")).values()):
            raise ValueError(f"Intake template is not blank: {name}")
    if manifest["independent_review"] != "NOT_STARTED" or manifest["draw"] != "BLOCKED":
        raise ValueError("Invalid gate status")
    return {"works": 372, "members": 389, "sentinels": 65,
            "integrity": "PASS", "independent_review": "NOT_STARTED", "draw": "BLOCKED"}


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
