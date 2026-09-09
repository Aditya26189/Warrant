# Certifying on REDACT

[REDACT](https://arxiv.org/abs/2606.19881) (ServiceNow, 18 June 2026) is a
multilingual PII benchmark: 13,427 records, 324,078 entity annotations, 51 entity
types, 4,127 surface-form patterns, 25 languages. It reports **span-level F1** for
five detectors on a locked 1,000-record evaluation split, and it releases that
split, the schema, the prompts and the harness.

This is the same 1,000 records, asked a different question:

> Does this record contain a `<type>`, at a threshold whose **false-positive rate
> is certified below *b* with 95% confidence** — or can that not be certified on
> this evidence at all?

Neither question subsumes the other. F1 says how good a detector is at the
operating point it happens to have. A certified budget says what you are allowed
to promise about it, which is the thing someone signs.

Results: [`results/external/MATRIX.md`](../results/external/MATRIX.md), rows
prefixed `redact-`. Reproduce any of them with
`python scripts/23_certify_external.py --pairing <id>`.

---

## The finding

**A rule-based detector has no operating point to tune.**

Across twenty target budgets from 0.01 to 0.20, each pairing produced this many
*distinct certified thresholds*:

| detector | pairings | distinct operating points |
|---|---|---|
| `presidio-analyzer` 2.2.364 | 11 | **1 – 3** |
| `protectai/deberta-v3-base-prompt-injection-v2` | 1 | 15 |
| our own probe | 1 | 20 |

Presidio emits **eight distinct scores across 1,000 records**, 668 of them
exactly 1.0. Its confidence is a rule-fired indicator, not a rankable score:
there is no threshold between "the regex matched" and "it did not".

So a false-positive budget is not a dial you can set on it. You get the single
operating point the rules produce, and your budget either is or is not satisfied
there. Ask for something tighter and the only threshold that satisfies it sits
above the maximum score — flagging nothing, recall 0.0.

**This is a property of the design, not a defect.** A regex matches or it does
not, and Presidio never advertised a tunable curve. It is a procurement fact: if
a deployment must hit a 5% false-positive budget, a rule-based detector cannot be
moved to it, and no amount of threshold tuning will change that.

**An F1 table cannot show this.** F1 is computed wherever the detector already
sits; it never varies the threshold, so it cannot say whether the detector could
sit somewhere else. REDACT reports Presidio at 0.195 partial micro-F1 and that
number is right. It just does not carry the information that the number is the
*only* one on offer.

---

## What the results say

Recall at the certified threshold, pooled across 25 languages unless noted.

| task | recall at a 20% budget | note |
|---|---|---|
| email (`EMAIL_ADDRESS`) | **0.9895** [0.9812, 0.9957] | 668 positives of 1,000 |
| IP address (`IP_ADDRESS`) | **0.9091** [0.8361, 0.9697] | |
| passport (`US_PASSPORT`) | 0.2660 [0.1786, 0.3579] | US-only recognizer — see below |
| national ID (`US_SSN`/`US_ITIN`) | 0.1658 [0.1302, 0.2012] | US-only recognizer — see below |
| credit card (`CREDIT_CARD`) | 0.0935 [0.0392, 0.1495] | checksum — see below |
| person (`PERSON`), English only | **REFUSED at every budget** | n=40, 5 clean negatives |
| HIGH-sensitivity triage | recall 0.0 at every budget | not a task an entity detector claims |

### Three results that would be misread without their reason

**Credit card at 0.0935.** Presidio's credit-card recognizer validates a
checksum; REDACT's card numbers are synthetically generated. A generated number
that fails the checksum is one the recognizer is *designed* to reject. This
replicates: the same detector scored 0.070 on `ai4privacy/pii-masking-200k` in
earlier work, an independent synthetic corpus. **Two benchmarks, same cause.** It
measures agreement between one vendor's validation rules and another project's
generator, and says nothing about real card numbers.

**National ID at 0.1658 and passport at 0.2660.** Presidio ships `US_SSN`,
`US_ITIN` and `US_PASSPORT`. REDACT's catalog spans 40+ national systems,
including Indian Aadhaar. Presidio is being asked about identifiers it does not
claim to cover. **This is coverage, not accuracy**, and the mapping was declared
before the run for exactly that reason.

**Person, refused everywhere.** REDACT's English subset is 40 records and 35 of
them contain a person name, leaving **5 clean negatives**. Certifying a 20%
false-positive budget needs 14; a 1% budget needs 299. No threshold on five
negatives can be certified at any budget on the grid, so every one is refused —
regardless of how good the detector is. That is the tool working.

### The HIGH-sensitivity row, stated plainly

REDACT tags each entity `HIGH`, `MEDIUM` or `LOW`, and its headline is that the
rule-based detector is weakest where the stakes are highest.

Asked as a budget, the question becomes: can a threshold separate records
carrying HIGH-sensitivity entities from records carrying the same entity types at
a lower tier? **It cannot, and it could not in principle.** Presidio detects
entity *types*; it has no notion of a sensitivity tier, so a MEDIUM-tier email
and a HIGH-tier one are the same event to it. 262 of the 526 negative records
score exactly 1.0 — the same as most positives.

So this row is a statement about **whether tier triage is thresholdable with an
entity detector at all**. The answer is no. It is kept in the table because the
negative answer is the useful part, and it is not a Presidio result.

---

## What the split can and cannot underwrite

Certifying a 1% budget needs **299** clean negatives at 95% confidence; 5% needs
59; 10% needs 29; 20% needs 14.

REDACT's locked split holds 40 records per language. So within any single
language, no task here can support a budget tighter than 10–20%, whatever the
detector does. Pooled across all 25 languages it clears 1% comfortably:

| task | negatives, English only (n=40) | pooled (n=1,000) |
|---|---|---|
| Work_Email_Address | 18 | 464 |
| Credit_Card_Numbers | 36 | 893 |
| National_Identification_Number | 26 | 626 |

**This is not a defect in REDACT.** Forty records per language is a
stratification built to estimate F1 across languages, and it does that. It simply
does not carry the evidence for a tight per-language false-positive bound — and
nothing in an F1 table would tell you so. Saying which budgets a benchmark can
and cannot underwrite is the one thing this adds.

## Method, and the two choices that decide results

**Pooling.** Presidio runs at `language='en'`, so scoring Hindi under an English
pipeline would measure the mismatch, not the detector. Pooling across 25
languages is therefore used **only** for pure regex/checksum recognizers —
email, credit card, IP, `US_SSN`, `US_ITIN`, `US_PASSPORT`. `PERSON` is spaCy NER
and runs English-only, which is why it refuses. `PHONE_NUMBER` is excluded
entirely: its recognizer takes region hints, and that confound is not worth
arguing about.

**Mapping.** REDACT's 51 canonical types map onto Presidio's 19 supported
entities conservatively, and the mapping is in
[`controlplane/external/redact.py`](../controlplane/external/redact.py). Two
choices were declared before any run: the US-only recognizers above, and the
deliberate **exclusion** of `Date_of_Birth` — Presidio's `DATE_TIME` fires on any
date, so scoring it against a date-of-birth label would count every ticket
timestamp as a true positive of a different question.

## One observation for the REDACT authors

`record_id` is not unique in the released locked split: **1,000 records carry 944
distinct ids, so 55 collide.** The colliding records are different documents
rather than duplicates — one inspected pair shares a generation configuration and
has a text similarity of 0.027 — so they appear to be independent items with a
clashing identifier rather than a data-quality problem in the corpus itself.

It surfaced because certification refuses a set with repeated ids: repeats
usually mean clustered items, and treating clustered items as independent
overstates the effective sample size. Here the disambiguation is positional and
the original id is preserved.

## Reproducing

```bash
python scripts/23_certify_external.py --list
python scripts/23_certify_external.py --pairing redact-national-id
```

REDACT is cloned to `~/.cache/warrant/benchmarks` at run time. **Nothing is
redistributed here** — no records, and no per-item scores derived from them.
REDACT's code is MIT; its dataset terms support research, evaluation and
auditing.

Adding a detector or a task is three dataclasses in
`controlplane/external/registry.py`; the grid, the Clopper-Pearson
certification and the intervals are unchanged from every other row.
