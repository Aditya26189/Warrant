# JOURNEY.md — what this project actually did, step by step

<sub>[🏠 Project README](../README.md) · [📚 Documentation index](README.md) · [🗺️ Diagrams](DIAGRAMS.md) · [📖 Glossary](GLOSSARY.md)</sub>

The narrative the commit log and `DECISIONS.md` contain between them, in one
place. No measured numbers here: the claim table in
[../README.md](../README.md) holds those, and this page is about what happened
and why.

For the same story as pictures, [DIAGRAMS.md](DIAGRAMS.md) §10. For the phase
gates as they were written in advance, [TASKS.md](TASKS.md).

> **Two numberings, not one.** The *build phases* 0–12 are the order
> [TASKS.md](TASKS.md) set before the submission. The *sprints* that followed also
> run 0–12, and each closed with a report at `reports/PHASE-<N>.md`. A reference
> to "Phase 6" means the action gate in the build plan and the sprint that built
> it; this page always says which.

**Contents:** [Round 1](#round-1--measuring-one-detector) · [The turn](#the-turn--from-a-detector-to-a-warrant) ·
[Build phases](#phase-by-phase) · [Five things that changed what we believed](#the-five-things-that-changed-what-we-believed) ·
[The reorganisation](#the-reorganisation) · [After the build: the sprints](#after-the-build--the-sprints) ·
[What changed our mind after the build](#what-changed-our-mind-after-the-build) · [Where it stands](#where-it-stands)

---

## Round 1 — measuring one detector

The competition brief asked how you would catch a model that is confidently
wrong without slowing it down. Round 1 answered by measuring one thing
properly: whether a **linear probe on question-time activations** — read after
the model has finished reading the question and before it generates a token —
can pick which responses are worth sending to an expensive checker.

The output was a single ratio and its interval: recall over the measured flag
rate, i.e. how many more errors you catch than random sampling at the same
budget, reported beside the ceiling that `1 / base_rate` imposes on any selector
at all.

What that work established, and Round 2 kept:

- **question-time, not mid-generation** — the signal is available before a token
  is paid for, so it can route as well as monitor;
- **splits by question, deduplicated first** — an example-level split leaks
  near-identical questions across train and test;
- **the padding trap and its positive control** — with right padding, position
  −1 is a pad token and every activation is meaningless with nothing raised, so
  the check that proves otherwise must itself be proved by requiring it to
  reject a deliberately broken variant;
- **precision and recall separately, never blended.**

That whole submission is preserved under `round1/`, moved unmodified.

**The question it could not answer:** the number was measured on TriviaQA. What
is it worth on traffic nobody measured it on? Nothing in Round 1 could say — and
neither can any dashboard that reports a detector's score without saying what
that score is worth *here*.

---

## The turn — from a detector to a warrant

Round 2's claim is not "our detector is good". It is:

> A detector produces a score. A **warrant** is a separate, time-bounded,
> evidence-backed statement about what that score is worth on this distribution
> right now — and policy reads the warrant, not the score.

Three consequences follow immediately, and they shaped everything after:

1. A warrant must be keyed by **(detector, operating point, envelope)**. Keyed
   by detector alone it would travel to distributions where it was never
   measured, which is the failure being fixed.
2. **Refusal must have no override.** If a flag existed to promote a failing
   detector, the whole thing would be theatre — and a reviewer would look for
   exactly that flag first.
3. `UNVALIDATED` must be a real, permanent third state. In production most
   (detector, envelope) pairs have never been measured, and collapsing that into
   "fine" or "bad" is how a dashboard stays green while a guardrail is dead.

---

## Phase by phase

Each phase had a gate written **before** it ran. That ordering is the point: a
gate composed after the number is visible is not a gate.

| Phase | What it built | The gate it had to clear |
|---|---|---|
| **0 — Scaffold** | Config dataclasses, YAML loading, SHA-256 config hashing, `provenance()` | The config hash is stable across runs, and `provenance()` reports `dirty` correctly after touching a file |
| **1 — Data model and store** | Frozen record types; the hash-chained SQLite ledger | A certificate round-trips; mutating a row **demonstrably breaks the chain**; an `EXACT` metric carries no interval and an `ESTIMATED` one always does |
| **2 — Validation harness** | The five controls, `/validate`, `issue_or_refuse`, the tier ablation | Every control reports with measured margins, the deliberately broken padding case is **rejected**, and no override path exists |
| **2.5 — Demo runner** | Two panes and a stream player, ugly on purpose | A recorded stream plays and "prove it" runs a **real** validation. Grown every phase after, rather than built at the end |
| **3 — Evaluation sets** | Hand-built Hinglish PII, hard negatives, long-context and canary sets, frozen and content-hashed | Every set registered and hashed; the PII sets **hand-written, not LLM-generated and called ground truth** |
| **4 — The warrant matrix** | Every (detector × envelope) cell as VALID / REFUSED / UNVALIDATED, plus routing | The matrix renders with every cell populated and the three states behave differently |
| **5 — Drift and revocation** | PSI on input token length, the revocation ladder, model-version invalidation. The other four declared envelope features and MMD were **not built** | Fed a shifted distribution as live traffic, the system detects, revokes, **routes to a detector that still holds a warrant, adopts its bounds**, and writes a certificate — with no manual trigger |
| **6 — On-traffic warrant** | **Specified, not built during the build.** The stratified estimator and the computed price list | Built afterwards, in sprint 4 |
| **7 — Policy engine** | Rego bundles as versioned data, load-time warrant resolution, three profiles | A bundle naming an unwarranted operating point **fails to load**, and three profiles give three actions at three points on one measured curve |
| **8 — Detector adapters** | The probe adapter, the three Presidio configurations, our reference PII detector | Stock Presidio is **refused** a warrant, with its measured recall inside the refusal reason |
| **9 — Action gate** | **Specified, not built during the build.** Reversibility registry, session Rule-of-Two, the gate | Built afterwards, in sprint 6 |
| **10 — Demo harness** | The five beats, rendered from committed artifacts | The demo runs end to end twice without intervention, and the drift beat shows **routing**, not just an alarm |
| **11 — Gateway adapter** | A LiteLLM-shaped adapter that returns certificates | Lowest value, first to be cut if pressed |
| **12 — Submission** | The claim table, the verification tiers, the clean-clone gate, the documentation audit | Every number traces to an artifact; the history reads as an account to someone who was not here |

---

## The five things that changed what we believed

These are the moments where a measurement contradicted a plan. They are the
reason `DECISIONS.md` is append-only.

### 1. The closed-form null bands were wrong — three times

A negative control asserts "consistent with chance", and whether an observed
value is consistent with chance depends on sampling noise. The first design
scaled the band by the Hanley–McNeil null standard error. A control then failed
at a value that model called a three-sigma event — on the second run.
Three-sigma events do not happen on the second run, so the model was wrong:
Hanley–McNeil assumes exchangeable scores under the null, and a **fitted**
probe's are not.

The same shape recurred for the drift monitor's PSI bands, which are
credit-scoring rules of thumb quoted without their sample size and are not
scale-free.

**What changed:** every band is now *simulated at construction* from the
measured spread, and reported with the band it applied. A monitor that fires on
a large fraction of stable windows is not a monitor.

### 2. A published claim was wrong, and stayed visible

One commit compared two models trained on different amounts of data and
concluded the reduction "cost nothing measurable". **Training size and
evaluation sample had both changed**, so the difference was unattributable.

The correct comparison pairs the two models on the items **both** held out and
bootstraps the difference. It found the opposite sign of conclusion.

**What changed:** the history was not rewritten. A git note attached to that
commit carries the correction, and the README tells readers to fetch
`refs/notes/*` in the setup section rather than in a footnote. A withdrawn claim
that stays visible next to its correction is worth more than a clean log.

### 3. Recall intervals were hiding where the threshold came from

Every published recall interval was **conditional on a threshold** that had
itself been estimated — at one operating point, from a handful of validation
negatives. Treating an estimated quantity as fixed narrows the interval by an
amount nobody had computed.

**What changed:** the selection-aware widening is computed and published as its
own row in the claim table, rather than buried or quietly folded in.

### 4. The guard against unsourced numbers had the defect it guarded against

A register was built to stop figures about the world entering as ordinary prose.
Its own provenance column then asserted a verification tier nobody had reached.

**What changed:** the register now declares only the two tiers that actually
exist, a relayed figure may be mentioned but never load-bearing, and a test
enforces the forbidden figures against the proposal. The write-up leads with the
correction instead of hiding it.

### 5. Reading is not a control

A trap documented in the contributing guide fired again **two messages after it
was written down**: piping a command whose exit status matters reports the
pipe's status, so a failing suite reads as green.

**What changed:** the correct form became a wrapper script rather than a
remembered rule. The general lesson runs through the whole design — an invariant
that depends on someone remembering it is not enforced. That is why metrics are
validated in `__post_init__`, why `issue_or_refuse` takes no promoting argument,
and why a policy bundle resolves its warrants at load time.

---

## The reorganisation

Until late in the build, cloning the repository landed a reader on Round 1 while
Round 2 sat one level down in a directory whose name contained a space.

Round 2 became the repository root and Round 1 moved whole into `round1/`, in
four commits, entirely with `git mv` — so `git log --follow` reaches the
original commits through every rename. Because artifacts record the paths they
were generated from, the move was audited before anything moved rather than
after. The full mapping is [PATHS.md](PATHS.md).

---

## After the build — the sprints

The submission ended the build, not the work. Each sprint asked one question,
registered its criteria before it ran, and closed with a report that leads with
the answer, favourable or not. The reports are the primary account; this is the
index to them.

| Sprint | The question | The answer, in short |
|---|---|---|
| [0](../reports/PHASE-0.md) | Is the probe's recall a ceiling, or a policy choice? | A policy choice: the false-positive budget was binding, not the probe |
| [1](../reports/PHASE-1.md) | Can any of it be quoted yet? | Yes: certified on validation and scored on test, the conclusion stood |
| [2](../reports/PHASE-2.md) | Can anyone else use it? | Yes: `warrant certify` on a customer's own file, reaching a warrant or a refusal in one command |
| [3](../reports/PHASE-3.md) | Does it mean anything outside the repository? | Yes, on other people's detectors and public data, and our detector is not the best entry |
| [4](../reports/PHASE-4.md) | Does the first clause, the on-traffic warrant, exist? | It did not, and the sizing quoted in its place had been in the wrong units. Built, and the sizing corrected |
| [5](../reports/PHASE-5.md) | Can the method certify a detector that emits no score? | Not yet for a real one; what repeated sampling buys is now priced |
| [6](../reports/PHASE-6.md) | Is there a control that survives a detector losing? | Yes, the action gate, but not as specified: the specified Rule-of-Two let the canonical injection through |
| [7](../reports/PHASE-7.md) | Does the evidence reproduce, or only pass its own checks? | It reproduces from the committed caches |
| [8](../reports/PHASE-8.md) | Does the outward-facing material claim what the evidence supports? | No, and it was wrong in both directions |
| [9](../reports/PHASE-9.md) | Does the repository pass its own documentation audit? | It had never been run; it failed most lines, and the audit is now checkable |
| [10](../reports/PHASE-10.md) | Does the specification describe what shipped? | No; each section walked and reconciled |
| [11](../reports/PHASE-11.md) | Does it meet the definition of done? | Everything code can produce is produced; what remains no code closes |
| [12](../reports/PHASE-12.md) | What in the customer path still promises more than its evidence? | Three things, each fixed or bounded; then the chain of rechecks, label error, and an independent review's findings |

### What sprint 12 and its addenda added

- **Rechecks as one test.** A year of rechecks is a change-detection problem, so
  the rule was chosen by a pre-registered comparison, then carried in the records
  as a chain (`DECISIONS.md` 187, 193, 196).
- **An independent review of the chain** found a revocation that could be
  continued past and fields that could be edited with verification still clean.
  The fixes are 194 and two dated addenda, the last of which seals every record
  and tests the whole class rather than the instances.
- **A budget picked off the frontier** is certified at the level the frontier
  held it to (192, 195).
- **Label error.** Every certificate says how many wrong labels it can take, and
  a second reviewer is measured beside it, never obeyed (197, 198, 199).
- **Release evidence**, a separate pre-registered workflow for one release
  decision, built in parallel (184–186).
- **The clean-clone gate** records the one commit it tested (200).

---

## What changed our mind after the build

The same pattern as the five above, at a larger scale: each time, a control
existed wherever a number might be arithmetically wrong, and nowhere else.

### 6. The error the project was built to prevent was in the project

`CLAUDE.md`'s silent-failure list opens with *sizing a prevalence and calling it
recall*. The repository's own label budget did exactly that, in the correct
arithmetic and the wrong units, for four sprints (`DECISIONS.md` 147).

**What changed:** sizing goes through the derivative of recall, in a module whose
docstring leads with the defect, and a test forbids mixing scenarios.

### 7. The rule as specified did not fire

The specification's Rule-of-Two read the session **before** the call. In the
canonical injection the dangerous call is the one that sets the third flag, so
the rule allowed it (`DECISIONS.md` 156).

**What changed:** the rule counts the call being made, and the defect is kept as a
test so it cannot come back.

### 8. A sample size is a probability, not a count

A recheck sized so that an observed breach would revoke catches a true breach
about half the time; the recall price, sized at its expected count, met its margin
about half the time (`DECISIONS.md` 183, 191).

**What changed:** every sample size the customer sees is quoted at a declared
power or assurance.

### 9. The verifier checked its own computation, not the record

The chain verifier recomputed what it knew how to recompute and never compared
it with what the record presented. Instances were fixed one at a time until a
schema-driven audit showed the class was much larger than the instances.

**What changed:** every chained record is sealed whole, and the test walks every
field of real records, mutates each one alone, and requires the verifier to
notice. A field added later is covered without anyone adding it.

---

## Where it stands

- A validation harness whose five controls include one that must **fail** on a
  deliberately broken input to pass.
- A (detector × envelope) warrant matrix in which most cells are honestly
  `UNVALIDATED`, several are `REFUSED` — including detectors we chose to point
  the machinery at — and the rest carry bounds with intervals and an expiry.
- A drift monitor with a simulated null and a revocation ladder that routes
  rather than alarms, on one feature.
- A policy layer that fails closed on a missing warrant, and an action gate whose
  first two rules read no detector.
- An on-traffic estimator and a computed price list, over a declared workload.
- A command a validation team runs on its own detector: certify or refuse,
  recheck, chain, plan, and a separate release workflow.
- A claim table that a stranger can check on a laptop in minutes, backed by
  frozen per-item scores and a clean-clone gate.

**What is still not established**, and no amount of code closes: no customer's
traffic, no human labels, no pilot, and no evidence that anyone will pay.
[LIMITATIONS.md](LIMITATIONS.md) and the last sprint report say so in full.

The through-line from Round 1 to here is one habit: **the number is not the
deliverable — the number plus what it is worth, plus what would make it stop
being true, is the deliverable.**
