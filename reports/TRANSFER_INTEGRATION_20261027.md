# Reviewed integration - 27 October 2026

Completed grader-transfer work and the validated B1 continuation are integrated
under the user's explicit instruction to merge completed work and push main.
The tracks retain separate scientific conclusions and authorization gates.

Starting GitHub main: `69eac49cf862ef744dd00ccb8c76de2cbfdbdba8`.
Clean code/evidence integration checkpoint:
`0428ced0a2a6700532082dfddb28e9ed4cc3f41a`.
This report is a subsequent documentation commit; the final publication hash
and clean smoke result are reported separately.

## Reviewed and included work

| Work | Completed source | Integration |
|---|---|---|
| Bounded grader transfer, frozen methods and evidence | `6c27cea83fc8a67ef53fe0cb46c87e1ca327dabd` | `8dff3f345bfb93beb4170e7397c518968fdfca10` |
| Closeout documentation, G025 failure record and WSL Git repair | `9b928b4758b7ba043869f3c6aff95e2270b94701` | `66e1e4e1cfa54e50da3a1d1b4f795b69c0988403` |
| Remaining stale README execution-gate prose | Integrated source above | `fa0f991` |
| Validated B1 checkpoint014 and current status | `caa4dd8b4396831a0b13d628f571c3b040274b46` | `0428ced0a2a6700532082dfddb28e9ed4cc3f41a` |

The transfer review covered the protocol/decision changes, prompt-first
properties, alternatives, preparation, execution, packaging, tests and closing
report. The closeout review covered its portable instructions, retained failure,
Git selection code and regressions. No evidence of a production certification
change or benchmark-method change was found in these completed commits.

The mixed-filesystem repair selects native Git for Linux clones/POSIX worktrees
and Windows Git only for a Windows-absolute gitdir pointer under WSL. It handles
nested working directories and propagates Git failures. No ownership override,
global configuration edit or trust bypass was introduced. This helper is in the
isolated experiment, outside production certification.

At the integration checkpoint all **124 local branch tips** and **45 fetched
origin refs** are ancestors of HEAD. Historical branches remain present; no
branch or other session's worktree/draft was deleted or reset. GitHub main was
fetched before publication and still named the starting commit above. Publication
uses normal non-force pushes.

## Scientific findings retained

The [closing grader study](GATE4-TRANSFER.md) is a valid bounded negative result.
The frozen method produced 37 mutants on the three reserved tasks; all were
rejected by the full existing grader, and all nine control trials passed. Two
mutants passed base tests but failed existing plus tests. No full survivor
reached mutant witness search and no new omission, repair or upstream submission
resulted. Together with calibration, the fixed method produced no new omission
from 50 mutants. These figures come from the committed derived packet and its
reproduced verifier, not newly run benchmark experiments in this integration.

The study does not establish discovery advantage, grader-defect prevalence,
human effort savings, product demand or publication novelty. Control diversity,
partial specification/abstention and full-worker timing limits remain disclosed.
The reserved tasks are now exposed and evaluated; they are not fresh holdouts
for a tuned follow-up. Retain the experiment and its replay as evidence, and
retain the closing decision to stop custom discovery-engine development on this
result. It supplies no statistical assurance improvement to Warrant itself.

The [B1 continuation addendum](../docs/research/fpr_reporting/b1/a05-deep-evidence-20261024/CONTINUATION_ADDENDUM_20261027.md)
records checkpoint014: **27 pointwise supported pending frame approval,
39 excluded, 306 UNCLEAR**, preserving all 372 works and 389 source memberships.
Checked method evidence now covers 95 works. The judgments are disclosed
exposed-custodian work under adopted A05, not fresh independent final review.
No paper draw, human assignment, outcome-sheet access or B2 extraction occurred.

B1 remains **FRAME_BLOCKED**. Pending actual source/restriction work is already
authorized; no new reviewer-reset or general permission cycle is required. The
same three source roles each reached a service limit after real progress. Their
completed receipts were frozen without inventing completion of larger batches.
Unchecked drafts remain unavailable as scientific evidence. Complete-frame
approval and later sampling/B2 remain separate gates. The adaptive-bound issue
[FPR-001](../docs/research/fpr_reporting/issues/FPR-001-adaptive-bound.md) remains
open for independent statistical review; historical certificates are unchanged.

## Verification actually performed

| Check | Result and source |
|---|---|
| Final integrated experimental unit tests | **85 passed, one skipped**: 74 discovered tests with one POSIX-only Windows skip, plus 12 separate P2/payments boundary tests, on clean `66e1e4e` |
| Research regression checks | **66 passed** during this continuation: 35 final deeper-helper tests, 13 original A05, 10 custodian-repair and eight reviewer-return checks |
| Research checkpoint014 replay | Four payloads byte-identical; audit008 from clean `8fdd172`, generated source `65e52c6` |
| Frozen research preservation | Original 345 files byte-identical; integrated-artifact guard passed; research scope pinned to approved `2187f85` |
| Integration research identity | All **972 research Git blobs** identical to validated research source `caa4dd8` |
| Transfer offline package replay | All **203 payloads** byte-identical on `8dff3f3`, and again after the provenance repair on clean `fa0f991`; no benchmark workers run |
| Earlier calibration/baseline evidence | All **90 payloads** byte-identical to starting main, with original manifest hashes verified |
| Published claim/score verification | **92/92 claims**, **25/25 frozen-score comparisons** reproduced on clean `8dff3f3` |
| Activation re-derivation | **SKIPPED** because the ignored activation cache is absent |
| Smoke before final documentation | **7/7**, clean `8dff3f3`; final publication receives a separate clean smoke check |
| Ruff | Passed for the final research helpers and explicit integrated experimental source/test files |
| Documentation | New research links checked; CRLF-aware whitespace checks pass; historical copied raw source whitespace retained |
| Production and core-artifact diff | Empty against starting main for `controlplane/`, `config.yaml`, `pyproject.toml`, `requirements.txt`, `results/` and `tests/` |
| Introduced blob limit | Largest **3,314,873 bytes**, below 10 MB |

The complete 2,316-test core suite previously passed on `b0e1cb5`, as recorded
in [the earlier integration report](MAIN_INTEGRATION_20261026.md). It was not
repeated for these isolated experimental/research changes. No current remote-CI
pass is claimed.

The source closeout session separately reports a fresh pinned Linux replay with
46 matching control/mutant trials and 55 Linux tests. Its local validation ledger
was read during review; these are attributed same-assistant portability checks,
not an independent Linux scientific replication performed by this integrator.
The integrator's own reruns above use retained packets and no benchmark workers.

The B1 scope guard was run on the isolated research branch. On combined main,
research preservation is established by exact subtree identity to that validated
branch plus explicit combined-change scope. The research allowlist was not
weakened to admit unrelated grader changes. Private source caches are needed for
the full B1 replay; a cache-free fresh-clone reproduction is not claimed.

Research commits, hashes, remaining questions and the importer repair's actual
red/green regression are listed in the continuation addendum. Historical audit
receipts, protocols and scientific packets were not rewritten. A normal Git
merge/push preserves completed work; it does not establish scientific feasibility
or remove a research approval gate.
