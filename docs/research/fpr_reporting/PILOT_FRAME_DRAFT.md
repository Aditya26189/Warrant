# Ten-paper frame — DRAFT_AWAITING_HUMAN_FRAME_APPROVAL

17 October 2026. Proposed feasibility pilot only. **No protocol is frozen,
candidate search snapshot retained, paper drawn, or pilot outcome extracted.**
Prior-art work is in `PRIOR_ART_GAP.md`; remaining access uncertainty is explicit.
The choices below need human approval before B1 in a new authorized turn.

**Amendment status:** the user's 17 October decision is **AMEND — CONDITIONAL
APPROVAL, NOT EXECUTION APPROVAL**. This revised draft implements the requested
clarifications; the frame remains unapproved for execution. Neither the
acceptable 3/10 and 2/10 feasibility heuristics nor completion of these edits
authorizes retrieval for selection, sampling, extraction or another stage.

## Question, domain and bibliographic boundary

Can explicit population-level benign-FPR assurance propositions be traced to
their observed evidence, decision units, threshold-selection protocol and
invoked method, in a bounded sample of binary input prompt-injection detector
papers? The pilot tests feasibility of a larger audit, not literature prevalence.

Proposed domain: English text **binary prompt-injection input classifiers**
that assign a malicious/benign score or decision to a prompt/document before
the downstream LLM answers. Direct and indirect delivery are recorded as
context within this one detector task; they are never pooled as one empirical
FPR population. Exclude harmful-content/jailbreak safety classifiers unless a
separate input prompt-injection detection evaluation is identified from the
abstract; exclude PII, output moderation, response refusal alone, end-to-end
attack-success-only defenses, tool-policy-only systems, surveys and positions.
Language eligibility concerns the evaluation setting, not authors' location.
If title/abstract cannot establish domain, retain `UNCLEAR` for human metadata
screening; never consult FPR tables to decide eligibility.

Include original empirical research manuscripts publicly released from
**2024-01-01 through 2026-10-16**, including preprints with venue status recorded
separately. Proposed bibliographic/version cutoff: **2026-10-17T00:00:00Z**.
Use the latest public version at or before that cutoff, not a later revision.
First-public date establishes window eligibility; archive histories establish
version. A date known only to month must fall entirely inside the window or be
`UNCLEAR`, resolved by human metadata review before selection. Unknown versions
remain excluded with reason; do not infer an earlier timestamp from a local file.
Actual B1 retrieval timestamps will be later and must never be backdated.

## Fixed retrieval proposal (not executed)

Primary indexes: **arXiv, ACL Anthology, OpenReview**. Publisher archives resolve
DOIs, publication status, versions and PDF access for retrieved works; they do
not silently expand the frame. No citation chasing or general web ranking may
add sampled candidates. The frame will miss papers absent from these indexes.

Fields: title and abstract only, plus identifiers, authors, release/version
dates, venue and PDF URLs. Never search FPR outcomes, benign sample sizes,
"zero false positives", confidence claims or individual results for inclusion.
Use these fixed queries/filters:

1. **arXiv Atom API**, exact query below; sort by submittedDate ascending,
   pages of 100 (`start=0,100,...,400`), maximum 500 records. Endpoint:
   `https://export.arxiv.org/api/query?search_query=<URL-encoded-Q>&sortBy=submittedDate&sortOrder=ascending&start=0&max_results=100`.

   ```text
   (ti:"prompt injection" OR abs:"prompt injection" OR ti:"prompt-injection" OR abs:"prompt-injection") AND (ti:detect* OR abs:detect* OR ti:guardrail* OR abs:guardrail* OR ti:classif* OR abs:classif*) AND submittedDate:[202401010000 TO 202610162359]
   ```

2. **ACL Anthology**, retain the official
   `https://aclanthology.org/anthology+abstracts.bib.gz` metadata bytes and hash.
   Parse title/abstract/date/ID fields, then apply the predicate below to those
   fields only. Retain all matches in the date window, maximum 500. No PDF
   scanning or citation-field matching. Missing abstracts are recorded, not
   treated as evidence of no evaluation.
