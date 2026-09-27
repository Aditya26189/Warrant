# Independent project review: Warrant

Reviewed 22-23 September 2026. Source anchor:
`cc1904e2215e1c6a85847125aef8997a2e0caac6` (`main`).

## Judgment

**Keep the project, narrow the promise, and repair the customer path before a
pilot.** Warrant has a substantive statistical and reproducibility foundation.
It is not yet a dependable installed product or a demonstrated venture-scale
business. This review found fresh-install failures, invalid grouped uncertainty,
and remaining lifecycle/integrity failures on the merged main branch.

Claude's recent work is useful and should be preserved. Its conclusion in
`reports/NEXT-STEPS-2026-09-17.md` that the engineering question is answered
well enough is too optimistic: the existing checks miss important customer
operations and statistical counterexamples. Its recommendation to test demand
before another broad feature sprint is sound. Correctness repairs and customer
discovery can proceed in parallel; neither substitutes for the other.

The founder's last supplied commercial evidence was none: no interviews, design
partners, pilots or revenue. No new commercial evidence was supplied during this
review. This is a statement about available evidence, not a prediction of failure.
No honest repository review can guarantee correctness, funding or founder success.

## Scope and verification ledger

The execution environment was Windows with Python 3.12.10, NumPy 2.2.6,
SciPy 1.16.3 and PyYAML 6.0.3. Linux CI status was not checked remotely.

The review used an isolated worktree from main, read-only subreviews of chain
integrity, statistical customer paths and packaging, independent counterexamples,
and current primary-source checks of competing products. Original dirty and
unfinished worktrees were preserved. No production source was changed, no
frozen scientific test set was selected on or rescored, and no customer data,
outreach, deployment or paid compute was used.

| Check | Evidence and limit |
|---|---|
| Current source | Main remained at `cc1904e` during review. The original shared checkout remained on older `feat/release-evidence`; the old unfinished integration worktree was not treated as the product. Running commands from that original checkout does not exercise current main. |
| Full suite | `python -m pytest -o addopts= -q --tb=short --junitxml=...`: **1,866 passed, 1 xfailed, 3 warnings; exit 0**, in 2,061.24 seconds. JUnit and the exit code were retained outside the checkout. The source tree stayed clean for the run. |
| Published claim crosswalk | `python scripts/verify.py --claims-only`: exit 0, 92/92 match their committed artifacts. Frozen-score and activation recomputation were explicitly skipped in this invocation. |
| Packaging/documentation/provenance tests | Independent bounded run: 95 tests passed, exit 0. These checks coexist with the installed-wheel defects below. |
| Installed wheel | Built from `git archive cc1904e`, installed into an isolated target, executed with `python -I` resolving Warrant from that installed package. Dependencies came from the existing interpreter; this was not a fresh dependency environment. Default certification fails; an explicit source config then exposes a missing package. Root reviewer independently repeated both failures. |
| New counterexamples | Synthetic grouped duplication and verdict precedence reproduced independently by two reviewers. Chain concurrency and malformed records exercised through public commands. These are regression inputs, not product performance measurements. |
| Existing clean-clone gate | `results/clean_clone.json` records source `e03279d`, smoke 7/7, claims 92/92, frozen scores 25/25 and test subprocess exit 0. Activation reproduction is skipped. The gate used the existing Windows interpreter, not a fresh wheel-only installation. Later changes through `cc1904e` are documentation/artifact changes. |
| Decision reconciliation | Preserved Codex entries match the original `55528c7` tail byte-for-byte, including per-entry hashes. No history corruption found. Automated enforcement of this scoped archive is still missing. |

A matching claim table establishes that prose agrees with stored artifacts.
Recomputing frozen scores establishes a deeper arithmetic link. Neither proves
the original model execution, population representativeness, label validity,
customer benefit, or correctness in untested cases. A passing suite also does
not establish those claims: the failures below are outside its present coverage.

## What is already good

- A small local scored-file interface avoids requiring customers to expose model
  activations or install the research GPU stack. The boundary is sensible for an
  initial offline evaluation product.
- Input parsing rejects duplicate IDs, ambiguous columns, ragged CSV and repeated
  JSON keys. Refusal is separated from malformed input.
- Release protocol 2 binds declared identity, fixed criteria, disjoint ID sets,
  expiry and evidence digests. Its simultaneous intervals and separate recall/FPR
  requirements are more precise than a generic quality score. Registration still
  relies on declarations; it does not authenticate the actual deployed system.
