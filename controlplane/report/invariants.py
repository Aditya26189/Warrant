"""The nine invariants, and the test that enforces each one.

``docs/TASKS.md`` Phase 12's documentation audit opens with a line that has
never been discharged:

> *every invariant in* ``CLAUDE.md`` *enforced somewhere in code; name file and
> line*

"Enforced somewhere" is the kind of claim this repository has spent five phases
learning not to accept. All nine invariants are *mentioned* in tests — a grep
finds 106 references — but a mention is not an enforcement, and nothing checked
that the enforcing test still exists, still runs, or still asserts what it was
written to assert.

This is the register that makes it checkable, built the way
:mod:`controlplane.report.causal` already works for mechanism claims: every
invariant names the specific tests that would fail if it stopped being true, and
``tests/test_invariants.py`` verifies that each of those tests is collectible by
pytest. **A named test that has been renamed or deleted fails the register**,
which is the difference between a claim of coverage and coverage.

**What it deliberately does not do.** It cannot check that a test *actually*
enforces what it claims — that needs mutation testing, and the honest version of
it is the falsifier-by-deliberate-breakage that ``DECISIONS.md`` 142's causal
register uses and which does not generalise to nine invariants cheaply. What it
does is close the specific gap: an invariant whose enforcement quietly
disappeared would, until now, have left no trace at all.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Invariant", "INVARIANTS"]


@dataclass(frozen=True)
class Invariant:
    """One ``CLAUDE.md`` invariant and the tests that hold it in place.

    Attributes:
        number: Its number in ``CLAUDE.md``'s list, 1 to 9.
        headline: The first few words, as ``CLAUDE.md`` writes them. Matched
            against the file, so editing the contract without updating the
            register fails.
        enforced_by: Pytest node ids. Each must be collectible.
        breaks_as: What the world looks like if this stops being enforced —
            written so a reader can tell whether the tests named are plausibly
            the right ones.
    """

    number: int
    headline: str
    enforced_by: tuple[str, ...]
    breaks_as: str


INVARIANTS: tuple[Invariant, ...] = (
    Invariant(
        number=1,
        headline="Warrants are keyed by (detector, operating_point, eval_set)",
        enforced_by=(
            "tests/test_model.py::test_warrant_key_requires_all_three_elements",
            "tests/test_compose.py::test_bounds_are_keyed_by_detector_and_never_merged",
        ),
        breaks_as=(
            "a bound measured on one eval set is quoted for another, and an "
            "envelope violation stops invalidating every detector measured on "
            "that distribution"
        ),
    ),
    Invariant(
        number=2,
        headline="Three warrant states, three behaviours",
        enforced_by=(
            "tests/test_compose.py::test_two_unvalidated_detectors_do_not_add_up_to_one_validated_one",
            "tests/test_model.py::test_a_refused_warrant_cannot_be_relabelled_valid",
            "tests/test_drift_response.py::test_a_refused_warrant_does_not_climb_back_up",
        ),
        breaks_as=(
            "UNVALIDATED decays into VALID because nobody objected, which is "
            "the modal way a stale claim survives"
        ),
    ),
    Invariant(
        number=3,
        headline="Refusal has no override",
        enforced_by=(
            "tests/test_validation.py::test_no_override",
            "tests/test_demo.py::test_a_refused_warrant_claims_no_bounds_at_all",
        ),
        breaks_as=(
            "the product becomes theatre, and a reviewer looking for exactly "
            "this bypass finds it"
        ),
    ),
    Invariant(
        number=4,
        headline="No point estimate reaches a user",
        enforced_by=(
            "tests/test_claims.py::test_a_hand_edited_interval_is_caught",
            "tests/test_demo.py::test_the_banner_never_shows_a_rate_without_its_interval",
        ),
        breaks_as=(
            "a rate is quoted as though it were counted, and the reader cannot "
            "tell how much evidence is behind it"
        ),
    ),
    Invariant(
        number=5,
        headline="Precision and recall travel together",
        enforced_by=(
            "tests/test_model.py::test_blended_scores_are_refused_by_name[f1]",
            "tests/test_fpr_sweep.py::test_precision_and_recall_travel_together",
        ),
        breaks_as=(
            "a blended score fixes the exchange rate between a wasted review "
            "and a user acting on a wrong answer, silently"
        ),
    ),
    Invariant(
        number=6,
        headline="One declared workload",
        enforced_by=(
            "tests/test_sampling.py::test_no_scenario_mixing",
            "tests/test_economics.py::test_rates_from_the_wrong_workload_are_flagged_not_silently_negative",
        ),
        breaks_as=(
            "a flag rate from one scenario sits in a table beside a base rate "
            "from another, and the numbers survive everything except a "
            "reviewer with a calculator"
        ),
    ),
    Invariant(
        number=7,
        headline="Reviewers are blind",
        enforced_by=(
            "tests/test_sampling.py::test_blinding",
            "tests/test_sampling.py::test_the_queue_refuses_a_context_key_that_would_leak",
        ),
        breaks_as=(
            "anchoring across strata biases the estimator in the direction "
            "that flatters the detector, which is the direction nobody checks"
        ),
    ),
    Invariant(
        number=8,
        headline="Every number in a document is computed by code",
        enforced_by=(
            "tests/test_claims.py::test_the_readme_has_a_claim_table",
            "tests/test_readme_prose_numbers.py::test_every_headline_field_the_prose_uses_is_also_a_claim_row",
        ),
        breaks_as=(
            "a figure in the README drifts from the artifact behind it, and "
            "the document that exists to be checkable stops being checkable"
        ),
    ),
    Invariant(
        number=9,
        headline="Eval sets are frozen and content-hashed",
        enforced_by=(
            "tests/test_policy.py::test_the_content_hash_covers_the_rules_and_not_only_the_manifest",
            "tests/test_construction_identity.py::test_the_frozen_literals_are_still_exactly_the_two_that_were_frozen",
        ),
        breaks_as=(
            "a changed corpus inherits the warrants of the one it replaced, "
            "and selection leaks into the set that scores it"
        ),
    ),
)
