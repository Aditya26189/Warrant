# CASES.md — the case matrix

Every behaviour this system claims, the test that covers it, and the artifact
that demonstrates it. "All the cases" is a table you can read, not a test count.

`tests/test_cases_matrix.py` fails if any test named here does not exist in the
suite, so this table cannot drift from the code.

**Artifact column.** `—` means the case is a code invariant with no measured
artifact behind it: it is enforced by construction, and the test *is* the
evidence. That is not a weaker guarantee, but it is a different one, and the
distinction is worth reading.

---

## 1. Warrant states

A warrant is a time-bounded, evidence-backed statement about what a detector's
score is worth **on one envelope**. Three states, three conditions.

| case | expected behaviour | test | artifact |
|---|---|---|---|
| **VALID** — all five controls pass, AUROC lower CI > 0.55, lift lower CI > 1.0, n ≥ 200 | warrant issued with measured bounds and a 24h TTL | `test_a_useful_detector_still_issues` | `results/validation-T1-last_token.json` |
| **REFUSED** — any criterion fails | no bounds are claimed at all, and the reason names every failed criterion, the measured value and the requirement | `test_a_refused_warrant_claims_no_bounds_at_all` | `results/transfer-T1-mean_pool.json` |
| **REFUSED** cannot be laundered | a refusal cannot be relabelled VALID by any downstream caller | `test_a_refused_warrant_cannot_be_relabelled_valid` | — |
| **UNVALIDATED** — this (detector, envelope) pair was never measured | a matrix cell state, never a warrant record's status; claims nothing and outranks nothing | `test_an_unvalidated_cell_never_outranks_a_measured_one` | `results/warrant_matrix.json` (39 of 56 cells) |
| REFUSED is not UNVALIDATED | a measured refusal and an absent measurement do not share a message | `test_refused_and_unvalidated_do_not_share_a_message` | — |
| **STALE** — TTL expired | reports stale rather than valid; bounds widen about the point estimate | `test_an_expired_valid_warrant_reports_stale` | — |
| a refusal names the build it refused | `status_reason` opens with `[detector_id==version]`, so the claim is about one release | `test_a_refusal_names_the_build_it_refused` | `results/detectors.json` |

## 2. Composition — two warranted detectors, one decision (DECISIONS 088)

| case | expected behaviour | test | artifact |
|---|---|---|---|
| **VALID / VALID, both flag** | the more restrictive action wins; bounds stay keyed per detector and are never merged | `test_case_1_both_flag_takes_the_more_restrictive_action` | — |
| VALID / VALID agreeing is not a vote | agreement does not strengthen either bound | `test_case_1_is_not_a_vote` | — |
| **VALID / VALID, disagreeing** | the flagging detector's action is taken; the silent one does not veto it | `test_case_2_disagreement_takes_the_flagging_detectors_action` | — |
| VALID / VALID, neither fires | ALLOW, still citing both warrants | `test_case_2_with_nothing_firing_allows_and_still_cites_both` | — |
| **VALID / REFUSED** | the refusal is not inherited by the valid detector; what was not checked is recorded | `test_case_3_refusal_is_not_inherited` | — |
| VALID / REFUSED records the gap | what was not checked appears on the decision | `test_case_3_records_what_was_not_checked` | — |
| VALID / REFUSED does not enqueue | a refused detector's output is not queued for review as though it meant something | `test_case_3_does_not_enqueue_a_refused_detector` | — |
| **VALID / UNVALIDATED, unvalidated fires** | triggers the profile default rather than its own action | `test_case_4_an_unvalidated_detector_that_fires_triggers_the_default` | — |
| VALID / UNVALIDATED, unvalidated silent | silence from an unmeasured detector is not evidence; no default triggered | `test_case_4_silent_unvalidated_detector_does_not_trigger_the_default` | — |
| case 4 is not case 3 | an unmeasured detector and a refused one take different paths | `test_case_4_is_distinct_from_case_3` | — |
| two UNVALIDATED detectors | do not add up to one validated one | `test_two_unvalidated_detectors_do_not_add_up_to_one_validated_one` | — |
| composing an empty set | a caller error, not a conservative outcome | `test_composing_nothing_is_a_caller_error_not_a_conservative_outcome` | — |
| findings survive an absent warrant | the finding is still recorded; only the claim about it is withheld | `test_findings_survive_even_when_no_warrant_backs_them` | — |

