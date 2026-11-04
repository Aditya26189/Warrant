# Reproduce the bounded feasibility evidence

Worktree: the local branch `research/agent-stopping-feedback-20261030`.
The successful acquisition/inspection source was
`6e96f4421cb78674ecf66d0c2fb5f271878d7f13`; configuration and module hashes
are in [acquisition.json](results/acquisition.json). Current source is unchanged
apart from closing documentation and retained evidence. No remote publication
was performed, so these instructions refer to the local checkout.

Python 3.12.10 was used with the existing psutil 7.1.0 installation recorded in the
receipt. The collector uses the standard library; psutil supplies the measured
Windows process high-water mark. Tests use pytest and Ruff. No model, tokenizer,
GPU, paid inference or full trajectory-corpus installation is required.

From the clean worktree root in PowerShell, choose a new directory outside that
worktree. The observed raw directory is its sibling `asf-data/final-001`.

```powershell
git status --porcelain
$ASStudy = 'agent-stopping-feedback-study'
$ASRaw = Join-Path (Split-Path (Get-Location).Path -Parent) 'asf-data/fresh-002'
python -B "$ASStudy/recon.py" --config "$ASStudy/config.json" --output-dir $ASRaw
if ($LASTEXITCODE -ne 0) { throw 'Acquisition failed; inspect the retained receipts.' }
python -B "$ASStudy/inspect_sample.py" --config "$ASStudy/config.json" `
  --acquisition "$ASRaw/acquisition.json" --label nebius_row0 `
  --output "$ASRaw/nebius_row0-summary.json"
if ($LASTEXITCODE -ne 0) { throw 'Nebius inspection failed.' }
python -B "$ASStudy/inspect_sample.py" --config "$ASStudy/config.json" `
  --acquisition "$ASRaw/acquisition.json" --label nvidia_row0 `
  --output "$ASRaw/nvidia_row0-summary.json"
```

The [configuration](config.json) lists the exact two card URLs pinned to source
commits and two one-row access URLs. HF's row endpoint does not document a
revision parameter: the code requires the *returned* X-Revision/body identity to
match the pin. If the service advances, it will reject the sample rather than
silently use a different release. This convenience endpoint is not a promise of
permanent tiny-row access to older revisions. The immutable original Parquet
URLs are retained in the [metadata notes](results/metadata-reconnaissance.json);
the study deliberately did not fetch their large message chunks.

Each request has a body cap and the combined body cap is 16 MiB. Advertised huge
responses are rejected before reading. Partial bodies and HTTP errors consume
the same aggregate budget and are retained. Raw text stays outside Git.
The inspector requires one accepted, complete revision-bound response, verifies
its body hash, rejects truncated cells and emits only safe schema/identity/count
evidence. It does not train or replay a stopping policy.

For offline reinspection, set ASRaw to the retained `asf-data/final-001` and run
only the inspector commands with *new* output filenames. Neither command
overwrites prior evidence. Original sample-body hashes are in
[source_manifest.json](results/source_manifest.json). Typed-feature and numerical
counts should agree; new invocation Git/environment metadata may differ.

Focused checks:

```powershell
python -B -m pytest agent-stopping-feedback-study/tests -q -p no:cacheprovider
python -m ruff check agent-stopping-feedback-study
```

The completed offline suite had 14 passing tests; no full repository suite was
claimed. Fixtures check revision identity, byte caps including failed reads,
source corruption, tracked clean source, truncation, outcome absence versus
zero, and exclusion of final/reference information from retained prefix-facing
summaries. Fixture labels are synthetic parser tests, not model results.

The first scripted acquisition failed before network access because a nested
Git path was checked from the wrong directory. The repair has a real nested-repo
regression; the later clean invocation succeeded. Engineering access errors,
the invalid early memory probe and quota interruption are retained in
[failure_history.json](results/failure_history.json). The metadata snapshot is
an explicitly labeled projection of helper notes with private paths replaced;
original and derived hashes are retained.

This reproduces the accepted small sample, not every exploratory browser search,
footer request or historical failure. Metered body bytes exclude unknown browser
traffic and are not complete wire-byte accounting. Peak values are per-process
measurements, not aggregate concurrent memory. Resources are in
[resources.json](results/resources.json). No larger experiment follows this STOP.
