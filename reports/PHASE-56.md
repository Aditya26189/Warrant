# Phase 56 — Repository closure review

## Question and answer

The author asked whether documentation and layout are complete enough to close,
and whether every branch is accounted for. At the reviewed baseline
`7d31bceb6506e6f769f81b8d0e5667f6d6d2ce74`, every fetched local/remote
branch tip was reachable from main. The shipped surfaces have an organized
guide set. The review nevertheless found concrete maintenance/documentation
defects and preserved local drafts that must not be called newly verified work.

This phase repairs the current guidance and generation/CI gaps, preserves
historical evidence and supplies a directory/ownership map. The justified
closure is a bounded technical repository and preprint artifact. It is not
independent scientific sign-off or a claim that every historical working tree
is clean.

## Review scope and evidence

The [operational inventory](audits/closure-20261105/inventory.json) records the
baseline, all fetched refs and redacted worktree states. The host audit read
Git state with optional index locks disabled; it did not reset, stash, prune,
delete, switch or stage another session's work. Private path details and binary
draft backups remain local.

The review inspected the root instructions, specialist contracts, handbook,
publication metadata/tooling, package/build layout, CI definitions, retained
release verification and original experiment boundaries. A local-link scan
covered 266 tracked Markdown pages across maintained root, docs, paper,
reports and examples, with no missing local targets/fragments at baseline.
It did not fetch every remote URL or certify the scientific accuracy of every
historical sentence.

