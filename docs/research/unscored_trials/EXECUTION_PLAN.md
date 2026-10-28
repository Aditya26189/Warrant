# Unscored-trials research: execution and publication decision plan

Date: 28 October 2026. Status: proposed research extension, not a completed experiment or submission-readiness claim.

Read [AGENT_PROMPT.md](AGENT_PROMPT.md) for the continuation prompt. The user's explicit request authorizes this planning document despite older instructions deferring prose documentation. This extension is separate from Warrant production, the closed grader-mutation experiment, and the FPR literature/source-review track.

## 1. Objective

Determine whether public agent-evaluation releases provide a reproducible, useful empirical lesson about execution accounting beyond applying established missing-outcome bounds to another score table.

> Can released records reconstruct the advertised evaluation population and score, and which reported comparisons depend on exclusion, weighting, or retry-accounting choices?

The deliverable is an honest decision: strengthen the paper for TMLR, retain a technical report, or document that available evidence cannot answer the question. A reversal, benchmark defect, new theorem, or favorable result is not required. Another corpus alone does not establish research value.

[Opinion] Check Terminal-Bench 2 first because its official release documents job configurations and trial artifacts. HAL is a conditional fallback. No paid model evaluations, GPUs, product SDK, dashboard, or grader engine are required.

## 2. Preserve and verify the baseline

The working paper is **What Survives Unscored Trials? A denominator audit of a public agent evaluation release**. Its directory is `outputs/warrant-exclusion-study` in the originating research workspace, not necessarily in a Warrant checkout.

Set `WARRANT_BASELINE_DIR` to that directory and `WARRANT_RESEARCH_DATA_DIR` to a separate external working-data directory. Find the baseline through the original conversation workspace or supplied archive. Absence from Git does not establish missing scientific data. Do not reconstruct results from this document.

Archive: `warrant-unscored-trials-research-artifact.zip`. SHA-256:

```text
620e321c99c86f1870f2ec10a8c99848db3fdd03c580522b876780401de755ed
```

From the archive directory, run `Get-FileHash -Algorithm SHA256 warrant-unscored-trials-research-artifact.zip` and compare with the hash above before extracting. From the baseline root, run `python src/verify_artifact.py` to verify the internal `MANIFEST.sha256.json`. Preserve the original directory/archive. Reproduce in a distinct copy. Rebuilding a PDF can change byte hashes; compare numerical outputs separately.

Read these baseline files:

- `README.md`, `PROTOCOL.md`, `DECISIONS.md`.
- `PUBLICATION-ASSESSMENT.md`, `DATA-AVAILABILITY.md`, `CLAIM-LEDGER.md`.
- `SOURCES.md`, `SOURCES.json`, `THIRD-PARTY-NOTICES.md`.
- `src/analyze.py`, `src/analyze_tau.py`, `src/crosscheck.py`.
- `results/cells.csv`, `pairs.csv`, `quarantine.csv`, `summary.json`, `policy-sensitivity.csv`, `tau-summary.json`.

[Evidence: baseline computed artifacts] The Marin analysis retains 86 of 88 cells. Of 417 strict observed orderings, 383 remain strict under bounded missing rewards; 22 allow reversal and 12 allow only equality. These are compatible completions, not observed corrected rankings. Two inconsistent cells remain quarantined. The historical tau2 control has 4,448 scored final slots; it does not establish complete pre-release retry history. Recheck all numbers before reusing them.

The baseline is exploratory. Prior exposure includes its outcomes and the Terminal-Bench issue below. A newly frozen extension protocol does not retrospectively preregister the whole project.

## 3. Corrections that govern the work

### Task alignment cannot tighten the proposed logical bounds

For a common fixed population of N equally weighted slots, let R be observed reward mass and U the number of unknown rewards. With each unknown independently free in [0,1]:

```text
L_s = R_s / N
H_s = (R_s + U_s) / N
identified difference(A, B) = [L_A - H_B, H_A - L_B]
```

Aligning task IDs leaves these extrema unchanged. If both systems miss the same task, their unknown rewards can still be (1,0) or (0,1). For fixed nonnegative slot weights summing to one, replace reward mass and missing count with weighted sums; the same separability argument applies.

Do not pursue a headline experiment asking whether pairing alone rescues bounds. Task linkage helps establish comparable populations, missingness overlap, weights, and paired sampling uncertainty. Tighter logical bounds require new information or defensible additional restrictions. Restricting to common observed tasks changes the target population.

### Caps must be compatible with the data

