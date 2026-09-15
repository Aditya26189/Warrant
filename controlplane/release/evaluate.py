"""Fixed-holdout inference with simultaneous uncertainty (DECISIONS 184).

The holdout must be an IID sample from the declared scope, unused for selection.
These conditions cannot be established from scores alone. The interval family
is fixed in advance; adding acceptance metrics requires a method-version change.
"""

from __future__ import annotations

import hashlib
import math
import platform
import subprocess
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import beta

from .. import __version__
from ..intake.contract import ScoredItems
from .contract import ReleaseContract, digest, id_hashes, timestamp, utc_time


RATE_NAMES = ("fpr", "recall", "precision", "flag_rate", "base_rate")
IDENTITY_FIELDS = ("system_id", "system_version", "detector_id", "detector_version",
                   "scope", "positive_label")
ASSUMPTIONS = (
    "IID items sampled from the declared scope; grouping is unsupported.",
    "Stable question IDs, accurate labels, and no semantic leakage are caller responsibilities.",
    "Threshold, detector and criteria were fixed without inspecting this holdout.",
    "Coverage is for one predeclared evaluation, not repeated selection across contracts.",
    "Versions and local times are declarations, not independently authenticated facts.",
    "A scoped detector measurement is not deployment approval or regulatory certification.",
)


def binomial_rate(k: int, n: int, alpha: float) -> dict:
    """Invert binomial tails for an equal-tailed Clopper-Pearson interval.

    This estimates a population proportion, not a count. With no denominator,
    the point is undefined and the interval is vacuous; never substitute zero.
    """
    if type(k) is not int or type(n) is not int or not 0 <= k <= n:
        raise ValueError("binomial counts must be integers with 0 <= k <= n")
    if not math.isfinite(alpha) or not 0 < alpha / 2 < 1 - alpha / 2 < 1:
        raise ValueError("invalid or unrepresentable interval alpha")
    lower = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    upper = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return {"kind": "ESTIMATED", "value": k / n if n else None,
            "lower": lower, "upper": upper, "n": n, "successes": k,
            "confidence": 1 - alpha, "method": "clopper_pearson_equal_tailed"}


def identity_for(contract: ReleaseContract) -> dict:
    """Require the scorer to restate identity instead of implicitly adopting it."""
    return {key: getattr(contract.spec, key) for key in IDENTITY_FIELDS}


def software_provenance() -> dict:
    """Record executed source and runtime, including an honest repository state.

    Wheels need no Git installation. Source hashes bind the implementation even
    there; repository metadata is present only when running inside this checkout.
    No customer paths, input rows or environment variables enter the record.
    """
    package = Path(__file__).resolve().parents[1]
    paths = sorted((package / "release").glob("*.py"))
    paths.extend((package / "cli.py", package / "intake" / "contract.py"))
    sources = {str(p.relative_to(package)).replace("\\", "/"):
               hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    root = package.parent
    git_commit, git_dirty = None, None
    if (root / ".git").exists():
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True,
                stderr=subprocess.DEVNULL, timeout=5).strip()
            git_dirty = bool(subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=root, text=True,
                stderr=subprocess.DEVNULL, timeout=5).strip())
        except (OSError, subprocess.SubprocessError):
            git_commit, git_dirty = None, None
    return {"warrant": __version__, "python": platform.python_version(),
            "numpy": np.__version__, "scipy": scipy.__version__,
            "source_hash": digest(sources), "source_files": sources,
            "git_commit": git_commit, "git_dirty": git_dirty,
            "randomness": "none; exact deterministic binomial calculations"}


def _validated_arrays(items: ScoredItems) -> tuple[np.ndarray, np.ndarray]:
    if items.groups is not None:
        raise ValueError("grouped input is unsupported; do not erase groups to obtain a result")
    id_hashes(items.ids)
    if items.n != len(items.labels) or items.n != len(items.scores):
        raise ValueError("IDs, labels and scores must have the same length")
    if any(type(y) not in (int, np.int64, np.int32) or y not in (0, 1) for y in items.labels):
        raise ValueError("labels must be binary integers; 1 means the detector should fire")
    if any(isinstance(s, (bool, str)) for s in items.scores):
        raise ValueError("scores must be finite numbers")
    labels, scores, _ = items.as_arrays()
    if not np.isfinite(scores).all():
        raise ValueError("scores must be finite numbers")
    return labels, scores