## 3. The three policy profiles

Three points on **one measured ROC**, not three invented thresholds. Same
detector, same envelope; only `target_flag_rate` moves. Selected on validation,
reported on test. Measured on `triviaqa-2400-t960`, n = 960, base rate 0.4510.

| profile | operating point | floor | measured recall | measured `f` | on drift | test | artifact |
|---|---|---|---|---|---|---|---|
| `customer_support` | `P-customer-support` @ 0.8909 | recall ≥ 0.10, FPR ≤ 0.02 | 0.2171 [0.1800, 0.2564] | 0.1062 | **REFUSE** — the economics are sized on the flag rate | `test_a_profile_that_refuses_drift_does_not_load_against_a_drifted_budget` | `results/policy-triviaqa-2400-t960.json` |
| `internal_knowledge` | `P-internal-knowledge` @ 0.7983 | recall ≥ 0.25, FPR ≤ 0.05 | 0.3603 [0.3173, 0.4063] | 0.1865 | **WIDEN_BUDGET** — quotable if quoted as measured | `test_a_profile_that_widens_quotes_the_measured_rate_not_the_declared_one` | `results/policy-triviaqa-2400-t960.json` |
| `decision_support` | `P-decision-support` @ 0.4656 | recall ≥ 0.50, FPR ≤ 0.10 | 0.7367 [0.6974, 0.7783] | 0.4677 | **IGNORE** — declared, so "considered and does not apply" is visible | `test_a_profile_that_ignores_drift_records_that_it_considered_it` | `results/policy-triviaqa-2400-t960.json` |

| case | expected behaviour | test | artifact |
|---|---|---|---|
| a profile compares against the interval, not the point | a point estimate above the floor whose lower bound is below it does not clear it | `test_profile_compares_against_the_interval_bound_not_the_point` | — |
| bounds fall below the floor | the profile suspends rather than degrading quietly | `test_a_profile_suspends_when_bounds_fall_below_its_minimum` | — |
| an envelope with no recall claim | refused; a floor cannot be checked against a bound that does not exist | `test_profile_refuses_an_envelope_with_no_recall_claim` | — |

## 4. The tier curve

| tier | what it reads | status | test | artifact |
|---|---|---|---|---|
| **T1 — activations** | last-token residual stream, question-time | **measured**, three aggregations | `test_the_tier_decides_and_not_the_detector_name` | `results/tier_ladder.json`, `results/validation-T1-last_token.json` |
| **T2 — logprobs** | generation logprobs | **fixture only — never measured on a language model** | `test_results_refuses_to_print_a_synthetic_number` | `results/fixtures/validation-T2-logprob-fixture.json` |
| **T3 — text only** | response text, no model internals | **measured** for the PII detectors; the judge rung is a fixture | `test_model_agnostic_tiers_survive_but_are_not_endorsed` | `results/detectors.json`, `results/fixtures/validation-T3-judge-fixture.json` |
| a tier is decided by access, not by name | renaming a detector cannot promote it to a tier it does not have | `test_the_tier_decides_and_not_the_detector_name` | — |

## 5. Detector refusals — the PII finding

Measured on `hinglish-pii-200` (n = 200, base rate 0.51) with
`presidio-analyzer==2.2.364`. **The version is part of the claim.**

| configuration | measured recall | status | refusal reason | test | artifact |
|---|---|---|---|---|---|
| `presidio-stock` | 0.1176 [0.0500, 0.2000] | **REFUSED** | canary recall 0.2000 vs required 1.0; AUROC lower CI 0.4456 vs required > 0.55; lift lower CI 0.454 crosses 1.0 | `test_stock_registers_no_indian_recognizer` | `results/detectors.json` |
| `presidio-enabled` | 0.2843 [0.2075, 0.3810] | **REFUSED** | canary recall 0.6000 vs required 1.0; AUROC lower CI 0.5409 vs required > 0.55 | `test_enabling_adds_exactly_the_shipped_indian_recognizers` | `results/detectors.json` |
| `presidio-enabled_plus_custom` | 0.6176 [0.5185, 0.7128] | VALID | — | `test_more_recognizers_never_lowers_canary_recall` | `results/detectors.json` |
| `pii-reference` (ours) | 0.7941 [0.6981, 0.8846] | VALID | — | `test_a_configuration_that_alarms_on_its_own_reference_is_refused` | `results/validation-pii-reference-hinglish-pii-200.json` |

