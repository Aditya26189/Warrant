# Branch integration audit

This release consolidates the completed committed work into the main release
line. It preserves the prior Git history and scientific artifacts; it does not
rewrite experimental outcomes or reopen stopped studies.

## Integration decisions

| Branch | Retained tip | Disposition |
|---|---|---|
| research/tmlr-direction-20261027 | c12023b | Merged: exact assurance diagnostic, source inventory, and exploratory publication planning. Planning remains historical rather than a completed-paper claim. |
| research/unscored-trials-20261029 | b2b468d | Merged: completed technical report, portable inputs, numerical reproduction, source-accounting evidence, and pending human review. REPORT decision preserved. |
| research/agent-stopping-feedback-20261030 | 94b9e70 | Merged: bounded source-inspection code, safe summaries, failure history, and closed STOP decision. |
| All other pre-existing local and fetched remote tips | See inventory below | Already ancestors of the starting GitHub main; no redundant merges or reversions. |

The integration started from GitHub main b5e34e9. The shared desktop checkout
was on an earlier release branch, so the integration used a separate worktree.
Merge commits preserve each completed study's history.

## Local material preserved outside the release

Historical worktrees contain partial cleanups and uncommitted drafts. Their
working trees were inspected without resetting, stashing, or staging another
session's files. Tracked drafts in the customer-evidence and grouped-agreement
worktrees were backed up as local binary patches before consolidation. Their
older changes overlap subsequent integrated implementations; they are not
silently substituted for the later reviewed code.

Local review archives, manual metadata answers, mentor-share folders, private
research caches, and partial-worktree deletions are preserved locally. They are
not automatically public release inputs. The completed reviewed source and
reports remain discoverable through the [project overview](PROJECT-OVERVIEW.md).

## Verify the integration

After fetching the final main, run:

    git for-each-ref --no-merged main --format='%(refname:short)' refs/heads refs/remotes

An empty output establishes ancestry for the refs currently available in that
checkout. It does not account for unknown remote branches or unpublished local
working-tree edits. This audit is a snapshot of the refs fetched for this
release, not a claim about future branches.

The [final release report](../reports/PHASE-FINAL-RELEASE-20261105.md) records
execution checks separately from branch ancestry.

<details>
<summary>Audited branch tips</summary>

