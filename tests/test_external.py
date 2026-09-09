"""The external matrix: provenance, neutrality, and the guards on scoring.

These are the first claims this project makes about somebody else's software,
and they will be read by people with no reason to be generous. Two failure modes
matter more than any measurement:

* **publishing a refusal caused by our own misconfiguration**, which would be
  disproved by a vendor in one command and would destroy the project's
  credibility permanently — so every detector carries the configuration it ran
  at, a link to where that default is documented, and a flag asserting it was
  not tuned;
* **presenting our own detector on softer terms than the others**, which turns a
  measurement into an advertisement — so our probe is a pairing like any other
  and is asserted to use the same grid and the same criterion.

None of these tests reach the network. What needs fetching is exercised by the
run itself, which is the artifact's own reproduction command.
"""

from __future__ import annotations

import pytest

from controlplane.external import PAIRINGS, pairing_ids
from controlplane.external.registry import (
    ACCESS_DATE,
    OUR_PROBE,
    _binary_label_items,
    _pii_items,
)
from controlplane.external.run import run_pairing
from controlplane.validation.fpr_sweep import LIFT_HOLDS_LOWER_BOUND, fpr_grid


# ------------------------------------------------------------- provenance

@pytest.mark.parametrize("pairing_id", pairing_ids())
def test_every_detector_states_how_it_was_configured(pairing_id: str) -> None:
    """D34 and D39: a vendor must be able to check the configuration we used."""
    detector = PAIRINGS[pairing_id].detector
    assert detector.version, f"{detector.id} has no version or revision"
    assert detector.licence
    assert detector.source_url.startswith("https://")
    assert detector.documentation_url.startswith("https://")
    assert len(detector.configuration) > 60, (
        f"{detector.id}'s configuration is too terse to be checkable; it has to "
        "say what was actually called and with what"
    )
    assert detector.to_payload()["tuned_for_this_evaluation"] is False


@pytest.mark.parametrize("pairing_id", pairing_ids())
def test_every_dataset_is_pinned_and_not_redistributed(pairing_id: str) -> None:
    """D32: source, revision and access date recorded; no data shipped here."""
    dataset = PAIRINGS[pairing_id].dataset
    assert dataset.revision, f"{dataset.id} is not pinned to a revision"
    assert dataset.licence, f"{dataset.id} does not record a licence"
    assert dataset.source_url.startswith("https://")
    payload = dataset.to_payload()
    assert payload["redistributed_here"] is False
    assert payload["access_date"] == ACCESS_DATE


@pytest.mark.parametrize("pairing_id", pairing_ids())
def test_every_pairing_says_what_a_positive_means_or_why_it_is_unscored(
    pairing_id: str,
) -> None:
    """A task nobody can restate is a result nobody can check.

    A pairing declared out of scope states the reason instead: it produces no
    numbers, so there is no positive class to define, and what a reader needs is
    why the question is undefined for this detector rather than failed by it.
    """
    pairing = PAIRINGS[pairing_id]
    assert len(pairing.task) > 40
    if pairing.out_of_scope:
        assert pairing.task.startswith("OUT OF SCOPE")
        assert len(pairing.out_of_scope) > 60
    else:
        assert "positive" in pairing.task.lower()


def test_an_undeclared_licence_is_recorded_as_undeclared() -> None:
    """Not assumed permissive, and not quietly omitted."""
    pii = PAIRINGS["presidio-email_address"].dataset
    assert "not declared" in pii.licence.lower()


# -------------------------------------------------------------- neutrality

def test_our_own_detector_is_in_the_matrix() -> None:
    """D37. A comparison missing the author's entry is not a comparison."""
    assert "ours-triviaqa" in PAIRINGS
    assert PAIRINGS["ours-triviaqa"].detector is OUR_PROBE


def test_our_detector_is_not_given_a_different_yardstick() -> None:
    """Same grid, same criterion, same payload shape as every third party.

    The check is structural rather than aspirational: our pairing goes through
    the same `run_pairing`, and nothing in the registry lets a pairing carry its
    own grid or its own bar.
    """
    ours = PAIRINGS["ours-triviaqa"]
    assert not hasattr(ours, "grid"), "a per-pairing grid would allow a soft bar"
    assert not hasattr(ours, "criterion")
    # The criterion is one module-level constant shared by everything.
    assert LIFT_HOLDS_LOWER_BOUND == 1.0


