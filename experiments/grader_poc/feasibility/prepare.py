"""Extract calibration bytes and prompt-only reservations; execute nothing."""

import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from experiments.grader_poc.run_trial import git_output

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(data: bytes) -> str:
    """Bind retained inputs without interpreting reserved grader contents."""
    return hashlib.sha256(data).hexdigest()


def clean_revision(root: Path) -> str:
    """Prevent a clean commit ID from labeling uncommitted scientific source."""
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError(f"Dirty source tree: {root.name}")
    return git_output(root, "rev-parse", "HEAD")


def select_records(raw: bytes, config: dict) -> tuple[dict, dict]:
    """Keep reserved test/reference fields out of the exported metadata."""
    records = {}
    for line in gzip.decompress(raw).splitlines():
        if line.strip():
            row = json.loads(line)
            task_id = row["task_id"]
            if task_id in records:
                raise ValueError("Duplicate task identity")
            records[task_id] = (row, digest(line))
    calibration = config["calibration_id"]
    ranked = sorted(
        (key for key in records if key != calibration),
        key=lambda key: digest((config["reservation_prefix"] + key).encode()),
    )[: config["reserved_count"]]
    public_fields = ("task_id", "prompt", "contract", "entry_point")
    manifest = {
        "selection_rule": "ascending SHA256(prefix + task_id), calibration excluded",
        "prefix": config["reservation_prefix"],
        "population_count": len(records),
        "calibration_id": calibration,
        "reserved_ids": ranked,
        "reserved": [
            {**{key: records[tid][0][key] for key in public_fields},
             "raw_record_sha256": records[tid][1],
             "runtime_eligibility": "UNVERIFIED_NOT_EXECUTED"}
            for tid in ranked
        ],
        "calibration_raw_record_sha256": records[calibration][1],
        "exposure": "Reserved records parsed and hashed for transport; only prompts, "
                    "contracts and identities exported. No reserved execution or "
                    "test/reference inspection. Not access-controlled blinding.",
    }
    return records[calibration][0], manifest


def main() -> None:
    """Prepare a fresh local packet without downloading or executing code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--evalplus-root", required=True, type=Path)
    parser.add_argument("--humaneval-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    revision = clean_revision(ROOT)
    config_bytes = (HERE / "config.json").read_bytes()
    config = json.loads(config_bytes)
    upstream = clean_revision(args.evalplus_root)
    if upstream != config["evalplus_revision"]:
        raise ValueError("Wrong EvalPlus revision")
    raw = args.archive.read_bytes()
    if digest(raw) != config["dataset_sha256"]:
        raise ValueError("Wrong dataset bytes")
    fixture, manifest = select_records(raw, config)
    args.out.mkdir(parents=True, exist_ok=False)
    fixture_bytes = (json.dumps(fixture, indent=2, ensure_ascii=True) + "\n").encode()
    (args.out / "calibration.json").write_bytes(fixture_bytes)
    manifest.update({
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": revision, "source_dirty": False,
        "config_sha256": digest(config_bytes),
        "dataset_url": config["dataset_url"], "dataset_sha256": digest(raw),
        "evalplus_revision": upstream,
        "calibration_file_sha256": digest(fixture_bytes),
    })
    for source, name in ((args.evalplus_root / "LICENSE", "EVALPLUS-LICENSE"),
                         (args.humaneval_root / "LICENSE", "HUMANEVAL-LICENSE")):
        payload = source.read_bytes()
        (args.out / name).write_bytes(payload)
        manifest[name + "_sha256"] = digest(payload)
    (args.out / "selection.json").write_bytes(
        (json.dumps(manifest, indent=2) + "\n").encode()
    )
    print(json.dumps({"reserved_ids": manifest["reserved_ids"],
                      "calibration_id": fixture["task_id"],
                      "dataset_sha256": digest(raw)}))


if __name__ == "__main__":
    main()
