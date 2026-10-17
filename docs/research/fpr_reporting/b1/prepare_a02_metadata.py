"""Parse the immutable A02 source bytes and apply only bibliographic filters.

No network, domain eligibility, sentinel filtering, paper selection or outcome
extraction occurs. A strict BibTeX lexer retains all source-record dispositions;
retained records are checked against the pinned reference parser before use.
"""
from __future__ import annotations

import calendar
from collections.abc import Iterator
import csv
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
DEPS = BASE.parents[5] / ".venv" / "fpr-b1-parser-deps"
# The existing research worktree is nested under the shared checkout's .venv.
sys.path.insert(0, str(DEPS))
import bibtexparser  # noqa: E402
import pyparsing  # noqa: E402
from bibtexparser.bparser import BibTexParser  # noqa: E402
from bibtexparser.latexenc import latex_to_unicode  # noqa: E402

OUT = BASE / "a02-metadata"
START = dt.date(2024, 1, 1)
END = dt.date(2026, 10, 16)
MONTHS = {n.casefold(): i for i in range(1, 13) for n in
          (calendar.month_name[i], calendar.month_abbr[i])}
ATOM = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
TOKEN = re.compile(r"[A-Za-z0-9_:+./-]+")


def sha(data: bytes) -> str:
    """Bind source bytes and parser implementations."""
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    """Use the approved field normalization verbatim after format decoding."""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = "".join(" " if unicodedata.category(c) == "Pd" else c for c in text)
    return " ".join(text.split())


def predicate(title: str, abstract: str) -> bool:
    """Restrict discovery to the prespecified title and abstract fields."""
    text = normalize(title + " " + abstract)
    return bool(re.search(r"\bprompt\s+injection\b", text)) and bool(
        re.search(r"\b(?:detect\w*|guardrail\w*|classif\w*)\b", text))


def date_state(year: str, month: str) -> str:
    """Keep partly overlapping or missing publication dates explicitly unclear."""
    if not re.fullmatch(r"\d{4}", year):
        return "UNCLEAR_DATE"
    y = int(year)
    if y < START.year or y > END.year:
        return "OUTSIDE_WINDOW"
    m = MONTHS.get(month.strip().casefold())
    if m is None and month.isdigit() and 1 <= int(month) <= 12:
        m = int(month)
    if m is None:
        return "UNCLEAR_DATE"
    low, high = dt.date(y, m, 1), dt.date(y, m, calendar.monthrange(y, m)[1])
    if high < START or low > END:
        return "OUTSIDE_WINDOW"
    return "IN_WINDOW" if START <= low <= high <= END else "UNCLEAR_DATE"


def entries(text: str) -> Iterator[tuple[dict[str, str], int, int]]:
    """Lex complete BibTeX fields without matching citation text or truncating.

    Quoted/braced values support nested braces and escaped delimiters. Month
    macros resolve only the standard month names; unknown relevant syntax stops.
    The source locator uses decoded-text character offsets, not byte offsets.
    """
    i, size = 0, len(text)

    def space(pos: int) -> int:
        while pos < size and text[pos].isspace():
            pos += 1
        return pos

    def value(pos: int) -> tuple[str, int]:
        pos = space(pos)
        if pos >= size:
            raise ValueError("Unterminated BibTeX value")
        opener = text[pos]
        if opener in '{"':
            quoted = opener == '"'
            depth = 0 if quoted else 1
            begin = pos + 1
            pos += 1
            while pos < size:
                c = text[pos]
                if c == "\\":
                    pos += 2
                    continue
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if not quoted and depth == 0:
                        return text[begin:pos], pos + 1
                    if quoted and depth < 0:
                        raise ValueError("Unbalanced braces in quoted value")
                elif quoted and c == '"' and depth == 0:
                    return text[begin:pos], pos + 1
                pos += 1
            raise ValueError("Unterminated BibTeX value")
        match = TOKEN.match(text, pos)
        if not match:
            raise ValueError("Unsupported BibTeX value token")
        token = match.group()
        if not token.isdigit():
            if token.casefold() not in MONTHS:
                raise ValueError("Unsupported BibTeX macro")
            token = calendar.month_name[MONTHS[token.casefold()]]
        return token, match.end()

    while True:
        i = space(i)
        if i == size:
            return
        begin = i
        match = re.match(r"@([A-Za-z]+)\s*\{\s*([^,\s]+)\s*,", text[i: i + 300])
        if not match:
            raise ValueError(f"Unsupported record header at character {i}")
        kind, key = match.groups()
        i += match.end()
        fields = {}
        while True:
            i = space(i)
            if i < size and text[i] == "}":
                i += 1
                break
            match = TOKEN.match(text, i)
            if not match:
                raise ValueError(f"Unsupported field at character {i}")
            name = match.group().casefold()
            i = space(match.end())
            if i >= size or text[i] != "=":
                raise ValueError("Missing field assignment")
            result, i = value(i + 1)
            i = space(i)
            while i < size and text[i] == "#":
                extra, i = value(i + 1)
                result += extra
                i = space(i)
            if name in fields:
                raise ValueError("Duplicate BibTeX field")
            fields[name] = result
            if i < size and text[i] == ",":
                i += 1
            elif i >= size or text[i] != "}":
                raise ValueError("Missing field separator")
        yield {"ENTRYTYPE": kind.casefold(), "ID": key, **fields}, begin, i


