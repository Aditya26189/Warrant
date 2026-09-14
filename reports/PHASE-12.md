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
| O-3 | **Codex's release path marks a tested-but-inconclusive holdout UNVALIDATED.** Invariant 2 reserves UNVALIDATED for "never tested here", and `certify` refuses the same case; the same file can be REFUSED by one command and UNVALIDATED by the other | a product decision, then a change to one of the two paths |
| O-4 | **Codex's release path sets a second standard for VALID**: a two-sided interval at alpha/5 per rate, roughly a one-sided alpha/10, beside `certify`'s one-sided alpha | the same review as O-3 |
| O-5 | **`FPRMonitor`'s cap** (187) | an owner for read-only `validation/warrant_stats.py` |
| O-6 | **Merge order.** Five branches chain on `feat/release-evidence`, which no human has reviewed; only 182-183 are on `main` | a human review of that branch, then `--no-ff` merges in chain order |
| O-7 | **This branch carries 191's code at `945f08b`, before its post-artifact fix** (`ca5ceab`, `1c13492` on accenture-8a's line) | merging accenture-8a's fixed line ahead of or into this one |
| carried | demo video; read-only defects; four drift features and MMD; customer conversations; `DECISIONS.md` 145's Linux Rego abort | `reports/PHASE-11.md` §6 |

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
