# Phase 4 — the on-traffic warrant, and the sizing that had been wrong for four phases

**The question: does the first of this project's three clauses exist?**

**Answer: it did not, and the number it had been quoting in its place was low by
6× to 13×.** `CLAUDE.md` opens its silent-failure list with *"sizing prevalence
and calling it recall"*; `SPEC.md` §6.2 calls it *"the error the spec exists to
prevent"*; `docs/CONTRIBUTING.md` uses a fix for it as its worked example of a
good commit message. `controlplane/economics/review.py` had been committing it
since Phase 3, and no control in this repository could see it, because every
control checks whether a number is reproducible from its artifact and that one
was reproducible to the last digit.

This phase builds `controlplane/sampling/` — the package four contract documents
specify and none of which had been written — and reports four further defects
found on the way, two of them in work done earlier this session.

- **Window:** 2026-09-11
- **Range:** `46bb4a8` → `HEAD`
- **Suite:** 1,130 at open → 1,168 at close, no failures at either end
- **Artifacts:** [`results/on_traffic/`](../results/on_traffic/)
- **Verification:** `verify.py` 40/40 claims at open → **49/49** at close; frozen scores and the activations tier both OK
- **Decisions:** `DECISIONS.md` 147–151
- **Method:** CPU only. No GPU, no paid API, no network except primary-source
  verification.

---

## 1. What was done

| # | task | outcome |
|---|---|---|
| T1 | Verify every external factual claim in the outward-facing documents against a primary source | **7 of 7 confirmed.** No corrections needed. §2 |
| T2 | Audit the shipped label sizing against the contract it is supposed to implement | **Defect found**, 6×–13×. §3 |
| T3 | Build `controlplane/sampling/` — planning, estimator, allocation, blinded queue, κ | Built. 26 tests, five of them the gate registered in advance. §4 |
| T4 | Produce the price list as an artifact | [`results/on_traffic/ON_TRAFFIC.md`](../results/on_traffic/ON_TRAFFIC.md) |
| T5 | Report defects found during the build, including in this phase's own work | Four. §5 |

---

## 2. The external claims, checked

`reports/STRATEGY-2026-09.md` rests its entire regulatory and competitive
picture on seven external claims, all made after this session's knowledge
cutoff. Every one was re-fetched from its primary source.

