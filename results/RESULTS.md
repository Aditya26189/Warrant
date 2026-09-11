# RESULTS

> [!WARNING]
> **8 of 17 populated cells are synthetic fixtures and their numbers are not printed below.**
>
> A fixture number is internally valid and is not evidence about a language model. The renderer refuses to print them rather than relying on a reader noticing a footnote. Cells affected:
>
> - `probe-T1-max_rolling_means` on `triviaqa-600-synthetic` — triviaqa-600-synthetic is a synthetic fixture; its numbers describe a generator we wrote, not a language model
> - `probe-T1-mean_pool` on `triviaqa-600-synthetic` — triviaqa-600-synthetic is a synthetic fixture; its numbers describe a generator we wrote, not a language model
> - `probe-T2-logprob` on `triviaqa-600-synthetic` — triviaqa-600-synthetic is a synthetic fixture; its numbers describe a generator we wrote, not a language model
> - `probe-T3-judge` on `triviaqa-600-synthetic` — triviaqa-600-synthetic is a synthetic fixture; its numbers describe a generator we wrote, not a language model
> - `probe-T1-max_rolling_means` on `triviaqa-longctx-600-synthetic` — triviaqa-longctx-600-synthetic is a synthetic fixture; its numbers describe a generator we wrote, not a language model
> - `probe-T1-mean_pool` on `triviaqa-longctx-600-synthetic` — triviaqa-longctx-600-synthetic is a synthetic fixture; its numbers describe a generator we wrote, not a language model
> - `probe-T2-logprob` on `triviaqa-longctx-600-synthetic` — triviaqa-longctx-600-synthetic is a synthetic fixture; its numbers describe a generator we wrote, not a language model
> - `probe-T3-judge` on `triviaqa-longctx-600-synthetic` — triviaqa-longctx-600-synthetic is a synthetic fixture; its numbers describe a generator we wrote, not a language model

## Warrant matrix

Cells on synthetic envelopes show their status but not their numbers.

| detector | triviaqa-600-synthetic | triviaqa-longctx-600-synthetic | hinglish-pii-200 | hinglish-pii-200-longctx | hard-negatives-200 | triviaqa-600 | triviaqa-longctx-600 |
|---|---|---|---|---|---|---|---|
| pii-reference | UNVALIDATED | UNVALIDATED | VALID R=0.79 [0.70, 0.88] @f=0.620 | VALID R=0.79 [0.70, 0.88] @f=0.620 | VALID FPR=0.000 [0.000, 0.015] | UNVALIDATED | UNVALIDATED |
| probe-T1-max_rolling_means | VALID · FIXTURE — NOT MEASURED | VALID · FIXTURE — NOT MEASURED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED |
| probe-T1-mean_pool | VALID · FIXTURE — NOT MEASURED | REFUSED · FIXTURE — NOT MEASURED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED |
| probe-T2-logprob | VALID · FIXTURE — NOT MEASURED | VALID · FIXTURE — NOT MEASURED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED |
| probe-T3-judge | VALID · FIXTURE — NOT MEASURED | REFUSED · FIXTURE — NOT MEASURED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED |
| probe-qwen2.5-7b-instruct-T1-last_token | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | VALID R=0.08 [0.05, 0.11] @f=0.042 · CAL:unresolved (±25%) | VALID R=0.13 [0.09, 0.17] @f=0.065 · CAL:unresolved (±25%) |
| probe-qwen2.5-7b-instruct-T1-max_rolling_means | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | VALID R=0.08 [0.05, 0.12] @f=0.042 · CAL:unresolved (±25%) | **REFUSED** |
| probe-qwen2.5-7b-instruct-T1-mean_pool | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | VALID R=0.08 [0.05, 0.11] @f=0.040 · CAL:unresolved (±25%) | **REFUSED** |

Cell states: VALID 13, REFUSED 4, UNVALIDATED 39. 39 of 56 cells have never been measured, which is the expected shape: UNVALIDATED is the modal state in production.

