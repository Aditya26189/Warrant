"""Bounded public GET receipts for the stopping-feedback feasibility sample.

This does not ingest a corpus or infer outcomes. Failed and revision-mismatched
responses remain evidence; returned bytes count against the same fixed cap.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import platform
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_TOTAL_BYTES = 16 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
SAFE_HEADERS = {
    "content-length", "content-type", "content-encoding", "date", "etag",
    "last-modified", "x-revision", "x-repo-commit",
}


def validate_url(url: str) -> None:
    """Reject credentials and insecure transport before opening a request."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Only absolute HTTPS URLs are accepted")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are forbidden")
    if any(ord(char) < 32 for char in url):
        raise ValueError("URL control characters are forbidden")


def validate_revision(observed: Mapping[str, Any], expected_revision: str) -> str:
    """Accept an actual response identity, never a revision request parameter.

    Conflicting identities fail even if one matches. An absent identity is
    unknown, rather than evidence that a revision parameter was respected.
    """
    if not re.fullmatch(r"[0-9a-fA-F]{40}", expected_revision):
        raise ValueError("Expected dataset revision must be a full Git SHA-1")
    identities = [
        str(value).strip().lower()
        for name, value in observed.items()
        if name.lower() in {"dataset_git_revision", "x-revision", "x-repo-commit"}
        and value is not None
    ]
    if not identities:
        raise ValueError("Response contains no dataset revision identity")
    if any(value != expected_revision.lower() for value in identities):
        raise ValueError("Response dataset revision differs from the expected pin")
    return identities[0]


