# Two examples: one certifies, one refuses

**These are synthetic demonstration files.** They were drawn by
`scripts/22_make_examples.py` from a seeded generator. Their numbers describe
that generator — not any detector, not any language model, and nothing in this
project's claim table. They exist so you can see both outcomes in under a
minute.

Run them in this order. The second one is the more important.

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

## Then try your own

Three columns: `id`, `label` (0/1, where **1 means the detector should fire**),
`score` (higher = more likely to be class 1). See
[docs/INPUT.md](../docs/INPUT.md).

Nothing leaves your machine.

---

## Regenerating these files

```bash
python scripts/22_make_examples.py
```

Seeded from `config.yaml`, so it reproduces the committed files exactly. The
`.warrant.json` records these commands write are gitignored — they are outputs,
and they carry the git state of whoever ran them.
