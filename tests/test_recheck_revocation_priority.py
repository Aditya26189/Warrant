"""An independent revocation survives weaker evidence and retained history (205)."""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pytest

from controlplane.cli import main
from controlplane.intake import ScoredItems, recheck_items, score_distribution
from controlplane.intake.chain import (
    ChainError, ChainState, canonical_sha256, continue_chain, feed, head_path,
    seal_record, start_chain,
)
from controlplane.intake.chain_verify import verify_chain_records
from controlplane.intake.recheck import _verdict, apply_chain, chain_units
from controlplane.model import WarrantStatus, to_jsonable


@pytest.fixture(scope="module")
def audited_case(config):
    """R3's exact counterexample, without unequal reference/current sample sizes."""
    scores = np.repeat(np.arange(.05, 1, .1), [10] * 8 + [858, 62])
    labels = np.ones(1000, dtype=int)
    labels[:94] = 0
    labels[-6:] = 0
    items = ScoredItems(
        tuple(f"audit-{i}" for i in range(len(labels))), tuple(map(int, labels)),
        tuple(map(float, scores)), None, (), "synthetic R3 regression",
    )
    reference = score_distribution(np.linspace(0, 1, 1000))
    warrant = {
        "status": "VALID", "budget_fpr": .05, "alpha": .05,
        "input": {"grouped": False}, "certification": {"threshold": .94},
        "score_distribution": to_jsonable(reference),
    }
    result = recheck_items(config, items, budget=.05, threshold=.94, reference=reference, alpha=.05)
    return items, warrant, result


def _fed(items, warrant):
    return feed(start_chain(warrant, horizon_units=100000, alpha=.05), *chain_units(items, .94))


def test_audited_fpr_warning_does_not_suppress_drift_revocation(audited_case):
    items, warrant, result = audited_case
    assert result.achieved_fpr_now == pytest.approx(.06)
    assert result.fpr_lower_bound_now < .05
    assert result.bound_still_holds is True
    assert result.drift_verdict == "REVOKED"
    assert not result.psi_driven_by_smoothing
    assert result.status is WarrantStatus.REVOKED
    fed = _fed(items, warrant)
    assert fed.state.revoked_at_unit is None
    assert apply_chain(result, fed).status is WarrantStatus.REVOKED


@pytest.mark.parametrize("bound,achieved,lower", [
    (True, .04, .02), (True, .06, .03), (False, .20, .10), (None, None, None),
])
def test_revoking_drift_outranks_every_fpr_evidence_state(config, audited_case, bound, achieved, lower):
    items, warrant, _ = audited_case
    result = _verdict(
        config, .05, .94, items, achieved, None, lower, None, None, bound,
        1.0, .03, True, True, "",
    )
    assert result.status is WarrantStatus.REVOKED
    # Aggregation must also work on old/inconsistent per-file results, without
    # depending on which early return created their top-level status.
    inconsistent = dataclasses.replace(result, status=WarrantStatus.STALE, drift_verdict="REVOKED")
    chained = apply_chain(inconsistent, _fed(items, warrant))
    assert chained.status is WarrantStatus.REVOKED
    assert "separate claim" in chained.reason


@pytest.mark.parametrize("psi,beyond,smoothed", [(0.0, False, False), (1.0, True, True)])
def test_weaker_fpr_and_drift_warnings_stay_stale(config, audited_case, psi, beyond, smoothed):
    items, _, _ = audited_case
    result = _verdict(
        config, .05, .94, items, .06, .10, .03, None, None, True,
        psi, .03, beyond, True, "", smoothed=1 if smoothed else 0,
        by_smoothing=smoothed,
    )
    assert result.status is WarrantStatus.STALE


def _legacy_parent(audited_case, *, status="STALE"):
    items, warrant, result = audited_case
    return seal_record({**result.to_payload(), "status": status, "chain": _fed(items, warrant).to_payload()})


@pytest.mark.parametrize("status", ["STALE", "VALID", "UNVALIDATED"])
def test_retained_drift_revocation_blocks_continuation_despite_aggregate_status(audited_case, status):
    _, warrant, _ = audited_case
    parent = _legacy_parent(audited_case, status=status)
    with pytest.raises(ChainError, match="REVOKED"):
        continue_chain(parent, warrant, alpha=.05)


def test_verifier_reports_a_sealed_inconsistent_parent_and_its_successor(audited_case):
    parent = _legacy_parent(audited_case)
    state = ChainState.from_payload(parent["chain"])
    successor_state = dataclasses.replace(
        state, sequence=state.sequence + 1, previous_record_sha256=canonical_sha256(parent),
        head_check="matched",
    )
    child = seal_record({
        "status": "VALID", "drift": {"verdict": "STABLE"},
        "chain": feed(successor_state, [f"later-{i}" for i in range(20)], np.zeros(20, dtype=bool)).to_payload(),
    })
    assert not verify_chain_records({"parent": parent}).clean
    report = verify_chain_records({"parent": parent, "child": child})
    assert {finding.kind for finding in report.findings} == {"revocation_status", "continued_after_end"}
    assert parent["status"] == "STALE", "verification must not rewrite retained evidence"


@pytest.mark.parametrize("remove_head", [False, True])
def test_new_cli_revocation_cannot_be_followed_by_a_valid_link(tmp_path, capsys, audited_case, remove_head):
    items, warrant, _ = audited_case
    source, record = tmp_path / "scores.csv", tmp_path / "warrant.json"
    rows = ["id,label,score"] + [
        f"{i},{y},{s}" for i, y, s in zip(items.ids, items.labels, items.scores, strict=True)
    ]
    source.write_bytes(("\n".join(rows) + "\n").encode())
    record.write_bytes(json.dumps(warrant).encode())
    parent, child = tmp_path / "first.json", tmp_path / "later.json"
    assert main(["recheck", "-w", str(record), "-i", str(source), "-o", str(parent),
                 "--horizon-labels", "100000", "--require-valid"]) == 1
    payload = json.loads(parent.read_text(encoding="utf-8"))
    assert payload["status"] == payload["drift"]["verdict"] == "REVOKED"
    assert payload["chain"]["revoked_at_unit"] is None
    assert main(["chain", "verify", str(parent), "--require-clean", "-q",
                 "-o", str(tmp_path / "verified.json")]) == 0
    if remove_head:
        head_path(record).unlink()
    # The refusal must precede any reuse-of-ID check or publication of a link.
    assert main(["recheck", "-w", str(record), "-i", str(source), "-o", str(child),
                 "--since", str(parent), "--fork", "-q"]) == 2
    assert "REVOKED" in capsys.readouterr().err
    assert not child.exists()


def test_cli_verification_rejects_a_legacy_inconsistent_record(tmp_path, audited_case):
    parent, report = tmp_path / "legacy.json", tmp_path / "verification.json"
    parent.write_bytes(json.dumps(_legacy_parent(audited_case)).encode())
    assert main(["chain", "verify", str(parent), "--require-clean", "-o", str(report), "-q"]) == 1
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert any(finding["kind"] == "revocation_status" for finding in payload["findings"])
