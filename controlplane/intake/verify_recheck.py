"""Replay one ordinary recheck from retained effective rows (DECISIONS 214)."""

from __future__ import annotations

import dataclasses
import re
from typing import Any, Optional

from ..config import Config
from ..model import EnvelopeFeature
from ..release.contract import canonical_json
from .certify import evidence_sha256
from .chain import canonical_sha256
from .contract import ScoredItems
from .recheck import RecheckResult, recheck_items
from .verify import CertificationVerification, verify_certification

__all__ = ["replay_measurement_from_warrant", "verify_recheck"]


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return value


def _result(status: str, reason: str) -> CertificationVerification:
    return CertificationVerification(status=status, reason=reason)


def replay_measurement_from_warrant(
    warrant: dict[str, Any], items: ScoredItems, config: Config,
) -> RecheckResult:
    """Recompute the pre-chain measurement using the issuer's warrant fields.

    Both ordinary and chained replay use this adapter so the threshold,
    reference distribution, reference sample size and alpha are read exactly
    as ``warrant recheck`` reads them, not reinterpreted by each verifier.
    """
    certification = _mapping(warrant.get("certification"), "warrant.certification")
    threshold = certification.get("threshold")
    budget = warrant.get("budget_fpr")
    if threshold is None or budget is None:
        raise ValueError("warrant has no certified threshold and budget")
    recorded_input = _mapping(warrant.get("input"), "warrant.input")
    distribution = warrant.get("score_distribution")
    if distribution is not None:
        distribution = _mapping(distribution, "warrant.score_distribution")
    try:
        reference = (
            EnvelopeFeature(
                name=distribution["name"],
                bin_edges=tuple(distribution["bin_edges"]),
                bin_probabilities=tuple(distribution["bin_probabilities"]),
                mean=distribution["mean"], std=distribution["std"],
            ) if distribution else None
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid warrant.score_distribution: {exc}") from exc
    return recheck_items(
        config, items, budget=budget, threshold=threshold, reference=reference,
        reference_n=recorded_input.get("n"), alpha=warrant.get("alpha"),
    )


def verify_recheck(
    record: dict[str, Any], warrant: dict[str, Any], items: ScoredItems,
    config: Config, *, certificate_items: Optional[ScoredItems] = None,
    frontier_record: Optional[dict[str, Any]] = None,
) -> CertificationVerification:
    """Check an ordinary recheck's binding and exact material recomputation.

    This cannot attest custody or replay a sequential chain from one link.
    Invariant 214 excludes chained and chain-revoked lifecycle records rather
    than presenting a partial arithmetic check as a full verification.
    """
    record = _mapping(record, "recheck")
    warrant = _mapping(warrant, "warrant")
    if "chain" not in record or record["chain"] is not None:
        return _result("UNVERIFIED", "chained or legacy recheck needs retained chain context")

    now = _mapping(record.get("now"), "recheck.now")
    binding = now.get("evidence_sha256")
    if binding is None:
        return _result("UNVERIFIED", "recheck has no fresh effective-row binding")
    if not isinstance(binding, str) or re.fullmatch(r"[0-9a-f]{64}", binding) is None:
        raise ValueError("recheck.now.evidence_sha256 must be a lowercase SHA-256 digest")
    if binding != evidence_sha256(items):
        return _result("MISMATCH", "fresh effective scored-row sequence differs")

    prior = _mapping(record.get("prior_warrant"), "recheck.prior_warrant")
    if prior.get("chain_revoked_at") is not None:
        return _result("UNVERIFIED", "chain-revoked lifecycle needs retained chain context")
    source_digest = prior.get("warrant_sha256")
    source_status = prior.get("certificate_verification")
    if source_digest is None or source_status is None:
        return _result("UNVERIFIED", "recheck has no certificate binding or source-check grade")
    if not isinstance(source_digest, str) or re.fullmatch(r"[0-9a-f]{64}", source_digest) is None:
        raise ValueError("recheck.prior_warrant.warrant_sha256 must be a lowercase SHA-256 digest")
    if source_digest != canonical_sha256(warrant):
        return _result("MISMATCH", "retained certificate differs from the recheck source")
    if source_status not in ("VERIFIED", "NOT_CHECKED"):
        raise ValueError("recheck.prior_warrant.certificate_verification is invalid")
    if source_status == "VERIFIED":
        if certificate_items is None:
            return _result("UNVERIFIED", "VERIFIED source needs --certificate-input for replay")
        checked = verify_certification(
            warrant, certificate_items, config, frontier_record=frontier_record,
        )
        if not checked.verified:
            return _result(checked.status, f"source certificate: {checked.reason}")
    elif certificate_items is not None or frontier_record is not None:
        raise ValueError("certificate evidence applies only to a recheck recorded as VERIFIED")

    provenance = _mapping(record.get("provenance"), "recheck.provenance")
    if provenance.get("config_hash") is None:
        return _result("UNVERIFIED", "recheck has no configuration hash")
    if provenance["config_hash"] != config.config_hash:
        return _result("MISMATCH", "current configuration differs from the recheck")

    recorded_input = _mapping(warrant.get("input"), "warrant.input")
    if recorded_input.get("grouped") is not None and bool(recorded_input["grouped"]) != (items.groups is not None):
        return _result("MISMATCH", "fresh-file grouping differs from the certificate")
    replay = replay_measurement_from_warrant(warrant, items, config)
    expected = dataclasses.replace(
        replay, warrant_sha256=source_digest,
        certificate_verification=source_status, evidence_sha256=binding,
    ).to_payload()
    for key, computed in expected.items():
        if key not in record or canonical_json(record[key]) != canonical_json(computed):
            return _result("MISMATCH", f"recheck.{key} differs from recomputation")
    extra = set(record) - set(expected) - {"provenance", "chain"}
    if extra:
        return _result("MISMATCH", f"unexpected recheck fields: {sorted(extra)}")
    source_note = (
        "source certificate also replayed" if source_status == "VERIFIED"
        else "source certificate was NOT_CHECKED at publication"
    )
    return _result("VERIFIED", f"fresh rows and material fields recompute; {source_note}")
