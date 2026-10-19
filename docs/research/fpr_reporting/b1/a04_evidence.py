"""Custodian-only A04 evidence acquisition, restriction and frozen transfer.

No eligibility dispositions, selection functions or outcome extraction exist here.
Unrestricted source material is confined to an ignored cache; released source
sentences must pass a full closed grammar and independently reconstructed locator.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
import re
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.errors import PdfReadError

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "a04-evidence-source"
CONFIG = BASE / "a04_evidence_config.json"
METHOD_ROLES = {
    "method", "methods", "methodology", "approach", "our approach", "framework",
    "proposed method", "proposed framework", "system design", "architecture",
    "dataset", "datasets", "data", "data collection", "dataset construction",
    "data construction", "benchmark construction", "experimental setup",
    "evaluation setup", "experimental settings", "evaluation settings",
    "experiment setup", "implementation details", "threat model", "problem formulation",
    "problem definition", "task definition", "preliminaries", "detection framework",
}
FORBIDDEN_SECTION = re.compile(
    r"abstract|result|performance|comparison|ablation|conclusion|discussion|related work|reference|limitation", re.I)
OUTCOME = re.compile(
    r"\b(?:FPR|FNR|TPR|ASR|AUC|ROC|accuracy|precision|recall|F1|true.positive|false.positive|"
    r"false.negative|confidence|guarantee\w*|assur\w*|statistic\w*|significan\w*|"
    r"outperform\w*|surpass\w*|achiev\w*|improv\w*|degrad\w*|superior|inferior|best|worst|"
    r"better|worse|highest|lowest|effective\w*|success\w*|failure\w*|robust\w*|"
    r"stronger|weaker|negligible|near.zero|competitive|performance|empirically|"
    r"findings?|results?|observed|demonstrate\w*|show(?:s|ed)?|reveal\w*|"
    r"hundred\w*|thousand\w*|million\w*|percent\w*)\b|[%=<>\d]", re.I)
SUBJECT = r"(?:the|our|this) (?:model|classifier|detector|guardrail|system)"
ITEM = r"(?:input )?(?:prompts|inputs|texts|documents)"
CLASS = r"(?:benign|malicious|safe|unsafe)"
LANG_ITEM = r"(?:text|texts|prompts|documents|inputs|data|datasets|examples)"
GRAMMARS = {
    "BINARY_LABEL_PROCEDURE": re.compile(
        rf"(?:we|{SUBJECT}) (?:classify|classifies|label|labels|categorize|categorizes) "
        rf"{ITEM} (?:as|into) (?:either )?{CLASS} (?:or|and|versus) {CLASS}\.", re.I),
    "ENGLISH_DATA_PROCEDURE": re.compile(
        rf"(?:we|the authors) (?:use|retain|select|collect|consider) (?:only )?"
        rf"(?:english|english-language) {LANG_ITEM}"
        r"(?: (?:for|in) (?:training|evaluation|testing|the evaluation|the experiments|our evaluation|our experiments))?\.", re.I),
    "ENGLISH_DATA_DESCRIPTION": re.compile(
        r"(?:(?:the|our|all) (?:dataset|datasets|test set|evaluation set|evaluation data|prompts|inputs|documents|data)) "
        r"(?:is|are) (?:entirely |only )?(?:written |provided |collected )?in english\.", re.I),
    "PRE_TARGET_TIMING": re.compile(
        rf"(?:detection|classification|{SUBJECT}) (?:is performed|is applied|runs|operates) "
        r"before (?:generation|the (?:target|downstream)(?: language)? model "
        r"(?:responds|answers|generates (?:a response|an answer)))\.", re.I),
    "BINARY_TASK_DEFINITION": re.compile(
        r"(?:we formulate (?:the|this) task as|the task is|this is) "
        r"(?:a )?binary (?:classification|classification task|classification problem)\.", re.I),
}
_REQUEST_LOCK = threading.Lock()
_LAST_REQUEST = 0.0


def sha(raw: bytes) -> str:
    """Hash exact bytes."""
    return hashlib.sha256(raw).hexdigest()


def encoded(value: object) -> bytes:
    """Canonical ASCII-safe UTF-8 JSON with LF terminator."""
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode()


def read(path: Path) -> object:
    """Read explicit UTF-8 JSON without Windows code-page dependence."""
    return json.loads(path.read_text(encoding="utf-8"))


def now() -> str:
    """Return the actual UTC action time, never the publication cutoff."""
    return datetime.now(timezone.utc).isoformat()


def git(*args: str) -> str:
    """Perform read-only Git provenance operations."""
    return subprocess.check_output(["git", *args], cwd=BASE, text=True).strip()


def clean_head() -> str:
    """Enforce the repository's clean-tree scientific-generation invariant."""
    if git("status", "--porcelain"):
        raise RuntimeError("Scientific generation/retrieval requires a clean committed tree")
    return git("rev-parse", "HEAD")


