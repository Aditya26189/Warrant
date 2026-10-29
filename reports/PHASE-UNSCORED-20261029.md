# Unscored-trials decision study — 29 October 2026

**Decision: REPORT.** The prepared handoff is published on GitHub main; the
research extension is preserved separately on `research/unscored-trials-20261029`.
No paper was submitted and no one was contacted.

## Publication and scope

Only the reviewed execution plan and agent handoff were integrated into main:
documentation commit `ef6e0fcb9703a31d82753c40dbda1f06c5662edc`, integration commit
`b5e34e9924142717a8c207cb830a1d916054a0d8`, tag `unscored-handoff-20261029`.
Remote main and the tag were verified. No force push or unrelated branch merge
was used. The supplied prepared worktree and frozen baseline were preserved.
Production, FPR and the closed grader-mutation track were not changed.

## Actual research result

The [findings](../docs/research/unscored_trials/FINDINGS.md) and
[decision](../docs/research/unscored_trials/PUBLICATION_DECISION.md) explain the
evidence and strongest objection. The official pinned final-record census is
feasible. Native zero accounting reproduces on the strict cohort; equal-task
versus pooled weighting has zero effect there. Raw/summary differences are
source-linked, but their causes and original attempt history are unresolved.
Closest-work overlap prevents a convincing submission upgrade on this evidence.
The completion bounds are hypothetical and do not recover corrected rankings.

All required accounting outputs, source manifests, cohort exclusions, native
checks, policy/pair tables, baseline receipts, audit worksheet and replay evidence
are under [the result directory](../results/unscored_trials/20261029-terminal-bench2/summary.json).
No planned-slot table or retry lineage was fabricated. Human review remains
pending. See [the claim ledger](../docs/research/unscored_trials/CLAIM_LEDGER.md).

## Validation, failures and remaining work

The clean canonical run at `92f162a8fee29f8f65bdd9293269e0bacb4d6411` passed its
blocked-network replay: all 107 canonical files byte-identical. The preserved
baseline reproduced all 15 numerical files with 21 tests passing. Scoped test
receipts cover retrieval integrity, normalization, exact bounds, reconciliation
and the post hoc explanatory arithmetic. Publication smoke checks and the
repository's non-activation verification also passed; no production behavior
changed.

Retained failures include temporary ACL/dependency problems, a dirty discovery
invocation, incomplete Git-stderr cleanliness detection, an acquisition budget
safe stop, transient HTTP failures/size caps and two serialization fixture
failures. These prompted logged fixes and clean reruns; they are not reported as
successful checks. One job-summary URL remains HTTP 404. A delegated check was
interrupted by account usage/approval-review capacity; later root checks completed
without buying credits. The decision log records these qualifications.

Active research/engineering effort is estimated conservatively below ten hours
in aggregate across root and delegates, below the twenty-hour ceiling. This is
an estimate, not an instrumented timesheet. Elapsed wall time includes a long
inactive usage-limit interval; retrieval timestamps and command receipts remain
in the external study directory. Added paid compute/API cost: INR 0.

Exact replay needs the retained external cache; a fresh public clone alone lacks
historical manifests and failed receipt bytes. Its durable location and validation
are recorded with the outputs. A public input bundle, human source verification,
original roster/attempt lineage and pinned website importer/adjudication evidence
are precisely identified remaining work, not completed publication artifacts.
No conditional manuscript stage was started. Stop here unless new evidence
justifies reopening the gate.
