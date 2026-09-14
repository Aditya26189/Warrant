# Shared checkout handoff

Updated for the founder's 2026-09-15 request to work alongside Claude.
This file records declared ownership; it is not a live connection between agents.
Claude's current task has not yet been confirmed in this session.

## Current checkout

- Branch observed by Codex: `feat/release-evidence`.
- Last committed checkpoint at handoff: `deac5d7`.
- Codex's pending files: README release-guide paragraph, `docs/README.md`,
  `docs/RELEASE.md`, `reports/STARTUP-VIABILITY-2026-09.md`, and
  `reports/CLAIM-AUDIT-2026-09.md`.
- Previous documentation commit was rejected when automatic approval review
  exhausted its account allowance. These edits remained intact and uncommitted.

## Codex's reserved work

- `controlplane/release/` and `tests/test_release_*.py`: finish review and
  validation of register/evaluate/verify.
- `controlplane/report/test_inventory.py`, `scripts/refresh_test_inventory.py`,
  and a focused smoke test: close the missing script-coverage regression.
- The pending release guide and claim audit listed above.
- Generated test counts in README/Makefile and `results/test_inventory.json`:
  refresh only after all agents' test additions are committed and the tree is clean.

An internal Codex reviewer is reviewing the release implementation read-only.
It is not the external Claude session.

## Suggested independent work for Claude

Record the actual scope here before editing overlapping files. Useful separate
work is a read-only review of sampling/recheck contracts or customer workflow
gaps. The legacy mixture-monitor and grouped-recheck defects are described in
DECISIONS 184 and the claim audit. Review does not by itself authorise editing
the explicitly read-only zones in `CLAUDE.md`.

## Shared Git discipline

- Do not switch the shared checkout's branch while the other agent is working.
- Stage named owned files only; inspect both staged and unstaged diffs before
  committing. Do not include the other agent's staged changes in a commit.
- Do not reset, clean, stash, rewrite history, or revert unfamiliar changes.
- Use separate worktrees for overlapping implementation if coordination cannot
  establish one owner. Merely naming separate branches does not isolate one directory.
- Reserve new decision numbers by checking the end of DECISIONS immediately
  before appending. Preserve the append-only record.
- Do not run artifact generators against a dirty tree. Existing research scores
  remain frozen; no unregistered rescoring.

## Verification status to carry forward

The first broad run completed with three failures: stale test-count claims,
unrecognised decision headings, and missing smoke coverage for the new test
inventory script. The heading repair has passed its focused tests. Counts must
be refreshed again after final additions. The script smoke test is still to add.
This is not a green full-suite checkpoint yet.

Release-specific tests passed in the isolated customer environment. The installed
wheel also completed registration, evaluation and verification without the
research stack. Full-run output and final repair checks belong in the closing
phase report; do not infer that the entire product is verified from these checks.
