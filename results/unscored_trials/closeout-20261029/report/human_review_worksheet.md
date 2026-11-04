# Human source-to-table review worksheet

All human conclusions, reviewer identities and dates remain **PENDING**. These are prioritized post hoc examples, not a prevalence sample. AI checks are not independent human adjudication.

For raw cases, retrieve the immutable URL and verify its original SHA-256 before inspecting the exact JSON pointers. Supporting sanitized ledgers reproduce retained-field arithmetic; hashes of omitted configurations or traces are attestations, not independent verification of that content.

## Priority 1: H03 — null reward

A null/absent verifier reward is unscored; documented native final-record accounting assigns zero.

Source: [submissions/terminal-bench/2.0/Ante__Gemini-3.1-Pro-Preview/2026-02-20__19-31-44/filter-js-from-html__UAzyzpS/result.json](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/raw/572b2614be2c0cb2527e14f5b1e4026f1072e6c1/submissions/terminal-bench/2.0/Ante__Gemini-3.1-Pro-Preview/2026-02-20__19-31-44/filter-js-from-html__UAzyzpS/result.json). SHA-256: `001c658de9290dd5ccf8ea8a6cd50e1db855dd7dfec9cc01a41c75eaeaaf9f2c`.

JSON pointers: `/verifier_result`, `/exception_info/exception_type`

```json
{
  "selector": {},
  "inputs": {
    "trial_uuid": "a80270ec-4eca-44ec-a9f9-798937b661a8",
    "reward_status": "null_verifier",
    "reward_decimal": null,
    "native_reward_decimal": "0",
    "score_present": false,
    "exception_present": true,
    "exception_class": "VerifierTimeoutError",
    "job_joint_reconciliation_status": "match"
  },
  "supporting_inputs": [
    {
      "file": "../numerical/executions.json.gz",
      "sha256": "dabe0f841ae1adfc3756b83d261a844017efb1e0ae23b44b1b8296608e99c4c3",
      "selector": {
        "source_path": "submissions/terminal-bench/2.0/Ante__Gemini-3.1-Pro-Preview/2026-02-20__19-31-44/filter-js-from-html__UAzyzpS/result.json"
      }
    }
  ]
}
```

Native record value = 0; per-eval denominator = 445; contribution = 0. Free [0,1] completion is a different, hypothetical target.

Expected computational output: `{"exception_present":true,"native_record_value":"0","native_weighted_contribution":"0","reward_status":"null_verifier","score_present":false}`.

Selection: first(source_sha256,source_path) within requested record category; post_hoc_diagnostic.

Check raw URL/hash before source adjudication; this generator reads retained scalar projections, not omitted raw fields. Job joint reconciliation is match; the record contribution does not establish whole-job index/population agreement.

| Human field | Actual entry |
| --- | --- |
| review status | PENDING |
| reviewer | PENDING |
| actual conclusion | PENDING |
| review date | PENDING |
| notes | PENDING |

## Priority 2: H02 — scored exception

A valid positive score survives the recorded exception.

Source: [submissions/terminal-bench/2.0/WOZCODE__Claude-Opus-4-7/2026-04-19__20-07-00/path-tracing-reverse__yKm284w/result.json](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/raw/572b2614be2c0cb2527e14f5b1e4026f1072e6c1/submissions/terminal-bench/2.0/WOZCODE__Claude-Opus-4-7/2026-04-19__20-07-00/path-tracing-reverse__yKm284w/result.json). SHA-256: `0014b81f6da3d44150f7785ea47404f667e59612e31f700680dc2960fd9c81ae`.

JSON pointers: `/verifier_result/rewards/reward`, `/exception_info/exception_type`

```json
{
  "selector": {},
  "inputs": {
    "trial_uuid": "3a036bab-6c9d-481f-9131-82cdced35646",
    "reward_status": "scored_positive",
    "reward_decimal": "1.0",
    "native_reward_decimal": "1.0",
    "score_present": true,
    "exception_present": true,
    "exception_class": "AgentTimeoutError",
    "job_joint_reconciliation_status": "unresolved_mismatch"
  },
  "supporting_inputs": [
    {
      "file": "../numerical/executions.json.gz",
      "sha256": "dabe0f841ae1adfc3756b83d261a844017efb1e0ae23b44b1b8296608e99c4c3",
      "selector": {
        "source_path": "submissions/terminal-bench/2.0/WOZCODE__Claude-Opus-4-7/2026-04-19__20-07-00/path-tracing-reverse__yKm284w/result.json"
      }
    }
  ]
}
```

