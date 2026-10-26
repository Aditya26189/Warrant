"""Cache primary B1 method sources without discovering candidates or sampling."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import importlib.metadata
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.errors import PdfReadError

BASE = Path(__file__).resolve().parent
CACHE = Path("C:/Users/LawLight/Desktop/accenture/.venv/fpr-b1-method-cache-20261019")
GOOD = re.compile(r"method|dataset|data set|data collection|experimental setup|evaluation setup|task definition|problem (?:setup|formulation)|implementation|preprocess|limitation|benchmark construction|framework|our approach|architecture|system design|threat model|overview", re.I)
BAD = re.compile(r"results|ablation|performance|comparison|metrics|references|related work", re.I)


def utc() -> str:
    """Record actual retrieval time, independent of the dated paper filename."""
    return datetime.now(timezone.utc).isoformat()


def save(path: Path, value: object) -> None:
    """Keep source caches immutable so earlier access evidence survives retries."""
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def masked(value: str) -> str:
    """Keep numerical outcomes out of the method display; metadata IDs stay separate."""
    return re.sub(r"\d+(?:[.,]\d+)*", "[NUM]", value)


def html_view(raw: bytes) -> dict:
    """Select method/dataset prose and language facts, omitting tables and results."""
    soup = BeautifulSoup(raw, "html.parser")
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(re.compile("^h[1-6]$"))]
    paragraphs = []
    for i, p in enumerate(soup.select("p.ltx_p")):
        if p.find_parent(["table", "figure"]) or p.find_parent(class_="ltx_abstract"):
            continue
        labels = []
        for section in p.find_parents("section"):
            h = section.find(re.compile("^h[1-6]$"), recursive=False)
            if h:
                labels.append(h.get_text(" ", strip=True))
        closest = labels[0] if labels else "UNHEADED"
        text = p.get_text(" ", strip=True)
        language_fact = bool(re.search(r"\bEnglish\b|\bmultilingual\b|\bcross.lingual\b|\blanguages\b|\blanguage (?:filtering|coverage|distribution|selection|setting)\b", text, re.I))
        if (any(BAD.search(label) for label in labels) and not GOOD.search(closest)) or "abstract" in closest.casefold():
            continue
        if not GOOD.search(" / ".join(labels)) and not language_fact:
            continue
        if re.search(r"false positive rate|false negative rate|\bFPR\b|\bTPR\b|\bASR\b|accuracy of|achieves? .*%", text, re.I) and not language_fact:
            continue
        if text:
            paragraphs.append({"paragraph": i, "section": " / ".join(reversed(labels)), "text": masked(text)})
    return {"kind": "HTML_SELECTED_METHOD_PROSE", "headings": headings, "paragraphs": paragraphs,
            "numeric_strings_masked": True, "tables_omitted": True, "not_full_text_review": True}


def pdf_view(raw: bytes) -> dict:
    """Expose selected language/method prose only, with page locators and masked numbers."""
    reader = PdfReader(io.BytesIO(raw))
    paragraphs = []
    headings = []
    for page_no, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        for line in text.splitlines():
            if re.match(r"^\s*(?:[IVX]+\.|\d+(?:\.\d+)*\.?|[A-Z]\.)\s+\S", line) and len(line) < 120:
                if GOOD.search(line) or BAD.search(line):
                    headings.append({"page": page_no, "heading": line.strip()})
        blocks = re.split(r"\n\s*\n", text)
        for i, block in enumerate(blocks):
            if not re.search(r"English|language|dataset|data set|before (?:generat|the|target)|last (?:input|prompt) token|input.only|binary classif|prompt.classif", block, re.I):
                continue
            # PDF column extraction may create large blocks. Keep evidence windows,
            # never print a whole page or a metric table as an eligibility oracle.
            for match in re.finditer(r"English|language|dataset|data set|before (?:generat|the|target)|last (?:input|prompt) token|input.only|binary classif|prompt.classif", block, re.I):
                excerpt = block[max(0, match.start() - 180):match.end() + 650]
                excerpt = re.sub(r"\s+", " ", excerpt).strip()
                if not excerpt:
                    continue
                paragraphs.append({"page": page_no, "block": i, "text": masked(excerpt)})
    unique = list({(p["page"], p["text"]): p for p in paragraphs}.values())
    return {"kind": "PDF_SELECTED_METHOD_WINDOWS", "headings": headings, "paragraphs": unique,
            "pages": len(reader.pages), "numeric_strings_masked": True,
            "layout_not_verified": True, "not_full_text_review": True}


def capture(question: dict, head: str) -> dict:
    """Retrieve the prespecified work/version from official sources, without adding IDs."""
    rid = question["review_id"]
    receipt_path = CACHE / f"{rid}.source.json"
    if receipt_path.exists():
        return json.loads(receipt_path.read_text(encoding="utf-8"))
    arxiv = next((re.search(r"\d{4}\.\d{4,5}v\d+", s).group() for s in question["captured_source_ids"]
                  if re.search(r"\d{4}\.\d{4,5}v\d+", s)), None)
    urls = ([f"https://arxiv.org/html/{arxiv}", f"https://arxiv.org/pdf/{arxiv}"] if arxiv else
            [question["source_links"][0].rstrip("/") + ".pdf"])
    attempts = []
    for ordinal, url in enumerate(urls, 1):
        attempt = {"url": url, "started_utc": utc()}
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Warrant-B1-method-verification/1.0 (research)"})
            with urllib.request.urlopen(request, timeout=35) as response:
                raw = response.read()
                attempt.update(status=response.status, content_type=response.headers.get("Content-Type"), final_url=response.url)
            kind = "pdf" if raw.startswith(b"%PDF") else "html"
            raw_path = CACHE / f"{rid}-{ordinal}.{kind}"
            if raw_path.exists():
                raise FileExistsError(raw_path)
            raw_path.write_bytes(raw)
            attempt.update(raw_path=str(raw_path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            view = pdf_view(raw) if kind == "pdf" else html_view(raw)
            view_path = CACHE / f"{rid}-{ordinal}.method-view.json"
            save(view_path, view)
            attempt.update(view_path=str(view_path), view_sha256=hashlib.sha256(view_path.read_bytes()).hexdigest(), paragraphs=len(view["paragraphs"]))
            attempt["finished_utc"] = utc()
            attempts.append(attempt)
            if view["paragraphs"]:
                break
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, PdfReadError) as exc:
            attempt.setdefault("status", getattr(exc, "code", None))
            if isinstance(exc, urllib.error.HTTPError):
                error_raw = exc.read()
                error_path = CACHE / f"{rid}-{ordinal}.error-body"
                if not error_path.exists():
                    error_path.write_bytes(error_raw)
                attempt.update(error_body_path=str(error_path), error_body_sha256=hashlib.sha256(error_raw).hexdigest())
            attempt.update(error_type=type(exc).__name__, error=str(exc), finished_utc=utc())
            attempts.append(attempt)
    result = {"review_id": rid, "work_id": question["work_id"], "source_git_commit": head,
              "scope": "METHOD_DOMAIN_ONLY_NO_OUTCOME_EXTRACTION", "attempts": attempts,
              "parser_versions": {n: importlib.metadata.version(n) for n in ("pypdf", "beautifulsoup4")}}
    save(receipt_path, result)
    return result


def main() -> None:
    """Use clean source provenance; put full source documents in ignored local cache only."""
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="+", help="Original Q IDs; ALL means the156 unresolved rows")
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=BASE):
        raise RuntimeError("Refusing dirty-tree scientific retrieval")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE, text=True).strip()
    questions = json.loads((BASE / "a02-human-batch002/PENDING_METADATA_ANSWERS_BLANK.json").read_text(encoding="utf-8"))["questions"]
    chosen = questions if args.ids == ["ALL"] else [q for q in questions if q["review_id"] in args.ids]
    assert len(chosen) == (156 if args.ids == ["ALL"] else len(set(args.ids)))
    CACHE.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        tasks = [pool.submit(capture, q, head) for q in chosen]
        for completed, task in enumerate(concurrent.futures.as_completed(tasks), 1):
            r = task.result()
            elapsed = time.monotonic() - started
            print(json.dumps({"utc": utc(), "review_id": r["review_id"],
                              "completed": completed, "total": len(tasks),
                              "eta_seconds": round(elapsed / completed * (len(tasks) - completed)), "attempts": [
                {k: a.get(k) for k in ("status", "error_type", "paragraphs")} for a in r["attempts"]]}), flush=True)


if __name__ == "__main__":
    main()
