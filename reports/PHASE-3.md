# Phase 3 — does any of this mean anything outside the repository?

**Answer: yes, and our detector is not the best entry in the table.** Seven
detector–task pairings certified across the standard budget grid: five entity
types from Presidio, a widely-used prompt-injection classifier, and our own
probe on identical terms.

**Results: [`results/external/MATRIX.md`](../results/external/MATRIX.md).
Written for outside readers: [`docs/EXTERNAL.md`](../docs/EXTERNAL.md).**

- **Window:** 2026-09-09
- **Range:** `3d68551` → `HEAD`
- **Suite:** 952 at open → 992 at close, no failures at either end
- **Verification:** `verify.py` 40/40 claims, 25/25 frozen scores — unchanged
- **Method:** CPU only. No GPU, no paid API, no vendor contacted.

---

## 1. What was done

| Task | Status | Outcome |
|---|---|---|
| **T0** baseline | done | 952 green. `DECISIONS.md` 131's SHA mapping re-checked by reachability — all 15 reachable, pre-registration ordering intact. |
| **T1** feasibility survey | done | Seven pairings feasible, five Presidio. Gate met. `DECISIONS.md` 139. |
| **T2** Presidio | done | Five entity types, `results/external/presidio-*`. |
| **T3** remaining pairings | done | Prompt-injection classifier on `deepset/prompt-injections`. |
| **T4** our probe, identical terms | done | `results/external/ours-triviaqa/`, same grid, same criterion. |
| **T5** the matrix | done | `results/external/MATRIX.md`, rendered from artifacts on disk. |
| **T6** the write-up | done | `docs/EXTERNAL.md`, 1027 words, aimed outward. |
| **T7** close-out | done | This report. |

---

## 2. The finding that shaped the phase

**Every row of `ai4privacy/pii-masking-200k` contains PII.** Zero of 400 sampled
rows have an empty span list. As a "does this contain PII" task it is
single-class: no negatives, therefore no false-positive rate to bound, therefore
no warrant possible at any budget.

The task is instead defined **per entity type**, from the dataset's own
annotations: positive if the row carries a span of that type, negative if it
does not. Negatives still contain other PII, which is correct — the question is
*"does this contain a credit card number"*, not *"is this clean"*.

The alternative was pairing these positives with negatives from a general
corpus, and that is worse than construction: a Wikipedia sentence naming a
person **does** contain PII, so labelling it negative would put wrong labels into
a false-positive rate. A guard now refuses any single-class pairing outright.

---

## 3. What the matrix says

Recall with 95% interval at the certified threshold, in-sample, for every row.

| detector | task | FPR 0.01 | FPR 0.05 | FPR 0.10 | FPR 0.20 |
|---|---|---|---|---|---|
| presidio 2.2.364 | EMAIL_ADDRESS | 1.000 | 1.000 | 1.000 | 1.000 |
| presidio 2.2.364 | URL | 1.000 | 1.000 | 1.000 | 1.000 |
| presidio 2.2.364 | IP_ADDRESS | 0.000 * | 0.488 | 1.000 | 1.000 |
| presidio 2.2.364 | PHONE_NUMBER | 0.103 | 0.103 | 0.673 | 0.673 |
| presidio 2.2.364 | CREDIT_CARD | 0.070 | 0.070 | 0.070 | 0.070 |
| protectai deberta v2 | prompt injection | 0.350 | 0.616 | 0.729 | 0.813 |
| **ours** | answer incorrectness | 0.011 * | 0.231 | 0.448 | 0.646 |

`*` marks a point where lift's 95% lower bound does not clear 1.0.

**The CREDIT_CARD cell is the one most likely to be misread**, and D36 exists
for it. Presidio's credit-card recognizer validates a checksum; the dataset's
card numbers are synthetically generated. A generated number that fails the
checksum is one the recognizer is *designed* to reject, and declining to fire on
a string that cannot be a real card number is correct behaviour. The cell
measures agreement between one vendor's validation rules and another project's
generator. It is not a quality judgement and `docs/EXTERNAL.md` says so in the
same paragraph as the number.

**Our probe is visibly not the strongest entry.** It is beaten on their own
tasks by every third-party detector in the table. That is what D37 is for: a
comparison in which the author's entry is presented differently is not evidence,
and one where it happens to win is worth less than one where it does not.

---

## 4. How the two failure modes were guarded

