# Findings and scientific discussion

This chapter separates observations, possible explanations and what would be
needed to test those explanations. Values link to the individual claim ledger;
shared methods and source limitations appear in the family catalog.

## Overview

| Question | Observation | Supported interpretation |
|---|---|---|
| Does the probe rank recorded answer errors? | [C001](claims.md#c001): AUROC 0.8256 | A within-envelope association under the recorded labels |
| Does ranking imply high operating recall? | Recall 0.0794, precision 0.8800, flag rate 0.0417 | Ranking and a restrictive threshold answer different questions |
| Does pooling survive added context? | Target AUROC: last token 0.8135, mean 0.5015, rolling maximum 0.5553 | The proposed rolling-maximum rescue did not hold in this transfer |
| Do recognizer configurations matter? | Stock and configured PII recognizers differ on authored challenges | Configuration coverage matters within this inventory |
| Is recall planning ordinary prevalence sizing? | The derivative and corrected plans differ from the superseded approach | Recall uncertainty must be propagated through missed-positive estimation |
| Is matching evidence sufficient? | 92 matching rows, with 15 direct dirty-source rows | Arithmetic agreement and source/scientific validity are distinct |

## Probe discrimination worked in the recorded envelope

The last-token probe has AUROC 0.8256 on the named held-out split, with the
interval retained in [C001](claims.md#c001). This supports a ranking association
between frozen prompt features and the project's answer-error labels.

The feature is the final real **prompt position before generation**, as the
[aggregation code](../../controlplane/detectors/aggregation.py) specifies.
It is not a post-answer representation of whether a particular response is
true. Its label comes from the recorded subsequent generation and matching rule.

Prompt states may contain information correlated with difficulty, familiarity
or likely behavior of a fixed generation procedure. That is a plausible
interpretation of supervised predictability, not an identified neural
truthfulness mechanism. Separating those explanations would require additional
interventions and independent confirmation.

## Good ranking did not give high recall at every cut

At its retained operating point the probe has recall 0.0794, precision
0.8800 and flag rate 0.0417 ([C002-C004](claims.md#c002)). The independently
checked frozen counts for that block are:

| Count | Value |
|---|---:|
| n rows | 600 |
| n positive | 277 |
| n negative | 323 |
| n flagged | 25 |
| true positives | 22 |
| false positives | 3 |

AUROC averages pair ordering across possible cuts. This operating point flags
only a restricted part of the stream. It can therefore concentrate positives
while missing many other positive rows. This explains the coexistence
arithmetically without requiring a software failure.

Whether that trade-off is useful requires an application workload, a recall
criterion and a cost of missed events. Those were not measured on customer
traffic.

The wider budget sweep illustrates trade-offs, but its largest-favorable-budget
headline is selected from an observed grid. The separate validation/test sweep
records useful split separation while retaining dirty-source provenance.
Neither is a newly collected confirmatory evaluation.

## The pooling hypothesis did not survive as predicted

The source-fitted last-token probe retains target AUROC 0.8135. Mean pooling
is near chance at 0.5015. Rolling maximum is 0.5553 and flags 0.5433 of
target rows ([C029-C032](claims.md#c029)).

The original motivation was that a local rolling window could retain signal
diluted by a global mean. The retained result does not establish a robust
rescue: the rolling-maximum representation is weak in this transfer and its
threshold behavior changes substantially.

Dilution, positional changes, feature-distribution changes and selection of
distractor extremes are possible mechanisms. The experiment does not isolate
them. A motivation in an old source comment is not evidence that the method
worked.

The target reuses original questions, answers and labels while changing feature
extraction context. It measures representation transfer, not fresh long-context
answer accuracy.

A stronger mechanism study would predeclare interventions on distractor length,
position and content, keep the source fit fixed, and confirm on independent
questions. That experiment was not performed here.

## Recognizer configuration helped on the authored PII inventory

The PII comparisons distinguish stock, enabled and custom-augmented
recognizers. A direct explanation is configuration/coverage mismatch: a
recognizer cannot reliably detect forms outside its configured behavior.

Custom patterns were informed by the base inventory. Their improvement does
not establish broad external validity or superiority to every current
upstream release. The companion variant set extends forms but shares design
choices with the original authors.

Positive enrichment also changes precision. These results are measurements
on constructed challenge distributions, not natural customer traffic.
See [F10](claim-families.md#f10).

## Correct recall sizing required the correct quantity

The earlier approach confused uncertainty in unflagged error prevalence with
uncertainty in recall. Recall depends on that prevalence, confirmed flagged
positives and the much larger unflagged pool.

Under the declared workload, [C056](claims.md#c056) records a derivative of
-4.6496. The unflagged-to-confirmed-positive ratio differs from the
unflagged-to-flagged-pool ratio ([C057-C058](claims.md#c057)). Interchanging
them misstates the amplification.

The corrected plans retain workload, assurance, discrete-planning and allocation
assumptions. Their interval coverage and design effect are simulation findings.
What worked was correcting the estimand and preserving the superseded result
as failure evidence. Real labeling cost and production coverage remain unmeasured.

## Repeated decisions needed a horizon-aware design

The monitoring simulations compare rules on the same label streams with
declared breach, cadence, change time and window. They distinguish a
per-recheck decision from a whole-horizon requirement.

Favorable chained cells are conditional on those scenarios and label supply.
A simulated share of one is not certainty on every future stream.

The poor historical capped-monitor cell belongs to the implementation studied
under Decision 187. It is not a measurement of the later repaired runtime.
That distinction is explicit in [C068](claims.md#c068).

## The evidence audit found a gap beyond arithmetic

The final [receipt](../../results/documentation_audit/20261105-final/audit.json)
finds 92 matching rows across 21
artifacts. Direct dirty-source flags occur in reconciliation, the
out-of-sample sweep and resplit policy results, affecting
15 rows.

All 25 independent frozen-score point-target
checks agree. Those targets directly back
19 current README point claims.
The remaining rows have their own reproduction boundaries. The target count
is not independent regeneration of the entire table.

Dirty provenance does not prove a result numerically false. It means that
the named commit cannot reconstruct the complete producing tree. Changing the
flag or re-recording old values under a clean later commit would hide that
limitation.

## A returned-bound interpretation failed a controlled check

The tied-score witness gives noncoverage approximately 0.076302 at nominal
0.05 for a general interpretation of the native adaptive returned U.
All selected risks in that example remain below the requested budget.

The diagnostic is useful because it distinguishes two propositions and
evaluates a finite probability directly. It does not prove a defect in other
methods or replace independent review of every native consumer.
[FPR-001](../../docs/research/fpr_reporting/issues/FPR-001-adaptive-bound.md)
remains open.

## The grader-discovery extension did not show transfer advantage

The frozen reserved-task study rejected every generated mutation under the
full existing graders and retained its accepted controls. The bounded method
found no new specification-backed omission.

A base-only view would have produced apparent survivors that the stronger
existing tests already rejected. That supports the value of those stronger
tests in those cases, not universal grader completeness.

Earlier controlled omission-and-repair demonstrations remain useful within
their scope. The later adverse result limits investment in a custom discovery
engine on the retained evidence.
See [the closing report](../../reports/GATE4-TRANSFER.md).

## Released-record accounting supported REPORT, not corrected ranks

The unscored-trial work distinguishes recorded zero, null reward, absent raw
file and exception in a pinned released-final-record corpus.

Uniform repetitions in its strict cohort make equal-task and pooled weighting
coincide algebraically. Native agreement is partly an eligibility condition.
Neither establishes that every released job reconciles.

Export differences do not reveal original retries or prove intentional
selection. Free completion changes the scoring target rather than recovering
official corrected rankings. The REPORT decision and pending source review
remain in the [retained report](../../results/unscored_trials/closeout-20261029/report/technical_report.md).

## The stopping-feedback project stopped before policy evaluation

The inspected sources did not establish the aligned expense and comparison
information required for its predeclared mechanism. No policy was fitted and
no policy effect was measured.

A token or interaction proxy could define another executable question. It
does not automatically answer the original expense question or establish a
distinct contribution. The result is a bounded
[feasibility STOP](../../agent-stopping-feedback-study/DECISION.md), not an
estimated zero policy effect.

## Overall discussion

A reproducible number is useful evidence only when its question, source,
unit, protocol and failure history remain attached. The project repeatedly
demonstrates that distinction, including where its own interpretations or
provenance are insufficient.

The supported contribution is an inspectable local toolkit and bounded
research record. A new neural architecture, universal safety certification,
production adoption and publication-level novelty are not established.
The [preprint](technical-report.md) presents the work at that scope.
