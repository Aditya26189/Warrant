# Phase 1 — can any of it be quoted yet?

**Answer: yes, and the number barely moved.** Certifying thresholds on the
validation split and scoring them on test — the discipline `DECISIONS.md` 124
was open about — gives recall **0.6318 [0.5782, 0.6880]** against **0.6462**
in-sample. 124 is closed. The Phase 0 conclusion stands.

**Two of five tasks are not done**, both blocked on resources rather than on
findings: the corpus expansion needs a GPU, and the closed-API matrix needs
provider credentials.

- **Window:** 2026-09-08
- **Range:** `db934b9` → `HEAD`, 13 commits
- **Suite:** 893 at open → 907 at close, no failures at either end
- **Verification:** `verify.py` 40/40 claims (up from 36)
- **Config hash:** unchanged at `533fb74983fcd8af` throughout

---

## 1. What was done

| Task | Status | Outcome |
|---|---|---|
| **T0** provenance + baseline | done | Eight of ten SHAs cited by the Phase 0 report were dangling. Mapping recorded, citations corrected, artifacts regenerated. Test-count guard extended to the Makefile. |
| **T1** frontier | done | Cost axis added to the sweep and to `SWEEP.md`, costed against the budgets `config.yaml` declares. |
| **T2** close 124 | **done** | Out-of-sample sweep in `results/fpr_sweep_oos/`. D13 met by 5.5x. |
| **T3** raise n | **blocked** | Power analysis delivered; the expansion needs activations that do not exist. `DECISIONS.md` 135. |
| **T4** closed-API | **blocked** | No provider credentials. Nothing built, and the logprob finding deliberately not written from memory. `DECISIONS.md` 136. |
| **T5** close-out | done | This report. |

---

## 2. T0 — the provenance repair, which was not a formality

The Phase 0 report cited ten commits. **Eight were unreachable from any ref.**
The authorship rewrite performed after that report was written changed every SHA
in the phase, including `2634d89` and `e76f5e3` — the pair carrying the claim
that the D6 criterion was registered *before* the sweep ran, which is the most
valuable provenance claim in the repository.

The trap is that they still **resolve** locally. Unreferenced objects survive
until `gc`, so `git rev-parse` finds them and reports success; a fresh clone
never had them. The check that tells the truth is
`git merge-base --is-ancestor <sha> HEAD`.

The mapping was reconstructed by tree identity — an authorship rewrite leaves
content untouched, so each old commit has exactly one tree-identical successor,
and every subject matched. Recorded in `DECISIONS.md` 131; entries 121–130 keep
their original `Commit:` fields because that file is append-only.

**The claim survives at new hashes.** `337dc7c` (criterion) is an ancestor of
`e58a43d` (the tree the sweep ran from) and `0b5964b` (the tree the artifacts
came from); author dates 22:11:28 against 22:23:37; all reachable.

Two rules follow, and the second is why T0 existed: cite SHAs sparingly and
check reachability rather than resolution; and rewrite history *before* writing
the documents that cite it, or not at all.

---

## 3. T2 — 124 is closed, and the bias was smaller than feared

**D13, registered before the run:** the dial conclusion survives if
out-of-sample recall at any swept target strictly exceeds **0.1115**, the upper
bound of the shipped point's 95% recall interval.

**Result: 0.6318 [0.5782, 0.6880] at target 0.20.** Met by a factor of five and
a half. Rule 10 does not fire.

Thresholds were certified on the validation split (600 items, 329 negatives) and
metrics measured on test (600 items) — selection on one split, test scored once.

### Three findings, two stronger than the phase expected

**The in-sample figures were not optimistic.** Out-of-sample recall is *higher*
at 16 of 20 targets:

| target | recall in-sample | recall out-of-sample | delta |
|---|---|---|---|
| 0.04 | 0.2274 | 0.2130 | −0.0144 |
| 0.08 | 0.4116 | 0.4332 | +0.0217 |
| 0.12 | 0.5126 | 0.5632 | +0.0505 |
| 0.20 | **0.6462** | **0.6318** | −0.0144 |

