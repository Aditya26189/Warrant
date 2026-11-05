# Primary sources and attribution

The repository's own artifacts support its measured values. External sources
identify data, methods and tools; they do not independently validate this
implementation.

This list records the role of sources consulted for the documentation.
Bibliographic/abstract review is distinguished from source-code inspection.
Earlier studies retain more detailed retrieval manifests and closest-work
assessments. This is not a new exhaustive literature or novelty review.

## Data and model

| Source | Role | Review boundary |
|---|---|---|
| [Joshi et al., TriviaQA, ACL 2017](https://aclanthology.org/P17-1147/) | Identify the upstream question-answer dataset | Bibliographic page and abstract; project sampling and labels come from retained manifests/code |
| [Qwen2.5-7B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) | Identify the named model and upstream implementation guidance | Model card; no reconstruction of historical weights |
| [Pinned Terminal-Bench release](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/tree/572b2614be2c0cb2527e14f5b1e4026f1072e6c1) | Released-record source for the accounting study | New docs use retained source manifests and reviewed projections; no full new corpus acquisition |

Dataset identity does not establish correct project labels, representative
sampling or absence of benchmark contamination. The model's pretraining exposure
to individual evaluation questions was not independently audited.

## Statistical foundations

| Source | Role | What is not inferred |
|---|---|---|
| [Clopper and Pearson, 1934](https://doi.org/10.1093/biomet/26.4.404), with [SciPy's exact-interval reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html) | Attribution of exact fixed-binomial intervals | Validity after arbitrary selection or dependence |
| [Tong, Feng and Li, NP classification](https://arxiv.org/abs/1608.03109) | Established rank-based type-I-error control | A new Warrant theorem or automatic proof of native code |
| [Efron, bootstrap, 1979](https://doi.org/10.1214/aos/1176344552) | Attribution of bootstrap methodology | Exact finite-sample coverage of this project's percentile intervals |
| [Howard et al., confidence sequences](https://arxiv.org/abs/1810.08240) | Established time-uniform inference context | That every monitoring implementation is anytime-valid |
| [Shin, Ramdas and Rinaldo, e-detectors](https://arxiv.org/abs/2203.03532) | Prior sequential-change-detection framework | A novel sequential method in this repo |
| [Bian and Barber, training-conditional coverage](https://arxiv.org/abs/2205.03647) | Distinguish marginal and training-conditional statements | A blanket invalidity claim about conformal prediction |
| [Coppola and Mazo, Bernoulli intervals and conformal prediction](https://arxiv.org/abs/2502.07497) | Existing interpretation warnings relevant to guarantee types | Proof that their result applies unchanged to every native branch |

The new documentation pass confirmed bibliographic identities and inspected
the cited official/reference material. The native FPR audit retains its own
selected-section source/proof mapping. No independent human theorem or
source-level sign-off is claimed.

The mathematical witness is reproduced by
[the exact program](../../experiments/assurance_semantics/exact.py), with its
[retained result](../../results/publication/assurance_semantics.json).
That computation, rather than an appeal to a citation, supports the
particular counterexample probability.

## Framework behavior

The [Presidio analyzer documentation](https://presidio.dataprivacystack.org/analyzer/)
explains configurable recognizers. Current upstream documentation is useful
context; it does not retroactively specify defaults in the older installed
version used by the project.

The [pinned Harbor mean implementation](https://raw.githubusercontent.com/harbor-framework/harbor/1c0f38644b94c2a9a5fa4a8b77667d8175d0869e/src/harbor/metrics/mean.py)
supports the inspected null-as-zero operational aggregation behavior. It
does not identify original missing executions or historical website
adjudication.

## Closed-study closest work

Use the retained
[unscored-trial related work](../../docs/research/unscored_trials/RELATED_WORK.md)
and [stopping-feedback comparison](../../agent-stopping-feedback-study/CLOSEST_WORK.md)
for their exact versioned scopes, discovery-only leads, access failures and
overlap assessments. These are dated study records, not a claim that all
subsequent work has been reviewed.

## Documentation and publication tools

The [LLVM documentation](https://llvm.org/docs/) motivates separating getting
started, implementation manuals, reference and testing. Adopting that
organization does not imply LLVM's scale or maturity.

[MkDocs configuration](https://www.mkdocs.org/user-guide/configuration/)
documents strict builds and navigation.
[Tectonic installation](https://tectonic-typesetting.github.io/book/latest/installation/)
documents the LaTeX engine used for the preprint. Toolchain releases and
archive checksums are recorded with the paper sources.

Zenodo's [resource types](https://help.zenodo.org/docs/deposit/describe-records/resource-type/)
and [license guidance](https://help.zenodo.org/docs/deposit/describe-records/licenses/)
inform the prepared deposit. A preprint deposit is not peer review or
publication acceptance. CC BY 4.0 applies to the manuscript/LaTeX source as
declared; MIT code and third-party input terms remain separate.

## Source-use rule

A citation should support the statement beside it. A dataset citation is not
evidence that a particular run used the dataset correctly. A framework manual
is not a measurement of that framework. A known theorem is not an audited
implementation proof. These distinctions apply to this handbook as much as
to the experiments it describes.
