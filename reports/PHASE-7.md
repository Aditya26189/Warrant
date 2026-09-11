# Phase 7 — the whole chain, rebuilt from the caches

**The question: does this repository's evidence actually reproduce, or does it
only pass the checks it wrote for itself?**

**Answer: it reproduces. 401 measured numbers, regenerated from the committed
activation caches on a different day from an empty audit ledger, and not one of
them moved.** The only differences between the committed artifacts and the
rebuilt ones are provenance timestamps and commit hashes.

That is a stronger statement than `make verify` makes. Tier 3 re-runs the
extraction-tier validation and compares; this re-ran the **whole chain** — the
eval-set build, the validation, the text detectors, the long-context transfer —
and rebuilt the warrant matrix from a ledger with nothing in it.

It also closes the contract item Phase 5 left open: `results/RESULTS.md` now
carries the computed price list, κ, and the score-free certification cost.

- **Window:** 2026-09-11
- **Range:** `2ecdeb2` → `HEAD`
- **Suite:** 1,224 at open -> 1,235 at close, green at both
- **Verification:** **66/66 claims, 25/25 frozen scores, 3/3 activations** — all
  three tiers, for the first time this session
- **Artifacts:** 15 regenerated, listed in §5
- **Decisions:** `DECISIONS.md` 157, 158

---

## 1. Why this was open

`DECISIONS.md` 155 built the renderer and could not fill the document. A fresh
run of `03_matrix.py` produced 21 table rows against the committed 32 and
**zero** of the 15 measured rows, so committing it would have regressed the
artifact. The conclusion at the time was that regenerating needed the full
chain, and the chain starts at `00_extract.py`, which needs a GPU.

**That was half right.** The chain does start at extraction — but extraction's
output is the `results/cache-*.npz` files, and those are on disk. Everything
downstream of them is CPU work. What was actually missing was not a GPU; it was
running the documented order instead of one script.

---

## 2. What the first attempt got wrong, twice

**`03_matrix.py` alone ablates only the synthetic envelopes.** The measured
warrants come from `02_validate.py` on `triviaqa-600` and `04_transfer.py` for
the long-context envelope, and the matrix is assembled from whatever the ledger
has accumulated. Running the matrix by itself produces a document that says
*Outstanding measurement* — which is honest, and only helps if somebody reads
it.

**And `02_validate.py` cannot run on the long-context envelope at all.** The
second attempt tried it and got:

```
controlplane.detectors.probe.ProbeError: train_index is empty
```

That envelope has no train split, because it is scored by *transfer* — a probe
fitted on `triviaqa-600` and evaluated on the long-context set with nothing
retrained. The script does not say so; it fails three layers down in the probe.

Both are recorded as an open item rather than fixed: **the run order is
documented in `docs/RUNBOOK.md` and enforced nowhere.**

---

## 3. What the rebuild proves

Run in the documented order against the committed caches, with the pre-110
ledger moved aside:

```
01_build_evalsets → 02_validate (triviaqa-600) → 09_detectors
                  → 04_transfer → 03_matrix
```

Then every numeric metric in every regenerated artifact compared against its
committed version:

| artifact | metrics compared | moved |
|---|---|---|
| `warrant_matrix.json` | 141 | **0** |
| `detectors.json` | 80 | **0** |
| `transfer-T1-*.json` (3) | 78 | **0** |
| `validation-T1-*.json` (3) | 39 | **0** |
| `validation-pii-reference-*.json` (3) | 30 | **0** |
| `tier_ladder.json` | 18 | **0** |
| `evalset_validation.json` | 15 | **0** |
| **total** | **401** | **0** |

The rebuilt ledger holds 20 records with the hash chain intact, against the 45
the local one had accumulated since August.

**This is the reproducibility claim the repository has been making, tested in
the one way that could have falsified it.** Every prior check compared a number
against the artifact it came from. This regenerated the artifact.

---

## 4. What `RESULTS.md` carries now

`CLAUDE.md`'s definition of done asks it for *"the warrant matrix, the tier
ladder, drift/revocation traces, the computed price list, and κ"*. The last two
existed nowhere until Phase 4 and Phase 5 built them.

| | before | after |
|---|---|---|
| table rows | 32 | **48** |
| measured rows | 15 | **15** |
| the price list | absent | **present**, with `dR/dq` and both regimes |
| κ and the blinded queue | absent | **present** |
| score-free certification cost | absent | **present** |
| *Outstanding measurement* banner | — | **gone**, the measurements landed |

Every section whose artifact is missing names the script that writes it rather
than disappearing, which is checked against an empty directory in
`tests/test_price_list_sections.py`.

---

## 5. What this does not establish

- **It does not re-run extraction.** The caches are the input, not the output.
  If the activations in them are wrong, everything here is consistently wrong
  and this phase would not have noticed. `make verify` tier 3 compares against
  those same caches, so the two share that assumption.
- **It is one machine, one platform.** Windows, Python 3.12.10, CPU. The library
  versions are in every provenance block. A different platform is untested and
  `DECISIONS.md` 145 records that the suite's first Linux run found a defect
  nobody had seen.
