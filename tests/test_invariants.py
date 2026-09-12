"""Every ``CLAUDE.md`` invariant names the test that enforces it, and it exists.

``docs/TASKS.md`` Phase 12's documentation audit opens with a line that had
never been discharged:

> *every invariant in* ``CLAUDE.md`` *enforced somewhere in code; name file and
> line*

All nine are *mentioned* in tests — a grep finds 106 references — and a mention
is not an enforcement. Nothing checked that the enforcing test still exists,
still runs under that name, or that a tenth invariant added to the contract
arrived with any enforcement at all.

These tests close that. They do **not** verify that a named test genuinely
enforces what it claims; that needs mutation testing, and the honest version is
the deliberate-breakage falsifier ``DECISIONS.md`` 142's causal register uses,
which does not generalise to nine invariants cheaply. What they close is
narrower and was completely open: **an invariant whose enforcement quietly
disappeared left no trace.**

**Why this parses the test files rather than asking pytest.** The first version
called ``pytest --collect-only`` at module scope. That subprocess collects
``tests/``, which imports this module, which spawns another subprocess — an
unbounded recursion that hangs rather than failing, so it does not even announce
itself. Reading the files with :mod:`ast` answers the same question, takes
milliseconds, and cannot re-enter.
"""

from __future__ import annotations

import ast
import re
from functools import lru_cache
from pathlib import Path

import pytest

