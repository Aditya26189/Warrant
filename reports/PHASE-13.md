# Phase 13: continue the handoff with bounded correctness repairs

Local repair checkpoint, 24 September 2026. Execution owner: Codex, following
the founder's explicit handoff that Claude is inactive. The September 17
integration is preserved; this work builds on the subsequent installed-package
repair at `d981fdc`, not on the old dirty shared checkout.

> Follow-up: local chain-publication repair R4 is recorded in
> [PHASE-14.md](PHASE-14.md). The results below remain the Phase 13 checkpoint.

## Question and answer

Can the two reproduced customer-path defects be repaired without replacing the
product or changing the scientific measurements?

Yes, within the tested scope. Grouped second-review agreement no longer receives
an unsupported population interval, and an inconclusive FPR warning no longer
hides an independent drift revocation. Retained inconsistent chain records are
diagnosed rather than rewritten. These are correctness repairs, not evidence of
demand, production readiness, or fundability.

The independent review requested in the old handoff is already recorded in
[PROJECT-REVIEW-2026-09-23.md](PROJECT-REVIEW-2026-09-23.md). Its findings supersede
the older conclusion that engineering was sufficiently complete. The older
recommendation to test demand before broad feature development remains valid.

## Work completed

### Grouped second-review evidence: decision 201, audit R5

- Both certification and recheck pass actual group IDs through to agreement
  analysis. Missing, blank or misaligned metadata fails explicitly.
- Preserve the observed pair table, raw agreement and descriptive sample kappa.
  Grouped records mark that description as `EXACT`, restricted to those observed
  pairs; it does not establish population agreement or label correctness.
- Population interval endpoints are null, with `interval_computed: false` and a
  reason. Both terminal renderers explain the withheld interval.
- Report reviewed pairs and distinct reviewed groups. Groups with no second
  review contribute no reviewed unit. Unequal review coverage does not cause
  implicit reweighting, and constant labels keep kappa undefined.
- Preserve the ungrouped bootstrap and JSON fields, every verdict and threshold,
  and primary-label sensitivity in whole groups. Grouped second-review disputes
  and their extrapolation remain withheld as before.
- Run the behavior through both the source CLI and the installed console entry
  point, including a wheel rebuilt from an sdist. Add the measured minimal-
  dependency regressions to customer CI.

Withholding the former interval is deliberate: repeated related rows do not
create independent evidence. A grouped estimator with validated coverage remains
future work. Consumers of grouped records must handle null interval endpoints.

### Independent revocation precedence: decision 205, audit R3

- The audit fixture first failed its new regression with overall `STALE` and
  drift `REVOKED`. It now returns overall `REVOKED`.
- Independent drift revocation outranks an inconclusive FPR warning or absent
  FPR evidence. Standalone established FPR breaches still revoke. In a chain,
  the existing distinction between one-file FPR evidence and the sequential
  statistic remains unchanged; drift is a separate decision.
- Continuation checks retained drift findings directly, including an old sealed
  record whose aggregate status incorrectly says `STALE` or `VALID`.
- Verification reports `revocation_status` for that contradiction and
  `continued_after_end` for a successor. Verification does not rewrite the old
  evidence or recompute its statistics.
- Regressions cover the audit fixture, missing/inconclusive/established FPR
  evidence, weaker warnings, CLI continuation with and without the sidecar,
  retained sealed contradictions and their successors.

No drift formula, threshold, null simulation, FPR estimator or protected source
file changed. A valid checksum can preserve an incorrect decision; internal
consistency is a separate check from content integrity.

## Validation ledger

The checks overlap and must not be added as independent coverage. These are local
Windows Python 3.12 checks, not a remote CI or full-suite claim.

