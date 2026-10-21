"""Provide pinned source identity and primary bibliography for existing requests.

No discovery queries, preferred-version decisions or eligibility labels are made.
Original captures remain immutable; new provenance states its exact evidence basis.
"""
from __future__ import annotations

import argparse
import calendar
import concurrent.futures
import json
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import fitz
from bs4 import BeautifulSoup

import a04_access_followup as followup
import a04_evidence as e
import a04_recovery_intake as recovery

_LOCK = threading.Lock()
_LAST = 0.0


def identity_text(text: str) -> str:
    """Compare work titles without releasing the possibly result-bearing strings."""
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def month_interval(year: str, month: str) -> tuple[str, str] | None:
    """Represent actual month precision without inventing a publication day."""
    try:
        number = list(calendar.month_name).index(month.title())
        if number == 0:
            return None
        y = int(year)
        return f"{y:04d}-{number:02d}-01", f"{y:04d}-{number:02d}-{calendar.monthrange(y, number)[1]}"
    except (ValueError, TypeError):
        return None


def source_binding(request: dict, metadata: dict, acquired: dict) -> dict:
    """Separate exact in-body revision proof from explicit primary URL/identity proof."""
    if (e.sha(e.encoded(metadata)) != request["metadata_record_sha256"]
            or acquired["request_sha256"] != e.sha(e.encoded(request))):
        raise ValueError("RECOVERY_INPUT_COMMITMENT_MISMATCH")
    row = {k: request[k] for k in ("work_id", "review_id", "member_id", "captured_version_id", "metadata_record_sha256")}
    row.update({"source_binding_basis": "SOURCE_UNAVAILABLE", "method_release_supported": False,
                "body_exact_revision_self_identified": False, "body_title_matches_frozen_work": None,
                "captured_title_sha256": e.sha(metadata["title"].encode()),
                "captured_title_identity_sha256": e.sha(identity_text(metadata["title"]).encode()),
                "captured_authors_sha256": e.sha(metadata["authors_raw"].encode()),
                "captured_date_fields": request["bibliography"], "cutoff": "2026-10-17T00:00:00Z",
                "protocol_preferred_version": None, "eligibility_decision": None,
                "limitation_codes": ["PROTOCOL_PREFERRED_VERSION_NOT_ADJUDICATED"]})
    body = acquired["body"]
    if not body:
        row["limitation_codes"].append("PRIMARY_BODY_UNAVAILABLE")
        return row
    raw = Path(body["raw_path"]).read_bytes()
    if e.sha(raw) != body["sha256"]:
        raise ValueError("RECOVERY_SOURCE_BODY_HASH_CHANGED")
    parsed = urllib.parse.urlparse(body["url"])
    if parsed.scheme != "https" or parsed.hostname not in {"arxiv.org", "export.arxiv.org", "aclanthology.org"}:
        raise ValueError("RECOVERY_SOURCE_HOST_UNAPPROVED")
    if body["url"] not in request["urls"]:
        raise ValueError("RECOVERY_SOURCE_URL_NOT_REQUESTED")
    if body.get("final_url") and body["final_url"].rstrip("/") != body["url"].rstrip("/"):
        raise ValueError("RECOVERY_SOURCE_RECORDED_REDIRECT_MISMATCH")
    row["body"] = {k: body[k] for k in ("raw_path", "url", "kind", "sha256", "version_state", "finished_utc", "status")}
    row["recorded_final_url"] = body.get("final_url")
    interval = month_interval(metadata["year"], metadata["month"]) if metadata["source"] == "acl" else None
    row["captured_publication_date_interval"] = list(interval) if interval else None
    date_ok = (bool(metadata["updated"] and datetime.fromisoformat(metadata["updated"].replace("Z", "+00:00"))
                    <= datetime.fromisoformat(row["cutoff"].replace("Z", "+00:00")))
               if metadata["source"] == "arxiv" else bool(interval and interval[1] < "2026-10-17"))
    if not date_ok:
        row["limitation_codes"].append("CAPTURED_SOURCE_DATE_CUTOFF_UNRESOLVED")
    version = (request["captured_version_id"] or "").removeprefix("arxiv:")
    if body["kind"] == "HTML":
        e.validate_body(raw, body["url"])
        exact = body["version_state"] == "EXACT_VERSION_SELF_LINK"
        row.update(body_exact_revision_self_identified=exact, source_binding_basis="EXACT_VERSION_SELF_LINK",
                   method_release_supported=bool(exact and date_ok))
        return row
    with fitz.open(stream=raw, filetype="pdf") as pdf:
        text = pdf[0].get_text()
        pdf_metadata_title = (pdf.metadata or {}).get("title", "")
        title = identity_text(metadata["title"])
        title_match = len(title) >= 20 and (title in identity_text(text) or title == identity_text(pdf_metadata_title))
        row["first_pdf_page_text_sha256"] = e.sha(text.encode())
    row["body_title_matches_frozen_work"] = title_match
    if not body.get("final_url"):
        row["limitation_codes"].append("RECORDED_REQUEST_URL_WITHOUT_SAVED_FINAL_REDIRECT_FIELD")
    exact = body["version_state"] == "EXACT_VERSION_IN_BODY"
    row["body_exact_revision_self_identified"] = exact
    if exact:
        row.update(source_binding_basis="EXACT_VERSION_IN_BODY", method_release_supported=bool(date_ok))
    elif metadata["source"] == "arxiv" and version and parsed.path == "/pdf/" + version and title_match:
        row.update(source_binding_basis="RECORDED_OFFICIAL_EXACT_VERSION_URL_AND_WORK_TITLE_MATCH",
                   method_release_supported=bool(date_ok))
        row["limitation_codes"].append("IN_BODY_REVISION_IDENTIFIER_NOT_FOUND")
    elif metadata["source"] == "acl" and body["url"] == metadata["url"].rstrip("/") + ".pdf" and title_match:
        row.update(source_binding_basis="OFFICIAL_ANTHOLOGY_PUBLICATION_ID_AND_WORK_TITLE_MATCH",
                   method_release_supported=bool(date_ok))
        row["limitation_codes"].append("PUBLICATION_ID_AND_FROZEN_MONTH_BASIS_NOT_ARXIV_REVISION_STAMP")
    else:
        row["source_binding_basis"] = "SOURCE_IDENTITY_REQUIRES_ADDITIONAL_VERIFICATION"
        row["limitation_codes"].append("WORK_TITLE_IDENTITY_NOT_ESTABLISHED")
    return row


