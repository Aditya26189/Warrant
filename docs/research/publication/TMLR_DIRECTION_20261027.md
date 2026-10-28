# TMLR direction assessment — 27 October 2026

Planning memo, not a protocol amendment, completed paper or readiness verdict.
The subsequent [paper prospectus](PAPER_PROSPECTUS.md) records the deeper
prior-art stress test and independently reproduced exact diagnostic. Read it
for the current contribution boundary and execution path.
The [28 October submission-route research](SUBMISSION_ROUTE_20261028.md)
identifies a separate controlled reproducibility candidate and checks its
public data availability; it does not amend the reporting pilot.
The user requested a publication direction and specifically asked to inspect
newly pushed branches. A successful `git fetch origin` confirmed the latest
remote tips available in this repository: main `c2e61a7` and
research/fpr-stage-a-20261017 `caa4dd8`. The research tip is already integrated
into main. The shared desktop checkout remains on older `b7de189`; this memo
is isolated on a branch from `c2e61a7`.

## Recommendation

Prioritize an empirical methods audit asking:

> What population-level false-positive conclusions are supported by the
> evaluation evidence reported for binary input prompt-injection detectors?

Provisional title: **From Measured False Positives to Population Assurance:
An Evidence Audit of Prompt-Injection Detectors**.

This is my assessment of the available evidence, conditional on the pilot
yielding a substantive finding. It is not an established novelty claim. The
strongest potential contribution is a reproducible link from each proposition
to its population, decision unit, threshold selection and evidence, with
source-verified examples of mechanisms that change the interpretation.

TMLR asks for convincing evidence supporting the claims and clear findings
of interest to its audience; a new algorithm is not required. That supports
considering an informative audit, but does not predict acceptance.
[Official acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html).

## What the previous work actually establishes

| Route | Current evidence | Publication judgment |
|---|---|---|
| Original activation probe | Frozen single-model/question-answering study, with disclosed test-scoring history and label/provenance limitations in the archived report | Useful foundation, but this review does not establish a sufficient contribution or generalization study for a probe paper |
| Sequential monitoring comparison | Historical discovery analyses and a proposed stronger study; the mentor packet retains baseline-faithfulness, attained-size and cost/cadence concerns | Conditional second candidate; needs its own feasibility decision and prospective evidence |
| Input-detector FPR evidence audit | Source audit, explicit claim taxonomy, retained retrieval frame and ongoing checked eligibility evidence | Preferred immediate direction because it asks a specific question tied to existing work; scientific outcomes are still absent |
| Grader-discovery engine | Closed bounded conventional-mutation study found no new omission; the report recommends stopping engine investment | Retain the negative artifact; no demonstrated method advantage supports making this the main paper |
| Broad Warrant system | Local software, statistical demonstrations and evidence replay infrastructure | Supporting artifact; the available evidence does not establish deployment effectiveness |

The latest [B1 status](../fpr_reporting/b1/B1_CURRENT_STATUS.md) points to
checkpoint 014: 27 works supported pointwise, 39 excluded and 306 UNCLEAR,
preserving 372 works and 389 source memberships. These are eligibility-progress
counts, **not results about reporting quality or false assurance**. The frame
remains incomplete, no papers have been drawn, and B2 outcomes are unavailable.
The report's verification checks are historical execution reports; this turn
did not rerun those suites or inspect every underlying source receipt.

The [native certification audit](../fpr_reporting/CERTIFY_AUDIT.md) and
[FPR-001](../fpr_reporting/issues/FPR-001-adaptive-bound.md) record a concrete
distinction: a fixed-budget threshold guarantee does not automatically justify
the smaller confidence bound returned after observing realized counts with ties.
For the preserved three-point witness the reported noncoverage is
`0.07630211515886068`, above the nominal `0.05`, while every selected population
FPR remains below the requested budget. This turn independently recomputed the
exact Decimal probability expression and matched the recorded value; it did
not independently verify the entire production implementation or proof.

This is an honest worked example of our own tool's limitation. It is neither
evidence that other papers make the error nor a new statistical theorem.
The issue remains open; this memo selects no repair and changes no runtime.

## Contribution and prior-art boundaries

Separate four propositions before interpreting any reported number:

- An observed sample rate describes those evaluated decisions.
- An operating target states an intended budget.
- A population confidence statement needs a valid method and its assumptions.
- A formal guarantee must be evaluated under its actual probability statement,
  which may differ from a high-probability population guarantee.

Missing information makes a claim unevaluable; it does not prove it false.
A descriptive zero count is not an assurance claim. A CP bound above a target
does not refute a different valid method, and exchangeability-based marginal
control must not be graded as though it asserted a different guarantee.

Known neighboring work substantially limits a generic reporting critique:

