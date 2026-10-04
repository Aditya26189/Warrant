# Production-oriented QA checkpoint — 4 October 2026

This checkpoint tests the local Warrant software as a user would run it. The
tested source is clean commit `c3353344e162a9d438c2cefb09428594ba07f90a` on
Windows with Python 3.12.10. The [clean-clone record](../results/clean_clone.json)
was produced from that commit and committed afterward as `a6decca`. It is an
execution record, not a claim that the later documentation commit was itself
the source cloned for the full suite.

## Executed gates

| Check | Result | Evidence and scope |
|---|---|---|
| Tracked-file clean clone | **PASS**; 611 tracked files, smoke and two-test preflight exit 0 | `python scripts/clean_clone_gate.py --out <local QA record>`; source and clone HEAD matched. No ignored cache or working-tree file was copied. |
| Full repository suite in that clone | **PASS**, exit 0 in 2,871.55 seconds | The gate ran `python -m pytest tests/ -q`. The generated [inventory](../results/test_inventory.json) says 2,191 *collected*, not 2,191 passed; the gate's captured tail has no numerical passed/xfail summary. |
| Published-claim replay in that clone | **PASS**: 92/92 claims and 25/25 frozen-score comparisons | `scripts/verify.py` ran without an activation cache. Tier 3 is explicitly **SKIPPED**, 0/0, not counted as passed. |
| Cached-activation replay on the repaired source | **PASS**, 3/3 comparisons | `reproduce_frozen_set` revalidated the retained local cache against the repaired source. This uses an ignored local cache, which is deliberately absent from the clean clone. |
| Exact-head installed distribution | **PASS**, 18 tests in 298.93 seconds | `tests/test_package_install.py` built the wheel and sdist, installed the rebuilt wheel outside source, and exercised the installed `warrant` command under the minimal customer environment. |
| Minimal customer dependency matrix | **PASS**, 1,024 tests in 1,002.25 seconds | The `ci/customer-path-tests.txt` matrix ran in the isolated Python 3.12.10 environment holding NumPy 2.5.3, SciPy 1.18.1, PyYAML 6.0.3, pytest 9.1.1 and build tools. It ran at preceding clean source `60db5df`; later behavior changes were confined to the reproduction verifier, not the customer CLI paths. The exact-head installed-wheel run above separately checks the final distribution. |
| Static and dependency checks | **PASS** | `ruff check controlplane/ scripts/ tests/ warrant.py`, `git diff --check`, `pip check` in the minimal environment, and the CLI import check finding none of torch, transformers, datasets, spaCy, scikit-learn, matplotlib or Presidio. |

The customer matrix emitted one `RuntimeWarning` when
`test_a_non_finite_update_raises_rather_than_asserting` deliberately forced an
invalid betting grid and checked that the monitor raised `FloatingPointError`.
The full suite also emitted third-party SWIG deprecation warnings. Neither was
treated as a passing test in place of an assertion.

## Feature and failure-path coverage

| Surface | Executed checks | Result |
|---|---|---|
| Export preparation and replay | `test_prepare.py`, `test_intake_ambiguity.py`, installed-wheel preparation and `verify-prepared` flow | In the passing full suite; malformed input, mapping ambiguity, excluded private values, deterministic output and altered package/source are exercised. |
| Certification, refusal, frontier and certificate replay | `test_intake.py`, `test_frontier*.py`, `test_certify*.py`, installed-wheel valid/refused/tampered flows | In the passing full suite; an ordinary refusal remains a result, and edited certificate material fails replay. |
| Rechecks, sequential chains and planning | `test_recheck*.py`, `test_chain*.py`, installed-wheel recheck/chain/plan flows | In the passing full suite; missing source evidence, changed fresh rows, broken seals, forks and cross-process publication lease are exercised. |
| Release evidence and label audit | `test_release_contract.py`, `test_release_evaluate.py`, `test_release_cli.py`, installed-wheel release flow | In the passing full suite; disjoint holdout, registered criteria, replay and altered evidence are exercised. |
| Research measurements and controls | `test_validation.py`, `test_scores.py`, `test_extraction.py`, `test_sampling*.py`, frozen-score replay | In the passing full suite; frozen scores recomputed 25/25. GPU extraction from the base model was not run. |
| Drift, policy, action gate and economics | `test_drift*.py`, `test_policy.py`, `test_gate.py`, `test_economics.py`, `test_sizing.py` | In the passing full suite. These are local implementations and studies, not a deployed traffic control. |
| Evidence verifier itself | `test_reproduce_failure.py`, strengthened `test_scores.py`, `test_clean_clone.py`; two disposable-clone CLI attacks below | In the passing full suite; the previously green failure paths now return nonzero. |

The two verifier defects were demonstrated by failing tests before repair and
are recorded in [Decisions 230 and 231](../DECISIONS.md). A present cache whose
revalidation subprocess exited 1 previously printed “failure, not a skip” but
still emitted `TIER|3|activations|SKIPPED|0/0` and `VERIFIED` with exit 0. An
absent or empty committed score directory similarly let mandatory tier 2 skip
with exit 0. The repaired report distinguishes a failed attempt from an
optional skip. The affected score/reproduction/clone suites passed 50 tests
after the second repair.

In a disposable clone of `c335334`, hiding `results/scores/` made the real
`scripts/verify.py --no-activations` exit **1** with tier 1 `OK|92/92` and tier
2 `DRIFT|0/0`. Restoring scores and adding an invalid *present* activation
cache made `scripts/verify.py` exit **1** with tiers 1 and 2 `OK|92/92` and
`OK|25/25`, and tier 3 `DRIFT|0/0`. The clone was restored and removed. These
are end-to-end negative tests of the CLI's exit status, not only mocked unit
tests.

## Limits of this checkpoint

The activation-tier 3/3 result reuses a retained local cache; it does not
re-extract activations from the model on a GPU. Python 3.10/3.11 and Linux are
declared in CI but no run for this commit was observed here. No real customer
export, production traffic, service load, deployment, or buyer trial was
available. Passing local software tests therefore supports this checkout and
its synthetic/frozen evidence, not a production-service or customer-performance
claim. The interrupted pre-repair gate attempts and the initial
filesystem-denied clone attempt are not counted as passes; the record linked
above is the completed full gate.
