# Phase 27 - Cheap release blockers before an expensive clone suite

The full clean-clone gate now checks two deterministic release assertions
before spending time on the entire suite. If either fails, the gate records the
preflight failure, marks the full suite as an unsuccessful SKIP, and still runs
the independent claim verifier. A passing preflight leaves the full-suite
command unchanged. This reduces time lost to known release errors without
turning an omitted test run into a green result.

## Trigger and behavior

The first Phase 25 full clone of integrated `d3544e5` took about 45 minutes in
`make test` and exited 1 because pytest collected 2,117 tests while README and
Makefile claimed 2,115. The failed record was preserved in Git history. A
second existing assertion requires the live committed
`results/clean_clone.json` to be green; leaving the failed record at that path
would have made the next full clone fail for a separate, deterministic reason.
That redundant run was interrupted before an outcome artifact was written.
Decision 224 records the failure and the execution rule before implementation.

On a full gate, the clone now runs
`test_every_stated_test_count_is_the_real_one` and
`test_the_committed_gate_artifact_is_readable_and_passed` after smoke. These
are the existing tests; their meaning was not weakened to make the gate pass.
If either fails, `make test preflight` is FAIL and `make test` is SKIP with
`ok=false` and an explicit reason. The gate continues to `make verify`, whose
three tier rows retain the Phase 26 fail-closed parser. A failure in one
preflight cannot be overwritten by a passing verifier. `--no-tests` continues
to run smoke and verify without claiming any test step ran.

The preflight takes up to 900 seconds because the count test asks pytest to
collect the repository; the full suite retains its 3,600-second timeout. Those
are operational bounds, not performance claims. In the actual corrected Phase
25 checkout, both named assertions passed before its full clone was restarted.

## Validation

| Gate | Result |
|---|---|
| Preregistered rule | Decision 224 committed at `77cb5ec` before code |
| Red regressions | Both new step-selection tests failed before `_run_suite_after_preflight` existed |
| Affected clone/report tests | Passed after implementation at `1e6b2fa` |
| Actual preflight node IDs | Both passed from clean Phase 27 head after the inventory commit |
| Ruff and whitespace | Passed for changed Python and diff |
| Test inventory | 2,124 collected from clean `d5f2ff4`, committed at `a999f33`; the report itself adds two parametrized cases, and collection is not a passing-suite result |
| Clean verifier | 92/92 README claims and 25/25 frozen-score comparisons; activation re-extraction explicitly skipped |
| Full clone on Phase 27 and final integrated tree | Pending; the earlier Phase 25 full clone is a different source commit |
| Remote CI | Unobserved |

## What this does not establish

The preflight can catch these two known deterministic blockers earlier. It
does not catch every possible full-suite failure, prove that a clean install
resolves dependencies, authenticate the local result, or make a skipped suite
equivalent to a passing one. The branch has not yet earned a full-clone pass;
that outcome must be attached to the exact commit tested after integration.
Neither this gate nor the broader engineering record supplies customer data,
buyer interviews, a paid pilot, or evidence that this is a fundable company.

## Open items

The corrected Phase 25 full clone passed on its earlier source and the
Phase 26 parser and this preflight have been integrated. Run the combined-tree
checks and record their exact source commit. Observe remote CI separately if
the branch is pushed.
Keep the customer-discovery stopping rule in `reports/STRATEGY-2026-09.md`:
local release hygiene cannot answer whether a buyer needs this certificate.

## Ledger

| Item | Source |
|---|---|
| First failed full clone and generated count repair | `4644c76`, `c243a0c` on the Phase 25 branch |
| Preflight rule | Decision 224, `77cb5ec` |
| Execution path and regressions | `controlplane/report/clean_clone.py`, `tests/test_clean_clone.py`, `1e6b2fa` |
| Generated collection inventory | `results/test_inventory.json`, `721e87d` before this report and `a999f33` after its two cases |
| Protected scientific scores | Unchanged |
