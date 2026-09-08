# FPR budget sweep — ai4privacy/pii-masking-200k · 2.2.364

Re-analysis of frozen scores in `results/scores/external-presidio-url.json`. No inference was run: every number is a function of the committed labels, scores and question ids.

- commit `8e709dc932a6` · dirty `False` · config `533fb74983fcd8af`
- detector `presidio-analyzer` · envelope `revision:7c22e6816b8fc24b`
- certification: Clopper-Pearson one-sided upper bound at alpha 0.050, via `certify_fpr`
- intervals: percentile bootstrap, 1000 resamples over questions, seed 1729
- thresholds certified and metrics measured on the same set, `external-presidio-url` — **in sample**
- n 2000 (129 positive, 1871 negative) · base rate 0.0645

## Verdict

Lift holds at 20 of 20 swept targets, the loosest being a target FPR of 0.20, where the certified threshold achieves FPR 0.0994 and lift 6.349 [6.170, 6.349] — 100% of the 6.35 ceiling. Recall there is 1.0000 [0.9718, 1.0000], against 1.0000 at the shipped operating point. Recall 1.0000 is a ceiling rather than a dial: even at the loosest budget where lift still holds, recall does not clear the upper bound of the shipped point's own 95% interval, so loosening the budget buys nothing this sample can distinguish from where the product already sits.

## The pre-registered criterion

Lift *holds* at a target FPR when the **lower bound** of its 95% bootstrap interval is strictly greater than 1.0. Registered before any output was seen (Phase 0 brief, D6) and not adjusted afterwards.

## Grid

| target FPR | threshold | achieved FPR | recall | precision | flag rate | lift | lift CI low > 1 | % of ceiling |
|---:|---:|---:|---|---|---|---|:--:|---:|
| 0.01 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.02 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.03 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.04 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.05 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.06 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.07 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.08 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.09 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.10 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.11 | 0.500000 | 0.0032 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.9556 [0.9173, 0.9857] (95% CI, n=2000) | 0.0675 [0.0555, 0.0795] (95% CI, n=2000) | 14.815 [14.397, 14.815] (95% CI, n=2000) | yes | 100% |
| 0.12 | 0.000000 | 0.0994 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.4095 [0.3526, 0.4647] (95% CI, n=2000) | 0.1575 [0.1405, 0.1735] (95% CI, n=2000) | 6.349 [6.170, 6.349] (95% CI, n=2000) | yes | 100% |
| 0.13 | 0.000000 | 0.0994 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.4095 [0.3526, 0.4647] (95% CI, n=2000) | 0.1575 [0.1405, 0.1735] (95% CI, n=2000) | 6.349 [6.170, 6.349] (95% CI, n=2000) | yes | 100% |
| 0.14 | 0.000000 | 0.0994 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.4095 [0.3526, 0.4647] (95% CI, n=2000) | 0.1575 [0.1405, 0.1735] (95% CI, n=2000) | 6.349 [6.170, 6.349] (95% CI, n=2000) | yes | 100% |
| 0.15 | 0.000000 | 0.0994 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.4095 [0.3526, 0.4647] (95% CI, n=2000) | 0.1575 [0.1405, 0.1735] (95% CI, n=2000) | 6.349 [6.170, 6.349] (95% CI, n=2000) | yes | 100% |
| 0.16 | 0.000000 | 0.0994 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.4095 [0.3526, 0.4647] (95% CI, n=2000) | 0.1575 [0.1405, 0.1735] (95% CI, n=2000) | 6.349 [6.170, 6.349] (95% CI, n=2000) | yes | 100% |
| 0.17 | 0.000000 | 0.0994 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.4095 [0.3526, 0.4647] (95% CI, n=2000) | 0.1575 [0.1405, 0.1735] (95% CI, n=2000) | 6.349 [6.170, 6.349] (95% CI, n=2000) | yes | 100% |
| 0.18 | 0.000000 | 0.0994 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.4095 [0.3526, 0.4647] (95% CI, n=2000) | 0.1575 [0.1405, 0.1735] (95% CI, n=2000) | 6.349 [6.170, 6.349] (95% CI, n=2000) | yes | 100% |
| 0.19 | 0.000000 | 0.0994 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.4095 [0.3526, 0.4647] (95% CI, n=2000) | 0.1575 [0.1405, 0.1735] (95% CI, n=2000) | 6.349 [6.170, 6.349] (95% CI, n=2000) | yes | 100% |
| 0.20 | 0.000000 | 0.0994 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.4095 [0.3526, 0.4647] (95% CI, n=2000) | 0.1575 [0.1405, 0.1735] (95% CI, n=2000) | 6.349 [6.170, 6.349] (95% CI, n=2000) | yes | 100% |