def inputs() -> tuple[list, dict]:
    """Bind each requested member to its original metadata commitment."""
    gaps = e.read(e.BASE / recovery.RUN / "SOURCE_GAP_REQUESTS.json")
    mids = {mid for row in gaps for mid in row["member_ids"]}
    requests = e.read(e.BASE / e.read(e.CONFIG)["run_id"] / "EVIDENCE_REQUESTS.json")["source_requests"]
    metadata = [json.loads(line) for line in (e.BASE / "a02-metadata/metadata_union.jsonl").read_text(encoding="utf-8").splitlines()]
    selected, by_mid = [], {}
    for req in requests:
        if req["member_id"] not in mids:
            continue
        raw = metadata[int(req["member_id"][1:]) - 1]
        if e.sha(e.encoded(raw)) != req["metadata_record_sha256"]:
            raise ValueError("RECOVERY_METADATA_MEMBER_COMMITMENT_CHANGED")
        selected.append(req)
        by_mid[req["member_id"]] = raw
    if len(selected) != len(mids):
        raise ValueError("RECOVERY_SOURCE_REQUEST_MEMBERSHIP_MISMATCH")
    return selected, by_mid


def build_bindings(head: str) -> None:
    """Freeze new explanatory source bindings without altering original receipts."""
    requests, metadata = inputs()
    cache = Path(e.read(e.CONFIG)["cache_root"])
    rows = []
    for req in requests:
        acquired = e.read(cache / "acquisition" / f"{req['member_id']}.json")
        saved = recovery.CACHE / "source-bindings" / f"{req['member_id']}.json"
        if saved.exists():
            row = e.read(saved)
            if (row["metadata_record_sha256"] != req["metadata_record_sha256"]
                    or row["original_acquisition_receipt_sha256"] != e.sha(e.encoded(acquired))):
                raise ValueError("RECOVERY_BINDING_RESUME_INPUT_CHANGED")
            if row.get("body") and e.sha(Path(row["body"]["raw_path"]).read_bytes()) != row["body"]["sha256"]:
                raise ValueError("RECOVERY_BINDING_RESUME_BODY_CHANGED")
            rows.append(row)
            continue
        row = source_binding(req, metadata[req["member_id"]], acquired)
        row.update({"source_git_commit": head, "checked_utc": e.now(),
                    "original_acquisition_receipt_sha256": e.sha(e.encoded(acquired))})
        e.write_new(recovery.CACHE / "source-bindings" / f"{req['member_id']}.json", row)
        rows.append(row)
    e.write_new(e.BASE / recovery.RUN / "SOURCE_BINDINGS.json", rows)
    print(json.dumps({"members": len(rows), "supported_method_sources": sum(r["method_release_supported"] for r in rows),
                      "source_identity_unresolved": [r["member_id"] for r in rows if not r["method_release_supported"]]}, sort_keys=True))


