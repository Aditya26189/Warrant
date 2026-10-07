# Phase 47 — Clean-clone installed handoff acceptance

A local clone of the published Phase 46 commit reached a verified certify
handoff through the installed `warrant` executable. The same clone refused
source copying without opt-in and reported a mismatch after an excluded
source-only timestamp was altered in the copied packet. One first-run friction
was observed: the exact public example commands create two untracked output
directories inside the source checkout. `docs/INPUT.md` now says so and directs
real-data operators to use an approved private working directory outside the
repository. No product code, statistical method or frozen result changed.

## Setup and source identity

The source was `f332e349f1f0a44c562f01044409046edaade6e7`, the remote-verified
Phase 46 merge. From the shared root, `git clone --no-hardlinks --quiet .
.venv/phase47-run` made a disposable local clone; `git rev-parse HEAD` in it
returned that full SHA and `git status --porcelain` was empty before the run.
The clone contained the committed synthetic export and mapping only; the
root's untracked `ARC180_BRIEF.md` was not copied or edited.

Inside the clone, `python -m venv --system-site-packages .venv/first-run`
completed in 19.95 seconds. With `PIP_NO_INDEX=1`, `pip install --no-deps
--no-build-isolation -e .` built and installed `warrant-0.2.0` in 9.79
seconds. `--system-site-packages` reused already installed NumPy, SciPy and
PyYAML; this was an **offline installed-command** test from a clean source
clone, not a test of fetching dependencies into an empty machine. The
[Phase 45 installed-wheel regression](PHASE-45.md) separately builds a
non-editable wheel and rebuilt sdist wheel outside the checkout.

## Commands and observed results

The commands below use the venv executable directly instead of activating
PowerShell; arguments otherwise match the [input guide](../docs/INPUT.md).
The `wall` column is the command-runner wall time, not a throughput benchmark.

| Command after `.venv/first-run/Scripts/warrant.exe` | Exit | Wall | Relevant output |
| --- | ---: | ---: | --- |
| `prepare --input examples/export_certifies.csv --mapping examples/export_certifies_mapping.json --out prepared-certifies` | 0 | 3.63 s | `PREPARED prepared-certifies` |
| `certify --input prepared-certifies/scored.csv --budget 0.05 --out prepared-certifies.warrant.json` | 0 | 8.49 s | `WARRANT: VALID`; 400 synthetic items, 102 positive and 298 negative; threshold `0.864735`; bound `0.0479` from 8 flagged negative units; recall `0.5686`, precision `0.8788`, flag rate `0.1650`, lift `3.446`; record written. |
| `handoff create --input examples/export_certifies.csv --mapping examples/export_certifies_mapping.json --prepared prepared-certifies --warrant prepared-certifies.warrant.json --out reviewer-packet --include-sensitive-input` | 0 | 12.96 s | `HANDOFF reviewer-packet` |
| `handoff verify --packet reviewer-packet` | 0 | 7.60 s | `VERIFIED: effective rows and material certificate fields recompute` |

The valid synthetic certificate says its primary labels support the stated
bound on this file. It does not say the labels are true, rows are independent
in a customer's population, or that this performance transfers to another
detector. The packet's `VERIFIED` status replays the retained preparation and
certificate links; it does not sign them or upgrade a refusal to a pass.

The negative paths were run in the same installed environment:

* Without `--include-sensitive-input`, `handoff create ... --out
  denied-packet` printed `warrant: --include-sensitive-input is required to
  copy source rows`. PowerShell's `$LASTEXITCODE` was **2**, and
  `Test-Path denied-packet` was **False**.
* The disposable `reviewer-packet/source.csv` was changed only by replacing
  the first synthetic `captured_at` timestamp `2026-09-01T12:00:00Z` with
  `2026-09-01T12:00:01Z`. `handoff verify --packet reviewer-packet` printed
  `MISMATCH: member bytes changed: source.csv`; `$LASTEXITCODE` was **1**.
  The original committed export and the certificate were not changed.

After those documented commands, `git status --short` in the clone showed
exactly `?? prepared-certifies/` and `?? reviewer-packet/`. The warrant JSON
is ignored by the repository's `*.warrant.json` pattern. This untracked
result is expected for example output, but it makes scientific provenance
dirty if someone next runs an artifact generator in that checkout and raises
an avoidable risk of staging a copied source export. The guide now explicitly
identifies the directories and says to use an approved private location for
real inputs. This is a documentation fix to an observed first-run behavior,
not a change to the CLI's output-location contract.

## What this does not establish

No independent human was asked to interpret the valid, refusal and mismatch
statuses. The tester knew the implementation and the fixture was public and
synthetic. The clone was local, not a network fetch from GitHub, and the
venv inherited dependencies; this does not establish remote installation,
Python 3.10 or Linux behavior. The test covers the certify packet only. A
release packet, recheck history, production data controls, real throughput,
authenticated custody, buyer demand and willingness to pay remain unobserved.
The original source may contain sensitive columns in a real case, so the
approved private output location and sharing rule are customer decisions.

The test does not replace the Phase 45 feature regression suite, which covers
malformed and forged packets, nor the prior integrated full suite in Phase 43.
It is one fresh-clone acceptance check at a named source commit. It produces
no new research measurement and does not claim to close the October discovery
gate or the current plan's requirement for a permissioned export and actual
incumbent packet.

## Evidence ledger and open items

The source-identity, install, valid and negative command outputs are listed
above. The documentation/report/inventory gate completed separately in the
clean report worktree:

| Check | Source | Observed result |
| --- | --- | --- |
| `python -m pytest tests/test_reports.py tests/test_docs_index.py -q -p no:cacheprovider --basetemp <workspace temp> -o addopts=--strict-markers` | Report and input-guide draft | 167 passed, zero failures. |
| `python scripts/refresh_test_inventory.py` | Clean `be3da43` | 2,260 collected; collection is not execution. |
| Decision, report, docs and inventory pytest modules, same flags | Clean inventory commit `b54db34` | 180 passed in 18.28 s. |
| `python scripts/smoke.py` | Clean `b54db34` | 7/7 passed; provenance `dirty=False`. |
| `python scripts/verify.py --no-activations` | Clean `b54db34` | Exit 0: claim table 92/92, frozen-score recomputation 25/25, activation tier explicitly skipped 0/0. |

That gate tests source links and retained arithmetic, not customer utility.
Editing this ledger adds no tests; its report/link checks are repeated before
integration. The next useful observation is
an unaided reviewer completing the blank worksheet in
`reports/DISCOVERY-2026-10.md`. A real packet needs its owner's permission,
retention rule, independently sourced labels, score direction, group unit and
named recurring decision before any claim of customer utility.