| Check | Completed result | Scope |
|---|---|---|
| Grouped agreement and existing label sensitivity, source checkout | 83 passed, exit 0 | Both intake paths and unchanged primary-label calculations |
| Grouped/label sensitivity plus built-distribution checks, minimal environment | 95 passed, exit 0 | Customer dependencies and build/test tools only |
| Surrounding intake, recheck, chain, release CLI and documentation checks after R5 | 187 passed, exit 0 | Neighboring behavior before the R3 change |
| New revocation regressions after repair | 14 passed, exit 0 | Pre-repair run first reproduced the status failure |
| Revocation, recheck and chain-verification suites, minimal environment | 79 passed, exit 0 | New and existing lifecycle checks after R3 |
| Final built-distribution, grouped-agreement and label-sensitivity batch after R3 | 96 passed, exit 0 | Minimal environment; both repairs through the real installed console |
| Repository-wide configured lint | Passed | Runtime, scripts and tests |
| Closing documentation, decision-integrity and packaging checks | 82 passed, exit 0 | Links, scoped decisions and declared CI suites |

No research test set was rescored and no frozen scientific output was
regenerated. Inventory collection is reported as collection, not passing
execution. Final collection at clean source
`62cb61af206f23795da485ccee4ee9efe20f1236` recorded 1933 tests, up from 1916 at
the R5 checkpoint. The subsequent claim, inventory and README-prose check batch
passed all 21 tests (exit 0). Full-suite execution and remote CI were not rerun
for this branch.

## What this does not establish

- No interviews, design partners, customer labels, paid pilots or revenue were
  supplied or produced. No outreach was sent.
- No global enterprise deployment, operational load capacity, regulatory
  acceptance, general statistical coverage or investment outcome was validated.
- Null grouped agreement intervals do not repair the separate grouped
  recall/precision interval defect R2.
- Correct precedence does not repair PSI reference-size calibration R8,
  concurrent chain publication R4, seal-removal policy R6 or malformed inputs R7.
- A retained old record can be checked, but an old sidecar alone contains no
  hidden drift finding to recover. Missing/pruned records and deliberately
  rewritten checksums remain outside this local integrity guarantee.
- A fresh unchained recheck can still ignore a revoked chain head. The coherent
  identity/lifecycle contract requested in the handoff remains separate work.

## Next work and the commercial gate

Engineering should continue with transactional chain publication and recovery,
strict integrity policy, malformed-input handling, reference-size calibration
and operating-point binding. Protected grouped-interval and legacy-monitor
repairs require their specified methodological review. The current code should
not be described as production-ready while these findings remain open.

The founder's next commercial task remains the preregistered eight to twelve
conversations with model-validation and compliance leads. Preserve the stopping
rule: if fewer than three of twelve can identify a wrong AI control claim that
had consequences for someone, treat the project as research. Do not replace
that test with more features or reinterpret a hypothetical use case as a buyer.
If it passes, test one recurring decision, one evidence handoff and willingness
to pay, using the existing [pilot protocol](../docs/PILOT-PROTOCOL.md).

## Source and reproduction ledger

- `3dd5c27`: grouped agreement primitive and fixed-seed compatibility checks.
- `8531bf2`: both customer paths, renderers, tests and contracts.
- `62b1f50`: installed grouped-review checks and minimal-dependency CI coverage.
- `f26ac42`: generated collection inventory after R5.
- `3ae479e`: decision 205, recorded before implementation.
- `71119d2`: independent revocation precedence and retained-history checks.
- `6c835c6`: installed lifecycle regression and measured CI expansion.

From the repair checkout, using its declared dependencies:

```powershell
python -m pytest -o addopts= -q tests/test_grouped_agreement.py tests/test_label_sensitivity.py tests/test_recheck_label_sensitivity.py tests/test_package_install.py
python -m pytest -o addopts= -q tests/test_recheck_revocation_priority.py tests/test_chain_verify.py tests/test_recheck.py tests/test_recheck_groups.py tests/test_recheck_chain.py tests/test_recheck_chain_review.py
python -m ruff check controlplane/ scripts/ tests/ warrant.py
```

The installed tests build in temporary copies and use the running interpreter's
dependencies. Run them under a minimal customer environment to verify the
dependency boundary, rather than inferring it from a research environment.
Remote Linux/Python-version jobs are configured but have not been observed here.

The original shared checkout and older partial worktrees remain intact. Changes
are on `fix/recheck-revocation-priority`, which includes the grouped-review and
installed-package work as ancestors. Local `main` remains at `cc1904e`; this
checkpoint has not been merged into main or pushed. A full integration gate is
still required before presenting this branch as the next release.
