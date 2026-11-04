"""Offline release-metadata census with verified, non-secret source pointers.

Configuration repetitions describe declared work. They do not establish an
exact planned roster, execution retry lineage, or any outcome denominator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, unquote, urlsplit


DATASET = "harborframework/terminal-bench-2-leaderboard"
REVISION = "572b2614be2c0cb2527e14f5b1e4026f1072e6c1"
SUBMISSION_ROOT = "submissions/terminal-bench/2.0"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> object:
    return json.loads(path.read_bytes())


def _inside(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("source path escapes external data root")
    return path


def _verify_sources(root: Path) -> dict[str, dict]:
    """Verify every successful cached receipt without interpreting outcomes."""
    verified = {}
    allowed = (
        "url", "final_url", "retrieved_utc", "status", "http_status",
        "size_bytes", "sha256", "limit_bytes", "timeout_seconds",
        "pagination_link", "content_length", "error_type",
    )
    for receipt_path in sorted(root.rglob("*.receipt.json")):
        name = receipt_path.relative_to(root).as_posix().removesuffix(".receipt.json")
        receipt = _read_json(receipt_path)
        if not isinstance(receipt, dict) or receipt.get("status") not in {"success", "failed"}:
            raise ValueError(f"invalid receipt: {name}")
        path = _inside(root, name)
        if receipt["status"] == "success":
            data = path.read_bytes()
            if (type(receipt.get("size_bytes")) is not int
                    or len(data) != receipt["size_bytes"]
                    or _digest(data) != receipt.get("sha256")
                    or len(data) > receipt.get("limit_bytes", len(data))):
                raise ValueError(f"cached bytes do not match receipt: {name}")
        elif path.exists():
            raise ValueError(f"failed receipt has ambiguous cached payload: {name}")
        verified[name] = {
            "local_path": name, "receipt_sha256": _digest(receipt_path.read_bytes()),
            **{key: receipt[key] for key in allowed if key in receipt},
        }
    return verified


def _pinned_request(row: dict) -> None:
    parsed = urlsplit(row["url"])
    prefixes = (
        f"/api/datasets/{DATASET}/tree/{REVISION}/",
        f"/datasets/{DATASET}/raw/{REVISION}/",
        f"/datasets/{DATASET}/resolve/{REVISION}/",
    )
    decoded = unquote(parsed.path)
    if (parsed.scheme != "https" or parsed.hostname != "huggingface.co"
            or parsed.username or parsed.password
            or not decoded.startswith(prefixes)):
        raise ValueError("population input is not pinned to the official release")
    if "source_path" in row and decoded.split(f"/{REVISION}/", 1)[-1] != row["source_path"]:
        raise ValueError("source mapping and official request path differ")


def _tree(root: Path, name: str, parent: str, sources: dict[str, dict]) -> list[dict]:
    receipt = sources.get(name, {})
    if receipt.get("status") != "success":
        raise ValueError(f"unavailable population listing: {name}")
    _pinned_request(receipt)
    parsed = urlsplit(receipt["url"])
    query = parse_qs(parsed.query)
    limit = int(query.get("limit", ["0"])[0])
    if query.get("recursive") != ["false"] or limit <= 0:
        raise ValueError("population listing must be explicitly nonrecursive and bounded")
    if unquote(parsed.path).split(f"/tree/{REVISION}/", 1)[-1] != parent:
        raise ValueError("listing request and declared parent differ")
    entries = _read_json(_inside(root, name))
    if (not isinstance(entries, list) or len(entries) >= limit
            or receipt.get("pagination_link")):
        raise ValueError(f"paginated or potentially truncated listing: {name}")
    paths = set()
    for entry in entries:
        if (not isinstance(entry, dict) or entry.get("type") not in {"file", "directory"}
                or PurePosixPath(entry.get("path", "")).parent.as_posix() != parent
                or entry["path"] in paths):
            raise ValueError(f"duplicate, recursive or malformed tree entry: {name}")
        paths.add(entry["path"])
    return entries


def _public_config(config: dict) -> dict:
    """Expose only population fields, never agent kwargs or environments."""
    datasets = config.get("datasets", [])
    tasks = config.get("tasks", [])
    if not isinstance(datasets, list) or not isinstance(tasks, list):
        raise ValueError("datasets and tasks must be lists")
    if type(config.get("n_attempts")) is not int or config["n_attempts"] < 1:
        raise ValueError("declared n_attempts must be a positive integer")
    projection = {"n_attempts": config.get("n_attempts"), "datasets": [], "tasks": []}
    for item in datasets:
        if not isinstance(item, dict):
            raise ValueError("dataset configuration must be an object")
        selected = {key: item.get(key) for key in (
            "name", "version", "ref", "task_names", "exclude_task_names", "n_tasks",
        )}
        for key in ("name", "version", "ref"):
            if selected[key] is not None and not isinstance(selected[key], str):
                raise ValueError("dataset identity must be a string or null")
        for key in ("task_names", "exclude_task_names"):
            if selected[key] is not None and (
                not isinstance(selected[key], list)
                or not all(isinstance(value, str) for value in selected[key])
            ):
                raise ValueError("task selectors must be lists of strings or null")
        selected["local_path_declared"] = item.get("path") is not None
        selected["registry_path_declared"] = item.get("registry_path") is not None
        if selected["n_tasks"] is not None and (
            type(selected["n_tasks"]) is not int or selected["n_tasks"] < 0
        ):
            raise ValueError("declared n_tasks must be a nonnegative integer or null")
        projection["datasets"].append(selected)
    for item in tasks:
        if isinstance(item, str):
            projection["tasks"].append({"selector_sha256": _digest(item.encode())})
        elif isinstance(item, dict):
            if any(item.get(key) is not None and not isinstance(item[key], str)
                   for key in ("name", "task_name", "version", "ref")):
                raise ValueError("explicit task identity must be a string or null")
            projection["tasks"].append({
                **{key: item.get(key) for key in ("name", "task_name", "version", "ref")},
                "local_path_declared": item.get("path") is not None,
            })
        else:
            raise ValueError("explicit task selector has unsupported type")
    return projection


def _request_index(requests: list[dict], prefix: str) -> dict[str, dict]:
    indexed = {}
    for row in requests:
        if row["path"].startswith(prefix):
            if row["source_path"] in indexed:
                raise ValueError("duplicate population-tree source mapping")
            indexed[row["source_path"]] = row
    return indexed


def build_inventory(data_root: Path) -> dict:
    """Reconstruct all listed submissions/jobs while retaining access failures.

    Args:
        data_root: External cache containing immutable request manifests/receipts.

    Returns:
        Verified source manifest, submission rows, job rows and feasibility counts.
        No reward or exception payload is parsed and no planned slots are invented.
    """
    root = Path(data_root).resolve()
    sources = _verify_sources(root)
    metadata = _read_json(_inside(root, "dataset-metadata.json"))
    if sources.get("dataset-metadata.json", {}).get("status") != "success":
        raise ValueError("dataset metadata lacks verified successful receipt")
    if not isinstance(metadata, dict) or metadata.get("id") != DATASET or metadata.get("sha") != REVISION:
        raise ValueError("official metadata does not match frozen dataset revision")
    requests = []
    manifests = []
    for name in ("submission-requests.json", "job-tree-requests.json",
                 "config-requests.json", "discovery-requests.json"):
        path = root / name
        if not path.exists():
            continue
        rows = _read_json(path)
        if not isinstance(rows, list):
            raise ValueError("request manifest must be a list")
        manifests.append({"local_path": path.name, "sha256": _digest(path.read_bytes())})
        for row in rows:
            if not isinstance(row, dict) or not {"path", "source_path", "url"} <= row.keys():
                raise ValueError("request row lacks path, source_path or url")
            _inside(root, row["path"])
            receipt = sources.get(row["path"])
            if receipt is None or receipt["url"] != row["url"]:
                raise ValueError("request and retained receipt do not match")
            _pinned_request(row)
            if row not in requests:
                requests.append(row)
    top = _tree(root, "submission-tree.json", SUBMISSION_ROOT, sources)
    submission_paths = sorted(entry["path"] for entry in top if entry["type"] == "directory")
    tree_requests = _request_index(requests, "submission-trees/")
    if set(tree_requests) != set(submission_paths):
        raise ValueError("submission requests do not cover exactly the listed submissions")
    submission_rows = []
    job_paths = []
    for source_path in submission_paths:
        row = tree_requests[source_path]
        entries = _tree(root, row["path"], source_path, sources)
        jobs = sorted(entry["path"] for entry in entries if entry["type"] == "directory")
        job_paths.extend(jobs)
        submission_rows.append({
            "submission": PurePosixPath(source_path).name, "source_path": source_path,
            "revision": REVISION, "job_directories": len(jobs),
            "tree_source": row["path"], "tree_sha256": sources[row["path"]]["sha256"],
        })
    job_requests = _request_index(requests, "job-trees/")
    if set(job_requests) != set(job_paths):
        raise ValueError("job requests do not cover exactly the listed job directories")
    job_rows = []
    for job_path in sorted(job_paths):
        tree_request = job_requests[job_path]
        receipt = sources[tree_request["path"]]
        entries = (_tree(root, tree_request["path"], job_path, sources)
                   if receipt["status"] == "success" else None)
        configs = [row for row in requests if row["source_path"] == job_path + "/config.json"]
        for row in configs:
            prior = row.get("prior_failed_path")
            if prior and sources.get(prior, {}).get("status") != "failed":
                raise ValueError("retrieval retry lacks its original failed receipt")
        successes = [row for row in configs if sources[row["path"]]["status"] == "success"]
        selected = max(successes, key=lambda row: (
            sources[row["path"]].get("retrieved_utc", ""), row["path"]
        )) if successes else None
        public = None
        if selected:
            raw = _read_json(_inside(root, selected["path"]))
            if not isinstance(raw, dict):
                raise ValueError("job config must be an object")
            public = _public_config(raw)
        job_rows.append({
            "submission": PurePosixPath(job_path).parent.name,
            "job": PurePosixPath(job_path).name, "source_path": job_path,
            "revision": REVISION, "tree_status": receipt["status"],
            "tree_source": tree_request["path"], "tree_sha256": receipt.get("sha256"),
            "listed_child_directories": (sum(e["type"] == "directory" for e in entries)
                                         if entries is not None else None),
            "config_status": "success" if selected else ("failed" if configs else "unrequested"),
            "config_source": selected["path"] if selected else None,
            "config_sha256": sources[selected["path"]]["sha256"] if selected else None,
            "config_source_url": selected["url"] if selected else None,
            "config_retrieval_paths": [row["path"] for row in configs],
            "declared_n_attempts": public["n_attempts"] if public else None,
            "population_config": public,
            "roster_evidence": "configuration_only" if public else "unavailable",
            "exact_planned_roster_established": False,
        })
    return {
        "source_manifest": {
            "dataset": DATASET, "revision": REVISION, "license": "apache-2.0",
            "sources": list(sources.values()), "request_manifests": manifests,
        },
        "submissions": submission_rows, "jobs": job_rows,
        "feasibility": {
            "dataset": DATASET, "revision": REVISION,
            "submission_count": len(submission_rows), "job_directory_count": len(job_rows),
            "config_status_counts": dict(Counter(row["config_status"] for row in job_rows)),
            "declared_n_attempts_counts": dict(Counter(str(row["declared_n_attempts"]) for row in job_rows)),
            "successful_receipts": sum(row["status"] == "success" for row in sources.values()),
            "failed_receipts": sum(row["status"] == "failed" for row in sources.values()),
            "outcomes_analyzed": False, "exact_planned_roster_established": False,
            "limitation": "Listed directories and declared repetitions do not establish exact planned slots or retry lineage.",
        },
    }


def clean_provenance() -> dict:
    """Refuse scientific generation from dirty or untracked source code."""
    repo = Path(__file__).resolve().parents[2]

    def git(*args: str) -> str:
        result = subprocess.run(["git", "-C", str(repo), *args], text=True,
                                capture_output=True, check=True)
        if result.stderr.strip():
            raise RuntimeError("Git cleanliness cannot be established: " + result.stderr.strip())
        return result.stdout.strip()

    dirty = bool(git("status", "--porcelain"))
    if dirty:
        raise RuntimeError("clean committed source is required; dirty: true")
    git("ls-files", "--error-unmatch", "experiments/unscored_trials/inventory.py")
    return {
        "git_commit": git("rev-parse", "HEAD"), "dirty": False,
        "source_sha256": _digest(Path(__file__).read_bytes()),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(), "git_version": git("--version"),
    }


def main() -> None:
    """Write a metadata census only after clean source and cache verification."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    provenance = clean_provenance()
    result = build_inventory(args.data_root)
    outputs = [args.output_dir / name for name in (
        "source_manifest.json", "feasibility.json", "provenance.json", "submissions.csv", "jobs.csv",
    )]
    if any(path.exists() for path in outputs):
        raise FileExistsError("refusing to replace prior inventory evidence")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name in ("source_manifest", "feasibility"):
        payload = {"provenance": provenance, **result[name]}
        (args.output_dir / (name + ".json")).write_bytes((json.dumps(payload, indent=2) + "\n").encode())
    (args.output_dir / "provenance.json").write_bytes((json.dumps(provenance, indent=2) + "\n").encode())
    for name in ("submissions", "jobs"):
        rows = result[name]
        with (args.output_dir / (name + ".csv")).open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
            writer.writeheader()
            writer.writerows({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
                             for key, value in row.items()} for row in rows)
    print(json.dumps(result["feasibility"], indent=2))


if __name__ == "__main__":
    main()