[Evidence: recomputation from baseline `results/cells.csv`] Eight of 86 retained cells exceed 5% missingness; the maximum is 20/205. All retained cells satisfy a 10% cap. Thus the existing 5% row is a hypothetical sensitivity, not merely coarsened information about every cell in this panel.

Before claiming information coarsening, verify U_s/N_s <= epsilon for every included cell and preserve the panel/weights when computing [(1-epsilon)q_s, (1-epsilon)q_s + epsilon]. Report cap violations. Do not silently remove violating cells and compare different panels. This is supporting analysis, not new theory.

### Keep essential distinctions explicit

- Recorded zero, missing reward, absent planned record, and malformed reward differ. Exceptions can coexist with valid scores; exception names alone do not identify causes.
- Planned logical slots, execution attempts, retries, final records, and published files differ. Repeated trials are not automatically retries.
- Exclusion-conditioned success, all-attempt operational success, and capability under hypothetical perfect infrastructure can be different estimands.
- Author checking, a second implementation by the same assistant, independent human review, and maintainer confirmation are different evidence categories.

## 4. Budget, scope and Git discipline

Maximum **20 hours of active research/engineering effort** for the decision study. This ceiling sums active effort across concurrent agents; parallel work does not multiply the allowance. This is a ceiling, not a requirement to run out the clock. Record actual elapsed times and effort estimates separately. Stop an unproductive branch when its gate fails.

| Stage | Maximum allocation | Required outcome |
|---|---:|---|
| A. Baseline and closest work | 1 hour | Baseline identity, limitations, prior-exposure record |
| B. Dataset feasibility | 4 hours | Population/score reconstruction evidence or early stop |
| C. Freeze extension protocol | 2 hours | Cohort, units, policies, comparisons and stop rules |
| D. Implement and analyze | 6 hours | Reconciliation, native reproduction, supported comparisons |
| E. Verify and challenge | 3 hours | Tests, clean replay, alternative-explanation review |
| F. Publication decision | 4 hours | Claim ledger and GO / REPORT / DATA-BLOCKED decision |

Additional compute/API/service budget: INR 0. Existing computer, internet and assistant access are not counted as free economic resources. Use selective CPU-only downloads. Inspect sizes first; default initial download ceiling is a configurable 2 GiB. Stop before exceeding it. Do not download entire trajectory archives automatically.

Use a separate branch/worktree based on current remote main. Read repository instructions and the coordination board. Claim only this track's paths. Preserve concurrent work. No subagents are required. Do not change production behavior, FPR decisions/source roles, closed grader-study packets, or historical scientific artifacts.

Commit protocol/code before generating scientific outputs. Record clean source commit, configuration hash, source hashes and environment. Commit artifacts separately. Never stage files above the repository limit. Keep raw downloads outside Git; publish only necessary fields with source references and licenses. Logs may contain secrets or personal data: do not republish them.

## 5. Stage A: baseline and closest-work check

1. Verify the baseline and read its limitations. Reproduce only in a copy; reuse its numerical code.
2. Record main/branch, paths, baseline identity and prior exposure in an extension-local decision log.
3. Read Gao and Zhou, Terminal-Bench issue 2246 and accessible linked materials, the HAL card, and TMLR criteria. Record exact versions/dates. Inaccessible code is an explicit limitation.
4. Make a comparison table: prior question, population, unknown-outcome treatment, execution history and our possible additional observation.

Gao and Zhou explicitly address denominator rules. Do not say they ignore infrastructure exclusions or agent-caused failures. Our Marin analysis reconciles published aggregate accounts; it does not reconstruct an original planned roster. AgentEval by Ruiqi Gao is a separate author team, not simply Gao and Zhou's follow-on.

**Gate A:** baseline identity and limitations understood. Baseline unavailability blocks paper integration but permits metadata-only candidate feasibility. Do not spend the budget rebuilding the old study from descriptions.

## 6. Stage B: establish data feasibility

### Candidate order and neutral selection

Start with `harborframework/terminal-bench-2-leaderboard`. Pin an immutable revision before bulk retrieval. Inventory all submission/job metadata. Discovery can inspect a small deterministic set of structurally distinct jobs; log every inspected job and any outcome exposure.

Use the full eligible inventory if affordable. Otherwise freeze a subset using metadata and a recorded hash ordering/seed independent of performance, missingness or ranks. Keep an exclusion ledger for the full inventory. Examples named in the prior issue are discovery cases, not a representative sample.

The `prime-radiant-inc/terminal-bench-analysis` mirror is a locator/indexing aid, not the official leaderboard. Check relevant fields against pinned upstream records. Record mirror transformations/redactions; redacted files need not be byte-identical. A mirror omission is not proof of a failed execution.

