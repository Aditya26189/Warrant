"""Freeze separately checked known-work bibliographic fields, never paper bodies."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import release_deep as r

HERE = Path(__file__).resolve().parent
CACHE = r.CACHE


def build(index_path: Path) -> tuple[dict, dict[str, bytes]]:
    """Retain literal date/type semantics and exact checker/provider bindings."""
    index_raw = index_path.read_bytes()
    index = json.loads(index_raw)
    supplement_path = CACHE / "PUBLISHER_SOURCES_SUPPLEMENT.0001.json"
    supplement_raw = supplement_path.read_bytes()
    if r.sha(supplement_raw) != index["source_supplement_sha256"]:
        raise ValueError("METADATA_ROUTING_CHANGED")
    supplement = json.loads(supplement_raw)
    files = {"CHECKER_INDEX.json": index_raw, "SOURCE_ROUTING.json": supplement_raw}
    facts = []
    for entry in index["files"]:
        checker_raw = (index_path.parent / entry["path"]).read_bytes()
        if r.sha(checker_raw) != entry["sha256"]:
            raise ValueError("METADATA_CHECKER_CHANGED")
        checker = json.loads(checker_raw)
        if checker["provider_supplement_sha256"] != r.sha(supplement_raw):
            raise ValueError("FOREIGN_METADATA_ROUTING")
        receipts = {}
        for source in checker["sources"]:
            raw = Path(source["receipt"]).read_bytes()
            if r.sha(raw) != source["receipt_sha256"] or r.sha(Path(source["raw_path"]).read_bytes()) != source["raw_sha256"]:
                raise ValueError("METADATA_SOURCE_CHANGED")
            receipts[source["receipt"]] = json.loads(raw)
            files["provider/" + Path(source["receipt"]).name] = raw
        name = "checker/" + Path(entry["path"]).name
        files[name] = checker_raw
        for n, check in enumerate(checker["per_fact"], 1):
            if check["decision"] != "APPROVE":
                continue
            if re.fullmatch(r"records\[\d+\]\.status", check["field_path"]):
                # Exact transport attempts remain in provider/checker receipts.
                # A status code is not a bibliographic edition/type assertion.
                continue
            match = re.fullmatch(r"records\[(\d+)\]\.metadata_fields\[(\d+)\]", check["field_path"])
            if match:
                record = supplement["records"][int(match[1])]
                receipt = receipts[record["receipt"]]
                item = receipt["metadata_fields"][int(match[2])]
                value = item["value"]
                field = item["field"]
                raw_hash = receipt["raw_source_sha256"]
                value_hash = r.sha(value.encode())
            elif check["field_path"].startswith("receipt.bibliographic_fields."):
                field = check["field_path"].removeprefix("receipt.bibliographic_fields.")
                selected = [x for x in receipts.values() if field in x.get("bibliographic_fields", {})]
                if len(selected) != 1:
                    raise ValueError("AMBIGUOUS_JSON_METADATA")
                receipt = selected[0]
                value = receipt["bibliographic_fields"][field]
                raw_hash = receipt["raw_source_sha256"]
                value_hash = r.sha(json.dumps(value, sort_keys=True).encode())
                if value != check["value"]:
                    raise ValueError("CHECKER_METADATA_VALUE_CHANGED")
            else:
                raise ValueError("UNSUPPORTED_METADATA_FIELD")
            if value_hash != check["value_sha256"] or receipt["review_id"] != checker["review_id"]:
                raise ValueError("METADATA_VALUE_OR_WORK_CHANGED")
            provider = receipt.get("actor")
            if not provider or provider == checker["actor"]:
                raise ValueError("METADATA_SELF_CHECK")
            facts.append({"evidence_id": "A05-BIB-DEEP-" + checker["review_id"] + "-" + r.sha(checker_raw)[:12] + "-F" + str(n).zfill(2),
                          "review_id": checker["review_id"], "field": field, "value": value,
                          "source_locator": check["source_locator"], "raw_source_sha256": raw_hash,
                          "source_receipt": "provider/" + next(Path(p).name for p, x in receipts.items() if x is receipt),
                          "checker_receipt": name, "checker_receipt_sha256": r.sha(checker_raw),
                          "provider_actor": provider, "checker_actor": checker["actor"],
                          "semantics": check["semantic_fidelity"], "fact_kind": "BIBLIOGRAPHY_ONLY",
                          "release_status": "SEPARATELY_CHECKED_LITERAL_METADATA_NOT_EDITION_DECISION"})
    return {"schema": "A05_CHECKED_BIBLIOGRAPHY_RELEASE_v1", "facts": facts,
            "source_files": {name: r.sha(raw) for name, raw in files.items()},
            "limits": "Literal bibliographic fields only; HTTP/DOI access is not VOR/edition proof. No discovery, methods, outcomes or eligibility labels."}, files


def main() -> None:
    """Write one new immutable release from a clean committed generator."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{3}", args.run):
        raise ValueError("BAD_RUN")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=HERE, text=True).strip():
        raise ValueError("DIRTY_TREE")
    release, files = build(args.index)
    release["source_git_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    destination = HERE / "bibliography" / args.run
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (destination / "FACTS.json").write_bytes(r.encoded(release))
    print(json.dumps({"facts": len(release["facts"]), "works": len({x["review_id"] for x in release["facts"]})}))


if __name__ == "__main__":
    main()
