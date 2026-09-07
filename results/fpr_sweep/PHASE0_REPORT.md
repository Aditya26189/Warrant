# Phase 0 — what was done, what was found, what is still open

**Question.** Is recall 0.079 a ceiling, or a policy choice?

**Answer.** A policy choice. The binding constraint was the false-positive
budget, not the probe's ability to separate the classes.

Every number below is in `sweep.json`, and the five headline ones are rows in
the README claim table, so `make verify` fails if any of them drifts.

---

## What was done

Re-analysis of frozen scores only. No inference, no refit, no model was loaded.
The inputs are the committed arrays in `results/scores/`, which is the same
footing `make verify`'s second tier stands on.

| Task | Outcome |
|---|---|
| T0 baseline | 870 tests passed at `1a9c4a71`; `verify.py` tier 1 31/31, tier 2 24/24, tier 3 SKIPPED. Two untracked ffmpeg logs gitignored so artifacts could be clean (`DECISIONS.md` 121). |
| T1 locate scores | `results/scores/validation-T1-last_token.json` (primary) and `transfer-T1-last_token.json` (secondary). Both `data_source: measured`, both test-split, 600 items, 277 positive / 323 negative. |
| T2 the sweep | `controlplane/validation/fpr_sweep.py` computes it, `controlplane/report/sweep.py` renders it, `scripts/19_fpr_sweep.py` wires it. Calls the existing `certify_fpr` and `build_warrant_metrics`; no bound and no estimator reimplemented (127). |
| T3 tests | `tests/test_fpr_sweep.py`, 17 tests covering the four required properties, plus a real end-to-end smoke test in `tests/test_smoke.py`. |
| T4 run | `results/fpr_sweep/{sweep.json, SWEEP.md, sweep.png}`, produced from a clean tree at commit `e76f5e3d`, `dirty: false`. |
| T5 verdict | Three sentences at the top of `SWEEP.md`, assembled from the sweep's own fields rather than typed. |
| T6 documentation | README and CLAUDE.md renamed to Warrant and repositioned; five sweep rows added to the claim table (31 → 36 verified). |
| T7 close-out | This document; closing suite compared against the T0 baseline. |

---

## What was found

**The pre-registered criterion (D6, `DECISIONS.md` 126).** Lift *holds* at a
target FPR when the lower bound of its 95% interval is strictly above 1.0.
Registered before the sweep ran and not adjusted afterwards.

### Primary — `triviaqa-600`

Lift holds at **19 of 20** swept targets. The loosest is a target FPR of
**0.20**, and it is the largest on the grid — the curve did not turn over
inside the swept range.

| | shipped point | target FPR 0.04 | target FPR 0.08 | target FPR 0.20 |
|---|---|---|---|---|
| achieved FPR | — | 0.0186 | 0.0526 | 0.1610 |
| recall | 0.0794 [0.0496, 0.1115] | 0.2274 [0.1809, 0.2800] | 0.4116 [0.3610, 0.4733] | **0.6462 [0.5950, 0.7051]** |
| precision | 0.8800 | 0.9130 | 0.8702 | 0.7749 |
| flag rate | 0.0417 | 0.1150 | 0.2183 | 0.3850 |
| lift | 1.906 | 1.978 | 1.885 | 1.678 |
| % of the 2.17 ceiling | 88% | 91% | 87% | 77% |

Recall moves **0.0794 → 0.6462, a factor of 8.1**, while precision falls only
0.88 → 0.77 and lift never leaves the band 1.68–1.98. Under the rule registered
in 126, recall counts as a **dial** because 0.6462 clears the upper bound of the
shipped point's own interval (0.1115) by a wide margin — not merely its point
estimate.

This is what AUROC 0.8256 beside precision 0.8800 implied: a detector with real
separating power, held at a very tight budget. The shipped operating point was
selected against a *flag-rate* budget of 5% and lands at an achieved FPR far
below what a 4% FPR budget would have permitted, which is why so much recall was
sitting unclaimed.

### Secondary — `triviaqa-longctx-600`

The same probe, unrefitted, on the long-context envelope. Lift holds at **18 of
20** targets; at 0.20, recall **0.6209 [0.5667, 0.6815]**, lift 1.663. The
finding survives the envelope shift that drives revocation elsewhere in this
system.

### No target was refused

323 negatives clears the 299 clean units a 1% budget needs at alpha 0.05, so
every point on the grid certified. The refusal path is therefore exercised by
tests rather than by this run — `test_refused_target_is_recorded_not_skipped`
drives it with 120 items and asserts the row survives with its reason and no
metrics attached.

---

## What this does **not** establish

**These recalls are in-sample and none of them is a warrant.** The threshold at
each grid point is certified on the same frozen test split it is then scored on,
because only test-split scores are committed and deriving validation-split
scores means refitting the probe, which Phase 0 forbids.

The bias is narrower than "selected on test" usually implies — `certify_fpr`
reads the **negatives only**, so the positives that determine recall play no
part in choosing the threshold — but the threshold still tracks this sample's
negative tail rather than the population's, at n⁻ = 323.

So the sweep establishes the **shape of the curve**. It does not warrant a point
on it. Publishing any row above as a warranted recall would be wrong.

---

## Open items requiring human review

**One**, and it is the item above.

| Entry | Status | What is needed |
|---|---|---|
| `DECISIONS.md` **124** — the sweep certifies and measures on the same split | OPEN — needs human review | Freeze **validation-split** scores so selection and measurement can be separated, then re-run. That is a GPU task (the caches are gitignored and ~100 MB) and was out of scope here. Until then the guard against misreading the table is prose in three places rather than code. |

No other entry in `DECISIONS.md` carries an OPEN status.

### Two smaller notes, decided rather than open

- **D5 was deviated from deliberately** (125): 1000 resamples at seed 1729 from
  `config.yaml`, not the brief's 10,000 at seed 42, so the sweep's intervals are
  the same object every other artifact in `results/` reports. Method
  (percentile) matches. Lift's interval is inherited from recall divided by the
  measured flag rate, which is the convention `WarrantMetrics.lift` already
  used.
- **D1's `pyproject.toml` clause is moot** — there is no `pyproject.toml` in
  this repository. The rest of D1 was applied: README, CLAUDE.md, the Makefile
  header and the single `ControlPlane` mention in `docs/DEMO.md`. Every
  `controlplane/` path reference is untouched, because those name the package.

---

## What this changes about the product

If the sweep had gone the other way, the honest conclusion would have been that
the probe is weak and the product is the refusal machinery alone. It did not.

The claim the product can now make is a **curve rather than a point**: at a
given false-positive budget, this is the recall you get, this is the interval
around it, and this is what it costs in flag rate. That is a materially
different conversation from "recall 0.079", and it is the same conversation the
warrant layer was built to have — *what is your error rate on your traffic, and
what does it cost to keep it true.*

What it does **not** license is quoting 0.6462 as a warranted recall. Closing
124 is what would make these numbers warrantable, and that is the next piece of
work.
