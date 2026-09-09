# FPR budget sweep — REDACT locked split (ServiceNow) · 2.2.364

Re-analysis of frozen scores in `results/scores/external-redact-high-tier.json`. No inference was run: every number is a function of the committed labels, scores and question ids.

- commit `9164879ea02a` · dirty `False` · config `533fb74983fcd8af`
- detector `presidio-analyzer` · envelope `revision:pii_benchmark_sa`
- certification: Clopper-Pearson one-sided upper bound at alpha 0.050, via `certify_fpr`
- intervals: percentile bootstrap, 1000 resamples over questions, seed 1729
- thresholds certified and metrics measured on the same set, `external-redact-high-tier` — **in sample**
- n 1000 (474 positive, 526 negative) · base rate 0.4740

## Verdict

Lift does not hold at any target FPR on the swept grid (0.01 to 0.20): at every point the lower bound of lift's 95% interval falls at or below 1.0, so no budget on this grid buys a detector that beats flagging at random. Recall 0.8608 at the shipped operating point is therefore not a policy choice being held down by the false-positive budget — loosening the budget does not produce a warrantable detector on this envelope. The probe is weak on REDACT locked split (ServiceNow), the FPR budget is not what is binding, and the product is the refusal machinery rather than the detector.

## The pre-registered criterion

Lift *holds* at a target FPR when the **lower bound** of its 95% bootstrap interval is strictly greater than 1.0. Registered before any output was seen (Phase 0 brief, D6) and not adjusted afterwards.

## Grid

| target FPR | threshold | achieved FPR | recall | precision | flag rate | lift | lift CI low > 1 | % of ceiling |
|---:|---:|---:|---|---|---|---|:--:|---:|
| 0.01 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.02 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.03 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.04 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.05 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.06 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.07 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.08 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.09 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.10 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.11 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.12 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.13 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.14 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.15 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.16 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.17 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.18 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.19 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |
| 0.20 | 1.000000 | 0.0000 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 [0.0000, 1.0000] (95% CI, n=1000) | 0.0000 [0.0000, 0.0037] (95% CI, n=1000) | n/a | no | n/a |

## The frontier: what recall costs

Everything flagged routes to the expensive check, so the flag rate is the bill. Costed against the flag-rate budgets `config.yaml` actually declares:

| profile | declared flag-rate budget |
|---|---:|
| `customer_support` | 0.10 |
| `internal_knowledge` | 0.20 |
| `decision_support` | 0.50 |

> **These are envelope figures, not production costs.** Flag rate is measured at base rate 0.4740. Production traffic is nowhere near that, and the same threshold would flag a different share of it. Quoting a judge-call figure from here as a production cost puts a flag rate from one workload beside a base rate from another — the scenario-mixing error `CLAUDE.md` names. `DECISIONS.md` 132.

| target FPR | recall | flag rate | judge calls / 1000 | lift | profiles within budget |
|---:|---|---:|---:|---:|---|
| 0.01 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.02 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.03 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.04 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.05 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.06 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.07 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.08 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.09 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.10 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.11 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.12 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.13 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.14 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.15 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.16 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.17 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.18 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.19 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.20 | 0.0000 [0.0000, 0.0078] (95% CI, n=1000) | 0.0000 | 0 | nan | `customer_support`, `decision_support`, `internal_knowledge` |

### The two ends of the trade

No point on this grid clears the pre-registered bar, so there is no operating point to recommend at either end. The rows above describe the shape of the curve and nothing more.

## The shipped operating point, for reference

- `None` at threshold 0.500000
- recall 0.8608 [0.8270, 0.8906] (95% CI, n=1000)
- precision 0.5930 [0.5551, 0.6353] (95% CI, n=1000)
- flag rate 0.6880 [0.6570, 0.7170] (95% CI, n=1000)
- lift 1.251 [1.202, 1.294] (95% CI, n=1000)

## What this sweep does not establish

The threshold at each grid point is certified on the **same** frozen test split the recall is then measured on. The pipeline's discipline is stricter — selection on validation, test scored once — and only test-split scores are frozen, so that discipline could not be applied here without refitting the probe. `certify_fpr` reads the negatives only, so the positives that determine recall play no part in choosing the threshold; the bias is that the threshold tracks this sample's negative tail rather than the population's. Each recall above is therefore an in-sample figure and is not a warrant.

