# Contributor instructions

Warrant is an installable local detector-evaluation toolkit with a reproducible
research harness. Begin with [README.md](README.md),
[the project overview](docs/PROJECT-OVERVIEW.md), and
[the current product state](docs/PRODUCT-STATE.md).

## Before editing

Read [CLAUDE.md](CLAUDE.md), [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md),
[docs/SPEC.md](docs/SPEC.md), and [docs/TASKS.md](docs/TASKS.md). The original
activation-only experiment is retained under round1/; it is not the entire
current project. Historical phase plans describe their original gates and do
not turn unbuilt features into current capabilities.

Read [COORDINATION.md](COORDINATION.md) and the local SHARED_CONTEXT.md when
present. Use the local coordination CLI to inspect current status and path
claims. Post your scope before overlapping edits, use a distinct session name,
and work in a separate worktree. Preserve other sessions' edits and private
review material. Stage named files only.

## Evidence and implementation rules

- Keep production intake, research experiments, and synthetic demonstrations
  distinct. Preserve explicit REPORT, STOP, blocked, and unvalidated outcomes.
- Never select thresholds, model layers, or hyperparameters using held-out test
  outcomes. Disclose every scoring under the applicable study protocol.
- Every published scientific number must trace to its source artifact. Never
  hand-edit a measured figure in README.md or results/RESULTS.md.
- Keep DECISIONS.md append-only. Research workstreams have their own protocols
  and decision logs; read them before changing their code or artifacts.
- Generate scientific artifacts only from clean committed source. Commit code
  first and artifacts separately with source provenance.
- Preserve frozen inputs, result bytes, source hashes, third-party attribution,
  and existing failure history. New analysis goes to a new destination.
- Scripts, notebooks, and demo runners call library code; public behavior
  belongs in controlplane/. Keep the customer CLI free of heavy ML imports.
- Respect grouping, label polarity, uncertainty, and the declared quantity.
  A checksum is not authentication; numerical replay is not human adjudication.
- Preserve existing line endings through byte-aware edits. Do not normalize the
  repository or rewrite committed scientific evidence for formatting alone.
- Follow the read-only module restrictions in CLAUDE.md. Never stage files over
  the repository's documented size limit, credentials, or real private labels.
- Commit logical changes with Conventional Commit subjects. Merge completed,
  tested branches without rewriting their history. Do not add tool co-authors.

## Release checks

Run the relevant focused tests and lint, then the core suite, smoke check, and
claim/frozen-score verification. Use scripts/clean_clone_gate.py for a final
clean-clone gate. Research suites are listed in experiments/README.md.

A collection count is not an executed pass. A skipped activation replay is not
a pass. Record the exact source commit, completed checks, and remaining limits
in a phase report. Current release context is in
[docs/BRANCH-INTEGRATION.md](docs/BRANCH-INTEGRATION.md).
