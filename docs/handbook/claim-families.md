# Claim families: methods, origins and limits

This reviewed catalog supplies the scientific context for each entry in the [claim ledger](claims.md). It is a source investigation, not independent human review.

## F01

### Probe discrimination and the chosen operating point

Evidence type: `measured_benchmark`.

**Question:** Can a supervised activation probe rank incorrect recorded answers and operate at the selected budget?

**Interpretation:** A logistic regression uses standardized pooled activations; scaling and fitting use training rows and regularization selection uses validation. The recorded held-out metric block describes one Qwen model, answer-matching rule, split and threshold. AUROC evaluates ranking across thresholds; recall, precision and flag rate evaluate the recorded threshold.

**Limitations:** The labels are outputs of an alias-matching rule, not independent human judgments of truth. Strong ranking can coexist with very low recall at a restrictive threshold. Frozen-score replay checks the metric calculation, not the original activation extraction, the validity of every interval or deployment generalization.

**Reproduction boundary:** CPU: python scripts/verify.py --no-activations. Activation-level replay additionally needs the original extraction cache; it is not bundled.

| Role | Repository evidence |
|---|---|
| Retained result | [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json) |
| Input/source reference | [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json) |
| Input/source reference | [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json) |
| Input/source reference | [config.yaml](../../config.yaml) |
| Writer/calculation | [scripts/02_validate.py](../../scripts/02_validate.py) |
| Writer/calculation | [controlplane/validation/runner.py](../../controlplane/validation/runner.py) |
| Writer/calculation | [controlplane/detectors/probe.py](../../controlplane/detectors/probe.py) |
| Writer/calculation | [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py) |

## F02

### Round-one reconciliation

Evidence type: `historical_comparison`.

**Question:** Does the reduced-training pipeline land in the predeclared reconciliation branch?

**Interpretation:** The artifact compares a retained round-one result with the round-two fit and records branch A. This is a consistency check across versions of this project, not independent replication by another investigator.

**Limitations:** The artifact explicitly records dirty=true and its config hash differs from the later main validation artifact. The source hash alone cannot reconstruct the complete original working tree. Matching a published interval does not establish equivalence of training protocols or scientific replication.

**Reproduction boundary:** The README values can be checked against the retained JSON. Re-executing the original comparison needs its historical code/configuration and extraction inputs; retain the dirty-provenance qualification.

| Role | Repository evidence |
|---|---|
| Retained result | [results/reconciliation.json](../../results/reconciliation.json) |
| Input/source reference | [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json) |
| Input/source reference | [round1/README.md](../../round1/README.md) |
| Writer/calculation | [scripts/06_reconcile.py](../../scripts/06_reconcile.py) |
| Writer/calculation | [controlplane/detectors/probe.py](../../controlplane/detectors/probe.py) |
| Writer/calculation | [controlplane/validation/stats.py](../../controlplane/validation/stats.py) |

## F03

### Paired training-size and selection comparisons

Evidence type: `measured_paired_comparison`.

**Question:** How does the training-size change affect the same held-out questions, and what does accounting for threshold selection cost?

**Interpretation:** The comparison couples both models on the same held-out question identities. The AUROC difference is a paired contrast. The widening value describes the particular selection-aware recall construction recorded for one profile.

**Limitations:** The compared datasets derive from the same original collection. A paired interval is not a new independent benchmark. Its selection-aware recall construction does not validate the separate adaptive returned-FPR bound. Original fitted-model replay needs untracked extraction inputs.

**Reproduction boundary:** Check split_relationship, thresholds and pinned_to_baseline_threshold in the JSON; inspect the paired and selection modules. Original fitting needs the historical extraction cache.

| Role | Repository evidence |
|---|---|
| Retained result | [results/paired_comparison.json](../../results/paired_comparison.json) |
| Input/source reference | [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json) |
| Input/source reference | [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json) |
| Writer/calculation | [scripts/08_paired.py](../../scripts/08_paired.py) |
| Writer/calculation | [controlplane/validation/paired.py](../../controlplane/validation/paired.py) |
| Writer/calculation | [controlplane/validation/selection.py](../../controlplane/validation/selection.py) |

## F04

### Exploratory FPR-budget sweep

Evidence type: `exploratory_measured_sweep`.

**Question:** Which operating budgets trade recall, precision and lift on these recorded scores?

**Interpretation:** The grid evaluates multiple budgets on frozen score vectors. The largest-budget headline is selected from the observed grid. Its recall/precision/lift explain the operating trade-off on those files.