def write_new(path: Path, value: object) -> None:
    """Write an immutable receipt atomically; never overwrite historical evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = encoded(value)
    if path.exists():
        if path.read_bytes() != raw:
            raise FileExistsError(path)
        return
    temporary = path.with_name(path.name + ".partial")
    if temporary.exists():
        if temporary.read_bytes() != raw:
            temporary.rename(path.with_name(path.name + f".interrupted-{time.time_ns()}"))
        else:
            temporary.rename(path)
            return
    temporary.write_bytes(raw)
    temporary.rename(path)


def baseline(config: dict) -> dict:
    """Verify every available historical lock before using frozen inventories."""
    verified = {}
    for lock_path in sorted(BASE.glob("PROTOCOL_LOCK*.json")):
        lock = read(lock_path)
        for name, expected in lock.get("files", {}).items():
            if not isinstance(expected, str) or sha((BASE / name).read_bytes()) != expected:
                raise ValueError(f"Historical lock mismatch: {name}")
        verified[lock_path.name] = sha(lock_path.read_bytes())
    archive = BASE / "a04-handoff/FRESH_REVIEWER_INTAKE.zip"
    if sha(archive.read_bytes()) != config["intake_archive_sha256"]:
        raise ValueError("Original A04 archive mismatch")
    return {"historical_locks": verified, "intake_sha256": sha(archive.read_bytes())}


def official_url(url: str, config: dict) -> bool:
    """Reject off-host redirects and arbitrary candidate discovery endpoints."""
    parsed = urllib.parse.urlparse(url)
    return (parsed.scheme == "https" and parsed.hostname in config["allowed_hosts"]
            and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment)


def make_requests(config: dict) -> dict:
    """Reconstruct requests from all frozen members without reading old decisions."""
    inventory = read(BASE / "a04-handoff/restricted/CANDIDATE_INVENTORY.json")
    source_records = [json.loads(line) for line in (BASE / "a02-metadata/metadata_union.jsonl").read_text(encoding="utf-8").splitlines()]
    numbered = {f"M{i:04d}": row for i, row in enumerate(source_records, 1)}
    works, requests = [], []
    for work in inventory:
        mids = []
        for m in work["members"]:
            mid = m["member_id"]
            row = numbered[mid]
            if sha(encoded(row)) != m["metadata_record_sha256"]:
                raise ValueError("Member-to-source commitment mismatch")
            if m["source"] == "arxiv":
                version = m["captured_version_id"].removeprefix("arxiv:")
                urls = [f"https://arxiv.org/html/{version}", f"https://arxiv.org/pdf/{version}"]
            else:
                version = None
                urls = [str(row["pdf_url"] or (row["url"].rstrip("/") + ".pdf"))]
            urls = [urllib.parse.urlunparse(urllib.parse.urlparse(u)._replace(scheme="https")) for u in urls]
            if not urls or not all(official_url(u, config) for u in urls):
                raise ValueError(f"Unapproved source locator: {mid}")
            requests.append({"member_id": mid, "work_id": work["work_id"], "review_id": work["review_id"],
                             "source": m["source"], "captured_version_id": m["captured_version_id"],
                             "bibliography": {k: m[k] for k in ("doi", "published", "updated", "year", "month")},
                             "metadata_record_sha256": m["metadata_record_sha256"], "urls": urls})
            mids.append(mid)
        works.append({"work_id": work["work_id"], "review_id": work["review_id"], "member_ids": mids,
                      "required_facts": ["T", "B", "P", "L", "BIBLIOGRAPHY", "VERSION", "IDENTITY", "SENTINEL", "ACCESS"],
                      "decision": None})
    if len(works) != 372 or len(requests) != 389 or len({r["member_id"] for r in requests}) != 389:
        raise ValueError("Frame or membership changed")
    return {"request_origin": "MECHANICALLY_RECONSTRUCTED_NO_AUTHENTICATED_REVIEWER_RETURN_AVAILABLE",
            "intake_sha256": config["intake_archive_sha256"], "works": works,
            "source_requests": sorted(requests, key=lambda r: r["member_id"])}


def legacy_index(config: dict) -> tuple[dict, dict]:
    """Verify raw legacy bodies and access receipts; never import old method views."""
    indexed, counts = {}, {"receipts": 0, "raw_bodies_verified": 0, "raw_errors_verified": 0, "invalid": 0}
    for path in sorted(Path(config["legacy_cache"]).glob("*.source.json")):
        receipt = read(path)
        counts["receipts"] += 1
        for attempt in receipt["attempts"]:
            for field, digest_field in (("raw_path", "sha256"), ("error_body_path", "error_body_sha256")):
                if field not in attempt:
                    continue
                raw_path = Path(attempt[field])
                if not raw_path.exists() or sha(raw_path.read_bytes()) != attempt[digest_field]:
                    counts["invalid"] += 1
                    continue
                counts["raw_bodies_verified" if field == "raw_path" else "raw_errors_verified"] += 1
                if field == "raw_path" and attempt.get("status") == 200:
                    indexed[attempt["url"]] = {**{k: attempt.get(k) for k in (
                        "url", "final_url", "started_utc", "finished_utc", "status", "content_type", "sha256", "raw_path")},
                        "original_receipt_sha256": sha(path.read_bytes()), "mode": "VERIFIED_LEGACY_RAW_BODY"}
    return indexed, counts


def validate_body(raw: bytes, url: str) -> tuple[str, str]:
    """Reject truncation/challenge pages and distinguish exact-body version evidence."""
    version = re.search(r"/(?:html|pdf)/(\d{4}\.\d{4,5}v\d+)$", url)
    if raw.startswith(b"%PDF"):
        if b"%%EOF" not in raw[-2048:]:
            raise ValueError("TRUNCATED_PDF")
        reader = PdfReader(io.BytesIO(raw), strict=True)
        if not len(reader.pages):
            raise ValueError("EMPTY_PDF")
        first_text = " ".join((p.extract_text() or "") for p in list(reader.pages)[:2])
        compact = re.sub(r"\s+", "", first_text)
        body_match = bool(version and version[1] in compact)
        return "PDF", "EXACT_VERSION_IN_BODY" if body_match else "EXPLICIT_URL_ONLY_BODY_VERSION_UNCONFIRMED"
    if not re.search(br"</html\s*>", raw[-8192:], re.I):
        raise ValueError("TRUNCATED_OR_NONHTML_BODY")
    soup = BeautifulSoup(raw, "html.parser")
    if not soup.select_one("article.ltx_document") or not soup.select("section"):
        raise ValueError("NOT_STRUCTURED_ARXIV_PRIMARY_HTML")
    if version and not soup.find("a", href=f"/abs/{version[1]}"):
        raise ValueError("BODY_VERSION_SELF_LINK_MISMATCH")
    return "HTML", "EXACT_VERSION_SELF_LINK" if version else "BODY_VERSION_UNCONFIRMED"


def acquisition(request: dict, config: dict, legacy: dict, head: str) -> dict:
    """Acquire one member with immutable resume receipts and bounded same-version retry."""
    global _LAST_REQUEST
    cache = Path(config["cache_root"])
    path = cache / "acquisition" / f"{request['member_id']}.json"
    if path.exists():
        saved = read(path)
        if saved["request_sha256"] != sha(encoded(request)):
            raise ValueError("RESUME_REQUEST_MISMATCH")
        if saved.get("body"):
            body = saved["body"]
            if sha(Path(body["raw_path"]).read_bytes()) != body["sha256"]:
                raise ValueError("RESUME_BODY_HASH_MISMATCH")
        return saved
    attempts, body = [], None
    for url in request["urls"]:
        if url in legacy:
            old = legacy[url]
            try:
                kind, version_state = validate_body(Path(old["raw_path"]).read_bytes(), url)
                body = {**old, "kind": kind, "version_state": version_state}
                attempts.append({"url": url, "mode": "REUSED_VERIFIED_CACHE", "status": 200})
                break
            except (OSError, ValueError, PdfReadError, EOFError) as exc:
                attempts.append({"url": url, "status": "LEGACY_BODY_REJECTED", "error_type": type(exc).__name__})
        for ordinal in range(config["max_attempts_per_url"]):
            with _REQUEST_LOCK:
                wait = config["minimum_request_interval_seconds"] - (time.monotonic() - _LAST_REQUEST)
                if wait > 0:
                    time.sleep(wait)
                _LAST_REQUEST = time.monotonic()
            attempt = {"url": url, "started_utc": now(), "mode": "PRIMARY_RETRIEVAL"}
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Warrant-B1-evidence-provision/1.0"})
                with urllib.request.urlopen(req, timeout=config["timeout_seconds"]) as response:
                    final = response.url
                    if not official_url(final, config) or final.rstrip("/") != url.rstrip("/"):
                        raise ValueError("UNAPPROVED_REDIRECT_OR_VERSION_CHANGE")
                    raw = response.read(config["max_body_bytes"] + 1)
                    attempt.update(status=response.status, final_url=final, content_type=response.headers.get("Content-Type"))
                if len(raw) > config["max_body_bytes"]:
                    raise ValueError("BODY_SIZE_LIMIT")
                digest = sha(raw)
                raw_path = cache / "raw" / digest
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                if raw_path.exists() and raw_path.read_bytes() != raw:
                    raise ValueError("CACHE_HASH_COLLISION")
                if not raw_path.exists():
                    raw_path.write_bytes(raw)
                attempt.update(sha256=digest, raw_path=str(raw_path), bytes=len(raw), finished_utc=now())
                kind, version_state = validate_body(raw, url)
                body = {**attempt, "kind": kind, "version_state": version_state}
                attempts.append(attempt)
                break
            except (OSError, ValueError, PdfReadError, EOFError) as exc:
                attempt.update(status=attempt.get("status", getattr(exc, "code", None)),
                               error_type=type(exc).__name__, error_code=str(exc)[:160], finished_utc=now())
                attempts.append(attempt)
                if isinstance(exc, urllib.error.HTTPError) and exc.code in {400, 401, 403, 404, 410}:
                    break
                if ordinal + 1 < config["max_attempts_per_url"]:
                    time.sleep(config["retry_backoff_seconds"] * (ordinal + 1))
        if body:
            break
    result = {"member_id": request["member_id"], "work_id": request["work_id"],
              "request_sha256": sha(encoded(request)), "source_git_commit": head,
              "attempts": attempts, "body": body, "completed_utc": now(),
              "source_available": body is not None, "eligibility_decision": None}
    write_new(path, result)
    return result


def normalized(value: str) -> str:
    """Normalize whitespace only, preserving the source sentence's words."""
    return re.sub(r"\s+", " ", value).strip()


