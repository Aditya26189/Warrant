# FPR budget sweep — triviaqa-600 · T1-last_token

Re-analysis of frozen scores in `results/scores/validation-T1-last_token.json`. No inference was run: every number is a function of the committed labels, scores and question ids.

- commit `6779908207f3` · dirty `True` · config `533fb74983fcd8af`
- detector `probe-qwen2.5-7b-instruct-T1-last_token` · envelope `sha256:e77c64f908491ad1`
- certification: Clopper-Pearson one-sided upper bound at alpha 0.050, via `certify_fpr`
- intervals: percentile bootstrap, 1000 resamples over questions, seed 1729
- n 600 (277 positive, 323 negative) · base rate 0.4617

## Verdict

Lift holds at 20 of 20 swept targets, the loosest being a target FPR of 0.20, where the certified threshold achieves FPR 0.1611 and lift 1.677 [1.535, 1.826] — 77% of the 2.17 ceiling. Recall there is 0.6318 [0.5782, 0.6880], against 0.0794 at the shipped operating point. Recall 0.0794 is a dial, not a ceiling: loosening the false-positive budget lifts recall clear of the shipped point's own 95% interval, so the number the product ships is a policy choice and the honest form of the claim is a curve rather than a point.

## The pre-registered criterion

Lift *holds* at a target FPR when the **lower bound** of its 95% bootstrap interval is strictly greater than 1.0. Registered before any output was seen (Phase 0 brief, D6) and not adjusted afterwards.

## Grid

