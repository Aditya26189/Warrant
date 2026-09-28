# The input contract

Warrant certifies a detector from **scores and labels**. You produce the scores;
Warrant tells you what they are worth at a false-positive budget you choose, or
refuses to say.

That boundary is deliberate. It means Warrant works against a detector nobody
here has ever seen, including one behind a closed API where no probe can exist.

---

## The three columns

A `.csv` or `.jsonl` file. One row per item. Three required columns:

| column | type | meaning |
|---|---|---|
| `id` | text | Unique per item. Duplicates are refused, not merged. |
| `label` | `0` or `1` | Ground truth. **`1` means the detector should fire on this item.** |
| `score` | number | The detector's output. **Higher must mean more likely to be class 1.** |

### Get the polarity right

These are the two ways to produce a confidently wrong answer, and both are
silent:

- **`label = 1` is the thing you are looking for** — the hallucination, the leak,
  the bad answer. Not "the response was fine". Inverted labels do not produce an
  obviously broken result; they produce a detector that looks strongly
  *anti*-predictive, which reads as a real finding.
- **Higher score = more likely class 1.** If your detector emits a "confidence
  this is safe" score, negate it before you get here.

Warrant cannot detect either mistake for you. Nothing in the data distinguishes
an inverted detector from a genuinely terrible one.

### A minimal file

```csv
id,label,score
req_00001,0,0.02
req_00002,1,0.91
req_00003,0,0.31
req_00004,1,0.77
```

Both classes must be present. A file of all-`0` has no false-positive rate to
bound; a file of all-`1` has no recall to measure. Either is refused with that
explanation.

---

## Optional: `group`

If your items are not independent — several turns from one conversation, several
fields from one document, several tickets from one customer — add a `group`
column naming the cluster.

It changes the **unit of inference**. Two hundred items from twenty
conversations are twenty units of evidence, not two hundred, and certifying as
though they were two hundred would overstate what you have by an order of
magnitude.

```csv
id,label,score,group
turn_1,0,0.11,convo_A
turn_2,1,0.88,convo_A
turn_3,0,0.09,convo_B
turn_4,0,0.14,convo_B
```

**Groups must be equal-sized.** The cluster-level bound only dominates the
item-level one when they are; with unequal sizes it is *anticonservative* —
it would promise a tighter false-positive rate than your data supports. Warrant
raises rather than certifying, and tells you to either equalise the groups or
drop the column and accept that items are treated as independent.

## Optional: `label_2`

If a second reviewer labelled some of your items, add their label as `label_2`:
`0` or `1` where they reviewed the item, **blank** where they did not.

```csv
id,label,score,label_2
item_1,0,0.11,0
item_2,1,0.88,
item_3,1,0.91,0
item_4,0,0.14,
```

It is **measured beside the warrant and changes nothing in it.** `label` is what
certifies; the status, threshold, bound and every rate are identical with or
without `label_2`, whatever it says. What you get is:

- **kappa** between the two reviewers over the double-labelled items, with the
  number of pairs it rests on; ungrouped files retain the paired-bootstrap
  interval, while grouped files carry only descriptive agreement (below);
- how many of those pairs sit in each class, and a warning if either class has
  none -- double-label both, or disagreement about that class goes unmeasured;
- at the certified threshold, how many double-labelled **flagged positives** the
  second reviewer calls clean and how many **unflagged negatives** they call
  positive, and what the certificate's confidence would be if each of those
  disputes were an error in `label`;
- if only some of each were double-labelled, an upper bound on how many in the
  whole file would be disputed, assuming the double-labelled ones were picked at
  random from their pool. The bounds narrow as more are double-labelled, and the
  confidence evaluated at them is a sensitivity, not a joint confidence.

A disagreement is not an error, and an agreement is not a correct label. Warrant
cannot see whether your reviewers were blind to the score, or how you chose the
items to double-label; the record says so.

**On a grouped file** the record keeps the observed pair table, raw agreement
and descriptive sample kappa. These describe the reviewed pairs, not population
agreement or label correctness. Population interval endpoints are null,
`interval_computed` is false, and `interval_reason` explains why: resampling
related pairs as independent is unsupported (`DECISIONS.md` 201). The record
names both `n_pairs` and kappa's `n_groups`, counting only groups containing a
second review. A group with no second review adds no reviewed unit. Undefined
kappa remains null with its own reason, separately from the withheld interval.

Second-review disputed counts and their whole-file extrapolation remain
uncomputed for grouped files. Primary-label sensitivity still counts whole-group
relabellings where every group carries one label; that calculation is unchanged.
See [LIMITATIONS.md](LIMITATIONS.md) section 3.6.

