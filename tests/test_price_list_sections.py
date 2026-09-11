"""The price list and kappa reach RESULTS.md, and say so when they cannot.

``CLAUDE.md``'s definition of done asks ``results/RESULTS.md`` for *"the warrant
matrix, the tier ladder, drift/revocation traces, the computed price list, and
kappa"*. The last two were absent because neither existed. They exist now
(``DECISIONS.md`` 146, 147, 152) and these tests are what keeps them in the
document.

**The behaviour worth testing is the absent case.** A renderer that silently
drops a section when its artifact is missing produces a document identical to
one where the section was never required, and this is the document a reviewer
checks the definition of done against.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from controlplane.report.price_list import price_list_sections

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_HEADINGS = (
    "The price list",
    "Inter-rater agreement",
    "Certifying a detector that emits no score",
)


def test_every_required_section_is_present_by_heading() -> None:
    """Three sections, always, whatever is or is not on disk."""
    sections = price_list_sections(PROJECT_ROOT / "results")
    headings = [heading for heading, _ in sections]
    assert len(headings) == len(REQUIRED_HEADINGS)
    for expected, actual in zip(REQUIRED_HEADINGS, headings):
        assert actual.startswith(expected)


def test_a_missing_artifact_names_the_script_rather_than_vanishing(tmp_path: Path) -> None:
    """The absent case, which is the one that would otherwise go unnoticed."""
    sections = price_list_sections(tmp_path)
    assert len(sections) == len(REQUIRED_HEADINGS)
    for _, body in sections:
        assert "Not generated in this run" in body
        assert "scripts/" in body
        # And no number is invented to fill the gap.
        assert "±" not in body


def test_the_price_list_section_carries_the_derivative_and_both_regimes() -> None:
    """The two things that make it a price list rather than a number."""
    artifact = PROJECT_ROOT / "results" / "on_traffic" / "on_traffic.json"
    if not artifact.is_file():
        pytest.skip("results/on_traffic/on_traffic.json is not committed")
    body = dict(price_list_sections(PROJECT_ROOT / "results"))[
        "The price list — what it costs to keep a warrant true"
    ]
    document = json.loads(artifact.read_text(encoding="utf-8"))
    assert f"{document['sensitivity']['derivative']:.3f}" in body
    assert "month one" in body and "steady state" in body
    # The superseded column has to stay visible: a correction nobody can see
    # the size of is a correction nobody checks.
    assert "superseded" in body.lower()
    assert "yield is exact" in body.lower()


def test_the_agreement_section_says_it_measures_no_reviewer() -> None:
    """A kappa from generated labels must not read as a measured one."""
    artifact = PROJECT_ROOT / "results" / "on_traffic" / "on_traffic.json"
    if not artifact.is_file():
        pytest.skip("results/on_traffic/on_traffic.json is not committed")
    body = dict(price_list_sections(PROJECT_ROOT / "results"))[
        "Inter-rater agreement, and the blinded queue"
    ]
    assert "measures no reviewer" in body
    assert "invariant 7" in body
    # Raw agreement beside kappa, because the two are routinely confused.
    assert "raw agreement" in body and "chance" in body


def test_the_scorefree_section_states_that_the_judge_is_simulated() -> None:
    """The scope caveat has to travel with the numbers or it will be dropped."""
    artifact = PROJECT_ROOT / "results" / "scorefree" / "scorefree.json"
    if not artifact.is_file():
        pytest.skip("results/scorefree/scorefree.json is not committed")
    body = dict(price_list_sections(PROJECT_ROOT / "results"))[
        "Certifying a detector that emits no score"
    ]
    assert "simulated" in body
    assert "upper bound" in body
    assert "certifies no real detector" in body
