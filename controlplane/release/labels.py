"""Descriptive primary-label stress test at a registered release threshold (216)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np

from ..intake.certify import evidence_sha256
from ..intake.contract import ScoredItems
from .contract import ReleaseContract, digest, timestamp, utc_time
from .evaluate import (
    RATE_NAMES, binomial_rate, software_provenance, verify_evaluation,
)


def _corrected_counts(counts: dict[str, int], kind: str, errors: int) -> tuple[int, int, int, int]:
    """Correct only one adverse label direction; scores and threshold stay fixed."""
    fp, negative = counts["fp"], counts["negative"]
    tp, positive = counts["tp"], counts["positive"]
    if kind == "flagged_positive_really_clean":
        return fp + errors, negative + errors, tp - errors, positive - errors
    if kind == "unflagged_negative_really_positive":
        return fp, negative - errors, tp, positive + errors
    raise ValueError(f"unknown label-error direction: {kind}")


def _bounds(contract: ReleaseContract, counts: dict[str, int], kind: str, errors: int) -> dict[str, Any]:
    fp, negative, tp, positive = _corrected_counts(counts, kind, errors)
    per_metric_alpha = contract.spec.alpha / len(RATE_NAMES)
    fpr = binomial_rate(fp, negative, per_metric_alpha)
    recall = binomial_rate(tp, positive, per_metric_alpha)
    fpr_clears = negative > 0 and fpr["upper"] <= contract.spec.max_fpr
    recall_clears = positive > 0 and recall["lower"] >= contract.spec.min_recall
    return {"fpr_upper": fpr["upper"], "recall_lower": recall["lower"],
            "fpr_clears": fpr_clears, "recall_clears": recall_clears,
            "release_criteria_hold": fpr_clears and recall_clears}


def _first_failure(contract: ReleaseContract, counts: dict[str, int], kind: str,
                   pool: int) -> int | None:
    """Binary-search the first failure; each correction weakens both bounds."""
    if pool == 0 or _bounds(contract, counts, kind, pool)["release_criteria_hold"]:
        return None
    low, high = 1, pool
    while low < high:
        middle = (low + high) // 2
        if _bounds(contract, counts, kind, middle)["release_criteria_hold"]:
            low = middle + 1
        else:
            high = middle
    return low


def _sensitivity(contract: ReleaseContract, evaluation: dict[str, Any]) -> dict[str, Any]:
    if evaluation["status"] != "VALID":
        return {"computed": False, "reason": "not computed for a non-VALID release; no label-edit recipe to approve a refusal"}
    counts = evaluation["counts"]
    directions = (
        ("flagged_positive_really_clean", counts["tp"]),
        ("unflagged_negative_really_positive", counts["tn"]),
    )
    result: dict[str, Any] = {
        "computed": True,
        "method": "fixed_threshold_separate_label_corrections_clopper_pearson",
        "threshold": contract.spec.threshold,
        "alpha_per_metric": contract.spec.alpha / len(RATE_NAMES),
        "meaning": (
            "First count of one specified primary-label error that makes at least one "
            "registered bound fail. Directions are separate, not a combined-error bound; "
            "a disagreement is not proof of an error."
        ),
    }
    for kind, pool in directions:
        result[kind] = {
            "pool_size": pool,
            "if_one": _bounds(contract, counts, kind, 1) if pool else None,
            "first_invalidating_count": _first_failure(contract, counts, kind, pool),
        }
    return result


def _second_review(items: ScoredItems, threshold: float) -> dict[str, Any]:
    if items.second_labels is None:
        return {"available": False}
    labels = np.asarray(items.labels)
    scores = np.asarray(items.scores)
    fired = scores >= threshold
    pools = {
        "flagged_positive_really_clean": (fired & (labels == 1), 0),
        "unflagged_negative_really_positive": (~fired & (labels == 0), 1),
    }
    result: dict[str, Any] = {
        "available": True,
        "meaning": "Observed second-review disagreements in two adverse pools only; no truth or population-error inference.",
    }
    for kind, (mask, adverse_label) in pools.items():
        reviewed = 0
        disputed = 0
        for in_pool, second in zip(mask, items.second_labels, strict=True):
            if in_pool and second is not None:
                reviewed += 1
                disputed += int(second == adverse_label)
        result[kind] = {"reviewed": reviewed, "disputed": disputed}
    return result


def label_audit(contract: ReleaseContract, evaluation: dict[str, Any], items: ScoredItems,
                identity: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Replay a release first, then describe exact fixed-threshold label fragility."""
    audited_at = timestamp(now)
    release_status = verify_evaluation(evaluation, contract, items, identity, now=utc_time(audited_at))
    return {
        "schema_version": 1,
        "kind": "warrant.release.label_audit",
        "contract_id": contract.to_dict()["contract_id"],
        "evaluated_evidence_id": evaluation["evidence_id"],
        "primary_data_sha256": evaluation["data_sha256"],
        "effective_rows_sha256": evidence_sha256(items),
        "audited_at": audited_at,
        "release_status_at_audit": release_status,
        "sensitivity": _sensitivity(contract, evaluation),
        "second_review": _second_review(items, contract.spec.threshold),
        "assumptions": [
            "The primary labels and fixed detector scores are supplied by the caller; neither is independently authenticated.",
            "The two adverse relabelling directions are evaluated separately; their joint effect is not bounded here.",
            "Second-review disagreements do not establish which reviewer is correct or how pairs were selected.",
            "This audit describes the retained release and never changes its verdict or expiry.",
        ],
    }


def seal_label_audit(body: dict[str, Any]) -> dict[str, Any]:
    """Add source provenance and a checksum, without claiming a signature."""
    payload = {**body, "software": software_provenance()}
    return {**payload, "audit_id": digest(payload)}


def verify_label_audit(record: dict[str, Any], contract: ReleaseContract,
                       evaluation: dict[str, Any], items: ScoredItems,
                       identity: dict[str, Any], *, now: datetime | None = None) -> str:
    """Require every material field to reproduce from retained release inputs."""
    body = {key: value for key, value in record.items() if key != "audit_id"}
    if "software" not in body or record.get("audit_id") != digest(body):
        raise ValueError("label-audit integrity check failed")
    audited_at = utc_time(record.get("audited_at"))
    if audited_at > utc_time(timestamp(now)):
        raise ValueError("label audit claims a future timestamp")
    expected = label_audit(contract, evaluation, items, identity, now=audited_at)
    actual = {key: value for key, value in body.items() if key != "software"}
    if digest(expected) != digest(actual):
        raise ValueError("label audit does not reproduce from this release and scored input")
    return verify_evaluation(evaluation, contract, items, identity, now=now)
