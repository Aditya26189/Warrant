# TESTING.md — what the suite defends

<sub>[🏠 Project README](../README.md) · [📚 Documentation index](README.md) · [🗺️ Diagrams](DIAGRAMS.md) · [📖 Glossary](GLOSSARY.md)</sub>

The tests here are not coverage. Each suite exists because a specific failure
either happened or would be invisible if it did — several of them were written
after the thing they now catch had already shipped once.

**Read test evidence by commit.** [The inventory](../results/test_inventory.json)
records which tests were collected from a clean source commit; its
`execution_status` explicitly says collection is not execution. Earlier
[phase reports](../reports/) record their own targeted runs, and
[the clean-clone record](../results/clean_clone.json) records a run on an earlier
source commit. Neither establishes a full-suite pass for a later head. The
[CI workflow](../.github/workflows/ci.yml) declares Linux customer/full-suite
jobs and a Windows minimum-version wheel job; consult the run for the exact
commit before stating that CI passed. The [product-state map](PRODUCT-STATE.md)
separates those checks from deployment evidence.

```bash
python -m pytest tests/ -q                    # the whole suite
python -m pytest tests/test_validation.py -q  # one suite
sh scripts/run.sh python -m pytest tests/ -q  # when you need the real exit status
```

**Never pipe a test run whose result you care about.** `pytest | tail` reports
*tail's* status, so a failing suite reads as green. That trap fired twice here,
the second time shortly after it was documented — which is why the wrapper
exists rather than the rule.