- [Tong, Feng and Li](https://pmc.ncbi.nlm.nih.gov/articles/PMC5804623/)
  already provide NP classification and high-probability type-I error control.
  Standard rank calibration and binomial sample floors are background.
- [ConformalGuard](https://arxiv.org/html/2610.14365v1) studies a calibration
  layer and legitimate-event false-positive control, with explicit limits.
  This assessment does not identify an error in it or treat it as a pilot case.
- [Bowyer et al.](https://proceedings.mlr.press/v267/bowyer25a.html) already
  address uncertainty failures in small LLM evaluations. Missing error bars
  alone are a weak contribution.
- [The CASCADE record-level audit](https://arxiv.org/abs/2604.17125) already
  analyzes decision conventions, corpus provenance and reproducibility for a
  specific system. Our candidate needs a distinct cross-paper question.

These official sources were reopened on 27 October. Read depth was selected
sections/search text for NP classification and ConformalGuard, and abstract
pages for Bowyer and CASCADE; this was not a new comprehensive literature audit.
The earlier [bounded gap review](../fpr_reporting/PRIOR_ART_GAP.md) retains
material inaccessible/partly inspected competitors. Global novelty is unknown.
Keep this targeted refresh outside the frozen selection frame; it adds no
candidate, exclusion, sentinel decision or outcome to B1.

## Work sequence and stopping conditions

1. Finish already authorized B1 source checking with the existing owners.
   Prioritize resolving exact missing evidence rather than creating more
   transfer packages. Preserve UNCLEAR when evidence does not resolve it.
   Do not trim the frame to completed or interesting-looking works.
2. Obtain the existing complete-frame approval, then execute only the
   prespecified draw and assignment under their applicable authorization.
   This memo does not authorize a draw or B2. Preserve the approved version,
   cutoff, exposure record and selection mechanism.
3. Follow the existing independent human-first / sealed assistant extraction
   sequence. Do not expose the human sheet before the assistant first pass is
   committed. Disclose the exposed-custodian B1 process; do not rename it a
   fresh independent review.
4. Apply the existing pilot feasibility criteria and human verification rules.
   An informative source-backed mechanism may justify designing a larger
   study. Sparse assurance claims, unreconstructable evidence, generic omitted
   intervals, or equivalent prior art may instead justify stopping this route.
   Do not weaken the criteria after seeing outcomes.
5. Only after a successful pilot, design and prospectively freeze a larger
   audit appropriate to the intended estimand and review budget. A small
   feasibility pilot does not estimate literature-wide prevalence. A fresh
   confirmatory sample cannot erase earlier exploratory exposure.

For any literature criticism, retain the exact proposition/version/locator,
decision unit, selected operating point, method and assumptions, independently
checked calculation and adjudication. Assess the method actually asserted.
Report inaccessible, ambiguous and not-reported evidence separately; avoid
selecting a single favorable operating point from a multi-arm paper.

## Proposed manuscript structure

1. Introduction: the inferential question and why it matters for detector
   evaluation; no headline about widespread failure before evidence exists.
2. Statistical setup: observed FPR, targets, confidence statements, formal
   guarantees, calibration/test separation and dependent units.
3. Audit design: bounded retrieval population, version policy, eligibility,
   sampling, claim taxonomy, missingness and reviewer exposure.
4. Results: generated sample flow and claim/evidence table, independently
   adjudicated examples, and disagreements. These sections remain unwritten
   until the authorized extractions exist.
5. Mechanisms and worked examples: source-specific findings, plus the clearly
   labeled synthetic Warrant counterexample if relevant and reviewed.
6. Practical reporting recommendations, limitations, artifact and AI-use
   disclosure. Suggestions must follow the actual findings.

An artifact should make each included proposition traceable to permitted source
locators and recomputable calculations, retaining immutable first passes and
adjudications. Source hashes establish integrity, not source authenticity or
statistical correctness. Avoid distributing third-party full texts without
checking redistribution rights. Double-blind packaging needs a separate
anonymous export: the ordinary repository identifies the authors.
[TMLR author guidance](https://jmlr.org/tmlr/author-guide.html).

## Immediate division of work

The active B1 work should remain with its current source/custodian workflow.
Codex can prepare the paper's definitions and evidence-to-claim map, review
mathematical distinctions, implement later authorized extraction validation,
generate tables from frozen records and draft results after they exist.
Human coauthors must own the research interpretation and the required private
source checks; another assistant's self-check is not that independent review.

The next useful milestone is a complete, approved frame and an interpretable
pilot decision. More product features, GPU extraction, a larger synthetic grid,
or a polished abstract cannot substitute for that evidence. If the audit fails
its gate, revisit the sequential-monitor feasibility question deliberately;
do not combine unrelated weak studies into one paper.

No ordinary ChatGPT conversation transcript was available in this turn. Context
was recovered from local research packets, repository history, coordination
posts and fetched remote branches, as the user clarified. No new experiment,
production change, merge, push or submission was performed.
