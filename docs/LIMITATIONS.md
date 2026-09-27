# LIMITATIONS.md — scope, declared gaps, open items

Read this before quoting any number from [README.md](../README.md).

Nothing here was found by a reviewer. Every item was found by this project's
own controls, pre-registrations or audits, and each names the decision entry
that records it. That is the point of the list: a system whose value rests on
saying what it does not know has to be willing to say it about itself.

---

## 1. What was measured, and on what

| | |
|---|---|
| Model | Qwen/Qwen2.5-7B-Instruct, NF4 4-bit. **One family, one size.** |
| Hallucination envelopes | TriviaQA no-context: 2,400 items, split by question into 960 / 480 / 960 |
| PII envelopes | `hinglish-pii-200`, `hinglish-pii-200b`, `hard-negatives-200` — **hand-built by us**, synthetic identifiers |
| Real traffic | **None.** No production data of any kind touched this. |
| Human labelling | **None.** Correctness labels come from TriviaQA alias matching; PII labels are construction-time. |

No result here transfers to another model family, another task, or real
traffic without being re-measured. That is not a caveat bolted on — it is the
argument. A detector's bounds are a property of a detector *and an envelope*,
and this repository exists to say so.

---

## 2. The six that change how you read the claim table

### 2.1 Calibration drift is detectable at 25%, not at 10%

Separating a 25% deviation from a declared flag-rate budget needs **n ≥ 1441**.
These envelopes were measured at n = 600 to 960. Every budget claim in the
matrix is therefore refused outright or marked **unresolved** — the interval
extends past the band and this sample could not have narrowed it.

This is a limitation of sample size, not of method. The *ranking* claims on the
same warrants are supported: AUROC intervals at this n are tight enough to
separate the detectors from each other, which is what the drift beat rests on.
Closing it needs more test items, not more code.

`DECISIONS.md` 069, and the sensitivity table in
[results/RESULTS.md](../results/RESULTS.md).

### 2.2 Every published recall interval is conditional on a threshold set by as few as five items

Thresholds are selected on validation to hit a flag-rate budget. At the
`customer_support` budget, the threshold is determined by **5 negatives** in a
480-item validation split. The published recall interval treats that threshold
as fixed, which it is not.

Propagating the selection noise widens the recall bound by **1.36x to 1.59x**:

| operating point | conditional | selection-aware | widening |
|---|---|---|---|
| `P-customer-support` | [0.1774, 0.2551] | [0.1468, 0.2706] | 1.59x |
| `P-internal-knowledge` | [0.3157, 0.4048] | [0.3009, 0.4269] | 1.42x |
| `P-decision-support` | [0.6935, 0.7747] | [0.6734, 0.7840] | 1.36x |

The claim table quotes the **conditional** interval, because that is what the
artifact's `metrics` block holds, and names the widening in its own row rather
than burying it. `DECISIONS.md` 083, `results/paired_comparison.json`.

### 2.3 Two of the four PII recalls are in-sample

`presidio-enabled_plus_custom` at 0.6176 and `pii-reference` at 0.7941 were
both measured on the set their patterns were written against. The sequence was:
measure stock → read the failures → widen the recognisers → re-measure. That is
a detector fitted to its evaluation data by a human rather than by gradient
descent, and the number is in-sample.

Decomposed by pattern origin, **11 of 34 patterns (32.4%) are spec-derived**;
the rest are fitted, including the spaced and obfuscated UPI/IFSC forms.

`hinglish-pii-200b` was pre-registered and built as an out-of-sample companion.
Every refusal reproduces on it, and every recall moved *up* by 0.03–0.04 —
including for the two detectors that were never fitted, which means the holdout
is marginally easier rather than that the fitting was harmless. **It is
underpowered**: only 5 of 102 positives carry formatting outside what the
recognisers were written against.

The half of the finding the demo rests on — that **stock and fully-enabled
Presidio are refused** — is not affected: neither was fitted to anything.

`DECISIONS.md` 084, 085, 086, 087.

### 2.4 8 of 17 populated matrix cells are synthetic fixtures

They exercise the harness. They are not measurements of a language model. The
renderer **refuses to print their numbers** rather than relying on a reader
noticing a footnote, and their eval sets hash differently so they occupy
different matrix cells and can never be read as measured ones.

