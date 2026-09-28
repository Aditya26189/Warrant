"""Replay a sealed linear chain prefix from retained scored batches (215)."""

from __future__ import annotations

import dataclasses
import re
from typing import Any, Optional, Sequence

from ..config import Config
from ..release.contract import canonical_json
from .certify import evidence_sha256
from .chain import ChainError, canonical_sha256, continue_chain, feed, record_sha256, start_chain
from .chain_verify import verify_chain_records
from .contract import ScoredItems
from .recheck import apply_chain, chain_units, require_chain_replaced
from .verify import CertificationVerification, verify_certification
from .verify_recheck import replay_measurement_from_warrant

__all__ = ["verify_chained_rechecks"]


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return value


def _result(status: str, reason: str) -> CertificationVerification:
    return CertificationVerification(status=status, reason=reason)


def verify_chained_rechecks(
    warrant: dict[str, Any], pairs: Sequence[tuple[str, dict[str, Any], ScoredItems]],
    config: Config, *, certificate_items: Optional[ScoredItems] = None,
    frontier_record: Optional[dict[str, Any]] = None,
) -> CertificationVerification:
    """Recompute every link in a presented, sealed, linear prefix.

    The result is scoped to these retained links. No mutable publication head
    is consulted, and missing later links or deliberately omitted forks are
    unknowable from one prefix (DECISIONS 215).
    """
    warrant = _mapping(warrant, "warrant")
    if not pairs:
        raise ValueError("at least one --pair RECORD FRESH is required")
    names = [name for name, _, _ in pairs]
    if len(set(names)) != len(names):
        raise ValueError("each --pair must name a distinct record")
    records: dict[str, dict[str, Any]] = {}
    for name, record, _ in pairs:
        record = _mapping(record, f"recheck {name}")
        _mapping(record.get("chain"), f"recheck {name}.chain")
        records[name] = record

    structure = verify_chain_records(records)
    if structure.unsealed:
        return _result("UNVERIFIED", "a retained chain link has no whole-record seal")
    if structure.findings:
        kinds = {finding.kind for finding in structure.findings}
        grade = "UNVERIFIED" if kinds <= {"missing_link", "sequence"} else "MISMATCH"
        return _result(grade, "retained chain is not clean: " + ", ".join(sorted(kinds)))

    source_digest = canonical_sha256(warrant)
    recorded_input = _mapping(warrant.get("input"), "warrant.input")
    statuses: set[str] = set()
    for position, (name, record, items) in enumerate(pairs, start=1):
        block = _mapping(record["chain"], f"recheck {name}.chain")
        if block.get("sequence") != position:
            return _result("UNVERIFIED", "pairs must start at link 1 and be in sequence")
        expected_head_check = "no_sidecar" if position == 1 else "matched"
        if block.get("head_check") != expected_head_check:
            return _result("UNVERIFIED", "fork or head-check history needs more than a linear prefix")
        now = _mapping(record.get("now"), f"recheck {name}.now")
        binding = now.get("evidence_sha256")
        if binding is None:
            return _result("UNVERIFIED", "a chain link has no fresh effective-row binding")
        if not isinstance(binding, str) or re.fullmatch(r"[0-9a-f]{64}", binding) is None:
            raise ValueError(f"recheck {name}.now.evidence_sha256 must be a lowercase SHA-256 digest")
        if binding != evidence_sha256(items):
            return _result("MISMATCH", f"fresh effective rows differ at link {position}")

        prior = _mapping(record.get("prior_warrant"), f"recheck {name}.prior_warrant")
        digest = prior.get("warrant_sha256")
        status = prior.get("certificate_verification")
        if digest is None or status is None:
            return _result("UNVERIFIED", "a chain link has no certificate binding or source-check grade")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError(f"recheck {name}.prior_warrant.warrant_sha256 must be a lowercase SHA-256 digest")
        if digest != source_digest:
            return _result("MISMATCH", f"certificate differs from the source of link {position}")
        if status not in ("VERIFIED", "NOT_CHECKED"):
            raise ValueError(f"recheck {name}.prior_warrant.certificate_verification is invalid")
        statuses.add(status)
        provenance = _mapping(record.get("provenance"), f"recheck {name}.provenance")
        if provenance.get("config_hash") is None:
            return _result("UNVERIFIED", "a chain link has no configuration hash")
        if provenance["config_hash"] != config.config_hash:
            return _result("MISMATCH", f"configuration differs at link {position}")
        if (recorded_input.get("grouped") is not None
                and bool(recorded_input["grouped"]) != (items.groups is not None)):
            return _result("MISMATCH", f"grouping differs at link {position}")

    if "VERIFIED" in statuses:
        if certificate_items is None:
            return _result("UNVERIFIED", "VERIFIED source needs --certificate-input for replay")
        checked = verify_certification(
            warrant, certificate_items, config, frontier_record=frontier_record,
        )
        if not checked.verified:
            return _result(checked.status, f"source certificate: {checked.reason}")
    elif certificate_items is not None or frontier_record is not None:
        raise ValueError("certificate evidence applies only when a link recorded source VERIFIED")

    alpha = warrant.get("alpha", 1.0 - config.validation.ci)
    previous: Optional[dict[str, Any]] = None
    for position, (name, record, items) in enumerate(pairs, start=1):
        block = record["chain"]
        try:
            if previous is None:
                state = start_chain(
                    warrant, horizon_units=block["horizon_units"], alpha=alpha,
                )
            else:
                state = continue_chain(
                    previous, warrant, alpha=alpha,
                    head=record_sha256(previous, "retained previous record"),
                    head_status=previous.get("status"),
                )
            base = replay_measurement_from_warrant(warrant, items, config)
            fed = feed(state, *chain_units(items, base.threshold))
            result = apply_chain(base, fed)
            require_chain_replaced(result)
        except ChainError as exc:
            return _result("MISMATCH", f"link {position} cannot replay: {exc}")
        result = dataclasses.replace(
            result, warrant_sha256=source_digest,
            certificate_verification=record["prior_warrant"]["certificate_verification"],
            evidence_sha256=record["now"]["evidence_sha256"],
        )
        expected = result.to_payload()
        for key, computed in expected.items():
            if key not in record or canonical_json(record[key]) != canonical_json(computed):
                return _result("MISMATCH", f"recheck.{key} differs at link {position}")
        if canonical_json(block) != canonical_json(fed.to_payload()):
            return _result("MISMATCH", f"chain statistic differs at link {position}")
        extra = set(record) - set(expected) - {"provenance", "chain", "record_sha256"}
        if extra:
            return _result("MISMATCH", f"unexpected fields at link {position}: {sorted(extra)}")
        previous = record

    unchecked = "NOT_CHECKED" in statuses
    note = (
        "; at least one source certificate was NOT_CHECKED at publication"
        if unchecked else "; source certificate also replayed"
    )
    return _result("VERIFIED", f"presented linear prefix through link {len(pairs)} recomputes{note}")