| case | expected behaviour | test | artifact |
|---|---|---|---|
| no shipped configuration recognises UPI VPA or IFSC | the specific claim, checked against the installed library rather than repeated | `test_no_shipped_configuration_recognises_upi_vpa_or_ifsc` | `results/detectors.json` |
| the pin is the claim | a silent Presidio upgrade fails the suite instead of quietly invalidating a published refusal | `test_the_installed_presidio_is_the_one_the_claim_was_measured_on` | `requirements.txt` |
| out of sample | every refusal reproduces on `hinglish-pii-200b`: 0.1471 / 0.3137 / 0.6471 / 0.8333 | `test_the_holdout_is_a_different_envelope_with_the_same_shape` | `results/holdout/detectors.json` |
| the eval-set identifiers are not the confound | the finding is about recognisers, not about our synthetic identifiers | `test_the_fixture_identifiers_are_not_the_confound` | `evalsets/hinglish-pii-200.json` |
| zero false positives on hard negatives | `pii-reference` FPR 0.0000 [0.0000, 0.0183] on a single-class benign set | `test_a_configuration_that_alarms_on_its_own_reference_is_refused` | `results/validation-pii-reference-hard-negatives-200.json` |

## 6. Drift, revocation, downgrade, refusal

The centrepiece. One shift, three detectors, and the matrix names the one that
survives it.

| case | expected behaviour | test | artifact |
|---|---|---|---|
| envelope violation detected | PSI past the significant boundary revokes (MMD is not built, `DECISIONS.md` 172) | `test_the_significant_boundary_revokes` | `results/warrant_matrix.json` |
| a real distribution shift | revokes rather than degrading quietly | `test_a_real_shift_revokes` | `results/warrant_matrix.json` |
| insufficient data | decides nothing | `test_insufficient_data_decides_nothing` | — |
| insufficient data after a revocation | does not lift it | `test_insufficient_data_does_not_lift_a_revoked_warrant` | — |
| revocation to tier downgrade | routing adopts the replacement detector's bounds, never the revoked one's | `test_a_revocation_routes_and_adopts_the_new_bounds` | `results/warrant_matrix.json` |
| the certificate cites the replacement | never the revoked warrant | `test_a_routed_certificate_cites_the_replacement_not_the_revoked` | — |
| nowhere to route | claims nothing rather than falling back silently | `test_an_unrouted_revocation_claims_nothing` | — |
| an unrouted certificate | cites nothing and claims nothing | `test_an_unrouted_certificate_cites_nothing_and_claims_nothing` | — |
| **refusal to certify decision-support** | when nothing holds a warrant at that floor, the gate refuses and enqueues | `test_the_gate_refuses_and_enqueues_when_nothing_holds_a_warrant` | — |
| a refused warrant does not climb back | no later window promotes it | `test_a_refused_warrant_does_not_climb_back_up` | — |
| an unknown envelope | raises rather than reading as an absence | `test_an_unknown_envelope_raises_rather_than_reading_as_an_absence` | — |
| a model version change | an activation warrant on a changed model is revoked | `test_an_activation_warrant_on_a_changed_model_is_revoked` | — |
| **measured** — `T1-mean_pool` under long-context shift | AUROC 0.5015 [0.4546, 0.5479], chance. REFUSED; flags nothing, so the dashboard reads clean | `test_transfer_refuses_a_mismatched_cache` | `results/transfer-T1-mean_pool.json` |
| **measured** — `T1-max_rolling_means` under the same shift | AUROC 0.5553 [0.5105, 0.6015], flags 54% of the stream. REFUSED | `test_the_significant_boundary_revokes` | `results/transfer-T1-max_rolling_means.json` |
| **measured** — `T1-last_token` under the same shift | AUROC 0.8256 to 0.8135 [0.7797, 0.8447]. Keeps its warrant | `test_a_valid_envelope_consults_nothing` | `results/transfer-T1-last_token.json` |

