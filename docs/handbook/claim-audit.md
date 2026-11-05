# How to read the claim investigation

## Question and coverage

For every current quantitative README-table row, the audit identifies the
retained value, exact artifact/selector, source metadata, calculation code,
data references and limits of interpretation.

The final [receipt](../../results/documentation_audit/20261105-final/audit.json)
covers 92 rows in 18 reviewed families across
21 artifacts. All retained values match.

A separate rank/count oracle agrees on all 25
frozen-score targets. Those targets directly back
19 current README point claims.
It does not independently reconstruct intervals, issuance controls, original
features or every historical simulation.

Direct dirty-source flags affect 15 rows:
C006-C007, C016-C019 and C020-C028. The original records are unchanged.

## Evidence levels

| Check | Establishes | Does not establish |
|---|---|---|
| File exists | Evidence is retained | Correct content |
| Selector resolves uniquely | One field is identified | Valid estimator |
| Table value matches | Agreement at stated precision | Independent reproduction |
| SHA-256 is recorded | Identity of retained bytes | Authenticated origin |
| Independent point oracle agrees | Separate ranking/count arithmetic agrees | Valid uncertainty or label truth |
| Original metric replay agrees | Supported blocks reproduce under their protocol | Original model execution or general coverage |
| Clean source is recorded | A named producing checkout was reported clean | Complete environment/weight identity |
| Scientific review | Assessment of assumptions and interpretation | Automatically supplied by the preceding checks |

## Contents of each entry

The [ledger](claims.md) retains the original value and interval, field,
checksum, source commit/config/dirty flag, writers and input references,
quantity-specific explanation, limitations and independent point evidence.

The [family catalog](claim-families.md) explains shared methods and origins.
The [qualitative register](qualitative-claims.md) separately investigates
software, research-status and prior verification statements.

This coverage is not described as verification of every sentence in the entire
historical repository.

## Dirty source

`DIRTY_SOURCE` means that the recorded commit does not describe the complete
producing working tree. An unrelated untracked file, a substantive source edit
or another uncommitted state could cause it. The record alone does not identify
which explanation applies.

The justified conclusion is source-state uncertainty. It is neither automatic
numerical falsity nor an invented clean lineage. Downstream uses also need
this context when their own producer was clean.

An archived original patch/environment could recover more. A new, clearly
identified clean study could supply new evidence. Neither is equivalent to
changing the old flag or re-recording old numbers under a later commit.

## Independent arithmetic

The point oracle uses sorted negative scores and binary-search pair counts for
tied AUROC, plus direct confusion counts at retained thresholds. It does not
obtain those points from the original AUROC/metric-builder functions.

This is independence of the calculation implementation, not an independent
investigator or dataset. The score loader still checks the recorded content
hash. The audit refuses an absent score hash.

An undefined precision is reported explicitly. A conventional stored zero
with an uncertainty warning is not promoted into independently measured
precision.

## Historical methods

Legacy grouped intervals remain reproducible under their old protocol. That
replay does not upgrade coverage. Old comments and plans may also preserve an
initial hypothesis superseded by a measured result.

The claim family and exact protocol therefore remain attached to each row.

## Failure behavior

The checks reject an empty table, unclassified artifact, ambiguous/missing
selector, changed value, invalid score evidence, point discrepancy or a source
change during artifact generation. Local link checks find missing files and
fragments.

They protect this audit's mechanical contract. Family explanations still need
scientific judgment.

## Reproduce

From clean committed source, choose a new output directory:

```shell
python scripts/audit_documentation.py --out ../warrant-audit-copy
```

For a read-only inspection and documentation link check:

```shell
python scripts/audit_documentation.py --links
```

Existing destinations are never replaced. The initial and final guarded
receipts are retained separately. [Developer instructions](developer-guide.md)
cover regeneration of the rendered pages.

No external label adjudication, model-weight reconstruction, production study,
complete novelty review or rerun of every historical experiment was performed.
Those limits bound the conclusions without discarding useful source evidence.
