"""Bind baseline replay and primary-source context without republishing logs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from experiments.unscored_trials import inventory


def digest(path: Path) -> str:
    """Name the exact retained input, including prior diagnostic evidence."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(study_root: Path, output: Path) -> dict:
    """Verify context bytes and emit portable receipts, preserving evidence grade."""
    provenance = inventory.clean_provenance()
    if output.exists():
        raise FileExistsError("preserve prior context evidence")
    replacements = {
        str(study_root): "$WARRANT_RESEARCH_DATA_DIR",
        r"C:\Users\LawLight\Documents\Codex\2026-10-16\task-you-are-my-independent-research\outputs": "$WARRANT_BASELINE_PARENT",
        r"C:\Users\LawLight\AppData\Local\Programs\Python\Python312\python.exe": "$PYTHON",
    }

    def portable(value: object) -> object:
        if isinstance(value, str):
            for old, new in replacements.items():
                value = value.replace(old, new)
            return value
        if isinstance(value, list):
            return [portable(row) for row in value]
        if isinstance(value, dict):
            return {key: portable(row) for key, row in value.items()}
        return value

    baseline = {}
    for name in ("verification-summary.json", "canonical-comparisons.json", "command-receipts.json", "review-receipt.json"):
        path = study_root / "baseline-verification" / name
        baseline[name] = {"original_receipt_sha256": digest(path),
                          "portable_data": portable(json.loads(path.read_bytes()))}
    native_root = study_root / "native-contract"
    native_path = native_root / "source_manifest.json"
    native = json.loads(native_path.read_bytes())
    for row in native["sources"]:
        path = native_root / row["cache_file"]
        if digest(path) != row["sha256"] or path.stat().st_size != row["bytes"]:
            raise ValueError("native-contract source hash mismatch")
    spec_path = native_root / "terminal-bench-2-spec-20260515.json"
    spec = json.loads(spec_path.read_bytes())
    registry_path = native_root / "harbor-20260515-registry.json"
    registry = json.loads(registry_path.read_bytes())
    index = int(spec["json_pointer"].removeprefix("/"))
    if registry[index] != spec["spec"]:
        raise ValueError("official task extraction differs from pinned registry")
    closest = []
    closest_root = study_root / "closest-work"
    for path in sorted(closest_root.rglob("*.receipt.json")):
        receipt = json.loads(path.read_bytes())
        source = path.with_name(path.name.removesuffix(".receipt.json"))
        if receipt["status"] == "success":
            if digest(source) != receipt["sha256"] or source.stat().st_size != receipt["size_bytes"]:
                raise ValueError("closest-work source hash mismatch")
        elif source.exists():
            raise ValueError("failed closest-work receipt has ambiguous payload")
        closest.append({"local_path": source.relative_to(closest_root).as_posix(),
                        "receipt_sha256": digest(path), **receipt})
    output.mkdir(parents=True)
    documents = {
        "baseline_verification.json": {"provenance": provenance, "receipts": baseline,
                                      "path_portability": "local prefixes replaced; original receipt hashes retained"},
        "native_source_manifest.json": {"provenance": provenance, **native,
                                        "all_saved_payload_hashes_verified": True,
                                        "task_spec_sha256": digest(spec_path),
                                        "registry_sha256": digest(registry_path),
                                        "task_spec_matches_registry_pointer": True},
        "closest_work_source_manifest.json": {"provenance": provenance, "sources": closest,
                                              "web_tool_extracts_sha256": digest(closest_root / "web_tool_receipts.json"),
                                              "web_extract_grade": "cached tool text, not raw HTTP bytes"},
        "task_spec.json": spec,
    }
    for name, data in documents.items():
        (output / name).write_bytes((json.dumps(data, indent=2, sort_keys=True) + "\n").encode())
    return {"baseline_comparisons": baseline["verification-summary.json"]["portable_data"]["comparison_count"],
            "verified_native_payloads": len(native["sources"]),
            "closest_work_receipts": len(closest)}


def main() -> None:
    """Keep external context locations explicit and independent of production."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(collect(args.study_root, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