A `label_2` column that is blank on every row is rejected: that is an export
mistake, not a second review.

**On `warrant recheck`** the same column gives the same kappa and, at the
warrant's threshold, the same disputed counts, with this file's lower bound if
every dispute were an error and whether that would have revoked. And every
recheck whose bound holds says how many labels of each kind would have to be
wrong for it to have revoked (`DECISIONS.md` 198). A recheck that does not revoke
is still an absence of evidence of breach; the counts say how far this file is
from showing one.

**Every certificate, with or without `label_2`, says how far it depends on its
labels.** Warrant picks the lowest threshold whose bound clears your budget, so
the certificate sits at the edge of it. Two label errors flatter it: a clean
item labelled `1` and flagged (a false positive counted as a hit), and a
positive item labelled `0` and not flagged (a clean negative your file has and
the truth does not). The first costs more per error; the second is the one that
realistic label noise makes material on a large file, because unflagged
negatives are most of it. For each, the summary prints the confidence at which
the budget still clears after one error, and how many it takes to fall below
90%, 80% and 50%; see `DECISIONS.md` 197. It is not computed on a refusal, where
it would be a count of relabellings that turns the refusal into a warrant. On a
grouped file it is counted in whole groups when every group carries one label,
and not computed when any group holds both.

## Optional: anything else

Every other column is read, checked, and **not kept**: neither its name nor its
values appear in any record Warrant writes, and none is used in a computation.
Checked means that a duplicate or blank column name, or a row with a missing or
extra field, is refused rather than silently resolved, since otherwise one of two
same-named columns would win without anyone choosing it. This page
used to say such columns were carried into the record untouched, and that was
wrong -- `examples/certifies.csv` has a `captured_at` column that no warrant
written from it contains.

So timestamps, model versions, prompt hashes and reviewer names belong in **your
own retained copy of the file**, not in the warrant. If the record must be tied
to that copy, see [EVIDENCE-HANDOFF.md](EVIDENCE-HANDOFF.md): a `certify` warrant
does not yet bind the rows it was issued on.

---

## What gets rejected, and what gets refused

These are different, and the difference matters.

**Rejected — the file is unreadable.** Exit code 2. Fix and re-run.

| what | message names |
|---|---|
| missing a required column | which columns, and which were found |
| a label that is not 0 or 1 | the row and the value |
| a score that is not a finite number | the row and the value |
| an empty cell in a required column | the row and the column |
| duplicate `id` values | the offending ids |
| a duplicate column name, after surrounding spaces are removed, or a duplicate key within a JSON line | the file, or the line, and the field |
| a blank column name in the CSV header | the file |
| a CSV row with more or fewer fields than the header | the line, and both counts |
| malformed CSV, such as an unclosed quote | the line |
| only one class present | which class |
| a `group` column with a blank cell | the row |
| a `label_2` that is not 0, 1 or blank | the row and the value |
| a `label_2` column blank on every row | what to do instead |
| unequal group sizes | what to do instead |

Nothing is coerced, filled or dropped. A blank is not a zero and `0.7` is not a
label.

**Refused — the file is fine and the evidence is insufficient.** Exit code 0.

A false-positive budget is a promise, and promises need evidence. Certifying
`FPR <= 0.01` at 95% confidence requires **at least 299 clean negative items**
even if the detector never fires on any of them; at `FPR <= 0.05` it is 59. If
you have fewer, no threshold can be certified at that budget — however good the
detector is.

Warrant says so, tells you the number it needed and the number you have, and
exits 0. That is the tool working. It is not an error, and it does not mean
your detector is bad — it means this file cannot prove it either way.

The requirement is `log(alpha) / log(1 - budget)`, and it grows fast as the
budget tightens:

| budget | clean negatives needed |
|---|---|
| 0.20 | 14 |
| 0.10 | 29 |
| 0.05 | 59 |
| 0.02 | 149 |
| 0.01 | 299 |

---

## Running it

```bash
python warrant.py certify --input your_scores.csv --budget 0.05
```

Or after `pip install -e .`:

```bash
warrant certify --input your_scores.csv --budget 0.05
```

| flag | what it does |
|---|---|
| `--input`, `-i` | your file |
| `--budget`, `-b` | the false-positive rate you want bounded |
| `--out`, `-o` | where to write the JSON record (default: beside the input) |
| `--quiet`, `-q` | suppress the summary, print only the record path |
| `--require-warrant` | exit non-zero on a refusal, for CI that wants that |
| `--frontier` | instead of certifying one budget, show every budget on the standard grid in exact counts |
| `--from-frontier RECORD` | certify a budget you picked from that frontier record, at the level the frontier held it to |

### Choosing a budget

