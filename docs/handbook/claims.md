# Claim-by-claim evidence ledger

This generated ledger checks retained evidence. Arithmetic agreement does not establish scientific validity.

Audit source: `c789c9514a1cdba09de63d0c77cd51a593837ba3`. The [machine receipt](../../results/documentation_audit/20261105-final/audit.json) retains hashes and explicit scope.

The audit covers 92 rows across 21 artifacts. 15 rows point directly to dirty-source artifacts. The independent point oracle checks 25 frozen-score targets, not every scientific proposition.

Read [how to interpret this audit](claim-audit.md) and [family methods and limits](claim-families.md) first.

## C001

**Probe AUROC, triviaqa-600, n=600**

Retained value: `0.8256`. Retained interval: `[0.7934, 0.8567]`. Artifact equality: **MATCH**.

- Evidence: [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json); field `metrics.auroc.value`.
- Artifact SHA-256: `ea20380d90002de6429aef8bddb8d3a7344728ae69d902cc1864769be79a6968`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F01: Probe discrimination and the chosen operating point](claim-families.md#f01); type `measured_benchmark`.

**Why this claim is included.** Can a supervised activation probe rank incorrect recorded answers and operate at the selected budget?

**What it means.** AUROC is the positive-versus-negative pair-ranking probability, with half credit for ties. It does not state recall at the selected budget.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [config.yaml](../../config.yaml); [scripts/02_validate.py](../../scripts/02_validate.py); [controlplane/validation/runner.py](../../controlplane/validation/runner.py); [controlplane/detectors/probe.py](../../controlplane/detectors/probe.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The labels are outputs of an alias-matching rule, not independent human judgments of truth. Strong ranking can coexist with very low recall at a restrictive threshold. Frozen-score replay checks the metric calculation, not the original activation extraction, the validity of every interval or deployment generalization.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C002

**Probe recall at its operating point**

Retained value: `0.0794`. Retained interval: `[0.0496, 0.1115]`. Artifact equality: **MATCH**.

- Evidence: [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json); field `metrics.recall.value`.
- Artifact SHA-256: `ea20380d90002de6429aef8bddb8d3a7344728ae69d902cc1864769be79a6968`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F01: Probe discrimination and the chosen operating point](claim-families.md#f01); type `measured_benchmark`.

**Why this claim is included.** Can a supervised activation probe rank incorrect recorded answers and operate at the selected budget?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [config.yaml](../../config.yaml); [scripts/02_validate.py](../../scripts/02_validate.py); [controlplane/validation/runner.py](../../controlplane/validation/runner.py); [controlplane/detectors/probe.py](../../controlplane/detectors/probe.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The labels are outputs of an alias-matching rule, not independent human judgments of truth. Strong ranking can coexist with very low recall at a restrictive threshold. Frozen-score replay checks the metric calculation, not the original activation extraction, the validity of every interval or deployment generalization.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C003

**Probe precision there**

Retained value: `0.8800`. Retained interval: `[0.7500, 1.0000]`. Artifact equality: **MATCH**.

- Evidence: [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json); field `metrics.precision.value`.
- Artifact SHA-256: `ea20380d90002de6429aef8bddb8d3a7344728ae69d902cc1864769be79a6968`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F01: Probe discrimination and the chosen operating point](claim-families.md#f01); type `measured_benchmark`.

**Why this claim is included.** Can a supervised activation probe rank incorrect recorded answers and operate at the selected budget?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [config.yaml](../../config.yaml); [scripts/02_validate.py](../../scripts/02_validate.py); [controlplane/validation/runner.py](../../controlplane/validation/runner.py); [controlplane/detectors/probe.py](../../controlplane/detectors/probe.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The labels are outputs of an alias-matching rule, not independent human judgments of truth. Strong ranking can coexist with very low recall at a restrictive threshold. Frozen-score replay checks the metric calculation, not the original activation extraction, the validity of every interval or deployment generalization.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C004

**Measured flag rate there**

Retained value: `0.0417`. Retained interval: `[0.0267, 0.0583]`. Artifact equality: **MATCH**.

- Evidence: [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json); field `metrics.flag_rate.value`.
- Artifact SHA-256: `ea20380d90002de6429aef8bddb8d3a7344728ae69d902cc1864769be79a6968`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F01: Probe discrimination and the chosen operating point](claim-families.md#f01); type `measured_benchmark`.

**Why this claim is included.** Can a supervised activation probe rank incorrect recorded answers and operate at the selected budget?

**What it means.** Flag rate is the observed fraction of rows at or above the threshold. It is not the requested false-positive budget; on a wholly benign set it equals descriptive FPR.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [config.yaml](../../config.yaml); [scripts/02_validate.py](../../scripts/02_validate.py); [controlplane/validation/runner.py](../../controlplane/validation/runner.py); [controlplane/detectors/probe.py](../../controlplane/detectors/probe.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The labels are outputs of an alias-matching rule, not independent human judgments of truth. Strong ranking can coexist with very low recall at a restrictive threshold. Frozen-score replay checks the metric calculation, not the original activation extraction, the validity of every interval or deployment generalization.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C005

**Base error rate of that envelope**

Retained value: `0.4617`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json); field `base_rate`.
- Artifact SHA-256: `ea20380d90002de6429aef8bddb8d3a7344728ae69d902cc1864769be79a6968`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F01: Probe discrimination and the chosen operating point](claim-families.md#f01); type `measured_benchmark`.

**Why this claim is included.** Can a supervised activation probe rank incorrect recorded answers and operate at the selected budget?

**What it means.** This is positive-label prevalence in the evaluated split. It is different from the whole manifest's prevalence and is not a production error rate.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [config.yaml](../../config.yaml); [scripts/02_validate.py](../../scripts/02_validate.py); [controlplane/validation/runner.py](../../controlplane/validation/runner.py); [controlplane/detectors/probe.py](../../controlplane/detectors/probe.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The labels are outputs of an alias-matching rule, not independent human judgments of truth. Strong ranking can coexist with very low recall at a restrictive threshold. Frozen-score replay checks the metric calculation, not the original activation extraction, the validity of every interval or deployment generalization.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C006

**Round 1 reproduced on Round 2's pipeline**

Retained value: `0.8256`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/reconciliation.json](../../results/reconciliation.json); field `round2.T1-last_token.test_auroc`.
- Artifact SHA-256: `375250d1dd5576638c8d22a5fc72231930a840a62f0699d6d385522b890ee1a3`.
- Recorded source: `efa1291e418d33c90a79aa00bf70ab2161209caf`; dirty: `True`; config: `b4ca1ec022266551`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F02: Round-one reconciliation](claim-families.md#f02); type `historical_comparison`.

**Why this claim is included.** Does the reduced-training pipeline land in the predeclared reconciliation branch?

**What it means.** This is the retained round-two AUROC used in the historical reconciliation, not an independently obtained replication.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [round1/README.md](../../round1/README.md); [scripts/06_reconcile.py](../../scripts/06_reconcile.py); [controlplane/detectors/probe.py](../../controlplane/detectors/probe.py); [controlplane/validation/stats.py](../../controlplane/validation/stats.py)

**What remains unproved.** The artifact explicitly records dirty=true and its config hash differs from the later main validation artifact. The source hash alone cannot reconstruct the complete original working tree. Matching a published interval does not establish equivalence of training protocols or scientific replication.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C007

**...landing inside Round 1's published interval**

Retained value: `A`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/reconciliation.json](../../results/reconciliation.json); field `branch`.
- Artifact SHA-256: `375250d1dd5576638c8d22a5fc72231930a840a62f0699d6d385522b890ee1a3`.
- Recorded source: `efa1291e418d33c90a79aa00bf70ab2161209caf`; dirty: `True`; config: `b4ca1ec022266551`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F02: Round-one reconciliation](claim-families.md#f02); type `historical_comparison`.

**Why this claim is included.** Does the reduced-training pipeline land in the predeclared reconciliation branch?

**What it means.** A is a branch of the predeclared comparison rule. It is not a statistical grade or evidence of external validation.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [round1/README.md](../../round1/README.md); [scripts/06_reconcile.py](../../scripts/06_reconcile.py); [controlplane/detectors/probe.py](../../controlplane/detectors/probe.py); [controlplane/validation/stats.py](../../controlplane/validation/stats.py)

**What remains unproved.** The artifact explicitly records dirty=true and its config hash differs from the later main validation artifact. The source hash alone cannot reconstruct the complete original working tree. Matching a published interval does not establish equivalence of training protocols or scientific replication.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C008

**Cost of the training reduction, paired on 600 held-out items**

Retained value: `-0.0110`. Retained interval: `[-0.0200, -0.0026]`. Artifact equality: **MATCH**.

- Evidence: [results/paired_comparison.json](../../results/paired_comparison.json); field `pinned_to_baseline_threshold[quantity=auroc].difference`.
- Artifact SHA-256: `0d4e49fbfe375e71a63127f115cd51aac7cf6895c8ff1d66c332a420fe830094`.
- Recorded source: `9fca6b94b36da86f51892d16539ff1c1e64089f7`; dirty: `False`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F03: Paired training-size and selection comparisons](claim-families.md#f03); type `measured_paired_comparison`.

**Why this claim is included.** How does the training-size change affect the same held-out questions, and what does accounting for threshold selection cost?

**What it means.** This is a paired AUROC contrast on shared held-out questions. The original comparison object defines its direction and pairing; an unpaired comparison of differently sized test sets cannot replace it.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/08_paired.py](../../scripts/08_paired.py); [controlplane/validation/paired.py](../../controlplane/validation/paired.py); [controlplane/validation/selection.py](../../controlplane/validation/selection.py)

**What remains unproved.** The compared datasets derive from the same original collection. A paired interval is not a new independent benchmark. Its selection-aware recall construction does not validate the separate adaptive returned-FPR bound. Original fitted-model replay needs untracked extraction inputs.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C009

**Selection-aware widening of the recall bound**

Retained value: `1.5922`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/paired_comparison.json](../../results/paired_comparison.json); field `selection_aware_bounds[operating_point_id=P-customer-support].widening`.
- Artifact SHA-256: `0d4e49fbfe375e71a63127f115cd51aac7cf6895c8ff1d66c332a420fe830094`.
- Recorded source: `9fca6b94b36da86f51892d16539ff1c1e64089f7`; dirty: `False`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F03: Paired training-size and selection comparisons](claim-families.md#f03); type `measured_paired_comparison`.

**Why this claim is included.** How does the training-size change affect the same held-out questions, and what does accounting for threshold selection cost?

**What it means.** This ratio compares the recorded selection-aware recall width with the conditional width for one operating point. It does not repair the adaptive returned-FPR-bound issue.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/08_paired.py](../../scripts/08_paired.py); [controlplane/validation/paired.py](../../controlplane/validation/paired.py); [controlplane/validation/selection.py](../../controlplane/validation/selection.py)

**What remains unproved.** The compared datasets derive from the same original collection. A paired interval is not a new independent benchmark. Its selection-aware recall construction does not validate the separate adaptive returned-FPR bound. Original fitted-model replay needs untracked extraction inputs.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C010

**Largest FPR budget where lift still holds**

