# Phase 2 — can anyone else use it?

**Answer: yes.** A stranger with a CSV of their own scores and labels reaches a
warrant, or a refusal, in one command:

```bash
python warrant.py certify --input your_scores.csv --budget 0.05
```

**One task of five was delivered.** It was the one that needed no gate. The
other four are blocked on resources — provider credentials and GPU access — and
D30 says record and stop rather than approximate. That is the honest accounting
and it is unchanged from Phase 1.

- **Window:** 2026-09-09
- **Range:** `f5faa00` → `HEAD`, 4 commits
- **Suite:** 907 at open → 952 at close, no failures at either end
- **Verification:** `verify.py` 40/40 claims, 25/25 frozen scores — unchanged
- **Config hash:** unchanged at `533fb74983fcd8af`

---

## 1. What was done

| Task | Status | Outcome |
|---|---|---|
| **T0** baseline | done | 907 green (Phase 1 close-out). The DECISIONS 131 SHA mapping re-checked by **reachability**: all 15 reachable, and the pre-registration ordering still holds. |
| **T1** bring-your-own-data | **done** | `warrant certify`, an input contract, two examples, a tested quickstart. 45 new tests. |
| **T2** closed-API matrix | **gated** | No provider credentials. `DECISIONS.md` 138. |
| **T3** corpus expansion | **gated** | No GPU. Corpus holds 1280 negatives; expansion needs new items. |
| **T4** out-of-distribution | **gated** | Needs a GPU and T3 first. Criterion registered, unfired. |
| **T5** close-out | done | This report. |

---

## 2. T1 — the door in

Warrant could measure its own detector on its own eval sets, driven by
twenty-one numbered scripts and a project-specific `config.yaml`. A customer
with a labelled task set had no way in. The product's thesis is that a customer
brings their task set and Warrant certifies against it; the software could not
accept one.

**The contract is three columns** — `id`, `label` (0/1, where **1 means the
detector should fire**), `score` (higher = more likely class 1) — in CSV or
JSONL. Optional `group` for items that are not independent. Everything else is
carried into the record and used in nothing.

**No model is required, and that is the correct boundary** rather than a
limitation. Warrant certifies a detector given scores and labels; producing the
scores is the customer's problem. It is exactly what makes the tool work against
a closed-API deployment where no probe can exist — which is the same question
T2 is gated on, approached from the other side.

### The refusal ships first

```bash
python warrant.py certify --input examples/refuses.csv --budget 0.01
```

37 negatives, and a 1% budget needs 299. No threshold on that file can be
certified at that budget however good the detector is. Warrant says so, names
both numbers, and **exits 0**.

The exit code is the design decision. A non-zero exit would make every CI
pipeline treat *"your detector cannot be certified on this evidence"* as a
broken tool, teaching users that refusals are malfunctions — which inverts the
product. `--require-warrant` exists for callers who want a gate, and it prints
the reason to stderr so a non-zero exit is never bare.

The examples README then has the reader run the **same file at a 20% budget**,
where it certifies. Nothing about the detector changed — only what Warrant was
asked to promise about it. That is the trade the whole tool exists to make
legible: a tighter budget is a stronger promise, and a stronger promise needs
more evidence.

### It is the same certification, not a copy

`controlplane/intake/` reads a file, validates it, and renders a summary. The
certification itself is `certify_fpr` and `build_warrant_metrics` unchanged, at
the config's bootstrap count, coverage and seed (`DECISIONS.md` 137).

A simplified variant would be a second implementation of one quantity — the
failure class behind 036, 040 and the metrics builder. It would also be the
worse half of the trade: the customer's number is the one scrutinised by
someone who does not trust us, so it is precisely the number that must come from
the code this project defends.

### Validation is strict and never coerces

Missing columns, non-binary labels, non-finite scores, blank cells, duplicate
ids, single-class files, blank group cells. Each names the column, the row and
what was expected. A blank is not a zero and `0.7` is not a label.

Two shapes get special handling:

- **Unequal groups raise rather than certify.** The cluster bound only dominates
  the item-level one when clusters are equal-sized; unequal, it is
  *anticonservative*. Certifying anyway would promise a tighter false-positive
  rate than the data supports while the group column sits there denying the
  independence that assumes.
- **A shortage of negatives is a refusal, not an error.** Both stop the run and
  they mean different things: an error is *we cannot read what you sent*; a
  refusal is *we read it and the evidence is insufficient*. Conflating them turns
  a fixable typo into a verdict on the detector, and a verdict into a typo.

---

## 3. What the acceptance test caught

The acceptance test does not run commands a test author typed. **It parses the
quickstart out of `README.md` and runs what it finds, inside a fresh
`git clone`.** If a flag is renamed or an example moves, the README fails the
build.

