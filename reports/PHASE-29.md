# Phase 29 - Make the legacy monitor's stopping decision match its mixture

The exported `FPRMonitor` now revokes only when its equal-weight mixture of
betting wealths reaches the configured boundary. Previously, a single large
component could trigger an early revocation even while the mixture remained
below the boundary. This repairs the concrete R10 decision error. It does not
establish that production labels satisfy the conditional assumptions needed
for a deployment-wide false-revocation claim, and the historical Decision 187
simulation remains a record of the old rule.

## Finding and scope

With `p0=0.05`, `alpha=0.05`, the default 40-bet grid, and two successive
false-positive labels, the largest component wealth is 110.25. The independent
mean across all components is 14.205849555361022, below the stopping boundary
20. The old `wealth` property checked the component maximum against
`log(1/alpha)+1` and returned 20. Consequently, `revoked` was true even though
the statistic described by its docstring had not crossed. The focused
regression reproduced this red behavior before the fix. The numbers here are
arithmetic on a synthetic two-label stream, not customer measurements or an
estimate of lifetime error probability.

Decision 226 was committed at `6e0eaa2` before code. It permits the narrow
repair in a formerly read-only path, without changing the customer recheck
chain or protected research scores. The founder directed continued correctness
work; leaving an exported false decision in place solely to preserve an old
simulation would not satisfy that instruction. The change to `CLAUDE.md` is in
the same commit as the code it permits.

## Method and behavior

Each fixed bet starts at wealth one and multiplies by
`1 + lambda * (x - p0)` for a Bernoulli label `x`. The monitored statistic is
the mean of all component wealths. The implementation now evaluates its log
with a maximum-shifted log-sum-exp expression, compares that *mixture log*
with `log(1/alpha)`, and caps the returned float at `1/alpha` only after the
mixture has crossed. The cap keeps serialized display wealth finite without
changing the crossing decision. On the counterexample, the monitor now reports
14.205849555361022 and does not revoke.

The state loader refuses a prior state that says it already revoked while the
reconstructed mixture is still below the boundary. Resuming it as active would
silently undo a recorded decision; accepting the old cap as mathematically
valid would preserve the defect. Such a record needs manual disposition. This
loader is not an integrity signature and cannot discover a historical alarm
that was acted on but never recorded in the state passed to it.

For a fixed grid and an adapted Bernoulli stream with conditional firing
probability at most `p0` at each step, each nonnegative component is a
supermartingale. A fixed equal-weight mixture is also a supermartingale, and
[Ville's inequality, as used in time-uniform supermartingale methods](https://arxiv.org/abs/1808.03204)
bounds the chance of **ever** crossing `1/alpha` by `alpha`. The premises are
stronger than a marginal FPR statement. They require an appropriate sequence
of labeled true negatives, a grid fixed before observing it, and uninterrupted
state across checks. Neither the tests nor committed artifacts prove those
premises for a customer's traffic. The newer chained recheck has a separate
construction and analysis; this repair does not borrow its evidence.

## Historical result boundary

`controlplane/economics/schedules.py` and
`results/recheck_schedules/comparison.json` retain Decision 187's five-rule
study. Its `monitor` rule explicitly reproduces the **old component-cap**
behavior; `monitor_uncapped` computes the mixture-only reference on the same
simulated streams. The current runtime matches that explicit uncapped branch
in focused stream tests. The schedule generator and its committed numbers were
not changed or rerun, so a citation to `rule=monitor` remains a historical
result and cannot be presented as a prospective current-monitor result. The
README claim label and current product docs say this explicitly. The
generator's old docstring still calls its `monitor` row the shipped class;
Claude has a standing ownership claim on that file, and a board handoff asks
its owner to relabel the source without rewriting Decision 187's data.

## Verification

| Check | Result |
|---|---|
| Counterexample before repair | Three new targeted regressions failed on the old implementation, including wealth 20 versus independent mixture 14.205849555361022 |
| Focused monitor and schedule suites | Passed after the fix; the historical capped rule remains separately tested |
| Ruff on changed Python files | Passed |
| Full tracked-file clone at `f2447b6` | Passed; 593 tracked files, smoke, preflight and full suite exited zero. The local gate ran 2,712.68 seconds for the full suite; [record](../results/clean_clone.json) committed at `0b50203` |
| Claim and frozen-score verifier | 92/92 claim rows and 25/25 frozen-score comparisons reproduced in that clone |
| Activation re-extraction | Not run; no model cache is claimed here |
| Remote CI and customer sampling assumptions | Unobserved |

The gate's activation tier was marked **SKIPPED**, not passed: ignored model
caches were absent from the tracked-only clone. Its first cleanup attempt hit a
Windows file lock after all checks finished. The exact named temporary clone
was then verified under the system temp directory and removed. The artifact
retains the original cleanup note so the record of the run is not rewritten.

## What this does not establish

The focused tests show agreement on selected deterministic and seeded streams.
They do not measure production false-revocation frequency or prove that a
customer's sampled true negatives obey the conditional-null assumption.
The source repair cannot retroactively validate a historical early revocation,
and the old Decision 187 schedule result cannot be reinterpreted as a current
runtime result. No research test set was rescored, and no Decision 187 artifact
was regenerated. Commercial validation remains absent: no customer interviews,
paid pilot, or revenue was provided for this phase.

## Open items

- Obtain real buyer/problem evidence under the stopping rule in
  `reports/STRATEGY-2026-09.md` before treating this code as a fundable company.
- Specify and audit how production true-negative labels are sampled and ordered
  before relying on the monitor's conditional-null guarantee.
- Have the owner of `controlplane/economics/schedules.py` relabel its historical
  rule docstring, preserving its frozen numbers and Decision 187 provenance.
- Observe remote CI separately; the local full clean-source gate is recorded
  above and does not imply a remote pass.

## Ledger

| Change | Evidence |
|---|---|
| Decision before code | `6e0eaa2`, Decision 226 |
| Focused code and regression commit | `bfd77a8`; targeted pytest and Ruff passed |
| Current-facing documentation | This report, README claim label, product state, code tour, release guide and testing guide |
| Inventory and full clone | Inventory at `f2447b6`; passing gate artifact at `0b50203` |
| Protected result status | Decision 187 artifact and frozen research scores unchanged |