## 7. Controls — including the one that must fail

Five controls run on every validation. A failed control refuses the warrant and
nothing promotes it back.

| control | expected behaviour | test | artifact |
|---|---|---|---|
| **padding_fault** | the deliberately right-padded variant must be **rejected**. If it is accepted, the control fails | `test_padding_control_fails_when_right_padding_would_be_accepted` | `results/validation-T1-last_token.json` |
| left padding asserted at load | right padding raises rather than producing a plausible 0.5 AUROC | `test_assert_left_padding_refuses_right_padding` | — |
| left padding accepted | the correct case still passes | `test_assert_left_padding_accepts_left` | — |
| padding evidence required | a control with no evidence behind it fails rather than passing | `test_padding_control_fails_without_evidence` | — |
| **label_shuffle** | AUROC must land in the measured null band; signal surviving permutation fails | `test_all_five_controls_run_and_report_margins` | `results/validation-T1-last_token.json` |
| **null_feature** | a probe on noise must score in-band | `test_all_five_controls_run_and_report_margins` | `results/validation-T1-last_token.json` |
| **canary** | recall must be exactly 1.0 on a deliberately easy set | `test_canary_control_requires_perfect_recall` | `results/detectors.json` |
| canary absent | fails; an absent control is not a passed one | `test_canary_control_fails_when_absent` | — |
| **determinism** | two runs at one seed are bit-identical | `test_all_five_controls_run_and_report_margins` | `results/validation-T1-last_token.json` |
| a control cannot report a pass it did not achieve | enforced at construction | `test_a_control_cannot_report_a_pass_it_did_not_achieve` | — |
| a failed control cannot be promoted afterwards | no argument anywhere lifts it | `test_a_failed_control_cannot_be_promoted_after_the_fact` | — |
| an applicable failed control | still refuses, whatever else passed | `test_an_applicable_failed_control_still_refuses` | — |

## 8. Guard rejections

Where the system refuses to proceed rather than producing a number that would
look fine.

| case | expected behaviour | test | artifact |
|---|---|---|---|
| **eval-set category mismatch** — a PII detector measured against hallucination labels | raises; recall against labels that mean something else is not recall | `test_a_pii_detector_cannot_be_warranted_against_hallucination_labels` | — |
| the mirror case — a hallucination detector against PII labels | raises | `test_a_hallucination_detector_cannot_be_warranted_against_pii_labels` | — |
| a detector declaring no category | allowed through; the guard refuses mismatches, not silence | `test_a_detector_declaring_no_category_is_allowed_through` | — |
| **override record missing a stratum** | cannot be constructed; a record without its stratum and draw probability is unusable for estimation | `test_a_record_without_a_stratum_cannot_be_built` | — |
| **unclassified detector entity** | raises rather than being silently filtered out of the count | `test_an_unclassified_entity_raises_rather_than_being_dropped` | — |
| every entity the shipped sets provoke is classified | no entity reaches scoring unclassified | `test_every_entity_the_shipped_sets_provoke_is_classified` | — |
| a bundle naming an unwarranted operating point | fails to load; fail-closed, not a warning | `test_a_bundle_naming_an_unwarranted_point_fails_to_load` | `policies/customer_support/bundle.yaml` |
| a bundle relying on no warrant at all | refused | `test_a_bundle_relying_on_no_warrant_is_refused` | — |
| a declared FPR ceiling with nothing behind it | refused rather than assumed met | `test_a_declared_fpr_ceiling_with_no_measurement_behind_it_is_refused` | — |
| a cache from a different eval set | refused, and the error names the row | `test_a_cache_from_a_different_set_is_refused_and_names_the_row` | — |
| a cache whose hash does not match | refused | `test_cache_load_refuses_a_hash_mismatch` | — |
| a cache of the wrong length | refused | `test_a_cache_of_the_wrong_length_is_refused` | — |
| a fixture cell | never reports a number, however internally valid | `test_results_refuses_to_print_a_synthetic_number` | `results/RESULTS.md` |
| a blended F1 anywhere | the metric name is refused at construction | `test_blended_scores_are_refused_by_name` | — |