Choose the budget **before** you look at the file if you can. If you want to see
what each budget costs first, run `--frontier`: it certifies every budget on a
grid and reports exact counts (flagged, caught, missed, false positives) with no
rates to estimate. Reading it and then picking a budget is a selection, so each
row is held to a stricter level, and a budget picked from it should be certified
with `--from-frontier`:

```bash
python warrant.py certify --input your_scores.csv --frontier
python warrant.py certify --input your_scores.csv --budget 0.05 --from-frontier your_scores.csv.frontier.json
```

A plain `--budget` run beside a frontier record for the same file prints a notice
asking whether you picked the budget from it.

### Verify a retained certificate

Keep the scored export and certificate, then replay the material fields:

```bash
warrant verify --warrant your_scores.csv.warrant.json --input your_scores.csv
```

For a certificate issued with `--from-frontier`, also pass the retained
`--frontier your_scores.csv.frontier.json`. `VERIFIED` exits 0. A changed row,
changed material field, changed configuration, or missing required evidence
reports `MISMATCH` or `UNVERIFIED` and exits 1; malformed input exits 2. Legacy
certificates without `input.evidence_sha256` cannot be verified this way.

The digest covers the **ordered effective rows**: ids, labels, scores, optional
groups and second labels. Reordering rows changes the digest because the seeded
bootstrap uses row positions. The input path and unused extra columns are not
covered. Verification checks arithmetic and consistency against files you
supply; it does not authenticate their author, creation time or custody.

To make a recheck perform this source check before measuring a new batch:

```bash
warrant recheck --warrant your_scores.csv.warrant.json --input next_batch.csv --certificate-input your_scores.csv
```

If the certificate was selected from a frontier, add
`--certificate-frontier your_scores.csv.frontier.json`. A failed or missing
source check exits 2 and writes no recheck. Without `--certificate-input`, the
recheck still runs, but its `prior_warrant.certificate_verification` reads
`NOT_CHECKED`. Every new CLI recheck also records
`prior_warrant.warrant_sha256`, the canonical digest of the exact certificate
it read, and `now.evidence_sha256` over the **new** batch's ordered effective
rows. To independently replay an ordinary recheck:

```bash
warrant verify-recheck --record next_batch.csv.recheck.json --warrant your_scores.csv.warrant.json --input next_batch.csv --certificate-input your_scores.csv
```

Omit `--certificate-input` only when the record says `NOT_CHECKED`; a record
that claims source `VERIFIED` must replay the original certificate again. For
a selected certificate, also pass `--certificate-frontier` with its retained
frontier record. `VERIFIED` exits 0, `MISMATCH` or `UNVERIFIED` exits 1, and
malformed evidence exits 2. Legacy rechecks without a fresh-row binding and
chained rechecks return `UNVERIFIED`. This verifies arithmetic against the
files supplied, not their author, collection time or traffic provenance.

**Nothing leaves your machine.** No network calls, no telemetry, no uploads. The
file is read, the arithmetic is local, and the record is written next to it.

---

## What you get back

A terminal summary and a JSON record carrying: the status, the budget and
confidence level, your input's shape, the certified threshold and its
Clopper-Pearson upper bound, and — when certified — recall, precision, flag rate
and lift, each with a 95% interval, and how far the certificate depends on its
labels (above, under `label_2`).

Two rules the output always follows:

- **Population rates carry intervals.** Grouped reviewer agreement instead
  describes the observed pairs only and explicitly withholds its unsupported
  population interval; it is not presented as population evidence.
- **Recall and precision travel together.** Neither is quotable alone, and lift
  is never shown without the flag rate it was computed at.

## What a warrant does not say

It bounds the false-positive rate **on the distribution you supplied**. If your
production traffic differs from the file — a different mix, a different period,
a different model version — the bound describes the file, not the traffic. That
is a property of every measurement, and it is why the record names your input
and its base rate.

It also does not say:

- **that your labels are right.** It is exact about the `label` column and blind
  to its errors; the label-error ladders say how many errors it can take.
- **that it will stay true.** Test it on fresh labelled traffic with
  `warrant recheck`, or run a year of rechecks as one test with a chain. The
  README's *Keeping it true* section has the commands, and
  [METHODS.md](METHODS.md) §14–16 the reasoning.
- **that nobody edited it.** `warrant verify` recomputes the material fields
  against retained rows, but the record has no authenticated seal. Someone who
  controls both files can rewrite them consistently; keep your own custody
  evidence ([LIMITATIONS.md](LIMITATIONS.md) §3.7).

Every message the command can print, and what to do about it, is in
[TROUBLESHOOTING.md](TROUBLESHOOTING.md).
