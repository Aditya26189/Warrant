# Grader-audit documentation and main publication — 25 October 2026

This closing phase brings the repository entry points up to date with the retained experimental grader work. The user explicitly requested an updated README and a push to GitHub main. The existing remote base was `b7de189a62943b18d512b58df606621270b06c6b`, an ancestor of the experiment branch. Publication preserves the experiment history and evidence; it does not integrate the audit into the installed Warrant command.

## Scope and reader entry points

The [root README](../README.md) now introduces the optional audit of graders that produce evaluation labels, links the latest [payments end-to-end result](PHASE-GRADER-PAYMENTS-E2E.md), and states the unproven comparison with ordinary testing. The [experiment README](../experiments/grader_poc/README.md) provides current status, historical evidence links and payments replay commands. The [product-state map](../docs/PRODUCT-STATE.md) distinguishes this experiment from the shipped certification workflow and corrects its historical full-suite reference from Phase 50 to Phase 53.

The underlying result remains bounded: the original payments grader accepts a worker with the wrong zero-balance predicate; appended checks reject it while accepting the supplied reference and equivalent implementation. The report retains the invalid initial harness attempt. Real Kafka/HTTP observations strengthen reachability evidence, while finite observation, narrow correct controls and untested concurrency schedules limit the claim. No new Harbor trial or scientific result was generated for this publication.

## Validation ledger

The first documentation source was `a4479e250d5b9903609fb676b23abda6950d0657`. On that clean source, the normal Windows research environment passed smoke (7/7), claim-table verification (92/92), frozen-score verification (25/25), and the existing estimator coverage test. Activation re-derivation was explicitly skipped with `--no-activations`. The documented Linux/WSL environment passed all 55 grader unit tests, including the P2 and payments modules. Ruff passed for the experiment source, excluding preserved evidence. No full core-suite execution is claimed here.

All 1,315 packaged payload hashes were recomputed successfully: 235 original results, 57 hardening, 527 P2, 138 cancellation and 358 payments payloads. These evidence directories are unchanged from `45397e7`. A local link check resolved 171 relative links across the three documentation entry points. A limited heuristic scan of 741 new history blobs found none of its token/private-key/home-name patterns; this is not a comprehensive secret audit. The largest scanned blob was 1,684,177 bytes. The longest relative tracked path was 222 characters and fits a typical GitHub Windows runner checkout; longer local roots still require the documented Git long-path setting.

## Failed checks and collection repair

Initial validation used an incomplete local virtual environment and encountered missing research imports. A sandboxed unit run also failed temporary-directory access. Those attempts are not passes. Smoke and unit validation were rerun with the installed research dependencies and supported WSL setup.

The documentation run then passed 87 tests but failed its count assertion. A separately retained collection diagnostic exposed the cause: `tests/test_reports.py` tried to extract a number from every `PHASE-*.md` filename, so preserved `PHASE-GRADER-*` reports aborted collection. Its partial count of 2,167 was not a valid inventory and was not written to the README.

[Decision G017](../experiments/grader_poc/DECISIONS.md) records the bounded repair before implementation. Numbered report discovery now explicitly identifies the numbered series, retaining its existing continuity and required-section checks. Named grader reports receive the existing non-stub check. An additional namespace check rejects unrecognized phase filenames, and a regression covers numerical sorting in the presence of a named report. Historical reports and scientific payloads remain unchanged. The existing inventory generator is the authority for updating README/Makefile counts after clean successful collection; collection is distinct from execution.

## Final local publication gate

The clean inventory source was `4b4cab88ef253523c3aef1cefa7556a6921cc4b2`. The existing generator successfully collected **2,287 tests**, updating the previous 2,279 claim: six named-report non-stub cases and two discovery checks were added. The [generated inventory](../results/test_inventory.json) records its source, command and collection hash. No core test was deleted, and the grader unit modules remain separate from this core collection.

On clean `39af2b885f13`, the combined documentation, claim, numerical-prose and report checks executed **208 tests, all passing**. The exact command was `python -m pytest -q -o addopts=--strict-markers tests/test_docs_index.py tests/test_claims.py tests/test_readme_prose_numbers.py tests/test_reports.py`. Smoke again passed **7/7** and reported `dirty=False`. The experiment guide includes the explicit P2 unit module as well as the payments module. A final link/scope check resolved **177 relative links**, confirmed the publication's declared file scope, and found the historical evidence packets unchanged. Subsequent edits to this closing report record these results; they do not claim that the earlier test command ran against its own future report commit.

## What this does not establish; open items

These publication checks do not establish production integration, customer demand, methodological novelty, independent human replication, or an advantage over manual assertion review and mutation testing. Those limits and the negative P2 comparison remain linked from the README. No upstream benchmark patch has been submitted. Core certification, statistical code and parallel B1 work are outside this phase.

Full Harbor trials are retained historical evidence, not rerun by this documentation gate. Activation-cache reproduction is skipped, and the prior full-suite record names its own source commit. GitHub Actions must be inspected for the exact eventual main commit; a workflow file, a local focused pass or a test collection count does not establish remote CI success. Publication uses an ordinary non-force main update, preserving any newer remote history rather than replacing it.

## Publication boundary after approval review

Automatic approval review rejected publishing the full experimental branch because the user's explicit GitHub request covers the README, not the additional code/evidence/report payload. The rejected compound command did not run. This gate report and the experiment remain local. A separate branch based on remote main will publish only the README, preserve main's existing collection count, and label the latest experimental results as local. The earlier validation ledger remains a record of the local experimental tree, not validation of a published experimental package. No experimental branch or evidence packet is exported by that narrower push.

## Verified README-only publication

GitHub main was updated with a non-force push to `27d2d97016e0b0610c3a73c27dae869b636012a4`. Its entire diff from the previous remote main is **README.md only**. The published README identifies the new grader track and recorded payments result as local experimental work; it does not link to unavailable evidence and retains the existing published test inventory. The separately validated README source was `6629d51`; all 88 documentation, claim and numerical-prose tests passed. The merge tree matched that source exactly. A fresh remote lookup/fetch confirmed main's hash and README bytes. Remote GitHub Actions status was not checked.

The full experimental history remains on the local `experiment/grader-poc-20261021` branch. This worktree was returned to that branch after verification. The published README-only branch does not contain the experiment, its evidence, the collection integration fix, or this local report. The separate production checkout and other agents' work were preserved.
