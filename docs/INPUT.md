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

## Optional: anything else

Every other column is carried into the JSON record untouched and used in no
computation. Timestamps, model versions, prompt hashes, reviewer names — keep
them in the file.

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
| only one class present | which class |
| a `group` column with a blank cell | the row |
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

**Nothing leaves your machine.** No network calls, no telemetry, no uploads. The
file is read, the arithmetic is local, and the record is written next to it.

---

## What you get back

A terminal summary and a JSON record carrying: the status, the budget and
confidence level, your input's shape, the certified threshold and its
Clopper-Pearson upper bound, and — when certified — recall, precision, flag rate
and lift, each with a 95% interval.

Two rules the output always follows:

- **No rate without an interval.** A point estimate on its own is not a
  measurement, and none is printed.
- **Recall and precision travel together.** Neither is quotable alone, and lift
  is never shown without the flag rate it was computed at.

## What a warrant does not say

It bounds the false-positive rate **on the distribution you supplied**. If your
production traffic differs from the file — a different mix, a different period,
a different model version — the bound describes the file, not the traffic. That
is a property of every measurement, and it is why the record names your input
and its base rate.
