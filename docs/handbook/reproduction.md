# Reproduction guide

## Choose the intended level

| Goal | Inputs | Additional requirements |
|---|---|---|
| Read the evidence | Committed report, artifact and source references | No execution |
| Match table fields | README and named JSON artifacts | Customer numerical environment |
| Independently check point arithmetic | Frozen scores and audit registry | No model or GPU |
| Replay metric intervals | Frozen scores, config and historical metric protocol | Existing research/test dependencies |
| Reconstruct probe measurements | Original extraction caches and fitting context | Cached-activation environment |
| Regenerate features and answers | Model/tokenizer, source dataset and extraction settings | GPU, downloads and the full research environment |

A deeper level must be reported separately. An unavailable input does not
silently become a successful replay.

## Begin from committed source

Use a clean checkout or a separate worktree. Scientific receipts name the source
that generated them. A dirty tree cannot be described accurately by its HEAD
alone.

Keep generated copies outside the checkout:

```shell
python scripts/smoke.py
python scripts/verify.py --no-activations
python scripts/audit_documentation.py --out ../warrant-audit-copy
```

The destination must be new. Preserve the original retained records.
The [audit guide](claim-audit.md) explains exactly what the last command checks.

## Read a single claim

Open its [ledger entry](claims.md), then:

1. Identify the artifact, selector, raw checksum and recorded source.
2. Read the family classification and data origins.
3. Inspect the metric denominator and independent unit.
4. Check dirty flags, model identity and historical protocol.
5. Decide whether field equality, point replay or a deeper rerun is required.

A claim's listed command can be a checking entry point rather than a complete
regeneration recipe. Some commands need ignored caches or historical versions.
The family reproduction boundary states this explicitly.

## Frozen-score replay

The committed score sets retain labels, scores, question IDs and target
thresholds. Their hashes identify those vectors. The metric verifier uses
the retained protocol and seeds to reproduce supported blocks.

The independent oracle uses a separate pair-ranking/count implementation for
points. It does not reproduce intervals, model features, controls or the
scientific truth of labels.

## Cached-activation reproduction

The activation tier needs original caches not included in an ordinary clone.
It can rerun fitting and validation on the recorded features. The source,
configuration, split identities and software versions still matter.

The current model identifier is not a substitute for immutable historical
weights. Reconstructing features from a later download is a new execution
whose identity must be recorded, not silently called byte-identical.

## GPU extraction

The main notebook is generated from
[its reviewed builder](../../scripts/build_notebooks.py). It covers extraction,
later stages and collection of outputs. Its final discussion refers to
committed research evidence; it is not fabricated execution output.

The pilot notebook is separate because expensive reference extraction should
not be rerun merely to reach a small later pilot stage. Hardware, model access,
precision and dependency constraints belong to the extraction instructions.

Do not start a GPU run to verify a statement that frozen scores or a local
parser can settle.

## Closed research tracks

The unscored-trial study has a
[portable numerical route](../../docs/research/unscored_trials/REPRODUCING.md)
and source-license notices. It reproduces stated tables and summaries, not
original unseen attempts or official corrected rankings.

The grader experiments have pinned methods and task identities. Their
verification should preserve rejected candidates, controls and no-survivor
outcomes.

The stopping-feedback project closed at feasibility. Its software tests
are reproducible; an unrun policy experiment has no result to reproduce.

## Documentation and preprint

Build the handbook with the isolated documentation dependencies:

```shell
python -m pip install -r requirements-docs.txt
python -m mkdocs build --strict --site-dir ../warrant-handbook-site
```

Build instructions for the LaTeX preprint and archival package are in
[the paper directory](../../paper/README.md). Compilation requires the declared
TeX engine or a compatible TeX installation. A first Tectonic run may download
its pinned typesetting resources; later compilation can use its cache.

## What to record

Retain the exact source, command, environment, input identities, output
checksums, exit code and each skipped tier. Separate code and artifact commits.

A failed or interrupted attempt remains part of the history. A later successful
run can close the software issue without making the earlier attempt a pass.