def heading_role(value: str) -> str | None:
    """Use complete normalized section labels, not broad keyword selection."""
    clean = re.sub(r"^(?:[A-Z]|[IVX]+|\d+(?:\.\d+)*)(?:[.\s:]+)", "", normalized(value)).casefold().strip()
    return clean if clean in METHOD_ROLES else None


def grammar(value: str) -> str | None:
    """Admit only entire sentences in a finite result-free method language."""
    if any(c.isdigit() for c in value) or OUTCOME.search(value):
        return None
    return next((name for name, pattern in GRAMMARS.items() if pattern.fullmatch(value)), None)


def html_regions(raw: bytes) -> list[dict]:
    """Resolve actual section ancestry and omit every non-prose/result container."""
    soup = BeautifulSoup(raw, "html.parser")
    regions = []
    for ordinal, paragraph in enumerate(soup.select("p.ltx_p")):
        if paragraph.find_parent(["figure", "table", "figcaption", "aside", "blockquote"]):
            continue
        if any("abstract" in " ".join(p.get("class", [])) for p in paragraph.parents if p.name):
            continue
        sections = list(paragraph.find_parents("section"))
        headings = []
        for section in sections:
            h = section.find(re.compile(r"^h[1-6]$"), recursive=False)
            headings.append(h.get_text(" ", strip=True) if h else "")
        if not sections or not headings[0] or any(FORBIDDEN_SECTION.search(h) for h in headings):
            continue
        role = heading_role(headings[0])
        if role is None:
            continue
        section_id = sections[0].get("id")
        if not section_id or not re.fullmatch(r"[A-Za-z0-9_.:-]+", section_id):
            continue
        regions.append({"locator": f"section#{section_id}/p.ltx_p[{ordinal}]",
                        "section_id": section_id, "section_role": role,
                        "paragraph_ordinal": ordinal, "text": normalized(paragraph.get_text(" ", strip=True))})
    return regions


