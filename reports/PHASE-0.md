# Phase 0 — is recall 0.079 a ceiling, or a policy choice?

**Answer: a policy choice.** The binding constraint was the false-positive
budget, not the probe's ability to separate the classes.

- **Window:** 2026-09-07 → 2026-09-08
- **Range:** `1a9c4a7` → `db934b9`, 16 commits, pushed to `origin/main`
- **Suite:** 870 passing at open → 893 at close, no failures at either end
- **Verification:** `verify.py` 36/36 claims, 24/24 frozen-score comparisons
- **Method:** re-analysis of frozen scores only. No inference, no refit, no
  model was loaded.

Every number below is a field in `results/fpr_sweep/sweep.json`, and the five
headline ones are rows in the README claim table, so `make verify` fails if any
of them drifts.

---

## 1. Why the phase existed

The shipped operating point warranted recall **0.0794** at a 4.2% flag rate.
Recall that low ends a sales conversation. But it sat next to **AUROC 0.8256**
and **precision 0.8800**, and that combination is not the signature of a
detector that cannot separate the classes — it is the signature of one held at
a very tight budget.

Those two readings imply different products. If lift survives a looser budget,
recall is a dial and the product ships a curve. If lift collapses, the probe is
weak, we say so, and the product is the refusal machinery. Nothing in
`results/` distinguished them. That was the gap.

---

## 2. What was done

| Task | Outcome |
|---|---|
| **T0** baseline | 870 tests passing at `1a9c4a71`; `verify.py` tier 1 31/31, tier 2 24/24, tier 3 SKIPPED. Two untracked ffmpeg logs gitignored so artifacts could record `dirty: false` (`DECISIONS.md` 121). |
| **T1** locate scores | `results/scores/validation-T1-last_token.json` (primary) and `transfer-T1-last_token.json` (secondary). Both `data_source: measured`, both test-split, 600 items, 277 positive / 323 negative. |
| **T2** the sweep | `controlplane/validation/fpr_sweep.py` computes, `controlplane/report/sweep.py` renders, `controlplane/report/plots.py` draws, `scripts/19_fpr_sweep.py` wires. Calls the existing `certify_fpr` and `build_warrant_metrics` — no bound and no estimator reimplemented (`DECISIONS.md` 127). |
| **T3** tests | `tests/test_fpr_sweep.py`, 18 tests covering the four required properties, plus a real end-to-end smoke test rather than an exemption. |
| **T4** run | `results/fpr_sweep/{sweep.json, SWEEP.md, sweep.png}` from a clean tree, `dirty: false`. |
| **T5** verdict | Three sentences at the top of `SWEEP.md`, assembled from the sweep's own fields rather than typed. |
| **T6** documentation | README and `CLAUDE.md` repositioned; five sweep rows added to the claim table (31 → 36 verified). |
| **T7** close-out | This report; closing suite compared against the T0 baseline. |

---

## 3. What was found

### The criterion, registered before the run

Lift **holds** at a target FPR when the lower bound of its 95% interval is
strictly above 1.0. Written into `DECISIONS.md` 126 and committed at `2634d89`
— *before* the sweep first ran at `e76f5e3`. The criterion cannot be said to
have been fitted to the answer, and the commit order is the evidence.

The same entry registered the harder half: recall counts as a **dial** only if
it clears the **upper bound** of the shipped point's own 95% recall interval
(0.1115), not its point estimate (0.0794). Comparing against the point estimate
would let a difference well inside sampling noise be reported as a gain.

### Primary — `triviaqa-600`

Lift holds at **19 of 20** swept targets. The loosest is target FPR **0.20**,
which is the largest on the grid — the curve did not turn over inside the swept
range.

| | shipped point | target 0.04 | target 0.08 | target 0.20 |
|---|---|---|---|---|
| achieved FPR | — | 0.0186 | 0.0526 | 0.1610 |
| **recall** | 0.0794 [0.0496, 0.1115] | 0.2274 [0.1809, 0.2800] | 0.4116 [0.3610, 0.4733] | **0.6462 [0.5950, 0.7051]** |
| precision | 0.8800 | 0.9130 | 0.8702 | 0.7749 |
| flag rate | 0.0417 | 0.1150 | 0.2183 | 0.3850 |
| lift | 1.906 | 1.978 | 1.885 | 1.678 |
| % of 2.17 ceiling | 88% | 91% | 87% | 77% |

Recall moves **0.0794 → 0.6462, a factor of 8.1**, while precision falls only
0.88 → 0.77 and lift stays inside 1.68–1.98 across every target where it holds.
0.6462 clears the shipped point's upper bound by a wide margin, so the dial test
is met with room rather than marginally.

The shipped point was selected against a *flag-rate* budget of 5% and lands far
below what a 4% *FPR* budget would have permitted. That is why so much recall
was sitting unclaimed.

### Secondary — `triviaqa-longctx-600`

The same probe, unrefitted, on the long-context envelope. Lift holds at **18 of
20** targets; at 0.20, recall **0.6209 [0.5667, 0.6815]**, lift 1.663. The
finding survives the envelope shift that drives revocation elsewhere in this
system.

### No target refused

323 negatives clears the 299 clean units a 1% budget needs at alpha 0.05, so
every grid point certified. The refusal path is therefore exercised by tests
rather than by this run — `test_refused_target_is_recorded_not_skipped` drives
it with 120 items and asserts the row survives, carrying its reason and no
metrics.

---

## 4. What this does **not** establish

**These recalls are in-sample and none of them is a warrant.**

