# Phase 48 — Integrated handoff and gate-preservation repair

The clean local suite passed at `37c7b3fa5112afbe4a15c8fa9935861a57176314`:
2,263 tests passed, zero failed and three warnings in 2,118.46 seconds. The
worktree was clean before and after execution. Two earlier red runs exposed
defects that were repaired before that final run. This report keeps those
failures visible; they are part of the QA result, not evidence of a first-try
pass. No estimator, held-out score, scientific artifact or certificate schema
changed. Decisions [237](../DECISIONS.md) and [238](../DECISIONS.md) record the
repair rationale before each implementation.

## The source-evidence preservation failure

The Phase 45 `handoff create` command replayed a prepared input directory,
then allowed `--out` to point *inside that same directory*. The packet was
successfully created, but the original prepared package then had an unexpected
third member and `verify-prepared` refused it. A disposable clean-clone run
against the public synthetic export observed `HANDOFF prepared-certifies\nested-packet`
with exit 0, followed by `warrant: incomplete or unexpected package files;
retain both outputs` with exit 2 from `verify-prepared`. This was a real
preservation defect: the packet contents existed, but its creation damaged the
replayability of the evidence from which it was assembled.

The repair in `controlplane/intake/handoff.py` resolves the destination and
prepared paths before making the output directory. It rejects an equal or
nested destination, including a normalized `..` alias, as an input error. It
does not weaken the prepared package's exact-member rule. The red-before
regression produced three failures; after the code change the three cases
passed. The adjacent handoff/preparation modules passed 73/73. The installed
wheel test passed 1/1 and checked the same exit-2 refusal through the packaged
command, absence of a new packet, and successful replay of the original
prepared evidence. `docs/INPUT.md` now states the destination constraint.

## The failed-gate artifact collision

The first resumed full-suite attempt at `e488c39` was saved to a durable log.
It stopped after 249 passes and one failure at
`test_failed_default_clone_keeps_green_record_and_separates_attempts`.
`write_outcome_artifact` used `time.time_ns()` as the entire unique portion of
its filename. Two consecutive failed attempts received the same value on this
Windows run. Exclusive creation correctly prevented replacement of the first
failure file, but the second attempt raised `FileExistsError` instead of
retaining its own record. The log and exit 1 were preserved in ignored local
`.venv/phase48-full-resume.log` and `.exit` files; they are not committed
artifacts.

Decision 238 was committed before implementation. The existing two-attempt
test now fixes `time.time_ns()` to one value, and failed deterministically
before the repair. The implementation keeps the original timestamped first
choice, then uses numbered suffixes on occupied filenames with exclusive
creation. It does not retry unrelated filesystem errors or replace the last
passing canonical record. The whole clean-clone reporting module passed
21/21, and Ruff plus `git -c core.whitespace=cr-at-eol diff --check` passed.

## Evidence ledger

| Check | Source and command | Observed result |
| --- | --- | --- |
| Nested output red-before | `pytest tests/test_handoff.py -k nested_destination` before the path guard | Three failures: library calls did not raise and the CLI returned success. |
| Handoff and preparation after repair | `python -m pytest tests/test_handoff.py tests/test_prepare.py -q -p no:cacheprovider --basetemp <workspace temp> -o addopts=--strict-markers` | 73 passed in 171.50 s. |
| Installed shipped command | `python -m pytest tests/test_package_install.py::test_installed_handoff_replays_without_checkout -q` with the same pytest isolation flags | 1 passed in 91.73 s. |
| Test-count guard at first source commit | Isolated `test_every_stated_test_count_is_the_real_one` at `4f2553d` | Failed: 2,263 collected while README and Makefile stated 2,260. The inventory script then recorded 2,263 from clean source; the isolated guard passed. |
| Failed-artifact collision red-before | Isolated `test_failed_default_clone_keeps_green_record_and_separates_attempts` with constant nanoseconds | Failed with `FileExistsError` on the second exclusive write. |
| Collision repair module | `python -m pytest tests/test_clean_clone.py -q -p no:cacheprovider --basetemp <workspace temp> -o addopts=--strict-markers` | 21 passed in 4.48 s. |
| Final integrated suite | `python -m pytest tests/ -q -x -p no:cacheprovider --basetemp <workspace temp> -o addopts=--strict-markers` at clean `37c7b3f` | 2,263 passed, 3 warnings, 0 failures in 2,118.46 s; durable local exit file contained `0`. |
| Smoke | `python scripts/smoke.py` at clean `37c7b3f` | 7/7 passed, provenance `dirty=False`. |
| Claims and frozen scores | `python scripts/verify.py --no-activations` at clean `37c7b3f` | Exit 0: claim table 92/92, frozen-score comparisons 25/25, activations explicitly SKIPPED 0/0. |
| Source collection inventory | `python scripts/refresh_test_inventory.py` from clean `0fa8846` | 2,263 collected for the tested source; artifact says `execution_status=not_measured_by_collection`. Collection is not execution. |

The three pytest warnings were two SWIG type `DeprecationWarning`s and a
`RuntimeWarning` from the deliberate nonfinite-update test in
`controlplane/validation/warrant_stats.py`. They were reported, not converted
into failures or hidden. The source commit in the collection artifact is the
clean commit *before* that generated artifact was committed; the final full
suite was executed at the later clean `37c7b3f` commit with the same collected
count. Adding this report and its index entries subsequently made the
documentation test collector report 2,265 cases. Those added cases need the
separate report/link gate and a refreshed inventory; they are not part of the
2,263-case clean-source full-suite result. An earlier full run at `e488c39` was deliberately stopped at roughly
9% after its test-count failure, and another run reached 60% without a
retained final status across a session boundary. Neither is counted as a
pass. The final durable log and exit file are the executed pass.

## What this does not establish

The suite exercises local software behavior on this Python 3.12 Windows host
and mostly synthetic fixtures. The final full test run did not fetch a clean
remote clone or re-extract GPU activations. The earlier Phase 47 installed
clone and Phase 45 installed-wheel checks remain separately scoped evidence.
The claims tier proves README values resolve to committed artifacts; the
frozen-score tier recomputes retained metrics. The activation tier was skipped,
so neither tier establishes that the cached scores came from the named model
on a fresh run. Remote CI on the final head was not observed.

The path guard prevents ordinary nested output from invalidating the prepared
directory, but it is not a filesystem sandbox: a hostile process could race a
path between resolution and creation. The collision retry preserves ordinary
consecutive failed-gate records, but cannot guarantee recording under a disk
failure or malicious directory changes. Neither repair authenticates packet
origin, label truth, sampling independence, nor reviewer sign-off.

## Open items and next decision

The commercial gate in [the October plan](BUILD-PLAN-2026-10.md) is still open.
No unaided reviewer filled out the [discovery worksheet](DISCOVERY-2026-10.md),
no owner-permitted customer export or actual incumbent packet was supplied,
and no repeat release decision or willingness to pay was observed. The next
useful test is one permissioned same-decision comparison: preserve the scored
export, label source, group unit, selection history and existing reviewer
packet; ask an independent reviewer what Warrant changes in their sign-off.
If the incumbent packet already answers that decision, the appropriate result
is to narrow or stop the product hypothesis, not to build an unrequested
adapter. A passing engineering gate alone does not make the venture fundable.