Native record value = 1; per-eval denominator = 445; contribution = 1/445.

Expected computational output: `{"exception_present":true,"native_record_value":"1","native_weighted_contribution":"1/445","reward_status":"scored_positive","score_present":true}`.

Selection: first(source_sha256,source_path) within requested record category; post_hoc_diagnostic.

Check raw URL/hash before source adjudication; this generator reads retained scalar projections, not omitted raw fields. Job joint reconciliation is unresolved_mismatch; the record contribution does not establish whole-job index/population agreement.

| Human field | Actual entry |
| --- | --- |
| review status | PENDING |
| reviewer | PENDING |
| actual conclusion | PENDING |
| review date | PENDING |
| notes | PENDING |

## Priority 3: H04 — raw summary difference

A differing raw/summary mean requires population and index investigation before any score-error claim.

Source: [submissions/terminal-bench/2.0/BashAgent__TermiGen-32B/qwen_claude_5/result.json](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/raw/572b2614be2c0cb2527e14f5b1e4026f1072e6c1/submissions/terminal-bench/2.0/BashAgent__TermiGen-32B/qwen_claude_5/result.json). SHA-256: `f5eb144577611e61fcecb544252bb09703a2ea4668a5381a452fabd61c791cd4`.

JSON pointers: `/stats/evals/qwen-agent__terminal-bench/metrics/0/mean`, `/stats/evals`, `/stats/n_trials`

```json
{
  "selector": {},
  "inputs": {
    "raw_named_final_record_count": "445",
    "raw_native_reward_mass": "86/1",
    "raw_native_zero_mean": "86/445",
    "summary_denominator": "445",
    "summary_reward_mass": "72/1",
    "summary_mean": "72/445",
    "published_mean": "129438202247191/800000000000000",
    "summary_only_name_count": "17",
    "raw_only_name_count": "17",
    "summary_vs_raw_name_population": "different_named_populations",
    "native_absolute_tolerance": "1E-12",
    "configuration_source_url": "https://raw.githubusercontent.com/Aditya26189/Warrant/46961e95324ba0f5ae3fab348a2a8766e3efafd5/experiments/unscored_trials/config.json",
    "configuration_sha256": "b00bbb68f957ee89345e1451f6d07243f276ce2c879491f5c993241e4b28f683",
    "configuration_json_pointer": "/native_absolute_tolerance"
  },
  "supporting_inputs": [
    {
      "file": "../numerical/whole_job_diagnostics.csv",
      "sha256": "54aeb774fcdafa33cc008c3a74d532d2e509562052b21309a42afa5a13f9b37e",
      "selector": {
        "job_path": "submissions/terminal-bench/2.0/BashAgent__TermiGen-32B/qwen_claude_5"
      }
    },
    {
      "file": "../numerical/executions.json.gz",
      "sha256": "dabe0f841ae1adfc3756b83d261a844017efb1e0ae23b44b1b8296608e99c4c3",
      "selector": {
        "job_path": "submissions/terminal-bench/2.0/BashAgent__TermiGen-32B/qwen_claude_5"
      }
    }
  ]
}
```

Raw reward mass 86 divided by 445 = 86/445; summary mass 72 divided by 445 = 72/445. Compare the published decimal at the frozen tolerance 1E-12, then inspect named reward/exception indexes.

Expected computational output: `{"strict_joint_native_status":"unresolved_mismatch","summary_internal_status":"match","whole_job_numeric_status":"difference"}`.

Selection: first(job_path) among all post_hoc whole-job numeric differences.

No retry/export cause or intended official population can be established from this arithmetic alone.

| Human field | Actual entry |
| --- | --- |
| review status | PENDING |
| reviewer | PENDING |
| actual conclusion | PENDING |
| review date | PENDING |
| notes | PENDING |

## Priority 4: H06 — native tie can break

A native null-as-zero tie can break under hypothetical completion.

