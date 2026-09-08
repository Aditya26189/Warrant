# FPR budget sweep — triviaqa-600 · T1-last_token

Re-analysis of frozen scores in `results/scores/validation-T1-last_token.json`. No inference was run: every number is a function of the committed labels, scores and question ids.

- commit `8e709dc932a6` · dirty `False` · config `533fb74983fcd8af`
- detector `probe-qwen2.5-7b-instruct-T1-last_token` · envelope `sha256:e77c64f908491ad1`
- certification: Clopper-Pearson one-sided upper bound at alpha 0.050, via `certify_fpr`
- intervals: percentile bootstrap, 1000 resamples over questions, seed 1729
- thresholds certified and metrics measured on the same set, `validation-T1-last_token` — **in sample**
- n 600 (277 positive, 323 negative) · base rate 0.4617

## Verdict

Lift holds at 19 of 20 swept targets, the loosest being a target FPR of 0.20, where the certified threshold achieves FPR 0.1610 and lift 1.678 [1.545, 1.831] — 77% of the 2.17 ceiling. Recall there is 0.6462 [0.5950, 0.7051], against 0.0794 at the shipped operating point. Recall 0.0794 is a dial, not a ceiling: loosening the false-positive budget lifts recall clear of the shipped point's own 95% interval, so the number the product ships is a policy choice and the honest form of the claim is a curve rather than a point.

## The pre-registered criterion

Lift *holds* at a target FPR when the **lower bound** of its 95% bootstrap interval is strictly greater than 1.0. Registered before any output was seen (Phase 0 brief, D6) and not adjusted afterwards.

## Grid

