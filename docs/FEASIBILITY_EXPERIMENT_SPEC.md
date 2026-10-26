# Grader auditing: bounded feasibility protocol

Status: the bounded study is closed after Gate1 calibration, the Gate2
conventional baseline and the subsequently authorized transfer to the three
reserved tasks. No confirmed omission was found by the frozen mutation method.
Coverage ranking was not built; the condition for an external finding packet
was not met. Human productivity, commercial value and broad effectiveness
remain unverified. See the closing transfer report for scope and limitations.

## Question and limits

Can a small automated audit find specification-backed grader omissions with
useful setup cost? A later human-effort claim additionally requires actual
human effort measurements. Agent elapsed time cannot substitute for those.
Payments remains an exposed development fixture and supplies no new-discovery
evidence. Keep this work separate from statistical certification and production.
No model inference, GPU or paid external service is required by this pilot.

The two-week investment limit is a stopping policy, not a delivery promise.
Runtime, engineering and sampling caps are declared in the experiment config;
they are operational choices, not economic or statistical guarantees.

## Correctness and outcomes

A confirmed false pass requires a completed unchanged-grader pass for candidate
M and a reproducible input x in declared D for which documented property P(M,x)
is false. A different reference output is insufficient. Specifications may
allow different ordering, tie breaking or internal state; unordered output
must preserve multiplicities where required. Invalid-input rejection can be
tested only where the task explicitly requires that behavior.

D is a domain; an input generator samples or enumerates a declared subset.
An oracle may be partial: out-of-domain inputs and unresolved specification
ambiguity produce abstention, not a failure. P must not be silently inferred
from the reference or from grader assertions. A reference may help compute a
specified unique result but cannot define unspecified behavior.

Keep independent dimensions: execution status (completed, invalid candidate,
timeout, apparatus error), grader verdict (pass/fail/unavailable), property
witness (found/not found/oracle error), and observed reference divergence.
Witness-search exhaustion is unresolved, never a proof of equivalence. The
absence of direct state reads or an uncovered branch is not a soundness proof.

A proposed repair must preserve the original grader tests, reject the same
counterexample, and accept the supplied reference and structurally varied
correct controls. State only preservation on those controls and validation
inputs, not all valid implementations. Count distinct requirement omissions,
not every mutant sharing an omission. No automatic patch submission.

## Gate1: completed calibration scope

Use one deterministic CPU function family. Pin source, dataset bytes, license,
calibration identity and held-out reservation rule before measuring outcomes.
Prepare only the calibration oracle/control; reserve held-out tasks from
identity/prompt metadata without inspecting or running their grader inputs or
reference bodies. Store and disclose incidental exposure. This is a held-out
pilot, not access-controlled or independent blinding.

The selected family is full HumanEvalPlus v0.1.10, using the pinned EvalPlus
evaluator, not just the weaker original HumanEval checks. Original HumanEval
now declares itself unmaintained; maintainer responsiveness for EvalPlus is
unverified. Both are established benchmarks with directly relevant prior work.
Discovering an omission would require a separate prior-report/stronger-test
check before calling it previously unknown.

HumanEval/0 is familiar calibration. The fixed SHA256 ranking reserves /87,
/57 and /18. Gate1 left their eligibility provisional; the later transfer
report records measured feasibility and remaining scope limits. No replacement after
observing results; any exclusion and its pre-outcome reason must be retained.
Task57's strict/weak monotonicity ambiguity must be resolved from authoritative
requirements or avoided with an explicitly narrower property, never decided
by copying reference/grader behavior.

The calibration domain uses exactly representable quarter-grid floats, with
positive thresholds, bounded list lengths and ranges from config.json. P uses
rational arithmetic over distinct positions; the alternative uses streaming
bisect-neighbor checks. Do not extend these observations to all floating inputs.
Grade both controls on every original base and plus input through the unchanged
upstream evaluator. Repeat in fresh processes and retain receipts and failures.

A calibration pass requires full grader acceptance, agreement with the scoped
independent property and the declared runtime target. It says nothing yet
about held-out feasibility, human effort savings or discovery advantage. The
human setup cap cannot be scored without human measurements; disclose agent
intervals separately, including acquisition and environment friction.

## Gate2: completed conventional calibration baseline