### Required feasibility checks

For each inspected submission/job establish:

1. Benchmark/version/task identity, task manifest, system/scaffold identity, configuration and source pointers.
2. Declared repetitions and whether configuration establishes exact logical slots. A minimum of five trials is not an exact roster of five trials for every job.
3. Available trial IDs, task IDs, rewards, exceptions, counters, and the versioned official score aggregation.
4. Reconciliation of final records with job summaries. Link attempts to logical slots only when explicit evidence supports it. Do not manufacture trial indices or retry lineage from file order.
5. Whether the official score is reproducible to its stated rounding precision. If unavailable, limit the claim to the published artifact's score.
6. Evidence level: exact planned roster; named final trials only; aggregate counts only; cleaned scored rows; or unreconciled accounts.

**HAL fallback:** the inspected `razam2/hal-response-matrix` revision `c367d8e49e31b572903064b1823cd33e81520be9` has 32,894 rows and binary scores throughout. The cleaned matrix is not a failure ledger. Follow run IDs to primary configs/logs and documented cleaning rules. Do not infer a planned Cartesian product from the union of observed task IDs. Without roster/failure evidence, HAL fails the missing-execution question even if useful for other questions.

**Gate B:** proceed with a defensible population and comparable records, including complete controls. Nonzero missingness is not an outcome-selected eligibility requirement. A complete cohort may support a useful negative finding if the other accounting questions remain informative.

Stop or narrow if versions cannot be aligned or absence cannot be separated from unplanned work. Final records can support a final-release audit, not pre-release retry claims. Do not search unrelated benchmarks until an alarming result appears.

Write `feasibility.json` and a short source-linked note naming the supported population and unresolved information before building the analysis engine.

## 7. Stage C: freeze the extension protocol

Commit these rules after feasibility inspection and before bulk comparative analysis. Disclose discovery exposure; label the extension exploratory.

### Cohort and identity

- Source revisions, metadata-based inclusion/exclusion and any deterministic subset rule.
- Benchmark/version/task universe, comparison unit, system configuration, job aggregation and task weights.
- Whether the claim concerns released records, declared logical slots, operational attempts or future tasks. Start with the fixed corpus.
- Exact-duplicate treatment, conflicting-duplicate quarantine, reward-channel selection, finite/range checks and incomplete-counter handling.
- A compatibility matrix for pairs sharing task definitions and declared weights. Matching benchmark names is insufficient.
- All compatible pairs in the frozen cohort are analyzed; exclusions and reasons remain visible. Examples are explanatory only.

### Canonical records

Maintain an execution table and, only where supportable, a separate planned-slot table.

| Field group | Required content |
|---|---|
| Source | Dataset/revision, relative source path, SHA-256, JSON pointer/line |
| System | Submission, model/scaffold identifiers, config hash |
| Population | Benchmark/version, task identity, job ID, roster evidence |
| Execution | Raw trial ID, attempt ID if explicit, logical-slot/parent ID if explicit |
| Outcome | Raw reward, validated reward, channel, score-present flag |
| Status | Exception, completion state, evidence-qualified cause or unknown |
| Audit | Duplicate/conflict status, eligibility/reason, policy provenance |

Keep statuses orthogonal. Exceptions may coexist with scores. A missing planned record differs from a present record with null reward. Contradictory evidence is quarantined, not coerced to zero.

### Prespecified reporting policies

1. **Native reporting:** reproduce the actual documented implementation, including weighting and error handling. A mirror's SQL is not automatically authoritative.
2. **Fixed-population unknown-outcome bounds:** preserve validated observations; only genuinely unscored known-population slots are free in [0,1]. No verified population means no invented interval.
3. **Operational failure accounting:** use zero only where the declared task/execution contract defines the event as failure. Separate this target from capability under perfect infrastructure.
4. **Equal-task versus pooled-trial aggregation:** labeled sensitivity where repetitions vary. Hold outcomes fixed and identify the different weights. This is not tighter missingness identification.
5. **Retry-policy diagnostics:** only with actual lineage and applicable budget records. Without lineage, mark this question unanswerable. Do not infer selective retrying.
6. **Common-observed-task diagnostic:** optional, with explicit population-selection caveat; never the primary repair.

Prespecify numerical tolerances and tie rules from raw precision and published rounding. Use Decimal/rational calculations where appropriate. When reward mass comes from rounded summaries, propagate a rounding envelope instead of inventing exact values. Cross-system missingness overlap does not establish a causal missingness mechanism.

## 8. Stage D: smallest sufficient implementation

Proposed new paths, subject to current ownership:

