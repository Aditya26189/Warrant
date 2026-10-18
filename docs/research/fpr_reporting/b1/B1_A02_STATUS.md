# A02 B1 status: FRAME_BLOCKED awaiting human domain metadata adjudication

The arXiv/ACL discovery and deduplication pass is complete. **The 500-unique-work
cap passes: 389 retained metadata records map to 373 works.** The earlier
OpenReview cap blocker is superseded for selection by A02; OpenReview discovery
records remain EXCLUDED_FROM_SELECTION_FRAME. No new discovery queries or source
refreshes occurred. A02 was separately committed as `e3f62ea53fca23a7cf295c5e6f4c903bbee1876b`
before metadata screening, eligibility decisions or randomization.

## Protocol and immutable provenance

The active protocol is the preserved original frame plus A01 plus
[AMENDMENT_A02_RETRIEVAL_SCOPE.md](AMENDMENT_A02_RETRIEVAL_SCOPE.md).
[PROTOCOL_LOCK_A02.json](PROTOCOL_LOCK_A02.json) binds all applicable source,
protocol, prior-manifest and storage hashes/commit references. The original
protocol, A01, original lock, raw source captures and OpenReview history have
not been rewritten. SHA-256:

- Original frame: `74e109f800fb40f9d8fe5da61c62baf826b9980357bc87ae4f506fab64d9e6ef`.
- A02 amendment: `bfad507a51bf480127cfbc4da474d49d181ffbf73a1d21f0c004b0817ebd6e81`.
- Updated protocol lock: `a8b736803da62bd399644abcc1f2ffb0a767b983560f16629ce16cf5d84147c7`.
- Canonical metadata union: `dea23a8f9198e3ecefd71ab92c91b0680a7b0cfe97f59119880997cfba69b808`.
- Deduplicated work records: `d911dcc233c9a27c03521009b145ca56e52381f427c94fc39828e98b63b45b21`.

The workspace-local research parser uses bibtexparser 1.4.3 (BSD license option)
and pyparsing 3.2.3; production requirements/global Python were not changed.
[PARSER_LOCK_A02.json](PARSER_LOCK_A02.json) binds script/checker and dependency
source hashes, and [check_a02_parser.py](check_a02_parser.py) supplies nine
passing offline checks. The strict lexer preserves all record locators and
compares retained ACL fields against the pinned reference parser.

## Completed metadata work

- arXiv: all 395 captured entries processed; 364 pass the exact local title/abstract
  predicate and source-date boundary. Every record, including nonmatches, is in
  `a02-metadata/arxiv_filter_ledger.jsonl`.
- ACL: all 131,708 captured BibTeX records processed; 25 pass the fixed field/date
  filters. None of those retained records has an unclear source month/date.
  Seven CSV ledger parts retain a decision/locator for every source record.
- Combined: 389 source records, with source/identifier uniqueness and complete
  ledger checks. No domain criterion or result was used to obtain this count.
- Deduplication: 16 identifier or exact-title/named-author links give 373 unique
  works, with every record mapped exactly once. Middle-name omissions are
  resolved only with agreeing full first/family names and complete author lists;
  initials and conflicting identities are not expanded or merged. No unresolved
  duplicate pair remains. This is bibliographic normalization, not an identity
  claim about the unresolved StepGuard URLs; A01 remains unchanged.

The clean-source run commits are recorded in the immutable
[metadata manifest](a02-metadata/METADATA_MANIFEST.json) and
[deduplication manifest](a02-dedup/DEDUP_MANIFEST.json). The source code was
committed before each generator ran. Local commits are not trusted timestamps
or retroactive preregistration.

## New eligibility stop

Manual domain screening followed sorted canonical work IDs. Seven works were
excluded under task/type rules; the eighth, **arxiv:2403.17710**, is UNCLEAR.
Its abstract mentions empirical attacks on responses supplied to an LLM judge
and detector defenses without establishing the required input-classification
evaluation. The original frame explicitly requires human metadata screening
when the title/abstract cannot establish domain. Selection cannot silently omit
this possible eligible work or assume its inclusion.

