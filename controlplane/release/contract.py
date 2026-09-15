"""Freeze identity, selection and holdout membership before evaluation.

DECISIONS 184: hashes detect changes relative to a retained trusted copy. They
are not signatures, anonymisation, or proof that a holdout was never inspected.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def canonical_json(value: Any) -> bytes:
    """Use one finite, deterministic encoding for every evidence digest."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    """Bind structured values without relying on indentation or key order."""
    return hashlib.sha256(canonical_json(value)).hexdigest()


def utc_time(value: str) -> datetime:
    """Reject naive times so expiry cannot depend on the reader's timezone."""
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO 8601 string with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be ISO 8601 with timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def timestamp(now: datetime | None = None) -> str:
    """Keep test clocks injectable without accepting timezone ambiguity."""
    return utc_time((now or datetime.now(timezone.utc)).isoformat()).isoformat()


def _keys(value: dict, expected: set[str], name: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{name} must contain exactly: {', '.join(sorted(expected))}")


@dataclass(frozen=True)
class ReleaseSpec:
    """Declared criteria; positive recall prevents a never-fire detector passing."""

    system_id: str
    system_version: str
    detector_id: str
    detector_version: str
    scope: str
    positive_label: str
    threshold: float
    max_fpr: float
    min_recall: float
    alpha: float
    expires_at: str
    data_origin: str
    sampling_assumption: str

    def __post_init__(self) -> None:
        for key in ("system_id", "system_version", "detector_id", "detector_version",
                    "scope", "positive_label"):
            value = getattr(self, key)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{key} must be a nonempty, trimmed string")
        for key in ("threshold", "max_fpr", "min_recall", "alpha"):
            value = getattr(self, key)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"{key} must be a finite number, not a boolean")
        for key in ("max_fpr", "min_recall", "alpha"):
            if not 0 < getattr(self, key) < 1:
                raise ValueError(f"{key} must be strictly between 0 and 1")
        if not 0 < self.alpha / 10 < 1 - self.alpha / 10 < 1:
            raise ValueError("alpha is outside supported floating-point precision")
        utc_time(self.expires_at)
        if self.data_origin not in ("customer", "synthetic"):
            raise ValueError("data_origin must be customer or synthetic")
        if self.sampling_assumption != "iid":
            raise ValueError("this release workflow supports sampling_assumption=iid only")

    @classmethod
    def from_dict(cls, value: dict) -> ReleaseSpec:
        """Reject unknown keys so misspelled acceptance criteria cannot vanish."""
        _keys(value, {f.name for f in fields(cls)}, "release specification")
        return cls(**value)


def id_hashes(ids: Iterable[str]) -> tuple[str, ...]:
    """Check membership without exporting raw IDs; hashes remain sensitive.

    Unsalted hashes allow guessing low-entropy IDs. Stable independent question
    IDs and detection of semantic duplicates remain the caller's responsibility.
    """
    values = tuple(ids)
    if not values or any(not isinstance(i, str) or not i or i != i.strip() for i in values):
        raise ValueError("ID manifests require nonempty, trimmed strings")
    if len(set(values)) != len(values):
        raise ValueError("ID manifests must not contain duplicates")
    return tuple(sorted(digest({"item_id": i}) for i in values))


@dataclass(frozen=True)
class ReleaseContract:
    """A content-addressed local registration, never a trusted timestamp."""

    spec: ReleaseSpec
    created_at: str
    development_ids: tuple[str, ...]
    holdout_ids: tuple[str, ...]
    schema_version: int = 2

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version not in (1, 2):
            raise ValueError("unsupported contract schema_version")
        if utc_time(self.created_at) >= utc_time(self.spec.expires_at):
            raise ValueError("contract must expire after registration")
        for values in (self.development_ids, self.holdout_ids):
            if not values or any(not isinstance(i, str) or len(i) != 64 or
                                any(c not in "0123456789abcdef" for c in i) for i in values):
                raise ValueError("invalid SHA-256 identifier in manifest")
            if tuple(sorted(set(values))) != values:
                raise ValueError("hashed ID manifests must be sorted and unique")
        if set(self.development_ids) & set(self.holdout_ids):
            raise ValueError("development and holdout IDs overlap")

    def to_dict(self) -> dict:
        """Include the method version in the registration's identity."""
        body = {"schema_version": self.schema_version, "kind": "warrant.release.contract",
                "spec": asdict(self.spec), "created_at": self.created_at,
                "development_ids": list(self.development_ids),
                "holdout_ids": list(self.holdout_ids)}
        return {**body, "contract_id": digest(body)}

    @classmethod
    def from_dict(cls, value: dict) -> ReleaseContract:
        """Check integrity and structure before a record can affect a result."""
        _keys(value, {"schema_version", "kind", "spec", "created_at",
                      "development_ids", "holdout_ids", "contract_id"}, "contract")
        if type(value["schema_version"]) is not int or value["schema_version"] not in (1, 2):
            raise ValueError("unsupported contract schema_version")
        if value["kind"] != "warrant.release.contract":
            raise ValueError("not a release contract")
        body = {k: v for k, v in value.items() if k != "contract_id"}
        if digest(body) != value["contract_id"]:
            raise ValueError("contract integrity check failed")
        for key in ("development_ids", "holdout_ids"):
            if not isinstance(value[key], list):
                raise ValueError(f"{key} must be an array")
        return cls(ReleaseSpec.from_dict(value["spec"]), value["created_at"],
                   tuple(value["development_ids"]), tuple(value["holdout_ids"]),
                   value["schema_version"])


def register(spec: ReleaseSpec, development_ids: Iterable[str],
             holdout_ids: Iterable[str], *, now: datetime | None = None) -> ReleaseContract:
    """Freeze disjoint membership, enforcing the question-split invariant."""
    return ReleaseContract(spec, timestamp(now), id_hashes(development_ids),
                           id_hashes(holdout_ids))


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def read_document(path: Path) -> dict:
    """Reject duplicate keys and nonstandard non-finite JSON numbers."""
    value = json.loads(path.read_text(encoding="utf-8-sig"),
                       object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
    if not isinstance(value, dict):
        raise ValueError("document must be a JSON object")
    return value


def write_document(path: Path, value: dict) -> None:
    """Refuse replacement, including concurrent attempts at the same path.

    An interrupted write can leave an incomplete file; verification rejects it.
    There is no overwrite flag to silently erase a previous decision.
    """
    payload = canonical_json(value) + b"\n"
    with path.open("xb") as handle:
        handle.write(payload)


def read_ids(path: Path) -> tuple[str, ...]:
    """Require one stable ID per line, without blanks or duplicates."""
    values = tuple(path.read_text(encoding="utf-8-sig").splitlines())
    id_hashes(values)
    return values
