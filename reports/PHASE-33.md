# Phase 33 - A public export reaches a replayable certificate

The public examples now contain one complete synthetic handoff. A reader can
prepare a differently named scored export, replay that preparation, certify
the resulting `scored.csv`, and replay the certificate. Before this phase,
the public four-row export showed mapping only; the demo certified a separate
file. The installed-wheel suite had already exercised an internally generated
export, so this phase adds a retained public input and instructions rather
than a new certification algorithm. Decision 234 registered the derivation
and evidence boundary before the fixture was added.

## Question and scope

The question was whether the public example itself could show both replay
steps without implying that one proves the other. `examples/export_certifies.csv`
is derived row-for-row from the existing seeded synthetic
`examples/certifies.csv`. It renames the required columns and renders labels
as `error` and `ok`; the versioned mapping makes that meaning explicit and
declares independent rows. It retains `captured_at` as a source-only column.
No new detector was evaluated and the fixture is not an additional sample.

The prepared manifest binds the source bytes and mapping to the canonical
scored file. The certificate binds the ordered effective scored rows. The
two verifiers therefore answer different questions. A change to an excluded
source field invalidates preparation replay while the unmodified scored-row
certificate still replays. Neither replay authenticates the owner or proves
that labels and independent-row declarations are correct.

## Work and findings

- `6d76a1f` recorded Decision 234 before fixture generation. `1708c22`
  committed the synthetic export, mapping, and an integration regression. The
  test compares every exported row to `certifies.csv` and compares all fields
  used by certification after preparation. It runs the real CLI for prepare,
  verify-prepared, certify and verify, checks the manifest's effective-row
  digest against the certificate, and tests the excluded-column boundary.
- The new integration module passed 2/2 in 34.94 seconds, and Ruff passed.
  `fa6cbe7` added the executable PowerShell sequence to `examples/README.md`,
  linked it from `docs/INPUT.md`, and identified the earlier short demo as a
  separate-file historical run. The docs change also corrected an old
  `docs/INPUT.md` sentence: certify has bound effective rows since Decisions
  211-212, though it does not bind source-only columns or a preparation
  mapping. Documentation index, report and README-prose checks passed 142/142.
- On clean `fa6cbe7`, the exact four documented PowerShell commands ran in a
  new OS-temp directory. They reported `PREPARED`, preparation `VERIFIED`,
  certificate `VALID`, and certificate `VERIFIED`; all exited zero in 20
  seconds total. The fixture had 400 synthetic rows, 102 positive and 298
  negative; the certificate's false-positive upper bound was 0.0479 at the
  declared 0.05 budget. These are the **same synthetic rows and result** as
  the existing `certifies.csv` demonstration, not a replication.

## What this does not establish

The fixture is synthetic, derived from an existing example. It provides no
evidence about performance on a customer's detector, a bank's export, label
quality, independent sampling, deployment, or willingness to pay. The
source-to-row manifest is a checksum record, not an authenticated origin.
Certificate replay says nothing about the excluded `captured_at` values.
The example does not prove grouped preparation can be certified on a real
clustered dataset or that grouped release evaluation is supported. The
PowerShell run checks one local interpreter and dependency set, not every
platform. No scientific test set or frozen result artifact was regenerated.

## Open items

The October plan's next week-one gate includes a user dry run; none has
occurred. The discovery worksheet exists, but there is still no supplied
real scored export, label provenance, sampling-unit declaration, reviewer
packet, or named decision owner. A future external handoff must retain the
original export and mapping alongside the prepared package and certificate,
then ask the reviewer to replay both boundaries. Adding a generic adapter
or asserting demand from this synthetic workflow would not close that gate.

## Ledger

| Change or check | Evidence |
|---|---|
| Preregistration | Decision 234; `6d76a1f` |
| Public fixture and full CLI regression | `1708c22`; `tests/test_prepare_handoff_example.py` |
| Public commands and corrected row-binding prose | `fa6cbe7`; `examples/README.md`, `docs/INPUT.md` |
| Direct clean-source PowerShell handoff | `fa6cbe7`: PREPARED, VERIFIED, VALID, VERIFIED; 20 seconds, all exit 0 |
| Documentation checks | 142 passed; link, report and README-prose tests |
