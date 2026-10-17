# Native `certify` audit — 17 October 2026

**Finding: FAIL for the general interpretation of the returned adaptive
`fpr_upper_bound` as a 95% bound with tied scores.** The fixed requested-budget
rank argument is a different assertion and is not falsified by this example.
Production behavior was not changed. **GUARANTEE NOT VERIFIED** as an
independently reviewed Warrant guarantee; no human statistical review occurred.

Production source tested: `b7de189a62943b18d512b58df606621270b06c6b`.
New tests: `tests/test_certify_stage_a.py`. All source references below refer
to that production SHA; subsequent scoped commits change only docs/tests.

## Actual procedure and boundary

| Issue | Source / actual semantics | Status |
| --- | --- | --- |
| Entry point | `pyproject.toml:28`, `controlplane/cli.py:482`; `_certify` loads scored input then calls `certify_items` at 597. No internal train/calibration split. | PASS (traced) |
| Scores/labels | `intake/contract.py:10–22,246–283`: higher score means positive; label 1 means detector SHOULD fire, 0 means clean. Any finite score range. No model or label correctness check. | PASS contract; UNKNOWN truth |
| Negative-only selection | `intake/certify.py:195–224` → `validation/warrant_stats.py:72–139`; positives do not choose the threshold. | PASS |
| Comparator / equality | Native cuts are `nextafter(sort(unique(unit_max)), +inf)` at `warrant_stats.py:134`; counts and runtime metrics use `score >= threshold` (136, `certify.py:330,380`). For finite float64 scores this is strict `score > observed pivot`. A new score equal to the actual successor threshold fires; a score equal to the pivot does not. | PASS |
| Rank / ties | Let K be largest k with U(k,n,delta_eff) <= B. Selected pivot is ascending one-indexed rank r=n−K. Ties may make realized k smaller than K; lowest qualifying unique pivot is used. No positive-score optimization. | PASS characterization |
| Numeric acceptance | `warrant_stats.py:138` uses literal `ucb <= target_fpr`, no epsilon. Selection metadata uses a separate level-consistency tolerance (`certify.py:281`) and CLI grid membership tolerance (`cli.py:550`); neither relaxes U<=B. | PASS for named vectors |
| Missing evidence | Lower helper n=0 or n=1 refuses at B=.05 without a threshold/k/U. `cp_upper(0,0)` raises. File intake requires both classes (`contract.py:409–417`): no negatives/all positives and all negatives are bad input, not CLI certificates. | PASS |
| Usefulness | Native `certify_items` returns VALID solely after FPR certification (`certify.py:345–384`). Recall/precision/lift are measured, with no native recall floor or usefulness veto. A no-fire threshold may issue. Historical research `issuance.py` is a different procedure. | NOT_APPLICABLE recall gate |
| Groups | All observed group sizes must be equal (`certify.py:215–221`); negatives alone then form cluster maxima, whose sizes must also match (`warrant_stats.py:104–120`). A group fires if any negative member fires. Mixed-label groups can pass if both size conditions hold. | PASS input characterization; UNKNOWN population assumptions |
| Duplicates | File intake rejects repeated IDs (`contract.py:398–406`), blank groups and malformed columns. Identical observations with distinct IDs are accepted; there is no semantic deduplication or independence test. | PASS explicit rejection; UNKNOWN independence |
| Multiple budgets | Helper divides alpha by `max(1,n_profiles)` (`warrant_stats.py:101`); native CLI single budget passes no profile count. Frontier splits family alpha over its fixed grid (`intake/frontier.py:120–121`); `--from-frontier` replays full default grid and binds levels/digests (`cli.py:526–603`). | PASS scoped tests |
| Frontier output units | Certificate `false_positives_at_threshold` is group k when grouped (`certify.py:378`); frontier `counts_exact.false_positives` counts negative rows (`frontier.py:170`) although payload `unit` names negative clusters (86). Both counts are exact; combining row k with group n to reconstruct CP is invalid. | UNKNOWN clarity; documented distinction |
| Labels | Primary label determines status/cut/U; `label_2`, disputes and sensitivity do not change those (`certify.py:325–343`). Agreement cannot prove truth. | PASS behavior; UNKNOWN label validity |

## Independent CP calculations

One-sided delta=.05, fixed binomial trials. For k<n,
U=Beta-inverse(.95;k+1,n−k); U=1 for k=n; n=0 is undefined.
The new oracle directly sums the binomial CDF using 60-digit Python Decimal
arithmetic and 160 bisection steps, independently of SciPy Beta. Printed and
native values are compared with absolute tolerance 1e−12, relative tolerance
zero. Eligibility always uses exact `<= B`, with no added tolerance.

