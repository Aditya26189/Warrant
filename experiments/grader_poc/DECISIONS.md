# Grader proof-of-concept decisions

## G001 — 2026-10-21: isolated, non-certifying experiment

The user's pasted review authorizes the bounded P0/P1 vertical slice, including ordinary implementation, dependencies, reruns and debugging. This experiment is on its own branch from production b7de189. It does not amend B1/A04, change certification, integrate a production CLI, or authorize publication, pushing, merging, or external messages. Source and results live under experiments/grader_poc; a closing phase report may also be added. This explicit scope supersedes the older probe-only project scope for this directory only.

Use small Python modules here for experimental logic, outside the shipped package. Keep runnable source, tests, configuration, candidate patches, and exact observed outcomes. No platform, SDK, or automatic repair system. Commit source before scientific runs; generated artifacts record the source SHA and dirty status. Research output is exact local observations, never an estimated population error rate.

## G002 — 2026-10-21: first target and predeclared gate

Pin Terminal-Bench 5a3f5dadcfa704f1741127ba64131d0b6217472b and Harbor 6c9d3d6609854375005a7b5c8f1906371d64c6ff. Use the complete session-window-debug task and original tests, including isolation hooks, with Harbor's local Docker backend. Disable optional Harbor telemetry. Record dependency/image identities and actual commands. No model API or paid compute.

Gate: the original task should reject (expected reward 0) and the supplied reference should accept (expected reward 1) under the unchanged verifier. These are prospective expectations, not results. Failures trigger diagnosis, not selective deletion of runs. Do not build a reusable framework before this gate. Docker and WSL setup is an explicitly recorded infrastructure cost.

## G003 — 2026-10-21: hypothesis and independent oracle

Investigate omission of aggregate maximum during merging, because inspected tests directly assert sum/count but no expected maximum. Create a plausible semantic mutant in an editable module of the supplied reference; never modify protected types, test runner, reward files, permissions, or test hooks. This is a deliberately constructed mutant: even success establishes a grading coverage gap, not that a real deployed agent produced it or that it is a novel vulnerability.

For the first partial oracle use one key, registered source, positive integer values, short finite traces, no firing or garbage collection, and event-time gaps away from equality boundaries. Independently derive connected sessions by sorting event times and joining adjacent times separated by less than the gap; ambiguous exact-gap cases are UNKNOWN. For each component compare start, end, count, sum and maximum. This is a partial correctness property, not a complete session semantics oracle. Hand-check small cases before candidate execution. Conflicts or out-of-domain inputs are UNKNOWN, never automatically invalid.

Keep candidate-grader execution separate from diagnostic trace execution. Preserve first failing traces and unsuccessful candidates. Reduce traces by deleting events and simplifying values/times while preserving domain and disagreement; report only the tested minimality condition. The fixed candidate's complete original-grader acceptance must be reproduced independently of the reduced trace.

## G004 — 2026-10-21: comparison and controls

After an accepted incorrect candidate is demonstrated, propose a small grader regression covering the independent aggregate property. Compare unchanged/repaired graders on original broken, reference, plausible incorrect, and independently coded equivalent-merge candidates. The equivalent candidate is a scoped legitimate control, not a proof of full program correctness. Include fresh executions; a failed control blocks a clean repair claim.

Count commands, execution duration, infrastructure/debugging time and human/assistant investigation effort. No baseline speedup can be claimed from post-hoc personal intuition. This vertical slice establishes no transferable automation advantage; compare a simple direct assertion as the honest baseline. Stop at an evidence packet or documented unsuccessful experiment; further product work requires another gate.
