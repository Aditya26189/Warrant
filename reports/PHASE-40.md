# Phase 40 - A partial preparation marker is rejected

The preparation handoff now has a fault-injection regression for an
interrupted `manifest.json` write. The existing implementation writes
`scored.csv` first and the manifest as its final completion marker. The new
test forces an error after creating a one-byte manifest and checks that
`verify_prepared` classifies the package as malformed and that a retry cannot
replace the reserved destination. All 52 preparation tests passed in the
lightweight customer environment. No production code, artifact format or
certificate statistic changed in this phase.

## Question and scope

The October preparation milestone requires interrupted writes not to look
like complete packages, and existing tests covered missing files, unexpected
files, corrupt manifests and existing destinations separately. They did not
force the publication sequence to stop **while the final marker is being
written**. That is a distinct failure: both expected file names can exist,
but the marker bytes are incomplete. If verification treated it as a valid
changed package, an operator might mistake a publication failure for an
ordinary mismatch; if preparation retried into it, it could overwrite the
evidence of the failed attempt. This phase tests that exact state.

The audit read `controlplane/intake/prepare.py` and the adjacent
`tests/test_prepare.py` cases before changing anything. `prepare_export`
normalizes and validates the source before reserving the destination with
`mkdir()`. It writes `scored.csv` with exclusive creation, then the manifest
with exclusive creation. `verify_prepared` checks the directory and its two
regular-file members, rebuilds expected bytes from the retained source and
mapping, and validates a changed manifest before returning a mismatch. Those
are existing contracts; the new test covers one interruption boundary in
them. No new data model or broader claim of atomic directory publication is
introduced.

## Work and observed result

Commit `69224e1` adds one deterministic test. It uses the existing local
JSONL export fixture and mapping, then monkeypatches `Path.open` only for
`manifest.json` in exclusive-binary mode. The injected branch opens that
marker, writes the byte `{`, closes the file and raises an `OSError` with a
specific message. All other file opens, including the source and mapping
reads, use the original method. The test therefore reaches the real scored
write before the simulated marker failure.

The assertions cover four observable consequences. First, `prepare_export`
propagates the simulated I/O error. Second, the destination contains the
canonical scored file and a one-byte incomplete marker rather than a
completed manifest. Third, `verify_prepared` raises `InputError` identifying
the malformed prepared manifest; it does not return `True` or a valid-package
`False` mismatch. Fourth, another `prepare_export` call raises
`FileExistsError` and leaves the one-byte marker intact. That last check
proves this path does not silently overwrite or merge an interrupted package.

The test was run with the Phase 34 customer-only Python 3.12.10 virtual
environment containing NumPy, SciPy, PyYAML, pytest and the build/test tools,
without the research dependency stack. The whole `tests/test_prepare.py`
module passed: 52 tests in 7.97 seconds. Ruff passed on the changed module,
and `git diff --check` found no whitespace issue. The source CLI's separate
corrupt-manifest test already checks an exit-2 error path; this phase's new
case targets the write ordering and no-overwrite guarantee directly.

The unchanged synthetic input has two rows, one positive and one negative.
It is used only to make the preparation path run; no certification or
performance estimate is derived here. The partial marker is intentionally
invalid JSON, so its classification is unambiguous. The test checks disk
contents after the exception, not just the exception type.

## What this does not establish

The injected Python exception is a process-level failure. It does not model
power loss, filesystem cache reordering, network filesystem semantics,
multi-process races, storage faults in the scored-file write, or a malicious
actor changing package members between checks. The code does not call
`fsync`; this phase does not claim crash-durable publication after sudden
power removal. A directory containing both final file names is not by
itself evidence of a complete package; replay must validate its contents.

The regression also does not prove the retained source came from a trusted
owner, that its labels are correct, or that row/group independence is true.
Checksums and byte comparison are integrity and reproducibility tools, not
signatures. The test uses a local synthetic fixture in one Windows/Python
environment. It does not validate an actual customer's export, a reviewer
workflow or a published package installed on another operating system.

No model activations were regenerated, no held-out detector result was
rescored, and no full-source test-suite pass is claimed by the focused
52-test result. The generated inventory is a collection count only. The
clean-source verifier later in the ledger recomputes retained score metrics
but leaves the activation tier explicitly skipped. Those distinctions matter
because a production regression passing does not create scientific evidence
or demand evidence.

## Open items

The October plan's first supplied-export and demand gates are still waiting
for permissioned customer material, independently sourced labels, an
appropriate sampling-unit declaration, a named reviewer and a recurring
decision. A human dry run has not been observed. If a real environment
requires stronger crash durability or shared-filesystem operation, that
requirement needs to be specified and tested on its filesystem; this local
fault-injection test should not be stretched into such a promise. Do not add
filesystem complexity without a demonstrated deployment need.

The available next check is an offline reviewer exercise with the retained
source, mapping, prepared directory and certificate, using the documented
valid and refusal commands. A reviewer should independently explain why a
changed excluded source note invalidates preparation replay while leaving
certificate replay of unchanged effective rows valid. If no reviewer is
available, record the missing observation. The October 8 research refresh
can update the market hypothesis only with new dated primary-source evidence.

## Ledger

| Change or check | Evidence |
|---|---|
| Write-order contract audited | `controlplane/intake/prepare.py`, `prepare_export` and `verify_prepared` |
| Fault-injection regression | `69224e1`; `tests/test_prepare.py::test_interrupted_manifest_write_never_looks_prepared` |
| Focused customer-only module | Python 3.12.10, 52 passed in 7.97 seconds |
| Static checks | Ruff all checks passed; `git diff --check` exit 0 |
| Clean test inventory | `results/test_inventory.json` generated from clean `2f013e7`; 2,226 collected, execution not implied |
| Clean preparation regression | `33aba3e`; 52 passed in 7.62 seconds |
| Clean documentation and inventory gate | `33aba3e`; 157 passed, exit 0 |
| Clean smoke and available verifier | `33aba3e`; smoke 7/7, claim table 92/92, frozen scores 25/25; activation tier skipped with `--no-activations` |
