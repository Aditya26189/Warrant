# Phase 35 - A clean-clone technical handoff, with the human gate still open

The discovery worksheet now leads a reviewer through the complete public
synthetic handoff instead of stopping at the four-row mapping example. A
tracked-file clean clone of the corrected worksheet's commit completed all
four documented commands in a fresh customer-only virtual environment:
prepare, verify-prepared, certify and verify. The technical week-one example
is runnable from a stranger's starting point. There has still been no human
dry run, customer export or review decision, so the plan's week-one user gate
has not passed.

## Question and scope

The worksheet in `reports/DISCOVERY-2026-10.md` was created before the
Phase 33 public export. It told a prospective reviewer to prepare and replay
`examples/export_sample.csv`, which has only four synthetic rows and cannot
support a useful false-positive certificate. It stopped before certification
and did not show the second replay boundary. That was a mismatch with the
newly available handoff, not a statistical or CLI defect. The worksheet now
points to the canonical four-command sequence in `examples/README.md` rather
than maintaining another copy of the commands. It names the retained source,
mapping, prepared package and certificate, and explains that the 400 rows are
a recoding of the existing seeded certificate example, not new evidence.

The question for this phase was whether the updated path works from a clean
clone with only customer dependencies. Phase 33 manually ran the commands in
its worktree and Phase 34 put the integration regression in the customer CI
list. Those checks are useful but neither is exactly the worksheet's
first-run setting: a tracked-file clone and a newly resolved venv. This phase
executes that setting and records the limits separately.

## Work and findings

The worksheet correction was committed as `c4eb8a3`. Its documentation link
checks passed 69/69. I cloned branch `docs/week-one-handoff-gate` from the
local repository using `git clone --no-local` into a new OS-temp directory.
The clone had 619 tracked files, HEAD `c4eb8a3`, and a clean `git status
--porcelain`. Untracked `ARC180_BRIEF.md` in the shared checkout was not
copied. A new Python 3.12.10 venv outside the clone installed only
`requirements-customer.txt`; pip resolved NumPy 2.5.3, SciPy 1.18.1 and
PyYAML 6.0.3, and `pip check` found no broken requirements. There was no
package installation, editable install, model download or research stack.

With that venv's `Scripts` directory first on `PATH`, I ran the exact
PowerShell setup and four `python warrant.py` commands printed in
`examples/README.md` section 4, from the cloned repo root. Output went to a
new OS-temp handoff directory, so the clone stayed clean. The four exit codes
were `0,0,0,0` over 45.28 seconds. The sequence reported `PREPARED`,
preparation `VERIFIED`, `WARRANT: VALID`, and certificate `VERIFIED`. The
certificate covered 400 synthetic rows: 102 positive, 298 negative. Its
observed false-positive bound was 0.0479 against a declared 0.05 budget,
with 8 false positives on 298 independent negative units as the synthetic
fixture declares. This is the existing example's result, not another test of
a detector. `git status --porcelain` in the clone remained empty afterward.

The two `VERIFIED` lines have distinct meanings. `verify-prepared` rebuilds
the canonical scored file and manifest from the retained source export and
mapping. `verify` recomputes certificate fields from the effective scored
rows. The source-only `captured_at` values are covered by the preparation
boundary but not by the certificate. Neither command proves that the labels
or independence declaration are true. The worksheet now states these limits
beside the practice path so a reviewer does not mistake a replay for
authenticity or data quality.

## What this does not establish

This was an agent-executed local clean clone on Windows, not an unaided human
trial. It does not establish that a new reviewer understands the mapping,
selects the right budget, retains the four files or can interpret a refusal.
The fixture is seeded synthetic data. It does not establish performance on a
customer detector, the feasibility of human labels, a real independent unit,
or the value of the certificate to a release decision. The local clone does
not show GitHub's Linux 3.11/3.12 CI result for this unpushed branch, and it
does not regenerate activations or rescore the protected research test set.

The observed `VALID` result depends on the synthetic labels and declared
independence. It is not a safety approval for an AI assistant. The two
checksums are replay and integrity mechanisms, not source authentication.
The work changed a discovery document only; it did not implement a customer
adapter or change the certification math. The user gate in the October plan
requires another person, and software cannot substitute for that observation.

## Open items

The next useful test is for a reviewer who did not build Warrant to follow
the worksheet, retain the source and mapping, and describe both replay
results without coaching. Record where that person gets stuck; do not count
this automated clone as that trial. A real scored export also needs an owner,
permission to use it, label provenance, score direction, a sampling-unit and
group declaration, and an actual recurring threshold decision. None has
been supplied. The October 14 targets of five conversations, two usable
exports and one named decision remain targets, not observed results. Until
that evidence exists, speculative platform or vendor adapter work remains
unjustified under the October plan's stop rule.

## Ledger

| Change or check | Evidence |
|---|---|
| Worksheet correction | `c4eb8a3`; `reports/DISCOVERY-2026-10.md` points to the four-command public handoff |
| Documentation link check | 69 passed after the worksheet correction |
| Tracked-file clone | `git clone --no-local --branch docs/week-one-handoff-gate`; clone HEAD `c4eb8a3`, 619 tracked files, clean status |
| Fresh dependency resolution | Python 3.12.10; only `requirements-customer.txt`, NumPy 2.5.3, SciPy 1.18.1, PyYAML 6.0.3; `pip check` clean |
| Exact documented handoff | PREPARED, VERIFIED, VALID, VERIFIED; exit codes 0/0/0/0, 45.28 seconds; clone remained clean |
| Human user gate | No human dry run, real export or review decision observed |