def primary_get(url: str) -> tuple[bytes | None, dict]:
    """Capture only direct official bibliographic pages, with bounded retries."""
    global _LAST
    parsed = urllib.parse.urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname not in {"arxiv.org", "aclanthology.org"}
            or parsed.query or parsed.fragment or parsed.username):
        raise ValueError("BIBLIOGRAPHIC_URL_UNAPPROVED")
    attempts = []
    for attempt in range(2):
        with _LOCK:
            delay = .8 - (time.monotonic() - _LAST)
            if delay > 0:
                time.sleep(delay)
            _LAST = time.monotonic()
        record = {"url": url, "started_utc": e.now()}
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Warrant-controlled-bibliographic-verification/1.0"})
            with urllib.request.urlopen(req, timeout=25) as response:
                final = urllib.parse.urlparse(response.url)
                if final.hostname != parsed.hostname or final.scheme != "https" or final.path.rstrip("/") != parsed.path.rstrip("/"):
                    raise ValueError("BIBLIOGRAPHIC_UNAPPROVED_REDIRECT")
                raw = response.read(5_000_001)
                if len(raw) > 5_000_000:
                    raise ValueError("BIBLIOGRAPHIC_BODY_TOO_LARGE")
                record.update(status=response.status, final_url=response.url)
            digest = e.sha(raw)
            path = recovery.CACHE / "bibliographic-raw" / digest
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(raw)
            elif path.read_bytes() != raw:
                raise ValueError("BIBLIOGRAPHIC_CACHE_HASH_COLLISION")
            record.update(finished_utc=e.now(), raw_source_sha256=digest, raw_path=str(path))
            attempts.append(record)
            return raw, {"attempts": attempts, "source_url": url, "raw_source_sha256": digest,
                         "retrieved_utc": record["finished_utc"], "http_or_access_status": record["status"]}
        except (OSError, ValueError) as exc:
            record.update(finished_utc=e.now(), status=getattr(exc, "code", None), error_type=type(exc).__name__)
            attempts.append(record)
            if isinstance(exc, urllib.error.HTTPError) and exc.code in {400, 401, 403, 404, 410}:
                break
            if attempt == 0:
                time.sleep(3)
    return None, {"attempts": attempts, "source_url": url, "raw_source_sha256": None,
                  "retrieved_utc": e.now(), "http_or_access_status": "UNAVAILABLE_RECORDED_ATTEMPTS"}