- **The ledger was rebuilt, not migrated.** The 45 records accumulated since
  August still exist as `results/controlplane.db.pre-110`, and 34 of them remain
  unreadable by the current model. Nothing here recovers them.
- **The rebuilt matrix has more populated cells than the committed one.** That
  is because a single ledger now holds every script's warrants rather than a
  ledger accumulated across schema changes. The extra cells are `UNVALIDATED`
  and `REFUSED` states made visible, not new measurements.

---

## 6. Open items

| # | item | what would close it |
|---|---|---|
| O-1 | **A chain dirties its own tree.** `01_build_evalsets.py` writes `evalsets/manifest.json`, which `provenance()` does not exclude, so every stage after it records `dirty: true`. The August artifacts carry the same flag. Worked around here by committing and re-rendering; not fixed. | Exclude generated corpora from the dirty check, or make the chain one stage. |
| O-2 | **The run order is documented and not enforced.** Running a stage out of order succeeds and produces a quietly incomplete artifact. **Partly closed** — see §6a. | Each script refusing when the artifact it reads is absent or older than its own input. |
| O-3 | Carried forward: the twelve conversations; certifying a real judge; `DECISIONS.md` 145's Linux abort; rule 1 duplicated between the gate and the Rego bundles. | See `reports/PHASE-5.md` §5 and `reports/PHASE-6.md` §6. |

---

## 6a. Closed at write-up: the one case that actually bit

O-2 is a design problem and I did not want to leave it as one, because the case
that occurred is closeable in a page.

`controlplane/report/regression.py` counts **populated cells** — a cell carrying
a `warrant_id`, meaning something was measured or refused there — and
`03_matrix.py` now refuses **before writing anything** if the incoming matrix
has fewer than the artifact on disk. Verified end to end against a directory
holding the committed matrix and a fresh ledger:

```
REFUSED: this run would replace a matrix of 17 populated cells with one of 11.
...
Nothing has been written.
```

and nothing was.

**The hard part was not the check; it was what the message should say.** The
poorer document is *not dishonest* — every missing cell reads `UNVALIDATED`,
which is what it is. A refusal that implied fraud would teach its reader to
distrust the wrong thing, so the message says so explicitly, then names the
likely out-of-order run and the two scripts whose warrants are missing. *Refused:
17 → 11* alone would send an operator to read the module instead of the runbook.

**The override needed justifying against `CLAUDE.md` invariant 3**, which is
absolute: *refusal has no override*. That rule is about **warrants** — a claim
the evidence does not support must not be issuable by anyone, and a bypass would
make the product theatre. This guards against clobbering a file, where the
operator sometimes genuinely wants the emptier document, and refusing with no way
through would mean deleting the artifact by hand to proceed.
`--allow-matrix-regression` prints what it discards, is unreachable from any
warrant path, and a test records the distinction so it cannot be cited as
precedent.

It guards one artifact, and the general problem stays open. Closing the case that
bit is worth more than a design for the ones that have not.
`DECISIONS.md` 158, `tests/test_matrix_regression.py`, 8 tests.

---

## 7. Ledger

**Regenerated** — `results/RESULTS.md`, `warrant_matrix.{json,md}`,
`detectors.json`, `tier_ladder.{json,png}`, `evalset_build.json`,
`evalset_validation.json`, `transfer-T1-*.json` (3),
`validation-T1-*.json` (3), `validation-pii-reference-*.json` (3),
`evalsets/manifest.json`.

**Changed** — `.gitignore` gains `results/*.db.pre-*`, so the stale ledger the
preflight tells an operator to rename has somewhere to live outside the
repository.

**Decisions** — 157, 158.

**Added at write-up** — `controlplane/report/regression.py`,
`tests/test_matrix_regression.py` (8 tests), `--allow-matrix-regression` on
`03_matrix.py`.

**Reproduce**

```
mv results/controlplane.db results/controlplane.db.pre-110
python scripts/01_build_evalsets.py --config config.yaml
python scripts/02_validate.py --config config.yaml --cache results/cache-triviaqa-600.npz --eval-set triviaqa-600
python scripts/09_detectors.py --config config.yaml
python scripts/04_transfer.py --config config.yaml \
  --source-cache results/cache-triviaqa-600.npz \
  --target-cache results/cache-triviaqa-longctx-600.npz \
  --source-eval-set triviaqa-600 --target-eval-set triviaqa-longctx-600
python scripts/03_matrix.py --config config.yaml
python scripts/verify.py
```

---

## 8. What this changes

**The strongest sentence this repository can now say about itself is not about a
detector.** It is: *every measured number here was regenerated from the raw
caches on a different day, from an empty audit ledger, and none of them moved.*

Four hundred and one of them.

That is the claim a model-validation function is actually buying. The probe's
recall is 0.0794 and that is a modest number; the fact that 0.0794 comes back
identical from a cold rebuild is the thing that makes it worth quoting at all.

**And the phase found its defects where the previous three did.** Not in a
wrong number — in a documented order nobody enforces and a provenance exclusion
list that is one entry short. `DECISIONS.md` 147, 151, 153, 156 and now 157:
five phases, and every finding has been a control aimed at the wrong thing
rather than a number computed incorrectly.
