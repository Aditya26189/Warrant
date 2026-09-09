# Certifying on REDACT

[REDACT](https://arxiv.org/abs/2606.19881) (ServiceNow, 18 June 2026) is a
multilingual PII benchmark: 13,427 records, 324,078 entity annotations, 51 entity
types, 4,127 surface-form patterns, 25 languages. It reports **span-level F1** for
five detectors on a locked 1,000-record evaluation split, and releases that split,
the schema, the prompts and the harness.

This asks a different question of the same records: **at a false-positive rate
certified below *b* with 95% confidence, what recall does a detector achieve — or
can that not be certified on this evidence at all?**

Results: [`results/external/MATRIX.md`](../results/external/MATRIX.md), rows
prefixed `redact-`. Reproduce any of them with
`python scripts/23_certify_external.py --pairing <id>`.

---

## 1. The finding: a benchmark has a certification capacity, and F1 never shows it

Certifying a false-positive budget at 95% confidence requires a floor of clean
negatives, and the floor grows fast as the budget tightens:

| budget | clean negatives required |
|---|---|
| 0.20 | 14 |
| 0.10 | 29 |
| 0.05 | 59 |
| 0.01 | **299** |

REDACT's locked split holds **40 records per language**. So:

> **Within any single language, REDACT's locked split cannot underwrite a
> false-positive bound tighter than 10–20% for any detector, however good.**
> Pooled across all 25 languages it clears 1% comfortably.

Worked through on the types measured here:

| task | negatives, English only (n=40) | pooled (n≈1,000) |
|---|---|---|
| email | 18 | 332 |
| credit card | 36 | 893 |
| IP address | 35 | 934 |
| person | **5** | — (NLP-dependent, cannot pool) |

The person row is the sharp end: 35 of the 40 English records contain a name,
leaving **five clean negatives**. A 20% budget needs fourteen. **Every budget on
the grid is refused**, and no detector — Presidio, GPT-4.1, Claude — could have
been certified there. The refusal is about the evidence, not the detector.

**This is not a defect in REDACT.** Forty records per language is a
stratification built to estimate F1 across languages, and it does that well. It
simply does not carry the evidence for a tight per-language false-positive bound.

**And an F1 table cannot say so.** F1 is computed at whatever operating point the
detector already has; it never varies the threshold and it never asks how many
clean negatives underwrite the claim. Capacity is invisible to it. Naming which
budgets a benchmark can and cannot underwrite is what a certification pass adds,
and it applies to every future detector measured on that split, not just the five
reported.

---

## 2. What the scored rows say

Recall at the certified threshold. Pooled across 25 languages except where noted.

| task | recall at a 20% budget | n | evidence |
|---|---|---|---|
| email (`EMAIL_ADDRESS`) | **0.9894** [0.9812, 0.9969] | 991 | 659 pos / 332 neg |
| IP address (`IP_ADDRESS`) | **0.9524** [0.8906, 1.0000] | 997 | 63 pos / 934 neg |
| credit card (`CREDIT_CARD`) | **0.6667** [0.4286, 0.9091] | 908 | 15 pos / 893 neg |
| person (`PERSON`), English only | **REFUSED at every budget** | 40 | 5 clean negatives |

The credit-card interval is wide because only 15 records carry a complete card
number once partial forms are excluded — see §3.

### A secondary observation about score granularity

Presidio emits **eight distinct scores across 1,000 records**, 668 of them
exactly 1.0. Across twenty budgets each pairing yields one to three distinct
certified thresholds.

This follows from Presidio's published design — its recognizers return fixed
confidence values, with regex-plus-checksum at 1.0 and bare pattern matches
lower — so it is a restatement of documented behaviour rather than a discovery.
It is recorded because the *consequence* is worth stating for a buyer: **a
false-positive budget is not a dial you can set on a rule-based detector.** You
get the operating point the rules produce. If it does not meet your budget, no
amount of threshold tuning will move it there.

---

## 3. The correction

An earlier version of this document reported Presidio at **recall 0.0935** on
credit cards and explained it as the detector's Luhn checksum meeting a generator
that does not produce checksum-valid numbers. **Both halves were wrong**, and the
error was ours.

Running Luhn over REDACT's 132 gold card spans:

| digits | count | |
|---|---|---|
| 4 | 104 | last-four fragments |
| 5–8 | 11 | partial forms |
| 16 | 17 | full numbers — 11 pass Luhn, 6 fail |

**109 of the 132 spans are labelled `partial` by REDACT's own metadata.** The task
had counted a four-digit fragment like `7821` as a positive that Presidio missed.
Presidio's recognizer is built for full card numbers and **correctly** declines to
call four digits a credit card.

The replication argument ran the wrong way too. Two independent corpora returning
0.070 and 0.093 points at the detector or at the task construction — not at two
unrelated generators independently failing the same checksum.

**The fix.** The task is now three-way: positive on a `complete` span, negative on
no span at all, and **excluded** when the only spans are partial or obfuscated. A
record containing a last-four fragment cannot be scored either way — it does
contain card information, so a detector that fired on it would be penalised for
being right.

**Corrected: recall 0.6667 [0.4286, 0.9091]**, with 92 records excluded. Seven
times the withdrawn figure.

`Credit_Card_Numbers` is 82.6% partial; every other type measured here is under
11%, so the correction moves one row. It would have been the row a reviewer
opened first.

---

## 4. Three questions that carry no numbers

`redact-national-id`, `redact-passport` and `redact-high-tier` were run, produced
recall figures, and have been **withdrawn as category errors**. They are recorded
with a reason and no numbers.

- **National ID and passport.** Presidio ships `US_SSN`, `US_ITIN` and
  `US_PASSPORT`. REDACT's catalog spans 40+ national systems including Indian
  Aadhaar. A recall figure measures the coverage mismatch, not the detector — and
  pooling across 25 languages made it worse by filling the denominator with
  identifiers the recognizer was never asked about.
- **Sensitivity tier.** Presidio detects entity *types* and has no representation
  of a sensitivity tier, so a MEDIUM-tier email and a HIGH-tier one are the same
  event to it. Tier triage is **undefined** for an entity detector, not failed by
  one.

The rule that forced this: a cell reading `presidio-analyzer | HIGH-sensitivity |
0.000` gets screenshotted without the paragraph that qualifies it. Prose does not
travel with a number, so the number does not ship.

---

## 5. The gap this method has

Certification needs a score to threshold. That excludes the detector family that
wins on this benchmark.

| detector family | score | certifiable today |
|---|---|---|
| fine-tuned classifiers, probes | continuous | yes |
| GLiNER, OpenAI Privacy Filter | continuous | yes |
| Presidio | 8 discrete values | technically, but with 1–3 operating points |
| **GPT-4.1, Claude Sonnet** | **spans and types, no confidence** | **no** |

REDACT's own results put the LLM extractors well ahead. They emit no score to
threshold, so **the method as it stands cannot certify the detectors that
perform best.** That is a structural limit and it is the first question a
reviewer should ask.

There is a route and it is unbuilt: derive a score from **repeated sampling
frequency** (how often the entity is extracted across *k* runs at temperature),
from **logprobs** where a provider exposes them, or from a pass^k statistic. Each
turns a set-valued extractor into something rankable. None of it exists here yet,
and until it does the honest scope of this work is: *classifiers and rule
systems, not generative extractors.*

---

## 6. Two observations for the REDACT authors

**`record_id` is not unique in the released locked split.** 1,000 records carry
944 distinct ids; 55 collide. The colliding records are different documents
rather than duplicates — one inspected pair shares a generation configuration and
has a text similarity of 0.027 — so they appear to be independent items with a
clashing identifier rather than a corpus problem. It surfaced because
certification refuses a set with repeated ids, since repeats usually indicate
clustered items and treating clusters as independent overstates the effective
sample size.

**Six of 17 complete, full-length credit card numbers fail Luhn.** The generation
contract specifies that identifiers satisfy real-world checksum specifications.
For `Credit_Card_Numbers` at complete disclosure, 11 of 17 pass and 6 do not
(prefixes 4000, 2223, 4532×3, 4152). Small n, and the release gates cover
offsets, zero-entity rate, name decomposition, type compliance, multi-mention
completeness and a per-type floor — none audits checksum validity, so this would
not have been caught downstream of the generator's own self-check.

---

## 7. Method

**Task shape.** Record-level binary: does this record carry a complete span of the
type. Labels are REDACT's own annotations. A negative record still contains other
PII — the question is *"does this contain a card number"*, not *"is this clean"*.

**Pooling.** Presidio runs at `language='en'`, so scoring Hindi under an English
pipeline would measure the mismatch. Pooling across 25 languages is used only for
pure regex recognizers whose token is Latin-script regardless of surrounding
language — email, IP, credit card. `PERSON` is spaCy NER and runs English-only,
which is why it refuses. `PHONE_NUMBER` is excluded: its recognizer takes region
hints. The US-only recognizers are no longer pooled at all (§4).

**Mapping.** In [`controlplane/external/redact.py`](../controlplane/external/redact.py).
`Date_of_Birth` is deliberately unmapped — Presidio's `DATE_TIME` fires on any
date, so scoring it against a date-of-birth label would count every ticket
timestamp as a true positive of a different question.

**Reproducing.** REDACT is cloned to `~/.cache/warrant/benchmarks` at run time.
**Nothing is redistributed here** — no records, no per-item scores. REDACT's code
is MIT; its dataset terms support research, evaluation and auditing.
