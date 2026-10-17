# B1 run status: FRAME_BLOCKED at OpenReview source cap

17 October 2026. **No papers selected; no human assignments; no pilot outcomes
extracted.** The StepGuard sentinel blocker is resolved for selection by the
user-authorized A01 exclusion amendment. Its underlying identity is still
unresolved and is not being revisited. The current blocker is a different,
unchanged source-cap rule in the approved frame.

## Prospective protocol and provenance

[A01](AMENDMENT_A01_SENTINEL_EXCLUSIONS.md) was committed separately as
`2f20e43b7e2b9e5f694157b0f9babe45dcdd9042` before candidate retrieval. It adds two
potentially distinct StepGuard exclusions and matching title/known versions,
without using numerical findings or claim classifications. The original
approved frame and original exposure inventory remain unchanged.

[PROTOCOL_LOCK.json](PROTOCOL_LOCK.json) binds the active original frame plus
A01 and the [65-record inventory](SENTINEL_INVENTORY_AMENDED.json). SHA-256:

- Approved original frame: `74e109f800fb40f9d8fe5da61c62baf826b9980357bc87ae4f506fab64d9e6ef`.
- A01 amendment: `a74caf940b5f9c0aa2b73435483bb586480a46539fd869b65bd8bfde001b6efb`.
- Amended inventory: `dafd88a2eb9e904054dd4dd0eeb579e9e8acabae8bc7062d49ca0355855ed69f`.
- Protocol lock: `7a3c73d465721fb2ea177c53bdc936e614ec5b504c6fb1fc0ef65ff7acc86f42`.

The lock and Git history record local provenance, not a trusted timestamp or
retroactive preregistration. Python was 3.12.10. The bibliographic cutoff remains
2026-10-17T00:00:00Z; actual retrieval times below were later and are not backdated.

## Retrieved sources and stop

1. **arXiv:** the exact approved query returned 395 metadata records, across
   offsets 0/100/200/300 (100/100/100/95 entries), HTTP 200 for every page.
   Request times: 2026-10-17T14:28:36.044816Z through
   2026-10-17T14:28:49.471854Z. Raw IDs are unique within the arXiv return.
   These are retrieved entries, not screened eligible papers or selected versions.
2. **ACL:** the exact approved bulk export returned HTTP 200 and 42,574,037
   compressed bytes, requested at 2026-10-17T14:28:49.481865Z and completed at
   2026-10-17T14:29:08.424848Z. The initial capture tool stopped at its local
   staging-size guard. The raw bytes remain unchanged locally; five committed
   parts, each below 10 MB, reconstruct the original file byte-for-byte.
   [Storage manifest](retrieval-01/STORAGE_MANIFEST.json) records part order,
   hashes and the original hash. This was lossless storage packaging, not a
   change to queries, frame caps or selection rules. No source request was
   repeated. The initial run's semantic status remains in its manifest;
   uncommitted provenance JSON was normalized to LF before its first commit,
   without changing fields or any HTTP response bytes.
3. **OpenReview title query:** the exact approved endpoint returned HTTP 200,
   100 notes and a declared total of **8,798** results. It was requested at
   2026-10-17T14:32:29.539812Z and completed at
   2026-10-17T14:32:30.935634Z. The approved maximum is **500 per field query**.
   The declared total establishes that completion would exceed the cap, so
   the run stopped immediately rather than keeping the first 500 or changing
   the query. The 8,798 is an API search-result total, not a count of eligible
   works, and the query's field/phrase semantics have not been independently
   validated against every returned note.
4. **OpenReview abstract query:** NOT_RUN after that stop.

Both network runs began on clean trees: initial capture source
`2628600e618b343151bced7117af00d84a9675a7`, continuation source
`1462499a5ae0987610bf10ec1583bc0514b96158`. The continuation verified the complete
arXiv response set, raw ACL bytes, lossless parts and protocol hashes before
requesting only the remaining fixed source. The continuation source also
records an explicit-LF manifest writer; the first run's script hash remains
bound to its original source commit.

The preserved [first manifest](retrieval-01/RETRIEVAL_MANIFEST.json) and
[continuation manifest](retrieval-02/RETRIEVAL_MANIFEST.json) retain exact URLs,
offsets, actual UTC times, statuses, body sizes and SHA-256 values. No abstracts,
results or tables were printed to the agent during capture. The raw responses
include the prespecified metadata fields, including abstracts; preserving those
bytes is not outcome extraction.

## Frame and selection states

[SOURCE_COVERAGE.json](SOURCE_COVERAGE.json) is the machine-readable current
status. [PARTIAL_RETURNED_IDS.json](PARTIAL_RETURNED_IDS.json) preserves the
395 arXiv identifiers and 100 OpenReview note/forum identifiers in returned
order, without filtering, canonical mapping or deduplication.

The canonical union, ACL predicate/date screening, cross-index deduplication,
version choice, eligibility decisions, PDF-access checks and eligible-frame
freeze are **NOT_RUN** after this frame-invalidating stop. There are no
candidate inclusion/exclusion or inaccessible-paper decisions to report;
known sentinel exclusions were locked prospectively, not derived from results.
No eligible-ID list, ten-paper draw, six-paper assignment or assigned worksheet
was created. Original blank extraction templates are unchanged. Neither seeded
sample command ran. No outcome values or claim classifications were extracted.
B2a/B2b remain unauthorized. The human should not begin a six-paper assignment
because none exists.

## Checks and limitations

PASS checks: original frame/inventory preservation, 65 unique locked exclusion
records, explicit unresolved identity, exact protocol and response hashes,
395 unique arXiv IDs, returned-order ID projection, complete byte-identical ACL
chunk reconstruction, pinned clean-source script hashes, file-size limits,
Python syntax, Ruff, offline HTTP-error preservation/stop contract, absence of
pilot outcome fields/selection artifacts, relative links, whitespace and
research-only Git scope. Final staged blob checks verify exact bytes, including
raw response files. The complete production pytest suite was not rerun for
metadata-only documentation/tooling; production and existing tests are unchanged.

Earlier checks exposed a one-off AST-check typo, a Ruff broad-exception warning,
Windows temporary-directory permissions and CRLF provenance whitespace. The
check typo and helper warning were corrected, the temporary directory safely
removed, an in-memory error-write contract passed, and only uncommitted JSON
line endings were normalized. These are not suppressed scientific failures.
The source-cap failure remains a real **FRAME_BLOCKED** result.

The three-index snapshot is incomplete and cannot support a valid approved
sample. No counts here estimate literature prevalence or pilot feasibility.
Unverified prior-art access remains a later novelty limitation. No publication
or TMLR-readiness conclusion follows. [FPR-001](../issues/FPR-001-adaptive-bound.md)
remains OPEN and unchanged; it did not cause this bibliographic stop. Production,
frozen research artifacts, push, merge and publication remain untouched.

## Required decision

A new prospective retrieval-frame decision is needed: authorize a validated
query/cap/index amendment, or stop the pilot. No other original rule was relaxed.
A later amendment must preserve this partial snapshot and explain the new
retrieval mechanics before additional source queries or selection. No outcome
results or completed human extraction sheet are needed to make that decision.
