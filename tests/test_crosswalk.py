"""The RBI crosswalk names code and tests that exist, and says where it stops.

``DECISIONS.md`` 189. A crosswalk that ticks a paragraph without naming what
holds it is a compliance claim with nothing behind it, and one whose named test
was renamed three commits ago is the same thing a month later. These tests read
the files with :mod:`ast`, as ``tests/test_invariants.py`` does, for the reason
given there: collecting through pytest from inside pytest recurses.
"""

from __future__ import annotations

import ast
import re
from functools import lru_cache
from pathlib import Path

import pytest

from controlplane.report.crosswalk import (
    RBI_MRM_2026,
    SOURCE,
    Coverage,
    Requirement,
    render_crosswalk,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGE = PROJECT_ROOT / "docs" / "RBI-MRM-2026-CROSSWALK.md"


@lru_cache(maxsize=None)
def _defined_names(relative: str) -> frozenset[str]:
    """Top-level functions and classes, and ``Class.method`` for methods."""
    tree = ast.parse((PROJECT_ROOT / relative).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        if isinstance(node, ast.ClassDef):
            names.update(
                f"{node.name}.{item.name}"
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
    return frozenset(names)


def _refs(attribute: str) -> list[tuple[str, str]]:
    return sorted(
        {(row.paragraph, ref) for row in RBI_MRM_2026 for ref in getattr(row, attribute)}
    )


@pytest.mark.parametrize("paragraph,ref", _refs("provided_by"))
def test_every_named_symbol_exists(paragraph: str, ref: str) -> None:
    path, symbol = ref.split("::", 1)
    assert (PROJECT_ROOT / path).is_file(), f"¶{paragraph}: {path} does not exist"
    assert symbol in _defined_names(path), f"¶{paragraph}: {path} defines no {symbol}"


@pytest.mark.parametrize("paragraph,ref", _refs("held_by"))
def test_every_named_test_exists(paragraph: str, ref: str) -> None:
    path, name = ref.split("::", 1)
    assert path.startswith("tests/test_"), f"¶{paragraph}: {ref} is not a test"
    assert (PROJECT_ROOT / path).is_file(), f"¶{paragraph}: {path} does not exist"
    assert name in _defined_names(path), f"¶{paragraph}: {path} has no {name}"


@pytest.mark.parametrize("paragraph,path", _refs("evidence"))
def test_every_evidence_path_exists(paragraph: str, path: str) -> None:
    assert (PROJECT_ROOT / path).exists(), f"¶{paragraph}: {path} does not exist"


def test_the_committed_page_is_the_register() -> None:
    assert PAGE.is_file(), "run: python -m controlplane.report.crosswalk"
    assert PAGE.read_bytes().decode("utf-8") == render_crosswalk(), (
        "docs/RBI-MRM-2026-CROSSWALK.md differs from the register; regenerate it "
        "with `python -m controlplane.report.crosswalk` rather than editing it"
    )


def test_paragraphs_are_not_mapped_twice() -> None:
    paragraphs = [row.paragraph for row in RBI_MRM_2026]
    assert len(paragraphs) == len(set(paragraphs))


def test_a_coverage_claim_with_nothing_holding_it_cannot_be_written() -> None:
    with pytest.raises(ValueError, match="names no code or no test"):
        Requirement(paragraph="x", topic="t", quote="q", coverage=Coverage.PROVIDES)
    with pytest.raises(ValueError, match="states no gap"):
        Requirement(
            paragraph="x", topic="t", quote="q", coverage=Coverage.PARTIAL,
            provided_by=("a.py::f",), held_by=("tests/test_a.py::test_f",),
        )


def test_the_gaps_a_buyer_asks_about_first_are_stated_not_ticked() -> None:
    """Explainability, fairness, red-teaming and exception approval.

    Each is a paragraph a model-validation lead reads for, and each is one this
    repository does not do. Moving any of them off NOT PROVIDED needs a decision
    entry, not an edit to this table.
    """
    by_paragraph = {row.paragraph: row for row in RBI_MRM_2026}
    for paragraph in ("54(1)(i)", "54(3)", "55", "34"):
        assert by_paragraph[paragraph].coverage is Coverage.NOT_PROVIDED


def test_the_page_says_it_is_a_draft_and_not_compliance() -> None:
    page = render_crosswalk()
    assert "DRAFT" in SOURCE["status"] and "DRAFT" in page
    assert "not a compliance claim" in page


def test_the_page_does_not_claim_an_anytime_valid_guarantee() -> None:
    """The crosswalk cannot infer a deployment guarantee from a code repair.

    Decision 226 fixes the monitor's component-cap error, but the customer
    sampling process has not established its conditional-null assumption.
    """
    page = render_crosswalk().lower()
    assert "anytime" not in page
    assert "fprmonitor" not in page


def test_the_page_carries_no_measured_number() -> None:
    """Orientation pages point at artifacts; a decimal here is a figure that goes stale."""
    assert not re.findall(r"\b\d+\.\d+\b", render_crosswalk())
