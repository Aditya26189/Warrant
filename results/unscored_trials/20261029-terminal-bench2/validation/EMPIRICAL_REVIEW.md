# Adversarial review of first canonical analysis

Review date 29 October 2026. Assistant source/arithmetic cross-check, not human adjudication or independent replication. No repository edits, network fetches, upstream code execution, cohort changes or parameter retuning. Main analysis/replay remains the root's evidence.

Reviewed canonical-001 generated from source commit 92f162a8fee29f8f65bdd9293269e0bacb4d6411. Current analyze.py hash ed42fb3e8bf682b0501e0a3123e3e8c19b6f30d37f917a192f3388bd1387efcb matches recorded provenance. Verified indexed request-shard hashes, jobchecks shard and each successfully read raw job/trial payload used below against its source SHA. The advisory arithmetic is saved in empirical_review_evidence.json. No native normalization function was used for those direct raw sums: single numeric reward values were summed as Fractions; absent/null verifier rewards contributed zero only for the operational policy.

## Main assessment

The canonical labels 20 unresolved_mismatch and 8 unavailable are broad reconciliation statuses. They must not be described as 28 incorrect scores or 20 numerical mean errors.

Across all 28 jobs, this checking pass found:
- 19 have one supported published mean numerically matching the pooled zero-filled raw-record mean within the frozen 1e-12 tolerance.
- 3 differ between the whole raw population and the published mean.
- 6 lack a single supported published mean: custom result schema, empty metrics, or failed job-source access.

Whole-job arithmetic matching is only an explanatory diagnostic. It does not resolve group identity, indexes, task identity, exact harness version or eligibility. Preserve the frozen primary cohort and all canonical exclusions. An earlier message raising a possible WozCode source-availability flag contradiction was withdrawn: the exact hash-verified shard records false, correctly matching its failed job request.

## Exhaustive cause table for the 28 non-match jobs

Job paths below are suffixes of submissions/terminal-bench/2.0/. Full URLs, hashes, raw sums, counter fields and request paths are in the advisory JSON; canonical jobchecks contains full name-level discrepancy evidence.

