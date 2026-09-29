# Phase 21 — fixed-threshold release label audit

**Answer.** A retained release evaluation can now have a separate,
replayable label audit at its **registered threshold**. It reports how many
primary-label errors of each of two adverse kinds, considered separately,
would first make a VALID release fail one of its existing acceptance bounds.
Optional `label_2` values add observed second-review disagreements in those
same two pools. The evaluation's verdict, threshold, five-interval family and
expiry do not change. This closes the specific operating-point gap recorded in
`docs/EVIDENCE-HANDOFF.md`; it does not tell us which labels are true.

The business status is unchanged: the founder reported no buyer interviews,
design partners, paid pilots or revenue. An auditable feature is not evidence
that an enterprise will buy this product. The 8–12 conversations and
pre-registered stop rule in `reports/NEXT-STEPS-2026-09-17.md` remain the first
commercial gate.

## Why this was needed

`warrant release evaluate` tests one threshold frozen before a holdout is
scored. `warrant certify` chooses a different threshold to clear a budget and
prints its own label-error ladder. Transferring that ladder to a release would
silently claim that two different operating points have the same fragile
items. The handoff document explicitly forbade this. Decision 216 registered
the new audit before implementation, without changing either estimator or
the protected research test set.

The audit first calls the ordinary release verifier on the complete registered
holdout and supplied scorer identity. A missing evaluation, changed ID, score,
primary label, criterion, identity or evaluation field fails before an audit
file is written. It then stores the exact contract and evaluation identifiers,
the evaluation's primary-row digest, and a second digest of the **ordered**
effective rows including optional `label_2`. A new companion is written once;
the command will not replace an existing copy. `verify-label-audit` checks its
checksum and recomputes the whole material body from retained files. A
rewritten count with a recomputed checksum still fails replay.

## The calculation and its limit

Write the observed fixed-threshold counts as `fp`, `negative`, `tp` and
`positive`. For `a` flagged positives actually clean, the corrected counts
are `(fp+a, negative+a, tp-a, positive-a)`. For `b` unflagged negatives
actually positive, they are `(fp, negative-b, tp, positive+b)`. Both corrections
weakly worsen the relevant FPR upper and recall lower bounds. The audit finds
the first count in **each direction alone** that makes either registered
criterion fail, using the same two-sided Clopper-Pearson intervals and
`alpha/5` allocation as release evaluation. An absent denominator fails; a
`null` first count means that one direction cannot fail within its finite
eligible pool. The output also shows the bounds after one correction.

Those counts are a deterministic stress test conditional on the hypothesized
corrections, not a probability that labels are wrong, a combined-error bound,
or a new release decision. If the retained evaluation is REFUSED or legacy
UNVALIDATED, the stress ladder is withheld; it never offers a label-edit route
to approve a refusal. If the release has expired, the companion says STALE
and cannot restore current validity.

When `label_2` is present, the companion counts reviewed and disputed items
in the two adverse pools at this registered threshold. A disagreement does
not establish which reviewer is right. The reviewed pairs may have been
selected after seeing scores; no population inference, independence or blind
review is asserted. Unlike a certify ladder, these particular counts really
belong to the release operating point, but they still do not establish label
truth. This follows the [NIST AI RMF Measure playbook](https://airc.nist.gov/airmf-resources/playbook/measure/)
emphasis on data quality and ground-truth validity as a measurement concern;
it is not a claim of NIST conformance.

## Validation ledger

- The missing CLI was reproduced in red tests before implementation. Source
  CLI tests then passed for a valid audit, a refused release, missing or
  changed evaluation input, optional second labels, no overwrite, and changed
  second-review values. A separate test corrected exactly the reported number
  of synthetic labels and independently reran the full release evaluator at
  the fixed threshold: the preceding count remained VALID and the reported
  count was REFUSED for both directions.
- An attack test changed the reported tolerance, recomputed `audit_id`, and
  confirmed that `verify-label-audit` still rejected the forged calculation.
  The neighboring release, contract, report, docs and decision tests passed.
  Ruff and whitespace checks passed. The new commands also passed from a built
  and installed wheel, not only a source checkout.
- Source review caught that the companion used the effective-row digest in
  `intake/certify.py` but its software manifest did not hash that module. A red
  test reproduced the omission. The audit now includes that source in its
  manifest, while an ordinary evaluation's manifest stays unchanged. Source
  release tests and a rebuilt-wheel check passed after the correction.
- A documentation cross-check found two stale descriptions: the handoff said no
  release-threshold label audit existed, and the methods guide described
  grouped reviewer intervals as if decision 201 had not landed. Both now match
  the implemented paths (`d746e26`); focused documentation and invariant tests
  passed before integration.
- The first clean-source inventory changed from 2,083 to 2,089 collected tests
  at feature commit `67d3663`. After this report and two inherited chain
  regression cases were added, the successor inventory records **2,093
  collected tests**. Its final clean-source provenance is `b80ff30`
  (inventory commit `eb098a9`) after the source-manifest repair and Phase 20
  close-out report.
  Collection is not execution. The full `tests/` suite on clean feature source
  `52a87eb` exited **0**, with one expected xfail and no failures. The later
  `d746e26` change is documentation only; its affected documentation and
  invariant checks passed separately. `python scripts/verify.py
  --no-activations` reproduced **92/92** README claims and **25/25**
  frozen-score comparisons; the activation tier was **SKIPPED**.

## Product and commercial interpretation

The [LangSmith evaluation documentation](https://docs.langchain.com/langsmith/evaluation-types)
already describes offline datasets, reference answers, online evaluation and
human review. **Inference:** a generic evaluation dashboard is not a credible
unique wedge here. [Braintrust's current CI/CD page](https://www.braintrust.dev/learn/ci-cd/v0)
also advertises pull-request evaluations, threshold-based merge blocking and
experiment comparisons. **Inference:** even a generic release gate is an
incumbent feature. The narrower candidate is a *defensible* release decision:
criteria registered before scoring, exact replay, visible uncertainty, and
label fragility at the same operating point. No buyer has said that this
distinction matters more than an incumbent's integrations. It remains a
product hypothesis, not proof of a budget holder or procurement path. This
repo still lacks a customer-labelled deployment sample and measured buyer
willingness to pay.

## What this does not establish

The current companion is local evidence, not authenticated custody. A person
who controls the contract, evaluation, scored rows and audit can rewrite a
coherent set and all checksums. The audit also cannot detect semantic
duplicates, verify the actual deployed detector version, prove pre-registration
time, establish representative IID sampling, or fix the grouped-release gap.
Those remain barriers to relying on it as a production release authority.

## Open items

Remote CI remains unobserved.
The first Phase 20 full run found three stale test expectations about the
new `label_2` row digest; those suites passed after the tests were corrected.
The repaired Phase 20 full run exited 0 with one expected xfail and no
failures; its claim and frozen-score gates passed separately. An early Phase
21 full run was stopped when the missing audit source hash was found, before
it could serve as a final gate. The provenance-fixed successor's full suite
subsequently exited 0. This local gate does not establish customer deployment,
representative labels or authenticated custody.
The separate business gate is still the buyer
conversations and their registered stopping rule; more local checks cannot
substitute for them.
