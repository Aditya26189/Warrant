# Warrant claim audit — 14 September 2026

The release-evidence extension improves traceability and the statistical
contract. It does not establish commercial demand, enterprise readiness or
fundability. This audit corrects the scope of earlier claims and keeps known
defects visible. It is an engineering review with primary-source checks, not
an independent assurance opinion.

The [viability assessment](STARTUP-VIABILITY-2026-09.md) was based principally on
revision `9a5336b`. The new implementation began from `7ae68d3`; its working
release CLI is committed at `369a829`. Historical result files were preserved.
The separate reviewers hit an account usage limit; no completed external or
independent expert review is claimed. Other private chats were not available.

## Section-by-section findings

| Assessment section | Finding and basis | What remains unproved |
|---|---|---|
| Investment judgment | Keep the conclusion: plausible problem, unvalidated business. The founder reports no customer evidence. | A budget owner, purchase event, willingness to pay, retention and repeatable sales. |
| Existing product | The original research and legacy CLI are real; release registration and fixed-holdout evaluation are now additive code. | A production deployment or complete application assurance. |
| Experiment | Recorded probe metrics remain recorded results; the claim-table check establishes consistency with artifacts. | Fresh model reproduction, cross-model generalisation or customer outcomes. |
| Competition | Existing model-validation platforms already offer workflows and attestations. See primary vendor documentation below. | That Warrant saves more effort or produces better decisions than those alternatives. |
| Regulation | Preserve the jurisdiction and scope qualifications. Current official pages support the revised timing and US guidance caveats. | Legal applicability to a particular customer or any obligation to purchase Warrant. |
| Technical risk | Identity, fixed criteria, disjoint IDs, expiry and reproducible evidence are implemented for the new IID path. | Authentication, grouped inference, repeated-study control and label quality. |
| Economics | The scenario file contains declared assumptions and arithmetic. It is not a customer quote or performance forecast. | Actual label effort, integration costs, price acceptance or gross margin. |
| Initial market | AI support vendors selling into financial services remain a proposed interview segment. | That this segment has a sufficiently frequent and expensive unmet problem. |
| Defensibility | Workflow adoption and longitudinal evidence are possible advantages, not current assets. | A moat, proprietary dataset, distribution advantage or switching costs. |
| Commercial programme | Discovery and paid repeat use are measurable future gates. No outreach, pilots or purchases occurred in this work. | Every commercial gate. |
| Build priorities | A narrow reproducible evidence workflow was added; a broad platform remains unjustified by demand evidence. | That this feature is the customer's most valuable missing capability. |
| Conclusion | More credible software is necessary progress, but it does not reverse the pre-customer investment conclusion. | Funding or venture scale. |

## Corrections to technical interpretation

**Long-context evidence has a narrower meaning than the earlier prose made
explicit.** The padded evaluation reuses answers and labels from the original
short-context generation. It tests how the probe's scores transfer against those
labels. It does not measure whether newly generated long-context answers are
correct. The actual token range also differs from the nominal construction
target. These limitations are already recorded in [SPEC](../docs/SPEC.md),
DECISIONS 171 and the extraction artifacts. Do not describe this as a measured
long-context production error detector without a new prospective experiment.

**The power correction is completed.** The earlier assessment described decision
183 as active development. Its implementation is `2259065`, with recorded checks
at `7ae68d3`. It prices a declared probability of detecting a breach. This does
not provide a lifetime error guarantee for repeated CLI rechecks.

**Grouped rechecks remain OPEN.** In
[intake/recheck.py](../controlplane/intake/recheck.py), the group array is
discarded before a row-level binomial calculation. Group-aware issuance does
not make this later calculation group-aware. Closure requires a justified
sampling-unit contract, an implementation matching it and regression/coverage
checks on dependent data. The new release path rejects grouped input; that
prevents reuse of this defect in the new workflow but does not repair the old
one or detect undeclared dependence.

**The legacy continuous monitor has a confirmed implementation defect.** In
[warrant_stats.py](../controlplane/validation/warrant_stats.py), `wealth` caps
based on the maximum component log wealth. The claimed stopping statistic is
the mean of component wealths. A maximum crossing that implementation cap
does not establish the mean crossed the revocation boundary.

This minimal reproduction exercises the preserved implementation without
scoring any research dataset:

```python
import numpy as np
from controlplane.validation.warrant_stats import FPRMonitor

monitor = FPRMonitor(p0=0.05)
monitor.update(1)
monitor.update(1)
actual_mixture = float(np.mean(np.exp(monitor._logw)))
assert monitor.revoked
assert actual_mixture < 1 / monitor.alpha
```

