# CODE_TOUR.md — what is in each package

<sub>[🏠 Project README](../README.md) · [📚 Documentation index](README.md) · [🗺️ Diagrams](DIAGRAMS.md) · [📖 Glossary](GLOSSARY.md)</sub>

A map of `controlplane/`, package by package, with the file you want for each
job. Descriptions follow the modules' own docstrings; where a module exists to
prevent a specific failure, that failure is named.

The rule that shapes all of it: **logic lives in `controlplane/`.** `scripts/`,
`demo/` and `notebooks/` call it and render. Logic that lives only in a script
or a notebook is unreviewable.

**Contents:** [Where do I go for…](#where-do-i-go-for) · [model](#controlplanemodel--the-records) · [validation](#controlplanevalidation--measuring-and-issuing) · [intake](#controlplaneintake--the-customer-path) · [release](#controlplanerelease--pre-registered-release-evidence) · [sampling](#controlplanesampling--the-on-traffic-estimate) · [gate](#controlplanegate--the-action-gate) · [external](#controlplaneexternal--other-peoples-detectors) · [evalsets](#controlplaneevalsets--the-envelopes) · [detectors](#controlplanedetectors--the-things-being-measured) · [extract](#controlplaneextract--the-gpu-stage) · [matrix](#controlplanematrix--detector--envelope) · [drift](#controlplanedrift--when-a-warrant-stops-being-true) · [policy](#controlplanepolicy--reading-the-warrant) · [store](#controlplanestore--the-ledger) · [economics](#controlplaneeconomics--what-can-and-cannot-be-derived) · [report](#controlplanereport--rendering-and-proving) · [demo, gateway, config](#controlplanedemo-gateway-and-config)

---

## Where do I go for…

| I want to | Open |
|---|---|
| understand the central record | `model/warrant.py` |
| see why a rate cannot exist without an interval | `model/metrics.py` |
| find the code that refuses a warrant | `validation/issuance.py` |
| read the five controls | `validation/controls.py` |
| see where test is scored | `validation/runner.py` |
| add a detector | `detectors/`, then `validation/text_runner.py` if it is stateless |
| add an evaluation set | `evalsets/builders.py` and `evalsets/registry.py` |
| understand a bootstrap interval | `validation/stats.py` |
| see how policy fails closed | `policy/resolution.py` |
| see how two detectors combine | `policy/compose.py` |
| understand drift bands | `drift/psi.py`, `drift/null_band.py` |
| find what the demo shows | `demo/session.py`, `report/beats.py` |
| find what checks the README | `report/claims.py` |
| certify a customer's scored file, or refuse | `intake/certify.py` |
| see exactly what a customer's file must contain | `intake/contract.py` |
| recheck a warrant on new data | `intake/recheck.py` |
| understand a chain of rechecks and what it guarantees | `intake/chain.py` |
| audit a kept set of chain records | `intake/chain_verify.py` |
| see how far a certificate depends on its labels | `intake/labels.py` |
| see every budget's counts, or a pick off them | `intake/frontier.py`, `intake/selection.py` |
| price a recheck, or a year of them | `economics/sizing.py`, `economics/schedules.py` |
| run a pre-registered release evaluation | `release/` |
| estimate recall on unreviewed traffic | `sampling/estimator.py` |
| see what the action gate refuses | `gate/gate.py` |
| find every command a customer can run | `cli.py` |
| read or post to the board concurrent coding sessions share | `coordination/`, and `COORDINATION.md` at the root |

---

## `controlplane/model` — the records

Frozen dataclasses validated at construction. You cannot build an illegal record
and fix it later, which is the difference between an invariant and a convention.

| Module | Holds |
|---|---|
| `warrant.py` | **The central type.** What a detector's score is worth, on one distribution, until when. Enforces that a refusal states a reason and that the key includes the envelope |
| `metrics.py` | Metrics that cannot be constructed in violation of their own kind — `EXACT` refuses an interval, `ESTIMATED` requires one, and a blended F1 is refused by name |
| `findings.py` | Findings, operating points, distribution envelopes |
| `certificate.py` | The bounded, falsifiable assertion a decision leaves behind |
| `calibration.py` | The calibration claim, kept beside the warrant that makes it |
| `override.py` | Human overrides on escalated items — **cannot be constructed without stratum and draw probability**, because a record missing those would silently bias any recall computed from the review queue |
| `enums.py` | The enumerations every other record is built from |
| `serde.py` | Typed JSON round-tripping and canonical hashing |

---

## `controlplane/validation` — measuring and issuing

The largest package, and the one to read first.

| Module | Does |
|---|---|
| `runner.py` | `/validate`: one detector, one operating point, one envelope |
| `text_runner.py` | `/validate` for stateless text detectors — regex, checksum, rule-based |
| `controls.py` | The five controls, each reporting the band it applied |
| `issuance.py` | `issue_or_refuse` — **takes no argument that could promote a failing detector** |
| `metrics_builder.py` | The single place a metrics block is built from scores and labels |
| `stats.py` | AUROC, recall, precision, flag rate, bootstrap intervals |
| `scores.py` | Frozen per-item scores — the evidence a clean clone can actually check |
| `selection.py` | Threshold-selection uncertainty in a warranted recall |
| `paired.py` | Paired comparison of two probes on nested splits |
| `roc.py` | The ROC curve and the local slope at an operating point |
| `calibration.py` | Does the threshold still spend what it said it would? |
| `ablation.py` | The tier ladder: what each level of model access actually buys |
| `evalsets.py` | Eval sets and the cached extraction `/validate` runs from |
| `synthetic.py` | Synthetic sets and caches, for exercising the harness without a GPU |
| `warrant_stats.py` | The certification statistics every path shares: the Clopper-Pearson bound, the lowest certifying threshold, the negatives a budget needs, and the legacy `FPRMonitor`. **Read-only by contract** -- findings about it are recorded as open items, not edited in |
| `fpr_sweep.py` | Sweeping the false-positive budget over frozen scores: is a low recall a ceiling, or a setting? |
| `scorefree.py` | Certifying a detector that emits no score, and what having a score is worth |
| `label_error.py` | This project's own measured certificates re-certified through the customer path, under label error (`DECISIONS.md` 199) |

**Read `runner.py` once, top to bottom.** The order is the argument: fit on
train, select on validation, run the controls, score test once, build metrics,
then issue or refuse.

---

## `controlplane/intake` — the customer path

Everything behind `warrant certify`, `recheck` and `chain verify`. It takes a
customer's scored file rather than this project's eval sets, and **calls the same
statistics the research path uses** -- a second implementation is how two
answers to one question drift apart.

| Module | Does |
|---|---|
| `contract.py` | Reads the scored file strictly: `id`, `label`, `score`, optional `group` and `label_2`. Nothing is coerced, filled or dropped, and a refusal for too little evidence is kept distinct from a file that cannot be read |
| `certify.py` | Certifies a false-positive budget or refuses, through `validation/warrant_stats.py`. The record carries recall and precision with intervals, the score distribution a recheck compares against, and the label-error block |
| `frontier.py` | Every budget at once, in exact counts, with no bootstrap |
| `selection.py` | How wrong is the row a customer picks off the frontier? The measurement behind `--from-frontier` (`DECISIONS.md` 192, 195) |
| `recheck.py` | Is the warrant still true on new data? The false-positive bound and the score distribution are tested and reported separately, and revocation turns on the lower bound, not on a failure to re-prove |
| `chain.py` | A year of rechecks as one sequential test, carried in the recheck records. Also the chain-head sidecar, the whole-record seal (`record_sha256`), and every refusal to continue: a revoked warrant, an edited or malformed record, an undeclared fork |
| `chain_verify.py` | What a kept set of chain records shows as a whole: edited records (by seal, chain-state digest and derived fields), malformed values, forks, restarts, missing links, links after a revocation; records written before sealing are listed as unsealed. **It cannot recompute the statistics**; those need the labelled files |
| `labels.py` | How far a certificate or a recheck depends on its labels being right: the two exact error ladders, and a second reviewer's agreement and disputes (`DECISIONS.md` 197, 198) |
| `render.py` | The terminal summary. Written so a refusal reads as a result rather than a malfunction |

**Read `certify.py`, then `recheck.py`, then `chain.py`.** That is the order a
customer meets them, and each one's docstring says what the previous one could
not.

---

## `controlplane/release` — pre-registered release evidence

A separate workflow from `certify`, and not interchangeable with it. A release
freezes the identity, criteria and holdout **before** anything is scored,
evaluates that holdout once, and expires. See [RELEASE.md](RELEASE.md).

| Module | Does |
|---|---|
| `contract.py` | Freezes identity, selection and holdout membership, and binds them into the contract's digest before evaluation |
| `evaluate.py` | Fixed-holdout inference with simultaneous intervals, a data digest over the rows, and verification that recomputes every field |
| `render.py` | The terminal evidence, with its uncertainty and scope limits |
| `cli.py` | Parsing and file IO for `warrant release`; no inference in the wrapper |

---

## `controlplane/evalsets` — the envelopes

Hand-written corpora, builders, and the frozen registry. The PII sets are
**hand-built, not LLM-generated and called ground truth**.

| Module | Does |
|---|---|
| `builders.py` | Assembles corpora into frozen, content-hashed sets |
| `registry.py` | Freezing to disk, and the manifest that registers each set |
| `categories.py` | What each set's labels *mean* — the guard that refuses to measure a detector against labels for something else |
| `hinglish.py` | Hand-written Hinglish scenarios |
| `identifiers.py` | Synthetic Indian identifiers, and the forms they get disclosed in |
| `hard_negatives.py` | Boundary cases that **must be allowed** — the set that measures false positives |
| `banking.py` | The dual-labelled banking pilot |
| `resplit.py` | Reallocating a frozen set's declared splits without touching its data |

---

## `controlplane/detectors` — the things being measured

| Module | Is |
|---|---|
| `probe.py` | The linear probe: standardise, fit logistic regression, score. Raises rather than fitting or scoring in a way that leaks |
| `aggregation.py` | Pooling a sequence of residual-stream vectors into one feature vector — last-token, mean-pool, max-of-rolling-means |
| `presidio_adapter.py` | Presidio behind the warrant machinery, **unmodified**. Raises on an entity type it has no classification for rather than filtering it away |
| `presidio_custom.py` | The custom recognizers for the third configuration |
| `pii_reference.py` | Our own reference detector: patterns plus checksums |
| `identifiers_patterns.py` | Regular expressions for Indian identifiers |

**Each configuration is a separate detector id.** `presidio-stock` and
`presidio-enabled` are not one detector with a flag.

---

## `controlplane/extract` — the GPU stage

The only part that needs a GPU, and the only part most readers never run.

| Module | Does |
|---|---|
| `pipeline.py` | TriviaQA in, frozen eval sets and caches out |
| `activations.py` | Question-time activation extraction, and the padding evidence that proves it |
| `model.py` | Loading the model and tokenizer, with the left-padding assertion that has to hold |
| `triviaqa.py` | Loading, deduplication, question-level splitting, labelling |

---

## `controlplane/matrix` — detector × envelope

| Module | Does |
|---|---|
| `matrix.py` | The matrix itself, with its three states |
| `routing.py` | `route()` — given an envelope, which detector still holds a warrant here |

---

## `controlplane/drift` — when a warrant stops being true

| Module | Does |
|---|---|
| `monitor.py` | The sliding window and the revocation ladder |
| `psi.py` | Population Stability Index against a warrant's stored reference bins |
| `null_band.py` | The null distribution of PSI, so a band can be **checked rather than assumed** |
| `ladder.py` | A drift verdict decides what a warrant is still worth |
| `response.py` | Detect, transition, route — with **no manual trigger** |
| `certify.py` | The certificate a drift response leaves behind |
| `model_version.py` | Model-version invalidation: changed weights invalidate what was measured on the old ones |

---

## `controlplane/policy` — reading the warrant

| Module | Does |
|---|---|
| `bundle.py` | Policy as versioned, content-hashed data |
| `resolution.py` | **Load-time** warrant resolution — the fail-closed path |
| `engine.py` | The Rego adapter, via `regopy`; the only thing here that evaluates a rule. An engine cannot be built from an unresolved bundle, so no ordering exists in which a rule runs before its warrants were checked |
| `compose.py` | Composing two warranted detectors into one decision |
| `objective.py` | The weighted-error objective |
| `runner.py` | Issues the three operating points and decides one input under all three profiles |
| `errors.py` | `BundleError`, `WarrantResolutionError` — the second is **never a warning** |

Two traps `engine.py` documents and defends against, both silent: a Rego binding
that accepts a JSON *string* as input and then resolves nothing, returning
`ALLOW` for reasons no log would show; and an entrypoint typo that surfaces as a
native exception through the FFI boundary rather than a Python error.

---

## `controlplane/sampling` — the on-traffic estimate

Recall on the traffic nobody reviewed has to be estimated, and an estimate costs
labels. This package does that estimation and prices it.

| Module | Does |
|---|---|
| `estimator.py` | Recall estimated on your traffic, stratified by flag, with an interval. Refuses a sampled stratum it cannot use |
| `planning.py` | How many labels a recall claim costs, propagated through the derivative of recall with respect to the miss rate -- **not** sized as a prevalence, which understates the labels needed |
| `allocation.py` | Where to spend the labels: proportional allocation in month one, Neyman allocation only once per-stratum rates exist |
| `queue.py` | The label queue, **blinded**: no flag, score, stratum or ordering signal reaches a reviewer |
| `agreement.py` | Cohen's kappa with its own interval, published beside the warrant it qualifies |

---

## `controlplane/gate` — the action gate

What stops an agent's action, as distinct from what flags a response. **The
first two rules consult no detector**, so a detector that fails cannot open them.

| Module | Does |
|---|---|
| `gate.py` | Five rules, in order |
| `registry.py` | The reversibility registry: what each tool can do, declared where the tool is defined |
| `session.py` | The session Rule-of-Two: three sticky flags, and two of three is the limit |
| `cost.py` | What the gate costs on legitimate work, counted rather than asserted |
| `agent.py` | A four-tool banking agent, and an indirect injection **no detector flags** that the gate blocks anyway |

---

## `controlplane/external` — other people's detectors

Certification run on detectors and datasets this project did not build, at their
published revisions and splits.

| Module | Does |
|---|---|
| `registry.py` | Third-party detectors and public datasets, declared rather than hardcoded |
| `run.py` | One pairing: fetch, score, certify across the budget grid, emit |
| `redact.py` | Certifying on the REDACT benchmark at its own locked split |
| `matrix.py` | The external matrix: detectors down, budgets across, every cell reproducible |

---

## `controlplane/store` — the ledger

`ledger.py` is an append-only, hash-chained SQLite store of every issuance,
refusal, revocation, override and decision. Mutating a row breaks the chain,
demonstrably — that is a test, not a claim. It is generated and gitignored,
because the chain is only meaningful for the run that built it.

---

## `controlplane/economics` — what can and cannot be derived

| Module | Does |
|---|---|
| `sizing.py` | **The price list**: the negatives a recheck needs to catch a breach at a stated power, the labels to obtain them, and a year of each cadence. Derived from the single declared workload in `config.yaml` |
| `schedules.py` | A year of rechecks compared as sequential change detection: how often each rule falsely revokes a detector keeping its promise, and how fast it catches a breach |
| `detection_grid.py` | The chained recheck across breach sizes, cadences and change points |
| `feasibility.py` | The abstention floor: what **no** detector can do, however good. An impossibility result, derived from measured rates, needing no cost model |
| `review.py` | Review volume, and how many reviewed items a recall claim needs |

**Every cost figure derives from one declared workload.** It is declared, not
measured on anyone's traffic, and each artifact labels its inputs by origin so a
declared figure cannot pass as a measured one.

---

## `controlplane/report` — rendering and proving

| Module | Does |
|---|---|
| `claims.py` | Parses the README claim table and checks every number against its artifact |
| `results.py` | Renders `results/RESULTS.md`, with a hard refusal to print fixture numbers |
| `reproduce.py` | Re-derives the frozen-set evaluation from cached activations and diffs it |
| `clean_clone.py` | Clones the repository into a temporary directory and runs the gates inside it. Fails if the clone is not the commit it names, and refuses to write its record if the source changed while it ran |
| `test_inventory.py` | Counts collected tests from a clean commit, without calling collection a passing run |
| `invariants.py` | The nine invariants, each mapped to the test that enforces it |
| `causal.py` | Causal claims: each mechanism named with the falsifier that would refute it |
| `crosswalk.py` | The RBI's **draft** model-risk guidance, paragraph by paragraph: what a warrant provides, in part, or not at all |
| `price_list.py` | Renders the price list and the agreement figure into `RESULTS.md` |
| `spec_sections.py` | The `SPEC.md` sections `RESULTS.md` must carry |
| `sweep.py` | Renders `SWEEP.md`, refusing fixture numbers as `results.py` does |
| `regression.py` | Refuses to replace a rich artifact with a poorer one |
| `beats.py` | Assembles the demo's beats from committed artifacts. Reads; decides nothing |
| `plots.py` | Plots, each carrying the provenance of the numbers in it |

---

## `controlplane/demo`, `gateway`, and `config`

- **`demo/session.py`** decides; `demo/stream.py` replays a recorded request
  stream so the demo does not depend on live traffic. The runner in `demo/`
  renders and holds no logic.
- **`gateway/adapter.py`** is an OpenAI-format adapter that returns
  certificates — an adapter, not a gateway. Explicitly the lowest-value piece.
- **`cli.py`** is the `warrant` command: `certify`, `recheck`, `plan`, `chain
  verify`, and `release` via `release/cli.py`. It parses arguments, calls the
  packages above and writes records, with one exit-code convention: `0` for any
  result including a refusal, `1` when a `--require-*` flag was not met, `2` for
  input that cannot be used.
- **`coordination/`** is development tooling, not product: a local, file-backed
  board where concurrent coding sessions post status, messages and advisory path
  claims (`python -m controlplane.coordination read`; `COORDINATION.md` at the
  root). It opens no network connection, and a claim does not stop an edit.
- **`config.py`** is the single source of every knob: typed dataclasses
  mirroring `config.yaml`, validation in `__post_init__` naming each invariant
  it enforces, SHA-256 config hashing, and `provenance()` — which shells out to
  `git status --porcelain` so an artifact can never silently claim a clean tree.

---

## Specified, and not built

An earlier version of this page said `controlplane/sampling/` and
`controlplane/gate/` did not exist, and that the price list was never built. All
three were built later (`DECISIONS.md` 146-150, 156) and are described above; the
sentence had gone stale, which is the failure an orientation page exists to
avoid.

What is genuinely absent is declared in [LIMITATIONS.md](LIMITATIONS.md) §3: the
Qwen3Guard and LLM-judge adapters, drift features beyond token length, embedding
MMD, a matrix that fills its own unvalidated cells, and a scheduler behind a
stale warrant's promised revalidation.

---

**See also:** [DIAGRAMS.md](DIAGRAMS.md) for how these fit together · [ARTIFACTS.md](ARTIFACTS.md) for what they write · [TESTING.md](TESTING.md) for what defends them.