from controlplane.report.invariants import (
    DERIVED_CLAIMS,
    INVARIANTS,
    READ_ONLY_WITHOUT_DERIVATION,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"
TESTS_DIR = PROJECT_ROOT / "tests"


@lru_cache(maxsize=1)
def _contract_invariants() -> tuple[tuple[int, str], ...]:
    """The numbered invariant list as ``CLAUDE.md`` actually writes it."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    parts = text.split("## Non-negotiable invariants", 1)
    assert len(parts) == 2, "CLAUDE.md has no 'Non-negotiable invariants' heading"
    body = parts[1].split("\n## ", 1)[0]
    found = [
        (int(match.group(1)), match.group(2).strip())
        for match in re.finditer(r"^(\d+)\.\s+\*\*(.+?)\*\*", body, re.M)
    ]
    return tuple(found)


@lru_cache(maxsize=1)
def _test_functions() -> frozenset[str]:
    """``tests/<file>.py::<function>`` for every test function on disk.

    Parsed rather than collected. Parametrised ids are not reconstructed —
    :func:`_base_node` strips the ``[...]`` suffix before lookup, because what
    is being checked is that the function still exists under that name, not that
    a particular parameter case still does.
    """
    names: set[str] = set()
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = f"tests/{path.name}"
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    names.add(f"{relative}::{node.name}")
    assert names, "no test functions found under tests/"
    return frozenset(names)


def _base_node(node_id: str) -> str:
    """A pytest node id with any parametrised suffix removed."""
    return node_id.split("[", 1)[0]


def test_the_register_covers_every_invariant_in_the_contract() -> None:
    """A tenth invariant cannot be added to ``CLAUDE.md`` with no enforcement.

    This is the direction that matters. A register listing nine when the
    contract lists ten reads exactly like a complete one — which is
    ``DECISIONS.md`` 161's finding about the problem-statement map, one document
    along.
    """
    contract = dict(_contract_invariants())
    assert contract, "no numbered invariants parsed out of CLAUDE.md"
    registered = {inv.number for inv in INVARIANTS}
    missing = sorted(set(contract) - registered)
    extra = sorted(registered - set(contract))
    assert not missing, (
        f"CLAUDE.md invariant(s) {missing} have no entry in "
        "controlplane/report/invariants.py. Add one naming the test that "
        "enforces it, or the contract is asserting something nothing checks."
    )
    assert not extra, (
        f"the register carries invariant(s) {extra} that CLAUDE.md no longer "
        "lists. Remove them rather than leaving a register describing a "
        "contract that has moved."
    )


@pytest.mark.parametrize("invariant", INVARIANTS, ids=lambda i: f"inv{i.number}")
def test_the_registered_headline_matches_the_contract(invariant) -> None:
    """Editing the contract without updating the register fails here."""
    actual = dict(_contract_invariants())[invariant.number]
    assert actual.startswith(invariant.headline), (
        f"invariant {invariant.number} reads {actual!r} in CLAUDE.md and "
        f"{invariant.headline!r} in the register. One of them moved."
    )


@pytest.mark.parametrize("invariant", INVARIANTS, ids=lambda i: f"inv{i.number}")
def test_every_named_enforcing_test_exists(invariant) -> None:
    """A renamed or deleted enforcing test fails the register.

    This is the whole point. Before this file, deleting
    ``tests/test_validation.py::test_no_override`` would have left invariant 3
    unenforced and nothing would have said so — the invariant would still be in
    the contract, still quoted in the README, and checked by nothing.
    """
    assert invariant.enforced_by, (
        f"invariant {invariant.number} names no enforcing test"
    )
    on_disk = _test_functions()
    absent = [
        node for node in invariant.enforced_by if _base_node(node) not in on_disk
    ]
    assert not absent, (
        f"invariant {invariant.number} ({invariant.headline}) names "
        f"enforcing test(s) that do not exist: {absent}. Either the test was "
        "renamed -- update the register -- or it was deleted, in which case the "
        "invariant is now unenforced."
    )


@pytest.mark.parametrize("invariant", INVARIANTS, ids=lambda i: f"inv{i.number}")
def test_every_invariant_says_what_breaks_without_it(invariant) -> None:
    """A register entry with no failure mode is a box someone ticked.

    The ``breaks_as`` field is what lets a reader judge whether the named tests
    are plausibly the right ones. Without it the register asserts coverage and
    supplies no way to check the assertion.
    """
    assert len(invariant.breaks_as) > 40, (
        f"invariant {invariant.number} does not say what its absence looks like"
    )


def test_the_enforcing_tests_are_spread_across_the_suite() -> None:
    """Nine invariants enforced by two files would be a register, not coverage.

    Not a deep check, and it is here because the cheapest way to make this
    register pass would have been to name two well-known tests nine times.
    """
    files = {
        _base_node(node).split("::", 1)[0]
        for inv in INVARIANTS
        for node in inv.enforced_by
    }
    assert len(files) >= 7, (
        f"the enforcing tests live in only {len(files)} files: {sorted(files)}"
    )


def test_the_register_finds_a_deleted_enforcement() -> None:
    """The register has to fail when an enforcement goes, so prove that it does.

    ``DECISIONS.md`` 142 built a causal register and verified it by flipping the
    evidence to the world in which the withdrawn claim was true. Same idea, much
    cheaper: assert against a node id that certainly does not exist, and check
    the lookup rejects it. A register whose check silently passes on a missing
    test is worse than no register, because it reports coverage that is not
    there.
    """
    on_disk = _test_functions()
    assert "tests/test_validation.py::test_no_override" in on_disk, (
        "the sentinel this test uses has itself been renamed; pick another"
    )
    assert (
        _base_node("tests/test_validation.py::test_a_name_nobody_has_used")
        not in on_disk
    )
    # And the parametrised-id stripping works, or invariant 5 would pass for the
    # wrong reason.
    assert (
        _base_node("tests/test_model.py::test_blended_scores_are_refused_by_name[f1]")
        in on_disk
    )


# --------------------------------------------------------------------------- #
# Statistical claims carry their derivation
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=None)
def _docstring(module: str, function: str) -> str:
    """The docstring of one public function, read from source."""
    path = PROJECT_ROOT / module
    assert path.is_file(), f"{module} does not exist"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function:
                return ast.get_docstring(node) or ""
    raise AssertionError(f"{module} has no function named {function!r}")


@pytest.mark.parametrize(
    "module,function", DERIVED_CLAIMS, ids=lambda v: v if isinstance(v, str) else str(v)
)
def test_every_registered_statistical_claim_states_its_derivation(
    module: str, function: str
) -> None:
    """``CLAUDE.md``: a sample size, interval or projection states its propagation.

    ``docs/TASKS.md`` Phase 12 repeats it as an audit line, and nothing checked
    it until `DECISIONS.md` 163 counted: **8 of 32** qualifying functions carried
    one.

    The check is that the pair cannot *disappear*. Two lines in a docstring are
    not a control on their own — a wrong derivation stated confidently is worse
    than none — but an absent one is a thing nobody looks for, and that is the
    failure that already happened: ``review.recall_sample_size`` carried no
    propagation for four phases while computing the wrong one.
    """
    doc = _docstring(module, function)
    assert doc, f"{module}::{function} has no docstring at all"
    low = doc.lower()
    assert "quantity:" in low, (
        f"{module}::{function} returns an interval, a bound or a sample size "
        "and does not say what quantity it estimates"
    )
    assert "propagation:" in low, (
        f"{module}::{function} does not say how the uncertainty was propagated. "
        "CLAUDE.md requires it wherever a statistical claim appears; "
        "DECISIONS.md 147 is what an unstated propagation cost."
    )


def test_the_read_only_gap_is_recorded_rather_than_quietly_absent() -> None:
    """The eight in read-only zones are an OPEN item, not an oversight.

    ``CLAUDE.md`` makes ``stats.py``, ``warrant_stats.py``, ``drift/`` and
    ``policy/`` read-only, so these cannot be fixed here. Listing them turns a
    silence into a number — and four of them are the most-used estimators in the
    repository, so the headline coverage figure understates the gap where it
    matters most.
    """
    assert READ_ONLY_WITHOUT_DERIVATION, "the OPEN list has been emptied"
    for module, function in READ_ONLY_WITHOUT_DERIVATION:
        assert (PROJECT_ROOT / module).is_file(), f"{module} no longer exists"
        # If one of these gains a derivation, it should move out of the list
        # rather than sit here misreporting the gap.
        doc = _docstring(module, function).lower()
        if "propagation:" in doc:
            pytest.fail(
                f"{module}::{function} now carries a derivation and should move "
                "from READ_ONLY_WITHOUT_DERIVATION into DERIVED_CLAIMS"
            )


def test_the_two_registers_do_not_overlap() -> None:
    """A function is either checked or recorded as unchecked, never both."""
    checked = set(DERIVED_CLAIMS)
    opened = set(READ_ONLY_WITHOUT_DERIVATION)
    assert not (checked & opened), (
        f"listed as both enforced and open: {sorted(checked & opened)}"
    )
