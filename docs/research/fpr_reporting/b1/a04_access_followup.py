"""Primary bibliographic follow-up for inaccessible exact revisions, without substitution."""
from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

import a04_evidence as e


def history(raw: bytes) -> list[dict]:
    """Project only official revision labels, UTC dates and withdrawal markers."""
    soup = BeautifulSoup(raw, "html.parser")
    block = soup.select_one(".submission-history")
    if block is None:
        raise ValueError("SUBMISSION_HISTORY_UNAVAILABLE")
    text = block.get_text(" ", strip=True)
    parts = re.split(r"\[(v\d+)\]", text)
    records = []
    for n in range(1, len(parts), 2):
        match = re.search(r"[A-Z][a-z]{2},\s+\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s+UTC", parts[n + 1])
        if not match:
            raise ValueError("REVISION_DATE_UNRESOLVED")
        stamp = datetime.strptime(match.group(), "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
        records.append({"revision": parts[n], "public_utc": stamp.isoformat(),
                        "withdrawn_in_history": bool(re.search(r"\bwithdrawn\b", parts[n + 1], re.I))})
    if not records:
        raise ValueError("REVISION_HISTORY_EMPTY")
    return records


def run() -> None:
    """Investigate both inaccessible members through official metadata and mirror URLs."""
    head = e.clean_head()
    config = e.read(e.CONFIG)
    requests = e.read(e.BASE / config["run_id"] / "EVIDENCE_REQUESTS.json")["source_requests"]
    cache = Path(config["cache_root"])
    outputs = []
    for request in requests:
        acquired = e.read(cache / "acquisition" / f"{request['member_id']}.json")
        if acquired["source_available"]:
            continue
        saved_path = cache / "bibliographic-followup" / f"{request['member_id']}.json"
        if saved_path.exists():
            saved_record = e.read(saved_path)
            if (saved_record["work_id"] != request["work_id"]
                    or saved_record["captured_version_id"] != request["captured_version_id"]):
                raise ValueError("FOLLOWUP_RESUME_IDENTITY_MISMATCH")
            outputs.append(saved_record)
            continue
        version = request["captured_version_id"].removeprefix("arxiv:")
        arxiv_id = version.split("v")[0]
        url = f"https://arxiv.org/abs/{arxiv_id}"
        started = e.now()
        raw, provenance = None, None
        if arxiv_id == "2410.21337":
            old_path = Path(config["legacy_cache"]) / "Q002-abs.provenance.json"
            old = e.read(old_path)
            saved = Path(old["raw_path"]).read_bytes()
            if e.sha(saved) != old["raw_sha256"]:
                raise ValueError("LEGACY_ABSTRACT_METADATA_HASH_MISMATCH")
            raw = saved
            provenance = {"source_url": old["url"], "retrieved_utc": old["finished_utc"],
                          "http_or_access_status": old["status"], "raw_source_sha256": old["raw_sha256"],
                          "locator": "div.submission-history", "mode": "VERIFIED_PRIMARY_METADATA_CACHE"}
        else:
            req = urllib.request.Request(url, headers={"User-Agent": "Warrant-B1-bibliographic-verification/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=config["timeout_seconds"]) as response:
                    if not e.official_url(response.url, config):
                        raise ValueError("UNAPPROVED_METADATA_REDIRECT")
                    raw = response.read(config["max_body_bytes"] + 1)
                    if len(raw) > config["max_body_bytes"]:
                        raise ValueError("METADATA_BODY_SIZE_LIMIT")
                digest = e.sha(raw)
                body_path = cache / "followup-raw" / digest
                body_path.parent.mkdir(parents=True, exist_ok=True)
                if not body_path.exists():
                    body_path.write_bytes(raw)
                provenance = {"source_url": url, "retrieved_utc": e.now(), "http_or_access_status": 200,
                              "raw_source_sha256": digest, "locator": "div.submission-history",
                              "mode": "OFFICIAL_PRIMARY_METADATA_RETRIEVAL"}
            except (OSError, ValueError) as exc:
                provenance = {"source_url": url, "retrieved_utc": e.now(), "http_or_access_status": getattr(exc, "code", None),
                              "raw_source_sha256": None, "locator": "METADATA_UNAVAILABLE", "mode": type(exc).__name__}
        mirror = {**request, "urls": [f"https://export.arxiv.org/pdf/{version}", f"https://export.arxiv.org/html/{version}"]}
        mirror_config = {**config, "cache_root": str(cache / "official-mirror-followup")}
        access = e.acquisition(mirror, mirror_config, {}, head)
        record = {"work_id": request["work_id"], "member_id": request["member_id"],
                  "captured_version_id": request["captured_version_id"], "metadata_provenance": provenance,
                  "revision_history": history(raw) if raw else [],
                  "official_mirror_attempts": [{k: a.get(k) for k in ("url", "status", "started_utc", "finished_utc")} for a in access["attempts"]],
                  "exact_revision_mirror_body_available": bool(access["body"]),
                  "earlier_version_substituted": False, "eligibility_decision": None,
                  "started_utc": started, "source_git_commit": head}
        e.write_new(cache / "bibliographic-followup" / f"{request['member_id']}.json", record)
        outputs.append(record)
    e.write_new(e.BASE / config["run_id"] / "PRIMARY_ACCESS_FOLLOWUPS.json", outputs)
    print(e.encoded({"followup_members": len(outputs), "older_version_substitutions": 0}).decode())


if __name__ == "__main__":
    run()
