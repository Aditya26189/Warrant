# Exact assurance-semantics diagnostic

This is a proof sketch and independent arithmetic reproduction of the known
[FPR-001 example](../fpr_reporting/issues/FPR-001-adaptive-bound.md), not a new
theorem, a survey outcome or a production fix. Human statistical review of the
code-to-proof mapping remains outstanding.

## Three different statements

Let D contain n IID benign calibration scores, with the scoring rule fixed
independently of D. Let t(D) be a selected threshold and R(D) its true
same-source benign false-positive probability. A requested budget B and
calibration failure probability delta can support

    P_D{R(D) > B} <= delta.

This does not imply a returned data-dependent number U(D) satisfies

    P_D{R(D) > U(D)} <= delta.

Neither statement is interchangeable with the marginal expectation condition
E_D[R(D)] <= B. The quantifier distinction is established theory, not our
contribution; see [Bian and Barber, §2.2 / Theorem 1](https://arxiv.org/html/2205.03647)
and [Coppola and Mazo, §§2–4](https://arxiv.org/html/2502.07497v1).
Do not conclude conformal prediction is generally invalid: evaluate the exact
prediction object and guarantee in the procedure being considered.

## Derivation for the preserved witness

Let U_j solve P{Bin(n,U_j)<=j}=delta, with fixed n and delta. Select K=1
by the requested budget: U_1<=B<U_2. For represented scores in {0,1,2}, set

    P(S>0)=q1, P(S>1)=q2,
    U_1 < q1 <= B, and U_0 < q2 <= U_1.

These strict and non-strict inequalities matter. The preserved decimal inputs
meet them; the diagnostic checks them through exact binomial CDF comparisons.
The selected pivot is the ascending order statistic X_(n-1), with strict firing
above that pivot. For these three float64-represented scores this agrees with
the production successor-threshold convention.

Write M1=#scores>=1 and M2=#scores>=2. All possible selected risks are
q1, q2 and zero, so the requested-budget violation event is empty.
The realized-count CP value has the following cases:

| Count event | Pivot | Realized count | Population risk | Returned bound covers? |
|---|---|---|---|---|
| M1<=1 | 0 | M1 | q1 | No, since U_0<=U_1<q1 |
| M1>=2, M2=0 | 1 | 0 | q2 | No, since U_0<q2 |
| M1>=2, M2=1 | 1 | 1 | q2 | Yes, since q2<=U_1 |
| M2>=2 | 2 | 0 | 0 | Yes |

The disjoint failure events are A={M1<=1} and C={M1>=2,M2=0}.
Their probabilities are

    P(A) = (1-q1)^n + n*q1*(1-q1)^(n-1),
    P(C) = (1-q2)^n - (1-q1)^n - n*(q1-q2)*(1-q1)^(n-1).

Therefore

    P(noncoverage) = (1-q2)^n + n*q2*(1-q1)^(n-1).

Replacing the numerical report by the fixed design value U_1 in this model
would leave only event A as noncoverage, whose probability is below delta
because q1>U_1. This is an illustrative evaluation of the existing proposed
repair, not selection or authorization of a production repair. Compatibility,
groups, other ranks and all consumers require their own review.

The exhaustive program sums multinomial probabilities over count triples,
not over independent simulated data. It never calls Warrant, SciPy or NumPy.
It independently checks the closed form, total mass, requested-budget event
and fixed-design event using exact fractions. The retained
[config](../../../experiments/assurance_semantics/config.json) is the existing
witness, without a parameter search or random seed.

## Reproduction

Run from a clean checkout of the source commit recorded in the artifact:

```powershell
python -m experiments.assurance_semantics.exact --config experiments/assurance_semantics/config.json --output results/publication/assurance_semantics.json
```

The [artifact](../../../results/publication/assurance_semantics.json) records
exact fractions, readable approximations, config bytes' hash and source HEAD.
It is a separate artifact commit, so its source revision precedes the commit
containing it. The generator refuses a dirty worktree. Save verification copies
outside the checkout or use a separate clean worktree for repeated runs.

Scientific role: establish a source of possible interpretation error that the
audit can distinguish from a budget violation. The literature may contain
none of this error. Its presence in Warrant cannot establish its prevalence,
the novelty of post-selection effects, or usefulness of a full paper alone.
