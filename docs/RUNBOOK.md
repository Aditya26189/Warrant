# RUNBOOK.md — every script, what it reads, what it writes

<sub>[🏠 Project README](../README.md) · [📚 Documentation index](README.md) · [🗺️ Diagrams](DIAGRAMS.md) · [📖 Glossary](GLOSSARY.md)</sub>

`scripts/` holds thin CLI wrappers. They parse arguments, call
`controlplane/`, and write files; **no logic lives in them**, which is why this
page can describe them by their inputs and outputs without lying.

Every script takes `--config config.yaml` unless noted. Every artifact it
writes carries a `provenance` block — config hash, git commit, dirty flag,
library versions, device, timestamp.

**Contents:** [Entry points](#the-entry-points) · [The customer CLI](#the-customer-cli-warrant) · [The measurement chain](#the-measurement-chain) · [The banking pilot](#the-banking-pilot) · [Studies on frozen evidence](#studies-that-run-on-frozen-evidence) · [Recheck and label studies](#the-recheck-and-label-error-studies) · [Maintenance](#maintenance-scripts) · [Order of operations](#order-of-operations) · [Rules](#rules-that-apply-to-every-run) · [Contract drift](#contract-drift-found-during-this-documentation-pass--now-reconciled)

---

## The entry points

Four commands cover almost everything a reader needs.

| Command | What it is for |
|---|---|
| `python scripts/smoke.py` | Did this clone come down intact? Under a minute, no network |
| `python scripts/verify.py` | Does every published number still reproduce? Three tiers, weakest first |
| `python -m pytest tests/ -q` | Is the suite green? |
| `python scripts/00_extract.py` | The GPU stage. Everything else runs from what it caches |

`scripts/verify.py` takes `--claims-only` (tier 1 alone, seconds), `--readme`
(check a different README path) and `--eval-set`.

`scripts/run.sh` is not a stage — it is the wrapper you should use when you
need a command's real exit status. `cmd | tail` reports *tail's* status, so a
failing suite reads as green; `sh scripts/run.sh <cmd>` writes the output to a
file, echoes `EXIT=<real status>`, and propagates it.

---

## The customer CLI (`warrant`)

`warrant` is the command a customer runs on their own scored file. It is
`python warrant.py`, or `warrant` after `pip install -e .`. It reads a CSV or
JSONL of `id,label,score` (the contract is [INPUT.md](INPUT.md)), sends nothing
over the network, and writes one JSON record per run.

Most commands exit 0 when they produce a result, **including a refusal or a
revocation**. The certify-record `warrant verify` command exits 0 for `VERIFIED`
and 1 for `MISMATCH` or `UNVERIFIED`. Other hard failures use an explicit
`--require-warrant`, `--require-valid` or `--require-clean` flag. Exit 2 means
the input could not be used: a malformed file, missing record, or chain that
may not be continued.

| Command | Reads | Writes by default | Answers |
|---|---|---|---|
| `warrant certify -i FILE -b BUDGET` | a scored file | `FILE.warrant.json` | What threshold certifies this false-positive budget on this file, and what does the detector do there? Or: why can it not? |
| `warrant certify -i FILE --frontier` | a scored file | `FILE.frontier.json` | Every budget's exact counts at once, with no bootstrap |
| `warrant certify -i FILE -b BUDGET --from-frontier FILE.frontier.json` | the file and its frontier record | `FILE.warrant.json` | Certify a budget picked off the frontier, at the frontier's adjusted level so the pick still holds ([DECISIONS 195](../DECISIONS.md)) |
| `warrant verify -w FILE.warrant.json -i FILE [--frontier FILE.frontier.json]` | a retained certificate, its scored file, and a frontier if selected | nothing | Does the effective-row digest and every material certificate field recompute? It checks arithmetic, not authorship |
| `warrant recheck -w WARRANT -i NEW` | a warrant and a fresh file | `NEW.recheck.json` | Does the promise still hold on new data? The bound and the score distribution are reported separately |
| `warrant recheck -w WARRANT -i NEW --certificate-input ORIGINAL [--certificate-frontier RECORD]` | the warrant, fresh file and retained original evidence | `NEW.recheck.json` | Replays the original certificate before measuring the new file; a mismatch, unverified legacy record or missing selected frontier exits 2 with no output |
| `warrant recheck -w WARRANT -i NEW --horizon-labels N` | as above | `NEW.recheck-0001.json`, and `WARRANT.chain-head` | Start a chain: a year of rechecks tested as one sequence ([DECISIONS 193](../DECISIONS.md)) |
| `warrant recheck -w WARRANT -i NEW --since RECORD` | the previous link too | `NEW.recheck-NNNN.json`, and moves the head | Continue a chain from its latest record |
| `warrant plan -w WARRANT --negative-share S` | a warrant | `warrant-plan.json` | How many labels a recheck needs to catch a breach, and what each cadence costs |
| `warrant chain verify RECORD...` | every kept chain record | `chain-verification.json` | What the set of records shows: an edited record (every chained record is sealed whole), a malformed value, forks, restarts, missing links, links after a revocation. Missing seals are reported as unknown integrity and prevent `clean` or `--require-clean`; structural inspection remains available |
| `warrant release register / evaluate / verify` | a specification, holdout ids, scored holdout | a contract, then `CONTRACT.evaluation.json` | A pre-registered, expiring, single-use evaluation of a fixed operating point ([RELEASE.md](RELEASE.md)) |

**Rules the CLI enforces, so you do not have to remember them.**

- **Nothing overrides a refusal.** No flag, variable or option turns REFUSED into
  VALID (invariant 3).
- **A chained record is never overwritten.** Each link is created exclusively; if
  the name exists, the command stops rather than replacing evidence.
- **A revoked warrant is not continued.** Once a chain's latest record is REVOKED
  -- by its own statistic or because the score distribution moved -- neither
  `--since` nor a new `--horizon-labels`, with or without `--fork`, may go on.
  Re-certify and start again.
- **A `label_2` column is measured, never obeyed.** A second reviewer's labels
  are reported beside the result and change no verdict ([INPUT.md](INPUT.md)).
- **An edited record is not continued.** `--since` recomputes the previous
  record's seal and chain-state digest and refuses one that does not reproduce.
  A seal is a checksum, not a signature ([LIMITATIONS.md](LIMITATIONS.md) §3.7).

---

## The measurement chain

Run in this order on a fresh machine. Each one reads what the previous wrote.

### `00_extract.py` — the only GPU stage

Extracts TriviaQA question-time activations for both envelopes and self-checks
the output.

- **reads** the model and TriviaQA, per `config.yaml`
- **writes** `results/cache-*.npz` (gitignored, ~100 MB each)
- **flags** `--batch-size`, `--max-new-tokens`, `--cache-dir`, `--out`
- **when** only when the model, the prompt, the layer set or the aggregation
  changes. The caches are the expensive thing in this repository

### `01_build_evalsets.py` — freeze the evaluation sets

Builds the hand-written corpora into frozen, content-hashed sets and registers
them in a manifest.

- **writes** `evalsets/*.json`, `evalsets/manifest.json`,
  `results/evalset_build.json`
- **when** a corpus changes. Note that this produces a *different set*, with a
  different hash and therefore no inherited warrants — that is the design

### `02_validate.py` — one detector, one operating point, one envelope

Runs `/validate` and the tier ablation, then issues or refuses a warrant.

- **reads** a cache and a frozen envelope
- **writes** `results/validation-*.json`, `results/tier_ladder.json`
- **this is where** the five controls run, the threshold is frozen on
  validation, and test is scored once

### `03_matrix.py` — populate the warrant matrix

Runs the ablation across every activation-tier envelope plus the text
detectors, and renders the matrix.

- **writes** `results/warrant_matrix.json`, `results/warrant_matrix.md`,
  `results/RESULTS.md`
- **note** the renderer refuses to print fixture numbers as if they were
  measured

### `04_transfer.py` — the long-context shift

Fits on one envelope, evaluates on another, with nothing retrained.

- **writes** `results/transfer-*.json`, one per probe aggregation
- **flags** `--source-cache`, `--target-cache`, `--source-eval-set`,
  `--target-eval-set`, `--target-flag-rate`
- **why it matters** this is the measurement where one aggregation holds its
  warrant and another collapses to chance while flagging almost nothing — the
  failure a conventional dashboard reads as clean traffic

### `05_canary.py` — freeze the regression tripwire

Builds a small, deliberately easy set from the **train split only**.

- **writes** a canary eval set and its control evidence
- **flags** `--cache`, `--eval-set`, `--variant`, `--n-items`,
  `--target-flag-rate`, `--canary-id`, `--evalsets-out`
- **read this before using it** the canary is a tripwire, not a measurement.
  Recall below 1.0 on it fails a control; a high number on it is not evidence
  of anything

### `06_reconcile.py` — Round 1 against Round 2's pipeline

Classifies the result against branches that were **pre-registered before the
number was visible**.

- **writes** `results/reconciliation.json`, including which branch was taken
  and what that branch means

### `07_policy.py` — the three profiles

Issues the three operating points, loads the three bundles, and decides one
input under all three.

- **reads** `policies/*/bundle.yaml`, the warrant matrix
- **writes** `results/policy-*.json`
- **expect** a `BundleError` if a bundle names an operating point that nothing
  has warranted. That is fail-closed behaviour, not a bug

### `08_paired.py` — comparing two probes properly

Pairs two models on the items **both** held out and bootstraps the difference.

- **writes** `results/paired_comparison.json`, including the selection-aware
  widening of the recall bounds
- **flags** `--baseline-set`, `--variant-set`, `--variant`, `--bootstrap`
- **why** the naive comparison changed the training size *and* the evaluation
  sample at once, which makes the difference unattributable.
  [METHODS.md](METHODS.md) §7

### `09_detectors.py` — the PII detectors

Validates each Presidio configuration and our reference detector, then issues
or refuses each warrant.

- **writes** `results/detectors.json`, `results/holdout/detectors.json`
- **flags** `--eval-set`, `--hard-negatives`, `--skip-reference`
- **note** each configuration is a *separate detector id*, because a shared id
  would let a warrant measured on one be quoted for another

### `10_freeze_scores.py` — the evidence a stranger can check

Freezes the per-item labels, scores and question ids behind every measured
block.

- **writes** `results/scores/*.json` — small, and **committed**
- **why** this is what makes tier 2 of `verify` possible on a fresh clone with
  no GPU and no cache

### `11_feasibility.py` — the bound that is not about our detector

Derives the abstention floor and the review sizing from what was measured.

- **reads** a policy artifact (`--policy-artifact`)
- **writes** `results/feasibility.json`, including a `not_derived_here` block
  naming what it deliberately does not claim

---

## The banking pilot

Four scripts, run in order, each pre-registered in `DECISIONS.md` before it ran.

| Script | Does |
|---|---|
| `12_pilot_freeze.py` | Freezes the pilot prompts and measures their distance from the fitted envelope |
| `13_pilot_run.py` | The GPU pass: generate, judge, extract, score. Flags `--reference`, `--variant`, `--evalsets-dir`, `--batch-size` |
| `14_pilot_null_band.py` | Regenerates the IQR-ratio null band and its power — the numbers the decision routes on |
| `15_pilot_seed_stability.py` | Prices the margin: how often does the gate clear across seeds? Flags `--seeds`, `--resamples` |

The last one exists because a gate that clears on the seed you happened to use
is not a gate. Its artifact records the verdict *and* how much of the
bootstrap-seed distribution agrees with it.

`17_presidio_coverage.py` is separate: it records which entity types stock
Presidio can recognise at all, by running the analyzer rather than by asserting
it. A claim about a dependency is checkable by running the dependency.

---

## Studies that run on frozen evidence

None of these needs a GPU. Most read committed artifacts -- usually
`results/scores/` -- or the declared workload, and write one directory under
`results/`. The exceptions are named in the table: two need external data. Where a
study tests a prediction, its `DECISIONS.md` entry records whether and when the
prediction was registered.

| Script | Writes | What it answers |
|---|---|---|
| `19_fpr_sweep.py` | `results/fpr_sweep/sweep.json`, `SWEEP.md` | Is a low recall a ceiling or a setting? Certifies every budget on a grid over the frozen scores. Flags `--start`, `--stop`, `--step` |
| `20_fpr_sweep_oos.py` | `results/fpr_sweep_oos/sweep.json`, a validation-split score set | The same sweep with the threshold certified on validation and scored on test, so selection and measurement use different items |
| `21_calibration_power.py` | `results/calibration_power/calibration_power.json`, `CALIBRATION_POWER.md` | What calibration drift can be detected at the sample sizes available, and what sample size a smaller drift needs |
| `23_certify_external.py` | `results/external/<pairing>/sweep.json`, `results/external/MATRIX.md` | Third-party detectors on public datasets. **Needs network**: datasets and models are fetched at pinned revisions. Flags `--pairing`, `--all`, `--list`, `--matrix-only` |
| `24_causal_claims.py` | `results/causal_claims.json` | Freezes the evidence each registered causal claim is checked against. **Needs the REDACT benchmark** cloned under `~/.cache/warrant/benchmarks`. Flag `--limit` |
| `25_on_traffic.py` | `results/on_traffic/on_traffic.json` | The on-traffic warrant: the label price list for the declared workload, and simulated evidence that the estimator covers ([METHODS.md](METHODS.md)) |
| `26_scorefree.py` | `results/scorefree/scorefree.json`, `SCOREFREE.md` | What certifying a detector that emits no score costs |
| `27_gate.py` | `results/gate/gate.json`, `GATE.md` | What the action gate stops, what it costs, and which rules read no detector at all |
| `28_revocation_trace.py` | `results/drift/revocation_trace.json`, `revocation.db` | Replays a real envelope shift against a real warrant and records the revocation. Needs the long-context caches. Flags `--n-normal`, `--n-shift` |

---

## The recheck and label-error studies

The four studies behind `warrant recheck`, `warrant plan` and the label-error
figures on every certificate. They simulate decision rules, or re-certify frozen
scores; they measure no new detector.

| Script | Writes | What it answers | Decision |
|---|---|---|---|
| `29_recheck_schedules.py` | `results/recheck_schedules/comparison.json` | Five revocation rules across a simulated year of rechecks: how often each falsely revokes a detector keeping its promise, and how fast each catches a breach | 187 |
| `30_frontier_selection.py` | `results/frontier_selection/selection.json` | How wrong is a budget picked by reading the frontier, measured before deciding what `--from-frontier` does. Flags `--replicates`, `--crosscheck-replicates` | 192 |
| `31_chain_detection.py` | `results/chain_detection/grid.json` | The chained recheck across breach sizes, cadences and change points. A non-registered `--years` requires `--out`, so a smoke run cannot overwrite the result | 196 |
| `32_label_sensitivity.py` | `results/label_sensitivity/triviaqa.json` | This project's own certificates under label error, with the strict matching rule as a second labeller. A budget subset (`--budgets`) requires `--out` | 199 |

**Read the decision before the number.** Each entry states its predictions and
criteria as registered, reports each as held or failed, and says what its figures
do not establish. The claim table carries the headline figures; the entries carry
the conditions they hold under.

`22_make_examples.py` regenerates `examples/certifies.csv` and
`examples/refuses.csv` from a seeded generator. It is tested to reproduce the
committed files byte for byte, because the examples are shipped evidence.

---

## Maintenance scripts

| Script | Does |
|---|---|
| `build_lock.py` | Regenerates `requirements.lock.txt` as the resolved closure of `requirements.txt`. **Holds every version where it is** — the existing lock is fed back as a constraint and the script exits non-zero if a pin moves. `--upgrade` is the only way to move one, and it prints the diff; `--check` resolves without writing. Needs `uv` |
| `build_notebooks.py` | Regenerates `notebooks/run_on_kaggle.ipynb`. **The script is the source of truth**; never hand-edit the notebook |
| `clean_clone_gate.py` | Clones this repository into a temporary directory and runs the gates inside it, so "it works on my machine" cannot be the reason it passes |
| `kaggle_run.py` | Pushes the extraction notebook to Kaggle as a batch kernel and collects the output. Flags `--yes`, `--accelerator`, `--timeout`, `--poll-seconds` |
| `refresh_test_inventory.py` | Counts the collected tests from a **clean committed** checkout and writes the count into `README.md`, `Makefile` and `results/test_inventory.json`. Collection is not execution: the count says how many tests exist, not that they pass. Refuses a dirty tree, and updates nothing if the tree changed while it was collecting |
| `run.sh` | Runs a command and reports its **real** exit status |

---

## Order of operations

```
00_extract ──► 01_build_evalsets ──► 02_validate ──► 03_matrix
                                          │
                                          ├──► 04_transfer
                                          ├──► 05_canary
                                          ├──► 06_reconcile
                                          ├──► 07_policy ──► 11_feasibility
                                          ├──► 08_paired
                                          └──► 09_detectors
                                                   │
                                                   ▼
                                            10_freeze_scores
                                                   │
                                                   ▼
                                              verify.py
```

`10_freeze_scores.py` runs last because it freezes what everything else
produced. Run `verify.py` after it, and again on a clean clone before
publishing anything.

The studies in the two sections above run **after** `10_freeze_scores.py`, in
any order. `20_fpr_sweep_oos.py` and `28_revocation_trace.py` need the
activation caches on disk; `23_certify_external.py` needs network, and
`24_causal_claims.py` the REDACT benchmark.
`clean_clone_gate.py` is the last step before anything is shared: it clones the
repository and runs smoke, the full suite and `verify` inside the clone. It refuses
to write its record if the source changed while it ran.

---

## Rules that apply to every run

1. **Commit first.** A dirty tree makes the artifact's recorded commit false.
   `provenance()` sets `dirty: true` and it stays in the file.
2. **One declared workload.** Every economic figure derives from the single
   `workload` block in `config.yaml`. Mixing a flag rate from one scenario with
   a base rate from another is silently wrong.
3. **Never pipe a command whose status you need.** Use `sh scripts/run.sh`.
4. **A stage never recomputes an earlier stage's metric.** Later stages read
   the earlier artifact, so two documents cannot disagree about one number.
5. **Nothing promotes a refusal.** No script takes a flag that could.

---

## Contract drift found during this documentation pass — now reconciled

`CLAUDE.md` ("Definition of done"), `CONTRIBUTING.md` (pre-merge checklist) and
`TASKS.md` (Phase 12 gate) all referred to **`scripts/run_all.py`**, which has
never existed in this repository. The four `make` targets are the actual entry
points, and `clean_clone_gate.py` is what exercises the clean-clone
reproduction those three documents describe.

All three now name what ships. The drift is recorded here rather than silently
corrected, because a contract that quietly changed is a contract nobody can
trust to have meant something yesterday — and because the interesting part is
not the name, it is that three binding documents agreed with each other and
with nothing on disk. A cited path that no test resolves is a claim like any
other.

---

**See also:** [SETUP.md](SETUP.md) to get the environment right · [ARTIFACTS.md](ARTIFACTS.md) for what each output file contains · [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for what a failure means.
