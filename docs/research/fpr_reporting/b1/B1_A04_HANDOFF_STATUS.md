# B1 A04 handoff checkpoint — FRAME_BLOCKED

Recorded 19 October 2026 after the user's explicit FRESH_REVIEWER_PATH adoption.
This is a prepared restricted handoff, not a completed independent review.

## Completed scoped work

Prospective A04 is committed as `651dd24587cdcacd60b50d30e0f5866966485efa`.
Preparation sources and boundary tests are committed as
`b295d9de0858955d399365e0d7a35613898e785e`. The generator ran from that clean
commit. `A04_AUTHORIZATION_RECEIPT.json` preserves the explicit adoption;
`A04_PROCESS_DECISION_SOURCE.txt` preserves the adopted recommendation's bytes.
Neither is included in the restricted reviewer archive.

Deliver **only** `a04-handoff/FRESH_REVIEWER_INTAKE.zip` to a fresh reviewer in a
separate empty workspace, with the following archive hash supplied separately:

`48c903779bda205c2af6231da92cca8b70e6ba9755cfa175f526c107e23e7290`

The archive is 82,931 bytes and contains ten flat files: eligibility instructions,
bibliographic constraints, all 372 work identifiers with all 389 source-member
commitments, the existing 65 sentinel identifiers, blank review/intake/evidence
forms, a manifest and a standalone offline verifier. Titles, abstracts, earlier
eligibility judgments, historical source displays and exposure details are not
included. Title/abstract withholding is uniform and changes no eligibility rule.
The full source inventory remains frozen outside the archive. Hashes alone cannot
resolve renamed-title/version matches; controlled bibliography intake is needed.

The unpacked `a04-handoff/restricted/` directory is byte-identical to the archive.
The rest of this repository, this report, previous chats, coordination board and
`CUSTODIAN_RECEIPT.json` must not be supplied to the fresh reviewer. The custodian
receipt binds the complete membership crosswalk and historical checkpoint.
`PROTOCOL_LOCK_A04.json` has SHA-256:

`00856fbdcc796ac4d04b52e67de46c79fdc8bb5b9d26115ef48d3c46c4cafbaf`

## Checks and historical preservation

- Eleven handoff boundary tests and nine existing metadata-parser checks pass.
  The new tests reject prior-decision/prose fields, extra source/result files,
  altered bytes, missing/repeated memberships, fabricated reviews/attestations
  and an unblocked draw status. Ruff and standalone package verification pass.
- All 20 A04 lock entries verify. Both historical A02/A03 file locks verify;
  the package's ten entries match the unpacked bytes. D01 is one work and D02
  remains two distinct works. All 372 previous ledger IDs are represented.
- All 122 B1 files at the historical `03834a0` checkpoint are unchanged. All 42
  assistant events, Q007's correction, earlier human records, source receipts,
  failed/corrected checks and the permanent exposure deviation are retained.
  Source-cache checks previously recorded at that checkpoint were not rerun;
  preservation does not constitute renewed source-level validation.
- The first two sandboxed new-test runs failed on Windows temporary-directory
  permissions, including a workspace-local attempt. The same scoped tests pass
  with sandbox escalation. The failure and corrected run are recorded in
  `A04_GATE_CHECKS.json`. No failed scientific check was treated as a pass.
- The byte-identical user process-decision attachment retains its original CRLF
  bytes. Default staged whitespace checking flags those 54 line endings; checking
  with `git -c core.whitespace=cr-at-eol diff --cached --check` passes. Other new
  text uses LF. The raw receipt was not normalized to suppress the warnings.
- No research retrieval, eligibility adjudication, selection, outcome extraction
  or production test run was performed in this amendment/handoff task. Production
  code and frozen research artifacts are unchanged; the changes are new B1 files.

## Remaining blockers and next gate

Reviewer and restricted primary-evidence provider are **UNASSIGNED**. Freshness,
isolated access and evidence-intake arrangements are **NOT ATTESTED**. No actual
independent review has begun, and preparation of the archive is not a transfer
to an identified reviewer. The shared checkout/subagent environment does not by
itself enforce the required isolation; no agent in that environment was labeled
an independent fresh reviewer.

The recipient must truthfully complete the blank intake, arrange controlled
primary bibliographic/method/dataset evidence, independently review every work,
and return a frozen/hash-bound complete review and evidence receipts. The
custodian must commit that independent return before comparison with the old
decisions. This includes reassessment of 41 assistant-judged works, adjudication
of 115 pending questions and reconciliation of all earlier human inclusions and
exclusions. No subgroup labels or previous decisions are in the reviewer sheet.

Q002's withdrawn/latest-version and access question, Q026/Q153's reproduced-study
overlap, and all other material eligibility/version/sentinel uncertainties remain
for that independent review. D01 SAME_WORK and D02 DISTINCT_WORKS are locked
bibliographic constraints. No earlier version is silently substituted and no new
exposure-based exclusions are added.

**The ten-paper draw remains blocked until complete independent review,
mechanical validation and another explicit B1 gate approval.** There are no
selected ten papers, six-paper assignment or human outcome worksheet to report.
No B2, production changes, merge or publication is authorized. Existing permission
to push these research-only commits remains in force. FPR-001 remains open and
unchanged. The original outcome exposure remains permanently disclosed; a fresh
review can mitigate its selection risk, not erase it.
