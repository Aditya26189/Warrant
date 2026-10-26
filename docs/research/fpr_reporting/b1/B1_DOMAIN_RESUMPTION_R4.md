# B1 resumption R4: FRAME_BLOCKED pending GenTel-Safe domain metadata

18 October 2026. [Human event003](HUMAN_DOMAIN_ADJUDICATION_003.json), committed
at `51b1cd0bda914e3eb92d3d71bfbbd2f3f67bea22`, records the user's INCLUDE for arxiv:2409.13331.
The judgment accepts a predominantly English dataset for domain eligibility.
The held-out test language composition and a separate English-only evaluation
are not established. Source evidence is attributed to the human review of v1,
Sections V/VI, PDF page 4; no independent Codex full-text review is claimed.
Other version, sentinel and eligibility requirements remain pending.

The [round4 ledger](a02-screening-round4/SCREENING_LEDGER.json) preserves every
previous ledger and applies that judgment, then records the next sorted work,
arxiv:2409.19521, GenTel-Safe, as UNCLEAR. Its abstract describes both prompt
injection and harmful-prompt safeguarding; qualifying binary input detection
and English evaluation require [human metadata review004](HUMAN_METADATA_REVIEW_REQUEST_004.md).
The original frame requires: "If title/abstract cannot establish domain, retain
`UNCLEAR` for human metadata screening". Screening stops at that unresolved work.
The abstract was within the first20 already logged exposures; no new abstract
was displayed. Numerical strings were masked in the repeated display; qualitative
performance wording was incidental exposure and was not used for screening.

Current 373-work state: **3 domain INCLUDE, 17 EXCLUDE, 1 UNCLEAR,
352 NOT_SCREENED**. Cap500 passes. Domain inclusions are not final eligible
versions. No source refresh, PDF/access review, version reconciliation, eligible
freeze, seeded ten-paper draw, six-paper assignment or assigned worksheet occurred.
No FPR outcomes, sample/false-positive counts or assurance classifications were
extracted. B2 remains unauthorized; production, frozen results, all historical
protocol/input/ledger bytes and the OPEN FPR-001 issue remain unchanged.

The user's new instruction authorizes pushing completed work to GitHub. It
supersedes prior no-push instructions only for this research branch. No merge,
release or publication submission is authorized. Historical no-push status
reports remain unchanged. Push result and remote hash will be reported at delivery.

[Round4 manifest](a02-screening-round4/SCREENING_MANIFEST.json) SHA bindings:

- Approved A02 lock: `a8b736803da62bd399644abcc1f2ffb0a767b983560f16629ce16cf5d84147c7`.
- Human event003: `6f1f6be491ad761283c060f131bcfbf50e560f9b42ea0fc158d2b8bfda5c64c6`.
- Round4 ledger: `95e7b1fd18fb7926fc21ecd1ac1e32ded8439234fd1f0b8550a83ba6115e1ee7`.

Checks cover input/historical hashes, 373-ID partition, exactly two changed
states, stop order, counts, domain-only scope/limitations, no outcome/sampling
fields, scoped staged bytes, links, size and whitespace. Unchanged parser and
production suites were not rerun for annotation-only changes. One read-only
inspection initially omitted UTF-8 and failed decoding; rerunning explicitly
with UTF-8 succeeded without changing inputs. Initial sandbox GitHub access
failed through the restricted proxy; elevated read-only access succeeded.
B1 remains incomplete pending metadata review004.
