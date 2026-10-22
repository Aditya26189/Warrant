# Assessment of the two received B1 reviewer packages

22 October 2026. **AMEND RETURNS / FRAME_BLOCKED / B2 NOT_AUTHORIZED.**

Both packages contain useful work and preserve the candidate universe. Neither
currently supplies a validated final eligibility frame. This assessment concerns
the received review artifacts and their source references; the exposed custodian
has not resumed scientific eligibility adjudication.

## Received originals and verification

The user identified the two archives as reviewer returns and clarified that the
earlier reply came from a fresh reviewer. That user-provided provenance is
preserved in [the custody receipt](ORIGINAL_RETURN_RECEIPTS.json). Original ZIP
bytes were committed at `b10c7a9bc4c00dc44dfe1c718f0f7cd22f7fd2ee` before
comparison. The labels A and B identify packages, not authenticated people.

| Package | SHA-256 | Bytes | Files |
| --- | --- | ---: | ---: |
| A: `B1_SUBSTANTIVE_REVIEW.zip` | `b2f0d658ebc0bf7e27d214029e1007327c363f4fd73a4c480833103e1eb8bcbb` | 443,565 | 10 |
| B: `ELIGIBILITY_REVIEWS.zip` | `b8d9352eb67b69765497b09818184f022127ffc79216495cea61cc096ef54fe7` | 458,398 | 375 |

Both ZIPs pass CRC, safe-path, unique-entry and frozen-byte checks. A's exact
manifest and its original `python -I B1_VERIFY_RETURN.py` pass. B has no supplied
hash manifest or executable verifier; its consolidated array, 372 individual
files and index were checked for exact agreement, and every payload is now
hash-bound in the custody receipt. This is custodian verification of received
bytes, not a cryptographic signature or proof of recipient independence.

Both returns preserve all 372 work IDs in the original inventory. A's rationales
explicitly preserve all 389 memberships; B does not separately enumerate member
IDs, but retains every original work, so its work projection has no dropped
membership owner. All cited evidence IDs resolve to the correct work, and all
provided source locators match the locked released evidence. A's 828 fact texts
and rationale passages match the original restricted facts without alterations.
All four component hash maps in A's source receipt match the authentic original
intake, base, semantic and recovery components.

## Same totals, different decisions

| Package | Included/eligible | Excluded | Unclear |
| --- | ---: | ---: | ---: |
| A | 6 | 8 | 358 |
| B | 6 | 8 | 358 |

| Package | Nominated work IDs |
| --- | --- |
| A | W0011, W0020, W0062, W0095, W0200, W0327 |
| B | W0020, W0200, W0208, W0327, W0339, W0352 |
| Common | W0020, W0200, W0327 |

There are 12 work-level disposition disagreements. They are recorded in
[MECHANICAL_REVIEW.json](MECHANICAL_REVIEW.json). The two eligible lists contain
nine distinct works altogether. Neither their union nor their intersection is
an approved sampling frame, and agreement on three works does not itself verify
their final eligibility.

Both returns correctly exclude the five exact all-version sentinels and preserve
the locked D01 SAME_WORK and D02 DISTINCT_WORKS identities. The other exclusions
and the methodological judgments differ:

| Work IDs | A | B | Matter requiring reviewer resolution |
| --- | --- | --- | --- |
| W0011, W0095 | INCLUDE | UNCLEAR | English component of the actual evaluation; distinguish the locked rule from an English-only/full-corpus characterization requirement. |
| W0062 | INCLUDE | UNCLEAR | Whether the described injection check is a qualifying evaluated binary input detector, and whether English evaluation is established. |
| W0021, W0067 | UNCLEAR | EXCLUDED | Explain withdrawal/version consequences under the locked rule separately from PDF access failure. |
| W0127, W0164, W0369 | EXCLUDE | UNCLEAR | Review/synthesis/proposal scope versus an original qualifying experiment; bounded evidence must not establish whole-work absence by omission. |
| W0208 | UNCLEAR | ELIGIBLE | A representation before the guard's verdict does not by itself locate the decision relative to the downstream target's answer. |
| W0290 | UNCLEAR | EXCLUDED | Tool-selection/provenance audit scope and whether a qualifying input-injection baseline exists elsewhere in the work. |
| W0339 | UNCLEAR | ELIGIBLE | Resolve the known journal DOI and publisher-VOR availability by cutoff before final preprint preference. |
| W0352 | UNCLEAR | ELIGIBLE | Establish the required methods in the selected ACL version, rather than combining version-specific passages without a bridge. |

