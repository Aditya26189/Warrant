# Phase 38 - Replaying an insufficient grouped export

The public export example now exercises an end-to-end refusal through the same
prepared file that a reviewer can replay. Its four rows represent two declared
conversation groups. At a 5% false-positive budget and 95% confidence, the
certificate refuses because there are only two independent units and the
zero-error bound would require at least 59 clean negative units. This is a
property of the small synthetic example and the registered statistical rule;
it is not an observed customer outcome or a new detector benchmark.

## Question and scope

The October plan's short-demo gate asks for a valid input, an unsupported
case and a tampered file, with synthetic status visible. The older short demo
used the four-row export for preparation but separate `certifies.csv` and
`refuses.csv` inputs for the two certificates. Phase 35 added a full prepared
valid handoff. This phase closes the parallel refusal path: prepare the
existing grouped export, verify its retained inputs, certify its own
`scored.csv`, and verify the resulting refusal record. Then alter an excluded
source note and verify the original preparation against the altered source.

No statistical formula, operating threshold, mapping rule or fixture labels
changed. No new adapter, product surface or customer workflow was inferred.
The implementation change is one public CLI regression test plus a documented
PowerShell walkthrough. The test belongs to the customer-only CI manifest and
ran in the previously created Python 3.12 environment with only the customer
requirements installed. The four-row fixture is explicitly synthetic.

## Work and observed result

Commit `2c511bc` added the test and the example walkthrough. The test invokes
the actual CLI subprocess for `prepare`, `verify-prepared`, `certify` and
`verify`, rather than calling an internal formatter. It asserts the refused
record's `status`, the two-unit/59-clean-unit reason, and that the record's
effective-row digest equals the preparation manifest's effective-row digest.
After one excluded source note changes, it asserts preparation replay fails
while certificate replay of the unchanged prepared rows succeeds. This
distinguishes the two integrity boundaries in executable form.

From clean commit `2c511bc`, the commands printed in
`examples/README.md` section 5 were executed in a new Windows OS-temp
directory. The status and process-exit sequence was:

| Operation | Observed status | Exit |
|---|---|---:|
| Prepare `examples/export_sample.csv` | `PREPARED` | 0 |
| Replay original source and mapping | `VERIFIED: prepared package matches retained inputs` | 0 |
| Certify prepared `scored.csv`, budget `0.05` | `WARRANT: REFUSED` | 0 |
| Verify refusal record against prepared rows | `VERIFIED: effective rows and material certificate fields recompute` | 0 |
| Change first excluded `synthetic example only` source note | File written | 0 |
| Replay changed source against original package | `MISMATCH: prepared package differs from retained inputs` | 1 |
| Verify original refusal against unchanged rows again | `VERIFIED: effective rows and material certificate fields recompute` | 0 |

The certificate output said `items 4 (2 positive, 2 negative)`, `units 2
groups`, base rate `0.5000`, and `only 2 independent units; need >= 59 clean
units to certify FPR<=0.05 at alpha=0.0500`. The wording about clean units
means clean **negative** independent units for this false-positive bound. The
source note was excluded from scored rows by the public mapping, so changing
it changes the source-byte boundary while leaving effective rows fixed. A
refusal is an ordinary recorded result and exits zero; a mismatch exits one.

The focused public handoff module passed three tests in 72.11 seconds in the
Python 3.12 customer-only environment; Ruff passed for the modified test.
The docs/intake regression batch passed 101 tests in 36.51 seconds. These
checks covered the added path and its adjacent documentation contract. The
last full clean-source suite was Phase 36's 2,215-test gate; Phase 37 and this
phase made no production-code changes, so a new full multi-hour run is not
necessary to interpret the new test. The clean-source documentation, inventory
and frozen-claim gates for this phase are recorded in the ledger below.

## What this does not establish

The source is a hand-written synthetic export. It does not show what a real
provider emits, whether one row per conversation is a correct sampling unit,
whether a reviewer agrees with any label, or whether the mapped score captures
a useful operational detector. Two declared groups are not sufficient to
estimate a useful operating point. The refusal is a correct response to the
declared tiny sample, not evidence that any real detector has an unacceptable
false-positive rate. The test has no external user, buyer or incumbent packet.

`verify-prepared` binds original source bytes, mapping, manifest and
normalized output; `verify` recomputes the certificate from effective scored
rows and material fields. Neither command authenticates a human reviewer or
proves that the labels and group meanings are true. The commands ran on one
Windows/Python environment from a source checkout. The test's customer-only
environment narrows dependency risk but does not demonstrate every supported
operating system or a customer's installation. The clean-source verifier does
not re-extract model activations; its frozen-score tier is a replay of retained
research artifacts.

## Open items

The October 14 demand gate remains open: five real conversations, two usable
permissioned exports and one named recurring decision have not been recorded.
A real team must supply source rows, score direction, positive-label meaning,
independent-unit declaration, label provenance, and the actual review decision
before a pilot can measure incremental value. A reviewer also needs the
configured incumbent packet for the same decision, including custom
evaluators, to determine whether this handoff adds anything. No synthetic
command can resolve that comparison.

The next engineering change should follow an observed import or replay defect
or a permissioned packet, rather than growing an adapter catalogue from the
example. The October 8 research refresh is a separate dated source check; a
search result will not substitute for a real buyer workflow. Keep any future
customer export out of Git unless its owner explicitly approves an appropriate
sanitized fixture and the repository's data-handling rules are satisfied.

## Ledger

| Change or check | Evidence |
|---|---|
| Public refusal walkthrough and regression | `2c511bc`; `examples/README.md` section 5; `tests/test_prepare_handoff_example.py` |
| Synthetic source and mapping | `examples/export_sample.csv`; `examples/export_mapping.json` |
| Exact PowerShell walkthrough from clean commit | `2c511bc`; seven statuses and exit codes shown above, including expected mismatch exit 1 |
| Focused customer-only test and lint | Three passed in 72.11 seconds; Ruff exit 0 |
| Adjacent documentation/intake regression | 101 passed in 36.51 seconds |
| Earlier full-source baseline | Phase 36, `reports/PHASE-36.md`, 2,215 passed |
| Clean documentation and inventory gate | Pending final clean commit and refresh |
| Clean smoke and available frozen verifier | Pending final clean commit |
