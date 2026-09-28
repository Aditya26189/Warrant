"""A retained certify result names the effective rows it was computed from."""

from __future__ import annotations

from pathlib import Path

from controlplane.config import load_customer_config
from controlplane.intake import certify_items, load_scored_items
from controlplane.intake.certify import evidence_sha256, input_sha256


def _file(path: Path, rows: list[str], *, note: str = "first") -> Path:
    path.write_text(
        "id,label,score,group,label_2,note\n"
        + "\n".join(f"{row},{note}" for row in rows) + "\n",
        encoding="utf-8",
    )
    return path


def test_effective_rows_are_bound_but_order_and_ignored_columns_are_not(
    tmp_path: Path,
) -> None:
    rows = ["a,0,0.1,g1,0", "b,1,0.9,g1,1", "c,0,0.2,g2,", "d,1,0.8,g2,0"]
    first = load_scored_items(_file(tmp_path / "first.csv", rows))
    reordered = load_scored_items(_file(tmp_path / "reordered.csv", rows[::-1], note="other"))
    assert evidence_sha256(first) == evidence_sha256(reordered)

    for changed in (
        ["other,0,0.1,g1,0", *rows[1:]],
        ["a,1,0.1,g1,0", *rows[1:]],
        ["a,0,0.3,g1,0", *rows[1:]],
        ["a,0,0.1,g2,0", *rows[1:]],
        ["a,0,0.1,g1,1", *rows[1:]],
    ):
        altered = load_scored_items(_file(tmp_path / "altered.csv", changed))
        assert evidence_sha256(altered) != evidence_sha256(first)

    second_review_changed = load_scored_items(
        _file(tmp_path / "review.csv", ["a,0,0.1,g1,1", *rows[1:]])
    )
    assert input_sha256(first) == input_sha256(second_review_changed)
    assert evidence_sha256(first) != evidence_sha256(second_review_changed)


def test_refusal_also_carries_effective_row_binding(tmp_path: Path) -> None:
    rows = ["a,0,0.1,g1,0", "b,1,0.9,g1,1", "c,0,0.2,g2,", "d,1,0.8,g2,0"]
    items = load_scored_items(_file(tmp_path / "refuses.csv", rows))
    result = certify_items(load_customer_config(), items, budget=0.01)
    assert result.to_payload()["input"]["evidence_sha256"] == evidence_sha256(items)