- Sequential rechecks retain state and disclose the scope of their FPR guarantee.
  Power studies and label-error sensitivity address operational questions that an
  AUROC alone cannot answer. Assumptions and negative results are often explicit.
- Claude repaired the original ordinary drift-REVOKED continuation, derived-field
  comparison and ordinary zero-alpha failures. A retained whole-record seal now
  detects edits to status, metrics and provenance. These old cases were checked
  again and should not be reported as unfixed.
- Small commits, preserved scientific artifacts, an append-only decision trail,
  source gates and explicit skipped tiers give future reviewers useful evidence.

## Confirmed findings, in repair order

P1 means a material correctness or customer-operation failure to close before
relying on the affected workflow. P2 means a narrower failure or assurance gap
that still needs an explicit disposition. These are engineering priorities,
not CVSS security ratings. Source line numbers refer to the pinned revision.

### R1. P1: the built wheel cannot perform ordinary certification

There are two independent packaging faults:

1. `controlplane/cli.py:120,157,235` locates the default config relative to the
   installed package. The wheel has no `config.yaml`; `config.py:968-969` raises
   `ConfigError`. Installed certify, plan and recheck fail with exit 1.
2. With an explicit config, certify reaches `intake/certify.py:286`, imports
   `intake/labels.py:42`, and raises `ModuleNotFoundError` for
   `controlplane.sampling`. `pyproject.toml:31-49` uses a package list that omits
   it. Ordinary certification is affected even without second-review labels.

The audited wheel SHA-256 is
`a64258b0f6c2f181a760d1db3a10c3c9551e413c298204d40d8b432d18d2a25a`.
Its version and release-help checks pass. As a positive control, an installed
release registration/evaluation/seal/verification API round trip returned VALID
and verified successfully on a synthetic fixture. This does not exercise every
release CLI operation. CI at `.github/workflows/ci.yml:58-86`
tests installed release imports/help, then runs real customer examples and tests
from the source checkout. That arrangement masks both missing resources.

**Close with:** packaged defaults loaded through an installed-resource mechanism,
all customer runtime packages included, and real wheel-only workflows executed
outside the source tree. Keep the minimal dependency promise; source imports or
an editable install do not demonstrate a distributable package.

### R2. P1: grouped recall and precision gain false certainty from duplication

`validation/stats.py:538-555` falls back from a degenerate grouped bootstrap to
row-level Clopper-Pearson intervals. `validation/metrics_builder.py:115` supplies
a row denominator. That fallback discards the dependence which the group column
explicitly declared.

Synthetic construction: 60 negative groups and four positive groups, homogeneous
labels within groups, perfectly separating scores. With one row per group,
recall and precision lower limits are `0.3976353644`. Repeat each row 100 times
without changing group membership: both lower limits become `0.9908201954`.
The same four independent positive groups produced both results. The certified
FPR bound, negative-unit count and operating point are unchanged.

This is more than an unattractive interval. In this homogeneous-group construction,
if true group recall is 0.5, all four positive groups succeed with probability
`0.5**4 = 0.0625`. That event alone exceeds 5% noncoverage for the interval near
one. The four-group binomial comparator is justified for this construction;
it is not a general prescription for arbitrary mixed groups.

**Close with:** a deliberately specified group-aware boundary treatment, or
withholding unsupported inference with a reason. Add uniform within-group duplication invariance and
boundary tests for both precision and recall. Do not silently replace every
denominator with the number of groups: the estimand and mixed-group assumptions
must be defined first. `validation/stats.py` is a protected area in local rules;
assign an explicit repair owner and record the method before editing it.

### R3. P1: a weaker FPR warning suppresses independently established drift revocation

`intake/recheck.py:601` returns STALE for an observed FPR above the budget whose
lower bound does not establish a breach. It returns before checking a REVOKED
drift verdict at line 612. `apply_chain` at lines 764-765 revisits drift only in
the other branch, where `bound_still_holds is False`.

The synthetic example in the appendix gives overall STALE, drift REVOKED,
`bound_still_holds=True`, FPR 0.06 and lower bound about 0.02645. A subsequent
stable sample becomes VALID, and the history verifier reports clean. This was
reproduced with valid seals, no tampering and no missing head file.

The old fix correctly handles an overall REVOKED parent. This different path
never gives the parent that overall status. `chain.py:508` and
`chain_verify.py:250-251` consequently miss it.

**Close with:** explicit aggregation of independent findings so a weaker warning
cannot demote a revocation; test all bound/drift combinations through ordinary
and chained recheck, including the subsequent continuation and history verifier.
Keep the sequential FPR guarantee separate from the independent drift criterion.