These are reconciliation questions, not new custodian eligibility decisions.

## A: substantive reasoning with explicit limitations

A provides an individual assessment of all 828 method facts, four criterion
reviews per work, version reasoning and 1,302 controlled follow-up items. This
is substantially more auditable scientific reasoning than a status matrix alone.
Its facts and references pass the mechanical comparisons. Its six nominated
works each have four positive criterion judgments, but its own text qualifies
those nominations and does not grant final frame approval.

Three corrections or limits remain material:

1. Its `B1_VALIDATION.json` explicitly says `A04_freshness_attested: false`, and
   its README/reviewer ID explicitly disclaim being a fresh A04 reviewer. It
   states that prior assistant screening judgments are visible in that
   conversation. This conflicts with treating A itself as an attested fresh
   independent return; the custodian cannot silently change its declaration.
   The user statement about fresh-reviewer provenance is retained alongside it.
2. Its 1,302 requests cover 357 of 358 UNCLEAR works. W0352 has a cross-version
   issue in the rationale but no corresponding explicit follow-up request.
3. `B1_CASE_NOTES.md` incorrectly calls W0048 a withdrawn-latest-revision case.
   Its own JSON identifies W0048 as `arxiv:2505.12368`, selected v2. The actual
   two withdrawn/access cases in the controlled source records are W0021
   (`arxiv:2410.21337`) and W0067 (`arxiv:2508.02961`). This needs a dated
   correction, preserving the original note and JSON.

A also reports that it received loose components rather than the outer recovery
ZIP. Its component commitments match the originals locally; actual outer receipt
and execution in that reviewer context are not established by that match. No
new package needs to be engineered to describe this limitation accurately.

## B: complete packaging, insufficiently supported finality

B's per-work JSON files and index are internally consistent. The README calls
the review completed and independent, while retaining 358 UNCLEAR works. It has
no separate original-intake/delivery receipt or criterion-specific scientific
rationale file. Missing receipts are not proof that the user selected a
non-fresh reviewer; the precise independence claim remains bounded by the user
statement and the available artifacts.

The substantive problems are reproducible:

1. **Provider availability closely determines the criterion labels.** For all
   367 non-sentinel works, a simple mapping of provider annotations produces
   exactly 1,465 of B's 1,468 criterion values: `further_controlled_evidence_needed`
   true becomes UNCLEAR; false becomes MET. The only three differences concern
   W0290. All 938 provider-flagged gaps remain UNCLEAR, and all 527 positive MET
   cells match the other side of that mapping. This does not prove how the
   review was produced. It does mean the artifact needs criterion-specific
   evidence and reasoning to demonstrate scientific adjudication distinct from
   the provider's availability flags. Those flags were expressly not decisions.
2. **Selected-version dates have 145 provenance issues.** There are 120 arXiv
   revision-date mismatches and 25 day-precision claims unsupported by the
   supplied month-only ACL publication records. For example, W0011 selects v6
   but reports 2024-06-02, whereas the official v6 history is 2025-03-06. W0001
   reports an ACL version date of 2025-08-31 when the supplied primary record
   establishes August 2025 only. Month bounds may be used as explicitly labeled
   intervals; they must not be represented as observed publication days.
