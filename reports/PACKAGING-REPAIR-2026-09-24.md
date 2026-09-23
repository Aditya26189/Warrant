# Installed customer workflow repair

Completed locally on 24 September 2026. Branch:
`fix/installed-customer-workflow`. Production-code checkpoint:
`770078ac5dc78af92b7a27458ceb00c705222924`.

## Question and answer

Can a customer install Warrant without the research stack and execute the
documented customer workflows outside the repository?

Yes, for the workflows and local environment exercised below. The wheel now
contains its required modules and defaults. Installed certification, refusal,
second-label diagnostics, planning, ordinary/chained rechecks, chain verification
and release registration/evaluation/verification all pass their regression
checks in a fresh Windows Python 3.12 environment containing only customer
dependencies and build/test tools. Linux and minimum-version CI checks are
configured but have not been executed remotely during this work.

This closes the locally reproduced installation failure R1 in the
[independent review](PROJECT-REVIEW-2026-09-23.md). It does not close the review's
statistical or chain-safety findings. The tests exercise ordinary supported
workflows; they do not establish correctness for every adversarial case.

## Changes

- Included the missing `controlplane.sampling` package. A wheel-content check
  also found `controlplane.external` and `controlplane.gate` missing; both are
  included without adding runtime dependencies.
- Kept root `config.yaml` as the single maintained source. The setuptools build
  command copies its exact bytes into `controlplane/default_config.yaml`.
  Source archives include both the canonical file and the build helper.
- Customer commands load the installed resource when no explicit config is
  given. Source/editable checkouts retain their root defaults. An incidental
  `config.yaml` in the customer's working directory cannot change the estimator.
- Preserved explicit configuration and the research `load_config()` path
  semantics. Missing, malformed, incorrectly encoded or structurally invalid
  explicit configuration raises `ConfigError`; the CLI returns bad-input status
  rather than a traceback or silent fallback.
- Added installed-distribution regressions that build a wheel directly and
  rebuild another from an sdist, inspect their contents and execute the actual
  installed console entry point from a separate working directory.
- Added these tests to Linux customer CI on Python 3.11/3.12 and a dedicated
  Windows Python 3.10 minimum-version job.

The source configuration values, resolved configuration hash, statistical
methods, research datasets and frozen scientific artifacts were not changed.
The generated test-collection inventory was refreshed using its existing
generator; collection is not represented as full-suite execution.

## An additional provenance defect found during verification

Installing the first repaired wheel below the founder's unrelated checkout
made its records report that checkout's `dfa43d7` Git revision, although the
wheel was built from `7ea49f9`. This was a real ordinary virtual-environment
installation, not a mocked provenance result.

Decision 204 records the correction. Git metadata is now reported only when
the executing config module is tracked in the candidate repository. Installed
code outside tracked source reports unknown/null Git commit, branch, dirty
state and dirty paths. Unknown is not changed to a claim that the code is clean.
Existing source/worktree provenance and dirty-file checks still pass.

The installed test fixture now creates an unrelated committed consumer Git
repository above the package. It verifies that imports and produced records
do not borrow that repository's identity. This is a provenance-boundary check,
not package authentication. Retain the wheel's build manifest separately to
associate its digest with the source revision.

## Validation ledger

Each row is a separate completed check; overlapping tests must not be added
together as if they were distinct coverage.

| Check | Result | Scope |
|---|---|---|
| Installed-distribution suite in fresh minimal environment, after provenance repair | 11 passed, exit 0 | Direct wheel, sdist rebuild, console workflows, resource identity and unrelated-parent Git boundary |
| Configuration, release CLI, recheck-chain and decision-integrity suites after provenance repair | 65 passed, exit 0 | Source provenance, dirty-file behavior, records and existing chain contracts |
| Claim, test-inventory and README prose checks | 21 passed, exit 0 | Generated labels and retained claim consistency |
| Earlier configuration/CLI/release/packaging/decision regression batch | 72 passed, exit 0 | Initial installation repair before the additional provenance correction |
| Targeted lint | Passed | Changed runtime, build helper and test files |
| Ordinary installation of the final clean-source wheel | Passed | No research packages present; installed Git provenance unknown; real console certification succeeds on the synthetic example |

