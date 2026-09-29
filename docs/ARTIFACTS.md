# ARTIFACTS.md — every output file, and what is inside it

<sub>[🏠 Project README](../README.md) · [📚 Documentation index](README.md) · [🗺️ Diagrams](DIAGRAMS.md) · [📖 Glossary](GLOSSARY.md)</sub>

`results/` and `evalsets/` are the evidence. This page says what each file is,
which stage wrote it, and which fields matter — so that following a number from
the claim table to the thing that produced it takes one lookup rather than a
search.

No values are quoted here. The claim table in [../README.md](../README.md) names
the artifact **and the field** for every published number, and `make verify`
resolves all of them.

**Contents:** [Provenance](#every-artifact-carries-provenance) · [Validation](#validation-artifacts) · [Matrix and policy](#matrix-and-policy) · [Comparisons](#comparisons-and-transfers) · [Detectors](#detector-artifacts) · [Pilot](#the-banking-pilot) · [Frozen scores](#frozen-scores--the-evidence-a-clean-clone-checks) · [Studies on frozen evidence](#studies-on-frozen-evidence) · [Recheck and label-error studies](#recheck-and-label-error-studies) · [Audit records](#audit-records) · [Customer records](#records-the-customer-cli-writes) · [Eval sets](#evalsets) · [Not committed](#what-is-deliberately-not-committed)

---

## Every artifact carries provenance

Each JSON file opens with a `provenance` block:

| Field | Why it is there |
|---|---|
| `timestamp_utc` | when |
| `git_commit`, `git_branch` | which code |
| `dirty`, `dirty_paths` | whether the tree was clean. A `dirty: true` artifact records a commit that does not describe the code that ran |
| `config_hash` | SHA-256 of the resolved config. **Two artifacts with different hashes do not describe one experiment** |
| `seed`, `config` | the full resolved configuration, inlined |
| `libraries`, `device`, `python` | the environment, without which several numbers are not interpretable |

That block is what turns a published number into something a stranger can check.
Compare `config_hash` across artifacts before quoting two of them in one
sentence.

---

## Validation artifacts

`results/validation-<detector>-<envelope>.json` — one per (detector, envelope)
measured. Written by `02_validate.py` and `09_detectors.py`.

| Field | Contains |
|---|---|
| `run_id`, `detector_id`, `variant`, `eval_set_id`, `envelope_id` | what was measured, and on what |
| `data_source` | where the items came from |
| `splits`, `base_rate`, `test_scored` | the split sizes, the envelope's base rate, and the record that test was scored |
| `probe_fit` | fitting details for probe detectors |
| `operating_point` | the threshold and the budget it was selected to hit |
| `metrics` | AUROC, recall, precision, flag rate — **each with `value`, its interval, and its `EXACT`/`ESTIMATED` kind**. A rate's `n` is the eval-set size, not its denominator: positives for recall, `confirmed_errors.n` for precision (see GLOSSARY, *`n`, and the denominator*) |
| `controls` | all five, each with pass/fail and the band actually applied |
| `warrant` | the issued warrant, or the refusal |
| `warrant_status`, `status_reason` | `VALID` / `REFUSED`, and the reason naming **every** failed criterion |

Present in the repository: the three probe aggregations on the TriviaQA
envelope, and the reference PII detector on the Hinglish, long-context and
hard-negative envelopes.

A single-class envelope — `hard-negatives-200` is all negatives — carries a
false-positive rate but no AUROC, recall or precision; the metrics builder
**refuses** to invent those ranking quantities. Its committed historical
artifacts use an exact row-binomial FPR interval despite four dependent
framings per scenario. They replay for provenance, not independent-unit
assurance. A prospective grouped hard-negative warrant uses the Phase 23
group-any one-sided bound on equal-sized negative groups, or withholds the
per-row bound when group sizes differ. An ungrouped set retains the
independent-item exact interval.

---

## Matrix and policy

| File | Written by | Contains |
|---|---|---|
| `warrant_matrix.json` | `03_matrix.py` | `matrix` — every (detector × envelope) cell with its state, plus a `summary` counting VALID / REFUSED / UNVALIDATED; and `routing`, which detector to fall back to per envelope |
| `warrant_matrix.md` | `03_matrix.py` | the same, rendered |
| `RESULTS.md` | `03_matrix.py` | the results narrative, with **fixture numbers refused rather than printed** |
| `policy-<envelope>.json` | `07_policy.py` | `operating_points` — one block per profile, each with its own metrics and warrant; and `comparison` across the three |
| `tier_ladder.json` / `.png` | `02_validate.py` | what each level of model access buys, with intervals |
| `feasibility.json` | `11_feasibility.py` | `abstention_floor` per target risk, `profiles` with achieved risk and efficiency, `measured` and `declared` inputs kept separate, and a `not_derived_here` block naming what it deliberately does not claim |

`policy-*.json` fields are addressed in the claim table by a filter, e.g.
`operating_points[operating_point.operating_point_id=P-customer-support].metrics.recall.value`.
That syntax is resolved by `controlplane/report/claims.py`, so a row naming a
field that no longer exists fails the build rather than going stale.

---

## Comparisons and transfers

| File | Written by | Contains |
|---|---|---|
| `transfer-<detector>.json` | `04_transfer.py` | `source` and `target` blocks — the same fitted detector measured on the envelope it was fitted on and on the shifted one, nothing retrained |
| `paired_comparison.json` | `08_paired.py` | `split_relationship` (why the two are comparable at all), `thresholds`, `pinned_to_baseline_threshold`, `each_at_its_own_threshold`, `roc`, and `selection_aware_bounds` with the widening factor per operating point |
| `reconciliation.json` | `06_reconcile.py` | `round1` and `round2` numbers, the `branch` taken, `branch_meaning`, and `preregistered_in` — the decision entry that fixed the branches **before** the number was visible |

`preregistered_in` appears in several artifacts. It is the field that separates a
decision rule from a post-hoc rationalisation, and it is worth checking first
when reading any of them.

---

## Detector artifacts

| File | Contains |
|---|---|
| `detectors.json` | `runs` — one per (detector, eval set), each with metrics, controls and warrant status. This is where the Presidio configurations and the reference detector live |
| `holdout/detectors.json` | the same detectors on the held-out variant set — the out-of-sample check |
| `presidio_coverage.json` | which entity types the pinned Presidio version can recognise **at all**, produced by running the analyzer rather than by asserting it, plus `interpretation` and `uncovered` |
| `evalset_validation.json` | detector-versus-set validation runs used while building the sets |
| `evalset_build.json` | what was built, with each set's hash |

---

## The banking pilot

Four artifacts, each naming the decision entry that pre-registered it.

| File | Contains |
|---|---|
| `pilot_envelope.json` | the frozen prompts' distance from the fitted envelope, with `units` and `interpretation` |
| `pilot_run.json` | the pilot pass: `probe_fit`, `generation`, `acceptance_band`, `saturation`, `auroc`, the `branch` taken and what `decided_by` it |
| `pilot_null_band.json` | the null band and the power behind the routing decision, including whether the effective `n` is clusters rather than items |
| `pilot_seed_stability.json` | how often the gate clears across bootstrap seeds — `stability`, `verdict`, `why` |

The last one exists because **a gate that clears on the seed you happened to use
is not a gate**. Read `pilot_seed_stability.json` beside `pilot_run.json` or you
are reading half the result.

---

## Frozen scores — the evidence a clean clone checks

`results/scores/*.json`, written by `10_freeze_scores.py`, **committed**.

One file per measured (detector, envelope) block, holding the per-item labels,
scores and question ids. A few hundred kilobytes in total, which is the whole
point: tier 2 of `make verify` recomputes every metrics block from these using
the same builder, bootstrap count and seed, **on a fresh clone with no GPU and
no cache**.

If you want to check this project's arithmetic yourself, this directory is where
to start.

---

## Studies on frozen evidence

Each writes under `results/`, reading the frozen scores, the declared workload
or pinned public data. Several carry a `question` field stating what the study
asks, and a `not_derived_here` block naming what it deliberately does not claim.
**Where that block exists, read it before quoting a number from the file.**

| Artifact | Written by | Fields that matter |
|---|---|---|
| `results/fpr_sweep/sweep.json`, `SWEEP.md` | `19_fpr_sweep.py` | `grid_spec` (the budgets), `sweeps[]` -- one per score set, each with `points[]` giving every budget's certified status, threshold, false positives, and recall and precision with intervals |
| `results/fpr_sweep_oos/sweep.json` | `20_fpr_sweep_oos.py` | as above, plus `certifying_split_metrics` and `integrity`: thresholds certified on one split and scored on another, and the check that the two did not overlap |
| `results/calibration_power/calibration_power.json` | `21_calibration_power.py` | `n_available`, `declared_tolerance`, `success_bar`, `budgets[]` -- the drift each sample size can detect -- and `expansion_not_done` |
| `results/external/<pairing>/sweep.json`, `MATRIX.md` | `23_certify_external.py` | one directory per detector-and-dataset pairing: `pairing` (the detector's version, the dataset's revision and licence), `criterion`, `neutrality` (the terms every detector, including ours, was run on) and `sweeps`; `MATRIX.md` renders them together |
| `results/causal_claims.json` | `24_causal_claims.py` | `claims[]`, each registered mechanism with its `evidence` and the falsifier it is checked against |
| `results/on_traffic/on_traffic.json` | `25_on_traffic.py` | `declared` (the workload inputs, by origin), `price_list`, `coverage` of the estimator over simulated trials, `allocation`, `blinding`, `headline`, `not_derived_here` |
| `results/scorefree/scorefree.json`, `SCOREFREE.md` | `26_scorefree.py` | `floors`, `crossovers`, `tunability` and `ranking` for a detector with no score, with `void_at_another_k` naming what changes if the sampling count changes |
| `results/gate/gate.json`, `GATE.md` | `27_gate.py` | `registry`, `injection`, `no_detector_evidence` -- the decisions reproduced with every detector removed -- and `cost` on legitimate workflows |
| `results/drift/revocation_trace.json` | `28_revocation_trace.py` | `stream`, `checkpoints`, the `revocation`, and `criteria` numbered 1-4 with each outcome |

---

## Recheck and label-error studies

The four studies behind `recheck`, `plan` and the label-error figures share one
shape, so one reading covers all four:

| Field | Holds |
|---|---|
| `design` | the registered setting -- budget, alpha, sizes, cadences or score sets -- and the `decision` that registered it |
| `what_these_are` | one sentence saying what kind of figure the file contains: **a simulated operating characteristic of a rule, or a re-certification of frozen scores, not a new measurement of any detector** |
| `cells` or `sets` | every simulated or certified row, each figure with its Monte Carlo standard error where it is simulated |
| `criteria` | each registered criterion **as registered**, and whether it held |

| Artifact | Written by | Criteria keys | Decision |
|---|---|---|---|
| `results/recheck_schedules/comparison.json` | `29_recheck_schedules.py` | `validity`, `primary` | 187 |
| `results/frontier_selection/selection.json` | `30_frontier_selection.py` | `M1_material`, `M2_bonferroni_alpha`, `M3_sanity`; also `crosscheck` and `registered_run` | 192 |
| `results/chain_detection/grid.json` | `31_chain_detection.py` | `V`, `P1`, `P2`, `P3` | 196 |
| `results/label_sensitivity/triviaqa.json` | `32_label_sensitivity.py` | `C0`, `P1`, `P2`, `reported`; also `design.registered_run` | 199 |

**A failed criterion stays in the file as failed.** The claim table quotes these
artifacts by field, and `DECISIONS.md` says what each criterion was, before and
after it ran.

---

## Audit records

| Artifact | Written by | Fields that matter |
|---|---|---|
| `results/clean_clone.json` | `clean_clone_gate.py` | `ok`, `commit` (the commit that was cloned and tested), `tracked_files`, `steps[]` (each gate with `ok`, `skipped` and its output tail), `notes`. Since `DECISIONS.md` 200 the provenance block describes the moment of cloning, and `provenance_taken` says so; a record written before that has no such field |
| `results/test_inventory.json` | `refresh_test_inventory.py` | `n_collected`, `git_commit`, `dirty`, and `execution_status: not_measured_by_collection` -- a count of the tests that exist, **not** a claim that they pass |

---

## Records the customer CLI writes

These are written beside the customer's own files, not under `results/`, and are
the customer's to keep. [EVIDENCE-HANDOFF.md](EVIDENCE-HANDOFF.md) gives every
field, record by record; this is the map.

| Record | Written by | Top-level fields |
|---|---|---|
| `<file>.warrant.json` | `warrant certify` | `status`, `budget_fpr`, `alpha`, `reason`, `input` (including the ordered effective-row `evidence_sha256`), `certification`, `metrics`, new `metrics_protocol` (absent on historical records), `score_distribution` (bin edges and probabilities, never values), `labels`, `selection`, `frontier_record_present` |
| `<file>.frontier.json` | `warrant certify --frontier` | `input` (including `input_sha256`), `note`, `frontier[]` -- each row with `budget_fpr`, `certified`, `threshold`, `fpr_upper_bound`, `row_alpha`, `family_alpha` and `counts_exact` |
| `<file>.recheck.json` | `warrant recheck` | `status`, `reason`, `prior_warrant` (including the exact `warrant_sha256`, `certificate_verification` of `VERIFIED` or `NOT_CHECKED`, and `chain_revoked_at`), `now` (including ordered effective-row `evidence_sha256`), `detection`, `drift`, `labels`; `chain` is null. The certificate check requires `--certificate-input`; `drift` names the reference size used for its null band (`DECISIONS.md` 209) |
| `<file>.recheck-NNNN.json` | `warrant recheck --horizon-labels` or `--since` | as above, with `chain` holding the chain state and its `state_sha256`, and **`record_sha256` sealing the whole record** |
| `<warrant>.chain-head` | the same | `head_record_sha256`, `sequence`, and the latest record's `status` |
| `chain-verification.json` | `warrant chain verify` | `clean`, `structurally_clean`, `integrity_status`, `integrity_meaning`, `findings[]` (each with `kind`, `records`, `detail`), `unsealed`, `cannot_check` |
| `warrant-plan.json` | `warrant plan` | `feasible`, `negatives_per_recheck`, `items_per_recheck`, `detection_floor`, `power_at_breach`, `false_revocation_per_recheck`, `sizes_by_power`, `cadences`, `declared_inputs`, `refusal_reason` |
| a release contract, then `<contract>.evaluation.json` | `warrant release register`, then `evaluate` | see [RELEASE.md](RELEASE.md) |
| `<contract>.label-audit.json` | `warrant release label-audit` after evaluation | `contract_id`, `evaluated_evidence_id`, primary and effective-row digests, `release_status_at_audit`, `sensitivity`, `second_review`, source provenance and `audit_id`; see [RELEASE.md](RELEASE.md) |

The chained recheck, release evaluation and separate label audit have
whole-record checksums. A certify
warrant has no seal but `warrant verify` recomputes its material fields from the
retained scored rows (and frontier for a selected budget). Frontier and plan
records have no standalone verifier. A new ordinary recheck binds its ordered
effective scored rows and `warrant verify-recheck` recomputes material fields
from retained rows, certificate and configuration. Chained records carry the
row digest. `warrant verify-chain-recheck` can recompute a complete, sealed
linear prefix when every link and its fresh scored file is retained. The
separate `warrant chain verify` checks structure and seals without scored
files; it does not recompute the statistic. All these digests are checksums,
not signatures; none authenticates a writer or proves no branch was omitted.

---

## `evalsets/`

Frozen, content-hashed evaluation sets plus `manifest.json` registering them.

| Set | Is |
|---|---|
| `triviaqa-600`, `triviaqa-2400-t960` | the TriviaQA envelopes |
| `hinglish-pii-200`, `hinglish-pii-200b` | hand-written Hinglish PII scenarios, and the held-out variant |
| `hard-negatives-200` | boundary cases that must be **allowed** — all negatives, so it measures false positives only |
| `canary-20-*` | the regression tripwires, built from train splits |
| `banking-dual-24` | the dual-labelled pilot set, with its `.draft` kept beside it |

The hash covers the items, the data source and the construction notes. **A
modified set is a different set** and cannot inherit the old one's warrants —
that is the design, and `DraftDivergedError` exists to enforce the pilot's
version of it.

---

## What is deliberately not committed

| Not committed | Why |
|---|---|
| `results/cache-*.npz` | ~100 MB each. Regenerable by `00_extract.py`; the frozen scores are the checkable evidence instead |
| the SQLite ledger | generated; the hash chain is only meaningful for the run that built it |
| `results/fixtures/*` values in prose | present as files, but the results renderer refuses to print fixture numbers as if they were measurements |

The rule behind all three: **never stage a file over 10 MB**, and never publish a
number whose provenance you cannot show.

---

**See also:** [RUNBOOK.md](RUNBOOK.md) for which stage writes each file · [METHODS.md](METHODS.md) for how the values inside them were computed · [TESTING.md](TESTING.md) for what stops them going stale.