Decision G022 fixes a custom, source-preserving implementation of conventional
first-order mutations on calibration only. This is not an actual PIT/mutmut
comparison. Reuse the pinned full grader and the seeded Gate1 witness subset;
do not weaken tests or tune the pool after seeing results. Grade both controls
before candidates and the reference again afterward. Keep original base and
additional plus results separate; only a full-grader survivor is eligible for
a specification-backed omission claim. Preserve raw output, all candidates,
timeouts, invalid runs and undefined ratios. See the
[baseline report](../reports/GATE2-BASELINE.md) and its generated evidence.

Payments remains an existing exposed example; it was not rerun in this step.
No human review arm or direct-reference coverage comparison was performed.
Coverage ranking is not added merely because the conventional pool yields no
finding: changing order cannot make a fully rejected fixed pool produce a
survivor. The subsequent transfer results are reported separately below.

## Gates3-4: ordering omitted; frozen transfer completed

Decision G023 authorizes the original reserved identities with task-specific
properties, alternatives and generators committed before reference/test
extraction. The existing mutation generator, source order and caps are unchanged.
The monotonicity property abstains on equality and other ambiguous inputs;
full-grader acceptance does not settle those specification questions. All
prepared bytes and outcomes are retained in the
[transfer report](../reports/GATE4-TRANSFER.md). This is held out from method
tuning, not access-controlled or independent blinding. No ordering comparison
was added after the calibration failed to find a survivor.

The following requirements apply if any later study reopens a comparison;
they are not a claim that these omitted arms were run:

Use one candidate pool with identical operators, inputs, oracle, witness budgets
and total resource caps for C/D. C uses declared source order (and a predeclared
random-order check if needed); D changes only the ordering using missing/hit
line and branch information. Standard coverage data are not frequency counts.
New deletion operators belong in both arms or neither. A custom implementation
is a custom baseline, not a measured comparison with PIT/mutmut.

Direct reference coverage is diagnostic, outside the confirmed-defect table.
A manual review arm requires a human; an agent review must be named as such.
Count setup and oracle construction, all executions including unsuccessful
searches, human/agent intervention and apparatus failures. Without measured
human review, drop the human-productivity claim.

Freeze method/configuration on calibration before constructing held-out oracles
from prompts and requirements. Freeze each oracle/generator before assertion
inspection or diagnostic feedback. Then run all declared arms. Retain failed
controls and infeasible tasks; do not tune against held-out outcomes. A single
seed and this small sample support feasibility only. Any later multi-seed
study requires its own predeclared budgets. No-finding runs are valid results.

Do not add complexity if conventional mutation already suffices. No ordering
advantage means drop ordering. Repeated bespoke oracle work can justify ending
this pilot, but is not universal evidence against amortized repeated auditing.

## Gate5: condition not met; no external submission

Only a task-specification-backed finding supports a maintainer packet. Retain
the quoted requirement, pinned grader/candidate, witness, expected/observed
behavior and repair controls. Acceptance, publication, employment and willingness
to pay remain open. External messages, PR submission and publication require
the user's instruction; this protocol does not send anything.

## Source-of-record files

- [Decisions](../experiments/grader_poc/DECISIONS.md), G019-G024.
- [Frozen config](../experiments/grader_poc/feasibility/config.json).
- [Prompt-only reservation manifest](../experiments/grader_poc/feasibility/fixtures/selection.json).
- [Calibration property](../experiments/grader_poc/feasibility/calibration.py).
- [Closing Gate1 report](../reports/GATE1-FEASIBILITY.md).
- [Gate2 baseline config](../experiments/grader_poc/baseline/config.json).
- [Closing Gate2 report](../reports/GATE2-BASELINE.md).
- [Closing transfer study](../reports/GATE4-TRANSFER.md).

Primary references checked 26 October 2026: [EvalPlus source](https://github.com/evalplus/evalplus/tree/26d6d00bb1fd0fa37f39c99d5290da67891d1c5e),
[EvalPlus paper](https://arxiv.org/abs/2305.01210),
[HumanEval deprecation notice](https://github.com/openai/human-eval/tree/b9453e8f1865df0a0057a1383767caa400acfbcf),
[dataset license](https://github.com/evalplus/humanevalplus_release), and
[coverage semantics](https://coverage.readthedocs.io/en/latest/howitworks.html).