def evaluate(contract: ReleaseContract, items: ScoredItems, identity: dict, *,
             now: datetime | None = None) -> dict:
    """Measure a fixed operating point on exactly the registered holdout.

    Five intervals each get alpha/5; the union bound gives joint coverage at
    least 1-alpha. Lift propagates the recall/flag-rate rectangle conservatively.
    No threshold, model or criterion is selected by this function.
    """
    evaluated_at = timestamp(now)
    if utc_time(evaluated_at) < utc_time(contract.created_at):
        raise ValueError("evaluation cannot precede registration")
    if utc_time(evaluated_at) >= utc_time(contract.spec.expires_at):
        raise ValueError("contract has expired; register a new study with fresh holdout data")
    if identity != identity_for(contract):
        raise ValueError("system, detector, version, scope or positive-label identity changed")
    labels, scores = _validated_arrays(items)
    if id_hashes(items.ids) != contract.holdout_ids:
        raise ValueError("input IDs do not match the complete registered holdout")
    fired = scores >= contract.spec.threshold
    tp = int(np.sum(fired & (labels == 1)))
    fp = int(np.sum(fired & (labels == 0)))
    positives = int(np.sum(labels == 1))
    negatives = items.n - positives
    flagged = tp + fp
    counts = {"n": items.n, "positive": positives, "negative": negatives,
              "flagged": flagged, "tp": tp, "fp": fp,
              "tn": negatives - fp, "fn": positives - tp}
    denominators = ((fp, negatives), (tp, positives), (tp, flagged),
                    (flagged, items.n), (positives, items.n))
    rates = {name: binomial_rate(k, n, contract.spec.alpha / len(RATE_NAMES))
             for name, (k, n) in zip(RATE_NAMES, denominators, strict=True)}
    recall, flag = rates["recall"], rates["flag_rate"]
    lift = {"kind": "ESTIMATED", "n": items.n,
            "value": recall["value"] / flag["value"] if positives and flagged else None,
            "lower": recall["lower"] / flag["upper"],
            "upper": recall["upper"] / flag["lower"] if flag["lower"] else None,
            "confidence": 1 - contract.spec.alpha,
            "method": "simultaneous_recall_over_measured_flag_rate",
            "undefined_when_population_flag_rate_is_zero": True}
    checks = []
    for name, limit, upper_limit in (("fpr", contract.spec.max_fpr, True),
                                     ("recall", contract.spec.min_recall, False)):
        metric = rates[name]
        supported = metric["upper"] <= limit if upper_limit else metric["lower"] >= limit
        violated = (metric["value"] > limit if upper_limit else metric["value"] < limit
                    ) if metric["value"] is not None else False
        reason = ("missing_denominator" if metric["n"] == 0 else
                  "bound_cleared" if supported else
                  "observed_violation" if violated else "inconclusive_bound")
        # DECISIONS 200: tested-but-inconclusive is a refusal, not "never tested".
        # Preserve protocol 1 exactly so retained registrations still reproduce.
        verdict = ("VALID" if reason == "bound_cleared" else "REFUSED")
        if contract.schema_version == 1 and reason in ("missing_denominator", "inconclusive_bound"):
            verdict = "UNVALIDATED"
        check = {"metric": name, "limit": limit,
                 "direction": "at_most" if upper_limit else "at_least", "status": verdict}
        if contract.schema_version >= 2:
            check["reason"] = reason
        checks.append(check)
    statuses = {check["status"] for check in checks}
    status = ("REFUSED" if "REFUSED" in statuses else
              "UNVALIDATED" if "UNVALIDATED" in statuses else "VALID")
    semantic_rows = sorted((digest({"item_id": i}), int(y), float(s))
                           for i, y, s in zip(items.ids, labels, scores, strict=True))
    return {"schema_version": contract.schema_version, "kind": "warrant.release.evaluation",
            "contract_id": contract.to_dict()["contract_id"],
            "evaluated_at": evaluated_at, "expires_at": contract.spec.expires_at,
            "identity": identity_for(contract), "data_origin": contract.spec.data_origin,
            "data_sha256": digest(semantic_rows), "status": status,
            "counts": counts, "rates": rates, "lift": lift, "checks": checks,
            "family_confidence": 1 - contract.spec.alpha,
            "specification_sha256": digest(asdict(contract.spec)),
            "assumptions": list(ASSUMPTIONS)}


def seal_evaluation(measurement: dict) -> dict:
    """Attach implementation provenance before calculating the evidence digest."""
    body = {**measurement, "software": software_provenance()}
    return {**body, "evidence_id": digest(body)}


def verify_evaluation(record: dict, contract: ReleaseContract, items: ScoredItems,
                      identity: dict, *, now: datetime | None = None) -> str:
    """Recompute decisions from bound input; return current status with expiry.

    Rehashing a fabricated metric is insufficient: every measurement field must
    reproduce. This does not authenticate the record's author or software claim.
    """
    body = {k: v for k, v in record.items() if k != "evidence_id"}
    if "software" not in body or record.get("evidence_id") != digest(body):
        raise ValueError("evaluation integrity check failed")
    measured_at = utc_time(record.get("evaluated_at"))
    checked_at = utc_time(timestamp(now))
    if measured_at > checked_at:
        raise ValueError("evaluation claims a future timestamp")
    expected = evaluate(contract, items, identity, now=measured_at)
    actual = {k: v for k, v in body.items() if k != "software"}
    if digest(expected) != digest(actual):
        raise ValueError("evaluation does not reproduce from this contract and scored input")
    return "STALE" if checked_at >= utc_time(contract.spec.expires_at) else record["status"]
