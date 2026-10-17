"""Continue the fixed B1 capture after lossless large-response packaging.

This only resolves a local storage guard, never a source access/schema/cap
failure. No prior query is repeated and no protocol parameter is changed.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET

import capture_metadata as capture


def main() -> int:
    """Validate the exact completed checkpoint before remaining fixed queries."""
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError("Refusing continuation from dirty checkout")
    base = Path(__file__).resolve().parent
    prior = base / "retrieval-01"
    prior_bytes = (prior / "RETRIEVAL_MANIFEST.json").read_bytes()
    checkpoint = json.loads(prior_bytes)
    assert checkpoint["blocker"] == "RAW_FILE_REVIEW_REQUIRED: acl raw response exceeds staging limit"
    assert checkpoint["requests"][-1]["source"] == "acl"
    assert len(checkpoint["requests"]) == 5
    ids = []
    for item in checkpoint["requests"]:
        assert item["http_status"] == 200
        body = (prior / item["body_file"]).read_bytes()
        assert capture.digest(body) == item["body_sha256"]
        if item["source"] == "arxiv":
            root = ET.fromstring(body)
            ids.extend(e.findtext("a:id", namespaces=capture.NS) for e in root.findall("a:entry", capture.NS))
    assert len(ids) == len(set(ids)) == checkpoint["requests"][0]["source_total"]
    storage_bytes = (prior / "STORAGE_MANIFEST.json").read_bytes()
    storage = json.loads(storage_bytes)
    chunks = []
    for part in storage["parts_in_concatenation_order"]:
        chunk = (prior / part["file"]).read_bytes()
        assert len(chunk) == part["bytes"] < 10_000_000
        assert capture.digest(chunk) == part["sha256"]
        chunks.append(chunk)
    acl = b"".join(chunks)
    assert capture.digest(acl) == storage["original_sha256"]
    assert acl == (prior / storage["original_file"]).read_bytes()
    gzip.decompress(acl)
    lock_bytes = (base / "PROTOCOL_LOCK.json").read_bytes()
    assert capture.digest(lock_bytes) == checkpoint["protocol_lock_sha256"]
    for name, sha in json.loads(lock_bytes)["files"].items():
        assert capture.digest((base / name).read_bytes()) == sha
    out = base / "retrieval-02"
    if out.exists():
        raise RuntimeError("Refusing to overwrite continuation snapshot")
    out.mkdir()
    capture.OUT = out
    manifest = {"started_utc": capture.now(), "status": "RETRIEVAL_RUNNING",
                "source_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "source_tree_clean_at_start": True, "python": platform.python_version(),
                "continuation_script_sha256": capture.digest(Path(__file__).read_bytes()),
                "capture_script_sha256": capture.digest((base / "capture_metadata.py").read_bytes()),
                "prior_manifest_sha256": capture.digest(prior_bytes),
                "storage_manifest_sha256": capture.digest(storage_bytes),
                "protocol_lock_sha256": capture.digest(lock_bytes),
                "bibliographic_cutoff": "2026-10-17T00:00:00Z",
                "arxiv_records_preserved": len(ids), "acl_raw_bytes_preserved": len(acl),
                "continuation_reason": "LOCAL_STORAGE_PACKAGING_RESOLVED_NO_PROTOCOL_CHANGE",
                "prior_queries_repeated": False, "requests": [], "per_query_cap": 500,
                "unique_screening_cap": 500, "screening": "NOT_RUN",
                "selection": "NOT_RUN", "outcome_extraction": "NOT_RUN"}
    code = 0
    try:
        capture.paged("openreview-title", manifest)
        capture.paged("openreview-abstract", manifest)
        manifest["status"] = "RAW_RETRIEVAL_COMPLETE_NOT_SCREENED"
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, ET.ParseError) as exc:
        code = 2
        manifest.update(status="FRAME_BLOCKED", blocker_type=type(exc).__name__, blocker=str(exc))
    finally:
        manifest["finished_utc"] = capture.now()
        (out / "RETRIEVAL_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: manifest[k] for k in ("status", "source_git_commit", "started_utc", "finished_utc")}))
    if code:
        print(manifest["blocker"])
    return code


if __name__ == "__main__":
    sys.exit(main())
