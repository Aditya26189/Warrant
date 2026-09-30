# Phase 23 — hard-negative bounds count independent scenarios

**Finding.** The historical `hard-negatives-200` research warrants treated 200
framed rows as 200 independent negative trials. The set actually contains 50
hand-written scenarios, each rendered in four framings under one `question_id`.
Within a scenario, the four flags can be dependent. The one-sided
Clopper–Pearson branch of `estimated()` received row counts even though the
metric builder also received groups. This can make the hard-negative FPR upper
bound too small and change a warrant decision.

The retained `presidio-enabled_plus_custom` score file has eight flagged rows
in two scenarios at its declared threshold. Its published row-based upper
bound is **0.07101416861601983** from 8/200. Counting a scenario as firing
when any framing fires yields **0.12061415542204408** from 2/50. The old
hard-negative warrant is `VALID` under the loosest declared 0.10 ceiling; the
prospective group-aware method refuses it. For zero-flag detectors, the old
0/200 upper bound is 0.014867039231272083, versus 0.058155079116972264 for
0/50. These are read-only calculations from the committed score vectors and
group IDs, **not** a new model run, threshold selection, edit to the protected
result, or a claim about customer traffic. Decision 220 registered the rule
before code changed.

## Why this correction is conservative

For each of G groups with the same number m of negative rows, let each row's
false-positive indicator be 0 or 1, and let a group indicator be 1 if *any*
row fires. Each group's mean row indicator is at most its group indicator.
Averaging over equal-sized groups therefore makes the observed group-any rate
at least the observed row rate. A one-sided bound on independently sampled
group-any events can upper-bound the corresponding item rate under that
sampling model. With unequal group sizes this inequality between the
*unweighted* group rate and the row rate can fail; the new metric reports a
vacuous upper bound of 1 and refuses any ordinary ceiling. The item-rate point
estimate remains descriptive, and the estimator names both row and group
counts. The bound is versioned as `group_any_cp_v1`; a new ungrouped
independent-item bound declares `independent_item_cp_v1`.

Original research on clustered binary outcomes shows why cluster structure
matters for error-rate inference ([simulation study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8847311/)).
That study does **not** validate this product's precise group-any method.
The equal-size inequality above is algebraic; the confidence interpretation
still requires an appropriate sampling design. Here the scenarios were
hand-built, so even the corrected arithmetic does not establish a population
guarantee for enterprise traffic. Original research on non-probability
prevalence samples discusses that separate representativeness problem
([sampling study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8088017/)).

## What changes in the product

The shared metric builder uses the group-any protocol by default for a new
grouped hard-negative warrant. New run IDs incorporate the protocol so the
same detector, score vector and config do not reuse an old method's identity.
`issue_or_refuse`, matrix routing, and policy loading reject a hard-negative
FPR bound whose estimator lacks a recognized independent-unit protocol. Thus
a retained `VALID` status cannot by itself clear a new routing or policy
ceiling. Historical `results/` files are unchanged; the frozen-score verifier
requests the old method explicitly to show exactly what those files said,
without mistaking reproducibility for statistical validity.

The certificate CLI's FPR threshold rule already counts negative groups and
rejects unequal sizes. Phase 23 addresses the separate research-warrant FPR
metric and its consumption paths. Its correction does not change customer
certificate rows, the protected test-set scores, or the Phase 22 grouped
recall/precision rule.

## Validation and limits

The red synthetic test repeated each of four independent negative groups 100
times: the old upper bound fell from about 0.527 to about 0.0075 with no new
independent information. The new test holds it fixed, counts one flagged
framing as one affected group, makes unequal sizes vacuous, and checks that a
bound between the old and new uppers changes issuance to REFUSED. Separate
tests check explicit legacy replay and block unversioned bounds in issuance,
routing and policy loading. A separate grouped flag-rate/descriptive-FPR
boundary gap was identified during review and preregistered as Decision 221
for Phase 24; Phase 23 does not claim to repair that interval.

| Gate | Result |
|---|---|
| Method decision | `DECISIONS.md` 220, committed before implementation |
| Synthetic grouped regressions | Passed, including duplication, unequal-size refusal and historical replay |
| Surrounding validation/policy suites | Passed after the final code correction |
| Clean frozen-score verifier | 92/92 README claims, 25/25 frozen-score comparisons; activation tier skipped by `--no-activations` |
| Full repository suite | Exited 0 from clean `83dbdd1`; one expected xfail, no test failures; runtime/deprecation warnings disclosed in test output |
| Independent statistical review | Requested from the coordinated session; no response observed |
| Remote CI and push | Unobserved |

## What this does not establish

The method marker is a local declaration, not a signature. Someone able to
rewrite a whole record coherently can still impersonate a protocol. Group
independence and customer representativeness are assumptions requiring
external evidence; neither is created by a narrower unit count. Existing
published research intervals remain historically recorded and method-limited.
The founder has reported no buyer interviews, design partners, paid pilots or
revenue, so this correctness fix changes no commercial validation conclusion.

## Open items

Seek independent review of the equal-size dominance argument and the
independence assumptions. Design representative customer sampling before
claiming a customer-population FPR; the hand-built set is an adversarial
regression set. Complete Decision 221's separate grouped flag-rate interval
repair. Give historical research claims a versioned migration rather than
rewriting protected artifacts. Obtain buyer interviews under the previously
registered conversation gate.

## Ledger

| Change | Commit or source |
|---|---|
| Preregistered the method and the historical example | `DECISIONS.md` 220, `f575c95` |
| Prospective grouped bound and legacy protocol guard | `c01928b` |
| Historical score and group IDs | `results/scores/text-presidio-enabled_plus_custom-hard-negatives-200.json` |
| Historical issued status and row bound | `results/detectors.json` |
| Group construction | `controlplane/evalsets/builders.py`, `build_hard_negatives` |
| Public historical-set caveat | `881975f`, `821228e` |


