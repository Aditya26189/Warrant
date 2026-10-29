"""Replay the frozen analysis with networking disabled and compare all tables."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from experiments.unscored_trials import analyze, inventory


def artifact_hashes(root: Path) -> dict[str, str]:
    """Compare every canonical file; only invocation provenance varies."""
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.relative_to(root).as_posix() != "provenance.json"}


def replay(data_root: Path, config: Path, task_spec: Path, reference: Path,
           output: Path, validation: Path) -> dict:
    """Recompute in an isolated destination and fail on any canonical difference."""
    source, target = reference.resolve(), output.resolve()
    if source.is_relative_to(target) or target.is_relative_to(source):
        raise ValueError("reference and replay destinations must be disjoint")
    if validation.exists():
        raise FileExistsError("preserve prior validation receipts")
    provenance = inventory.clean_provenance()
    before = artifact_hashes(reference)
    if not before:
        raise ValueError("reference contains no canonical artifacts")
    with patch("socket.socket", side_effect=RuntimeError("offline replay forbids networking")), \
            patch("socket.create_connection", side_effect=RuntimeError("offline replay forbids networking")):
        summary = analyze.run_analysis(data_root, config, task_spec, output,
                                       provenance=provenance)
    after = artifact_hashes(output)
    differences = sorted(name for name in before.keys() | after.keys()
                         if before.get(name) != after.get(name))
    receipt = {"provenance": provenance, "networking_disabled": True,
               "compared_canonical_files": len(before),
               "excluded_file": "provenance.json (invocation time/environment)",
               "differences": differences, "match": not differences,
               "canonical_sha256": before, "replayed_summary": summary,
               "review_category": "same-system computational replay, not independent human review"}
    validation.parent.mkdir(parents=True, exist_ok=True)
    validation.write_bytes((json.dumps(receipt, indent=2, sort_keys=True,
                                       default=analyze._json_default, allow_nan=False) + "\n").encode())
    if differences:
        raise ValueError("offline replay differs: " + ", ".join(differences))
    return receipt


def main() -> None:
    """Keep commands explicit and retain replay failures before exiting."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("data-root", "config", "task-spec", "reference-dir", "output-dir", "validation"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    receipt = replay(args.data_root, args.config, args.task_spec, args.reference_dir,
                     args.output_dir, args.validation)
    print(json.dumps({key: receipt[key] for key in
                      ("networking_disabled", "compared_canonical_files", "match")}, indent=2))


if __name__ == "__main__":
    main()
