"""Audit current continuation against immutable history and exact output replay."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import compile_continuation as c
import release_deep as r

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def audit(checkpoint: Path) -> dict:
    """Verify scientific preservation and replay without running any selection."""
    baseline_files = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", c.BASELINE, "docs/research/fpr_reporting/b1"],
        cwd=ROOT, text=True).splitlines()
    mutable = "docs/research/fpr_reporting/b1/B1_CURRENT_STATUS.md"
    checked = {}
    for name in baseline_files:
        if name == mutable:
            continue
        expected = subprocess.check_output(["git", "show", c.BASELINE + ":" + name], cwd=ROOT)
        if (ROOT / name).read_bytes() != expected:
            raise ValueError("HISTORICAL_RESEARCH_CHANGED:" + name)
        checked[name] = r.sha(expected)
    changed = subprocess.check_output(["git", "diff", "--name-only", c.BASELINE, "HEAD"], cwd=ROOT, text=True).splitlines()
    allowed = "docs/research/fpr_reporting/b1/a05-deep-evidence-20261024/"
    if any(name != mutable and not name.startswith(allowed) for name in changed):
        raise ValueError("OUT_OF_SCOPE_CHANGE")
    proposal = json.loads((checkpoint / "FRAME_PROPOSAL.json").read_bytes())
    generated_head = proposal["summary"]["source_git_commit"]
    expected = c.assemble(generated_head)
    payloads = {}
    for name, value in expected.items():
        raw = value.encode() if isinstance(value, str) else r.encoded(value)
        actual = (checkpoint / name).read_bytes()
        if actual != raw:
            raise ValueError("SCIENTIFIC_REPLAY_MISMATCH:" + name)
        payloads[name] = r.sha(actual)
    files = []
    for release in [*sorted(HERE.glob("releases/*/FACTS.json")), *sorted(HERE.glob("bibliography/*/FACTS.json"))]:
        document = json.loads(release.read_bytes())
        for name, digest in document["source_files"].items():
            if r.sha((release.parent / name).read_bytes()) != digest:
                raise ValueError("RELEASE_SOURCE_CHANGED")
        files.append({"path": str(release.relative_to(HERE)), "sha256": r.sha(release.read_bytes())})
    evidence = c.load_evidence()
    methods = [x for x in evidence.values() if x.get("release_status") == "CHECKED_METHOD_FIELD_NOT_ELIGIBILITY"]
    bibliography = [x for x in evidence.values() if x.get("fact_kind") == "BIBLIOGRAPHY_ONLY"]
    tracked_sizes = []
    for name in subprocess.check_output(["git", "ls-files", "docs/research/fpr_reporting/b1/a05-deep-evidence-20261024"], cwd=ROOT, text=True).splitlines():
        size = (ROOT / name).stat().st_size
        if size > 10_000_000:
            raise ValueError("TRACKED_FILE_OVER_10_MB")
        tracked_sizes.append(size)
    return {"status": "PASS", "checkpoint": str(checkpoint.relative_to(HERE)),
            "generated_source_commit": generated_head, "frozen_history_baseline": c.BASELINE,
            "historical_files_byte_identical": len(checked), "historical_file_hashes": checked,
            "scope_check": "RESEARCH_CONTINUATION_AND_ACTIVE_POINTER_ONLY",
            "checkpoint_payloads": payloads, "exact_replay": True, "releases": files,
            "unique_new_checked_method_fields": len(methods),
            "works_with_new_checked_method_fields": len({x["review_id"] for x in methods}),
            "unique_new_checked_bibliographic_fields": len(bibliography),
            "maximum_new_tracked_file_bytes": max(tracked_sizes, default=0),
            "draw_executed": False, "b2_authorized": False, "summary": proposal["summary"]}


def main() -> None:
    """Write a new audit receipt, preserving previous receipts and all artifacts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise ValueError("DIRTY_TREE")
    result = audit(args.checkpoint.resolve())
    result["auditor_source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    with args.output.open("xb") as stream:
        stream.write(r.encoded(result))
    print(json.dumps({k: v for k, v in result.items() if k not in {"historical_file_hashes", "summary", "releases"}}, sort_keys=True))


if __name__ == "__main__":
    main()
