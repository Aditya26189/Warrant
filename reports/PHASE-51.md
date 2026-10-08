# Phase 51 — Windows clean-clone cleanup repair

The tracked-file clean-clone gate passed on committed source
`e9724de842974beea37b5c7f206cc50a70d0cd32` on Windows with Python
3.12.10. It cloned 638 tracked files, ran its smoke and test preflight, ran
the full test suite to 100% with return code 0, and ran the tiered verifier.
The gate itself exited 0. It removed its temporary clone without a cleanup
warning. The passing record is [`results/clean_clone.json`](../results/clean_clone.json),
committed separately as `2461810`. The record names the source commit before
the artifact and this report were added; it is not evidence that those later
commits underwent another full clone gate.

## Finding and decision

[Phase 50](PHASE-50.md) passed its test steps but reported a Windows
`PermissionError` during removal of its temporary `.git/objects` tree. After
verifying that gate-created directory's absolute path under Windows Temp, the
leftover was removed manually. A controlled read-only file in a disposable
clone directory under the workspace `.venv` reproduced the cleanup failure:
the old `_remove_clone` returned `PermissionError` and left the directory.
The reproduction establishes one cause the cleanup can encounter. It does not
establish that the Phase 50 Git-object error had that cause; another process
holding a file open could produce a similar symptom.

[Decision 239](../DECISIONS.md) registered the change before implementation.
The bounded retries remain. On the final recursive removal, a Python
3.10-compatible error callback acts only on a Windows `PermissionError`: it
adds the write bit to the failing path and retries that removal operation.
Other errors still surface in the gate's cleanup note. The code neither
changes a gate verdict nor removes anything outside the gate-created clone.
The implementation is in
[`controlplane/report/clean_clone.py`](../controlplane/report/clean_clone.py),
and the regression is in
[`tests/test_clean_clone.py`](../tests/test_clean_clone.py). This is a QA
harness repair, not a change to the customer command or statistical result.

## Test evidence ledger

The Windows-only read-only-file regression failed against the old cleanup
implementation before the fix: the returned value contained `PermissionError`
and the directory remained. With the repair, the complete clean-clone test
module passed 23/23. The module includes an ordinary deletion, an absent path,
the read-only case and a deliberately persistent permission error; the last
must remain visible rather than being treated as a successful cleanup. Ruff
and whitespace checks passed on the implementation commit. The collection
inventory generated from clean implementation commit `09e77c7` recorded
2,271 tests **collected**, not 2,271 execution passes. That inventory was
committed at `e9724de` before the full gate began.

| Gate step in the retained artifact | Result | Wall time | Meaning |
| --- | --- | ---: | --- |
| Local `git clone` | OK | 5.2 s | Only tracked files from the named source were copied. This was not a remote GitHub clone. |
| Clone HEAD and local notes | OK | 0.0 s; 0.3 s | The clone matched the source commit and obtained local commit notes. |
| Smoke recipe | OK | 3.67 s | Seven import/config/provenance/artifact checks succeeded; provenance in the clone said `dirty=False`. |
| Test preflight | OK | 25.55 s | Test-count and committed-gate-artifact guards succeeded. |
| Full `tests/` suite | OK, return code 0 | 1,564.63 s | Pytest reached 100%; its retained output tail omits the numeric pass summary, so collection is not presented as a pass count. |
| Verify recipe | OK | 29.43 s | Claim table 92/92 and frozen-score recomputation 25/25 succeeded. |
| Activation re-derivation | SKIPPED | 0.0 s | The gitignored extraction cache was absent from the clone. |
| Temporary clone cleanup | No warning | — | The gate did not report a leftover on this run. |

The exact Python command, return code, duration, status and retained output
tail for each step are in the JSON. The verifier's protocol rows are
`TIER|1|claim_table|OK|92/92`, `TIER|2|frozen_scores|OK|25/25` and
`TIER|3|activations|SKIPPED|0/0`. The three pytest warnings in the retained
tail include two SWIG deprecations and a deliberate nonfinite-update warning;
an additional SWIG deprecation appeared at interpreter shutdown. They did
not change the suite's return code. The local `.venv/phase51-clean-clone.exit`
file contained `0`; its accompanying log and the exit file are scratch QA
records, not committed scientific artifacts.

For comparison only, Phase 50's named source had 637 tracked files and its
full-suite step took 1,747.14 seconds, followed by a cleanup warning. The
current source had 638 tracked files and its step took 1,564.63 seconds with
no cleanup warning. Those durations are not a speed comparison: the source,
test count and ambient machine conditions differed. The outcome relevant to
this repair is the absence of a cleanup warning in one real gate after the
deterministic read-only regression turned green.

## What this does not establish; open items

The fix covers a Windows read-only deletion failure and was exercised by one
complete Windows gate. It cannot guarantee removal when an external process
continues to hold a Git object open or when permissions prevent changing the
file mode. Such failures remain reported. The full gate was a local tracked
clone on one Windows/Python environment. It does not establish remote CI on
the final merge, Linux or Python 3.10/3.11 behavior, GPU extraction provenance,
customer data handling, authenticated custody, independent label truth or
buyer demand. The activation tier explicitly skipped its untracked cache.

The next venture evidence gate remains an owner-permitted real scored export,
independent labels and sampling unit, the configured incumbent's report for
the same decision, and an unaided reviewer of the two packets. The
[discovery worksheet](DISCOVERY-2026-10.md) is blank; no completed customer
trial or configured same-decision comparison was supplied. This phase improves
the repeatability of local QA and does not establish a production service or
a fundable company.
