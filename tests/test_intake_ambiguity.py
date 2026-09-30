"""Reject ambiguous scored exports before they can change an evidence decision."""

from pathlib import Path

import pytest

from controlplane.intake.contract import InputError, load_scored_items


@pytest.mark.parametrize("header,rows,field", [
    ("id,label,score,score", "a,0,0.9,0.1\nb,1,0.1,0.9\n", "score"),
    ("id,label,label,score", "a,1,0,0.1\nb,0,1,0.9\n", "label"),
    ("id,id,label,score", "wrong,a,0,0.1\nwrong,b,1,0.9\n", "id"),
    ("id,label,score, score", "a,0,0.9,0.1\nb,1,0.1,0.9\n", "score"),
    ("id,label,score,group, group", "a,0,0.1,x,y\nb,1,0.9,x,z\n", "group"),
    ("id,label,score,note,note", "a,0,0.1,x,x\nb,1,0.9,y,y\n", "note"),
])
def test_duplicate_csv_headers_are_not_resolved_by_last_value(
    tmp_path: Path, header: str, rows: str, field: str,
) -> None:
    """A conflicting or redundant field must not disappear during dict parsing."""
    path = tmp_path / "ambiguous.csv"
    path.write_bytes((header + "\n" + rows).encode("utf-8"))

    with pytest.raises(InputError) as failure:
        load_scored_items(path)

    message = str(failure.value).lower()
    assert "duplicate" in message
    assert field in message


@pytest.mark.parametrize("first,field", [
    ('{"id":"a","label":0,"score":0.9,"score":0.1}', "score"),
    ('{"id":"a","label":1,"label":0,"score":0.1}', "label"),
    ('{"id":"wrong","id":"a","label":0,"score":0.1}', "id"),
    ('{"id":"a","label":0,"score":0.1,"note":"x","note":"x"}', "note"),
])
def test_duplicate_jsonl_fields_are_not_resolved_by_last_value(
    tmp_path: Path, first: str, field: str,
) -> None:
    """Specification JSON and scored JSON must reject the same ambiguity."""
    path = tmp_path / "ambiguous.jsonl"
    path.write_bytes((first + '\n{"id":"b","label":1,"score":0.9}\n').encode("utf-8"))

    with pytest.raises(InputError) as failure:
        load_scored_items(path)

    message = str(failure.value).lower()
    assert "duplicate" in message
    assert field in message


@pytest.mark.parametrize("suffix,raw", [
    ("csv", "id,label,score,note\na,0,0.1,first\nb,0,0.2,second\n"),
    ("jsonl", '{"id":"a","label":0,"score":0.1,"note":"first"}\n'
     '{"id":"b","label":0,"score":0.2,"note":"second"}\n'),
])
def test_unambiguous_single_class_keeps_explicit_release_opt_in(
    tmp_path: Path, suffix: str, raw: str,
) -> None:
    """Stricter field parsing must preserve the existing missing-class contract."""
    path = tmp_path / f"clean.{suffix}"
    path.write_bytes(raw.encode("utf-8"))

    with pytest.raises(InputError, match="every label"):
        load_scored_items(path)

    items = load_scored_items(path, require_both_classes=False)
    assert items.ids == ("a", "b")
    assert items.labels == (0, 0)
    assert items.scores == (0.1, 0.2)
    assert items.passthrough_columns == ("note",)
