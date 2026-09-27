"""A missing seal cannot silently lower the assurance policy (decision 207)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from controlplane.cli import main
from controlplane.intake.chain import (
    ChainError, SEAL_FIELD, continue_chain, feed, seal_record, start_chain,
)
from controlplane.intake.chain_verify import render_chain_verification, verify_chain_records


WARRANT = {"status": "VALID", "budget_fpr": .05, "alpha": .05,
           "input": {"grouped": False}, "certification": {"threshold": .5},
           "score_distribution": None}


def _record():
    state = start_chain(WARRANT, horizon_units=10000, alpha=.05)
    return seal_record({"status": "VALID", "reason": "original retained result",
                        "drift": {"verdict": "STABLE"},
                        "chain": feed(state, ["original"], np.array([False])).to_payload()})


def _stripped():
    record = _record()
    del record[SEAL_FIELD]
    record["reason"] = "changed after the seal was removed"
    return record


def test_stripped_seal_cannot_satisfy_the_clean_gate():
    result = verify_chain_records({"edited.json": _stripped()})
    assert not result.clean, "removing a modern seal must not downgrade it to clean legacy input"
    assert result.structurally_clean
    assert result.integrity_status == "UNVERIFIED"
    payload = result.to_payload()
    assert payload["integrity_status"] == "UNVERIFIED"
    assert payload["structurally_clean"] is True
    assert "age" in payload["unsealed_meaning"]
    rendered = render_chain_verification(result)
    assert "UNVERIFIED" in rendered and "CLEAN --" not in rendered
    assert "written before" not in rendered
    rendered.encode("ascii")


def test_sealed_record_still_satisfies_both_assurance_checks():
    result = verify_chain_records({"retained.json": _record()})
    assert result.clean and result.structurally_clean
    assert result.integrity_status == "VERIFIED"
    assert "checksums, not signatures" in result.to_payload()["cannot_check"]


@pytest.mark.parametrize("seal", [None, "", "not-a-digest", 5, [], {}])
def test_present_but_invalid_seal_is_failed_not_legacy(seal):
    record = _record()
    record[SEAL_FIELD] = seal
    result = verify_chain_records({"invalid.json": record})
    assert not result.clean
    assert result.integrity_status == "FAILED"
    assert result.unsealed == ()
    assert any(f.kind == "digest" for f in result.findings)


def test_one_unsealed_parent_prevents_clean_history_even_with_a_sealed_child():
    parent = _stripped()
    # Construct retained legacy history without asking the modern continuation
    # API to accept missing integrity; a child cannot retroactively establish age.
    import dataclasses
    from controlplane.intake.chain import ChainState, canonical_sha256
    state = dataclasses.replace(ChainState.from_payload(parent["chain"]), sequence=2,
                                previous_record_sha256=canonical_sha256(parent))
    child = seal_record({"status": "VALID", "chain": feed(state, ["next"], np.array([False])).to_payload()})
    result = verify_chain_records({"parent": parent, "child": child})
    assert result.structurally_clean
    assert not result.clean and result.integrity_status == "UNVERIFIED"
    assert result.unsealed == ("parent",)


@pytest.mark.parametrize("fork", [False, True])
def test_an_unsealed_record_cannot_be_continued_without_a_sidecar(fork):
    with pytest.raises(ChainError, match="unsealed"):
        continue_chain(_stripped(), WARRANT, alpha=.05, fork=fork)


def test_resealing_can_still_hide_consistent_edits_without_authentication():
    record = seal_record(_stripped())
    result = verify_chain_records({"rewritten": record})
    assert result.clean
    assert "checksums, not signatures" in result.to_payload()["cannot_check"]


def test_cli_strict_gate_refuses_stripped_record_but_keeps_inspection(tmp_path, capsys):
    path = tmp_path / "stripped.json"
    path.write_bytes(json.dumps(_stripped()).encode())
    before = path.read_bytes()
    output = tmp_path / "verification.json"
    args = ["chain", "verify", str(path), "-o", str(output)]
    assert main(args) == 0
    assert "UNVERIFIED" in capsys.readouterr().out
    payload = json.loads(output.read_bytes())
    assert payload["clean"] is False and payload["integrity_status"] == "UNVERIFIED"
    assert main([*args, "--require-clean"]) == 1
    assert "unsealed" in capsys.readouterr().err
    assert path.read_bytes() == before


@pytest.mark.parametrize("fork", [False, True])
def test_cli_copied_warrant_cannot_continue_stripped_record(tmp_path, capsys, fork):
    warrant, parent, output = tmp_path / "copied-warrant.json", tmp_path / "parent.json", tmp_path / "next.json"
    warrant.write_bytes(json.dumps(WARRANT).encode())
    parent.write_bytes(json.dumps(_stripped()).encode())
    scores = tmp_path / "fresh.csv"
    rows = ["id,label,score"] + [f"fresh-{i},{int(i >= 80)},{.9 if i >= 80 else .1}" for i in range(100)]
    scores.write_bytes(("\n".join(rows) + "\n").encode())
    before = parent.read_bytes()
    args = ["recheck", "-w", str(warrant), "-i", str(scores), "--since", str(parent), "-o", str(output), "-q"]
    assert main([*args, *(["--fork"] if fork else [])]) == 2
    assert "unsealed" in capsys.readouterr().err
    assert not output.exists() and parent.read_bytes() == before
    assert not Path(str(warrant) + ".chain-head").exists()
    assert not Path(str(warrant) + ".chain-pending").exists()


def test_input_records_are_not_modified_during_inspection():
    records = {"original": _record(), "unsealed": _stripped()}
    before = copy.deepcopy(records)
    verify_chain_records(records)
    assert records == before


def test_empty_api_input_cannot_be_called_verified():
    result = verify_chain_records({})
    assert not result.clean and not result.structurally_clean
    assert result.integrity_status == "UNVERIFIED"


def test_a_failed_seal_is_not_hidden_by_other_missing_seals():
    failed = _record()
    failed["reason"] = "changed but old seal kept"
    result = verify_chain_records({"missing": _stripped(), "failed": failed})
    assert not result.clean and result.integrity_status == "FAILED"
    assert result.unsealed == ("missing",)
