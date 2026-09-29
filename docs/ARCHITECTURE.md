# ARCHITECTURE.md — what the system is and how the pieces fit

<sub>[🏠 Project README](../README.md) · [📚 Documentation index](README.md) · [🗺️ Diagrams](DIAGRAMS.md) · [🧭 Code tour](CODE_TOUR.md)</sub>

The one-sentence version: **a detector produces a score, a warrant says what
that score is worth on a named distribution, and policy reads the warrant
rather than the score.**

Everything below is a consequence of that separation.

**Contents:** [The three objects](#the-three-objects) ·
[Three ways in](#three-ways-in-one-set-of-statistics) ·
[The measurement pipeline](#the-measurement-pipeline) · [The five controls](#the-five-controls) ·
[Policy](#why-policy-reads-the-warrant-and-not-the-score) · [Composition](#composition) ·
[Drift](#drift-and-what-happens-after-it) · [The customer path](#the-customer-path-certify-recheck-chain-plan) ·
[Release evidence](#release-evidence) · [On-traffic estimation](#on-traffic-estimation-and-the-price-list) ·
[The action gate](#the-action-gate) · [Records](#records-the-ledger-and-what-detects-an-edit) ·
[Invariants](#where-the-invariants-live)

---

## The three objects

### Detector

Anything that reads a request or a response and emits a score. A linear probe
on question-time activations, a Presidio configuration, a reference PII
matcher. A detector knows nothing about how good it is.

Its **identity includes its configuration**: `presidio-stock` and
`presidio-enabled` are different detectors, not one detector with a flag,
because they have different measured bounds and a shared id would let a warrant
measured on one be quoted for the other.

`controlplane/detectors/`

### Envelope

A frozen, content-hashed evaluation set **plus a label definition**. The hash
covers the items, the `data_source` and the construction notes, so a modified
set is a *different* set and cannot inherit the old one's warrants.

An envelope is not just a distribution. `hinglish-pii-200` and `triviaqa-600`
differ in what their labels *mean*, and the category guard refuses to measure a
PII detector against hallucination labels — recall against labels that mean
something else is not recall.

`controlplane/evalsets/`, `evalsets/`

### Warrant

A time-bounded, evidence-backed statement keyed by
**(detector, operating point, envelope)**. It carries measured metrics with
intervals, the five control results, an issue time and an expiry
(`warrant_ttl_hours` in `config.yaml`), and either `VALID` or `REFUSED` with a
reason naming every failed criterion.

A warrant is in one of five states with three behaviours. `VALID` is validated
and cleared. `REFUSED` is validated and failed. `UNVALIDATED` means never tested
on this distribution, and it is the normal state of most cells, never collapsed
into either of the others. `STALE` and `REVOKED` mean it was valid and the
evidence has since moved: `STALE` widens the interval, `REVOKED` stops
certifying. `controlplane/model/enums.py` defines them.

A warrant is issued by `issue_or_refuse`, which takes **no argument that could
promote a failing detector**. There is no `force`, no `override`, no
`min_confidence` to relax. A refusal cannot be relabelled downstream.

`controlplane/model/warrant.py`, `controlplane/validation/issuance.py`

---

## Three ways in, one set of statistics

The repository is used in three ways. They share the certification statistics in
`controlplane/validation/` and differ in what they read and what they leave behind.

| | The measurement pipeline | The customer path | Release evidence |
|---|---|---|---|
| **Who runs it** | this project, to produce its own evidence | a validation team, on its own detector | a validation team, for one release decision |
| **Reads** | a model's activations, frozen eval sets | one scored, labelled file | a registered contract, then a scored holdout |
| **Entry point** | `scripts/00`–`32`, `make verify` | `warrant certify`, `recheck`, `plan`, `chain verify` | `warrant release register`, `evaluate`, `verify`, `label-audit`, `verify-label-audit` |
| **Package** | `extract`, `validation`, `matrix`, `drift`, `policy` | `intake`, `economics` | `release` |
| **Writes** | `results/`, the ledger | JSON records beside the customer's file | a contract and one evaluation record |
| **GPU** | once, for extraction | never | never |

The on-traffic estimator (`sampling`) and the action gate (`gate`) are measured by
the pipeline, on declared workloads and scenarios. Neither has run on a
customer's traffic.

---

## The measurement pipeline

```
                  frozen eval set                 config.yaml
                  (envelope, hashed)              (one workload, one seed)
                         │                                │
                         ▼                                ▼
  model ──► extract ──► activations cache ──►  validation runner
  (GPU, once)           (results/cache-*.npz)        │
                                                     │  five controls
                                                     │  bootstrap intervals
                                                     ▼
                                            issue_or_refuse
                                                     │
                              ┌──────────────────────┴──────────────────────┐
                              ▼                                             ▼
                       VALID warrant                                  REFUSED
                       bounds + expiry                       reason names every
                              │                              failed criterion and
                              │                              the build it refused
                              ▼
                      warrant matrix  ◄──── drift monitor ────► revoke / downgrade
                    (detector × envelope)   PSI on token length
                              │
                              ▼
                      policy bundle (Rego)
                      fails closed on a missing warrant
                              │
                              ▼
                        composed decision ──► certificate ──► ledger (hash chain)
```

### Stages

| stage | script | reads | writes |
|---|---|---|---|
| extract | `00_extract.py` | model, TriviaQA | `results/cache-*.npz` |
| build eval sets | `01_build_evalsets.py` | hand-written corpora | `evalsets/*.json`, manifest |
| validate | `02_validate.py` | a cache, an envelope | `results/validation-*.json` |
| matrix | `03_matrix.py` | every validation | `results/warrant_matrix.json`, `RESULTS.md` |
| transfer | `04_transfer.py` | two caches | `results/transfer-*.json` |
| canary | `05_canary.py` | canary cache | control evidence |
| reconcile | `06_reconcile.py` | Round 1 numbers | `results/reconciliation.json` |
| policy | `07_policy.py` | bundles, warrants | `results/policy-*.json` |
| paired | `08_paired.py` | two models, shared holdout | `results/paired_comparison.json` |
| detectors | `09_detectors.py` | PII envelopes | `results/detectors.json` |
| freeze scores | `10_freeze_scores.py` | every measured block | `results/scores/` |
| feasibility | `11_feasibility.py` | measured rates, the workload | `results/feasibility.json` |

The later scripts read what those stages wrote. `12`–`17` run the banking pilot;
`19`–`28` are studies on frozen evidence (budget sweeps, external detectors,
the on-traffic estimator, the gate, the revocation trace); `29`–`32` are the
pre-registered studies behind `recheck`, the frontier, the chain and the
label-error figures. [RUNBOOK.md](RUNBOOK.md) gives each one's inputs, outputs
and order; [ARTIFACTS.md](ARTIFACTS.md) gives each output's fields.

Every stage writes to `results/` and every later stage reads from disk, so any
stage is independently re-runnable without repeating the GPU extraction.

---

## The five controls

Run on every validation. **Any failure refuses the warrant**, and nothing
promotes it back.

| control | what it proves | how it fails |
|---|---|---|
| `padding_fault` | activations came from real tokens | a right-padded variant is **accepted** rather than rejected |
| `label_shuffle` | the signal is not an artefact of the fitting | AUROC survives permutation |
| `null_feature` | the pipeline does not manufacture signal | a probe on noise scores outside the null band |
| `canary` | the detector detects the thing at all | recall below 1.0 on a deliberately easy set |
| `determinism` | the number is reproducible | two runs at one seed differ |

The null band is **measured, not assumed**: on the synthetic fixture the
Hanley–McNeil closed form understated the true spread by 2.1x at d=32, because a
fitted probe's scores are not exchangeable; on the real 3,584-feature probes it
did not (0.7–1.0x, `DECISIONS.md` 169). Measuring costs nothing either way, so
each control simulates its own null at construction.
`DECISIONS.md` 029, 031, 070.

---

## Why policy reads the warrant and not the score

A threshold on a score is a number someone chose. A warrant is a number
someone measured, with an interval, on a named distribution, that expires.

The three profiles are **three points on one measured ROC**, not three invented
thresholds — same detector, same envelope, only `target_flag_rate` moves. Each
profile declares a floor, and the engine compares the floor against the
**interval bound**, not the point estimate. A bundle naming an operating point
with no warrant behind it **fails to load**; that is fail-closed, not a warning.

`controlplane/policy/`, `policies/*/bundle.yaml`

---

## Composition

Two warranted detectors, one decision. The rules were written before the code
(`DECISIONS.md` 088) and the four cases are enumerated in
[CASES.md](CASES.md) §2. The load-bearing ones:

- **bounds are keyed per detector and never merged.** Two detectors agreeing
  does not strengthen either bound; it is not a vote.
- **a refusal is not inherited.** One detector being refused does not
  invalidate the other's warrant; what was not checked is recorded instead.
- **an unvalidated detector that fires triggers the profile default**, not its
  own action — and one that stays silent triggers nothing, because silence from
  an unmeasured detector is not evidence.

`controlplane/policy/compose.py`

---

## Drift, and what happens after it

The monitor computes PSI on **input token length**, and refuses a configuration
whose false-alarm rate would exceed 5% — simulated at construction, because
PSI's 0.10/0.25 bands are credit-scoring rules of thumb quoted without their
sample size and are not scale-free.

`config.yaml` declares four more envelope features (script mix, embedding
centroid distance, reference perplexity, category mix) and `SPEC.md` specifies
MMD on embeddings. **None of those is computed**, so a shift in language or topic
at a constant length passes unseen ([LIMITATIONS.md](LIMITATIONS.md) §3.4,
`DECISIONS.md` 172).

Past the significant boundary, the ladder runs:

```
envelope violation → revoke → route to a detector that still holds a warrant
                            → adopt ITS bounds, cite ITS warrant
                            → if nothing holds one at this floor: REFUSE and enqueue
```

The measured version is the centrepiece. One long-context shift, three probe
aggregations, nothing retrained:

| detector | `triviaqa-600` | `triviaqa-longctx-600` |
|---|---|---|
| `T1-last_token` | 0.8256 [0.7934, 0.8567] | **VALID** 0.8135 [0.7797, 0.8447] |
| `T1-max_rolling_means` | 0.7853 | **REFUSED** 0.5553 [0.5105, 0.6015], flags 54% |
| `T1-mean_pool` | 0.7855 | **REFUSED** 0.5015 [0.4546, 0.5479], flags nothing |

Mean-pool at chance flags nothing, so a conventional dashboard reads it as
clean traffic. That is the failure this system exists to name.

`controlplane/drift/`

---

## The customer path: certify, recheck, chain, plan

`warrant` runs on one file a customer supplies (`id`, `label`, `score`) with no
model, no GPU and no network. It is `controlplane/cli.py` over
`controlplane/intake/`.

```
  scored file ──► contract ──────────► exit 2: input the command cannot use
                     │                  (nothing certified, nothing written)
                     ▼
                  certify ──► REFUSED (exit 0): too few clean negatives, or no
                     │        threshold whose bound clears the budget
                     ▼
                VALID warrant ── threshold, Clopper-Pearson bound, metrics with
                     │           intervals, label-error ladders, label_2 measured
                     │
          ┌──────────┴───────────────────────────┐
          ▼                                      ▼
  recheck on a fresh file                recheck --horizon-labels N,
  bound and distribution, separately     then --since <last record>
  REVOKED only on evidence of breach     one sequential test over N units
                                         sealed records, chain-head sidecar
                                                 │
                                                 ▼
                                         chain verify: findings, unsealed
```

| Step | What it decides | Why it is built that way |
|---|---|---|
| **Contract** (`contract.py`) | whether the file can be read at all | a bad file exits 2 and is never confused with a refused detector. Rows are refused, never dropped or filled in |
| **Certify** (`certify.py`) | the lowest threshold whose one-sided Clopper-Pearson upper bound clears the budget | the most recall the promise allows. It also puts every certificate at the edge of its budget, which is why each one prints its label-error ladders (`DECISIONS.md` 197) |
| **Frontier** (`frontier.py`, `selection.py`) | every budget on a grid at once | reading it and then picking a budget is a selection, so a pick is certified at the frontier's row level with `--from-frontier` (192, 195) |
| **Labels** (`labels.py`) | how many wrong labels each result tolerates, and what a second reviewer disputes | `label_2` is **measured, never obeyed**: it changes no status, threshold, bound or metric |
| **Recheck** (`recheck.py`) | whether a warrant still holds on new data | the false-positive bound and the score distribution are separate checks with separate fixes. Revocation needs the **lower** bound above the budget; failing to re-prove is not breach. Every verdict states its detection floor |
| **Chain** (`chain.py`, `chain_verify.py`) | a year of rechecks as one test | independent rechecks each spend alpha. The chain spends it once over a declared horizon, refuses to resume a revoked warrant, makes forks visible, and seals every record (187, 193, 194) |
| **Plan** (`economics/`) | what rechecking costs | sized by the chance of catching a breach, with the false-revocation rate of each cadence (183) |

On a grouped file (a `group` column) the unit of inference is the group, groups
must be equal in size, and a recheck re-tests in the same unit (188, 190).
New `certify` records name `grouped_boundary_vacuous_v2` in `metrics_protocol`:
if grouped recall, precision, flag-rate or descriptive within-set FPR bootstrap
resampling collapses, its interval
is the uninformative `[0, 1]` range rather than a binomial interval that counts
dependent rows. `warrant verify` replays v2, retained v1 and unmarked records
under their respective calculations (217-219, 221). The certificate's separate
FPR bound and threshold do not change.

---

## Release evidence

`warrant release` (`controlplane/release/`) is a separate workflow with its own
records, for one release decision rather than ongoing monitoring (`DECISIONS.md`
184, 185).

```
register ──► contract: identity, criteria, development and holdout ids, expiry
                │       frozen before any score exists
                ▼
evaluate ──► one evaluation of one fixed threshold on the holdout; a second
                │       evaluation at the same location is refused
                ▼
verify   ──► recompute metrics and decision from the retained files, check
                        identity and digests, apply expiry
label-audit ──► after evaluation, describe separate adverse label-error
                counts at the same fixed threshold; bind optional label_2
verify-label-audit ──► replay that companion from the retained files
```

It differs from `certify` in three ways that matter to a reader: the threshold is
fixed in advance rather than searched for; every rate gets a simultaneous
interval family; and the evaluation record is sealed and recomputed on verify.
The two verdicts are **not interchangeable** on the same counts. Grouped files
are rejected. [RELEASE.md](RELEASE.md) is the procedure, and
[EVIDENCE-HANDOFF.md](EVIDENCE-HANDOFF.md) says what to hand a validation
function from either path.

---

## On-traffic estimation and the price list

Recall on production traffic cannot be read off an eval set. The flagged pool is
reviewed anyway, so it is a **census**: this month's confirmed-error count is
exact and free. Recall needs the misses in the unflagged pool, which must be
**sampled**, which costs labels and carries an interval.

| Piece | Where | Rule |
|---|---|---|
| Estimator | `sampling/estimator.py` | stratified by flag; yield and rate returned in separate fields with different types |
| Sizing | `sampling/planning.py`, `economics/sizing.py` | labels sized through the derivative of recall with respect to the miss rate, not as a prevalence, and with a declared probability of meeting the margin (147, 191) |
| Allocation | `sampling/allocation.py` | proportional in month one; Neyman only once per-stratum rates exist (150) |
| Queue | `sampling/queue.py` | blinded: no flag, score, stratum or ordering signal reaches a reviewer |
| Agreement | `sampling/agreement.py` | Cohen's kappa with its own interval |

Every figure derives from the one `workload` block in `config.yaml`. The workload
is declared, not observed, and the estimator's coverage is measured on simulated
traffic with known truth (`results/on_traffic/`).

---

## The action gate

What stops an agent's **action**, as distinct from what flags a response
(`controlplane/gate/`, `DECISIONS.md` 156). Five rules, in order:

| # | Decision | When | Reads a detector? |
|---|---|---|---|
| 1 | BLOCK | the tool is irreversible and the relevant warrant is not `VALID` | no: it reads the warrant's status |
| 2 | BLOCK | the tool is irreversible and the session, **counting this call**, would hold all three of sensitive access, untrusted input and the ability to change state; two is the limit | no |
| 3 | CONFIRM | the tool is irreversible and severity is at least medium | yes |
| 4 | ESCALATE | severity is high and the confidence band is uncertain | yes |
| 5 | ALLOW | otherwise, naming the rule | — |

Reversibility is **declared** in a registry where the tool is defined; an
unregistered tool is refused, and reversibility cannot be downgraded at runtime.
Session flags are sticky and have no unsetter. Rules 1 and 2 are the claim: an
attacker who defeats every detector moves neither, which `test_gate_no_detector`
checks by removing every detector input. That is **not a robustness claim**, and
the cost on legitimate work is counted over declared workflows
(`results/gate/`).

---

## Records, the ledger, and what detects an edit

Every issuance, refusal, revocation, override and decision in the measurement
pipeline is appended to a SQLite store with a hash chain over records. Retention is 400 days (DPDP Rules
6(1)(e) and 8(3): one year, from 13 May 2027). An override record **cannot be constructed without its
stratum and draw probability**, because a record missing those is unusable for
estimation and would silently bias any recall computed from the review queue.

The store is generated and gitignored: the chain is only meaningful for the run
that built it.

`controlplane/store/ledger.py`

**The customer path does not write to the ledger.** Its records are JSON files
beside the customer's input, and they differ in what can detect an edit:

| Record | Detects an edit? |
|---|---|
| chained recheck record | yes: sealed over every field, checked by `warrant chain verify` and by `--since` |
| release evaluation | yes: sealed, and recomputed from the retained files by `warrant release verify` |
| certify warrant | effective scored rows and material fields are replayed by `warrant verify`; no whole-record seal or authenticated custody |
| ordinary recheck | `warrant verify-recheck` binds ordered fresh effective rows and recomputes material fields from retained files; no authenticated custody |
| sealed linear chain prefix | `warrant verify-chain-recheck` checks each retained record and matching scored batch from link 1, then recomputes the sequential statistic; no assurance about omitted branches or a later head |
| frontier record, plan | **no** standalone verifier |

Every seal and digest here is a **checksum, not a signature**: anyone who can
write the records can recompute them consistently
([LIMITATIONS.md](LIMITATIONS.md) §3.7).

---

## Where the invariants live

They are enforced at construction, not by convention.

| invariant | enforced by |
|---|---|
| no blended F1 anywhere | `Metric.__post_init__` refuses the name |
| every rate carries an interval | `Metric` refuses `ESTIMATED` without one |
| exact counts carry none | `Metric` refuses `EXACT` with one |
| a refusal states a reason | `Warrant.__post_init__` |
| the warrant key includes the envelope | `Warrant.compute_id` |
| left padding | asserted at load and again before every batched call |
| config invariants | `controlplane/config.py` `__post_init__`, naming each one |
| a customer's refusal has no override | `warrant certify` takes no flag that promotes one; `--require-warrant` only changes the exit code (`test_require_warrant_flips_the_exit_code_and_still_says_why`) |
| a bad file is not a refused detector | `InputError`, exit 2 (`test_a_bad_file_exits_two_and_says_why`) |
| a second reviewer changes no verdict | `test_label_2_changes_no_status_threshold_bound_or_metric` |
| no chained record's field is edited silently | the seal, and a property test over every leaf (`test_every_leaf_of_every_link_edited_alone_is_flagged`) |
| the gate's first two rules read no detector | `test_gate_no_detector` |
| each `CLAUDE.md` invariant names its test | `tests/test_invariants.py` |

A silent wrong answer is worse than a crash, so every boundary asserts.
