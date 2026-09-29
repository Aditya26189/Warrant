# Scoped release evidence

Use `warrant release` to measure a fixed detector operating point against
criteria declared before a holdout is evaluated. It is a local command-line
workflow. It does not approve deployment, certify regulatory compliance, or
establish that a model is safe.

The existing `certify`, `recheck` and `plan` commands remain available. Their
records are different schemas; a legacy warrant is not a release contract.

## Prepare the study

Choose the detector, threshold and acceptance criteria using development data.
Treat the system version as the version of the complete application: generator,
prompt, retrieval sources, tools and relevant configuration. Changing one should
change that version. Warrant checks the supplied version string; it cannot
inspect or authenticate the actual deployment.

Define what the positive label means and how reviewers apply it. Labels must
come from a reliable review process. An interval quantifies sampling uncertainty,
not mistakes in the rubric or reviewers' judgments.

Draw a fresh holdout from the declared target population. This first workflow
supports IID items only. A class-balanced challenge set, repeated messages from
one conversation, or many paraphrases of one question do not establish that
assumption. Grouped scored files are rejected. Do not erase the group column to
make them pass. Stratified or clustered designs need a different estimator.

Prepare two text files, one stable question ID per line:

- `development.txt`: every item used for development or selection.
- `holdout.txt`: every item in the fixed holdout, without scores or labels.

The lists must be nonempty, unique and disjoint. Holdout membership and size
are frozen. Adding rows after an inconclusive result, discarding hard rows or
renaming development items does not create a valid holdout. Warrant checks
exact IDs; near-duplicate content detection remains your responsibility.

## Register

Write `release-spec.json`. These are illustrative inputs, not recommended risk
tolerances or measured performance. Choose an appropriate future expiry.

```json
{
  "system_id": "support-assistant",
  "system_version": "application-commit-and-configuration-id",
  "detector_id": "answer-review-trigger",
  "detector_version": "detector-artifact-id",
  "scope": "English support answers for the declared product and traffic window",
  "positive_label": "answer fails the agreed support-answer rubric",
  "threshold": 0.5,
  "max_fpr": 0.05,
  "min_recall": 0.1,
  "alpha": 0.05,
  "expires_at": "2026-10-14T00:00:00Z",
  "data_origin": "customer",
  "sampling_assumption": "iid"
}
```

Use `data_origin: "synthetic"` for generated fixtures. Human summaries then
suppress metric values; the machine-readable record remains available for
software testing. The field is a declaration, not an automatic provenance test.

```shell
python warrant.py release register --spec release-spec.json --development-ids development.txt --holdout-ids holdout.txt --out release-contract.json
```

Keep the resulting contract with the reviewer before opening the holdout.
Existing files cannot be replaced by the command. A retained content hash
allows later comparison, but this local timestamp is not trusted notarisation.
Someone controlling every copy can rewrite them all.

## Evaluate once

Score and label every registered holdout item using the frozen system and rubric.
Use the [scored-file contract](INPUT.md): `id,label,score`, higher score means
more likely positive and the detector fires when `score >= threshold`.

Write `context.json` from the scorer's actual run metadata, containing exactly
`system_id`, `system_version`, `detector_id`, `detector_version`, `scope`, and
`positive_label`. Each must match the registered specification. Copying these
fields without checking the actual run would defeat the check's purpose.

```shell
python warrant.py release evaluate --contract release-contract.json --context context.json --input holdout-scores.csv --require-valid
```

This writes `release-contract.evaluation.json` beside the contract. The command
refuses a second evaluation at that location; use verification to replay the
existing result. Copying or deleting files does not reset the statistical
consequences of reusing a holdout. Coverage does not extend over arbitrary
repeated studies or selection among several contracts.

| Status | Meaning |
|---|---|
| VALID | Both registered acceptance bounds clear their limits on this evidence. |
| REFUSED | At least one bound did not clear: observed violation, inconclusive bound or missing denominator. This is not proof of a population violation. |
| STALE | Verification finds that the registered expiry has passed. |

New registrations use release protocol 2 (Codex-parallel decision 200,
[docs/decisions/CODEX-PARALLEL.md](decisions/CODEX-PARALLEL.md)). Protocol-1 records
remain verifiable with their original UNVALIDATED spelling for inconclusive or
missing evidence, explicitly labelled LEGACY in the output. A tested study is
not the same as an untested warrant-matrix cell.

