# FPR-001 — Review the adaptive returned confidence bound

Status: **OPEN — LOCAL TRACKED ISSUE; NO PRODUCTION FIX AUTHORIZED**.
Recorded 17 October 2026, following the user's B1 approval message.

## Problem and preserved evidence

Native `certify_fpr` selects a negative-score order-statistic pivot for a fixed
requested budget, but returns CP U(realized k,n). With ties, realized k may be
below the design K. The smaller numerical value is named `fpr_upper_bound` in
the evidence artifact even though its general adaptive coverage is not justified.

Production source: `b7de189a62943b18d512b58df606621270b06c6b`.
Regression introduction: `c0ca9c1968132f79347b45c0aed005ebe13be46c`.
Audit clarification: `09a85089d2792ab3045ab7eab412c30764296a48`.
See the [completed audit](../CERTIFY_AUDIT.md) and
[unchanged regression](../../../../tests/test_certify_stage_a.py).

Exact IID witness: n=100, B=.05, delta=.05, K=1; probabilities for scores
0,1,2 are .95344, .017046, .029514. Put q1=.04656 and q2=.029514. Noncoverage
of the returned U occurs when M1<=1 or when M1>=2 and M2=0, where M1/M2 count
scores >=1/>=2. Its exact probability is

`100*q2*(1-q1)^99 + (1-q2)^100 = .0763021151588606840623422782651608181692763432159496127634294`.

All possible selected population FPRs are 0, q2 or q1, below B=.05. This witness
therefore challenges the returned numerical bound, not the requested-budget
guarantee. The audit preserves the standard fixed-budget argument and its
assumptions; it is not an independently reviewed implementation proof.

The user now reports independent mathematical reproduction of this witness.
Record that as **USER_REPORTED_ARITHMETIC_REPRODUCED** only. The user explicitly
did not verify the complete production implementation; independent source-level
and statistical review remain pending. No reviewer identity or broader sign-off
is inferred from this statement.

## Consumers to inspect before a repair

- `controlplane/validation/warrant_stats.py:134–139`: candidate selection,
  realized count and returned U.
- `controlplane/intake/certify.py:133–138,365–378`: evidence field, estimator
  description and confidence/bound language.
- `controlplane/intake/frontier.py:167` and `intake/render.py:195,470,485`:
  frontier/terminal propagation and presentation.
- Certificate/frontier verification and retained-record replay: determine which
  material fields/contracts depend on the old value. Review label-sensitivity
  and downstream API/policy use for additional assumptions. This is a review
  scope, not a claim that every listed consumer independently fails.

## Proposed investigation and completion criteria

1. Independently reproduce the native branches and exact witness from the
   cited source/test commits; review both coverage propositions under IID and
   grouped/tied score assumptions.
2. Inventory consumers and agree on a versioned evidence contract. Options
   include retaining the pivot/verdict while reporting design U(K,n), or
   reporting the budget guarantee and labeling realized CP as diagnostic.
   No option is selected or implemented by this issue.
3. Obtain separate authorization for behavioral/reporting changes. A future
   patch needs source-faithful regression/compatibility checks and independent
   statistical review appropriate to the final claim.
4. Preserve historical certificates and frozen results. Version any new
   semantics and disclose old-record limitations; do not silently replace an
   estimator or upgrade/rewrite an old artifact.

This local Git-tracked issue is not a remote GitHub issue or public disclosure.
Opening it changes no production code, certificate or statistical behavior.