## Measured results

| detector | envelope | status | AUROC | recall | precision | flag rate | base rate | lift | n |
|---|---|---|---|---|---|---|---|---|---|
| `pii-reference` | `hinglish-pii-200` | VALID | 0.773 [0.690, 0.856] (95% CI, n=200) | 0.794 [0.698, 0.885] (95% CI, n=200) | 0.653 [0.511, 0.810] (95% CI, n=200) | 0.6200 [0.5143, 0.7350] (95% CI, n=200) | 0.5100 | 1.281 [1.126, 1.427] (95% CI, n=200) — 79% of the 1.61 ceiling at base rate 0.510 | 200 |
| `pii-reference` | `hinglish-pii-200-longctx` | VALID | 0.773 [0.690, 0.856] (95% CI, n=200) | 0.794 [0.698, 0.885] (95% CI, n=200) | 0.653 [0.511, 0.810] (95% CI, n=200) | 0.6200 [0.5143, 0.7350] (95% CI, n=200) | 0.5100 | 1.281 [1.126, 1.427] (95% CI, n=200) — 79% of the 1.61 ceiling at base rate 0.510 | 200 |
| `pii-reference` | `hard-negatives-200` | VALID | n/a | n/a | n/a | 0.0000 [0.0000, 0.0183] (95% CI, n=200) | 0.0000 | n/a | 200 |
| `probe-qwen2.5-7b-instruct-T1-last_token` | `triviaqa-600` | VALID | 0.826 [0.793, 0.857] (95% CI, n=600) | 0.079 [0.050, 0.112] (95% CI, n=600) | 0.880 [0.750, 1.000] (95% CI, n=600) | 0.0417 [0.0267, 0.0583] (95% CI, n=600) | 0.4617 | 1.906 [1.190, 2.676] (95% CI, n=600) — 88% of the 2.17 ceiling at base rate 0.462 | 600 |
| `probe-qwen2.5-7b-instruct-T1-max_rolling_means` | `triviaqa-600` | VALID | 0.785 [0.750, 0.821] (95% CI, n=600) | 0.083 [0.054, 0.117] (95% CI, n=600) | 0.920 [0.800, 1.000] (95% CI, n=600) | 0.0417 [0.0283, 0.0583] (95% CI, n=600) | 0.4617 | 1.993 [1.286, 2.819] (95% CI, n=600) — 92% of the 2.17 ceiling at base rate 0.462 | 600 |
| `probe-qwen2.5-7b-instruct-T1-mean_pool` | `triviaqa-600` | VALID | 0.785 [0.750, 0.821] (95% CI, n=600) | 0.079 [0.050, 0.113] (95% CI, n=600) | 0.917 [0.786, 1.000] (95% CI, n=600) | 0.0400 [0.0250, 0.0567] (95% CI, n=600) | 0.4617 | 1.986 [1.254, 2.835] (95% CI, n=600) — 92% of the 2.17 ceiling at base rate 0.462 | 600 |
| `probe-qwen2.5-7b-instruct-T1-last_token` | `triviaqa-longctx-600` | VALID | 0.813 [0.780, 0.845] (95% CI, n=600) | 0.126 [0.090, 0.170] (95% CI, n=600) | 0.897 [0.794, 0.978] (95% CI, n=600) | 0.0650 [0.0483, 0.0850] (95% CI, n=600) | 0.4617 | 1.944 [1.388, 2.613] (95% CI, n=600) — 90% of the 2.17 ceiling at base rate 0.462 | 600 |
| `probe-qwen2.5-7b-instruct-T1-max_rolling_means` | `triviaqa-longctx-600` | REFUSED | 0.555 [0.511, 0.602] (95% CI, n=600) | 0.585 [0.527, 0.642] (95% CI, n=600) | 0.497 [0.447, 0.550] (95% CI, n=600) | 0.5433 [0.5050, 0.5833] (95% CI, n=600) | 0.4617 | 1.076 [0.969, 1.182] (95% CI, n=600) — 58% of the 1.84 ceiling at base rate 0.462 | 600 |
| `probe-qwen2.5-7b-instruct-T1-mean_pool` | `triviaqa-longctx-600` | REFUSED | 0.502 [0.455, 0.548] (95% CI, n=600) | 0.000 [0.000, 0.013] (95% CI, n=600) | 0.000 [0.000, 1.000] (95% CI, n=600) | 0.0000 [0.0000, 0.0061] (95% CI, n=600) | 0.4617 | n/a | 600 |

