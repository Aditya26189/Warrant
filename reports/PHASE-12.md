# Phase 12 -- the customer path promised more than its evidence, three times

**The question: after the final version shipped, what in the customer path is
still wrong, and what does current regulation say a buyer has to do?**

**Answer: the customer path made three promises its evidence did not support,
and each is now fixed or bounded.** `warrant plan` quoted a recheck size that
catches the breach it is sized for about half the time. `certify --frontier`
reported budgets as certified on grouped files that `certify` refuses. And the
frontier invited a choice among its rows whose chosen row was wrong up to 0.1064
of the time against a nominal 0.05. Separately, `plan --warrant` had never
worked. None of the three was found by a failing test; each was found by reading
the shipped code.

The research found a primary-source draft from the Reserve Bank of India that
brings third-party and generative AI models under independent validation by the
regulated entity and sets no evidential standard for it. That names the buyer
more precisely than anything before it. **It is still not evidence that anyone
pays**, and the twelve conversations in `reports/STRATEGY-2026-09.md` remain the
test that decides.

- **Window:** 2026-09-14 to 2026-09-15
- **Range:** `c00ec63` -> `9a81e82` on `exp/frontier-selection`; `main` holds
  182-183 only (`c14da56`, pushed)
- **Suite:** 1,362 collected at `c00ec63` -> 1,617 at `9a81e82`, a count that
  includes two other agents' work (section 6). Full suite at `9a81e82`: 1,616 passed, 1 expected failure (`DECISIONS.md` 179's strict xfail), none failed.
- **Decisions in this report:** 182, 183, 189, 190, 192. Entries 184-186 are
  Codex's and 187, 188, 191 and 193 are accenture-8a's (section 6).

---

## 1. What was found, in the order found

### 1.1 `plan --warrant` exited 2 on every record `certify` writes (182)

`plan` read `record["budget"]`; `certify` writes `budget_fpr`. The help text said
it "takes the budget and alpha from it rather than having you retype them"; it
never had. With `--budget` also given, the record was ignored without a word.

Fixed: `plan` reads `budget_fpr` and `alpha`, refuses a `--budget` that disagrees
with the record, refuses a REFUSED record as `recheck` does, and `recheck` now
tests at the record's alpha. **No test had run `plan` from the command line.**
`tests/test_cli_records.py` now runs every command against a real certified
record and checks that every key a command reads is one `certify` writes.

### 1.2 The price list quoted a coin flip (183, pre-registered)

`DECISIONS.md` 146 sized a recheck so that an *observed* rate equal to the breach
revokes. At a *true* breach the count is binomial and reaches the critical count
about half the time.

| budget | breach | quoted before | its power | quoted now (power 0.80) |
|---|---|---|---|---|
| 0.05 | 0.075 | 287 | 0.489 | 628 |
| 0.05 | 0.10 | 86 | 0.495 | 191 |
| 0.01 | 0.015 | 1,501 | 0.488 | 3,295 |

**The quoted label cost roughly doubles.** Criteria were committed before the
implementation (`9a5336b`); all four passed, and the implementation landed within
1.6% of the scratch estimates recorded beforehand.

**A year of rechecks is not one test.** At n = 628, one recheck revokes a
detector sitting exactly at its budget with probability 0.0365, and a weekly
programme does so at least once a year with probability 0.86 (monthly 0.36).
`plan` now prints this beside every cadence. **It states the cost and does not
remove it**; accenture-8a's 187 measures rules that would.

Found alongside: `recheck` raised on a record certified at a budget above 2/3.

### 1.3 The frontier certified grouped files at item level (190)

`frontier` dropped the `group` column and certified every budget at item level.
On a constructed file of 150 groups of four -- 110 negative clusters, 440
negative items -- it reported budgets 0.01 and 0.02 certified where `certify`
refuses ("110 independent units; need >= 149"), quoted a lower threshold than
`certify` at 0.03, and certified a file with unequal groups that `certify`
rejects as anticonservative. **Found by reading `frontier.py` after 188 fixed the
same omission in `recheck`.**

Fixed by making `intake.certify.certify_budget` the only certification step,
called by both. `tests/test_frontier_groups.py` compares every frontier row with
`certify_items` end to end, and fails on the old code with *"frontier says
certified=True, certify says REFUSED"*.

### 1.4 The frontier's invitation to pick a row (192, pre-registered)

The frontier tells its reader to pick "the row whose 'missed' you can live
with" and then certify it on the same file -- `CLAUDE.md`'s *selecting on test*,
on the customer path. Each row holds at 95% alone. `certify_fpr`'s argument that
sweeping thresholds needs no correction covers one budget, whose failure is a
single event at one fixed threshold; eight budgets have eight.

Registered before any study code (`c1463d7`); run at `dcb9a1a`:

| n | joint miscoverage | picked row wrong, d'=1 | d'=2 | rows certified at alpha/8 |
|---|---|---|---|---|
| 150 | 0.127 | **0.106** | 0.048 | 5 of 7 |
| 300 | 0.155 | 0.080 | 0.039 | 7 of 8 |
| 600 | 0.151 | 0.072 | 0.047 | 8 of 8 |
| 1200 | 0.177 | 0.054 | 0.057 | 8 of 8 |
| 5000 | 0.184 | 0.052 | 0.047 | 8 of 8 |

**Material by the registered rule, narrowly: 0.1064 +/- 0.0033 against 0.10, 1.9
SE above it, in one cell.** The rule is read as the picked row's error *given
that a row is picked*; that reading was fixed in code before the run, and it is
the quantity a customer holding a picked row has. **Read unconditionally it
would not have been material** (at most 0.057). A 2,000-replicate speed check
at n = 600 was seen after the criteria were committed and before the registered
run.

The registered remedy was adopted: the frontier certifies at `alpha / 8`, so its
certified rows hold at once, and says so. Its cost is two rows at n = 150 and
one at n = 300; from n = 600 every row certifies, with thresholds tightened by at
most 1.3 percentage points of expected false-positive rate.

### 1.5 `FPRMonitor` does not deliver the guarantee its docstring states

`FPRMonitor.wealth` returns `1/alpha` once the largest single bet exceeds
`e/alpha`. At `p0 = 0.05`, two false positives in the first two labels report
wealth 20.0 and revoke while the mixture is 14.21. The deployment-wide
false-revocation bound is not established as implemented. **Found by
accenture-8a (187), confirmed independently here; the file is read-only.** The
crosswalk and this report do not repeat the guarantee.

---

## 2. The research

**RBI, draft *Guidance on Regulatory Principles for Model Risk Management,
2026*** -- released 24 June 2026, comments closed 24 July 2026, still a draft
when read on 14 September. Read on rbi.org.in, not through a vendor summary.

