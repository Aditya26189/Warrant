# Final repository consolidation and presentation

The release brings the completed committed work onto one release line and
provides a clear route through the working toolkit and its research evidence.
Scientific conclusions and original numerical artifacts retain their scope.

## What changed

- Merged the assurance/publication exploration, unscored-trials closeout, and
  stopping-feedback feasibility branches with their original history.
- Replaced the decorative remote banner with a repository-owned SVG and a
  concise description of the working software.
- Added an audience-oriented project overview and a research portfolio linking
  each study's findings, reproduction, and explicit completion or stopping state.
- Added a research-workstream index and a separate offline research CI workflow.
- Recorded branch integration and preserved historical local drafts and private
  review packages outside the public release.

## Verification boundary

The research suites were checked during integration. The initial attempt used
an existing customer-only environment and stopped at collection because tqdm
was absent. Re-running with the existing research interpreter resolved that
environment mismatch. A whitespace check initially treated preserved CRLF
scientific evidence as trailing whitespace; recognizing CR-at-EOL allowed the
check without rewriting the evidence bytes.

The integrated artifact and numerical verification completed; activation
re-derivation is outside this CPU release pass. Final clean-source suite and
clone-gate results are recorded below once the release source is committed.
No new model extraction, benchmark acquisition, label adjudication, or paid
compute was performed.

The real fresh-clone acceptance test also exposed a Windows path-length
failure in the retained grader fixtures. Decision 241 records the repair:
set core.longpaths in each new clone before checkout, and show that option in
the PowerShell quickstart. This preserves the original evidence layout and
does not require changing a user's global Git configuration.

## Remaining limits

This is an installable local evaluation toolkit and research artifact. No
production deployment, commercial validation, authenticated provenance, or
independent human source adjudication is established by presentation polish.
The adaptive returned-bound issue FPR-001 remains open and is linked from the
entry pages; this release does not apply an unreviewed statistical repair.
The closed grader, unscored-trial, and stopping-feedback decisions remain
closed. Publication proposals are historical planning material.

## Reproduce

    python scripts/smoke.py
    python -m pytest tests/ -q
    python scripts/verify.py --no-activations
    python -m pytest -q experiments/assurance_semantics/test_exact.py
    python -m pytest -q experiments/unscored_trials/tests
    python -m pytest -q agent-stopping-feedback-study/tests
    python scripts/clean_clone_gate.py

See the [branch audit](../docs/BRANCH-INTEGRATION.md),
[project overview](../docs/PROJECT-OVERVIEW.md), and
[research index](../experiments/README.md) for source and evidence entry points.