def restrict(raw: bytes, kind: str, config: dict) -> tuple[list, list, dict]:
    """Separate provable closed-language quotes from unverified semantic proposals."""
    evidence, proposals = [], []
    if kind == "PDF":
        reader = PdfReader(io.BytesIO(raw), strict=True)
        for page, item in enumerate(reader.pages, 1):
            text = normalized(item.extract_text() or "")
            if re.search(r"\b(?:dataset|threat model|binary classification|English)\b", text, re.I):
                proposals.append({"page": page, "text": text,
                                  "restriction_state": "QUARANTINE_PDF_LAYOUT_AND_SEMANTIC_CHECK_REQUIRED"})
            if len(proposals) >= config["max_quarantine_proposals_per_member"]:
                break
        return evidence, proposals, {"structural_regions": 0, "method_terms_found": bool(proposals),
                                     "reason": "PDF_LAYOUT_NOT_INDEPENDENTLY_VERIFIED"}
    regions = html_regions(raw)
    for region in regions:
        text = region["text"]
        if len(proposals) < config["max_quarantine_proposals_per_member"] and re.search(
                r"\b(?:binary|English|classif\w*|detect\w*|dataset|threat|before)\b", text, re.I):
            proposals.append({**region, "restriction_state": "QUARANTINE_SEMANTIC_CHECK_REQUIRED"})
        # Reject the whole context when outcomes/numerical content adjoin a match.
        if OUTCOME.search(text):
            continue
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text):
            rule = grammar(sentence)
            if rule and len(evidence) < config["max_verified_method_items_per_member"]:
                evidence.append({"quote": sentence, "grammar_rule": rule,
                                 **{k: region[k] for k in ("locator", "section_id", "section_role", "paragraph_ordinal")},
                                 "paragraph_sha256": sha(text.encode()),
                                 "limitation": "EXACT_METHOD_SENTENCE_ONLY_NOT_A_COMPLETE_ELIGIBILITY_DETERMINATION"})
    return evidence, proposals, {"structural_regions": len(regions), "method_terms_found": bool(proposals)}


