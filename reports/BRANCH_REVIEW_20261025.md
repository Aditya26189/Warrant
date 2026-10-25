# Branch review and experimental integration ? 25 October 2026

The user explicitly authorized review of all branches and merging useful completed work, while continuing B1. This expands the earlier README-only publication authorization. No branch or tag was deleted or rewritten.

The initial refreshed inventory contained 164 local/remote refs: 154 were already ancestors of origin/main 27d2d97. Of the ten remaining refs, two name the same continuing research line. The machine-readable sibling report pins the inspected refs and merge source.

| Branch group | Disposition and evidence |
|---|---|
| docs/phase21-crosscheck; docs/phase22-report; docs/phase23-public-caveat; fix/grouped-boundary | All unique historical commits are patch-equivalent to changes already on main (`git cherry -v` reports minus). Leave branches intact; merging adds no missing implementation. |
| feat/chain-evidence-replay | Three substantive commits are patch-equivalent. Its remaining unique inventory commit records 2,085 tests at an old source; current generated inventory records 2,287. Preserve historical branch instead of replacing current inventory. |
| feat/release-evidence | A parallel-root draft preserved before prior integration, including an older coordination implementation, duplicated decision numbering and README deletions. Current coordination/intake/inventory mechanisms already exist and pass their current tests. Keep archival draft; do not reintroduce its older state. |
| test/open-findings-executable | Historical strict xfails describe R2 and R10 as open. Current grouped metric boundary and mixture-monitor tests cover their repaired behavior. Importing obsolete strict xfails would fail on unexpected passes and mislabel fixed issues. Preserve historical branch. |
| experiment/grader-poc-20261021 | MERGED with history at 95ac26b. Includes isolated experiment, original evidence, failed attempts, negative comparisons, replay guide and named-report collection repair. README conflict resolved to guide links now present. |
| research/fpr-stage-a-20261017 (local and origin) | Continuing A05 frame remains FRAME_BLOCKED. Push completed research checkpoints to its research branch; do not merge an unfinished scientific frame into main or infer sampling/B2 approval. |

## Checks and practical limits

At merged source 95ac26b, 208 documentation/claim/report checks pass, 38 coordination/intake/inventory checks pass and all 55 grader unit tests pass. Ruff passes on experiment source. Rehashed all 1,315 packaged evidence payloads: 235 original, 57 hardening, 527 P2, 138 cancellation and 358 payments. Every changed blob is below 10 MB; largest is 1,684,177 bytes. No controlplane production source or B1 file is in the integration diff. The JSON receipt pins the checked sources.

The initial sandbox runs failed temporary-folder permissions; the normal-access reruns above passed. Git long-path checkout restored archived nested paths in the isolated integration worktree. A broad whitespace check reports preserved archived logs/CRLF evidence, which remain byte-identical rather than being reformatted. The documentation and executable-source changes pass their scoped checks. Smoke passed 7/7; its first invocation used a nonexistent module name, corrected to scripts/smoke.py. The smoke run after creating the untracked review receipt correctly disclosed dirty=True; no scientific experiment was generated from that state.

These are focused integration checks, not a rerun of the entire core suite, Docker/Harbor trials or remote CI. The archived trials are historical evidence. The experiment has not demonstrated an advantage over ordinary mutation testing/manual review and is outside the shipped CLI. Integration does not repair or close the separate adaptive-bound certification issue FPR-001.

A verified complete Git bundle of all local branches and tags was saved outside tracked files at `.venv/branch-safety-20261025.bundle` (193 refs at creation). This is a local backup, not an off-machine backup; pushed main and research histories provide GitHub copies of the newly completed scoped work. Existing untracked user uploads and other worktrees were untouched.