| target FPR | threshold | achieved FPR | recall | precision | flag rate | lift | lift CI low > 1 | % of ceiling |
|---:|---:|---:|---|---|---|---|:--:|---:|
| 0.01 | 0.952481 | 0.0000 | 0.0469 [0.0246, 0.0737] (95% CI, n=600) | 0.9286 [0.7692, 1.0000] (95% CI, n=600) | 0.0233 [0.0117, 0.0367] (95% CI, n=600) | 2.011 [1.052, 3.158] (95% CI, n=600) | yes | 93% |
| 0.02 | 0.940434 | 0.0061 | 0.0794 [0.0496, 0.1115] (95% CI, n=600) | 0.8800 [0.7500, 1.0000] (95% CI, n=600) | 0.0417 [0.0267, 0.0583] (95% CI, n=600) | 1.906 [1.190, 2.676] (95% CI, n=600) | yes | 88% |
| 0.03 | 0.924327 | 0.0122 | 0.1119 [0.0785, 0.1504] (95% CI, n=600) | 0.9118 [0.8056, 1.0000] (95% CI, n=600) | 0.0567 [0.0400, 0.0767] (95% CI, n=600) | 1.975 [1.385, 2.654] (95% CI, n=600) | yes | 91% |
| 0.04 | 0.887110 | 0.0213 | 0.2130 [0.1673, 0.2638] (95% CI, n=600) | 0.9219 [0.8548, 0.9831] (95% CI, n=600) | 0.1067 [0.0850, 0.1333] (95% CI, n=600) | 1.997 [1.568, 2.474] (95% CI, n=600) | yes | 92% |
| 0.05 | 0.857347 | 0.0274 | 0.2708 [0.2230, 0.3274] (95% CI, n=600) | 0.8621 [0.7922, 0.9300] (95% CI, n=600) | 0.1450 [0.1200, 0.1750] (95% CI, n=600) | 1.867 [1.538, 2.258] (95% CI, n=600) | yes | 86% |
| 0.06 | 0.816441 | 0.0365 | 0.3321 [0.2789, 0.3960] (95% CI, n=600) | 0.8679 [0.8017, 0.9286] (95% CI, n=600) | 0.1767 [0.1500, 0.2100] (95% CI, n=600) | 1.880 [1.579, 2.241] (95% CI, n=600) | yes | 87% |
| 0.07 | 0.767593 | 0.0456 | 0.4116 [0.3610, 0.4733] (95% CI, n=600) | 0.8636 [0.8015, 0.9191] (95% CI, n=600) | 0.2200 [0.1900, 0.2533] (95% CI, n=600) | 1.871 [1.641, 2.151] (95% CI, n=600) | yes | 86% |
| 0.08 | 0.751711 | 0.0517 | 0.4332 [0.3772, 0.4929] (95% CI, n=600) | 0.8511 [0.7920, 0.9058] (95% CI, n=600) | 0.2350 [0.2033, 0.2684] (95% CI, n=600) | 1.843 [1.605, 2.098] (95% CI, n=600) | yes | 85% |
| 0.09 | 0.725764 | 0.0608 | 0.4765 [0.4228, 0.5370] (95% CI, n=600) | 0.8354 [0.7784, 0.8882] (95% CI, n=600) | 0.2633 [0.2317, 0.2984] (95% CI, n=600) | 1.810 [1.605, 2.039] (95% CI, n=600) | yes | 84% |
| 0.10 | 0.719509 | 0.0699 | 0.4838 [0.4301, 0.5444] (95% CI, n=600) | 0.8375 [0.7810, 0.8902] (95% CI, n=600) | 0.2667 [0.2350, 0.3017] (95% CI, n=600) | 1.814 [1.613, 2.042] (95% CI, n=600) | yes | 84% |
| 0.11 | 0.675542 | 0.0790 | 0.5199 [0.4683, 0.5814] (95% CI, n=600) | 0.8276 [0.7688, 0.8791] (95% CI, n=600) | 0.2900 [0.2583, 0.3267] (95% CI, n=600) | 1.793 [1.615, 2.005] (95% CI, n=600) | yes | 83% |
| 0.12 | 0.651885 | 0.0881 | 0.5632 [0.5083, 0.6241] (95% CI, n=600) | 0.8083 [0.7514, 0.8615] (95% CI, n=600) | 0.3217 [0.2883, 0.3600] (95% CI, n=600) | 1.751 [1.580, 1.940] (95% CI, n=600) | yes | 81% |
| 0.13 | 0.634857 | 0.0973 | 0.5704 [0.5154, 0.6345] (95% CI, n=600) | 0.7940 [0.7376, 0.8485] (95% CI, n=600) | 0.3317 [0.2983, 0.3700] (95% CI, n=600) | 1.720 [1.554, 1.913] (95% CI, n=600) | yes | 79% |
| 0.14 | 0.616486 | 0.1064 | 0.5921 [0.5318, 0.6553] (95% CI, n=600) | 0.7885 [0.7330, 0.8433] (95% CI, n=600) | 0.3467 [0.3117, 0.3867] (95% CI, n=600) | 1.708 [1.534, 1.890] (95% CI, n=600) | yes | 79% |
| 0.15 | 0.610455 | 0.1155 | 0.5957 [0.5351, 0.6581] (95% CI, n=600) | 0.7820 [0.7251, 0.8366] (95% CI, n=600) | 0.3517 [0.3150, 0.3917] (95% CI, n=600) | 1.694 [1.522, 1.871] (95% CI, n=600) | yes | 78% |
| 0.16 | 0.603774 | 0.1246 | 0.6065 [0.5482, 0.6690] (95% CI, n=600) | 0.7850 [0.7286, 0.8396] (95% CI, n=600) | 0.3567 [0.3217, 0.3950] (95% CI, n=600) | 1.700 [1.537, 1.876] (95% CI, n=600) | yes | 79% |
| 0.17 | 0.597633 | 0.1337 | 0.6101 [0.5522, 0.6717] (95% CI, n=600) | 0.7788 [0.7224, 0.8349] (95% CI, n=600) | 0.3617 [0.3250, 0.4017] (95% CI, n=600) | 1.687 [1.527, 1.857] (95% CI, n=600) | yes | 78% |
| 0.18 | 0.592105 | 0.1429 | 0.6209 [0.5656, 0.6805] (95% CI, n=600) | 0.7783 [0.7229, 0.8341] (95% CI, n=600) | 0.3683 [0.3317, 0.4067] (95% CI, n=600) | 1.686 [1.536, 1.847] (95% CI, n=600) | yes | 78% |
| 0.19 | 0.584959 | 0.1520 | 0.6282 [0.5735, 0.6871] (95% CI, n=600) | 0.7733 [0.7207, 0.8273] (95% CI, n=600) | 0.3750 [0.3350, 0.4133] (95% CI, n=600) | 1.675 [1.529, 1.832] (95% CI, n=600) | yes | 77% |
| 0.20 | 0.580776 | 0.1611 | 0.6318 [0.5782, 0.6880] (95% CI, n=600) | 0.7743 [0.7220, 0.8281] (95% CI, n=600) | 0.3767 [0.3383, 0.4150] (95% CI, n=600) | 1.677 [1.535, 1.826] (95% CI, n=600) | yes | 77% |

## The frontier: what recall costs

Everything flagged routes to the expensive check, so the flag rate is the bill. Costed against the flag-rate budgets `config.yaml` actually declares:

| profile | declared flag-rate budget |
|---|---:|
| `customer_support` | 0.10 |
| `internal_knowledge` | 0.20 |
| `decision_support` | 0.50 |

> **These are envelope figures, not production costs.** Flag rate is measured at base rate 0.4617. Production traffic is nowhere near that, and the same threshold would flag a different share of it. Quoting a judge-call figure from here as a production cost puts a flag rate from one workload beside a base rate from another — the scenario-mixing error `CLAUDE.md` names. `DECISIONS.md` 132.

