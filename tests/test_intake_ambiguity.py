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
    ("id,label,score,label_2, label_2", "a,0,0.1,0,1\nb,1,0.9,1,0\n", "label_2"),
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
    ('{"id":"a","label":0,"score":0.1,"label_2":0,"label_2":1}', "label_2"),
    ('{"id":"a","label":0,"score":0.1,"group":"x","group":"y"}', "group"),
    ('{"id":"a","label":0,"score":0.1,"note":{"tag":"x","tag":"y"}}', "tag"),
    (r'{"id":"a","label":0,"score":0.1,"sco\u0072e":0.9}', "score"),
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


@pytest.mark.parametrize("header", ["id,label,score,", "id,label,score,   "])
def test_blank_csv_header_cannot_hide_an_extra_field(tmp_path: Path, header: str) -> None:
    path = tmp_path / "blank-header.csv"
    path.write_bytes((header + "\na,0,0.1,ignored\nb,1,0.9,ignored\n").encode())
    with pytest.raises(InputError, match="non-blank column"):
        load_scored_items(path)


@pytest.mark.parametrize("row", ["a,0,0.1", "a,0,0.1,meta,extra"])
def test_ragged_csv_rows_do_not_fill_or_discard_metadata(tmp_path: Path, row: str) -> None:
    path = tmp_path / "ragged.csv"
    path.write_bytes(("id,label,score,note\n" + row + "\nb,1,0.9,meta\n").encode())
    with pytest.raises(InputError, match="expected 4 CSV fields") as failure:
        load_scored_items(path)
    assert "ragged.csv" in str(failure.value)
    assert "line 2" in str(failure.value)


def test_unclosed_csv_quote_is_an_input_error(tmp_path: Path) -> None:
    path = tmp_path / "unclosed.csv"
    path.write_bytes(b'id,label,score,note\na,0,0.1,"unfinished\nb,1,0.9,meta\n')
    with pytest.raises(InputError, match="not valid CSV"):
        load_scored_items(path)


def test_normalized_csv_headers_preserve_groups_and_second_labels(tmp_path: Path) -> None:
    path = tmp_path / "normalized.csv"
    path.write_bytes(
        b' id , label , score , group , label_2 , note \n'
        b'a,0,0.1,"team,A",0,"first, with comma"\n'
        b'\n'
        b'b,1,0.9,"team,B",,"second\nwith newline"\n'
    )
    items = load_scored_items(path)
    assert items.ids == ("a", "b")
    assert items.labels == (0, 1)
    assert items.scores == (0.1, 0.9)
    assert items.groups == ("team,A", "team,B")
    assert items.second_labels == (0, None)
    assert items.passthrough_columns == ("note",)


def test_json_duplicate_error_reports_the_physical_line(tmp_path: Path) -> None:
    path = tmp_path / "line.jsonl"
    path.write_bytes(
        b'\n{"id":"a","label":0,"score":0.1}\n'
        b'{"id":"b","label":1,"score":0.1,"score":0.9}\n'
    )
    with pytest.raises(InputError, match="line.jsonl line 3: duplicate JSON field 'score'"):
        load_scored_items(path)
