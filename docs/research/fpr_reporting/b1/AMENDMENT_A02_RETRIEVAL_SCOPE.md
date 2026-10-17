# A02: arXiv and ACL Anthology discovery frame

Authorized by the user's 17 October 2026 decision. Recorded UTC: 2026-10-17T17:47:57.409228+00:00.
Source commit `d6c9b15cbc4c492846f6897c815ff418bf7ca661`. This is a prospective amendment before
metadata screening, eligibility decisions, candidate randomization or human
assignment. Raw source retrieval already occurred and is disclosed below;
this is not a retroactive preregistration or a trusted timestamp.

## Reason and scope

The originally approved OpenReview title query returned HTTP 200 with 100
records and declared 8,798 total results, exceeding the 500-per-query cap.
The partial response and original stop are preserved. The first 500 cannot
be substituted for a complete frame. No replacement OpenReview discovery
query, exact-mode experiment or ranking-based truncation is authorized.

For this ten-paper feasibility pilot, **primary discovery is arXiv plus ACL
Anthology only**. Reuse the already captured complete arXiv response set and
byte-identical ACL bulk export. Do not refresh either source. OpenReview may
be consulted solely for bibliographic verification of works independently
retrieved from those indexes; it must not add candidates. OpenReview discovery
records are EXCLUDED_FROM_SELECTION_FRAME. Their raw bytes, returned IDs,
request/response manifests and cap-failure history remain immutable.

The resulting frame is an **arXiv/ACL-retrieved frame**, not a representative
sample of all prompt-injection guardrail research. Omitted indexes, query
coverage, preprint/publication overlap and inaccessible versions limit inference.
Future findings must retain this feasibility-only scope and must not imply
literature prevalence or publication readiness.

## Preserved rules

The original approved frame plus A01 remains applicable except for removal of
OpenReview primary discovery. Keep the same title/abstract field predicate and
normalization, date window and version cutoff, original-research/domain rules,
version preference, canonical deduplication, locked sentinel exclusions,
outcome-blind eligibility, PDF-access policy, missingness treatment, no-replacement
rule, sampling seeds (20261017 and 20261018), Python 3.12.10, human blinding,
assurance-specific GO/STOP criteria and complete claim taxonomy.

Retain the maximum **500 unique works to screen** over the combined two-index
frame; do not truncate or sample before eligibility screening. Establish the
combined count through the fixed local metadata predicate/date boundary and
deduplication, not through domain-eligibility or outcome decisions. If the count
exceeds 500, report it and stop. Ambiguous metadata or duplicate identities that
materially prevent a valid count or outcome-blind selection retain the original
FRAME_BLOCKED rule. Unknown versions are handled as the original protocol says;
no dates are inferred from a local PDF file.

Freeze the parser/version before metadata screening. Retain every included,
excluded and uncertain record, raw-record provenance and dedup/version crosswalk.
A missing abstract is recorded, not evidence of no evaluation. Preserve complete
raw source bytes and a canonical metadata union if parsing succeeds. If a valid
complete frame has at least ten eligible unexposed works, freeze and hash it
before the original seeded ten-paper draw and six-paper human assignment. The
human worksheet contains only identifiers, versions and source links; outcome
cells remain blank. A new invalidating condition means FRAME_BLOCKED, not an
improvised relaxation.

## Preservation and verification

`PROTOCOL_LOCK_A02.json` is a new lock; the original `PROTOCOL_LOCK.json` is
unchanged. It binds the approved frame, A01, A02, sentinel inventory, original
lock, all retrieval/storage manifests, raw arXiv responses, ACL raw/chunk hashes,
excluded OpenReview response and existing commit references. ACL parts reconstruct
the exact captured gzip export; lossless packaging does not alter its bytes.
All historical evidence remains preserved. Partial OpenReview IDs cannot enter
the candidate frame via the mixed historical returned-ID index.

This amendment uses bibliographic provenance and a source-result cap failure,
not FPR findings, numerical paper results or claim classifications. There have
been no eligibility decisions or random draws before this amendment. A01's
conservative StepGuard exclusions remain in force without claiming an identity
mapping. FPR-001 remains OPEN and unchanged.

Authorization remains **B1 only**. B2, outcome/count/claim extraction, production
certification changes, frozen-artifact rewrites, push, merge and publication
remain unauthorized. Stop after B1 and await the next user decision.