- ¶9: "all models, including AI / ML models, irrespective of whether such models
  are developed internally, sourced from third-parties, or a combination thereof".
- ¶29-30: independent validation **by the regulated entity**, "prior to and after
  deployment of a model, following modification, on internal or external
  triggers, and periodically".
- ¶54(2): control boundaries against hallucination in generative models.
- **Nothing on evidential standard**: no confidence level, no sample size, nothing
  about a validation the data cannot support.

Contrast, verified in `reports/STRATEGY-2026-09.md` §3: the US agencies' SR 26-2
excludes generative and agentic AI.

**The crosswalk** (189, [docs/RBI-MRM-2026-CROSSWALK.md](../docs/RBI-MRM-2026-CROSSWALK.md))
registers 20 paragraphs: **2 PROVIDES, 13 PARTIAL, 5 NOT PROVIDED** --
explainability thresholds, fairness assessment, red-teaming, exception approval
and reports to the risk committee. The page is generated from a register, and a
test fails if any code, test or artifact it names disappears. It says on its
face that it is not a compliance claim.

**Considered and deliberately not built.** OpenTelemetry's GenAI conventions
define a `gen_ai.evaluation.result` event, at Development stability. It scores
one response; a warrant is a statement about a detector on a distribution, with
an interval, and forcing one into the other would drop the interval invariant 4
requires. SEBI's AI/ML guidance was found only as a June 2025 consultation paper
and is not mapped.

---

## 3. What this does not establish

- **Nothing here touched production traffic**, and no measured detector number
  moved: every figure in section 1 is exact arithmetic, a simulation with known
  truth, or a constructed file built to show a disagreement.
- **The power fix makes the quoted sample honest; it does not make rechecking
  cheap**, and the year's false revocations are stated, not bounded.
- **192's verdict is narrow.** One cell of ten crossed the line, on a reading of
  the criterion that the entry had to state because the other reading reverses
  it. The pick rule is one plausible rule under two ROC shapes, item-level, with
  continuous scores; grouped files and ties were out of scope.
- **The crosswalk is a register of evidence toward a draft**, not compliance with
  a final text. Its quotes were read through a fetch tool from the HTML page, and
  the PDF returned a verification page; check any quote used externally against
  the PDF.
- **The RBI draft is not demand evidence.** An obligation to validate does not
  show a budget for interval-backed validation or for refusal.

---

## 4. Open items

| # | item | what would close it |
|---|---|---|
| O-1 | **A warrant from `certify --budget` on a budget picked off the frontier is still at the unadjusted level.** The frontier now holds; the command after it does not (192) | a decision on certifying a picked budget at the frontier's level |
| O-2 | **Exception approval (RBI ¶34) against invariant 3.** The draft contemplates deploying a model approved with exceptions; nothing records one beside a REFUSED warrant (189) | a founder decision on whether the product records exceptions at all |
| O-3 | **Codex's release path marks a tested-but-inconclusive holdout UNVALIDATED.** Invariant 2 reserves UNVALIDATED for "never tested here", and `certify` refuses the same case; the same file can be REFUSED by one command and UNVALIDATED by the other | **closed by Codex's release protocol 2** (`fc706c1`, its own DECISIONS 200 on `feat/shared-context`): a tested study that cannot clear every bound is REFUSED, with the reason named; UNVALIDATED stays the legacy protocol-1 spelling, and the schema version is bound into the contract identity so an old record cannot be reread under the new meaning. Verified read-only at `55528c7` |
| O-4 | **Codex's release path sets a second standard for VALID**: a two-sided interval at alpha/5 per rate, roughly a one-sided alpha/10, beside `certify`'s one-sided alpha | **closed as disclosure, not alignment** (`fc706c1`): the intervals stay as registered, the render names the protocol and says release divides alpha across the family and both tails while `certify` uses a one-sided bound, and a test pins a case where `certify` clears and release refuses on the same items. Verified read-only at `55528c7` |
| O-5 | **`FPRMonitor`'s cap** (187) | an owner for read-only `validation/warrant_stats.py` |
| O-6 | **Merge order.** Five branches chain on `feat/release-evidence`, which no human has reviewed; only 182-183 are on `main` | a human review of that branch, then `--no-ff` merges in chain order |
| O-7 | **This branch carries 191's code at `945f08b`, before its post-artifact fix** (`ca5ceab`, `1c13492` on accenture-8a's line) | merging accenture-8a's fixed line ahead of or into this one |
| carried | demo video; read-only defects; four drift features and MMD; customer conversations; `DECISIONS.md` 145's Linux Rego abort -- **cause named and a one-line guard verified on Linux and Windows (2026-09-15)**, still needing an owner for read-only `policy/` | `reports/PHASE-11.md` §6 |

---

## 5. Defects in how this sprint was run

Reported here because `CLAUDE.md` asks for defects found by rereading, and these
say what the process was not covering.

- **Three agents wrote to one repository.** Codex checked out
  `feat/release-evidence` over the working tree mid-sprint, with uncommitted
  edits. From then on this sprint worked only in separate git worktrees and
  coordinated decision numbers by message. Nothing was lost, and nothing
  prevented it either.
- **A scratch helper edited the shared tree twice.** A count-bump script had the
  main repository path hardcoded and rewrote "1450 tests" to "1452 tests" in
  `README.md` and `Makefile` there, among Codex's uncommitted edits. Both times
  only those bytes were reverted and `git status` was checked against its prior
  state; the helper now refuses that path. The second occurrence happened because
  a failed patch to the helper was not chained with `&&` to the command after it.
- **The same helper's alt-text pattern missed a count twice**, caught both times
  by `test_every_stated_test_count_is_the_real_one` before commit.
- **190's first draft cited the wrong entry** (136 for the cluster rule, which
  is 107 and 137); corrected before the commit was shared.

---

## 6. The parallel work this report does not cover

Two other agents committed in this range. Their results are theirs to report,
and accenture-8a will add its section as an addendum. Listed so the decision
numbers and the commit range read correctly.

- **Codex:** 184 (release evidence), 185 (intake reuse), 186 (audit repair), and
  `reports/STARTUP-VIABILITY-2026-09.md`, on `feat/release-evidence`. **Found on
  review:** its tip `deac5d7` failed `test_every_script_has_a_smoke_test`, and it
  introduced mixed line endings in `.github/workflows/ci.yml`,
  `controlplane/cli.py` and `pyproject.toml`; both were fixed by accenture-8a in
  `b8b0f00` and `963dde6`. O-3 and O-4 above are the open product questions.
- **accenture-8a:** [187](../DECISIONS.md) (a year of rechecks as change
  detection -- complete, with results and the `FPRMonitor` defects),
  [188](../DECISIONS.md) (`recheck` rechecks a grouped warrant in clusters --
  complete), 191 (recall assurance -- in progress) and 193 (not started).

