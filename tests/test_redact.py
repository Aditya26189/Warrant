"""The REDACT adapter: labels from their gold, and the mapping decisions.

This is the second body of work making claims about somebody else's software,
and the first making them about somebody else's *benchmark*. The failure that
matters is publishing a number that a mapping choice produced rather than a
detector — so the mapping is pinned by tests and the two decisions that shape a
result are asserted explicitly.

No network. The corpus is fetched at run time by the artifact's own reproduction
command; everything checkable without it is checked here.
"""

from __future__ import annotations

import pytest

from controlplane.external.redact import (
    LANGUAGE_INDEPENDENT,
    PRESIDIO_MAPPING,
    _unique_id,
    pooling_check,
    redact_high_tier_items,
    redact_items,
)


def _row(record_id, types=(), tiers=None, language="EN", text="t", forms=None):
    tiers, forms = tiers or {}, forms or {}
    return {
        "record_id": record_id,
        "text": text,
        "axes": {"language": language},
        "entities": [
            {
                "entity_type": t,
                "sensitivity_tier": tiers.get(t, "MEDIUM"),
                "disclosure_form": forms.get(t, "complete"),
            }
            for t in types
        ],
    }


# ------------------------------------------------------------- the mapping

def test_date_of_birth_is_deliberately_unmapped() -> None:
    """Presidio's DATE_TIME fires on any date.

    Scoring it against a date-of-birth label would count every delivery date and
    every ticket timestamp as a true positive of a different question, and would
    make the detector look good at something it was never asked.
    """
    assert "Date_of_Birth" not in PRESIDIO_MAPPING
    assert "DATE_TIME" not in {e for v in PRESIDIO_MAPPING.values() for e in v}


def test_national_id_and_passport_map_to_us_only_recognizers() -> None:
    """The scope mismatch is declared in the mapping, before any run.

    REDACT's catalog spans 40+ national systems including Indian Aadhaar;
    Presidio ships US_SSN, US_ITIN and US_PASSPORT. A low recall here is a
    statement about coverage, and the artifact has to say so rather than let it
    read as a defect.
    """
    assert PRESIDIO_MAPPING["National_Identification_Number"] == ("US_SSN", "US_ITIN")
    assert PRESIDIO_MAPPING["Passport_Number"] == ("US_PASSPORT",)


def test_only_regex_recognizers_may_be_pooled_across_languages() -> None:
    """Pooling 25 languages under an English NLP engine is the confound.

    PERSON is spaCy NER, so pooling it would measure the language mismatch.
    PHONE_NUMBER takes region hints and is excluded for the same reason.
    """
    assert "Full_Name" not in LANGUAGE_INDEPENDENT
    assert "Telephone_Numbers_Personal" not in LANGUAGE_INDEPENDENT
    assert "Telephone_Numbers_Work" not in LANGUAGE_INDEPENDENT
    for pooled in LANGUAGE_INDEPENDENT:
        assert pooled in PRESIDIO_MAPPING


# ----------------------------------------------------- the id collision

def test_colliding_record_ids_are_disambiguated_not_dropped() -> None:
    """REDACT's locked split has 944 distinct record_ids for 1,000 records.

    The colliding records are different documents, not duplicates, so they are
    independent items with a clashing label. Position disambiguates and the
    original id stays visible; discarding them would throw away 55 records, and
    passing them through would trip the sweep's independence guard for the wrong
    reason.
    """
    rows = [_row(1636, text="first"), _row(1636, text="second")]
    ids, _, texts = redact_items("Full_Name")(rows)
    assert len(set(ids)) == 2, "colliding ids were not disambiguated"
    assert all(str(1636) in i for i in ids), "the original record_id was lost"
    assert texts == ["first", "second"]


def test_unique_id_keeps_the_original_visible() -> None:
    assert _unique_id({"record_id": 42}, 7) == "42#7"


# ------------------------------------------- partial disclosure, the correction

def test_a_record_whose_only_span_is_partial_is_excluded_not_scored() -> None:
    """The correction that mattered, pinned.

    REDACT annotates Credit_Card_Numbers at 82.6% partial — 104 of 132 gold
    spans are four-digit last-four fragments. Counting those as positives
    measured Presidio at recall 0.0935 and produced a confident wrong
    explanation about checksums. Presidio's recognizer is built for full card
    numbers and correctly declines to call four digits a card.

    Scoring such a record as a negative is equally wrong: it does contain card
    information, so a detector that fired would be penalised for being right.
    The only defensible treatment is to drop it.
    """
    rows = [
        _row(1, ("Credit_Card_Numbers",), forms={"Credit_Card_Numbers": "complete"}),
        _row(2, ("Credit_Card_Numbers",), forms={"Credit_Card_Numbers": "partial"}),
        _row(3, ()),
    ]
    ids, labels, _ = redact_items("Credit_Card_Numbers")(rows)
    assert labels == [1, 0], "the partial-only record was scored instead of dropped"
    assert len(ids) == 2
    assert "2#1" not in ids


