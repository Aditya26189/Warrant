"""Numbers in README prose track their artifacts, not just numbers in the table.

``CLAUDE.md`` invariant 8: *every number in a document is computed by code; if
it cannot be traced to an artifact in* ``results/``\\ *, it does not go in the
README.*

`scripts/verify.py` enforces that for the **claim table**, which is parsed and
recomputed row by row. It does not look at prose. So a figure quoted in a
sentence — which is the part a reader actually reads, and the part that gets
screenshotted — could drift from its artifact and nothing would notice.

That is the same gap three times over in this repository's history: the test
count was checked in prose and not in the badge (`DECISIONS.md` 151), two
artifacts were each internally reproducible and disagreed with each other
(`DECISIONS.md` 153), and the sizing was arithmetically perfect in the wrong
units (`DECISIONS.md` 147). **A control existed wherever a number might be
arithmetically wrong, and nowhere else.** This is one of the elsewheres.

The check is deliberately narrow. It does not try to find every number in the
README — that needs a parser for English. It re-reads the artifacts behind the
three-clause section and asserts each figure still appears, formatted the way
the section formats it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
README = PROJECT_ROOT / "README.md"
SECTION_HEADING = "## 🧭 The three clauses, and where each one is proved"


def _section() -> str:
    text = README.read_text(encoding="utf-8")
    assert SECTION_HEADING in text, (
        "the three-clause section is gone from README.md. If that is "
        "deliberate, delete this test rather than leaving one that passes on a "
        "section it is not reading."
    )
    after = text.split(SECTION_HEADING, 1)[1]
    return after.split("\n## ", 1)[0]


def _artifact(*parts: str) -> dict:
    path = PROJECT_ROOT.joinpath("results", *parts)
    if not path.is_file():
        pytest.skip(f"{path.relative_to(PROJECT_ROOT)} is not committed")
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_on_traffic_figures_in_prose_match_the_artifact() -> None:
    """The price list and the derivative, as the section formats them."""
    head = _artifact("on_traffic", "on_traffic.json")["headline"]
    section = _section()
    expected = {
        "dR/dq": f"{head['derivative']:.3f}",
        "coverage": f"{head['coverage']:.1%}",
        "trials": f"{head['coverage_trials']:,}",
        "labels at +/-0.05": f"{head['labels_month_one_5pp']:,}",
        "superseded sizing": f"{head['superseded_sizing_5pp']}",
    }
    missing = {name: value for name, value in expected.items() if value not in section}
    assert not missing, (
        f"these figures are in results/on_traffic/on_traffic.json but not in "
        f"the README prose that quotes them: {missing}. Re-run "
        "scripts/25_on_traffic.py and update the section."
    )


def test_the_scorefree_figures_in_prose_match_the_artifact() -> None:
    """The tunability claim is the one most likely to be quoted back at us."""
    head = _artifact("scorefree", "scorefree.json")["headline"]
    section = _section()
    expected = {
        "single-sample floor": f"{head['single_sample_floor_median']:.3f}",
        "operating points at k=1": str(head["operating_points_at_k1"]),
        "notches at k=50": str(head["notches_at_k50"]),
        "operating points at k=50": str(head["operating_points_at_k50"]),
    }
    missing = {name: value for name, value in expected.items() if value not in section}
    assert not missing, f"scorefree figures missing from README prose: {missing}"


def test_the_gate_figures_in_prose_match_the_artifact() -> None:
    """The no-detector count is the product's only adversarial claim."""
    head = _artifact("gate", "gate.json")["headline"]
    section = _section()
    expected = {
        "identical decisions": str(head["decisions_identical_without_a_detector"]),
        "decisions compared": str(head["decisions_compared"]),
        "blocked at step": str(head["injection_blocked_at_step"]),
        "workflows blocked": str(head["legitimate_workflows_blocked"]),
        "workflows declared": str(head["legitimate_workflows"]),
    }
    missing = {name: value for name, value in expected.items() if value not in section}
    assert not missing, f"gate figures missing from README prose: {missing}"


def test_the_section_makes_no_robustness_claim() -> None:
    """``CLAUDE.md`` puts adversarial robustness out of scope, in those words.

    The gate is the part of this system most likely to be oversold, because what
    it does is genuinely strong and one sentence of enthusiasm turns it into a
    claim the repository has spent six phases refusing to make.
    """
    section = _section().lower()
    assert "not** a robustness claim" in section or "not a robustness claim" in section
    # The claim the refusal rests on must carry its primary source. It appears
    # in six files and had no citation anywhere until it was checked: Nasr et
    # al., "The Attacker Moves Second", bypassed 12 published defences at above
    # 90% attack success for most, where the majority had reported near-zero.
    # "I read it somewhere" is exactly the evidence standard
    # reports/STRATEGY-2026-09.md was written to stop this project accepting.
    assert "2510.09023" in section, "the injection claim has lost its citation"
    assert "90%" in section
    assert "12" in section
    for overclaim in (
        "immune",
        "cannot be bypassed",
        "unbreakable",
        "prevents all",
        "guarantees safety",
    ):
        assert overclaim not in section, f"the section claims {overclaim!r}"


def test_every_headline_field_the_prose_uses_is_also_a_claim_row() -> None:
    """Prose and table must not diverge on which figures are checked.

    ``verify.py`` recomputes claim-table rows and ignores prose. A figure quoted
    in a sentence with no row behind it is checked by this file alone; a figure
    with a row is checked by both. Requiring a row for each means the stronger
    control always applies.
    """
    import re

    text = README.read_text(encoding="utf-8")
    rows = set(re.findall(r"\|\s*(headline\.[a-z0-9_]+)\s*\|", text))
    assert rows, "no headline.* claim rows found; has the table moved?"

    used = {
        "derivative",
        "coverage",
        "coverage_trials",
        "labels_month_one_5pp",
        "superseded_sizing_5pp",
        "operating_points_at_k1",
        "single_sample_floor_median",
        "notches_at_k50",
        "operating_points_at_k50",
        "decisions_identical_without_a_detector",
        "decisions_compared",
        "injection_blocked_at_step",
        "legitimate_workflows_blocked",
        "legitimate_workflows",
        "blocked_workflows_recoverable",
    }
    missing = sorted(f for f in used if f"headline.{f}" not in rows)
    assert not missing, (
        f"quoted in README prose with no claim-table row: {missing}. Add a row "
        "so make verify recomputes it, rather than leaving this test as the "
        "only thing between the number and its artifact."
    )
