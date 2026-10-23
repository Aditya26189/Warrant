# Bounded grader experiment

Read [the generated phase report](../../reports/PHASE-GRADER-P0-P1.md) and [observed summary](results/summary.json) first. This directory is an isolated experiment, outside Warrant's shipped CLI and certification pipeline. The report describes the result and its limits; this file describes replay.

The subsequent [runner hardening report](../../reports/PHASE-GRADER-HARDENING.md) records fixes prompted by a separate assistant review. Its evidence is archived under `hardening/`; the original `results/` packet is retained unchanged. The original report remains a historical account of its producing code.

The [P2 validation report](../../reports/PHASE-GRADER-P2.md) records additional-task comparisons, the stronger maximum-repair study, negative results and actual Harbor cancellation checks. Read its scope limits before replay. Its tested forced-cancellation policy left delegated Docker resources running. The subsequent [cancellation correction](../../reports/PHASE-GRADER-CANCELLATION.md) records the scoped runner fix and its validation separately, under `cancellation/`. P2 remains unchanged, experimental and without a comparative superiority or certification claim. Its protocol, modules and preserved evidence live under `p2/`.

## Inspect without execution

- `results/runs/`: all full Harbor invocations, outcomes, trial logs, CTRF records and collected candidate files. Host paths are redacted in these copies.
- `results/diagnostic/`: independent-oracle result and append-only observation journal, including all reduction attempts.
- `results/cases/`: byte hashes and exact candidate/repair patches.
- `results/environment/`: dependencies, wheel hashes, Docker version and installation logs.
- `results/evidence-manifest.json`: raw-copy and packaged-copy hashes. A packaged copy is not represented as byte-identical to a raw file if paths were redacted.

Terminal-Bench-derived files retain upstream canary comments and are covered by `results/TERMINAL_BENCH_LICENSE.txt`. Patches under `results/cases/` identify the changes made. Do not use this task or its solutions as uncontaminated model-training/evaluation data.

## Replay prerequisites

Use Linux or WSL with Python 3.12, Git, Docker Engine and Docker Compose. Windows can execute the diagnostic using Docker Desktop; full Harbor trials in the recorded run used WSL. Docker must have access to the task and output paths. Downloading packages/images requires internet; no paid API credentials, GPU or model are needed.

The retained Harbor archive contains deeply nested paths. On Windows use a short checkout path or Git's per-command `-c core.longpaths=true` option for checkout, staging and verification. The archive preserves original run layouts rather than renaming evidence paths.

Use a clean checkout of this experiment branch. The modules require clean Git provenance before scientific generation. Keep all generated tasks and run directories **outside** the source checkout. Do not write results over the retained packet; each run refuses an existing output directory. Scripts use only the Python standard library except for the separately installed Harbor runtime.

Create sibling checkouts named `terminal-bench-poc` and `harbor-poc`, pinned to the commits in `config.json`. Public sources:

- <https://github.com/harbor-framework/terminal-bench>
- <https://github.com/harbor-framework/harbor>

Install `results/environment/harbor-dependencies.txt` in a dedicated virtualenv, then install the pinned Harbor source with `pip install --no-deps /path/to/harbor-poc`. The original cached wheel hashes are recorded; a rebuild may differ. The complete original freeze records `harbor==0.24.0`; that version alone does not identify the pinned source revision, so the portable dependencies file deliberately excludes Harbor itself. Keep `HARBOR_TELEMETRY=0` (the runner also sets it).

The upstream Dockerfiles pin the base image and direct pytest packages. Their apt dependencies and all build tools are not snapshot-pinned; reproducing behavior does not imply a bit-identical image. The report states which image and dependency records were actually retained.

## Execute the comparison

From the experiment checkout, set paths for your machine. These examples are Bash:

```bash
WORK=/absolute/path/to/fresh-replay
TB=/absolute/path/to/terminal-bench-poc
HB=/absolute/path/to/harbor-poc
HARBOR_BIN=/absolute/path/to/venv/bin/harbor
mkdir -p "$WORK"
python -m unittest experiments.grader_poc.test_oracle experiments.grader_poc.test_reducer -v
python -m experiments.grader_poc.prepare_cases \
  --source "$TB/tasks/session-window-debug" --out "$WORK/cases"
```

Run each row below with `run_trial`; the row's name determines the output subdirectory. `nop` leaves the original broken implementation unchanged. `oracle` here is Harbor's name for installing the provided candidate via `solution/solve.sh`; it does **not** mean the candidate is semantically correct or that an LLM was queried.