```text
docs/research/unscored_trials/
  EXECUTION_PLAN.md
  AGENT_PROMPT.md
  PROTOCOL.md
  DECISIONS.md
  FINDINGS.md
  PUBLICATION_DECISION.md
experiments/unscored_trials/
  inventory.py
  normalize.py
  analyze.py
  reproduce.py
  tests/
results/unscored_trials/<run-id>/
  provenance.json
  source_manifest.json
  feasibility.json
  eligibility.csv
  executions.csv
  planned_slots.csv
  reconciliation.csv
  native_score_reproduction.csv
  policy_comparisons.csv
  pairwise_comparisons.csv
  validation.json
```

These paths describe intended outputs, not files/commands already implemented. Create `planned_slots.csv` only if supported. Prefer a small reusable research module with thin entry points. Keep downloads outside Git with retrieval manifests and an offline replay route.

Implementation order:

1. Retrieve pinned required records with successful/failed receipts, size limits and bounded timeouts. Avoid indefinite retry loops.
2. Normalize without silently discarding unmatched/contradictory records. Reconcile planned slots, final trials, scores, unknowns and job aggregates separately.
3. Reproduce native reporting. Investigate disagreements at source level first. Status: match, rounding-compatible, unresolved mismatch or unavailable.
4. Compute fixed-population bounds and all compatible pair comparisons. Separate robust strict order, identified tie, equality-compatible ambiguity and reversal-compatible ambiguity. Endpoint fills and compatible reversals are counterfactuals, not recovered rankings.
5. Run only supported prespecified policy diagnostics. Every output states population, weights, denominator, evidence availability and interpretation.
6. Generate accounting/reconciliation, native-score, policy-comparison and claim/limitation tables. Missingness-overlap plots remain descriptive unless a stronger design is justified.

Do not fit an elaborate missingness model or inverse-probability estimator to compensate for absent execution evidence. Sampling uncertainty is optional and separate: pair/cluster by task, state sampling assumptions and address multiplicity for simultaneous winner claims. Repeated trials are not independent tasks. The primary fixed-corpus analysis requires no population p-values.

## 9. Stage E: verification and adversarial review

Tests must defend meaningful failure modes:

- Zero, null, absent planned record and malformed reward remain distinct.
- Scored records with exceptions retain scores where the source contract supports them.
- Explicit identity controls deduplication; conflicting duplicates are quarantined.
- Multiple jobs, unequal repetitions, version changes and missing IDs cannot silently change populations or weights.
- Fractional rewards and rounding envelopes are handled correctly.
- Native aggregation matches hand-calculated small fixtures for each supported schema.
- Pairing leaves unconstrained fixed-population bounds unchanged, including shared missing slots.
- All-scored bounds collapse; all-unknown bounds span [0,1]; equality boundaries are classified correctly.
- A cap below actual missingness is rejected as an information-coarsening assumption.
- Unknown attempt lineage cannot enter retry-policy conclusions.

Synthetic fixtures establish software behavior, not real-world prevalence or novelty.

Run from a clean committed source. Retain command, exit status, hashes, environment and output. Replay numerical analysis offline and compare canonical results. A second implementation by the same agent is a cross-check, not independent replication.

Challenge each apparent finding: could rounding, task/version differences, weights, mirror extraction, legitimate repetitions, native failure semantics, or a changed estimand explain it? Keep negative controls and counterexamples. Do not select only favorable examples.

Prepare a human audit worksheet covering ordinary and discrepant cases with source pointers and arithmetic. Human-review status stays pending until a human performs it. Author verification does not establish independent outcome adjudication.

## 10. Stage F: publication decision

Build a claim ledger: claim; evidence/source; unit/population; prior-art overlap; strongest alternative explanation; supported/conditional/unsupported status; permitted manuscript wording.

Issue one decision by the budget ceiling:

| Decision | Required basis | Deliverable |
|---|---|---|
| GO: develop submission | Reproducible accounting/score analysis; a useful lesson beyond baseline and closest audit; limitations proportional to evidence | Exact proposed claims/tables, revised outline, remaining author-review items and next-work estimate |
| REPORT: technical report | Correct analysis that mainly repeats standard bounds or existing audits without enough additional explanation | Limitations/related-work update and candid stop rationale; preserve artifacts |
| DATA-BLOCKED | Records cannot establish the needed population, outcome status or reporting rule | Feasibility note identifying missing evidence and exact reopening conditions |

GO does not require a reversal or novel method. A systematic robustness result with actionable scope can qualify. GO is not an acceptance prediction. Dataset count, code volume and time invested do not establish publication value.