It earned that design twice on its first day.

**The Windows encoding bug.** The terminal summary was drawn with box-drawing
characters and died with `UnicodeEncodeError` on a cp1252 console *before
printing anything*. A stranger on Windows following the quickstart would have
seen a traceback where the warrant should be. Output is ASCII now, and a test
runs the CLI under `PYTHONIOENCODING=cp1252` to keep it that way. Output that
cannot be printed is output that does not work, whatever it looks like on the
machine it was written on.

**The missing file.** Its first run failed on `warrant.py` missing from the
clone — because the file was not committed yet. Exactly the "works on my
machine" failure the test exists to catch.

**One process error of mine, recorded because it invalidated a measurement.**
The T0 baseline run failed on `test_every_script_has_a_smoke_test`. Not a
regression: I created a new script *while that run was in flight*, and the check
enumerates `scripts/` at runtime. The real baseline is Phase 1's close-out, 907
green. Do not edit the tree while the baseline is running.

---

## 4. What this does not establish

**That `pip install` works.** The acceptance test clones and runs with the
current interpreter. It proves the *repository* carries everything the
quickstart needs and that no command depends on untracked local state. It does
not build a virtualenv or resolve dependencies from an index — the suite has to
run offline, and `pip install` is a claim about PyPI rather than about this
repo.

**That the tool is right for data unlike the examples.** Both examples are
synthetic, drawn from a seeded generator, and `examples/README.md` says so in
its first line. They demonstrate both outcomes; they are evidence about a
generator written here and nothing else.

**Anything about the numbers in the claim table**, which are unchanged. This
phase added a door, not a measurement.

---

## 5. Open items

| Entry | Status | What would close it |
|---|---|---|
| **138** — T2 closed-API matrix | OPEN | Credentials for one provider that exposes logprobs and one that does not, so the matrix carries both a populated Tier 1 and a recorded UNAVAILABLE. |
| **138** — T3 corpus expansion | OPEN | A GPU session extracting new items. Size against `internal_knowledge` at 1649 items for the 10% calibration bar (`DECISIONS.md` 135) — not against 1441, which answers a different question. |
| **138** — T4 out-of-distribution | OPEN | A corpus this project did not construct, plus T3's session. Criterion registered and unfired: transfer holds if lift's 95% lower bound exceeds 1.0 at any swept target. |

Each of these has an obvious way to look finished — an all-UNVALIDATED matrix, a
logprob table written from what is widely known, an OOD claim made against the
long-context set. All three would pass every test here and support conclusions
nothing measured. `DECISIONS.md` 118 settled that rule: a claim about a
dependency is checkable by running the dependency.

---

## 6. Ledger

**Code**

| Path | What it is |
|---|---|
| `controlplane/intake/contract.py` | the input contract; strict, never coerces |
| `controlplane/intake/certify.py` | certification, reusing the pipeline's estimators |
| `controlplane/intake/render.py` | the terminal summary; ASCII, refusal legible as a result |
| `controlplane/cli.py` | `warrant certify`; exit codes 0 / 2 / 1 |
| `warrant.py` | the zero-install entry point the quickstart uses |
| `pyproject.toml` | `pip install -e .` gives a real `warrant` command |
| `scripts/22_make_examples.py` | the seeded example generator |
| `tests/test_intake.py` | 32 tests: the contract, refusals, both examples |
| `tests/test_acceptance.py` | fresh clone, README's own commands, both outcomes |

**Docs** — `docs/INPUT.md` (the contract), `examples/README.md` (why the refusal
matters), and a rewritten README quickstart leading with the customer path.

**Decisions** — `DECISIONS.md` 137, 138.

**Reproduce**

```bash
python warrant.py certify --input examples/certifies.csv --budget 0.05
python warrant.py certify --input examples/refuses.csv   --budget 0.01
python scripts/22_make_examples.py     # regenerates the examples, seeded
python -m pytest tests/ -q             # 952 tests
python scripts/verify.py --no-activations   # 40/40 claims, 25/25 scores
```

---

## 7. What this changes

Phase 1 made the measurement quotable. Phase 2 makes it **transferable**, which
is a different kind of work: the test is not whether the code is clean but
whether someone who has never seen this project reaches a warrant without asking
a question.

The thing worth selling is the second command. Everyone shipping a detector can
produce a number; almost nobody ships a system that will tell you the number is
not supported by what you gave it. `examples/refuses.csv` demonstrates that in
one line, against a budget a buyer will recognise as reasonable, and it exits 0
while doing it.

What remains unmeasured is unchanged and named: whether the numbers hold on a
corpus this project did not build, and whether any of it works without open
weights. Both are gated on resources rather than on findings, and neither has
been guessed at.