## Detection sensitivity — a declared limitation

**Calibration drift is detectable at a 25% deviation from the declared flag-rate budget, and is not detectable at 10%, on the evidence here.**

Separating a 25% deviation from the budget needs **n >= 1441**. These envelopes were measured at **n = 600**. So every budget claim below is either refused outright or unresolved -- the interval extends past the band, and this sample could not have narrowed it.

This is a limitation of sample size, not of the method: the ranking claims on the same warrants are supported, because AUROC intervals at this n are tight enough to separate the detectors from each other. Closing it needs more test items, not more code.

| detector | envelope | calibration | unresolved | power |
|---|---|---|---|---|
| `pii-reference` | `hinglish-pii-200` | UNKNOWN | no | n/a |
| `pii-reference` | `hinglish-pii-200-longctx` | UNKNOWN | no | n/a |
| `pii-reference` | `hard-negatives-200` | UNKNOWN | no | n/a |
| `probe-qwen2.5-7b-instruct-T1-last_token` | `triviaqa-600` | CALIBRATED | yes | n=600, needs n>=1441 |
| `probe-qwen2.5-7b-instruct-T1-max_rolling_means` | `triviaqa-600` | CALIBRATED | yes | n=600, needs n>=1441 |
| `probe-qwen2.5-7b-instruct-T1-mean_pool` | `triviaqa-600` | CALIBRATED | yes | n=600, needs n>=1441 |
| `probe-qwen2.5-7b-instruct-T1-last_token` | `triviaqa-longctx-600` | CALIBRATED | yes | n=600, needs n>=1441 |
| `probe-qwen2.5-7b-instruct-T1-max_rolling_means` | `triviaqa-longctx-600` | DRIFTED | no | n=600, needs n>=1441 |
| `probe-qwen2.5-7b-instruct-T1-mean_pool` | `triviaqa-longctx-600` | DRIFTED | no | n=600, needs n>=1441 |

## The price list — what it costs to keep a warrant true

What a recall claim on **your traffic** costs, from the one declared workload `enterprise-3pct` (N=200,000, base error rate 0.03). Every figure is computed by `controlplane/sampling`; none is typed.

Recall is not measured. It is computed from a measured prevalence, so the margin travels through the derivative:

```
R      = TP / (TP + q*N_u)
dR/dq  = -4.650   (TP=850, N_u=197,016, q=0.02614)
m_q    = m_R / |dR/dq|
n      = z^2 q(1-q) / m_q^2
```

| operating point | margin | month one | steady state | superseded |
|---|---|---|---|---|
| declared workload point | ±0.05 | **1,014** | 804 | 187 |
| declared workload point | ±0.02 | **5,566** | 4,413 | 1,168 |
| customer_support @ P-customer-support | ±0.05 | **1,808** | 1,434 | 262 |
| customer_support @ P-customer-support | ±0.02 | **10,636** | 8,434 | 1,633 |
| decision_support @ P-decision-support | ±0.05 | **4,049** | 3,211 | 299 |
| decision_support @ P-decision-support | ±0.02 | **24,591** | 19,499 | 1,863 |
| internal_knowledge @ P-internal-knowledge | ±0.05 | **3,582** | 2,840 | 355 |
| internal_knowledge @ P-internal-knowledge | ±0.02 | **21,598** | 17,125 | 2,214 |