| Submission/job | Canonical status | Direct raw arithmetic | Explanation and remaining qualification |
| --- | --- | --- | --- |
| 0error-Ledger__Claude-Opus-4.7 / tbench-2.1-k5-v01 | unresolved | 177/445 matches | Eval metric/index checks match; task identity is unsupported by current Git-path adapter and this is a 2.1-labelled variant. New global counters are 445 completed and 215 errored, consistent with raw records. Not a numerical mean defect. |
| BashAgent__TermiGen-32B / qwen_claude_5 | unresolved | 86/445 versus summary 72/445 | Raw and summary retain different names on 17 records, with different score/error counts. The summary itself has 445 unique indexed names, reward mass72 and internally coherent 72/445. Cross-artifact export/population disagreement; cause and retry history unknown. |
| Capy__Claude-Opus-4.6 / eval-terminal-bench-2-0-anthropic-claude-opus-4-6-ae1eef84-1773189792834 | unresolved | 68/89 versus summary 21/29 | Job summary names29 trials, while89 raw final records exist; common indexed records agree. Summary arithmetic21/29 is internally coherent. A partial/stale summary is plausible, but not adjudicated. |
| Crux__Claude-Opus-4.6 / submission-run | unavailable | raw272/445; no supported mean target | Custom top-level result, not Harbor stats/evals. It records445 trials,272 pass,134 fail,39 error, matching raw scored/null counts. pass_rate0.9663 is compatible with86 solved tasks/89, a different task-level success target. Do not compare this rate to272/445 as a scoring error. |
| Dirac__Gemini-3-Flash-Preview / 2026-04-18__15-04-03 | unavailable | raw58/89 | Published metrics list empty; indexes/counters otherwise align. Missing task identity also remains. No numeric target to reproduce. |
| JJAgent__Multiple / 2026-05-04__14-46-15 | unavailable | 77/89 matches published mean | Raw model label Multiple versus summary group multiple creates artificial separate groups in current exact-label adapter. Named-population arithmetic agrees; no automatic alias repair or cohort expansion authorized. |
| JJAgent__Multiple / 2026-05-05__18-36-48 | unavailable | 78/89 matches published mean | Same labelcase issue; new global completed/errored counters agree with445 records/9 exceptions. |
| MAYA__Claude-4.5-sonnet / 2025-11-13__09-25-32 | unresolved | 38/89 matches |3 null raw records indexed as reward0.0; declared scored counter89 versus86 observed. Exception count also differs13 versus3. |
| MAYA__Claude-4.5-sonnet / 2025-12-05__06-20-00 | unresolved | 38/89 matches |3 null raw records indexed as reward0.0; declared scored counter89 versus86 observed. |
| MAYA__Claude-4.5-sonnet / 2025-12-05__16-42-55 | unresolved | 38/89 matches |2 nulls indexed as0.0; name/directory differences and38 summary-only names remain. |
| MAYA__Claude-4.5-sonnet / 2025-12-06__16-31-45 | unresolved | 38/89 matches |5 nulls indexed as0.0; name/directory differences and38 summary-only names remain. |
| MAYA__Claude-4.5-sonnet / 2025-12-09__13-26-21 | unresolved | 38/89 matches |1 null indexed as0.0; name/directory differences and38 summary-only names remain. |
| MAYA__Claude-4.6-opus / 2026-02-27__16-48-59 | unresolved | 65/89 matches |1 null indexed as0.0; scored-count/index convention differs. |
| MAYA__Claude-4.6-opus / 2026-03-02__08-17-24 | unresolved | 66/89 matches |4 nulls indexed as0.0; scored-count/index convention differs. |
| MAYA__Claude-4.6-opus / 2026-03-04__07-44-02 | unresolved | 63/89 matches |3 nulls indexed as0.0; scored-count/index convention differs. |
| MAYA__Claude-4.6-opus / 2026-03-05__07-04-22 | unresolved | 61/89 matches |2 nulls indexed as0.0; scored-count/index convention differs. |
| MAYA__Claude-4.6-opus / 2026-03-09__08-44-46 | unresolved | 65/89 matches |1 null indexed as0.0; scored-count/index convention differs. |
| NexAU-AHE__gpt-5.5 / run-1 | unresolved | whole-job74/89 matches | Some raw records use source terminal-bench-2, while summary groups terminal-bench. Group partitions differ; one ghost name remains. |
| NexAU-AHE__gpt-5.5 / run-2 | unresolved | whole-job76/89 matches | Source/group partition differences, two ghost names and one raw-unindexed name. |
| NexAU-AHE__gpt-5.5 / run-3 | unresolved | whole-job151/178 matches | Source/group partition differences, three ghost names and one raw-unindexed name. |
| NexAU-AHE__gpt-5.5 / run-4 | unresolved | whole-job75/89 matches | Source/group partition differences, two ghost names and one raw-unindexed name. |
| WOZCODE__Claude-Opus-4-7 / 2026-04-19__20-07-00 | unresolved | 357/445 matches | Reward arithmetic aligns; exception-name/class/index evidence differs. Summary47 exceptions versus raw35, with36 summary-only exception names and24 record/index mismatch names. |
| Wecode__GPT-5.5 / wecode-tb2-4-30-5 | unresolved | 392/445 matches | Eval arithmetic/indexes match; task-name/path mismatch is the exclusion trigger. No numerical mean error demonstrated. |
| WozCode__Claude-Opus-4.6 / 2026-03-28__16-52-39 | unavailable | raw303/445 | Job-source HTTP retrieval failed after bounded attempts; raw trial records exist. No released job mean was recovered through that source. |
| grok-cli__grok-4.20-0309-reasoning / job-part1 | unresolved | 81/130 versus summary81/131 | One summary-only name video-processing__4AWyGxL already carries recorded reward0. Summary arithmetic81/131 is coherent; raw-file population130 differs. Job finished_at is null. This is not an unknown-reward slot or proof of an unexecuted planned trial. |
| logos-latest__claude-opus-4.7 / 2026-04-21 | unavailable | raw372/445 | Empty published metrics; indexes/counters align, task identity unsupported. |
| logos-ts__claude-opus-4.7 / 2026-04-19 | unavailable | raw4/5 | Empty published metrics; indexes/counters align, task identity unsupported. |
| logos__claude-opus-4.6 / 2026-04-09 | unavailable | raw59/89 | Empty published metrics; indexes/counters align, task identity unsupported. |

MAYA's zero-index representation can be legitimate operational null-to-zero serialization, an older/custom exporter, or postprocessing. January source alone is not an exact harness pin, especially for earlier dated jobs. Scored-status/index discordance remains a real released-artifact distinction, but it does not by itself invalidate the native operational mean or establish benchmark misconduct.

