# Phase 31 - Serialize routed drift responses and repair Windows onboarding

A drift response with a routing decision now has a JSON payload. Previously,
`DriftResponse.to_payload()` called a missing method on `RoutingDecision` and
raised `AttributeError`. The revocation trace carried a private serializer to
avoid that path. The matrix decision now supplies the same routing summary,
and the trace uses the public response method. The existing strict expected
failure is an ordinary passing regression. Decision 232 registered the shape
and boundary before the repair; Decision 179 remains the historical defect
record.

The README now gives PowerShell commands that work without activation or the
`&&` separator. The former inline Windows hint appeared on a Unix command
line and did not run in Windows PowerShell 5.1. This was observed in the
Arc180 fresh-run audit, not inferred from the README alone.

## Question and scope

The correctness question was whether a routed drift response could be
serialized through its public API without changing the read-only `drift/`
package or the frozen revocation result. The answer is yes for both a route
without an eligible warrant and a warrant-backed route in the regression. A
routing payload includes the envelope, profile, selected detector ID or null,
action, suspension, reason, considered detector/verdict pairs, and validation
queue keys. Claimed bounds remain on the enclosing drift response. The route
does not duplicate a warrant object or its claims.

The onboarding question was whether a Windows user could follow the Quickstart
with a fresh virtual environment. The new PowerShell block invokes the venv's
Python directly. The Unix command block remains available for Unix shells.

## Work and evidence

- `35eda46` appended Decision 232 before source changes. `6fc2187` added
  `RoutingDecision.to_payload()`, removed the duplicate trace serializer, and
  converted the strict xfail into a regression. `6eab9f7` documented the
  PowerShell path.
- Before the source repair,
  `python -m pytest -p no:cacheprovider -q tests/test_revocation_trace.py::test_a_routed_drift_response_serialises`
  failed with `AttributeError: 'RoutingDecision' object has no attribute
  'to_payload'`. The same command passed after the repair. The test checks
  both route states, JSON encoding, queue keys, and that claimed bounds occur
  only on the outer response.
- The focused batch covering revocation trace, matrix, drift response, demo
  beats, and gateway passed. Ruff passed on the changed Python files. On clean
  source `6fc2187`, `python scripts/smoke.py` returned 7/7 and
  `python scripts/verify.py --no-activations` returned 92/92 claim rows and
  25/25 frozen-score comparisons; the activation tier was explicitly skipped.
- README prose, docs-index and report tests passed after the PowerShell edit.
  The documented command sequence was run from a new remote clone in a new
  venv under Windows PowerShell 5.1. Clone, install, and both certify commands
  exited zero in 130.6 seconds. `certifies.csv` reported VALID, 400 items,
  threshold 0.864735 and FPR upper bound 0.0479 at budget 0.05.
  `refuses.csv` reported REFUSED because it had 37 independent negative units
  and needed at least 299 at budget 0.01. These are the synthetic examples,
  not a customer sample.

## What this does not establish

The serialization regression establishes a JSON representation of local
routing objects. It does not establish that a downstream service consumes it,
that a live revocation occurred, or that the frozen trace was re-measured. The
repair does not change the threshold, estimator, label, test split, or claim
table. The worktree lacks the ignored activation cache, so the local verifier
skip cannot be read as an activation replay. The fresh-clone Quickstart proves
that the two examples run in that Windows environment; it does not establish
that the broader workflow is usable by a bank, that another Python version
resolves the same dependencies, or that real labels are reliable. The remote
clone was the older published line, so its Quickstart execution validates the
commands and example behavior, while source tests validate the local repair.

## Open items

The product still needs an observed review packet, a permissioned scored
export, a named decision owner, and a repeatable customer decision as described
in `reports/BUILD-PLAN-2026-10.md` and `docs/PILOT-PROTOCOL.md`. No customer
conversation, production data, remote CI pass, or GPU re-extraction is claimed
here. Decision 232 closes the implementation defect from 179, not the other
open methodological and deployment limits in `docs/LIMITATIONS.md`. A future
consumer of routed response JSON should test its own schema expectations.

## Ledger

| Change or check | Evidence |
|---|---|
| Preregistration | Decision 232; `35eda46` |
| Routed-response source and regression | `6fc2187`; `tests/test_revocation_trace.py` |
| Windows Quickstart documentation | `6eab9f7`; `README.md` |
| Clean source smoke and available verifier | `6fc2187`: 7/7, 92/92, 25/25; activations skipped |
| Fresh PowerShell clone and examples | Local execution on 2026-10-04; 130.6 seconds, both certify commands exited zero |