---

## 7. Ledger

**Code**
- `controlplane/cli.py` -- `plan` reads the record; `--power`; frontier exits 2
  on unequal groups (182, 183, 190, 192)
- `controlplane/economics/sizing.py` -- `critical_counts`,
  `revocation_probability`, `negatives_for_power`, `false_revocation_in_year`;
  `monitoring_plan` at a declared power (183)
- `controlplane/intake/recheck.py`, `render.py` -- power-based hint and
  disclosures (183)
- `controlplane/intake/certify.py` -- `certify_budget`, the one certification
  step (190)
- `controlplane/intake/frontier.py` -- certifies through it, at `alpha / len(grid)` (190, 192)
- `controlplane/intake/selection.py`, `scripts/30_frontier_selection.py` -- the
  192 study
- `controlplane/report/crosswalk.py` -- the RBI register (189)
- `config.yaml` -- `validation.recheck_power: 0.80` (183)

**Artifacts** -- `results/frontier_selection/selection.json` (192, at `dcb9a1a`);
`docs/RBI-MRM-2026-CROSSWALK.md` (generated, 189).

**Tests** -- `test_cli_records.py`, `test_recheck_power.py`, `test_crosswalk.py`,
`test_frontier_groups.py`, `test_frontier_selection.py`; updated
`test_sizing.py`, `test_smoke.py`.

**Decisions** -- 182; 183 (`9a5336b` registered, `2259065`, `7ae68d3` results);
189 (`d472dc1`, `f088c4c`); 190 (`94e2c68`, `f0d9f11`); 192 (`c1463d7`
registered, `dcb9a1a`, `eeb45f5` artifact, `6feafa6` results, `9a81e82` remedy).

**Reproduce**

```
python -m pytest tests/ -q
python scripts/30_frontier_selection.py --config config.yaml      # 192; about 20 minutes, most of it the cross-check
python -m controlplane.report.crosswalk                           # regenerates the crosswalk page
python warrant.py plan -b 0.05 --negative-share 0.9               # 628 negatives at power 0.80
python warrant.py certify -i examples/certifies.csv --frontier    # rows certified at alpha/8
```

---

## 8. Addendum -- accenture-8a's line: 187, 188, 191, 193

**The question: when a warrant is kept true over time, does the customer path
tell the truth about how often it will be wrong, and what it costs?**

**Answer: no, twice more, and one of this line's own fixes was wrong when first
committed.** A year of the shipped per-recheck test revokes a detector that kept
its promise in 0.8515 of simulated years, and the research path's anytime-valid
monitor -- the one built to avoid that -- catches a breach that follows six good
months within a quarter in 2 of 4,000 years. The recall price was sized so its
margin is realised about half the time (0.4882). Both are fixed or given an
alternative that measures well. **The first fix to the recall price counted one
tail where there are two, and committed wrong `decision_support` sizes
(`11d7d90`)**; it was caught by reading `RESULTS.md`, not by a test.

- **Branch:** `feat/recheck-chain` (merges 189, 190, 192 and this report).
- **Suite:** 1,635 collected at `baef95a`. Full suite there: one failure,
  `test_acceptance` on a README template line, fixed at `595dbc4` (8.7).
- **`verify.py`:** claim table 81/81, frozen scores 25/25, activations 3/3 (at
  `ab12e41`).

### 8.1 A year of rechecks, measured as change detection (187, pre-registered)

Five rules on the same simulated labels, 4,000 years per cell, seed 1729
(`results/recheck_schedules/comparison.json`, run at `b8b0f00` and reproduced
exactly after a rebase). Weekly, 52 rechecks of 628 negatives:

| rule | false revocation, sound year | breach at 26 weeks, caught in 13 | breach after 26 weeks at 0.0371, caught in 13 |
|---|---|---|---|
| per-recheck test (shipped `recheck`) | **0.8515** | 0.3790 | 0.9940 |
| alpha split | 0.0280 | 0.9772 | 0.9892 |
| `FPRMonitor` (shipped research monitor) | 0.0248 | 0.9830 | **0.0005** |
| e-detector | **0.0085** | **0.9965** | **1.0000** |

The registered criteria chose the e-detector. **One prediction failed**: at the
monthly cadence, after good months, the alpha split caught more (0.8420 against
0.7877). **The finding that matters most was not the question asked:** the
research path's monitor decays through good behaviour and then cannot fire in
time, and its cap roughly doubles false revocation (0.0248 against 0.0115
uncapped). `validation/warrant_stats.py` is read-only; both are OPEN.

Two errors in the pre-registration were corrected **before** any simulation, in
separate commits: rule D as first written was a single fixed bet with negative
growth at the breach, and C' was added once the cap was found.

### 8.2 `recheck` discarded the groups `certify` certified on (188)

A grouped warrant was re-tested item by item: a different rate, at a sample size
counting correlated items as independent. Four whole clusters firing -- 40 false
positives in 400 items, 4 in 40 clusters -- revoked per item and is STALE per
cluster. Fixed: cluster units, unequal clusters and grouping mismatches exit 2,
no drift verdict on grouped files. Codex's 184 had logged it OPEN; `intake/` is
not read-only, so it was closed rather than carried. 190 then found the same
omission in `frontier`.

### 8.3 The recall price bought its margin about half the time (191, pre-registered)

`labels_for_recall` sized at the expected error count. Criteria passed: the
published 1,014 labels realise +/-0.05 with probability **0.4882** (C2); at 0.80
assurance the size is **1,399** (C3); 2,000 samples through the real estimator
realise the margin in 0.8045 against 0.8004 computed (C1). Month one, from
`results/on_traffic/on_traffic.json` at `05b2a52`:

| | +/-0.05 | +/-0.02 |
|---|---|---|
| declared workload | 1,014 -> **1,399** | 5,566 -> **6,518** |
| `customer_support` | 1,808 -> 2,283 | 10,636 -> 11,803 |
| `internal_knowledge` | 3,582 -> 4,101 | 21,598 -> 22,886 |
| `decision_support` | 4,049 -> 4,068 | 24,591 -> 24,659 |

**The defect.** The recall half-width rises to one peak near `n TP / (3 N_u)` and
falls after. The first implementation assumed only the falling side, which holds
at the declared workload and fails at `decision_support`, where the peak sits at
the expected count: at +/-0.02 and 21,108 labels it returned assurance 1.0 where
brute force gives 0.0000, and `11d7d90` committed 21,108 and 16,737 for that
profile -- below the sizes they replaced, which is how it showed. The tests had
checked the property only where it held. Fixed at `ca5ceab` with both tails and
brute-force checks at every shipped operating point; artifacts regenerated at
`05b2a52`, and `RESULTS.md` through the chain at `478e674` (3,075 metrics, 0
moved). The wrong commit stays in history.

