# Incumbent evaluation-packet comparison — 2 October 2026

## Decision this research informs

The proposed October handoff is an independently replayable measurement of a
review trigger at a stated budget, prepared from a team's existing scored
export. An export button, human-review queue, reference answer, or custom
precision/recall scorer is already available elsewhere. Warrant should earn
use only when the team's **actual packet** leaves an important review decision
unanswered and the same source rows can be measured more defensibly.

This is a desk review of current vendor documentation, checked 2 October
2026. We have not opened an account, downloaded an incumbent export, inspected
a customer's review packet, or interviewed its owner. A missing item in a
documentation page is **unknown**, not proof that a product lacks it.

## Documented incumbent capabilities

| Product | Evidence the product documents | Consequence for Warrant's hypothesis | Still unverified in a real packet |
| --- | --- | --- | --- |
| LangSmith | Its experiment view shows inputs, outputs, reference outputs, feedback scores and metrics; the CSV download includes all columns regardless of view filters, with a 5,000-row download limit. [Experiment guide](https://docs.langchain.com/langsmith/analyze-an-experiment) Its datasets have versions and splits and can be exported. [Dataset guide](https://docs.langchain.com/langsmith/manage-datasets) | Generic CSV export, reference answers and dataset versioning are incumbent capabilities. | Whether the chosen export retains a distinct trigger score and independent outcome label per sampling unit, their provenance, a selected operating point and its uncertainty. The row limit matters only if the team's actual export crosses it. |
| Braintrust | The experiment record links scorers, dataset, saved parameters and model metadata; trace view shows expected values, scores and explanations; rows can be assigned for human review. Experiment results export as CSV or JSON, with an all-fields choice. [Results guide](https://www.braintrust.dev/docs/evaluate/interpret-results) Its cookbook gives a precision/recall scorer. [Cookbook](https://www.braintrust.dev/docs/cookbook/recipes/PrecisionRecall) | Human review, an all-fields export, metadata and classification metrics cannot be claimed as novel. | Which source, version and time each exported human label represents; whether its existing report already answers the review-trigger decision and is reproducible outside the service. |
| Amazon Bedrock AgentCore Evaluations | On-demand evaluation accepts expected responses, assertions and expected tool trajectories and can save CLI results as JSON. [Ground-truth guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/ground-truth-evaluations.html) Online results are JSON in CloudWatch, linked to trace/session IDs and exposed as metrics. [Results guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/results-and-output.html) | Do not claim that AgentCore lacks ground-truth support or exportable results. Its online evaluator has different reference availability: AWS says custom evaluators requiring ground-truth placeholders cannot run on live online traffic. | Whether the team's on-demand or online packet preserves an independently checked outcome, sampling frame, selection history and budget-specific uncertainty, or whether its current process already covers those. |
| SuccessKPI | Its September company release describes AI-ranked contact-center interactions, evidence shown with draft evaluation answers, human overrides and a shared data layer across quality workflows. [Company release](https://www.globenewswire.com/news-release/2026/09/03/3355947/0/en/three-successkpi-ai-releases-automate-quality-review-work-for-human-and-ai-agents-while-leaving-human-judgment-in-place.html) | This is especially close to the proposed support-review user. Alert selection, explanations and human sign-off are incumbent claims, not Warrant differentiators. | The release is marketing material, not a packet schema or independent product trial. Obtain the customer's actual quality report before claiming a statistical evidence gap. |
| Dataiku Agent Management | Its September announcement describes cross-platform agent inventory, risk records, certification status and scheduled tests. [Company announcement](https://www.dataiku.com/company/news/dataiku-agent-management-general-availability) | General agent governance and standing certification records are not open space. | The announced product's exact exports and statistical methods were not inspected. Its planned October availability is not evidence of one customer's adopted workflow. |

These are product-documented capabilities, not a hands-on feature benchmark.
The documentation does not provide a shared customer scenario or matched
dataset, so this table makes no superiority claim.

## The actual packet test

Request one permissioned, de-identified scored export **and** the report or
screenshots the team currently gives its reviewer. Ask the owner to define:

1. The concrete decision: what review budget or threshold changes, who signs
   off, and what evidence makes that person comfortable?
2. The unit of analysis and sampling frame: question, conversation, session,
   or customer; why rows are present; and which IDs group related examples.
3. For each row, the trigger score and its polarity, the independently
   determined outcome label and its meaning, their source/time/version, and
   any abstain or unreviewed state. A model-judge score is not silently a
   human-verified outcome.
4. Training, validation and test history: whether cases or users overlap;
   when threshold/model selection occurred; and whether the purported holdout
   has already influenced selection.
5. The current packet's budget-specific flag rate, recall, precision and
   uncertainty, plus exact inputs/config needed for another reviewer to
   recompute them. Record unavailable fields explicitly.

Run Warrant's existing intake on the permitted export only after the owner
confirms the mapping and rights. Preserve the original bytes and mapping;
show the owner both the incumbent packet and a replayed Warrant report for
the **same decision**. Record preparation time, objections, and what—if
anything—changed the sign-off. A synthetic fixture exercises software, not
this demand test.

## Outcome rule

If the incumbent packet already answers the decision, if the needed labels
or sampling units cannot be obtained, or if the reviewer declines the extra
artifact, do not build a native adapter just to demonstrate compatibility.
If two independent teams identify the same missing evidence and can provide
usable exports, implement the smallest adapter from one observed schema and
measure repeat use. The October [build plan](BUILD-PLAN-2026-10.md) retains
the time-boxed demand and pilot gates.

## 6 October addendum: LangSmith and Dataiku overlap more than an export button

The first table's LangSmith row describes experiments, rows and exports. Its
[evaluation-types guide](https://docs.langchain.com/langsmith/evaluation-types)
also documents programmable summary evaluators for experiment-level precision,
recall and custom aggregate statistics. That means an incumbent customer may
already compute the same basic classification rates inside its existing
workflow. The [Engine v2 announcement](https://www.langchain.com/blog/langsmith-engine-v2-redteam)
describes production-trace issue grouping, proactive red teaming and automated
testing of proposed fixes, with some features in private beta. The
[Custom Apps announcement](https://www.langchain.com/blog/langsmith-custom-apps)
describes shared review interfaces on LangSmith data for Plus and Enterprise.
These are company descriptions checked 6 October, not a hands-on trial or a
matched performance comparison.

Dataiku's [Agent Management product page](https://www.dataiku.com/product/agent-management)
describes scheduled tests and exportable risk records, but still says it will
be available in October 2026. The precise general-availability date and an
example customer's exported packet remain unknown. Do not turn a scheduled
launch into an observed installation.

For a LangSmith or Dataiku user, the packet test must now compare against the
**configured** incumbent workflow, not just its default UI: ask whether a
custom evaluator already bounds the team's predeclared false-positive budget,
whether the reviewer can reproduce it from retained labeled rows and selection
history, and whether that evidence changes a recurring sign-off. If the answer
is yes, the Warrant handoff has no demonstrated incremental value for that
team. If those fields are missing from an observed packet, record which ones
and why the reviewer needs them before building a native integration.

## 8 October addendum: review operations are incumbent features too

This is another documentation review, not a hands-on comparison or proof of a
new market niche. The [MLflow review-queue guide](https://mlflow.org/docs/latest/genai/assessments/review-queues/)
documents named queues, reviewer assignment, common questions, shared review
status, and answers attached to traces. It calls the feature experimental and
says it was added in MLflow 3.14.0. On a server without authentication,
individual reviewer assignment is unavailable. Its
[feedback model](https://mlflow.org/docs/latest/genai/concepts/feedback/)
records human, judge and code sources and describes multiple annotators and
revision history. Its
[evaluation-dataset guide](https://mlflow.org/docs/latest/genai/datasets/)
describes datasets from traces or manually supplied examples. Therefore a
review queue, label-source field, collaborative annotation or trace-to-dataset
path is not a defensible standalone Warrant differentiator. The docs do not
establish how any particular buyer configured or exported those fields.

[Braintrust's experiment guide](https://www.braintrust.dev/docs/evaluate/interpret-results)
now explicitly documents assigned and unreviewed rows, scorer and dataset
metadata, and CSV/JSON export with an all-fields option. Its API and CLI paths
also let a team fetch or query experiment results. The
[LangSmith evaluation-types guide](https://docs.langchain.com/langsmith/evaluation-types)
documents custom offline summary evaluators that calculate experiment-level
precision and recall. The
[AgentCore evaluation-types guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations-types.html)
documents batch evaluation with ground truth in session metadata and aggregate
results. These are documented capabilities, not evidence that an incumbent
does or does not implement Warrant's exact predeclared budget test or local
replay packet for one customer. A capable team may be able to implement a
similar test in its incumbent tool; that possibility remains UNKNOWN until a
configured same-decision packet is inspected.

The matched-packet request must now include the incumbent's *configured*
review queue or equivalent, not only a default experiment screenshot. Ask for
the reviewer assignment and completion record; the human versus judge label
source and any revision or disagreement history; the exact export columns and
row population; the score polarity and threshold-selection history; and the
report the decision owner actually signed. Compare those retained inputs with
Warrant's local replay of the **same** predeclared false-positive budget,
recall/precision, sampling unit and refusal condition. Time both preparation
and independent review, and record what changed the sign-off in the
reviewer's words if sharing is permitted. If the incumbent already supplies
the necessary bounded decision and replay, there is no observed wedge. If the
owner cannot produce independent labels or a defensible sample, the Warrant
packet cannot fix that missing evidence either.