### R4. P1: concurrent CLI writers create undeclared chain forks

The CLI reads the head at `cli.py:600-607`, writes its record, and only later
advances the head at line 655. `chain.py:423` performs an ordinary head write;
there is no transaction spanning these steps.

Two simultaneous public recheck commands against one fresh warrant, with
different scored files and output names, both exited 0. Both wrote sequence 1
with `head_check=no_sidecar`, without `--fork`. The final sidecar named one of
the two records. Exclusive creation of output files does not protect this shared
state transition.

**Control:** if both records are supplied to verification, it reports a restart.
The defect is silent admission of two writers and loss of one branch from the
head, not failure to detect a fully retained fork. The evidence does not quantify
an aggregate false-alarm rate across those independent branches.

**Close with:** a per-warrant transaction or lock spanning head read, validation,
record publication and head update, with recovery semantics for interrupted
writes. A multiprocess regression must show one writer succeeds and the other
refuses/retries without creating an undeclared fork or corrupting the head.

### R5. P1, known and unfinished: grouped reviewer agreement uses item resampling

`intake/labels.py:452,493-505,866` computes agreement without actual group IDs.
Four groups of repeated reviewer pairs produce an interval and `n=400` as if
there were 400 independent pairs. Decision 201 preregisters a remedy; it does
not implement one. The partially edited older Codex worktree is not main.

**Close with:** the preregistered descriptive grouped agreement, withheld population
interval, explicit reason, reviewed-pair count and distinct reviewed-group count.
Preserve the existing ungrouped calculation, withhold second-review dispute
extrapolation for grouped inputs, and preserve supported whole-group primary-label
sensitivity ladders. Update INPUT, LIMITATIONS and PILOT-PROTOCOL with the implementation.

### R6. P2: deleting a seal downgrades a modern record into accepted legacy input

`chain.py:115-122` treats an absent seal as legacy. `chain_verify.py:89,166`
lists the record as unsealed but still reports clean; `cli.py:282` therefore lets
`--require-clean` succeed. The renderer calls it a record written before sealing,
which cannot be inferred from absence alone.

Starting with a new CLI-written record, deleting `record_sha256` and changing
status/reason/drift produces exit 0 and `clean=true`. No checksum recomputation
is needed. Continuation also accepted that record using a copied warrant without
its original sidecar. The output does disclose that it is unsealed.

This differs from the documented limitation that a person controlling all copies
can rewrite and rehash them. It is an assurance-policy downgrade. The broad claim
in NEXT-STEPS that edits necessarily require resealing is false for this case.

**Close with:** distinguish unknown/unsealed integrity from verified integrity;
provide a strict sealed-history requirement for modern automated use while
retaining explicit legacy inspection. Do not describe an unsealed record's age
as established. Rewriting history with fresh checksums remains outside the
guarantee unless an external trust anchor is introduced.

### R7. P2: malformed but valid JSON still causes public-command tracebacks

An arbitrary-size integer such as `10**1000` in `chain.alpha` or
`chain.horizon_units` reaches overflow-prone validation/arithmetic
(`chain.py:150,197`). The public verifier exits 1 with `OverflowError`. A
`--since` file containing `[]` exits 1 with `AttributeError` because the outer
record type is not checked before dictionary access.

The same oversized-integer failure also exists in Codex-authored release
registration: `release/contract.py:78` calls `math.isfinite` before establishing
representability, and `release/cli.py:66` does not catch the overflow. A public
`release register` command with `threshold=10**1000` exited 1 with a traceback
and created no contract. The repair must cover both record families.

**Close with:** outer-schema/type checks and representable numeric-domain checks
before arithmetic; return a malformed finding or the documented input-error
exit, never a traceback. The existing ordinary zero/NaN fixes should remain.

### R8. P2: PSI noise calibration assumes the old and new files have equal sizes

`intake/recheck.py:330` passes `n_reference=items.n`, substituting current sample
size for the historical reference size. The simulator in `drift/null_band.py`
explicitly accepts separate sizes.

A 100-item reference against 10,000 current items yielded PSI `0.169460`.
Current code uses null p95 `0.003239`; the same simulator with reference size
100 gives `0.186492`. The current decision is STALE; with the actual size its
rule returns STABLE. This is a synthetic counterexample, not measured false-alarm
frequency. The historical sample size is available in certificate metadata but
does not reach this calculation.

**Close with:** carry and validate the actual reference sample size, with explicit
legacy behavior if it is absent. Test unequal reference/current sizes and retain
the existing warning for smoothing-dominated PSI. Restoring this input does not
by itself establish nominal coverage of the plug-in simulation or account for
data-selected histogram edges.

