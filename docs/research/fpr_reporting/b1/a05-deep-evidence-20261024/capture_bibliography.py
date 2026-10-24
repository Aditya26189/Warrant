"""Capture known-work publisher metadata without displaying abstracts or results."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import subprocess
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "a05-custodian-adjudication-20261023"
CACHE = HERE.parents[5] / "fpr-a05-deep-20261024" / "publisher-metadata"
FIELDS = {"citation_title", "citation_author", "citation_doi", "citation_publication_date",
          "citation_online_date", "citation_date", "citation_pdf_url", "citation_publisher",
          "citation_journal_title", "citation_conference_title", "dc.title", "dc.creator",
          "dc.date", "dc.identifier", "dc.publisher", "dcterms.issued", "dcterms.modified",
          "article:published_time", "article:modified_time"}


def sha(raw: bytes) -> str:
    """Commit exact acquisition bytes, including unsuccessful captures."""
    return hashlib.sha256(raw).hexdigest()


def known_requests() -> list[dict]:
    """Use only known frozen works with a documented publisher-version question."""
    book = {r["review_id"]: r for r in json.loads((PREVIOUS / "SOURCE_CASEBOOK.json").read_bytes())["cases"]}
    rows = json.loads((PREVIOUS / "CUSTODIAN_FRAME_PROPOSAL.json").read_bytes())["rows"]
    result = []
    for row in rows:
        if row["decision"] == "EXCLUDE" or not row["bibliography"]["version_issues"]:
            continue
        if not row["work_id"].startswith("doi:"):
            raise ValueError("EXPECTED_KNOWN_DOI_WORK")
        case = book[row["review_id"]]
        registrations = [x for x in case["evidence"] if x["evidence_id"].startswith("R01-DOI-")]
        result.append({"review_id": row["review_id"], "work_id": row["work_id"],
            "url": "https://doi.org/" + row["work_id"].removeprefix("doi:"),
            "prior_registration_evidence_ids": [x["evidence_id"] for x in registrations]})
    return result


def capture(request: dict, run: str, head: str) -> dict:
    """Save raw before parsing; return bibliographic allowlist fields only."""
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    raw = b""
    response = None
    error = None
    try:
        response = requests.get(request["url"], timeout=25, allow_redirects=True,
                                headers={"User-Agent": "Warrant-B1-bibliographic-verification/1.0"})
        raw = response.content
    except requests.RequestException as exc:
        error = type(exc).__name__ + ": " + str(exc)
    raw_path = CACHE / "private-raw" / sha(raw)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if not raw_path.exists():
        with raw_path.open("xb") as stream:
            stream.write(raw)
    fields = []
    if response is not None and "html" in response.headers.get("Content-Type", ""):
        soup = BeautifulSoup(raw, "html.parser")
        for node in soup.select("meta[name],meta[property]"):
            key = str(node.get("name", node.get("property", ""))).casefold()
            if key in FIELDS:
                fields.append({"field": key, "value": str(node.get("content", "")),
                               "locator": "meta[" + ("name" if node.has_attr("name") else "property") + "='" + key + "']"})
    result = {**request, "actor": "ROOT_BIBLIOGRAPHIC_CAPTURE_PROVIDER_ONLY", "source_git_commit": head,
        "started_utc": started, "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "http_status": response.status_code if response is not None else None,
        "final_url": response.url if response is not None else None,
        "content_type": response.headers.get("Content-Type") if response is not None else None,
        "last_modified": response.headers.get("Last-Modified") if response is not None else None,
        "raw_source_sha256": sha(raw), "private_raw_path": str(raw_path), "metadata_fields": fields,
        "error": error, "status": "PROVIDER_CAPTURE_NOT_RESTRICTION_RELEASED", "eligibility_decision": None,
        "boundary": "Metadata allowlist only; no abstracts/description/results/claims displayed or parsed."}
    path = CACHE / (run + "-" + request["review_id"] + ".json")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return {"review_id": request["review_id"], "http_status": result["http_status"],
            "metadata_fields": len(fields), "error_type": error.split(":", 1)[0] if error else None}


def main() -> None:
    """Run one explicitly named metadata-only known-work verification attempt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    if not args.run.replace("-", "").isalnum():
        raise ValueError("UNSAFE_RUN_NAME")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=HERE, text=True).strip():
        raise ValueError("DIRTY_TREE")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    CACHE.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = []
        for request in known_requests():
            futures.append(pool.submit(capture, request, args.run, head))
            time.sleep(0.5)
        for future in futures:
            print(json.dumps(future.result(), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
