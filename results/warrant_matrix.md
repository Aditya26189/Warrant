| detector | triviaqa-600-synthetic | triviaqa-longctx-600-synthetic | hinglish-pii-200 | hinglish-pii-200-longctx | hard-negatives-200 | triviaqa-600 | triviaqa-longctx-600 |
|---|---|---|---|---|---|---|---|
| pii-reference | UNVALIDATED | UNVALIDATED | VALID R=0.79 [0.70, 0.88] P=0.65 [0.51, 0.81] @f=0.620 | VALID R=0.79 [0.70, 0.88] P=0.65 [0.51, 0.81] @f=0.620 | VALID FPR=0.000 [0.000, 0.015] | UNVALIDATED | UNVALIDATED |
| probe-T1-max_rolling_means | VALID · FIXTURE — NOT MEASURED | VALID · FIXTURE — NOT MEASURED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED |
| probe-T1-mean_pool | VALID · FIXTURE — NOT MEASURED | REFUSED · FIXTURE — NOT MEASURED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED |
| probe-T2-logprob | VALID · FIXTURE — NOT MEASURED | VALID · FIXTURE — NOT MEASURED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED |
| probe-T3-judge | VALID · FIXTURE — NOT MEASURED | REFUSED · FIXTURE — NOT MEASURED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED |
| probe-qwen2.5-7b-instruct-T1-last_token | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | VALID R=0.08 [0.05, 0.11] P=0.88 [0.75, 1.00] @f=0.042 · CAL:unresolved (±25%) | VALID R=0.13 [0.09, 0.17] P=0.90 [0.79, 0.98] @f=0.065 · CAL:unresolved (±25%) |
| probe-qwen2.5-7b-instruct-T1-max_rolling_means | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | VALID R=0.08 [0.05, 0.12] P=0.92 [0.80, 1.00] @f=0.042 · CAL:unresolved (±25%) | **REFUSED** |
| probe-qwen2.5-7b-instruct-T1-mean_pool | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | UNVALIDATED | VALID R=0.08 [0.05, 0.11] P=0.92 [0.79, 1.00] @f=0.040 · CAL:unresolved (±25%) | **REFUSED** |

Cell states: VALID 13, REFUSED 4, UNVALIDATED 39. 39 of 56 cells have never been measured, which is the expected shape: UNVALIDATED is the modal state in production.
