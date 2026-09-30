# Phase 28 - Preserve failed clone evidence without poisoning the next run

The default clean-clone command now preserves the last passing
`results/clean_clone.json` when a later gate fails. Each failed attempt writes
its own JSON record under `results/clean_clone_failures/`, and the command
still exits nonzero. A successful default run replaces the canonical record.
An explicit `--out` keeps its previous meaning: the caller receives either
outcome at the path they selected. This is release-evidence plumbing; it does
not change any scientific score, threshold, customer certificate or result.

## Trigger and decision

Phase 25 found a stale collection count in a full tracked-file clone. The
failed gate was committed at `4644c76` in the canonical result path so the
failure remained reviewable. But an existing test requires the committed
canonical record to be passing, which made the next full clone fail on that
record even after the original count was repaired. Restoring the prior green
record at `3e08595` let the corrected gate run and retained the failure in Git
history; it did not fix the output contract. Phase 27 moved this assertion
into a preflight so the same mistake would cost less time, but the output
contract still allowed the next attempt to be blocked.

Decision 225 was committed at `5458686` before code. A default failed run
must leave the canonical bytes untouched and write a distinct failure
artifact named for the tested commit and a write-time nonce. The failure
record is created exclusively, so an existing record cannot be replaced by
accident. The runner prints the actual path and returns failure. The existing
`check_record` comparison still refuses to write either outcome if the source
became dirty or changed during the run. The path decision lives in
`controlplane/report/clean_clone.py`, keeping the script a thin caller.

This separates two questions that were being conflated. The canonical file
answers which tracked-file gate last passed. A named failure file answers
what went wrong in a later attempt. A green canonical file must never be
quoted as a pass for that failed source; its own provenance and commit name
show what it tested. The failed record must be inspected and retained when a
release is refused. No record here is a trusted timestamp or signed audit
event.

## Validation

| Check | Result |
|---|---|
| Decision before implementation | Decision 225 at `5458686` |
| Focused clone-gate suite | 20 tests passed after the change at `f06b080`; Ruff passed for changed Python files |
| Failed default placement | Synthetic regression writes two different failure paths, reads both red payloads and confirms byte-for-byte preservation of the prior green canonical record |
| Successful default placement | Synthetic regression confirms success writes the canonical path |
| Explicit custom output | Synthetic regression confirms a failed result writes the requested custom path without creating a canonical record |
| Corrected Phase 25 full tracked-file gate | Passed on earlier source `3e08595`, with its result committed at `0c929a7`; it does not exercise this later output-placement change |
| Final combined-tree full gate and remote CI | Pending at the time of this report |

The first focused pytest invocation used a nonexistent nested temporary
directory and errored during fixture setup. Rerunning with the existing
workspace temporary parent passed all 20 tests. That environment mistake
did not indicate a code failure and did not produce a passing result for the
first invocation. The test evidence is therefore the second command only.

## What this does not establish

These regressions construct gate outcomes; they do not force a real full
clone to fail just to exercise output placement. The passing Phase 25 clone
belongs to an earlier commit. An integrated full gate must be run on the
combined source before calling this line release-ready. A local clone uses
the installed Python environment, so it does not establish a fresh install,
remote CI, GPU activation re-extraction from ignored caches or deployment
behavior. The failure directory is not append-only storage protected from a
malicious writer. Most importantly, no buyer interviews, customer pilot or
revenue has been provided; cleaner local evidence cannot establish a
fundable market.

## Open items

Regenerate the test inventory after all integrated reports are committed,
run the actual preflight and full tracked-file clone on the clean combined
source, and attach the result to its exact commit. Inspect each verification
tier separately and keep activation re-derivation marked skipped if the
cache is absent. Observe the remote CI run only after a push, and do not
represent local results as a remote pass. Continue the registered buyer
conversations and apply the commercial stopping rule in
`reports/STRATEGY-2026-09.md` before treating the product as validated.

## Ledger

| Item | Source |
|---|---|
| Output contract | Decision 225, `DECISIONS.md` |
| Implementation and synthetic regressions | `f06b080`, `controlplane/report/clean_clone.py`, `scripts/clean_clone_gate.py`, `tests/test_clean_clone.py` |
| Earlier failed full clone | `4644c76`, source `d3544e5` |
| Earlier corrected passing clone | `0c929a7`, source `3e08595` |
| Protected scientific scores | Unchanged |
