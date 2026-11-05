# Methods and statistical interpretation

## Define the estimand first

A scored file supplies observations. A scientific claim additionally needs a
population, positive-label definition, independent unit, operating rule,
selection procedure and uncertainty statement.

The fraction of supplied rows flagged, the future FPR of a fixed rule, recall
on an alias-labelled benchmark, the share of simulated monitoring years that
revoke, and the number of authored workflows blocked are different estimands.
A common field name or numeric representation does not make them interchangeable.

## Point estimates

With `score >= threshold` meaning flagged:

| Quantity | Definition | Denominator |
|---|---|---|
| Recall | `TP / (TP + FN)` | Positive-labelled rows |
| Precision | `TP / (TP + FP)` | Flagged rows |
| Descriptive FPR | `FP / (FP + TN)` | Negative-labelled rows |
| Flag rate | `(TP + FP) / N` | All rows |
| Base rate | `(TP + FN) / N` | All rows |
| Lift | `recall / flag_rate = precision / base_rate` | Relative to random selection on the same population |

AUROC is the positive-versus-negative pair-ranking probability, giving half
credit to tied pairs. It summarizes ranking across thresholds and need not
imply high recall at a restrictive operating point.

The [audit oracle](../../controlplane/report/documentation_audit.py) computes
that pair probability and direct confusion counts without using the original
metric formulas. This checks point arithmetic, not confidence intervals.

When nothing is flagged, precision has denominator zero. A conventional stored
point value is not measured precision; the current customer record supplies a
vacuous interval and an explanation. On a single-class challenge, the research
builder withholds AUROC, recall and precision.

## Selection protocols are different

The original probe experiments fit on training rows, select regularization and
operating decisions using validation, then describe test behavior. Some profile
decisions target a flag-rate budget. That differs from constraining FPR among
clean items.

The exploratory sweep inspects multiple budgets on frozen scores. The
out-of-sample sweep declares separate threshold-certification and evaluation
splits. Split separation does not erase earlier test exposure or repair dirty
source provenance.

The release workflow evaluates an already fixed threshold under a registered
holdout contract. It is another protocol, with its own simultaneous criteria.
A status from one workflow cannot substitute for evidence from another.

## Fixed-threshold binomial inference

For independent negative trials and a fixed rule, the one-sided
Clopper-Pearson upper bound is:

```text
U(k,n,delta) = BetaQuantile(1-delta; k+1, n-k), k < n
U(n,n,delta) = 1
U(0,n,delta) = 1 - delta^(1/n)
```

Here `k` is the false-positive count and `n` the independent negative-trial
count. The repeated-sampling statement assumes the binomial model. It does not
correct wrong labels, dependence or distribution shift.

See [the primitive](../../controlplane/validation/warrant_stats.py) and
[primary-source attribution](sources.md). Applying a classical interval is
engineering use of established statistics, not a novel theorem.

## A selected threshold and a returned bound

Under the declared order-statistic design and its assumptions, a fixed
requested budget `B` and calibration failure probability `delta` concern:

```text
P_calibration{ selected same-source risk > B } <= delta
```

The assumptions include a scoring rule fixed independently of calibration,
declared sample size and budget, independent negative units, correct labels
and an appropriate same-source population. The retained
[native audit](../../docs/research/fpr_reporting/CERTIFY_AUDIT.md) maps the
rank argument and documents the outstanding independent-review boundary.

This is different from claiming that the data-dependent numerical return
`U(D)` satisfies:

```text
P_calibration{ selected risk > U(D) } <= delta
```

With ties, the realized exceedance count can fall below the design count.
The native procedure reports a smaller realized-count bound. The retained
[exact witness](../../docs/research/publication/EXACT_WITNESS.md) demonstrates
noncoverage approximately 0.076302 at nominal 0.05 for the stronger returned-U
interpretation. Every selected risk in that particular distribution remains
below the requested budget.

This controlled counterexample does not establish a budget violation in that
distribution, a prevalence of defects in other systems, or a general critique
of conformal prediction. It also does not replace independent review of the
complete native implementation. No production repair is applied here.

## Groups and independent units

A negative group fires if any member fires in the group-any construction.
An inference about group firing can dominate item FPR only with the appropriate
equal-size/weight assumptions in the intended population.

The software validates declared group structure and supported size restrictions.
It cannot discover all real dependence or certify a population sampling design.
Equal sizes in one file do not alone establish the required target-population
assumptions.

Historical hard-negative records used row-count intervals for repeated
framings. They remain replayable as historical method records. New issuance
uses explicit independent-unit protocols; a legacy `VALID` string does not
upgrade the old inference.

## Bootstrap and selection uncertainty

Research intervals use the recorded bootstrap count, seed, grouping and metric
protocol. Reconstructing them does not prove finite-sample coverage under
arbitrary dependence or selection.

Paired comparisons retain common held-out question identities. Otherwise a
contrast between differently sized test sets mixes model and sample effects.
The separate selection-aware recall analysis measures a particular widening
relative to conditioning on an estimated threshold. It does not repair the
native adaptive returned-FPR bound.

## Rechecking over a horizon

Repeated one-shot tests at the same nominal level do not automatically control
a whole monitoring horizon. The studies compare rules on identical simulated
label streams and retain the cadence, breach, change time and catch window.

The chained finite-horizon construction uses:

```text
R_t = (R_(t-1) + 1) * (1 + lambda * (X_t - p0))
```

Under its conditional-mean null and horizon `H`, the code's argument uses
`R_t + (H-t)` and a threshold scaled by `H/alpha`. This applies established
sequential-detection theory. The empirical figures are Monte Carlo operating
characteristics under the declared scenarios.

The historical capped monitor and the later repaired runtime are different
implementations. A frozen result for the former cannot be relabelled as a
measurement of the latter.

## Recall on traffic

If the flagged pool is fully reviewed, its confirmed positives `TP` are a
census for that pool. For unflagged volume `N_u` and error prevalence `q`:

```text
R(q) = TP / (TP + q*N_u)
dR/dq = -TP*N_u / (TP + q*N_u)^2
```

A recall margin must be propagated through this derivative. Substituting the
recall margin directly into a prevalence-sizing formula targets the wrong
quantity.

The retained label plans also depend on workload assumptions, discrete and
finite-population planning, and a stated assurance of attaining the margin.
The derivative alone does not produce the headline count. Neyman allocation
requires information unavailable on day one; the measured simulation design
effect is not a measured customer cost.

## Interpretation rule

An appropriate formula, valid input schema or matching replay does not establish
correct labels, authentic origin, representative traffic, absence of hidden
selection, a causal mechanism or product demand. Use the
[individual ledger](claims.md) for the narrower checks completed for each claim.
