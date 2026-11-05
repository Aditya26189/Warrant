# Introduction: from a score to an evidence-backed decision

## The problem

A detector assigns a score to an item. A larger score may mean that an answer
is likely to be incorrect, a message contains an identifier, or another
declared positive condition holds. A score alone says neither how many clean
items will be flagged nor how many positive items will be missed.

Warrant makes the next question explicit: **what operating claim can the
available labelled sample support, under stated assumptions?** It records the
input, operating point, measured quantities, method and result. A refusal is a
useful answer when the evidence does not support the requested decision.

The positive condition must be defined for each task. In the TriviaQA research,
positive means the recorded answer failed the declared matching rule. In a PII
challenge, positive means the message contains an identifier. Those meanings
are not interchangeable.

## A small vocabulary

| Term | Meaning | Common mistake |
|---|---|---|
| Score | A detector's ordered output | Reading it as a calibrated probability |
| Label | The supplied reference judgment, usually 0 or 1 | Treating a recorded label as independently verified truth |
| Threshold | The cut at which the detector fires | Changing it after evaluation while keeping the old certificate |
| False-positive budget | A declared tolerated probability of flagging a clean item | Confusing it with the fraction of all items flagged |
| Calibration sample | Evidence used to choose or certify an operating point | Treating it as an untouched evaluation sample |
| Evaluation sample | Evidence used to describe performance of a fixed procedure | Reusing it for development and continuing to call it fresh |
| Group | A declared unit containing related rows | Counting paraphrases or repeated turns as independent trials |
| Warrant | A scoped local record about an operating decision and evidence | Reading it as an external safety approval |
| Envelope | The distributional context in which a result was measured | Assuming a model's result transfers to every input distribution |
| Refusal | The requested claim is unsupported under the implemented criteria | Treating it as a software crash |
| Replay | Recalculation from retained inputs | Mistaking agreement for authentication or label validation |
| Protocol | The versioned meaning of a calculation and record | Replaying old records with silently changed semantics |

## Follow one item through the system

A source export first becomes an explicit scored-file contract:
`id,label,score`, with optional grouping and second-review labels. The input
reader validates structure and values. Certification then uses clean-labelled
scores to evaluate a false-positive-budget decision. The metric builder
describes what the resulting threshold did on the labelled file.

The writer retains a record tied to the effective rows. Another reviewer can
supply that record and the same rows to the verifier. A changed score can be
detected even when the number of predicted positives is unchanged, because
the evidence binds rows rather than only aggregate counts.

Fresh scored batches can be checked later. A sequence of rechecks is a distinct
statistical design, not a collection of unrelated one-shot tests. The release
workflow is different again: it registers a fixed threshold and evaluation
criteria before a declared holdout is evaluated.

See [workflows](workflows.md) for those distinctions in executable form.

## Two kinds of exactness

Counting confirmed positive items in a fully reviewed flagged pool can be exact
for that pool. Estimating how many positive items were missed outside it is a
sampling problem. Similarly, computing a fraction of the supplied rows is
exact arithmetic; claiming that fraction describes a future population requires
sampling assumptions and uncertainty.

An interval addresses some sampling uncertainty. It does not automatically
address wrong labels, data leakage, an inappropriate unit of independence,
distribution shift or a selection procedure absent from its derivation.

This distinction is central to the [methods](methods.md), not an optional
qualification appended after a favorable result.

## Three software surfaces

The **customer path** is a local Python CLI with small numerical dependencies.
It consumes an existing scored file and does not need to load a language model.

The **research path** extracts or loads model features, fits probes, constructs
controlled evaluation sets, measures transfer and studies statistical procedures.
Its environment is deliberately larger and its conclusions are scoped to
particular experiments.

The **demonstration path** exercises policy, gate and drift behavior in authored
scenarios. It can establish what happened in those scenarios without measuring
a production population.

These surfaces share some types and methods. That does not make their evidence
interchangeable.

## What would make the project useful?

For an applied engineer, the practical value is a reproducible operating
decision with explicit refusal and retained inputs. For a researcher, it is a
record of assumptions, measurements, counterexamples and failure cases. For a
software reviewer, it is the separation of contracts, calculations,
publication, replay and tests.

The [findings](findings.md) explain what the retained work actually demonstrated.
The [limitations](limitations.md) explain which stronger conclusions would
require additional evidence.
