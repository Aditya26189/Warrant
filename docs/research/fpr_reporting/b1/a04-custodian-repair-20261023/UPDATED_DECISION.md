# Updated B1 decision and completed repairs

23 October 2026. **Accept B's documented intake and use B as the primary return
for further scientific correction; retain A as advisory. FRAME_BLOCKED remains
the scientific gate.** No new discovery, replacement reviewer or new evidence
package is required merely to settle the administrative issues addressed here.

This implements the user's instruction to use judgment and update the work.
The [prospective repair scope](DECISION_AND_SCOPE.md) preserves A04. Original
reviewer decisions are not replaced by the exposed custodian's own eligibility
judgments. No selection or B2 is authorized by this decision.

## Correction to the previous provenance assessment

The original `INDEPENDENT_REVIEWER_B1_RETURN.zip` was already in Downloads.
The previous assessment inspected only the narrower `ELIGIBILITY_REVIEWS.zip`
export and missed this companion. It was incomplete about the availability of
B's intake and receipts. This dated addendum supersedes that part of
[the earlier assessment](../a04-reviewer-returns-20261022/TWO_REVIEW_ASSESSMENT.md);
the earlier files are preserved.

The companion SHA-256 is
`7466fa2253358b24917b93b24a4214e3b42103c7f7d994006a9efaa6ad7a43ed`.
It contains five files, including `REVIEWER_INTAKE.json`,
`EVIDENCE_RECEIPTS.json`, `CONTROLLED_REQUESTS_RETURN.json` and
`FREEZE_MANIFEST.json`. It was frozen before comparison at
`6ccb0f314dd38c20b5bce023672121e89bd3465e`.

The actual checks in [COMPANION_VALIDATION.json](COMPANION_VALIDATION.json) show:

- The eligibility array is byte-identical to B's previously frozen export.
- Every file matches the companion's manifest commitment.
- The original intake is marked ATTESTED at 2026-10-22T11:05:00Z, before the
  recorded review at 11:15:00Z. It declares a separate empty workspace,
  previously unseen assistant judgments, results and human outcome sheet, and
  no previously familiar works requiring reassignment.
- Its recorded out-of-band digest and declared verified transfer digest both
  equal the authentic original recovery ZIP's hash.
- All 827 receipts match the released fact hashes, source URLs, exact versions,
  raw-source commitments and locators. Every method fact cited by B has a
  matching receipt.
- Requests cover exactly the 358 UNCLEAR works and their 930 unresolved
  criterion items.

The 827 receipts cover 549 semantic plus 278 recovery facts. A's separate count
of 828 also includes one base procedural clause; B does not cite that clause.
This difference is not missing receipt coverage for a B citation.

Accept these as the original reviewer's recorded declarations, consistent with
the user's statement that the review was fresh. The custodian has verified
their presence, timing consistency, commitments and expected digest; personal
review history is not independently observable from file bytes. No replacement
attestation is requested or fabricated. B's claim of completed review does not
by itself settle scientific completeness or approve a sampling frame.

## Administrative corrections completed locally

[REPAIRED_B_WORKING_COPY.json](REPAIRED_B_WORKING_COPY.json) corrects 170 fields
across 145 works:

| Field | Corrected values |
| --- | ---: |
| Selected-version date | 145 |
| First-public date | 25 |

The version-date corrections address the 120 revision-date mismatches and 25
unsupported exact-day ACL dates previously identified. First-public corrections
address 17 dates later than known preprint releases and eight additional
unsupported day-level values in month-only records. For example, W0011's v6
date is 2025-03-06, while its first documented release remains 2024-06-02.
An August-only publisher record remains `2025-08`, rather than an invented day.

Every change in [ADMINISTRATIVE_CHANGE_LOG.json](ADMINISTRATIVE_CHANGE_LOG.json)
records the original value, corrected value, supported interval, primary
bibliographic evidence IDs and original-row hash. These are dates supported by
the already captured primary records, not a new source search. Earliest
documented release does not rule out an unknown earlier publisher version;
preferred-version uncertainties remain scientific review questions.

