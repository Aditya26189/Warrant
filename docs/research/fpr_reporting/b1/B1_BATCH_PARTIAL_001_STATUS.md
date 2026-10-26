# Partial human batch001: received decisions and remaining gate

18 October 2026. **FRAME_BLOCKED_AWAITING_REMAINING_BATCH_METADATA**.
The incoming combined reply stopped during Q003 after its title. It is not a
complete JSON document; missing content/closures were not manufactured.
[Preserved fragment](HUMAN_BATCH_RESPONSE_001_FRAGMENT.txt) and
[receipt](HUMAN_BATCH_RECEIPT_001.json) were committed at `7807951`.
Four complete objects were received (D01, D02, Q001, Q002), plus the identifiable
partial Q003 object. Q004--Q177 (174 original question IDs) were not received.

Received user decisions, attributed without independent Codex source review:

- D01 SAME_WORK: InjecGuard/PIGuard, based on the reported author README naming
  change and bibliographic overlap. Consolidate work identity, not PDF bytes.
- D02 DISTINCT_WORKS: the MCP STRIDE/DREAD paper reportedly cites the earlier
  technical report; keep both identities. Their domain exclusions are unchanged.
- Q001 INCLUDE: Palisade v1, English-only prompt selection (Section I, PDF p.2)
  and layered binary screen (Section II, p.3). This is domain only; no inference
  about other-language coverage or cutoff-selected version is made.
- Q002 UNCLEAR: user explicitly states this is not a completed method review;
  no reviewed version is established. Do not treat it as a completed check.
- Q003 UNCLEAR: partial method inspection supports binary classification but
  leaves English evaluation unresolved. Its object is truncated; Q003 and its
  captured source ID identify the requested work without inventing a work_id field.

The [new ledger](a02-human-batch001/SCREENING_LEDGER.json),
[work records](a02-human-batch001/WORK_RECORDS.json), and
[crosswalk](a02-human-batch001/WORK_ID_CROSSWALK.json) preserve all old source
members and IDs. D01 maps arxiv:2410.22770 to the existing DOI work ID
10.18653/v1/2025.acl-long.1468 under the existing DOI-first bookkeeping rule;
that is not a final publication/version selection. D02 stays distinct.
Original 373-record ledgers, raw metadata and protocol locks remain unchanged.

Current state: **372 work records, 6 domain INCLUDE, 191 EXCLUDE, 175 UNCLEAR**.
All 389 retained metadata records remain mapped exactly once. Cap500 passes.
The unresolved works correspond to 176 original question IDs, Q002--Q177:
Q004/Q165 now share one work identity. Neither identity adjudication supplies
their missing English-evaluation fact. A single explicitly version-supported
domain answer can cover both original IDs. No unseen answer is assumed.

[Remaining combined answer file](a02-human-batch001/PENDING_METADATA_ANSWERS_BLANK.json)
retains the original question IDs and blank answer fields, with Q002/Q003's
received limitations carried as prior evidence. Identity questions and Q001
need no repeat answer. Please supply the remainder in one combined response;
Q002/Q003 still need source-level resolution, not a repeat of their uncertainty.
This is metadata review, not the selected-six independent outcome sheet.

[Manifest](a02-human-batch001/MANIFEST.json) binds the source commit, receipt,
original frame and new projection hashes. Checks cover history/input/output
hashes, complete 389-source partition, 373-to-372 crosswalk, D01/D02 consistency,
Q001-only resolved domain change, preserved exclusions/uncertainty, pending
coverage and blank answer cells, links, scope, sizes, staged bytes and whitespace.
No new parser/production tests were needed or rerun for these annotations.
No new source retrieval, outcome/PDF reading, version/access reconciliation,
eligible freeze, seeded draw, six-paper assignment, outcome/claim extraction,
B2, production behavior change or merge occurred. FPR-001 remains OPEN.
The work is committed and pushed only to the authorized research branch;
exact final commits and remote verification are reported at delivery.
