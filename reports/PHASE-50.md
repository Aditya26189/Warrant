# Phase 50 — Full tracked-file clone gate

The repository's own clean-clone gate passed from clean source
`40207136e669b3ac8eb46948b932492996be2516` on Windows with Python
3.12.10. It cloned 637 tracked files into a new local temporary directory,
ran smoke, the test-count and prior-gate preflight, the complete pytest suite,
and the tiered claim verifier. Its native exit code was 0 and it wrote a
passing [`results/clean_clone.json`](../results/clean_clone.json), committed
separately as `b9a5fb3`. The test step returned 0 and reached 100% in
1,747.14 seconds. The gate report's retained output tail does not include a
separate pytest "N passed" summary, so this report does not turn the 2,267
*collected* cases into an asserted execution count. The result is a passing
full-suite step on the named tracked-file clone, with its exact step status in
the artifact.

## Why this gate matters

Phase 48 ran the full suite in a clean isolated worktree and repaired two
preservation failures. Phase 49 added source-backed incumbent research. The
older canonical clean-clone artifact still named `c335334` and 611 tracked
files. A clean worktree alone cannot show that a needed file was committed:
local ignored caches, a generated database or an untracked helper might make
it appear to work. This gate used the repository's `scripts/clean_clone_gate.py`
to test only tracked source. The shared root's untracked `ARC180_BRIEF.md` and
`warrant-agent-pack/` were not copied into the tested clone or staged.

The gate ran from `.venv/phase50-gate` with `git status --porcelain` empty.
`results/clean_clone.json` records `provenance.git_commit=4020713...`,
`provenance.dirty=false`, `commit=4020713...`, `tracked_files=637`, the
Python/library/device snapshot, every step's command, return code and
duration, tier statuses, and notes. The source commit in that artifact is the
commit before the artifact itself was added. Subsequent report and inventory
commits do not retroactively become a new clean-clone test.

## Executed steps and observed result

| Step in retained artifact | Status | Wall time | What it establishes |
| --- | --- | ---: | --- |
| `git clone` | OK | 10.1 s | A local clone was created from tracked source. It was not fetched from GitHub. |
| Clone matches source HEAD; fetch notes | OK | 0.0 s; 0.4 s | The tested clone named the source commit and obtained local notes. |
| `make smoke` recipe | OK | 5.1 s | Python imports, config, provenance, frozen eval-set hashes and claim-table parsing succeeded in the clone. |
| `make test` preflight | OK | 34.8 s | The stated test count and retained gate-artifact assertions did not block the suite. |
| `make test` full suite | OK, return code 0 | 1,747.14 s | The suite reached 100% in the tracked-file clone. The retained tail lists three pytest warnings and an interpreter-shutdown SWIG warning; it does not retain a numeric pass summary. |
| `make verify` recipe | OK | 30.5 s | Claim table 92/92 and frozen-score recomputation 25/25 succeeded. |
| Activation re-derivation | SKIP | 0.0 s | The gitignored extraction cache was absent in the clone; no model re-extraction was performed. |

Here `make` names the repository gate steps; on this Windows host the script
invoked their Python recipes directly. The verifier's retained protocol rows
are `TIER|1|claim_table|OK|92/92`,
`TIER|2|frozen_scores|OK|25/25`, and
`TIER|3|activations|SKIPPED|0/0`. The test warnings were two SWIG
`DeprecationWarning`s and a deliberate nonfinite-update `RuntimeWarning` in
`test_warrant_stats.py`. A later `swigvarlink` deprecation printed at
interpreter shutdown. None changed the test step's return code. The
[Phase 48 report](PHASE-48.md) retains the earlier 2,263-test full execution
count for its different named source. The Phase 49 collection inventory says
2,267 collected at `535ff18`; collection alone is not a pass.

## Windows cleanup finding

The gate's normal cleanup tried to remove its temporary clone, then reported
`PermissionError: [WinError 5]` on a `.git/objects` file and left about 26 MB.
This did not change the result of the checks, and the warning was retained in
`results/clean_clone.json` instead of being hidden. The same cleanup function
already documents prior Windows leftovers and reports its final failure. I
verified that this run's absolute path resolved under the named Windows Temp
directory, removed only that gate-created clone with PowerShell after the
gate exited, and observed `Test-Path=False`. This manual cleanup does not
rewrite the artifact's original observation. No general filesystem-cleanup
fix is claimed here; a future Windows run may hit the same permission race.

## Evidence ledger and checks after publication

The untracked local durable log `.venv/phase50-clean-clone.log` captured the
rendered gate status and the matching `.exit` file contained `0`. Those files
are local QA scratch, not scientific artifacts. The passing canonical JSON is
committed; its exact fields, rather than this prose, are the machine-readable
evidence. The artifact moved from a prior source `c335334` with 611 tracked
files and a 2,871.55-second full-suite step to the current named source and
1,747.14-second step. The two durations are not a throughput comparison:
source, suite size and ambient machine load differ.

After the artifact commit, `tests/test_clean_clone.py` passed 21/21 and the
draft report/link tests passed 173/173. The inventory was then generated from
clean report commit `4cf0507`: 2,269 collected, with
`execution_status=not_measured_by_collection`. On clean inventory commit
`3526b23`, the combined artifact/report/link/claim subset passed 208/208,
smoke passed 7/7 with `dirty=False`, and `python scripts/verify.py
--no-activations` again reported 92/92 claims, 25/25 frozen-score comparisons
and activation tier SKIPPED 0/0. This follow-up gate did not repeat the
expensive clean clone; it checked that the published artifact, report and
README remain internally consistent.

## What this does not establish; open items

A local tracked-file clone on one Windows/Python environment does not establish
remote CI on the final merge, Linux behavior, Python 3.10 or 3.11, GPU
extraction provenance, customer data handling, authenticated packet custody,
label truth, or buyer demand. The activation tier explicitly skipped because
its cache is not committed. The clone had no gitignored long-context eval sets
or caches, which is a strength for the checked tiers and a limit for those not
run. The gate does not rerun a permissioned real export or an unaided reviewer
trial; neither exists in the supplied workspace.

The remaining venture test is still the one in
[the discovery packet](DISCOVERY-2026-10.md): an owner-permitted scored export,
independent labels and sampling unit, the configured incumbent report for the
same recurring decision, and a reviewer who can say whether the Warrant
packet changes sign-off. The official-source
[incumbent comparison](INCUMBENT-PACKET-COMPARISON-2026-10.md) makes generic
review and export features poor differentiation. Passing this technical gate
improves confidence that the current local tool is reproducible from tracked
files; it does not validate a fundable company.
