# Warrant unscored-trial accounting: exploratory technical report

**Decision: REPORT.** This is exploratory, AI-assisted work, not peer-reviewed work or a submitted TMLR paper. The bounded decision study is closed; no benchmark correction or corrected official ranking is established.

## Question and corpus

Can public agent-evaluation exports support a useful, reproducible finding about accounting for unscored outcomes? We test what the released final records identify before changing any scoring target. Recorded zero, absent/null reward, absent raw file and exception are distinct evidence states.

The official [Terminal-Bench release](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/tree/572b2614be2c0cb2527e14f5b1e4026f1072e6c1) is pinned at `572b2614be2c0cb2527e14f5b1e4026f1072e6c1`. The retained census contains 75 submissions, 245 jobs and 32,803 named final records. These files describe released final records; configurations and minimum repetition rules do not establish an exact original execution roster or attempt/retry history.

The historical Marin/tau baseline is preserved. Its [earlier verification and replay receipts](https://github.com/Aditya26189/Warrant/blob/46961e95324ba0f5ae3fab348a2a8766e3efafd5/results/unscored_trials/20261029-terminal-bench2/context/baseline_verification.json) remain archival evidence; this closeout does not rerun that baseline or rewrite its canonical outputs. Eight retained Marin cells violate a 5% missingness cap, so that full-panel cap remains hypothetical.

## Native-score and population reconciliation

| Full-census joint status | Jobs | Primary-selected jobs |
| --- | --- | --- |
| match | 217 | 200 |
| unavailable | 8 | 0 |
| unresolved_mismatch | 20 | 0 |

Source: [generated census accounting](census_accounting.csv), with selectors into [all-job reconciliation](../numerical/reconciliation.csv). Joint reconciliation tests identity, name indexes and counters as well as means. An unresolved joint status is not synonymous with a numerical score error.

Primary eligibility retains 56 submissions and excludes unreconciled native job populations. Therefore native agreement on the strict cohort is partly an **inclusion condition**, rather than an independent claim that every released job reconciles. See [eligibility](../numerical/eligibility.csv) for every exclusion.

The separately labeled post hoc whole-job diagnostic gives 236 matching means, 3 differing means and 6 unavailable supported means across the full census. Whole-job pooling does not repair evaluation-group aliases, indexes, task identities or primary eligibility, and does not reconstruct an official leaderboard.

| Differing exported account | Raw mass / final records | Own summary mass / denominator | Summary-internal status |
| --- | --- | --- | --- |
| [BashAgent__TermiGen-32B / qwen_claude_5](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/raw/572b2614be2c0cb2527e14f5b1e4026f1072e6c1/submissions/terminal-bench/2.0/BashAgent__TermiGen-32B/qwen_claude_5/result.json) | 86 / 445 | 72 / 445 | match |
| [Capy__Claude-Opus-4.6 / eval-terminal-bench-2-0-anthropic-claude-opus-4-6-ae1eef84-1773189792834](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/raw/572b2614be2c0cb2527e14f5b1e4026f1072e6c1/submissions/terminal-bench/2.0/Capy__Claude-Opus-4.6/eval-terminal-bench-2-0-anthropic-claude-opus-4-6-ae1eef84-1773189792834/result.json) | 68 / 89 | 21 / 29 | match |
| [grok-cli__grok-4.20-0309-reasoning / job-part1](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/raw/572b2614be2c0cb2527e14f5b1e4026f1072e6c1/submissions/terminal-bench/2.0/grok-cli__grok-4.20-0309-reasoning/job-part1/result.json) | 81 / 130 | 81 / 131 | match |

Source: [whole-job diagnostics](../numerical/whole_job_diagnostics.csv), including immutable source hashes and published-mean JSON pointers. Equal record counts do not prove equal outcomes; differing named populations can each have internally coherent means. A summary-recorded zero without a raw file is already observed summary evidence, not an invented unknown reward. Export causes, intended historical populations and website adjudication remain unresolved.

Raw outcomes include 20,648 positive scores, 11,229 recorded zeros and 926 genuinely unscored retained records. Scores coexist with exceptions in 4,472 records, including 845 positive scores. A valid reward survives its exception label; the label alone establishes no causal diagnosis.

[Pinned Harbor source](https://raw.githubusercontent.com/harbor-framework/harbor/1c0f38644b94c2a9a5fa4a8b77667d8175d0869e/src/harbor/metrics/mean.py) documents null-as-zero operational means for the supported single reward channel. Free [0,1] completion changes the target: it assigns hypothetical rewards to present unscored outcomes. It is not a recovery of corrected ranks, missing original executions or capability under repaired infrastructure.

## Structural weighting and supported comparisons

| Uniform records per task | Retained submissions |
| --- | --- |
| 1 | 3 |
| 5 | 53 |

Every retained submission has uniform within-submission repetitions. For T tasks and r records per task,

```text
equal-task = (1/T) Σ_t [(1/r) Σ_k y_tk] = (1/(Tr)) Σ_tk y_tk = pooled
```

Thus policy equality for all 56 retained submissions follows algebraically from their record weights. It is a property of this selected cohort and an implementation check, not strong evidence that weighting is unimportant in general. Nonuniform repetitions or changed conditioning sets can change the estimand.

Source: [weighting structure](weighting_structure.csv), with exact record weights and policy selectors. The historical policies remain unchanged.

The 56 eligible submissions form 1,540 unordered candidate pairs; 109 are excluded by the frozen compatibility rules, leaving all 1,431 compatible pairs analyzed. Reported task-definition/checksum signature group sizes are [54, 1, 1]. See the [frozen compatibility matrix](https://github.com/Aditya26189/Warrant/blob/46961e95324ba0f5ae3fab348a2a8766e3efafd5/results/unscored_trials/20261029-terminal-bench2/compatibility_matrix.csv).

| Exact completion class | Compatible equal-task pairs |
| --- | --- |
| strict robust | 1360 |
| reversal compatible | 56 |
| equality compatible | 14 |
| identified tie | 1 |

The 14 equality-compatible cases comprise 8 existing strict orders that can become ties without reversing and 6 existing native ties that can break. They are not all tie-only losses. [Pairwise explanations](pairwise_explanation.csv) retain the canonical class and identify these subtypes separately.

Comparisons use complete matching task-definition/checksum signatures and fixed populations/weights. Unknown rewards remain independently free in [0,1], so the difference interval is exactly [L_A−H_B, H_A−L_B]. Pairing task IDs does not tighten it without additional restrictions. Reversal-compatible means a hypothetical completion can reverse an existing strict order; it does not mean that a corrected reversal was observed.

## Concrete source-to-table examples

| Example | Computational check | Review |
| --- | --- | --- |
| scored exception | Native record value = 1; per-eval denominator = 445; contribution = 1/445. | [H02](human_review_worksheet.md) |
| robust comparison | [L_A-H_B,H_A-L_B] = [-9/89,-38/445]. Task pairing alone adds no restriction on independently free unknown rewards. | [H05](human_review_worksheet.md) |
| native tie can break | [L_A-H_B,H_A-L_B] = [-1/89,2/445]. Task pairing alone adds no restriction on independently free unknown rewards. | [H06](human_review_worksheet.md) |

These examples are post hoc illustrations, not a random sample or independent adjudication. The worksheet also covers ordinary zero, null reward and a raw/summary discrepancy, with original source hashes, exact pointers, retained values and expected arithmetic.

## Closest-work overlap and REPORT decision

[Terminal-Bench issue 2246](https://github.com/harbor-framework/terminal-bench/issues/2246) and [honestboard at its pinned revision](https://github.com/jopoku16/honestboard/tree/97bd812d07c9c852d05666128ff3b59cbe461a0c) already examine this release's summary-based denominator and ranking sensitivity. Free-outcome bounds and denominator distinctions are established in [Gao and Zhou](https://arxiv.org/html/2605.10448v1), while [AgentEval](https://arxiv.org/html/2610.21177v1) addresses execution accounting. See the [closest-work comparison](https://github.com/Aditya26189/Warrant/blob/research/unscored-trials-20261029/docs/research/unscored_trials/RELATED_WORK.md).

The additional useful result is an auditable separation of scalar agreement from record population, task identity and index agreement. The strongest objection is closest-work overlap plus unresolved export causes: these checks have not yet changed a substantive benchmark conclusion or identified an actionable scoring-policy defect. Structural policy equality and hypothetical completion envelopes do not resolve that objection. Preserve the technical report and stop, rather than manufacture a submission claim.

## Limitations, reproducibility and human handoff

Original planned slots, durable attempt/retry lineage, exact submitted harnesses and official website importer/adjudication history remain unavailable. Repeated final records are not assumed to be retries. A raw-supported population outside strict native eligibility is descriptive evidence, not a secondary ranking. HAL was not invoked to replace missing execution evidence.

The portable inputs are reviewed scalar projections with original source hashes, transformation identity and derived hashes. They support numerical regeneration of retained fields. Opaque configuration/semantic hashes are attestations: omitted raw configurations, transcripts and exception traces are not independently verified by this route. Third-party data retain their source licensing; Warrant's code license does not relicense them.

From a clean checkout and a new empty study-data directory:

```powershell
python -B -m experiments.unscored_trials.portable reproduce --study-data-dir C:\path\to\empty-study-data
```

This command uses the committed minimal input bundle and reference to regenerate numerical tables and this report. Consult the [reproduction guide](https://github.com/Aditya26189/Warrant/blob/research/unscored-trials-20261029/docs/research/unscored_trials/REPRODUCING.md) and the invocation's `validation.json` for actual acquisition, integrity, numerical and report outcomes. Report generation itself does not prove that an empty-cache test ran. The earlier exact cached replay remains a separate archival check; historical timestamps, paths and failed-download receipts are not numerical targets.

The [human worksheet](human_review_worksheet.md) and [editable CSV](human_review_worksheet.csv) remain entirely **PENDING**. A human can verify source-to-scalar fields, exclusions and arithmetic now. AI and subagent checks are not independent human adjudication; reviewing these files cannot recover missing execution/importer evidence.

Reopen only with specific evidence: an original roster/attempt lineage and pinned importer/harness history relevant to an accounting claim, or a demonstrated substantive consequence beyond the closest audit. More benchmark rows alone are insufficient. Human responsibility for source checks and the text is still required before authorship/publication claims.

This work was generated and checked with AI assistance, including OpenAI's Codex. OpenAI develops models evaluated in the corpus, creating a relevant maker conflict for this AI-assisted analysis. No human authors, affiliations, funding, endorsement or independent review are invented. No paper submission or outreach is part of this study.