Retained value: `0.20`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep/sweep.json](../../results/fpr_sweep/sweep.json); field `sweeps[eval_set_id=triviaqa-600].headline.largest_target_fpr_where_lift_holds`.
- Artifact SHA-256: `3a15821c418adad31e881c6738be3160de79dfb3e6655410c42b4edd273ce74f`.
- Recorded source: `8356af74cc70dd0a602ca39eae8c154c1616f363`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/19_fpr_sweep.py`. This is not a claim that this audit executed that command.
- Evidence family: [F04: Exploratory FPR-budget sweep](claim-families.md#f04); type `exploratory_measured_sweep`.

**Why this claim is included.** Which operating budgets trade recall, precision and lift on these recorded scores?

**What it means.** This is the largest examined budget satisfying the study headline criterion. Selecting it from the observed grid makes it exploratory.

**Where the data and calculation come from.** [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [scripts/19_fpr_sweep.py](../../scripts/19_fpr_sweep.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py)

**What remains unproved.** This is exploration, not an untouched confirmatory test. The largest favorable grid point cannot be treated as a predeclared success criterion. Any calibration-bound interpretation inherits the open FPR-001 review. Shifted scores reuse the original questions and labels.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C011

**Recall there — the same probe, a looser budget**

Retained value: `0.6462`. Retained interval: `[0.5950, 0.7051]`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep/sweep.json](../../results/fpr_sweep/sweep.json); field `sweeps[eval_set_id=triviaqa-600].points[target_fpr=0.2].recall.value`.
- Artifact SHA-256: `3a15821c418adad31e881c6738be3160de79dfb3e6655410c42b4edd273ce74f`.
- Recorded source: `8356af74cc70dd0a602ca39eae8c154c1616f363`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/19_fpr_sweep.py`. This is not a claim that this audit executed that command.
- Evidence family: [F04: Exploratory FPR-budget sweep](claim-families.md#f04); type `exploratory_measured_sweep`.

**Why this claim is included.** Which operating budgets trade recall, precision and lift on these recorded scores?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [scripts/19_fpr_sweep.py](../../scripts/19_fpr_sweep.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py)

**What remains unproved.** This is exploration, not an untouched confirmatory test. The largest favorable grid point cannot be treated as a predeclared success criterion. Any calibration-bound interpretation inherits the open FPR-001 review. Shifted scores reuse the original questions and labels.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C012

**Precision there**

Retained value: `0.7749`. Retained interval: `[0.7227, 0.8290]`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep/sweep.json](../../results/fpr_sweep/sweep.json); field `sweeps[eval_set_id=triviaqa-600].points[target_fpr=0.2].precision.value`.
- Artifact SHA-256: `3a15821c418adad31e881c6738be3160de79dfb3e6655410c42b4edd273ce74f`.
- Recorded source: `8356af74cc70dd0a602ca39eae8c154c1616f363`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/19_fpr_sweep.py`. This is not a claim that this audit executed that command.
- Evidence family: [F04: Exploratory FPR-budget sweep](claim-families.md#f04); type `exploratory_measured_sweep`.

**Why this claim is included.** Which operating budgets trade recall, precision and lift on these recorded scores?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [scripts/19_fpr_sweep.py](../../scripts/19_fpr_sweep.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py)

**What remains unproved.** This is exploration, not an untouched confirmatory test. The largest favorable grid point cannot be treated as a predeclared success criterion. Any calibration-bound interpretation inherits the open FPR-001 review. Shifted scores reuse the original questions and labels.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C013

**Lift there, against a 2.17 ceiling**

Retained value: `1.678`. Retained interval: `[1.545, 1.831]`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep/sweep.json](../../results/fpr_sweep/sweep.json); field `sweeps[eval_set_id=triviaqa-600].points[target_fpr=0.2].lift.value`.
- Artifact SHA-256: `3a15821c418adad31e881c6738be3160de79dfb3e6655410c42b4edd273ce74f`.
- Recorded source: `8356af74cc70dd0a602ca39eae8c154c1616f363`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/19_fpr_sweep.py`. This is not a claim that this audit executed that command.
- Evidence family: [F04: Exploratory FPR-budget sweep](claim-families.md#f04); type `exploratory_measured_sweep`.

**Why this claim is included.** Which operating budgets trade recall, precision and lift on these recorded scores?

**What it means.** Lift is recall divided by realized flag rate, equivalently precision divided by prevalence on the same population. It is not recall and it has a prevalence-dependent ceiling.

**Where the data and calculation come from.** [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [scripts/19_fpr_sweep.py](../../scripts/19_fpr_sweep.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py)

**What remains unproved.** This is exploration, not an untouched confirmatory test. The largest favorable grid point cannot be treated as a predeclared success criterion. Any calibration-bound interpretation inherits the open FPR-001 review. Shifted scores reuse the original questions and labels.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C014

**...and it survives the long-context shift**

Retained value: `0.6209`. Retained interval: `[0.5667, 0.6815]`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep/sweep.json](../../results/fpr_sweep/sweep.json); field `sweeps[eval_set_id=triviaqa-longctx-600].points[target_fpr=0.2].recall.value`.
- Artifact SHA-256: `3a15821c418adad31e881c6738be3160de79dfb3e6655410c42b4edd273ce74f`.
- Recorded source: `8356af74cc70dd0a602ca39eae8c154c1616f363`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/19_fpr_sweep.py`. This is not a claim that this audit executed that command.
- Evidence family: [F04: Exploratory FPR-budget sweep](claim-families.md#f04); type `exploratory_measured_sweep`.

**Why this claim is included.** Which operating budgets trade recall, precision and lift on these recorded scores?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [scripts/19_fpr_sweep.py](../../scripts/19_fpr_sweep.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py)

**What remains unproved.** This is exploration, not an untouched confirmatory test. The largest favorable grid point cannot be treated as a predeclared success criterion. Any calibration-bound interpretation inherits the open FPR-001 review. Shifted scores reuse the original questions and labels.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C015

**...its precision there**

Retained value: `0.7679`. Retained interval: `[0.7137, 0.8214]`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep/sweep.json](../../results/fpr_sweep/sweep.json); field `sweeps[eval_set_id=triviaqa-longctx-600].points[target_fpr=0.2].precision.value`.
- Artifact SHA-256: `3a15821c418adad31e881c6738be3160de79dfb3e6655410c42b4edd273ce74f`.
- Recorded source: `8356af74cc70dd0a602ca39eae8c154c1616f363`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/19_fpr_sweep.py`. This is not a claim that this audit executed that command.
- Evidence family: [F04: Exploratory FPR-budget sweep](claim-families.md#f04); type `exploratory_measured_sweep`.

**Why this claim is included.** Which operating budgets trade recall, precision and lift on these recorded scores?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [scripts/19_fpr_sweep.py](../../scripts/19_fpr_sweep.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py)

**What remains unproved.** This is exploration, not an untouched confirmatory test. The largest favorable grid point cannot be treated as a predeclared success criterion. Any calibration-bound interpretation inherits the open FPR-001 review. Shifted scores reuse the original questions and labels.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C016

**Out-of-sample recall at the same budget**

Retained value: `0.6318`. Retained interval: `[0.5782, 0.6880]`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep_oos/sweep.json](../../results/fpr_sweep_oos/sweep.json); field `sweeps[eval_set_id=triviaqa-600].points[target_fpr=0.2].recall.value`.
- Artifact SHA-256: `70f8d8310c5b07d25ea77ad781cf48b78a7c424912e4d11ab4fc8c2056521938`.
- Recorded source: `3523da8748801a14209f4689f783c6d722ffa88d`; dirty: `True`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/20_fpr_sweep_oos.py`. This is not a claim that this audit executed that command.
- Evidence family: [F05: Validation-selected, test-scored sweep](claim-families.md#f05); type `held_out_calculation_with_provenance_gap`.

**Why this claim is included.** Does the operating trade-off persist when threshold certification and evaluation use different declared splits?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [results/scores/valsplit-T1-last_token.json](../../results/scores/valsplit-T1-last_token.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [scripts/20_fpr_sweep_oos.py](../../scripts/20_fpr_sweep_oos.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py); [controlplane/validation/paired.py](../../controlplane/validation/paired.py)

**What remains unproved.** The artifact has dirty=true. The split declaration and numerical values are retained evidence; they do not identify the full original source state. A reused project test split is not a newly collected independent study. The stronger adaptive returned-U interpretation remains unsupported.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Upstream caution:** declared input references include dirty-source evidence: results/scores/valsplit-T1-last_token.json.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C017

**...its precision**

Retained value: `0.7743`. Retained interval: `[0.7220, 0.8281]`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep_oos/sweep.json](../../results/fpr_sweep_oos/sweep.json); field `sweeps[eval_set_id=triviaqa-600].points[target_fpr=0.2].precision.value`.
- Artifact SHA-256: `70f8d8310c5b07d25ea77ad781cf48b78a7c424912e4d11ab4fc8c2056521938`.
- Recorded source: `3523da8748801a14209f4689f783c6d722ffa88d`; dirty: `True`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/20_fpr_sweep_oos.py`. This is not a claim that this audit executed that command.
- Evidence family: [F05: Validation-selected, test-scored sweep](claim-families.md#f05); type `held_out_calculation_with_provenance_gap`.

**Why this claim is included.** Does the operating trade-off persist when threshold certification and evaluation use different declared splits?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [results/scores/valsplit-T1-last_token.json](../../results/scores/valsplit-T1-last_token.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [scripts/20_fpr_sweep_oos.py](../../scripts/20_fpr_sweep_oos.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py); [controlplane/validation/paired.py](../../controlplane/validation/paired.py)

**What remains unproved.** The artifact has dirty=true. The split declaration and numerical values are retained evidence; they do not identify the full original source state. A reused project test split is not a newly collected independent study. The stronger adaptive returned-U interpretation remains unsupported.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Upstream caution:** declared input references include dirty-source evidence: results/scores/valsplit-T1-last_token.json.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C018

**...its lift**

Retained value: `1.677`. Retained interval: `[1.535, 1.826]`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep_oos/sweep.json](../../results/fpr_sweep_oos/sweep.json); field `sweeps[eval_set_id=triviaqa-600].points[target_fpr=0.2].lift.value`.
- Artifact SHA-256: `70f8d8310c5b07d25ea77ad781cf48b78a7c424912e4d11ab4fc8c2056521938`.
- Recorded source: `3523da8748801a14209f4689f783c6d722ffa88d`; dirty: `True`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/20_fpr_sweep_oos.py`. This is not a claim that this audit executed that command.
- Evidence family: [F05: Validation-selected, test-scored sweep](claim-families.md#f05); type `held_out_calculation_with_provenance_gap`.

**Why this claim is included.** Does the operating trade-off persist when threshold certification and evaluation use different declared splits?

**What it means.** This lift uses the retained test-scored rates at the validation-selected operating point. Its meaning remains population-specific.

**Where the data and calculation come from.** [results/scores/valsplit-T1-last_token.json](../../results/scores/valsplit-T1-last_token.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [scripts/20_fpr_sweep_oos.py](../../scripts/20_fpr_sweep_oos.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py); [controlplane/validation/paired.py](../../controlplane/validation/paired.py)

**What remains unproved.** The artifact has dirty=true. The split declaration and numerical values are retained evidence; they do not identify the full original source state. A reused project test split is not a newly collected independent study. The stronger adaptive returned-U interpretation remains unsupported.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Upstream caution:** declared input references include dirty-source evidence: results/scores/valsplit-T1-last_token.json.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C019

**Thresholds certified on validation, scored on test**

Retained value: `True`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/fpr_sweep_oos/sweep.json](../../results/fpr_sweep_oos/sweep.json); field `sweeps[eval_set_id=triviaqa-600].out_of_sample`.
- Artifact SHA-256: `70f8d8310c5b07d25ea77ad781cf48b78a7c424912e4d11ab4fc8c2056521938`.
- Recorded source: `3523da8748801a14209f4689f783c6d722ffa88d`; dirty: `True`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/20_fpr_sweep_oos.py`. This is not a claim that this audit executed that command.
- Evidence family: [F05: Validation-selected, test-scored sweep](claim-families.md#f05); type `held_out_calculation_with_provenance_gap`.

**Why this claim is included.** Does the operating trade-off persist when threshold certification and evaluation use different declared splits?

**What it means.** The Boolean records the artifact's split protocol. Inspect the split identities and writer; a Boolean alone does not prove source cleanliness or untouched test use.

**Where the data and calculation come from.** [results/scores/valsplit-T1-last_token.json](../../results/scores/valsplit-T1-last_token.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [scripts/20_fpr_sweep_oos.py](../../scripts/20_fpr_sweep_oos.py); [controlplane/validation/fpr_sweep.py](../../controlplane/validation/fpr_sweep.py); [controlplane/validation/paired.py](../../controlplane/validation/paired.py)

**What remains unproved.** The artifact has dirty=true. The split declaration and numerical values are retained evidence; they do not identify the full original source state. A reused project test split is not a newly collected independent study. The stronger adaptive returned-U interpretation remains unsupported.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Upstream caution:** declared input references include dirty-source evidence: results/scores/valsplit-T1-last_token.json.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C020

**customer_support recall, n=960**

Retained value: `0.2171`. Retained interval: `[0.1800, 0.2564]`. Artifact equality: **MATCH**.

- Evidence: [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); field `operating_points[operating_point.operating_point_id=P-customer-support].metrics.recall.value`.
- Artifact SHA-256: `32f7141dfcdfe0a855ca89526ba9444c9c9a0d858bb90d5ceadbb362e669f507`.
- Recorded source: `0ad8c769527b7345edf6abae92ec611780948b14`; dirty: `True`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F06: Three policy operating points](claim-families.md#f06); type `measured_resplit_study_with_provenance_gap`.

**Why this claim is included.** What does moving along one recorded detector curve buy for different declared profiles?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/07_policy.py](../../scripts/07_policy.py); [controlplane/policy/runner.py](../../controlplane/policy/runner.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C021

**customer_support measured flag rate**

Retained value: `0.1062`. Retained interval: `[0.0885, 0.1260]`. Artifact equality: **MATCH**.

- Evidence: [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); field `operating_points[operating_point.operating_point_id=P-customer-support].metrics.flag_rate.value`.
- Artifact SHA-256: `32f7141dfcdfe0a855ca89526ba9444c9c9a0d858bb90d5ceadbb362e669f507`.
- Recorded source: `0ad8c769527b7345edf6abae92ec611780948b14`; dirty: `True`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F06: Three policy operating points](claim-families.md#f06); type `measured_resplit_study_with_provenance_gap`.

**Why this claim is included.** What does moving along one recorded detector curve buy for different declared profiles?

**What it means.** Flag rate is the observed fraction of rows at or above the threshold. It is not the requested false-positive budget; on a wholly benign set it equals descriptive FPR.

**Where the data and calculation come from.** [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/07_policy.py](../../scripts/07_policy.py); [controlplane/policy/runner.py](../../controlplane/policy/runner.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C022

**customer_support precision**

Retained value: `0.9216`. Retained interval: `[0.8676, 0.9684]`. Artifact equality: **MATCH**.

- Evidence: [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); field `operating_points[operating_point.operating_point_id=P-customer-support].metrics.precision.value`.
- Artifact SHA-256: `32f7141dfcdfe0a855ca89526ba9444c9c9a0d858bb90d5ceadbb362e669f507`.
- Recorded source: `0ad8c769527b7345edf6abae92ec611780948b14`; dirty: `True`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F06: Three policy operating points](claim-families.md#f06); type `measured_resplit_study_with_provenance_gap`.

**Why this claim is included.** What does moving along one recorded detector curve buy for different declared profiles?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/07_policy.py](../../scripts/07_policy.py); [controlplane/policy/runner.py](../../controlplane/policy/runner.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C023

**internal_knowledge recall, n=960**

Retained value: `0.3603`. Retained interval: `[0.3173, 0.4063]`. Artifact equality: **MATCH**.

- Evidence: [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); field `operating_points[operating_point.operating_point_id=P-internal-knowledge].metrics.recall.value`.
- Artifact SHA-256: `32f7141dfcdfe0a855ca89526ba9444c9c9a0d858bb90d5ceadbb362e669f507`.
- Recorded source: `0ad8c769527b7345edf6abae92ec611780948b14`; dirty: `True`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F06: Three policy operating points](claim-families.md#f06); type `measured_resplit_study_with_provenance_gap`.

**Why this claim is included.** What does moving along one recorded detector curve buy for different declared profiles?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/07_policy.py](../../scripts/07_policy.py); [controlplane/policy/runner.py](../../controlplane/policy/runner.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C024

**internal_knowledge measured flag rate**

Retained value: `0.1865`. Retained interval: `[0.1635, 0.2125]`. Artifact equality: **MATCH**.

- Evidence: [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); field `operating_points[operating_point.operating_point_id=P-internal-knowledge].metrics.flag_rate.value`.
- Artifact SHA-256: `32f7141dfcdfe0a855ca89526ba9444c9c9a0d858bb90d5ceadbb362e669f507`.
- Recorded source: `0ad8c769527b7345edf6abae92ec611780948b14`; dirty: `True`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F06: Three policy operating points](claim-families.md#f06); type `measured_resplit_study_with_provenance_gap`.

**Why this claim is included.** What does moving along one recorded detector curve buy for different declared profiles?

**What it means.** Flag rate is the observed fraction of rows at or above the threshold. It is not the requested false-positive budget; on a wholly benign set it equals descriptive FPR.

**Where the data and calculation come from.** [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/07_policy.py](../../scripts/07_policy.py); [controlplane/policy/runner.py](../../controlplane/policy/runner.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C025

**internal_knowledge precision**

Retained value: `0.8715`. Retained interval: `[0.8218, 0.9214]`. Artifact equality: **MATCH**.

- Evidence: [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); field `operating_points[operating_point.operating_point_id=P-internal-knowledge].metrics.precision.value`.
- Artifact SHA-256: `32f7141dfcdfe0a855ca89526ba9444c9c9a0d858bb90d5ceadbb362e669f507`.
- Recorded source: `0ad8c769527b7345edf6abae92ec611780948b14`; dirty: `True`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F06: Three policy operating points](claim-families.md#f06); type `measured_resplit_study_with_provenance_gap`.

**Why this claim is included.** What does moving along one recorded detector curve buy for different declared profiles?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/07_policy.py](../../scripts/07_policy.py); [controlplane/policy/runner.py](../../controlplane/policy/runner.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C026

**decision_support recall, n=960**

Retained value: `0.7367`. Retained interval: `[0.6974, 0.7783]`. Artifact equality: **MATCH**.

- Evidence: [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); field `operating_points[operating_point.operating_point_id=P-decision-support].metrics.recall.value`.
- Artifact SHA-256: `32f7141dfcdfe0a855ca89526ba9444c9c9a0d858bb90d5ceadbb362e669f507`.
- Recorded source: `0ad8c769527b7345edf6abae92ec611780948b14`; dirty: `True`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F06: Three policy operating points](claim-families.md#f06); type `measured_resplit_study_with_provenance_gap`.

**Why this claim is included.** What does moving along one recorded detector curve buy for different declared profiles?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/07_policy.py](../../scripts/07_policy.py); [controlplane/policy/runner.py](../../controlplane/policy/runner.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C027

**decision_support measured flag rate**

Retained value: `0.4677`. Retained interval: `[0.4365, 0.4990]`. Artifact equality: **MATCH**.

- Evidence: [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); field `operating_points[operating_point.operating_point_id=P-decision-support].metrics.flag_rate.value`.
- Artifact SHA-256: `32f7141dfcdfe0a855ca89526ba9444c9c9a0d858bb90d5ceadbb362e669f507`.
- Recorded source: `0ad8c769527b7345edf6abae92ec611780948b14`; dirty: `True`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F06: Three policy operating points](claim-families.md#f06); type `measured_resplit_study_with_provenance_gap`.

**Why this claim is included.** What does moving along one recorded detector curve buy for different declared profiles?

**What it means.** Flag rate is the observed fraction of rows at or above the threshold. It is not the requested false-positive budget; on a wholly benign set it equals descriptive FPR.

**Where the data and calculation come from.** [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/07_policy.py](../../scripts/07_policy.py); [controlplane/policy/runner.py](../../controlplane/policy/runner.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C028

**decision_support precision**

Retained value: `0.7105`. Retained interval: `[0.6690, 0.7506]`. Artifact equality: **MATCH**.

- Evidence: [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); field `operating_points[operating_point.operating_point_id=P-decision-support].metrics.precision.value`.
- Artifact SHA-256: `32f7141dfcdfe0a855ca89526ba9444c9c9a0d858bb90d5ceadbb362e669f507`.
- Recorded source: `0ad8c769527b7345edf6abae92ec611780948b14`; dirty: `True`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F06: Three policy operating points](claim-families.md#f06); type `measured_resplit_study_with_provenance_gap`.

**Why this claim is included.** What does moving along one recorded detector curve buy for different declared profiles?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [evalsets/triviaqa-2400-t960.json](../../evalsets/triviaqa-2400-t960.json); [scripts/07_policy.py](../../scripts/07_policy.py); [controlplane/policy/runner.py](../../controlplane/policy/runner.py); [controlplane/validation/metrics_builder.py](../../controlplane/validation/metrics_builder.py)

**What remains unproved.** The top-level provenance is dirty=true. These are retrospective within-project comparisons on a derived split, not new production traffic or an external held-out corpus. Frozen scores can replay supported metric blocks without repairing the original source provenance.

**Source caution:** DIRTY_SOURCE. A matching value does not reconstruct the original working tree.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C029

**Last-token probe survives the long-context shift**

Retained value: `0.8135`. Retained interval: `[0.7797, 0.8447]`. Artifact equality: **MATCH**.

- Evidence: [results/transfer-T1-last_token.json](../../results/transfer-T1-last_token.json); field `target.metrics.auroc.value`.
- Artifact SHA-256: `4675122d88b2d9bcc0a3ec13d882ee3f2122541127ef178cf6abcb3ea539d779`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F07: Pooling under long-context shift](claim-families.md#f07); type `paired_distribution_shift_measurement`.

**Why this claim is included.** Which fitted representations retain discrimination when distractor context changes the extraction envelope?

**What it means.** AUROC is the positive-versus-negative pair-ranking probability, with half credit for ties. It does not state recall at the selected budget.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [results/scores/transfer-T1-mean_pool.json](../../results/scores/transfer-T1-mean_pool.json); [results/scores/transfer-T1-max_rolling_means.json](../../results/scores/transfer-T1-max_rolling_means.json); [scripts/04_transfer.py](../../scripts/04_transfer.py); [controlplane/validation/runner.py](../../controlplane/validation/runner.py); [controlplane/detectors/aggregation.py](../../controlplane/detectors/aggregation.py)

**What remains unproved.** This is a paired representation-shift test, not newly generated long-context answer accuracy. Mean-signal dilution is a plausible explanation, not an independently isolated neural mechanism. One model family and constructed distractors cannot establish universal pooling rankings.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C030

**Mean-pool probe collapses to chance under it**

Retained value: `0.5015`. Retained interval: `[0.4546, 0.5479]`. Artifact equality: **MATCH**.

- Evidence: [results/transfer-T1-mean_pool.json](../../results/transfer-T1-mean_pool.json); field `target.metrics.auroc.value`.
- Artifact SHA-256: `39981530977e7c123b27c66ca07fc2cd1afce038d8ca0d4f575b61cfae56fc68`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F07: Pooling under long-context shift](claim-families.md#f07); type `paired_distribution_shift_measurement`.

**Why this claim is included.** Which fitted representations retain discrimination when distractor context changes the extraction envelope?

**What it means.** AUROC is the positive-versus-negative pair-ranking probability, with half credit for ties. It does not state recall at the selected budget.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [results/scores/transfer-T1-mean_pool.json](../../results/scores/transfer-T1-mean_pool.json); [results/scores/transfer-T1-max_rolling_means.json](../../results/scores/transfer-T1-max_rolling_means.json); [scripts/04_transfer.py](../../scripts/04_transfer.py); [controlplane/validation/runner.py](../../controlplane/validation/runner.py); [controlplane/detectors/aggregation.py](../../controlplane/detectors/aggregation.py)

**What remains unproved.** This is a paired representation-shift test, not newly generated long-context answer accuracy. Mean-signal dilution is a plausible explanation, not an independently isolated neural mechanism. One model family and constructed distractors cannot establish universal pooling rankings.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C031

**Max-rolling-means probe under it**

Retained value: `0.5553`. Retained interval: `[0.5105, 0.6015]`. Artifact equality: **MATCH**.

- Evidence: [results/transfer-T1-max_rolling_means.json](../../results/transfer-T1-max_rolling_means.json); field `target.metrics.auroc.value`.
- Artifact SHA-256: `783464e608ae49ca1065770aa1f37d5b5cea5ff092087f948eec862adc1a18e6`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F07: Pooling under long-context shift](claim-families.md#f07); type `paired_distribution_shift_measurement`.

**Why this claim is included.** Which fitted representations retain discrimination when distractor context changes the extraction envelope?

**What it means.** AUROC is the positive-versus-negative pair-ranking probability, with half credit for ties. It does not state recall at the selected budget.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [results/scores/transfer-T1-mean_pool.json](../../results/scores/transfer-T1-mean_pool.json); [results/scores/transfer-T1-max_rolling_means.json](../../results/scores/transfer-T1-max_rolling_means.json); [scripts/04_transfer.py](../../scripts/04_transfer.py); [controlplane/validation/runner.py](../../controlplane/validation/runner.py); [controlplane/detectors/aggregation.py](../../controlplane/detectors/aggregation.py)

**What remains unproved.** This is a paired representation-shift test, not newly generated long-context answer accuracy. Mean-signal dilution is a plausible explanation, not an independently isolated neural mechanism. One model family and constructed distractors cannot establish universal pooling rankings.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C032

**...and it flags 54% of the stream**

Retained value: `0.5433`. Retained interval: `[0.5050, 0.5833]`. Artifact equality: **MATCH**.

- Evidence: [results/transfer-T1-max_rolling_means.json](../../results/transfer-T1-max_rolling_means.json); field `target.metrics.flag_rate.value`.
- Artifact SHA-256: `783464e608ae49ca1065770aa1f37d5b5cea5ff092087f948eec862adc1a18e6`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F07: Pooling under long-context shift](claim-families.md#f07); type `paired_distribution_shift_measurement`.

**Why this claim is included.** Which fitted representations retain discrimination when distractor context changes the extraction envelope?

**What it means.** Flag rate is the observed fraction of rows at or above the threshold. It is not the requested false-positive budget; on a wholly benign set it equals descriptive FPR.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/transfer-T1-last_token.json](../../results/scores/transfer-T1-last_token.json); [results/scores/transfer-T1-mean_pool.json](../../results/scores/transfer-T1-mean_pool.json); [results/scores/transfer-T1-max_rolling_means.json](../../results/scores/transfer-T1-max_rolling_means.json); [scripts/04_transfer.py](../../scripts/04_transfer.py); [controlplane/validation/runner.py](../../controlplane/validation/runner.py); [controlplane/detectors/aggregation.py](../../controlplane/detectors/aggregation.py)

**What remains unproved.** This is a paired representation-shift test, not newly generated long-context answer accuracy. Mean-signal dilution is a plausible explanation, not an independently isolated neural mechanism. One model family and constructed distractors cannot establish universal pooling rankings.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C033

**Replayed shift to long context begins at request**

Retained value: `401`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/drift/revocation_trace.json](../../results/drift/revocation_trace.json); field `stream.shift_starts_at_request`.
- Artifact SHA-256: `21bee4cdb356084f361e2faa2af196e830fb58f1a70a095aa80b019ca29bb3ab`.
- Recorded source: `71d24345b4cb940af55751301666a6c7de49351c`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/28_revocation_trace.py`. This is not a claim that this audit executed that command.
- Evidence family: [F08: Drift and revocation trace](claim-families.md#f08); type `controlled_replay`.

**Why this claim is included.** Does the declared drift criterion revoke a retained warrant on a constructed distribution shift?

**What it means.** This request index locates the constructed shift in one replay, not a production incident time.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/transfer-T1-last_token.json](../../results/transfer-T1-last_token.json); [scripts/28_revocation_trace.py](../../scripts/28_revocation_trace.py); [controlplane/demo/revocation_trace.py](../../controlplane/demo/revocation_trace.py); [controlplane/drift/psi.py](../../controlplane/drift/psi.py)

**What remains unproved.** The request indices and PSI values are deterministic observations of this replay. They are not a production latency, false-alarm-rate estimate, general drift detector validation, or evidence that the source of a real shift can be diagnosed.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C034

**...the probe's warrant is revoked at request**

Retained value: `450`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/drift/revocation_trace.json](../../results/drift/revocation_trace.json); field `revocation.at_request`.
- Artifact SHA-256: `21bee4cdb356084f361e2faa2af196e830fb58f1a70a095aa80b019ca29bb3ab`.
- Recorded source: `71d24345b4cb940af55751301666a6c7de49351c`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/28_revocation_trace.py`. This is not a claim that this audit executed that command.
- Evidence family: [F08: Drift and revocation trace](claim-families.md#f08); type `controlled_replay`.

**Why this claim is included.** Does the declared drift criterion revoke a retained warrant on a constructed distribution shift?

**What it means.** This request index locates the recorded revocation under that replay's window and criteria, not a general detection delay guarantee.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/transfer-T1-last_token.json](../../results/transfer-T1-last_token.json); [scripts/28_revocation_trace.py](../../scripts/28_revocation_trace.py); [controlplane/demo/revocation_trace.py](../../controlplane/demo/revocation_trace.py); [controlplane/drift/psi.py](../../controlplane/drift/psi.py)

**What remains unproved.** The request indices and PSI values are deterministic observations of this replay. They are not a production latency, false-alarm-rate estimate, general drift detector validation, or evidence that the source of a real shift can be diagnosed.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C035

**...at a PSI of**

Retained value: `0.3526`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/drift/revocation_trace.json](../../results/drift/revocation_trace.json); field `checkpoints[after_request=450].psi`.
- Artifact SHA-256: `21bee4cdb356084f361e2faa2af196e830fb58f1a70a095aa80b019ca29bb3ab`.
- Recorded source: `71d24345b4cb940af55751301666a6c7de49351c`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/28_revocation_trace.py`. This is not a claim that this audit executed that command.
- Evidence family: [F08: Drift and revocation trace](claim-families.md#f08); type `controlled_replay`.

**Why this claim is included.** Does the declared drift criterion revoke a retained warrant on a constructed distribution shift?

**What it means.** This is the PSI value at the named checkpoint and declared binning. It is not an error rate or a calibrated probability of drift.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/transfer-T1-last_token.json](../../results/transfer-T1-last_token.json); [scripts/28_revocation_trace.py](../../scripts/28_revocation_trace.py); [controlplane/demo/revocation_trace.py](../../controlplane/demo/revocation_trace.py); [controlplane/drift/psi.py](../../controlplane/drift/psi.py)

**What remains unproved.** The request indices and PSI values are deterministic observations of this replay. They are not a production latency, false-alarm-rate estimate, general drift detector validation, or evidence that the source of a real shift can be diagnosed.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C036

**...where the last all-normal window read**

Retained value: `0.0543`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/drift/revocation_trace.json](../../results/drift/revocation_trace.json); field `checkpoints[after_request=400].psi`.
- Artifact SHA-256: `21bee4cdb356084f361e2faa2af196e830fb58f1a70a095aa80b019ca29bb3ab`.
- Recorded source: `71d24345b4cb940af55751301666a6c7de49351c`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/28_revocation_trace.py`. This is not a claim that this audit executed that command.
- Evidence family: [F08: Drift and revocation trace](claim-families.md#f08); type `controlled_replay`.

**Why this claim is included.** Does the declared drift criterion revoke a retained warrant on a constructed distribution shift?

**What it means.** This is the prior all-normal checkpoint in the same replay. Its comparison is conditional on the replay and monitoring configuration.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/transfer-T1-last_token.json](../../results/transfer-T1-last_token.json); [scripts/28_revocation_trace.py](../../scripts/28_revocation_trace.py); [controlplane/demo/revocation_trace.py](../../controlplane/demo/revocation_trace.py); [controlplane/drift/psi.py](../../controlplane/drift/psi.py)

**What remains unproved.** The request indices and PSI values are deterministic observations of this replay. They are not a production latency, false-alarm-rate estimate, general drift detector validation, or evidence that the source of a real shift can be diagnosed.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C037

**Warrant matrix cells VALID**

Retained value: `13`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/warrant_matrix.json](../../results/warrant_matrix.json); field `matrix.summary.VALID`.
- Artifact SHA-256: `6aa90bbd58ea8328269b996e7e90d79cdc500d85e73253369125c36c44b01d5e`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F09: Warrant-matrix inventory](claim-families.md#f09); type `mixed_measured_and_fixture_inventory`.

**Why this claim is included.** Which detector-envelope combinations have a recorded state, and which remain unvalidated?

**What it means.** This counts retained VALID matrix cells, including synthetic fixtures and historical method records. It does not count independently deployed models.

**Where the data and calculation come from.** [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json); [results/detectors.json](../../results/detectors.json); [scripts/03_matrix.py](../../scripts/03_matrix.py); [controlplane/matrix/matrix.py](../../controlplane/matrix/matrix.py); [controlplane/matrix/routing.py](../../controlplane/matrix/routing.py)

**What remains unproved.** Some VALID cells are fixtures; some historical hard-negative cells use legacy row-count inference. Current eligibility must inspect the evidence protocol and data source, not use a historical VALID string alone. UNVALIDATED is absence of a run, not a negative performance result.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C038

**Warrant matrix cells REFUSED**

Retained value: `4`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/warrant_matrix.json](../../results/warrant_matrix.json); field `matrix.summary.REFUSED`.
- Artifact SHA-256: `6aa90bbd58ea8328269b996e7e90d79cdc500d85e73253369125c36c44b01d5e`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F09: Warrant-matrix inventory](claim-families.md#f09); type `mixed_measured_and_fixture_inventory`.

**Why this claim is included.** Which detector-envelope combinations have a recorded state, and which remain unvalidated?

**What it means.** This counts cells with a recorded refusal under their historical criteria. It is not a prevalence of detector failure in the world.

**Where the data and calculation come from.** [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json); [results/detectors.json](../../results/detectors.json); [scripts/03_matrix.py](../../scripts/03_matrix.py); [controlplane/matrix/matrix.py](../../controlplane/matrix/matrix.py); [controlplane/matrix/routing.py](../../controlplane/matrix/routing.py)

**What remains unproved.** Some VALID cells are fixtures; some historical hard-negative cells use legacy row-count inference. Current eligibility must inspect the evidence protocol and data source, not use a historical VALID string alone. UNVALIDATED is absence of a run, not a negative performance result.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C039

**Warrant matrix cells never measured**

Retained value: `39`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/warrant_matrix.json](../../results/warrant_matrix.json); field `matrix.summary.UNVALIDATED`.
- Artifact SHA-256: `6aa90bbd58ea8328269b996e7e90d79cdc500d85e73253369125c36c44b01d5e`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F09: Warrant-matrix inventory](claim-families.md#f09); type `mixed_measured_and_fixture_inventory`.

**Why this claim is included.** Which detector-envelope combinations have a recorded state, and which remain unvalidated?

**What it means.** This counts combinations with no qualifying recorded run. Missing evidence is different from a negative result.

**Where the data and calculation come from.** [results/validation-T1-last_token.json](../../results/validation-T1-last_token.json); [results/detectors.json](../../results/detectors.json); [scripts/03_matrix.py](../../scripts/03_matrix.py); [controlplane/matrix/matrix.py](../../controlplane/matrix/matrix.py); [controlplane/matrix/routing.py](../../controlplane/matrix/routing.py)

**What remains unproved.** Some VALID cells are fixtures; some historical hard-negative cells use legacy row-count inference. Current eligibility must inspect the evidence protocol and data source, not use a historical VALID string alone. UNVALIDATED is absence of a run, not a negative performance result.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C040

**presidio-stock recall on Hinglish PII, REFUSED**

Retained value: `0.1176`. Retained interval: `[0.0500, 0.2000]`. Artifact equality: **MATCH**.

- Evidence: [results/detectors.json](../../results/detectors.json); field `runs[detector_id=presidio-stock,eval_set_id=hinglish-pii-200].metrics.recall.value`.
- Artifact SHA-256: `49c2eb238b1095819fbe466f242f5c900ef66994860e5384f53f131bacc026fc`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C041

**...its precision there**

Retained value: `0.5455`. Retained interval: `[0.2592, 0.9002]`. Artifact equality: **MATCH**.

- Evidence: [results/detectors.json](../../results/detectors.json); field `runs[detector_id=presidio-stock,eval_set_id=hinglish-pii-200].metrics.precision.value`.
- Artifact SHA-256: `49c2eb238b1095819fbe466f242f5c900ef66994860e5384f53f131bacc026fc`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C042

**presidio-enabled recall, REFUSED**

Retained value: `0.2843`. Retained interval: `[0.2075, 0.3810]`. Artifact equality: **MATCH**.

- Evidence: [results/detectors.json](../../results/detectors.json); field `runs[detector_id=presidio-enabled,eval_set_id=hinglish-pii-200].metrics.recall.value`.
- Artifact SHA-256: `49c2eb238b1095819fbe466f242f5c900ef66994860e5384f53f131bacc026fc`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C043

**...its precision there**

Retained value: `0.7436`. Retained interval: `[0.5416, 0.9584]`. Artifact equality: **MATCH**.

- Evidence: [results/detectors.json](../../results/detectors.json); field `runs[detector_id=presidio-enabled,eval_set_id=hinglish-pii-200].metrics.precision.value`.
- Artifact SHA-256: `49c2eb238b1095819fbe466f242f5c900ef66994860e5384f53f131bacc026fc`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C044

**presidio-enabled_plus_custom recall, VALID**

Retained value: `0.6176`. Retained interval: `[0.5185, 0.7128]`. Artifact equality: **MATCH**.

- Evidence: [results/detectors.json](../../results/detectors.json); field `runs[detector_id=presidio-enabled_plus_custom,eval_set_id=hinglish-pii-200].metrics.recall.value`.
- Artifact SHA-256: `49c2eb238b1095819fbe466f242f5c900ef66994860e5384f53f131bacc026fc`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C045

**...its precision there**

Retained value: `0.8630`. Retained interval: `[0.7262, 0.9828]`. Artifact equality: **MATCH**.

- Evidence: [results/detectors.json](../../results/detectors.json); field `runs[detector_id=presidio-enabled_plus_custom,eval_set_id=hinglish-pii-200].metrics.precision.value`.
- Artifact SHA-256: `49c2eb238b1095819fbe466f242f5c900ef66994860e5384f53f131bacc026fc`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C046

**Our pii-reference recall, VALID**

Retained value: `0.7941`. Retained interval: `[0.6981, 0.8846]`. Artifact equality: **MATCH**.

- Evidence: [results/detectors.json](../../results/detectors.json); field `runs[detector_id=pii-reference,eval_set_id=hinglish-pii-200].metrics.recall.value`.
- Artifact SHA-256: `49c2eb238b1095819fbe466f242f5c900ef66994860e5384f53f131bacc026fc`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C047

**...its precision there**

Retained value: `0.6532`. Retained interval: `[0.5114, 0.8100]`. Artifact equality: **MATCH**.

- Evidence: [results/detectors.json](../../results/detectors.json); field `runs[detector_id=pii-reference,eval_set_id=hinglish-pii-200].metrics.precision.value`.
- Artifact SHA-256: `49c2eb238b1095819fbe466f242f5c900ef66994860e5384f53f131bacc026fc`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C048

**presidio-stock reproduces out of sample**

Retained value: `0.1471`. Retained interval: `[0.0714, 0.2341]`. Artifact equality: **MATCH**.

- Evidence: [results/holdout/detectors.json](../../results/holdout/detectors.json); field `runs[detector_id=presidio-stock,eval_set_id=hinglish-pii-200b].metrics.recall.value`.
- Artifact SHA-256: `4ee28992c807f70bc42e2ed884db7171ce49aaff1ea1c521f9def95479815b1f`.
- Recorded source: `cd1cc243750e05e646b7d961e70aca7aae1589a7`; dirty: `False`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Recall is the fraction of labeled positive rows flagged at this operating point. It must be read alongside the same cohort's precision and realized flag rate.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C049

**...its precision there**

Retained value: `0.5357`. Retained interval: `[0.2812, 0.8621]`. Artifact equality: **MATCH**.

- Evidence: [results/holdout/detectors.json](../../results/holdout/detectors.json); field `runs[detector_id=presidio-stock,eval_set_id=hinglish-pii-200b].metrics.precision.value`.
- Artifact SHA-256: `4ee28992c807f70bc42e2ed884db7171ce49aaff1ea1c521f9def95479815b1f`.
- Recorded source: `cd1cc243750e05e646b7d961e70aca7aae1589a7`; dirty: `False`; config: `ae6eec9d1f8897af`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F10: PII configurations and companion set](claim-families.md#f10); type `measured_handcrafted_challenge_set`.

**Why this claim is included.** How do explicit recognizer configuration and disclosed custom patterns affect detection on the constructed PII cases?

**What it means.** Precision is the positive share among flagged rows, not among all rows. It depends on prevalence and cannot be transported to another population without assumptions.

**Where the data and calculation come from.** [evalsets/hinglish-pii-200.json](../../evalsets/hinglish-pii-200.json); [evalsets/hinglish-pii-200b.json](../../evalsets/hinglish-pii-200b.json); [scripts/09_detectors.py](../../scripts/09_detectors.py); [controlplane/detectors/presidio_adapter.py](../../controlplane/detectors/presidio_adapter.py); [controlplane/detectors/presidio_custom.py](../../controlplane/detectors/presidio_custom.py); [controlplane/detectors/pii_reference.py](../../controlplane/detectors/pii_reference.py)

**What remains unproved.** The cases are hand-authored and enriched for positives, so precision does not transport to production prevalence. Companion variants are not independently authored real traffic. Custom rules were designed with knowledge of the base inventory. These results do not establish the general quality of current Presidio releases.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C050

**pii-reference historical row flag rate on a hand-built benign set**

Retained value: `0.0000`. Retained interval: `[0.0000, 0.0183]`. Artifact equality: **MATCH**.

- Evidence: [results/validation-pii-reference-hard-negatives-200.json](../../results/validation-pii-reference-hard-negatives-200.json); field `metrics.flag_rate.value`.
- Artifact SHA-256: `77ad0d6f33088578804e05a8ca8ca95305d5d4d73eaf97104ce790985355a60d`.
- Recorded source: `05b2a52193f089943edfbbb4c547bf5b9625a3d8`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `make verify`. This is not a claim that this audit executed that command.
- Evidence family: [F11: Benign hard-negative result](claim-families.md#f11); type `historical_dependent_rows`.

**Why this claim is included.** How often did the reference detector fire on the declared benign challenge rows?

**What it means.** Flag rate is the observed fraction of rows at or above the threshold. It is not the requested false-positive budget; on a wholly benign set it equals descriptive FPR.

**Where the data and calculation come from.** [evalsets/hard-negatives-200.json](../../evalsets/hard-negatives-200.json); [results/scores/text-pii-reference-hard-negatives-200.json](../../results/scores/text-pii-reference-hard-negatives-200.json); [controlplane/evalsets/hard_negatives.py](../../controlplane/evalsets/hard_negatives.py); [controlplane/validation/text_runner.py](../../controlplane/validation/text_runner.py); [controlplane/validation/metric_protocols.py](../../controlplane/validation/metric_protocols.py)

**What remains unproved.** Dependent framings are not independent Bernoulli trials. The old row interval is not current group-aware assurance. A zero observed count does not establish zero population risk. No AUROC, recall or precision is defined for this single-class set.

**Additional arithmetic check:** a separate rank/count oracle agrees with the frozen-score point estimate. Confidence intervals, label truth and warrant issuance are outside that oracle.

## C051

**Abstention floor at a 5% residual-risk target**

Retained value: `0.4221`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/feasibility.json](../../results/feasibility.json); field `abstention_floor[target_risk=0.05].floor`.
- Artifact SHA-256: `8b366a92eff835210a983bedd2263ef56f98da68af9a5e865bddd2be402d5402`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/11_feasibility.py`. This is not a claim that this audit executed that command.
- Evidence family: [F12: Abstention feasibility](claim-families.md#f12); type `declared_scenario_calculation`.

**Why this claim is included.** What fraction must a perfect error selector abstain on to attain a chosen residual-risk target?

**What it means.** This is the ideal abstention floor for the stated residual-risk target and source prevalence, assuming perfect error selection.

**Where the data and calculation come from.** [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); [config.yaml](../../config.yaml); [scripts/11_feasibility.py](../../scripts/11_feasibility.py); [controlplane/economics/feasibility.py](../../controlplane/economics/feasibility.py)

**What remains unproved.** The ideal selector is not an implemented model. These are conditional arithmetic consequences of their inputs. The source policy artifact has dirty provenance, and its measurement population differs from a declared production workload. No ROI, savings or buyer value is measured.

**Upstream caution:** declared input references include dirty-source evidence: results/policy-triviaqa-2400-t960.json.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C052

**...at a 10% target**

Retained value: `0.3900`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/feasibility.json](../../results/feasibility.json); field `abstention_floor[target_risk=0.1].floor`.
- Artifact SHA-256: `8b366a92eff835210a983bedd2263ef56f98da68af9a5e865bddd2be402d5402`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/11_feasibility.py`. This is not a claim that this audit executed that command.
- Evidence family: [F12: Abstention feasibility](claim-families.md#f12); type `declared_scenario_calculation`.

**Why this claim is included.** What fraction must a perfect error selector abstain on to attain a chosen residual-risk target?

**What it means.** This is the same idealized calculation at a different declared residual-risk target, not a separately measured detector.

**Where the data and calculation come from.** [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); [config.yaml](../../config.yaml); [scripts/11_feasibility.py](../../scripts/11_feasibility.py); [controlplane/economics/feasibility.py](../../controlplane/economics/feasibility.py)

**What remains unproved.** The ideal selector is not an implemented model. These are conditional arithmetic consequences of their inputs. The source policy artifact has dirty provenance, and its measurement population differs from a declared production workload. No ROI, savings or buyer value is measured.

**Upstream caution:** declared input references include dirty-source evidence: results/policy-triviaqa-2400-t960.json.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C053

**Residual risk decision_support actually ships**

Retained value: `0.2231`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/feasibility.json](../../results/feasibility.json); field `profiles[operating_point_id=P-decision-support].achieved_risk.residual_risk`.
- Artifact SHA-256: `8b366a92eff835210a983bedd2263ef56f98da68af9a5e865bddd2be402d5402`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/11_feasibility.py`. This is not a claim that this audit executed that command.
- Evidence family: [F12: Abstention feasibility](claim-families.md#f12); type `declared_scenario_calculation`.

**Why this claim is included.** What fraction must a perfect error selector abstain on to attain a chosen residual-risk target?

**What it means.** Residual risk is the error share remaining among unflagged items under the measured profile rates. It is not a measured customer risk.

**Where the data and calculation come from.** [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); [config.yaml](../../config.yaml); [scripts/11_feasibility.py](../../scripts/11_feasibility.py); [controlplane/economics/feasibility.py](../../controlplane/economics/feasibility.py)

**What remains unproved.** The ideal selector is not an implemented model. These are conditional arithmetic consequences of their inputs. The source policy artifact has dirty provenance, and its measurement population differs from a declared production workload. No ROI, savings or buyer value is measured.

**Upstream caution:** declared input references include dirty-source evidence: results/policy-triviaqa-2400-t960.json.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C054

**...costing this multiple of the perfect-selector floor**

Retained value: `1.5941`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/feasibility.json](../../results/feasibility.json); field `profiles[operating_point_id=P-decision-support].achieved_risk.efficiency`.
- Artifact SHA-256: `8b366a92eff835210a983bedd2263ef56f98da68af9a5e865bddd2be402d5402`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/11_feasibility.py`. This is not a claim that this audit executed that command.
- Evidence family: [F12: Abstention feasibility](claim-families.md#f12); type `declared_scenario_calculation`.

**Why this claim is included.** What fraction must a perfect error selector abstain on to attain a chosen residual-risk target?

**What it means.** Efficiency is actual abstention divided by the perfect-selector floor at the achieved residual risk. It describes distance from an ideal, not inference speed.

**Where the data and calculation come from.** [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); [config.yaml](../../config.yaml); [scripts/11_feasibility.py](../../scripts/11_feasibility.py); [controlplane/economics/feasibility.py](../../controlplane/economics/feasibility.py)

**What remains unproved.** The ideal selector is not an implemented model. These are conditional arithmetic consequences of their inputs. The source policy artifact has dirty provenance, and its measurement population differs from a declared production workload. No ROI, savings or buyer value is measured.

**Upstream caution:** declared input references include dirty-source evidence: results/policy-triviaqa-2400-t960.json.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C055

**customer_support at the same measure**

Retained value: `1.1490`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/feasibility.json](../../results/feasibility.json); field `profiles[operating_point_id=P-customer-support].achieved_risk.efficiency`.
- Artifact SHA-256: `8b366a92eff835210a983bedd2263ef56f98da68af9a5e865bddd2be402d5402`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/11_feasibility.py`. This is not a claim that this audit executed that command.
- Evidence family: [F12: Abstention feasibility](claim-families.md#f12); type `declared_scenario_calculation`.

**Why this claim is included.** What fraction must a perfect error selector abstain on to attain a chosen residual-risk target?

**What it means.** This applies the same ideal-floor efficiency definition to the customer-support profile. Different profiles must retain their own rates.

**Where the data and calculation come from.** [results/policy-triviaqa-2400-t960.json](../../results/policy-triviaqa-2400-t960.json); [config.yaml](../../config.yaml); [scripts/11_feasibility.py](../../scripts/11_feasibility.py); [controlplane/economics/feasibility.py](../../controlplane/economics/feasibility.py)

**What remains unproved.** The ideal selector is not an implemented model. These are conditional arithmetic consequences of their inputs. The source policy artifact has dirty provenance, and its measurement population differs from a declared production workload. No ROI, savings or buyer value is measured.

**Upstream caution:** declared input references include dirty-source evidence: results/policy-triviaqa-2400-t960.json.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C056

**dR/dq at the declared workload**

Retained value: `-4.6496`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.derivative`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This is the negative derivative of recall with respect to unflagged error prevalence, holding the flagged census and unflagged volume fixed.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C057

**Unflagged pool against confirmed true positives**

Retained value: `231.9`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.amplification_over_confirmed_errors`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This ratio uses the unflagged pool and confirmed true positives. It explains amplification in recall sensitivity; it is not the unflagged-to-flagged pool ratio.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C058

**...against the flagged pool, which is a different ratio**

Retained value: `66.0`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.pool_ratio_over_flagged`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This separate ratio divides the unflagged pool by the entire flagged pool. Interchanging these denominators causes a sizing error.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C059

**Labels for recall +/-0.05, month one, full SRS cost, 0.80 assurance**

Retained value: `1399`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.labels_month_one_5pp`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This is a label plan for the declared first-month regime, margin and assurance target. It incorporates more than a first-order derivative calculation.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C060

**...at steady state, Neyman at the measured design effect**

Retained value: `1109`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.labels_steady_state_5pp`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This is the steady-state label plan conditional on the measured simulation design effect and available band-prevalence information.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C061

**...what the superseded sizing quoted (DECISIONS 147)**

Retained value: `187`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.superseded_sizing_5pp`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This is a superseded historical sizing result retained to expose the earlier error. It is not a current recommendation.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C062

**Labels for recall +/-0.02, month one**

Retained value: `6518`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.labels_month_one_2pp`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This is the first-month label plan for the tighter declared recall margin; its workload and assurance assumptions still apply.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C063

**Recall-interval coverage, 1000 trials, nominal 0.95**

Retained value: `0.9680`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.coverage`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This is the observed fraction of simulated intervals covering the known simulated recall. It has Monte Carlo error and is not customer validation.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C064

**...over how many trials**

Retained value: `1000`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.coverage_trials`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This counts simulated trials behind the coverage proportion. It is not a count of independent production deployments.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C065

**Measured Neyman design effect vs the declared 0.67**

Retained value: `0.7929`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/on_traffic/on_traffic.json](../../results/on_traffic/on_traffic.json); field `headline.measured_design_effect`.
- Artifact SHA-256: `883f3c3dfd126747d83ae02f8bff8f16edfee21b17192044e1e8ff94731abb25`.
- Recorded source: `478b02af7619a5aa822ea73fac451ca16c9f3e8b`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/25_on_traffic.py`. This is not a claim that this audit executed that command.
- Evidence family: [F13: On-traffic review planning](claim-families.md#f13); type `simulation_and_declared_workload`.

**Why this claim is included.** What labels would the declared workload need to estimate recall, and does the interval cover in its controlled simulation?

**What it means.** This is the measured allocation design effect in the declared simulation. It is different from the earlier declared expectation.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/25_on_traffic.py](../../scripts/25_on_traffic.py); [controlplane/sampling/planning.py](../../controlplane/sampling/planning.py); [controlplane/sampling/estimator.py](../../controlplane/sampling/estimator.py); [controlplane/sampling/allocation.py](../../controlplane/sampling/allocation.py)

**What remains unproved.** No production traffic or paid review process was observed. The workload rates are declared inputs, even where their field names contain measured. The headline label count is not recovered from the derivative alone. The superseded count is historical failure evidence, not a current recommendation. Simulation coverage is local to its design.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C066

**A year of weekly per-recheck tests revokes a detector that kept its promise, share of simulated years (DECISIONS 187)**

Retained value: `0.8515`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/recheck_schedules/comparison.json](../../results/recheck_schedules/comparison.json); field `cells[rule=fixed,cadence=weekly,scenario=S0].revoked_in_year.value`.
- Artifact SHA-256: `a1ff3cb8ee7a4e15ef92695a0d59c451e2f2451bad1d17f683997b2d6e003890`.
- Recorded source: `b8b0f00c38170bed8c4d7a42d5380c304e1eddd6`; dirty: `False`; config: `91a7d65c347e688c`.
- Recorded check/regeneration entry: `python scripts/29_recheck_schedules.py`. This is not a claim that this audit executed that command.
- Evidence family: [F14: Year-long recheck comparisons](claim-families.md#f14); type `historical_simulation`.

**Why this claim is included.** How do repeated revocation rules trade false revocation and delayed breach detection on the same simulated labels?

**What it means.** This is the share of simulated years revoked by repeated fixed tests when the true rate is at the declared budget.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/29_recheck_schedules.py](../../scripts/29_recheck_schedules.py); [controlplane/economics/schedules.py](../../controlplane/economics/schedules.py)

**What remains unproved.** These are Monte Carlo characteristics of decision rules, not detector performance. The monitor cell is the historical capped implementation from Decision 187, not the repaired runtime in Decision 226. Apparent failure of repeated fixed tests is not evidence that all monitoring methods fail.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C067

**...a chained recheck on the same labels (DECISIONS 193)**

Retained value: `0.0085`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/recheck_schedules/comparison.json](../../results/recheck_schedules/comparison.json); field `cells[rule=e_detector,cadence=weekly,scenario=S0].revoked_in_year.value`.
- Artifact SHA-256: `a1ff3cb8ee7a4e15ef92695a0d59c451e2f2451bad1d17f683997b2d6e003890`.
- Recorded source: `b8b0f00c38170bed8c4d7a42d5380c304e1eddd6`; dirty: `False`; config: `91a7d65c347e688c`.
- Recorded check/regeneration entry: `python scripts/29_recheck_schedules.py`. This is not a claim that this audit executed that command.
- Evidence family: [F14: Year-long recheck comparisons](claim-families.md#f14); type `historical_simulation`.

**Why this claim is included.** How do repeated revocation rules trade false revocation and delayed breach detection on the same simulated labels?

**What it means.** This is the corresponding simulated false-revocation share for the finite-horizon chained rule on the same design.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/29_recheck_schedules.py](../../scripts/29_recheck_schedules.py); [controlplane/economics/schedules.py](../../controlplane/economics/schedules.py)

**What remains unproved.** These are Monte Carlo characteristics of decision rules, not detector performance. The monitor cell is the historical capped implementation from Decision 187, not the repaired runtime in Decision 226. Apparent failure of repeated fixed tests is not evidence that all monitoring methods fail.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C068

**A breach after six months at the certified rate, caught within 13 weeks, by the historical capped monitor (Decision 187; not the repaired runtime)**

Retained value: `0.0005`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/recheck_schedules/comparison.json](../../results/recheck_schedules/comparison.json); field `cells[rule=monitor,cadence=weekly,scenario=S3].caught_in_window.value`.
- Artifact SHA-256: `a1ff3cb8ee7a4e15ef92695a0d59c451e2f2451bad1d17f683997b2d6e003890`.
- Recorded source: `b8b0f00c38170bed8c4d7a42d5380c304e1eddd6`; dirty: `False`; config: `91a7d65c347e688c`.
- Recorded check/regeneration entry: `python scripts/29_recheck_schedules.py`. This is not a claim that this audit executed that command.
- Evidence family: [F14: Year-long recheck comparisons](claim-families.md#f14); type `historical_simulation`.

**Why this claim is included.** How do repeated revocation rules trade false revocation and delayed breach detection on the same simulated labels?

**What it means.** This catch proportion concerns the historical capped monitor. The runtime repair is a different implementation and must not inherit this result.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/29_recheck_schedules.py](../../scripts/29_recheck_schedules.py); [controlplane/economics/schedules.py](../../controlplane/economics/schedules.py)

**What remains unproved.** These are Monte Carlo characteristics of decision rules, not detector performance. The monitor cell is the historical capped implementation from Decision 187, not the repaired runtime in Decision 226. Apparent failure of repeated fixed tests is not evidence that all monitoring methods fail.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C069

**...by the chained recheck**

Retained value: `1.0000`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/recheck_schedules/comparison.json](../../results/recheck_schedules/comparison.json); field `cells[rule=e_detector,cadence=weekly,scenario=S3].caught_in_window.value`.
- Artifact SHA-256: `a1ff3cb8ee7a4e15ef92695a0d59c451e2f2451bad1d17f683997b2d6e003890`.
- Recorded source: `b8b0f00c38170bed8c4d7a42d5380c304e1eddd6`; dirty: `False`; config: `91a7d65c347e688c`.
- Recorded check/regeneration entry: `python scripts/29_recheck_schedules.py`. This is not a claim that this audit executed that command.
- Evidence family: [F14: Year-long recheck comparisons](claim-families.md#f14); type `historical_simulation`.

**Why this claim is included.** How do repeated revocation rules trade false revocation and delayed breach detection on the same simulated labels?

**What it means.** This is the chained rule's catch proportion in the named breach scenario and window. An observed proportion of one is not certainty on all streams.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/29_recheck_schedules.py](../../scripts/29_recheck_schedules.py); [controlplane/economics/schedules.py](../../controlplane/economics/schedules.py)

**What remains unproved.** These are Monte Carlo characteristics of decision rules, not detector performance. The monitor cell is the historical capped implementation from Decision 187, not the repaired runtime in Decision 226. Apparent failure of repeated fixed tests is not evidence that all monitoring methods fail.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C070

**Monthly chained rechecks, 628 negatives each, catch a 1.5x breach within three months, share of simulated years (DECISIONS 196)**

Retained value: `0.8325`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/chain_detection/grid.json](../../results/chain_detection/grid.json); field `cells[breach=0.075,cadence=monthly-6,scenario=S2,rule=e_detector].caught_in_window.value`.
- Artifact SHA-256: `50e6ac0abb5477af25bcf5322c1b78a647146a3edf3c751e0447dd67ee93bf56`.
- Recorded source: `c300d2769243842164cc25e76c2c94698fb02f67`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/31_chain_detection.py`. This is not a claim that this audit executed that command.
- Evidence family: [F15: Chained detection grid](claim-families.md#f15); type `finite_horizon_simulation`.

**Why this claim is included.** How does a fixed chained rule detect several declared breach sizes and change times?

**What it means.** This is a simulated catch-window proportion for a particular monthly schedule, breach and change point.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/31_chain_detection.py](../../scripts/31_chain_detection.py); [controlplane/economics/detection_grid.py](../../controlplane/economics/detection_grid.py); [controlplane/economics/schedules.py](../../controlplane/economics/schedules.py)

**What remains unproved.** A share of 1.0 means every simulated year in that cell, not certainty for all future streams. Detection probability depends on the breach, label supply, change time and horizon. These simulations are not external validation on customer traffic.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C071

**...weekly, a 1.5x breach from week 26, within 13 weeks**

Retained value: `0.9965`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/chain_detection/grid.json](../../results/chain_detection/grid.json); field `cells[breach=0.075,cadence=weekly-26,scenario=S2,rule=e_detector].caught_in_window.value`.
- Artifact SHA-256: `50e6ac0abb5477af25bcf5322c1b78a647146a3edf3c751e0447dd67ee93bf56`.
- Recorded source: `c300d2769243842164cc25e76c2c94698fb02f67`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/31_chain_detection.py`. This is not a claim that this audit executed that command.
- Evidence family: [F15: Chained detection grid](claim-families.md#f15); type `finite_horizon_simulation`.

**Why this claim is included.** How does a fixed chained rule detect several declared breach sizes and change times?

**What it means.** This is the corresponding particular weekly setting. It does not make weekly monitoring universally preferable or free of labeling cost.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/31_chain_detection.py](../../scripts/31_chain_detection.py); [controlplane/economics/detection_grid.py](../../controlplane/economics/detection_grid.py); [controlplane/economics/schedules.py](../../controlplane/economics/schedules.py)

**What remains unproved.** A share of 1.0 means every simulated year in that cell, not certainty for all future streams. Detection probability depends on the breach, label supply, change time and horizon. These simulations are not external validation on customer traffic.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C072

**This project's measured TriviaQA certificates: the fewest flagged positives that, if really clean, take one below 0.80 confidence, over all certified rows (DECISIONS 199)**

Retained value: `2`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/label_sensitivity/triviaqa.json](../../results/label_sensitivity/triviaqa.json); field `criteria.reported.flagged_clean_errors_to_fall_below_0_80_min`.
- Artifact SHA-256: `235e3a676dfc84e20a127b4fa5500f73d9d7333acb07e6acadf6417a01ffda48`.
- Recorded source: `bb800beeb00aeaeaf0a40e7dfb43e2850c321591`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/32_label_sensitivity.py`. This is not a claim that this audit executed that command.
- Evidence family: [F16: Label-sensitivity study](claim-families.md#f16); type `exact_sensitivity_on_recorded_labels`.

**Why this claim is included.** How sensitive are the retained certificate calculations to specified possible label errors?

**What it means.** This is the least label-count robustness among the retained certificate rows under the specified confidence-sensitivity calculation.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/validation-T1-mean_pool.json](../../results/scores/validation-T1-mean_pool.json); [results/scores/validation-T1-max_rolling_means.json](../../results/scores/validation-T1-max_rolling_means.json); [scripts/32_label_sensitivity.py](../../scripts/32_label_sensitivity.py); [controlplane/validation/label_error.py](../../controlplane/validation/label_error.py); [controlplane/extract/triviaqa.py](../../controlplane/extract/triviaqa.py)