| B | n | k | U (rounded) | U<=B |
| --- | ---: | ---: | ---: | --- |
| .05 | 58 | 0 | .050339338330 | NO |
| .05 | 59 | 0 | .049507609888 | YES |
| .01 | 298 | 0 | .010002432438 | NO |
| .01 | 299 | 0 | .009969146793 | YES |
| .01 | 472 | 1 | .010010788209 | NO |
| .01 | 473 | 1 | .009989707474 | YES |
| .05 | 600 | 20 | .048069909806 | YES |
| .05 | 600 | 21 | .050011443530 | NO |

**PASS:** independent CDF acceptance gives maximum K=1,8,20 for n=100,300,600
at B=.05; native continuous-rank cuts agree. These K values correspond to
r=99,292,580, respectively, not order indices 1,8,20. The provided external
oracle also passed its independent SciPy binomial-root inversion; this is
numerical corroboration, not proof of native selection validity.

**FAIL (conservative boundary):** `min_n_for=ceil(log(delta)/log(1−B))`
(`warrant_stats.py:53–59`) can round up unnecessarily. With
B=`cp_upper(0,600,.05)`, equality U<=B holds but floor is 601; n=600 refuses.
n=1/B=.95 similarly gives floor 2. At a nonzero-count boundary, n=100 and
B=`cp_upper(1,100,.05)`, equality accepts k=1; one float below selects k=0.
The named near-budget n=600/k=21 case is correctly rejected.

## Rank argument: what can be supported under assumptions

