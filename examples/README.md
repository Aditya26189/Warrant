# Synthetic examples: certify, refuse and prepare an export

**These are synthetic demonstration files.** `certifies.csv` and `refuses.csv`
were drawn by `scripts/22_make_examples.py` from a seeded generator; the export
fixture is a small hand-written format example. Their numbers describe neither
a real detector nor a language model and are outside this project's claim
table. The first two show certification and refusal in under a minute.

Run the first two in order. The refusal is the more important outcome.

---

## 1. A detector that certifies

```bash
python warrant.py certify --input examples/certifies.csv --budget 0.05
```

400 items, 298 of them negative. A 5% budget needs 59 clean negative units, so
there is plenty of evidence, and the detector separates well enough to be worth
something at that budget.

You get a threshold, its Clopper-Pearson upper bound, and what the detector does
there — recall, precision, flag rate and lift, each with a 95% interval.

Read the lift line beside its ceiling. Lift is capped at `1 / base rate`, so on a
set where a quarter of items are positive the most any detector can achieve is
about 3.9x. A detector at 3.4x is close to the physical limit, not merely
"above 1".

---

## 2. A detector that is refused

```bash
python warrant.py certify --input examples/refuses.csv --budget 0.01
```

60 items, 37 of them negative, and a 1% budget needs **299** clean negatives.
No threshold on this file can be certified at that budget — not because the
detector is bad, but because the file cannot prove anything either way at 1%.

Warrant says so, names the number it needed and the number you have, and
**exits 0**. This is the tool working.

That distinction is the entire product. A system that always returns a number
returns one when it has no business doing so, and the number looks exactly like
the ones that were earned.

### Try the same file at a budget it can support

```bash
python warrant.py certify --input examples/refuses.csv --budget 0.20
```

A 20% budget needs 14 clean negatives and this file has 37, so the same data now
certifies. Nothing about the detector changed — only what you asked Warrant to
promise about it.

That is the trade the whole tool exists to make legible: **a tighter budget is a
stronger promise, and a stronger promise needs more evidence.**

---

## 3. Prepare a differently named export

`export_sample.csv` has an item identifier, text labels, a risk score, a
conversation grouping, some second reviews and a deliberately excluded note.
The mapping declares what each field means; Warrant does not guess polarity or
silently turn conversation segments into independent evidence.

```bash
python warrant.py prepare --input examples/export_sample.csv --mapping examples/export_mapping.json --out prepared-example
python warrant.py verify-prepared --input examples/export_sample.csv --mapping examples/export_mapping.json --prepared prepared-example
```

Inspect `prepared-example/scored.csv` and `manifest.json`. The scored file is a
canonical input for existing commands, while the manifest binds the retained
source, mapping and normalized bytes for local replay. This tiny fixture is a
format demonstration, not evidence for certification. Keep the source and
mapping; `verify-prepared` needs both. Pick another output directory if you
repeat `prepare`, because it will not replace a package. See the
[input contract](../docs/INPUT.md) for limits and sensitive-data handling.

---

## Then try your own

Three columns: `id`, `label` (0/1, where **1 means the detector should fire**),
`score` (higher = more likely to be class 1). See
[docs/INPUT.md](../docs/INPUT.md).

Nothing leaves your machine.

---

## Regenerating the certification examples

```bash
python scripts/22_make_examples.py
```

Seeded from `config.yaml`, so it reproduces `certifies.csv` and `refuses.csv`
exactly. The separate export fixture and mapping are hand-written. The
`.warrant.json` records these commands write are gitignored — they are outputs,
and they carry the git state of whoever ran them.
