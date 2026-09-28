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
- The first clean-source inventory changed from 2,083 to 2,089 collected tests
  at feature commit `67d3663`. After this report and two inherited chain
  regression cases were added, the successor inventory records **2,093
  collected tests** from clean source `d908530` (inventory commit `dc6aa25`).
  Collection is not execution. `python scripts/verify.py --no-activations`
  reproduced **92/92** README claims and **25/25** frozen-score comparisons;
  the activation tier was **SKIPPED**. A full repository execution result for
  this branch has not yet been established.

## Product and commercial interpretation

The [LangSmith evaluation documentation](https://docs.langchain.com/langsmith/evaluation-types)
already describes offline datasets, reference answers, online evaluation and
human review. **Inference:** a generic evaluation dashboard is not a credible
unique wedge here. The narrower candidate is a defensible release decision:
criteria registered before scoring, exact replay, visible uncertainty, and
label fragility at the same operating point. That is a product hypothesis,
not proof of a budget holder or a procurement path. This repo still lacks a
customer-labelled deployment sample and any measured buyer willingness to pay.

## What this does not establish

The current companion is local evidence, not authenticated custody. A person
who controls the contract, evaluation, scored rows and audit can rewrite a
coherent set and all checksums. The audit also cannot detect semantic
duplicates, verify the actual deployed detector version, prove pre-registration
time, establish representative IID sampling, or fix the grouped-release gap.
Those remain barriers to relying on it as a production release authority.

## Open items

The full repository suite on this branch and remote CI remain unobserved.
The first Phase 20 full run found three stale test expectations about the
new `label_2` row digest; those suites passed after the tests were corrected.
The repaired Phase 20 full run is still in progress. Complete that gate, and
then execute this successor's full suite, before calling the line release-ready.
The separate business gate is still the buyer
conversations and their registered stopping rule; more local checks cannot
substitute for them.