def canonical_record(entry: dict, source: str, ordinal: int, locator: dict) -> dict:
    """Retain metadata needed for later version/dedup/domain decisions."""
    title = entry.get("title", "")
    abstract = entry.get("abstract", "")
    if source == "acl":
        title, abstract = latex_to_unicode(title), latex_to_unicode(abstract)
    author = entry.get("author", "")
    return {"source": source, "source_id": entry["ID"], "source_ordinal": ordinal,
            "title": title, "abstract": abstract, "abstract_missing": not bool(abstract.strip()),
            "authors_raw": author, "doi": entry.get("doi", ""),
            "url": entry.get("url", ""), "pdf_url": entry.get("pdf", ""),
            "source_date_state": entry.get("date_state", ""),
            "year": entry.get("year", ""), "month": entry.get("month", ""),
            "published": entry.get("published", ""), "updated": entry.get("updated", ""),
            "entry_type": entry.get("ENTRYTYPE", ""), "venue": entry.get("booktitle", entry.get("journal", "")),
            "locator": locator,
            "normalized_title": normalize(title), "disposition": "RETAINED_METADATA_NOT_DOMAIN_SCREENED"}


def main() -> int:
    """Validate locked bytes and save all metadata-filter decisions once."""
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError("Refusing dirty-tree metadata generation")
    if OUT.exists():
        raise RuntimeError("Refusing to overwrite metadata snapshot")
    lock_bytes = (BASE / "PROTOCOL_LOCK_A02.json").read_bytes()
    lock = json.loads(lock_bytes)
    parser_lock = json.loads((BASE / "PARSER_LOCK_A02.json").read_text())
    assert sha(Path(__file__).read_bytes()) == parser_lock["script_sha256"]
    for file, expected in lock["files"].items():
        assert sha((BASE / file).read_bytes()) == expected
    assert bibtexparser.__version__ == "1.4.3"
    assert pyparsing.__version__ == "3.2.3"
    for file, expected in parser_lock["dependency_files"].items():
        assert sha((DEPS / file).read_bytes()) == expected
    OUT.mkdir()
    manifest = {"started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "source_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "source_tree_clean_at_start": True, "protocol_lock_sha256": sha(lock_bytes),
                "parser_lock_sha256": sha((BASE / "PARSER_LOCK_A02.json").read_bytes()),
                "status": "PARSING", "source_refresh": False,
                "openreview": "EXCLUDED_FROM_SELECTION_FRAME", "domain_eligibility": "NOT_RUN",
                "randomization": "NOT_RUN", "outcome_extraction": "NOT_RUN", "files": {}}
    counts = {"acl_total": 0, "acl_retained": 0, "arxiv_total": 0, "arxiv_retained": 0,
              "acl_date_unclear_retained": 0}
    all_records = []
    ledger_files = []
    ledger = None
    try:
        for file in sorted((BASE / "retrieval-01").glob("*arxiv*.body")):
            root = ET.fromstring(file.read_bytes())
            for local_index, row in enumerate(root.findall("a:entry", ATOM), 1):
                counts["arxiv_total"] += 1
                entry = {"ID": row.findtext("a:id", namespaces=ATOM),
                         "title": row.findtext("a:title", default="", namespaces=ATOM),
                         "abstract": row.findtext("a:summary", default="", namespaces=ATOM),
                         "author": " and ".join(a.findtext("a:name", default="", namespaces=ATOM) for a in row.findall("a:author", ATOM)),
                         "doi": row.findtext("x:doi", default="", namespaces=ATOM),
                         "published": row.findtext("a:published", namespaces=ATOM),
                         "updated": row.findtext("a:updated", namespaces=ATOM)}
                entry["date_state"] = "IN_WINDOW" if START <= dt.date.fromisoformat(entry["published"][:10]) <= END else "OUTSIDE_WINDOW"
                entry["url"] = entry["ID"]
                for link in row.findall("a:link", ATOM):
                    if link.get("title") == "pdf":
                        entry["pdf"] = link.get("href", "")
                record = canonical_record(entry, "arxiv", counts["arxiv_total"], {"raw_file": file.name, "entry_index_in_response": local_index})
                keep = entry["date_state"] != "OUTSIDE_WINDOW" and predicate(record["title"], record["abstract"])
                record["field_filter_disposition"] = "RETAIN" if keep else "EXCLUDE_FIELD_OR_DATE"
                # Every arXiv record is retained in its own ledger, including nonmatches.
                with (OUT / "arxiv_filter_ledger.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                if keep:
                    all_records.append(record)
                    counts["arxiv_retained"] += 1
        storage = json.loads((BASE / "retrieval-01/STORAGE_MANIFEST.json").read_text())
        compressed = b"".join((BASE / "retrieval-01" / p["file"]).read_bytes() for p in storage["parts_in_concatenation_order"])
        assert sha(compressed) == lock["acl_original_sha256"]
        text = gzip.decompress(compressed).decode("utf-8")
        declared_headers = len(re.findall(r"(?m)^@", text))
        for entry, begin, end in entries(text):
            ordinal = counts["acl_total"]
            if ordinal % 20000 == 0:
                if ledger:
                    ledger.close()
                file = OUT / f"acl_filter_ledger_{ordinal // 20000 + 1:02d}.csv"
                ledger_files.append(file)
                ledger = file.open("w", encoding="utf-8", newline="")
                writer = csv.writer(ledger, lineterminator="\n")
                writer.writerow(["ordinal", "id", "entry_type", "abstract_missing", "date_state", "predicate", "disposition", "text_char_start", "text_char_end"])
            counts["acl_total"] += 1
            state = date_state(entry.get("year", ""), entry.get("month", ""))
            abstract_missing = not bool(entry.get("abstract", "").strip())
            if state == "OUTSIDE_WINDOW":
                matched, disposition = "NOT_EVALUATED_DATE_OUTSIDE", "EXCLUDE_DATE"
            else:
                record = canonical_record({**entry, "date_state": state}, "acl", counts["acl_total"], {"raw_file": "05-acl-bulk.body", "text_char_start": begin, "text_char_end": end})
                matched = predicate(record["title"], record["abstract"])
                disposition = "RETAIN" if matched else "EXCLUDE_NO_LOCAL_FIELD_MATCH"
                if matched:
                    parser = BibTexParser(common_strings=True)
                    parser.ignore_nonstandard_types = False
                    reference = bibtexparser.loads(text[begin:end], parser=parser)
                    assert len(reference.entries) == 1
                    assert set(reference.entries[0]) == set(entry)
                    assert all(normalize(reference.entries[0][k]) == normalize(v) for k, v in entry.items())
                    all_records.append(record)
                    counts["acl_retained"] += 1
                    counts["acl_date_unclear_retained"] += state == "UNCLEAR_DATE"
            writer.writerow([counts["acl_total"], entry["ID"], entry["ENTRYTYPE"], abstract_missing, state, matched, disposition, begin, end])
            if counts["acl_total"] % 10000 == 0:
                print(json.dumps({"acl_records_parsed": counts["acl_total"]}), flush=True)
        assert counts["acl_total"] == declared_headers
        assert counts["arxiv_total"] == 395
        ids = [(r["source"], r["source_id"]) for r in all_records]
        assert len(ids) == len(set(ids))
        file = OUT / "metadata_union.jsonl"
        file.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in sorted(all_records, key=lambda r: (r["source"], r["source_id"]))), encoding="utf-8", newline="\n")
        manifest["status"] = "METADATA_PARSED_PENDING_DEDUP_AND_CAP"
    except (OSError, ValueError, TypeError, KeyError, AssertionError, ET.ParseError) as exc:
        manifest.update(status="FRAME_BLOCKED", error_type=type(exc).__name__, error=str(exc)[:300])
    finally:
        if ledger:
            ledger.close()
        manifest["counts"] = counts
        manifest["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        for file in sorted(OUT.iterdir()):
            manifest["files"][file.name] = {"bytes": file.stat().st_size, "sha256": sha(file.read_bytes())}
        (OUT / "METADATA_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": manifest["status"], "counts": counts}), flush=True)
    if manifest["status"] == "FRAME_BLOCKED":
        print(manifest.get("error_type"), manifest.get("error"))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