| Run name | Case | Agent | Expected reward |
|---|---|---|---|
| original-001 | reference_original | nop | 0 |
| reference-001 | reference_original | oracle | 1 |
| omit-max-001 | omit_max_original | oracle | 1 |
| equivalent-001 | equivalent_original | oracle | 1 |
| omit-max-repaired-001 | omit_max_repaired | oracle | 0 |
| reference-repaired-001 | reference_repaired | oracle | 1 |
| equivalent-repaired-001 | equivalent_repaired | oracle | 1 |
| original-repaired-001 | reference_repaired | nop | 0 |
| omit-max-repeat-001 | omit_max_original | oracle | 1 |

Example:

```bash
python -m experiments.grader_poc.run_trial \
  --task "$WORK/cases/omit_max_original" \
  --out "$WORK/runs/omit-max-001" --name omit-max-001 \
  --tb-repo "$TB" --harbor-repo "$HB" --harbor-bin "$HARBOR_BIN" \
  --agent oracle --expected-reward 1
```

After the three accepting original-grader cases are present, execute the independently scoped check and reduction:

```bash
python -m experiments.grader_poc.diagnose \
  --runs "$WORK/runs" --cases "$WORK/cases" --out "$WORK/diagnostic"
```

The diagnostic binds the exact collected app hashes to completed accepting full trials, executes candidate code only in constrained containers, and records every observation. The partial oracle can return `UNKNOWN`; runtime errors remain errors and cannot establish a semantic disagreement. A failing control makes the result inconclusive. Read `outcome.json` and `attempts.jsonl`, not only the process exit code.

The hardened diagnostic creates an owned, labeled container before attaching to it, attempts removal in a `finally` path, and verifies absence. Failed cleanup invalidates the observation. Catchable interruption writes an attempt and final diagnostic receipt and stops the CLI with exit code 130. A supported checked trace with no disagreement yields `NO_COUNTEREXAMPLE_FOUND_IN_SCOPE`; this says nothing about untested inputs. `UNKNOWN` is a separate abstention.

The full-trial runner writes atomic final receipts with explicit `TIMEOUT`, `INTERRUPTED`, or `INFRASTRUCTURE_ERROR` states. Partial results remain available but cannot promote an incomplete run to success. On POSIX it sends SIGINT to its owned process group, then escalates after a grace period, including remaining Compose children. Its pinned-Harbor environment adapter assigns ownership to agent and separate-verifier resources without modifying task files. Cleanup reinspects exact ownership labels, removes only owned resources, and verifies repeated absence. It preserves prebuilt images and external volumes/networks. Failed or unverified cleanup blocks completion and remains in `ownership/cleanup.json` and `outcome.json`; no global prune is performed.

This cleanup scope is Linux/WSL with local Docker and trusted task definitions. Built-image tags and managed resource names are unique per invocation; this can reduce cache reuse. Windows containers, explicit container names, privileged/host-network services and non-public Harbor network policies are unsupported. Host failure, uncatchable process death, an unavailable Docker daemon, indefinitely delayed daemon work and filesystem failure remain outside the cleanup/receipt guarantee. Labels are operational ownership records, not a security boundary against Docker-daemon access. Shared layers and BuildKit cache are retained.

To rerun targeted failure validation under Linux/WSL, with fresh output paths:

```bash
python -m unittest discover -s experiments/grader_poc -p 'test_*.py' -v
python -m ruff check --no-cache experiments/grader_poc --exclude results --exclude hardening --exclude evidence --exclude cancellation
python -m experiments.grader_poc.validate_hardening \
  --runs "$WORK/runs" --cases "$WORK/cases" --out "$WORK/hardening-checks" \
  --tb-repo "$TB" --harbor-repo "$HB"
```

The failure fixtures deliberately sleep and emit partial results; they are synthetic process tests, not new grader experiments. The real witness/control replay reuses the frozen example. `package_hardening.py` archives that verification and the supplied prior review, with raw and packaged hashes; it refuses to overwrite its archive.

For the current actual-Harbor cancellation validation, run `python -m experiments.grader_poc.validate_cancellation --tb "$TB" --harbor "$HB" --harbor-bin "$HARBOR_BIN" --out "$WORK/cancellation-checks"`. It creates disposable tasks plus foreign-resource preservation controls and exercises agent timeout, agent interruption, separate-verifier interruption and a normal reference. See the correction report for the preserved invalid fixture attempt, exact outcomes and limitations. The earlier failure-validation command above remains a historical synthetic check, not the actual-Harbor gate.

`package_result.py` is the one-time closing assembler for the original workspace layout. It is not needed to reproduce the software result and refuses to overwrite the committed packet. Its input layout and generated report template are preserved so the original evidence assembly is reviewable. No automatic publication or integration command exists in this experiment.