def verify_quote(raw: bytes, item: dict) -> None:
    """Reconstruct source attribution and recheck the entire released sentence."""
    soup = BeautifulSoup(raw, "html.parser")
    paragraphs = soup.select("p.ltx_p")
    p = paragraphs[item["paragraph_ordinal"]]
    text = normalized(p.get_text(" ", strip=True))
    if sha(text.encode()) != item["paragraph_sha256"] or OUTCOME.search(text):
        raise ValueError("CONTEXT_CHANGED_OR_RESULT_BEARING")
    if item["quote"] not in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text):
        raise ValueError("QUOTE_NOT_A_COMPLETE_SOURCE_SENTENCE")
    if grammar(item["quote"]) != item["grammar_rule"]:
        raise ValueError("QUOTE_OUTSIDE_CLOSED_GRAMMAR")
    matching = [r for r in html_regions(raw) if r["paragraph_ordinal"] == item["paragraph_ordinal"]]
    if len(matching) != 1 or any(matching[0][k] != item[k] for k in ("locator", "section_id", "section_role")):
        raise ValueError("INCORRECT_SECTION_ATTRIBUTION")


def process(request: dict, config: dict) -> dict:
    """Derive resumable, deterministic restricted evidence; leave decisions blank."""
    cache = Path(config["cache_root"])
    receipt = read(cache / "acquisition" / f"{request['member_id']}.json")
    body = receipt["body"]
    evidence, proposals, structure = [], [], {"reason": "SOURCE_UNAVAILABLE", "method_terms_found": False}
    if body:
        raw = Path(body["raw_path"]).read_bytes()
        if sha(raw) != body["sha256"]:
            raise ValueError("PROCESS_SOURCE_HASH_MISMATCH")
        validate_body(raw, body["url"])
        evidence, proposals, structure = restrict(raw, body["kind"], config)
        for item in evidence:
            verify_quote(raw, item)
    result = {"member_id": request["member_id"], "work_id": request["work_id"],
              "request_sha256": sha(encoded(request)), "acquisition_receipt_sha256": sha(encoded(receipt)),
              "raw_source_sha256": body["sha256"] if body else None,
              "source_available": bool(body), "method_structure": structure,
              "method_proposal_count": len(proposals), "verified_method_items": evidence,
              "semantic_checker": "NOT_ESTABLISHED", "independent_eligibility_review": "NOT_PERFORMED"}
    write_new(cache / "proposals" / f"{request['member_id']}.json", {"member_id": request["member_id"], "proposals": proposals})
    write_new(cache / "processed" / f"{request['member_id']}.json", result)
    return result