**What remains unproved.** Disagreement is not a proven error, and strict matching is not a human gold standard. The confidence-under-perturbation calculation is conditional on its assumptions and must not be read as validation of the general adaptive returned bound. The original label truth is unresolved.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C073

**...the most, over the same rows**

Retained value: `8`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/label_sensitivity/triviaqa.json](../../results/label_sensitivity/triviaqa.json); field `criteria.reported.flagged_clean_errors_to_fall_below_0_80_max`.
- Artifact SHA-256: `235e3a676dfc84e20a127b4fa5500f73d9d7333acb07e6acadf6417a01ffda48`.
- Recorded source: `bb800beeb00aeaeaf0a40e7dfb43e2850c321591`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/32_label_sensitivity.py`. This is not a claim that this audit executed that command.
- Evidence family: [F16: Label-sensitivity study](claim-families.md#f16); type `exact_sensitivity_on_recorded_labels`.

**Why this claim is included.** How sensitive are the retained certificate calculations to specified possible label errors?

**What it means.** This is the greatest robustness over that same declared set. It is not a population range for arbitrary detectors.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/validation-T1-mean_pool.json](../../results/scores/validation-T1-mean_pool.json); [results/scores/validation-T1-max_rolling_means.json](../../results/scores/validation-T1-max_rolling_means.json); [scripts/32_label_sensitivity.py](../../scripts/32_label_sensitivity.py); [controlplane/validation/label_error.py](../../controlplane/validation/label_error.py); [controlplane/extract/triviaqa.py](../../controlplane/extract/triviaqa.py)

**What remains unproved.** Disagreement is not a proven error, and strict matching is not a human gold standard. The confidence-under-perturbation calculation is conditional on its assumptions and must not be read as validation of the general adaptive returned bound. The original label truth is unresolved.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C074

**...certified rows in that range (3 probes x 20 budgets)**

Retained value: `60`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/label_sensitivity/triviaqa.json](../../results/label_sensitivity/triviaqa.json); field `criteria.reported.certified_rows`.
- Artifact SHA-256: `235e3a676dfc84e20a127b4fa5500f73d9d7333acb07e6acadf6417a01ffda48`.
- Recorded source: `bb800beeb00aeaeaf0a40e7dfb43e2850c321591`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/32_label_sensitivity.py`. This is not a claim that this audit executed that command.
- Evidence family: [F16: Label-sensitivity study](claim-families.md#f16); type `exact_sensitivity_on_recorded_labels`.

**Why this claim is included.** How sensitive are the retained certificate calculations to specified possible label errors?

**What it means.** This counts probe-by-budget certificate rows. Reusing a score vector across budgets does not create independent experiments.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/validation-T1-mean_pool.json](../../results/scores/validation-T1-mean_pool.json); [results/scores/validation-T1-max_rolling_means.json](../../results/scores/validation-T1-max_rolling_means.json); [scripts/32_label_sensitivity.py](../../scripts/32_label_sensitivity.py); [controlplane/validation/label_error.py](../../controlplane/validation/label_error.py); [controlplane/extract/triviaqa.py](../../controlplane/extract/triviaqa.py)

