"""Every mechanism a document asserts is checked, on every run.

This suite exists because of a specific failure, not a hypothetical one. Three
causal explanations were published in one session and all three were wrong; not
one was caught by 1,033 tests or by ``make verify``, because every control here
checks whether a *number* is right and none checked whether the *story about the
number* was right (``DECISIONS.md`` 142).

The claim table already solves that problem for numbers. This is the same
mechanism for the other half of the sentence: a registered mechanism carries a
predicate that would be false if the mechanism were wrong, and the predicate runs
against frozen evidence on every test run.

The rule being enforced is the sibling of "no rate without an interval":
**no mechanism without a test**.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from controlplane.report.causal import CLAIMS, check_claim, load_evidence

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LIVE = [c for c in CLAIMS if c.withdrawn is None]
WITHDRAWN = [c for c in CLAIMS if c.withdrawn is not None]


@pytest.fixture(scope="module")
def evidence() -> dict:
    return load_evidence(PROJECT_ROOT)


def test_the_register_is_not_empty() -> None:
    """A register with nothing in it passes trivially and checks nothing."""
    assert LIVE, "no live causal claims are registered"


@pytest.mark.parametrize("claim", LIVE, ids=lambda c: c.id)
def test_every_asserted_mechanism_survives_its_falsifier(claim, evidence) -> None:
    """The mechanism a document states must be consistent with the evidence.

    A failure here means the **document** is wrong, not the test. The message
    says what to conclude, because a failing assertion that leaves the reader to
    work out which sentence to retract is half a control.
    """
    holds, detail = check_claim(claim, evidence)
    assert holds, (
        f"{claim.id} is asserted in {claim.asserted_in} and its falsifier now "
        f"fails.\n  mechanism: {claim.mechanism}\n  means: {detail}"
    )


@pytest.mark.parametrize("claim", WITHDRAWN, ids=lambda c: c.id)
def test_a_withdrawn_mechanism_still_fails_its_falsifier(claim, evidence) -> None:
    """A withdrawn claim is kept, and it is kept *failing*.

    Deleting a disproved mechanism leaves the documents tidy and the history
    unrecoverable. Keeping it as a live falsifier means the register can show
    what was believed, what disproved it, and that the disproof still stands —
    and it guards the reverse error of quietly reinstating the old story.
    """
    holds, _ = check_claim(claim, evidence)
    assert not holds, (
        f"{claim.id} was withdrawn on the grounds that its falsifier fails, but "
        f"it now passes. Either the evidence changed or the withdrawal was "
        f"wrong.\n  withdrawn: {claim.withdrawn}"
    )


@pytest.mark.parametrize("claim", CLAIMS, ids=lambda c: c.id)
def test_every_claim_points_at_a_document_that_exists(claim) -> None:
    """A mechanism nobody can locate is one nobody can check."""
    document = claim.asserted_in.split(",")[0].split(" ")[0].strip()
    assert (PROJECT_ROOT / document).is_file(), (
        f"{claim.id} cites {document}, which does not exist"
    )
    assert len(claim.mechanism) > 40, f"{claim.id}'s mechanism is too terse to check"
    assert len(claim.falsified_means) > 30, (
        f"{claim.id} does not say what a failure would mean, so a reader who "
        "hits it would not know which sentence to retract"
    )


def test_the_evidence_names_the_corpus_each_measurement_came_from(evidence) -> None:
    """Evidence without provenance is an assertion with extra steps."""
    for key, block in evidence["evidence"].items():
        assert block.get("corpus"), f"{key} does not name the corpus it measured"


def test_missing_evidence_fails_rather_than_passes_quietly() -> None:
    """The dangerous failure is a register that checks nothing and says OK."""
    with pytest.raises(FileNotFoundError, match="24_causal_claims"):
        load_evidence(Path("/nonexistent-root-for-this-test"))