### R9. P2: the handoff combines evidence from potentially different operating points

`docs/EVIDENCE-HANDOFF.md:36-40,170-175` says to attach certification of the same
scored file to supply release label-quality evidence. Shared rows do not establish
the same threshold, flags or statistical protocol. `certify` selects a threshold;
release evaluates its preregistered threshold. The sensitivity ladders depend
on those threshold-specific counts.

For a synthetic file with 96 negative scores at 0.1, four at 0.9 and 20 positive
scores at 0.85, certification at budget 0.05 selects
`0.9000000000000001` and flags nothing. A predeclared release threshold 0.8 flags
24 rows on the same file. A ladder for the first cannot support the second.
Their one-sided versus simultaneous-family uncertainty protocols also differ.

**Close with:** state that only threshold-independent descriptive label agreement
can be attached generically. Operating-point sensitivity must be computed and
identified for the release threshold and its relevant method; do not turn an
unbound second certificate into evidence for the first verdict.

### R10. P1 in the legacy runtime path: the mixture monitor still revokes early

This previously reported issue remains in `validation/warrant_stats.py:203-208`.
After two false positives, `FPRMonitor(p0=.05)` reports wealth 20 and revokes.
The actual mean of its component wealths is about `14.20585`, below the boundary
20. The cap uses a component maximum rather than the claimed mixture statistic.
Root independently repeated the counterexample on current main.

This proves an incorrect decision for that path; it does not estimate lifetime
false-revocation probability. The newer customer recheck chain uses different
statistics and must not be blamed for this specific cap defect.

**Close with:** an explicitly owned protected-code repair using stable log-mixture
arithmetic, validated state and an independent stopping-rule review. Keep the
claim scoped until fixed. The known native Rego undefined-result abort and
misdocumented PSI epsilon are other unresolved legacy findings, not new discoveries
of this review; Linux behavior was not rerun here.

## Product and architecture gaps

**The customer story crosses incompatible records.** Release has declared identity,
expiry and data binding, while certify/recheck provide label diagnostics and
grouped inputs but lack that complete identity/lifecycle contract. An unchained
recheck does not identify its parent warrant and ignores a revoked chain head;
a public-command reproduction returned VALID after a chain revocation. This is
already documented, but it needs a product decision before automated reliance.
A guide cannot supply missing machine-enforced bindings.

The next schema work should unify identity, source hashes, operating point,
sampling unit, criteria, label rubric, lifecycle and parent linkage at the record
boundary. Preserve legacy replay with explicit versions. It should not be a
second parallel orchestration platform. Do this after correctness repairs and
against one concrete handoff requirement.

**Operational scalability is unmeasured.** The local CLI is an appropriate pilot
shape; absence of SSO, tenancy, high availability or a hosted UI is not itself a
bug in that scope. It also means the repository does not establish a global
enterprise service. Shared-state races matter even for local automation. Load,
memory use, repeated run costs, restore procedures and operational support have
not been independently benchmarked here. Choose infrastructure only when a real
customer deployment requires it.

**Some checks validate descriptions more than behavior.** The wheel example shows
why installed imports and source tests need a real packaged workflow alongside
them. Likewise, scoped archived citations and their hashes are not checked by
the current decision test: `CODEX-PARALLEL.md 999` is ignored and
`DECISIONS 198a` matches numeric 198. The actual preserved archive is correct;
this is a future regression gap, not evidence that history was altered.

**Assumptions remain the expensive part.** Unique IDs do not establish independent
sampling, correct labels, untouched selection data or authentic model versions.
Stable score histograms do not establish stable correctness. Record the source
of each assurance, make missing evidence visible, and avoid relabelling every
uncertainty as a statistical interval problem.

## Market and fundability assessment

Primary sources were checked on 22 September 2026. These are capability and
problem statements, not independent evidence of vendor efficacy or Warrant demand.

