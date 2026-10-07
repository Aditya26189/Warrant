"""Real CLI and fault-boundary tests for the certify handoff (Decision 236)."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from controlplane.intake import handoff
from controlplane.intake.contract import InputError
from controlplane.intake.prepare import prepare_export, verify_prepared


ROOT = Path(__file__).resolve().parents[1]


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "warrant.py"), *args], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", timeout=300,
    )


@pytest.fixture(scope="module")
def refused_inputs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    directory = tmp_path_factory.mktemp("handoff-refusal")
    source = directory / "source.csv"
    mapping = directory / "mapping.json"
    source.write_bytes((ROOT / "examples" / "export_sample.csv").read_bytes())
    mapping.write_bytes((ROOT / "examples" / "export_mapping.json").read_bytes())
    prepared = prepare_export(source, mapping, directory / "prepared")
    warrant = directory / "refused.json"
    result = _cli("certify", "--input", str(prepared / "scored.csv"),
                  "--budget", "0.05", "--out", str(warrant), "--quiet")
    assert result.returncode == 0, result.stderr
    assert json.loads(warrant.read_text(encoding="utf-8"))["status"] == "REFUSED"
    return {"source": source, "mapping": mapping, "prepared": prepared,
            "warrant": warrant}


@pytest.fixture(scope="module")
def valid_inputs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    directory = tmp_path_factory.mktemp("handoff-valid")
    source = directory / "source.csv"
    mapping = directory / "mapping.json"
    source.write_bytes((ROOT / "examples" / "export_certifies.csv").read_bytes())
    mapping.write_bytes((ROOT / "examples" / "export_certifies_mapping.json").read_bytes())
    prepared = prepare_export(source, mapping, directory / "prepared")
    warrant = directory / "valid.json"
    result = _cli("certify", "--input", str(prepared / "scored.csv"),
                  "--budget", "0.05", "--out", str(warrant), "--quiet")
    assert result.returncode == 0, result.stderr
    assert json.loads(warrant.read_text(encoding="utf-8"))["status"] == "VALID"
    return {"source": source, "mapping": mapping, "prepared": prepared,
            "warrant": warrant}


def _create(inputs: dict[str, Path], out: Path, *, opt_in: bool = True,
            frontier: Path | None = None) -> subprocess.CompletedProcess[str]:
    args = ["handoff", "create", "--input", str(inputs["source"]),
            "--mapping", str(inputs["mapping"]), "--prepared", str(inputs["prepared"]),
            "--warrant", str(inputs["warrant"]), "--out", str(out)]
    if frontier is not None:
        args += ["--frontier", str(frontier)]
    if opt_in:
        args.append("--include-sensitive-input")
    return _cli(*args)


@pytest.fixture
def refused_packet(refused_inputs: dict[str, Path], tmp_path: Path) -> Path:
    out = tmp_path / "packet"
    result = _create(refused_inputs, out)
    assert result.returncode == 0, result.stderr
    return out


def test_valid_packet_replays_and_preserves_original_source(
    valid_inputs: dict[str, Path], tmp_path: Path,
) -> None:
    out = tmp_path / "packet"
    created = _create(valid_inputs, out)
    assert created.returncode == 0, created.stderr
    assert "HANDOFF" in created.stdout
    assert (out / "source.csv").read_bytes() == valid_inputs["source"].read_bytes()
    assert "captured_at" in (out / "source.csv").read_text(encoding="utf-8")
    assert not (out / "prepared" / "scored.csv").read_text(
        encoding="utf-8",
    ).startswith("item,review,risk")
    checked = _cli("handoff", "verify", "--packet", str(out))
    assert checked.returncode == 0, checked.stderr
    assert checked.stdout.startswith("VERIFIED:")
    manifest = json.loads((out / "handoff.json").read_text(encoding="utf-8"))
    assert manifest["workflow"] == "prepare+certify"
    assert manifest["members"]["source.csv"]["role"] == "source_export"


def test_refused_certificate_is_replayed_as_refused_evidence(refused_packet: Path) -> None:
    assert json.loads((refused_packet / "warrant.json").read_text(
        encoding="utf-8",
    ))["status"] == "REFUSED"
    checked = _cli("handoff", "verify", "--packet", str(refused_packet))
    assert checked.returncode == 0, checked.stderr
    assert "VERIFIED" in checked.stdout


def test_copy_requires_explicit_sensitive_input_opt_in(
    refused_inputs: dict[str, Path], tmp_path: Path,
) -> None:
    out = tmp_path / "packet"
    result = _create(refused_inputs, out, opt_in=False)
    assert result.returncode == 2
    assert "--include-sensitive-input" in result.stderr
    assert not out.exists()


@pytest.mark.parametrize("name", ["source.csv", "mapping.json", "prepared/scored.csv",
                                  "prepared/manifest.json", "warrant.json"])
def test_changed_member_bytes_are_mismatches(
    refused_packet: Path, name: str,
) -> None:
    member = refused_packet / name
    member.write_bytes(member.read_bytes() + b"\n")
    result = _cli("handoff", "verify", "--packet", str(refused_packet))
    assert result.returncode == 1, result.stderr
    assert f"MISMATCH: member bytes changed: {name}" in result.stdout


def test_matching_packet_digests_cannot_override_semantic_replay(
    refused_packet: Path,
) -> None:
    warrant = refused_packet / "warrant.json"
    record = json.loads(warrant.read_text(encoding="utf-8"))
    del record["input"]["evidence_sha256"]
    warrant.write_text(json.dumps(record), encoding="utf-8")
    marker = refused_packet / "handoff.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    manifest["members"]["warrant.json"]["sha256"] = hashlib.sha256(
        warrant.read_bytes(),
    ).hexdigest()
    marker.write_text(json.dumps(manifest), encoding="utf-8")
    result = _cli("handoff", "verify", "--packet", str(refused_packet))
    assert result.returncode == 1, result.stderr
    assert "UNVERIFIED" in result.stdout


def test_matching_source_digest_cannot_override_preparation_replay(
    refused_packet: Path,
) -> None:
    source = refused_packet / "source.csv"
    source.write_bytes(source.read_bytes().replace(
        b"synthetic example only", b"changed example only", 1,
    ))
    marker = refused_packet / "handoff.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    manifest["members"]["source.csv"]["sha256"] = hashlib.sha256(
        source.read_bytes(),
    ).hexdigest()
    marker.write_text(json.dumps(manifest), encoding="utf-8")
    result = _cli("handoff", "verify", "--packet", str(refused_packet))
    assert result.returncode == 1, result.stderr
    assert "MISMATCH: source, mapping and prepared rows differ" in result.stdout


def test_missing_and_extra_members_fail_closed(
    refused_packet: Path, tmp_path: Path,
) -> None:
    missing = tmp_path / "missing"
    shutil.copytree(refused_packet, missing)
    (missing / "mapping.json").unlink()
    assert _cli("handoff", "verify", "--packet", str(missing)).returncode == 2

    extra = tmp_path / "extra"
    shutil.copytree(refused_packet, extra)
    (extra / "private.txt").write_text("unexpected", encoding="utf-8")
    assert _cli("handoff", "verify", "--packet", str(extra)).returncode == 2


def test_member_symlink_is_rejected(
    refused_packet: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:

    linked = tmp_path / "linked"
    shutil.copytree(refused_packet, linked)
    (linked / "mapping.json").unlink()
    try:
        (linked / "mapping.json").symlink_to(refused_packet / "mapping.json")
    except (OSError, NotImplementedError):
        # Windows without symlink privilege still exercises the guard itself.
        shutil.copyfile(refused_packet / "mapping.json", linked / "mapping.json")
        real_is_symlink = Path.is_symlink
        monkeypatch.setattr(Path, "is_symlink", lambda path: (
            path == linked / "mapping.json" or real_is_symlink(path)
        ))
        with pytest.raises(InputError, match="regular file"):
            handoff.verify_handoff(linked)
    else:
        assert _cli("handoff", "verify", "--packet", str(linked)).returncode == 2


@pytest.mark.parametrize("change", [
    lambda record: record.update(source_name=[]),
    lambda record: record["members"].update({"../escape": {"role": "x", "sha256": "0" * 64}}),
    lambda record: record["members"]["source.csv"].update(sha256="bad"),
])
def test_malformed_manifest_never_replays(
    refused_packet: Path, change,
) -> None:
    marker = refused_packet / "handoff.json"
    record = json.loads(marker.read_text(encoding="utf-8"))
    change(record)
    marker.write_text(json.dumps(record), encoding="utf-8")
    result = _cli("handoff", "verify", "--packet", str(refused_packet))
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_existing_destination_is_untouched(
    refused_inputs: dict[str, Path], tmp_path: Path,
) -> None:
    out = tmp_path / "packet"
    out.mkdir()
    keep = out / "keep.txt"
    keep.write_text("owned", encoding="utf-8")
    result = _create(refused_inputs, out)
    assert result.returncode == 2
    assert keep.read_text(encoding="utf-8") == "owned"


@pytest.mark.parametrize("alias", [False, True])
def test_nested_destination_preserves_prepared_evidence(
    refused_inputs: dict[str, Path], tmp_path: Path, alias: bool,
) -> None:
    source = tmp_path / "source.csv"
    source.write_bytes(refused_inputs["source"].read_bytes())
    prepared = prepare_export(source, refused_inputs["mapping"], tmp_path / "prepared")
    before = {name: (prepared / name).read_bytes()
              for name in ("scored.csv", "manifest.json")}
    out = prepared / ("../prepared/packet" if alias else "packet")
    with pytest.raises(InputError, match="outside the prepared directory"):
        handoff.create_handoff(
            source, refused_inputs["mapping"], prepared, refused_inputs["warrant"],
            out, include_sensitive_input=True,
        )
    assert not out.exists()
    assert {member.name for member in prepared.iterdir()} == set(before)
    assert {name: (prepared / name).read_bytes() for name in before} == before
    assert verify_prepared(source, refused_inputs["mapping"], prepared)


def test_nested_destination_cli_is_an_input_error_without_side_effects(
    refused_inputs: dict[str, Path], tmp_path: Path,
) -> None:
    source = tmp_path / "source.csv"
    source.write_bytes(refused_inputs["source"].read_bytes())
    prepared = prepare_export(source, refused_inputs["mapping"], tmp_path / "prepared")
    inputs = dict(refused_inputs, source=source, prepared=prepared)
    out = prepared / "packet"
    result = _create(inputs, out)
    assert result.returncode == 2, result.stderr
    assert "outside the prepared directory" in result.stderr
    assert not out.exists()
    assert verify_prepared(source, refused_inputs["mapping"], prepared)


def test_source_change_during_copy_leaves_no_completion_marker(
    refused_inputs: dict[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.csv"
    source.write_bytes(refused_inputs["source"].read_bytes())
    prepared = prepare_export(source, refused_inputs["mapping"], tmp_path / "prepared")
    out = tmp_path / "packet"
    original_copy = handoff._copy

    def mutate_then_copy(path: Path, target: Path) -> None:
        if path == source:
            path.write_bytes(path.read_bytes().replace(
                b"synthetic example only", b"changed example only", 1,
            ))
        original_copy(path, target)

    monkeypatch.setattr(handoff, "_copy", mutate_then_copy)
    with pytest.raises(InputError, match="copied evidence MISMATCH"):
        handoff.create_handoff(source, refused_inputs["mapping"], prepared,
                               refused_inputs["warrant"], out,
                               include_sensitive_input=True)
    assert out.is_dir()
    assert not (out / "handoff.json").exists()
    with pytest.raises(InputError):
        handoff.verify_handoff(out)


def test_frontier_selected_certificate_needs_its_record(
    valid_inputs: dict[str, Path], tmp_path: Path,
) -> None:
    frontier = tmp_path / "frontier.json"
    scored = valid_inputs["prepared"] / "scored.csv"
    made = _cli("certify", "--input", str(scored), "--frontier", "--out",
                str(frontier), "--quiet")
    assert made.returncode == 0, made.stderr
    selected = tmp_path / "selected.json"
    certified = _cli("certify", "--input", str(scored), "--budget", "0.05",
                     "--from-frontier", str(frontier), "--out", str(selected),
                     "--quiet")
    assert certified.returncode == 0, certified.stderr
    selected_inputs = dict(valid_inputs, warrant=selected)
    omitted = _create(selected_inputs, tmp_path / "omitted")
    assert omitted.returncode == 2
    assert not (tmp_path / "omitted").exists()
    out = tmp_path / "packet"
    created = _create(selected_inputs, out, frontier=frontier)
    assert created.returncode == 0, created.stderr
    assert _cli("handoff", "verify", "--packet", str(out)).returncode == 0
    (out / "frontier.json").write_bytes(frontier.read_bytes() + b"\n")
    changed = _cli("handoff", "verify", "--packet", str(out))
    assert changed.returncode == 1
    assert "MISMATCH" in changed.stdout