**Limitations:** This is exploration, not an untouched confirmatory test. The largest favorable grid point cannot be treated as a predeclared success criterion. Any calibration-bound interpretation inherits the open FPR-001 review. Shifted scores reuse the original questions and labels.

**Reproduction boundary:** Inspect grid_spec and sweeps; regenerate only into a new output directory using the script flags. This family is not automatically re-executed by the ordinary claim-table verifier.

| Role | Repository evidence |
|---|---|
| Retained result | [results/fpr_sweep/sweep.json](../../results/fpr_sweep/sweep.json) |
| Input/source reference | [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json) |
| Input/source reference | [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json) |
| Writer/calculation | [scripts/19_fpr_sweep.py](../../scripts/19_fpr_sweep.py) |
| Writer/calculation | [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py) |

## F05

### Validation-selected, test-scored sweep

Evidence type: `held_out_calculation_with_provenance_gap`.

**Question:** Does the operating trade-off persist when threshold certification and evaluation use different declared splits?

**Interpretation:** The artifact records threshold certification on validation and metric evaluation on test, and exposes those split choices rather than using the descriptive test-set operating curve as calibration evidence.

**Limitations:** The artifact has dirty=true. The split declaration and numerical values are retained evidence; they do not identify the full original source state. A reused project test split is not a newly collected independent study. The stronger adaptive returned-U interpretation remains unsupported.

**Reproduction boundary:** Inspect certifying_split_metrics, integrity and out_of_sample. The original script may need the extraction cache. Artifact equality is weaker than source-faithful historical re-execution.

| Role | Repository evidence |
|---|---|
| Retained result | [results/fpr_sweep_oos/sweep.json](../../results/fpr_sweep_oos/sweep.json) |
| Input/source reference | [results/scores/valsplit-T1-last_token.json](../../results/scores/valsplit-T1-last_token.json) |
| Input/source reference | [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json) |
| Input/source reference | [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json) |
| Writer/calculation | [scripts/20_fpr_sweep_oos.py](../../scripts/20_fpr_sweep_oos.py) |
| Writer/calculation | [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py) |
| Writer/calculation | [controlplane/validation/paired.py](../../controlplane/validation/paired.py) |

## F06

### Three policy operating points

Evidence type: `measured_resplit_study_with_provenance_gap`.

**Question:** What does moving along one recorded detector curve buy for different declared profiles?

**Interpretation:** The profiles are different thresholds on a common scoring, not three independently trained systems. The derived manifest declares a 40/20/40 resplit of the same original items so its test portion can support the chosen calibration-sensitivity exercise.

**Limitations:** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Reproduction boundary:** Follow operating_points, the derived manifest and matching targets under results/scores. Metric replay does not rerun policy issuance controls.

| Role | Repository evidence |
|---|---|
| Retained result | [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json) |
| Input/source reference | [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json) |
| Writer/calculation | [scripts/07_policy.py](../../scripts/07_policy.py) |
| Writer/calculation | [controlplane/policy/runner.py](../../controlplane/policy/runner.py) |
| Writer/calculation | [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py) |

## F07

### Pooling under long-context shift

Evidence type: `paired_distribution_shift_measurement`.

**Question:** Which fitted representations retain discrimination when distractor context changes the extraction envelope?

**Interpretation:** The source-fitted probes are transferred without retuning. Last-token discrimination persists in the retained target scores; mean pooling is near chance and max-of-rolling-means is weaker, with a much larger flag rate. The target reuses short-context answers and labels while changing the context used for feature extraction.

**Limitations:** This is a paired representation-shift test, not newly generated long-context answer accuracy. Mean-signal dilution is a plausible explanation, not an independently isolated neural mechanism. One model family and constructed distractors cannot establish universal pooling rankings.

**Reproduction boundary:** The frozen target metrics replay on CPU. Reproducing the activations and transfer fit additionally needs the original short- and long-context caches.

| Role | Repository evidence |
|---|---|
| Retained result | [results/transfer-T1-last_token.json](../../results/transfer-T1-last_token.json) |
| Retained result | [results/transfer-T1-mean_pool.json](../../results/transfer-T1-mean_pool.json) |
| Retained result | [results/transfer-T1-max_rolling_means.json](../../results/transfer-T1-max_rolling_means.json) |
| Input/source reference | [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json) |
| Input/source reference | [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json) |
| Input/source reference | [results/scores/transfer-T1-mean_pool.json](../../results/scores/transfer-T1-mean_pool.json) |
| Input/source reference | [results/scores/transfer-T1-max_rolling_means.json](../../results/scores/transfer-T1-max_rolling_means.json) |
| Writer/calculation | [scripts/04_transfer.py](../../scripts/04_transfer.py) |
| Writer/calculation | [controlplane/validation/runner.py](../../controlplane/validation/runner.py) |
| Writer/calculation | [controlplane/detectors/aggregation.py](../../controlplane/detectors/aggregation.py) |

