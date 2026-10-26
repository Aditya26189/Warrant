"""Bind A05 inputs and display released method evidence for human-model judgment.

This module never infers scientific eligibility from provider flags. Its output
is a source casebook; separate, attributed decisions are supplied explicitly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
import a04_recovery_intake as intake  # noqa: E402


def encoded(value: object) -> bytes:
    """Return canonical review bytes."""
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def sha(raw: bytes) -> str:
    """Commit exact bytes."""
    return hashlib.sha256(raw).hexdigest()


def read_archive(path: Path) -> dict[str, bytes]:
    """Check archive integrity before reading component bytes."""
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() or len(set(archive.namelist())) != len(archive.namelist()):
            raise ValueError("ARCHIVE_INTEGRITY")
        return {name: archive.read(name) for name in archive.namelist()}


def inputs() -> tuple[dict, list]:
    """Bind originals, adopted authority and repaired administrative layer."""
    inventory, evidence, _, sentinels = intake.frozen_inputs()
    recovery = read_archive(BASE / intake.RUN / "transfer/RECOVERY_CONTROLLED_EVIDENCE.zip")
    for name in ("RECOVERY_METHOD_FACTS.json", "OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json",
                 "RECOVERY_SOURCE_BINDINGS.json", "RECOVERY_IDENTITY_EVIDENCE.json",
                 "REGISTERED_DOI_EVIDENCE.json", "REGISTRATION_FOLLOWUP_EVIDENCE.json"):
        for row in json.loads(recovery[name]):
            eid = row["evidence_id"]
            if eid in evidence:
                raise ValueError("EVIDENCE_ID_COLLISION")
            evidence[eid] = row
    prior = json.loads((BASE / "a04-custodian-repair-20261023/REPAIRED_B_WORKING_COPY.json").read_bytes())
    previous = {r["review_id"]: r for r in prior["rows"]}
    crosswalk = {r["review_id"]: r for r in sentinels}
    files = [BASE / name for name in ("PROTOCOL_LOCK.json", "PROTOCOL_LOCK_A02.json",
             "PROTOCOL_LOCK_A03.json", "PROTOCOL_LOCK_A04.json", "PARSER_LOCK_A02.json")]
    files += [BASE / path for path, _, _ in intake.ARCHIVES.values()]
    files += [BASE / path for path in (
        intake.RUN + "/REVIEWER_RECOVERY_TRANSFER.zip",
        "a04-reviewer-returns-20261022/B1_SUBSTANTIVE_REVIEW.zip",
        "a04-reviewer-returns-20261022/ELIGIBILITY_REVIEWS.zip",
        "a04-custodian-repair-20261023/INDEPENDENT_REVIEWER_B1_RETURN.zip",
        "a04-custodian-repair-20261023/REPAIR_MANIFEST.json",
        "a04-custodian-repair-20261023/REPAIRED_B_WORKING_COPY.json")]
    files += [HERE / name for name in ("A05_APPROVAL_RECEIPT.json",
        "AMENDMENT_A05_CUSTODIAN_ADJUDICATION.md", "INTERPRETATION_BEFORE_ADJUDICATION.md")]
    lock = {"status": "A05_CUSTODIAN_ADJUDICATION_ONLY", "adoption_commit":
        "c9538747dbb762b7312763ec54da2c7a91510bae", "sampling_authorized": False,
        "b2_authorized": False, "files": {
            str(p.relative_to(BASE)).replace("\\", "/"): sha(p.read_bytes()) for p in files}}
    cases = []
    for work in inventory:
        rid = work["review_id"]
        member_ids = {m["member_id"] for m in work["members"]}
        refs = [r for r in evidence.values() if r.get("review_id") == rid
                or (r.get("member_id") in member_ids)
                or bool(member_ids & set(r.get("member_ids", [])))]
        cases.append({"review_id": rid, "inventory": work, "prior_b_administrative": previous[rid],
                      "sentinel_crosswalk": crosswalk[rid], "evidence": refs})
    if len(cases) != 372 or sum(len(c["inventory"]["members"]) for c in cases) != 389:
        raise ValueError("FROZEN_UNIVERSE_CHANGED")
    return lock, cases


def clean_head() -> str:
    """Require true clean-tree provenance before generating scientific inputs."""
    root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
        raise ValueError("DIRTY_TREE")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def main() -> None:
    """Generate immutable input commitments or display full bounded method facts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-inputs", action="store_true")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=30)
    args = parser.parse_args()
    if args.freeze_inputs:
        head = clean_head()
        lock, cases = inputs()
        lock["source_git_commit"] = head
        for name, value in (("PROTOCOL_LOCK_A05.json", lock), ("SOURCE_CASEBOOK.json", {
                "source_git_commit": head, "actor_scope": "SOURCE_CASEBOOK_NOT_JUDGMENTS",
                "cases": cases})):
            with (HERE / name).open("xb") as stream:
                stream.write(encoded(value))
        print(json.dumps({"works": len(cases), "memberships": 389, "source_git_commit": head}))
        return
    book = json.loads((HERE / "SOURCE_CASEBOOK.json").read_bytes())
    for case in book["cases"][args.start - 1:args.end]:
        rid = case["review_id"]
        p = case["prior_b_administrative"]
        print(f"\n{rid} {case['inventory']['work_id']} SELECTED={p['selected_version_id']} "
              f"DATE={p['version_date']} FIRST={p['first_public_date']}")
        facts = [r for r in case["evidence"] if "method_fact" in r or "quote" in r]
        for n, fact in enumerate(facts, 1):
            print(f" {n}. [{fact['evidence_id']}] {fact.get('version')} "
                  f"{fact.get('method_fact', fact.get('quote'))}")
        if not facts:
            print(" NO RELEASED METHOD FACTS")
    print("\nDisplayed full released method facts; no eligibility is inferred.")


if __name__ == "__main__":
    main()