### 8.4 The chain: 187's rule on the customer path (193)

`warrant recheck --horizon-labels N` starts a chain and `--since RECORD`
continues it: every recheck's clean-negative units feed one e-detector that
revokes at `N / alpha`, so a year of rechecks revokes a sound detector with
probability at most alpha. `N`, alpha and the grid are frozen; units are ordered
by digest, so arranging a file changes nothing; consumed units, edited states,
other warrants and ended or revoked chains are refused with exit 2 and nothing
written. `plan` prints each cadence's `N` as a copyable command. Acceptance A1-A4
pass, including that the chain equals the study's statistic at every recheck and
revokes no later. Two acceptance criteria were overclaimed as first committed
and corrected before any code.

### 8.5 What this does not establish

- **The chain's guarantee holds for the chain as kept.** Discarding a bad record
  and restarting spends it, and nothing on one machine prevents that; the
  records only make it visible.
- **187 is one budget, one breach size, one change point, independent fresh
  samples, a step change.** The chain's detection is not measured for any other
  setting, and `plan` quotes none.
- **Assurance is over sampling noise at a declared prevalence**, not over the
  prevalence being wrong, which is the larger month-one risk. The Neyman rows use
  the effective-`n` approximation.
- **No detector, labeller or production traffic** is involved in any number in
  this addendum.

### 8.6 Open items added

| # | item | what would close it |
|---|---|---|
| O-8 | **`FPRMonitor` decays through good behaviour** and almost never catches a breach that follows it in time (187) | an owner for `validation/warrant_stats.py` replacing the runtime trigger with a change detector |
| O-9 | **The demo still states `FPRMonitor`'s deployment-wide guarantee**: `controlplane/report/beats.py` prints "anytime-valid; P(false revoke) <= alpha over the whole deployment", which 187 found is not established as implemented. No code path runs the monitor | **closed at `2a9f7ee`**: the beat and `DEMO_SCRIPT.md` now name the chain's bound |
| O-10 | **The chain's detection outside 187's registered setting is unmeasured** | **closed by `DECISIONS.md` 196**: the bound held in every setting; monthly rechecks catch a breach within a quarter in only 0.83-0.90 of years (`docs/LIMITATIONS.md` 3.5) |

### 8.7 Defects in how this line was run

- **A fix committed wrong artifacts** (8.3). Caught by a number moving in the
  impossible direction, not by a test; the tests now cover the shipped operating
  points that exposed it.
- **A chain rebuild was started against a leftover ledger** by backgrounding a
  whole `&&` list with `&`, which also hid the commit's confirmation. Stopped at
  its first stage; the ledger was moved aside, not deleted, and the chain rerun
  clean.
- **Three pre-registrations needed corrections before running** (187's rule D,
  191's direction of the half-width, 193's A1 and A2). Each is a separate commit
  and a note in the entry; none moved a criterion after results were seen.
- **The README said the price list and gate were never written**, long after
  both were built; retired at `defd36d`.
- **A README example broke the fresh-clone acceptance test.** The chained-recheck
  lines were not marked as templates, so `test_acceptance` ran them; found by the
  full suite, fixed at `595dbc4`.

### 8.8 Ledger

**Code** -- `controlplane/economics/schedules.py`, `scripts/29_recheck_schedules.py`
(187); `controlplane/intake/recheck.py` cluster units (188);
`controlplane/sampling/planning.py` assurance, `config.yaml`
`sampling.margin_assurance: 0.80` (191); `controlplane/intake/chain.py`,
`recheck --horizon-labels/--since`, `plan` chain horizons (193).

**Artifacts** -- `results/recheck_schedules/comparison.json` (187, `96f4d65`);
`results/on_traffic/`, `results/feasibility.json` (191, `05b2a52`);
`results/RESULTS.md` and the chain's 14 artifacts (`478e674`).

**Tests** -- `test_recheck_schedules.py`, `test_test_inventory.py`,
`test_recheck_groups.py`, `test_sampling_assurance.py`, `test_recheck_chain.py`.

**Decisions** -- 187 (`cce5d8d`, `194172d`, `6fea4da` registered and corrected;
`2f9f25c` code; `948a9e8` results); 188 (`f231a68`, `0c8ae39`); 191 (`c94d2c7`,
`ff004e8` registered and corrected; `945f08b`, `ca5ceab`, `1c13492` code;
`ab12e41` results); 193 (`01d8117`, `3ff15d9` design and correction; `d33cd4a`
code).

**Reproduce**

```
python scripts/29_recheck_schedules.py --config config.yaml       # 187; about ten minutes
python scripts/25_on_traffic.py --config config.yaml              # 191's price list
python warrant.py plan -b 0.05 --negative-share 0.9               # prints each cadence's chain horizon
python warrant.py recheck -w W.warrant.json -i week01.csv --horizon-labels <N from plan>
python -m pytest tests/test_recheck_chain.py tests/test_sampling_assurance.py -q
```

### 8.9 After the addendum: an independent review of 193 found what its tests had not (194)

accenture-c4 reviewed 193 and 191 read-only, reproducing every finding through
the CLI. **191's fix was confirmed correct** by brute force over every count and
390 configurations beyond the shipped points. **193 was not.**

- **A defect.** A file whose bound breaks *and* whose distribution moved lost its
  drift revocation inside a chain -- the bound-first verdict hid it, and the
  chain mapped it to STALE. Fixed: drift carries its own verdict, and a chain
  cannot hide it.
- **Three overclaims.** The consumed-unit check is per id, not per item; `plan`'s
  horizon counts negatives fed, not weeks; chained reasons omitted the chain's
  end and the units it never saw. Each now says so.
- **Four ways past the fork guard**, three found on a second pass: continuing
  from an older record, copying the warrant, editing the head sidecar, and
  overwriting last week's record by exporting to one filename. The first, second
  and fourth are refused unless `--fork` declares them; the third cannot be
  refused locally, so `warrant chain verify` (built by accenture-c4) detects forks,
  restarts, missing links, edited states and spliced links **from the records a
  user keeps**, and the records say what "matched" cannot prove.
- **Hardening from the 191 review:** every quoted recall size is now checked
  against brute force at run time, and raises rather than returning a size it
  cannot confirm.

**What this says about the process.** 193 shipped with passing acceptance
criteria written by its author. Every defect above was found by a second reader
with a reproduction, none by those criteria. A review loop also introduced and
caught its own line-ending flip before it reached a branch.

Head `86b0f9b`: full suite 0 failures, 1 expected xfail; 1,667 collected.

### 8.10 The last two decisions of the sprint, and the gate (195, 196)

