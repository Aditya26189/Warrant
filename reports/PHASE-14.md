# Phase 14: serialize chain publication and recover interrupted writes

Local repair checkpoint, 24 September 2026. Continuation of the founder's
handoff, on `fix/chain-publication`, based on the completed Phase 13 checkpoint
`290c5e0`. The shared checkout and earlier worktrees are preserved.

> Follow-up: the missing-seal policy repair R6 is recorded in
> [PHASE-15.md](PHASE-15.md). The results below remain the Phase 14 checkpoint.

## Question and answer

Can two concurrent rechecks silently accept different successors of the same
local chain head, and can an interrupted write leave an ambiguous next step?

The old check/write sequence allowed that race (audit R4). The new command holds
a per-warrant OS lock over validation and publication. It retains a sealed
publication intent so a later command can finish the exact original record
after process interruption. The tested contract is for cooperating local
processes, not distributed storage or resistance to deliberate history removal.

## Work completed

- Register the protocol and acceptance cases before implementation in decision
  206. Preserve existing chain, fork, revocation and statistical rules.
- Share artifact preparation with the ordinary writer so a record receives its
  provenance and seal once. Recovery cannot refresh its timestamp or decision.
- Publish complete files through same-directory temporary files. New evidence
  uses a hard link without replacement; only the mutable head uses replacement.
  Unsupported filesystem operations fail explicitly.
- Acquire a nonblocking OS lock using the canonical warrant path before reading
  the head or validating a parent. Keep the lock name after exit; another process
  can acquire the OS lock when the holder closes or exits.
- Retain the complete sealed record, prior head and absolute destination in a
  sealed pending intent. Publication writes the record, advances the head, then
  removes the intent. Recovery accepts either the old head or this exact new
  head, and refuses changed warrants, conflicting records or malformed state.
- After recovery, exit 2 with the recovered path. No further link is accepted
  implicitly. The user can inspect the retained result and explicitly continue
  with `--since` if its status and horizon permit.
- Add synchronized real-process races for both initial and successor links,
  real process exits after intent/record/head writes, conflict and alias tests,
  and a built-wheel test of contention and default output location.

## Findings during verification

The first broad regression batch had **126 passes and one failure**. The existing
`test_a_chained_recheck_never_overwrites_and_names_its_link` caught a mistake in
this refactor: `items.source` is a display label, not the original input path.
Using it put the default record in the working directory. The command now passes
the actual input path explicitly. The assertion was retained, and the installed
regression also uses the default output path. The stray synthetic test artifact
was removed from this isolated checkout after its origin was checked.

A primitive test initially compared bytes against the legacy Windows text-mode
writer. That writer uses CRLF; the atomic writer uses deterministic UTF-8/LF.
The compatibility assertion now checks identical parsed JSON and a reproducing
seal, which bind content rather than whitespace. Recovery itself requires the
exact prepared atomic representation when a destination already exists.

No scientific test set was reopened, statistical method changed, or frozen
research output regenerated. No customer data or external outreach was used.

## Completed validation ledger

All execution in this ledger was local Windows Python 3.12.10. The minimal
customer environment held NumPy, SciPy and PyYAML plus build/test tools, with
no research-model stack. The batches overlap; their counts are not additive
coverage and are not a full-suite result.

| Check | Result | Evidence retained locally |
|---|---|---|
| Artifact preparation and atomic primitives with existing config tests | 50 passed, exit 0 | Initial primitive/config run |
| Initial concurrent-process and interruption suite | 15 passed, exit 0 | `.venv/chain-publication-initial.xml` |
| First broad chain/lifecycle batch | 126 passed, 1 failed, exit 1 | `.venv/chain-publication-minimal.xml`; default-path defect described above |
| Corrected chain/lifecycle batch, including alias and malformed-state cases | 127 passed, exit 0 | `.venv/chain-publication-minimal-final.xml` |
| Final built-wheel workflows, including contention and default location | 14 passed, exit 0 | `.venv/chain-publication-installed-final.xml` |
| Documentation, decision integrity and packaging | 82 passed, exit 0 | `.venv/chain-publication-docs.xml` |
| Packaging after CI expansion | 10 passed, exit 0 | Subsequent targeted run |
| Repository-wide configured lint and whitespace audit | Passed | `ruff check` and `git diff --check` |

