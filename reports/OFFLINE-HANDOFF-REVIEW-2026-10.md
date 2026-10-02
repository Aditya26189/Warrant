# Offline handoff and minimum-data review — 2 October 2026

## What was checked

This is a local review of the Phase 30 **synthetic** scored-export example and
the existing handoff contract. It is not an inspection of customer data, an
incumbent export, or a reviewer trial. The prepared example was created by the
executed [short demo](REPRODUCIBLE-DEMO-2026-10.md) from clean implementation
commit `87070b6`. Its two output files were inspected directly, and the
existing [input guide](../docs/INPUT.md) and
[evidence handoff map](../docs/EVIDENCE-HANDOFF.md) were checked for the files
another person must retain.

| Check | Observed result | Limit |
| --- | --- | --- |
| Prepared directory members | Exactly `scored.csv` and `manifest.json` in the inspected example. | The producer refuses an existing destination and writes the manifest last, but this check is one completed run, not a concurrent-writer or hostile-filesystem proof. |
| Canonical scored columns | `id,label,score,group,label_2`; four rows and two groups recorded in the manifest. | IDs, labels and groups can still be sensitive in real exports. |
| Excluded example column | `private_prompt` appears by **name** in `excluded_columns`; its synthetic note value is absent from both prepared files. | A column name itself may reveal information. This is not anonymization or a general secret scanner. |
| Replay inputs | `verify-prepared` needs the original export, mapping, and prepared directory. | The two-file prepared directory alone is not self-contained evidence of the source transformation. |
| Integrity | The [demo](REPRODUCIBLE-DEMO-2026-10.md) replayed the unchanged source and rejected a one-score edit with `MISMATCH` and exit code 1. | Hashes compare retained bytes; they do not authenticate the source owner or prove label quality. |

## Required handoff, by decision

For a reviewer to reproduce **preparation**, retain the original export and
versioned mapping alongside `scored.csv` and `manifest.json`. The originals
remain under the owner's control; `prepare` does not automatically copy them
into its output. Transfer of a real original may be impermissible even when
the canonical file omits prompt or transcript columns. If that is the case,
replay must occur in the owner's approved environment, or the reviewer must
accept a narrower claim. A hash by itself is not the missing original.

For **certification**, retain the canonical scored file and its certificate;
`warrant verify` recomputes the certificate on those effective rows. For a
**release** decision, the registered specification, development/holdout ID
lists, release contract, context, holdout scored file and evaluation record
belong together; retain the separate label-audit companion when one was run.
The [handoff map](../docs/EVIDENCE-HANDOFF.md) names exact roles and replay
commands. A certify threshold selected from the same rows is not the
preregistered release threshold.

## Compatibility and remaining evidence

The package declares Python `>=3.10`. The repository's CI workflow is
configured to exercise the installed wheel on Windows 3.10, the customer path
on Linux 3.11 and 3.12, and the full suite on Linux 3.12. This machine has
Python 3.12 only. The Phase 30 clean-clone suite and installed-wheel test
passed locally on 3.12; no result from the newly pushed remote CI run was
observed while writing this review. Configuration of a matrix is not a pass.

The next useful handoff test needs an owner-approved export, a current review
packet and a reviewer who can attempt replay without the author. Record which
file or instruction is missing and whether the current map already fixes it.
Do not add an archive command simply because four files must be carried:
the [packet design review](PACKET-DESIGN-REVIEW-2026-10.md) requires an observed
failure before that feature is justified.
