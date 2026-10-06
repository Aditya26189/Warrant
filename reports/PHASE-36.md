# Phase 36 - Remove preparation's intermediate plaintext files

Preparation now parses its already-read source and generated scored rows in
memory. Before this phase, it wrote the complete original export, including
excluded columns, into an OS temporary directory and wrote the canonical
scored file there for validation. Normal cleanup removed those files, but an
abnormal termination could leave another plaintext copy outside the retained
inputs and declared output package. Decision 235 registered the repair before
code changes. The normal output package and certificate statistics are
unchanged for the committed examples.

## Question and scope

The original `prepare._build` read source and mapping bytes once to bind
their hashes, then wrote the source to `input.csv` or `input.jsonl` under
`tempfile.TemporaryDirectory` because the strict intake parsers accepted
paths only. It wrote `scored.csv` to the same temporary directory so the
ordinary scored-item validator could read it. The source may carry excluded
fields such as prompts or customer identifiers. `docs/INPUT.md` and
`docs/PRODUCT-STATE.md` accurately disclosed the extra temporary copy.
The question was whether the same strict parsing and validation could use
the already-read bytes without a second disk write.

This is a data-minimization repair, not a cryptographic change. The caller's
source and mapping remain on disk and must still be retained for replay.
The declared prepared directory still contains `scored.csv` and
`manifest.json`; those outputs may contain identifiers and groups. A process
can still expose plaintext through memory, swap or a crash dump. None of
this changes whether the submitted labels, row independence or scoring
procedure are correct.

## Work and findings

Decision 235 was committed as `106fb17`. A new test monkeypatched
`tempfile.TemporaryDirectory` to fail and then prepared and replayed both CSV
and JSONL. Both cases failed before the implementation at the original
temporary-directory call. The final test covers CSV, JSONL and NDJSON,
checks the exact canonical scored bytes, confirms the excluded private text
is absent from the manifest, and replays the prepared package. All three
cases pass after the repair.

The shared strict CSV and JSONL readers now accept either a path or bytes.
The byte path uses the same CSV reader with UTF-8 BOM handling and newline
behavior, and the same JSON duplicate-key and flat-object checks. The
scored-item contract has one row-validation helper used by both file and
byte entry points. `prepare._build` feeds the original bytes into those
readers and validates its generated scored bytes directly; it no longer
imports `tempfile` or creates an intermediate file. Errors still name the
legacy `input.csv`, `input.jsonl` or `input.ndjson` snapshot, and the
canonical byte validator names `scored.csv`.

The affected prepare suite passed 50 tests after the first implementation.
Adjacent intake, public handoff, installed-package and publication tests
passed 131/131 in 367.88 seconds. After preserving the `.ndjson` diagnostic
name and adding NDJSON to the regression, preparation, ambiguity and link
checks passed 144/144; Ruff passed. The repaired modules also passed 77
focused tests in the Python 3.12 customer-only venv, with no research stack
installed. These checks cover malformed and ambiguous inputs, grouped rows,
second labels, package replay and real installed CLI execution.

On clean `e068940`, I computed SHA-256 for the `scored.csv` and
`manifest.json` bytes returned by `_build` on both committed export examples,
and compared them with the pre-repair clean `phase-35` checkout. Both pairs
were identical. For `export_certifies.csv`, the scored digest was
`e9b196dea55d0cea7afdf9f98ef030a626103098e56ef0d94416956a1ea1935a`
and the manifest digest was
`5fa769b8eac1e3b63942b6349dc4478113f7545d2b4281f8bc35fb0aeec415c2`.
For `export_sample.csv`, they were
`39bb0b520f7e1e292a1fd3ab377e169383590032a61d0fe59eef46f7f9223772`
and `a850e63e1602a2d9036bba4e7602696a1eba7777b4867edd13be16a7af59e792`.
These comparisons show this source change did not move those example bytes;
they do not establish equivalence for every possible customer export.

The current input guide and product-state table now describe process-memory
parsing and the retained sensitivity accurately. The dated 2 October mentor
brief remains historical: its statement about the temporary copy was true
at that earlier source commit and is not a current implementation guide.

## What this does not establish

No test can prove the host operating system never writes process memory to
swap or a crash dump. This change removes the specific intermediate files
created by Warrant during preparation; it is not a secure deletion facility
for caller-owned source files or the prepared package. The monkeypatch test
would not detect every hypothetical alternate file-writing API, which is
why code review of the changed `_build` path matters alongside it. The
current CLI still trusts the caller's mapping and labels. The synthetic
certificate result, source and manifest digest agreement, and passing tests
do not establish a real customer's data quality or a useful review decision.

The clean-source full suite at `122b913` passed 2,215 tests with three
warnings and no failures in 3,072.48 seconds. Smoke passed 7/7. Claim replay
passed 92/92 and frozen-score comparisons passed 25/25; the activation tier
was explicitly skipped with `--no-activations`. The frozen GPU activation
tier cannot be claimed from this CPU-only repair. No protected test set was
rescored and no claim-table number was regenerated.

## Open items

A real export still needs permission, a retention rule, human label
provenance, declared grouping and a decision owner. The discovery worksheet
and week-one clean-clone practice path exist, but no independent human dry
run has occurred. The October plan freezes speculative platform work until
an actual reviewer packet shows a gap. The temporary-file repair reduces
one concrete local data-handling risk; it does not remove that market or
methodological gate.

## Ledger

| Change or check | Evidence |
|---|---|
| Preregistration | Decision 235, `106fb17` |
| Red-before regression | CSV and JSONL both failed at `tempfile.TemporaryDirectory` before repair |
| In-memory parser and current docs | `e068940`; `contract.py`, `prepare.py`, `test_prepare.py`, `docs/INPUT.md`, `docs/PRODUCT-STATE.md` |
| Repaired preparation regression | CSV, JSONL and NDJSON pass; canonical bytes and replay asserted |
| Adjacent installed and CLI gate | 131 passed in 367.88 seconds |
| Refined parser and docs gate | 144 passed; Ruff passed |
| Customer-only focused gate | 77 passed in 38.77 seconds, Python 3.12 |
| Committed-example byte equivalence | Both scored and manifest SHA-256 pairs match the pre-repair checkout |
| Clean full-suite gate | `122b913`; `python -m pytest tests/ -q -p no:cacheprovider --basetemp <os-temp> -o addopts=--strict-markers`; 2,215 passed, three warnings, exit 0 |
| Clean smoke and available verifier | `122b913`; smoke 7/7, claim table 92/92, frozen scores 25/25; activations skipped |