**195 (accenture-c4, reviewed by accenture-8a).** `certify --budget B
--from-frontier RECORD` certifies a budget picked off the frontier at the level the
frontier held its rows to, so the pick 192 measured is paid for once. Review found
the frontier record's own numbers were trusted: an edited `row_alpha`, a record cut
to the one picked row, or an edited threshold each certified at the unadjusted
level while the warrant claimed a frontier pick. Fixed by recomputing the whole
frontier from the input and refusing any row that does not reproduce. The warrant
now also says that its recall and precision were measured on the file the budget
was picked from, and carry the pick's optimism; only the false-positive bound is
adjusted. **The default `certify --budget` is unchanged and OPEN for the user.**

**196 (accenture-8a, reviewed by accenture-c4).** A registered study of the chained
recheck across three breach sizes, weekly rechecks with the breach starting at
three points, and monthly rechecks (`results/chain_detection/grid.json`). **The
false-revocation bound held in every setting** (at most 0.012 against a limit of
0.0646). Monthly rechecks caught a breach within a quarter in only 0.8325 to
0.8970 of simulated years. **One prediction failed as registered**, strictly and
within noise at the ceiling. **Review found a confound the entry had missed**: each
breach was rechecked at its own 0.80-power size, so the larger breaches were also
rechecked with far fewer labels, and the monthly figures do not order detection by
breach size at comparable effort. `docs/LIMITATIONS.md` 3.5, the README claim row
and the entry say so; P3's stated mechanism is marked unsupported.

**What the two reviews say about the sprint's method.** In both directions, the
author's own acceptance criteria passed and the second reader found what they
missed: a trusted input in 195, a confound in 196. That is the pattern of 193 as
well. 193, 195 and 196 were each reviewed by the other session before they reached
the integrated line, and 194 was itself the product of review. Its second-round
fixes (A to C) went unreviewed until drafting this section exposed the gap; the
review that followed found two bypasses that are limits of a local tool (a record
rewritten with a recomputed digest verifies clean; a copied warrant can restart a
chain), a check-then-write race, and a filename collision. The texts now say what
the digests cannot prove, and the race is closed (194).

**The gate.** `scripts/clean_clone_gate.py` passed at `9c1fc68` (accenture-c4,
`results/clean_clone.json`, committed at `8df9e80`): a fresh clone of 519 tracked
files (477 at the last gate, `f6aac79`); `make smoke`, `make test` (1,941.7 s in the
clone) and `make verify` all ok; the claim table 87/87 (81/81 before, no existing
row moved); frozen scores 25/25; the activations tier skipped for gitignored
caches, as before. The gate could not delete its temporary clone (a Windows
permission error on one git object, about 26 MB left in TEMP) and records that
as a note, not a failure.

**What the gate does not cover.** The two commits after it -- 194's A to C review
section and its fixes (`287d366`, `ef8996d`) -- and this section. They were
checked by the chain, verifier, config and acceptance tests and by the full suite
at the head, not by a clean clone.

### 8.11 After the gate: how far a warrant depends on its labels (197, 198, 199)

**The question.** `certify` and `recheck` treat the customer's `label` column as
truth, and `CLAUDE.md` requires kappa beside every warrant. The customer path
published none, and nothing said how far a certificate moves if labels are wrong.

**The answer.** Further than the interval suggests. How many errors a
certificate tolerates is set by the evidence, not the detector. `certify` picks
the lowest threshold whose bound clears the budget, so every certificate sits at
the edge. On this project's own
measured TriviaQA certificates (60 rows: 3 probes x 20 budgets),
**between 2 and 8 flagged positives that are really clean take a certificate from
at least 0.95 to below 0.80 confidence**. The one labelling ambiguity this
project can measure does not do that: counting every strict/lenient matching
dispute as a lenient error leaves the lowest at **0.8127**.
(`results/label_sensitivity/triviaqa.json`; `DECISIONS.md` 199.)

**What was done.**

- **197:** every VALID certificate carries two exact ladders, one for each label
  error that flatters its bound. A flagged positive that is really clean gives
  `(k+1, n+1)`; an unflagged negative that is really positive gives `(k, n-1)`.
  The confidence is `c = 1 - P(Bin(n+a-b, B) <= k+a)`. Ladders are counted in
  items, or in whole groups when each group carries one label. An optional
  `label_2` column gives kappa, the disputed counts, and exact hypergeometric
  bounds on disputes in the whole file.
- **198:** the recheck analogue, as counts: how many errors of each kind would have
  made this file revoke. At 628 negatives, a recheck at the certified rate needs
  20 or 311; one a step below the critical count needs 1 or 3.
- **199, pre-registered:** 197 on the project's measured certificates, with strict
  exact match recomputed from the frozen eval set as `label_2`.

None of the three changes a verdict. A test certifies and rechecks one file three
ways and compares the records: with no `label_2`, with one, and with a `label_2`
that contradicts every label. Nothing is computed where it would be a recipe (a
refusal, a broken bound), undefined (a mixed-label group), or misread (a chain
link).

**What was found.**

- **At the minimum file, one label error is most of the certificate.** 59
  negatives go from 0.952 to 0.808 with one flagged-clean error and to 0.376 with
  three (arithmetic, held by `tests/test_label_sensitivity.py`).
- **On large files the other error matters.** At 5,000 negatives, if 3.3% of
  the unflagged negatives were really positive (158 items), the certificate would
  be at 0.878. A flagged-clean error costs it under a point. The 3.3% is
  Northcutt et al.'s average label error over all labels in ten benchmark test
  sets, not a measured rate of this one error direction.
- **The tolerance is identical across the three probes (199, not predicted).**
  At a fixed alpha, with untied negative-unit scores, the lowest certifying
  threshold admits exactly the largest count that certifies, so `k` and both
  ladders depend only on `n`, the budget and alpha. A better detector cannot
  change how many errors a certificate tolerates. It changes how many flagged
  positives there are to be wrong, and one that flags more positives is exposed
  to more of the costly kind. This file shows the limit case: at budget 0.01,
  `last_token` flags 3 positives, and 2 errors take it below 0.80. As first
  written, this finding was wider than its conditions and conflated tolerance
  with exposure; review corrected both (199 review).
- **199's registered criteria.**
  - C0 holds: the customer path reproduces the research sweep's 20 `last_token`
    rows.
  - P1 holds: one flagged-clean error takes every certificate below 0.95.
  - **P2 fails:** the strict/lenient disputes take no certificate below 0.80.
  - Kappa between the rules is 0.8640 [0.8213, 0.9035] over 600 pairs.

**What review found (accenture-c4, read-only).**

