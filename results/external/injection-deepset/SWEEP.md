# FPR budget sweep — deepset/prompt-injections · 90c9989b1a342275

Re-analysis of frozen scores in `results/scores/external-injection-deepset.json`. No inference was run: every number is a function of the committed labels, scores and question ids.

- commit `438269284194` · dirty `False` · config `533fb74983fcd8af`
- detector `protectai/deberta-v3-base-prompt-injection-v2` · envelope `revision:4f61ecb038e9c3fb`
- certification: Clopper-Pearson one-sided upper bound at alpha 0.050, via `certify_fpr`
- intervals: percentile bootstrap, 1000 resamples over questions, seed 1729
- thresholds certified and metrics measured on the same set, `external-injection-deepset` — **in sample**
- n 546 (203 positive, 343 negative) · base rate 0.3718

## Verdict

Lift holds at 20 of 20 swept targets, the loosest being a target FPR of 0.20, where the certified threshold achieves FPR 0.1633 and lift 2.008 [1.865, 2.139] — 81% of the 2.47 ceiling. Recall there is 0.8128 [0.7550, 0.8660], against 0.4286 at the shipped operating point. Recall 0.4286 is a dial, not a ceiling: loosening the false-positive budget lifts recall clear of the shipped point's own 95% interval, so the number the product ships is a policy choice and the honest form of the claim is a curve rather than a point.

## The pre-registered criterion

Lift *holds* at a target FPR when the **lower bound** of its 95% bootstrap interval is strictly greater than 1.0. Registered before any output was seen (Phase 0 brief, D6) and not adjusted afterwards.

## Grid

