# Portable numerical reproduction

The portable route regenerates the scientific tables from committed, reviewed scalar observations. It needs a clean checkout, Python 3.12 and tqdm (observed 4.67.1), an empty study-data destination, and no private cache, model, GPU or paid API. The input bundle is `experiments/unscored_trials/portable_inputs/`; its manifest identifies input roles, pinned original URLs/revisions, original and derived hashes, transformations and licenses.

For a new public checkout on Windows (choose a new path):

```powershell
git -c core.longpaths=true clone --depth 1 --single-branch `
  --branch research/unscored-trials-20261029 `
  https://github.com/Aditya26189/Warrant.git C:\path\to\warrant-report
Set-Location C:\path\to\warrant-report
git config core.longpaths true
```

The demonstrated validation used a fresh shallow local-file clone of the same
committed branch, not this HTTPS acquisition command. Normal Git cloning is the
only network step here; the numerical command itself uses the committed bundle.
From the repository root in an existing suitable Python environment:

```powershell
git status --porcelain
python -B -m experiments.unscored_trials.portable reproduce `
  --study-data-dir C:\path\to\new-empty-study-data
```

The command rejects dirty source and a nonempty destination. It locates the bundle in the checkout, verifies it, copies it into `inputs/`, regenerates tables in `numerical/`, compares them with the committed scientific reference, and generates `report/technical_report.md` and a pending human worksheet. `validation.json` records acquisition, integrity, numerical comparison and report generation separately, including failure details. Socket creation is disabled during the route; there is no network fallback.

For a machine that also contains the original private cache, add one `--forbid-path` argument per root to demonstrate that those inputs are unavailable to the Python run. The study test should forbid both the external study directory and the original baseline. Read-guard probes must fail with PermissionError and the receipt must record the number rejected. This is a guard against accidental Python file access, not an operating-system sandbox.

For a new environment, install `tqdm==4.67.1`; the portable route otherwise uses Python's standard library. Test/check tools observed here were pytest 8.2.2 and Ruff 0.16.6. The fresh test reused an existing suitable environment; it did not claim an isolated dependency installation.

## Minimal inputs and supported claims

| Input | Role in numerical regeneration | Boundary |
|---|---|---|
| `config.json` and `task_spec.json` | Frozen tolerance/channel, task identities, exact official task universe and expected Git revision | Config/task-spec byte hashes match the canonical inputs; no cohort choices are retuned |
| Manifest hierarchy projections | Exact disclosed submission/job/final-directory population; 321 pinned listing bindings | Original listing hashes attest omitted listing bytes; final-record completeness does not establish original execution completeness |
| `trials.json.gz` | 32,803 projected trial identities, task checksums, rewards/null states and exception classes; native means, eligibility, policies and all compatible bounds | No transcripts, exception messages/traces or agent kwargs; original hashes do not independently verify omitted content |
| `jobs.json.gz` | 245 job populations, counters, summary reward/exception indexes, metrics, public population selectors and source availability | One unavailable summary stays unavailable; summary agreement does not reconstruct website import or adjudication |
| Opaque config/system/semantic digests | Preserve comparisons of omitted configuration and exception semantics used in alias/conflict/configuration-disposition checks | These are original-derived attestations, not independently reconstructed meanings |
| Attribution, notices and license texts | Preserve third-party source attribution and modification notices | Dataset observations and task specification retain Apache-2.0; Warrant's code license does not relicense them |
| Committed reference tables | Expected scientific outputs used only after regeneration | No reference cohort, score or pair labels are imported as scientific inputs |

The reviewed bundle was exported from clean source `0313fadbb975f2995530d5454d51efd8830a8ed9`. Its manifest SHA-256 is `1f410807b14f171e5222138f6693c6c27ab6a99cc8bfc1b9998816813922264e`. The canonical configuration SHA-256 is `b00bbb68f957ee89345e1451f6d07243f276ce2c879491f5c993241e4b28f683`; original task-specification SHA-256 is `bd7ad58bb59954b8fffeecfc53651c8ebc116a50cb4ff0336d29bb09c812f6bc`. The final clean invocation source was `93f6f34e967c21d33d2b4586fe27339af0991dec`; its Python 3.12.10/tqdm 4.67.1 environment and module hashes are recorded in the receipt.

The exporter reread original payloads, verified original byte hashes, checked complete listing coverage, and tested equivalence between original and projected normalization/reconciliation. The reader verifies payload and row hashes, schema, pinned URLs, hierarchy and exact trial coverage. Actual committed trial projections contain only `job_id` within config and `exception_type` within exception objects. They contain no exception messages, traces, trajectories or environment/agent kwargs. All eight payload hashes and sizes were checked, as were the absence of local-user paths, credential assignments and transcript/trace fields in the expanded observation payloads. Those checks are a scoped inspection, not a general promise that hashes prove omitted source content.

## What is compared

Ten scientific tables are compared, including full-census native reconciliation, eligibility, weighting policies, all pair classifications, raw-population support and the separate post hoc whole-job explanation. The scientific summary fields and whole-job summary must agree. Numerical scalar spellings such as `1/2` and `0.5` may differ only when their exact rational values agree; identity strings remain exact. The whole-job table's `raw_ledger_shards` locator is excluded because it names the archival output layout, not an observation.

Historical download timestamps, failed-download receipts, conservative byte totals, invocation paths/time/environment and output shard/rendering bytes are provenance rather than numerical targets. The portable route does not invent replacement historical receipts. Report generation is a separate success condition and by itself does not prove numerical reproduction or source validity.

The [retained final receipt](../../../results/unscored_trials/closeout-20261029/validation/portable-validation.json) records an actual fresh checkout and empty-directory success: acquisition/integrity, ten scientific tables, 31 scientific summary fields, the full post hoc summary and report generation all passed. Both forbidden-root probes were blocked. The earlier first run also passed; the second run includes the final report presentation fixes, with no scientific quantity changes. A successful public numerical route supports regeneration from reviewed projections. It does not independently verify omitted original fields, recover original roster/retry lineage, establish exact submitted harnesses or reproduce historical website adjudication. Every human review conclusion/date remains PENDING.

## Separate archival replay

The original byte-preserving reference remains `canonical-001` in the retained external study directory. At canonical source `92f162a8fee29f8f65bdd9293269e0bacb4d6411`, the existing blocked-network replay compared all 107 canonical files except invocation provenance and found them byte-identical. This assistant computational replay remains valid for its exact unchanged source and cache inputs. It is separate from the portable route and is not independent human replication.

The following archival command requires the external cache and its original historical receipts. Do not pass the expanded published evidence directory as an exact reference: it contains later explanatory/validation files beyond the 107-file canonical set. Do not overwrite the frozen cache or canonical outputs.

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

## Focused validation

```powershell
python -B -m pytest experiments/unscored_trials/tests -q -p no:cacheprovider
python -m ruff check experiments/unscored_trials
python -B scripts/smoke.py
python -B scripts/verify.py --no-activations
```

Use accessible temporary fixture directories if Windows sandbox ACLs obstruct pytest setup; retain such setup failures. The final verify command checks README claims and frozen score-to-metric reproduction while explicitly skipping the activation tier. Do not call it a complete model/probe rerun. If the main documentation index changes, `python -B -m pytest tests/test_docs_index.py tests/test_smoke.py -q -p no:cacheprovider` is a relevant focused repository check. Actual check outcomes and retained failures are listed in the [closeout report](../../../reports/PHASE-UNSCORED-CLOSEOUT-20261029.md) and [check receipt](../../../results/unscored_trials/closeout-20261029/validation/checks.json). Only scoped tests were run; this is not a claim that the complete repository test suite passed.