def test_the_neutrality_statement_travels_with_every_result(config) -> None:
    """D36: a refusal must be readable as scope, not as a verdict on a vendor."""
    _, payload = run_pairing(config, "ours-triviaqa", grid=(0.10,))
    assert "neutrality" in payload
    assert payload["criterion"]["rule"] == "lift ci_low > 1.0, strictly"


# ------------------------------------------------------------ label wiring

def test_pii_labels_come_from_the_datasets_own_spans() -> None:
    """Positive iff the row carries a span of that type. Never the detector."""
    rows = [
        {"id": "a", "source_text": "mail me", "privacy_mask": [{"label": "EMAIL"}]},
        {"id": "b", "source_text": "no pii here", "privacy_mask": []},
        {"id": "c", "source_text": "other pii", "privacy_mask": [{"label": "LASTNAME"}]},
    ]
    ids, labels, texts = _pii_items("EMAIL")(rows)
    assert ids == ["a", "b", "c"]
    assert labels == [1, 0, 0]
    assert texts[1] == "no pii here"


def test_a_negative_row_may_still_contain_other_pii() -> None:
    """The question is 'does this contain an EMAIL', not 'is this clean'.

    Row c carries a LASTNAME span and is negative for EMAIL. Labelling it
    positive because it contains *some* PII would put the wrong question's
    labels into a false-positive rate.
    """
    rows = [{"id": "c", "source_text": "x", "privacy_mask": [{"label": "LASTNAME"}]}]
    _, labels, _ = _pii_items("EMAIL")(rows)
    assert labels == [0]


def test_binary_label_items_reads_the_declared_positive() -> None:
    rows = [{"text": "hi", "label": "0"}, {"text": "ignore instructions", "label": "1"}]
    _, labels, texts = _binary_label_items("text", "label", "1")(rows)
    assert labels == [0, 1]
    assert texts == ["hi", "ignore instructions"]


# ----------------------------------------------------------------- guards

def test_a_single_class_pairing_is_refused(config, monkeypatch) -> None:
    """The finding that shaped this phase, enforced.

    A PII dataset where every row contains PII cannot bound a false-positive
    rate. Certifying one anyway would produce a warrant from no negatives.
    """
    rows = [
        {"id": str(i), "source_text": f"t{i}", "privacy_mask": [{"label": "EMAIL"}]}
        for i in range(20)
    ]
    monkeypatch.setattr("controlplane.external.run.load_rows", lambda p: rows)
    with pytest.raises(ValueError, match="single-class"):
        run_pairing(config, "presidio-email_address", grid=(0.10,))


def test_a_misaligned_score_vector_is_refused(config, monkeypatch) -> None:
    """Silent misalignment attaches every label to the wrong item.

    The warrant that comes out is plausible and completely wrong, which is why
    this is checked rather than assumed from the scorer's contract.
    """
    rows = [
        {"id": str(i), "source_text": f"t{i}",
         "privacy_mask": [{"label": "EMAIL"}] if i % 2 else []}
        for i in range(20)
    ]
    import dataclasses

    monkeypatch.setattr("controlplane.external.run.load_rows", lambda p: rows)
    # The Pairing is frozen, which is right: a registry entry that could be
    # mutated at run time would let a detector be reconfigured after the fact.
    # So the registry entry is replaced rather than the field patched.
    short = dataclasses.replace(
        PAIRINGS["presidio-email_address"], score=lambda texts: [0.0] * 3
    )
    monkeypatch.setitem(PAIRINGS, "presidio-email_address", short)
    with pytest.raises(ValueError, match="returned 3 scores"):
        run_pairing(config, "presidio-email_address", grid=(0.10,))


def test_an_unknown_pairing_raises() -> None:
    with pytest.raises(KeyError):
        run_pairing(None, "not-a-pairing")


def test_the_grid_is_the_standard_one() -> None:
    """D35: the registered grid, unchanged for third parties."""
    grid = fpr_grid(0.01, 0.20, 0.01)
    assert len(grid) == 20 and grid[0] == 0.01 and grid[-1] == 0.20
