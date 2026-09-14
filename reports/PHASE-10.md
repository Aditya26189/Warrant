# Phase 10 — the specification, walked against what shipped

**The question: does `docs/SPEC.md`, the binding contract, describe the system
this repository actually built?**

**Answer: no, and the ways it was wrong were worse than drift.** With this phase every
one of the eleven sections has been walked — §10 and §11 in Phase 9, the rest
here. The shipped code was mostly right. The specification
**misquoted a regulation, presented synthetic-fixture measurements as real ones,
stated a property of a frozen eval set that the project's own extraction cache
contradicts, kept a hand-typed price table under a sentence forbidding one, and
promised a revalidation nothing schedules.** Walking it also found invariant 5
unenforced at the two surfaces a reader stops on — and fixing that put an
unflattering number in the claim table: our reference PII detector's recall lead
on Hinglish is bought with precision (0.6532 against Presidio-custom's 0.8630).

- **Window:** 2026-09-13 to 2026-09-14
- **Range:** `e307718` → `HEAD`
- **Suite:** 1,319 → 1,345
- **Verification:** claim table 66/66 → **77/77**; frozen scores 25/25; activations 3/3
- **Decisions:** `DECISIONS.md` 168–177
- **Method:** CPU only; the Qwen2.5-7B tokenizer and the installed Presidio read
  locally; six primary sources fetched

---

## 1. The findings, by section

| § | what the spec said | what is true | fixed |
|---|---|---|---|
| 1.5 | DPDP Rule 6 requires the store be queryable by six predicates | Rule 6(1)(c) requires visibility on access and names no predicate; 6(1)(e) says one year; "minimum" is Rule 8(3); both commence 13 May 2027 | spec and seven files; two read-only files **OPEN** |
| 2.1 | null spread 0.068 / 0.271; closed form understates by 2.1x / 8.3x; 8 / 22 / 125 repeats | all **fixture** figures; the real 3,584-feature probes measure **0.7–1.0x** and resolve at 8 repeats | labelled in five documents |
| 2.1 | (artifacts) "0.8x the closed form, which is why the closed form is not the reference" | a non sequitur in every real validation artifact | note branches on the ratio; rebuilt artifacts carry it |
| 2.3 | five refusal criteria | six — lift lower bound ≤ 1.0 (`DECISIONS.md` 043) | spec + a test mapping every criterion |
| 3 | matrix cell `R=… @f=…`; "the matrix self-populates" | recall without precision; the enqueue callback logs | precision added; annotated |
| 4 | `triviaqa-longctx-600` is 4–16k tokens | **2,838–11,103, median 6,954, 82 of 600 under 4,000** | corrected everywhere it was claimed |
| 5 | five envelope features, PSI + MMD, STALE triggers revalidation | **one** feature computed; no MMD; nothing schedules revalidation | disclosed; ladder message **OPEN** (read-only) |
| 6.4 | ~847 / ~5,292 labels, typed; FPR free | superseded (computed: 1,014); FPR depends on the estimated misses | annotated |
| 6.5 | "published work: 48% agreement" | RedactionBench: 47.7% consensus **with target labels** — not a κ | cited |
| 7.4 | the weighted-error objective picks τ | **no shipped point is chosen by it**; all three are flag-rate budgets, and the weights are identical across bundles | disclosed |
| 8.1 | Presidio HIGH recall 0.07, uncited | REDACT, partial overlap, LLM-generated documents; recognisers verified in 2.2.364 | cited |
| 9.1, 9.4 | — | match | — |

**One class covers most of the table: a claim true in the context it was
written in, copied into one where it is not.** Fixture measurements into the
spec that governs real ones. A builder's *target* into the description of what
it built. A spec's *plan* for five features into a config that reads as five
monitored. A regulator's *purpose* into a list of the project's own design
choices. Each was right once, somewhere.

---

## 2. The long-context envelope is shorter than every document said

`results/cache-triviaqa-longctx-600.npz` records `__token_lengths` from the GPU
extraction: **2,838 to 11,103 tokens, median 6,954; 82 of 600 prompts under
4,000.** Recounted locally with the cached tokenizer on the frozen prompts:
2,813 to 11,078, 83 under 4,000. The builder sized padding at 4.0 characters per
token and this filler tokenises at 5.77.

**The number was on disk the whole time.** The notebook's check read only the
maximum, and 11,103 is inside 4–16k.

What survives: the shift is still ~165x the short-context median, and the
mean-pool collapse and last-token survival are measured on the set as built.
What does not: any sentence saying 16k. Two construction facts nobody had stated
also bound the result — the padding repeats eight paragraphs, and labels are the
short-context pass's. Both are now in `docs/LIMITATIONS.md` §2.5. The set is
frozen and was not rebuilt. `DECISIONS.md` 171.

---

## 3. Invariant 5 was enforced everywhere except where a reader looks

*"Precision and recall travel together."* The register named a blended-score
test and the FPR sweep. The matrix cell rendered recall and flag rate. The README
claim table had **nine** recall rows with no precision beside them.

A test for each surface; eleven rows added, each checked by `scripts/verify.py`.

**What that made visible:**

| `hinglish-pii-200` | recall | precision |
|---|---|---|
| `pii-reference` (ours) | 0.7941 [0.6981, 0.8846] | **0.6532 [0.5114, 0.8100]** |
| `presidio-enabled_plus_custom` | 0.6176 [0.5185, 0.7128] | 0.8630 [0.7262, 0.9828] |

The recall row alone read as a clean win for our detector. It is a trade. That
is the entire reason the invariant exists, and the README broke it in the one
place where breaking it flattered us. `DECISIONS.md` 170, 176.

---

## 4. A committed matrix is true for 24 hours

Re-rendering the matrix after the rendering fix turned **all 13 VALID cells
STALE**. `warrant_ttl_hours` is 24 and the ledger's warrants were two days old.
The product was right; the consequence was undocumented: `RESULTS.md` is a
snapshot, and `03_matrix.py` reads the ledger rather than re-issuing, so a
development machine cannot reproduce a VALID cell a day later — and should not.

**Rejected: render "as of" issuance.** Printing VALID for an expired warrant is
the stale claim the TTL exists to stop; a flag that does it is an override by
another name.

**Done instead:** the chain was rebuilt from the committed caches with the ledger
moved aside:

| | |
|---|---|
| artifacts regenerated | 17 |
| numeric fields compared against the committed versions | 3,075 |
| fields that moved or changed shape | **0** |

Every regenerated artifact records `dirty: false`; the set it replaced recorded
`dirty: true`. `RESULTS.md` now opens its matrix with the render time and says
the VALID cells report STALE if re-rendered 24 hours later. `DECISIONS.md` 177.

---

## 5. Defects found in this phase's own work

- **`DECISIONS.md` 171 cited the wrong entries** (045–046 for 051–052, and
  156–158 for 156). Caught by checking the citations before continuing.
- **`DECISIONS.md` 168 named a function that does not exist**
  (`certify_verdict` for `certify_drift_response`), and 177 counted seven
  commits where the scan found six. Both corrected before they were cited.
- **The patch scripts converted CRLF files to LF.** Whole-file diffs in six
  commits since `report-4`, 13 files. `40031b6` was amended before it left the
  machine; the rest are recorded and left, because the repository has no
  line-ending norm to restore. Found by reading `git diff --stat`, which no test
  reads. **And the rule was already written**: `docs/CONTRIBUTING.md`, *"Do not
  let a tool rewrite line endings"*, gives the bytes-safe form. It was not read
  before the scripted edits started (corrected 2026-09-14, `DECISIONS.md` 177).
- **A shell heredoc failed to append four entries** with a parse error;
  nothing was written, and the entries went in through a file instead. Not
  silent, but only because the shell said so.

---

## 6. What this does not establish

- **The walk checked each section against code and artifacts, not against
  intent.** A section that matches what shipped can still specify the wrong
  thing.
- **The lift interval is still the fixed-flag-rate one.** It is pinned as
  conservative at the lower bound; a correct joint interval would issue warrants
  the current bar refuses, and that is a threshold change needing its own
  pre-registered entry.
- **Nothing here re-measured the long context.** The corrected range describes
  the set as built; no result past 11,103 tokens exists.
- **Four of five drift features, MMD, background revalidation, on-traffic FPR and
  weight-driven threshold selection remain unbuilt.** They are now disclosed, not
  delivered.

---

## 7. Open items

| # | item | what would close it |
|---|---|---|
| O-1 | `store/ledger.py`, `drift/certify.py` still carry the DPDP attribution 168 corrected elsewhere — the rule names no predicate | docstring wording in read-only code; then delete them from `KNOWN_READ_ONLY` |
| O-2 | `drift/ladder.py` says revalidation is scheduled; the 1.5x factor is a default argument, not config | read-only `drift/`; a scheduler, or the sentence removed |
| O-3 | `Metric.n` on a rate is the set size | read-only `validation/stats.py` |
| O-4 | lift's upper bound exceeds the physical ceiling | a pre-registered decision on the joint interval |
| O-5 | four drift features and MMD | build them, or remove them from `config.yaml` |
| O-6 | carried: eight to twelve customer conversations; a real LLM judge; `DECISIONS.md` 145's Linux abort; rule 1 duplicated in gate and Rego; the §11.6 revocation trace; eight read-only estimators without derivations | see `reports/PHASE-9.md` §6 |

Carried item O-1 of `reports/PHASE-7.md` — *a chain dirties its own tree* — **did
not recur** in this rebuild: `evalsets/manifest.json` was rewritten
byte-identical, and the tree was clean outside `results/` before every stage.
It is not closed by a fix; it stops firing when the corpora do not change.

---

## 8. Ledger

**Code** — `controlplane/matrix/matrix.py` (precision in the cell),
`controlplane/report/results.py` (denominators, lift lower bound, the 24-hour
snapshot note),
`controlplane/validation/controls.py` (the note), `scripts/03_matrix.py`
(masked standalone matrix); docstrings in `model/{certificate,override,serde,enums,metrics}.py`,
`config.py`, `evalsets/builders.py`.

**Tests** — `test_regulatory_attribution.py`, `test_lift_interval.py`,
`test_spec_refusal_criteria.py`,
`test_claims.py::test_every_recall_claim_travels_with_precision`,
`test_matrix.py::test_a_valid_cell_carries_precision_beside_recall`,
`test_validation.py::test_the_null_note_is_true_at_the_ratio_measured`,
`test_fixture_guards.py::test_results_say_when_their_statuses_expire`.

**Artifacts** — the measurement chain rebuilt on a clean tree (`4deb282`), and
`RESULTS.md` re-rendered with its expiry stated (`abe0f02`).

**Documents** — `SPEC.md` §1–§8 annotated, §1.5 corrected in place;
`LIMITATIONS.md` §2.5, §2.6, §3.4 added, §3.1–3.2 closed; `CLAUDE.md` layout
reconciled; `METHODS`, `ARCHITECTURE`, `DIAGRAMS`, `TROUBLESHOOTING`, `GLOSSARY`,
`ARTIFACTS`, `ONBOARDING`; README claim table 66 → 77 rows.

**Decisions** — 168 (§1, DPDP), 169 (§2), 170 (§3, invariant 5), 171 (§4, token
lengths), 172 (§5), 173 (§6), 174 (§7), 175 (§8–9), 176 (rendering), 177 (the
24-hour snapshot).

**Sources** — DPDP Rules 2025, Rules 6 and 8; RedactionBench, arXiv:2606.18782;
REDACT, arXiv:2606.19881; Qwen3Guard-Gen-0.6B model card; LettuceDetect
repository.

**Reproduce**

```
python -m pytest tests/ -q
python scripts/verify.py
sh scripts/run.sh python scripts/03_matrix.py --config config.yaml   # STALE after 24h, by design
```

---

## 9. What this changes

**The contract now says what the system does, including where it does less.**
Before this walk a reader of `SPEC.md` believed the envelope was watched on five
axes, the long context reached 16k tokens, a regulator dictated the audit
schema, and the weights in each bundle chose each threshold. None was true, and
none was hidden by the code — the monitor names unscored features, the cache
records token lengths, the ladder calls its factor declared policy. **The code
was honest and the documents were not**, which is the inverse of the usual
failure and harder to find, because nothing fails.

And the finding that matters most for a buyer was not in the spec at all. It
was a row missing from the claim table, and restoring it made our own detector
look worse. That is what the invariant is for.
