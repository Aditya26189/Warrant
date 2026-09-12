"""`RESULTS.md` contains every item `SPEC.md` §11 says it must.

§11 is titled *"What `results/RESULTS.md` must contain"* and lists twelve
items. `CLAUDE.md`'s definition of done names the same document. It had never
been audited against the list, and `DECISIONS.md` 164 found **six of twelve**
present — three of which had arrived four days earlier with the price list.

**Every absent item already had a committed artifact.** Nothing was missing
except the rendering, which is the specific shape of the failure and the reason
a test is worth more here than a one-off fix: the evidence was gathered,
committed and verified, and the document that exists to present it did not
mention it.

**The required list is parsed out of `SPEC.md` rather than hard-coded**, so the
spec and this check cannot drift apart in either direction. A thirteenth
requirement added to §11 fails here until something renders it.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import pytest

from controlplane.report.spec_sections import spec_section_11_sections

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC = PROJECT_ROOT / "docs" / "SPEC.md"
RESULTS = PROJECT_ROOT / "results" / "RESULTS.md"

#: Each §11 item to a substring that must appear in ``RESULTS.md``. Written out
#: rather than matched by keyword, because a fuzzy match would let a section
#: satisfy an item it has nothing to do with — which is how a checklist stops
#: meaning anything.
EXPECTED: dict[int, tuple[str, ...]] = {
    1: ("## Provenance", "config hash", "git commit"),
    2: ("## Eval set registry", "content hash"),
    3: ("## Warrant matrix",),
    4: ("## Tier ladder",),
    5: ("## Control results", "padding_fault"),
    6: ("## Routing",),
    7: ("## The price list",),
    8: ("Interval coverage", "trials"),
    9: ("Inter-rater agreement", "κ ="),
    10: ("## Presidio, three configurations",),
    11: ("## The action gate", "detector-nulled"),
    12: ("limitation",),
}


@lru_cache(maxsize=1)
def _spec_items() -> tuple[tuple[int, str], ...]:
    """§11's numbered list, as `SPEC.md` writes it."""
    text = SPEC.read_text(encoding="utf-8")
    parts = text.split("## 11. What `results/RESULTS.md` must contain", 1)
    assert len(parts) == 2, "SPEC.md §11 heading not found"
    body = parts[1].split("\n## ", 1)[0]
    items = [
        (int(m.group(1)), m.group(2).strip())
        for m in re.finditer(r"^(\d+)\.\s+(.+)$", body, re.M)
    ]
    assert items, "no numbered items parsed out of SPEC.md §11"
    return tuple(items)


@lru_cache(maxsize=1)
def _results_text() -> str:
    if not RESULTS.is_file():
        pytest.skip("results/RESULTS.md is not committed")
    return RESULTS.read_text(encoding="utf-8")


def test_the_expected_map_covers_every_item_the_spec_lists() -> None:
    """A thirteenth requirement cannot be added to §11 and silently ignored.

    This is the direction that matters, and it is `DECISIONS.md` 161's finding
    about the problem-statement map in a third document: a checklist covering
    twelve of thirteen reads exactly like a complete one.
    """
    spec_numbers = {number for number, _ in _spec_items()}
    mapped = set(EXPECTED)
    missing = sorted(spec_numbers - mapped)
    extra = sorted(mapped - spec_numbers)
    assert not missing, (
        f"SPEC.md §11 item(s) {missing} have no entry in EXPECTED. Add one "
        "naming what RESULTS.md must contain for it, or the spec is requiring "
        "something nothing checks."
    )
    assert not extra, (
        f"EXPECTED carries item(s) {extra} that SPEC.md §11 no longer lists"
    )


@pytest.mark.parametrize("number", sorted(EXPECTED), ids=lambda n: f"item{n}")
def test_results_md_contains_every_spec_section_11_item(number: int) -> None:
    """The audit `DECISIONS.md` 164 ran, as a test that keeps running it."""
    text = _results_text()
    item = dict(_spec_items()).get(number, "")
    absent = [needle for needle in EXPECTED[number] if needle.lower() not in text.lower()]
    assert not absent, (
        f"SPEC.md §11.{number} requires {item!r} and results/RESULTS.md is "
        f"missing {absent}. Regenerate it with scripts/03_matrix.py, or render "
        "the section if nothing renders it yet."
    )


def test_the_renderer_produces_all_six_of_the_sections_that_were_missing() -> None:
    """Six headings, always, whatever is on disk."""
    sections = spec_section_11_sections(PROJECT_ROOT / "results")
    assert len(sections) == 6
    headings = [heading for heading, _ in sections]
    assert len({h for h in headings}) == 6, f"duplicate headings: {headings}"


def test_a_missing_artifact_names_its_script_rather_than_vanishing(tmp_path: Path) -> None:
    """The absent case, which is the one that would otherwise go unnoticed."""
    sections = spec_section_11_sections(tmp_path)
    assert len(sections) == 6
    for heading, body in sections:
        assert "Not generated in this run" in body, heading
        assert "scripts/" in body, heading


def test_the_routing_section_says_the_revocation_trace_is_missing() -> None:
    """§11.6 asks for a revocation trace and there is not one.

    The routing decisions exist. A live drift run that revoked a warrant does
    not, because the drift machinery has never been pointed at a moving
    distribution with a warrant outstanding. Rendering the half that exists and
    implying the other would be exactly the overclaim this document is for.
    """
    body = dict(spec_section_11_sections(PROJECT_ROOT / "results"))[
        "Routing, and the revocation trace that is missing"
    ]
    if "Not generated in this run" in body:
        pytest.skip("results/warrant_matrix.json is not committed")
    assert "revocation half of this section is missing" in body
    assert "OPEN" in body


def test_the_gate_section_makes_no_robustness_claim() -> None:
    """The section most likely to be oversold, checked by name."""
    body = dict(spec_section_11_sections(PROJECT_ROOT / "results"))[
        "The action gate, and the detector-nulled case"
    ]
    if "Not generated in this run" in body:
        pytest.skip("results/gate/gate.json is not committed")
    assert "not a robustness claim" in body.lower()
    assert "2510.09023" in body, "the injection claim has lost its citation"