FPR, recall, precision, flag rate and base rate each receive an exact two-sided
Clopper-Pearson interval with error allocation `alpha / 5`. Their simultaneous
coverage is at least `1 - alpha` under the declared assumptions. Each interval
names its denominator. Lift uses measured recall divided by measured flag rate;
its interval conservatively propagates the two bounds. Undefined values and
unbounded endpoints are explicit. There is no model-selection or lifetime
monitoring guarantee. See [DECISIONS 184](../DECISIONS.md).

A release verdict is conditional on this simultaneous interval protocol. The
separate `certify` workflow uses a one-sided FPR bound at alpha; release
allocates alpha across the interval family and both tails. Identical observed
counts can therefore clear certify and still be inconclusive in release. Read
the protocol and registered criteria with the status; the verdicts are not
interchangeable.

## Verify retained evidence

```shell
python warrant.py release verify --contract release-contract.json --context context.json --input holdout-scores.csv --require-valid
```

Verification checks the contract and evidence digests, recomputes the metrics
and decision, checks identity and applies current expiry. `--evidence` selects
a saved record in another location. Reordering the rows is permitted; changing
an ID, label or score changes the semantic data hash. Unused metadata columns
are outside that hash and are not part of the release inference. Optional
`label_2` is outside this evaluation hash but enters the separate label audit.

## Audit label sensitivity at the registered threshold

After an evaluation, run the separate audit on the **same complete holdout**.
You may add a `label_2` column with a second reviewer's judgments while leaving
the primary `id,label,score` values unchanged. The original release evaluation
does not change or adopt those judgments.

```shell
python warrant.py release label-audit --contract release-contract.json --context context.json --input holdout-scores.csv
python warrant.py release verify-label-audit --contract release-contract.json --context context.json --input holdout-scores.csv
```

The first command verifies the retained evaluation from the complete scored
input before writing `release-contract.label-audit.json` without replacement.
Use `--evidence` if the evaluation has been moved; `verify-label-audit` also
accepts `--audit` for a moved companion. The second command recomputes all
material audit fields. Both reject a changed primary score or label, or a
changed second-review value relative to the retained audit. The audit binds
the ordered effective rows, so restoring the same rows in a different order
requires restoring their original order for audit replay; the release
evaluation's own semantic hash remains order independent.

For a VALID release, the companion gives two separate counts: the first number
of flagged positives that, if actually clean, would invalidate either bound;
and the first number of unflagged negatives that, if actually positive, would
do so. It uses the same exact FPR and recall intervals and `alpha / 5` per
metric as the release evaluation. It shows each finite eligible pool and the
corrected bounds after one error. `null` means no failure within that one
pool. It does not compute combined errors. For a REFUSED or legacy UNVALIDATED
release, sensitivity is deliberately not computed. Optional `label_2` counts
observed disagreements in those two pools; it does not establish which label
is right, whether reviewers were blind, or a population error rate. A stale
release remains stale. The audit never changes VALID, REFUSED or expiry.
Its software manifest includes the effective-row digest implementation in
`intake/certify.py`; the original evaluation's source manifest is unchanged.

Exit codes: a completed measurement or verification returns zero by default;
`--require-valid` returns one for any current state other than VALID; malformed,
changed, unsupported or missing input returns two. An expired contract cannot
be used for a new evaluation.

The evidence includes source hashes, runtime versions and repository provenance
when available. Hashes are integrity checks against retained copies, not digital
signatures. Identifier hashes can reveal low-entropy IDs through guessing;
treat records as sensitive metadata. Keep customer files outside Git and share
them only through the customer's approved review process.

## Current limits

There is no authenticated reviewer sign-off, tenant boundary, SSO, deployment
attestation, automatic freshness detection, repeated-testing controller or
supported grouped-data estimator in this workflow. Small fixed-holdout files
may be incapable of supporting a demanding bound. The workflow reports that
absence of evidence rather than selecting easier criteria.

The preserved runtime paths have separate OPEN audit findings: legacy recheck
uses row-level bounds after dropping grouping, and the legacy mixture monitor
can report revocation before its actual mixture reaches the boundary. Neither
path is used by `release evaluate`, `release verify` or the label audit. See the
[claim audit](../reports/CLAIM-AUDIT-2026-09.md) before production reliance.
