# Phase 22 — grouped-boundary customer evidence and historical replay

**Answer.** A newly issued grouped `certify` record no longer turns repeated
rows inside a group into a narrow recall or precision interval when the
group-resampling bootstrap collapses. It keeps the descriptive point estimate
and reports a clearly explained, vacuous `[0, 1]` interval. Its one-sided FPR
certificate still uses independent negative groups. The record now names its
metric protocol, so an older bound certificate can replay its original
arithmetic with a legacy-method warning. This is a customer-path correction,
**not** a claim that every historical research interval or other grouped
estimator has been repaired.

The commercial position did not change: the founder has reported no buyer
interviews, design partners, paid pilots or revenue. This correctness repair
does not establish that a validation lead needs this workflow or will fund it.
The conversation gate in `reports/NEXT-STEPS-2026-09-17.md` still precedes a
claim of a venture-scale market.

## Why the method changed

The independent project review's R2 constructed 60 clean groups and four
positive groups with perfect separation. Repeating each row 100 times inside
its same group raised both reported lower limits from about 0.398 to 0.991
without adding an independent unit
(`reports/PROJECT-REVIEW-2026-09-23.md`, R2). The group bootstrap itself sampled
groups, but its zero-width result fell through to a binomial calculation using
row counts. The Phase 22 red test reproduced that failure before code changed:
the first recall lower limit was `0.3976353643835254`. An [original simulation
study of clustered binary outcomes](https://pubmed.ncbi.nlm.nih.gov/35093646/)
supports concern about inference that ignores within-cluster dependence and
small numbers of clusters. It does not validate a replacement interval for
this product. `[0, 1]` is chosen because it is the full range of recall and
precision, so it conveys no invented population precision.

Decision 217 registered the narrow method before implementation. The fix lives
in `controlplane/validation/metrics_builder.py`, leaving the explicitly
read-only `controlplane/validation/stats.py` untouched. It keeps the original
group percentile interval when that interval has width. On a collapsed raw
interval it reports `[0, 1]`, the point estimate, the group count and a reason.
Undefined bootstrap samples still trigger the prior error rule. Tests cover
uniform duplication, all and zero observed successes, an interior collapsed
ratio with mixed and unequal groups, a noncollapsed grouped control, and an
ungrouped exact-binomial control. A customer-certificate test checks the
resulting JSON, not just the helper function.

## What the clean-source gate found

The first implementation applied the safer grouped interval to **every**
metric-builder caller at commit `2eb3ea6`. `python scripts/verify.py
--no-activations` then reproduced **92/92** README claims but only **24/25**
frozen-score metric blocks. The one drift was the retained
`results/transfer-T1-mean_pool.json`: its historical `recall.ci_high` is
`0.013228972042469731`, while the new vacuous interval has upper endpoint
`1.0`. That old file was generated at `05b2a52` using the historical method.
The drift was a real methodological difference, not an edited score or an
excuse to update a protected result by hand. The recorded interval should not
be quoted as valid population evidence under grouped dependence.

Decision 218 therefore scoped the new method to *new customer certificates*.
The common metric builder retains its historical default for exact replay of
the frozen research scores. `certify_items` opts into the corrected grouped
behavior. On clean commit `4b7a5f8`, the verifier returned **92/92** claims and
**25/25** frozen-score comparisons again; the activation tier was skipped.
That green result establishes historical reproducibility, not validity of the
old mean-pool interval. The old research method remains an explicit open debt
requiring a versioned, pre-registered migration and new provenance.

A second read-only review found that `warrant verify` calls `certify_items` to
replay an issued certificate. Without a method version, a retained older bound
grouped record could be labelled MISMATCH solely because new issuance changed
the interval method. Decision 219 registered a material top-level
`metrics_protocol: grouped_boundary_vacuous_v1` for new certificates and
refusals. The verifier replays that declared method; an older bound record
without the field replays historical arithmetic and warns when grouped. An
unknown protocol is rejected. The source regression verifies new, retained,
stripped-marker and unknown-marker cases. The marker is a replay selector, not
a trusted timestamp or a defence against coherent local rewriting.

## Validation ledger

- The preregistration is `DECISIONS.md` 217; the clean-source drift and scoped
  correction are decision 218; the certificate compatibility rule is decision
  219. Each was committed before the implementation it governed.
- The six new synthetic/customer regressions brought the first clean inventory
  from **2,093** to **2,099** collected tests at `4b7a5f8`. One protocol replay
  regression brings the successor inventory to **2,100 collected tests** at
  clean source `fc0239b` (inventory commit `2e9d625`). Collection is not a
  claim of execution.
- Focused grouped, certificate, frontier, recheck, documentation and invariant
  tests passed on the protocol implementation. Ruff and whitespace checks
  passed. Installed-wheel tests passed. On clean protocol source, `python
  scripts/verify.py --no-activations` reproduced **92/92** claims and **25/25**
  frozen-score comparisons; activation re-derivation was **SKIPPED**.
- The first full Phase 22 suite was stopped near its start after the
  certificate-replay compatibility gap was found in source review. The final
  full suite on clean `2e9d625` exited **0** with one expected xfail and no
  reported failures. Remote CI is unobserved. An independent statistical
  review was requested from the other coordinated session; no response has
  been observed yet.

## What this does not establish

The vacuous interval is intentionally uninformative. The noncollapsed grouped
percentile interval was preserved, not newly proven to have nominal
finite-sample coverage. The research path still replays its historical
grouped-boundary fallback, and its mean-pool upper recall limit is not sound
population evidence. Other grouped metrics, including a hard-negative FPR
path, need separate review. A VERIFIED older certificate means its rows and
material fields reproduce under the old declared-by-absence method; it does
not validate that method's interval or authenticate when the record was made.
No test here establishes representative customer traffic, label truth,
authenticated custody, or buyer demand.

## Open items

Obtain independent statistical review before describing this as final
inferential assurance.
For the research artifact, design a versioned estimator migration and
pre-register how new results and old claims coexist before any protected
test-set rescore. Audit the remaining grouped metrics separately. For the
company, run the buyer conversations and apply the registered stop rule;
another local interval fix cannot supply that evidence.

## Ledger

| Change | Commit | Reproduce or inspect |
|---|---|---|
| Registered collapsed-group method | `81f4ef9` | `DECISIONS.md` 217 |
| Universal implementation and red-test repair | `2eb3ea6` | `tests/test_grouped_metric_boundary.py`; clean `verify.py` exposed 24/25 |
| Registered customer-only scope | `b0d0880` | `DECISIONS.md` 218 |
| Customer opt-in and historical research replay | `4b7a5f8` | grouped, certify and docs tests; clean `verify.py` returned 25/25 |
| Registered certificate protocol | `2649412` | `DECISIONS.md` 219 |
| New/legacy certificate replay and docs | `fc0239b` | grouped, certify, frontier, recheck and docs tests |
| Generated test collection inventory | `2e9d625` | `python scripts/refresh_test_inventory.py` from clean `fc0239b` |

The full gate command is `python -m pytest tests/ -q -p no:cacheprovider
--basetemp <temporary-directory> --tb=short`. The claim gate is `python
scripts/verify.py --no-activations`. No protected result JSON was modified.