**Contents:** [The five kinds](#the-five-kinds-of-test-here) · [Suite by suite](#suite-by-suite) · [The customer path](#the-customer-path) · [The chain of rechecks](#the-chain-of-rechecks) · [Release evidence](#release-evidence) · [Tests that guard documents](#the-tests-that-guard-documents) · [Adding a test](#adding-a-test)

---

## The five kinds of test here

1. **Construction guards.** A record that would misrepresent what is known about
   it cannot be built. A rate without an interval, a count with one, a refusal
   without a reason, an override without its stratum. These run at
   `__post_init__`, so the invariant holds everywhere rather than everywhere it
   was remembered.
2. **Negative tests.** A checker that passes on the real input proves very
   little — it would also pass if it silently found nothing. So the tampering
   cases are tested too: a wrong value, a dead field, a missing artifact, a
   mutated ledger row.
3. **Gate tests.** Named in [TASKS.md](TASKS.md) before the phase was built.
   `test_hash_chain`, `test_warrant_key`, `test_yield_vs_rate`,
   `test_no_override`, `test_three_states`.
4. **Class scans.** A test that fails on the *next* instance rather than the one
   just fixed. The AST scan for `assert` statements in library code is one: the
   fix was eleven edits, but the test is what stops the twelfth. Fixing
   instances one at a time is how a class of defect survives.
   `test_chain_record_seal.py` is another: after three edited chain fields were
   fixed one by one, a schema audit found 197 more, so the test walks **every
   field of real records**, mutates each alone, and requires the verifier to
   notice. A field added later is covered without anyone adding it.
5. **Document gates.** Tests that read the repository's own prose and fail when
   it drifts from the artifacts or from the register that governs it.

---

## Suite by suite

### The records and the store

| Suite | Defends |
|---|---|
| `test_model.py` | Record-model invariants, including two of the three Phase 1 gate tests — the warrant key, and yield-vs-rate |
| `test_store.py` | Ledger behaviour, including `test_hash_chain`: mutating a row **demonstrably** breaks the chain |
| `test_override.py` | An override record the estimator could not use cannot be written |
| `test_calibration.py` | The calibration claim as a warrant's second, separable assertion |
| `test_construction_identity.py` | `construction` records the inputs to generation, never the generator's code |

### Measurement

| Suite | Defends |
|---|---|
| `test_validation.py` | The controls, refusal, leakage, polarity and determinism — the core of the harness |
| `test_warrant_stats.py` | Certification at issuance, and `FPRMonitor` -- whose anytime-valid claim `DECISIONS.md` 187 found is not established as implemented; the chained recheck (`test_recheck_chain.py`) is what carries a bound |
| `test_paired.py` | The paired comparison and the ROC geometry — the fix for the confounded comparison that once shipped |
| `test_scores.py` | Frozen scores, and the verification tier they make possible |
| `test_fpr_sweep.py` | The budget sweep over frozen scores, and what it must not get wrong |
| `test_lift_interval.py` | The lift interval's lower bound is conservative on every shipped artifact |
| `test_scorefree.py` | Certifying a detector with no score, against the claims registered before the code |
| `test_spec_refusal_criteria.py` | Every refusal the issuance path can produce traces to a criterion `SPEC.md` names |
| `test_extraction.py` | Everything about extraction that can be checked without a GPU |
| `test_dual_path.py` | The failure class that bit twice: two code paths computing the same thing, one drifting |

### Envelopes and detectors

| Suite | Defends |
|---|---|
| `test_evalsets.py` | Construction, freezing, and which claims a set can support |
| `test_categories.py` | An envelope is a distribution **plus a label definition** — a detector cannot be scored against labels that mean something else |
| `test_resplit.py` | Re-splitting a frozen set, and the cache reuse that licenses |
| `test_presidio.py` | The Presidio adapter, including that the finding is a statement about a pinned version |
| `test_banking_pilot.py` | The pilot, its pre-registration, and its divergence guard |
| `test_redact.py` | The REDACT adapter: labels taken from the benchmark's own gold, and each mapping decision |
| `test_external.py` | Third-party detectors on public datasets: every pairing pinned and its licence stated, our own detector held to the same yardstick, and a single-class or misaligned pairing refused rather than scored |

### Matrix, drift, policy

| Suite | Defends |
|---|---|
| `test_matrix.py` | The matrix and routing on it |
| `test_drift.py` | PSI against a warrant's stored bins, and the honesty flag on top of it |
| `test_drift_response.py` | The revocation ladder, the routing it triggers, and the record it leaves |
| `test_model_version.py` | Changed weights invalidate warrants measured on the old ones |
| `test_policy.py` | The policy engine, including that an unresolvable bundle does not load |
| `test_compose.py` | The four composition cases, written before the code |
| `test_revocation_trace.py` | The revocation trace: pre-registered, replayed on real lengths, and reported honestly |

### The customer path

What `warrant certify` and `warrant recheck` must get right on a file nobody here
has seen.

| Suite | Defends |
|---|---|
| `test_intake.py` | The input contract, the refusal that exits 0, and both shipped examples reproducible from their generator |
| `test_intake_ambiguity.py` | Duplicate columns, duplicate JSON keys, blank headers and ragged rows are refused, never resolved by whichever value came last |
| `test_malformed_numeric_inputs.py` | A number no arithmetic can use is refused rather than crashed on, in a chained record and in a release specification alike. The boundary is pinned at `2**1024 - 1`, the value a bit-length bound lets through |
| `test_psi_reference_size.py` | The drift null is simulated at the reference's own size, and the record says which size it came from |
| `test_recheck_after_chain_revocation.py` | An unchained recheck of a warrant its chain revoked reports the revocation instead of a fresh VALID, and still writes every measured field |
| `test_cli_records.py` | A `certify` record read back correctly by every command that takes one |
| `test_frontier.py` | The frontier in quantities that need no interval |
| `test_frontier_groups.py` | The frontier certifies what `certify` certifies, on grouped files too |
| `test_certify_from_frontier.py` | A budget picked off the frontier is certified at the frontier's level, and a frontier record that was edited or truncated is refused |
| `test_certify_evidence.py` | The certificate digest covers the ordered effective rows, including group and second label, while ignoring unused columns and file path |
| `test_certify_verification.py` | Retained certificate replay detects row or material-field edits, requires a selected frontier, and distinguishes legacy unverified records |
| `test_frontier_selection.py` | The frontier-selection study measures what it says it measures |
| `test_recheck.py` | A recheck keeps the broken bound and the moved distribution apart, and revokes on the lower bound |
| `test_recheck_evidence.py` | Every new CLI recheck names its exact certificate and binds fresh ordered effective rows; optional source replay refuses edited, missing or malformed evidence before writing; ordinary replay detects changed fresh rows and statistics while declining to call a chained record verified |
| `test_chain_replay_evidence.py` | A retained linear prefix replays from every fresh batch; changed rows, a rehashed sequential statistic, incomplete or unsealed history and missing claimed source evidence cannot earn VERIFIED |
| `test_recheck_groups.py` | A grouped warrant is rechecked in the unit it was certified in |
| `test_recheck_power.py` | A recheck's sample size is a probability of catching a breach, not a single sufficient count |
| `test_label_sensitivity.py` | A certificate's label-error ladders, and a `label_2` column that changes **no** verdict even when it contradicts every label |
| `test_recheck_label_sensitivity.py` | How many label errors would have hidden a revocation, checked against the recheck's own bound |
| `test_label_error_study.py` | The label-error study's criteria, applied as registered and as amended |

### The chain of rechecks

| Suite | Defends |
|---|---|
| `test_recheck_chain.py` | A year of rechecks as one sequential test |
| `test_recheck_chain_review.py` | The review of the chain, as tests: forks, head checks, drift that the chain must not mask |
| `test_chain_verify.py` | What `warrant chain verify` reports for each kind of finding |
| `test_chain_integrity.py` | The defects an independent review reproduced: continuing after a drift revocation, a fork restart around one, edited derived fields, malformed values. The drift case runs through the CLI and **asserts its own precondition**, so a changed fixture cannot quietly test something else |
| `test_chain_record_seal.py` | **Every stored field of a chained record is checked on verify.** A property test over every leaf of records the CLI wrote |
| `test_recheck_schedules.py` | The study that chose the chain's rule, as registered |
| `test_chain_detection.py` | The chain's detection grid is the study that was registered |

### Release evidence

These use synthetic fixtures only, never the frozen scores.

| Suite | Defends |
|---|---|
| `test_release_contract.py` | Registration boundaries: identity, criteria and holdout frozen before evaluation |
| `test_release_evaluate.py` | The statistics and the leakage checks, independently |
| `test_release_cli.py` | The release workflow as a customer runs it, including label-audit replay, second-review binding and first-invalidating counts against full re-evaluation |
| `test_release_render.py` | The terminal summary: a timestamp cannot inject terminal output |

### Economics and the demo

| Suite | Defends |
|---|---|
| `test_economics.py` | The abstention floor and the review sizing |
| `test_sizing.py` | The price list: recheck sizes, labels and cadence costs from one declared workload |
| `test_sampling.py` | The on-traffic estimator, and the gates registered before it was written |
| `test_sampling_assurance.py` | A recall plan's sample realises its margin with a declared probability, not merely on average |
| `test_price_list_sections.py` | The price list and kappa reach `RESULTS.md`, or it says why they cannot |
| `test_causal_claims.py` | Every mechanism a document asserts is checked against its falsifier, on every run |
| `test_demo.py` | The demo runs a **real** validation, with real certificates and a real chain |
| `test_demo_beats.py` | Each beat assembles from committed artifacts, **or says why it cannot** |
| `test_gateway.py` | The adapter returns certificates on an unmodified OpenAI-format response |
| `test_gate.py` | The action gate: its five rules, the two that consult no detector, the session Rule-of-Two, and what it costs on legitimate work |

### The repository itself

| Suite | Defends |
|---|---|
| `test_optimized_guards.py` | No `assert` survives in `controlplane/` — an AST scan over every module, plus the claim-table guard executed in a subprocess with `python -O` actually set. A guard the optimiser deletes is a guard that does not exist where it matters |
| `test_reproduce_tolerance.py` | The reproduction comparison accepts last-ulp float noise and **nothing wider** — a difference at the published precision must still fail, and the tolerance constant itself is asserted to stay tight |
| `test_smoke.py` | Every script actually runs |
| `test_script_wiring.py` | Every call a script makes into `controlplane/` binds to a **real signature** — the largest suite, because a thin wrapper that calls a renamed function fails only when someone runs it |
| `test_config.py` | Config loading, hashing, layer resolution, provenance |
| `test_clean_clone.py` | The clean-clone gate requires one well-formed status per verify tier; missing, duplicate or unknown lines fail the gate, as does a skipped claim or frozen-score tier. Only an explicitly skipped activation re-extraction is tolerated and labelled SKIP. |
| `test_fixture_guards.py` | A fixture number can never be read as a measurement |
| `test_lint.py` | The CI lint step, run locally whenever ruff is installed |
| `test_packaging.py` | What someone installing the package actually touches |
| `test_test_inventory.py` | A test-count claim is taken from a clean commit, or not taken |
| `test_coordination.py` | The coordination board: concurrent posts survive, sequence numbers stay unique, overlapping path claims are refused |
| `test_matrix_regression.py` | A richer artifact cannot be replaced by a poorer one |
| `test_invariants.py` | Every invariant in `CLAUDE.md` names the test that enforces it, and that test exists |
| `test_decisions_integrity.py` | `DECISIONS.md` stays contiguous, and every citation of it in the repository resolves |
| `test_reports.py` | Phase reports exist, are contiguous, and say the parts that are hard to say |
| `test_spec_section_11.py` | `RESULTS.md` contains every item `SPEC.md` requires of it |

---

## The tests that guard documents

These suites read the prose and fail when it drifts. They exist because **reading
is not a control** — a register nobody checks is a register nobody consults.

| Suite | Enforces |
|---|---|
| `test_claims.py` | Every number in `README.md` resolves to a field in `results/`, at the precision quoted. The negative cases matter more than the positive one: a wrong value, a wrong interval, a missing artifact and a dead field are all tested to fail |
| `test_cases_matrix.py` | [CASES.md](CASES.md) cannot drift from the suite — every row names a test that exists and an artifact that exists, and every row is covered |
| `test_docs_index.py` | `docs/README.md` cannot drift from `docs/` — every docs page is indexed and every relative link resolves |
| `test_external_figures.py` | The external-figure register gates the proposal: figures marked dropped or unverified must not appear there, and the register may not claim a provenance tier nobody reached |
| `test_fixture_guards.py` | Synthetic fixtures cannot be rendered as measurements |
| `test_readme_prose_numbers.py` | Numbers in README **prose** track their artifacts, not only the numbers in the claim table |
| `test_acceptance.py` | A stranger with a fresh clone follows the README quickstart to both a warrant and a refusal, the summary prints on a narrow ASCII terminal, and the no-network promise is stated where a buyer reads it |
| `test_crosswalk.py` | The RBI crosswalk names code and tests that exist, and says where it stops |
| `test_regulatory_attribution.py` | The repository says what the DPDP Rules it cites say, and no more |

If you add a number to a document, one of these is what will tell you.

---

## Adding a test

Match the kind to the failure:

- **Something could be constructed that misrepresents itself** → enforce it in
  `__post_init__` and test both directions. The illegal case must raise.
- **A checker could pass vacuously** → write the tampering case. Assert that a
  deliberately wrong input **fails**, not only that the right one passes. This is
  the same argument as the `padding_fault` control: a check that only ever
  passes is indistinguishable from a check that does nothing.
- **A script calls into the package** → `test_script_wiring.py` already binds
  every call to a real signature; keep it that way rather than discovering a
  rename at run time.
- **A document makes a claim** → give it a gate, in the suites above.

And follow the repository rule that produced most of these: when a bug is found,
the commit that fixes it carries the test that would have caught it, and the
commit body records what moved.

---

**See also:** [CASES.md](CASES.md) — every case, its test and its artifact · [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for what a failure means · [CONTRIBUTING.md](CONTRIBUTING.md) for the pre-merge checklist.