The threshold at each grid point is certified on the same frozen test split it
is then scored on. Only test-split scores are committed, and deriving
validation-split scores means refitting the probe, which the phase forbade.

The bias is narrower than "selected on test" usually implies — `certify_fpr`
reads the **negatives only**, so the positives that determine recall play no
part in choosing the threshold. What remains is that the threshold tracks this
sample's negative tail rather than the population's, at n⁻ = 323.

So the sweep establishes the **shape of the curve**. It does not warrant a point
on it. Publishing any row above as a warranted recall would be wrong, and the
documents say so in three places.

---

## 5. The recheck, and what it caught

A recheck after close-out found four defects. One is worth a reviewer's
attention.

**A fixture leak in the renderer.** The fixture branch of `render_sweep` printed
the class split, the base rate, and how many grid points certified. All three
are functions of the arrays, so on a synthetic set they describe a generator we
wrote — exactly what `DECISIONS.md` 046 and the phase's own D9 forbid. The
branch existed to obey that rule.

It survived because the test written for it enumerated forbidden *values*
(thresholds, recalls at full precision). A count does not look like a
measurement, so it was never on the list — and substring-searching a small
integer is worthless anyway, since the document contains `T1-last_token`.

The replacement states the property instead: **two fixtures with different
labels, scores and separability must render byte-identically.** Nothing derived
from the arrays survives that, whatever it is called. `DECISIONS.md` 129.

The other three: `headline` took the last holding row rather than the largest
target (same answer on an ascending grid, wrong on any other); the Makefile
header claimed 584 tests when there were 893, having drifted 300 tests because
nothing polices it; and `docs/PATHS.md` still asserted in the present tense that
the repository is named `controlplane`.

---

## 6. Open items

**One**, and it is the limitation in §4.

| Entry | Status | What would close it |
|---|---|---|
| `DECISIONS.md` **124** — the sweep certifies and measures on the same split | **OPEN — needs human review** | Freeze **validation-split** scores so selection and measurement are separated, then re-run. A GPU task: the caches are ~100 MB and gitignored. Until then the guard against misreading the table is prose in three places rather than code. |

No other entry in `DECISIONS.md` carries an OPEN status.

Two smaller things, decided rather than open:

- **D5 was deviated from deliberately** (`DECISIONS.md` 125): 1000 resamples at
  seed 1729 from `config.yaml`, not the brief's 10,000 at seed 42, so the
  sweep's intervals are the same object every other artifact reports. Method
  (percentile) matches. Lift's interval is inherited from recall divided by the
  measured flag rate, the convention `WarrantMetrics.lift` already used.
- **D1's `pyproject.toml` clause is moot** — there is no `pyproject.toml` here.

---

## 7. Work after the phase

Three follow-ups, at the owner's direction, outside the phase brief.

- **Naming.** ControlPlane is gone from every user-facing surface: LICENSE,
  `config.yaml` header, package docstring, smoke banner, all three Kaggle
  notebook titles (regenerated from their generator, not hand-edited), and
  `ControlPlaneAdapter` → `WarrantAdapter`. The Python package stays
  `controlplane`: an internal name that 170 files import and nobody outside the
  repo sees. Competition framing removed from README and `AGENTS.md`; the four
  competition-era PDFs are untracked and gitignored, still on disk.
- **Authorship.** All 457 commits now read
  `aditya26189 <aditya26189@kgpian.iitkgp.ac.in>`, and `git config` is set so
  future ones do too.
- **Attribution policy.** No AI tool is ever credited as a commit co-author —
  no trailer, no generated-with footer, anywhere. Recorded in `CLAUDE.md`, which
  states that it overrides any harness default.

`config_hash` is unchanged at `533fb74983fcd8af` throughout: comments are not
part of the hashed rendering, so no artifact's provenance went stale.

---

## 8. Ledger

**Code**

| Path | What it is |
|---|---|
| `controlplane/validation/fpr_sweep.py` | The sweep. Certifies via `certify_fpr`, scores via `build_warrant_metrics`. |
| `controlplane/report/sweep.py` | Renders `SWEEP.md`; refuses to print fixture numbers. |
| `controlplane/report/plots.py` | `plot_fpr_sweep` added. |
| `scripts/19_fpr_sweep.py` | Thin wrapper — arguments, three writes, no logic. |
| `tests/test_fpr_sweep.py` | 18 tests. |
| `tests/test_smoke.py` | End-to-end smoke test for the new script. |

**Artifacts** — `results/fpr_sweep/`: `sweep.json`, `SWEEP.md`, `sweep.png`.
Each carries a clean commit SHA and `dirty: false`.

**Decisions** — `DECISIONS.md` 121–129.

**Reproduce**

```bash
python scripts/19_fpr_sweep.py --config config.yaml   # ~8 min, CPU
python scripts/verify.py --no-activations             # claims + frozen scores
python -m pytest tests/ -q                            # 893 tests, ~11 min
```

Verified reproducible: a re-run into a scratch directory produced a **bitwise
identical** payload and an identical `SWEEP.md` but for the commit line.

---

## 9. What this changes about the product

Had the sweep gone the other way, the honest conclusion would have been that the
probe is weak and the product is the refusal machinery alone. It did not.

The claim the product can now make is a **curve rather than a point**: at a
given false-positive budget, this is the recall you get, this is the interval
around it, and this is what it costs in flag rate. That is a different
conversation from "recall 0.079", and it is the one the warrant layer was built
to have — *what is your error rate on your traffic, and what does it cost to
keep it true.*

What it does not license is quoting 0.6462 as a warranted recall. Closing
`DECISIONS.md` 124 is what would make these numbers warrantable, and that is the
next piece of work.