**What remains unproved.** Disagreement is not a proven error, and strict matching is not a human gold standard. The confidence-under-perturbation calculation is conditional on its assumptions and must not be read as validation of the general adaptive returned bound. The original label truth is unresolved.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C075

**...the lowest confidence among them if every strict-vs-lenient matching dispute were a lenient labelling error**

Retained value: `0.8127`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/label_sensitivity/triviaqa.json](../../results/label_sensitivity/triviaqa.json); field `criteria.reported.confidence_at_disputes_min`.
- Artifact SHA-256: `235e3a676dfc84e20a127b4fa5500f73d9d7333acb07e6acadf6417a01ffda48`.
- Recorded source: `bb800beeb00aeaeaf0a40e7dfb43e2850c321591`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/32_label_sensitivity.py`. This is not a claim that this audit executed that command.
- Evidence family: [F16: Label-sensitivity study](claim-families.md#f16); type `exact_sensitivity_on_recorded_labels`.

**Why this claim is included.** How sensitive are the retained certificate calculations to specified possible label errors?

**What it means.** This is the least calculated confidence under the hypothetical assumption that all strict-versus-lenient matching disputes are errors in the retained labels.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/validation-T1-mean_pool.json](../../results/scores/validation-T1-mean_pool.json); [results/scores/validation-T1-max_rolling_means.json](../../results/scores/validation-T1-max_rolling_means.json); [scripts/32_label_sensitivity.py](../../scripts/32_label_sensitivity.py); [controlplane/validation/label_error.py](../../controlplane/validation/label_error.py); [controlplane/extract/triviaqa.py](../../controlplane/extract/triviaqa.py)

**What remains unproved.** Disagreement is not a proven error, and strict matching is not a human gold standard. The confidence-under-perturbation calculation is conditional on its assumptions and must not be read as validation of the general adaptive returned bound. The original label truth is unresolved.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C076

**...the highest**

Retained value: `0.9412`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/label_sensitivity/triviaqa.json](../../results/label_sensitivity/triviaqa.json); field `criteria.reported.confidence_at_disputes_max`.
- Artifact SHA-256: `235e3a676dfc84e20a127b4fa5500f73d9d7333acb07e6acadf6417a01ffda48`.
- Recorded source: `bb800beeb00aeaeaf0a40e7dfb43e2850c321591`; dirty: `False`; config: `2640a176a26a80a0`.
- Recorded check/regeneration entry: `python scripts/32_label_sensitivity.py`. This is not a claim that this audit executed that command.
- Evidence family: [F16: Label-sensitivity study](claim-families.md#f16); type `exact_sensitivity_on_recorded_labels`.

**Why this claim is included.** How sensitive are the retained certificate calculations to specified possible label errors?

**What it means.** This is the greatest confidence under the same hypothetical substitution. Neither matching rule supplies independent human truth.

**Where the data and calculation come from.** [evalsets/triviaqa-600.json](../../evalsets/triviaqa-600.json); [results/scores/validation-T1-last_token.json](../../results/scores/validation-T1-last_token.json); [results/scores/validation-T1-mean_pool.json](../../results/scores/validation-T1-mean_pool.json); [results/scores/validation-T1-max_rolling_means.json](../../results/scores/validation-T1-max_rolling_means.json); [scripts/32_label_sensitivity.py](../../scripts/32_label_sensitivity.py); [controlplane/validation/label_error.py](../../controlplane/validation/label_error.py); [controlplane/extract/triviaqa.py](../../controlplane/extract/triviaqa.py)

**What remains unproved.** Disagreement is not a proven error, and strict matching is not a human gold standard. The confidence-under-perturbation calculation is conditional on its assumptions and must not be read as validation of the general adaptive returned bound. The original label truth is unresolved.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C077

**Tightest budget a single-sample judge can certify**

Retained value: `0.1045`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json); field `headline.single_sample_floor_median`.
- Artifact SHA-256: `a421626446f42dd3037c6fc43ddd3bf029ac556b42e4646e814bfda968ed0740`.
- Recorded source: `62f74ae012029e270b18a7487c1726c102c25741`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/26_scorefree.py`. This is not a claim that this audit executed that command.
- Evidence family: [F17: Score-free detector tunability](claim-families.md#f17); type `simulated_independent_judge_votes`.

**Why this claim is included.** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**What it means.** This is the median floor across the declared simulated one-vote cells. It is not a floor measured for an actual commercial judge.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/26_scorefree.py](../../scripts/26_scorefree.py); [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py)

