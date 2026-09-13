# Next steps — where the 2026-09-13 session stopped

**Not a phase report.** A work queue, written when the session was stopped, so
the next session starts on the right item instead of re-deriving it. Every item
names the entry that records it, the files it touches, and what "done" means.
Delete this file once the queue is empty or superseded by `reports/PHASE-10.md`.

---

## State at stop

| | |
|---|---|
| last commit | `0b843fe` — DPDP attribution fix and `SPEC.md` §1 walk (`DECISIONS.md` 168) |
| at stop | `DECISIONS.md` 169 and this file committed together, on top of `0b843fe` |
| suite | 1,331 tests at `0b843fe`. The touched suites and the DECISIONS, reports, invariants and attribution guards passed; the full run was still going at stop — **rerun it first** |
| claim table | 66/66 at `e307718`; no measured number has moved since |
| `SPEC.md` walk | §1, §6.2, §9.2–9.3, §10, §11 reconciled. §2 walked, **findings unfixed**. §3–§5, §6.1, §6.3–6.5, §7, §8, §9.1, §9.4 not walked |

Rules that bind every item below: no AI co-author trailer on any commit; the
read-only zones (`validation/warrant_stats.py`, `validation/stats.py`,
`store/ledger.py`, `drift/**`, `policy/**`, existing `results/`) are read and
called, never edited; a `DECISIONS.md` entry before the code it justifies; no
artifact from a dirty tree; `sh scripts/run.sh` for any command whose exit
status matters; update the test-count badge in `README.md` and the `Makefile`
comment whenever tests are added.

---

## 1. Fix the `SPEC.md` §2 findings — `DECISIONS.md` 169

In this order; the first three are text only and move no number.

### 1a. Label the fixture figures, and state the real ones beside them

- **Files:** `docs/SPEC.md` §2.1 paragraph 3; `config.yaml` comment above
  `null_control_min_repeats` (a comment edit does not change the config hash —
  the hash is over parsed values, `controlplane/config.py::config_hash`);
  `docs/METHODS.md` §3; `docs/ARCHITECTURE.md` (the "measured, not assumed"
  paragraph); `controlplane/validation/controls.py` — the `label_shuffle_control`
  docstring and `_null_auroc_se_closed_form`.
- **Say:** 2.1x / 8.3x, 0.068 / 0.271 and 8 / 22 / 125 repeats are from the
  **fixture** (`DECISIONS.md` 031, base rate 0.152). The real T1 runs measure
  0.7–1.0x the closed form (0.0237) and resolve at 8 repeats — cite
  `results/validation-T1-*.json` `controls[1..2].detail`. The empirical rule
  stays: free, and it guards the low-dimensional case, which has no real
  instance yet.
- `docs/DIAGRAMS.md` and `docs/TROUBLESHOOTING.md` are orientation pages and
  carry no numbers: change "understates the spread here" to "can understate the
  spread — a fitted probe's scores are not exchangeable" with no figure.
- **Done when:** a grep for `2.1x`, `8.3x`, `0.068`, `0.271` outside
  `DECISIONS.md` finds each next to the word *fixture*.

### 1b. The non sequitur in every validation artifact

- **File:** `controlplane/validation/controls.py::_summarise_null`, the `note`.
- **Change:** branch on `ratio`. Above 1: "wider than the Hanley-McNeil closed
  form, which is why the measured spread is the reference". At or below 1:
  "within the closed form on this run; the measured spread is still the
  reference because the closed form understates it at low dimension (fixture,
  DECISIONS.md 031)".
- **Test:** `tests/test_validation.py` — a null with spread under the closed
  form must not produce "which is why the closed form is not the reference".
  `tests/test_demo.py:284` asserts `"null spread"` is in the detail; keep it.
- Existing artifacts keep the old sentence until the next chain run. Say so in
  the commit body.

### 1c. The ±2 SE floor in `docs/METHODS.md`

Delete the sentence "A ±2 SE floor is retained as a backstop …"; replace with
what `_summarise_null` does: pass requires the mean inside the band **and**
SE of the mean ≤ half the band's half-width, else fail as underpowered.

### 1d. §2.3 lists five refusal criteria; the code enforces six

Add the lift criterion to `docs/SPEC.md` §2.3 — lift lower bound ≤ 1.0,
`DECISIONS.md` 043, `issuance.py::MIN_LIFT_LOWER_BOUND` — and a note that 1.0 is
a definitional null (random sampling at the same budget), which is why it is a
constant and not a config value. A mechanical check fits the pattern of
`tests/test_invariants.py`: every `criterion=` string in `issuance.py` appears
in §2.3.

### 1e. The lift interval: correct the reason, pin the conservatism

- **File:** `controlplane/model/metrics.py::WarrantMetrics.lift` docstring. The
  claim "the flag rate's uncertainty is an order of magnitude smaller" is false
  (relative half-widths: recall 0.38–0.40, flag rate 0.36–0.40). The real reason
  the lower bound is safe: recall and flag rate are positively correlated —
  true positives are a subset of flagged items — so holding `f` fixed
  **widens** the ratio's interval.
- **Test (new):** for each `results/validation-T1-*.json`, rebuild labels and
  flags from `base_rate`, `confirmed_errors.value` and `confirmed_errors.n`,
  bootstrap lift jointly (2,000 draws, seed from config), and assert the shipped
  `ci_low` ≤ the joint lower bound. At stop the gap was 1.19–1.29 vs 1.59–1.71.
- **Do not change the computation in this item.** A tighter interval would issue
  warrants the current bar refuses. If wanted, that is a separate pre-registered
  `DECISIONS.md` entry recording the original bar and the reason.