## F08

### Drift and revocation trace

Evidence type: `controlled_replay`.

**Question:** Does the declared drift criterion revoke a retained warrant on a constructed distribution shift?

**Interpretation:** A replay stream changes from the source envelope to the constructed long-context envelope. The artifact identifies the first shifted request, the monitored checkpoints, the PSI values and the revocation decision.

**Limitations:** The request indices and PSI values are deterministic observations of this replay. They are not a production latency, false-alarm-rate estimate, general drift detector validation, or evidence that the source of a real shift can be diagnosed.

**Reproduction boundary:** Inspect stream, criteria, checkpoints and revocation together. The script is a controlled replay; regeneration may require extraction inputs and the retained ledger.

| Role | Repository evidence |
|---|---|
| Retained result | [results/drift/revocation_trace.json](../../results/drift/revocation_trace.json) |
| Input/source reference | [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json) |
| Input/source reference | [results/transfer-T1-last_token.json](../../results/transfer-T1-last_token.json) |
| Writer/calculation | [scripts/28_revocation_trace.py](../../scripts/28_revocation_trace.py) |
| Writer/calculation | [controlplane/demo/revocation_trace.py](../../controlplane/demo/revocation_trace.py) |
| Writer/calculation | [controlplane/drift/psi.py](../../controlplane/drift/psi.py) |

## F09

### Warrant-matrix inventory

Evidence type: `mixed_measured_and_fixture_inventory`.

**Question:** Which detector-envelope combinations have a recorded state, and which remain unvalidated?

**Interpretation:** The three state counts describe the entire retained matrix, including explicitly synthetic envelopes. They count cells and historical statuses, not independently validated deployable models.

**Limitations:** Some VALID cells are fixtures; some historical hard-negative cells use legacy row-count inference. Current eligibility must inspect the evidence protocol and data source, not use a historical VALID string alone. UNVALIDATED is absence of a run, not a negative performance result.

**Reproduction boundary:** Read detector and envelope IDs, each cell and its originating artifact. The rendered results mask fixture measurements; do not promote inventory counts into empirical success rates.

| Role | Repository evidence |
|---|---|
| Retained result | [results/warrant_matrix.json](../../results/warrant_matrix.json) |
| Input/source reference | [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json) |
| Input/source reference | [results/detectors.json](../../results/detectors.json) |
| Writer/calculation | [scripts/03_matrix.py](../../scripts/03_matrix.py) |
| Writer/calculation | [controlplane/matrix/matrix.py](../../controlplane/matrix/matrix.py) |
| Writer/calculation | [controlplane/matrix/routing.py](../../controlplane/matrix/routing.py) |

## F10

### PII configurations and companion set

Evidence type: `measured_handcrafted_challenge_set`.

**Question:** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**Interpretation:** Stock, enabled and enabled-plus-custom configurations are compared on labeled synthetic-identifier scenarios. The companion set uses a new seed and expanded separator forms. A configured recognizer can succeed where a stock configuration lacks the relevant coverage.

**Limitations:** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Reproduction boundary:** The committed text score sets replay the retained metric blocks. A fresh analyzer run needs the pinned research dependency/model environment; current upstream defaults may differ.

| Role | Repository evidence |
|---|---|
| Retained result | [results/detectors.json](../../results/detectors.json) |
| Retained result | [results/holdout/detectors.json](../../results/holdout/detectors.json) |
| Input/source reference | [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json) |
| Input/source reference | [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json) |
| Writer/calculation | [scripts/09_detectors.py](../../scripts/09_detectors.py) |
| Writer/calculation | [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py) |
| Writer/calculation | [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py) |
| Writer/calculation | [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py) |

## F11

### Benign hard-negative result

Evidence type: `historical_dependent_rows`.

**Question:** How often did the reference detector fire on the declared benign challenge rows?

**Interpretation:** The point count is descriptive for this all-benign set. The rows are systematic framings of fewer hand-written scenarios. The retained interval is historical row-binomial inference, explicitly preserved for arithmetic replay.

**Limitations:** Dependent framings are not independent Bernoulli trials. The old row interval is not current group-aware assurance. A zero observed count does not establish zero population risk. No AUROC, recall or precision is defined for this single-class set.

**Reproduction boundary:** The legacy score replay deliberately selects the historical method. New issuance uses the independent-unit protocol and must not inherit a legacy status or row interval.