The T2 (logprob) and T3 (judge) rungs of the tier ladder are fixture-only. The
tier curve as a *measured* object covers T1 activations and T3 text detectors.

`DECISIONS.md` 034, and the warning at the top of
[results/RESULTS.md](../results/RESULTS.md).

### 2.5 The long-context envelope is 2.8k to 11.1k tokens of repeated filler

`triviaqa-longctx-600` was specified as *4-16k tokens*. As built, the
extraction cache records **2,838 to 11,103 tokens, median 6,954, with 82 of 600
prompts under 4,000** (`results/cache-triviaqa-longctx-600.npz`,
`__token_lengths`). The builder estimated four characters per token; this filler
tokenises at about 5.8.

Two construction facts bound what the long-context results mean:

- **The padding is a small pool of paragraphs, repeated** — a median of 238
  paragraphs per prompt drawn from eight. It is a dilution test, not a retrieved
  corpus, and a detector's behaviour on varied long documents is not measured.
- **Labels are the short-context pass's.** The long pass is prefill-only, so a
  label records whether the model answered correctly *without* the padding.

The mean-pool collapse and last-token survival are measured on this set and hold
for it. Nothing here was measured past 11,103 tokens. `DECISIONS.md` 052, 171.

### 2.6 `n` on a rate is the eval set's size, and lift's upper bound is not a bound

Every rate carries `n`, and on recall, precision and flag rate it is the number
of eval-set items resampled — **not the proportion's denominator**. A precision
of 23/25 carries `n = 600` and an interval the width of 25 trials. The RESULTS
table now prints positives and flagged beside `n`; the field itself is set in
read-only `validation/stats.py` and is an open item.

Lift's interval holds the flag rate fixed. That makes its **lower** bound
conservative — the one the refusal bar reads, and pinned by
`tests/test_lift_interval.py` — and pushes its upper bound past the physical
ceiling on every real T1 artifact. RESULTS.md shows the lower bound only.
`DECISIONS.md` 169, 176.

---

## 3. Specified and not built

### 3.1 Phase 6 economics — the price list, and five contracts still citing it

> **Closed 2026-09-11** (`DECISIONS.md` 146-150). The price list is built:
> `controlplane/economics/sizing.py` derives it from the one `workload` block,
> `controlplane/sampling/` holds the on-traffic estimator it prices, and
> `tests/test_sampling.py::test_no_scenario_mixing` enforces invariant 6. The
> figures are rendered into `results/RESULTS.md` from
> `results/on_traffic/on_traffic.json`. What remains true below: **no production
> traffic exists**, so the price list is priced on a declared workload and the
> estimator's coverage is measured on synthetic traffic with known truth. The
> original text is kept as the record of the gap.

> **Amended 2026-08-29** (`DECISIONS.md` 099). Two quantities that needed no new
> measurement are now derived rather than declared: the **abstention floor**,
> and **how far each operating point sits above it**. See
> [PROPOSAL.md](PROPOSAL.md) §1–2 and `results/feasibility.json`.
> `controlplane/economics/` now holds `feasibility.py` and `review.py`.
> Everything below still applies to the **price list**, which is what remains
> unbuilt.

`controlplane/economics/sizing.py` and `test_no_scenario_mixing` are cited as
load-bearing in **five** documents — `config.yaml`, `CLAUDE.md`,
[SPEC.md](SPEC.md) §6.4 and §12, [TASKS.md](TASKS.md) Phase 6, and
[KICKOFF.md](KICKOFF.md). **Neither exists.**

The claim those citations make is that no economic figure is typed by hand,
because a module derives all of them from the single `workload` block. That
enforcement does not exist. What does:

- `config.yaml` declares exactly one `workload` block, so there is one scenario
  to mix figures *from*, and no second one anywhere in the tree;
- **no economic figure appears in any committed artifact.** The measured
  outputs are AUROC, recall, precision, flag rate, lift and their intervals.
  Nothing downstream consumes `workload`.

So the invariant currently holds by *absence* rather than by construction —
there are no economics to mix. That is much weaker than what the contracts
describe, and it stops holding the moment anyone writes a cost number into the
proposal or the deck.

**Any cost, headcount or ROI figure in [PROPOSAL.md](PROPOSAL.md) or the deck
is hand-derived and must be labelled a declared estimate, not a measured
result** — the same treatment as the two carried-forward Round 1 numbers. The
feasibility bound and the efficiency ratios are exempt: they are derived from
measured rates and carry no cost model. The review volumes are half-exempt —
the flag rates are measured, the workload is declared, and the artifact labels
every input by origin so a later conversion to money cannot lose which was
which.

