# METHODS.md — estimators, bootstraps, bands, and where they came from

<sub>[🏠 Project README](../README.md) · [📚 Documentation index](README.md) · [📖 Glossary](GLOSSARY.md) · [⚠️ Limitations](LIMITATIONS.md)</sub>

Every number in [README.md](../README.md) is produced by one of the estimators
below. This says which, why, and what each one assumes.

The recurring theme: **the closed forms were wrong here, and the fix was to
measure the null rather than to look it up.** Three separate times.

**Part I, the measurement pipeline:** [1 Resampling](#1-resampling) ·
[2 Intervals](#2-what-carries-an-interval-and-what-does-not) ·
[3 Control bands](#3-the-negative-control-band-measured-three-times) ·
[4 Drift false alarms](#4-the-drift-monitors-false-alarm-rate-same-story) ·
[5 Lift](#5-lift-and-its-ceiling) · [6 Threshold selection](#6-threshold-selection-and-the-interval-that-ignores-it) ·
[7 Paired comparison](#7-comparing-two-models-pair-on-what-both-held-out) ·
[8 Power](#8-power-computed-against-what-matters) · [9 Single-class](#9-single-class-envelopes) ·
[10 Labels](#10-labels) · [11 Reproducibility](#11-reproducibility)

**Part II, the customer path and release:** [12 Certification](#12-certification-the-lowest-threshold-whose-exact-bound-clears-the-budget) ·
[13 The frontier](#13-the-frontier-and-the-cost-of-choosing-from-it) ·
[14 Recheck](#14-recheck-revoke-on-evidence-of-breach) ·
[15 Sizing a recheck](#15-sizing-a-recheck-by-power-not-by-a-single-sufficient-count) ·
[16 The chain](#16-the-chain-one-sequential-test-over-a-declared-horizon) ·
[17 Label error](#17-label-error-exact-ladders-and-a-second-reviewer) ·
[18 Recall on traffic](#18-recall-on-traffic-sizing-through-the-derivative) ·
[19 Release](#19-release-evidence-one-fixed-threshold-simultaneous-intervals)

---

## 1. Resampling

**Bootstrap-percentile, 1000 resamples for validation runs, 2000 for the
paired comparison, seed 1729, resampled over `question_id` rather than over
rows.**

Resampling rows would break the group structure: TriviaQA ships several items
per question, so a row-level bootstrap treats correlated items as independent
and produces intervals that are too narrow. Every split in this project is by
question, deduplicated on the normalised question string first, with zero
overlap asserted between splits.

Percentile rather than BCa: BCa's acceleration term is estimated by jackknife,
which at n=600 over groups is itself noisy, and the correction was smaller than
its own uncertainty when checked.

`controlplane/validation/stats.py`

---

## 2. What carries an interval, and what does not

Two axes that are easy to conflate.

| | `EXACT` | `ESTIMATED` |
|---|---|---|
| means | a count of reviewed, confirmed items | a rate, i.e. a claim about a process |
| interval | **refused** — construction fails if one is supplied | **required** — construction fails without one |
| examples | `confirmed_errors` | `auroc`, `recall`, `precision`, `flag_rate` |

**Free** is a third and separate axis: it is a statement about *label cost* and
lives in the price list, not in the type. Precision is free *and* estimated —
free because the flagged pool is reviewed anyway, estimated because the flagged
pool is a finite sample of the traffic distribution and next month's precision
is a forward claim.

`DECISIONS.md` 022. `Metric.__post_init__` enforces both directions.

---

## 3. The negative-control band, measured three times

A negative control asserts *"AUROC is consistent with 0.5"*. Whether an
observed value is consistent with 0.5 depends on sampling noise, so a **fixed**
`[0.45, 0.55]` band is only a valid test at one holdout size.

**First attempt** — scale the band by the Hanley–McNeil null standard error.
That model said 5 repeats made the band a ±3.45 SE bar at n=600. Label-shuffle
then failed at 0.5546 on the second run. Three-sigma events do not happen on
the second run, so **the model was wrong.**

**Why it was wrong.** Hanley–McNeil assumes exchangeable scores under the null.
A *fitted* probe's scores are not: the fit itself induces structure that
survives label permutation. Measured over 200 permutations per variant **on the
synthetic fixture**, the true spread exceeded the closed-form SE by **2.1x at
d=32 and 8.3x at d=1**. On the real T1 probes (d=3,584, holdout 600) it is
**0.7–1.0x** and every negative control resolves at the 8-repeat minimum
(`results/validation-T1-*.json`), so the closed form would not have understated
anything there. The measured spread stays the reference: it is free, and the
low-dimensional case it guards has no real instance yet. `DECISIONS.md` 169.

**What is used.** Each control simulates its own null at construction —
between 8 and 200 repeats, sized from the *measured* spread — and reports the
band it actually applied and why. It passes only if the mean lies inside the
band **and** the standard error of that mean is at most half the band's
half-width; a control that cannot get there within the cap fails as
underpowered. There is no ±2 SE floor — entry 029 proposed one and 031 retired
it.

`DECISIONS.md` 029, 031.

---

## 4. The drift monitor's false-alarm rate, same story

PSI's 0.10 / 0.25 bands are credit-scoring rules of thumb quoted without their
sample size, and they are not scale-free: the null grows as `(k-1)/n`, so the
same band means different things at different bin counts and window sizes.

The monitor simulates its own null at construction and **refuses a
configuration** whose STABLE-window false-alarm rate would exceed 5%. A
threshold that fires on 30% of stable windows is not a monitor; it is noise
with a dashboard.

`DECISIONS.md` 070. `controlplane/drift/psi.py`, `null_band.py`

---

## 5. Lift, and its ceiling

```
lift = R / f = precision / base_rate
```

`f` is always the **measured** test-set flag rate, never the target the
threshold was aimed at. On test the realised rate differs from the budget, and
every downstream figure uses the realised one.

Because precision ≤ 1, lift is capped at `1 / base_rate`. That ceiling is
reported beside every lift figure, because a lift of 1.9 means something very
different at a ceiling of 2.17 (88% of attainable) than at a ceiling of 10.

A warrant is refused when the **lift lower bound does not exceed 1.0** — that
is, when the evidence cannot show the detector beats random sampling at the
same budget. `DECISIONS.md` 043.

---

## 6. Threshold selection, and the interval that ignores it

Thresholds are selected on **validation** to hit a declared flag-rate budget,
and reported on **test**. Test is never consulted by any selection.

The published recall interval is **conditional on that threshold** — it treats
as fixed a quantity that was itself estimated, sometimes from very few items.
At the `customer_support` budget the threshold is determined by **5 negatives**
in a 480-item validation split.

Propagating the selection noise widens the recall bound by **1.36x to 1.59x**.
Both are computed and both are in `results/paired_comparison.json`; the claim
table quotes the conditional interval, which is what the artifact's `metrics`
block holds, and gives the widening its own row rather than burying it.

`DECISIONS.md` 083. See [LIMITATIONS.md](LIMITATIONS.md) §2.2.

---

## 7. Comparing two models: pair on what both held out

The trap, and this project fell into it once and published the result.

Commit `67167ed` compared AUROC 0.8256 on a 600-item test set against 0.8232 on
a 960-item one and concluded the training reduction "cost nothing measurable".
**Training size and evaluation sample both changed between those numbers**, so
the difference is unattributable and the narrower interval is a test-n effect
that says nothing about training size.

The correct comparison pairs the two models on the **600 items both held out**
and bootstraps the *difference*, resampling the pairing. It found the opposite:
the reduction cost **0.0110 AUROC [0.0026, 0.0200]**, an interval excluding
zero.

The three warranted recalls were **underpowered** at that n — minimum
detectable difference 0.034 to 0.043 — and are reported as underpowered rather
than as no difference. An interval containing zero is not evidence of no
effect; it is evidence the sample could not resolve one.

`DECISIONS.md` 081. `controlplane/validation/paired.py`

---

## 8. Power, computed against what matters

Power is measured against the **declared tolerance**, not against whatever
deviation happened to be observed. An estimate landing near its target needs an
enormous n to be distinguished from it — which says nothing about whether the
sample could have caught a deviation that mattered.

At a 25% calibration tolerance, separating a real deviation from the budget
needs **n ≥ 1441**. Measured at n = 600 to 960, so every budget claim is
refused or unresolved, and each says which.

`DECISIONS.md` 069.

---

## 9. Single-class envelopes

`hard-negatives-200` is all negatives. AUROC, recall and precision are
**undefined** on it, and the warrant claims an FPR only — with an exact
binomial interval, since the bootstrap of a zero-variance statistic is
degenerate. `pii-reference` measures FPR 0.0000 [0.0000, 0.0183] there.

The metric builder detects the single-class case and refuses to emit the
undefined quantities rather than emitting a plausible-looking 0.5.

---

## 10. Labels

**Correctness**: TriviaQA alias matching against greedy generations. Aliases
shorter than 3 characters require an exact token match rather than substring
containment — a gold alias of `"US"` appears inside thousands of unrelated
generations, and substring matching would inflate the correct rate silently.

**PII**: construction-time. The identifiers are synthetic and the label is
known when the item is built, so there is no annotation noise — and equally, no
independent check that the labels mean what we think.

**No human labelling was done.** Cohen's κ (`sampling/agreement.py`), the
blinded review queue (`sampling/queue.py`) and a second reviewer's `label_2` on the
customer path (§17) are built, and none has been run on human labels. What this
project measured instead is its own lenient matching rule against a strict one,
as two labellers of the same responses ([LIMITATIONS.md](LIMITATIONS.md) §3.6,
`DECISIONS.md` 199).

---

## 11. Reproducibility

`random`, `numpy` and `torch` are seeded from `config.yaml` (seed 1729). Every
artifact records the resolved config, a SHA-256 config hash, the git commit, a
dirty flag, library versions and the device.

The `determinism` control asserts two runs at one seed are bit-identical, and
`make verify` re-derives the frozen-set validation from cached activations and
compares field by field — all three probe variants currently reproduce
bit-identically.

The **dirty flag** excludes `results/` and nothing else, because the pipeline
writes its own artifacts there and a bare `git status --porcelain` would mark
every stage after the first as dirty regardless of the code.

---

# Part II — the customer path and release

Everything below runs on a file a customer supplies, with no model and no GPU.
Code is under `controlplane/intake/`, `economics/`, `sampling/` and `release/`.

## 12. Certification: the lowest threshold whose exact bound clears the budget

**Quantity.** An upper bound on the false-positive rate at a threshold, at
confidence `1 - alpha`, over **independent negative units**: items, or groups on a
grouped file.

**Estimator.** With `k` negatives at or above the threshold out of `n`, the
one-sided Clopper-Pearson upper bound is the `1 - alpha` quantile of
`Beta(k+1, n-k)`, and `1 - alpha^(1/n)` when `k = 0`. It covers at least `1 - alpha`
for every true rate. `certify` walks candidate thresholds from lowest to highest,
each just above an observed negative score, and returns the first whose bound is
at most the budget `B`: the most recall the promise allows.

**Why the sweep needs no multiplicity correction.** The bound is non-increasing in
the threshold, so the certifying thresholds form an upper set, and returning its
infimum is one coverage event at one fixed (unknown) threshold, not a search over
many hypotheses. The coverage was checked empirically below nominal
(`controlplane/validation/warrant_stats.py`).

**The floor.** With no false positive at all, the bound is `1 - alpha^(1/n)`, which
clears `B` only when

```
n >= ceil( log(alpha) / log(1 - B) )
```

Below that, every threshold refuses, whatever the detector does. At `alpha = 0.05`
this is 59 units for a 5% budget and 299 for 1% ([INPUT.md](INPUT.md)).

**Groups.** On a grouped file a group counts as a false positive when any member
fires. That bound dominates the item-level rate **only when groups are equal in
size**; with unequal sizes one large all-firing group among many silent
singletons makes it anticonservative, so unequal groups are refused. Metric
intervals on a grouped file bootstrap over groups.

**The consequence.** The next lower threshold does not certify, so every
certificate sits at the edge of its budget and is sensitive to label error (§17).

`controlplane/validation/warrant_stats.py` (`cp_upper`, `min_n_for`, `certify_fpr`),
`controlplane/intake/certify.py`.

## 13. The frontier, and the cost of choosing from it

`certify --frontier` certifies every budget on a grid and reports exact counts, no
rates, so it needs no bootstrap. Each row is certified at

```
row_alpha = alpha / |grid|
```

a Bonferroni split, so that all rows hold together at the family level `alpha`.
**The split was measured before it was adopted**: reading the frontier and then
picking a budget is a selection, and the study behind the choice asked how wrong
the picked row is without it (`DECISIONS.md` 192, `results/frontier_selection/`).
`certify --from-frontier` then certifies the picked budget at `row_alpha`, so the
promise survives the choice (195). Later rechecks, plans and chains of that
warrant run at the family `alpha`, because they select nothing.

`controlplane/intake/frontier.py`, `selection.py`.

## 14. Recheck: revoke on evidence of breach

**Two checks, kept apart.** A recheck reports the false-positive bound and the
score distribution separately, because a broken bound and a moved distribution
call for different actions. A broken bound outranks a moved distribution.

**The bound.** At the warrant's threshold, on the new file's `k` of `n` negative
units:

| Condition | Status |
|---|---|
| no negatives | `UNVALIDATED`: nothing was tested |
| the one-sided Clopper-Pearson **lower** bound, the `alpha` quantile of `Beta(k, n-k+1)`, exceeds `B` | `REVOKED`: the data establishes a breach |
| observed rate `k/n` above `B`, lower bound not above it | `STALE` |
| otherwise | the distribution check decides |

**Why the lower bound.** Certification puts the true rate close to the budget
(§12). A recheck that revoked whenever the upper bound missed the budget would
revoke detectors that kept their promise. Revocation needs evidence of breach;
failing to re-prove the promise is not that (`DECISIONS.md` 143).

**The dead zone, stated with every verdict.** The *detection floor* is the
smallest observed rate whose lower bound clears `B`, found by exact search over
integer `k`. Between `B` and the floor, a real breach returns `VALID`. Worked
example from the code: at 591 negatives and a 5% budget, the lower bound first
clears at `k = 40`, an observed 6.8%.

**The distribution.** PSI over ten bins of the warrant's stored score histogram,
judged against a **null band simulated at both sample sizes** -- this file's, and
the one the reference was built from (`DECISIONS.md` 070, 209) -- not against the
0.10 / 0.25 folklore alone. The reference's own estimation error is part of the
null: a reference of a hundred items is noisy, and a band that assumed it was as
large as the new file was far too narrow. The recheck record names the reference
size it used, or says the warrant did not record one.

| Condition | Status |
|---|---|
| fewer than 200 items | not assessed, and the verdict says so |
| most of the index comes from bins the new file left empty | `STALE`: missing data, not a measured shift |
| PSI at or above the significant band **and** beyond the null's 95th percentile | `REVOKED` |
| PSI at or above the stable band **and** beyond the noise | `STALE` |

The empty-bin rule exists because the smoothing epsilon sets such a PSI's size:
one empty bin contributes about 13 at `1e-6` and about 9 at `1e-4`. Where that
epsilon lives is an open item ([LIMITATIONS.md](LIMITATIONS.md) §4.4).

`controlplane/intake/recheck.py`.

## 15. Sizing a recheck by power, not by a single sufficient count

**Quantity.** The number of clean negatives at which a recheck revokes a detector
whose **true** false-positive rate is a breach rate `p1 > B`, with probability at
least a declared power.

**Propagation.** Exact binomial power at the exact Clopper-Pearson critical
count, searched over integer `n`. Two corrections are built in:

- **Power, not an observed rate.** Sizing so that an *observed* rate equal to the
  breach would revoke catches a true breach about half the time, because the
  observed count is binomial around it. At a 5% budget and a 1.5x breach, 287
  negatives became 628 at power 0.80 (`DECISIONS.md` 146, 183).
- **Stable, not first.** Detection is a sawtooth in `n`: it can hold at one size
  and fail at a larger one. The size quoted is the smallest from which power holds
  at every larger `n` up to a horizon.

`warrant plan` adds the false-revocation probability of each cadence of
independent rechecks, which grows with the number of rechecks and motivates §16.

`controlplane/economics/sizing.py` (`negatives_for_power`).

## 16. The chain: one sequential test over a declared horizon

**The problem.** Each independent recheck spends `alpha`, so a year of weekly
rechecks revokes a detector that kept its promise in most years (`DECISIONS.md`
187).

**The statistic.** A Shiryaev-Roberts e-detector per bet `lambda` on a fixed
geometric grid, averaged over the grid. For each clean negative unit, in an order
fixed by `sha256(warrant digest, unit id)` before any score is read:

```
L_t(lambda) = 1 + lambda * (x_t - B)          x_t = 1 if the unit fired, else 0
R_t(lambda) = (R_{t-1}(lambda) + 1) * L_t(lambda)
M_t         = mean over the grid of R_t(lambda)
revoke when M_t >= N / alpha
```

**The guarantee.** For any true rate at or below `B`, `R_t + (N - t)` is a
nonnegative supermartingale starting at `N` that dominates the statistic over the
first `N` units, so by Ville's inequality

```
P( M_t >= N / alpha for some t <= N ) <= alpha
```

**What it covers, and what it does not.**

- It covers **this statistic only**. A chained recheck `REVOKED` because the score
  distribution moved (§14) is a separate check, outside the bound (addendum
  2026-09-16).
- It holds for the chain **as kept**. Restarting after an unfavourable record
  spends it; so the chain-head sidecar makes forks declare themselves, and a
  revoked warrant cannot be continued, forked or restarted around.
- It does not extend past `N`.
- Detection is not uniform across cadences: monthly rechecks miss a breach for a
  quarter noticeably more often than weekly ones ([LIMITATIONS.md](LIMITATIONS.md)
  §3.5, `DECISIONS.md` 196).

**Revocation precedence (DECISIONS 205).** A separate drift revocation stands
regardless of whether the FPR result is a breach, an inconclusive warning, or
untested. The aggregate status cannot hide it. Continuation also reads the drift
finding on an old record whose aggregate status was inconsistent. Verification
flags that inconsistency and any successor; this is a consistency check, not a
recalculation of drift or an extension of the sequential guarantee.

**Integrity.** Each record carries a digest of its chain state, and since the
addendum of 2026-09-17 a seal over the whole record. Both are checksums, not
signatures. A missing record seal is unknown integrity, not proof of legacy age
(DECISIONS 207). Verification retains structural inspection while requiring
complete seals for `clean` and `--require-clean`. Continuation also requires a
reproducing seal, even with `--fork`; missing metadata is never silently repaired.

**Local publication (DECISIONS 206).** The command holds one OS lock for the
canonical warrant path while checking the parent, publishing the complete sealed
record and advancing the head. A competing command exits with bad input and can
retry after the writer exits. A retained pending intent lets the next invocation
finish an interrupted write with exactly the original prepared evidence. That
recovery exits explicitly before any further link; continue by naming the
recovered record with `--since`. Conflicting retained data is preserved and
refused. This repairs a local publication race, without changing the statistic
or extending it to distributed writers. Keep the persistent lock name and every
record; neither locking nor checksums defend against deliberate history removal.

`controlplane/intake/chain.py` (`feed`), `chain_verify.py`, `chain_publication.py`.

## 17. Label error: exact ladders, and a second reviewer

**The two errors that flatter a certificate.** With `k` false positives on `n`
negative units:

| Error | Effect on the counts |
|---|---|
| a flagged item labelled positive that is really clean | `(k, n) -> (k+1, n+1)` |
| an unflagged item labelled negative that is really positive | `(k, n) -> (k, n-1)` |

The other two errors make the bound conservative and are never used to tighten it.

**The confidence after correction.** By the Clopper-Pearson duality the bound at
`(k, n)` equals `B` at confidence `1 - P(Bin(n, B) <= k)`. With `a` errors of the
first kind and `b` of the second:

```
c(a, b) = 1 - P( Bin(n + a - b, B) <= k + a )
```

non-increasing in each. Every certificate prints, for each kind separately, how
many errors take `c` below 0.90, 0.80 and 0.50: an exact **ladder**, not an
estimate (`DECISIONS.md` 197). It is not computed on a refusal, where it would be
a recipe for relabelling one into a warrant. On a grouped file it counts whole
groups when every group carries one label, and is not computed otherwise.

**Tolerance is not a property of the detector.** At fixed `alpha`, with untied
scores, `k` at the certified threshold is determined by `n`, `B` and `alpha`, so
the ladder is too. A better detector changes how many flagged positives there
are to be wrong, which is exposure, not tolerance.

**On a recheck** the question is reversed: the fewest errors of each kind that
would have made the recheck revoke, `lower(k+a, n+a) > B` or `lower(k, n-b) > B`,
evaluated at every count up to a limit so no monotonicity is assumed
(`DECISIONS.md` 198).

**A second reviewer (`label_2`).** Measured beside the result, never used to change
it:

- **Cohen's kappa** over the double-labelled items, percentile bootstrap over
  pairs. On a grouped file the pairs are still resampled independently, which
  ignores correlation within a group; a fix is pre-registered and not merged.
- **Disputes** at the certified threshold, in both flattering directions, and `c`
  if each dispute were an error: a worst case over the reviewed pairs, not a
  bound on the truth.
- **A whole-file bound on disputes**, when only some items were double-labelled
  and assuming they were drawn at random from their pool: with `d` disputed of `r`
  reviewed in a pool of `M`,

  ```
  D_upper = max{ D : P( Hypergeom(M, D, r) <= d ) >= alpha }
  ```

  exact, equal to `d` when the whole pool was reviewed. The two pools' bounds hold
  jointly at `>= 1 - 2 alpha`, and `c` evaluated at them is a sensitivity, not a
  joint confidence.

`controlplane/intake/labels.py`, `controlplane/sampling/agreement.py`.

## 18. Recall on traffic: sizing through the derivative

**Quantity.** Recall on production traffic, `R = TP / (TP + q * N_u)`, where `TP` is
the confirmed errors in the flagged pool (a census, exact and free), `N_u` the size
of the unflagged pool, and `q` the error prevalence in it, which labels estimate.

**Propagation.** A margin on `q` reaches `R` multiplied by

```
dR/dq = -TP * N_u / (TP + q * N_u)^2
```

and sample size scales as `1 / margin^2`, so sizing `q` as if it were recall
understates the labels needed by the square of the derivative. This repository
made exactly that error, and `DECISIONS.md` 147 records its size.

**Assurance.** Sizing at the expected count delivers the margin about half the
time. Sizes are quoted at a declared probability that the **realised** margin meets
the target, computed exactly (`DECISIONS.md` 191).

**Allocation.** Proportional in month one, at full simple-random-sampling cost:
Neyman allocation needs per-stratum rates that month one does not have (150).
The estimator's coverage is measured on simulated traffic with known truth, over
the declared workload (`results/on_traffic/`).

`controlplane/sampling/planning.py`, `estimator.py`, `allocation.py`;
`controlplane/economics/sizing.py`.

## 19. Release evidence: one fixed threshold, simultaneous intervals

`warrant release` measures **one** threshold fixed before the holdout is evaluated,
so there is no search and no selection correction (`DECISIONS.md` 184).

**Intervals.** Five rates, false-positive rate, recall, precision, flag rate and
base rate, each get an exact two-sided Clopper-Pearson interval at `alpha / 5`. By
the union bound their joint coverage is at least `1 - alpha` under the declared
assumptions: IID items from the declared scope, a holdout unused for selection,
one evaluation. Lift is measured recall over measured flag rate, with its interval
propagated conservatively from the two bounds.

**Decision.** `VALID` when every registered acceptance bound clears its limit.
Otherwise `REFUSED`, with the reason for each criterion: an observed violation, an
inconclusive bound, or a missing denominator. A tested study that could not clear
is a refusal, not "never tested". `STALE` on verification after expiry. This is
release protocol 2 (Codex-parallel decision 200,
[decisions/CODEX-PARALLEL.md](decisions/CODEX-PARALLEL.md)); a contract registered
under protocol 1 replays with its original `UNVALIDATED` for an inconclusive bound
or a missing denominator, labelled as the legacy protocol.
These verdicts come from a different interval family than `certify` (one-sided,
per budget, at `alpha`) and are **not interchangeable** on the same counts.

Grouped files are rejected: the interval family assumes independent items.

`controlplane/release/evaluate.py`; procedure in [RELEASE.md](RELEASE.md).
