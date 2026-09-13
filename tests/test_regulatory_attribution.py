"""The repository says what DPDP Rules 6 and 8 say, and no more.

``DECISIONS.md`` 168. ``SPEC.md`` §1.5 credited Rule 6 with naming six query
predicates -- session, time range, policy version, detector version, warrant
status, personal-data category. Rule 6(1)(c) requires *"visibility on the
accessing of such personal data, through appropriate logs, monitoring and
review"* and names no predicate; 6(1)(e) keeps those logs *"for a period of one
year"*. The word *minimum* is Rule 8(3)'s. The attribution had spread to seven
files, two of them read-only.

The check is a sentence heuristic, and deliberately narrow. A sentence naming
Rule 6 fails if, together with the sentence after it, it

- mentions querying, predicates or indexes without saying the predicates are
  this project's or that the rule names none; or
- calls the retention a *minimum* without citing Rule 8(3).

It is a claim about phrasing, not about meaning (``DECISIONS.md`` 165), which is
why it carries a self-test on the sentences that started this.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RULE_6 = re.compile(r"\bRules? 6\b")
QUERYING = re.compile(r"quer|predicate|index", re.IGNORECASE)
DISCLAIMS = ("names no", "names none", "this project's", "not the rule")
SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml", ".rego", ".txt", ".ipynb", ".cfg"}

#: Whole trees whose text is not a claim by this repository.
EXEMPT_PREFIXES = (
    "evalsets/",  # frozen corpora; the sentence is hard-negative input text
    "round1/",  # the Round 1 submission, moved whole and unmodified
    "results/",  # read-only artifacts
)

#: Single files exempt for a stated reason.
EXEMPT_FILES = {
    "DECISIONS.md": "append-only; 026 and 093 carry the original wording",
    "tests/test_regulatory_attribution.py": "quotes the sentences it detects",
    "controlplane/evalsets/hard_negatives.py": (
        "builds the frozen hard-negative corpus; the sentence is input text and "
        "changing it changes a content-hashed eval set"
    ),
}

#: Read-only files known to carry the attribution (CLAUDE.md: read and call, do
#: not modify). Each must still be caught, so the exemption expires with the fix.
KNOWN_READ_ONLY = (
    "controlplane/store/ledger.py",
    "controlplane/drift/certify.py",
)


def _sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text)
    return [s for s in re.split(r"(?<=[.!?])\s+|\n\n", flat) if s]


def misattributions(text: str) -> list[str]:
    """Sentences crediting Rule 6 with query predicates or a minimum."""
    sentences = _sentences(text)
    found = []
    for i, sentence in enumerate(sentences):
        if not RULE_6.search(sentence):
            continue
        window = sentence + " " + (sentences[i + 1] if i + 1 < len(sentences) else "")
        if QUERYING.search(sentence) and not any(d in window for d in DISCLAIMS):
            found.append(sentence)
        elif re.search(r"minimum", sentence, re.IGNORECASE) and "8(3)" not in window:
            found.append(sentence)
    return found


def _tracked_text_files() -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [p for p in listed if Path(p).suffix in SUFFIXES]


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# The heuristic is not vacuous
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "sentence",
    [
        "Requirements from DPDP Rule 6: ≥1 year retention; queryable by session, "
        "time range, policy version, detector version, warrant status, and "
        "personal-data category accessed.",
        "Required — the store must be queryable by session (DPDP Rule 6).",
        "Every predicate DPDP Rule 6 names, and they compose.",
        "DPDP Rule 6 sets a minimum, and this store will not go under it.",
        "Retention is 400 days (DPDP Rule 6 minimum is one year).",
    ],
)
def test_the_original_wordings_are_caught(sentence: str) -> None:
    assert misattributions(sentence), f"not caught: {sentence!r}"


@pytest.mark.parametrize(
    "sentence",
    [
        "Rule 6(1)(c) requires visibility on access; it names no predicate.",
        "Rule 6(1)(e) requires logs be kept for a period of one year, and Rule "
        "8(3) sets a minimum period of one year.",
        "Retention is 400 days (DPDP Rules 6(1)(e) and 8(3): one year).",
    ],
)
def test_the_corrected_wordings_pass(sentence: str) -> None:
    assert not misattributions(sentence), f"false positive: {sentence!r}"


# --------------------------------------------------------------------------- #
# The repository
# --------------------------------------------------------------------------- #


def test_no_tracked_file_credits_rule_6_with_query_predicates() -> None:
    offenders = []
    for relative in _tracked_text_files():
        if relative.startswith(EXEMPT_PREFIXES) or relative in EXEMPT_FILES:
            continue
        if relative in KNOWN_READ_ONLY:
            continue
        for sentence in misattributions(_read(relative)):
            offenders.append(f"{relative}: {sentence[:140]}")
    assert not offenders, (
        "DPDP Rule 6 names no query predicate and says 'one year', not "
        "'minimum' (Rule 8(3)). DECISIONS.md 168.\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("relative", KNOWN_READ_ONLY)
def test_the_read_only_exemptions_have_not_outlived_the_problem(relative: str) -> None:
    """When the read-only text is corrected, remove it from KNOWN_READ_ONLY."""
    assert misattributions(_read(relative)), (
        f"{relative} no longer carries the Rule 6 attribution; delete it from "
        "KNOWN_READ_ONLY and close the OPEN item in DECISIONS.md 168"
    )


def test_the_spec_states_the_rules_with_their_clauses() -> None:
    spec = _read("docs/SPEC.md")
    for clause in ("Rule 6(1)(c)", "Rule 6(1)(e)", "Rule 8(3)", "13 May 2027"):
        assert clause in spec, f"SPEC.md §1.5 no longer cites {clause}"