## Old versus new counter and grouping semantics

[January JobStats](https://github.com/harbor-framework/harbor/blob/1c0f38644b94c2a9a5fa4a8b77667d8175d0869e/src/harbor/models/job/result.py#L48) increments global n_trials for every returned final record; eval n_trials only for nonnull verifier/rewards, and errors independently.

[May JobStats](https://github.com/harbor-framework/harbor/blob/5a22a1dd4cc42fff8418bcb1e796ceb3624df931/src/harbor/models/job/result.py#L50) explicitly migrates old n_trials to n_completed_trials and old n_errors to n_errored_trials. Its increment method around line129 retains the same completed/scored/exception distinction. Completed does not mean error-free. A valid reward can coexist with an exception. Current normalizer retaining completed but ignoring the renamed global errored field makes legacy-style match flags partly vacuous for these fields; expose schema-specific counter availability rather than claim full counter verification.

January replaces slashes in eval labels; May preserves them. Neither inspected formatter lowercases model labels. JJAgent's case difference therefore supports a label/provenance discrepancy, not an asserted native casefold rule. NexAU's source-name difference likewise cannot be silently repaired from task names alone.

No summary counter or minimum trial requirement creates an exact original trial roster. May's aggregate retry counter still does not identify individual attempts or their parent lineage.

## Precise source anchors

All official results are pinned at https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/tree/572b2614be2c0cb2527e14f5b1e4026f1072e6c1 . Append each table job suffix beneath submissions/terminal-bench/2.0/ and result.json. The full immutable raw URLs and SHA256 are in empirical_review_evidence.json / each entry's job_request.

Representative job-file hashes:
- Bash: f5eb144577611e61fcecb544252bb09703a2ea4668a5381a452fabd61c791cd4
- Capy: bcff49b5b4524bb62289df729879be21451d22499af969b3d3a69658bda51207
- grok: 8254093a45d5cde08a78ddc8ec7673c42b1554b97536c6540a8cc6cd521e7bb7
- Crux: 980825ea42c9ad9d8eb46083d1b9e298ed336771c8eeab5b01a8a032bacf99be

Relevant JSON pointers: /stats/evals/<escaped-key>/metrics/0/mean; /stats/evals/<escaped-key>/reward_stats/reward; /stats/evals/<escaped-key>/exception_stats; /stats/n_trials or /stats/n_completed_trials; /stats/n_errors or /stats/n_errored_trials; /n_total_trials. Raw trial pointers: /verifier_result/rewards/reward, /exception_info/exception_type, /trial_name, /task_id, /config/job_id and /source. Crux custom pointers: /result/total_trials, /result/trial_pass_count, /result/trial_fail_count, /result/trial_error_count, /result/tasks_solved, /result/total_tasks, /result/pass_rate.

## Contribution and gate recommendation

The defensible addition beyond pinned honestboard is a reproducible, version-aware cross-artifact reconciliation: a summary can have correct arithmetic for its own named population while disagreeing with the exported raw population or reward/status indexes. Raw records recover distinctions that summary-only rank analysis cannot establish. Conversely, apparent defects often dissolve into a changed population, native zero semantics, unsupported grouping or a different metric target. Publishing this ledger, replay and negative controls is useful technical work.

The strongest objection to a TMLR upgrade is that honestboard already covers this release's broad rank/handling questions, preserves rewarded exceptions, pools task rates, stores pooled means and studies best-job sensitivity. Gao/Zhou already supplies the completion bounds. The current evidence does not show a corrected official ranking, empirical tighter bounds, selective retries, or a new weighting effect. Only three raw-versus-summary mean differences remain here, and all three published means are internally coherent for their own indexes. These facts support REPORT now; a GO would require a clearer distinct empirical lesson and convincing audience interest, not simply relabeling the known bounds or the broad20/8 status counts. Novel methodology is not required by TMLR, but this evidence alone does not establish submission readiness.

Human adjudication remains PENDING. Root's completed offline replay is reported separately; it is not independently re-executed in this checking pass. Existing comparisons/cohort stay frozen. Suggested next step is the root's post hoc source-linked all-job explanation, explicitly labeled as such.

Captured review clocks span 09:26 to13:05 IST; estimated active source/arithmetic review effort about0.20 hours, distinct from wall-clock span. INR0 additional spend.