def test_an_obfuscated_only_record_is_excluded_too() -> None:
    rows = [_row(1, ("Credit_Card_Numbers",), forms={"Credit_Card_Numbers": "obfuscated"})]
    ids, labels, _ = redact_items("Credit_Card_Numbers")(rows)
    assert ids == [] and labels == []


def test_a_record_with_both_forms_counts_as_positive() -> None:
    """A complete span present means the detector can be asked about it."""
    row = _row(1, ("Credit_Card_Numbers",))
    row["entities"].append(
        {"entity_type": "Credit_Card_Numbers", "sensitivity_tier": "HIGH",
         "disclosure_form": "partial"}
    )
    _, labels, _ = redact_items("Credit_Card_Numbers")(rows=[row])
    assert labels == [1]


def test_the_uncorrected_construction_is_still_reachable() -> None:
    """So the original number can be reproduced rather than taken on trust."""
    rows = [_row(2, ("Credit_Card_Numbers",), forms={"Credit_Card_Numbers": "partial"})]
    _, labels, _ = redact_items("Credit_Card_Numbers", complete_only=False)(rows)
    assert labels == [1]


# ------------------------------------------------------------- out of scope

def test_the_three_undefined_tasks_carry_no_numbers() -> None:
    """A task the detector does not claim is undefined for it, not failed by it.

    `presidio-analyzer | HIGH-sensitivity | 0.000` gets screenshotted without
    the paragraph that qualifies it, so these carry a reason and no recall.
    """
    from controlplane.external import PAIRINGS

    for name in ("redact-national-id", "redact-passport", "redact-high-tier"):
        pairing = PAIRINGS[name]
        assert pairing.out_of_scope, f"{name} must declare why it is not scored"
        assert len(pairing.out_of_scope) > 60
        assert pairing.task.startswith("OUT OF SCOPE")


def test_an_out_of_scope_pairing_refuses_to_be_scored(config) -> None:
    from controlplane.external.run import run_pairing

    with pytest.raises(ValueError, match="out of scope"):
        run_pairing(config, "redact-high-tier", grid=(0.10,))


# ------------------------------------------------------------ the labels

def test_labels_come_from_redacts_gold_annotations() -> None:
    rows = [
        _row(1, ("Work_Email_Address",)),
        _row(2, ("Full_Name",)),
        _row(3, ()),
    ]
    _, labels, _ = redact_items("Personal_Email_Address", "Work_Email_Address")(rows)
    assert labels == [1, 0, 0]


def test_a_negative_record_may_carry_other_pii() -> None:
    """The question is "does this contain an email", not "is this clean"."""
    rows = [_row(1, ("Full_Name", "Passport_Number"))]
    _, labels, _ = redact_items("Work_Email_Address")(rows)
    assert labels == [0]


def test_several_redact_types_may_share_one_presidio_entity() -> None:
    """Both email fields map to EMAIL_ADDRESS, so the task spans both.

    Running them separately would score a detector that cannot tell them apart
    against a distinction it never claimed.
    """
    rows = [_row(1, ("Personal_Email_Address",)), _row(2, ("Work_Email_Address",))]
    _, labels, _ = redact_items("Personal_Email_Address", "Work_Email_Address")(rows)
    assert labels == [1, 1]


# ------------------------------------------------------- the stratified task

def test_high_tier_is_restricted_to_types_the_detector_claims() -> None:
    """Otherwise the result is a scope mismatch dressed up as a failure.

    A record whose only HIGH-sensitivity entity is a type Presidio does not
    claim must not count as a positive it missed.
    """
    claimed = ("Credit_Card_Numbers",)
    rows = [
        _row(1, ("Credit_Card_Numbers",), {"Credit_Card_Numbers": "HIGH"}),
        _row(2, ("Religion",), {"Religion": "HIGH"}),          # HIGH, not claimed
        _row(3, ("Credit_Card_Numbers",), {"Credit_Card_Numbers": "LOW"}),
    ]
    _, labels, _ = redact_high_tier_items(claimed)(rows)
    assert labels == [1, 0, 0]


# ---------------------------------------------------- the pooling assumption

def test_the_pooling_assumption_is_measured_rather_than_asserted() -> None:
    """Pooling is only sound if the recognizer behaves the same off English.

    Reporting the two flag rates side by side is what makes that checkable by a
    reader instead of taken on the module's word.
    """
    rows = [_row(i, language="EN") for i in range(4)] + [
        _row(i, language="JA") for i in range(4, 10)
    ]
    scores = [1.0, 1.0, 0.0, 0.0] + [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    out = pooling_check(rows, scores, threshold=0.5)
    assert out["n_english"] == 4 and out["n_non_english"] == 6
    assert out["english_flag_rate"] == pytest.approx(0.5)
    assert out["non_english_flag_rate"] == pytest.approx(1 / 6)


def test_pooling_check_handles_an_all_english_set() -> None:
    rows = [_row(i, language="EN") for i in range(3)]
    out = pooling_check(rows, [0.0, 1.0, 1.0], threshold=0.5)
    assert out["non_english_flag_rate"] is None
    assert out["english_flag_rate"] == pytest.approx(2 / 3)
