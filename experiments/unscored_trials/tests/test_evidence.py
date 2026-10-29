"""Defend offline replay and honest, source-bound pending audit worksheets."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from experiments.unscored_trials import analyze, audit, inventory, reproduce
from experiments.unscored_trials.tests.test_analysis import fixture


def setup_analysis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple:
    """Keep fixture evidence explicitly synthetic while exercising file contracts."""
    provenance = {"dirty": False, "git_commit": "synthetic_fixture_not_empirical"}
    monkeypatch.setattr(inventory, "clean_provenance", lambda: provenance)
    data, config, spec, output = fixture(tmp_path)
    analyze.run_analysis(data, config, spec, output, provenance=provenance, progress=False)
    return data, config, spec, output


def test_replay_compares_all_canonical_files_with_network_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data, config, spec, output = setup_analysis(tmp_path, monkeypatch)
    receipt = reproduce.replay(data, config, spec, output, tmp_path / "replay", tmp_path / "validation.json")
    assert receipt["match"] and receipt["networking_disabled"]
    assert not receipt["differences"]


def test_changed_reference_is_reported_in_retained_replay_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data, config, spec, output = setup_analysis(tmp_path, monkeypatch)
    path = output / "summary.json"
    value = json.loads(path.read_bytes())
    value["submission_count"] += 1
    path.write_text(json.dumps(value))
    validation = tmp_path / "failed-validation.json"
    with pytest.raises(ValueError, match="offline replay differs"):
        reproduce.replay(data, config, spec, output, tmp_path / "replay", validation)
    assert "summary.json" in json.loads(validation.read_bytes())["differences"]


def test_replay_rejects_overlapping_destinations_before_analysis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data, config, spec, output = setup_analysis(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="disjoint"):
        reproduce.replay(data, config, spec, output, output / "nested", tmp_path / "validation.json")


def test_replay_guard_prevents_an_actual_socket_attempt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data, config, spec, output = setup_analysis(tmp_path, monkeypatch)
    monkeypatch.setattr(analyze, "run_analysis", lambda *args, **kwargs: socket.socket())
    with pytest.raises(RuntimeError, match="forbids networking"):
        reproduce.replay(data, config, spec, output, tmp_path / "replay", tmp_path / "validation.json")


def test_worksheet_keeps_unavailable_categories_and_human_review_pending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, _, _, output = setup_analysis(tmp_path, monkeypatch)
    target = tmp_path / "audit"
    receipt = audit.build(output, target)
    rows = audit.read_csv(target / "human_audit_worksheet.csv")
    assert receipt["human_review_completed"] is False
    assert len(rows) == 6 and all(row["human_review_status"] == "PENDING" for row in rows)
    assert any(row["case_status"] == "NOT_AVAILABLE" for row in rows)
    assert all(row["independent_adjudication"] == "False" for row in rows)


def test_audit_rejects_a_corrupted_execution_shard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, _, _, output = setup_analysis(tmp_path, monkeypatch)
    index = audit.read_csv(output / "executions.csv")
    path = output / index[0]["path"]
    path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="differs from canonical index"):
        audit.build(output, tmp_path / "audit")