Potential useful findings, if supported: recurring differences between documented and reproducible denominators; interactions between unequal task repetitions and failure handling; a small additional release artifact that demonstrably resolves a reporting uncertainty; or precise conditions under which a reported comparison remains supported. A lone arithmetic correction or deterministic algebraic identity is insufficient by itself.

Do not claim exclusion caused a rank error without recovered evidence and an established target. Do not call a mirror discrepancy an official leaderboard bug. Do not generalize one campaign's prevalence to all agent evaluations.

## 11. Conditional route from GO to a submission candidate

This is a separate writing/packaging stage. The initial agent run ends with the decision and estimated remaining work; it does not silently exceed the 20-hour research ceiling. A later continuation can authorize this stage without restarting finished research.

1. Rewrite around the actual empirical lesson. Keep Marin's aggregate scope and tau2's final-slot control accurate. Remove unsupported pairing/planned-roster claims.
2. Use the official TMLR LaTeX template. Compile and inspect every page; recheck current author/editorial policies. The working PDF is not already TMLR-format.
3. Generate tables/figures from committed outputs. Include population, weights, denominator, rounding, exclusions and source identity.
4. Disclose closest work, exploratory exposure, data availability, licenses, limitations, AI assistance and conflicts. OpenAI develops evaluated models; the assistant's maker conflict is relevant. Do not invent authors, affiliations, funding or endorsements.
5. Human authors verify representative source-to-table cases, understand the methods and take responsibility for the text. Describe that work accurately. Keep independent-review claims absent unless supported.
6. Prepare an anonymized supplement and reproduction guide. Test in a fresh environment and check link/metadata anonymity. Preserve the original archive; new versions receive new manifests.
7. Deliver compiled paper, editable sources, artifact manifest, completed checks and unresolved issues. Submission and external outreach require separate explicit authorization.

## 12. Sources and evidence quality

Checked 28 October 2026 unless stated. Author documents establish what their authors report; they are not independent validation. No acceptance probability is estimated.

| Source | Date / grade | Supported use |
|---|---|---|
| [TMLR acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html) | Current policy; official primary | Accurate evidence and audience interest; method novelty not mandatory |
| [TMLR author guide](https://jmlr.org/tmlr/author-guide.html) | Current policy; official primary | Template, anonymity and preparation; recheck before submission |
| [TMLR editorial policies](https://jmlr.org/tmlr/editorial-policies.html) | Current policy; official primary | Scope, author responsibility and AI-assisted work |
| [Gao and Zhou](https://arxiv.org/html/2605.10448v1) | 11 May 2026; primary preprint | Evidence bounds, outcome audits and explicit denominator rules |
| [AgentEval, Ruiqi Gao](https://arxiv.org/html/2610.21177v1) | 15 October 2026; primary preprint | Evidence-bound assessment workflows; separate author team |
| [Terminal-Bench official release](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard) | Living release; official primary | Config/trial structure and repeat policy; pin execution cohort |
| [Terminal-Bench audit issue 2246](https://github.com/harbor-framework/terminal-bench/issues/2246) | 13 October 2026; primary author report | Prior missing-result and ranking audit, not reproduced here |
| [Terminal-Bench mirror](https://github.com/prime-radiant-inc/terminal-bench-analysis) | Living third-party implementation | Indexing aid, not official scoring/completeness authority |
| [HAL response matrix](https://huggingface.co/datasets/razam2/hal-response-matrix/tree/c367d8e49e31b572903064b1823cd33e81520be9) | Pinned release inspected 28 October; primary data | Cleaned scored records, not planned-roster/exception evidence |
| [Hardy et al.](https://arxiv.org/abs/2610.00651v1) | 30 September 2026; primary preprint | Evaluation reliability and task/scaffold comparison context |
| [Marin baseline](https://huggingface.co/datasets/open-athena/marin-eval-policy-2026-09-24/tree/01f235dfdb16e3ac85c01ab6cb9376ac0c335da1) | Pinned September release; primary data | Aggregate-account evidence, not raw execution history |

## 13. Completion criteria

- Baseline preserved; availability and verification stated.
- Sources pinned; research status distinguished from writing/submission status.
- Cohort/exclusions recorded without outcome-driven benchmark shopping.
- Native reproduction precedes criticism; every comparison names its target and weights.
- Pairing identity and cap correction enforced.
- Actual tests/replay evidence retained, including failed checks.
- Closest work and alternative explanations addressed.
- GO / REPORT / DATA-BLOCKED decision delivered within the ceiling.
- No invented independent review, causal result, official correction or acceptance odds.
- Exact commits, paths, commands, limitations and next action reported; a remote push claimed only after verification.