3. **OpenReview API v2**, two field queries, retaining public forum submissions
   only (not reviews/replies):
   `https://api2.openreview.net/notes/search?term=prompt%20injection&type=terms&content=title&source=forum&limit=100&offset=0`
   and the same URL with `content=abstract`. Page offsets 0,100,...,400,
   maximum 500 per field query; apply the same local predicate/date window.
   Preserve returned order and all returned IDs before any filtering.

Local field predicate, executable on normalized title+abstract string `text`:

```python
bool(re.search(r"\bprompt\s+injection\b", text)) and bool(
    re.search(r"\b(?:detect\w*|guardrail\w*|classif\w*)\b", text)
)
```

Normalization is Unicode NFKC, casefold, Unicode category `Pd` hyphens replaced by spaces,
and collapsed whitespace. Freeze the metadata parser/version in B1 before
screening. Source API mechanics are documented by the
[arXiv manual](https://info.arxiv.org/help/api/user-manual.html),
[ACL bulk-export guide](https://aclanthology.org/faq/bib/), and
[OpenReview API specification](https://docs.openreview.net/reference/api-v2/openapi-definition).
These are planned executable retrieval queries, not evidence of a successful
B1 run. Any unsupported pagination, access/authentication failure, changed API
meaning, cap reached with remaining records, or more than **500 unique works
to screen** means `FRAME_BLOCKED`: preserve partial responses and stop for an
amendment before outcomes. Do not switch engines or keep the first ranked hits.

## Deduplication, screening, access and freeze

Deduplicate by DOI/arXiv-ID/OpenReview forum crosslinks first, then normalized
title plus author identity. One work, one selected version. Retain every raw
record and crosswalk; ambiguous duplicate pairs need human metadata adjudication.
Version preference: publisher version of record available by cutoff, then
accepted public conference version, then latest dated preprint by cutoff.
Retain preprint IDs and their crosslinks even when publisher PDF is preferred.

Screen all retained works in sorted canonical-ID order using metadata, abstract
and recorded exclusion reasons. Eligibility must not require an FPR statement,
denominator, small sample, assurance claim, or statistically interesting result.
Abstract headlines encountered are exposure logs, never screening criteria.
Known exposed works below remain outside the ten-paper denominator, with
`known_prior_art_sentinel=true`, regardless of whether they would be eligible.
Human must approve/amend the sentinel inventory before frame lock.

Lock the named sentinel inventory before retrieval/screening. Newly encountered
headline numbers in a screening abstract must be logged and ignored for the
inclusion/exclusion decision; they do not automatically turn that paper into
an excluded sentinel. Distinguish those incidental screening exposures from a
recognized **earlier** project exposure. Log any correction to the prior-exposure
inventory with its reason before selection. Never exclude a paper merely
because its abstract reports an outcome.

B1 must **save raw source responses before deterministic selection**: complete
retrieved IDs/metadata, source/query/offset, response/error status, actual UTC
retrieval time, bibliographic cutoff, source totals and caps. Preserve exact
raw bytes and a canonical JSONL union; compute SHA-256 of each and the frozen
snapshot manifest. Retain included/excluded/unclear records with reasons and
dedup/version crosswalk; hash the screened eligible-ID/version file separately.
The frozen snapshot defines the frame; a future re-query does not reproduce it
by assumption. A local commit is not a trusted timestamp or preregistration.

Before selection, check PDF availability through bibliographic links without
reading outcome tables. **PDF accessibility is not an eligibility criterion.**
Keep every inaccessible candidate in the raw/screening records and retain
otherwise eligible inaccessible works in the eligible-ID frame. Record
`INACCESSIBLE`, attempted sources, timestamps and the bibliographic eligibility
decision separately. **Keep inaccessible selected papers; no replacement**
and no outcome-driven re-draw. Preserve them in the ten-paper denominator;
never substitute the number of accessible or completely reported papers.
If fewer than ten
eligible unexposed works exist, stop as `FRAME_INSUFFICIENT`; do not pad it with
sentinels. Access failures may make human verification infeasible and force STOP.

## Uniform selection proposal — commands for B1 only

Seed **20261017**, Python **3.12.10**, sorted unique canonical versioned paper IDs;
`eligible_ids.json` is the approved frozen JSON list. This is a seeded uniform
draw **within the bounded search-retrieved frame**, not a probability sample
of all guardrail research. Proposed deterministic command:

```text
python -c "import json,random; from pathlib import Path; ids=json.loads(Path('eligible_ids.json').read_text()); assert len(ids)==len(set(ids)) and len(ids)>=10; print(json.dumps(random.Random(20261017).sample(sorted(ids),10),indent=2))"
```

B1 saves that output as `selected_ids.json`, binds its hash to the raw snapshot
and screened frame hashes, then chooses six using this predeclared second seed:

```text
python -c "import json,random; from pathlib import Path; ids=json.loads(Path('selected_ids.json').read_text()); assert len(ids)==len(set(ids))==10; print(json.dumps(random.Random(20261018).sample(sorted(ids),6),indent=2))"
```

Neither command has been executed. B1 supplies only ID/version metadata and
six blank human rows, then **STOPS before any outcome extraction**.

## Known sentinels and accidental exposure log

All versions of each following work are excluded from fresh draws. This is a
prospective transparency rule, not evidence that its findings are wrong.

- **arXiv:2605.06669v2**, Maiorano, *Evaluating Prompt Injection Defenses for
  Educational LLM Tutors* ([abstract](https://arxiv.org/abs/2605.06669v2),
  revised 21 May 2026): abstract only. Exposed zero-FP pipeline language, NeMo
  16.22% FPR/0% bypass/~1.5s and Prompt Guard 3.60% FPR/38.48% bypass; also
  interval/test/seed-sweep language. No PDF tables or counts sought.
- **arXiv:2609.33671v1**, Hao Chen, *COGNIT-Guard* ([abstract](https://arxiv.org/abs/2609.33671v1),
  27 Sep 2026): abstract only. Exposed N=607, accuracy 98.85%, FPR .42%
  (1/238), McNemar/Fisher tests, ECE/Brier; cascade zero-FPR/99.23%-accuracy
  and latency headlines, SafetyBench-ZH N=2,100 and OOD/replay/in-domain ranges.
  This records exposure, not a verified extraction, claim label or anomaly.
- All sources in `PRIOR_ART_GAP.md`, including alternate-title
  arXiv:2407.02551v2, and A1's arXiv:1608.03109 are known sentinels. Their
  versions/depths are recorded there. CASCADE v3 abstract additionally exposed
  5,000 samples, 11.70% versus 1.51% FPR, 68.5% referrals, wrapper proportions,
  threshold-history and review-model effects. Position Appendix A.5 exposed
  its reconstructed XSTest/StrongREJECT comparisons. These are prior-art
  exposures, not pilot extractions.
- Incidental search snippets also exposed input-detector findings at
  [Electronics 15(11),2242](https://www.mdpi.com/2079-9292/15/11/2242)
  (benign training/testing sample sizes),
  [Electronics 15(16),3554](https://www.mdpi.com/2079-9292/15/16/3554)
  (120-prompt/three-class corpus and performance limitations),
  [Future Internet 18(7),376](https://www.mdpi.com/1999-5903/18/7/376)
  (PromptSentinel-X, 465-record grouped test and uncertainty language),
  [Applied Sciences 16(16),7974](https://www.mdpi.com/2076-3417/16/16/7974)
  (SecureMCP denominator-adjusted miss-rate claims), and
  [OpenReview 4et1dh8D23](https://openreview.net/pdf?id=4et1dh8D23)
  (benign-FPR table existence and single-run reporting). No targeted tables
  were opened for these; bibliographic identity/version remains metadata
  reconciliation work in B1. Keep on the exposure exclusion list meanwhile.
- Additional snippet leads—arXiv:2605.31042v1 (clean/evaluation split counts),
  2609.14079 (verifier-performance critique), 2607.23999 (denominator-dependent
  containment rankings), 2605.17986 (small-denominator deployment findings),
  2606.09315 (route-safety denominator hierarchy), and medRxiv
  10.64898/2026.06.04.26354950v2—are exposure exclusions if otherwise eligible.
  Unresolved titles *MAGE*, *Indirect Prompt Injections: Are Firewalls All You
  Need, or Stronger Benchmarks?*, and *Strengthening Polymorphic Prompt
  Assembling* must be resolved by metadata before B1 screening; no outcomes
  should be sought to resolve them. If unresolved, stop rather than assert a
  fully reconciled exposure list. Nonresearch blogs are discovery leads only.

These are recorded observations of abstracts/snippets, not verified scientific
claims. The human must add any earlier exposed papers from previous chats or
their own reading; inaccessible chat history was not invented or silently
treated as outcome-blind. A newly recognized prior exposure is logged before
selection; it must never be hidden to retain an otherwise attractive candidate.

## Blank schema and interpretation contract

`PILOT_EXTRACTION_TEMPLATE.csv` and `HUMAN_EXTRACTION_TEMPLATE.csv` contain
identical headers and **no rows**. The package's `EXTRACTION_CODEBOOK.md`
governs both sheets. Extra fields keep reporting sufficiency separate from
inference, and retain source/protocol provenance. Controlled values:

- `claim_type`: **NONE, DESCRIPTIVE, OPERATING_TARGET, ASSURANCE,
  FORMAL_GUARANTEE, AMBIGUOUS**. NONE means no relevant FPR statement;
  ASSURANCE requires population/statistical-confidence language;
  FORMAL_GUARANTEE requires separate theorem/assumption review.
- `duplicates_or_clusters`: **REPORTED, NOT_REPORTED, UNCLEAR**.
- `reporting_sufficiency`: **FULLY_RECONSTRUCTABLE, PARTIALLY_RECONSTRUCTABLE,
  MISSING_NEGATIVE_COUNT, MISSING_FP_COUNT, MISSING_THRESHOLD_INFO,
  ESTIMAND_MISMATCH, INACCESSIBLE**.
- `inference_reading`: **DESCRIPTIVE_ONLY, EVIDENCE_COMPATIBLE,
  NOT_CERTIFIED_FROM_AVAILABLE_EVIDENCE, NEEDS_OTHER_VALID_METHOD,
  NOT_EVALUABLE, AMBIGUOUS**.
- `cp_eligibility`: **ELIGIBLE_IID_FIXED, DIAGNOSTIC_ONLY, NOT_ELIGIBLE, UNKNOWN**.
  Missingness reasons: **NOT_REPORTED, INACCESSIBLE, AMBIGUOUS, NOT_APPLICABLE,
  CAN_ONLY_INFER_FROM_ROUNDING, EXTRACTION_PENDING, UNVERIFIED_SOURCE**.
- `threshold_selection_policy`: **FIXED_BEFORE_TEST, DEVELOPMENT_SELECTED,
  EVALUATION_SELECTED, ORDER_STATISTIC_CERTIFIED, UNKNOWN** (the codebook's
  `threshold_policy` vocabulary under the requested template column name).
- `n_provenance` and `k_provenance`: **EXPLICIT, DERIVED_EXACT_WITH_EVIDENCE,
  NOT_REPORTED, AMBIGUOUS**.

Unknown numeric cells are blank/null with a reason, never zero. Strict integer
n/k reject booleans, require 0<=k<=n, and cite locators. Never infer counts from
rounded rates or a pooled total. Record evaluation/grouping units, benign label
definition, comparator and selection protocol before binomial interpretation.
Multiple claims/evaluation populations use separate source-linked rows, but a
paper counts at most once toward each feasibility gate.

Claim classification must preserve all six distinctions: **NONE** is an
observed absence of a relevant claim; **DESCRIPTIVE** states an observed FPR;
**OPERATING_TARGET** names a nominal threshold target; **ASSURANCE** explicitly
asserts statistical/population confidence; **FORMAL_GUARANTEE** invokes a
theorem-based guarantee; **AMBIGUOUS** records unclear wording. Where source
access prevents establishing a claim type, keep it unknown (blank/null with
`INACCESSIBLE`), not NONE. PDF-access status is separate from any claim that
can be established from an accessible official version; abstract-only wording
must remain provisional until its full context can be checked.
Neither a title promising safety nor a nominal target silently becomes an
ASSURANCE. Classify the proposition separately from whether its evidence
supports it, and preserve uncertain classifications for human adjudication.

A descriptive 0/111 is not an erroneous guarantee; U95>B does not prove FPR>B.
CP applied after adaptive threshold selection is not automatically certification.
Independent groups may be fewer than rows. A different valid theorem/estimator
requires review under its own assumptions, not automatic CP criticism.

## Prespecified feasibility and continuation gates

For the **statistical-assurance headline**, require at least **3 of 10** papers
with reconstructable relevant benign n **and observed k**, and at least **2 of
10** with explicit ASSURANCE or FORMAL_GUARANTEE propositions. Otherwise
`STOP_ASSURANCE_HEADLINE`. Two OPERATING_TARGET papers alone do not pass.
These are proposed feasibility heuristics, not significance tests.

Compute the two paper counts separately, each with the fixed denominator ten
and each paper counted once. Only explicit **ASSURANCE** or **FORMAL_GUARANTEE**
claims enter the assurance count; NONE, DESCRIPTIVE, OPERATING_TARGET and
AMBIGUOUS never do. Unknown/inaccessible evidence cannot be counted as a
verified assurance or reconstructable n/k pair. These counts describe this
pilot's feasibility, not prevalence in the research literature.

`GO_DESIGN_ONLY` to design a larger independently verified study requires ALL:
the above counts; a question demonstrably distinct from prior art; at least one
substantive source-supported, human-verified anomaly **or** reproducible
generalizable methodological pattern beyond the CP floor/omitted interval;
and a feasible human-verification plan.

An anomaly requires a specific quoted population assurance proposition, full
source/method/assumption interpretation, and evidence incompatible with that
method **under its own assumptions**, or an independently checked explicit
numerator/denominator/wording inconsistency. A pattern needs a specified
evaluation-design mechanism with corroborating source-backed examples.
Descriptive zero events, U>B, missing denominators, unclear threshold protocol,
or a different valid estimator are not anomalies. Use neutral language.

Before labeling any substantive discrepancy, retain this source-specific
review record: (1) the exact version and proposition locator with a short quote
or precise paraphrase; (2) its estimand, population and decision/group unit;
(3) the threshold-selection procedure and required assumptions; (4) the
statistical method actually asserted; and (5) a reproducible contradiction
under **that method's own assumptions**, or an explicit internal count/wording
inconsistency. The human must check the source, interpretation and calculation.
Missing intervals alone, an inconclusive upper CP bound, descriptive 0/111,
or an unknown protocol cannot satisfy this record. If an assumption cannot be
established, record the uncertainty rather than infer an erroneous assurance.

Otherwise use `STOP_ASSURANCE_HEADLINE`, `CONDITIONAL_NEW_QUESTION`, or
`AWAITING_HUMAN_VERIFICATION`. A target/reporting-quality pivot needs a newly
approved prospective question and criteria. An equivalent accessible audit
triggers `PRIOR_ART_STOP`. Report **counts and source-specific examples only**;
no ten-paper percentages, literature prevalence, representativeness,
misconduct inference or journal-readiness claim. GO authorizes design only.

## Human ownership and independent sequence

The human must approve domain, queries/indexes, period/cutoff, version policy,
sentinels, caps, missing-PDF rule, freeze/selection mechanics and GO/STOP
conditions before B1. At least six selected papers need independent human
re-extraction from original PDFs. Every potentially critical paper-specific
finding needs human source/method checking before any public use.

- **B1 (later authorization):** lock approved protocol, snapshot/hash/screen,
  select ten IDs/versions, select six human IDs, supply blank sheet, then STOP.
- **Human offline:** complete the six privately, **outside every Codex-readable
  directory, chat or connected workspace**, without seeing Codex counts/labels.
  Do not upload the sheet yet.
- **B2a (later authorization):** after the human reports offline completion
  while keeping the sheet hidden, Codex independently extracts all ten without
  accessing any human sheet, commits its unchanged first-pass extraction/hash,
  reports that SHA, then STOP.
- **B2b (later authorization):** only after that commit may the human provide
  the previously completed sheet. Preserve both unchanged originals and use an
  append-only adjudication log. If human results were visible to Codex before
  its extraction commit, mark independence **COMPROMISED**. No human check means
  **AWAITING_HUMAN_VERIFICATION**, never PASS.

Do not upload, link, paste or expose the human's completed sheet to any
Codex-readable surface before the independently completed B2a extraction is
committed. B1's six-paper human worksheet remains blank apart from ID/version
metadata; no Codex numerical outcomes or claim labels accompany it.

Stage A ends here. Approval of a draft is not a human extraction, completed
pilot, prospective scientific result, runtime-fix approval or paper submission.
