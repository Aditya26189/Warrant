# Phase 57 - Manuscript clarification and revision

## Question and answer

Can the requested preprint corrections be made without expanding the retained
evidence or replacing its history? Yes. Version 1.0.1 clarifies the finite
counterexample and the native replay boundary, removes the requested wording,
and preserves the original scientific results and version-1.0 tag. The reported
C031 closing bracket was already present in both the source and rendered PDF.

## Work completed

1. Inspected the original Table 2, its generated C031 interval and its rendered
   page. The existing value remains `[0.5105, 0.6015]`; no result was changed.
2. Added the three one-sided Clopper-Pearson endpoints immediately before the
   selection-event explanation. The publication helper inverts the binomial
   CDF by bisection using the retained witness parameters. An independent
   SciPy beta-quantile comparison checks the endpoints and the displayed
   precision needed to preserve both strict inequalities.
3. Checked exact artifact selectors, rather than inferring claim coverage from
   a file-level target. Section 6.1 now explicitly names the limitation.
4. Removed the two requested assistance/sign-off sentences. The internal
   arithmetic-oracle distinction and technical-preprint status remain accurate.
5. Updated author/version and prepared deposit metadata to 1.0.1. The author,
   affiliation, license, original measurement values and bibliography identities
   are unchanged. The original preprint remains at `warrant-preprint-v1.0`.
6. Compiled from clean committed source, rendered and individually inspected
   all ten final pages. Literal command hyphens are preserved. Standard smaller
   bibliography text keeps the expanded explanation within ten readable pages.

## Findings and evidence

### Numerical intuition

The generated `paper/generated/claims.tex` now retains the approximations
`0.02951304961`, `0.04655981145` and `0.06161920040` for counts zero, one
and two. These are computed from `n` and `alpha` in the unchanged
[exact witness](../results/publication/assurance_semantics.json), not copied
from the review. The review approximation for the count-one endpoint was
inaccurate; the corrected endpoint remains strictly below the retained q1.

Counts zero and one clear the requested budget while count two fails it.
The explanation states how a selected threshold returns a bound below its
population tail risk in the two disjoint events. The original exact rational
noncoverage calculation, state count and zero requested-budget violations are
unchanged. The new endpoint inversion is explanatory code, not a repair to
production threshold selection or a new statistical guarantee.

### Dirty-source coverage

The [audit receipt](../results/documentation_audit/20261105-final/audit.json)
identifies fifteen directly dirty-source rows. Their native replay scope is:

| Claim fields | Artifact | Direct frozen-score target for those fields |
| --- | --- | --- |
| C006-C007 | `results/reconciliation.json` | None |
| C016-C018 | `results/fpr_sweep_oos/sweep.json`, selected sweep point | None |
| C019 | Same artifact, `out_of_sample` flag | None |
| C020-C028 | `results/policy-triviaqa-2400-t960.json` | None |

The [validation-split score set](../results/scores/valsplit-T1-last_token.json)
does target the sweep artifact, but specifically `certifying_split_metrics`.
That object is distinct from `sweeps[...].points[...]`. Replaying the former
cannot be described as recomputing the latter. The native verifier also has
no target for the reconciliation or resplit-policy artifact. A coincidentally
equal point estimate in a different artifact does not identify the original
computation. This is a coverage limitation; it does not itself demonstrate
that any of those numbers is wrong or impossible to reconstruct by other work.

All table fields still match their artifacts, and the existing frozen-score
target blocks still replay. The manuscript distinguishes those checks rather
than claiming the fifteen fields gained score-replay coverage in this phase.

### Typesetting and guard outcomes

The final [build receipt](../paper/build-receipt.json) binds source
`02f29c8aa585dba4829203c941f0c127abc8f72a` to the retained PDF and all
LaTeX/BibTeX inputs. [Visual QA](../paper/visual-review.json) records hashes
for all final page renders and the checks performed.

The first correction build was valid but extended the references to eleven
pages. A layout follow-up exposed a long unbreakable inline command; the
overfull-box guard rejected build 02. Rephrasing that paragraph fixed the
overflow. Build 03 passes unresolved-reference and overfull-box checks.
The compiler still emits nonfatal fontconfig/underfull-paragraph/BibTeX warnings
recorded in the build logs; successful compilation is not a zero-warning claim.

An early clean-clone attempt completed smoke and numerical checks but refused
to write a provenance receipt because this checkout advanced during layout work.
That refusal is retained as an operational finding, not counted as a completed
provenance-bearing gate. Final clean-clone acceptance must use stable source.

## Verification

The final focused publication/audit/docs/invariant/report/decision selection
and the exact assurance-semantic checks completed with 329 passes. Source generation and bibliography checks, strict
handbook compilation, all four generated reference pages, maintained Markdown
links, and Ruff checks passed. The native verifier completed claim-table and
frozen-score tiers; activation replay was explicitly skipped.

The updated collection receipt is generated only after this report is committed.
It describes collection, not executed passes. Exact full-suite outcomes belong
to the completed CI jobs for the published main commit; see the repository
[Actions history](https://github.com/Aditya26189/Warrant/actions). Release
packaging does not turn pending jobs or historical passes into current passes.

## What this does not establish

This revision does not establish external peer review, independent label truth,
valid adaptive returned-bound coverage, reconstructed dirty source states,
fresh model extraction, additional detector performance or production utility.
No statistical implementation, frozen score vector, eval set or original
scientific artifact was changed. The QA collection inventory is separate.

## Open items

FPR-001 and historical inference/source limitations retain their existing status.
Closing those requires the separately scoped analysis or original evidence
identified in the research records, not further editorial changes. Zenodo
publication and DOI assignment remain author actions. The local package is
prepared without uploading, publishing or changing repository visibility.

## Reproduction ledger

- Decision: [247](../DECISIONS.md).
- Source: [publication helper](../controlplane/report/technical_paper.py),
  [independent endpoint check](../tests/test_technical_paper.py),
  [manuscript](../paper/warrant.tex) and its included sections.
- Artifact records: [build receipt](../paper/build-receipt.json),
  [visual QA](../paper/visual-review.json), [guide](../paper/README.md).
- Preserve original result bytes and the immutable original preprint tag.

```sh
python paper/build.py --generate --check
python -m pytest tests/test_technical_paper.py tests/test_documentation_audit.py tests/test_invariants.py tests/test_docs_index.py tests/test_cases_matrix.py -o addopts=--strict-markers -q
python scripts/audit_documentation.py --check-generated --links-all
python -m mkdocs build --strict --site-dir ../handbook-revision
python -m ruff check controlplane/report/technical_paper.py tests/test_technical_paper.py
python scripts/verify.py --no-activations
python scripts/clean_clone_gate.py --no-tests --out ../clean-clone-revision.json
python paper/build.py --engine /absolute/path/to/tectonic --out ../new-build
python paper/build.py --package-out ../new-zenodo-package
```

Build, clone-receipt generation and packaging require clean, unchanged source
and new output destinations. The standalone LaTeX ZIP retains generated macros;
reproducing those macros requires the accompanying tracked source/evidence.
