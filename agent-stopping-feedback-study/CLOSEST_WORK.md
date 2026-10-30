# Closest-work assessment

Primary sources were inspected on 30 October 2026 UTC. The
[search log](results/search_log.json) records actual queries, including
unsuccessful searches. Abstract-only discoveries are separated from sources
whose relevant methods were read. No new sampling method is proposed.

| Work | Question | Intervention | Observable feedback | Evaluation conditions | Audit/label cost | Artifacts and remaining difference |
| --- | --- | --- | --- | --- | --- | --- |
| [StopLoss](https://arxiv.org/html/2610.25525v1), §§2.3, 3.3, 5.2, C | Predict failure and reduce cost per retained solve | Abort original run | Complete outcomes and prefix scores | Cross executor/benchmark; successful-run calibration | Monitoring-inclusive economics; one-off calibration excluded | [Code](https://github.com/TIGER-AI-Lab/StopLoss/tree/c131d69d410d9f89d840981bc09bb1e6e9216cc8), weights/training windows/prices; inspected release lacks evaluation score arrays and call ledgers. Does not budget randomized continuation to recover censored labels. |
| [Continue or Restart?](https://arxiv.org/html/2610.35971v1), §§III–IV | Distinguish prefix information from task difficulty | Learned/random restart versus continuation | Recorded complete attempts | Same requested corpora; issue controls, repository holdouts, multiple executor/framework settings | Reconstructed transcript-token frontier | Analysis repository not identified in inspected paper. Rules out another classifier/transfer comparison as a contribution; does not measure selective-feedback acquisition. |
| [Calibration-transfer audit](https://arxiv.org/pdf/2609.25647), §§3–5 | Broad versus target-specific calibration transfer error | Frozen predictor/threshold audits | Completed trajectories | Leave-agent-out, prior correction, cohort and task controls | Complete-feedback calibration analysis | [Public release](https://github.com/caoyanze426-crypto/early-outcome-calibration-audit) explicitly excludes trajectory-level predictions. Transfer failure itself is covered; continuation-feedback expense is not evaluated. |
| [Monitor Accuracy Isn't the Answer](https://arxiv.org/html/2610.36544v1), §4.3 | Evaluate restart decision value or abstain | Restart/continue comparison | Complete observation through horizon | IID attempts within task/runtime; simultaneous binomial intervals | Finite-sample audit on existing traces | A public analysis-package URL was not located. Certificate/sample insufficiency is already addressed; not a censored-feedback expenditure study. |
| [Selective labels, KDD 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5958915/) | Evaluate predictions when acceptance determines labels | Observational contraction of accepted sets | Accepted-case outcomes | Comparable allocation and differing decision makers | Avoids randomized acquisition under motivating constraints | Primary assumptions/evaluation read; code not verified. Selection bias itself is established. |
| [Decision-making under selective labels](https://proceedings.mlr.press/v139/wei21a/wei21a.pdf) | Balance decision utility with future learning | Accept reveals, reject hides label | Accepted binary outcomes | Stationary arrivals; finite-domain optimal policies and extension | Explicit exploration utility/cost | Primary methods/supplement located, code not verified. Feedback acquisition expense is not a new concern; current-window transferred stopping audit differs. |
| [Performative Prediction with Selective Labels](https://arxiv.org/html/2610.08272v1) | Learn when policies shift population and label visibility | Repeated risk minimization | Accepted labels, conditional bounds | Sensitivity/regularity assumptions, lending experiments | Risk optimization rather than execution suffix accounting | [Code](https://github.com/recod-ai/perf_selective). External executor change is not automatically performativity; no supplied finite-window certificate. |
| [Exact finite-population sequential auditing](https://www.mdpi.com/2227-7390/14/18/3427) | Verify adverse share in model-proposed candidate sets | Random review without replacement, release/extend/fallback | Hidden candidate labels and available outside outcomes | Frozen finite batch, randomized audit order | Exact hypergeometric audit demand and savings | Relevant indexed primary equations/sections read; direct main-page access failed and supplement not downloaded. Direct mathematical match under relabeling; heterogeneous suffix expense needs empirical evidence, not renamed sampling. |
| [Finite-sample coverage audits](https://arxiv.org/html/2607.21480v1) | Certify missed relevant mass/recall | Audit excluded pool | Included-only labels insufficient | Frozen finite population; exact inversion | Audit lower bounds and sample planning | Primary impossibility/certification sections read; code not verified. Explains audit hunger at strict retention targets; additional intervals alone add little. |
| [Risk-limiting financial audits](https://proceedings.mlr.press/v216/shekhar23a.html) | Audit weighted finite-population assertions | Adaptive weighted sampling without replacement | Known sampling probabilities, imperfect side information | Finite population, confidence sequences | Label efficiency with residual/control-variate corrections | Primary PDF read. Weighted/adaptive auditing is established; actual continuation expense still requires data. |
| [Active Testing](https://proceedings.mlr.press/v139/kossen21a/kossen21a.pdf) | Estimate fixed-model performance with fewer labels | Active test-label acquisition | Corrected probability samples | Fixed model and unlabeled test pool | Label-efficiency comparison with uniform acquisition | [Author code](https://github.com/jlko/active-testing). Active evaluation is established; no executor-suffix economics question resolved. |
| [Cost-Optimal Active AI Model Evaluation](https://arxiv.org/html/2506.07949v1) | Allocate weak/strong ratings under a budget | Select expensive labels with positive probability | Residual-corrected strong-rating target | IID displayed theory, weak/strong annotation costs | Explicit cost/precision tradeoff | Primary methods read; dedicated code not verified. Cost-sensitive acquisition is established; run-specific continuation cost/retained success is a different empirical setting. |

## Direct mapping and surviving question

For the MDPI article's mapping, candidates are proposed stops and adverse labels
are recorded successful runs. Let S be successes among ordinary continuations,
K successes among all proposed stops and k successes restored by auditing. Then
actual retention is `(S+k)/(S+K)` and lost-success share is `(K-k)/(S+K)`.
The latter is its released-adverse fraction under relabeling. A bound on K
therefore propagates directly to retention. This is an algebraic mapping of
existing work, not a new result. Zero total successes remains undefined rather
than silently adopting a zero-loss convention.

Positive audit inclusion probabilities and established finite-population methods
can recover current-window information. An unbiased total estimator does not
make a substituted retention ratio exactly unbiased. Current-window design
uncertainty does not establish safety on future workloads.

The narrow remaining question concerns a changed joint distribution of risk and
remaining execution expense: does buying feedback erase an otherwise useful
stopping advantage, beyond known label-sample-size effects? Its distinguishing
controls would compare actual versus homogenized suffix expense and established
uniform versus stratified continuation at matched expenditure. The current
inputs fail that expense question. An interaction-count replay is executable
but has no established substantive distinction here. See [STOP](DECISION.md).

Further agent-method primary sections were checked for [EarlyEval](https://arxiv.org/html/2609.02783v1),
[FailFast–RestartSmart](https://arxiv.org/html/2608.03222v1),
[PrefixGuard](https://arxiv.org/html/2605.06455v1) and
[AgentStop](https://brave.com/research/files/AgentStop.pdf). Their outcome
prediction, alternate restart/patch-delivery interventions or backend signals
cannot be assumed available from an original saved suffix. Restart Economics
(SSRN 7538000), EET (2601.05777) and Active Evaluation of General Agents
(2601.07651) were discovery/abstract leads, not evidence from full methods.

## Artifact availability matters

StopLoss's pinned [example configuration](https://github.com/TIGER-AI-Lab/StopLoss/blob/c131d69d410d9f89d840981bc09bb1e6e9216cc8/configs/evaluation_example.json)
expects externally supplied scores/runs/judge packages. Its public tree and
training dataset do not supply evaluation predictions. Its cost code requires
call ledgers for some executors because trajectory exports omit cache writes.
Historical prices cannot replace absent usage. The calibration-audit README
also explicitly excludes row-level prediction intermediates. We did not infer
cheap access to monitor predictions from released weights, and did not evaluate
those monitors.
