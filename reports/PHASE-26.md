# Phase 26 - Fail-closed clean-clone verification

The clean-clone gate now refuses to call an incomplete or contradictory
verification summary a pass. It checks each of the three machine-readable
`TIER|number|key|outcome|passed/total` lines emitted by `scripts/verify.py`.
This repairs the evidence gate itself; it does not change a probe score,
customer certificate, threshold, or protected test-set result.

## Failure found and repaired

Before this phase, `_verify_tiers` manufactured a successful skipped row when
an expected tier was absent. A later duplicate `OK` could overwrite an earlier
`DRIFT`, and a newly added tier could be ignored. Decision 222 records these
synthetic parser counterexamples before the implementation. The gate now
requires exactly one well-formed line for every expected number and key,
rejects duplicate or unknown lines, and fails on missing or malformed lines.
The default clone command requires the claim-table and frozen-score tiers to
run. Only activation re-extraction may report `SKIPPED` in a cache-free clone;
the record displays that as SKIP rather than claiming re-extraction passed.

A second review found that syntax alone still allowed `OK|0/0` or `OK|30/31`
to count as success. Decision 223 records the follow-up rule. Every count must
have `passed <= total`; `OK` requires a positive total and all comparisons to
pass; `SKIPPED` requires `0/0`. `DRIFT` always fails, even when its displayed
counts are complete, because the verifier can have a separate reason to fail.
The gate deliberately does not hardcode today's claim or score totals, which
will change as tracked artifacts change.

These cases are constructed consumer inputs, not evidence that the current
verifier emitted a bad line in a real run. The red regression for `OK|0/0`
failed against the old parser before the count rule was implemented. Both
decisions and their tests remain in the repository so a future summary change
cannot silently turn an unrun check green.

## Validation

| Gate | Result |
|---|---|
| Preregistered decisions | 222 at `40269aa`, then 223 at `6a54cdd`, each before its code change |
| Parser, report, smoke, and docs tests | Passed after the final parser fix; deprecation warnings, no failures |
| Ruff and whitespace | Passed for the changed Python files and diff |
| Test inventory | 2,120 collected from clean `20bdb9d`; collection does not claim execution passed |
| Claim and frozen-score verifier | 92/92 and 25/25 from clean `3093fd8`; activation tier explicitly skipped by `--no-activations` |
| Fresh-clone smoke and verifier on Phase 26 | Passed from clean `3093fd8`: 586 tracked files, smoke, 92/92 claims, 25/25 frozen-score comparisons; activation tier SKIP; full suite deliberately omitted |
| Full repository suite on Phase 26 | Pending |
| Phase 25 full clean-clone gate | First separate run on `d3544e5` failed on a stale test-count claim; a corrected-source rerun is in progress. Neither run validates this parser change |
| Remote CI, independent statistical review | Unobserved |

The clone gate reuses the caller's installed Python environment. Even when it
passes, it establishes that tracked source survives a local clone and its
recorded checks, not that dependencies resolve afresh, a remote CI runner
passed, or model activations can be re-extracted without the ignored caches.
The gate's output is local evidence and has no authenticated custody.

## Product relevance and limits

An enterprise buyer cannot assess a release claim if its own evidence gate
silently treats missing checks as successful. This repair narrows that failure
mode, but does not establish a representative customer holdout, valid labels,
statistical coverage, a production deployment, or purchasing demand. The
founder has reported no buyer interviews, design partners, paid pilots, or
revenue. The twelve-conversation stopping rule remains in
`reports/STRATEGY-2026-09.md`; it should be applied before claiming a fundable
enterprise case from the engineering record alone.

## Open items

Run and record the full repository suite on the final Phase 26 tree, then
integrate this branch with the corrected Phase 25 clone evidence and rerun
the combined-tree checks. A separate environment install and remote CI run
remain unobserved. Independent review of the grouped statistical methods and
representative customer validation still matter more to a release or funding
claim than another local parser regression.

## Ledger

| Change | Commit or source |
|---|---|
| Missing, duplicate, unknown, malformed, and mandatory-skip rule | Decision 222; `0b18fcb` |
| Contradictory count rule | Decision 223; `20bdb9d` |
| Generated inventory | `a57a38a`, then `3093fd8` after the added regression |
| Phase 26 tracked-file clone record | `results/clean_clone_phase26.json` at `c56cd52`, testing `3093fd8` |
| Verification tiers | `scripts/verify.py` and `controlplane/report/clean_clone.py` |
| Protected scientific scores | Unchanged in this phase |