The baseline release's completed verification remains at:
[core](https://github.com/Aditya26189/Warrant/actions/runs/41968359278),
[research](https://github.com/Aditya26189/Warrant/actions/runs/41968563830) and
[documentation](https://github.com/Aditya26189/Warrant/actions/runs/41968359259).
Those runs describe that exact baseline, not automatically a later maintenance
commit.

## Findings and dispositions

| Finding | Why it mattered | Disposition |
|---|---|---|
| Contributor instructions still said CI/versioning were not used. | A new contributor received a process description contradicted by the repository. | Describe the actual workflows and package metadata; preserve original competition context as historical. |
| Dirty-source guidance suggested a provenance-only replacement under a clean commit. | Equal values cannot reconstruct an unrecorded working tree, and frozen evidence must not be rewritten. | Preserve the original flag/artifact; an authorized clean rerun uses a new destination and disclosed source. |
| Python 3.11 and blanket 95% language conflicted with shipped contracts. | The customer minimum is 3.10; record protocols can withhold intervals or allocate a registered error rate differently. | Reconcile the instructions with implemented decisions and explicit uncertainty. |
| Command/API pages had no committed regeneration recipe or drift gate. | A changed parser/signature could leave a page labelled generated while stale. | Add a source declaration, four-page render/check modes, negative tests and CI enforcement. |
| Documentation PR triggers omitted some source/script inputs. | Documentation checks could be skipped when an actual input changed. | Align push/PR path coverage with the check's maintained inputs. |
| The original spec/phase plan mixed current extensions with endpoint notation and old goals. | Readers could infer a running HTTP service, live queue or completed optional phase. | Add current-scope notices and route to implemented workflows and product state. |
| Documentation and standalone research have uneven historical placement. | A directory listing alone does not explain user guides versus receipts/fixtures. | Add a [layout and source-ownership guide](../docs/handbook/repository-layout.md), preserving cited paths. |
| Some old worktrees retain source edits, deletion residue or untracked plans. | Merged branch heads do not include those working-tree bytes. | Inspect/classify them below; preserve them without treating them as new release work. |

## Documentation coverage

| Surface | Current entry point | Assessment |
|---|---|---|
| First run and supported input | [Quickstart](../docs/handbook/quickstart.md), [input](../docs/INPUT.md) | Covered, with successful/refused synthetic examples and replay |
| Prepare, certify, frontier, recheck, chain and handoff | [Workflows](../docs/handbook/workflows.md), [CLI](../docs/handbook/cli-reference.md) | Covered; required user inputs and protocol distinctions remain explicit |
| Registered release and label review | [Release](../docs/RELEASE.md), [protocols](../docs/handbook/records-and-protocols.md) | Covered as a separate fixed-threshold workflow |
| Architecture and maintenance interfaces | [Architecture](../docs/handbook/architecture.md), [API](../docs/handbook/api-reference.md) | Covered; the selected API catalog is not a stability promise for every internal symbol |
| Statistical methods and scientific results | [Methods](../docs/handbook/methods.md), [findings](../docs/handbook/findings.md) | Covered with estimands, assumptions, adverse results and mechanistic hypotheses distinguished |
| Data origins and every numerical README claim | [Data](../docs/handbook/data-sources.md), [ledger](../docs/handbook/claims.md), [qualitative register](../docs/handbook/qualitative-claims.md) | Covered within declared audit scope, not independent label adjudication |
| Tests and CPU/GPU reproduction levels | [Testing](../docs/handbook/testing.md), [reproduction](../docs/handbook/reproduction.md) | Covered; skipped activation replay and missing historical inputs remain visible |
| Contribution and generation | [Maintainer guide](../docs/handbook/developer-guide.md), [rules](../docs/CONTRIBUTING.md) | Reconciled and given executable reference-generation checks |
| Manuscript and deposit preparation | [Paper guide](../paper/README.md) | Existing reviewed manuscript/source/license retained; no upload or peer review claimed |
| Current versus historical structure | [Repository map](../docs/handbook/repository-layout.md), [docs index](../docs/README.md) | Covered without a risky archive migration |

This is completeness of the supported reading/maintenance paths. It is not
proof that all historical aspirations shipped or that another researcher has
reviewed every source claim.

## Branch and worktree accounting

The baseline snapshot contains **133 local branches and 47 remote refs**.
All **180** tips are ancestors of the baseline main. This includes the new
review branch before its first review commit. The exact refs and full SHAs
are retained in the inventory, rather than inferred from branch names.

The **95** registered worktrees split into:
**49 clean**, **20 with working material**, and **26 missing/nonfunctional
registrations**. This is host operational state, not a project-quality score.

| Working material | Observation | Closure interpretation |
|---|---|---|
| Shared desktop main | No tracked changes; seven original untracked private paths | Preserved and excluded from the release |
| Fourteen old temporary checkouts | Their tracked differences consist entirely of unstaged deletions; no added/modified source or untracked work | Partial checkout/cleanup residue; original committed bytes are already in history |
| Customer-evidence worktree | 33 tracked changed/added paths | Historical staged/unstaged drafts, compared with the later integrated implementation; not substituted for it |
| Grouped-agreement worktree | Five modified source files | Earlier implementation approach; current code has the later group-aware/withheld-interval contract |
| Chain-integrity worktree | One untracked regression module using earlier fixture/schema expectations | Preserved historical test draft; current chain tests and later integrity/publication implementations are the release evidence |
| Shared-context worktree | One untracked dated handoff instruction | Local historical instructions, not a current implementation backlog |
| Unscored-plan worktree | Two untracked planning Markdown files beneath one directory | Earlier plan/prompt versions; published successors and the completed REPORT track are retained |
| Missing registrations | No functioning checkout at the registered location | No working bytes can be audited there; committed heads remain preserved |

The [draft comparison record](audits/closure-20261105/drafts.json) lists every
changed path in the two substantive source worktrees. Every draft production
module exists in current main. The label-error module, its thin script and
two companion test modules match current bytes exactly. Other common symbols
have later changes. Matching names or ASTs alone is not a semantic proof;
the source review also traced the relevant current contracts and tests.

The old grouped helper `_descriptive_agreement` is replaced by the current
group-aware `cohens_kappa`/second-review path with withheld population
intervals. See [grouped agreement tests](../tests/test_grouped_agreement.py)
and [whole-group recheck sensitivity](../tests/test_recheck_label_sensitivity.py).
The customer-evidence draft's alternate decision-archive tests assume a JSON
manifest/whole-wrapper format that is not the current preserved Markdown
archive. Main already checks archived entry hashes, headings, parallel
citations and suffixes in [decision integrity tests](../tests/test_decisions_integrity.py).
Blindly copying that draft would add incompatible assumptions rather than
recover a missing customer feature.

Branch integration is therefore accounted for. Historical per-head tests were
not rerun for every branch, and private/uncommitted drafts are not claimed as
validated release candidates. Current integrated execution is a separate CI
gate. No branch, worktree, draft, private archive or closed study was deleted.

## Structure assessment

The implementation/test/evidence/publication split is useful. Keep it. The
main compromises are research receipts under `docs/research/` and the standalone
stopping-feedback study at the root. Both have stable consumers and historical
citations. A future relocation would require an explicit migration map and
compatibility verification; closeout is not a reason to perform it.

Ignored environments, competition PDFs and private folders visible on the
desktop do not describe the tracked repository. The published layout should be
assessed with Git's tracked tree, not a raw desktop-folder listing.

## Verification ledger

New maintenance checks exercise real reference consistency, parser drift,
missing/stale distinction and exclusion of private root material from the
specialist link scan. The initial focused implementation pass completed
**28 documentation-audit tests**. Closing checks are recorded after the final
guide/report changes, with collection distinct from passing execution.

Reproduction commands:

```shell
python scripts/audit_documentation.py --check-generated --links-all
python -m mkdocs build --strict --site-dir ../warrant-handbook-site
python -m pytest tests/test_documentation_audit.py tests/test_docs_index.py tests/test_cases_matrix.py tests/test_reports.py -q
python scripts/verify.py --no-activations
git for-each-ref --no-merged main --format='%(refname:short)' refs/heads refs/remotes
```

## What this does not establish

This is not an exhaustive security audit, external literature/novelty review,
independent human scientific review, production validation or authentication
of source truth. A passing link scan does not fetch remote pages. A generated
reference can accurately describe a method whose statistical interpretation
still needs review. The audit does not reconstruct missing checkout directories,
private source states, unavailable activations or original model weights.

## Open items

FPR-001 remains open, alongside historical dirty-source/model identity gaps,
unvalidated grouped-method interpretations, the documented Linux native-policy
expected failure, external label validity and production/customer evidence.
These do not disappear when branches are merged. Their evidence and closure
conditions remain in [limitations](../docs/handbook/limitations.md).

Optional future housekeeping includes removing stale local registrations or
retiring already-merged branch names after owner review. It is not required
to expose the current source, and this phase does not destroy working material.
Zenodo publication and independent scientific sign-off remain separate actions.


## Closing local results

The updated audit/ref, paper, docs-index, case-matrix and phase-report selection
passed **251 tests** in the isolated documentation environment. The strict
MkDocs build passed. The new reference check matched all four declared pages,
and the broader link scan checked **268 Markdown pages** successfully.
The legacy two-page rendering mode was exercised against the same declaration
and left the generated references current. Full-tree Ruff checks passed.

The preprint directory has no changes relative to the reviewed baseline.
Existing frozen scientific result files, datasets, model scores and the
notebook content remain unchanged. New records are the explicit operational
review snapshots, not replacement scientific measurements.

The closing collection inventory and clean-clone checks use committed source.
As in Phase 55, full release CI is assessed on its published source revision;
the baseline's pass and this focused selection are not substitutes for that
later result. The final response identifies the actual completed release checks.


The clean-clone gate passed at `3894dc2049cf0b2f44e3fe6f8a7b70911290784e`:
3,630 tracked files, smoke success, 92/92 claim rows and 25/25 frozen-score
blocks reproduced. It used `--no-tests` and explicitly skipped activation
replay. The [new receipt](audits/closure-20261105/clean-clone.json) retains
that clean producing source; it does not claim a full-suite run.

The refreshed [collection inventory](../results/test_inventory.json) records
2,370 tests collected from clean `12a22fc7b71f63a1d0ef399c3091bb1e808ac2f6`.
Collection remains separate from completed execution.


## Late semantic finding before the final gate

The last prose pass found an old statement in the contributor context and
agreement module docstring claiming that kappa 0.5 necessarily makes a recall
interval meaningless and that reviewer uncertainty is then necessarily larger.
That does not follow from kappa. Agreement between reviewers does not identify
accuracy against truth, nor does one kappa value yield a recall-error bound.

Decision 245 records the correction. Only the module docstring and contributor
wording changed; an AST comparison excluding the module docstring confirms that
all agreement calculations, bootstrap logic and interval-withholding behavior
are unchanged. The final published revision must receive its own release CI;
the earlier baseline runs do not stand in for that check.


## Full-gate failure and repair

The full CI run at `2b693296722304ae46a2044b7856cb581362bd8a`
([retained failed run](https://github.com/Aditya26189/Warrant/actions/runs/42000148400))
completed with **1 failed, 2,366 passed, 2 skipped, 1 expected failure and
4 warnings**. The single failure was
`test_the_registered_headline_matches_the_contract[inv4]`. The uncertainty
wording in `CLAUDE.md` had been corrected without updating the declarative
headline in `controlplane/report/invariants.py`. This was a review-introduced
documentation/register mismatch, not a failed statistical computation.

Decision 246 records the repair. The register now uses the corrected explicit
uncertainty headline, retains both original enforcing checks, and also names
existing sample-size/estimator and withheld-grouped-interval tests. The invariant
test itself is unchanged. Documentation CI now runs the invariant suite and
triggers on its source, so this contract mismatch is caught by the fast gate.

The expanded local selection passed **314 tests** after the repair, and
full-tree Ruff checks passed. A new full release run is required on the corrected
published revision; the failed run remains part of the evidence and is not
relabelled as a pass.
