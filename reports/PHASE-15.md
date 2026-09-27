# Phase 15: missing seals cannot lower chain assurance

Local repair checkpoint, 25 September 2026. Continuation at the founder's request
on `fix/chain-integrity-policy`, based on the clean Phase 14 checkpoint `eb8becf`.

## Question and answer

Can deleting a modern record's seal make a modified record pass the clean gate
or allow continuation by treating it as legacy data?

Before this repair, yes. The new policy reports missing seals as **UNVERIFIED**,
prevents them from satisfying `clean` or `--require-clean`, and refuses their
continuation even with `--fork`. Legacy records remain readable for structural
inspection. Absence of a seal no longer claims anything about a record's age.
This is the bounded repair for audit R6, not proof of authenticity or production
readiness.

## Work completed

- Preregister decision 207, including the intentional compatibility change,
  before implementing it. Reproduce the verification bypass and continuation
  bypass both with and without `--fork` as failing tests on the prior code.
- Add `structurally_clean` and `integrity_status` to verification output.
  VERIFIED means record/chain checksum checks reproduce; UNVERIFIED means seal
  evidence is missing; FAILED means an integrity or malformed-data check failed.
  Structural findings still prevent clean assurance, even with valid checksums.
- Require nonempty input, full seal coverage and successful existing checks for
  `clean`. An empty direct API call is not called verified. Present-but-invalid
  seals remain failures, distinct from absent seals.
- Preserve ordinary read-only inspection, which exits 0 with its explicit
  result. `--require-clean` exits 1 on missing seals as well as findings, and
  its error names both counts and the integrity status.
- Refuse unsealed continuation without a compatibility override or silent
  resealing. Leave the records, head and publication intent unchanged when that
  continuation is refused. Existing eligibility failures still reject as before.
- Update source and installed regressions, machine-output documentation,
  terminology, troubleshooting and the case matrix. Modern structural fixtures
  now carry seals; a deliberately rewritten fixture recomputes its full seal
  to continue demonstrating the documented authentication limit.

## Findings during verification

The prerepair check failed all three focused cases: stripping the seal still
produced clean verification, and continuation succeeded both with and without
`--fork`. After implementation the initial policy suite passed all sixteen cases.
Additional tests cover empty API input and simultaneous missing/invalid seals.

The first surrounding batch had **145 passes and one failure**. A NaN outside
the chain block on an unsealed record was being reported as missing integrity
before the existing malformed-JSON diagnostic ran. The correction preserves the
full-record encoding check before the missing-seal refusal. The original test
assertion was retained; the policy and input-integrity batch then passed all
59 tests. No malformed data is admitted by preserving this diagnostic order.

The installed-distribution batch passed all 15 tests. After the diagnostic-order
correction, the installed seal-removal test was rerun against a freshly rebuilt
package: one passed, fourteen deselected. It checks a normal sealed record,
stripping and editing, inspection, strict verification, a copied warrant and
continuation with/without `--fork`, with retained bytes preserved.

Documentation, decision-integrity, packaging and case-matrix checks passed all
94 tests. The final Windows CI declaration and legacy-shaped inspection check
passed eleven tests. These overlapping batches are not additive coverage or a
full-suite result. Execution was local Windows Python 3.12.10; the customer
checks ran without torch, transformers, datasets, spaCy, sklearn, matplotlib or
Presidio. Remote platform/version jobs remain unobserved for this branch.

The corrected surrounding history batch then passed **all 146 tests**, exit 0,
including the source policy cases, existing seal/structure checks, revocation
precedence and concurrent-publication recovery. Its log is
`.venv/chain-integrity-policy-minimal-final.xml`. Final report-link and case-matrix
checks passed all 79 tests (exit 0); repository-wide configured lint and whitespace
checks also passed. No full-suite execution claim follows from those checks.

## What this does not establish

- A reproducible checksum is not an authenticated author, independently trusted
  timestamp or proof that the original contents were truthful. Consistent edits
  plus recomputed checksums still pass; a regression preserves this limitation.
- Integrity verification does not recompute statistics or recover omitted
  history. It cannot tell when a missing seal was removed or prove legacy age.
- The ordinary inspection command still exits 0 with a result. Automation that
  needs acceptance must use `--require-clean` or inspect `clean`; reading only
  `structurally_clean` deliberately requests less assurance.
- Genuine unsealed histories can no longer be continued. This is intentional:
  accepting them would also accept stripped modern records. No evidence file
  is destroyed or automatically resealed; inspect, recover a retained verified
  copy, or re-certify before beginning a new chain.
- Protected grouped-interval R2 and monitor R10 findings, malformed-input R7,
  PSI reference-size R8, operating-point handoff R9, and ordinary certification
  identity/expiry/input binding remain separate work. Unchained rechecks still
  ignore a revoked chain head. This phase does not change statistical formulas.
- There is still no supplied interview, design-partner, customer-label, paid-pilot
  or revenue evidence. Local correctness does not establish funding prospects.

## Open items: remaining work and the commercial gate

The next release needs integration of the accumulated repair branches and actual
full-suite/remote CI execution. The original shared checkout and other worktrees
remain intact; main is still `cc1904e`. This checkpoint is local and unpushed.
Do not label it a passed release gate.

The preregistered discovery gate remains eight to twelve conversations with
validation and compliance leads. If fewer than three of twelve can name a wrong
AI control claim with consequences, treat this as research. No outreach was sent.
If that gate passes, use the existing [pilot protocol](../docs/PILOT-PROTOCOL.md)
to test one recurring decision, a usable evidence handoff and willingness to pay.

## Source and reproduction ledger

- `d46da39`: decision 207 before implementation.
- `7526c77`: strict assurance, continuation refusal, contract and source tests.
- `1e019e3`: installed and legacy-inspection regressions with measured CI coverage.
- Local XML logs: `.venv/chain-integrity-policy-before.xml` (original failures),
  `chain-integrity-policy-after.xml` (initial policy suite),
  `chain-integrity-policy-minimal.xml` (first broader batch),
  `chain-integrity-policy-input-order.xml` (corrected diagnostics),
  `chain-integrity-policy-installed.xml` (installed batch),
  `chain-integrity-policy-installed-final.xml` (rebuilt installed regression),
  and `chain-integrity-policy-docs.xml` (documentation checks).

With customer dependencies plus pytest, setuptools and wheel:

```powershell
python -m pytest -o addopts= -q tests/test_chain_integrity_policy.py tests/test_chain_verify.py tests/test_chain_integrity.py tests/test_chain_record_seal.py tests/test_recheck_chain.py tests/test_recheck_chain_review.py tests/test_recheck_revocation_priority.py tests/test_chain_publication.py
python -m pytest -o addopts= -q tests/test_package_install.py
python -m ruff check controlplane/ scripts/ tests/ warrant.py
```

The new verification fields are additive, but the meaning of `clean` is
intentionally stricter. No scientific test set was reopened and no frozen
research measurements were regenerated. No new runtime dependency was added.