## 9. Reproduction

| case | expected behaviour | test | artifact |
|---|---|---|---|
| the notebook is generated, never hand-edited | a hand-edited notebook fails the suite | `test_notebook_is_generated_from_its_script` | `notebooks/run_on_kaggle.ipynb` |
| every README claim resolves | each number in the claim table matches a field in `results/` at the stated precision | `test_every_readme_claim_resolves` | `README.md` |
| every metric recomputes from frozen scores | the committed numbers follow from the committed per-item scores, on a clone with no activation cache | `test_every_committed_metrics_block_recomputes` | `results/scores/` |
| an edited score file is refused | the arrays are content-hashed, so tampering cannot pass as evidence | `test_an_edited_score_file_is_refused_on_load` | `results/scores/` |
| a flipped label fails verification | the check compares what it claims to compare | `test_a_tampered_score_set_fails_verification` | — |
| missing scores are a defect, not a skip | unlike the activation cache, they are committed evidence | `test_an_absent_scores_directory_is_a_defect_not_a_skip` | — |
| `construction` carries no code identity | a module path inside a content hash couples every warrant to the package layout | `test_construction_records_inputs_not_code_identity` | — |
| the rule fires on a new occurrence | freezing two sites is a patch; this makes the class non-recurring | `test_a_new_generator_string_is_caught` | — |
| the frozen literals have not moved | correcting one would orphan every fixture warrant | `test_the_frozen_literals_are_still_exactly_the_two_that_were_frozen` | `results/fixtures/` |
| the abstention floor matches an optimal selector | the closed form is checked against an exhaustive simulation, not against itself | `test_the_floor_matches_an_exhaustive_perfect_selector` | `results/feasibility.json` |
| no operating point beats the floor | an efficiency below 1.0 would mean the bound is wrong | `test_efficiency_is_never_below_one_for_an_achievable_point` | `results/feasibility.json` |
| rates from different envelopes are refused | catching more errors than were flagged cannot describe one distribution | `test_catching_more_errors_than_were_flagged_is_refused` | — |
| derived figures name their declared inputs | a number from a declared workload is not a measurement, and must say so | `test_review_volume_labels_which_inputs_were_declared` | `results/feasibility.json` |
| the artifact states what it does not derive | the unbuilt price list travels with the numbers | `test_the_artifact_states_what_it_does_not_derive` | `results/feasibility.json` |
| verify emits a machine-readable tier summary | a gate parsing prose depends on output length; a contract does not | `test_each_verify_tier_gets_its_own_row` | `results/clean_clone.json` |
| prose alone does not satisfy the gate | the regression guard: output saying the right thing in words is rejected without the contract line | `test_prose_alone_is_not_enough` | — |
| a tier absent from the summary | reported skipped, never passed — absence means unknown | `test_a_tier_missing_from_the_summary_is_not_counted_as_a_pass` | — |
| a drifted tier fails the gate | SKIPPED is tolerable, DRIFT is not | `test_a_drifted_tier_fails_the_gate` | — |
| a failed cleanup is reported | an operation reporting success without completing is the same failure one level down | `test_a_failed_cleanup_is_reported_rather_than_swallowed` | `results/clean_clone.json` |
| every case here has a covering test | this table cannot drift from the suite | `test_every_case_names_a_real_test` | — |
| the scripts are wired together | each stage runs end to end in a subprocess | `test_every_script_has_a_smoke_test` | — |

## 10. The banking pilot (`DECISIONS.md` 090 corrected, 101)

Not yet measured. The prompts are frozen; correctness is judged on the GPU
pass and nothing here reports a number about the probe.

