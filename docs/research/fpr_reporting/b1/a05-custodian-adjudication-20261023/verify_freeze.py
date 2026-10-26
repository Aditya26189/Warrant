"""Freeze and verify A05 payloads, scope and original-file preservation."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adjudicate as a  # noqa: E402
import compile_proposal as c  # noqa: E402

BASELINE = "23f099bda488bcf2cfcd88fa47c831eaf0072e99"
ROOT = HERE.parents[4]
PREFIX = str(HERE.relative_to(ROOT)).replace("\\", "/")


def preservation() -> tuple[int, list[str]]:
    """Replay Git blob identities without changing an old artifact or Git object."""
    before = subprocess.check_output(["git", "ls-tree", "-rz", BASELINE, "--",
                                      "docs/research/fpr_reporting/b1"], cwd=ROOT)
    count = 0
    for record in before.split(b"\0"):
        if not record:
            continue
        meta, name = record.split(b"\t")
        raw = (ROOT / name.decode()).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != meta.decode().split()[2]:
            raise ValueError("HISTORICAL_B1_FILE_CHANGED:" + name.decode())
        count += 1
    changed = subprocess.check_output(["git", "diff", "--name-only", BASELINE, "HEAD"], cwd=ROOT, text=True).splitlines()
    allowed = (PREFIX + "/", "docs/research/fpr_reporting/b1/a04-scientific-continuation-20261023/")
    if any(not (name.startswith(allowed) or name == "docs/research/fpr_reporting/b1/B1_CURRENT_STATUS.md")
           for name in changed):
        raise ValueError("OUT_OF_RESEARCH_SCOPE_CHANGE")
    return count, changed


def verify(manifest: dict) -> None:
    """Fail on byte changes or an attempt to unlock selection/B2 in the payload."""
    for name, digest in manifest["files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("UNSAFE_MANIFEST_PATH")
        if a.sha((HERE / name).read_bytes()) != digest:
            raise ValueError("FROZEN_FILE_DIGEST_MISMATCH:" + name)
    if a.sha((HERE.parent / "B1_CURRENT_STATUS.md").read_bytes()) != manifest["navigation_sha256"]:
        raise ValueError("CURRENT_NAVIGATION_CHANGED")
    if subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() != "research/fpr-stage-a-20261017":
        raise ValueError("UNEXPECTED_BRANCH")
    validation = json.loads((HERE / "PROPOSAL_VALIDATION.json").read_bytes())
    if validation["sampling_authorized"] or validation["b2_authorized"] or validation["global_frame_clearance"]:
        raise ValueError("UNAUTHORIZED_GATE_PROMOTION")
    outputs = c.assemble(validation["source_git_commit"])
    for name, value in outputs.items():
        if a.encoded(value) != (HERE / name).read_bytes():
            raise ValueError("PROPOSAL_REPLAY_MISMATCH:" + name)
    count, _ = preservation()
    if count != manifest["preserved_preexisting_b1_files"]:
        raise ValueError("PRESERVATION_COUNT_CHANGED")


def main() -> None:
    """Seal once from a clean committed tree, or replay an existing manifest."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    target = HERE / "FREEZE_MANIFEST.json"
    if args.freeze:
        head = a.clean_head()
        count, changed = preservation()
        paths = subprocess.check_output(["git", "ls-files", "--", PREFIX], cwd=ROOT, text=True).splitlines()
        files = {str((ROOT / name).relative_to(HERE)).replace("\\", "/"):
                 a.sha((ROOT / name).read_bytes()) for name in paths if not name.endswith("/FREEZE_MANIFEST.json")}
        manifest = {"source_git_commit": head, "baseline_commit": BASELINE, "files": files,
            "navigation_sha256": a.sha((HERE.parent / "B1_CURRENT_STATUS.md").read_bytes()),
            "preserved_preexisting_b1_files": count, "scoped_tracked_changes": changed,
            "sampling_authorized": False, "b2_authorized": False,
            "status": "FRAME_BLOCKED_CUSTODIAN_PROPOSAL_NOT_COMPLETE_ELIGIBLE_FRAME"}
        verify(manifest)
        with target.open("xb") as stream:
            stream.write(a.encoded(manifest))
    else:
        manifest = json.loads(target.read_bytes())
        verify(manifest)
    print(json.dumps({"status": "PASS", "frozen_files": len(manifest["files"]),
        "preserved_preexisting_b1_files": manifest["preserved_preexisting_b1_files"],
        "sampling_authorized": False, "b2_authorized": False}))


if __name__ == "__main__":
    main()