- **197, at `aa7b0af`:**
  - F1: the entry named one flattering error of two, and the one it missed is
    what matters at scale.
  - F2: the whole-file figure extrapolated one pool and counted the other.
  - F3: a confidence at a bound read as a joint confidence.
  - F4: grouped files could carry whole-group ladders. The premise (certifying
    groups carry one label) was wrong, and it was accepted in narrower form.
  - The same review's full suite found a ruff B905 in a new test file and a stale
    test count.
- **198, at `1b5d8b2`:** correct, verified by brute force over the recheck's own
  bound. Three changes were adopted:
  - report the observed disputes on a broken bound, which a customer contests a
    revocation with;
  - a past-tense conditional;
  - a loud check that chained records carry no per-file counts.
- **199's registration, before the run:** sound. It sharpened P1's rationale and
  asked for the claim rows to read as a range over N rows. Wiring the script then
  found that the sweep covers one set of three, so C0 was amended before any
  certificate was computed, with the original wording kept.
- **199's results, at `6320c80`:** the numbers and claim rows checked out, and the
  review recomputed the 32-of-271 line. The one finding that wasn't predicted
  was stated wider than its conditions: it needed a fixed alpha and untied
  negative-unit scores. It also said a better detector cannot buy a less fragile
  certificate, which is true of tolerance and false of exposure. Both were
  corrected in text.

**What the full suite covered.** Each run was by accenture-c4 in its own
worktree, and each had 0 failures:

- `1f6dc69` (197 and its review fixes): 1,731 passed, 1 xfail.
- `d97fc02` (the 198 review fixes, the 199 pre-registration): 1,751 passed, 1 xfail.
- `93aca48` (the 199 study code and artifact, `LIMITATIONS` 3.6): 1,759 passed,
  1 xfail, 1,760 collected.

The xfail is 179's strict one on Windows.

**The clean-clone gate passed at `1a3fd58`** (`results/clean_clone.json`, committed
at `897446b`):
- a fresh clone of 529 tracked files (519 at `9c1fc68`);
- `make smoke`, `make test` (2,165.6 s in the clone) and `make verify` all ok;
- the claim table 92/92 (87/87 before; the five 199 rows added, no existing row
  moved) and frozen scores 25/25;
- the activations tier skipped for gitignored caches, as before;
- the clone again could not be fully deleted (about 26 MB left in TEMP).

**While it ran, the gate itself was found to have a race (200).** The source's
HEAD was read before a separate clone, and provenance was taken after the
roughly 37-minute run. A commit or a dirty tree during the run would have
produced a record naming two commits, with nothing refusing. This run is
unaffected: both commits are `1a3fd588` and the tree was clean. The gate now
fails when the clone is not the commit it names, takes provenance at clone time,
and refuses to write a record whose source changed. Review found the fix correct,
and asked that the record say its provenance now means clone time, not write
time (`provenance_taken`). The full suite at `b78091d`, which includes the fix, was
green: 1,762 passed, 1 xfail (accenture-c4). The last code change after it,
`18dfbae`, adds that one field and its assertion, covered by targeted tests only.
No gate has run on the fix.

**Defects in how this was run.**

- **The pipe trap, a third time.** A backgrounded suite chained `; tail` after
  `run.sh`. One named file did not exist, pytest collected nothing, and the task
  reported exit 0, which was `tail`'s. It was caught by reading the log and rerun
  without the trailing command. `CLAUDE.md`'s rule was known; the correct form was
  still not the default.
- **Selected suites instead of the lint job.** The related-suite runs omitted
  `tests/test_lint.py`, which is how B905 reached a commit.
- **197 stated the recheck figure as `critical - k`.** It was found while writing
  198. Each flagged-clean error also adds a negative, the critical count moves
  with `n`, and at `k` = 23 of 628 the count is 20, not 19.
- **A commit hash sent to the reviewing session was written from memory, not
  read from `git log`**, and was wrong. It was corrected in the next message.
  Nothing in the repository cites it.
- **Twice the inventory went stale while a full suite was requested at that
  head.** Both times it was refreshed before the suite started.
- **A polarity error in 199's committed results, found by rereading this
  report.** The closing paragraph put the unmeasured alias-list error among the
  unflagged negatives (32 of 271). Those answers are labelled incorrect, so they
  are flagged-clean errors, and 8 of 179 flagged positives break the certificate.
  The review had checked the arithmetic of 32/271, which was right, and not which
  pool the sentence placed the error in; the reviewing session counts it as a miss
  of its own. Author and reviewer both missed it. Nothing tests prose polarity, and this is the kind of
  error the codebase's `EXACT`/`ESTIMATED` and positive-class conventions exist to
  stop in code (`DECISIONS.md` 199 correction).
- **A whole-file line-ending flip, again.** An inline script rewrote
  `tests/test_clean_clone.py` with `Path.write_text`, which turned LF into CRLF on
  Windows: a 524-line diff for a 4-line change. `CONTRIBUTING.md` forbids this, a
  memory note written after the same mistake was already loaded, and review found
  it anyway. It was amended before publication. A check of every file changed in
  this range found no other flip.
- **The clean-clone gate could have recorded two commits (200).** This was
  latent since the gate was written, and was found by the reviewing session while
  the author held an edit so as not to disturb a run. The gate existed to rule
  out exactly this kind of silent mismatch, and no test covered its own record.

**What this does not establish.**

- **The ladders are for the certificate as issued, at its threshold.** They say
  how far this certificate's confidence moves if its labels are wrong. They do not
  say that no certificate exists on corrected labels. Certifying the corrected
  file could choose a higher threshold and certify again at 95%, at a different
  recall; nothing here measures that.
- **Each ladder counts one error kind at a time.** A file with some of each is
  worse than either ladder read alone.
- A disagreement is not an error. Every dispute figure counts disagreements
  against the primary label: a worst case over the pairs. Two reviewers who both
  saw the score agree and are counted clean.
- Strict EM is not a better labeller. P2's failure says the strict/lenient
  ambiguity alone does not break these certificates. It does not say their labels
  are right. Correct answers missing from the alias list are labelled incorrect,
  are invisible to both rules, and when flagged are the costly error: at budget
  0.20, 8 of `last_token`'s 179 flagged positives (4.5%) take its certificate
  below 0.80.
- The whole-file bounds assume the double-labelled items were sampled at random
  from each pool.
- Recall and precision intervals are still silent about label error.
- A chained recheck carries no sensitivity.
- No customer file has been run.

**Open.**

- **Recall and precision under label error:** would close with the same two-error
  treatment on those intervals.
- **Chain sensitivity:** would close with a simulation of the e-detector with
  mislabelled units.
- **Alias-list completeness on TriviaQA:** would close with a blind human audit of
  a sample of lenient-incorrect answers, the only way to measure the error both
  rules share.
- **The gate's own fix (200) has not run a gate.** That would close with
  `scripts/clean_clone_gate.py` at a head that includes it.

