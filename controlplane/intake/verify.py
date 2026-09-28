"""Replay a certify result against retained scored rows (DECISIONS 211-212)."""

from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path
from typing import Any, Optional

from ..config import Config
from ..numeric import finite_double
from ..release.contract import canonical_json
from .certify import certify_items, evidence_sha256, input_sha256
from .chain import canonical_sha256
from .contract import ScoredItems
from .frontier import frontier

__all__ = [
    "CertificationVerification", "FRONTIER_METRICS_NOTE", "load_evidence_record",
    "verify_certification",
]

FRONTIER_METRICS_NOTE = (
    "Only the false-positive bound is adjusted for the pick. Recall and "
    "precision are measured on the file the budget was picked from, and "
    "a pick made by reading the frontier's caught and missed columns "
    "selects on them, so they carry that optimism (DECISIONS 195)."
)


@dataclasses.dataclass(frozen=True)
class CertificationVerification:
    """A replay result, deliberately distinct from the warrant's verdict."""

    status: str
    reason: str

    @property
    def verified(self) -> bool:
        return self.status == "VERIFIED"


def load_evidence_record(path: str | Path) -> dict[str, Any]:
    """Read one unambiguous JSON object; duplicate keys cannot silently win."""

    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> Any:
        raise ValueError(f"{path}: non-finite JSON number {value}")

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"),
                           object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: malformed JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: record must contain a JSON object")
    return value


def _result(status: str, reason: str) -> CertificationVerification:
    return CertificationVerification(status=status, reason=reason)


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return value


def verify_certification(
    record: dict[str, Any], items: ScoredItems, config: Config, *,
    frontier_record: Optional[dict[str, Any]] = None,
) -> CertificationVerification:
    """Recompute material certificate fields; never infer authorship or time.

    A matching file and record can still be rewritten together by their holder.
    This is arithmetic and input-binding verification, not authentication.
    """
    record = _mapping(record, "warrant")
    recorded_input = _mapping(record.get("input"), "warrant.input")
    binding = recorded_input.get("evidence_sha256")
    if binding is None:
        return _result("UNVERIFIED", "legacy warrant has no effective-row binding; re-certify")
    if not isinstance(binding, str) or re.fullmatch(r"[0-9a-f]{64}", binding) is None:
        raise ValueError("warrant.input.evidence_sha256 must be a lowercase SHA-256 digest")
    if binding != evidence_sha256(items):
        return _result("MISMATCH", "effective scored-row sequence differs from the warrant")

    provenance = _mapping(record.get("provenance"), "warrant.provenance")
    recorded_config = provenance.get("config_hash")
    if recorded_config is None:
        return _result("UNVERIFIED", "warrant has no configuration hash")
    if recorded_config != config.config_hash:
        return _result("MISMATCH", "current configuration differs from the warrant")

    budget = finite_double(record.get("budget_fpr"), "warrant.budget_fpr")
    if not 0.0 < budget < 1.0:
        raise ValueError("warrant.budget_fpr must be in (0, 1)")
    source = recorded_input.get("source")
    if not isinstance(source, str) or not source:
        raise ValueError("warrant.input.source must be nonempty text")

    selection = record.get("selection")
    expected_selection: Optional[dict[str, Any]] = None
    if selection is None:
        if frontier_record is not None:
            raise ValueError("--frontier is only for a warrant picked from a frontier")
        alpha = finite_double(record.get("alpha"), "warrant.alpha")
        if not 0.0 < alpha < 1.0:
            raise ValueError("warrant.alpha must be in (0, 1)")
    else:
        selection = _mapping(selection, "warrant.selection")
        if frontier_record is None:
            return _result("UNVERIFIED", "selected warrant needs its retained --frontier record")
        frontier_record = _mapping(frontier_record, "frontier")
        frontier_provenance = _mapping(frontier_record.get("provenance"),
                                       "frontier.provenance")
        if frontier_provenance.get("config_hash") != config.config_hash:
            return _result("MISMATCH", "frontier configuration differs from the warrant")
        frontier_input = _mapping(frontier_record.get("input"), "frontier.input")
        if frontier_input.get("input_sha256") != input_sha256(items):
            return _result("MISMATCH", "frontier was computed from different scored rows")
        if selection.get("from_frontier") != canonical_sha256(frontier_record):
            return _result("MISMATCH", "frontier record differs from the selected one")
        computed_rows = [point.to_payload() for point in frontier(config, items)]
        if canonical_json(frontier_record.get("frontier")) != canonical_json(computed_rows):
            return _result("MISMATCH", "frontier rows do not recompute")
        first = computed_rows[0]
        expected_selection = {
            "from_frontier": canonical_sha256(frontier_record),
            "grid": [row["budget_fpr"] for row in computed_rows],
            "row_alpha": first["row_alpha"],
            "family_alpha": first["family_alpha"],
            "metrics_note": FRONTIER_METRICS_NOTE,
        }
        if canonical_json(selection) != canonical_json(expected_selection):
            return _result("MISMATCH", "selected frontier details differ from recomputation")
        alpha = first["row_alpha"]

    # The path is a declaration and need not be the path of a retained copy.
    # Replaying with the recorded path preserves the original explanatory text.
    replay_items = dataclasses.replace(items, source=source)
    expected = certify_items(config, replay_items, budget=budget, alpha=alpha,
                             selection=expected_selection).to_payload()
    for key, computed in expected.items():
        if key == "frontier_record_present":
            continue  # Whether a sibling file existed is not a statistic.
        if key not in record or canonical_json(record[key]) != canonical_json(computed):
            return _result("MISMATCH", f"warrant.{key} differs from recomputation")
    extra = set(record) - set(expected) - {"provenance"}
    if extra:
        return _result("MISMATCH", f"unexpected warrant fields: {sorted(extra)}")
    return _result("VERIFIED", "effective rows and material certificate fields recompute")
