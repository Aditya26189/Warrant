# Phase 25 - Fresh-clone evidence at the integrated head

The last committed clean-clone record predates the grouped-method repairs.
Phase 25 reruns that gate against the clean local `integration/phase24` tree so
a reviewer can distinguish a working developer checkout from the files a
stranger actually receives. The test clones tracked files only, then runs
smoke, the full suite, and the claim verifier in that clone. Its result will
name the commit tested; a later documentation commit is not retrospectively
part of that test.

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
any GitHub Actions job ran. This run keeps the temporary clone for inspection;
its cleanup is operational housekeeping and does not alter the tested commit.

## Validation

| Gate | Result |
|---|---|
| Source | Clean local `d3544e5`, the merge tree matching `phase-24` |
| Fresh-clone smoke, full suite, and verifier | Running; record and exit pending |
| Provenance artifact | `results/clean_clone.json` will be written only if the source stays clean and unchanged during the gate |
| Dependency isolation and remote CI | Not established by this local gate |

## What this does not establish

Even a passing fresh clone cannot prove that model activations can be
re-extracted without the ignored GPU caches, that the published scenarios
represent customer traffic, or that the evidence has an authenticated author.
It does not supply the buyer conversations, pilot, or revenue needed to test
whether this is a fundable enterprise company.

## Open items

Capture the gate's exit, inspect each step and tier, and record any failure
without turning a skip into a pass. Continue with representative customer
sampling and the previously registered buyer conversations; the clone gate
does not answer those questions.

## Ledger

| Item | Source |
|---|---|
| Prior clean-clone record | `results/clean_clone.json`, tested at an earlier commit |
| Gate implementation | `scripts/clean_clone_gate.py`, `controlplane/report/clean_clone.py` |
| Current source tree | `integration/phase24` at `d3544e5` |

