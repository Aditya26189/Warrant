# Reproduction and evidence locations

The canonical source is `92f162a8fee29f8f65bdd9293269e0bacb4d6411`.
The final branch also contains the separately labeled post hoc explanation.
Use a clean checkout, Python 3.12 and tqdm (observed 4.67.1). Tests use pytest;
Ruff checks the scoped Python files. No model, GPU or paid API is required.

The committed evidence is
`results/unscored_trials/20261029-terminal-bench2`. Execution, source and request
indexes refer to hashed shards; do not treat an index CSV as the complete ledger.
The original byte-preserving task specification is
`context/task_spec.original.json`. The sorted context projection has the same
parsed contents but a different byte hash and cannot replace it in exact replay.

The retained external study directory contains `terminal` (all raw inputs and
historical receipts), `canonical-001`, `replay-001`, original baseline-verification
receipts and engineering logs. Its durable location is recorded in
`validation/external_data.json`. Raw configs, transcripts and exception traces
are outside Git; published ledgers contain selected scalar fields and hashes.
The baseline archive and original directory remain at the user-supplied paths.

## Exact cached replay

From a separate clean checkout at the canonical source commit, set the following
paths in PowerShell. Use a new output/validation destination for every invocation.

```powershell
$WarrantStudy = 'C:\Users\LawLight\Documents\Codex\warrant-unscored-study-20261029'
$WarrantReference = Join-Path $WarrantStudy 'canonical-001'
$WarrantReplay = Join-Path $env:TEMP 'warrant-replay-new'
$WarrantValidation = Join-Path $env:TEMP 'warrant-replay-new.json'
git status --porcelain
python -B -m experiments.unscored_trials.reproduce `
  --data-root (Join-Path $WarrantStudy 'terminal') `
  --config experiments/unscored_trials/config.json `
  --task-spec (Join-Path $WarrantStudy 'native-contract/terminal-bench-2-spec-20260515.json') `
  --reference-dir $WarrantReference `
  --output-dir $WarrantReplay --validation $WarrantValidation
```

This rejects dirty source, disables Python socket creation, verifies cached bytes
and compares every canonical file except invocation provenance. The retained
receipt reports 107 byte-identical files. It is assistant computational replay,
not independent human replication. It does not rebuild a current website score.

To generate the post hoc diagnostic from the final branch, again with clean
source and a new output path:

```powershell
python -B -m experiments.unscored_trials.explain `
  --data-root (Join-Path $WarrantStudy 'terminal') `
  --analysis-dir $WarrantReference `
  --output-dir (Join-Path $env:TEMP 'warrant-explanation-new')
python -B -m pytest experiments/unscored_trials/tests -q -p no:cacheprovider
python -m ruff check experiments/unscored_trials
```

The diagnostic uses hash-verified normalized trial ledgers and reverifies raw job
summaries. Its own provenance identifies that distinction; it does not adjudicate
the raw rewards anew or amend frozen primary results.

## Acquisition and public reproducibility limit

The source shards publish immutable URLs, byte hashes, original read limits,
timeouts and successful/failed receipt metadata. `fetch_batch.py` accepts lists
of `path`, `url`, `limit_bytes`, `timeout`; join these fields from source receipt
shards rather than passing the result-request shards directly. New payloads must
match the expected hashes. New retrieval receipts have new timestamps/hashes.

`acquire.py` prepares/executes the result census only after the retained metadata
listings, configs, their receipts and request manifests exist. Its adaptive
bounded acquisition is not a complete fresh-cache bootstrap command. Historical
failed receipts and the six original manifest contents cannot be reconstructed
from published hashes alone. The full retained cache supplies those inputs for
the user's exact replay; a fresh public clone alone does not reproduce every
canonical byte. A reviewed portable public input bundle remains packaging work
before any public artifact-readiness claim. This limitation is part of REPORT.

Do not overwrite the frozen cache to refresh acquisition. Use a separate copy,
preserve failures, enforce the aggregate 2 GiB ceiling including failed reads and
other sources, and retain any new source differences explicitly.