**What remains unproved.** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C078

**...distinct operating points it offers**

Retained value: `1`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json); field `headline.operating_points_at_k1`.
- Artifact SHA-256: `a421626446f42dd3037c6fc43ddd3bf029ac556b42e4646e814bfda968ed0740`.
- Recorded source: `62f74ae012029e270b18a7487c1726c102c25741`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/26_scorefree.py`. This is not a claim that this audit executed that command.
- Evidence family: [F17: Score-free detector tunability](claim-families.md#f17); type `simulated_independent_judge_votes`.

**Why this claim is included.** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**What it means.** This is the useful nontrivial operating-point count supplied by one binary vote under the study's convention.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/26_scorefree.py](../../scripts/26_scorefree.py); [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py)

**What remains unproved.** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C079

**Notches at k=50**

Retained value: `51`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json); field `headline.notches_at_k50`.
- Artifact SHA-256: `a421626446f42dd3037c6fc43ddd3bf029ac556b42e4646e814bfda968ed0740`.
- Recorded source: `62f74ae012029e270b18a7487c1726c102c25741`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/26_scorefree.py`. This is not a claim that this audit executed that command.
- Evidence family: [F17: Score-free detector tunability](claim-families.md#f17); type `simulated_independent_judge_votes`.

**Why this claim is included.** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**What it means.** This is a count of possible vote-fraction notches, including boundary values. It is different from the number of selected certified thresholds.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/26_scorefree.py](../../scripts/26_scorefree.py); [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py)

