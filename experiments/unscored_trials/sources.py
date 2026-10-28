"""Bounded public-source retrieval for the unscored-trials decision study.

Keep downloaded bytes outside Git and bind each successful or failed request
to its URL. This prevents an inaccessible source being mistaken for an empty
evaluation population. No upstream code is executed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def retrieve(url: str, destination: Path, limit_bytes: int, timeout: float) -> dict:
    """Retain immutable input bytes and a receipt, without unbounded retries."""
    if limit_bytes <= 0 or timeout <= 0:
        raise ValueError("positive size limit and timeout required")
    receipt_path = destination.with_name(destination.name + ".receipt.json")
    if destination.exists() or receipt_path.exists():
        raise FileExistsError("refusing to replace prior retrieval evidence")
    destination.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "limit_bytes": limit_bytes,
        "timeout_seconds": timeout,
    }
    try:
        request = Request(url, headers={"User-Agent": "Warrant-unscored-audit/1.0"})
        with urlopen(request, timeout=timeout) as response:
            data = response.read(limit_bytes + 1)
            receipt["bytes_read"] = len(data)
            if len(data) > limit_bytes:
                raise ValueError("response exceeds configured byte limit")
            receipt.update(
                status="success", http_status=response.status,
                final_url=response.url, size_bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                pagination_link=response.headers.get("Link"),
                content_length=response.headers.get("Content-Length"),
            )
        destination.write_bytes(data)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        receipt.update(status="failed", error_type=type(exc).__name__, error=str(exc))
    receipt_path.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    return receipt


def retrieve_cached(url: str, destination: Path, limit_bytes: int, timeout: float) -> dict:
    """Reuse only hash-verified successful bytes from the identical request."""
    receipt_path = destination.with_name(destination.name + ".receipt.json")
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_bytes())
        if receipt.get("status") != "success" or receipt.get("url") != url:
            raise ValueError("prior failure or request mismatch; retain it and use a new path")
        data = destination.read_bytes()
        if (len(data) != receipt["size_bytes"] or len(data) > limit_bytes
                or hashlib.sha256(data).hexdigest() != receipt["sha256"]):
            raise ValueError("cached bytes do not match receipt or configured limit")
        return receipt
    return retrieve(url, destination, limit_bytes, timeout)


def main() -> None:
    """Parse a single public request; selection remains in the frozen plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("destination", type=Path)
    parser.add_argument("--limit-bytes", type=int, required=True)
    parser.add_argument("--timeout", type=float, required=True)
    args = parser.parse_args()
    receipt = retrieve(args.url, args.destination, args.limit_bytes, args.timeout)
    print(json.dumps(receipt, indent=2))
    if receipt["status"] != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
