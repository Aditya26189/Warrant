# Phase 25 - Fresh-clone evidence at the integrated head

The first full clean-clone run of the integrated `d3544e5` tree failed. It
collected 2,117 tests, while the committed README and Makefile still claimed
2,115. That is a real integration error: the phase-24 inventory had not been
refreshed after later test additions. Phase 25 preserves the failed record,
corrects those generated claims from a clean source, and reruns the gate.
The gate clones tracked files only, then runs smoke, the full suite, and the
claim verifier in that clone. Each record names the commit it tested; a later
fix or documentation commit is not retrospectively part of the earlier test.

## Why this gate matters

A local full-suite pass can depend accidentally on untracked files, ignored
caches, or the original checkout's path. The clean-clone gate detects those
dependencies without changing a scientific score. It also records the three
verification tiers separately: README claims, metrics recomputed from frozen
scores, and activation re-extraction. A skipped tier remains skipped even when
the other two pass.

The gate reuses the caller's Python interpreter and installed environment.
It therefore tests tracked-source completeness and local reproducibility, not
a fresh dependency resolution, package registry install, or remote CI runner.
The repository's installed-package tests and CI jobs are separate evidence.

The runner checks the source Git state before cloning and again before writing
the record. It also compares the clone's HEAD with the intended source commit.
That matters here because a passing clone of one commit must not be attributed
to a later edit. The retained JSON lists every subprocess, exit code, elapsed
time and verification tier; `ok` is the aggregate result, not a substitute for
reading those rows. A clone made from a local worktree has a local Git origin.
It does not show that the configured GitHub remote contains this branch or that
any GitHub Actions job ran. The temporary clones are retained for inspection
during each run and removed only after their paths are checked. Cleanup does
not alter the tested commit or the committed outcome record.

The first failure is retained at `4644c76` as an earlier version of
`results/clean_clone.json`. Its smoke step passed. The full suite exited 1 on
`tests/test_claims.py::test_every_stated_test_count_is_the_real_one`; the
assertion reported 2,117 collected versus 2,115 stated. The verifier still
reproduced 92/92 README claims and 25/25 frozen-score comparisons, with
activation re-extraction explicitly skipped. A green verifier does not make
the failed test gate green. The correction at `c243a0c` updates README,
Makefile, and `results/test_inventory.json` to 2,117 from a clean `4644c76`
source; inventory collection itself does not assert test execution passed.

The first failed artifact also exposed a self-reference in the test suite:
`tests/test_clean_clone.py` requires the *currently committed*
`results/clean_clone.json` to be green. A rerun cloned the red artifact and
would therefore have failed even after the count was fixed. We interrupted
that redundant run before it wrote a second record. Commit `3e08595`
restores the exact earlier generated green artifact bytes to the live path;
the failed `d3544e5` record remains accessible at `4644c76`. The corrected
gate passed from clean source `3e08595`; its measured record is committed at
`0c929a7`. The count assertion and live-artifact assertion both passed before
the full run. The record shows successful clone, smoke, full suite, verifier,
and two available verifier tiers. Re-derivation from the ignored activation
cache is explicitly skipped. Its full-suite step took 2,653 seconds on this
Windows machine, which is a measurement of this run, not a runtime promise
for another environment.

## Validation

| Gate | Result |
|---|---|
| First source | Clean local `d3544e5`, the merge tree matching `phase-24` |
| First fresh-clone gate | Failed only on the stale 2,115 versus 2,117 test-count claim; failed artifact committed at `4644c76` |
| Inventory repair | Generated 2,117 from clean `4644c76`, committed at `c243a0c` |
| Live artifact preparation | Failed record retained in Git history; prior generated green record restored at `3e08595` so its own test can run |
| Two deterministic preflights | Count assertion and live-clone-artifact assertion both passed on corrected source |
| Corrected fresh-clone gate | Passed on clean `3e08595`: clone and smoke, full suite, verifier 92/92 claims and 25/25 frozen-score comparisons; activation re-derivation skipped |
| Provenance artifact | Passing result committed at `0c929a7`; the record names the clean source `3e08595` |
| Dependency isolation and remote CI | Not established by this local gate |

## What this does not establish

Even a passing fresh clone cannot prove that model activations can be
re-extracted without the ignored GPU caches, that the published scenarios
represent customer traffic, or that the evidence has an authenticated author.
It does not supply the buyer conversations, pilot, or revenue needed to test
whether this is a fundable enterprise company.

## Open items

Continue with representative customer sampling and the previously registered buyer
conversations; the clone gate does not answer those questions.

## Ledger

| Item | Source |
|---|---|
| Failed integrated clean-clone record | `results/clean_clone.json` as committed at `4644c76` |
| Generated inventory correction | `c243a0c`, source `4644c76` |
| Live artifact restore before rerun | `3e08595`, byte-for-byte from the prior generated record |
| Corrected passing gate record | `0c929a7`, generated from clean `3e08595` |
| Gate implementation | `scripts/clean_clone_gate.py`, `controlplane/report/clean_clone.py` |
| First integrated source tree | `integration/phase24` at `d3544e5` |