The contracts keep their references rather than having them quietly deleted. A
spec that describes an unbuilt module and says so is scoped; one edited to hide
it is not. `DECISIONS.md` 096. Found by the E.1 path audit, which was looking
for something else.

### 3.2 Phase 9 action gate

> **Closed 2026-09-11** (`DECISIONS.md` 156, 160). The gate is built:
> `controlplane/gate/`, measured by `scripts/27_gate.py` into `results/gate/`.
> Its first two rules read no detector. What it does **not** establish: the
> injection result is one declared scenario, the cost is an exact count over
> eight declared workflows rather than a production rate, and it is not a
> robustness claim. `reports/PHASE-6.md` §5 lists what it does not defend
> against. The original text is kept below.

`controlplane/gate/` — the reversibility registry, session Rule-of-Two and
action ladder — was specified and not built. Composition produces an action;
nothing enforces one. Marked NOT BUILT in the `CLAUDE.md` layout block.

### 3.3 Other declared absences

- **No serving layer.** No auth, no rate limiting, no HA, no deployment
  manifests. Ruled out of scope in `CLAUDE.md`; the LiteLLM adapter is an
  adapter and holds no credentials and no routing, enforced by
  `test_the_adapter_owns_no_credentials_and_no_routing`.
- **No second model family and no second task.** Every cross-envelope claim
  here is one model under a distribution shift, not two models.
- **`qwen3guard` and the LLM-judge adapter are not built.** The judge rung is a
  fixture.
- **OPA is not used.** Rego is evaluated through `regopy` (rego-cpp), which is
  not OPA and does not share its evaluation semantics in every corner.
  `DECISIONS.md` 076.

### 3.4 Specified in `SPEC.md`, declared in config, and not computed

Found by walking the specification against the code, section by section.
Each is visible at runtime — a verdict or certificate names it — and none was
stated here.

- **Drift is watched on one axis.** Of the five envelope features in
  `config.yaml`, only input token length is computed and fed to the monitor.
  Script mix, embedding centroid distance, reference perplexity and category
  mix are not, so a shift in language or topic at a constant length passes
  unseen. MMD on embeddings is not implemented. `DECISIONS.md` 172.
- **`STALE` promises a revalidation nothing schedules.** The ladder widens
  bounds by a declared 1.5x and its message says revalidation is scheduled;
  no scheduler exists. The message is in read-only `drift/`. `DECISIONS.md` 172.
- **The matrix does not self-populate.** Unvalidated cells are handed to a
  callback that logs them. `DECISIONS.md` 170.
- **The weighted-error weights select no threshold.** Every shipped operating
  point is chosen at a declared flag-rate budget; the objective in §7.4 is
  implemented and tested and has no caller, and the bundles' weights are
  identical across the three profiles. The tradeoff that moves the threshold
  is the flag-rate budget. `DECISIONS.md` 174.
- **On-traffic FPR is not computed.** The price list calls it free; its
  denominator depends on the estimated misses, so it is nearly free and
  estimated. `DECISIONS.md` 173.
- **There is no labelled agent-action trace set.** The gate is measured on
  declared scenarios. `DECISIONS.md` 171.

### 3.5 The recheck chain catches a breach less reliably at a monthly cadence

`warrant recheck --horizon-labels / --since` (`DECISIONS.md` 193, 194) bounds the
chance that the chain's sequential false-positive statistic falsely revokes a sound
detector over its declared negatives. A revocation because the score distribution
moved is a separate check, outside that bound. The statistic's bound held
in every setting simulated: at most **0.012** of years across three breach sizes
and four cadences, against a limit of 0.0646 (`DECISIONS.md` 196,
`results/chain_detection/grid.json`).

**Detection is not uniform.** Each breach size was rechecked at its own 0.80-power
size -- 628, 191 and 59 negatives. At those sizes, weekly rechecks caught a breach
within 13 weeks in at least 0.9900 of simulated years, and **monthly rechecks caught
it within three months in only 0.8325 to 0.8970** -- a breach missed for a quarter
in about one year in six to one in ten. **The miss rate depends on the labels per
recheck as much as on the breach size**: the larger breaches were rechecked with
far fewer labels, so these figures do not order detection by breach size at
comparable effort (`DECISIONS.md` 196, review).