**What remains unproved.** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C080

**...distinct operating points they actually buy**

Retained value: `10`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json); field `headline.operating_points_at_k50`.
- Artifact SHA-256: `a421626446f42dd3037c6fc43ddd3bf029ac556b42e4646e814bfda968ed0740`.
- Recorded source: `62f74ae012029e270b18a7487c1726c102c25741`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/26_scorefree.py`. This is not a claim that this audit executed that command.
- Evidence family: [F17: Score-free detector tunability](claim-families.md#f17); type `simulated_independent_judge_votes`.

**Why this claim is included.** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**What it means.** This counts the distinct selected operating points in the declared simulated study, not every theoretically possible threshold.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/26_scorefree.py](../../scripts/26_scorefree.py); [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py)

**What remains unproved.** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C081

**Samples before granularity stops binding, 200 negatives**

Retained value: `3`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json); field `headline.crossover_k_smallest_pool`.
- Artifact SHA-256: `a421626446f42dd3037c6fc43ddd3bf029ac556b42e4646e814bfda968ed0740`.
- Recorded source: `62f74ae012029e270b18a7487c1726c102c25741`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/26_scorefree.py`. This is not a claim that this audit executed that command.
- Evidence family: [F17: Score-free detector tunability](claim-families.md#f17); type `simulated_independent_judge_votes`.

**Why this claim is included.** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**What it means.** This is the first examined vote count where granularity ceases to bind in the smaller declared calibration-pool setting.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/26_scorefree.py](../../scripts/26_scorefree.py); [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py)

