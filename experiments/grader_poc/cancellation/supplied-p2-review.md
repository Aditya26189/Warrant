## My review of Warrant P2 — 23 October 2026

Verdict: P2 delivered meaningful technical results, but it also confirms that Warrant has not demonstrated an advantage over conventional grader testing. I recommend closing P2 as a completed exploratory experiment, fixing the demonstrated cancellation-cleanup problem, and postponing further platform expansion.

The report is stronger than P0/P1 because it includes a second task, a comparison against ordinary testing methods, negative findings, and an actual Harbor cancellation test.

### 1. What P2 achieved

| Investigation              | Result                                                                       | My assessment                                           |
| -------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------- |
| Payments grader            | Faulty candidate accepted twice, 3/3 tests passed                            | Meaningful coverage-gap evidence                        |
| Payments semantic witness  | Zero-balance overdraft notification reproduced with service doubles          | Valid scoped counterexample; not end-to-end Kafka proof |
| Maximum-aggregation repair | Conditional mutant bypasses old repair; stronger regression suite rejects it | Shows why one assertion was insufficient                |
| Math grader                | No additional incorrect survivor detected                                    | Important negative result                               |
| Distributed deduplication  | Reference timed out during setup                                             | Inconclusive; not a semantic result                     |
| Harbor cancellation        | Owned Docker resources survived forced cancellation                          | Confirmed operational defect                            |

These are findings reported by the supplied P2 document. I have reviewed their technical interpretation, but I have not independently executed the archived experiments.

### 2. Strongest result: payments

The payments finding is reasonably persuasive.

Zero-balance boundary error

Correct condition

## `balance < 0`

No overdraft notification when the remaining balance is exactly zero.

Faulty mutation

## `balance <= 0`

Incorrectly generates an overdraft notification at zero.

The full original grader accepted the faulty worker. The controlled diagnostic demonstrated its semantic error using the exact collected worker bytes.

This supports a genuine grader-coverage concern. However, the counterexample was not reproduced through a complete Kafka/HTTP transaction. That matters for the strength of any public claim.

The report correctly distinguishes full-grader acceptance from the separate semantic witness. I would preserve that distinction.

### 3. The most important negative finding

The math experiment is particularly informative: ordinary mutation testing produced multiple mutants rejected by the existing suite, while Warrant's additional diagnostic found zero additional incorrect survivors.

That does not make the tool useless. It does weaken the argument for building a dedicated product around a novel discovery method.

The report also acknowledges that the payments omission was identifiable through direct assertion review before execution.

Therefore, Warrant has demonstrated careful counterexample validation—not superior defect discovery.

That distinction should drive the next investment decision.

### 4. The operational issue is now confirmed, not hypothetical

This is the most concerning engineering result from P2.

Actual Harbor cancellation tests left owned Docker containers, networks, volumes and images behind. The separate experimental harness subsequently removed them using ownership-checked cleanup.

Runner cleanup incomplete

I would treat this as a required fix before sustained unattended or shared-host execution, not another optional refinement.

The correct next engineering task is narrowly defined: implement and test scoped resource ownership and cleanup in the runner's actual Harbor cancellation workflow. Do not use global Docker pruning or assume terminating the Harbor process removes its delegated resources.

The existing evidence is sufficient to justify this correction without commissioning another research study.

### 5. The scientific limitations are appropriately disclosed

The report is unusually disciplined in distinguishing what was observed from what would be needed for generalization.

The unresolved issues are substantial:

- No independently blinded investigator.
- No measured active engineering time for matched methods.
- No evidence of lower cost than direct assertion review.
- No demonstrated transfer without new task-specific engineering.
- No independently reproduced end-to-end payment failure.
- Incomplete prospective property validation, particularly the payments rolling-worker property.
- No demonstrated generalization from the tested task set to other graders.

I would also flag the maximum-repair validation result: the conditional mutant produced 53 discovery disagreements but zero validation disagreements. That illustrates how strongly results depend on the selected value domain. It is a reason to improve held-out property design, not to interpret the zero as successful validation.

### 6. My gate decisions

| Gate                                        | Decision                       |
| ------------------------------------------- | ------------------------------ |
| P0/P1 technical demonstration               | PASS                           |
| Runner hardening in previously tested scope | PASS                           |
| P2 exploratory technical result             | PASS                           |
| Transfer to another task                    | PARTIAL PASS                   |
| Advantage over ordinary testing             | NOT DEMONSTRATED               |
| Harbor delegated cleanup                    | FAIL under tested cancellation |
| Publication-level methodology claim         | NOT READY                      |
| Product integration                         | NOT APPROVED                   |
| Independent scientific replication          | NOT ESTABLISHED                |

## What I recommend now

I would not start a large P3 project immediately.

First, preserve P2 unchanged and finish the narrow cancellation-cleanup correction. Then, if you want to invest further, the next scientific experiment should test a genuinely different proposition:

Can Warrant help another engineer audit a previously unfamiliar grader more reliably or with less effort than a simple checklist plus standard mutation testing?

That would require independent participants or a design that controls investigator carryover, frozen tasks and properties, genuinely held-out tests, and measured work effort. Without that evidence, additional architecture will increase implementation complexity without resolving the central research question.

There is also a reasonable alternative: retain the current system as a reproducible, optional audit tool and contribute individual regression tests to upstream projects after validating the corresponding end-to-end behaviors and following their contribution policies.

Final recommendation: Close P2 as a successful exploratory engineering study with a negative methodological-superiority result. Fix cancellation cleanup, preserve all evidence, and require a new explicit decision before further scientific expansion.

Keep this independent of the Warrant B1/A04 review and the separate unresolved `certify` statistical issue.