The headline moves by 0.0144 and the largest deviation in either direction is
0.05. The winner's curse 124 was open about is real in principle and did not
materialise in the direction feared — as the Phase 0 analysis predicted, since
`certify_fpr` reads the negatives only and the positives that determine recall
play no part in choosing the threshold.

**The certified budget held on unseen data at all 20 targets.** Zero breaches:
at every grid point the FPR measured on test came in at or below the target
certified on validation. The Clopper-Pearson bound was checked out of sample
rather than assumed.

**Lift now holds at 20 of 20, not 19.** Target 0.01 clears the bar out-of-sample
(recall 0.0469) where in-sample it did not (0.0108). That failure was an
artefact of a threshold fitted to that split's own negative tail.

### What licensed running this on CPU

D12 scheduled T2 into a GPU session. It did not need one:
`results/cache-triviaqa-600.npz` was already on disk. The GPU extracts
activations; T2 scores rows already extracted.

The script refuses to proceed unless the probe reproduces the committed
test-split scores **bit-identically** — a probe that scores test differently is
not the pipeline's probe, and nothing certified from it would describe the
shipped system. It reproduces them, max abs diff 0.0.

---

## 4. T1 — what recall costs, against the budgets that actually exist

The brief asked to surface that a 0.385 flag rate routes 38.5% of traffic
"against the 3–5% the architecture assumes". **Neither figure exists in this
repository.** `config.yaml` declares three profiles with real budgets: 0.10,
0.20 and 0.50 (`DECISIONS.md` 132).

That changes the headline in the direction that matters. A 0.385 flag rate is
not 8× an assumed budget — it sits **inside** `decision_support`'s declared 0.50
and breaks the other two.

| target | recall | flag rate | judge calls / 1000 | lift | within budget for |
|---|---|---|---|---|---|
| 0.03 | 0.1516 | 0.0767 | 77 | 1.978 | all three profiles |
| 0.04 | 0.2274 | 0.1150 | 115 | 1.978 | internal_knowledge, decision_support |
| 0.08 | 0.4116 | 0.2183 | 218 | 1.885 | decision_support |
| 0.20 | 0.6462 | 0.3850 | 385 | 1.678 | decision_support |

`customer_support` — the highest-volume profile, tightest latency — caps out at
target 0.03 and recall 0.1516. Reaching 0.6462 costs 38.5% of this envelope and
only `decision_support` admits it. That is the business choice, in the units the
system declares.

**These are envelope figures, not production costs.** Flag rate is measured at
base rate 0.4617; production traffic is nowhere near that. The field is named
`judge_calls_per_1000_on_this_envelope` so it cannot be lifted without its
condition, and a test asserts the bare name is absent from the payload.

---

## 5. T3 — blocked, and the 1441 figure relocated

**D14's n⁻ ≥ 1441 is unreachable from what is extracted.** The entire 2400-item
corpus holds **1280** negatives — 161 short before the train split is even
excluded, and train cannot be certified against because it fits the probe.
Raising n needs activations for items that do not exist. **OPEN**
(`DECISIONS.md` 135).

The half that needs no GPU is delivered — D15 asks for the smallest reliably
detectable calibration deviation, which is a binomial power question:

| budget | detectable at n=600 | n for 10% |
|---|---:|---:|
| 0.05 (shipped) | 41.0% | 7987 |
| 0.10 `customer_support` | 26.7% | 3761 |
| 0.20 `internal_knowledge` | 17.0% | 1649 |
| 0.50 `decision_support` | **8.0%** | 381 |

**D15's 10% bar is already met for `decision_support`** and is out of reach for
the others at any n this project will plausibly extract.

**The 1441 figure is `n_to_detect_deviation(0.05, 0.25)`** — the sample for a
**25%** deviation at the shipped 5% budget, not a 10% one. Detecting 10% there
needs **7987**, more than three times the whole corpus. The table contains 1441
in exactly that cell and a test asserts it does, so the provenance of the number
is checkable rather than asserted.