- **Record, and decide separately:** the shipped upper bound (2.68–2.84) exceeds
  the physical ceiling `1/max(b, f)` = 2.166, and `report/sweep.py`,
  `validation/fpr_sweep.py` and the refusal message print it. Options: clip the
  rendered upper bound at `lift_ceiling` with a note, or stop printing the upper
  bound. Needs an entry either way.

### 1f. What `n` means on a rate — read-only root, non-read-only mitigation

- `validation/stats.py::estimated` sets `n = labels.size`, so recall 23/277 and
  precision 23/25 both read `n = 600`. **Read-only: do not edit.** It stays OPEN
  for human review.
- Mitigation that is allowed: define `n` in `docs/ARTIFACTS.md` and
  `docs/GLOSSARY.md` ("items in the eval set the bootstrap resampled; the
  proportion's denominator is positives for recall, `confirmed_errors.n` for
  precision, negatives for FPR"), and add the denominator to the RESULTS.md
  matrix table rendered by `controlplane/report/results.py` — which changes
  `results/RESULTS.md` and must be regenerated from a clean tree
  (`python scripts/03_matrix.py`), an `exp:` commit.

### 1g. "Precision carries no interval" — scope it

- **Files:** `README.md` (the "Yield is exact; rate is estimated" paragraph under
  the three clauses) and `controlplane/report/price_list.py` (the same sentence
  rendered into `results/RESULTS.md`).
- **Say:** the flagged stratum **of your traffic** is reviewed in full, so this
  month's confirmed-error count and precision on it are a census and carry no
  sampling interval. The eval-set precision in the claim table is a different
  estimand — the detector's precision, estimated from a sample — and carries one.
- `tests/test_readme_prose_numbers.py` and `tests/test_price_list_sections.py`
  may pin the sentence; run both.

---

## 2. Continue the `SPEC.md` walk

One section per commit, one `DECISIONS.md` entry per section, reconciliation
paragraphs **added** under the section rather than rewriting it (except a
misquotation of a third party, which is corrected in place — 168's precedent).

| section | check against | first thing to verify |
|---|---|---|
| §3 matrix and routing | `controlplane/matrix/`, `results/warrant_matrix.json` | the §3.1 illustrative table vs the shipped matrix — `hinglish-pii-200` and T2/T3 rows; `route()` pseudo-code vs `matrix/routing.py`; whether `enqueue_for_validation` exists |
| §4 eval sets | `controlplane/evalsets/`, `evalsets/manifest.json` | "`triviaqa-longctx-600` padded to 4–16k tokens" against the builder and the frozen set; `agent-actions-N` exists or not; "hand-built, not LLM-generated" against the builders' provenance |
| §5 drift and revocation | `controlplane/drift/` (read-only) | PSI/MMD parameters vs config; the revocation ladder states; any external claim (PSI bands are credit-scoring rules of thumb — cited?) |
| §6.1, §6.3–6.5 | `controlplane/sampling/`, `economics/` | allocation, κ floor, price list against `results/on_traffic/` |
| §7, §8 | read first; unknown | — |
| §9.1, §9.4 | `controlplane/gate/`, `results/gate/` | registry classes; the injection scenario as specified vs `run_injection_scenario` |

Every external claim met on the way gets the treatment 160 and 168 gave theirs:
fetch the primary source, quote the clause, correct what does not match.

---

## 3. Close the walk

- `reports/PHASE-10.md` — the SPEC walk as a phase: question (does the binding
  spec describe what shipped?), answer, findings by section with artifact paths,
  what it does not establish, open items, ledger. The unfavourable findings go in
  the first two lines. Include 168's misquotation and 169's fixture-as-real
  figures as the headline class: **claims copied from a context where they were
  true into one where they are not.**
- Update `reports/PHASE-9.md` open item O-1 with the walk's status.
- Tag `report-10`.

---

## 4. Carried open items — need a human, or a key, or a GPU

| item | where recorded | what would close it |
|---|---|---|
| eight to twelve customer conversations, with a registered falsifier | `reports/STRATEGY-2026-09.md` | the founder holding them |
| certifying a real LLM judge | `reports/PHASE-6.md` O-3 | an API key; `scripts/26_scorefree.py` against real votes |
| Linux Rego abort | `DECISIONS.md` 145 | a fix in `policy/**` (read-only) |
| rule 1 duplicated in the gate and the Rego bundles | `reports/PHASE-8.md` §5 | one owner, decided by a human |
| the chain dirties its own tree (`evalsets/manifest.json`) | `reports/PHASE-7.md` §6, O-1 | a builder that writes only on change, or excluding generated corpora from the dirty check |
| run order enforced only for the matrix artifact | `reports/PHASE-7.md` §6, O-2 | preflight checks in each script |
| revocation trace missing from RESULTS.md §11.6 | `DECISIONS.md` 164 | a drift run that writes the trace artifact |
| eight read-only estimators without stated derivations | `controlplane/report/invariants.py::READ_ONLY_WITHOUT_DERIVATION` | docstrings in read-only files, by a human |
| DPDP attribution in `store/ledger.py`, `drift/certify.py` | `DECISIONS.md` 168 | docstring wording; then delete both from `KNOWN_READ_ONLY` in `tests/test_regulatory_attribution.py` — the test fails until you do |
| metric `n` on rates is the set size | `DECISIONS.md` 169 item 6 | a change to `validation/stats.py::estimated` (read-only) |

---

## To resume

```
git log --oneline -3
sh scripts/run.sh python -m pytest tests/ -q
python scripts/verify.py
```

Then start at 1a.
