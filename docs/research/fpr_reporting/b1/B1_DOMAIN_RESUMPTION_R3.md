# B1 resumption R3: FRAME_BLOCKED pending English-setting metadata

18 October 2026. Human domain adjudication002 is committed at
`84500a74ae354ec349503b5ae9329edd4d863aa9`. It includes arxiv:2406.00799 for domain only,
using the user's v6 method review: English primary tasks (Section III/Appendix D)
and input activations/classification before generation (Sections IV-A/IV-C).
[HUMAN_DOMAIN_ADJUDICATION_002.json](HUMAN_DOMAIN_ADJUDICATION_002.json) records
that attributed evidence without claiming independent Codex source verification.
No outcome values or assurance labels were supplied or used. The reviewed v6
has not automatically become an approved cutoff-based selected version.

The prior round2 ledger and every earlier adjudication/input remain unchanged.
The [new round3 ledger](a02-screening-round3/SCREENING_LEDGER.json) applies the
human decision and four sorted-work-ID domain screening events preserved in
[DOMAIN_SCREENING_ADDENDA_R3.jsonl](DOMAIN_SCREENING_ADDENDA_R3.jsonl):

- arxiv:2408.03095: EXCLUDE, unit-test generation/repair; prompt injection is used
  as an engineering technique, rather than the approved security detection task.
- arxiv:2408.03515: EXCLUDE, robotic navigation/secure prompting under multimodal
  attacks without an identified separate binary text input-classifier evaluation.
- arxiv:2408.07291: EXCLUDE, personal-information extraction and its countermeasures.
- arxiv:2409.13331: UNCLEAR. The abstract explicitly supports binary prompt
  classification, but the English evaluation setting remains unstated.

Current state among 373 works: **2 domain INCLUDE, 17 EXCLUDE, 1 UNCLEAR and
353 NOT_SCREENED**. The exclusions comprise 12 manual domain exclusions and
5 unchanged mechanical sentinel exclusions. Both domain inclusions remain
subject to cutoff/version, sentinel and all other locked eligibility checks.
No manual domain decisions were made beyond the next unresolved record.

[Metadata request003](HUMAN_METADATA_REVIEW_REQUEST_003.md) asks only for the
English dataset/evaluation fact and a method locator. The approved frame says:
"If title/abstract cannot establish domain, retain `UNCLEAR` for human metadata
screening". The question has been sent to the user; no answer is assumed.
This is a planned human metadata judgment, not a requested protocol amendment.
Sequential metadata review is currently the screening bottleneck; it provides
no evidence about FPR reconstructability or assurance prevalence.

The [round3 manifest](a02-screening-round3/SCREENING_MANIFEST.json) binds the
previous ledger, human event002, new addenda and current projection. SHA-256:

- A02 protocol lock: `a8b736803da62bd399644abcc1f2ffb0a767b983560f16629ce16cf5d84147c7`.
- Prior round2 ledger: `c9244d8096bba1e31053e8c4ea9f7884b23342b1343f59b09206c10ac8768df0`.
- Human event002: `974ed0b94e8a142067bd6d8a5db2ae30177b234a51f0180ef6ae4c2d161a78b4`.
- Current round3 ledger: `9d9a89689be02b27d82f42bc733c34ae176eee089000524d8f003f4e5f8bf52a`.

A02 arXiv/ACL-only scope and all locked rules remain unchanged. The 373-work
frame passes the 500-work cap. Original protocol/locks, raw source captures,
prior metadata/dedup/screening artifacts and FPR-001 are preserved. No source
refresh, new discovery query, new abstract exposure beyond the logged first20,
PDF access, cutoff/version reconciliation or eligible-frame freeze occurred.
There is no ten-paper draw, six-paper assignment or assigned human worksheet.
B2, FPR/count extraction, assurance classification, production changes, frozen
artifact rewrites, push and merge remain unauthorized/unperformed.

Checks cover historical/input/projection hashes, exactly five updated work
states, 373-work membership and count consistency, domain-only inclusion scope,
stop order, no sampling/outcome fields, links, sizes, scope, staged bytes and
whitespace. Unchanged parser/production tests were not rerun for these annotation
and documentation addenda. Results and final commits are reported at delivery.
Stop pending the requested domain metadata evidence; B1 remains incomplete.
