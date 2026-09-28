# Phase 16: current product state made reviewable

Documentation audit, 28 September 2026. This phase responds to the founder's
request to walk the repository and make the extent of completed work clear to a
new reader. The review began from local `main` at `02d1483`; changes were made
on the isolated `docs/product-state-2026-09-28` worktree. The original shared
checkout and Claude's worktrees were left untouched.

## Question and answer

Can an evaluator tell what Warrant actually does today, which claims reproduce,
and where a production or fundability claim would go beyond the evidence?

The new [product-state map](../docs/PRODUCT-STATE.md) answers that in one place.
It distinguishes an installable local command, a reproducible research harness,
demonstrations and declared but unproven enterprise capabilities. The README and
documentation index now route a reader there before they mistake a demo or
configured CI job for deployment evidence. This is a documentation and evidence
clarification, not a product launch or a claim that a buyer exists.

## Work completed

- Traced the public command from `warrant.py` and `controlplane/cli.py` into
  `controlplane/intake/`, `controlplane/release/`, planning and their source and
  installed tests. Ran the command's `--help` paths to confirm the exposed
  certify, recheck, plan, release and chain verbs.
- Read the research and demonstration packages, the frozen `results/` artifacts,
  `scripts/verify.py`, the clean-clone record, the test inventory and CI workflow.
  The product-state matrix links each surface to those sources and names what its
  evidence does and does not establish.
- Compared the independent review and later repair commits with current code.
  R7 malformed-number refusal, R8 PSI reference-size calibration, R9 handoff
  operating-point warning and the unchained-recheck revocation repair are now on
  local `main`. The protected grouped-interval R2 and legacy-monitor R10
  findings remain open. Older phase reports are dated checkpoints, not a
  current-main defect list.
- Corrected setup's Python-version statement: CI declares a Windows minimum
  version installed-wheel job, but the declaration itself is not a passing run.
  Corrected the shell activation example and the index's outdated “latest
  phase” description. Added a test-evidence note explaining collection, local
  execution, frozen-score reproduction and remote CI as distinct observations.
- Preserved all generated scientific results and avoided any test-set rescore.
  The new page carries no copied metric table; readers follow the claim table
  to the artifact and verifier that establish each research number.

## Verification and findings

On the committed documentation changes `e3d7d3d` and `cdcc10f`, the focused
documentation/claim/decision/report batch passed **130 tests**, with the one
test-count check deselected until the clean-source inventory could be refreshed.
An earlier sandboxed attempt reached **125 passes, one count failure and five
temp-directory errors**. The errors were Windows `PermissionError` for pytest's
default temp root; rerunning with temp access passed. The count failure was
real and expected: adding a docs page adds parametrized link checks. The count
is regenerated from a clean committed source after this report, not typed into
the README by hand.

The clean-source claim verifier completed with exit zero: **92/92 claim rows**
matched committed artifacts and **25/25 frozen-score comparisons** reproduced.
Activation regeneration was explicitly skipped. The installed-package and recent
repair batch completed with **110 passes**, including package installation,
atomic publication, chain integrity, malformed numeric input, PSI reference
size and unchained revocation checks. These are local Windows results for this
branch. The full suite was attempted but stopped during its early portion
because it was taking substantially longer; there is **no full-suite pass** for
this documentation head. Remote CI results were not observed in this phase.

## What this does not establish

- No customer supplied scored production data, design-partner commitment,
  interview, pilot, procurement evidence or revenue. No fundability conclusion
  follows from the local tests. The preregistered discovery gate in
  [STRATEGY-2026-09.md](STRATEGY-2026-09.md) remains unrun.
- Frozen-score reproduction does not regenerate activations from the model, and
  the local targeted test batch is not the full suite or the remote CI matrix.
- The customer CLI is a local file workflow. There is no hosted service,
  authentication, tenant isolation, deployment manifests, availability target
  or demonstrated live-traffic integration. The gate and monitoring studies do
  not close those operational gaps.
- Checksums on retained release and chain records do not authenticate an
  author. Ordinary certify warrants lack input-row binding, identity, expiry and
  a verifier. The detailed record-level boundary is in
  [EVIDENCE-HANDOFF.md](../docs/EVIDENCE-HANDOFF.md).
- The grouped-interval R2 and legacy monitor R10 review findings remain open.
  Nothing in this documentation phase changes their statistics.

## Open items

Before treating this branch as a release, run the complete test suite and the
remote CI matrix on the exact merged head, review its installed-wheel journey,
and resolve or explicitly constrain the remaining statistical findings. The
documentation inventory must be regenerated from a clean source commit after
this report is added, because report-link tests also affect collection. The
commercial next step remains the registered validation-lead conversations, with
the stopping rule stated before outreach; the [pilot protocol](../docs/PILOT-PROTOCOL.md)
is useful only if that gate supports a pilot.

## Source and reproduction ledger

- `02d1483`: local `main` source reviewed, including Claude's merged R7–R9 and
  later repair stack; no remote status inferred from this hash.
- `e3d7d3d`: product-state page, README entry point and docs index.
- `cdcc10f`: setup and verification-evidence corrections.
- `python warrant.py --help` and subcommand help: public surface inspected.
- `python -m pytest -o addopts= -q tests/test_docs_index.py
  tests/test_readme_prose_numbers.py tests/test_reports.py
  tests/test_decisions_integrity.py tests/test_claims.py -k
  "not test_every_stated_test_count_is_the_real_one"`: focused green batch.
- `python scripts/verify.py --no-activations`: claim/frozen-score tiers green,
  activation tier skipped.
- `python -m pytest -o addopts= -q tests/test_package_install.py
  tests/test_atomic_publication.py tests/test_chain_publication.py
  tests/test_chain_integrity_policy.py tests/test_malformed_numeric_inputs.py
  tests/test_psi_reference_size.py tests/test_recheck_after_chain_revocation.py`:
  installed and repair batch green.
- `python -m pytest -o addopts= -q tests/`: interrupted, no pass claim.
