# FPR budget sweep — REDACT locked split (ServiceNow) · 2.2.364

Re-analysis of frozen scores in `results/scores/external-redact-person-en.json`. No inference was run: every number is a function of the committed labels, scores and question ids.

- commit `ec1fc03bb243` · dirty `False` · config `533fb74983fcd8af`
- detector `presidio-analyzer` · envelope `revision:pii_benchmark_sa`
- certification: Clopper-Pearson one-sided upper bound at alpha 0.050, via `certify_fpr`
- intervals: percentile bootstrap, 1000 resamples over questions, seed 1729
- thresholds certified and metrics measured on the same set, `external-redact-person-en` — **in sample**
- n 40 (35 positive, 5 negative) · base rate 0.8750

## Verdict

Lift does not hold at any target FPR on the swept grid (0.01 to 0.20): at every point the lower bound of lift's 95% interval falls at or below 1.0, so no budget on this grid buys a detector that beats flagging at random. Recall 1.0000 at the shipped operating point is therefore not a policy choice being held down by the false-positive budget — loosening the budget does not produce a warrantable detector on this envelope. The probe is weak on REDACT locked split (ServiceNow), the FPR budget is not what is binding, and the product is the refusal machinery rather than the detector.

## The pre-registered criterion

Lift *holds* at a target FPR when the **lower bound** of its 95% bootstrap interval is strictly greater than 1.0. Registered before any output was seen (Phase 0 brief, D6) and not adjusted afterwards.

## Grid

| target FPR | threshold | achieved FPR | recall | precision | flag rate | lift | lift CI low > 1 | % of ceiling |
|---:|---:|---:|---|---|---|---|:--:|---:|
| 0.01 | REFUSED | — | — | — | — | — | — | — |
| 0.02 | REFUSED | — | — | — | — | — | — | — |
| 0.03 | REFUSED | — | — | — | — | — | — | — |
| 0.04 | REFUSED | — | — | — | — | — | — | — |
| 0.05 | REFUSED | — | — | — | — | — | — | — |
| 0.06 | REFUSED | — | — | — | — | — | — | — |
| 0.07 | REFUSED | — | — | — | — | — | — | — |
| 0.08 | REFUSED | — | — | — | — | — | — | — |
| 0.09 | REFUSED | — | — | — | — | — | — | — |
| 0.10 | REFUSED | — | — | — | — | — | — | — |
| 0.11 | REFUSED | — | — | — | — | — | — | — |
| 0.12 | REFUSED | — | — | — | — | — | — | — |
| 0.13 | REFUSED | — | — | — | — | — | — | — |
| 0.14 | REFUSED | — | — | — | — | — | — | — |
| 0.15 | REFUSED | — | — | — | — | — | — | — |
| 0.16 | REFUSED | — | — | — | — | — | — | — |
| 0.17 | REFUSED | — | — | — | — | — | — | — |
| 0.18 | REFUSED | — | — | — | — | — | — | — |
| 0.19 | REFUSED | — | — | — | — | — | — | — |
| 0.20 | REFUSED | — | — | — | — | — | — | — |

### Refused targets

- **0.01** — only 5 independent units; need >= 299 clean units to certify FPR<=0.01 at alpha=0.0500 (have 5 independent units, need 299)
- **0.02** — only 5 independent units; need >= 149 clean units to certify FPR<=0.02 at alpha=0.0500 (have 5 independent units, need 149)
- **0.03** — only 5 independent units; need >= 99 clean units to certify FPR<=0.03 at alpha=0.0500 (have 5 independent units, need 99)
- **0.04** — only 5 independent units; need >= 74 clean units to certify FPR<=0.04 at alpha=0.0500 (have 5 independent units, need 74)
- **0.05** — only 5 independent units; need >= 59 clean units to certify FPR<=0.05 at alpha=0.0500 (have 5 independent units, need 59)
- **0.06** — only 5 independent units; need >= 49 clean units to certify FPR<=0.06 at alpha=0.0500 (have 5 independent units, need 49)
- **0.07** — only 5 independent units; need >= 42 clean units to certify FPR<=0.07 at alpha=0.0500 (have 5 independent units, need 42)
- **0.08** — only 5 independent units; need >= 36 clean units to certify FPR<=0.08 at alpha=0.0500 (have 5 independent units, need 36)
- **0.09** — only 5 independent units; need >= 32 clean units to certify FPR<=0.09 at alpha=0.0500 (have 5 independent units, need 32)
- **0.10** — only 5 independent units; need >= 29 clean units to certify FPR<=0.1 at alpha=0.0500 (have 5 independent units, need 29)
- **0.11** — only 5 independent units; need >= 26 clean units to certify FPR<=0.11 at alpha=0.0500 (have 5 independent units, need 26)
- **0.12** — only 5 independent units; need >= 24 clean units to certify FPR<=0.12 at alpha=0.0500 (have 5 independent units, need 24)
- **0.13** — only 5 independent units; need >= 22 clean units to certify FPR<=0.13 at alpha=0.0500 (have 5 independent units, need 22)
- **0.14** — only 5 independent units; need >= 20 clean units to certify FPR<=0.14 at alpha=0.0500 (have 5 independent units, need 20)
- **0.15** — only 5 independent units; need >= 19 clean units to certify FPR<=0.15 at alpha=0.0500 (have 5 independent units, need 19)
- **0.16** — only 5 independent units; need >= 18 clean units to certify FPR<=0.16 at alpha=0.0500 (have 5 independent units, need 18)
- **0.17** — only 5 independent units; need >= 17 clean units to certify FPR<=0.17 at alpha=0.0500 (have 5 independent units, need 17)
- **0.18** — only 5 independent units; need >= 16 clean units to certify FPR<=0.18 at alpha=0.0500 (have 5 independent units, need 16)
- **0.19** — only 5 independent units; need >= 15 clean units to certify FPR<=0.19 at alpha=0.0500 (have 5 independent units, need 15)
- **0.20** — only 5 independent units; need >= 14 clean units to certify FPR<=0.2 at alpha=0.0500 (have 5 independent units, need 14)

## The shipped operating point, for reference

- `None` at threshold 0.500000
- recall 1.0000 [0.9000, 1.0000] (95% CI, n=40)
- precision 0.9459 [0.8649, 1.0000] (95% CI, n=40)
- flag rate 0.9250 [0.8500, 1.0000] (95% CI, n=40)
- lift 1.081 [0.973, 1.081] (95% CI, n=40)

## What this sweep does not establish

The threshold at each grid point is certified on the **same** frozen test split the recall is then measured on. The pipeline's discipline is stricter — selection on validation, test scored once — and only test-split scores are frozen, so that discipline could not be applied here without refitting the probe. `certify_fpr` reads the negatives only, so the positives that determine recall play no part in choosing the threshold; the bias is that the threshold tracks this sample's negative tail rather than the population's. Each recall above is therefore an in-sample figure and is not a warrant.

