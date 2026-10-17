"""Resolve A02 bibliographic identities before domain screening or selection.

Use explicit DOI/arXiv identifiers, then exact normalized titles plus named
authors. Omitted middle names are compatible only when full first/family names
and the complete author list agree; conflicting names remain unresolved.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
import subprocess
import urllib.parse

import prepare_a02_metadata as p

BASE = Path(__file__).resolve().parent
OUT = BASE / "a02-dedup"


def doi(value: str) -> str:
    """Canonicalize identifier syntax without interpreting paper contents."""
    value = urllib.parse.unquote(value).strip().casefold()
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)


def arxiv(value: str) -> str:
    """Match the work family independently of a retained source version."""
    match = re.search(r"(?<![0-9])([0-9]{4}\.[0-9]{4,5})(?:v[0-9]+)?", value)
    return match.group(1) if match else ""


def names(value: str) -> list[tuple[str, ...]]:
    """Retain every name token; BibTeX comma order is immaterial to identity."""
    value = p.latex_to_unicode(value)
    return [tuple(re.findall(r"[^\W_]+", p.normalize(person)))
            for person in re.split(r"\s+and\s+", value) if person.strip()]


def author_match(left: str, right: str) -> str | None:
    """Accept exact names or unconflicted omitted middle names, never initials."""
    a, b = names(left), names(right)
    if not a or len(a) != len(b):
        return None
    if sorted(tuple(sorted(n)) for n in a) == sorted(tuple(sorted(n)) for n in b):
        return "EXACT_NAMED_AUTHORS"
    # For BibTeX lists, family comes first; the arXiv list has given names first.
    def structured(raw: str) -> list[tuple[str, str, tuple[str, ...]]]:
        result = []
        for person in re.split(r"\s+and\s+", p.latex_to_unicode(raw)):
            if "," in person:
                family, given = person.split(",", 1)
                family_tokens = re.findall(r"[^\W_]+", p.normalize(family))
                given_tokens = re.findall(r"[^\W_]+", p.normalize(given))
            else:
                tokens = re.findall(r"[^\W_]+", p.normalize(person))
                family_tokens, given_tokens = tokens[-1:], tokens[:-1]
            if not family_tokens or not given_tokens or len(given_tokens[0]) == 1:
                return []
            result.append((" ".join(family_tokens), given_tokens[0], tuple(given_tokens[1:])))
        return sorted(result)
    x, y = structured(left), structured(right)
    if len(x) != len(a) or len(y) != len(b):
        return None
    if len({(z[0], z[1]) for z in x}) != len(x):
        return None
    for u, v in zip(x, y, strict=True):
        if u[:2] != v[:2] or (u[2] and v[2] and u[2] != v[2]):
            return None
    return "MATCHING_FULL_FIRST_FAMILY_NAMES_OMITTED_MIDDLE_NAMES"


def main() -> int:
    """Preserve the entire crosswalk, uncertainty and cap disposition once."""
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError("Refusing dirty-tree deduplication")
    if OUT.exists():
        raise RuntimeError("Refusing overwrite")
    source = BASE / "a02-metadata/metadata_union.jsonl"
    records = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    assert all(r["source"] in {"arxiv", "acl"} for r in records)
    parent = list(range(len(records)))
    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    links = []
    def join(i: int, j: int, reason: str) -> None:
        a, b = root(i), root(j)
        if a != b:
            parent[max(a, b)] = min(a, b)
        links.append({"left": [records[i]["source"], records[i]["source_id"]],
                      "right": [records[j]["source"], records[j]["source_id"]], "reason": reason})
    identifiers = {}
    titles = {}
    for i, r in enumerate(records):
        for key in (["doi:" + doi(r["doi"])] if r["doi"] else []) + (["arxiv:" + arxiv(r["source_id"])] if r["source"] == "arxiv" else []):
            if key in identifiers:
                join(i, identifiers[key], "EXPLICIT_IDENTIFIER:" + key)
            else:
                identifiers[key] = i
        titles.setdefault(r["normalized_title"], []).append(i)
    unresolved = []
    for title, group in titles.items():
        for pos, i in enumerate(group):
            for j in group[pos + 1:]:
                if root(i) == root(j):
                    continue
                match = author_match(records[i]["authors_raw"], records[j]["authors_raw"])
                if match:
                    join(i, j, "EXACT_NORMALIZED_TITLE_PLUS_" + match)
                else:
                    unresolved.append({"left": [records[i]["source"], records[i]["source_id"]],
                                       "right": [records[j]["source"], records[j]["source_id"]],
                                       "title": title, "status": "HUMAN_METADATA_ADJUDICATION_REQUIRED"})
    groups = {}
    for i, r in enumerate(records):
        groups.setdefault(root(i), []).append(r)
    works = []
    for group in groups.values():
        ids = sorted({"doi:" + doi(r["doi"]) for r in group if r["doi"]})
        ids += sorted({"arxiv:" + arxiv(r["source_id"]) for r in group if r["source"] == "arxiv"})
        ids += sorted({"acl:" + urllib.parse.urlparse(r["url"]).path.strip("/") for r in group if r["source"] == "acl"})
        works.append({"work_id": ids[0], "identifiers": ids,
                      "members": [{"source": r["source"], "source_id": r["source_id"]} for r in group],
                      "version_selection": "PENDING", "domain_eligibility": "NOT_RUN"})
    OUT.mkdir()
    outputs = {"dedup_links.json": links, "unresolved_pairs.json": unresolved,
               "work_records.json": sorted(works, key=lambda w: w["work_id"])}
    for name, data in outputs.items():
        (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    manifest = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "source_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "source_tree_clean_at_start": True, "metadata_union_sha256": p.sha(source.read_bytes()),
                "script_sha256": p.sha(Path(__file__).read_bytes()),
                "protocol_lock_A02_sha256": p.sha((BASE / "PROTOCOL_LOCK_A02.json").read_bytes()),
                "source_records": len(records), "resolved_work_groups": len(works),
                "unresolved_pairs": len(unresolved), "unique_work_screening_cap": 500,
                "cap_check": "PASS" if len(records) <= 500 else "REQUIRES_FINAL_IDENTITY_COUNT",
                "status": "FRAME_BLOCKED" if unresolved or len(works) > 500 else "DEDUP_COMPLETE_READY_FOR_DOMAIN_SCREENING",
                "outcome_use": "NONE", "eligibility": "NOT_RUN", "randomization": "NOT_RUN",
                "files": {name: p.sha((OUT / name).read_bytes()) for name in outputs}}
    (OUT / "DEDUP_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: manifest[k] for k in ("status", "source_records", "resolved_work_groups", "unresolved_pairs", "cap_check")}))
    return 2 if manifest["status"] == "FRAME_BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
