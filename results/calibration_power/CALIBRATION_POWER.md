# Calibration power — what deviation is detectable, and at what n

At **n = 600** per split. The estimator is the binomial requirement already used by `assess_calibration`; nothing here is a second implementation.

| budget | smallest detectable at n | meets 10% bar | n for 5% | n for 10% | n for 15% | n for 20% | n for 25% | n for 50% |
|---|---:|:--:|---:|---:|---:|---:|---:|---:|
| `(shipped P-conservative)` (0.05) | 41.0% | no | 30576 | 7987 | 3702 | 2167 | 1441 | 427 |
| `customer_support` (0.10) | 26.7% | no | 14441 | 3761 | 1738 | 1015 | 673 | 196 |
| `internal_knowledge` (0.20) | 17.0% | no | 6374 | 1649 | 756 | 438 | 289 | 81 |
| `decision_support` (0.50) | 8.0% | yes | 1533 | 381 | 167 | 93 | 58 | 12 |

## What this says

The requirement scales as `z^2 p'(1-p') / (p t)^2`. The numerator falls roughly linearly in the budget while the denominator falls as its square, so **halving a flag-rate budget roughly doubles the sample needed** at a fixed relative tolerance. A tight budget is intrinsically expensive to calibrate, and that is a property of the binomial rather than of this detector.

The 1441 figure quoted for this phase is `n_to_detect_deviation(0.05, 0.25)` = 1441 — the sample for a **25%** deviation at the shipped 5% budget. Detecting **10%** there needs 7987, which is more than three times the entire 2400-item corpus.

The expansion itself is not done and needs a GPU: the extracted corpus holds 1280 negatives against D14's target of 1441. `DECISIONS.md` 135.
