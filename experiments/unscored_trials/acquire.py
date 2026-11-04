"""Acquire only frozen census result JSON, with an aggregate byte ceiling."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from fetch_batch import run
from inventory import build_inventory, clean_provenance
from sources import retrieve_cached


def prepare(data_root: Path, config: dict) -> list[dict]:
    """Bind every named final directory to its result, without reading rewards."""
    inventory = build_inventory(data_root)
    if (inventory["source_manifest"]["revision"] != config["revision"]
            or inventory["source_manifest"]["dataset"] != config["dataset"]):
        raise ValueError("configuration and source revision differ")
    cached = {row["url"]: row for row in inventory["source_manifest"]["sources"]
              if row["status"] == "success"}
    requests = []
    for job in inventory["jobs"]:
        entries = json.loads((data_root / job["tree_source"]).read_bytes())
        paths = [(job["source_path"] + "/result.json", "job")]
        paths.extend((row["path"] + "/result.json", "trial")
                     for row in entries if row["type"] == "directory")
        for path, kind in paths:
            url = (f'https://huggingface.co/datasets/{config["dataset"]}/raw/'
                   f'{config["revision"]}/{quote(path, safe="/")}')
            key = hashlib.sha256(path.encode()).hexdigest()
            requests.append({
                "path": cached[url]["local_path"] if url in cached else f"results/{key}.json",
                "source_path": path, "kind": kind, "job": job["source_path"],
                "submission": job["submission"], "url": url,
                "limit_bytes": config[f"{kind}_limit_bytes"],
                "timeout": config["request_timeout_seconds"],
            })
    return sorted(requests, key=lambda row: row["source_path"])


def consumed_bytes(data_root: Path) -> int:
    """Count retained responses; other-source downloads require a separate reserve."""
    receipts = (json.loads(path.read_bytes()) for path in data_root.rglob("*.receipt.json"))
    return sum(row["size_bytes"] if row["status"] == "success"
               else row.get("limit_bytes", 0) + 1 for row in receipts)


def _fetch_or_retain(manifest_path: Path, rows: list[dict], data_root: Path,
                     config: dict, remaining: int) -> list[dict]:
    """Retain prior failures without treating them as cache successes or retrying."""
    pending = []
    stored_failures = {}
    for row in rows:
        receipt_path = data_root / (row["path"] + ".receipt.json")
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_bytes())
            if receipt["url"] != row["url"]:
                raise ValueError("retained request identity mismatch")
            if receipt["status"] == "failed":
                stored_failures[row["path"]] = receipt
                continue
        pending.append(row)
    manifest_path.write_bytes((json.dumps(pending, indent=2) + "\n").encode())
    fetched = run(manifest_path, data_root, config["workers"], remaining) if pending else []
    by_path = {row["path"]: row for row in fetched}
    return [stored_failures[row["path"]] if row["path"] in stored_failures
            else by_path[row["path"]] for row in rows]


def validate_request(row: dict, config: dict) -> None:
    """Bind resumed requests to the same official dataset, path and limits."""
    expected = (f'https://huggingface.co/datasets/{config["dataset"]}/raw/'
                f'{config["revision"]}/{quote(row["source_path"], safe="/")}')
    if (row["url"] != expected or row["kind"] not in {"job", "trial"}
            or row["limit_bytes"] != config[f'{row["kind"]}_limit_bytes']
            or row["timeout"] != config["request_timeout_seconds"]
            or not row["source_path"].startswith(row["job"] + "/")
            or not row["source_path"].endswith("/result.json")):
        raise ValueError("frozen request identity or limits differ from protocol")


def verify_completed(rows: list[dict], data_root: Path, config: dict) -> None:
    """Reverify resumed completed sources, including all successful byte hashes."""
    root = data_root.resolve()
    for row in rows:
        validate_request(row, config)
        destination = (root / row["path"]).resolve()
        if not destination.is_relative_to(root):
            raise ValueError("completed source escapes working-data root")
        receipt_path = destination.with_name(destination.name + ".receipt.json")
        if not receipt_path.is_file():
            raise ValueError("completed source lacks its retained receipt")
        receipt = json.loads(receipt_path.read_bytes())
        if receipt["url"] != row["url"]:
            raise ValueError("completed receipt request mismatch")
        if receipt["status"] == "success":
            retrieve_cached(row["url"], destination, row["limit_bytes"], row["timeout"])
        elif receipt["status"] != "failed" or destination.exists():
            raise ValueError("ambiguous completed failure")


def acquire(data_root: Path, config: dict, other_source_bytes: int) -> dict:
    """Stop before aggregate worst-case reservation exceeds remaining allowance."""
    provenance = clean_provenance()
    if other_source_bytes < 0:
        raise ValueError("nonnegative other-source reserve required")
    manifest_path = data_root / "census-requests.json"
    if manifest_path.exists():
        requests = json.loads(manifest_path.read_bytes())
    else:
        requests = prepare(data_root, config)
        manifest_path.write_bytes((json.dumps(requests, indent=2) + "\n").encode())
    for row in requests:
        validate_request(row, config)
    if len({row["source_path"] for row in requests}) != len(requests):
        raise ValueError("duplicate frozen source identity")
    receipts_dir = data_root / "acquisition"
    receipts_dir.mkdir(exist_ok=True)
    batch_index = 0
    start = 0
    identity_fields = ("source_path", "url", "kind", "job", "submission", "limit_bytes", "timeout")
    while start < len(requests):
        completed_path = receipts_dir / f"batch-{batch_index:03d}-completed.json"
        if completed_path.exists():
            completed_rows = json.loads(completed_path.read_bytes())
            frozen_rows = requests[start:start + len(completed_rows)]
            if (not completed_rows or len(frozen_rows) != len(completed_rows)
                    or any(any(row.get(key) != frozen.get(key) for key in identity_fields)
                           for row, frozen in zip(completed_rows, frozen_rows, strict=True))):
                raise ValueError("completed batch differs from frozen source paths")
            verify_completed(completed_rows, data_root, config)
            start += len(completed_rows)
            batch_index += 1
            continue
        remaining = config["max_download_bytes"] - other_source_bytes - consumed_bytes(data_root)
        chunk, reserved = [], 0
        for row in requests[start:start + config["max_batch_requests"]]:
            if reserved + row["limit_bytes"] + 1 > remaining:
                break
            chunk.append(row)
            reserved += row["limit_bytes"] + 1
        if not chunk:
            raise ValueError("next source cannot fit remaining total download ceiling")
        chunk_path = receipts_dir / f"batch-{batch_index:03d}.json"
        receipts = _fetch_or_retain(chunk_path, chunk, data_root, config, remaining)
        # Preserve failures in place, then use separate bounded attempts.
        for attempt in range(1, config["max_extra_attempts"] + 1):
            failed = []
            for row, receipt in zip(chunk, receipts, strict=True):
                if receipt["status"] == "success":
                    continue
                replacement = dict(row)
                replacement["prior_failed_path"] = row["path"]
                replacement["path"] = f'retry{attempt}/' + Path(row["path"]).name
                failed.append(replacement)
            if not failed:
                break
            retry_path = receipts_dir / f"batch-{batch_index:03d}-retry-{attempt}.json"
            remaining = config["max_download_bytes"] - other_source_bytes - consumed_bytes(data_root)
            if sum(row["limit_bytes"] + 1 for row in failed) > remaining:
                raise ValueError("retry batch exceeds remaining total download ceiling")
            retry_receipts = _fetch_or_retain(retry_path, failed, data_root, config, remaining)
            replacements = {row["source_path"]: (row, receipt)
                            for row, receipt in zip(failed, retry_receipts, strict=True)}
            for i, row in enumerate(chunk):
                if row["source_path"] in replacements:
                    chunk[i], receipts[i] = replacements[row["source_path"]]
        (receipts_dir / f"batch-{batch_index:03d}-completed.json").write_bytes(
            (json.dumps(chunk, indent=2) + "\n").encode())
        print(json.dumps({"batch": batch_index, "requests_completed": start + len(chunk),
                          "total_requests": len(requests), "consumed_bytes": consumed_bytes(data_root),
                          "remaining_failures": sum(r["status"] != "success" for r in receipts)}), flush=True)
        start += len(chunk)
        batch_index += 1
    completed = []
    for index in range(batch_index):
        path = receipts_dir / f"batch-{index:03d}-completed.json"
        completed.extend(json.loads(path.read_bytes()))
    if ([row["source_path"] for row in completed] != [row["source_path"] for row in requests]
            or len({row["source_path"] for row in completed}) != len(requests)):
        raise ValueError("completed census differs from frozen population")
    if other_source_bytes + consumed_bytes(data_root) > config["max_download_bytes"]:
        raise ValueError("completed sources exceed aggregate download ceiling")
    manifest = {"provenance": provenance, "config": config,
                "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
                "requests": completed, "other_source_bytes_reserved": other_source_bytes}
    (data_root / "census-completed.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode())
    return manifest


def main() -> None:
    """Parse frozen source/config locations; no outcome-dependent selection."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--other-source-bytes", type=int, required=True)
    args = parser.parse_args()
    if args.other_source_bytes < 0:
        raise ValueError("nonnegative other-source reserve required")
    manifest = acquire(args.data_root, json.loads(args.config.read_bytes()), args.other_source_bytes)
    print(json.dumps({"completed_requests": len(manifest["requests"])}))


if __name__ == "__main__":
    main()