**Month one costs more, and it is not a discount anyone can take early.** Neyman allocation needs the per-band prevalences the first month's labels are bought to discover, so month one runs proportional at full simple-random-sampling cost. **superseded** is what this repository quoted before `DECISIONS.md` 147, and it was low by 6x to 13x.

**Yield is exact; rate is estimated.** The flagged stratum is reviewed in full, so the confirmed-error count and precision carry no interval and cost nothing. Recall needs the whole sampling apparatus. The two are not views of one measurement — they are a free claim and an expensive one.

Interval coverage on synthetic traffic with known ground truth: **96.8%** over 1,000 trials against a nominal 95%. Above nominal, because Clopper-Pearson is conservative and the published interval carries no finite-population correction. Over-covering claims less than the evidence supports.

## Inter-rater agreement, and the blinded queue

Every interval this project publishes is a statement about **sampling** error and nothing else. It answers *how much would this number move on a different sample?* It is silent on *how much would it move if a different person reviewed the same sample?* — and at κ = 0.5 the second question has the larger answer. So κ is reported beside the warrant and a low value **widens the recall interval** rather than sitting in a footnote.

- κ = **0.6522** [0.4976, 0.7899] (95% percentile bootstrap over pairs, n=100)
- raw agreement 0.8300, chance agreement 0.5112 — reported together because κ is routinely mistaken for the first of them

> **This κ demonstrates the mechanism and measures no reviewer.** There are no doubly-labelled items in this repository. What is shown is that a low κ widens the interval and records why on the metric, so a widened interval can never be mistaken for a measured one.

**The queue is blinded** (`CLAUDE.md` invariant 7). A reviewer who can see that an item was flagged confirms it more often, and one who can see it was not confirms less often; both push recall up. The payload carries only `content`, `question`, `queue_id` — flag status, score, stratum and ordering are withheld by construction rather than by convention, and the double-labelled items are split across both strata ({'flagged': 4, 'unflagged': 36}) because agreement measured on one stratum says nothing about the other.

## Certifying a detector that emits no score

A warrant is a statement about a threshold, and the detector family that wins on REDACT — GPT-4.1, Claude Sonnet — emits no score to threshold. Repeated sampling fixes that: run the judge `k` times and score each item by the fraction of runs that flagged it.

**A single-sample judge cannot be certified to a tight false-positive budget however much data you have.** At `k = 1` the tightest budget any useful threshold reaches is **0.105** — which is nothing but the judge's own error rate. One bit gives one cut point, so there is no dial to turn.

| negatives | data floor | k=1 | k=2 | k=3 | k=5 | k=9 |
|---|---|---|---|---|---|---|
| 200 | 0.01487 | **0.13628** | **0.03831** | **0.01918** | 0.01487 | 0.01487 |
| 1,000 | 0.00299 | **0.11058** | **0.02180** | **0.00913** | 0.00299 | 0.00299 |
| 5,000 | 0.00060 | **0.09848** | **0.01684** | **0.00462** | **0.00095** | 0.00060 |
| 20,000 | 0.00015 | **0.09424** | **0.01516** | **0.00364** | **0.00046** | 0.00015 |

**Bold** means granularity is what binds; plain means the benchmark's own certification capacity does. The crossover between them is `k = 3` at 200 negatives and `k = 7` at 20,000. **Past it, more samples are inference spend fixing a data problem.**

`k` is part of the operating point. Certified at `k = 9` with an upper bound of 0.0336, the same vote-fraction threshold at `k = 1` realises 0.0790 — 2.4× the bound. The warrant is void, which is why `k` enters the warrant key.

> **The judge is simulated**, with independent Bernoulli draws. A real judge's runs share a prompt and a temperature and are correlated, which makes the vote fraction a worse estimate, pushes the crossover up, and makes every figure here an **upper bound** on what `k` buys. It certifies no real detector.

## Provenance

- config hash `533fb74983fcd8af`
- git commit `840e9d93e2531401a3914e6595a5e92ce87ea700`
- dirty tree: `False`
- seed `1729`
- generated `2026-09-11T19:33:00+00:00`
