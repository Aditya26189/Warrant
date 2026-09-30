# Phase 24 - Grouped-rate boundary evidence

New grouped certificates now abstain when a flag-rate or descriptive within-set
FPR bootstrap collapses. The old calculation could give a narrow row-binomial
interval even when hundreds of rows were copies of only a few independent
scenarios. This repair changes the reported uncertainty, not the observed rate,
the selected certificate threshold, or its separate negative-group FPR bound.

## What was wrong

`build_warrant_metrics` already resampled groups for interval interiors. At a
collapsed boundary, `estimated()` instead used the supplied row event/trial
counts for flag rate and ordinary FPR. The synthetic regression repeats each
of four negative scenarios 100 times with no flags. Duplicating rows leaves
four independent scenarios but made the old flag-rate upper interval much
narrower; Decision 221 records the exact diagnostic. Decision 217 repaired
grouped recall and precision, while Decision 220 separately repaired the
one-sided warrant-facing hard-negative FPR. Neither covered these remaining
descriptive rates.

For a new grouped metric block, a noncollapsed cluster-percentile interval is
unchanged. A collapsed flag-rate or ordinary FPR interval is `[0, 1]`, with
the observed point estimate, group count, and reason retained. Ungrouped
boundary behavior stays on its former independent-item method. A hard-negative
warrant still uses the distinct group-any one-sided protocol from Phase 23.

The cluster bootstrap is a reasonable way to retain within-group dependence,
but [Huang's simulation study](https://pubmed.ncbi.nlm.nih.gov/29795957/)
concerns other clustered settings and does not validate this exact Warrant
estimator. Small cluster counts and selective or hand-built samples still need
independent review. A vacuous interval explicitly withholds a population
claim; it is not an achieved 95% coverage estimate.

## Compatibility and provenance

New `certify` records state `metrics_protocol: grouped_boundary_vacuous_v2`.
The certificate verifier replays v2, retained v1, and older unmarked records
under their own calculations. A v1 record retains the Phase 22 grouped
recall/precision repair and its original flag-rate method; an unmarked record
retains the older method throughout. Replaying either proves consistency with
the supplied rows and declared configuration, not statistical coverage or
authenticity. Unknown protocol markers fail verification.

Prospective grouped research run IDs include `grouped_rate_vacuous_v1` to avoid
reusing an old identity after changing estimator arithmetic. Frozen score
artifacts remain untouched and are compared with an explicit legacy option.
The verifier's historical 25/25 replay is evidence of reproducibility, not
endorsement of the old grouped intervals. No protected test-set scoring was
performed or selected on in this phase.

## Validation

| Gate | Result |
|---|---|
| Decision | `DECISIONS.md` 221 committed before implementation (`17a977b`) |
| Regressions | Four-group row duplication, noncollapsed parity, independent-item parity, and v1/v2/unmarked certificate replay passed in focused runs |
| Affected intake, metrics, routing and report suites | Passed before the final code commit |
| Clean frozen-score verifier | 92/92 README claims and 25/25 frozen-score comparisons; activation tier skipped by `--no-activations` |
| Full repository suite | Exited 0 from clean `36a2544`; one expected xfail, no test failures; runtime/deprecation warnings disclosed in test output |
| Test inventory | 2,115 collected from clean `91d1070`; collection is not a passing-suite claim |
| Independent statistical review | Not observed |
| Remote CI and push | Unobserved |

## Remaining evidence gap

The fix does not establish that scenario groups are independent, sampled from
a customer's deployment population, or labeled reliably. It also does not
establish demand: the founder has reported no buyer interviews, design
partners, paid pilots, or revenue. The previously registered test in
`reports/STRATEGY-2026-09.md` calls for twelve buyer conversations and treats
fewer than three concrete consequential wrong-control incidents as a reason to
regard this as research rather than a validated company. The uncertainty
repair is worth keeping, but it cannot substitute for that test.

## Open items

Obtain independent statistical review of the clustered estimators and their
sampling assumptions.
Give historical research intervals a versioned migration rather than editing
the protected results. Run the pre-registered buyer conversations before
claiming an enterprise purchase case or seeking funding on that premise.

## Ledger

| Change | Commit or source |
|---|---|
| Decision and synthetic diagnostic | `DECISIONS.md` 221, `17a977b` |
| Estimator, protocol replay, run identity, regression and contracts | `91d1070` |
| Generated inventory | `36a2544` |
| Historical artifact replay | `controlplane/report/reproduce.py`; protected `results/scores/` unchanged |
| Public caveats and product-state corrections | `881975f`, `821228e`, `2ed19aa`, `f1bb471`, `3a4d63a` |

