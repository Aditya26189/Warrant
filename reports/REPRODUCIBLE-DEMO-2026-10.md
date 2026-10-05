# Synthetic export handoff: reproducible short demo

Run from the repository root with the declared Python dependencies installed.
The input files in `examples/` are synthetic. This demonstrates local
representation, replay, a supported measurement and an explicit refusal; it
does not measure a deployed detector or validate anyone's labels.
This 2 October run prepared a four-row file and certified separate examples.
The later [complete synthetic handoff](../examples/README.md#4-run-a-complete-synthetic-export-handoff)
certifies the prepared output itself and replays both boundaries.

```powershell
$demoDir = Join-Path $env:TEMP ("warrant-demo-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $demoDir | Out-Null

python warrant.py prepare -i examples/export_sample.csv `
  --mapping examples/export_mapping.json -o (Join-Path $demoDir "prepared")
python warrant.py verify-prepared -i examples/export_sample.csv `
  --mapping examples/export_mapping.json --prepared (Join-Path $demoDir "prepared")

python warrant.py certify -i examples/certifies.csv -b .05 `
  -o (Join-Path $demoDir "valid.json")
python warrant.py certify -i examples/refuses.csv -b .01 `
  -o (Join-Path $demoDir "refused.json")
```

Expected: `PREPARED`, then `VERIFIED`; the two separate certification examples
write `VALID` and `REFUSED` records. The four-row prepared export is only a
format example; it is not the input to the valid certification. A refusal is
an ordinary result and exits zero unless `--require-warrant` is specified.

To show that replay binds the source bytes, copy and change one source score:

```powershell
$editedExport = Join-Path $demoDir "edited-export.csv"
Copy-Item -LiteralPath examples/export_sample.csv -Destination $editedExport
$sourceText = [System.IO.File]::ReadAllText($editedExport)
[System.IO.File]::WriteAllText($editedExport, $sourceText.Replace('0.10', '0.11'))
python warrant.py verify-prepared -i $editedExport `
  --mapping examples/export_mapping.json --prepared (Join-Path $demoDir "prepared")
$LASTEXITCODE
```

Expected: `MISMATCH: prepared package differs from retained inputs` and exit
code `1`. The copy has the same original bytes before the one-character change,
so the failed replay is attributable to changed source content. This is an
integrity check, not an authentication signature.

These commands were run on Windows against clean `87070b6` on 2 October 2026.
All four expected statuses appeared; the tampered replay exited `1`. On that
first attempt, the managed sandbox denied its normal OS-temp parser copy;
rerunning the same commands with normal filesystem permissions succeeded.
The run left only ignored local demo files. The installed-wheel path is
separately covered by `tests/test_package_install.py` and the Phase 30 report;
this demonstration runs the source CLI.
