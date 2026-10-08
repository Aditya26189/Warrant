# Phase 49 — Incumbent review-workflow refresh, 8 October 2026

The October build plan calls for a research refresh and competitor workflow
comparison after the week-one technical gate. This phase revisited official
documentation for LangSmith, Braintrust, MLflow and Amazon Bedrock AgentCore.
The result narrows the product hypothesis: human review queues, annotated
labels, trace-derived datasets, aggregate classification metrics and result
exports are already documented elsewhere. Warrant should not claim those
features as a novel wedge or add a queue/dashboard merely to match a list of
features. This phase changes research prose only; it contains no new command,
test result, customer observation, detector measurement or revenue evidence.

## What the primary sources actually show

The [MLflow review-queue documentation](https://mlflow.org/docs/latest/genai/assessments/review-queues/)
describes named queues, common questions, assigned reviewers, shared completion
status and feedback or ground-truth answers written to traces. It labels the
feature experimental, says it was added in MLflow 3.14.0, and specifies that
individual assignment requires authentication. The
[feedback concepts](https://mlflow.org/docs/latest/genai/concepts/feedback/)
describe human, judge and code feedback sources, multiple annotators and
revision history. The
[evaluation-dataset guide](https://mlflow.org/docs/latest/genai/datasets/)
describes using historical traces or manually created examples. These are
documentation claims about available MLflow functionality, not an installation
or packet examined by this project. They directly undercut any Warrant pitch
centered on collecting human labels or organizing their review.

The [Braintrust experiment guide](https://www.braintrust.dev/docs/evaluate/interpret-results)
documents rows assigned for human review, unreviewed filters, scorer and
dataset metadata, and CSV/JSON export with an all-fields choice. It also names
API and CLI access to experiment results. The
[LangSmith evaluation-types guide](https://docs.langchain.com/langsmith/evaluation-types)
documents offline summary evaluators for whole-experiment metrics including
precision and recall. The
[AgentCore evaluation-types guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations-types.html)
documents ground-truth batch evaluation and aggregate results. These sources
show overlap with a generic "agent evals plus review" pitch. They do not show
that any vendor has run Warrant's exact fixed-budget statistical procedure on
a particular buyer's selected holdout, nor that the buyer needs that procedure.

The existing [incumbent comparison](INCUMBENT-PACKET-COMPARISON-2026-10.md)
now includes these facts and a more specific matched-packet request. The
request is for the configured incumbent queue or equivalent, label source and
revision history, exact exported row population, score polarity, threshold
selection, and the report actually used for sign-off. Warrant's prepared
scored rows and local handoff can then be compared on the *same* decision and
retained input, including a predeclared false-positive budget and refusal.
Without such a packet, whether Warrant adds value is UNKNOWN.

## Product decision from this refresh

No review UI, feedback database, native LangSmith/MLflow/Braintrust/AWS adapter,
or hosted service is justified by these pages alone. A vendor's documented
capability is neither a customer installation nor proof of product-market fit,
but it raises the bar for a new company. The narrow remaining hypothesis is
that a team with an existing scored, independently labelled export lacks an
independently replayable *decision* at a chosen false-alarm budget and that a
real reviewer would change or accelerate sign-off when Warrant supplies it.
Even that may be implementable with a custom evaluator in the team's current
tool; the configured packet test is the only way to tell. Warrant's local
checksum packet is not authenticated custody or a replacement for label and
sampling provenance.

The October plan's demand gate asks for real conversations, permissioned
exports and a named recurring decision. None is present in the repository.
With that gate open, the next executable work inside the repo is to keep the
synthetic first-run path reproducible and the evidence request precise, then
wait for an actual owner-permitted same-decision packet before building an
integration. The decision to pause speculative platform features follows the
plan's stopping rule; it is not an inference that no demand exists.

## Evidence ledger

| Question | Source read | Observation and limit |
| --- | --- | --- |
| Does an incumbent have human review queues? | Official MLflow review-queue guide, linked above | Yes, documented as experimental with stated authentication conditions. No customer configuration was inspected. |
| Does an incumbent distinguish label sources and revisions? | Official MLflow feedback concepts, linked above | Human, judge and code sources and collaborative revision metadata are documented. No independent-label workflow was observed. |
| Can an incumbent export or query experiment results? | Official Braintrust experiment guide, linked above | CSV/JSON all-fields export and API/CLI access are documented. Completeness of a buyer's chosen packet is unknown. |
| Can incumbents compute aggregate metrics or batch ground truth? | Official LangSmith and AgentCore guides, linked above | Summary evaluators and batch ground-truth evaluation are documented respectively. Their exact customer-selected statistical procedure is unknown. |
| What was edited here? | `reports/INCUMBENT-PACKET-COMPARISON-2026-10.md` and this report | Added a dated source-backed addendum and a concrete matched-packet request. No runtime or scientific artifact changed. |
| What technical gate applies? | `tests/test_reports.py`, `tests/test_docs_index.py`, `tests/test_claims.py`, `scripts/smoke.py`, `scripts/verify.py` | Run after the report/index are committed and the generated collection count is refreshed. Collection must not be reported as execution. |

## What this does not establish; open items

This is a desk review of public vendor documentation on 8 October 2026.
Documentation may change, and some features are experimental. No vendor
account, customer workspace, actual export, packet, independent reviewer or
buyer was supplied or examined. No product capability or performance was
benchmarked side by side. The report cannot identify a unique niche, certify
market demand, price the product, predict funding, or claim Warrant beats a
configured incumbent. A real customer may already have the exact uncertainty
and replay evidence needed, may lack valid labels entirely, or may not make a
recurring threshold decision. Those alternatives remain open and materially
change whether the venture hypothesis survives.

The first open action is a permissioned owner conversation about a recent
threshold or release decision, followed by the exact incumbent packet and
scored export if the owner permits their use. Record the sampling unit,
independent labels, selection history, reviewer interpretation and sign-off
change before asking for an adapter. A second independent team must repeat the
same gap before generalizing it into a product category. Until then, verified
software quality and source-backed competitor research should be described as
readiness for that test, not as commercial validation.