The final installed suite's JUnit file is retained locally at
`.venv/installed-workflow-provenance.xml` relative to the shared checkout.
The earlier run is `.venv/installed-workflow-minimal.xml`.
The minimal environment is `.venv/warrant-customer-verify`.

Test commands from the implementation checkout:

```shell
python -m pytest -o addopts= -q tests/test_package_install.py
python -m pytest -o addopts= -q tests/test_config.py tests/test_release_cli.py tests/test_recheck_chain.py tests/test_decisions_integrity.py
python -m pytest -o addopts= -q tests/test_claims.py tests/test_test_inventory.py tests/test_readme_prose_numbers.py
python -m ruff check controlplane/config.py tests/test_package_install.py build_support.py
```

For the minimal run, `python` was the interpreter in the fresh verification
environment, not the research interpreter. It contained NumPy, SciPy and PyYAML
plus pip/build/test tooling. Absence of torch, transformers, datasets, spaCy,
scikit-learn, matplotlib and Presidio was checked explicitly. Test-generated
fixtures are software checks and provide no production-performance evidence.

## Build receipt

The final candidate was built offline from a Git archive of the named
committed packaging paths at `770078ac5dc78af92b7a27458ceb00c705222924`.
No uncommitted source files were used. It was then installed normally into the
verification environment, with no dependency installation during that step.

- Local bundle: `.venv/wheels/installed-770078a/`, relative to the shared checkout.
- Wheel: `dist/warrant-0.2.0-py3-none-any.whl`.
- Wheel SHA-256:
  `94ffbdfed90e7ee3a69ecaa0ebd903ab06b095091d850dd4a2090da65dcdcaf3`.
- Canonical and packaged configuration byte SHA-256:
  `65fc9c507eae2737b880a83a7273274d7ba891520572f7d27188267589e9bca3`.
- Resolved configuration hash: `2640a176a26a80a0`.
- `build-manifest.json` records the source, build command, hashes and checks;
  adjacent logs retain build, installation, provenance and console results.

The earlier `installed-7ea49f9` bundle remains a superseded diagnostic build:
it predates the provenance correction. The candidate above remains local and
uses the existing development package version; it was not published to an index.
Its digest identifies this build, not a promise of byte-identical wheel rebuilds.

## Commit ledger and coordination

| Commit | Change |
|---|---|
| `1ca9244` | Decision 203: installed defaults and distribution acceptance checks |
| `871f4bc` | Package contents, canonical configuration resource and controlled config errors |
| `7ea49f9` | Installed-distribution regressions and CI coverage |
| `cfd8de9` | Generated collection count: 1,867 before, 1,885 after |
| `ddc6c47` | Decision 204: prevent unrelated Git provenance |
| `770078a` | Tracked-source provenance check and regression extension |

The inventory describes collection at `7ea49f9`. The subsequent provenance
repair extends existing tests without changing their collection count.

Work was isolated from the shared dirty checkout and Claude's worktrees. Main
remains at the reviewed baseline `cc1904e`; these commits have not been merged
or pushed by this session. The shared board carries status and handoff details.
The earlier approval-service usage-limit rejection delayed a commit; resuming
the session allowed that commit and subsequent checkpoints to complete.

## What this does not establish; open items

- No full-suite execution is claimed for this branch. Relevant regression
  suites passed; the prior full-suite audit remains evidence for its own
  earlier baseline only.
- Remote CI and Python 3.10/Linux execution remain to be observed. Configuring
  those jobs is not equivalent to executing them.
- Grouped confidence intervals and grouped second-review uncertainty, revocation
  precedence, concurrent chain publication, seal stripping and the remaining
  review findings are still open. A successful ordinary chain test does not
  resolve them.
- No production customer study, willingness to pay, funding outcome or broader
  enterprise-readiness claim follows from these software checks.

The next correctness work is the grouped-evidence repair specified in the
[Claude instructions](CLAUDE-INSTRUCTIONS-2026-09-23.md), coordinated with the
revocation and concurrency work. Preserve the scientific baseline and require
each repair to close its reproduced failure before expanding product scope.