This is established order-statistic/NP classification theory, not a new
Warrant algorithm. [Tong, Feng and Li, *Science Advances* (2018)](https://doi.org/10.1126/sciadv.aao1659),
[primary manuscript](https://arxiv.org/pdf/1608.03109), Proposition 1
(PDF p.7), rank rule Eq.(2), and supplementary proof (pp.18–19), were inspected
as SELECTED_SECTIONS. The journal identity is confirmed by its
[bibliographic record](https://pubmed.ncbi.nlm.nih.gov/29423442/).
The PMC full-text page was CAPTCHA-blocked; the arXiv PDF was accessible.

Mapping the standard argument to native code requires: scoring rule trained
independently of calibration; fixed n/B/delta; IID negative scores from the
same source distribution; correct labels; the same represented scoring rule
at deployment. Mere dependent exchangeability does not supply a binomial law.
For groups the IID units must be whole negative groups; item domination also
needs equal negative group weighting/size in the intended population, not just
equal sizes in this file. Input validation cannot establish these assumptions.

Agent-derived mapping: with CDF F, pivot X_(r), r=n−K, and strict firing above
the pivot, the bad region A={x:F(x)<1−B} has probability p<=1−B. If the selected
population FPR exceeds B, at least r calibration scores fall in A. Thus
P(bad) <= P(Bin(n,1−B)>=r) = P(Bin(n,B)<=K) <= delta_eff.
Atoms make this inequality conservative. The successor implementation is
equivalent on the float64 score domain; it is at least as conservative if
interpreted against intervening real scores. Deterministic uniform 1-, 10-
and 50-level population tails in the new tests corroborate this mapping;
they are not a theorem inferred from Monte Carlo.

Accordingly the intended **fixed-budget** statement is
`P(issue AND FPR_source(selected_policy)>B) <= delta_eff`, subject to those
assumptions and independent review of the code mapping. It does not establish
`P(FPR>B | issued)<=delta` in a more general selective workflow, target-domain
validity, conditional stream validity, or an adaptive numerical upper bound.
For this native fixed-n finite-score procedure issuance is effectively
deterministic once the sample-size floor clears; that special fact must not be
exported to another selection/issuance protocol.

## FAIL: returned U is not generally a calibrated adaptive bound

The code returns U(realized k,n), not U(K,n). With ties those differ. The JSON
calls it `fpr_upper_bound` and its estimator a one-sided CP bound
(`intake/certify.py:133–138,365–378`); terminal/frontier call it “FPR bound”
(`intake/render.py:195,470,485`). Fixed-budget control does not justify this
stronger reading of a data-dependent number.

Exact counterexample (new test
`test_returned_adaptive_upper_bound_currently_undercovers_with_ties`):
n=100, B=.05, delta=.05, K=1; IID scores in {0,1,2} with
q1=P(S>=1)=.04656, q2=P(S>=2)=.029514.
U0=.029513049607039932 and U1=.046559811453538914.
Let M1/M2 count calibration scores >=1/>=2. Noncoverage of returned U is
the disjoint union `{M1<=1}` and `{M1>=2,M2=0}`. Its exact probability is

`100*q2*(1−q1)^99 + (1−q2)^100 = .07630211515886068 > .05`.

The expression is evaluated directly with rational decimal inputs, without
simulation or using native CP as the probability oracle. Tests exercise all
pivot/k branches and independently invert the CDF to locate U0/U1. Every
possible selected population FPR here is 0, q1 or q2, all below B. This example
therefore falsifies the general returned-U coverage interpretation while
preserving the distinction from budget failure. It is a synthetic audit
counterexample, not an empirical result about guardrail papers or traffic.

## Other limits and proposed patches (not implemented)

- **FAIL helper input validation:** exported `certify_fpr` accepts all-NaN
  negatives and returns a certified NaN threshold/k=0. `cp_upper` does not fully
  validate k/n/alpha. CLI intake rejects NaN/infinity; no malformed CSV pass
  was demonstrated. Proposed separate patch: validate shape, finite values,
  integer counts, domains and aligned group IDs at public helper boundaries.
- **FAIL extreme threshold serialization boundary:** largest finite float
  pivot overflows `nextafter` to +infinity (warning, characterized in tests).
  Full certificate serialization of that extreme case: NOT_RUN. A separate
  patch must choose explicit refusal or documented no-fire representation.
- **FAIL API prose consistency:** explicit `certify_items(alpha=.01)` with
  config ci=.95 records alpha=.01 but its non-frontier reason says 95%
  (`certify.py:365`). CLI exposes no alpha override; terminal uses result.alpha
  correctly (`render.py:154`). Source-review fixture reproduced this; not a
  changed verdict. Proposed patch: derive prose from actual alpha.
- **UNKNOWN repeated use:** no native registry prevents trying many budgets,
  scorers, sample sizes, input variants or reissuance after inspection. An exact
  deterministic rerun of the same policy/data adds no event; opportunistic
  selection across new attempts needs prospective family/sequential control.
  Native certification is not anytime-valid. Recheck/chain are separate APIs
  and were not scientifically revalidated here.
- **UNKNOWN descriptive metrics:** bootstrap recall/precision on the same
  calibration file are not a simultaneous assurance result. Frontier selection
  explicitly notes their optimism. Grouped collapsed intervals abstain under
  `grouped_boundary_vacuous_v2`; this is not a group-coverage proof.

Proposed primary repair for later authorization: preserve selected pivot and
fixed-budget verdict, compute the deterministic design K from (n,B,delta_eff),
report U(K,n) as the rank-based assurance bound, and label realized k/U(k,n)
as descriptive diagnostics. Version the record/replay contract and associated
language; do not silently rewrite old certificates. Alternatively retain only
the requested-budget guarantee. Human statistical review and approval are
required before either behavior/reporting change; Stage A implements neither.

## Verification ledger

- External package oracle: `python <shared-root>/WARRANT_CODEX_ONE_PACKAGE/reference_oracle_certify.py`
  — exit 0; all eight values and three accepted-count checks passed. Run after
  clean snapshot commit `4efc31d`; no output artifacts written; `--ties` NOT_RUN.
- New deterministic tests: `python -m pytest tests/test_certify_stage_a.py
  -o addopts= -q -p no:cacheprovider` — 29 passed, exit 0 (delegated execution).
  Root rerun and existing-suite result are recorded in the closing addendum.
- `python -m ruff check tests/test_certify_stage_a.py` — exit 0.
- Initial ten-module pytest attempt (172 collected cases): exit 1; numerous
  fixture setup errors from sandbox WinError 5 on pytest's default temporary
  directory. A one-module maxfail diagnostic also exited 1. Explicit sandboxed
  basetemp still failed at temporary-directory access/session cleanup. Those
  runs are **not passing suites**. Approved escalated rerun uses a new dedicated
  workspace basetemp with cache disabled; final result is appended below.
- Full repository suite, installed wheel, Python 3.10, GPU, model inference,
  frozen-artifact replay and Monte Carlo: NOT_RUN; not needed to characterize
  these source-level changes and not substitutes for statistical review.

Tests characterize known defects with passing assertions about current
behavior. Their pass status does **not** mark those findings PASS. No production
statistical behavior, historical decision or frozen result was modified.
