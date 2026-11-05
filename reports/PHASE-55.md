# Phase 55 — Source-connected handbook and technical preprint

## Scope and baseline

The author requested an organized OSS manual, a scientific explanation of the
findings, investigation of the claims, a final notebook discussion and a LaTeX
preprint suitable for a later Zenodo deposit. The consolidated baseline is
`9dbdee03e77b698c497186b9b00297ee506cd0fe`. This phase uses a separate
worktree and preserves the desktop checkout's private untracked review material.

The author supplied **Aditya Singh, IIT KGP**, rendered as **IIT Kharagpur**.
The prepared manuscript/source license is CC BY 4.0; software remains MIT and
third-party materials retain their terms. No DOI, ORCID, degree, email, external
review, venue acceptance or institutional endorsement is invented. Publication
on Zenodo is outside this operation.

## Deliverables and organization

The handbook has tutorials, concepts, workflow and protocol guides, statistical
methods, architecture, parser-derived command reference, selected library API
reference, testing, reproduction, maintenance and limits. The docs index routes
new readers to it while retaining specialist manuals and historical material.
MkDocs navigation and a strict build provide a browsable form.

The research chapters explain data origins, construction and labels, the
retained findings and adverse outcomes, and interpretations that need more
evidence. A reviewed family registry and per-row ledger trace every README
quantitative claim to its selector, artifact hash, writer, source flags and
reproduction boundary. A qualitative register separately investigates capability,
readiness and prior-check statements.

The canonical preprint is LaTeX with a primary-source BibTeX bibliography.
Author and numeric macros are generated from declared records. Its build
copies only manuscript inputs into an isolated destination, retains compiler
logs and hashes, checks unresolved references/overfull text, and requires clean,
stable source. Visual inspection remains a separate check. The package command
exports tracked source through git archive, preserving evidence and attribution
while excluding ignored caches, private untracked material and history.

## Evidence ledger

| Investigation | Observation | Interpretation and limit |
| --- | --- | --- |
| README field audit | All 92 rows match values/intervals in 21 artifacts across 18 reviewed families. | Agreement with retained fields; not independent scientific validation. |
| Direct producing state | 15 rows reference dirty-source artifacts. | The complete producing source cannot be reconstructed from HEAD alone. A dirty flag does not identify the exact cause. |
| Separate point oracle | Rank/count calculation agrees on 25 frozen-score targets, directly backing 19 current README point claims. | Calculation independence only; not independent labels, interval coverage, controls or model replay. |
| Probe | Within-envelope ranking coexists with low operating recall. | AUROC and recall at a restrictive cut have different targets. |
| Context transfer | Mean/rolling pooling did not supply the expected robust rescue. | Candidate dilution/position/extreme explanations are hypotheses, not causal identification. Original answers/labels are reused. |
| Challenge measurements | Detector configuration affects retained PII results. | Authored/enriched cases and companion design limit transport and independence. |
| Assurance diagnostic | Preserved exact tied-score witness distinguishes budget control from a general adaptive returned-number claim. | FPR-001 remains open. This phase does not repair statistical issuance. |
| Closed studies | REPORT and STOP outcomes remain explicit. | A complete technical artifact does not establish a new publishable method. |

Initial and refined audit receipts are retained separately under
`results/documentation_audit/20261105/` and
`results/documentation_audit/20261105-final/`. The refined receipt records
clean producing source `c789c95`; consult its full SHA. Original result bytes
and the 92 numeric README table rows are unchanged.

## Implementation and verification record

The source-audit tests exercise tie-aware AUROC, undefined quantities, selectors,
evidence hashes, classification, source-stability guards, new-output protection
and repository-link resolution. Paper tests exercise macro drift, missing
citations, metadata escaping, dirty-source/existing-output refusal and a real
temporary-Git packaging example that excludes private files.

The isolated documentation environment initially exposed eager plotting imports
in `controlplane.report`. Decision 243 records the repair: retain established
public exports with lazy attributes so publication/audit imports do not load
plotting or model packages. No metric or threshold changed. A fresh-process
import test checks that dependency boundary.

The notebook builder appends one Markdown discussion cell. A JSON comparison
confirmed preservation of all 30 preceding main-notebook cells and metadata,
and the entire pilot notebook. Neither notebook contains executed outputs;
generation is not model execution.

Completed build, execution and PDF page-inspection results are recorded in the
closing verification section added after those operations. Collection inventory
counts are generated only from clean source and are not passing execution.

## What this does not establish

This phase does not establish independently correct labels, valid coverage for
all historical methods, a recovered historical model state, immutable model
weight identity, public availability of a private repository, new model
inference, production performance, commercial benefit or publication novelty.
Hash identity does not authenticate an author. Separately implemented arithmetic
does not become an external investigator.

## Open items

FPR-001 remains unresolved; historical dependent-row calculations and dirty
lineage retain their limitations. Original activation replay needs unavailable
or separately held caches and fuller model provenance. Independent blinded
label adjudication, external scientific review and operational validation remain
future evidence requirements. A Zenodo deposit needs the author's review and
publication action, including the accompanying source/evidence supplement.


## Closing local verification

- The isolated documentation/customer environment passed **119 focused tests**:
  audit, manuscript contracts, documentation indexing and case references.
  It has no plotting/model stack requirement for those commands.
- The existing notebook/index/case/report selection passed **217 tests**, with
  **33 deselected** and two reported SWIG deprecation warnings. The selection
  is not the full core suite.
- `python scripts/verify.py --no-activations` reproduced **92/92 claim rows**
  and **25/25 frozen-score blocks**. The activation tier was explicitly SKIPPED.
- A real fresh clone at `0d412cff6174` contained 3,624 tracked files and
  passed clone identity, smoke, claim replay and frozen-score replay. The
  gate used `--no-tests`; its new retained receipt does not claim a full-suite
  execution or activation replay.
- The strict MkDocs build passed. The repository link checker checked 24
  handbook/paper Markdown pages. The optional localhost browser preview was
  rejected by the browser approval gate because access was declined; no
  browser layout verification is claimed.
- Tectonic 0.17.0 built the final ten-page manuscript from clean source
  `5f01077e9f8bcd8c8b25e8851d3fdc8879289c13`. The first rejected layout
  attempt exposed an overfull source-hash line; subsequent commits fixed
  that line and float ordering. Final logs have no unresolved citations or
  overfull boxes above one point. A nonfatal font-configuration diagnostic and
  an underfull paragraph warning remain in the retained logs.
- Every final page was checked as a Poppler PNG. Nine final renders are
  byte-identical to already inspected build-03 images; the changed page 8 was
  inspected again after adding the source URL. The PDF hash, source inputs
  and page-render hashes are retained with the manuscript.
- The generated inventory records **2,364 collected tests**, produced from
  clean `b54daa344e72`. Collection is not execution.
- Full-tree Ruff checks passed. Frozen scientific result files and the original
  numeric claim-table rows were preserved byte-for-byte.

The full core release workflow is a separate check on the published main
revision; consult that revision's GitHub Actions status rather than treating
the local selections or prior baseline run as a new full-suite pass.