| target FPR | threshold | achieved FPR | recall | precision | flag rate | lift | lift CI low > 1 | % of ceiling |
|---:|---:|---:|---|---|---|---|:--:|---:|
| 0.01 | 0.966568 | 0.0000 | 0.0108 [0.0000, 0.0256] (95% CI, n=600) | 1.0000 [0.0000, 1.0000] (95% CI, n=600) | 0.0050 [0.0000, 0.0117] (95% CI, n=600) | 2.166 [0.000, 5.129] (95% CI, n=600) | no | 100% |
| 0.02 | 0.946788 | 0.0062 | 0.0650 [0.0390, 0.0962] (95% CI, n=600) | 0.9000 [0.7500, 1.0000] (95% CI, n=600) | 0.0333 [0.0200, 0.0483] (95% CI, n=600) | 1.949 [1.170, 2.887] (95% CI, n=600) | yes | 90% |
| 0.03 | 0.909941 | 0.0124 | 0.1516 [0.1126, 0.1957] (95% CI, n=600) | 0.9130 [0.8235, 0.9808] (95% CI, n=600) | 0.0767 [0.0567, 0.0983] (95% CI, n=600) | 1.978 [1.469, 2.552] (95% CI, n=600) | yes | 91% |
| 0.04 | 0.877921 | 0.0186 | 0.2274 [0.1809, 0.2800] (95% CI, n=600) | 0.9130 [0.8451, 0.9718] (95% CI, n=600) | 0.1150 [0.0917, 0.1417] (95% CI, n=600) | 1.978 [1.573, 2.435] (95% CI, n=600) | yes | 91% |
| 0.05 | 0.870323 | 0.0279 | 0.2310 [0.1844, 0.2843] (95% CI, n=600) | 0.8767 [0.7971, 0.9444] (95% CI, n=600) | 0.1217 [0.0967, 0.1500] (95% CI, n=600) | 1.899 [1.515, 2.336] (95% CI, n=600) | yes | 88% |
| 0.06 | 0.845821 | 0.0372 | 0.2924 [0.2428, 0.3519] (95% CI, n=600) | 0.8710 [0.8064, 0.9355] (95% CI, n=600) | 0.1550 [0.1283, 0.1867] (95% CI, n=600) | 1.887 [1.567, 2.270] (95% CI, n=600) | yes | 87% |
| 0.07 | 0.798930 | 0.0433 | 0.3610 [0.3082, 0.4207] (95% CI, n=600) | 0.8772 [0.8173, 0.9344] (95% CI, n=600) | 0.1900 [0.1617, 0.2233] (95% CI, n=600) | 1.900 [1.622, 2.214] (95% CI, n=600) | yes | 88% |
| 0.08 | 0.771292 | 0.0526 | 0.4116 [0.3610, 0.4733] (95% CI, n=600) | 0.8702 [0.8116, 0.9250] (95% CI, n=600) | 0.2183 [0.1883, 0.2517] (95% CI, n=600) | 1.885 [1.653, 2.168] (95% CI, n=600) | yes | 87% |
| 0.09 | 0.752185 | 0.0619 | 0.4296 [0.3754, 0.4892] (95% CI, n=600) | 0.8561 [0.7956, 0.9103] (95% CI, n=600) | 0.2317 [0.2000, 0.2650] (95% CI, n=600) | 1.854 [1.620, 2.112] (95% CI, n=600) | yes | 86% |
| 0.10 | 0.743222 | 0.0712 | 0.4477 [0.3928, 0.5074] (95% CI, n=600) | 0.8435 [0.7831, 0.8993] (95% CI, n=600) | 0.2450 [0.2150, 0.2800] (95% CI, n=600) | 1.827 [1.603, 2.071] (95% CI, n=600) | yes | 84% |
| 0.11 | 0.715858 | 0.0805 | 0.4946 [0.4413, 0.5528] (95% CI, n=600) | 0.8405 [0.7844, 0.8924] (95% CI, n=600) | 0.2717 [0.2400, 0.3067] (95% CI, n=600) | 1.821 [1.624, 2.035] (95% CI, n=600) | yes | 84% |
| 0.12 | 0.686978 | 0.0867 | 0.5126 [0.4601, 0.5751] (95% CI, n=600) | 0.8353 [0.7778, 0.8872] (95% CI, n=600) | 0.2833 [0.2517, 0.3183] (95% CI, n=600) | 1.809 [1.624, 2.030] (95% CI, n=600) | yes | 84% |
| 0.13 | 0.672424 | 0.0960 | 0.5307 [0.4778, 0.5922] (95% CI, n=600) | 0.8258 [0.7688, 0.8791] (95% CI, n=600) | 0.2967 [0.2650, 0.3317] (95% CI, n=600) | 1.789 [1.611, 1.996] (95% CI, n=600) | yes | 83% |
| 0.14 | 0.666849 | 0.1053 | 0.5415 [0.4873, 0.6047] (95% CI, n=600) | 0.8152 [0.7590, 0.8686] (95% CI, n=600) | 0.3067 [0.2750, 0.3433] (95% CI, n=600) | 1.766 [1.589, 1.972] (95% CI, n=600) | yes | 82% |
| 0.15 | 0.650673 | 0.1146 | 0.5632 [0.5083, 0.6241] (95% CI, n=600) | 0.8083 [0.7514, 0.8615] (95% CI, n=600) | 0.3217 [0.2883, 0.3600] (95% CI, n=600) | 1.751 [1.580, 1.940] (95% CI, n=600) | yes | 81% |
| 0.16 | 0.638638 | 0.1238 | 0.5704 [0.5154, 0.6345] (95% CI, n=600) | 0.7980 [0.7421, 0.8522] (95% CI, n=600) | 0.3300 [0.2950, 0.3700] (95% CI, n=600) | 1.728 [1.562, 1.923] (95% CI, n=600) | yes | 80% |
| 0.17 | 0.621277 | 0.1331 | 0.5921 [0.5318, 0.6553] (95% CI, n=600) | 0.7923 [0.7357, 0.8479] (95% CI, n=600) | 0.3450 [0.3100, 0.3850] (95% CI, n=600) | 1.716 [1.541, 1.900] (95% CI, n=600) | yes | 79% |
| 0.18 | 0.600007 | 0.1424 | 0.6101 [0.5522, 0.6717] (95% CI, n=600) | 0.7860 [0.7289, 0.8397] (95% CI, n=600) | 0.3583 [0.3217, 0.3967] (95% CI, n=600) | 1.703 [1.541, 1.875] (95% CI, n=600) | yes | 79% |
| 0.19 | 0.590980 | 0.1517 | 0.6209 [0.5656, 0.6805] (95% CI, n=600) | 0.7783 [0.7229, 0.8341] (95% CI, n=600) | 0.3683 [0.3317, 0.4067] (95% CI, n=600) | 1.686 [1.536, 1.847] (95% CI, n=600) | yes | 78% |
| 0.20 | 0.566509 | 0.1610 | 0.6462 [0.5950, 0.7051] (95% CI, n=600) | 0.7749 [0.7227, 0.8290] (95% CI, n=600) | 0.3850 [0.3483, 0.4250] (95% CI, n=600) | 1.678 [1.545, 1.831] (95% CI, n=600) | yes | 77% |

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
| 0.01 | 0.0108 [0.0000, 0.0256] (95% CI, n=600) | 0.0050 | 5 | 2.166 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.02 | 0.0650 [0.0390, 0.0962] (95% CI, n=600) | 0.0333 | 33 | 1.949 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.03 | 0.1516 [0.1126, 0.1957] (95% CI, n=600) | 0.0767 | 77 | 1.978 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.04 | 0.2274 [0.1809, 0.2800] (95% CI, n=600) | 0.1150 | 115 | 1.978 | `decision_support`, `internal_knowledge` |
| 0.05 | 0.2310 [0.1844, 0.2843] (95% CI, n=600) | 0.1217 | 122 | 1.899 | `decision_support`, `internal_knowledge` |
| 0.06 | 0.2924 [0.2428, 0.3519] (95% CI, n=600) | 0.1550 | 155 | 1.887 | `decision_support`, `internal_knowledge` |
| 0.07 | 0.3610 [0.3082, 0.4207] (95% CI, n=600) | 0.1900 | 190 | 1.900 | `decision_support`, `internal_knowledge` |
| 0.08 | 0.4116 [0.3610, 0.4733] (95% CI, n=600) | 0.2183 | 218 | 1.885 | `decision_support` |
| 0.09 | 0.4296 [0.3754, 0.4892] (95% CI, n=600) | 0.2317 | 232 | 1.854 | `decision_support` |
| 0.10 | 0.4477 [0.3928, 0.5074] (95% CI, n=600) | 0.2450 | 245 | 1.827 | `decision_support` |
| 0.11 | 0.4946 [0.4413, 0.5528] (95% CI, n=600) | 0.2717 | 272 | 1.821 | `decision_support` |
| 0.12 | 0.5126 [0.4601, 0.5751] (95% CI, n=600) | 0.2833 | 283 | 1.809 | `decision_support` |
| 0.13 | 0.5307 [0.4778, 0.5922] (95% CI, n=600) | 0.2967 | 297 | 1.789 | `decision_support` |
| 0.14 | 0.5415 [0.4873, 0.6047] (95% CI, n=600) | 0.3067 | 307 | 1.766 | `decision_support` |
| 0.15 | 0.5632 [0.5083, 0.6241] (95% CI, n=600) | 0.3217 | 322 | 1.751 | `decision_support` |
| 0.16 | 0.5704 [0.5154, 0.6345] (95% CI, n=600) | 0.3300 | 330 | 1.728 | `decision_support` |
| 0.17 | 0.5921 [0.5318, 0.6553] (95% CI, n=600) | 0.3450 | 345 | 1.716 | `decision_support` |
| 0.18 | 0.6101 [0.5522, 0.6717] (95% CI, n=600) | 0.3583 | 358 | 1.703 | `decision_support` |
| 0.19 | 0.6209 [0.5656, 0.6805] (95% CI, n=600) | 0.3683 | 368 | 1.686 | `decision_support` |
| 0.20 | 0.6462 [0.5950, 0.7051] (95% CI, n=600) | 0.3850 | 385 | 1.678 | `decision_support` |

