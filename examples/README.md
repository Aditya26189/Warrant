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

## 4. Run a complete synthetic export handoff

`export_certifies.csv` is a row-for-row recoding of the seeded synthetic
`certifies.csv`: `item`, `review` and `risk` replace `id`, `label` and `score`;
`error` means class 1, `ok` means class 0. The mapping declares that the rows
are independent. `captured_at` stays in the retained source but is excluded
from the scored file. This is the **same synthetic evidence** as section 1,
not a second detector or evaluation set.

Run these commands from the repo root in PowerShell. The new directory in the
OS temp folder keeps generated records out of the checkout:

```powershell
$handoff = Join-Path $env:TEMP ("warrant-handoff-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $handoff | Out-Null
$prepared = Join-Path $handoff "prepared"
$warrant = Join-Path $handoff "prepared.warrant.json"

python warrant.py prepare --input examples/export_certifies.csv --mapping examples/export_certifies_mapping.json --out $prepared
python warrant.py verify-prepared --input examples/export_certifies.csv --mapping examples/export_certifies_mapping.json --prepared $prepared
python warrant.py certify --input (Join-Path $prepared "scored.csv") --budget 0.05 --out $warrant
python warrant.py verify --warrant $warrant --input (Join-Path $prepared "scored.csv")
```

The two `VERIFIED` results answer different questions. `verify-prepared`
replays the source-to-scored-file mapping from the retained export and mapping.
`verify` recomputes the certificate from the scored rows. The certificate
binds those effective rows, but does not bind `captured_at` or prove the
mapping, labels or independent-row declaration. Keep the source, mapping,
prepared directory and certificate together for this handoff.

---

## 5. Replay a refusal and detect an altered source

The four-row grouped export from section 3 is too small to certify. Use it to
exercise the same handoff with an honest `REFUSED` outcome. Run from the repo
root in PowerShell; all generated files stay in a new OS-temp directory:

```powershell
$refusalDemo = Join-Path $env:TEMP ("warrant-refusal-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $refusalDemo | Out-Null
$smallPrepared = Join-Path $refusalDemo "prepared"
$refusedRecord = Join-Path $refusalDemo "refused.warrant.json"

python warrant.py prepare --input examples/export_sample.csv --mapping examples/export_mapping.json --out $smallPrepared
python warrant.py verify-prepared --input examples/export_sample.csv --mapping examples/export_mapping.json --prepared $smallPrepared
python warrant.py certify --input (Join-Path $smallPrepared "scored.csv") --budget 0.05 --out $refusedRecord
python warrant.py verify --warrant $refusedRecord --input (Join-Path $smallPrepared "scored.csv")
```

Certification reports `REFUSED`: the four rows are only two conversation
groups, while the 5% budget requires at least 59 clean negative units.
Refusal exits 0, writes a record, and that record verifies. This does not
mean the detector was found bad; the example lacks enough evidence.

Now change one excluded source note while retaining the original prepared
package and record. The changed source is still well-formed CSV:

```powershell
$changedSource = Join-Path $refusalDemo "changed-export.csv"
Copy-Item -LiteralPath examples/export_sample.csv -Destination $changedSource
python -c "import sys; from pathlib import Path; p=Path(sys.argv[1]); p.write_bytes(p.read_bytes().replace(b'synthetic example only', b'changed example only', 1))" $changedSource
python warrant.py verify-prepared --input $changedSource --mapping examples/export_mapping.json --prepared $smallPrepared
python warrant.py verify --warrant $refusedRecord --input (Join-Path $smallPrepared "scored.csv")
```

`verify-prepared` now reports `MISMATCH` and exits 1 because the retained
source bytes changed. Certificate `verify` still reports `VERIFIED` and exits
0 because its effective scored rows did not change. These are two different
replay boundaries, not conflicting verdicts. Keep the untouched original
source for an ordinary preparation replay.

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
exactly. The four-row export fixture and mapping are hand-written.
`export_certifies.csv` is a labelled recoding of the seeded `certifies.csv`;
`tests/test_prepare_handoff_example.py` checks every row against that source.
The generated `.warrant.json` records these commands write are gitignored — they are outputs,
and they carry the git state of whoever ran them.