| target FPR | threshold | achieved FPR | recall | precision | flag rate | lift | lift CI low > 1 | % of ceiling |
|---:|---:|---:|---|---|---|---|:--:|---:|
| 0.01 | 0.992833 | 0.0000 | 0.3498 [0.2828, 0.4109] (95% CI, n=546) | 1.0000 [0.9494, 1.0000] (95% CI, n=546) | 0.1300 [0.1026, 0.1557] (95% CI, n=546) | 2.690 [2.175, 3.160] (95% CI, n=546) | yes | 100% |
| 0.02 | 0.963441 | 0.0058 | 0.3990 [0.3317, 0.4676] (95% CI, n=546) | 0.9759 [0.9342, 1.0000] (95% CI, n=546) | 0.1520 [0.1209, 0.1813] (95% CI, n=546) | 2.625 [2.182, 3.076] (95% CI, n=546) | yes | 98% |
| 0.03 | 0.011199 | 0.0117 | 0.4877 [0.4147, 0.5598] (95% CI, n=546) | 0.9612 [0.9192, 0.9915] (95% CI, n=546) | 0.1886 [0.1538, 0.2216] (95% CI, n=546) | 2.585 [2.198, 2.968] (95% CI, n=546) | yes | 96% |
| 0.04 | 0.002558 | 0.0204 | 0.5369 [0.4673, 0.6117] (95% CI, n=546) | 0.9397 [0.8897, 0.9766] (95% CI, n=546) | 0.2125 [0.1758, 0.2491] (95% CI, n=546) | 2.527 [2.200, 2.879] (95% CI, n=546) | yes | 94% |
| 0.05 | 0.000290 | 0.0292 | 0.6158 [0.5467, 0.6827] (95% CI, n=546) | 0.9259 [0.8760, 0.9664] (95% CI, n=546) | 0.2473 [0.2088, 0.2839] (95% CI, n=546) | 2.490 [2.211, 2.761] (95% CI, n=546) | yes | 93% |
| 0.06 | 0.000062 | 0.0379 | 0.6798 [0.6168, 0.7400] (95% CI, n=546) | 0.9139 [0.8662, 0.9548] (95% CI, n=546) | 0.2766 [0.2381, 0.3168] (95% CI, n=546) | 2.458 [2.230, 2.676] (95% CI, n=546) | yes | 91% |
| 0.07 | 0.000033 | 0.0466 | 0.6897 [0.6265, 0.7500] (95% CI, n=546) | 0.8974 [0.8491, 0.9412] (95% CI, n=546) | 0.2857 [0.2473, 0.3260] (95% CI, n=546) | 2.414 [2.193, 2.625] (95% CI, n=546) | yes | 90% |
| 0.08 | 0.000026 | 0.0525 | 0.6946 [0.6316, 0.7550] (95% CI, n=546) | 0.8868 [0.8360, 0.9310] (95% CI, n=546) | 0.2912 [0.2509, 0.3315] (95% CI, n=546) | 2.385 [2.169, 2.593] (95% CI, n=546) | yes | 89% |
| 0.09 | 0.000018 | 0.0612 | 0.6995 [0.6372, 0.7626] (95% CI, n=546) | 0.8712 [0.8182, 0.9205] (95% CI, n=546) | 0.2985 [0.2601, 0.3370] (95% CI, n=546) | 2.343 [2.135, 2.554] (95% CI, n=546) | yes | 87% |
| 0.10 | 0.000010 | 0.0700 | 0.7291 [0.6700, 0.7889] (95% CI, n=546) | 0.8605 [0.8068, 0.9102] (95% CI, n=546) | 0.3150 [0.2765, 0.3553] (95% CI, n=546) | 2.314 [2.127, 2.504] (95% CI, n=546) | yes | 86% |
| 0.11 | 0.000007 | 0.0787 | 0.7438 [0.6822, 0.8030] (95% CI, n=546) | 0.8483 [0.7947, 0.8983] (95% CI, n=546) | 0.3260 [0.2857, 0.3645] (95% CI, n=546) | 2.282 [2.093, 2.463] (95% CI, n=546) | yes | 85% |
| 0.12 | 0.000005 | 0.0875 | 0.7586 [0.6990, 0.8165] (95% CI, n=546) | 0.8370 [0.7833, 0.8870] (95% CI, n=546) | 0.3370 [0.2985, 0.3755] (95% CI, n=546) | 2.251 [2.074, 2.423] (95% CI, n=546) | yes | 84% |
| 0.13 | 0.000004 | 0.0991 | 0.7685 [0.7108, 0.8276] (95% CI, n=546) | 0.8211 [0.7668, 0.8743] (95% CI, n=546) | 0.3480 [0.3113, 0.3864] (95% CI, n=546) | 2.208 [2.043, 2.378] (95% CI, n=546) | yes | 82% |
| 0.14 | 0.000004 | 0.1079 | 0.7734 [0.7162, 0.8299] (95% CI, n=546) | 0.8093 [0.7525, 0.8651] (95% CI, n=546) | 0.3553 [0.3168, 0.3938] (95% CI, n=546) | 2.177 [2.016, 2.336] (95% CI, n=546) | yes | 81% |
| 0.15 | 0.000004 | 0.1166 | 0.7734 [0.7162, 0.8299] (95% CI, n=546) | 0.7970 [0.7387, 0.8550] (95% CI, n=546) | 0.3608 [0.3223, 0.3993] (95% CI, n=546) | 2.144 [1.985, 2.300] (95% CI, n=546) | yes | 80% |
| 0.16 | 0.000003 | 0.1254 | 0.7734 [0.7162, 0.8299] (95% CI, n=546) | 0.7850 [0.7255, 0.8421] (95% CI, n=546) | 0.3663 [0.3278, 0.4066] (95% CI, n=546) | 2.111 [1.955, 2.266] (95% CI, n=546) | yes | 79% |
| 0.17 | 0.000003 | 0.1341 | 0.7833 [0.7250, 0.8392] (95% CI, n=546) | 0.7756 [0.7135, 0.8341] (95% CI, n=546) | 0.3755 [0.3351, 0.4158] (95% CI, n=546) | 2.086 [1.931, 2.235] (95% CI, n=546) | yes | 78% |
| 0.18 | 0.000003 | 0.1429 | 0.7931 [0.7354, 0.8528] (95% CI, n=546) | 0.7667 [0.7040, 0.8243] (95% CI, n=546) | 0.3846 [0.3443, 0.4249] (95% CI, n=546) | 2.062 [1.912, 2.217] (95% CI, n=546) | yes | 79% |
| 0.19 | 0.000003 | 0.1516 | 0.7931 [0.7354, 0.8528] (95% CI, n=546) | 0.7559 [0.6927, 0.8142] (95% CI, n=546) | 0.3901 [0.3480, 0.4322] (95% CI, n=546) | 2.033 [1.885, 2.186] (95% CI, n=546) | yes | 79% |
| 0.20 | 0.000002 | 0.1633 | 0.8128 [0.7550, 0.8660] (95% CI, n=546) | 0.7466 [0.6844, 0.8045] (95% CI, n=546) | 0.4048 [0.3626, 0.4451] (95% CI, n=546) | 2.008 [1.865, 2.139] (95% CI, n=546) | yes | 81% |

## The frontier: what recall costs

Everything flagged routes to the expensive check, so the flag rate is the bill. Costed against the flag-rate budgets `config.yaml` actually declares:

| profile | declared flag-rate budget |
|---|---:|
| `customer_support` | 0.10 |
| `internal_knowledge` | 0.20 |
| `decision_support` | 0.50 |

> **These are envelope figures, not production costs.** Flag rate is measured at base rate 0.3718. Production traffic is nowhere near that, and the same threshold would flag a different share of it. Quoting a judge-call figure from here as a production cost puts a flag rate from one workload beside a base rate from another — the scenario-mixing error `CLAUDE.md` names. `DECISIONS.md` 132.