**Publishing a refusal caused by our own misconfiguration.** Every detector runs
at its documented default and records, in the artifact and in the matrix, the
exact configuration used, a link to where that default is documented, its
version or revision, and the one command that reproduces the row. Nothing was
tuned in either direction. The claim about Presidio's supported entity set comes
from calling `get_supported_entities()`, and the injection classifier's positive
class index is read from the loaded config's `id2label` rather than assumed to
be 1.

**Presenting our own detector on softer terms.** Our probe is a pairing like any
other, through the same `run_pairing`, the same grid and the same criterion.
Nothing in the registry lets a pairing carry its own grid or its own bar, and a
test asserts that. Every row including ours is in-sample — thresholds certified
on the data they are scored on — which is a real limitation applying identically
to everyone, and stated rather than buried.

---

## 5. What could not be measured

**D33's Indian identifier classes.** No public dataset with Aadhaar, PAN, UPI or
IFSC labels was located; `pii-masking-200k` carries 56 entity types across its
English rows and none is India-specific. This is a gap in public data, not a
finding about any detector, and it is separable from the *coverage* result this
project already measured: presidio-analyzer 2.2.364 exposes 19 supported entity
types, none India-specific, which needs no labelled data. Certifying performance
on those identifiers needs data that does not appear to exist publicly.

**`jackhhao/jailbreak-classification` was deliberately not paired.** It is
reachable and balanced, but running an injection-trained classifier on jailbreak
prompts measures transfer to a task the model does not claim. Reporting that
beside its own task invites exactly the misreading D36 forbids. Recorded as
available for a later phase with a detector that claims the task.

**Anything needing a GPU or a paid key**, unchanged from `DECISIONS.md` 138.

---

## 6. What the closing suite caught

The test-count guard added in Phase 1 fired: the suite collected 992 while
`README.md` and `Makefile` both said 990. The parametrised library-file guards
had picked up `controlplane/external/matrix.py` and `registry.py` after the
count was last written.

Trivial to fix and worth recording anyway, because it is the second time this
guard has earned its place. It exists because the Makefile drifted by 300 tests
across the whole of Phase 0 while only the README was policed; it now names
every file that disagrees, and it named both.

---

## 7. What this does not establish

**These are not rankings.** Rows answer different questions on different data.
What is comparable within a row is the shape across budgets.

**Nothing here is a production warrant.** Every row is in-sample, and each is one
version of one tool on one public dataset at one point in time.

**Perfect separation is a statement about the pairing.** Presidio's email
recognizer scoring 1.000 against synthetic emails says the recognizer and the
generator agree. It does not establish behaviour on messy production text.

---

## 8. Open items

Unchanged from Phase 2 — both still gated on resources:

| Entry | Status | What would close it |
|---|---|---|
| **138** — closed-API matrix | OPEN | Provider credentials for one API exposing logprobs and one not. |
| **138** — corpus expansion, out-of-distribution transfer | OPEN | GPU extraction; size against `internal_knowledge` at 1649 items. |

Phase 3 answers a *different* question from the out-of-distribution one 138
tracks: it shows the machinery works on other people's detectors and other
people's data, not that our probe's numbers survive a corpus it has not seen.

---

## 9. Ledger

| Path | What it is |
|---|---|
| `controlplane/external/registry.py` | detectors, datasets and pairings as declared data |
| `controlplane/external/run.py` | fetch, score, certify through the standard sweep |
| `controlplane/external/matrix.py` | MATRIX.md, rendered from artifacts on disk |
| `scripts/23_certify_external.py` | `--list`, `--pairing`, `--all`, `--matrix-only` |
| `tests/test_external.py` | 38 tests, none touching the network |
| `docs/EXTERNAL.md` | the outward-facing write-up |
| `results/external/` | seven pairings plus the matrix |

**Decisions** — `DECISIONS.md` 139.

**Reproduce**

```bash
python scripts/23_certify_external.py --list
python scripts/23_certify_external.py --all          # ~30 min, CPU, needs network
python scripts/23_certify_external.py --matrix-only  # re-render from disk
python -m pytest tests/ -q                           # 992 tests
python scripts/verify.py --no-activations            # 40/40 claims, 25/25 scores
```

---

## 10. What this changes

Every number this project had published certified our detector, on our corpus,
against a budget we chose. That is the good version of self-assessment and it is
still self-assessment.

The matrix is the first evidence that the machinery says something about
software this project did not write. It is also the only asset here a stranger
would forward to a colleague — a table showing which widely-used detectors can
and cannot be certified at a stated budget, with the command to re-run any cell
printed beside it.

The result worth having is the one where a vendor reads a cell, disagrees, runs
the command, and gets the same number. Every row is built so that is possible.