| Role | Repository evidence |
|---|---|
| Retained result | [results/validation-pii-reference-hard-negatives-200.json](../../results/validation-pii-reference-hard-negatives-200.json) |
| Input/source reference | [evalsets/hard-negatives-200.json](../../evalsets/hard-negatives-200.json) |
| Input/source reference | [results/scores/text-pii-reference-hard-negatives-200.json](../../results/scores/text-pii-reference-hard-negatives-200.json) |
| Writer/calculation | [controlplane/evalsets/hard_negatives.py](../../controlplane/evalsets/hard_negatives.py) |
| Writer/calculation | [controlplane/validation/text_runner.py](../../controlplane/validation/text_runner.py) |
| Writer/calculation | [controlplane/validation/metric_protocols.py](../../controlplane/validation/metric_protocols.py) |

## F12

### Abstention feasibility

Evidence type: `declared_scenario_calculation`.

**Question:** What fraction must a perfect error selector abstain on to attain a chosen residual-risk target?

**Interpretation:** For base error probability p and target residual error r, the ideal floor is max(0,(p-r)/(1-r)). Actual residual risk and efficiency combine the recorded profile rates under the stated scenario. This separates a mathematical feasibility bound from a detector operating point.

**Limitations:** The ideal selector is not an implemented model. These are conditional arithmetic consequences of their inputs. The source policy artifact has dirty provenance, and its measurement population differs from a declared production workload. No ROI, savings or buyer value is measured.

**Reproduction boundary:** Inspect measured, declared and not_derived_here; use the feasibility module for the formula. Do not mix benchmark prevalence with another workload without stating the transport assumption.

| Role | Repository evidence |
|---|---|
| Retained result | [results/feasibility.json](../../results/feasibility.json) |
| Input/source reference | [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json) |
| Input/source reference | [config.yaml](../../config.yaml) |
| Writer/calculation | [scripts/11_feasibility.py](../../scripts/11_feasibility.py) |
| Writer/calculation | [controlplane/economics/feasibility.py](../../controlplane/economics/feasibility.py) |

## F13

### On-traffic review planning

Evidence type: `simulation_and_declared_workload`.

**Question:** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**Interpretation:** Reviewed flagged items form a census; unflagged errors must be sampled. The recall derivative propagates uncertainty in unflagged prevalence. The label plan also incorporates the stated assurance target, discrete planning and finite-population assumptions. Allocation and interval coverage are evaluated under a declared simulator.

**Limitations:** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Reproduction boundary:** Read declared, sensitivity, price_list, coverage and allocation together; reproduce with a new output location. A different prevalence, grouping or reviewer process needs a new study.

| Role | Repository evidence |
|---|---|
| Retained result | [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json) |
| Input/source reference | [config.yaml](../../config.yaml) |
| Writer/calculation | [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py) |
| Writer/calculation | [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py) |
| Writer/calculation | [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py) |
| Writer/calculation | [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py) |

## F14

### Year-long recheck comparisons

Evidence type: `historical_simulation`.

**Question:** How do repeated revocation rules trade false revocation and delayed breach detection on the same simulated labels?

**Interpretation:** The predeclared simulation compares fixed, alpha-split, historical capped-monitor, uncapped reference and e-detector rules. S0 runs at the budget; S3 changes from a lower certified rate to a breach. Every quoted cell is tied to its rule, cadence, scenario and horizon.

**Limitations:** These are Monte Carlo characteristics of decision rules, not detector performance. The monitor cell is the historical capped implementation from Decision 187, not the repaired runtime in Decision 226. Apparent failure of repeated fixed tests is not evidence that all monitoring methods fail.

**Reproduction boundary:** Inspect design and each cells selector; use the historical implementation when reproducing historical numbers. Do not silently regenerate them with the repaired runtime and call that a byte-identical replay.

| Role | Repository evidence |
|---|---|
| Retained result | [results/recheck_schedules/comparison.json](../../results/recheck_schedules/comparison.json) |
| Input/source reference | [config.yaml](../../config.yaml) |
| Writer/calculation | [scripts/29_recheck_schedules.py](../../scripts/29_recheck_schedules.py) |
| Writer/calculation | [controlplane/economics/schedules.py](../../controlplane/economics/schedules.py) |

## F15

### Chained detection grid

Evidence type: `finite_horizon_simulation`.

**Question:** How does a fixed chained rule detect several declared breach sizes and change times?

**Interpretation:** The grid retains each breach/cadence/scenario combination and simulated catch window. It reports finite-horizon operating characteristics, with the same predeclared decision rule across cells.

**Limitations:** A share of 1.0 means every simulated year in that cell, not certainty for all future streams. Detection probability depends on the breach, label supply, change time and horizon. These simulations are not external validation on customer traffic.