Source: [../numerical/pairwise_comparisons.csv](../numerical/pairwise_comparisons.csv). SHA-256: `3cb0ca2d6bc7ac05bf4182740b82729fee725934c18a68c552ed79768c2703be`.

JSON pointers: CSV row selector below; no JSON pointer applies.

```json
{
  "selector": {
    "submission_a": "Ante__Gemini-3-Pro-Preview",
    "submission_b": "Terminus2__GPT-5.3-Codex",
    "policy": "equal_task"
  },
  "inputs": {
    "submission_a": "Ante__Gemini-3-Pro-Preview",
    "submission_b": "Terminus2__GPT-5.3-Codex",
    "a": {
      "record_count": "445",
      "task_count": "89",
      "unknown_record_count": "2",
      "score_completion_lower": "288/445",
      "score_completion_upper": "58/89"
    },
    "b": {
      "record_count": "445",
      "task_count": "89",
      "unknown_record_count": "5",
      "score_completion_lower": "288/445",
      "score_completion_upper": "293/445"
    }
  },
  "supporting_inputs": [
    {
      "file": "../numerical/policy_comparisons.csv",
      "sha256": "b5ad3b2748754aadcabf607408c01b00e0585d405dd9b69a1591c9232c2d2c4b",
      "selector": {
        "submission": "Ante__Gemini-3-Pro-Preview",
        "policy": "equal_task"
      }
    },
    {
      "file": "../numerical/policy_comparisons.csv",
      "sha256": "b5ad3b2748754aadcabf607408c01b00e0585d405dd9b69a1591c9232c2d2c4b",
      "selector": {
        "submission": "Terminus2__GPT-5.3-Codex",
        "policy": "equal_task"
      }
    },
    {
      "file": "../numerical/executions.json.gz",
      "sha256": "dabe0f841ae1adfc3756b83d261a844017efb1e0ae23b44b1b8296608e99c4c3",
      "selector": {
        "submission": "Ante__Gemini-3-Pro-Preview"
      }
    },
    {
      "file": "../numerical/executions.json.gz",
      "sha256": "dabe0f841ae1adfc3756b83d261a844017efb1e0ae23b44b1b8296608e99c4c3",
      "selector": {
        "submission": "Terminus2__GPT-5.3-Codex"
      }
    }
  ]
}
```

[L_A-H_B,H_A-L_B] = [-1/89,2/445]. Task pairing alone adds no restriction on independently free unknown rewards.

Expected computational output: `{"classification":"equality_compatible","difference_lower":"-1/89","difference_upper":"2/445","native_order":"tie","native_tie_can_break":"True"}`.

Selection: first(submission_a,submission_b) among requested equal-task comparison category; post_hoc_diagnostic.

Verify record sums/identity in the supporting scalar ledgers; counterfactual assignments are not recovered corrected outcomes.

| Human field | Actual entry |
| --- | --- |
| review status | PENDING |
| reviewer | PENDING |
| actual conclusion | PENDING |
| review date | PENDING |
| notes | PENDING |

## Priority 5: H05 — robust comparison

A robust strict order survives every allowed independent completion.

Source: [../numerical/pairwise_comparisons.csv](../numerical/pairwise_comparisons.csv). SHA-256: `3cb0ca2d6bc7ac05bf4182740b82729fee725934c18a68c552ed79768c2703be`.

JSON pointers: CSV row selector below; no JSON pointer applies.

