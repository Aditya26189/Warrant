# Evidence package: REPORT

Read [the findings](../../../docs/research/unscored_trials/FINDINGS.md),
[decision](../../../docs/research/unscored_trials/PUBLICATION_DECISION.md) and
[reproduction guide](../../../docs/research/unscored_trials/REPRODUCING.md).

- `summary.json` and `provenance.json`: frozen primary run and its clean source/config identity.
- `source_manifest.json`: hashed source and result-request shard indexes. Failed requests are HTTP history, not unscored executions.
- `executions.csv`: index of safe normalized execution shards, not the entire ledger in one CSV.
- `jobchecks.json`: index of full job/index/counter reconciliation checks.
- `native_score_reproduction.csv`: compact per-evaluation arithmetic and reconciliation dimensions. Its joint status is not a numerical-error count.
- `eligibility.csv`, `compatibility_matrix.csv`, `raw_population_support.csv`: exclusions, compatible pairs and descriptive raw support.
- `policy_comparisons.csv`, `pairwise_comparisons.csv`: explicitly labeled fixed-population completion envelopes and weighting policies, not corrected website ranks.
- `explanation/`: post hoc all-job numerical/population explanations with separate provenance. Primary results were not reclassified.
- `context/`: baseline verification and primary-source manifests; `task_spec.original.json` preserves exact input bytes.
- `validation/`: offline replay, focused checks, source cross-check and pending human worksheet. Advisory assistant checks are not human adjudication.

The immutable canonical reference remains the external `canonical-001`
directory. This published directory adds explanatory/validation files, so do not
pass the entire expanded directory as an exact canonical replay reference.
`validation/offline-replay-001.json` names the original compared files and hashes.
The external cache's durable path is in `validation/external_data.json`.

The official HF source declares Apache-2.0; see
[the pinned dataset](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/tree/572b2614be2c0cb2527e14f5b1e4026f1072e6c1)
and [license](https://www.apache.org/licenses/LICENSE-2.0).
Raw trajectories, configs and exception traces are retained outside Git. The
source manifests cite Harbor and honestboard; their code is not vendored here.
The frozen user-supplied baseline is preserved under its own notices.
