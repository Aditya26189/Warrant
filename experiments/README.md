# Research workstreams

These modules preserve exploratory code, controlled examples, audit evidence,
and completed research decisions. They do not extend the installed `warrant`
command's guarantees. Begin with each workstream's decision and claim boundary.

| Workstream | Entry point | Current interpretation |
|---|---|---|
| Grader auditing | [Guide](grader_poc/README.md), [closing feasibility report](../reports/GATE4-TRANSFER.md) | Known omissions and repair controls retained; custom discovery development stopped after the bounded comparison |
| Assurance semantics | [Exact diagnostic](assurance_semantics/exact.py), [witness](../docs/research/publication/EXACT_WITNESS.md) | A controlled diagnostic, with no general production or population-survey claim |
| Publication feasibility | [Inventory code](publication_feasibility/inventory.py), [prospectus](../docs/research/publication/PAPER_PROSPECTUS.md) | Exploratory source inventory and proposed routes, not a completed paper |
| Unscored-trial accounting | [Findings](../docs/research/unscored_trials/FINDINGS.md), [portable reproduction](../docs/research/unscored_trials/REPRODUCING.md) | Completed technical report; original-attempt lineage and independent human review remain unavailable |
| Stopping-feedback feasibility | [Decision](../agent-stopping-feedback-study/DECISION.md), [reproduction](../agent-stopping-feedback-study/REPRODUCING.md) | Closed at its data-feasibility gate; no stopping-policy performance result |

## Offline software checks

From the repository root, use Python with pytest and tqdm installed:

    python -m pytest -q experiments/assurance_semantics/test_exact.py
    python -m pytest -q experiments/unscored_trials/tests
    python -m pytest -q agent-stopping-feedback-study/tests

These are separate invocations to keep each study's import context explicit.
They test finite examples, parsing, evidence integrity, and report behavior.
They do not fetch datasets, run model inference, or establish independent human
adjudication. The [research CI workflow](../.github/workflows/research.yml)
executes these suites separately from the installed customer path.

For numerical report reproduction, follow the workstream's guide and choose a
new output directory outside the checkout. Scientific generators require clean,
committed source. Preserve original artifacts and source revisions.

## Licensing and data

The project code is MIT. Bundled third-party numerical inputs retain their
own licenses and notices; see [unscored-trials attribution](unscored_trials/portable_inputs/NOTICE.md).
Raw private review packages and local research caches are not release inputs.