Only these two date fields change. All selected versions, paper/member IDs,
criterion judgments, evidence references and original eligibility dispositions
are preserved. Counts remain **6 ELIGIBLE, 8 EXCLUDED and 358 UNCLEAR** across
372 works/389 memberships. The repaired copy is explicitly marked as an
administrative working artifact with sampling unauthorized.

The old date checker now reports zero issues on the repaired copy. All five
generated payloads reproduce byte for byte from the frozen inputs. The source
commit is `6cbde7885e8425bc11dded628ab278ab79ec65a8`; the generated repairs were
committed at `d8936db3377e27fab2f35bfafd97af3236680e9a`.

For A, [the custodian note](CUSTODIAN_NOTE_A_CORRECTIONS.md) repairs the W0048
member/work cross-reference and adds the missing W0352 version-evidence
question. It is labeled as the custodian's own administrative note; A's original
requests, scientific decisions and freshness disclaimer remain unchanged.

## The remaining decision concerns scientific eligibility

The earlier scientific concerns remain. The observed agreement between B's
criterion labels and provider flags does not prove copying or lack of
independence. It does require explicit source-linked reasoning so that provider
availability is not silently treated as criterion satisfaction. W0208 timing,
W0339 publisher-version preference, W0352 same-version support, withdrawal/access
treatment and the W0069/W0325 study-unit issue remain specific questions.

[REMAINING_REVIEW_WORKLIST.json](REMAINING_REVIEW_WORKLIST.json) preserves B's
actual requests and attaches already released method references. It does not
automatically authorize a new source harvest or convert 930 unresolved items
into 930 independently validated source deficiencies. Much of the next work is
assessing existing evidence and explaining decisions.

Use [NEXT_REVIEW_REQUEST.md](NEXT_REVIEW_REQUEST.md) for one further substantive
pass by the **existing** B reviewer. Its administrative instructions supersede
the earlier request to send 145 date errors back for manual repair. The
scientific pass must preserve the English-component rule, consider qualifying
baselines and keep UNCLEAR when material evidence is missing. Do not send the
comparative A/B assessment or A's judgments to that reviewer.

The user has delegated routine judgment; the custodian has completed the
supported repairs without another permission cycle. A04 still assigns
scientific adjudication to an independent reviewer. Choosing a union or
intersection of nominations, changing statuses on the custodian's authority or
declaring a ten-paper frame complete would bypass that rule. No such action
has occurred. The study has not established FRAME_INSUFFICIENT either: unresolved
works have not been shown ineligible.

## Validation and preserved scope

- Ten new administrative-repair tests and eight existing provenance tests:
  **18 PASS**. Tests cover wrong-version/date substitution, conflicting primary
  dates, month uncertainty, overlapping date intervals, unchanged scientific
  fields and the distinction between an intake declaration and frame approval.
- Ruff for both new Python files: PASS.
- Full companion manifest, 827 source receipts, request foreign keys/coverage,
  original B byte identity and expected transfer digest: PASS.
- All five derived payloads: exact deterministic replay and manifest hashes PASS.
- Repaired copy against the previous date checker: zero issues.
- Field conservation: only the 170 logged date fields change; all reviewer
  scientific judgments, selected versions and original records are preserved.
- All 292 previously committed B1 files remain byte-identical to research
  baseline `8f625e73f5bc070b6faa5f4a3335020d8c738fa7`. Eight local document
  links, manifest commitments, JSON/count consistency, file sizes and whitespace
  checks pass. New work is confined to this dated repair directory.

All prior research artifacts, original protocols/locks, sentinels, source
snapshots, frozen outcomes and production behavior are preserved. No historical
custodian screening judgments were read or compared, no discovery refreshed,
no papers selected or assigned, and no outcome/claim extraction, B2, merge or
publication occurred. FPR-001 remains open and separate. Unchanged production
tests were not rerun for this research-only administrative repair.
