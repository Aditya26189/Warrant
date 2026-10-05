# Phase 34 - Put the public handoff regression through the customer CI gate

The public synthetic export added in Phase 33 now runs in the lightweight
customer-path CI list. Before this phase, CI did not select the new
`tests/test_prepare_handoff_example.py` module, and its comment for
`tests/test_prepare.py` still described a 2 October run made before the Phase
32 edits. The changed module and the new handoff module were measured together
in a fresh Python 3.12 virtual environment before the CI list was changed.
The complete list then passed on the committed change. No certification
statistic, prepared-package format, or frozen research result changed.

## Question and scope

The question was whether an installed customer environment can keep exercising
the whole prepare, verify-prepared, certify and verify handoff without pulling
in the research stack. The new test's imports alone are not adequate evidence:
it starts CLI subprocesses and reads a prepared package. The repository's
`ci/customer-path-tests.txt` rule therefore requires execution in a minimal
environment before membership. Its 47 selected files are the same list that
the GitHub `customer-path` job expands; that job also runs on Linux with Python
3.11 and 3.12. This phase ran the Windows Python 3.12 side locally. It does
not claim a GitHub job ran for this local-only commit.

The test added in Phase 33 checks row-for-row derivation of the synthetic
export, both replay boundaries and the difference between source-only fields
and certified effective rows. Including it in CI preserves that contract
whenever a future change modifies intake or certification. The fixture remains
the same 400 seeded synthetic rows as `examples/certifies.csv`, not a customer
export or an additional independent measurement.

## Work and findings

I created a fresh Python 3.12.10 venv outside the checkout and installed
`requirements-customer.txt`, `pytest`, `setuptools>=68` and `wheel`, matching
the customer CI install. `pip freeze` showed NumPy 2.5.3, SciPy 1.18.1,
PyYAML 6.0.3, pytest 9.1.1, setuptools 84.0.0 and wheel 0.48.0, plus pytest's
small dependencies. An `importlib.util.find_spec` check returned false for
`torch`, `transformers`, `datasets`, `spacy`, `sklearn`, `matplotlib` and
`presidio_analyzer`. The focused command selected both preparation modules:

```text
<fresh-venv-python> -m pytest tests/test_prepare.py tests/test_prepare_handoff_example.py -q -p no:cacheprovider --basetemp <os-temp> -o addopts=--strict-markers
50 passed in 78.15s
```

Only after that measurement, commit `e7ab196` added the handoff test to
`ci/customer-path-tests.txt` and updated the stale comment. The complete
47-file list was then read from that committed file and passed to pytest in
the same venv. This includes acceptance, installed-package, preparation,
chain, release and statistical customer-path tests; the result was 1,033
passed, one runtime warning and no failures in 987.46 seconds. The warning
comes from `test_a_non_finite_update_raises_rather_than_asserting`, which
deliberately exercises a divide-by-zero path and asserts it raises. This
whole-list check detects interactions that the 50-test check cannot.

On clean `e7ab196`, `python scripts/smoke.py` passed 7/7. The available
`python scripts/verify.py --no-activations` tiers passed 92/92 README claims
and 25/25 frozen-score comparisons; cached-activation replay was explicitly
skipped. These checks establish that the CI manifest change did not alter the
committed result arithmetic or claim table. They are not fresh model
extraction. The source tree was clean for these checks.

## What this does not establish

The local run is Windows Python 3.12. It does not establish that the Linux
Python 3.11 or 3.12 jobs pass on GitHub, nor that a fresh third-party clone
completed the public handoff unaided. The 47-file subset is intentional; its
1,033 passes are not a replacement for Phase 33's full 2,206-test gate.
Adding a test to CI does not make the declared row independence or review
labels true. Preparation replay establishes byte agreement with retained
inputs; certificate replay establishes the recorded statistic from the
effective scored rows. Neither authenticates the source owner. There was no
real export, reviewer packet, or external user in this phase.

## Open items

The October plan's week-one gate calls for a user dry run. No human dry run
has been observed, and the discovery worksheet still has no supplied export,
label provenance, decision owner or declared real sampling unit. A real pilot
must expose whether those prerequisites exist before any domain-specific
adapter is built. The GitHub CI result for this local commit is also unknown
until the commit is published and the remote job actually runs. The frozen
activation tier remains unavailable in a clean clone without its cache or a
new GPU extraction; this phase did not infer that it passed.

## Ledger

| Change or check | Evidence |
|---|---|
| Fresh customer environment | Python 3.12.10; `pip install -r requirements-customer.txt pytest 'setuptools>=68' wheel`; package versions above; seven heavy-package lookups false |
| Focused measurement before CI inclusion | Both preparation modules, 50 passed in 78.15 seconds |
| CI manifest change | `e7ab196`; `ci/customer-path-tests.txt` adds the measured module |
| Complete committed customer list | 47 files, 1,033 passed, one warning, 987.46 seconds, exit 0 |
| Clean-source smoke | `e7ab196`, 7/7, exit 0 |
| Claim and frozen-score replay | `e7ab196`, 92/92 and 25/25; activation tier skipped, exit 0 |
