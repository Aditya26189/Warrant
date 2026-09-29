"""A retained linear chain prefix can replay its statistics from fresh rows."""

from __future__ import annotations

import json
import dataclasses
import subprocess
import sys
from pathlib import Path

import pytest

from controlplane.intake.chain import ChainState, seal_record
from controlplane.intake.chain_verify import verify_chain_records

ROOT = Path(__file__).resolve().parents[1]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "warrant.py"), *args], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )


@pytest.fixture(scope="module")
def certificate(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    directory = tmp_path_factory.mktemp("chain-replay-certificate")
    original = directory / "original.csv"
    original.write_bytes((ROOT / "examples" / "certifies.csv").read_bytes())
    warrant = directory / "issued.json"
    made = _run("certify", "-i", str(original), "-b", ".05", "-o", str(warrant), "-q")
    assert made.returncode == 0, made.stderr
    return original, warrant


def _linear_prefix(
    directory: Path, certificate: tuple[Path, Path], *, checked: bool = False,
) -> tuple[Path, Path, Path, Path, Path]:
    original, issued = certificate
    warrant = directory / "warrant.json"
    warrant.write_bytes(issued.read_bytes())
    first_rows = directory / "first.csv"
    first_rows.write_bytes(original.read_bytes())
    second_rows = directory / "second.csv"
    second_rows.write_text(
        original.read_text(encoding="utf-8").replace("req_", "later_"),
        encoding="utf-8",
    )
    first, second = directory / "first.json", directory / "second.json"
    guarded = ("--certificate-input", str(original)) if checked else ()
    made = _run("recheck", "-w", str(warrant), "-i", str(first_rows),
                *guarded, "--horizon-labels", "10000", "-o", str(first), "-q")
    assert made.returncode == 0, made.stderr
    made = _run("recheck", "-w", str(warrant), "-i", str(second_rows),
                *guarded, "--since", str(first), "-o", str(second), "-q")
    assert made.returncode == 0, made.stderr
    return warrant, first_rows, first, second_rows, second


def _replay(
    warrant: Path, first_rows: Path, first: Path, second_rows: Path, second: Path,
    *more: str,
) -> subprocess.CompletedProcess[str]:
    return _run("verify-chain-recheck", "-w", str(warrant),
                "--pair", str(first), str(first_rows),
                "--pair", str(second), str(second_rows), *more)


def test_complete_linear_prefix_replays_both_links(
    certificate: tuple[Path, Path], tmp_path: Path,
) -> None:
    args = _linear_prefix(tmp_path, certificate)
    result = _replay(*args)
    assert result.returncode == 0, result.stderr
    assert "VERIFIED" in result.stdout and "2" in result.stdout
    assert not (tmp_path / "chain-verification.json").exists()


def test_changed_fresh_rows_and_resealed_statistic_do_not_replay(
    certificate: tuple[Path, Path], tmp_path: Path,
) -> None:
    warrant, first_rows, first, second_rows, second = _linear_prefix(tmp_path, certificate)
    changed_rows = tmp_path / "changed.csv"
    lines = second_rows.read_text(encoding="utf-8").splitlines()
    cells = lines[1].split(",")
    cells[2] = str(float(cells[2]) + 0.01)
    lines[1] = ",".join(cells)
    changed_rows.write_text("\n".join(lines) + "\n", encoding="utf-8")
    changed = _replay(warrant, first_rows, first, changed_rows, second)
    assert changed.returncode == 1 and "MISMATCH" in changed.stdout

    payload = json.loads(second.read_text(encoding="utf-8"))
    payload["now"]["achieved_fpr"] = 0.99
    second.write_text(json.dumps(seal_record(payload)), encoding="utf-8")
    changed = _replay(warrant, first_rows, first, second_rows, second)
    assert changed.returncode == 1 and "MISMATCH" in changed.stdout


def test_missing_prefix_or_unsealed_link_is_unverified(
    certificate: tuple[Path, Path], tmp_path: Path,
) -> None:
    warrant, first_rows, first, second_rows, second = _linear_prefix(tmp_path, certificate)
    missing = _run("verify-chain-recheck", "-w", str(warrant),
                   "--pair", str(second), str(second_rows))
    assert missing.returncode == 1 and "UNVERIFIED" in missing.stdout

    payload = json.loads(first.read_text(encoding="utf-8"))
    del payload["record_sha256"]
    first.write_text(json.dumps(payload), encoding="utf-8")
    unsealed = _replay(warrant, first_rows, first, second_rows, second)
    assert unsealed.returncode == 1 and "UNVERIFIED" in unsealed.stdout


def test_checked_source_requires_original_evidence_again(
    certificate: tuple[Path, Path], tmp_path: Path,
) -> None:
    args = _linear_prefix(tmp_path, certificate, checked=True)
    missing = _replay(*args)
    assert missing.returncode == 1 and "UNVERIFIED" in missing.stdout
    replayed = _replay(*args, "--certificate-input", str(certificate[0]))
    assert replayed.returncode == 0 and "VERIFIED" in replayed.stdout


def test_rehashed_chain_statistic_still_fails_arithmetic_replay(
    certificate: tuple[Path, Path], tmp_path: Path,
) -> None:
    warrant, first_rows, first, second_rows, second = _linear_prefix(tmp_path, certificate)
    payload = json.loads(second.read_text(encoding="utf-8"))
    state = ChainState.from_payload(payload["chain"])
    changed = (state.statistics[0] + 0.01, *state.statistics[1:])
    payload["chain"] = {
        **dataclasses.replace(state, statistics=changed).to_payload(),
        "this_recheck": payload["chain"]["this_recheck"],
    }
    payload = seal_record(payload)
    assert verify_chain_records({
        "first": json.loads(first.read_text(encoding="utf-8")),
        "second": payload,
    }).clean
    second.write_text(json.dumps(payload), encoding="utf-8")
    replay = _replay(warrant, first_rows, first, second_rows, second)
    assert replay.returncode == 1 and "MISMATCH" in replay.stdout


def test_legacy_unbound_link_cannot_gain_a_verified_grade(
    certificate: tuple[Path, Path], tmp_path: Path,
) -> None:
    warrant, first_rows, first, _, _ = _linear_prefix(tmp_path, certificate)
    payload = json.loads(first.read_text(encoding="utf-8"))
    del payload["now"]["evidence_sha256"]
    first.write_text(json.dumps(seal_record(payload)), encoding="utf-8")
    result = _run("verify-chain-recheck", "-w", str(warrant),
                  "--pair", str(first), str(first_rows))
    assert result.returncode == 1 and "UNVERIFIED" in result.stdout


def test_concrete_digest_failure_is_not_hidden_by_another_unsealed_link(
    certificate: tuple[Path, Path], tmp_path: Path,
) -> None:
    warrant, first_rows, first, second_rows, second = _linear_prefix(tmp_path, certificate)
    unsealed = json.loads(first.read_text(encoding="utf-8"))
    unsealed.pop("record_sha256")
    first.write_text(json.dumps(unsealed), encoding="utf-8")
    damaged = json.loads(second.read_text(encoding="utf-8"))
    damaged["now"]["achieved_fpr"] = 0.99
    second.write_text(json.dumps(damaged), encoding="utf-8")
    result = _replay(warrant, first_rows, first, second_rows, second)
    assert result.returncode == 1 and "MISMATCH" in result.stdout


def test_presented_fork_is_unverified_by_linear_prefix_replay(
    certificate: tuple[Path, Path], tmp_path: Path,
) -> None:
    warrant, first_rows, first, second_rows, second = _linear_prefix(tmp_path, certificate)
    branch = tmp_path / "branch.json"
    made = _run("recheck", "-w", str(warrant), "-i", str(second_rows),
                "--since", str(first), "--fork", "-o", str(branch), "-q")
    assert made.returncode == 0, made.stderr
    result = _run("verify-chain-recheck", "-w", str(warrant),
                  "--pair", str(first), str(first_rows),
                  "--pair", str(second), str(second_rows),
                  "--pair", str(branch), str(second_rows))
    assert result.returncode == 1 and "UNVERIFIED" in result.stdout