**What remains unproved.** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C082

**...at 20,000 negatives**

Retained value: `7`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json); field `headline.crossover_k_largest_pool`.
- Artifact SHA-256: `a421626446f42dd3037c6fc43ddd3bf029ac556b42e4646e814bfda968ed0740`.
- Recorded source: `62f74ae012029e270b18a7487c1726c102c25741`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/26_scorefree.py`. This is not a claim that this audit executed that command.
- Evidence family: [F17: Score-free detector tunability](claim-families.md#f17); type `simulated_independent_judge_votes`.

**Why this claim is included.** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**What it means.** This is the corresponding crossover in the larger declared pool. It is conditional on the simulator and budget grid.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/26_scorefree.py](../../scripts/26_scorefree.py); [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py)

**What remains unproved.** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C083

**AUROC lost to a single sample**

Retained value: `0.2288`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json); field `headline.auroc_gap_at_k1`.
- Artifact SHA-256: `a421626446f42dd3037c6fc43ddd3bf029ac556b42e4646e814bfda968ed0740`.
- Recorded source: `62f74ae012029e270b18a7487c1726c102c25741`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/26_scorefree.py`. This is not a claim that this audit executed that command.
- Evidence family: [F17: Score-free detector tunability](claim-families.md#f17); type `simulated_independent_judge_votes`.

**Why this claim is included.** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**What it means.** This is the simulated ranking gap relative to the latent-probability reference at a single vote.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/26_scorefree.py](../../scripts/26_scorefree.py); [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py)

