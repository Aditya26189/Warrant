"""Inventory public score availability before designing a performance study.

P002 prohibits outcome reanalysis in this stage. Schema and label-count checks
establish data availability, not independent sample size or detector quality.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
from typing import Any


def git(root: Path, *args: str) -> str:
    """Inspect provenance without invoking third-party analysis code."""
    return subprocess.check_output(
        ["git", "-c", "core.longpaths=true", *args], cwd=root, text=True,
    ).strip()


def sha256(raw: bytes) -> str:
    """Bind metadata assertions to the exact inspected bytes."""
    return hashlib.sha256(raw).hexdigest()


def inspect_scores(source: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Validate score-vector schema while computing no performance metric."""
    files = sorted(source.glob(config["score_glob"]))
    if not files:
        raise ValueError("no source score files matched")
    rows = []
    by_set: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for path in files:
        raw = path.read_bytes()
        data = json.loads(raw)
        detector, dataset = data["detector"], data["set"]
        if not isinstance(detector, str) or not isinstance(dataset, str):
            raise ValueError(f"invalid identities: {path.name}")
        pair = detector, dataset
        if pair in seen:
            raise ValueError(f"duplicate detector/set pair: {pair}")
        seen.add(pair)
        scores, labels = data["probs"], data["labels"]
        if not isinstance(scores, list) or not scores:
            raise ValueError(f"missing score vector: {path.name}")
        if any(type(s) not in (int, float) or not math.isfinite(s) for s in scores):
            raise ValueError(f"nonfinite/nonnumeric score: {path.name}")
        if labels is not None and (
            not isinstance(labels, list) or len(labels) != len(scores)
            or any(type(y) is not int or y not in (0, 1) for y in labels)
        ):
            raise ValueError(f"invalid label vector: {path.name}")
        row = {
            "file": path.relative_to(source).as_posix(), "sha256": sha256(raw),
            "bytes": len(raw), "detector": detector, "set": dataset,
            "rows": len(scores), "negative_labels": labels.count(0) if labels else None,
            "positive_labels": labels.count(1) if labels else None,
            "label_sequence_sha256": sha256(json.dumps(labels).encode()),
            "identity_fields_present": sorted(set(config["identity_fields"]) & data.keys()),
        }
        rows.append(row)
        by_set[dataset].append(row)
    return {
        "score_files": len(rows), "declared_detector_identities": len({r["detector"] for r in rows}),
        "files": rows,
        "sets": {
            name: {
                "detector_identities": sorted(r["detector"] for r in members),
                "row_counts": sorted({r["rows"] for r in members}),
                "label_sequences_agree": len({r["label_sequence_sha256"] for r in members}) == 1,
                "all_have_record_identity_fields": all(r["identity_fields_present"] for r in members),
            } for name, members in sorted(by_set.items())
        },
        "performance_metrics_computed": False,
        "independent_unit_counts": "UNKNOWN; row count is not task or independent-unit count",
        "alignment": "matching labels/lengths cannot authenticate text/order identity",
    }


def build_inventory(source: Path, config_path: Path) -> dict[str, Any]:
    """Require clean, pinned inputs before retaining a feasibility inventory."""
    own_root = Path(__file__).resolve().parents[2]
    raw = config_path.read_bytes()
    config = json.loads(raw)
    if git(own_root, "status", "--porcelain") or git(source, "status", "--porcelain"):
        raise RuntimeError("inventory requires clean source and research worktrees")
    source_commit = git(source, "rev-parse", "HEAD")
    if source_commit != config["expected_source_commit"]:
        raise ValueError("source revision differs from the frozen inventory config")
    return {
        "provenance": {
            "git_commit": git(own_root, "rev-parse", "HEAD"), "dirty": False,
            "config_sha256": sha256(raw), "python": platform.python_version(),
            "libraries": "Python standard library only", "seed": None,
            "randomness": "none; deterministic schema inspection", "source_commit": source_commit,
            "source_dirty": False, "source_url": config["source_url"],
        },
        "config": config,
        "reviewed_source_hashes": {
            name: sha256((source / name).read_bytes()) for name in config["reviewed_paths"]
        },
        "inventory": inspect_scores(source, config),
    }


def main() -> None:
    """Write an independently reproducible availability artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = build_inventory(args.source, args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(artifact, indent=2) + "\n").encode())
    inv = artifact["inventory"]
    print(json.dumps({k: inv[k] for k in ("score_files", "declared_detector_identities", "performance_metrics_computed")}))


if __name__ == "__main__":
    main()
