"""Export boundaries that could otherwise silently change evaluation meaning."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from controlplane.intake.contract import InputError, load_scored_items
from controlplane.intake.prepare import prepare_export, verify_prepared
from controlplane.cli import main


def inputs(tmp_path, *, grouped=False, second=False, direction="higher"):
    columns = {"id": "item", "label": "review", "score": "risk"}
    if grouped:
        columns["group"] = "conversation"
    if second:
        columns["label_2"] = "review2"
    mapping = tmp_path / "mapping.json"
    mapping.write_text(json.dumps({
        "schema_version": 1, "columns": columns,
        "positive_label": "bad", "negative_label": "good",
        "score_direction": direction, "independent_rows": not grouped,
    }), encoding="utf-8")
    rows = [
        {"item": "001", "review": "good", "risk": 0.2,
         "conversation": "c1", "review2": "", "prompt": "private text"},
        {"item": "002", "review": "bad", "risk": 0.9,
         "conversation": "c1", "review2": "good", "prompt": "private text"},
    ]
    source = tmp_path / "export.jsonl"
    source.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    return source, mapping


def change_mapping(path, **changes):
    record = json.loads(path.read_text(encoding="utf-8"))
    record.update(changes)
    path.write_text(json.dumps(record), encoding="utf-8")


def test_preserves_groups_labels_order_and_excludes_private_values(tmp_path):
    source, mapping = inputs(tmp_path, grouped=True, second=True)
    out = prepare_export(source, mapping, tmp_path / "prepared")
    items = load_scored_items(out / "scored.csv")
    assert items.ids == ("001", "002")
    assert items.labels == (0, 1)
    assert items.groups == ("c1", "c1")
    assert items.second_labels == (None, 0)
    manifest = json.loads((out / "manifest.json").read_bytes())
    assert manifest["counts"] == {
        "rows": 2, "positive": 1, "negative": 1, "groups": 1, "second_reviews": 1,
    }
    assert manifest["excluded_columns"] == ["prompt"]
    assert all(b"private text" not in p.read_bytes() for p in out.iterdir())
    assert verify_prepared(source, mapping, out)


def test_lower_direction_negates_without_probability_assumption(tmp_path):
    source, mapping = inputs(tmp_path, direction="lower")
    source.write_text('{"item":"a","review":"good","risk":-8}\n'
                      '{"item":"b","review":"bad","risk":12}', encoding="utf-8")
    out = prepare_export(source, mapping, tmp_path / "prepared")
    assert load_scored_items(out / "scored.csv").scores == (8.0, -12.0)


def test_csv_bom_quoted_values_and_determinism(tmp_path):
    _, mapping = inputs(tmp_path)
    source = tmp_path / "export.csv"
    source.write_bytes(b'\xef\xbb\xbfitem,review,risk\n"a,b",good,0.2\nc,bad,0.9\n')
    first = prepare_export(source, mapping, tmp_path / "first")
    second = prepare_export(source, mapping, tmp_path / "second")
    assert load_scored_items(first / "scored.csv").ids == ("a,b", "c")
    for name in ("scored.csv", "manifest.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


@pytest.mark.parametrize("format", ["csv", "jsonl", "ndjson"])
def test_preparation_never_writes_an_intermediate_plaintext_copy(
    tmp_path, monkeypatch, format,
):
    source, mapping = inputs(tmp_path)
    if format == "csv":
        source = tmp_path / "export.csv"
        source.write_bytes(
            b"\xef\xbb\xbfitem,review,risk,prompt\r\n"
            b"001,good,0.2,private text\r\n"
            b"002,bad,0.9,private text\r\n"
        )
    elif format == "ndjson":
        source = tmp_path / "export.ndjson"
        source.write_bytes((tmp_path / "export.jsonl").read_bytes())

    def refuse_temporary_copy(*args, **kwargs):
        raise AssertionError("preparation wrote an intermediate plaintext copy")

    monkeypatch.setattr(tempfile, "TemporaryDirectory", refuse_temporary_copy)
    package = prepare_export(source, mapping, tmp_path / "prepared")
    assert (package / "scored.csv").read_bytes() == (
        b"id,label,score\n001,0,0.2\n002,1,0.9\n"
    )
    assert b"private text" not in (package / "manifest.json").read_bytes()
    assert verify_prepared(source, mapping, package)


@pytest.mark.parametrize("field,value", [
    ("schema_version", True), ("schema_version", 2),
    ("independent_rows", "true"), ("independent_rows", False),
    ("score_direction", "guess"), ("score_direction", {}),
    ("positive_label", "good"), ("positive_label", True),
    ("negative_label", " good"), ("columns", []),
    ("columns", {"id": "item", "label": "review", "score": "review"}),
    ("unknown", "ignored"),
])
def test_mapping_rejected_without_output(tmp_path, field, value):
    source, mapping = inputs(tmp_path)
    change_mapping(mapping, **{field: value})
    with pytest.raises(InputError):
        prepare_export(source, mapping, tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("content", [
    'item,review,risk\na,good,nan\nb,bad,0.9\n',
    'item,review,risk\na,good,inf\nb,bad,0.9\n',
    'item,review,risk\na,good,0.1\na,bad,0.9\n',
    'item,review,risk\na,unknown,0.1\nb,bad,0.9\n',
    'item,review,risk,risk\na,good,0.1,0.8\n',
    'item,review,risk\na,good,0.1,unexpected\n',
    'item,review,risk\na,good\n',
    'item,review,risk\n',
    'item,review,risk,group\na,good,0.1,c1\nb,bad,0.9,c1\n',
    'item,review,risk,label_2\na,good,0.1,good\nb,bad,0.9,good\n',
])
def test_csv_ambiguity_and_silent_loss_rejected(tmp_path, content):
    _, mapping = inputs(tmp_path)
    source = tmp_path / "bad.csv"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(InputError):
        prepare_export(source, mapping, tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("content", [
    '{"item":"a","review":"good","risk":0.1,"risk":0.9}',
    '{"item":{},"review":"good","risk":0.1}',
    '{"item":"a","review":true,"risk":0.1}',
    '{"item":"a","review":"good","risk":true}',
    '{"item":"a","review":"good"}',
    '[]', 'not JSON',
])
def test_json_ambiguity_rejected(tmp_path, content):
    source, mapping = inputs(tmp_path)
    source.write_text(content, encoding="utf-8")
    with pytest.raises(InputError):
        prepare_export(source, mapping, tmp_path / "out")


def test_huge_json_integer_score_is_refused_without_output(tmp_path, capsys):
    source, mapping = inputs(tmp_path)
    source.write_text(json.dumps({
        "item": "a", "review": "good", "risk": 10 ** 400,
    }), encoding="utf-8")
    out = tmp_path / "out"
    assert main(["prepare", "--input", str(source), "--mapping", str(mapping),
                 "--out", str(out)]) == 2
    assert "row 1" in capsys.readouterr().err
    assert not out.exists()


def test_grouped_mapping_requires_complete_groups(tmp_path):
    source, mapping = inputs(tmp_path, grouped=True)
    source.write_text('{"item":"a","review":"good","risk":0.1,'
                      '"conversation":""}', encoding="utf-8")
    with pytest.raises(InputError):
        prepare_export(source, mapping, tmp_path / "out")


def test_single_class_is_preparable_but_not_implicitly_certified(tmp_path):
    source, mapping = inputs(tmp_path)
    source.write_text('{"item":"a","review":"good","risk":0.1}', encoding="utf-8")
    out = prepare_export(source, mapping, tmp_path / "out")
    assert verify_prepared(source, mapping, out)
    with pytest.raises(InputError, match="one class"):
        load_scored_items(out / "scored.csv")


@pytest.mark.parametrize("changed", ["source", "mapping", "scored.csv", "manifest.json"])
def test_replay_detects_each_changed_component(tmp_path, changed):
    source, mapping = inputs(tmp_path)
    out = prepare_export(source, mapping, tmp_path / "out")
    target = {"source": source, "mapping": mapping}.get(changed, out / changed)
    target.write_bytes(target.read_bytes() + b"\n")
    assert not verify_prepared(source, mapping, out)


def test_incomplete_extra_and_existing_destinations(tmp_path):
    source, mapping = inputs(tmp_path)
    out = prepare_export(source, mapping, tmp_path / "out")
    original = (out / "scored.csv").read_bytes()
    with pytest.raises(FileExistsError):
        prepare_export(source, mapping, out)
    assert (out / "scored.csv").read_bytes() == original
    (out / "extra").write_text("unexpected")
    with pytest.raises(InputError, match="unexpected"):
        verify_prepared(source, mapping, out)
    (out / "extra").unlink()
    (out / "manifest.json").unlink()
    with pytest.raises(InputError, match="incomplete"):
        verify_prepared(source, mapping, out)


def test_interrupted_manifest_write_never_looks_prepared(tmp_path, monkeypatch):
    """A partial completion marker cannot turn scored bytes into a package."""
    source, mapping = inputs(tmp_path)
    destination = tmp_path / "interrupted"
    marker = destination / "manifest.json"
    original_open = Path.open

    def interrupt_marker(path, mode="r", *args, **kwargs):
        handle = original_open(path, mode, *args, **kwargs)
        if path == marker and mode == "xb":
            with handle:
                handle.write(b"{")
            raise OSError("simulated interruption while writing completion marker")
        return handle

    monkeypatch.setattr(Path, "open", interrupt_marker)
    with pytest.raises(OSError, match="simulated interruption"):
        prepare_export(source, mapping, destination)
    assert (destination / "scored.csv").is_file()
    assert marker.read_bytes() == b"{"
    with pytest.raises(InputError, match="prepared manifest.json"):
        verify_prepared(source, mapping, destination)
    with pytest.raises(FileExistsError):
        prepare_export(source, mapping, destination)
    assert marker.read_bytes() == b"{"


def test_cli_reports_prepared_verified_mismatch_and_bad_input(tmp_path, capsys):
    source, mapping = inputs(tmp_path)
    package = tmp_path / "package"
    assert main(["prepare", "--input", str(source), "--mapping", str(mapping),
                 "--out", str(package)]) == 0
    assert "PREPARED" in capsys.readouterr().out
    command = ["verify-prepared", "--input", str(source), "--mapping",
               str(mapping), "--prepared", str(package)]
    assert main(command) == 0
    assert "VERIFIED" in capsys.readouterr().out
    scored = package / "scored.csv"
    scored.write_bytes(scored.read_bytes().replace(b"0.2", b"0.3", 1))
    assert main(command) == 1
    assert "MISMATCH" in capsys.readouterr().out
    assert main(["prepare", "--input", str(source), "--mapping", str(mapping),
                 "--out", str(package)]) == 2
    assert "exists" in capsys.readouterr().err


@pytest.mark.parametrize("member,content", [
    ("manifest.json", b"not JSON"),
    ("manifest.json", b"[]"),
    ("manifest.json", b'{"schema_version": 1}'),
    ("scored.csv", b"id,label,score\na,0,not-a-number\n"),
])
def test_malformed_package_is_bad_input_not_a_changed_package(
    tmp_path, capsys, member, content,
):
    source, mapping = inputs(tmp_path)
    package = prepare_export(source, mapping, tmp_path / "package")
    (package / member).write_bytes(content)
    with pytest.raises(InputError, match="prepared"):
        verify_prepared(source, mapping, package)
    command = ["verify-prepared", "--input", str(source), "--mapping",
               str(mapping), "--prepared", str(package)]
    assert main(command) == 2
    output = capsys.readouterr()
    assert "warrant:" in output.err and "prepared" in output.err
    assert "MISMATCH" not in output.out


def test_real_cli_rejects_corrupt_manifest_with_exit_two(tmp_path):
    source, mapping = inputs(tmp_path)
    package = prepare_export(source, mapping, tmp_path / "package")
    (package / "manifest.json").write_bytes(b"{")
    command = [sys.executable, str(Path(__file__).resolve().parents[1] / "warrant.py"),
               "verify-prepared", "--input", str(source), "--mapping",
               str(mapping), "--prepared", str(package)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert result.returncode == 2
    assert "prepared" in result.stderr
    assert "MISMATCH" not in result.stdout


def test_unsupported_manifest_version_is_bad_input(tmp_path):
    source, mapping = inputs(tmp_path)
    package = prepare_export(source, mapping, tmp_path / "package")
    manifest = package / "manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["schema_version"] = 2
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(InputError, match="unsupported schema"):
        verify_prepared(source, mapping, package)


def test_well_formed_changed_manifest_remains_mismatch(tmp_path, capsys):
    source, mapping = inputs(tmp_path)
    package = prepare_export(source, mapping, tmp_path / "package")
    manifest = package / "manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["scope"] = "changed but still well-formed"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    assert not verify_prepared(source, mapping, package)
    command = ["verify-prepared", "--input", str(source), "--mapping",
               str(mapping), "--prepared", str(package)]
    assert main(command) == 1
    assert "MISMATCH" in capsys.readouterr().out
