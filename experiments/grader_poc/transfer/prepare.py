"""Expose reserved task bytes only after properties and methods are committed."""

import argparse
import gzip
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from experiments.grader_poc.baseline.candidates import mutations
from experiments.grader_poc.feasibility.prepare import HERE as CALIBRATION, ROOT, clean_revision, digest
from experiments.grader_poc.feasibility.run_calibration import control_code, json_bytes
from experiments.grader_poc.run_trial import git_output

from .properties import HERE, alternative_code, config, witness_inputs


def frozen_baseline() -> dict:
    """Reject operator/config drift from the previously evaluated calibration."""
    cfg = config()
    for relative in ("experiments/grader_poc/baseline/candidates.py", "experiments/grader_poc/baseline/config.json"):
        old = git_output(ROOT, "show", cfg["baseline_revision"] + ":" + relative)
        assert (ROOT / relative).read_text(encoding="utf-8").strip() == old
    return json.loads((ROOT / "experiments/grader_poc/baseline/config.json").read_bytes())


def prepare(archive: Path, out: Path) -> None:
    """Bind all selections, properties, alternatives and candidate pools before execution."""
    revision = clean_revision(ROOT)
    cfg = config()
    baseline = frozen_baseline()
    selection = json.loads((CALIBRATION / "fixtures/selection.json").read_bytes())
    assert cfg["task_ids"] == selection["reserved_ids"]
    raw = archive.read_bytes()
    assert digest(raw) == selection["dataset_sha256"]
    records = {}
    for line in gzip.decompress(raw).splitlines():
        if line.strip():
            row = json.loads(line)
            if row["task_id"] in cfg["task_ids"]:
                records[row["task_id"]] = (row, digest(line))
    out.mkdir(parents=True, exist_ok=False)
    manifest = {"source_revision": revision, "source_dirty": False,
                "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
                "dataset_sha256": digest(raw), "config_sha256": digest((HERE / "config.json").read_bytes()),
                "property_source_sha256": digest((HERE / "properties.py").read_bytes()),
                "baseline_source_sha256": digest((ROOT / "experiments/grader_poc/baseline/candidates.py").read_bytes()),
                "tasks": [], "payloads": {}}
    for identity in selection["reserved"]:
        task = identity["task_id"]
        before = time.perf_counter()
        row, raw_hash = records[task]
        assert raw_hash == identity["raw_record_sha256"]
        for field in ("prompt", "contract", "entry_point"):
            assert row[field] == identity[field]
        folder = out / task.split("/")[1]
        folder.mkdir()
        source = control_code(row, "reference")
        candidates = mutations(source, row["entry_point"], baseline["operators"])
        pool = {"reference_sha256": digest(source.encode()), "generated_count": len(candidates),
                "candidates": candidates[:baseline["candidate_cap"]], "excluded_by_cap": candidates[baseline["candidate_cap"]:]}
        for name, data in (("fixture.json", json_bytes(row)), ("pool.json", json_bytes(pool)),
                           ("witness_inputs.json", json_bytes(witness_inputs(task))),
                           ("alternative.py", alternative_code(task, row["entry_point"]).encode())):
            (folder / name).write_bytes(data)
            manifest["payloads"][folder.name + "/" + name] = {"sha256": digest(data), "bytes": len(data)}
        manifest["tasks"].append({"task_id": task, "raw_record_sha256": raw_hash,
                                  "generated_count": len(candidates), "included_count": len(pool["candidates"]),
                                  "base_inputs": len(row["base_input"]), "plus_inputs": len(row["plus_input"]),
                                  "automated_preparation_seconds": time.perf_counter() - before})
    (out / "manifest.json").write_bytes(json_bytes(manifest))
    print(json.dumps({"prepared_tasks": manifest["tasks"], "reference_test_exposure_begins_here": True}))


def main() -> None:
    """Extract only the original reservations to a fresh directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.archive, args.out)


if __name__ == "__main__":
    main()
