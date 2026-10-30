# Bounded REPORT closeout checklist

Starting audit: clean research `46961e9`; remote research and main were verified;
frozen gate still peels to `008aae9`. Canonical code is `92f162a`, post hoc code
`28edd34`. Original source/module hashes and existing replay/test receipts agree.

- [x] Identify committed artifacts versus cache-only inputs. Scientific outputs,
  normalized ledgers and source hashes are committed; complete raw records,
  configs/listings and original acquisition manifests/receipts remain external.
- [x] Verify interpretation counts from actual policy/pair/reconciliation tables.
  Closeout must explain conditioning, algebraic weighting equality and ambiguity
  subtypes rather than merely repeat the headline counts.
- [x] Package reviewed minimal inputs with source/derived hashes and licenses.
  See [dependency audit](CLOSEOUT_AUDIT.md) and [guide](REPRODUCING.md).
- [x] Demonstrate empty-cache numerical reproduction with old-cache reads blocked.
  Two actual runs passed; final source `93f6f34`, ten tables plus 31 scientific
  summary fields and the full post hoc summary matched; two guard probes blocked.
- [x] Generate a standalone exploratory report and prioritized pending human sheet.
  The [report](../../../results/unscored_trials/closeout-20261029/report/technical_report.md)
  is REPORT; all six cases' human fields remain PENDING.
- [x] Run focused checks and inspect the scoped contents/diff. Final scoped suite
  passed 199 tests; relevant smoke/claim/frozen-score checks passed. Activation
  checks were skipped. See [phase report](../../../reports/PHASE-UNSCORED-CLOSEOUT-20261029.md).
- [x] Publish reviewed closeout to the research branch and verify remote refs.
  Reviewed package `7a3b4f5` was pushed normally and verified remotely; main and
  the gate tag were unchanged. The [publication receipt](../../../results/unscored_trials/closeout-20261029/validation/publication.json)
  follows that verified package commit.

This is a closeout checklist, not a new research agenda. REPORT, original inputs,
historical outputs and scientific tags remain preserved. Human review and absent
original execution/importer evidence cannot be completed by this software task.