The assertions passed during the audit. This proves a premature decision in
that case; it does not estimate the overall false-revocation probability. The
advertised guarantee cannot be justified by treating this implementation as the
stated mixture process. The file is explicitly read-only in `CLAUDE.md`, so it
was preserved and the defect logged in DECISIONS 184. Closure requires a
deliberately authorised repair, stable log-mixture arithmetic, state validation,
replay checks and an independent review of the stopping rule. The release
workflow uses fixed-holdout binomial inference and does not call this monitor.

**Registration is not authentication.** The new contract fixes criteria and
membership and binds them by hash. It cannot prove the holdout was unseen, the
model version truthful, the clock correct or the labels reliable. Renaming IDs
can conceal leakage. Deleting or copying local records does not create a new
statistical guarantee. Rehashed fabricated metrics are rejected by recomputation,
but someone controlling every input and every retained copy can fabricate a
self-consistent story. No cryptographic or independent-signoff claim is made.

## Primary-source checks and their limits

The Bank of England roundtables support the existence of validation and
procurement friction. They report participants' views, including caution in
second-line functions and skills constraints. They do not measure market size,
software budgets or willingness to buy this product. Their mention of older
US guidance reflects when the discussions occurred, not the current US rule.
[Bank of England, February 2026](https://www.bankofengland.co.uk/minutes/2026/february/summary-of-ai-roundtables-feb-2026)

The Federal Reserve's April 2026 letter supersedes SR 11-7. Footnote 3 of its
attachment excludes generative and agentic AI models from that guidance while
still pointing firms toward appropriate governance and controls. A generic
claim that this guidance mandates a Warrant assessment for generative AI would
therefore be wrong. [Supervisory letter](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm),
[attachment, footnote 3](https://www.federalreserve.gov/supervisionreg/srletters/SR2602a1.pdf)

The Commission's current page records the AI Omnibus entering into force in
July 2026 and different application dates for the relevant high-risk categories
in December 2027 and August 2028. Other provisions already apply. This supports
the report's caution against a universal near-term deadline sales pitch; it is
not a customer-specific legal classification.
[European Commission timeline](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)

ValidMind documents workflows triggered by threshold-breach events and permanent
attestation sign-offs. These are direct feature-overlap evidence. They do not
prove comparative accuracy, actual customer adoption of every feature, or a
particular enterprise price. Warrant cannot claim novelty merely for having a
refusal result or an evidence record.
[Breach workflows](https://docs.validmind.com/guide/monitoring/trigger-workflows-on-threshold-breach.html),
[attestation sign-off](https://docs.validmind.com/guide/attestation/approve-attestations.html)

The release interval method follows exact binomial inversion. Allocating alpha
equally over a fixed family and applying the union bound does not require the
five intervals to be independent. IID sampling across the underlying items and
absence of selection on the holdout are separate assumptions. This conservative
construction is established methodology, not a proprietary invention.
[NIST exact binomial intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm),
[NIST Bonferroni inequality](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm)

Other vendor prices and examples in the assessment retain their dated source
links and vendor/assumption labels. This follow-up did not rerun every vendor
trial or independently audit a vendor case study. No exact price or regulatory
deadline should be copied into a customer proposal without rechecking its
current official source and applicability.

## Remaining work in order

The following is a proposed week of work, not a claim that a week of background
execution has been scheduled or completed. Follow the evidence gates rather
than accumulating features.

| Work block | Concrete deliverable | Evidence needed before claiming completion |
|---|---|---|
| Release foundation | Registered identity, holdout membership, scoped criteria and reproducible evidence. | Unit, CLI, installed-wheel and repository regression checks; scope documentation. |
| Statistical reliability | Resolve the OPEN recheck and monitor issues through an explicit method decision. | Adversarial cases, exact calculations or justified simulations, restored-state checks and independent challenge. |
| Change accountability | Bind full application configuration and reviewer rubric to the evidence; describe review handoff. | A real operator can identify what changed and when new evidence is required. |
| Sampling practicality | Support the first customer's actual unit of sampling and review process. | A justified estimator, label-quality checks and measured review effort; no silent assumption of IID rows. |
| Workflow integration | Add one export or CI handoff that a design partner actually needs. | Customer acceptance of the exported evidence in an existing decision process. |
| Commercial validation | Interview material and a bounded pilot protocol with explicit data and buyer responsibilities. | Actual customer conversations and willingness to pay; these cannot be manufactured in code. |
| Investment evidence | A concise, source-linked account of the problem, product, limits and measured pilot economics. | Paid repeat use or clearly labelled absence of it. No invented traction, testimonials or funding probabilities. |

The engineering work can continue autonomously within the repository. Customer
access, independent expert review and a purchase decision require external
participants. None should be marked complete because the software runs.