The requirement scales as `z²·p'(1−p')/(p·t)²`, so halving a budget roughly
doubles the sample needed at fixed relative tolerance. A tight flag-rate budget
is intrinsically expensive to calibrate — a property of the binomial, not of
this detector. Extraction should therefore be sized against the profile whose
calibration gates a deploy, not against 1441 as a round number.

---

## 6. T4 — blocked, and deliberately not written from memory

No provider credentials are configured. **OPEN** (`DECISIONS.md` 136).

The brief calls provider logprob support "a finding worth stating explicitly in
`README.md`". A finding is something measured. Writing *"OpenAI exposes
logprobs, Anthropic does not"* from recollection would put a claim in the README
that traces to nothing in `results/` — the exact failure this repository has
recorded four times (113, 116, 117, 118). Entry 118 settled the rule: *a claim
about a dependency is checkable by running the dependency.*

**Unblocking needs** credentials for one provider that exposes logprobs and one
that does not, so the matrix has both a populated Tier 1 and a recorded
UNAVAILABLE. The spend is small; it is someone's account, so it is the owner's
call.

D17's criterion is registered and unfired. The closed-API question is still
open, and the README says the measured cells assume open-weight access rather
than implying anything about the rest.

---

## 7. What this does not establish

**Out-of-sample within one corpus is not out-of-distribution.** Both splits are
drawn from the same frozen 2400 items, 600 each, one model, no production
traffic. T2 establishes that the threshold does not depend on the items it is
scored against. It does not establish transfer to another corpus. The
long-context transfer set is the nearest thing to that question and is reported
separately.

**The frontier's cost axis is an envelope figure**, per §4.

**Calibration at the shipped 5% budget is not achievable at this corpus size.**
41% is the detectable deviation today and 7987 items would be needed for 10%.
That is worth recognising rather than pursuing.

---

## 8. Open items

| Entry | Status | What would close it |
|---|---|---|
| **135** — corpus expansion | OPEN | GPU extraction of new items; the corpus is 161 negatives short of D14's target before splits. Size it against `internal_knowledge` (1649 items for the 10% bar), which is the cheapest meaningful target. |
| **136** — closed-API matrix | OPEN | Provider credentials for one API that exposes logprobs and one that does not. |

`DECISIONS.md` **124 is CLOSED** by 134 — it was the sole open item entering this
phase.

---

## 9. Ledger

**Code**

| Path | What it is |
|---|---|
| `controlplane/validation/fpr_sweep.py` | `certify_on` for split-separated sweeps; cost axis; two overlap guards |
| `controlplane/report/sweep.py` | frontier section; supersession banner; split provenance line |
| `controlplane/report/plots.py` | `plot_fpr_frontier` |
| `scripts/20_fpr_sweep_oos.py` | the out-of-sample sweep, with the bit-identity gate |
| `scripts/21_calibration_power.py` | the power analysis |
| `tests/test_claims.py` | test-count guard extended to the Makefile |

**Artifacts** — `results/fpr_sweep_oos/` (4 files), `results/calibration_power/`
(2 files), `results/fpr_sweep/frontier.png`, and
`results/scores/valsplit-T1-last_token.json`.

**Decisions** — `DECISIONS.md` 131–136.

**Reproduce**

```bash
python scripts/20_fpr_sweep_oos.py --config config.yaml   # needs the cache
python scripts/21_calibration_power.py --config config.yaml
python scripts/verify.py --no-activations                 # 40/40 claims
python -m pytest tests/ -q                                # 907 tests
```

---

## 10. What this changes

Phase 0 produced a curve nobody could quote. Phase 1 makes it quotable: recall
**0.6318 [0.5782, 0.6880]** at a 0.20 FPR budget, certified on one split and
measured on another, with the certified bound holding on unseen data at every
point on the grid.

What it also does is price the curve. Recall 0.6318 costs 38.5% of this envelope
routed to the expensive check, which only the loosest declared profile admits.
The honest sentence for a buyer is not "recall 0.63" — it is *"at your
false-positive budget, this is the recall, this is the interval, and this is the
share of your traffic it sends to a judge."*

Two things remain unmeasured and both are known: whether the numbers hold on a
different corpus, and whether any of it works without open weights. Neither is
hidden, and neither has been guessed at.
