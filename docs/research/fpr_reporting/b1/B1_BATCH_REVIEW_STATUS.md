# B1: consolidated metadata-review gate

18 October 2026. **FRAME_BLOCKED_AWAITING_BATCH_HUMAN_METADATA**.
The user's request to collect all reviews together is preserved in
[BATCH_REVIEW_WORKFLOW_20261018.md](BATCH_REVIEW_WORKFLOW_20261018.md), committed
at `3171587`. It changes review batching only; no Palisade judgment was supplied.

All 373 provisional work records now have a first-pass domain disposition:
**5 INCLUDE, 191 EXCLUDE, 177 UNCLEAR, 0 NOT_SCREENED**. The unchanged 500-work
cap passes even before resolving possible duplicates. Five exclusions are the
unchanged sentinel matches; other exclusions have explicit metadata rationales.
The additional domain inclusion, arxiv:2605.07269 (MIPIAD), explicitly describes
English/Bangla input-injection sequence classification in its abstract.
No domain inclusion is a final cutoff-version eligibility decision.

The [single review packet](a02-screening-batch/BATCH_METADATA_REVIEW_REQUEST.md)
contains all 177 current domain questions and two possible-duplicate questions.
It includes Palisade as Q001, replacing a separate reply to request005. Existing
human decisions001--004 are preserved and are not asked again. Domain question
counts: English setting only41; timing+English25; task+English71; task+timing+
English32; task only1; binary-unit+English3; binary-unit+timing+English1;
binary-unit+task+English3. These are current records, not 177 verified distinct
papers or a selected pilot. The new identity questions concern InjecGuard/
PIGuard and the two related MCP-client studies. No canonical mapping is asserted.

[Blank combined answers](a02-screening-batch/BATCH_METADATA_ANSWERS_BLANK.json)
accept bibliographic/method evidence only. This is not the six-paper independent
human outcome sheet. Human answers may be returned together; retain UNCLEAR when
evidence cannot establish a requirement, and give limitations rather than infer.
A task/timing exclusion can resolve a case without investigating its language.

Frozen annotations/exposure records and the projection helper are committed at
`ac93104`. The [manifest](a02-screening-batch/SCREENING_MANIFEST.json) records
clean source ac93104bb20da7319b8564b2750a670b702733b9, Python version, actual creation
UTC, and input/output hashes. Screening includes full and explicitly abbreviated
abstract views; unknown facts are referred for human review. Abstract numerals
were masked; verbatim bibliographic titles can contain headline numbers. No
performance values or assurance labels were extracted or used for decisions.
The exposure log records display limitations and repaired console truncation.

Original protocols/locks, raw source captures, prior ledgers, and OPEN FPR-001
remain unchanged. No new source retrieval, PDF reading/access checks, cutoff
version reconciliation, eligible-frame freeze, draw, human assignment or B2
occurred. Production/tests/frozen research artifacts remain unchanged. A02's
arXiv/ACL frame and original seeds, taxonomy and GO/STOP rules remain in force.

Checks cover all original lock hashes, historical/input/output bindings, 373-ID
membership, unchanged prior decisions, 348 new annotations, exact question
coverage and blank answer fields, all source references, no numeric outcome
fields, scope, links, sizes, whitespace and helper Ruff/syntax. Unchanged parser
and production suites were not rerun for this metadata-only change. Final
commits, checks and authorized research-branch push are reported at delivery.
Later human/source/version verification may reveal further ambiguities; these
must be reported and batched, not hidden by declaring the eligible frame complete.
