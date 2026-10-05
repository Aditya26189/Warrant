# Phase 32 - Refuse malformed prepared-package evidence

`verify-prepared` now distinguishes a changed but well-formed package from a
package it cannot parse. Before this phase, a complete directory containing
`manifest.json` with `not JSON`, or `scored.csv` with an invalid score, returned
`MISMATCH` and exit 1. `docs/INPUT.md` promises exit 2 for malformed evidence.
The previous test asserted exit 1 after writing the invalid bytes `tampered`
as the scored file, so it preserved the contradiction. Decision 233 recorded
the revised classification before source changes.

## Question and scope

The question was whether a reviewer could tell a complete changed package
from invalid evidence using the documented command interface. The answer is
now yes. `verify-prepared` still rebuilds expected bytes from the retained
original export and mapping. If the package bytes differ, it first checks that
the scored file satisfies the canonical input contract and that the manifest
is a unique-key UTF-8 JSON object with the version-1 prepared-record fields,
types and status. Valid changed bytes then return `MISMATCH`/1; malformed
members return an input error/2. An unchanged package still returns
`VERIFIED`/0. Missing members and unexpected extra members retain their input
error behavior.

The parser does not infer the truth of labels or independence of rows. It
does not change the source-to-row mapping, threshold, confidence interval,
certification status or any committed scientific artifact. `manifest.json`
continues to be a checksum record, not an authenticated signature.

## Work and findings

- `1c9afd6` registered Decision 233, including the distinction between a
  valid altered field and an invalid package member.
- Five new focused cases failed before the repair. Four malformed member
  cases returned normally from the library instead of raising `InputError`;
  the real CLI returned exit 1 for corrupt manifest JSON instead of exit 2.
  The full failure output was observed before editing the verifier.
- `a34f22d` checks changed package members before classifying their byte
  difference. The test that previously wrote the invalid bytes `tampered`
  now changes one numeric score to another valid numeric score. A separate
  case changes a well-formed manifest value and still expects `MISMATCH`/1.
  Another case changes `schema_version` and expects an input error.
- `tests/test_prepare.py` passed 48/48 after the repair. The preparation,
  installed-package and certificate-consumer batch passed 73/73 in 304.97
  seconds. Ruff and `git diff --check` passed on the changed files.
- On clean source `a34f22d`, `python scripts/smoke.py` passed 7/7.
  `python scripts/verify.py --no-activations` reproduced 92/92 claim-table
  entries and 25/25 frozen-score comparisons; the activation tier was
  explicitly skipped.
- On clean source `ecef0b4`, the full suite with strict markers and a
  dedicated OS-temp fixture directory passed 2,202/2,202 tests in 2,781.59
  seconds (command wall clock 2,794.3 seconds). Pytest reported three
  warnings: two SWIG deprecations and a nonfinite-update runtime warning.
  The separate inventory from `bf344cc` counted 2,202 tests; that collection
  was not used as a substitute for execution.

## What this does not establish

These tests use synthetic scored files and local package directories. They
do not show how a customer's export is labelled, whether its unit of evidence
is independent, whether its score direction declaration is right, or whether
a reviewer can make a decision from the packet. The verifier compares local
bytes; it does not attest to the source owner or to a trusted creation time.
The activation re-extraction tier did not run in this isolated worktree. A
passing installed CLI check does not prove every Python version or operating
system behaves the same. A caller can still retain a well-formed but false
mapping; neither preparation nor this classification can discover it.

## Open items

The October plan's next public handoff step is a complete prepare-to-certify
example: the four-row format example is too small to certify. The next phase
will add a synthetic end-to-end example and a regression for both preparation
replay and certificate replay, making the boundary between them observable.
The real-customer gate remains an owner-approved scored export, label
provenance, a declared sampling unit and a named recurring decision. None was
supplied or inferred during this phase.

## Ledger

| Change or check | Evidence |
|---|---|
| Preregistered classification | Decision 233; `1c9afd6` |
| Red-before regressions | Five failed cases in `tests/test_prepare.py` before source repair |
| Verifier source and test repair | `a34f22d`; `controlplane/intake/prepare.py`, `tests/test_prepare.py` |
| Adjacent installed/CLI batch | 73 passed, 304.97 seconds; Ruff passed |
| Clean-source smoke and available verifier | `a34f22d`: 7/7, 92/92, 25/25; activations skipped |
| Full strict-marker source suite | `ecef0b4`: 2,202 passed, 3 warnings, exit 0 |