### The two ends of the trade

**Most recall available** — target 0.20: recall 0.6462, costing 385 judge calls per 1000 requests (38.5% of this envelope). Within budget for: `decision_support`.

**Best lift per flagged item** — target 0.03: lift 1.978 (91% of ceiling) at recall 0.1516, costing 77 calls per 1000. Within budget for: `customer_support`, `decision_support`, `internal_knowledge`.

The operating point is a business choice between the two, and this table is the whole of what the measurement can say about it. Which profile a point can actually serve is decided by the policy layer, which conjoins a recall floor and an FPR ceiling to the flag-rate budget; fitting the budget is necessary and not sufficient.

## The shipped operating point, for reference

- `P-conservative` at threshold 0.940337
- recall 0.0794 [0.0496, 0.1115] (95% CI, n=600)
- precision 0.8800 [0.7500, 1.0000] (95% CI, n=600)
- flag rate 0.0417 [0.0267, 0.0583] (95% CI, n=600)
- lift 1.906 [1.190, 2.676] (95% CI, n=600)

## What this sweep does not establish

The threshold at each grid point is certified on the **same** frozen test split the recall is then measured on. The pipeline's discipline is stricter — selection on validation, test scored once — and only test-split scores are frozen, so that discipline could not be applied here without refitting the probe. `certify_fpr` reads the negatives only, so the positives that determine recall play no part in choosing the threshold; the bias is that the threshold tracks this sample's negative tail rather than the population's. Each recall above is therefore an in-sample figure and is not a warrant.

