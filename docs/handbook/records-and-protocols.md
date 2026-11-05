# Records, protocols and compatibility

A record is a claim plus enough context to interpret and replay it. A JSON
file that merely contains a status is not sufficient.

## Record families

| Record | Question | Important retained material |
|---|---|---|
| Prepared export | Did the declared mapping produce these effective rows? | Source export, mapping, scored output and manifest |
| Certification | What did the native operating-point procedure return for this file and budget? | Effective-row identity, threshold, counts, method and limitations |
| Frontier | What does the declared budget grid produce? | Grid, adjusted levels, row identities and selection binding |
| Ordinary recheck | What does a fresh batch say about one retained certificate? | Exact source certificate, fresh rows and result |
| Chained recheck | What does a declared monitoring prefix establish? | Horizon, complete prefix, linked batches and current local head |
| Release contract | What study was fixed before holdout evaluation? | Identity, threshold, criteria, development IDs, holdout membership and expiry |
| Release evaluation | Did that fixed study clear its registered criteria? | Contract, scorer context, complete holdout and evaluation |
| Handoff | Can a supported preparation/certification package be replayed elsewhere? | Fixed member inventory, checksums and original source data |

The same word `VALID` can appear in different families. Its scope comes from
the schema, method and question rather than the word alone.

## Required interpretive information

A reviewer should be able to identify the positive condition, score direction,
threshold, population or sample design, independent unit, uncertainty method,
source rows and version. Missing information should reduce the strength of the
claim rather than be filled in from an unrelated current configuration.

For benchmark artifacts, source commit, config hash, seed and environment
metadata also matter. A source hash identifies committed code only when the
producing state was fully recorded. The [audit](claim-audit.md) preserves dirty
flags instead of converting them into clean-looking provenance.

## Protocol versions

Historical records must replay under their historical interpretation.
Changing grouped-boundary inference, the meaning of a status, a material digest
or the release acceptance protocol needs an explicit compatibility decision.

The current customer grouped-rate protocol can withhold useful uncertainty
by reporting a vacuous interval when the grouped percentile calculation
collapses. Historical records may retain earlier behavior. An arithmetic
replay of an old record does not upgrade its coverage.

Hard-negative issuance likewise distinguishes independent-item and group-any
protocols. Current routing/policy eligibility must inspect the required
protocol rather than accept an old row-binomial bound by status alone.

The [metric protocol implementation](../../controlplane/validation/metric_protocols.py)
and [specification](../../docs/SPEC.md) retain the detailed migration history.
The [release guide](../../docs/RELEASE.md) documents that workflow's separate
protocols.

## Counts and units

A metric's displayed `n` is not necessarily its statistical denominator.
Recall divides by positives, precision by flagged items, FPR by negatives and
flag rate by all rows. Groups can further change the independent-unit count.

Retain row counts and group counts separately. Do not combine a row-level
false-positive count with a group-level trial count to reconstruct an interval.
A group that contains any fired member is one group event even when several
rows fire.

## Identity and checksums

The implementation distinguishes effective-row evidence, raw files and
semantic material fields. Their hashes serve different purposes.

- A raw checksum identifies exact file bytes.
- Effective-row binding connects a calculation to parsed data.
- Linked records connect a presented history.
- A contract digest detects changes relative to a retained contract.

None authenticates the author if all copies can be replaced. Neither a local
timestamp nor a hash is a trusted timestamp or a digital signature.

## Local publication

Writers avoid silently replacing registered evidence and distinguish complete
publication from interrupted state. Chains require additional coordination so
two writers cannot both appear to continue the same local head successfully.

These are software-integrity guarantees within the local publication model.
They do not establish that no private fork exists elsewhere.

## Verification grades and exits

A replay can be VERIFIED, MISMATCH or UNVERIFIED according to the command and
record family. UNVERIFIED is not the same as proving a record false; evidence
may be missing or a legacy schema may lack the required binding.

Read-only replay commands use nonzero exits for mismatched or unverified
results. Ordinary scientific workflows can instead return a supported refusal
with exit zero. Automation must choose the command and explicit requirement
flag for its actual acceptance policy.

## Retention procedure

Retain the original input, declaration and record together. For selected
frontiers, retain the exact selection evidence. For chains, retain every
presented link and its batch, not just the final summary. For release, retain
the identity context and complete registered holdout.

Do not publish private source exports merely because a prepared file dropped
sensitive columns. The handoff's original source member can still contain them.
