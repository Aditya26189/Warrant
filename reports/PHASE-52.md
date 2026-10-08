# Phase 52 — Certify handoff in customer-only CI coverage

The certify handoff regression module is now in
[`ci/customer-path-tests.txt`](../ci/customer-path-tests.txt), the manifest
executed by the Linux customer-path CI job. Before this change, the handoff
module existed and passed in the general suite, but the declared
minimal-dependency customer job did not include it. The change adds that
module only after measuring it in the existing isolated Python 3.12.10
customer environment. It changes no product behavior, dependency requirement,
statistical method, fixture label or frozen result.

## The gap and the measured choice

The [CI workflow](../.github/workflows/ci.yml) reads the manifest in its
`customer-path` job for Python 3.11 and 3.12 on Linux. The job installs
`requirements-customer.txt`, pytest and build tools, and checks that heavy
research packages are not installed. The earlier manifest included preparation
tests but omitted `tests/test_handoff.py`, even though the public workflow now
offers `handoff create` and `handoff verify`. The manifest's own rule says a
test file belongs there only after it has run in a minimal venv, because an
import scan can miss dependencies imported inside a test body. This phase
followed that rule instead of assuming the module was compatible from source
inspection.

From the clean Phase 51 merge `0e6446d3961ff8ca8edf75d295f416c5c458ac83`,
an isolated `test/phase52-handoff-ci` worktree was created. The already
isolated `.venv/customer-minimal-october` interpreter reported Python
3.12.10. Its installed packages were NumPy 2.5.3, SciPy 1.18.1, PyYAML
6.0.3, pytest 9.1.1, pip and build/test support packages; the explicit
`importlib.util.find_spec` check returned an empty list for `torch`,
`transformers`, `datasets`, `spacy`, `sklearn`, `matplotlib` and
`presidio_analyzer`. This was an existing customer-only environment, not a
fresh dependency-resolution test or a remote Linux runner.

The complete `tests/test_handoff.py` module then passed **21/21** in 102.12
seconds under that interpreter. It runs actual CLI subprocesses for valid and
refused packets and checks changed, missing, extra and forged members;
explicit source-copy opt-in; existing and nested destination preservation;
an interrupted copy without a completion marker; and the selected-frontier
record requirement. The module's symlink test has a Windows fallback when
symlink creation is not permitted. Passing this module is evidence about the
synthetic packet cases, not about real export custody.

After that measured run, commit `039cfcf` added the module to the manifest
and described it in [`docs/TESTING.md`](../docs/TESTING.md). The packaging and
documentation checks passed **79/79** before that commit. The manifest itself
has a test in `tests/test_packaging.py`; the newly added module was run again
as part of the whole manifest rather than accepted on the earlier isolated
run alone.

## Evidence ledger

| Check | Named source and command | Observed result |
| --- | --- | --- |
| Heavy-package availability | Phase 51 source, customer-only interpreter, `python -c` using `importlib.util.find_spec` for seven named packages | `python 3.12.10`; `heavy_packages []`. This tests package availability in that venv, not all possible transitive imports. |
| Handoff module before manifest edit | Phase 51 source, customer-only `python -m pytest tests/test_handoff.py -q -p no:cacheprovider -o addopts=--strict-markers --basetemp <workspace temp>` | 21 passed in 102.12 s; exit 0. |
| Manifest and doc guards | Edited Phase 52 worktree, `python -m pytest tests/test_packaging.py tests/test_docs_index.py` with strict markers and disposable workspace temp | 79 passed in 1.12 s; exit 0. |
| Complete customer manifest | Clean `039cfcf`, customer-only `python -m pytest $files -q -p no:cacheprovider -o addopts=--strict-markers --basetemp <workspace temp>`, where `$files` are the noncomment, nonblank manifest lines | **1,061 passed**, one warning, zero failures, in **627.45 s**; exit 0. |

The sole full-matrix warning was the deliberate divide-by-zero exercise in
`test_warrant_stats.py::test_a_non_finite_update_raises_rather_than_asserting`.
The result establishes that the complete current customer test manifest runs
in this local Windows Python 3.12.10 minimal environment with those installed
versions. It does not prove that the entire repository suite runs without the
research dependencies; the manifest is a selected customer-path subset.

## What this does not establish; open items

The CI workflow declares Linux jobs on Python 3.11 and 3.12, but this report
does not assert that a remote run for the published Phase 52 commit passed.
The local environment was created earlier and may differ from a new resolver
result. The Windows Python 3.10 installed-minimum job includes installed
package tests, but this specific full handoff module was not run under Python
3.10 here. A successful synthetic handoff test does not establish permission
to copy a customer's export, secure transport, authentication, independent
labels, representative sampling, an unaided reviewer result, buyer demand or
production traffic reliability.

The next externally meaningful gate is still the
[discovery worksheet](DISCOVERY-2026-10.md): a data owner, a permissioned
scored export, its label and grouping meaning, the configured incumbent's
same-decision packet, and an independent reviewer. Until those are supplied,
additional packet surfaces would be speculative. The local CI coverage change
closes a test-selection gap, not the commercial evidence gap.