[HUMAN_METADATA_REVIEW_REQUEST_A02.md](HUMAN_METADATA_REVIEW_REQUEST_A02.md)
provides the precise question and source locator. It requests only a domain
judgment and bibliographic/method evidence, not numerical outcomes or a human
extraction sheet. The pending question was also sent to the user. No reply has
been assumed. A protocol amendment is not needed merely to supply this planned
human metadata adjudication.

The independent mechanical sentinel pass matches the locked identifiers and
exact known titles, including A01's StepGuard title/prefix. Current ledger:
**12 exclusions** (7 manual
domain exclusions and 5 locked-sentinel
exclusions), **1 UNCLEAR**, and
**360 NOT_SCREENED**. No manual domain judgment was
made beyond the first material uncertainty. The remaining records are pending,
not rejected. These are administrative progress counts, not feasibility or
literature-prevalence estimates.

[SCREENING_LEDGER.json](a02-screening/SCREENING_LEDGER.json) records every work's
current state, rationale and source references.
[SCREENING_EXPOSURE_LOG.json](a02-screening/SCREENING_EXPOSURE_LOG.json) records
that the first 20 metadata abstracts were displayed with every numeral generically
redacted. Qualitative headlines may have been visible but were ignored; no FPR
values or claim classifications were extracted or used. Newly encountered B1
screening abstracts were not automatically added as prior-exposure sentinels.
The unmodified original abstracts remain in the frozen metadata snapshot.

## B1 gate and checks

Version preference/cutoff reconciliation and PDF availability checks have not
run because eligibility remains unresolved. No completed eligible-ID frame,
seeded ten-paper draw, six-paper assignment or assigned blank human worksheet
exists. Original empty templates are unchanged. No sampling command ran;
B2, outcome/count extraction and claim classifications remain NOT_RUN and
NOT_AUTHORIZED. FPR-001 remains OPEN, untouched and independent of this stop.

PASS checks: all historical A02-bound bytes; raw ACL exact reconstruction;
parser/dependency/script hashes; all 131,708 ACL and 395 arXiv ledger entries;
389 retained unique source records; exact 373-work partition; no OpenReview
selection inputs; zero unresolved duplicate pairs; cap; nine offline parser
checks; identifier/author-matching ambiguity fixtures; Ruff/syntax; source-only
scope; file sizes; local links; JSON/ledger/hash consistency; no draw or outcome
fields; staged byte preservation and whitespace. The production suite was not
rerun for these research-only metadata changes; production and existing tests
are unchanged. Initial development escaping/path and strict-zip lint issues were
corrected before their generators ran; no source data or outcome was changed.

This remains a feasibility pilot within an **arXiv/ACL-retrieved frame**. A full
eligible frame and selection cannot be claimed. No assurance sufficiency,
novelty, representativeness or TMLR-readiness conclusion follows. No production
change, frozen-artifact rewrite, push, merge or publication occurred.

Required next input: human domain metadata adjudication for arxiv:2403.17710,
then resume the remaining B1 eligibility work under the unchanged protocol.
Stop remains in force before randomization and B2.


## Dated addendum: 18 October 2026

Human adjudication includes arxiv:2403.17710 for domain only. See
[B1_DOMAIN_RESUMPTION_20261018.md](B1_DOMAIN_RESUMPTION_20261018.md) for the
preserved decision, resumed screening and next domain metadata gate. The
first-pass stop narrative above is retained as historical context.


## Dated addendum: 18 October 2026, resumption R3

Human adjudication002 includes arxiv:2406.00799 for domain only. See
[B1_DOMAIN_RESUMPTION_R3.md](B1_DOMAIN_RESUMPTION_R3.md) for the new projection,
three subsequent scope exclusions and English-setting metadata request003.
Earlier stop records are retained as historical context.
