"""Boundary tests for release registration; these are synthetic fixtures."""

from dataclasses import asdict, replace
from datetime import datetime, timezone

import pytest

from controlplane.release.contract import (
    ReleaseContract, ReleaseSpec, read_document, register, write_document,
)


@pytest.fixture
def release_spec():
    return ReleaseSpec("support", "v1", "probe", "v2", "English QA",
                       "incorrect answer", 0.5, 0.05, 0.1, 0.05,
                       "2030-01-01T00:00:00Z", "synthetic", "iid")


@pytest.fixture
def release_now():
    return datetime(2026, 9, 14, tzinfo=timezone.utc)


def test_registration_roundtrip_freezes_identity(release_spec, release_now):
    contract = register(release_spec, ["train-1"], ["holdout-2", "holdout-1"], now=release_now)
    assert ReleaseContract.from_dict(contract.to_dict()) == contract
    assert "holdout-1" not in str(contract.to_dict())
    assert register(release_spec, ["train-1"], ["holdout-1", "holdout-2"],
                    now=release_now) == contract
    assert register(replace(release_spec, threshold=0.6), ["train-1"],
                    ["holdout-1", "holdout-2"], now=release_now) != contract


@pytest.mark.parametrize("development,holdout", [
    (["a"], ["a"]), (["a"], ["b", "b"]), ([], ["b"]), (["a"], [" b"]),
])
def test_refuse_invalid_split(release_spec, release_now, development, holdout):
    with pytest.raises(ValueError):
        register(release_spec, development, holdout, now=release_now)


@pytest.mark.parametrize("key,value", [
    ("threshold", float("nan")), ("alpha", 0), ("alpha", 1e-30),
    ("max_fpr", True), ("min_recall", 0), ("system_version", ""),
    ("expires_at", "2030-01-01"), ("data_origin", "real-ish"),
    ("sampling_assumption", "clustered"), ("typo", 0.2),
])
def test_criteria_cannot_be_silently_ignored(release_spec, key, value):
    with pytest.raises(ValueError):
        ReleaseSpec.from_dict({**asdict(release_spec), key: value})


def test_registration_cannot_begin_expired(release_spec):
    with pytest.raises(ValueError, match="expire"):
        register(release_spec, ["a"], ["b"], now=datetime(2031, 1, 1, tzinfo=timezone.utc))


def test_altered_contract_and_replacement_fail(release_spec, release_now, tmp_path):
    payload = register(release_spec, ["a"], ["b"], now=release_now).to_dict()
    path = tmp_path / "contract.json"
    write_document(path, payload)
    assert read_document(path) == payload
    with pytest.raises(FileExistsError):
        write_document(path, {"replacement": True})
    payload["spec"]["min_recall"] = 0.01
    with pytest.raises(ValueError, match="integrity"):
        ReleaseContract.from_dict(payload)


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":NaN}', '[]'])
def test_ambiguous_json_is_rejected(tmp_path, raw):
    path = tmp_path / "bad.json"
    path.write_bytes(raw.encode())
    with pytest.raises(ValueError):
        read_document(path)
