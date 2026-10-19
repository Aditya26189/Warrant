# Restricted independent eligibility review — intake only

Use only the contents of this archive in a separate empty workspace. Do not
open the source repository, its Git history, coordination board, prior chats,
previous screening decisions, full-text caches or human outcome sheet.
The archive prepares a handoff; it does not attest that a reviewer is fresh,
that evidence access is isolated or that independent review has started.

First run `python verify_package.py` locally. Its integrity checks do not require
network access or any third-party package. Check the archive hash against the
custodian's separately supplied receipt. Complete `REVIEWER_INTAKE_BLANK.json`
truthfully before reviewing any work. All fields are initially null. If you have
seen previous judgments or result-bearing displays, stop. Report any previously
familiar work for reassignment to another fresh reviewer, without describing its
findings and without excluding it from the frame.

Review all 372 works independently under `ELIGIBILITY_RULES.md`. Every work starts
with a blank record in `ELIGIBILITY_REVIEW_BLANK.json`; no old decision is a default.
Do not infer a decision from membership, identifier order, missing evidence,
absence of an abstract or the presence of a bibliographic issue note. Preserve
all 389 captured metadata memberships and the locked identity constraints.

Titles and abstracts are withheld uniformly, with hashes retained. This is an
access restriction, not a new screening rule. The inventory carries bibliographic
identifiers, captured date fields and source-byte commitments. A captured arXiv
version is not automatically the protocol-selected version. Bibliographic links
are reference locators, not permission to browse unrestricted abstracts/full text.

No primary methods evidence is preloaded and no evidence curator is assigned.
Before review begins, arrange a separate controlled evidence intake supplying
only primary bibliography and relevant method/dataset/threat-model passages.
Record each request, exact version/locator, source URL, actual retrieval UTC,
status, raw-source hash, restricted-evidence hash, provider and restriction check.
Full abstracts, results, tables, captions, conclusions, numerical or qualitative
performance findings and statistical-claim language must not reach the reviewer.
Merely masking digits is insufficient. Request only missing method facts and
the source's evaluation context; do not request rates, class/sample counts or
assurance classifications. If restriction cannot be maintained, stop and notify
the custodian without copying result-bearing content into the review.

Use `EVIDENCE_RECEIPT_BLANK.json` as a per-evidence receipt template. Fill the
eligibility sheet with method facts and limitations, not outcomes. T/B/P/L denote
input-injection task, binary evaluation, pre-target-answer timing and English
evaluation. An unresolved fact stays UNCLEAR. Freeze and hash the completed
independent review in the isolated workspace. The custodian must commit the
returned review before comparing it with historical decisions. Do not clone the
source repository or create a new repository for this intake. Return the versioned
review artifact with
reviewer attestation, evidence receipts and complete work/member reconciliation.

This intake contains no sampling program. Do not draw papers or perform any
outcome extraction. Complete review and mechanical validation must be followed
by explicit B1 gate approval before the original seeded ten-paper draw. No B2
or human outcome worksheet is authorized. Current status: FRAME_BLOCKED.