| Ref at audit time | Commit |
|---|---|
| archive/pre-rewrite-round1 | daaaa39031bf |
| chore/october-test-inventory | 1049b9741d70 |
| chore/october-test-inventory-v2 | eb68d67450d3 |
| docs/clean-clone-three-outcomes | cfe123f7caee |
| docs/evidence-handoff | d8834e64c410 |
| docs/first-run-observation | c77716591c1b |
| docs/october-03-market-refresh | 1d6c6236db3c |
| docs/october-04-mentor-checkpoint | 12eeca582f60 |
| docs/october-compatibility-checkpoint | 962f15633305 |
| docs/october-handoff-audit | 1707510b8aae |
| docs/october-mentor-ask | 7d8199b6ee4d |
| docs/october-research-addendum | de42f8994670 |
| docs/phase21-crosscheck | b66a700d6e7d |
| docs/phase22-report | 5d5ec75ed69d |
| docs/phase23-public-caveat | ffdc9641f785 |
| docs/phase24-report | 69f0981f8ea5 |
| docs/phase25-report | 12b5e24d4491 |
| docs/phase26-report | d763a6801aab |
| docs/pilot-protocol | 8614b35f906e |
| docs/pilot-protocol-phase46 | 1ec7c94de3fe |
| docs/prepare-ci-comment | 40efbeea9bea |
| docs/prepare-downstream-boundary | 30a1ea87240d |
| docs/prepare-overflow-checkpoint | deaa24ad8fc0 |
| docs/product-state-2026-09-28 | 9b5163f50637 |
| docs/product-state-phase43 | ca938ebaeec0 |
| docs/professional-pass | b5ed07e4af5e |
| docs/readme-main-20261025 | 6629d513620e |
| docs/redact-unit-caveat | 39dc552d501b |
| docs/strategy-primary-audit | 6ff6b5220a4f |
| docs/unscored-handoff-publish-20261029 | ef6e0fcb9703 |
| docs/unscored-research-plan-20261028 | c2e61a76b979 |
| docs/week-one-handoff-gate | 9ae424358eb7 |
| exp/branch-a | 13e0092b5538 |
| exp/chain-detection | ba8020da6816 |
| exp/frontier-selection | 5402b178c1c2 |
| exp/last-token | 6d4fa1139934 |
| exp/october-03-clean-clone | f8ca4f004314 |
| exp/phase25-clean-clone | ba156339cf06 |
| exp/recheck-schedules | b8b0f00c3817 |
| exp/recheck-schedules-results | 948a9e80b32b |
| experiment/grader-baseline-20261026 | c9f10774ebe5 |
| experiment/grader-feasibility-20261026 | 5cd5b00fa289 |
| experiment/grader-poc-20261021 | a66cdcb7f0b3 |
| experiment/grader-transfer-20261027 | 9b928b4758b7 |
| feat/calibration-claim | e6bb0f28caae |
| feat/canary | 4e6324a658ed |
| feat/certify-evidence-binding | 7f4699fff766 |
| feat/certify-from-frontier | a2ac9712a6cc |
| feat/certify-handoff-20261007 | 31879f6acfcb |
| feat/chain-evidence-replay | fffc6f040cea |
| feat/chain-verify | 1677881ac94f |
| feat/customer-evidence-integration | 55528c7ccc16 |
| feat/customer-handoff-ci | c4ebb7be1c38 |
| feat/drift | 07ab7ac0dd3c |
| feat/drift-response | 9ce0710fb8e2 |
| feat/larger-test-split | 0b9a14084987 |
| feat/measured-beat4 | 839c9d01bdd9 |
| feat/policy | b0dc12d17f24 |
| feat/public-prepared-handoff | c51d9db4c430 |
| feat/rbi-crosswalk | f088c4cd054a |
| feat/recheck-batch-replay | 279aec47cc38 |
| feat/recheck-chain | da7e28ef5915 |
| feat/recheck-evidence-linkage | d97b31a92595 |
| feat/release-evidence | fc7686456ee7 |
| feat/release-label-evidence | 6ae6aa96f53f |
| feat/shared-context | 55528c7ccc16 |
| feat/warrant-stats | 5ad83873de3a |
| fix/chain-integrity | 18dfbae790ca |
| fix/chain-integrity-8a | 9b3b911d6d82 |
| fix/chain-integrity-policy | 80e45914a80c |
| fix/chain-publication | eb8becf6cd6f |
| fix/chunked-prefill | 56763d69c9a5 |
| fix/clone-failure-artifacts | f06b08005362 |
| fix/clone-inventory-preflight | b183a6f5f622 |
| fix/clone-tier-fail-closed | c56cd52d86c7 |
| fix/demo-evidence-caption | 2872a28ee7ad |
| fix/envelope-units-and-null-band | 4c1c9b3ac184 |
| fix/frontier-groups | f0d9f117163f |
| fix/grouped-agreement | 68dba7daf61c |
| fix/grouped-boundary | f4e1f33317e9 |
| fix/grouped-hard-negative | 95f4907c94d4 |
| fix/grouped-rate-boundary | 4ba3271a1ca6 |
| fix/grouped-recheck | 0c8ae399ae48 |
| fix/grouped-review-evidence | f26ac4213033 |
| fix/installed-customer-workflow | d981fdc22c39 |
| fix/longctx-logits | f5557ce0eb6b |
| fix/longctx-measured | 90075a60ead0 |
| fix/malformed-record-inputs | ee5ca18a7c11 |
| fix/october-doc-whitespace | e11338ebb891 |
| fix/phase51-clone-cleanup | 4932e1560fa9 |
| fix/phase53-clone-pytest-summary | 037cbbb9f524 |
| fix/plan-reads-the-record | 2cdaf3d5fb62 |
| fix/prepare-score-overflow | 6f0cbcdec0e2 |
| fix/prepare-source-snapshot | d50627edb719 |
| fix/prepared-malformed-evidence | 181dc1f39b97 |
| fix/recall-assurance | a1771e0fb706 |
| fix/recheck-power | 7ae68d3b5e98 |
| fix/recheck-revocation-priority | 290c5e0839fc |
| fix/reconcile-and-fork | 18e415ee2a6c |
| fix/routed-response-serialization | 60b32f5f74a6 |
| fix/verify-revalidation-fail-closed | 0fb7ccc9fc3d |
| gate/phase47-handoff-clone | 054c29a907d4 |
| gate/phase48-full-suite | 48a5cfe964c4 |
| gate/phase50-clean-clone | 27d621fa9028 |
| gate/week-one-20261007 | c8e527502ef3 |
| integration/all-completed-20261026 | c2e61a76b979 |
| integration/phase24 | 4aa36b0ea413 |
| integration/reviewed-branches-20261025 | dd4ee852d94f |
| integration/unscored-handoff-20261029 | b5e34e992414 |
| main | 02d1483d4180 |
| phase/30-export-preparation | c6f220f89a66 |
| phase/7.2-paired-comparison | 7fe1c90f4d03 |
| phase/7.3-selection-uncertainty | f9321996568d |
| phase/8-detectors | e40bfe484282 |
| release/readme-main-20261025 | 27d2d97016e0 |
| release/root-main | b7de189a6294 |
| research/agent-stopping-feedback-20261030 | 94b9e70ba8b1 |
| research/fpr-stage-a-20261017 | caa4dd8b4396 |
| research/october-6-competition | 870c388b37f9 |
| research/phase49-incumbent | 57cb8eac1457 |
| research/tmlr-direction-20261027 | c12023bae4f6 |
| research/unscored-trials-20261029 | b2b468dd03cd |
| review/project-2026-09-22 | a7940023191b |
| test/installed-grouped-refusal | d1ace6f092e2 |
| test/open-findings-executable | e3b0c5f91e4e |
| test/phase52-handoff-ci | 707bd84778be |
| test/phase54-python310 | d57bcf52e3e9 |
| test/preparation-marker-interruption | 58bd2fa7ec42 |
| test/prepare-customer-matrix | 18f407aff4b4 |
| test/prepared-refusal-demo | 22cae7e7c8b4 |
| origin/archive/pre-rewrite-round1 | daaaa39031bf |
| origin/docs/evidence-handoff | d8834e64c410 |
| origin/docs/pilot-protocol | 8614b35f906e |
| origin/docs/professional-pass | b5ed07e4af5e |
| origin/exp/branch-a | 13e0092b5538 |
| origin/exp/chain-detection | ba8020da6816 |
| origin/exp/frontier-selection | 5402b178c1c2 |
| origin/exp/last-token | 6d4fa1139934 |
| origin/exp/recheck-schedules | b8b0f00c3817 |
| origin/exp/recheck-schedules-results | 948a9e80b32b |
| origin/feat/calibration-claim | e6bb0f28caae |
| origin/feat/canary | 4e6324a658ed |
| origin/feat/certify-from-frontier | a2ac9712a6cc |
| origin/feat/certify-handoff-20261007 | 36e31e3a2d73 |
| origin/feat/chain-verify | 1677881ac94f |
| origin/feat/customer-evidence-integration | 55528c7ccc16 |
| origin/feat/drift | 07ab7ac0dd3c |
| origin/feat/drift-response | 9ce0710fb8e2 |
| origin/feat/larger-test-split | 0b9a14084987 |
| origin/feat/measured-beat4 | 839c9d01bdd9 |
| origin/feat/policy | b0dc12d17f24 |
| origin/feat/rbi-crosswalk | f088c4cd054a |
| origin/feat/recheck-chain | da7e28ef5915 |
| origin/feat/release-evidence | dfa43d7a00a5 |
| origin/feat/shared-context | 55528c7ccc16 |
| origin/feat/warrant-stats | 5ad83873de3a |
| origin/fix/chain-integrity | 18dfbae790ca |
| origin/fix/chain-integrity-8a | 9b3b911d6d82 |
| origin/fix/chunked-prefill | 56763d69c9a5 |
| origin/fix/envelope-units-and-null-band | 4c1c9b3ac184 |
| origin/fix/frontier-groups | f0d9f117163f |
| origin/fix/grouped-agreement | 68dba7daf61c |
| origin/fix/grouped-recheck | 0c8ae399ae48 |
| origin/fix/longctx-logits | f5557ce0eb6b |
| origin/fix/longctx-measured | 90075a60ead0 |
| origin/fix/plan-reads-the-record | 2cdaf3d5fb62 |
| origin/fix/recall-assurance | a1771e0fb706 |
| origin/fix/recheck-power | 7ae68d3b5e98 |
| origin/fix/reconcile-and-fork | 18e415ee2a6c |
| origin/gate/phase48-full-suite | 448329445f66 |
| origin/main | b5e34e992414 |
| origin/phase/7.2-paired-comparison | 7fe1c90f4d03 |
| origin/phase/7.3-selection-uncertainty | f9321996568d |
| origin/phase/8-detectors | e40bfe484282 |
| origin/research/fpr-stage-a-20261017 | caa4dd8b4396 |
| origin/research/unscored-trials-20261029 | b2b468dd03cd |

</details>
