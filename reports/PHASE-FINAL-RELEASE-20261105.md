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

The integrated artifact and numerical verification completed. No new model
extraction, benchmark acquisition, label adjudication, or paid compute was
performed. Activation re-derivation is explicitly skipped.

## Completed local checks

| Check | Result | Source and scope |
|---|---|---|
| Lint | Passed | Core code, scripts, tests, CLI, and all three newly integrated research suites |
| Windows fresh-clone and gate-contract regressions | 27 passed | Clone repair at `5ca1e09`; uses repository-local long-path configuration |
| Report-series guard | 124 passed | `a2041af`; includes the three newly retained named reports |
| Assurance semantics | 3 passed | Clean source `d17f6fa` |
| Unscored-trial software suite | 199 passed | Clean source `d17f6fa` |
| Stopping-feedback software suite | 14 passed | Clean source `d17f6fa` |
| Test inventory | 2,326 collected | Generated on clean source `a2041af`; collection is not execution |
| Fresh tracked-files-only clone | Passed | Clean source `b0e6e03`; 3,568 tracked files; smoke and evidence checks |
| Artifact-backed claim verification in the clone | 92/92 reproduced | Source `b0e6e03`; no claim-table rows changed |
| Frozen-score metric verification in the clone | 25/25 reproduced | Source `b0e6e03`; original score artifacts retained |
| Activation replay | Skipped | Extraction caches are not part of this CPU release check |

The [local clone receipt](../results/final_release_20261105.json) records the
exact source, environment, steps and output tails. Its invocation used
`--no-tests`: it does **not** claim a completed local full-suite run. The earlier
canonical [full clone-gate receipt](../results/clean_clone.json) is preserved for
its original source rather than overwritten by a narrower check.

The full core suite is enforced separately by [Core CI](https://github.com/Aditya26189/Warrant/actions/workflows/ci.yml)
on the published commit, alongside minimal-dependency customer jobs and the
Windows/Python 3.10 installed-package job. The [research workflow](https://github.com/Aditya26189/Warrant/actions/workflows/research.yml)
checks the three retained study suites separately. Consult the runs for the
exact commit: this local receipt does not substitute a collection count or an
older CI result for execution on the release.

The real fresh-clone acceptance test also exposed a Windows path-length
failure in the retained grader fixtures. Decision 241 records the repair:
set core.longpaths in each new clone before checkout, and show that option in
the PowerShell quickstart. This preserves the original evidence layout and
does not require changing a user's global Git configuration.

The report-discovery guard initially rejected the two retained unscored-trial
reports and this release report because it recognized only numbered and grader
series. Its supported-series discovery now includes these dated names and
checks their minimum content size. An unsupported prefix or undated draft still
fails the guard. The first long verification attempts were interrupted after
this focused failure was reproduced; they are not counted as passing runs.

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
