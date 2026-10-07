# Phase 45 — Opt-in portable certify handoff

Phase 45 adds a bounded local reviewer packet for the already supported
`prepare` → `certify` path. A holder can explicitly permit copying the original
source export, mapping, prepared rows and manifest, certificate and optional
frontier into a new directory. Creation replays both existing verifiers before
and after copying. Verification checks the exact file tree and byte digests,
then replays both links again. The result is a portable *consistency* check,
not an authenticated attestation, a release record or a commercial finding.
The change is additive: existing commands, estimators and committed research
artifacts were not edited.

## Why this bounded extension

The prior [packet design review](PACKET-DESIGN-REVIEW-2026-10.md) correctly
observed that `verify-prepared` and `verify` already answer the separate
source-to-row and row-to-certificate questions. The operational gap was that a
second person had to gather the correct originals and companion files, then
choose both commands and the optional frontier correctly. The founder's
7 October instruction authorized a concrete product extension despite the
unclosed demand gate. Decision 236 records it as a product experiment rather
than observed customer need. The implementation deliberately excludes release,
recheck and chain workflows; these have different registration and evidence
requirements, and a single generic packet would imply they share semantics.

Current official [LangSmith evaluation documentation](https://docs.langchain.com/langsmith/evaluation-types)
and [MLflow evaluation documentation](https://mlflow.org/docs/latest/genai/eval-monitor)
already describe datasets, evaluation, summary metrics and review feedback.
Their existence rules out presenting a CSV export, precision/recall or a
review workflow as novel. The [in-toto](https://github.com/in-toto/attestation/blob/main/spec/README.md)
and [Sigstore](https://docs.sigstore.dev/about/bundle/) specifications make
clear that subject digests alone are not authenticated origin. No incumbent
account or configured customer packet was inspected, so whether this local
replay changes a reviewer's decision remains unknown. The separate
[claim audit](CLAIM-AUDIT-2026-10-07.md) records numeric and market limits.

## Contract and behavior

`warrant handoff create` requires `--input`, `--mapping`, `--prepared`,
`--warrant`, a new `--out` directory and `--include-sensitive-input`. The
opt-in is intentional: `prepare` excludes unmapped values from scored rows,
but the original export in this packet still contains them. A certificate
selected from a frontier also requires `--frontier`. The command first runs
`verify_prepared` on the retained source, mapping and prepared directory,
then `verify_certification` on the scored rows and certificate. Any mismatch,
legacy unbound certificate or missing frontier is refused before creating the
destination. A valid refused certificate can pass replay and remains a refusal.

The destination is reserved with an exclusive directory creation. It contains
one `source.csv`, `source.jsonl` or `source.ndjson`, `mapping.json`,
`prepared/scored.csv`, `prepared/manifest.json`, `warrant.json`, optional
`frontier.json`, and `handoff.json`. The completion manifest has a version,
workflow identity, source name, fixed member roles and lowercase SHA-256
digests. File writes are flushed and synced; the manifest is written last.
A copy or post-copy replay failure leaves an incomplete directory, which the
verifier refuses. The command never replaces an existing destination. It
streams file copying and hashing in bounded chunks, although the inherited
`prepare` verifier still parses its inputs in memory.

`warrant handoff verify` requires the exact root and prepared member sets,
regular files and directories, no member symlinks, an unambiguous manifest
schema, fixed relative names and valid digests. Changed bytes are `MISMATCH`
with exit 1. Missing, unexpected or malformed evidence is an input error with
exit 2. Matching digests alone are insufficient: the verifier calls both
underlying replayers; a consistent but legacy/unbound certificate returns
`UNVERIFIED` with exit 1, and a changed original with a recomputed packet hash
still fails preparation replay. A `VERIFIED` packet exits 0 and says only that
the retained evidence recomputes. It does not change the certificate verdict.

## Test evidence ledger

| Check | Source state | Observed result |
| --- | --- | --- |
| `python -m pytest tests/test_handoff.py -q -p no:cacheprovider --basetemp <workspace temp> -o addopts=--strict-markers` | Feature commit `0cb5c13` plus the test's Windows symlink fallback | 18 passed, zero skipped, 141.77 s. Includes valid/refused/frontier packet, five changed members, malformed manifest, absent/extra/symlink members, opt-in, no overwrite, source mutation during copy and forged matching digest cases. |
| Adjacent preparation, public handoff, certification, frontier and CLI regression modules, same pytest flags | Clean source through `5f34030` before report/test edits | 110 passed, 0 failed, 306.38 s. The modules were `test_prepare`, `test_prepare_handoff_example`, `test_certify_verification`, `test_certify_from_frontier`, `test_frontier`, `test_frontier_groups`, `test_frontier_selection` and `test_cli_records`. |
| `python scripts/verify.py` (exact `make verify` recipe on a Windows host without GNU make) | Clean `5f34030` | Exit 0. `TIER|1|claim_table|OK|92/92`; `TIER|2|frozen_scores|OK|25/25`; `TIER|3|activations|SKIPPED|0/0` because its ignored cache is absent. |
| `python -m pytest tests/test_package_install.py::test_installed_handoff_replays_without_checkout -q -p no:cacheprovider --basetemp <workspace temp> -o addopts=--strict-markers` | Feature and installed-test source, with report draft uncommitted | 1 passed in 70.59 s. Offline direct wheel and rebuilt-sdist wheel were constructed; the installed console entry point ran outside the checkout, denied absent opt-in, verified a copied packet and rejected changed source bytes. |
| Decision, docs, inventory and phase-report pytest modules, same flags | Clean inventory commit `01c8350` | 176 passed in 18.27 s, zero failures. |
| `python scripts/smoke.py` | Clean `01c8350` | 7/7 passed; provenance reported `dirty=False`. |
| `python scripts/verify.py --no-activations` | Clean `01c8350` | Exit 0; claim table 92/92, frozen scores 25/25, activation tier explicitly skipped 0/0. |
| `python -m pytest --collect-only tests/ -q -o addopts=--strict-markers` | Clean `01c8350` | 2,256 collected in 26.74 s, with two SWIG import deprecation warnings and a shutdown deprecation warning. Collection is not test execution. |
| `python -m ruff check controlplane/intake/handoff.py controlplane/cli.py tests/test_handoff.py tests/test_package_install.py` | Feature and installed-test source | `All checks passed!` |

Initial sandboxed pytest attempts failed before test execution because
pytest could not create/read its temporary directory on this Windows runner.
They are environment failures, not passing or failing feature checks. Reruns
with the required filesystem access used the same test commands and produced
the results above. The native symlink attempt was unavailable on this Windows
host; the passing test exercises the `Path.is_symlink` guard through a
controlled fallback. A native POSIX symlink test and remote CI result remain
unobserved. Ruff and Git whitespace checks are recorded separately at close.

## What this does not establish

The packet does not establish that its author is a customer, that an export was
complete, that labels were independently reviewed, that the declared sampling
unit is correct, or that the certified file represents future traffic. A
person with write access can rewrite all members and the manifest together;
there is no key, signature, transparency log or trusted timestamp. Copying
the source increases the number of places sensitive identifiers can reside,
and `--include-sensitive-input` is consent to a local copy, not permission to
send it to a third party. No customer data was used in the tests, and a
synthetic packet is not a successful pilot.

This code does not cover a release's pre-registered threshold, evaluation
context or expiry, nor a recheck chain's complete history. It cannot be used
to imply that certification and release are the same decision. It also does
not scale the inherited statistical method to arbitrarily large exports:
`verify_prepared` builds canonical rows in memory, and expensive bootstrap
replay can take time. Performance on a real export size and filesystem must
be measured before a production service-level claim. The old full integrated
suite at Phase 43 and the new focused gates have different source commits;
neither is remote CI, a GPU re-extraction, a fresh 2,000-plus-test full-suite
run on this phase head, or proof of general correctness.

## Open items

An unaided reviewer still needs to run the packet and existing synthetic
valid/refused/changed-source paths and explain what each status means. A
permissioned customer export, existing incumbent packet, named decision owner,
label lineage, group unit, and retention/sharing rule are still absent.
Only such a side-by-side trial can show whether a bundled replay saves real
review effort or changes a recurring sign-off. The next engineering work
should be led by that observation; `reports/BUILD-PLAN-2026-10.md` retains
the demand stop gate. The stale draft preconditions in
`docs/PILOT-PROTOCOL.md` section 10 should be reconciled with already-fixed
chain defects before anyone treats it as a current checklist. The phase gate
above is local; remote CI, an unaided reviewer and an owner-approved real
packet remain open after the branch is merged or pushed.
