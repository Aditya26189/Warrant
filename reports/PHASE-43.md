# Phase 43 - Week-one technical gate passes; human gate remains open

The 7 October clean-source full suite passed at integrated commit `98ba529`:
2,230 tests passed, zero failed, three pytest warnings, exit 0, in 3,269.60
seconds (54m29s). This closes the local **technical** week-one regression
gate for the current source and its public synthetic handoffs. It does not
close the plan's unaided-human dry run, real-export or demand gates. Those
observations have not been recorded.

## Question and scope

The October plan's Day 7 gate calls for an exact tested commit, report and
usable commands, with any human trial recorded separately. Since the last
full-source suite in Phase 36, Phases 37-42 added dated research, public
valid/refused/tamper demonstrations, installed-wheel and interrupted-write
regressions, a fresh-clone run and a blank reviewer worksheet. Each changed
area had focused checks, but no single full-suite result covered their
integrated local head. The user also explicitly authorized pushing to GitHub
`main` after each completed phase. This phase measures the integrated source
before closing and publishing its own checkpoint.

The measured commit is the local Phase 42 merge `98ba529d66c9f9c4d6719b39a8620d9c4dfc38e1`.
The run used a separate worktree checked out at that commit, with an empty
`git status --porcelain` before and after. The OS-temp `--basetemp` kept test
scratch files out of the checkout. The shared checkout's untracked
`ARC180_BRIEF.md` was not staged or altered. The full suite was executed once
on Windows under Python 3.12.10 with the current local research dependencies:

```text
python -m pytest tests/ -q -p no:cacheprovider --basetemp <OS-temp> -o addopts=--strict-markers
2230 passed, 3 warnings in 3269.60s (0:54:29)
exit 0
```

This is an execution result, unlike `results/test_inventory.json`'s
collection count. The inventory on this tested source also said 2,230
collected. Adding this report makes two more report-parametrized cases in the
next inventory; those additional cases are checked separately and are not
retroactively part of the 2,230-test full-suite result.

## Observed warnings and other checks

Two pytest warnings came from SWIG extension types without a `__module__`
attribute: `SwigPyPacked` and `SwigPyObject`. The third was a `RuntimeWarning`
from division by zero in `controlplane/validation/warrant_stats.py:193`,
raised by `test_a_non_finite_update_raises_rather_than_asserting`. That test
intentionally exercises the non-finite update path and passed. After the
pytest summary, interpreter shutdown printed a further `swigvarlink`
deprecation warning. It was outside pytest's three-warning count and did not
change its exit code. None of these warnings is being reported as a failed
test, and none is being hidden as a zero-warning run.

The public source handoffs were separately run from a fresh tracked-file
clone in Phase 41: preparation, preparation replay, certification and
certificate replay produced a valid record; the grouped four-row example
produced a refused record; and changing an excluded source note caused
preparation replay to report mismatch while the unchanged certificate still
verified. The Phase 39 installed-wheel module passed 19/19 in the lightweight
customer environment. Phase 40's complete preparation module passed 52/52
with a partial-manifest write fault injection. Those are separate
commit-specific measurements, now supplemented by the full integrated suite.

On 7 October, before this phase report was written, GitHub `main` was
fast-forwarded from `8556585` to `98ba529`, and missing phase tags 31-42
were published. `git ls-remote` confirmed `main` and `phase-42` both at
`98ba529d66c9f9c4d6719b39a8620d9c4dfc38e1`. The unauthenticated GitHub
Actions API returned 404 for this repository, so a remote CI result for this
commit was not observed. A successful push and configured workflow are not
a CI pass. The Phase 43 push and remote-ref check belong in the final ledger.

The clean-source smoke, README claim replay and frozen-score recomputation
are run after the report and test inventory are committed; their exact
outcomes are recorded below. The activation tier requires cached model
activations or a GPU extraction, and is explicitly skipped when running the
available CPU verifier with `--no-activations`.

## What this does not establish

The suite exercises code and committed synthetic/frozen artifacts. It does
not establish that a customer can obtain independent human labels, that the
declared grouping and selection assumptions hold on live traffic, or that a
reviewer values the refusal. It does not show anyone outside the project has
used Warrant. No human followed the newly updated blank first-run worksheet
without author assistance. The Day 7 user gate is therefore open even though
the technical gate passed.

The full run was local on Windows and Python 3.12.10. It is not evidence that
the configured Windows Python 3.10 or Linux Python 3.11/3.12 CI jobs passed
for this commit. Nor does the full pytest suite re-extract the protected
question-time activations or repeat a model run. Frozen-score verification
checks retained arithmetic, while the skipped activation tier limits what
can be said about original extraction provenance.

The synthetic clean-clone valid case reuses the seeded example and the
refusal case has only two declared groups. Their outputs are correct local
demonstrations, not estimates for a deployed detector or proof that an
incumbent packet lacks the same information. The user's month plan is not
complete merely because its first technical milestone is tested. Several
later items require an owner-approved export, an actual packet or a calendar-
later repeat use that cannot be manufactured by additional local tests.

## Open items

The immediate human task is an unaided trial of the two public walkthroughs
using the blank observation table in `reports/DISCOVERY-2026-10.md`. Record
the participant's environment, exact failed command, statuses, elapsed time
and explanation of the two replay boundaries before coaching. A real export
requires its owner, permission, retention rule, score direction, human label
provenance, sampling unit and a named threshold decision. The October 14
commercial targets of five conversations, two usable exports and one
recurring decision remain targets, not observed results.

The scheduled 8 October research refresh should look for new dated official
evidence and an actual configured incumbent packet if one is made available.
Until a reviewer identifies a concrete missing handoff step, the package
design review's condition against speculative bundling still applies. If a
supported-version CI job or a real first run fails, reproduce its exact
environment and make that the next engineering regression. Keep remote CI
status marked unknown until a run for the published commit can be inspected.

## Ledger

| Change or check | Evidence |
|---|---|
| Integrated source under test | `98ba529d66c9f9c4d6719b39a8620d9c4dfc38e1`; clean isolated worktree before and after |
| Full-suite command and outcome | Command above; 2,230 passed, 3 pytest warnings, exit 0, 3,269.60 seconds |
| Week-one source CLI practice | `reports/PHASE-41.md`; clean clone, valid/refused/tamper outcomes |
| Installed wheel and interrupted marker | `reports/PHASE-39.md` and `reports/PHASE-40.md`; 19/19 and 52/52 focused modules |
| Prior completed-phase publication | Remote `main` and `phase-42` verified at `98ba529`; tags 31-42 pushed |
| Human dry run | None observed; `reports/DISCOVERY-2026-10.md` remains blank |
| Clean documentation and inventory gate | Pending final report commit and refresh |
| Clean smoke and available verifier | Pending final report commit |
| Phase 43 remote publication | Pending final phase merge, tag and push |