| case | expected behaviour | test | artifact |
|---|---|---|---|
| correctness is measured, never authored | the draft has no label field at all, so a placeholder cannot exist | `test_labels_are_absent_because_correctness_is_measured` | `evalsets/banking-dual-24.draft.json` |
| the frame is held fixed within a question | the two identifier states differ only by the inserted clause | `test_the_two_states_differ_only_by_the_identifier_clause` | `evalsets/banking-dual-24.draft.json` |
| a frame that moves with the identifier is refused | otherwise the identifier axis measures authorship | `test_a_frame_that_moves_with_the_identifier_is_refused` | — |
| the identifier matches what its clause says | a clause reading "registered number" must not carry an Aadhaar | `test_the_identifier_kind_matches_what_the_clause_says` | — |
| every gold answer carries source and check-date | the one artifact class that previously had no provenance | `test_every_gold_answer_carries_its_source_and_date` | `evalsets/banking-dual-24.draft.json` |
| slow-moving facts preferred over rates | structural rules move over years, thresholds over months | `test_slow_moving_facts_are_preferred_over_fast_ones` | — |
| both ends of difficulty are represented | 101's band tests construction only if the span was deliberate | `test_both_ends_of_the_difficulty_range_are_represented` | — |
| the label can contradict the authored expectation | proves the expectation never drives a label | `test_the_measured_label_can_contradict_the_authored_expectation` | — |
| a single-class result raises | every answer correct means the set measures nothing | `test_a_single_class_result_raises_rather_than_being_reported` | — |
| the wrong-count is over questions, not items | 101's band is derived for 12 clusters, so it is counted on 12 | `test_the_wrong_count_is_over_questions_not_items` | — |
| the labelled set carries the draft hash | the prompts scored are provably the prompts frozen | `test_the_labelled_set_carries_the_draft_hash` | — |
| the draft is reproducible at a seed | and the questions themselves do not depend on it | `test_the_draft_is_reproducible_at_a_seed` | `results/pilot_envelope.json` |
| a set outside the band is a construction defect | too easy and too hard both mean off-regime | `test_a_set_outside_the_band_is_a_construction_defect` | — |
| saturation is the only branch that costs the retry | the separation 101 exists to enforce | `test_saturation_is_the_only_branch_that_costs_the_retry` | — |
| healthy spread + low AUROC is a result, not a retry | re-authoring there is tuning the set until the detector passes | `test_a_healthy_spread_with_a_low_auroc_is_a_result_not_a_retry` | — |
| the band is checked before the spread | a saturated IQR on an off-regime set is not saturation | `test_the_band_is_checked_before_the_spread` | — |
| the spread is checked before the AUROC | a low AUROC on off-distribution activations is not a probe finding | `test_the_spread_is_checked_before_the_auroc` | — |

## 11. The customer path: certify

What `warrant certify` must do with a file nobody here has seen. The procedure is
[INPUT.md](INPUT.md); the derivations are [METHODS.md](METHODS.md) §12–13.

| case | expected behaviour | test | artifact |
|---|---|---|---|
| a file that breaks the contract | exits 2 and says why; nothing is certified or written | `test_a_bad_file_exits_two_and_says_why` | — |
| a non-finite score | refused, never dropped | `test_a_non_finite_score_is_refused_not_dropped` | — |
| an empty cell | never filled in | `test_an_empty_cell_is_never_filled_in` | — |
| **too few clean negatives** | a refusal, not an error | `test_insufficient_evidence_is_a_refusal` | `examples/refuses.csv` |
| the refusing example | refuses **and exits 0** | `test_the_refusing_example_refuses_and_exits_zero` | `examples/refuses.csv` |
| the same data at a looser budget | certifies: the refusal was about evidence, not the detector | `test_the_refusing_example_certifies_at_a_looser_budget` | — |
| `--require-warrant` | changes only the exit code, and still says why | `test_require_warrant_flips_the_exit_code_and_still_says_why` | — |
| a certified result | carries an interval on every rate | `test_a_certified_result_carries_intervals_on_every_rate` | — |
| the certified bound | is respected on the negatives supplied | `test_the_bound_is_respected_on_the_supplied_negatives` | — |
| **unequal groups** | refused, because a cluster-level bound would be anticonservative | `test_unequal_groups_are_refused_rather_than_certified_anticonservatively` | — |
| groups | change the unit of inference | `test_groups_change_the_unit_of_inference` | — |
| the frontier on a grouped file | every row matches what `certify` would do | `test_every_frontier_row_matches_certify` | — |
| **a budget picked off the frontier** | certified at the frontier row's level, with its threshold | `test_the_picked_warrant_carries_the_frontier_rows_threshold` | `results/frontier_selection/selection.json` |
| a pick at the wrong level | refused | `test_a_selection_at_the_wrong_level_is_refused` | — |
| a plain certify beside a frontier record | unchanged, but prints a notice | `test_the_default_is_unchanged_but_notices_the_frontier` | — |