3. **First-public dates also need repair.** Seventeen rows report a first-public
   date later than an already documented arXiv release of the same work. For
   example, W0352 reports 2025-11-01 despite the supplied preprint history
   establishing 2025-05-08. These metadata problems do not automatically imply
   an out-of-window paper, but the returned fields do not mean what they claim.
4. **W0352 combines versions.** B selects the ACL publication, while four of its
   five cited method facts are bound to `arxiv:2505.06311v2`; only its timing fact
   is from the ACL PDF. No same-version confirmation or version-equivalence
   argument is supplied. This may be repairable, but it is not established by
   shared work identity alone.
5. **Specific decisions need method/policy reasoning.** W0208's cited timing
   fact describes the guard's verdict; W0339's selected preprint requires the
   known journal-VOR check; W0021/W0067 need a version-policy basis distinct from
   access-only exclusion. The W0069/W0325 reproduced-study issue is labeled
   `REPRODUCED_STUDY_SEPARATE_STUDY_UNIT` without a source-linked rationale
   resolving the paper/thesis overlap. None is silently repaired here.

All 145 selected-version and 17 first-public questions, with existing primary
bibliographic evidence IDs, are in
[REVIEWER_B_PROVENANCE_QUESTIONS.json](REVIEWER_B_PROVENANCE_QUESTIONS.json).
The [supplementary checks](SUPPLEMENTARY_CHECKS.json) record A's missing request
and note error. No FPR outcomes, counts or assurance classifications were used.

## Recommended next step

Request a correction/addendum from the existing reviewer responsible for B,
using [REVIEWER_B_CORRECTION_REQUEST.md](REVIEWER_B_CORRECTION_REQUEST.md) and the
provenance questions. That request contains no A decisions. Do not send this
comparative custodian report or A's judgments to a reviewer whose independent
review is to be preserved. Keep both original returns unchanged.

Ask A's provider to correct the mislabeled case and missing W0352 follow-up if
that advisory assessment is maintained. Its own freshness disclaimer means it
cannot silently become the required fresh return. Resolve any conflicting
intake declarations truthfully rather than fabricating a new attestation.

There is no reason to restart discovery or automatically launch another source
harvest for all 1,302 requests. First distinguish requirements already supported
by released facts from genuinely missing primary method/version evidence.
Specific surviving requests can then use the existing controlled-evidence path.

The full independently adjudicated frame remains incomplete. **FRAME_BLOCKED**
is appropriate. **FRAME_INSUFFICIENT** would be premature because the unresolved
works have not been shown ineligible. No paper draw, human assignment, B2,
production change or historical-decision comparison occurred.

## Checks and provenance

Original archives/receipt: `b10c7a9bc4c00dc44dfe1c718f0f7cd22f7fd2ee`.
Checker and eight negative controls: `1f347c36586b548453b57bb56f03ed520f3a9ec9`.
Clean-checkout mechanical output: `b2c91dbb1a2ffba3c92806472f86cb550607abcf`.

- Eight unit tests: PASS. They reject outer-hash drift, valid-CRC payload
  tampering, unsafe paths, other-work references and changed locators, and check
  revision dates, month precision and the availability-projection diagnostic.
- Ruff on the two added Python files: PASS.
- Original substantive-return verifier: PASS, exit 0.
- Both inventories, A's manifest, B's index/individual records, source receipts,
  fact text and source references: PASS within the stated scope.
- Both original reviewer ZIPs remain byte-identical. All 282 B1 files committed
  before this task remain byte-identical to `9608deda5e8c8573b36162fda8555a47801e0f92`;
  new additions are confined to this review-receipt directory. Five local
  document links, JSON/count/gate consistency, file sizes and whitespace pass.
- Date metadata, explicit request coverage and independence/finality are findings
  requiring the corrections above; an integrity PASS does not clear them.
- Unchanged production tests were not rerun. No production code was edited.

The outputs are receipts of this custodian audit, not a preregistration,
independent statistical review or publication-readiness decision.