The XML logs are disposable local test evidence, outside versioned scientific
results. The reproduction commands below exercise the committed tests. Remote
Linux, Windows/Python 3.10 and customer Python-version jobs are configured, but
were not observed running for this branch. Full-suite and integration validation
remain pending. No new release tag is asserted by this repair checkpoint.

## What this does not establish

- These checks do not establish production reliability, throughput, regulatory
  acceptance, customer demand or fundability.
- This is coordination between processes using the same canonical warrant path.
  It does not coordinate separately copied warrants, distributed writers or
  writers that bypass the protocol. Do not remove an active lock file to bypass it.
- OS locks and atomic filesystem operations require supporting filesystems. No
  universal power-loss durability is claimed; Windows directory durability and
  network filesystem semantics are not demonstrated here. Process termination
  can leave an unreferenced temporary file, which is not an accepted chain link.
- Checksums do not authenticate authors or prevent consistent rewriting. The
  separate legacy seal-removal policy defect R6 remains open.
- Unchained rechecks still ignore the chain head. Identity, expiry and input
  binding of ordinary certification need their separate product/schema contract.
- The protected grouped-interval defect R2, malformed-input findings R7, PSI
  reference-size calibration R8, operating-point handoff R9 and legacy monitor
  bound R10 remain open. This repair does not quietly modify protected code.

## What remains and how to close it

Review and integrate the accumulated installed-package, Phase 13 and Phase 14
repairs after the integration gate passes. Remote Linux and Python-version jobs
must actually run before claiming cross-platform verification. Retain the
independent audit as historical evidence; do not relabel every finding closed
because this one now has a bounded repair.

The commercial gate is unchanged: conduct eight to twelve conversations with
validation and compliance leads. If fewer than three of twelve can name a wrong
AI control claim with consequences, treat this as research. No new commercial
evidence was supplied during this work. Further feature volume is not a substitute
for that test; the [pilot protocol](../docs/PILOT-PROTOCOL.md) applies if it passes.

## Design sources and reproduction

Decision 206 records the protocol, its alternatives and the access limitations
of its source review. The lock APIs are documented by
[Python msvcrt](https://docs.python.org/3/library/msvcrt.html) and
[Python fcntl](https://docs.python.org/3/library/fcntl.html); the file operations by
[Python os](https://docs.python.org/3.10/library/os.html) and
[Linux link(2)](https://man7.org/linux/man-pages/man2/link.2.html).
Those sources describe primitives; they do not validate this application protocol.

Use the customer dependencies plus pytest, setuptools and wheel to reproduce:

```powershell
python -m pytest -o addopts= -q tests/test_atomic_publication.py tests/test_chain_publication.py tests/test_recheck.py tests/test_recheck_chain.py tests/test_recheck_chain_review.py tests/test_recheck_groups.py tests/test_recheck_label_sensitivity.py tests/test_recheck_revocation_priority.py tests/test_chain_verify.py
python -m pytest -o addopts= -q tests/test_package_install.py
python -m ruff check controlplane/ scripts/ tests/ warrant.py
```

Installed tests build a direct wheel and an sdist, rebuild the latter into a wheel,
and install into a temporary target below an unrelated Git repository. Running
under a minimal environment proves the dependency boundary; running under a full
research environment alone would not.


## Commit and handoff ledger

- `4675957`: register decision 206 before implementation.
- `430b187`: shared artifact preparation and atomic file primitives.
- `c0fd3e4`: locked publication, exact recovery and source regressions.
- `039a263`: installed contention/default-path regression and CI expansion.

The repair branch includes the prior packaging and Phase 13 fixes as ancestors.
Local main remains at `cc1904e`; these repairs have not been merged or pushed.
The old dirty shared checkout and other agents' historical worktrees remain
intact. This is a local correctness checkpoint, not a completed release gate.


Final inventory collection from clean source
`56285147305aa1985785ed6e52d98f0b21c3bf62` recorded **1966 collected tests**, up
from 1933. Commit `66aaef8` contains that generated inventory. The subsequent
claims, inventory and README-prose batch passed all 21 tests (exit 0), with
local XML at `.venv/chain-publication-claims.xml`. This collection count is not
a claim that the entire suite executed. The final source worktree was clean
at handoff; integration and remote CI remain open.
