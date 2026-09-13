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

__all__ = [
    "DERIVED_CLAIMS",
    "INVARIANTS",
    "Invariant",
    "READ_ONLY_WITHOUT_DERIVATION",
    "SPEC_TEST_ALIASES",
]


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
            # The two surfaces a reader stops on, uncovered until DECISIONS 170.
            "tests/test_claims.py::test_every_recall_claim_travels_with_precision",
            "tests/test_matrix.py::test_a_valid_cell_carries_precision_beside_recall",
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


#: Public functions that return an interval, a bound, or a sample size, and
#: therefore must carry a ``Quantity:`` and a ``Propagation:`` line.
#:
#: ``CLAUDE.md``: *statistical claims carry their derivation, wherever they
#: appear. A sample size, interval or projection states the quantity being
#: estimated and the propagation used.* ``docs/TASKS.md`` Phase 12 repeats it as
#: an audit line. Nothing checked it until ``DECISIONS.md`` 163: 8 of 32
#: qualifying functions carried one.
#:
#: Entries are ``module path`` to ``function name``. The test reads the
#: docstring and fails if the pair is gone, so a derivation cannot vanish in a
#: tidy-up — which is the failure that already happened once, in
#: ``review.recall_sample_size``, and cost ``DECISIONS.md`` 147.
DERIVED_CLAIMS: tuple[tuple[str, str], ...] = (
    ("controlplane/economics/feasibility.py", "abstention_floor"),
    ("controlplane/economics/review.py", "recall_sample_size"),
    ("controlplane/economics/sizing.py", "negatives_for_detection"),
    ("controlplane/economics/sizing.py", "smallest_detectable_at"),
    ("controlplane/intake/certify.py", "certify_items"),
    ("controlplane/intake/recheck.py", "smallest_detectable_breach"),
    ("controlplane/sampling/estimator.py", "estimate_on_traffic"),
    ("controlplane/sampling/planning.py", "labels_for_prevalence"),
    ("controlplane/sampling/planning.py", "labels_for_recall"),
    ("controlplane/sampling/planning.py", "recall_sensitivity"),
    ("controlplane/sampling/agreement.py", "cohens_kappa"),
    ("controlplane/sampling/allocation.py", "design_effect"),
    ("controlplane/validation/calibration.py", "n_to_detect_deviation"),
    ("controlplane/validation/paired.py", "paired_bootstrap"),
    ("controlplane/validation/scorefree.py", "smallest_certifiable_budget"),
    ("controlplane/validation/scorefree.py", "tunability"),
    ("controlplane/validation/selection.py", "selection_aware_recall"),
)

#: Qualifying functions in read-only zones (``CLAUDE.md``, Read-only). Reported
#: rather than fixed, and listed here so the gap is a recorded number rather
#: than an absence.
#:
#: **OPEN — needs human review.** Four of these are the most-used estimators in
#: the repository, so the coverage figure in ``DECISIONS.md`` 163 understates
#: the gap in the places it matters most.
READ_ONLY_WITHOUT_DERIVATION: tuple[tuple[str, str], ...] = (
    ("controlplane/drift/certify.py", "certify_drift_response"),
    ("controlplane/drift/null_band.py", "iqr_ratio_power"),
    ("controlplane/drift/response.py", "can_certify"),
    ("controlplane/validation/stats.py", "auroc"),
    ("controlplane/validation/stats.py", "bootstrap_interval"),
    ("controlplane/validation/stats.py", "estimated"),
    ("controlplane/validation/stats.py", "bootstrap_seed_stability"),
    ("controlplane/validation/warrant_stats.py", "certify_fpr"),
)


#: ``SPEC.md`` §10 names eighteen tests. Thirteen exist under exactly those
#: names. These five do not, and in every case **the behaviour is tested under a
#: descriptive name** -- checked by reading the tests, not inferred from the
#: absence of a match. Stopping at the name check would have reported three
#: missing tests that are not missing (``DECISIONS.md`` 167).
#:
#: Each maps the spec's name to the tests that implement it. The test for this
#: table fails if a spec name has neither an exact match nor an alias whose
#: targets all exist, so the spec's test table cannot drift from the suite again.
SPEC_TEST_ALIASES: dict[str, tuple[str, ...]] = {
    "test_controls": (
        "tests/test_validation.py::test_all_five_controls_run_and_report_margins",
        "tests/test_validation.py::test_label_shuffle_catches_a_label_leaking_feature",
        "tests/test_validation.py::test_underpowered_negative_control_fails_rather_than_passing",
        "tests/test_validation.py::test_canary_control_fails_when_absent",
        "tests/test_validation.py::test_determinism_control_detects_a_wobble",
    ),
    "test_padding_equivalence": (
        "tests/test_validation.py::test_padding_control_rejects_the_deliberate_fault",
        "tests/test_validation.py::test_padding_control_fails_when_left_padding_does_not_match",
        "tests/test_extraction.py::test_assert_left_padding_refuses_right_padding",
    ),
    "test_policy_refusal": (
        "tests/test_policy.py::test_a_bundle_naming_an_unwarranted_point_fails_to_load",
        "tests/test_policy.py::test_a_bundle_relying_on_no_warrant_is_refused",
    ),
    "test_determinism": (
        "tests/test_validation.py::test_determinism_control_detects_a_wobble",
    ),
    "test_smoke": (
        "tests/test_smoke.py::test_smoke_validate_fixture",
        "tests/test_smoke.py::test_smoke_matrix",
    ),
}
