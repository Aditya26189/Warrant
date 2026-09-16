# ONBOARDING.md — your first hour

<sub>[🏠 Project README](../README.md) · [📚 Documentation index](README.md) · [🗺️ Diagrams](DIAGRAMS.md) · [📖 Glossary](GLOSSARY.md)</sub>

Written for someone who has just cloned this and has to be useful today. Read
the parts in order; each one is sized to what it costs.

**Contents:** [Minute 0](#minute-0--the-one-sentence) · [Make it run](#minutes-15--make-it-run) ·
[See the shape](#minutes-515--see-the-shape) · [Read](#minutes-1530--read-the-two-documents-that-matter-most) ·
[The code](#minutes-3045--the-code) · [Pick up a thread](#minutes-4560--pick-up-a-thread) ·
[What will bite you](#the-things-that-will-bite-you) · [Ask the repository](#where-to-ask-the-repository-instead-of-a-person)

---

## Minute 0 — the one sentence

**A detector produces a score. A warrant is a separate, time-bounded,
evidence-backed statement about what that score is worth on this distribution
right now.**

Everyone ships detectors. Almost nobody ships the second thing — so a guardrail
that has quietly stopped working looks exactly like one that works, and the
dashboard stays green either way.

If you remember nothing else: **policy reads the warrant, not the score.**

---

## Minutes 1–5 — make it run

```bash
python -m venv .venv && . .venv/Scripts/activate    # macOS/Linux: . .venv/bin/activate
pip install -r requirements.lock.txt
python scripts/smoke.py
```

Seven checks, under a minute, no network. It tells you the package imports, the
config loads and hashes, an artifact is readable, the eval sets are frozen, and
the claim table parses. If that passes, your clone is sound.

Then the real one:

```bash
python scripts/verify.py
```

It resolves every number in the README against the artifact and field that
README names, then recomputes every metrics block from the frozen per-item
scores. On a fresh clone the third tier reports SKIPPED, because the activation
caches are gitignored — that is correct behaviour, not a failure.

Then see the tool a customer runs, on the two shipped examples:

```bash
python warrant.py certify --input examples/certifies.csv --budget 0.05
python warrant.py certify --input examples/refuses.csv --budget 0.01
```

The first issues a warrant. The second **refuses and still exits 0**: the file
has too few clean negatives for that budget, and the message names both numbers.
A refusal is a result, not an error. [INPUT.md](INPUT.md) is the input contract.

Details and the other entry points: [SETUP.md](SETUP.md).

---

## Minutes 5–15 — see the shape

Open [DIAGRAMS.md](DIAGRAMS.md) and read the first three diagrams:

1. **The three objects** — detector, envelope, warrant.
2. **The pipeline** — which script writes which artifact.
3. **The warrant lifecycle** — and why `UNVALIDATED` is the modal state.

Then look at one real artifact, because the diagrams are only a claim about it:

```bash
python -c "import json;d=json.load(open('results/validation-T1-last_token.json'));print(list(d))"
```

You will see `controls`, `metrics`, `warrant`, `warrant_status`,
`status_reason`, and a `provenance` block carrying the config hash, the git
commit, a dirty flag and the library versions. Every artifact in `results/` has
that block. It is what makes a published number checkable rather than claimed.

---

## Minutes 15–30 — read the two documents that matter most

**[../README.md](../README.md)'s claim table.** Every quantitative claim the
project makes, the artifact that contains it, and the field inside that
artifact. This is the spine. If you are ever unsure whether something is
measured or asserted, look for it here — if it is not in the table, it is not a
measured claim.

**[LIMITATIONS.md](LIMITATIONS.md).** Read before quoting anything. The items in
§2 change how the claim table should be read; §3 lists what was specified and
not built, what was built since, and what the customer path cannot see. Knowing
these before a reviewer raises them is the difference between a defensible answer
and a scramble.

Then skim [ARCHITECTURE.md](ARCHITECTURE.md), *Three ways in*: the measurement
pipeline, the customer path and release evidence share statistics and nothing
else, and most confusion about this repository is confusion about which of the
three a sentence is describing.

---

## Minutes 30–45 — the code

[CODE_TOUR.md](CODE_TOUR.md) maps every package. The four files that carry the
most weight, in reading order:

| File | Why start here |
|---|---|
| `controlplane/model/warrant.py` | The central record. Its `__post_init__` enforces that a refusal states a reason and that the key includes the envelope |
| `controlplane/model/metrics.py` | Where `EXACT` vs `ESTIMATED` is enforced at construction — a rate without an interval cannot be built |
| `controlplane/validation/issuance.py` | `issue_or_refuse`, which takes **no argument** that could promote a failing detector |
| `controlplane/policy/resolution.py` | Load-time warrant resolution: a bundle naming an operating point with no warrant does not load |

Notice the pattern: the invariants are enforced at construction, not by
convention. You cannot build an illegal record and fix it later.

If your work is on the customer path instead, read these:

| File | Why start here |
|---|---|
| `controlplane/cli.py` | Every `warrant` command, its flags and its exit codes. Refusal exits 0 by design; the docstring says why |
| `controlplane/intake/contract.py` | What a customer's file must contain, and the `InputError` that keeps "we cannot read your file" apart from "your detector was refused" |
| `controlplane/intake/certify.py` | The lowest certifying threshold, and the label-error figures every certificate carries |
| `controlplane/intake/recheck.py` | The two checks a recheck keeps apart, and why it revokes only on the lower bound |
| `controlplane/intake/chain.py` | A year of rechecks as one test; its module docstring states the guarantee and exactly what it does not cover |

---

## Minutes 45–60 — pick up a thread

Whichever fits what you were asked to do:

- **Add or change a detector** → `controlplane/detectors/`, then
  [RUNBOOK.md](RUNBOOK.md) `09_detectors.py`. Remember that a detector's
  identity includes its configuration.
- **Add an evaluation set** → `controlplane/evalsets/`, then
  `01_build_evalsets.py`. Sets are frozen and content-hashed; changing one
  creates a different set, deliberately.
- **Change a policy profile** → `policies/*/bundle.yaml`, then
  `07_policy.py`. Expect the bundle to refuse to load if you name an operating
  point nothing has warranted.
- **Change what `warrant` prints or accepts** → `controlplane/intake/` and
  `controlplane/cli.py`. `tests/test_acceptance.py` runs the README quickstart in
  a fresh clone, so a renamed flag fails there; update
  [TROUBLESHOOTING.md](TROUBLESHOOTING.md)'s message tables and
  [INPUT.md](INPUT.md) in the same change.
- **Add a record field** → the record's `to_payload`, then
  [ARTIFACTS.md](ARTIFACTS.md) and [EVIDENCE-HANDOFF.md](EVIDENCE-HANDOFF.md). A
  new field on a chained recheck record is covered by the seal and its property
  test automatically.
- **Run a new study** → register its criteria in `DECISIONS.md` **before** it runs,
  as `scripts/29`–`32` did, then write it as a thin script over `controlplane/`.
  A criterion changed after seeing output needs a new entry recording the
  original.
- **Understand a statistical choice** → [METHODS.md](METHODS.md), then the
  `DECISIONS.md` entry it cites.

---

## The things that will bite you

1. **Never pipe a command whose exit status you need.** `cmd | tail` reports
   *tail's* status, so a failing test suite reads as green. Use
   `sh scripts/run.sh <cmd>`. This trap fired twice in one session here.
2. **Never run a script against a dirty tree.** Artifacts record the `HEAD` they
   were built from; `provenance()` sets `dirty: true` and the record becomes a
   lie about which code produced the numbers.
3. **Test is never consulted by a selection.** Layer, threshold and
   regularisation are validation decisions. Selecting on test inflates the
   headline and is the first thing a reviewer checks.
4. **Positive class is *incorrect*.** Inverting it silently yields `1 − AUROC`,
   which reads as a strong negative result and misdirects debugging for hours.
5. **Yield is exact; rate is estimated.** *"We surfaced N real errors this
   month"* is a count of reviewed, confirmed items — free, no interval.
   *"We caught X% of errors"* is a claim about traffic nobody reviewed — it
   costs labels and always carries an interval.
   Conflating them converts a free exact claim into an unbacked estimate and
   nobody notices.
6. **Never type a test count.** The counts in `README.md` and the `Makefile` are
   written by `scripts/refresh_test_inventory.py` from a clean commit, and a test
   fails if either disagrees with collection. A count is a claim that tests
   exist, not that they pass.
7. **`DECISIONS.md` is append-only.** Never edit or delete an entry; supersede it
   with a new one. Its citations are checked across the repository.
8. **Keep each file's line endings.** Some files are CRLF and most are LF. An
   edit that normalises them produces a whole-file diff that hides the real
   change.

---

## Where to ask the repository instead of a person

| Question | Where the answer already is |
|---|---|
| Why was this done this way? | [../DECISIONS.md](../DECISIONS.md) — search the topic |
| Is this case handled? | [CASES.md](CASES.md) — every case names its test and its artifact |
| Where did this number come from? | The README claim table, then [ARTIFACTS.md](ARTIFACTS.md) |
| What does this word mean here? | [GLOSSARY.md](GLOSSARY.md) |
| What broke? What does this `warrant` message mean? | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| What does this record field mean? | [ARTIFACTS.md](ARTIFACTS.md), then [EVIDENCE-HANDOFF.md](EVIDENCE-HANDOFF.md) |
| What does this test defend? | [TESTING.md](TESTING.md) |
| What is deliberately missing? | [LIMITATIONS.md](LIMITATIONS.md) §3 |