| target FPR | recall | flag rate | judge calls / 1000 | lift | profiles within budget |
|---:|---|---:|---:|---:|---|
| 0.01 | 0.0469 [0.0246, 0.0737] (95% CI, n=600) | 0.0233 | 23 | 2.011 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.02 | 0.0794 [0.0496, 0.1115] (95% CI, n=600) | 0.0417 | 42 | 1.906 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.03 | 0.1119 [0.0785, 0.1504] (95% CI, n=600) | 0.0567 | 57 | 1.975 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.04 | 0.2130 [0.1673, 0.2638] (95% CI, n=600) | 0.1067 | 107 | 1.997 | `decision_support`, `internal_knowledge` |
| 0.05 | 0.2708 [0.2230, 0.3274] (95% CI, n=600) | 0.1450 | 145 | 1.867 | `decision_support`, `internal_knowledge` |
| 0.06 | 0.3321 [0.2789, 0.3960] (95% CI, n=600) | 0.1767 | 177 | 1.880 | `decision_support`, `internal_knowledge` |
| 0.07 | 0.4116 [0.3610, 0.4733] (95% CI, n=600) | 0.2200 | 220 | 1.871 | `decision_support` |
| 0.08 | 0.4332 [0.3772, 0.4929] (95% CI, n=600) | 0.2350 | 235 | 1.843 | `decision_support` |
| 0.09 | 0.4765 [0.4228, 0.5370] (95% CI, n=600) | 0.2633 | 263 | 1.810 | `decision_support` |
| 0.10 | 0.4838 [0.4301, 0.5444] (95% CI, n=600) | 0.2667 | 267 | 1.814 | `decision_support` |
| 0.11 | 0.5199 [0.4683, 0.5814] (95% CI, n=600) | 0.2900 | 290 | 1.793 | `decision_support` |
| 0.12 | 0.5632 [0.5083, 0.6241] (95% CI, n=600) | 0.3217 | 322 | 1.751 | `decision_support` |
| 0.13 | 0.5704 [0.5154, 0.6345] (95% CI, n=600) | 0.3317 | 332 | 1.720 | `decision_support` |
| 0.14 | 0.5921 [0.5318, 0.6553] (95% CI, n=600) | 0.3467 | 347 | 1.708 | `decision_support` |
| 0.15 | 0.5957 [0.5351, 0.6581] (95% CI, n=600) | 0.3517 | 352 | 1.694 | `decision_support` |
| 0.16 | 0.6065 [0.5482, 0.6690] (95% CI, n=600) | 0.3567 | 357 | 1.700 | `decision_support` |
| 0.17 | 0.6101 [0.5522, 0.6717] (95% CI, n=600) | 0.3617 | 362 | 1.687 | `decision_support` |
| 0.18 | 0.6209 [0.5656, 0.6805] (95% CI, n=600) | 0.3683 | 368 | 1.686 | `decision_support` |
| 0.19 | 0.6282 [0.5735, 0.6871] (95% CI, n=600) | 0.3750 | 375 | 1.675 | `decision_support` |
| 0.20 | 0.6318 [0.5782, 0.6880] (95% CI, n=600) | 0.3767 | 377 | 1.677 | `decision_support` |

### The two ends of the trade

**Most recall available** — target 0.20: recall 0.6318, costing 377 judge calls per 1000 requests (37.7% of this envelope). Within budget for: `decision_support`.

**Best lift per flagged item** — target 0.01: lift 2.011 (93% of ceiling) at recall 0.0469, costing 23 calls per 1000. Within budget for: `customer_support`, `decision_support`, `internal_knowledge`.

The operating point is a business choice between the two, and this table is the whole of what the measurement can say about it. Which profile a point can actually serve is decided by the policy layer, which conjoins a recall floor and an FPR ceiling to the flag-rate budget; fitting the budget is necessary and not sufficient.

## The shipped operating point, for reference

- `P-conservative` at threshold 0.940337
- recall 0.0794 [0.0496, 0.1115] (95% CI, n=600)
- precision 0.8800 [0.7500, 1.0000] (95% CI, n=600)
- flag rate 0.0417 [0.0267, 0.0583] (95% CI, n=600)
- lift 1.906 [1.190, 2.676] (95% CI, n=600)

## What this sweep does not establish

The threshold at each grid point is certified on the **same** frozen test split the recall is then measured on. The pipeline's discipline is stricter — selection on validation, test scored once — and only test-split scores are frozen, so that discipline could not be applied here without refitting the probe. `certify_fpr` reads the negatives only, so the positives that determine recall play no part in choosing the threshold; the bias is that the threshold tracks this sample's negative tail rather than the population's. Each recall above is therefore an in-sample figure and is not a warrant.

