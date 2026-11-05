# Testing and verification

## A green suite answers a bounded question

Tests can establish that specified cases satisfy implementation contracts.
They do not by themselves establish sampling assumptions, correct labels,
statistical coverage, external validity or research novelty.

The current system uses several verification layers because each detects
different failures. A collection count is an inventory, not an executed pass.

## Verification layers

| Layer | Purpose | Representative source |
|---|---|---|
| Input rejection | Malformed, nonfinite, duplicate or unsupported evidence cannot silently enter | [Intake contract](../../controlplane/intake/contract.py) |
| Unit and property tests | Exercise formulas, invariants and boundary cases | [Core tests](../../tests/) |
| Negative controls | Ensure deliberate faults, wrong labels or meaningless features can fail | [Controls](../../controlplane/validation/controls.py) |
| Artifact equality | Resolve each README field and compare at stated precision | [Claim checker](../../controlplane/report/claims.py) |
| Independent point oracle | Recompute frozen ranking/count points using a separate algorithm | [Audit tests](../../tests/test_documentation_audit.py) |
| Metric replay | Rebuild supported metric blocks with their retained protocol | [Reproduction](../../controlplane/report/reproduce.py) |
| Installed-package tests | Exercise a real wheel and source-distribution rebuild | [Packaging tests](../../tests/test_package_install.py) |
| Fresh clone | Detect dependence on untracked local state | [Clone gate](../../controlplane/report/clean_clone.py) |
| Documentation build | Check navigability, references, source paths and manuscript build | [Documentation workflow](../../.github/workflows/docs.yml) |

## Negative controls matter

A successful run alone does not show that a harness could detect a fault.
The research controls include padding faults, shuffled labels, null features,
canary regressions and deterministic replay.

Their interpretations differ. Shuffled-label and null-feature controls test
whether the analysis can produce a null result when useful signal is removed.
Canaries are deliberately selected regression tripwires, not independent
quality evidence. The code records a power/precision condition for null controls;
reaching a cap without resolving the null is not a pass.

The audit has negative cases too: missing or ambiguous evidence, wrong values,
invalid score hashes, undefined metrics, source changes during generation and
unsupported claim families must not produce a clean passing receipt.

## Publication and integrity tests

Arithmetic tests are insufficient for an evidence tool. The suite also covers
interrupted publication, changed records, concurrent writers, head continuity,
schema versions and real installed execution.

Examples include [atomic publication](../../tests/test_atomic_publication.py),
[chain publication](../../tests/test_chain_publication.py) and
[chain integrity](../../tests/test_chain_integrity.py).
These tests defend the represented local workflow. They do not authenticate
an external deployment or prove absence of a hidden fork.

## CI environments

The core workflow separates minimal-dependency customer jobs from the larger
research environment. It also checks the advertised minimum Python version
through a Windows installed-wheel path.

The research workflow executes the assurance, unscored-trial and
stopping-feedback suites independently. Their green jobs establish retained
software checks, not external confirmation of the studies' conclusions.

The documentation job builds this handbook and checks the paper/tooling.
Documentation dependencies do not become customer runtime dependencies.

See [core CI](../../.github/workflows/ci.yml),
[research CI](../../.github/workflows/research.yml) and
[docs CI](../../.github/workflows/docs.yml) for exact selections.

## Run the relevant checks

```shell
python -m pytest tests/test_documentation_audit.py -q
python -m pytest tests/test_claims.py tests/test_docs_index.py tests/test_reports.py -q
python -m ruff check controlplane/ scripts/ tests/ warrant.py
python scripts/smoke.py
python scripts/verify.py --no-activations
```

The full core suite is:

```shell
python -m pytest tests/ -q
```

The research suites are separate invocations:

```shell
python -m pytest -q experiments/assurance_semantics/test_exact.py
python -m pytest -q experiments/unscored_trials/tests
python -m pytest -q agent-stopping-feedback-study/tests
```

Use the declared environment. A customer-only environment is not expected
to contain the full model-extraction stack.

## Interpreting verification tiers

The standard verifier distinguishes:

1. README values against retained artifacts.
2. Supported metric blocks recalculated from frozen scores.
3. Deeper reproduction from extraction caches.

An absent optional cache produces a skipped activation tier. It is not a pass.
The score tier does not rerun issuance controls or prove that the score vectors
came from the claimed model.

The documentation oracle adds independent point arithmetic. It still does not
independently validate bootstrap intervals or labels.

## Known expected failures and warnings

The retained Linux native-policy regression for an undefined entrypoint is
marked as an expected failure and names the underlying third-party native
abort (Decision 145). This is disclosed behavior, not an ordinary passing test.

Warnings, expected failures and skips must retain their reasons. A baseline
release's counts describe its exact source; they must not be presented as the
current count after tests change.

## Choose useful tests

Add a test when it guards a behavior that can plausibly fail: an independent
formula, an ambiguity, a publication interruption or a compatibility boundary.
Avoid tests that merely assert the current wording of a paragraph.

For documentation, test real links, complete source coverage, parser-derived
flags, generated notebook consistency and honest evidence status. Those are
maintenance contracts that matter to a reader.
