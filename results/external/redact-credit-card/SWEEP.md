# FPR budget sweep — REDACT locked split (ServiceNow) · 2.2.364

Re-analysis of frozen scores in `results/scores/external-redact-credit-card.json`. No inference was run: every number is a function of the committed labels, scores and question ids.

- commit `9164879ea02a` · dirty `False` · config `533fb74983fcd8af`
- detector `presidio-analyzer` · envelope `revision:pii_benchmark_sa`
- certification: Clopper-Pearson one-sided upper bound at alpha 0.050, via `certify_fpr`
- intervals: percentile bootstrap, 1000 resamples over questions, seed 1729
- thresholds certified and metrics measured on the same set, `external-redact-credit-card` — **in sample**
- n 1000 (107 positive, 893 negative) · base rate 0.1070

## Verdict

Lift holds at 19 of 20 swept targets, the loosest being a target FPR of 0.20, where the certified threshold achieves FPR 0.0067 and lift 5.841 [2.451, 9.347] — 62% of the 9.35 ceiling. Recall there is 0.0935 [0.0392, 0.1495], against 0.0935 at the shipped operating point. Recall 0.0935 is a ceiling rather than a dial: even at the loosest budget where lift still holds, recall does not clear the upper bound of the shipped point's own 95% interval, so loosening the budget buys nothing this sample can distinguish from where the product already sits.

## The pre-registered criterion

Lift *holds* at a target FPR when the **lower bound** of its 95% bootstrap interval is strictly greater than 1.0. Registered before any output was seen (Phase 0 brief, D6) and not adjusted afterwards.

## Grid

| target FPR | threshold | achieved FPR | recall | precision | flag rate | lift | lift CI low > 1 | % of ceiling |
|---:|---:|---:|---|---|---|---|:--:|---:|
| 0.01 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0339] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.02 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.03 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.04 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.05 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.06 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.07 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.08 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.09 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.10 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.11 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.12 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.13 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.14 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.15 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.16 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.17 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.18 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.19 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |
| 0.20 | 0.000000 | 0.0067 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.6250 [0.3529, 0.8571] (95% CI, n=1000) | 0.0160 [0.0090, 0.0240] (95% CI, n=1000) | 5.841 [2.451, 9.347] (95% CI, n=1000) | yes | 62% |

## The frontier: what recall costs

Everything flagged routes to the expensive check, so the flag rate is the bill. Costed against the flag-rate budgets `config.yaml` actually declares:

| profile | declared flag-rate budget |
|---|---:|
| `customer_support` | 0.10 |
| `internal_knowledge` | 0.20 |
| `decision_support` | 0.50 |

> **These are envelope figures, not production costs.** Flag rate is measured at base rate 0.1070. Production traffic is nowhere near that, and the same threshold would flag a different share of it. Quoting a judge-call figure from here as a production cost puts a flag rate from one workload beside a base rate from another — the scenario-mixing error `CLAUDE.md` names. `DECISIONS.md` 132.

| target FPR | recall | flag rate | judge calls / 1000 | lift | profiles within budget |
|---:|---|---:|---:|---:|---|
| 0.01 | 0.0000 [0.0000, 0.0339] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.02 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.03 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.04 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.05 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.06 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.07 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.08 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.09 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.10 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.11 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.12 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.13 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.14 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.15 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.16 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.17 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.18 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.19 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.20 | 0.0935 [0.0392, 0.1495] (95% CI, n=1000) | 0.0160 | 16 | 5.841 | `customer_support`, `decision_support`, `internal_knowledge` |

### The two ends of the trade

**Most recall available** — target 0.02: recall 0.0935, costing 16 judge calls per 1000 requests (1.6% of this envelope). Within budget for: `customer_support`, `decision_support`, `internal_knowledge`.

**Best lift per flagged item** — target 0.02: lift 5.841 (62% of ceiling) at recall 0.0935, costing 16 calls per 1000. Within budget for: `customer_support`, `decision_support`, `internal_knowledge`.

The operating point is a business choice between the two, and this table is the whole of what the measurement can say about it. Which profile a point can actually serve is decided by the policy layer, which conjoins a recall floor and an FPR ceiling to the flag-rate budget; fitting the budget is necessary and not sufficient.

## The shipped operating point, for reference

- `None` at threshold 0.500000
- recall 0.0935 [0.0392, 0.1495] (95% CI, n=1000)
- precision 0.6250 [0.3529, 0.8571] (95% CI, n=1000)
- flag rate 0.0160 [0.0090, 0.0240] (95% CI, n=1000)
- lift 5.841 [2.451, 9.347] (95% CI, n=1000)

## What this sweep does not establish

The threshold at each grid point is certified on the **same** frozen test split the recall is then measured on. The pipeline's discipline is stricter — selection on validation, test scored once — and only test-split scores are frozen, so that discipline could not be applied here without refitting the probe. `certify_fpr` reads the negatives only, so the positives that determine recall play no part in choosing the threshold; the bias is that the threshold tracks this sample's negative tail rather than the population's. Each recall above is therefore an in-sample figure and is not a warrant.

