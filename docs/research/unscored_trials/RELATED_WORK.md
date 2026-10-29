# Closest work and the remaining contribution

This is an exploratory extension. Sources and retrieval grades are retained in
[the context manifest](../../../results/unscored_trials/20261029-terminal-bench2/context/closest_work_source_manifest.json).
The original baseline and exposed issue outcomes were known before this
extension's protocol was frozen. An additional assistant's source check is not
independent replication or human adjudication.

| Primary work | Existing contribution | What this extension adds or cannot add |
|---|---|---|
| [Gao and Zhou, v1](https://arxiv.org/html/2605.10448v1) | Outcome evidence, bounds and denominator rules; distinguishes infrastructure exclusions from agent-caused failures | Applying free-outcome bounds is not new theory. We must reproduce native zero handling before offering another target. |
| [AgentEval, Ruiqi Gao and coauthors, v1](https://arxiv.org/html/2610.21177v1) | Allocated/completed/decidable/unresolved accounting and execution attempts | Separate author team. Similar accounting vocabulary is prior work, not a new taxonomy here. |
| [Terminal-Bench issue 2246](https://github.com/harbor-framework/terminal-bench/issues/2246) and [honestboard](https://github.com/jopoku16/honestboard) at `97bd812d07c9c852d05666128ff3b59cbe461a0c` | Same released corpus; summary-based task pooling, exception-only zeros, preserved scored exceptions, missingness/ranking sensitivity and job-selection diagnostics | Generic denominator sensitivity and rank fragility are occupied. Our additional layer checks raw UUIDs, task Git identities/checksums, individual final records and native job/index reconciliation. Its usefulness must come from what those checks establish, not their code volume. |
| [Hardy et al., v1](https://arxiv.org/abs/2610.00651v1) | Evaluation reliability and sparse task/scaffold comparisons | Their loader's distinct/filter operations and older row count do not by themselves establish an omission defect. |
| [HAL response matrix](https://huggingface.co/datasets/razam2/hal-response-matrix/tree/c367d8e49e31b572903064b1823cd33e81520be9) | Cleaned scored response matrix | Does not identify missing executions without primary roster/log evidence. Fallback was not triggered. |

The pinned issue snapshot is open with no comments. Its author's audit is not
maintainer confirmation. Direct retrieval later recovered the linked repository;
earlier web-only access failures do not establish source unavailability. Its
loader uses summary trial names, binarizes rewards, preserves rewarded
exceptions and pools jobs by task. It does not reconcile raw UUID/task checksums
or reconstruct the original attempts. Its best-job sensitivity is hypothetical;
we do not infer actual selective submission or retries. Its claim about website
aggregation is not adopted without a pinned official importer.

The release-level differences found here are reproducible, but different export
populations, schemas or snapshots explain them at least as well as a scoring
policy defect. No observed difference supplies original retry history. The
strict eligible cohort has no equal-task versus pooled weighting effect. These
are useful limits for a technical report; they do not yet establish a sufficiently
distinct empirical contribution for a submission.

[TMLR's criteria](https://jmlr.org/tmlr/acceptance-criteria.html) concern convincing
evidence and audience interest; a novel method is not required. The REPORT
decision is an assessment of the present evidence and overlap, not a claim that
another theorem is needed or an estimate of acceptance probability.