class _HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> Any:
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def load_config(path: Path) -> tuple[dict[str, Any], str]:
    """Bind the exact configuration bytes before any network access."""
    raw = path.read_bytes()
    config = json.loads(raw)
    requests = config.get("requests")
    if not isinstance(requests, list) or not 1 <= len(requests) <= 64:
        raise ValueError("Configuration requires between one and 64 requests")
    cap = config.get("max_total_bytes", MAX_TOTAL_BYTES)
    if type(cap) is not int or not 1 <= cap <= MAX_TOTAL_BYTES:
        raise ValueError("Aggregate cap must be positive and at most 16 MiB")
    timeout = config.get("timeout_seconds", 30)
    if type(timeout) not in (int, float) or not 0 < timeout <= 60:
        raise ValueError("Timeout must be positive and at most 60 seconds")
    labels: set[str] = set()
    for item in requests:
        if not isinstance(item, dict):
            raise ValueError("Each request must be an object")
        label = item.get("label")
        if not isinstance(label, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", label):
            raise ValueError("Request labels must be unique safe file stems")
        if label in labels:
            raise ValueError("Request labels must be unique")
        labels.add(label)
        validate_url(item["url"])
        if type(item.get("max_bytes")) is not int or not 1 <= item["max_bytes"] <= cap:
            raise ValueError("Each body cap must be positive and within the aggregate cap")
        if "expected_revision" in item:
            validate_revision({"dataset_git_revision": item["expected_revision"]}, item["expected_revision"])
    config["max_total_bytes"] = cap
    config["timeout_seconds"] = timeout
    return config, hashlib.sha256(raw).hexdigest()


def clean_git_provenance(config_path: Path) -> dict[str, Any]:
    """Enforce the clean-source artifact rule before acquiring scientific inputs."""
    source = Path(__file__).resolve()

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(source.parent), *args], text=True, encoding="utf-8"
        ).strip()

    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    if git("status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("Scientific acquisition requires a clean Git worktree")
    for path in (source, config_path.resolve()):
        relative = path.relative_to(root).as_posix()
        git("ls-files", "--error-unmatch", relative)
    return {
        "git_root": str(root), "git_commit": git("rev-parse", "HEAD"), "dirty": False,
        "source_path": source.relative_to(root).as_posix(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }


def peak_memory() -> dict[str, Any]:
    """Report the actual Windows process high-water mark, or explicit unknown."""
    try:
        import psutil

        value = getattr(psutil.Process().memory_info(), "peak_wset", None)
        return {
            "peak_working_set_bytes": value if value and value > 0 else None,
            "memory_measurement": "psutil.Process.memory_info.peak_wset" if value and value > 0
            else "unknown: psutil exposes no positive peak_wset on this platform",
            "psutil_version": psutil.__version__,
        }
    except (ImportError, OSError) as exc:
        return {"peak_working_set_bytes": None, "memory_measurement": f"unknown: {type(exc).__name__}",
                "psutil_version": None}


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def fetch_one(item: dict[str, Any], output_dir: Path, index: int, remaining: int,
              timeout: float, opener: Any) -> dict[str, Any]:
    """Persist bounded response bytes and honest receipts, including HTTP errors."""
    started = time.perf_counter()
    cap = min(item["max_bytes"], remaining)
    payload_name = f"{index:03d}-{item['label']}.body"
    receipt: dict[str, Any] = {
        "label": item["label"], "original_url": item["url"],
        "requested_max_bytes": item["max_bytes"], "effective_max_bytes": cap,
        "expected_revision": item.get("expected_revision"), "observed_revision": None,
        "revision_observations": {},
        "status": None, "headers": {}, "body_file": payload_name,
        "body_bytes": 0, "body_sha256": None, "body_complete": False,
        "ok": False, "error": None,
    }
    digest = hashlib.sha256()
    response = None
    try:
        validate_url(item["url"])
        if cap <= 0:
            raise ValueError("Aggregate byte budget exhausted; request not opened")
        request = urllib.request.Request(
            item["url"], headers={"Accept-Encoding": "identity", "User-Agent": "bounded-stopping-feasibility/1"}
        )
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            response = exc
        receipt["status"] = response.status
        headers = {name.lower(): value for name, value in response.headers.items() if name.lower() in SAFE_HEADERS}
        receipt["headers"] = headers
        declared = int(headers["content-length"]) if "content-length" in headers else None
        if declared is not None and (declared < 0 or declared > cap):
            raise ValueError("Advertised Content-Length exceeds the remaining body cap")
        with (output_dir / payload_name).open("xb") as payload:
            while receipt["body_bytes"] < cap:
                chunk = response.read(min(CHUNK_BYTES, cap - receipt["body_bytes"]))
                if not chunk:
                    receipt["body_complete"] = True
                    break
                if len(chunk) > cap - receipt["body_bytes"]:
                    raise ValueError("Response reader violated the requested read bound")
                payload.write(chunk)
                digest.update(chunk)
                receipt["body_bytes"] += len(chunk)
            if receipt["body_bytes"] == cap and declared == cap:
                receipt["body_complete"] = True
        receipt["body_sha256"] = digest.hexdigest()
        if declared is not None and receipt["body_bytes"] != declared:
            raise ValueError("Body length differs from advertised Content-Length")
        if not receipt["body_complete"]:
            raise ValueError("Body cap reached without verified end-of-body")
        if not 200 <= receipt["status"] < 300:
            raise ValueError(f"HTTP status {receipt['status']}")
        if item.get("expected_revision"):
            identities = dict(headers)
            try:
                body = json.loads((output_dir / payload_name).read_bytes())
            except (ValueError, UnicodeDecodeError):
                body = None
            if isinstance(body, dict) and body.get("dataset_git_revision") is not None:
                identities["dataset_git_revision"] = body["dataset_git_revision"]
            receipt["revision_observations"] = {
                key: value for key, value in identities.items()
                if key in {"dataset_git_revision", "x-revision", "x-repo-commit"}
            }
            receipt["observed_revision"] = validate_revision(identities, item["expected_revision"])
        receipt["ok"] = True
    except (OSError, ValueError, http.client.HTTPException) as exc:
        # Redacted exception text avoids echoing a redirect's temporary signed URL.
        detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        receipt["error"] = {"kind": type(exc).__name__, "detail": detail[:300]}
    finally:
        if response is not None:
            response.close()
        if (output_dir / payload_name).exists():
            receipt["body_sha256"] = digest.hexdigest()
        else:
            receipt["body_file"] = None
        receipt["wall_seconds"] = time.perf_counter() - started
        _write_json(output_dir / f"{index:03d}-{item['label']}.receipt.json", receipt)
    return receipt


def run(config_path: Path, output_dir: Path, opener: Any = None) -> dict[str, Any]:
    """Acquire only the explicitly configured sample into a new external directory."""
    started = time.perf_counter()
    config, config_hash = load_config(config_path)
    provenance = clean_git_provenance(config_path)
    root = Path(provenance.pop("git_root"))
    output_dir = output_dir.resolve()
    if output_dir == root or root in output_dir.parents:
        raise ValueError("Raw payload output must be outside the Git worktree")
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise ValueError("Output must be a new or empty directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    opener = opener or urllib.request.build_opener(_HTTPSRedirect())
    report: dict[str, Any] = {
        "schema_version": 1, "started_utc": datetime.now(timezone.utc).isoformat(),
        "provenance": {**provenance, "config_sha256": config_hash},
        "environment": {"python_version": platform.python_version(), "platform": platform.platform()},
        "max_total_bytes": config["max_total_bytes"], "total_body_bytes": 0,
        "requests": [], "complete": False,
    }
    _write_json(output_dir / "acquisition.json", report)
    for index, item in enumerate(config["requests"]):
        receipt = fetch_one(item, output_dir, index,
                            config["max_total_bytes"] - report["total_body_bytes"],
                            config["timeout_seconds"], opener)
        report["requests"].append(receipt)
        report["total_body_bytes"] += receipt["body_bytes"]
        assert report["total_body_bytes"] <= config["max_total_bytes"]
        report["wall_seconds"] = time.perf_counter() - started
        report.update(peak_memory())
        _write_json(output_dir / "acquisition.json", report)
    report["complete"] = all(item["ok"] for item in report["requests"])
    report["wall_seconds"] = time.perf_counter() - started
    report.update(peak_memory())
    _write_json(output_dir / "acquisition.json", report)
    return report


def main() -> int:
    """Expose acquisition only; no model execution or experiment is available."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.config, args.output_dir)
    print(json.dumps({"complete": report["complete"], "total_body_bytes": report["total_body_bytes"],
                      "wall_seconds": report["wall_seconds"]}))
    return 0 if report["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