### 8.12 What an independent review found afterwards: four defects, and a coordination failure

**The gate at `1a3fd58` predates this section.** It reported a clean clone, a
green suite and 92 of 92 claims, and none of that is evidence against what
follows. A passing suite says the tests that exist pass.

**Four defects, found by an independent Codex review of this line and
reproduced.** Two are serious, and both are in the chain work of 193 and 194:

| Severity | Defect | Reproduced |
|---|---|---|
| P0 | A recheck whose overall status is REVOKED **by drift** can be continued. `continue_chain` checks only the chain state's `revoked_at_unit` and `ended`, never the record's status, so a later link on stable data returns VALID | yes, through the public CLI |
| P0 | The serialized derived fields of a chain record -- `threshold`, `mean_statistic`, `ended` -- can be edited without rehashing and still verify. `_body()` hashes them, but `from_payload` rebuilds them from the core fields and never compares the serialized values | yes, all three independently |
| P1 | Grouped agreement resamples individual pairs. 400 rows that are four repeated groups report the same kappa interval as 400 independent rows | yes: both give kappa 0.0, interval [-0.1001, 0.0924] |
| P1 | A chain record with `alpha` of 0 or NaN raises `ZeroDivisionError` or produces NaN inside the grid reconstruction, before any digest comparison, so the verifier shows a traceback instead of a finding | yes |

`warrant chain verify` reports **zero findings** on the first two histories. The
verifier is the instrument a customer would use to detect exactly this, and it
says the history is clean.

**What the reproduction corrected in the method.** The first attempt at the drift
case shifted scores upward, which raised the observed false-positive rate to
0.28, revoked the chain's own detector at unit 28, and produced a refusal that
had nothing to do with drift. It read as a PASS. Only a downward shift -- the
distribution moves while firings fall, so the chain stays live and the bound
holds -- isolates the defect. A reproduction that confirms the absence of a bug
by accident is worse than none, and this one nearly did.

**What this says about the tests.** 1,763 tests did not catch any of the four.
The chain tests assert the digest round-trips and that a revoked *chain* refuses
continuation; none asserts that a record revoked by the *other* failure mode
refuses it, and none mutates a serialized field without rehashing. 197's
agreement tests cover kappa on independent pairs and never a grouped file. The
gap is not coverage in the usual sense: each test checks the path its author was
thinking about.

**The coordination failure, which is the reason these sat unread.** Codex posted
findings to the shared board from post 13 onward. This session had been told to
set Codex aside, and read nothing between posts 12 and 29; the other Claude
session read nothing after post 4. Meanwhile both lines allocated DECISIONS
198, 199 and 200 to different entries. A shared page is not coordination if
nobody reads it.

**How the collision was resolved, by the integrator:** no history is rewritten
and no entry is renumbered. This line's 198-200 stay as they are; Codex's are
preserved byte-for-byte in `docs/decisions/CODEX-PARALLEL.md` with their source
commits and digests, and a later entry documents the mapping. All numbering is
allocated by one owner until integration completes. That is stricter about
append-only than the renumbering this session proposed.

**Status at the time of writing.** The four defects are being fixed by Codex on
`fix/chain-integrity` and `fix/grouped-agreement`, both based on `18dfbae`; this
session holds every file involved and reviews read-only. `certify`, `recheck`
without a chain, `plan`, the frontier and the release path are unaffected by all
four. A merge rehearsal of this line with Codex's stricter input parser
(`9f436d3`) is green apart from the stated test count, which the merge must
refresh.

**What this means for the claims in 8.11 and elsewhere.** The label-sensitivity
results stand: they are arithmetic on counts and do not touch the chain. The
chain's guarantee as stated in 187, 193 and 196 is unaffected as a statistical
claim, but its *record integrity* -- that a kept set of records shows what
happened -- does not hold until the two P0s are closed, and no pilot should run
on a build that hands a validator an artefact with a known integrity defect.

### 8.13 After 8.12: the chain defects closed as a class, and what a documentation pass found

**The status line of 8.12 is superseded.** Codex's claim on the four defects
produced no commit for 22 hours, so this line took the repair over on
`fix/chain-integrity-8a`, after posting the takeover; Codex acknowledged it and
will review the commits independently. **That review has not happened yet**, and
nothing here is merged or pushed.

**The two P0s, and what the repair found beyond them.**

| Pass | What was wrong | Closed by | Suite |
|---|---|---|---|
| 1 | Continuing a record REVOKED by drift; editing `threshold`, `mean_statistic` or `ended`; `alpha` of 0 or NaN crashing the verifier | `continue_chain` refuses any REVOKED record; derived fields compared on load; malformed values refused before arithmetic (`DECISIONS.md` addendum on 194) | `20e3347`: 1,797 passed, 1 xfail, 0 failed |
| 2 | **A forked restart went around a drift revocation**: `--fork` on a revoked warrant returned exit 0 and a VALID record. The guarantee text also said alpha bounds "any false revocation" | the head sidecar records status and a revoked head refuses every continuation; the guarantee names the chain's statistic only (addendum 2026-09-16) | `d9fa4bf`: 1,803 passed, 1 xfail, 0 failed |
| 3 | **The derived-field defect was a class.** A schema-driven audit mutated every leaf of a real two-link chain, 3,210 mutations; 197 edits to the latest record verified clean, including its `status` | every chained record sealed whole; `chain verify` and `--since` recompute the seal; a property test walks every leaf. After: 3,218 mutations, 0 survive (addendum 2026-09-17) | `5b13d22`: 1,812 passed, 1 xfail, 0 failed |

**What the tests had missed, again.** Pass 1 was written against the four
reported instances and passed. Passes 2 and 3 found more of the same defect by
attacking the records from their schema rather than from the report. The lesson
8.12 drew — each test checks the path its author was thinking about — held a
second time, inside the fix for it.

The P1 on grouped agreement remains Codex's, pre-registered and not merged.

**A documentation pass, on `docs/professional-pass`, found these by reading.**
None was caught by a failing test except the first.

