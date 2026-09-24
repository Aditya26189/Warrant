"""Publication primitives must fail before exposing partial or replaced evidence."""

from __future__ import annotations

import json

import numpy as np
import pytest

from controlplane.config import prepare_json_artifact, write_json_artifact
from controlplane.intake._atomic_files import write_json_atomic
from controlplane.intake.chain import seal_record, seal_reproduces


def test_new_record_never_replaces_an_existing_name(tmp_path):
    target = tmp_path / "record.json"
    write_json_atomic(target, {"original": True})
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        write_json_atomic(target, {"original": False})
    assert target.read_bytes() == before
    assert list(tmp_path.iterdir()) == [target]


def test_head_replacement_exposes_only_complete_json(tmp_path, monkeypatch):
    import controlplane.intake._atomic_files as module

    target = tmp_path / "head.json"
    target.write_bytes(b'{"previous": true}\n')
    original_replace = module.os.replace

    def inspect_before_replace(source, destination):
        assert json.loads(target.read_bytes()) == {"previous": True}
        assert json.loads(source.read_bytes()) == {"next": True}
        original_replace(source, destination)

    monkeypatch.setattr(module.os, "replace", inspect_before_replace)
    write_json_atomic(target, {"next": True}, replace=True)
    assert json.loads(target.read_bytes()) == {"next": True}


def test_failed_filesystem_operation_has_no_partial_record_or_fallback(tmp_path, monkeypatch):
    import controlplane.intake._atomic_files as module

    def unsupported(*args, **kwargs):
        raise OSError("hard links unsupported")

    monkeypatch.setattr(module.os, "link", unsupported)
    with pytest.raises(OSError, match="unsupported"):
        write_json_atomic(tmp_path / "record.json", {"complete": True})
    assert not list(tmp_path.iterdir())


def test_prepared_sealed_record_matches_the_existing_writer(config, tmp_path, monkeypatch):
    import controlplane.config as module

    calls = []
    def fixed_provenance(received):
        calls.append(received)
        return {"fixture": "same original provenance"}

    monkeypatch.setattr(module, "provenance", fixed_provenance)
    payload = {"number": np.float32(.25), "items": np.array([1, 2]), "flag": np.bool_(True)}
    prepared = prepare_json_artifact(payload, config, seal_with=seal_record)
    assert len(calls) == 1
    write_json_atomic(tmp_path / "transaction.json", prepared)
    assert len(calls) == 1, "publication must not refresh the record's provenance"
    write_json_artifact(tmp_path / "ordinary.json", payload, config, seal_with=seal_record)
    # The text-mode writer uses CRLF on Windows; sealing binds JSON content,
    # not whitespace. Publication uses deterministic UTF-8/LF for replay.
    assert json.loads((tmp_path / "transaction.json").read_bytes()) == json.loads(
        (tmp_path / "ordinary.json").read_bytes()
    )
    assert seal_reproduces(json.loads((tmp_path / "transaction.json").read_bytes())) is True


def test_invalid_json_never_creates_a_destination(tmp_path):
    with pytest.raises(ValueError):
        write_json_atomic(tmp_path / "record.json", {"not_finite": float("nan")})
    assert not list(tmp_path.iterdir())
