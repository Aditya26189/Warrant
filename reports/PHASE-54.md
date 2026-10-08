# Phase 54 — Local test of the advertised Python 3.10 minimum

Warrant's [`pyproject.toml`](../pyproject.toml) declares `requires-python =
">=3.10"`. The [CI workflow](../.github/workflows/ci.yml) declares a Windows
Python 3.10 installed-wheel job, but the prior local customer-only suite ran
under Python 3.12.10 and the status of the remote CI run for the published
commit was unavailable. This phase created a workspace-local CPython 3.10.22
environment and ran the **same four test files** named by the Windows
`installed-minimum` job, plus the complete certify handoff module. On clean
source `7b32990035039e1de4b506ddc712f8c3e02afa0d`, **87 tests passed in
267.26 seconds**, with exit code 0. No product code, dependency contract,
statistical result or frozen score changed.

## Test environment and source identity

The isolated `test/phase54-python310` worktree began at the published Phase
53 merge. Its Git status was clean before execution. The shared root's
untracked `ARC180_BRIEF.md` was not copied into that worktree or edited. This
machine had only a system Python 3.12 interpreter. Docker's CLI was installed
but its Linux engine pipe was absent, so no Docker test is claimed.

The [uv Python-version documentation](https://docs.astral.sh/uv/concepts/python-versions/)
describes managed CPython downloads. `uv 0.12.23` was installed into an
ignored workspace bootstrap venv; it installed `cpython-3.10.22-windows-x86_64-none`
under the ignored `.venv/phase54-python-install` directory with `--no-bin`.
The test venv was created under `.venv/phase54-py310` with
`--managed-python --no-python-downloads`, so it used that installed runtime
without replacing the system interpreter or PATH. `UV_CACHE_DIR` and
`UV_PYTHON_INSTALL_DIR` were pointed under the workspace. The managed Python
distribution is an Astral `python-build-standalone` build, not the exact
CPython binary used by GitHub's Windows runner; this is one local
minimum-version environment.

The environment installed the three declared customer dependencies from
[`requirements-customer.txt`](../requirements-customer.txt), plus pytest,
setuptools, wheel and pip as test/build tools. Runtime checks reported Python
3.10.22, NumPy 2.2.6, SciPy 1.15.3, PyYAML 6.0.3, pytest 9.1.1 and pip
26.2.1. `importlib.util.find_spec` found none of `torch`, `transformers`,
`datasets`, `spacy`, `sklearn`, `matplotlib` and `presidio_analyzer` in that
venv. The exact dependency versions are observations from this run, not pins
or a claim that every allowed version works.

## Evidence ledger

| Check | Command/scope | Observed result |
| --- | --- | --- |
| Runtime identity | Isolated interpreter `--version` and `importlib.metadata.version` | CPython 3.10.22; the customer dependencies and test tools above. |
| Heavy-package availability | `importlib.util.find_spec` for the seven named research packages | Empty list. This does not inspect every possible transitive import. |
| Broad customer manifest, exploratory | Existing noncomment lines of `ci/customer-path-tests.txt` under Python 3.10 | Exit 2 during collection, before product tests ran: `tests/test_packaging.py` imports stdlib `tomllib`, unavailable before Python 3.11. This manifest is declared only in Linux Python 3.11/3.12 CI, so the result is a test-harness boundary, not evidence that the installed product fails on 3.10. |
| Declared installed minimum plus handoff | `python -m pytest tests/test_package_install.py tests/test_atomic_publication.py tests/test_chain_publication.py tests/test_chain_integrity_policy.py tests/test_handoff.py -q -p no:cacheprovider -o addopts=--strict-markers --basetemp <workspace temp>` | **87 passed in 267.26s**, exit 0, no warnings in the retained summary. The first four files are the Windows 3.10 CI selection; handoff is the extra module tested here. |

The test log and exit-code file were retained only under ignored `.venv/`
scratch. The installed-package tests build and exercise Warrant outside the
source import path; the atomic publication, chain publication and chain
integrity-policy tests check the surrounding local customer workflow. The
handoff module covers valid and refused packets, opt-in to source copying,
changed or forged members, destination preservation and incomplete
publication. These use synthetic fixtures, not customer exports.

The exploratory collection error is deliberately retained in this report.
`tomli` happened to be installed as a Python 3.10 pytest dependency, but the
repository's Linux customer manifest is not currently a Python 3.10 job and
no fallback import or new test dependency was added merely to expand that
undeclared matrix. The declared Windows minimum selection itself completed.

## What this does not establish; open items

This local pass does not establish a green GitHub Actions run on the published
merge, Linux behavior under Python 3.10, or compatibility with every version
allowed by the loose NumPy/SciPy/PyYAML ranges. It does not exercise the
research pipeline or re-derive frozen scores from GPU activations. The
customer-only venv had no model or Presidio stack, by design. The full
customer CI manifest was **not** run to completion on Python 3.10 because
the test collection error occurred first; it must not be counted as passing.

The tests also do not establish representative customer labels, permitted
source-export custody, an unaided reviewer, recurring decision use or buyer
demand. The next external gate remains the owner-permitted export and
same-decision incumbent packet in the
[discovery worksheet](DISCOVERY-2026-10.md). This phase narrows the package's
minimum-version uncertainty for the tested Windows files; it is not product
validation.