| Source | What it supports | Consequence for this project |
|---|---|---|
| [Bank of England AI roundtables](https://www.bankofengland.co.uk/minutes/2026/february/summary-of-ai-roundtables-feb-2026) | Participants described validation bottlenecks, skills constraints and difficulty scaling traditional validation to generative systems. | The problem is credible; this does not establish a buyer for this implementation. |
| [ValidMind guides](https://docs.validmind.com/guide/guides.html), [attestations](https://docs.validmind.com/guide/attestation/working-with-attestations.html), [breach workflows](https://docs.validmind.com/guide/monitoring/trigger-workflows-on-threshold-breach.html) | Documented validation reports, evidence/artifacts, review/sign-off and monitoring-triggered workflows. | The validation/evidence layer is an existing category. Avoid the unsupported README positioning that almost nobody supplies it. |
| [LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types) | Offline datasets and regression evaluation, production evaluation and human-review feedback loops. | A generic evaluation/monitoring dashboard is not a distinctive first investment. |
| [Braintrust evaluation](https://www.braintrust.dev/docs/evaluate) | Experiments, CI evaluation, online scoring and feedback into datasets. | Another broad eval platform would face established workflows. |

My inference is that Warrant's best candidate entry point is **a narrow,
independently reviewable evidence package for one recurring detector decision**,
integrated into a buyer's existing process. Its most useful possible distinction
is explaining when evidence is insufficient and what additional review would
resolve the decision, with explicit sampling and label-quality limits.

That is a hypothesis. Binomial intervals, bootstraps, hashes and sequential tests
are not by themselves a durable commercial moat. Defensibility would need to
come from accepted workflow integration, trustworthy evidence history, repeatable
domain-specific validation, efficient labelling, or distribution. None is yet
commercially demonstrated. An MIT codebase can support a company, but the paid
value must exceed what a customer can copy or implement internally.

The model-validation function is a plausible user, not an established economic
buyer. Identify separately who experiences the pain, who approves the method,
who provides the data, who can purchase, and who owns the consequences of a
refusal. A claimed regulatory need is not a purchase order. This review does not
establish the current legal status of every regulation cited by older reports.

The economic test is total workflow cost and decision usefulness: data extraction,
rubric design, blinded labels, adjudication, integration, reviewer sign-off and
repeat operation, as well as computation. Existing reviewer-time and workload
figures are declared scenarios. Do not convert them into customer savings or
market size without customer measurements.

For funding, the strongest next evidence would be a named buyer's recurring
problem, a retained output that changes or supports a real decision, a comparison
with its existing process, and paid repeat use. The current code can support
preparation for that test after repairs. More internal simulations, documents or
test counts alone do not establish product-market fit or venture scale.

## Recommended sequence

1. Repair distribution, grouped inference and verdict/chain transitions. Use the
   reproduced cases as regression tests and preserve all already-valid behavior.
2. Add strict integrity policy, malformed-input coverage and a coherent record
   handoff; correct overbroad claims immediately, without changing old evidence.
3. Run one installed-package customer journey from a clean environment with a
   valid result, a refusal, grouped handling, a recheck and retained verification.
4. In parallel, prepare the existing pilot/discovery materials for one buyer and
   one recurring decision. The founder conducts or explicitly authorizes contact;
   agents do not invent conversations, commitments or customer data.
5. Expand features only when correctness or observed customer needs justify them.

Claude's repair brief is [CLAUDE-INSTRUCTIONS-2026-09-23.md](CLAUDE-INSTRUCTIONS-2026-09-23.md).
It supersedes stale assignments in the uncommitted September 16 draft; it does
not reopen the already-completed integration.

## Reproduction appendix: statistical counterexamples

Run from the pinned source checkout with its dependencies. These synthetic
examples write no artifacts and perform no scientific dataset scoring.

```python
from dataclasses import replace
import numpy as np
from controlplane.config import load_config
from controlplane.intake.certify import certify_items
from controlplane.intake.contract import ScoredItems
from controlplane.intake.recheck import recheck_items, score_distribution

config = load_config("config.yaml")
config = replace(config, validation=replace(config.validation, bootstrap_samples=100))

def items(labels, scores, groups=None):
    return ScoredItems(
        tuple(map(str, range(len(labels)))), tuple(map(int, labels)),
        tuple(map(float, scores)), None if groups is None else tuple(groups),
        (), "synthetic review",
    )

for copies in (1, 100):
    labels = np.repeat([0] * 60 + [1] * 4, copies)
    groups = np.repeat([f"g{i}" for i in range(64)], copies)
    result = certify_items(config, items(labels, labels, groups), budget=.05)
    print(copies, result.negative_units, result.recall.ci_low, result.precision.ci_low)

scores = np.repeat(np.arange(.05, 1, .1), [10] * 8 + [858, 62])
labels = np.ones(1000, dtype=int)
labels[:94] = 0
labels[-6:] = 0
result = recheck_items(
    config, items(labels, scores), budget=.05, threshold=.94,
    reference=score_distribution(np.linspace(0, 1, 1000)),
)
print(result.status.value, result.drift_verdict, result.bound_still_holds)
```