| claim | source | verdict |
|---|---|---|
| REDACT: 13,427 records, 324,078 annotations, 51 entity types, 4,127 patterns, 25 languages, 9 scripts, 18 June 2026 | [arXiv 2606.19881](https://arxiv.org/abs/2606.19881) | **confirmed, every figure** |
| REDACT reports Presidio at recall 0.07 on HIGH-sensitivity entities | same | **confirmed** |
| PIIBench: 10 datasets, 2,369,883 sequences, 48 entity types, 8 comparator systems, April 2026 | [arXiv 2604.15776](https://arxiv.org/abs/2604.15776) | **confirmed** |
| SR 26-2 / OCC 2026-13: *"Generative AI and agentic AI models are novel and rapidly evolving. As such, they are not within the scope of this guidance"* | [OCC Bulletin 2026-13](https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html) | **confirmed verbatim**, 17 April 2026, over \$30bn in assets, RFI planned |
| EU AI Act high-risk deferred to 2 December 2027 by Regulation (EU) 2026/1744 | Official Journal, in force 27 July 2026 | **confirmed**, Annex I products to August 2028 |
| India DPDP: notified 13 Nov 2025, consent managers 13 Nov 2026, substantive obligations 13 May 2027 | MeitY | **confirmed** |
| ACL 2026 conformal routing uses the same Clopper-Pearson machinery and never abstains | [2026.acl-srw.70](https://aclanthology.org/2026.acl-srw.70/) | **confirmed** — *Conformal LLM Routing with Distribution-Free Safety Guarantees*, Uddin and Bauer |

**Nothing needed correcting.** That is worth stating plainly, because the
audit of 2026-09-09 found three confidently wrong external claims and the prior
here was that more would surface. The strategy document's rule — *a convenient
claim needs a primary source, and a convenient absence needs a positive search
for the thing that would refute it* — appears to have held.

One detail the documents do not record and should: **SR 26-2 replaces SR 11-7**,
the first revision in fifteen years, issued jointly by the Federal Reserve, OCC
and FDIC.

---

## 3. The defect

`economics/review.py::recall_sample_size` returned

    n = z^2 * R * (1 - R) / m^2 * design_effect

labelled `unit="reviewed items"` and named *"reviewed items for recall ± m"*.

That is a binomial sizing for recall estimated by drawing `n` items **from the
population of true errors**. Nobody can run that design: the error population is
not enumerable without the labels the sample exists to buy. It is the one
sampling design that makes the formula correct and the only one unavailable.

**What the shipped design actually is.** Stratum A (flagged) is reviewed in
full, so `TP` is an exact count. Stratum B (unflagged) is sampled, and what the
sample estimates is `q`. Recall is a *function* of that estimate, so the margin
has to travel through the derivative:

    R      = TP / (TP + q*N_u)
    dR/dq  = -TP*N_u / (TP + q*N_u)^2  =  -4.650  at the declared workload
    m_q    = m_R / |dR/dq|
    n      = z^2 q(1-q) / m_q^2

**Measured**, both columns at the same declared design effect of 0.67, from
`results/feasibility.json` as it stands:

| profile | m_R | shipped | correct | factor |
|---|---|---|---|---|
| customer_support | 0.05 | 175 | 1,096 | **6.3×** |
| customer_support | 0.02 | 1,094 | 6,632 | **6.1×** |
| internal_knowledge | 0.05 | 238 | 2,233 | **9.4×** |
| internal_knowledge | 0.02 | 1,483 | 13,016 | **8.8×** |
| decision_support | 0.05 | 200 | 2,511 | **12.6×** |
| decision_support | 0.02 | 1,249 | 13,964 | **11.2×** |

**No outward-facing number was wrong**, which is checkable rather than asserted:
`recall_sample_size` appears in no row of the README claim table and no line of
`results/RESULTS.md`. It reached `results/feasibility.json` and the log of
`scripts/11_feasibility.py`. The damage was to whoever budgeted from it first.

**How it survived four phases.** Three tests covered it and all three tested the
formula against itself — that sizing at the measured recall beats sizing at 0.5,
that a finer margin costs more, that a zero margin raises. None asked what
quantity the number was in. `DECISIONS.md` 147.

---

## 4. What was built

`controlplane/sampling/`, 2,005 lines across five modules, and the asymmetry
that makes the project's central distinction structural rather than a convention
anybody has to remember:

| stratum | reviewed | cost | yields |
|---|---|---|---|
| A — flagged | in full | free | `TP` and precision, **EXACT** |
| B — unflagged | sampled | labels | `q`, and so recall, **ESTIMATED** |

Precision over a census carries no interval and needs no labels; recall over a
sampled pool carries one and costs them. That is why `CLAUDE.md` insists the two
travel together: they are a free claim and an expensive one, not two views of
one measurement.

**The interval is propagated by exact monotone transformation, not the delta
method.** `R` is strictly decreasing in `q`, so `[g(q_hi), g(q_lo)]` covers `R`
with exactly the coverage `[q_lo, q_hi]` has for `q`. The delta method degrades
precisely where this project operates — small event counts in a large pool — and
can put a recall bound above 1, which the transformation cannot.

### The gate, registered before the code was written

| check | result |
|---|---|
| `test_sizing_derivative` — recall sizing differs from prevalence sizing by exactly `(dR/dq)^2` | **pass**, to `rel=1e-3` |
| `test_sizing_units` — no sample size without a declared estimand | **pass** |
| `test_stratified_unbiased` — nominal coverage over 1,000 trials on known ground truth | **pass**, 96.8% against nominal 95% |
| `test_blinding` — payload carries no flag status, score, stratum or ordering signal | **pass**, by permutation test |
| `test_no_scenario_mixing` | **pass** |

`DECISIONS.md` 147 registered the coverage band as [0.93, 0.97] and said an
out-of-band result would be reported rather than retuned. **96.8% is inside the
band but above nominal**, and the reason is stated rather than tuned away:
Clopper-Pearson is conservative by construction, and the published interval
carries no finite-population correction, so it over-covers. An interval that
over-covers claims less than the evidence supports; one that under-covers claims
more than it can.

### The price list

From [`results/on_traffic/ON_TRAFFIC.md`](../results/on_traffic/ON_TRAFFIC.md),
at ±0.05 on recall:

| subject | month one (proportional, full SRS) | steady state (Neyman, measured deff) | superseded sizing |
|---|---|---|---|
| declared workload point | **1,014** | 804 | 187 |
| customer_support | **1,189** | 943 | 213 |
| internal_knowledge | **3,226** | 2,558 | 341 |
| decision_support | **4,046** | 3,208 | 301 |

**The tool refuses.** At ±0.001 on recall, no sample of the 197,016-item
unflagged pool reaches the margin, and `labels_for_recall` says so and names what
would have to change. The closed form returns 180,223 for that margin — a number
for a margin no sample achieves, which is what makes the refusal worth having.

---

## 5. Four more defects, three of them in this session's own work

**An unfavourable result is reported as plainly as a favourable one.** Three of
these four were mistakes made during this phase.

### 5.1 The correction notice nearly shipped with a wrong table

The first draft of `DECISIONS.md` 147 stated the understatement as 9.4× to
19.2×. It is 6.1× to 12.6×. The corrected column had been computed without the
declared design effect and the shipped column with it — a factor of 1.49 applied
to one side of a ratio and not the other. **That is the same class of error as
the defect the entry corrects**, one level up: two quantities compared without
checking they were in the same units. It was caught by recomputing through the
module instead of in a scratch script, and it is recorded inside 147 rather than
quietly fixed.

### 5.2 The `232×` in `CLAUDE.md` and `SPEC.md` names the wrong ratio

| ratio | value |
|---|---|
| `N_u / N_flagged` — *"the unflagged pool is ~232× the flagged one"* | **66.0** |
| `N_u / TP` | **231.9** |

The number is right and the noun is wrong. `R = TP/(TP + q*N_u)`, so a
perturbation `dq` moves the denominator by `dq*N_u`, and what decides whether
that matters is its size relative to `TP` — the other term in the same
denominator. The flagged pool never appears in the derivative; it holds the
false positives, which are exactly the items that do not enter `R`.

**A wrong label on a right number is worse here than a wrong number**, because a
wrong number is caught by the arithmetic check that the label evades. A reviewer
who checks the paragraph this project uses to demonstrate that it takes
propagation seriously finds 66 where the text says 232. Corrected in both
contracts; `DECISIONS.md` 148.

### 5.3 The month-one price was quoted at Neyman's discount

`config.yaml` carries `expected_design_effect: 0.67`. That is **Neyman's**
design effect, and `CLAUDE.md` lists using it early as a named silent failure:
*"Month one runs proportional allocation at full SRS cost."* The first version of
`scripts/25_on_traffic.py` applied 0.67 to the month-one plan and quoted **680**
labels for ±0.05 where the correct month-one figure is **1,014** — 49% larger,
in the one month with no prior estimate to notice it against.
`scripts/11_feasibility.py` still applies it, and `results/feasibility.json`
still records it.

The price list now quotes two regimes and never one, and the steady-state column
uses a design effect **measured** from a band structure (0.7929) rather than the
declared expectation — which is 18% worse than the expectation, in the direction
`SPEC.md` §6.3 warns about. `DECISIONS.md` 150.

### 5.4 `reports/PHASE-3.md` was destroyed and nothing noticed for twenty commits

    d696832  docs: Phase 3 report                        9,905 bytes
    49156b9  docs: where this should go next -- strategy      4 bytes

`git show 49156b9 --numstat` reads `1 207`. The commit was adding the strategy
document and never mentions the report; what survived was the single word `can`.
It passed more than twenty commits, a full `make verify`, and 1,130 tests,
because **nothing in `tests/` referenced `reports/` at all**.

Restored from `d696832`. `tests/test_reports.py` now guards it, ten tests.
`DECISIONS.md` 151.

**This is the audit of 2026-09-09 for a third time in a third place.** That audit
found the machinery checked arithmetic and not question design. §3 found it
checked arithmetic and not the estimand. This finds it checked artifacts and not
deliverables. The common shape: **a control exists wherever a number might be
wrong and nowhere else, and the failures that actually happen are not wrong
numbers.**

---

## 6. What this does not establish

- **No recall figure on real production traffic exists.** This repository has no
  traffic. The estimator is evidenced by a coverage simulation against known
  ground truth, which is evidence that the interval is sound and is not evidence
  that anybody's recall is anything.
- **The band structure in the artifact is declared, not measured.** A real one
  comes from the detector's score distribution on the operator's own traffic.
  What is measured is the design effect that *follows* from a band structure.
- **The κ figure demonstrates the mechanism, not any reviewer.** There are no
  double-labelled items in this repository. What is shown is that a low κ widens
  the recall interval and records why, not what any κ is.
- **The whole package is untested against an adversarial reviewer.** A reviewer
  who wants to bias the estimate can still do it; the queue defends against the
  unconscious version, which is the one that happens.
- **It does not make anybody want this.** The strategy document's central
  question is unchanged and unanswered by any amount of code: whether anyone is
  punished for a wrong claim. §7.
- **`results/feasibility.json` was not regenerated.** It is superseded rather
  than corrected, deliberately: the quantity it sizes is the wrong estimand under
  147 regardless of which design effect multiplies it, and regenerating it would
  produce a corrected-looking wrong number.

---

## 7. Open items

| # | item | what would close it |
|---|---|---|
| O-1 | **The twelve conversations.** Whether anyone is punished for a wrong AI control claim. Open since 2026-09-09 and still the only question that decides whether this is a business. | Eight to twelve interviews. The falsifier is registered in `reports/STRATEGY-2026-09.md` §5: fewer than three of twelve naming a specific consequence means refusal has no buyer. |
| O-2 | **The score-free gap.** Certification needs a score to threshold, and the detectors that win on REDACT — GPT-4.1, Claude — emit none. The method cannot certify the family that performs best. The largest genuine limitation in the method itself. | Repeated-sampling frequency, logprobs, or pass^k. |
| O-3 | **`DECISIONS.md` 145 — the Rego entrypoint aborts on Linux.** Open, in a read-only zone, `xfail` carrying the crash output. | The child's stderr naming the aborting library. |
| O-4 | **`scripts/11_feasibility.py` still publishes the superseded sizing at Neyman's design effect.** | Either point it at `sampling.planning` or withdraw the artifact. Not done here because it is a Phase 3 artifact and the supersession is recorded. |
| O-5 | **`gate/` is unbuilt** (TASKS Phase 9), and clause-three economics do not yet reach the README claim table. | Both are build work, neither is blocked. |
| O-6 | **`DECISIONS.md` 138**, open for four phases now. An item carried indefinitely is a decision made by default. | Close it or scope it out. |

---

## 8. Ledger

**Code added**

| file | lines |
|---|---|
| `controlplane/sampling/planning.py` | 703 |
| `controlplane/sampling/estimator.py` | 476 |
| `controlplane/sampling/allocation.py` | 278 |
| `controlplane/sampling/queue.py` | 249 |
| `controlplane/sampling/agreement.py` | 210 |
| `controlplane/sampling/__init__.py` | 89 |
| `tests/test_sampling.py` | 653 |
| `tests/test_reports.py` | 107 |
| `scripts/25_on_traffic.py` | 520 |

**Code changed** — `controlplane/economics/review.py` (superseded, unit
corrected, arithmetic unchanged), `controlplane/economics/sizing.py` and
`__init__.py` (stale pointers to the superseded function), `tests/test_claims.py`
(the count guard now reads the badge form as well as the prose form).

**Contracts corrected** — `CLAUDE.md`, `docs/SPEC.md`, `docs/CONTRIBUTING.md`:
the `232×` ratio.

**Restored** — `reports/PHASE-3.md`, from `d696832`.

**Artifacts** — `results/on_traffic/on_traffic.json`,
`results/on_traffic/ON_TRAFFIC.md`.

**Decisions** — 147 (the estimand defect), 148 (the ratio), 149 (the closed form
does not deliver its margin), 150 (Neyman's discount on day one), 151 (the
destroyed report and the guard).

**Reproduce**

```
python -m pytest tests/test_sampling.py tests/test_reports.py -q
python scripts/25_on_traffic.py --config config.yaml
python scripts/verify.py
```

---

## 9. What this changes

**The pitch can now be said in full.** *"We tell you what your error rate is on
your traffic, we tell you when that number stops being true, and we tell you what
it costs to keep it true"* had one clause with no implementation behind it and
one clause quoting a number that was low by an order of magnitude. Both are
closed.

**And the honest version of clause three is more expensive than the repository
had been saying.** Recall to ±5pp on the declared workload costs 1,014 reviewed
items in month one, not 187. At the profile this project's own README leads with
it is 4,046. That is a real number, it is larger than anybody wanted, and it is
the first one here that somebody could actually budget from.

**The thing worth carrying forward is not the package.** It is that three of the
five defects in this report were found by reading code against a contract rather
than by any test, and the fourth by noticing a file was the wrong size. Every
control in this repository asks *is this number right*. Nothing asks *is this
number the answer to the question it is labelled with* — and after
`DECISIONS.md` 142, 147 and 151, that is three separate incidents of the same
shape. The next control worth building is not another estimator.
