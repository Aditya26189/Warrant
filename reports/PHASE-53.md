# Phase 53 — Executed test count in the tracked-clone record

The full tracked-file clean-clone gate passed on source
`bfa1631ee7e3279852f8fb267e458bc7938f4ca6` with 640 tracked files. Its
retained `make test` step now says **`2275 passed, 3 warnings in 1609.51s`**
and records return code 0. The step wall time was 1,615.5 seconds; pytest's
own duration and the enclosing step duration measure different boundaries.
The complete gate exited 0, claim-table verification passed 92/92, frozen
scores recomputed 25/25, activation re-derivation was SKIPPED, and the gate
reported no cleanup warning. The machine-readable
[`results/clean_clone.json`](../results/clean_clone.json) is committed as
`760439b`. It names the tested source commit, not the later artifact, report
or inventory commits.

## Why the count had been missing

Prior Phase 50 and Phase 51 clone records showed a successful full-suite step
and 100% progress, but their retained output tails had no numeric pass count.
[`pytest.ini`](../pytest.ini) already sets `addopts = -q --strict-markers`,
and the gate passed another `-q`. On the same 23-case focused module, the
double-quiet invocation printed progress with no summary; a single quiet flag
printed `23 passed in 3.80s`. The prior `results/test_inventory.json` values
were collection counts only, so they could not fill this execution gap.

[Decision 240](../DECISIONS.md) registered a reporting-only correction before
implementation. The clean-clone full-suite command still selects `tests/`,
uses one `-q`, enforces strict markers and retains the two-hour timeout. Its
explicit `-o addopts=--strict-markers` removes only the duplicate quiet option
from repository defaults for this gate invocation. The exact command is
recorded in the artifact. The repository-wide pytest defaults and `make test`
recipe were not changed, and neither test selection nor test assertions were
weakened. A user invoking `make test` directly still gets its existing output
format; the clone gate's equivalent full-suite invocation retains the count.

## Evidence ledger

| Check | Named source | Observed result |
| --- | --- | --- |
| Same-module output comparison | Phase 52 source, `tests/test_clean_clone.py` under the two reporting configurations | Both executions selected 23 tests. The single-quiet run ended `23 passed in 3.80s`; the double-quiet run reached 100% but omitted the summary. |
| Red-before regression | Decision 240 committed, implementation still old | `test_passing_clone_preflight_runs_the_full_suite` failed because the full-suite command lacked `-o addopts=--strict-markers`; 1 failed, exit 1. |
| Focused green regression and docs | Changed source before implementation commit `c98df1a` | `tests/test_clean_clone.py tests/test_docs_index.py`: 92 passed in 6.47s, exit 0. Ruff and whitespace checks passed. The regression also invokes a tiny real pytest run under default double-quiet configuration and requires `1 passed` in the captured tail. |
| Generated collection inventory | Clean `c98df1a` | 2,275 collected, unchanged from Phase 52. The inventory records collection, not execution. |
| Full tracked clone | Clean `bfa1631` | 640 tracked files; clone, HEAD match, notes fetch, smoke, preflight, full suite and verifier all returned success. Gate exit 0. |
| Full suite in that clone | Clean `bfa1631`, `python -m pytest tests/ -q -o addopts=--strict-markers` | **2,275 passed**, 3 pytest warnings, 0 failed; pytest duration 1,609.51s; step duration 1,615.5s and return code 0. |
| Claim and score verifier in that clone | Clean `bfa1631` | `TIER|1|claim_table|OK|92/92`, `TIER|2|frozen_scores|OK|25/25`, `TIER|3|activations|SKIPPED|0/0`. |

The gate's smoke step recorded `dirty=False` inside the clone. Its full-suite
tail includes two SWIG deprecation warnings and the deliberate nonfinite
update warning from `test_warrant_stats.py`. A further `swigvarlink`
deprecation printed at interpreter shutdown after pytest's counted warning
summary. These warnings did not alter the return code. The local
`.venv/phase53-clean-clone.exit` file contained `0`; it and its log are QA
scratch outside the committed record. The artifact's notes contain no
temporary-clone cleanup warning. This is one observed cleanup success, not a
guarantee that Windows cannot leave a clone after a future external file lock.

The 2,275 **executed passes** in this gate happen to equal the 2,275
**collected** in the pre-gate inventory. They are separate observations from
different commands. Neither the matching counts nor the successful exit
proves that an untracked GPU activation cache was present; the activation
verification tier explicitly says it was not.

## What this does not establish; open items

This local Windows/Python 3.12.10 clone did not fetch its files from GitHub.
It does not establish that remote Linux CI passed on the final merge, that
Python 3.10 or 3.11 behaves identically, or that the frozen scores can be
re-derived from the absent activation cache. The reporting change says how
many tests executed; it does not expand their coverage or validate a customer's
labels, sampling unit, data custody, detector performance or decision workflow.
No customer packet, unaided reviewer or buyer evidence has been supplied.

The next external gate remains the named, owner-permitted workflow in the
[discovery worksheet](DISCOVERY-2026-10.md), including a real scored export,
independently sourced labels and the configured incumbent's same-decision
report. Further speculative product surfaces remain outside this QA phase.