def bibliographic_fields(raw: bytes, source: str) -> dict:
    """Allowlist official dates, version history and identifiers; never emit abstracts."""
    soup = BeautifulSoup(raw, "html.parser")
    fields = {"revision_history": [], "publication_date_literals": [], "linked_identifiers": [],
              "title_identity_sha256": None,
              "title_sha256": None, "authors_sha256": [], "locators": [], "uncertainty_codes": []}
    if source == "arxiv":
        try:
            fields["revision_history"] = followup.history(raw)
            fields["locators"].append("div.submission-history")
        except ValueError:
            fields["uncertainty_codes"].append("OFFICIAL_REVISION_HISTORY_NOT_PARSED")
    for tag in soup.find_all("meta"):
        key = (tag.get("name") or tag.get("property") or "").casefold()
        value = tag.get("content", "")
        if key == "citation_title":
            fields["title_sha256"] = e.sha(value.encode())
            fields["title_identity_sha256"] = e.sha(identity_text(value).encode())
        elif key == "citation_author":
            fields["authors_sha256"].append(e.sha(value.encode()))
        elif key in {"citation_publication_date", "citation_date", "citation_online_date"} and re.fullmatch(r"\d{4}(?:[-/]\d{1,2}){0,2}", value):
            fields["publication_date_literals"].append({"metadata_field": key, "value": value})
        elif key == "citation_doi" and re.fullmatch(r"10\.\d{4,9}/[^\s<>]+", value):
            fields["linked_identifiers"].append("doi:" + value)
        if key.startswith("citation_") and key in {"citation_title", "citation_author", "citation_publication_date", "citation_date", "citation_online_date", "citation_doi"}:
            fields["locators"].append("meta[name='" + key + "']")
    if not fields["revision_history"] and not fields["publication_date_literals"]:
        fields["uncertainty_codes"].append("OFFICIAL_PUBLIC_DATE_NOT_ESTABLISHED")
    return fields


def bibliographic_one(request: dict, metadata: dict, head: str) -> dict:
    """Resume one immutable official metadata response for an existing membership."""
    path = recovery.CACHE / "bibliographic" / f"{request['member_id']}.json"
    if path.exists():
        row = e.read(path)
        if row["metadata_record_sha256"] != request["metadata_record_sha256"]:
            raise ValueError("BIBLIOGRAPHIC_RESUME_MEMBER_CHANGED")
        for attempt in row["provenance"]["attempts"]:
            if attempt.get("raw_path") and e.sha(Path(attempt["raw_path"]).read_bytes()) != attempt["raw_source_sha256"]:
                raise ValueError("BIBLIOGRAPHIC_RESUME_BODY_CHANGED")
        return row
    version = (request["captured_version_id"] or "").removeprefix("arxiv:")
    url = "https://arxiv.org/abs/" + version if version else metadata["url"].replace("http://", "https://")
    raw, provenance = primary_get(url)
    fields = bibliographic_fields(raw, metadata["source"]) if raw else {
        "revision_history": [], "publication_date_literals": [], "linked_identifiers": [],
        "title_sha256": None, "title_identity_sha256": None, "authors_sha256": [], "locators": [], "uncertainty_codes": ["PRIMARY_BIBLIOGRAPHIC_ACCESS_UNAVAILABLE"]}
    row = {k: request[k] for k in ("member_id", "work_id", "review_id", "captured_version_id", "metadata_record_sha256")}
    row.update({"evidence_id": "R01-BIB-" + request["member_id"], "source_git_commit": head,
                "provenance": provenance, "official_fields": fields,
                "selected_protocol_preferred_version": None, "eligibility_decision": None})
    e.write_new(path, row)
    return row


def bibliography(head: str, limit: int | None = None) -> None:
    """Process all requested metadata memberships in a bounded resumable pool."""
    requests, metadata = inputs()
    if limit:
        requests = requests[:limit]
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(bibliographic_one, req, metadata[req["member_id"]], head): req for req in requests}
        for n, future in enumerate(concurrent.futures.as_completed(futures), 1):
            row = future.result()
            rows.append(row)
            print(json.dumps({"utc": e.now(), "completed": n, "total": len(requests), "member_id": row["member_id"],
                              "official_response_available": bool(row["provenance"]["raw_source_sha256"])}), flush=True)
    if not limit:
        e.write_new(e.BASE / recovery.RUN / "OFFICIAL_BIBLIOGRAPHIC_EVIDENCE.json", sorted(rows, key=lambda r: r["member_id"]))


def main() -> None:
    """Run only after source tools are committed; no frame or sampling operations."""
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["bindings", "bibliography"])
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    head = e.clean_head()
    e.baseline(e.read(e.CONFIG))
    if args.phase == "bindings":
        build_bindings(head)
    else:
        bibliography(head, args.limit)


if __name__ == "__main__":
    main()
