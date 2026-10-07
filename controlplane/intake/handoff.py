"""Portable replay of one prepared-export certify result (DECISIONS 236).

The packet is a local collection of retained evidence, not an attestation.
Its checksum manifest has no signer, timestamp authority or custody claim.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any

from ..config import load_customer_config
from .contract import InputError, load_scored_items
from .prepare import verify_prepared
from .verify import load_evidence_record, verify_certification

PROTOCOL = "certify_handoff_v1"
_INTEGRITY = "Local checksums and replay only; no authenticated origin."
_SOURCE_NAMES = {"source.csv", "source.jsonl", "source.ndjson"}
_ROLES = {
    "mapping.json": "source_mapping",
    "prepared/scored.csv": "effective_scored_rows",
    "prepared/manifest.json": "preparation_record",
    "warrant.json": "certify_record",
}


@dataclass(frozen=True)
class HandoffVerification:
    """One packet replay outcome, separate from the warrant verdict."""

    status: str
    reason: str

    @property
    def verified(self) -> bool:
        """Whether every retained evidence link replayed."""
        return self.status == "VERIFIED"


def _regular(path: Path) -> None:
    """Reject links and special files before opening private evidence."""
    if path.is_symlink() or not path.is_file():
        raise InputError(f"handoff member must be a regular file: {path}")


def _digest(path: Path) -> str:
    """Hash a member in bounded memory."""
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _copy(source: Path, target: Path) -> None:
    """Copy only named evidence into an exclusively created member."""
    _regular(source)
    with source.open("rb") as reader, target.open("xb") as writer:
        shutil.copyfileobj(reader, writer, length=1024 * 1024)
        writer.flush()
        os.fsync(writer.fileno())


def _paths(directory: Path, source_name: str, *, frontier: bool) -> dict[str, Path]:
    names = dict(_ROLES)
    names[source_name] = "source_export"
    if frontier:
        names["frontier.json"] = "frontier_record"
    return {name: directory / name for name in names}


def _replay(directory: Path, source_name: str, *, frontier: bool) -> HandoffVerification:
    """Use existing verifiers, preserving their statistical protocols."""
    source = directory / source_name
    mapping = directory / "mapping.json"
    prepared = directory / "prepared"
    if not verify_prepared(source, mapping, prepared):
        return HandoffVerification("MISMATCH", "source, mapping and prepared rows differ")
    record = load_evidence_record(directory / "warrant.json")
    selected = load_evidence_record(directory / "frontier.json") if frontier else None
    items = load_scored_items(prepared / "scored.csv")
    outcome = verify_certification(
        record, items, load_customer_config(), frontier_record=selected,
    )
    return HandoffVerification(outcome.status, outcome.reason)


def _members(directory: Path, source_name: str, *, frontier: bool,
             complete: bool) -> dict[str, Path]:
    """Require the exact fixed file tree, with no symlink traversal."""
    if directory.is_symlink() or not directory.is_dir():
        raise InputError("handoff must be a regular directory")
    expected = {source_name, "mapping.json", "prepared", "warrant.json"}
    if frontier:
        expected.add("frontier.json")
    if complete:
        expected.add("handoff.json")
    if {member.name for member in directory.iterdir()} != expected:
        raise InputError("handoff has missing or unexpected members")
    prepared = directory / "prepared"
    if prepared.is_symlink() or not prepared.is_dir():
        raise InputError("prepared member must be a regular directory")
    if {member.name for member in prepared.iterdir()} != {"scored.csv", "manifest.json"}:
        raise InputError("prepared member has missing or unexpected files")
    paths = _paths(directory, source_name, frontier=frontier)
    if complete:
        paths["handoff.json"] = directory / "handoff.json"
    for member in paths.values():
        _regular(member)
    return paths


def _manifest(directory: Path, source_name: str, *, frontier: bool) -> dict[str, Any]:
    members = _paths(directory, source_name, frontier=frontier)
    roles = dict(_ROLES)
    roles[source_name] = "source_export"
    if frontier:
        roles["frontier.json"] = "frontier_record"
    return {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "status": "COMPLETE",
        "workflow": "prepare+certify",
        "source_name": source_name,
        "members": {
            name: {"role": roles[name], "sha256": _digest(path)}
            for name, path in sorted(members.items())
        },
        "integrity": _INTEGRITY,
    }


def _validated_manifest(path: Path) -> dict[str, Any]:
    """Parse one versioned manifest without accepting alternative file paths."""
    record = load_evidence_record(path)
    if set(record) != {"schema_version", "protocol", "status", "workflow",
                       "source_name", "members", "integrity"}:
        raise InputError("handoff manifest has missing or unexpected fields")
    if (type(record["schema_version"]) is not int or record["schema_version"] != 1
            or record["protocol"] != PROTOCOL or record["status"] != "COMPLETE"
            or record["workflow"] != "prepare+certify"
            or type(record["source_name"]) is not str
            or record["source_name"] not in _SOURCE_NAMES
            or record["integrity"] != _INTEGRITY):
        raise InputError("handoff manifest has unsupported metadata")
    source_name = record["source_name"]
    roles = dict(_ROLES)
    roles[source_name] = "source_export"
    members = record["members"]
    if not isinstance(members, dict):
        raise InputError("handoff manifest members must be an object")
    if "frontier.json" in members:
        roles["frontier.json"] = "frontier_record"
    if set(members) != set(roles):
        raise InputError("handoff manifest has missing or unexpected member paths")
    for name, entry in members.items():
        if (not isinstance(entry, dict) or set(entry) != {"role", "sha256"}
                or entry["role"] != roles[name]
                or type(entry["sha256"]) is not str
                or re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is None):
            raise InputError(f"handoff manifest member is malformed: {name}")
    return record


def create_handoff(source: str | Path, mapping: str | Path, prepared: str | Path,
                   warrant: str | Path, out: str | Path, *,
                   frontier: str | Path | None = None,
                   include_sensitive_input: bool = False) -> Path:
    """Publish a new local packet only after both evidence links replay.

    The opt-in covers copying the original export, which can include excluded
    private columns. A failed copy leaves an incomplete destination for review.
    """
    if not include_sensitive_input:
        raise InputError("--include-sensitive-input is required to copy source rows")
    source_path, mapping_path = Path(source), Path(mapping)
    prepared_path, warrant_path = Path(prepared), Path(warrant)
    suffix = source_path.suffix.lower()
    source_name = f"source{suffix}"
    if source_name not in _SOURCE_NAMES:
        raise InputError("source must be .csv, .jsonl or .ndjson")
    for path in (source_path, mapping_path, warrant_path):
        _regular(path)
    if frontier is not None:
        _regular(Path(frontier))
    if not verify_prepared(source_path, mapping_path, prepared_path):
        raise InputError("prepared rows do not replay from retained source and mapping")
    original = load_evidence_record(warrant_path)
    selected = load_evidence_record(frontier) if frontier is not None else None
    outcome = verify_certification(
        original, load_scored_items(prepared_path / "scored.csv"),
        load_customer_config(), frontier_record=selected,
    )
    if not outcome.verified:
        raise InputError(f"certificate {outcome.status}: {outcome.reason}")

    destination = Path(out)
    destination.mkdir()  # Exclusive reservation: never replace an existing packet.
    (destination / "prepared").mkdir()
    originals = {
        source_name: source_path,
        "mapping.json": mapping_path,
        "prepared/scored.csv": prepared_path / "scored.csv",
        "prepared/manifest.json": prepared_path / "manifest.json",
        "warrant.json": warrant_path,
    }
    if frontier is not None:
        originals["frontier.json"] = Path(frontier)
    for name, path in originals.items():
        _copy(path, destination / name)
    _members(destination, source_name, frontier=frontier is not None, complete=False)
    copied = _replay(destination, source_name, frontier=frontier is not None)
    if not copied.verified:
        raise InputError(f"copied evidence {copied.status}: {copied.reason}")
    manifest = _manifest(destination, source_name, frontier=frontier is not None)
    with (destination / "handoff.json").open("xb") as stream:
        stream.write((json.dumps(manifest, sort_keys=True, indent=2,
                                 allow_nan=False) + "\n").encode("utf-8"))
        stream.flush()
        os.fsync(stream.fileno())
    return destination


def verify_handoff(directory: str | Path) -> HandoffVerification:
    """Check exact packet bytes, then replay preparation and certification."""
    root = Path(directory)
    if root.is_symlink() or not root.is_dir():
        raise InputError("handoff must be a regular directory")
    marker = root / "handoff.json"
    _regular(marker)
    record = _validated_manifest(marker)
    source_name = record["source_name"]
    frontier = "frontier.json" in record["members"]
    paths = _members(root, source_name, frontier=frontier, complete=True)
    for name, entry in record["members"].items():
        if _digest(paths[name]) != entry["sha256"]:
            return HandoffVerification("MISMATCH", f"member bytes changed: {name}")
    return _replay(root, source_name, frontier=frontier)
