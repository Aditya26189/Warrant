"""Capture the approved B1 index responses; never screen papers or outcomes.

Run once from a clean research checkout after committing A01. Raw HTTP entity
bytes and UTC request/response provenance are retained. Any access/schema/cap
failure stops the run; no alternate engine or retry is used.
"""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

QUERY = ('(ti:"prompt injection" OR abs:"prompt injection" OR '
         'ti:"prompt-injection" OR abs:"prompt-injection") AND '
         '(ti:detect* OR abs:detect* OR ti:guardrail* OR abs:guardrail* OR '
         'ti:classif* OR abs:classif*) AND '
         'submittedDate:[202401010000 TO 202610162359]')
BASE = Path(__file__).resolve().parent
OUT = BASE / "retrieval-01"
NS = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/"}


def now() -> str:
    """Record actual UTC rather than the bibliographic cutoff."""
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data: bytes) -> str:
    """Bind preserved bytes without treating Git as a trusted timestamp."""
    return hashlib.sha256(data).hexdigest()


def capture(url: str, source: str, offset: int | None, manifest: dict) -> bytes:
    """Preserve success/error bodies before any parsing; print no abstracts."""
    item = {"source": source, "requested_url": url, "offset": offset,
            "started_utc": now(), "http_status": None, "body_file": None,
            "body_sha256": None, "body_bytes": None}
    manifest["requests"].append(item)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Warrant-B1-Metadata-Pilot/1.0", "Accept-Encoding": "identity"})
        try:
            response = urllib.request.urlopen(req, timeout=45)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            body = response.read()
            item["http_status"] = response.code
            item["response_url"] = response.geturl()
            item["response_headers"] = {k: v for k, v in response.headers.items()
                                        if k.lower() in {"content-type", "content-encoding", "date", "etag", "last-modified", "retry-after"}}
        item["finished_utc"] = now()
        name = f"{len(manifest['requests']):02d}-{source}-{offset if offset is not None else 'bulk'}.body"
        (OUT / name).write_bytes(body)
        item.update(body_file=name, body_sha256=digest(body), body_bytes=len(body))
        if item["http_status"] != 200:
            raise RuntimeError(f"ACCESS_BLOCKED: {source} HTTP {item['http_status']}")
        if len(body) >= 10_000_000:
            raise RuntimeError(f"RAW_FILE_REVIEW_REQUIRED: {source} raw response exceeds staging limit")
        return body
    except Exception as exc:
        item.setdefault("finished_utc", now())
        item["error_type"] = type(exc).__name__
        item["error"] = str(exc)
        raise


def paged(source: str, manifest: dict) -> None:
    """Capture prescribed pagination and stop on unknown schema or truncation."""
    total_seen = None
    seen = 0
    for offset in range(0, 500, 100):
        if source == "arxiv":
            params = urllib.parse.urlencode({"search_query": QUERY, "sortBy": "submittedDate", "sortOrder": "ascending", "start": offset, "max_results": 100})
            url = "https://export.arxiv.org/api/query?" + params
        else:
            field = source.split("-", 1)[1]
            url = ("https://api2.openreview.net/notes/search?term=prompt%20injection&type=terms&content="
                   + field + "&source=forum&limit=100&offset=" + str(offset))
        body = capture(url, source, offset, manifest)
        if source == "arxiv":
            root = ET.fromstring(body)
            if root.tag != "{" + NS["a"] + "}feed":
                raise RuntimeError("SCHEMA_BLOCKED: expected Atom feed")
            total = int(root.findtext("o:totalResults", namespaces=NS))
            start = int(root.findtext("o:startIndex", namespaces=NS))
            rows = root.findall("a:entry", NS)
            if start != offset or any("api/errors" in (r.findtext("a:id", default="", namespaces=NS)) for r in rows):
                raise RuntimeError("SCHEMA_BLOCKED: arxiv pagination/error entry")
        else:
            result = json.loads(body)
            total = result["count"]
            rows = result["notes"]
            if type(total) is not int or not isinstance(rows, list):
                raise RuntimeError("SCHEMA_BLOCKED: OpenReview notes/count")
        if total < 0 or len(rows) > 100 or (total_seen is not None and total != total_seen):
            raise RuntimeError("SCHEMA_BLOCKED: inconsistent pagination totals")
        manifest["requests"][-1].update(source_total=total, returned_records=len(rows))
        total_seen = total
        if total > 500:
            raise RuntimeError(f"SOURCE_CAP_BLOCKED: {source} total {total} exceeds 500")
        seen += len(rows)
        if seen == total:
            return
        if len(rows) != 100 or seen > total:
            raise RuntimeError("SCHEMA_BLOCKED: incomplete or overlapping pagination")
        time.sleep(3.1)
    raise RuntimeError("SOURCE_CAP_BLOCKED: remaining records after prescribed pages")


def main() -> int:
    """Refuse dirty provenance and bind all partial responses to the lock."""
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError("Refusing retrieval from dirty working tree")
    if OUT.exists():
        raise RuntimeError("Refusing to overwrite an existing snapshot")
    lock_bytes = (BASE / "PROTOCOL_LOCK.json").read_bytes()
    lock = json.loads(lock_bytes)
    for name, sha in lock["files"].items():
        if digest((BASE / name).read_bytes()) != sha:
            raise RuntimeError("Protocol lock mismatch: " + name)
    OUT.mkdir()
    manifest = {"started_utc": now(), "status": "RETRIEVAL_RUNNING",
                "source_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "source_tree_clean_at_start": True, "python": platform.python_version(),
                "capture_script_sha256": digest(Path(__file__).read_bytes()),
                "protocol_lock_sha256": digest(lock_bytes), "bibliographic_cutoff": "2026-10-17T00:00:00Z",
                "arxiv_query": QUERY, "per_query_cap": 500, "unique_screening_cap": 500,
                "requests": [], "screening": "NOT_RUN", "selection": "NOT_RUN", "outcome_extraction": "NOT_RUN"}
    code = 0
    try:
        paged("arxiv", manifest)
        body = capture("https://aclanthology.org/anthology+abstracts.bib.gz", "acl", None, manifest)
        gzip.decompress(body)  # Validate transport format only; no screening.
        paged("openreview-title", manifest)
        paged("openreview-abstract", manifest)
        manifest["status"] = "RAW_RETRIEVAL_COMPLETE_NOT_SCREENED"
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, ET.ParseError) as exc:
        code = 2
        manifest.update(status="FRAME_BLOCKED", blocker_type=type(exc).__name__, blocker=str(exc))
    finally:
        manifest["finished_utc"] = now()
        raw = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        (OUT / "RETRIEVAL_MANIFEST.json").write_text(raw, encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("status", "source_git_commit", "started_utc", "finished_utc")}))
    if code:
        print(manifest["blocker"])
    return code


if __name__ == "__main__":
    sys.exit(main())