```json
{
  "selector": {
    "submission_a": "Ante__Gemini-3-Pro-Preview",
    "submission_b": "Ante__Gemini-3.1-Pro-Preview",
    "policy": "equal_task"
  },
  "inputs": {
    "submission_a": "Ante__Gemini-3-Pro-Preview",
    "submission_b": "Ante__Gemini-3.1-Pro-Preview",
    "a": {
      "record_count": "445",
      "task_count": "89",
      "unknown_record_count": "2",
      "score_completion_lower": "288/445",
      "score_completion_upper": "58/89"
    },
    "b": {
      "record_count": "445",
      "task_count": "89",
      "unknown_record_count": "5",
      "score_completion_lower": "328/445",
      "score_completion_upper": "333/445"
    }
  },
  "supporting_inputs": [
    {
      "file": "../numerical/policy_comparisons.csv",
      "sha256": "b5ad3b2748754aadcabf607408c01b00e0585d405dd9b69a1591c9232c2d2c4b",
      "selector": {
        "submission": "Ante__Gemini-3-Pro-Preview",
        "policy": "equal_task"
      }
    },
    {
      "file": "../numerical/policy_comparisons.csv",
      "sha256": "b5ad3b2748754aadcabf607408c01b00e0585d405dd9b69a1591c9232c2d2c4b",
      "selector": {
        "submission": "Ante__Gemini-3.1-Pro-Preview",
        "policy": "equal_task"
      }
    },
    {
      "file": "../numerical/executions.json.gz",
      "sha256": "dabe0f841ae1adfc3756b83d261a844017efb1e0ae23b44b1b8296608e99c4c3",
      "selector": {
        "submission": "Ante__Gemini-3-Pro-Preview"
      }
    },
    {
      "file": "../numerical/executions.json.gz",
      "sha256": "dabe0f841ae1adfc3756b83d261a844017efb1e0ae23b44b1b8296608e99c4c3",
      "selector": {
        "submission": "Ante__Gemini-3.1-Pro-Preview"
      }
    }
  ]
}
```

[L_A-H_B,H_A-L_B] = [-9/89,-38/445]. Task pairing alone adds no restriction on independently free unknown rewards.

Expected computational output: `{"classification":"strict_robust","difference_lower":"-9/89","difference_upper":"-38/445","native_order":"b","native_tie_can_break":"False"}`.

Selection: first(submission_a,submission_b) among requested equal-task comparison category; post_hoc_diagnostic.

Verify record sums/identity in the supporting scalar ledgers; counterfactual assignments are not recovered corrected outcomes.

| Human field | Actual entry |
| --- | --- |
| review status | PENDING |
| reviewer | PENDING |
| actual conclusion | PENDING |
| review date | PENDING |
| notes | PENDING |

## Priority 6: H01 — ordinary record

A recorded zero is an observed score, not an unscored outcome.

Source: [submissions/terminal-bench/2.0/Terminus2__GLM-5/2026-02-14__13-57-51/protein-assembly__h8XCtr8/result.json](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/raw/572b2614be2c0cb2527e14f5b1e4026f1072e6c1/submissions/terminal-bench/2.0/Terminus2__GLM-5/2026-02-14__13-57-51/protein-assembly__h8XCtr8/result.json). SHA-256: `000152db0deb65d500a3e98cccec4d7d6b6c060e3eaf89289eac17b5df07fcae`.

JSON pointers: `/verifier_result/rewards/reward`, `/exception_info`

```json
{
  "selector": {},
  "inputs": {
    "trial_uuid": "52cb2142-f83c-4452-a4ae-17a19312fa67",
    "reward_status": "scored_zero",
    "reward_decimal": "0.0",
    "native_reward_decimal": "0.0",
    "score_present": true,
    "exception_present": false,
    "exception_class": null,
    "job_joint_reconciliation_status": "match"
  },
  "supporting_inputs": [
    {
      "file": "../numerical/executions.json.gz",
      "sha256": "dabe0f841ae1adfc3756b83d261a844017efb1e0ae23b44b1b8296608e99c4c3",
      "selector": {
        "source_path": "submissions/terminal-bench/2.0/Terminus2__GLM-5/2026-02-14__13-57-51/protein-assembly__h8XCtr8/result.json"
      }
    }
  ]
}
```

Native record value = 0; per-eval denominator = 445; contribution = 0.

Expected computational output: `{"exception_present":false,"native_record_value":"0","native_weighted_contribution":"0","reward_status":"scored_zero","score_present":true}`.

Selection: first(source_sha256,source_path) within requested record category; post_hoc_diagnostic.

Check raw URL/hash before source adjudication; this generator reads retained scalar projections, not omitted raw fields. Job joint reconciliation is match; the record contribution does not establish whole-job index/population agreement.

| Human field | Actual entry |
| --- | --- |
| review status | PENDING |
| reviewer | PENDING |
| actual conclusion | PENDING |
| review date | PENDING |
| notes | PENDING |

## Review boundary

A human can now inspect source fields, transformations, exclusions and arithmetic. Original planned executions, retry/export causes, exact submitted harnesses and official website import/adjudication remain unverified without new external execution or importer evidence. Reviewing this worksheet cannot supply those missing records.