| Found | Where | Fixed |
|---|---|---|
| `docs/PILOT-PROTOCOL.md` cited a decision number Codex has pre-registered on its own branch and that does not exist on this line, so `test_decisions_integrity` failed on the branch that introduced it. The same sentence stated Codex's pending grouped-agreement change as current behaviour | this line's own pilot commit | `51c77ba` |
| `drift/psi.py` says its smoothing epsilon is declared in config; it is a module constant | read-only `drift/` | recorded, LIMITATIONS §4.4 |
| ARCHITECTURE and DIAGRAMS described drift as PSI **and MMD** over five features; only token length is computed and MMD is not built. DIAGRAMS drew warrant states the enum does not have and omitted STALE | orientation pages | `d0489d1`, `aeca3ee` |
| FAQ and METHODS said the price list, kappa and the blinded queue were not built | orientation pages | `8789546`, `75db639` |
| SETUP said Python 3.11+; the package and `smoke.py` declare 3.10, and CI tests 3.11 and 3.12 | SETUP | `8f80e56` |
| The README's reading notes pointed at "the last five rows" for two different blocks, counted three refused detectors where four were measured, and claimed every interval was a bootstrap over questions | README | `0092210` |
| `read_json_artifact` told a reader to see `scripts/run_all.py`, which never existed | `config.py` | `32ab29b` |
| `chain.py`'s module docstring still stated the guarantee the 2026-09-16 addendum narrowed | `intake/chain.py` | `aca204c` |
| CODE_TOUR described the gate's agent as "the indirect injection it does not stop"; the gate blocks it | CODE_TOUR | `aca204c` |

**What this section does not establish.** No clean-clone gate has run on either
branch. The chain fix has not been independently reviewed. The documentation pass
checked each page against the code it describes and ran the tests that read
documents; it did not re-derive any measured number, all of which still come from
the claim table (92 of 92 reproduce at `0092210`).

---

## 9. Close-out: both lines integrated on `main`, and the gate

**The question: does one branch now hold all of this sprint's work, with the two
decision logs reconciled and the documents describing the merged code, and does
it pass the gate?**

**Answer: yes.** `main` holds both lines and every branch, the logs are reconciled without renumbering either, and it passes the full suite and the clean-clone gate. Merged at the founder's direction on 2026-09-17, by this
line, before Codex's independent review of the chain fix. That review is still
owed. `main` and every branch were then pushed to GitHub at the founder's
direction.

### 9.1 What was merged, in order

| Commit | What |
|---|---|
| `8432d28` | `docs/professional-pass` into `main`: the chain integrity fix, sprint 12's customer-path work (184-200 on this line and three dated addenda), the handoff and pilot documents, the documentation pass. `main` had only its own merge commit beyond it, so the tree is identical to that branch's |
| `9a75e9c` | Codex's `feat/customer-evidence-integration` (also `feat/shared-context`): the coordination board, refusal of ambiguous scored-input fields, release protocol 2, Codex's review of this line |
| `076f645` | Codex's `fix/grouped-agreement`: `DECISIONS.md` 201, pre-registered and not implemented |
| `8303879` | `DECISIONS.md` 202: the reconciliation |
| `956a9aa` | The documents brought to the merged code |
| `049853b` | Test inventory 1,817 -> 1,867 collected. Pushed to GitHub with every branch |
| `e03279d` | The README's Authors section and team note removed, at the founder's direction: the project was done by one person. Pushed |

Every local branch is now contained in `main`. Two scratch worktrees hold
superseded commits whose patches `git cherry` finds on `main` under other hashes.
Codex's uncommitted edits in the main checkout were not touched and are not on
`main`.

### 9.2 The decision numbers

Both lines had committed different entries as 198, 199 and 200. The mapping
agreed on the board (posts 34 and 36) was carried out as agreed: `DECISIONS.md`
keeps this line's 198-200; Codex's are preserved byte-for-byte in
`docs/decisions/CODEX-PARALLEL.md`, each with its source commits and a SHA-256
of its bytes; 201 is Codex's; 202 records the reconciliation and the two
alternatives rejected.

**The citation defect this could have caused, and nearly did.** Codex's code
and documents cited its own 198-200 as `DECISIONS 198` and so on. After the
merge those citations still *resolve*, to this line's unrelated entries, so
`test_decisions_integrity` passes on every one of them. The first search found
six and repointed them. A second, broader search found a seventh,
`(DECISIONS 185, 200)` in `intake/contract.py`, which the first pattern missed
because the number did not follow the word directly. All seven now name the
parallel log. **No test can catch this class**: a citation that resolves to the
wrong entry is indistinguishable from a right one to anything that checks
existence.

### 9.3 What the documents had to absorb

- **Release protocol 2.** `docs/METHODS.md` §19 and `docs/DIAGRAMS.md` §14 said
  an inconclusive release study is UNVALIDATED. Under protocol 2 it is REFUSED
  with a named reason; UNVALIDATED survives only for protocol-1 replay.
- **Strict input.** `docs/INPUT.md` and `docs/TROUBLESHOOTING.md` gained the four
  new refusals (duplicate names, blank headers, ragged rows, malformed CSV), with
  the messages the code prints.
- **`intake/contract.py`'s module docstring** still said extra columns are
  "carried into the artifact untouched", the claim `docs/INPUT.md` corrected in
  section 12 of the review pack. No writer uses them. `tests/test_intake.py`'s
  docstring made the same claim. Both corrected.
- `CODE_TOUR`, `TESTING` and `CASES` gained the coordination package and the new
  suites; every test `CASES` names exists.

### 9.4 The gate

| Check | At | Result |
|---|---|---|
| Full suite, in the integration worktree | `049853b` | **1,866 passed, 1 xfail, 0 failed** in 33 minutes; 1,867 collected, matching the refreshed inventory. The xfail is `DECISIONS.md` 179's strict one |
| Clean-clone gate | `e03279d` | **PASSED.** A fresh clone of 543 tracked files matched source HEAD; smoke passed; the full suite passed inside the clone (exit 0, the same xfail); `verify` reproduced the claim table **92/92** and the frozen-score metrics **25/25**. The activation tier was skipped, as on every clone, because the caches are gitignored. Record: `results/clean_clone.json`, committed at `5f5e3c4` |
| Between the two | | The only commit after `049853b` and before `e03279d` removes the README's Authors section; no test reads those lines |

One note from the gate, not a failure: Windows denied deletion of a git object in
the temporary clone, leaving about 26 MB in `%TEMP%`.

### 9.5 What this does not establish

- **No human has reviewed the merged line**, and Codex has not reviewed the chain
  fix. A passing suite says that the tests which exist pass; sections 8.12 and
  8.13 are the record of what the tests did not cover.
- **One machine, one platform**: Windows, Python 3.12.10, CPU.
- **CI on the pushed commits was not observed from here**: the GitHub CLI is not
  installed on this machine.
- Everything section 3 and `docs/LIMITATIONS.md` list is unchanged: no customer,
  no production traffic, no human labels, no second model family.

### 9.6 Open, and what would close it

The full list, ordered, with owners, is `reports/NEXT-STEPS-2026-09-17.md`. The
item that blocks everything else is a decision for the founder: whether the
registered conversations run.

### 9.7 Ledger

```bash
git checkout main                                    # gated at e03279d
python -m pytest tests/ -o addopts="--strict-markers"
python scripts/verify.py
python scripts/clean_clone_gate.py
git show 55528c7:DECISIONS.md                        # Codex's original 198-200
```