| target FPR | recall | flag rate | judge calls / 1000 | lift | profiles within budget |
|---:|---|---:|---:|---:|---|
| 0.01 | 0.3498 [0.2828, 0.4109] (95% CI, n=546) | 0.1300 | 130 | 2.690 | `decision_support`, `internal_knowledge` |
| 0.02 | 0.3990 [0.3317, 0.4676] (95% CI, n=546) | 0.1520 | 152 | 2.625 | `decision_support`, `internal_knowledge` |
| 0.03 | 0.4877 [0.4147, 0.5598] (95% CI, n=546) | 0.1886 | 189 | 2.585 | `decision_support`, `internal_knowledge` |
| 0.04 | 0.5369 [0.4673, 0.6117] (95% CI, n=546) | 0.2125 | 212 | 2.527 | `decision_support` |
| 0.05 | 0.6158 [0.5467, 0.6827] (95% CI, n=546) | 0.2473 | 247 | 2.490 | `decision_support` |
| 0.06 | 0.6798 [0.6168, 0.7400] (95% CI, n=546) | 0.2766 | 277 | 2.458 | `decision_support` |
| 0.07 | 0.6897 [0.6265, 0.7500] (95% CI, n=546) | 0.2857 | 286 | 2.414 | `decision_support` |
| 0.08 | 0.6946 [0.6316, 0.7550] (95% CI, n=546) | 0.2912 | 291 | 2.385 | `decision_support` |
| 0.09 | 0.6995 [0.6372, 0.7626] (95% CI, n=546) | 0.2985 | 299 | 2.343 | `decision_support` |
| 0.10 | 0.7291 [0.6700, 0.7889] (95% CI, n=546) | 0.3150 | 315 | 2.314 | `decision_support` |
| 0.11 | 0.7438 [0.6822, 0.8030] (95% CI, n=546) | 0.3260 | 326 | 2.282 | `decision_support` |
| 0.12 | 0.7586 [0.6990, 0.8165] (95% CI, n=546) | 0.3370 | 337 | 2.251 | `decision_support` |
| 0.13 | 0.7685 [0.7108, 0.8276] (95% CI, n=546) | 0.3480 | 348 | 2.208 | `decision_support` |
| 0.14 | 0.7734 [0.7162, 0.8299] (95% CI, n=546) | 0.3553 | 355 | 2.177 | `decision_support` |
| 0.15 | 0.7734 [0.7162, 0.8299] (95% CI, n=546) | 0.3608 | 361 | 2.144 | `decision_support` |
| 0.16 | 0.7734 [0.7162, 0.8299] (95% CI, n=546) | 0.3663 | 366 | 2.111 | `decision_support` |
| 0.17 | 0.7833 [0.7250, 0.8392] (95% CI, n=546) | 0.3755 | 375 | 2.086 | `decision_support` |
| 0.18 | 0.7931 [0.7354, 0.8528] (95% CI, n=546) | 0.3846 | 385 | 2.062 | `decision_support` |
| 0.19 | 0.7931 [0.7354, 0.8528] (95% CI, n=546) | 0.3901 | 390 | 2.033 | `decision_support` |
| 0.20 | 0.8128 [0.7550, 0.8660] (95% CI, n=546) | 0.4048 | 405 | 2.008 | `decision_support` |

### The two ends of the trade

**Most recall available** — target 0.20: recall 0.8128, costing 405 judge calls per 1000 requests (40.5% of this envelope). Within budget for: `decision_support`.

**Best lift per flagged item** — target 0.01: lift 2.690 (100% of ceiling) at recall 0.3498, costing 130 calls per 1000. Within budget for: `decision_support`, `internal_knowledge`.

The operating point is a business choice between the two, and this table is the whole of what the measurement can say about it. Which profile a point can actually serve is decided by the policy layer, which conjoins a recall floor and an FPR ceiling to the flag-rate budget; fitting the budget is necessary and not sufficient.

## The shipped operating point, for reference

- `None` at threshold 0.500000
- recall 0.4286 [0.3571, 0.4976] (95% CI, n=546)
- precision 0.9560 [0.9091, 0.9908] (95% CI, n=546)
- flag rate 0.1667 [0.1337, 0.1978] (95% CI, n=546)
- lift 2.571 [2.143, 2.986] (95% CI, n=546)

## What this sweep does not establish

The threshold at each grid point is certified on the **same** frozen test split the recall is then measured on. The pipeline's discipline is stricter — selection on validation, test scored once — and only test-split scores are frozen, so that discipline could not be applied here without refitting the probe. `certify_fpr` reads the negatives only, so the positives that determine recall play no part in choosing the threshold; the bias is that the threshold tracks this sample's negative tail rather than the population's. Each recall above is therefore an in-sample figure and is not a warrant.

