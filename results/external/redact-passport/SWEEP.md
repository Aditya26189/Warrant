# FPR budget sweep — REDACT locked split (ServiceNow) · 2.2.364

Re-analysis of frozen scores in `results/scores/external-redact-passport.json`. No inference was run: every number is a function of the committed labels, scores and question ids.

- commit `9164879ea02a` · dirty `False` · config `533fb74983fcd8af`
- detector `presidio-analyzer` · envelope `revision:pii_benchmark_sa`
- certification: Clopper-Pearson one-sided upper bound at alpha 0.050, via `certify_fpr`
- intervals: percentile bootstrap, 1000 resamples over questions, seed 1729
- thresholds certified and metrics measured on the same set, `external-redact-passport` — **in sample**
- n 1000 (94 positive, 906 negative) · base rate 0.0940

## Verdict

Lift holds at 20 of 20 swept targets, the loosest being a target FPR of 0.20, where the certified threshold achieves FPR 0.0375 and lift 4.508 [3.026, 6.067] — 42% of the 10.64 ceiling. Recall there is 0.2660 [0.1786, 0.3579], against 0.0000 at the shipped operating point. Recall 0.0000 is a dial, not a ceiling: loosening the false-positive budget lifts recall clear of the shipped point's own 95% interval, so the number the product ships is a policy choice and the honest form of the claim is a curve rather than a point.

## The pre-registered criterion

Lift *holds* at a target FPR when the **lower bound** of its 95% bootstrap interval is strictly greater than 1.0. Registered before any output was seen (Phase 0 brief, D6) and not adjusted afterwards.

## Grid

| target FPR | threshold | achieved FPR | recall | precision | flag rate | lift | lift CI low > 1 | % of ceiling |
|---:|---:|---:|---|---|---|---|:--:|---:|
| 0.01 | 0.100000 | 0.0033 | 0.0851 [0.0364, 0.1429] (95% CI, n=1000) | 0.7273 [0.4286, 1.0000] (95% CI, n=1000) | 0.0110 [0.0050, 0.0170] (95% CI, n=1000) | 7.737 [3.305, 12.987] (95% CI, n=1000) | yes | 73% |
| 0.02 | 0.050000 | 0.0044 | 0.1596 [0.0909, 0.2359] (95% CI, n=1000) | 0.7895 [0.5908, 0.9585] (95% CI, n=1000) | 0.0190 [0.0110, 0.0280] (95% CI, n=1000) | 8.399 [4.785, 12.414] (95% CI, n=1000) | yes | 79% |
| 0.03 | 0.050000 | 0.0044 | 0.1596 [0.0909, 0.2359] (95% CI, n=1000) | 0.7895 [0.5908, 0.9585] (95% CI, n=1000) | 0.0190 [0.0110, 0.0280] (95% CI, n=1000) | 8.399 [4.785, 12.414] (95% CI, n=1000) | yes | 79% |
| 0.04 | 0.050000 | 0.0044 | 0.1596 [0.0909, 0.2359] (95% CI, n=1000) | 0.7895 [0.5908, 0.9585] (95% CI, n=1000) | 0.0190 [0.0110, 0.0280] (95% CI, n=1000) | 8.399 [4.785, 12.414] (95% CI, n=1000) | yes | 79% |
| 0.05 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.06 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.07 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.08 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.09 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.10 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.11 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.12 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.13 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.14 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.15 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.16 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.17 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.18 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.19 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |
| 0.20 | 0.000000 | 0.0375 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.4237 [0.3061, 0.5539] (95% CI, n=1000) | 0.0590 [0.0450, 0.0740] (95% CI, n=1000) | 4.508 [3.026, 6.067] (95% CI, n=1000) | yes | 42% |

## The frontier: what recall costs

Everything flagged routes to the expensive check, so the flag rate is the bill. Costed against the flag-rate budgets `config.yaml` actually declares:

| profile | declared flag-rate budget |
|---|---:|
| `customer_support` | 0.10 |
| `internal_knowledge` | 0.20 |
| `decision_support` | 0.50 |

> **These are envelope figures, not production costs.** Flag rate is measured at base rate 0.0940. Production traffic is nowhere near that, and the same threshold would flag a different share of it. Quoting a judge-call figure from here as a production cost puts a flag rate from one workload beside a base rate from another — the scenario-mixing error `CLAUDE.md` names. `DECISIONS.md` 132.

| target FPR | recall | flag rate | judge calls / 1000 | lift | profiles within budget |
|---:|---|---:|---:|---:|---|
| 0.01 | 0.0851 [0.0364, 0.1429] (95% CI, n=1000) | 0.0110 | 11 | 7.737 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.02 | 0.1596 [0.0909, 0.2359] (95% CI, n=1000) | 0.0190 | 19 | 8.399 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.03 | 0.1596 [0.0909, 0.2359] (95% CI, n=1000) | 0.0190 | 19 | 8.399 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.04 | 0.1596 [0.0909, 0.2359] (95% CI, n=1000) | 0.0190 | 19 | 8.399 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.05 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.06 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.07 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.08 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.09 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.10 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.11 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.12 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.13 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.14 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.15 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.16 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.17 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.18 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.19 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.20 | 0.2660 [0.1786, 0.3579] (95% CI, n=1000) | 0.0590 | 59 | 4.508 | `customer_support`, `decision_support`, `internal_knowledge` |

### The two ends of the trade

**Most recall available** — target 0.05: recall 0.2660, costing 59 judge calls per 1000 requests (5.9% of this envelope). Within budget for: `customer_support`, `decision_support`, `internal_knowledge`.

**Best lift per flagged item** — target 0.02: lift 8.399 (79% of ceiling) at recall 0.1596, costing 19 calls per 1000. Within budget for: `customer_support`, `decision_support`, `internal_knowledge`.

The operating point is a business choice between the two, and this table is the whole of what the measurement can say about it. Which profile a point can actually serve is decided by the policy layer, which conjoins a recall floor and an FPR ceiling to the flag-rate budget; fitting the budget is necessary and not sufficient.

## The shipped operating point, for reference

- `None` at threshold 0.500000
- recall 0.0000 [0.0000, 0.0385] (95% CI, n=1000)
- precision 0.0000 [0.0000, 1.0000] (95% CI, n=1000)
- flag rate 0.0000 [0.0000, 0.0037] (95% CI, n=1000)
- lift n/a

## What this sweep does not establish

The threshold at each grid point is certified on the **same** frozen test split the recall is then measured on. The pipeline's discipline is stricter — selection on validation, test scored once — and only test-split scores are frozen, so that discipline could not be applied here without refitting the probe. `certify_fpr` reads the negatives only, so the positives that determine recall play no part in choosing the threshold; the bias is that the threshold tracks this sample's negative tail rather than the population's. Each recall above is therefore an in-sample figure and is not a warrant.