What this does not cover: one budget (0.05), step changes, independent fresh
samples, the recheck sizes `plan` quotes at power 0.80, and a fixed number of
negatives in every recheck -- a real chain that exhausts its horizon early is not
live through the last window. `plan` quotes no
detection figure, and should not, for settings outside this grid.

**Publication scope (DECISIONS 206).** Chained CLI invocations now serialize
head validation and publication under a lock keyed by the canonical warrant path.
A retained intent recovers the original sealed record after process interruption;
conflicting data fails closed. This coordinates cooperating local processes on
filesystems with the required lock, hard-link and atomic-replace semantics. It is
not distributed consensus, protection against removing the sidecars, a lock
shared by separately copied warrants, or proof of durability through power loss.
A process killed while preparing a file can leave an unreferenced temporary file;
that file is not an accepted chain link. Unsupported operations fail explicitly.
The unchained recheck now consults the chain-head sidecar and reports a recorded
revocation as the status while keeping the measurement (`DECISIONS.md` 210); with
no sidecar, nothing is known and nothing is claimed. Local process
and installed-wheel test evidence, plus untested platforms, are recorded in
[PHASE-14.md](../reports/PHASE-14.md).

### 3.6 A warrant is exact about its labels and cannot see whether they are right

Every certificate is a statement about the `label` column it was given. Since
`DECISIONS.md` 197 each one says how far it depends on it, and on this project's
own measured TriviaQA certificates that is not far. **Between 2 and 8 flagged
positives that are really clean take a certificate from at least 0.95 to below
0.80 confidence**, across 60 certified rows (3 probes x 20 budgets;
`results/label_sensitivity/triviaqa.json`, `DECISIONS.md` 199). How many errors a
certificate tolerates is set by its negatives, budget and alpha, not by the
detector. A detector that flags more positives is exposed to more of the costly
kind. The figure is for the certificate as issued, at its threshold, and counts
one error kind at a time. It does not say that corrected labels could not be
certified: they could be, at another threshold and another recall.

**What was measured.** The labels are lenient alias matching. Strict exact match
on the same responses disagrees on 41 of 600 test items (kappa 0.8640
[0.8213, 0.9035]), every one a response lenient calls correct. Counting all of
them as labelling errors leaves the lowest certificate at 0.8127.

**What was not.** A correct answer whose wording is missing from the alias list
is labelled incorrect by both rules, so no comparison of the two can see it. When
flagged, it is exactly the costly error: at budget 0.20, 8 of `last_token`'s 179
flagged positives would take its certificate below 0.80. How many exist is
unknown. What would close it is a blind human audit of a sample of the flagged
lenient-incorrect answers.

On the customer path, an optional `label_2` column measures agreement beside the
warrant and changes nothing in it (`docs/INPUT.md`). Recall and precision
intervals are still silent about label error, and a chained recheck carries no
sensitivity. **On grouped files, the population agreement interval is withheld**
(`DECISIONS.md` 201): independent-pair resampling cannot account for dependence
inside a group, and no validated grouped agreement interval is implemented.
Observed pairs retain their descriptive kappa, raw agreement and contingency
table, with reviewed-pair and reviewed-group counts. These are descriptions of
that reviewed subset, not evidence of population agreement or label correctness.
Group counts exclude groups with no second review. Null kappa when both
reviewers use one category is distinct from a withheld confidence interval.
Ungrouped paired-bootstrap intervals are unchanged. Neither pathway detects
shared reviewer mistakes or establishes that review selection was representative.
This repair does not change recall/precision intervals or claim to validate
other grouped estimators; their separate audit findings remain open in
`reports/PROJECT-REVIEW-2026-09-23.md`.

### 3.7 Most records the customer CLI writes can be edited without detection

A chained recheck record is sealed over every field, and `warrant chain verify`
recomputes each seal (`DECISIONS.md` addendum 2026-09-17). A release evaluation is
sealed and recomputed by `warrant release verify`. **Nothing else is.** A `certify`
warrant, a frontier record, an unchained recheck and a `plan` record carry no seal,
and no command verifies them. `recheck` reads the warrant it is given as written.

Two limits apply even to the sealed records:

- **A seal is a checksum, not a signature.** Anyone who can write the records can
  recompute every seal consistently. It catches an edit made without recomputing,
  not a forger.
- **A missing seal is unknown integrity**, not an established legacy creation
  date. It can mean legacy data or a removed seal. Such a record remains
  inspectable but cannot pass `clean` or `--require-clean`, and cannot be
  continued, including with `--fork` (DECISIONS 207). Available structural checks
  are reported separately; they do not recover full-record assurance.

What would close it: a seal and a verifier for the certify warrant, which every
later record depends on. A signature would need a key, and a key is custody this
project does not hold.

---

## 4. Open items at submission

### 4.1 The D.2 measured pair — **open**

The composition rules of `DECISIONS.md` 088 are implemented and exhaustively
tested against fixtures. What is missing is a **measured pair**: no eval set
carries labels for both a hallucination positive class and a PII positive
class, and the category guard now correctly refuses to manufacture one by
warranting a detector against labels that mean something else.

Construction notes are inside the content hash, so adding a second label to a
frozen set would change its identity and orphan every warrant keyed on it —
the third time that constraint has bitten.

Three ways forward, all requiring a GPU pass, none taken:

1. a dual-labelled eval set — the honest fix, and the only one that makes the
   brief's actual claim measurable;
2. both detectors on `hard-negatives-200`, giving two FPR-only warrants and a
   real composed decision on an envelope where neither can claim recall;
3. report the mechanism as built and tested and the measured pair as an open
   gap — **this is what was done.**

The finding is worth more than the demo it blocked. A system that will happily
warrant a PII detector against hallucination labels is one whose warrants mean
less than they appear to, and nothing else in the build would have surfaced it.
`DECISIONS.md` 089, 090.

### 4.2 `DECISIONS.md` 080 — **unresolved**

080 reports all four pre-registered re-split criteria met. Its criterion 3
turns on `customer_support` loading at n_test 960 against the 673 a 0.10 budget
needs at 25% sensitivity — and §2.1 above says every budget claim at these
sample sizes is unresolved. The two statements are in tension and 080 has not
been superseded with the resolution.

Quote 080's recall numbers, which are measured and reproduce. Do not quote it
as evidence that the calibration question is settled.

### 4.3 The withdrawn claim at `67167ed`

That commit message states the training reduction "cost nothing measurable".
**It is wrong**, the comparison was confounded, and the correction lives in a
git note rather than a rewritten history:

```bash
git fetch origin "refs/notes/*:refs/notes/*"
```

Without that fetch a reader sees the withdrawn claim and not its correction.
The paired comparison found the reduction cost **0.0110 AUROC [0.0026,
0.0200]**, an interval excluding zero. `DECISIONS.md` 081.

### 4.4 PSI's smoothing epsilon is not declared in config — **open**

The `drift/psi.py` module docstring says the epsilon that floors an empty bin "is
declared in config rather than buried". It is not: it is the module constant
`DEFAULT_EPSILON`, `drift/null_band.py` repeats the same value as a keyword
default, and `config.yaml` has no such key. Because the live computation and the
null band use the same value, no PSI figure or band is inconsistent. What is wrong
is the statement, and the knob a reviewer is told exists.

`drift/` is a read-only zone, so this is recorded rather than fixed. What would
close it: a `drift` config key read by both call sites, or a docstring that says
the value is a constant.

---

## 5. Things that are limitations of the *result*, not of the work

Worth separating, because they read as weaknesses and are not.

- **Recall is low.** 0.0794 at a 4.2% flag rate. That is a lift of ~1.9x at a
  ceiling of 2.17x — about 88% of everything attainable at this base rate.
  TriviaQA no-context is deliberately hard; the model is wrong on 46% of it,
  which caps what any triage can beat random sampling by.
- **39 of 56 matrix cells are UNVALIDATED.** This is the expected shape, not a
  gap. UNVALIDATED is the modal state in any real deployment, and the value of
  the matrix is that it can say so.
- **Four warrants are REFUSED.** Also the point. A component correctly refused
  is a stronger artifact than one tuned until it passed.
- **Our reference PII detector buys its recall with precision.** On
  `hinglish-pii-200` it has the highest recall of the four configurations and
  a lower precision than Presidio with custom recognisers; both are in the
  claim table, side by side, because invariant 5 requires it and because the
  recall row alone read as a clean win. `DECISIONS.md` 170.