## The frontier: what recall costs

Everything flagged routes to the expensive check, so the flag rate is the bill. Costed against the flag-rate budgets `config.yaml` actually declares:

| profile | declared flag-rate budget |
|---|---:|
| `customer_support` | 0.10 |
| `internal_knowledge` | 0.20 |
| `decision_support` | 0.50 |

> **These are envelope figures, not production costs.** Flag rate is measured at base rate 0.0645. Production traffic is nowhere near that, and the same threshold would flag a different share of it. Quoting a judge-call figure from here as a production cost puts a flag rate from one workload beside a base rate from another — the scenario-mixing error `CLAUDE.md` names. `DECISIONS.md` 132.

| target FPR | recall | flag rate | judge calls / 1000 | lift | profiles within budget |
|---:|---|---:|---:|---:|---|
| 0.01 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.02 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.03 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.04 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.05 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.06 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.07 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.08 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.09 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.10 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.11 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.0675 | 68 | 14.815 | `customer_support`, `decision_support`, `internal_knowledge` |
| 0.12 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.1575 | 158 | 6.349 | `decision_support`, `internal_knowledge` |
| 0.13 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.1575 | 158 | 6.349 | `decision_support`, `internal_knowledge` |
| 0.14 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.1575 | 158 | 6.349 | `decision_support`, `internal_knowledge` |
| 0.15 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.1575 | 158 | 6.349 | `decision_support`, `internal_knowledge` |
| 0.16 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.1575 | 158 | 6.349 | `decision_support`, `internal_knowledge` |
| 0.17 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.1575 | 158 | 6.349 | `decision_support`, `internal_knowledge` |
| 0.18 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.1575 | 158 | 6.349 | `decision_support`, `internal_knowledge` |
| 0.19 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.1575 | 158 | 6.349 | `decision_support`, `internal_knowledge` |
| 0.20 | 1.0000 [0.9718, 1.0000] (95% CI, n=2000) | 0.1575 | 158 | 6.349 | `decision_support`, `internal_knowledge` |

### The two ends of the trade

**Most recall available** — target 0.01: recall 1.0000, costing 68 judge calls per 1000 requests (6.8% of this envelope). Within budget for: `customer_support`, `decision_support`, `internal_knowledge`.

**Best lift per flagged item** — target 0.01: lift 14.815 (100% of ceiling) at recall 1.0000, costing 68 calls per 1000. Within budget for: `customer_support`, `decision_support`, `internal_knowledge`.

The operating point is a business choice between the two, and this table is the whole of what the measurement can say about it. Which profile a point can actually serve is decided by the policy layer, which conjoins a recall floor and an FPR ceiling to the flag-rate budget; fitting the budget is necessary and not sufficient.

## The shipped operating point, for reference

- `None` at threshold 0.500000
- recall 1.0000 [0.9718, 1.0000] (95% CI, n=2000)
- precision 0.4095 [0.3526, 0.4647] (95% CI, n=2000)
- flag rate 0.1575 [0.1405, 0.1735] (95% CI, n=2000)
- lift 6.349 [6.170, 6.349] (95% CI, n=2000)

## What this sweep does not establish

The threshold at each grid point is certified on the **same** frozen test split the recall is then measured on. The pipeline's discipline is stricter — selection on validation, test scored once — and only test-split scores are frozen, so that discipline could not be applied here without refitting the probe. `certify_fpr` reads the negatives only, so the positives that determine recall play no part in choosing the threshold; the bias is that the threshold tracks this sample's negative tail rather than the population's. Each recall above is therefore an in-sample figure and is not a warrant.

