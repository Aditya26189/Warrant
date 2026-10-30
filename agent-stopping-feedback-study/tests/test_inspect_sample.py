"""Synthetic schema fixtures only; no executor performance is simulated."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("inspect_sample", Path(__file__).parents[1] / "inspect_sample.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def example(outcome: int | None = 0) -> dict:
    return {"row_idx": 0, "truncated_cells": [], "row": {
        "resolved": outcome, "instance_id": "fixture-issue", "trajectory_id": "fixture-run",
        "messages": [{"role": "assistant", "content": "fixture", "tool_calls": []}],
        "metadata": {"teacher_model": {"name": "fixture"}, "reference_patch": {"patch": "GOLD"}},
        "model_patch": "FINAL"}}


def test_missing_label_is_not_recorded_zero() -> None:
    assert module.row_summary(example(-1), "fixture")["label_available"] is False
    assert module.row_summary(example(0), "fixture")["label_available"] is True
    with pytest.raises(ValueError):
        module.row_summary(example(None), "fixture")


def test_truncated_cell_cannot_support_schema_conclusion() -> None:
    item = example()
    item["truncated_cells"] = ["messages"]
    with pytest.raises(ValueError, match="truncated"):
        module.row_summary(item, "fixture")


def test_final_outcome_fields_are_not_prefix_features_or_retained_text() -> None:
    result = module.row_summary(example(), "fixture")
    assert "metadata.reference_patch" in result["excluded_from_any_future_prefix_features"]
    assert "resolved" in result["excluded_from_any_future_prefix_features"]
    assert "GOLD" not in json.dumps(result) and "FINAL" not in json.dumps(result)


def test_accounting_fields_are_structured_not_words_in_messages() -> None:
    assert module.accounting_paths({"content": "total_tokens=99"}) == []
    assert module.accounting_paths({"usage": {"input_tokens": 12}}) == ["/usage", "/usage/input_tokens"]


def test_corrupted_source_hash_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "response.json"
    path.write_bytes(json.dumps({"partial": False, "rows": [example()]}).encode())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert module.inspect_payload(path, "fixture", digest)["rows"][0]["recorded_resolved"] == 0
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash mismatch"):
        module.inspect_payload(path, "fixture", digest)