**Reproduction boundary:** Inspect the complete design, the stated Monte Carlo units and the exact selector. Re-run the grid into a fresh directory; preserve the original study identity.

| Role | Repository evidence |
|---|---|
| Retained result | [results/chain_detection/grid.json](../../results/chain_detection/grid.json) |
| Input/source reference | [config.yaml](../../config.yaml) |
| Writer/calculation | [scripts/31_chain_detection.py](../../scripts/31_chain_detection.py) |
| Writer/calculation | [controlplane/economics/detection_grid.py](../../controlplane/economics/detection_grid.py) |
| Writer/calculation | [controlplane/economics/schedules.py](../../controlplane/economics/schedules.py) |

## F16

### Label-sensitivity study

Evidence type: `exact_sensitivity_on_recorded_labels`.

**Question:** How sensitive are the retained certificate calculations to specified possible label errors?

**Interpretation:** The study computes exact consequences of perturbing label counts and compares lenient versus strict answer matching over recorded items. Its range summarizes the declared probe-budget rows, not an independently sampled set of labeling mistakes.

**Limitations:** Disagreement is not a proven error, and strict matching is not a human gold standard. The confidence-under-perturbation calculation is conditional on its assumptions and must not be read as validation of the general adaptive returned bound. The original label truth is unresolved.

**Reproduction boundary:** Inspect design, sets and criteria; the frozen responses allow rule disagreement to be recomputed. Independent blinded source adjudication would answer a stronger question.

| Role | Repository evidence |
|---|---|
| Retained result | [results/label_sensitivity/triviaqa.json](../../results/label_sensitivity/triviaqa.json) |
| Input/source reference | [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json) |
| Input/source reference | [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json) |
| Input/source reference | [results/scores/validation-T1-mean_pool.json](../../results/scores/validation-T1-mean_pool.json) |
| Input/source reference | [results/scores/validation-T1-max_rolling_means.json](../../results/scores/validation-T1-max_rolling_means.json) |
| Writer/calculation | [scripts/32_label_sensitivity.py](../../scripts/32_label_sensitivity.py) |
| Writer/calculation | [controlplane/validation/label_error.py](../../controlplane/validation/label_error.py) |
| Writer/calculation | [controlplane/extract/triviaqa.py](../../controlplane/extract/triviaqa.py) |

## F17

### Score-free detector tunability

Evidence type: `simulated_independent_judge_votes`.

**Question:** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**Interpretation:** The simulator draws per-item latent probabilities and conditionally independent Bernoulli votes. A single binary decision permits one useful nontrivial threshold; more votes supply a discrete vote fraction. Available notches and distinct selected operating points are different counts.

**Limitations:** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Reproduction boundary:** Inspect declared, scope, headline and not_derived_here. The historical scope uses upper-bound language; the defensible reading is conditional on the specified latent-probability model.

| Role | Repository evidence |
|---|---|
| Retained result | [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json) |
| Input/source reference | [config.yaml](../../config.yaml) |
| Writer/calculation | [scripts/26_scorefree.py](../../scripts/26_scorefree.py) |
| Writer/calculation | [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py) |

## F18

### Action-gate demonstration

Evidence type: `finite_controlled_software_demonstration`.

**Question:** Do the declared session and reversibility rules act consistently without a detector score, and what do they block in the declared workflow set?

**Interpretation:** The sweep and scenario runner enumerate known session/tool/warrant combinations. The earliest gate rules use reversibility and session state, so the selected comparisons are identical when detector evidence is removed. The legitimate-workflow cost is an exact count in the authored demonstration set.

**Limitations:** No empirical adversarial-robustness or production false-block rate follows from this finite sweep. A prompt-injection scenario and a small set of legitimate workflows do not represent arbitrary banking systems, attackers or users. Recovery by a new session is specific to the demonstrated policy.

**Reproduction boundary:** Inspect registry, injection, no_detector_evidence, cost and headline. Re-run only the authored scenario set; external robustness would require a separate threat model and evaluation.

| Role | Repository evidence |
|---|---|
| Retained result | [results/gate/gate.json](../../results/gate/gate.json) |
| Input/source reference | [config.yaml](../../config.yaml) |
| Writer/calculation | [scripts/27_gate.py](../../scripts/27_gate.py) |
| Writer/calculation | [controlplane/gate/gate.py](../../controlplane/gate/gate.py) |
| Writer/calculation | [controlplane/gate/agent.py](../../controlplane/gate/agent.py) |
| Writer/calculation | [controlplane/gate/cost.py](../../controlplane/gate/cost.py) |