def initialize(config: dict, head: str) -> None:
    """Freeze mechanically reconstructed requests after baseline verification."""
    checked = baseline(config)
    _, legacy_counts = legacy_index(config)
    requests = make_requests(config)
    write_new(BASE / config["run_id"] / "EVIDENCE_REQUESTS.json", requests)
    write_new(BASE / config["run_id"] / "BASELINE.json", {
        "created_utc": now(), "source_git_commit": head, "source_tree_clean_at_start": True,
        **checked, "legacy_cache_integrity": legacy_counts,
        "reviewer_return": "NOT_AVAILABLE_LOCALLY_NO_IMPORT_CLAIMED", "works": 372, "members": 389,
        "independent_reviewer": "REPORTED_BY_USER_NOT_LOCALLY_ATTESTED", "semantic_checker": "NOT_ESTABLISHED",
        "config_sha256": sha(CONFIG.read_bytes()), "requests_sha256": sha(encoded(requests)),
        "draw_executed": False, "B2": "NOT_AUTHORIZED"})
    print(json.dumps({"initialized": config["run_id"], "works": 372, "members": 389, "legacy_cache": legacy_counts}))


def main() -> None:
    """Run bounded phases without creating or changing an eligibility disposition."""
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["init", "acquire", "process", "freeze"])
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    head = clean_head()
    config = read(CONFIG)
    if args.phase == "init":
        initialize(config, head)
        return
    requests = read(BASE / config["run_id"] / "EVIDENCE_REQUESTS.json")["source_requests"]
    chosen = requests[:args.limit] if args.limit else requests
    if args.phase == "acquire":
        legacy, counts = legacy_index(config)
        print(json.dumps({"legacy_validation": counts, "requested_members": len(chosen)}), flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=config["max_workers"]) as pool:
            futures = {pool.submit(acquisition, r, config, legacy, head): r for r in chosen}
            for n, future in enumerate(concurrent.futures.as_completed(futures), 1):
                request = futures[future]
                try:
                    result = future.result()
                    print(json.dumps({"utc": now(), "completed": n, "total": len(chosen),
                                      "member_id": request["member_id"], "source_available": result["source_available"]}), flush=True)
                except (OSError, ValueError, KeyError, IndexError, TypeError, PdfReadError, RuntimeError, EOFError) as exc:
                    print(json.dumps({"member_id": request["member_id"], "quarantined_error": type(exc).__name__}), flush=True)
    elif args.phase == "process":
        for n, request in enumerate(chosen, 1):
            try:
                result = process(request, config)
                print(json.dumps({"completed": n, "member_id": request["member_id"],
                                  "verified_method_items": len(result["verified_method_items"]),
                                  "quarantine_proposals": result["method_proposal_count"]}), flush=True)
            except (OSError, ValueError, KeyError, IndexError, TypeError, PdfReadError, RuntimeError, EOFError) as exc:
                print(json.dumps({"member_id": request["member_id"], "quarantined_error": type(exc).__name__}), flush=True)
    else:
        freeze(config, head)


def freeze(config: dict, head: str) -> None:
    """Implemented after bounded parser/restriction validation; never sample."""
    raise RuntimeError("Transfer release not implemented before boundary tests")


if __name__ == "__main__":
    main()
