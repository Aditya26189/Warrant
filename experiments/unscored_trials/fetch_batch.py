"""Execute an explicit bounded request manifest; never discover by outcomes."""

from __future__ import annotations

import argparse
import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sources import retrieve_cached


def run(manifest: Path, data_root: Path, workers: int, budget_bytes: int) -> list[dict]:
    """Fetch named sources, rejecting path escape and a worst-case budget overrun."""
    requests = json.loads(manifest.read_bytes())
    if any(type(row["limit_bytes"]) is not int or row["limit_bytes"] <= 0
           or not math.isfinite(row["timeout"]) or row["timeout"] <= 0
           for row in requests):
        raise ValueError("each request requires positive finite limits")
    if workers < 1 or sum(row["limit_bytes"] for row in requests) > budget_bytes:
        raise ValueError("worker count or worst-case request budget invalid")
    root = data_root.resolve()
    destinations = [(root / row["path"]).resolve() for row in requests]
    if len(set(destinations)) != len(destinations):
        raise ValueError("duplicate destination")
    for destination in destinations:
        if not destination.is_relative_to(root):
            raise ValueError("destination escapes working-data directory")

    def fetch(item: tuple[dict, Path]) -> dict:
        row, destination = item
        receipt = retrieve_cached(row["url"], destination, row["limit_bytes"], row["timeout"])
        return {"path": row["path"], **receipt}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        receipts = list(pool.map(fetch, zip(requests, destinations, strict=True)))
    print(json.dumps({
        "requests": len(receipts),
        "success": sum(row["status"] == "success" for row in receipts),
        "bytes": sum(row.get("size_bytes", 0) for row in receipts),
        "failed_paths": [row["path"] for row in receipts if row["status"] != "success"],
    }, indent=2))
    return receipts


def main() -> None:
    """Keep request selection in the supplied recorded manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("data_root", type=Path)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--budget-bytes", type=int, required=True)
    args = parser.parse_args()
    receipts = run(args.manifest, args.data_root, args.workers, args.budget_bytes)
    if any(row["status"] != "success" for row in receipts):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