**What remains unproved.** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C084

**...at nine samples**

Retained value: `0.0215`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json); field `headline.auroc_gap_at_k9`.
- Artifact SHA-256: `a421626446f42dd3037c6fc43ddd3bf029ac556b42e4646e814bfda968ed0740`.
- Recorded source: `62f74ae012029e270b18a7487c1726c102c25741`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/26_scorefree.py`. This is not a claim that this audit executed that command.
- Evidence family: [F17: Score-free detector tunability](claim-families.md#f17); type `simulated_independent_judge_votes`.

**Why this claim is included.** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**What it means.** This is the corresponding simulated ranking gap at the named repeated-vote setting, assuming independent votes conditional on an item.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/26_scorefree.py](../../scripts/26_scorefree.py); [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py)

**What remains unproved.** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C085

**Certified at k=9, deployed at k=1: breach of the bound**

Retained value: `2.3521`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/scorefree/scorefree.json](../../results/scorefree/scorefree.json); field `headline.breach_factor_deploying_at_k1`.
- Artifact SHA-256: `a421626446f42dd3037c6fc43ddd3bf029ac556b42e4646e814bfda968ed0740`.
- Recorded source: `62f74ae012029e270b18a7487c1726c102c25741`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/26_scorefree.py`. This is not a claim that this audit executed that command.
- Evidence family: [F17: Score-free detector tunability](claim-families.md#f17); type `simulated_independent_judge_votes`.

**Why this claim is included.** How does binary output constrain thresholds, and how much can repeated independent votes improve granularity?

**What it means.** This is the observed breach factor when deployment changes the vote count after calibration in the specified simulator. The scoring rule has changed.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/26_scorefree.py](../../scripts/26_scorefree.py); [controlplane/validation/scorefree.py](../../controlplane/validation/scorefree.py)

**What remains unproved.** This is not an evaluation of a real commercial judge. Real repeated calls can be correlated and their costs were not measured. The simulation is an optimistic independent-vote scenario, not a distribution-free mathematical upper bound on every possible real judge. Changing vote count changes the deployed detector.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C086

**Gate decisions made without reading any detector**

Retained value: `33`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/gate/gate.json](../../results/gate/gate.json); field `headline.decisions_identical_without_a_detector`.
- Artifact SHA-256: `62e57f8f259ff40bafe5c6950a493d54c74edc345cea6b222afa72b4d6e8f531`.
- Recorded source: `4a6413079cec37f3f2e64f10e1d3910d1dfe8ab5`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/27_gate.py`. This is not a claim that this audit executed that command.
- Evidence family: [F18: Action-gate demonstration](claim-families.md#f18); type `finite_controlled_software_demonstration`.

**Why this claim is included.** Do the declared session and reversibility rules act consistently without a detector score, and what do they block in the declared workflow set?

**What it means.** This counts the selected gate comparisons whose decisions remain identical with detector evidence removed.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/27_gate.py](../../scripts/27_gate.py); [controlplane/gate/gate.py](../../controlplane/gate/gate.py); [controlplane/gate/agent.py](../../controlplane/gate/agent.py); [controlplane/gate/cost.py](../../controlplane/gate/cost.py)

**What remains unproved.** No empirical adversarial-robustness or production false-block rate follows from this finite sweep. A prompt-injection scenario and a small set of legitimate workflows do not represent arbitrary banking systems, attackers or users. Recovery by a new session is specific to the demonstrated policy.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C087

**...of how many rule-1/rule-2 decisions swept**

Retained value: `33`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/gate/gate.json](../../results/gate/gate.json); field `headline.decisions_compared`.
- Artifact SHA-256: `62e57f8f259ff40bafe5c6950a493d54c74edc345cea6b222afa72b4d6e8f531`.
- Recorded source: `4a6413079cec37f3f2e64f10e1d3910d1dfe8ab5`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/27_gate.py`. This is not a claim that this audit executed that command.
- Evidence family: [F18: Action-gate demonstration](claim-families.md#f18); type `finite_controlled_software_demonstration`.

**Why this claim is included.** Do the declared session and reversibility rules act consistently without a detector score, and what do they block in the declared workflow set?

**What it means.** This is the size of that same enumerated comparison set, not all possible programs or attacker states.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/27_gate.py](../../scripts/27_gate.py); [controlplane/gate/gate.py](../../controlplane/gate/gate.py); [controlplane/gate/agent.py](../../controlplane/gate/agent.py); [controlplane/gate/cost.py](../../controlplane/gate/cost.py)

**What remains unproved.** No empirical adversarial-robustness or production false-block rate follows from this finite sweep. A prompt-injection scenario and a small set of legitimate workflows do not represent arbitrary banking systems, attackers or users. Recovery by a new session is specific to the demonstrated policy.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C088

**Injection blocked at step**

Retained value: `4`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/gate/gate.json](../../results/gate/gate.json); field `headline.injection_blocked_at_step`.
- Artifact SHA-256: `62e57f8f259ff40bafe5c6950a493d54c74edc345cea6b222afa72b4d6e8f531`.
- Recorded source: `4a6413079cec37f3f2e64f10e1d3910d1dfe8ab5`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/27_gate.py`. This is not a claim that this audit executed that command.
- Evidence family: [F18: Action-gate demonstration](claim-families.md#f18); type `finite_controlled_software_demonstration`.

**Why this claim is included.** Do the declared session and reversibility rules act consistently without a detector score, and what do they block in the declared workflow set?

**What it means.** This is the stopping step in one authored injection scenario. It is not a distribution of adversarial detection times.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/27_gate.py](../../scripts/27_gate.py); [controlplane/gate/gate.py](../../controlplane/gate/gate.py); [controlplane/gate/agent.py](../../controlplane/gate/agent.py); [controlplane/gate/cost.py](../../controlplane/gate/cost.py)

**What remains unproved.** No empirical adversarial-robustness or production false-block rate follows from this finite sweep. A prompt-injection scenario and a small set of legitimate workflows do not represent arbitrary banking systems, attackers or users. Recovery by a new session is specific to the demonstrated policy.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C089

**...and the detector that flagged it**

Retained value: `False`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/gate/gate.json](../../results/gate/gate.json); field `headline.injection_flagged_by_detector`.
- Artifact SHA-256: `62e57f8f259ff40bafe5c6950a493d54c74edc345cea6b222afa72b4d6e8f531`.
- Recorded source: `4a6413079cec37f3f2e64f10e1d3910d1dfe8ab5`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/27_gate.py`. This is not a claim that this audit executed that command.
- Evidence family: [F18: Action-gate demonstration](claim-families.md#f18); type `finite_controlled_software_demonstration`.

**Why this claim is included.** Do the declared session and reversibility rules act consistently without a detector score, and what do they block in the declared workflow set?

**What it means.** The declared detector did not flag this authored scenario. The gate decision follows its separate state/reversibility rules.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/27_gate.py](../../scripts/27_gate.py); [controlplane/gate/gate.py](../../controlplane/gate/gate.py); [controlplane/gate/agent.py](../../controlplane/gate/agent.py); [controlplane/gate/cost.py](../../controlplane/gate/cost.py)

**What remains unproved.** No empirical adversarial-robustness or production false-block rate follows from this finite sweep. A prompt-injection scenario and a small set of legitimate workflows do not represent arbitrary banking systems, attackers or users. Recovery by a new session is specific to the demonstrated policy.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C090

**Legitimate workflows the gate blocks (EXACT, declared set)**

Retained value: `2`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/gate/gate.json](../../results/gate/gate.json); field `headline.legitimate_workflows_blocked`.
- Artifact SHA-256: `62e57f8f259ff40bafe5c6950a493d54c74edc345cea6b222afa72b4d6e8f531`.
- Recorded source: `4a6413079cec37f3f2e64f10e1d3910d1dfe8ab5`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/27_gate.py`. This is not a claim that this audit executed that command.
- Evidence family: [F18: Action-gate demonstration](claim-families.md#f18); type `finite_controlled_software_demonstration`.

**Why this claim is included.** Do the declared session and reversibility rules act consistently without a detector score, and what do they block in the declared workflow set?

**What it means.** This is an exact count of blocked workflows in the authored legitimate demonstration set, not a production false-block rate.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/27_gate.py](../../scripts/27_gate.py); [controlplane/gate/gate.py](../../controlplane/gate/gate.py); [controlplane/gate/agent.py](../../controlplane/gate/agent.py); [controlplane/gate/cost.py](../../controlplane/gate/cost.py)

**What remains unproved.** No empirical adversarial-robustness or production false-block rate follows from this finite sweep. A prompt-injection scenario and a small set of legitimate workflows do not represent arbitrary banking systems, attackers or users. Recovery by a new session is specific to the demonstrated policy.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C091

**...of how many declared**

Retained value: `8`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/gate/gate.json](../../results/gate/gate.json); field `headline.legitimate_workflows`.
- Artifact SHA-256: `62e57f8f259ff40bafe5c6950a493d54c74edc345cea6b222afa72b4d6e8f531`.
- Recorded source: `4a6413079cec37f3f2e64f10e1d3910d1dfe8ab5`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/27_gate.py`. This is not a claim that this audit executed that command.
- Evidence family: [F18: Action-gate demonstration](claim-families.md#f18); type `finite_controlled_software_demonstration`.

**Why this claim is included.** Do the declared session and reversibility rules act consistently without a detector score, and what do they block in the declared workflow set?

**What it means.** This counts the declared legitimate workflows used in the demonstration cost calculation.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/27_gate.py](../../scripts/27_gate.py); [controlplane/gate/gate.py](../../controlplane/gate/gate.py); [controlplane/gate/agent.py](../../controlplane/gate/agent.py); [controlplane/gate/cost.py](../../controlplane/gate/cost.py)

**What remains unproved.** No empirical adversarial-robustness or production false-block rate follows from this finite sweep. A prompt-injection scenario and a small set of legitimate workflows do not represent arbitrary banking systems, attackers or users. Recovery by a new session is specific to the demonstrated policy.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.

## C092

**...that a new session recovers**

Retained value: `2`. Retained interval: `-`. Artifact equality: **MATCH**.

- Evidence: [results/gate/gate.json](../../results/gate/gate.json); field `headline.blocked_workflows_recoverable`.
- Artifact SHA-256: `62e57f8f259ff40bafe5c6950a493d54c74edc345cea6b222afa72b4d6e8f531`.
- Recorded source: `4a6413079cec37f3f2e64f10e1d3910d1dfe8ab5`; dirty: `False`; config: `533fb74983fcd8af`.
- Recorded check/regeneration entry: `python scripts/27_gate.py`. This is not a claim that this audit executed that command.
- Evidence family: [F18: Action-gate demonstration](claim-families.md#f18); type `finite_controlled_software_demonstration`.

**Why this claim is included.** Do the declared session and reversibility rules act consistently without a detector score, and what do they block in the declared workflow set?

**What it means.** This counts the blocked declared workflows recovered by a new session under the demonstration's policy assumptions.

**Where the data and calculation come from.** [config.yaml](../../config.yaml); [scripts/27_gate.py](../../scripts/27_gate.py); [controlplane/gate/gate.py](../../controlplane/gate/gate.py); [controlplane/gate/agent.py](../../controlplane/gate/agent.py); [controlplane/gate/cost.py](../../controlplane/gate/cost.py)

**What remains unproved.** No empirical adversarial-robustness or production false-block rate follows from this finite sweep. A prompt-injection scenario and a small set of legitimate workflows do not represent arbitrary banking systems, attackers or users. Recovery by a new session is specific to the demonstrated policy.

**Additional arithmetic check:** this row is not directly covered by the frozen-score point oracle. Its MATCH status is retained-field agreement, with the family's reproduction requirements stated separately.