## 12. Rechecking a warrant

| case | expected behaviour | test | artifact |
|---|---|---|---|
| a stable world | keeps its warrant | `test_a_stable_world_keeps_its_warrant` | — |
| **a broken bound** | revokes | `test_a_broken_bound_revokes` | — |
| revocation turns on the lower bound | not on failing to re-prove the promise | `test_the_lower_bound_is_the_one_recheck_revokes_on` | — |
| no negatives in the new file | UNVALIDATED, never VALID | `test_no_negatives_is_untestable_not_valid` | — |
| **the dead zone** | every verdict states its detection floor | `test_the_dead_zone_is_stated_with_every_verdict` | — |
| the two failures | the summary keeps a broken bound and a moved distribution apart | `test_the_summary_keeps_the_two_failures_apart` | — |
| PSI | judged against this file's own noise | `test_psi_is_judged_against_this_files_own_noise` | — |
| PSI driven by empty bins | does not revoke | `test_a_psi_driven_by_empty_bins_does_not_revoke` | — |
| a small file | gets no drift verdict | `test_a_small_file_gets_no_drift_verdict` | — |
| a grouped warrant | rechecked in clusters, not items | `test_the_recheck_counts_clusters_not_items` | — |
| a grouped warrant rechecked without groups | refused | `test_a_grouped_warrant_rechecked_without_groups_is_refused` | — |
| **a recheck size** | catches the breach it is sized for with the planned power, not half the time | `test_the_sizes_146_quoted_catch_their_breach_half_the_time` | — |
| independent rechecks | revoke a sound detector more often the more there are | `test_more_rechecks_revoke_a_sound_detector_more_often` | `results/recheck_schedules/comparison.json` |

## 13. A chain of rechecks

| case | expected behaviour | test | artifact |
|---|---|---|---|
| the chain | is the rule the pre-registered study measured | `test_a1_the_chain_is_the_rule_the_study_measured` | `results/recheck_schedules/comparison.json` |
| a sound detector | keeps the chain's guarantee | `test_a1_the_chain_keeps_its_guarantee_on_a_sound_detector` | `results/chain_detection/grid.json` |
| permuting a file | changes nothing | `test_a2_permuting_a_file_changes_nothing` | — |
| **a drift revocation** | is not hidden by a chain | `test_f1_a_drift_revocation_is_not_hidden_by_a_chain` | — |
| **a warrant revoked by drift** | is not continued through the CLI | `test_a_warrant_revoked_by_drift_is_not_continued_through_the_cli` | — |
| `--fork` after a revocation | cannot restart a revoked warrant | `test_a_revoked_warrant_cannot_be_restarted_with_fork` | — |
| a fork from an earlier valid link after a revocation | refused | `test_a_fork_from_an_earlier_valid_link_after_a_revocation_is_refused` | — |
| head, fork and restart | an undeclared fork is refused; a declared one is recorded | `test_f5_head_fork_and_restart` | — |
| a fork | is flagged by verify whatever the head check said | `test_a_fork_is_flagged_whatever_head_check_says` | — |
| a unit id already consumed | refused, and the refusal names the id rule | `test_f3_the_refusal_names_the_id_rule` | — |
| a chained record | is never overwritten | `test_a_chained_record_is_created_exclusively` | — |
| **any stored field edited** | verify flags it; a property test over every leaf of real records | `test_every_leaf_of_every_link_edited_alone_is_flagged` | — |
| an edited `--since` record | is not continued, and the head is unchanged | `test_an_edited_since_record_is_not_continued` | — |
| a malformed value, or NaN | a finding, not a traceback | `test_nan_anywhere_in_a_record_is_a_finding_not_a_traceback` | — |
| a record written before sealing | listed as unsealed, not flagged | `test_an_unsealed_legacy_record_is_listed_not_flagged` | — |
| the guarantee text | names the statistic and excludes drift | `test_the_guarantee_names_the_statistic_and_excludes_drift` | — |
| `--require-clean` | turns a finding into exit 1 | `test_require_clean_turns_a_finding_into_exit_one` | — |

