"""Explicit, replayable scored-export preparation (DECISIONS 227).

Preparation changes representation only. It never selects an operating point,
infers independence, or promotes a model-generated score into a reference label.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

from .certify import evidence_sha256
from .contract import (
    InputError, _load_scored_items_bytes, _rows_from_csv, _rows_from_jsonl,
    _unique_json_object,
    load_scored_items,
)

PROTOCOL = "scored_export_v1"
_FIELDS = {"id", "label", "score", "group", "label_2"}
_KEYS = {
    "schema_version", "columns", "positive_label", "negative_label",
    "score_direction", "independent_rows",
}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def _mapping(raw: bytes) -> dict[str, Any]:
    try:
        spec = json.loads(raw.decode("utf-8-sig"),
                          object_pairs_hook=_unique_json_object)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("mapping must be UTF-8 JSON") from exc
    if not isinstance(spec, dict) or set(spec) != _KEYS:
        raise InputError(f"mapping requires exactly these keys: {sorted(_KEYS)}")
    if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
        raise InputError("mapping schema_version must be integer 1")
    columns = spec["columns"]
    if (not isinstance(columns, dict) or not {"id", "label", "score"} <= set(columns)
            or not set(columns) <= _FIELDS):
        raise InputError("columns requires id, label, score; optional group, label_2")
    if any(not isinstance(v, str) or not v or v != v.strip()
           for v in columns.values()):
        raise InputError("mapped column names must be nonblank, trimmed strings")
    if len(set(columns.values())) != len(columns):
        raise InputError("each mapped field must use a distinct source column")
    for name in ("positive_label", "negative_label"):
        value = spec[name]
        if not isinstance(value, str) or not value or value != value.strip():
            raise InputError(f"{name} must be a nonblank, trimmed string token")
    if spec["positive_label"] == spec["negative_label"]:
        raise InputError("positive_label and negative_label must differ")
    if spec["score_direction"] not in ("higher", "lower"):
        raise InputError("score_direction must be higher or lower")
    independent = spec["independent_rows"]
    if type(independent) is not bool or independent == ("group" in columns):
        raise InputError("declare independent_rows=true OR map group with false")
    return spec


def _label(value: Any, spec: dict[str, Any], *, optional: bool, row: int) -> str:
    if optional and (value is None or value == ""):
        return ""
    if type(value) not in (str, int, float):
        raise InputError(f"row {row}: label must match a declared scalar token")
    token = str(value).strip()
    if optional and not token:
        return ""
    if token == spec["positive_label"]:
        return "1"
    if token == spec["negative_label"]:
        return "0"
    raise InputError(f"row {row}: label does not match either declared token")


def _build(source: Path, mapping: Path) -> tuple[bytes, bytes]:
    """Read each original once, so hashes bind the actual parsed snapshot."""
    suffix = source.suffix.lower()
    if suffix not in (".csv", ".jsonl", ".ndjson"):
        raise InputError("input must be flat .csv, .jsonl or .ndjson")
    source_raw, mapping_raw = source.read_bytes(), mapping.read_bytes()
    spec = _mapping(mapping_raw)
    columns = spec["columns"]
    try:
        rows, header = (_rows_from_csv(source_raw) if suffix == ".csv"
                        else _rows_from_jsonl(source_raw, source_name="input" + suffix))
    except UnicodeError as exc:
        raise InputError("input must be UTF-8") from exc
    missing = set(columns.values()) - set(header)
    if missing:
        raise InputError(f"mapped columns absent from input: {sorted(missing)}")
    for name in ("group", "label_2"):
        if name in header and columns.get(name) != name:
            raise InputError(f"source contains {name}; explicitly map that column")
    names = [name for name in ("id", "label", "score", "group", "label_2")
             if name in columns]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=names, lineterminator="\n")
    writer.writeheader()
    for number, row in enumerate(rows, 1):
        normalized: dict[str, Any] = {}
        for name in names:
            value = row.get(columns[name])
            if name in ("label", "label_2"):
                normalized[name] = _label(value, spec, optional=name == "label_2",
                                          row=number)
            elif name == "score":
                if type(value) not in (str, int, float):
                    raise InputError(f"row {number}: score must be a finite number")
                try:
                    score = float(value)
                except ValueError as exc:
                    raise InputError(f"row {number}: score must be numeric") from exc
                except OverflowError as exc:
                    raise InputError(
                        f"row {number}: score must be a finite number"
                    ) from exc
                normalized[name] = -score if spec["score_direction"] == "lower" else score
            else:
                if type(value) not in (str, int):
                    raise InputError(f"row {number}: {name} must be a string or integer")
                normalized[name] = str(value).strip()
        writer.writerow(normalized)
    scored = stream.getvalue().encode("utf-8")
    items = _load_scored_items_bytes(scored, require_both_classes=False)

    manifest = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "status": "PREPARED",
        "source_sha256": _digest(source_raw),
        "source_format": "csv" if suffix == ".csv" else "jsonl",
        "mapping_sha256": _digest(mapping_raw),
        "mapping": spec,
        "scored_sha256": _digest(scored),
        "effective_rows_sha256": evidence_sha256(items),
        "excluded_columns": [name for name in header if name not in columns.values()],
        "counts": {
            "rows": items.n, "positive": items.n_positive, "negative": items.n_negative,
            "groups": None if items.groups is None else len(set(items.groups)),
            "second_reviews": sum(x is not None for x in (items.second_labels or ())),
        },
        "scope": "Representation only; not a warrant, independence test, or label audit.",
        "integrity": "Checksums against retained inputs; no authenticated origin.",
    }
    return scored, _json_bytes(manifest)


def prepare_export(source: str | Path, mapping: str | Path, out: str | Path) -> Path:
    """Publish an exclusive local package, with its completion marker last.

    An interrupted destination is deliberately left incomplete, never replaced.
    Preparation preserves invariant 3's declared question/group units without
    claiming that the user's independence declaration has been established.

    Args:
        source: Original flat scored export, retained by the caller.
        mapping: Versioned explicit mapping JSON, also retained by the caller.
        out: New directory under an existing parent; must not already exist.

    Returns:
        The new package directory containing scored.csv and manifest.json.
    """
    scored, manifest = _build(Path(source), Path(mapping))
    destination = Path(out)
    destination.mkdir()  # Exclusive name reservation; no replacement or merging.
    with (destination / "scored.csv").open("xb") as handle:
        handle.write(scored)
    with (destination / "manifest.json").open("xb") as handle:
        handle.write(manifest)
    return destination


def _validate_prepared_manifest(raw: bytes, expected: bytes) -> None:
    """Classify malformed package evidence before comparing valid changed bytes."""
    try:
        record = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except (UnicodeError, json.JSONDecodeError, InputError) as exc:
        raise InputError("prepared manifest.json is not unique-key UTF-8 JSON") from exc
    template = json.loads(expected)
    if not isinstance(record, dict) or set(record) != set(template):
        raise InputError("prepared manifest.json has missing or unexpected fields")
    if (type(record["schema_version"]) is not int or record["schema_version"] != 1
            or record["protocol"] != PROTOCOL or record["status"] != "PREPARED"):
        raise InputError("prepared manifest.json has an unsupported schema or status")
    if (record["source_format"] not in ("csv", "jsonl")
            or any(type(record[key]) is not str for key in ("scope", "integrity"))):
        raise InputError("prepared manifest.json has malformed metadata")
    hashes = ("source_sha256", "mapping_sha256", "scored_sha256",
              "effective_rows_sha256")
    if any(type(record[key]) is not str
           or re.fullmatch(r"[0-9a-f]{64}", record[key]) is None for key in hashes):
        raise InputError("prepared manifest.json has malformed digests")
    if (not isinstance(record["excluded_columns"], list)
            or any(type(value) is not str for value in record["excluded_columns"])):
        raise InputError("prepared manifest.json has malformed excluded columns")
    counts = record["counts"]
    if not isinstance(counts, dict) or set(counts) != set(template["counts"]):
        raise InputError("prepared manifest.json has malformed counts")
    if any(type(counts[key]) is not int or counts[key] < 0
           for key in ("rows", "positive", "negative", "second_reviews")):
        raise InputError("prepared manifest.json has malformed counts")
    if counts["groups"] is not None and (
        type(counts["groups"]) is not int or counts["groups"] < 0
    ):
        raise InputError("prepared manifest.json has malformed group count")
    if not isinstance(record["mapping"], dict):
        raise InputError("prepared manifest.json has malformed mapping")
    try:
        _mapping(_json_bytes(record["mapping"]))
    except (InputError, ValueError, TypeError) as exc:
        raise InputError("prepared manifest.json has malformed mapping") from exc


def verify_prepared(source: str | Path, mapping: str | Path, prepared: str | Path) -> bool:
    """Replay exact package bytes; this does not authenticate the source owner.

    Missing files and malformed originals are errors, not a verified package.
    Unknown additional package files are rejected to keep the handoff explicit.
    """
    expected_scored, expected_manifest = _build(Path(source), Path(mapping))
    directory = Path(prepared)
    if not directory.is_dir() or directory.is_symlink():
        raise InputError("prepared must be a regular package directory")
    members = list(directory.iterdir())
    if {p.name for p in members} != {"scored.csv", "manifest.json"}:
        raise InputError("incomplete or unexpected package files; retain both outputs")
    if any(p.is_symlink() or not p.is_file() for p in members):
        raise InputError("package members must be regular files")
    scored_path = directory / "scored.csv"
    scored = scored_path.read_bytes()
    manifest = (directory / "manifest.json").read_bytes()
    if scored != expected_scored:
        try:
            load_scored_items(scored_path, require_both_classes=False)
        except (InputError, UnicodeError) as exc:
            raise InputError("prepared scored.csv is malformed") from exc
    if manifest != expected_manifest:
        _validate_prepared_manifest(manifest, expected_manifest)
    return scored == expected_scored and manifest == expected_manifest