## 14. Label error

| case | expected behaviour | test | artifact |
|---|---|---|---|
| the confidence after correction | is the level at which the corrected bound equals the budget | `test_the_confidence_is_the_level_at_which_the_corrected_bound_equals_the_budget` | — |
| adding errors | never raises the confidence | `test_the_confidence_never_rises_as_errors_are_added` | — |
| a certificate | carries its sensitivity, and the disputes count what they say | `test_a_certificate_carries_its_sensitivity_and_the_disputes_count_what_they_say` | `results/label_sensitivity/triviaqa.json` |
| **a refusal** | carries no count of relabellings, which would be a recipe | `test_a_refusal_carries_no_count_of_relabellings` | — |
| **`label_2`** | changes no status, threshold, bound or metric | `test_label_2_changes_no_status_threshold_bound_or_metric` | — |
| `label_2` on a recheck | changes no verdict | `test_label_2_changes_no_recheck_verdict` | — |
| the whole-file dispute bound | covers every true count | `test_the_dispute_bound_covers_every_true_count` | — |
| a grouped file with a mixed group | has no sensitivity | `test_a_grouped_file_with_a_mixed_group_has_no_sensitivity` | — |
| a recheck whose bound holds | carries both counts of errors that would have revoked it | `test_a_recheck_whose_bound_holds_carries_both_counts` | — |
| a chained recheck | carries no per-file count | `test_a_chained_recheck_carries_no_per_file_count` | — |

## 15. Release evidence

| case | expected behaviour | test | artifact |
|---|---|---|---|
| registration | freezes identity | `test_registration_roundtrip_freezes_identity` | — |
| development and holdout ids | must be disjoint | `test_refuse_invalid_split` | — |
| an altered or replaced contract | fails | `test_altered_contract_and_replacement_fail` | — |
| the bounds | agree with an independent binomial tail inversion | `test_bounds_agree_with_independent_binomial_tail_inversion` | — |
| failure and missing evidence | are distinguished | `test_decisions_distinguish_failure_from_missing_evidence` | — |
| a rehashed fabrication, or expiry | caught on verify | `test_recompute_catches_rehashed_fabrication_and_expiry` | — |
| changed scores with unchanged counts | detected | `test_changed_scores_are_detected_even_without_changed_counts` | — |
| register, evaluate, verify from the CLI | work, and a second evaluation is not a replacement | `test_real_cli_register_evaluate_verify_and_no_replacement` | — |

## 16. The action gate and the on-traffic estimate

| case | expected behaviour | test | artifact |
|---|---|---|---|
| **no detector** | the gate's decisions are identical with every detector input removed | `test_gate_no_detector` | `results/gate/gate.json` |
| an injection that passes every check | is blocked anyway | `test_an_injected_instruction_passes_every_check_and_is_blocked_anyway` | `results/gate/gate.json` |
| the Rule-of-Two | counts the call being made, not only the history | `test_the_rule_is_prospective_not_historical` | — |
| an unregistered tool | refused rather than guessed | `test_an_unregistered_tool_is_refused_rather_than_guessed` | — |
| reversibility | cannot be downgraded at runtime | `test_reversibility_cannot_be_downgraded_at_runtime` | — |
| session flags | sticky, with no unsetter | `test_session_flags_are_sticky_and_there_is_no_unsetter` | — |
| **one declared workload** | no scenario mixing | `test_no_scenario_mixing` | `results/on_traffic/on_traffic.json` |
| sizing | through the derivative of recall, in the right units | `test_sizing_units` | — |
| yield and rate | precision exact, recall estimated | `test_precision_is_exact_and_recall_is_estimated` | — |
| the review queue | blinded | `test_blinding` | — |
| a label budget | realises its margin with the declared assurance | `test_c1_the_estimator_realises_the_margin_as_often_as_computed` | `results/on_traffic/on_traffic.json` |
