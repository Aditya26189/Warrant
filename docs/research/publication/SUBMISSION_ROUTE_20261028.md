# A concrete route to a submittable paper

28 October 2026. Research assessment and proposed study, not a completed paper,
an acceptance prediction or an amendment to the existing reporting pilot.

## Recommendation after the deeper search

Test a **controlled reproducibility extension** before committing to a full
reporting survey. Candidate title:

**From Benchmark Recall to Certifiable Operating Points in Prompt-Injection
Detection**.

Question: after fixing the scorer, how do finite benign calibration evidence,
the promised assurance level, and the decision unit affect the recall that a
researcher can support at a declared false-positive budget?

This route can produce an interpretable comparison even if Warrant never wins
and no other author made an error. It uses published scores as potential inputs,
not a new detector or a new statistical theorem. The reporting-audit route
remains a separate candidate; its unfinished B1 frame cannot supply empirical
results for this paper. This recommendation supersedes treating completion of
the broad literature audit as the only possible next step.

The route is worth a bounded feasibility check, not an open-ended commitment.
Generic calibration comparisons are already well covered. A completed study
must add a useful mechanism or decision-relevant result beyond known sample
floors, ordinary conservatism and the fact that distribution shift hurts.

## Why this fits the venue

TMLR explicitly permits reproducibility work that systematically probes a
method and provides useful generalizable lessons. Its criteria do not require
an invented algorithm. Its editorial policy also rejects unsupported claims
and mere reimplementation of an already reproduced idea.
[Acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html),
[editorial policy](https://jmlr.org/tmlr/editorial-policies.html).

For us, the missing ingredient is an empirical contribution, not formatting.
The existing exact Warrant witness can motivate a section about assurance
semantics. Reproducing our own bug cannot carry the submission alone.

## Closest prior work: what the extension cannot claim

This is a bounded primary-source search on 28 October, not a systematic
novelty proof. Read depths are stated to avoid implying complete paper audits.

| Primary source / inspection | Already established or performed | Remaining distinction to test |
|---|---|---|
| Liu, [*Passing the Test You Trained On*](https://arxiv.org/html/2610.03448v1), §§4–6 selected text; current [source checkout](https://github.com/lzwhehe/benign-instruction-bench/tree/5d0ae7c438a7b01be2ac0a2e8bc943e45c8f851f) and `analysis/compute_robust.py` inspected | Low-FPR detector comparisons across agent benchmarks. The preprint discloses retrospective thresholds; the newer code already includes held-out-suite thresholds and task-cluster bootstrap uncertainty | High-probability FPR operating points under explicit calibration budgets and independence units. Merely adding a held-out split or cluster bootstrap is redundant |
| Bista et al., [*ConformalGuard*](https://arxiv.org/html/2610.14365v1), methods/limitations and sensitivity headings selected | Marginal legitimate-event control, coarse scores and calibration sensitivity for LM email classifiers | A different assurance contract on input-injection benchmarks. Do not present conformal marginal validity as a failed PAC guarantee |
| Priye et al., [*Available Guardrails*](https://arxiv.org/pdf/2609.22048v1), abstract, §§2–3 and reproducibility statement selected | Finite-data certificate availability, selective risk, reporting granularity and multiplicity; explicitly builds on LTT | Benign-class FPR and recall at frozen detector operating points are a different estimand. That difference alone does not establish a sufficient contribution |
| [*Calibration and Risk-Budgeted Decisions with System One Models*](https://arxiv.org/html/2610.19811v1), §§3.1,5.2–5.4 and discussion selected | Applies LTT to False Omission Rate, including prompt injection, with empirical/naive alternatives and non-deployment outcomes | An FPR rather than FOR constraint, and the effect of task/context units and finite calibration on existing detector comparisons. Simply applying LTT to another classifier is weak |
| Shire and Kim, [*PIDS-Bench*](https://arxiv.org/html/2609.15017v1), official abstract and selected text | Hard-benign over-defense, fixed thresholds, provenance and shift evaluation | Controlled assurance/calibration consequences, rather than another hard-negative dataset or threshold sweep |
| Chaudhari, [*Regime-Adaptive Conformal Guardrails*](https://www.preprints.org/manuscript/202609.2642), Propositions 1–2 and limitations selected; explicitly a preprint | Negative-class marginal conformal control, finite-bank abstention and stateful refresh under specified assumptions | A static, fixed-scorer calibration study; no new monitoring algorithm or claim that this source promises per-batch FPR control |
| Tong et al., [NP classification](https://stat.arizona.edu/sites/default/files/2023-09/Journal%20Paper%20091823.pdf), prior audit's selected Proposition 1/proof; Angelopoulos et al., [LTT](https://arxiv.org/abs/2110.01052), official abstract/bibliographic source in this continuation | High-probability type-I control and valid policy selection already exist | Attribute the machinery; contribute an empirical finding and a faithful, useful comparison |

The new sources do not establish that our exact question is globally unoccupied.
They sharply limit the safe novelty claim. The paper should be positioned as
a reproducibility/evaluation study with added analysis, not a new certifier.

## What is actually available

I downloaded the public MIT-licensed score/code repository and inspected it
without running its scripts. The checkout is pinned to
`5d0ae7c438a7b01be2ac0a2e8bc943e45c8f851f`.
Our [metadata inventory](../../../results/publication/source_inventory.json)
was generated by a committed program from clean inputs; it records hashes of
the score files and the principal inspected scripts/license.

The inventory finds 113 files, 18 declared scorer identities and seven set IDs.
These identities include aliases/variants, not 18 independent model families.
All within-set vector lengths and label sequences agree. The inspected score
schema supplies no configured per-record identity or task fields. No detector
performance, thresholds, score quantiles or rankings were calculated here.

The primary candidate data are AgentDojo and tau-bench tool outputs and BIPIA
contexts. Existing scores may avoid new model inference. That is a feasibility
opportunity, not a demonstrated end-to-end CPU reproduction: upstream scripts
rebuild data from external packages/repositories whose exact correspondence
must be established. The original full runner includes GPU/model stages and
must not be launched wholesale.

**First technical gate: recover and validate the unit mapping.** Reconstruct
task/context IDs, common base texts and attack variants from pinned source
inputs; retain their hashes and index mapping to score arrays. Matching lengths
and labels is necessary but cannot authenticate text/order identity. General
text chunks also need their parent-document identity; a sequential row number
does not make chunks independent. If correspondence cannot be established,
limit claims to a conditional analysis of the released arrays, obtain better
source evidence, or stop the group-aware extension. Do not fabricate group IDs.

The [upstream robustness script](https://github.com/lzwhehe/benign-instruction-bench/blob/5d0ae7c438a7b01be2ac0a2e8bc943e45c8f851f/analysis/compute_robust.py)
already checks label/length agreement, rebuilds task assignments and reports
clean/matched text overlap. Those checks are useful starting points, not proof
that every new split is independent. Do not equate repeated clean outputs from
different attack variants with additional calibration evidence.

## Smallest defensible experimental study

Freeze a standalone design before performance reanalysis. This is a proposed
design, with exact budgets, sample grids, seeds and analysis multiplicity to
be resolved from the unit inventory, not selected after seeing favorable results.
Published score outcomes are already exposed: a prespecified reanalysis is
still a follow-up to published evidence, not fresh confirmatory data.

**Hold the scorer fixed.** Include a declared set of available, comparable
scorers and retain exclusions/aliases. Do not fine-tune, add paid API judges,
or select models from the new evaluation outcomes. Higher-score orientation,
truncation, model revision and comparator conventions must be source-verified.

**Compare procedures with their actual contracts visible:**

| Procedure | Role |
|---|---|
| Original retrospective low-FPR ROC point | Reproduce the published descriptive benchmark; an optimistic reference, never a deployable certificate |
| Empirical quantile on separate benign calibration | Source-faithful held-out baseline, including the upstream revision's implementation |
| Standard negative-class conformal rank | Marginal next-benign-event control under its assumptions; no expectation that it satisfies an unclaimed PAC contract |
| Standard fixed-rank NP calibration | High-probability same-source FPR control; report the design guarantee, never an unjustified CP bound based on a smaller tied realized count |
| Development-selected threshold plus independent exact-binomial check, or source-faithful LTT | A valid alternative under the same high-probability risk contract; do not compare only against intentionally invalid methods |

The last choice should be settled by conformance and data allocation before
outcomes; use the established LTT machinery if the study includes selection
among several candidate policies. Implementing a novel method is unnecessary.

**Separate units and risk targets.** A per-output benign FPR and the chance
that a benign task has any flagged output are different quantities. Task-max
calibration can target the latter under IID tasks. It does not automatically
certify traffic-weighted per-output risk for unequal-length tasks. Make
comparisons within each common risk contract, and explain separately what
changes when the operational target changes. Task-bootstrap intervals alone
do not establish a task-level PAC guarantee.

**Split by underlying task/context, then deduplicate shared text.** Development,
calibration and evaluation must not share a base context through attack variants.
Keep same-source experiments separate from cross-suite/domain stress tests;
the latter do not inherit same-source guarantees. Freeze every scoring of the
evaluation set and disclose it; do not select a method, budget or threshold on it.

**Measure utility and uncertainty, not only nominal validity.** Report recall,
precision and benign FPR separately, their actual denominators, vacuous/no-fire
outputs, and how useful recall changes with calibration evidence. Compare
valid procedures under matched contracts and data budgets. For model choice,
handle the declared family or use separate selection evidence; a per-model
guarantee does not automatically cover a chosen winner.

Empirical held-out FPR exceeding a target is not itself proof that a population
guarantee failed. A repeated-calibration diagnostic can use a declared finite
empirical population with known risk, but must be labeled as such. Resampling
does not create new independent real-world tasks or validate deployment risk.

## Added value required before writing the full paper

The study needs to explain a practical conclusion. Plausible, unmeasured
outcomes include stable detector choices despite assurance overhead; a
well-supported change in choices caused by finite calibration; or a clear
separation between score-discreteness and independent-unit scarcity as the
source of utility loss. Retain whichever outcome occurs.

A useful result must extend the closest source studies, have interpretable
uncertainty, and tell readers how to make or assess an operating-point choice.
It cannot consist solely of the known clean-sample floor, an uninformative
winner table, or the familiar observation that valid methods are conservative.
Stop or narrow the project if a bounded feasibility run yields only those.

## Work order that protects time

1. Resolve the source identity/group mapping and count usable independent
   units; check whether the intended budgets leave nonvacuous comparisons.
   This comes before a large parameter grid or new detector inference.
2. Check baseline conformance on deterministic tiny distributions, ties and
   boundary cases; freeze the risk contracts and data allocation. Use the
   existing exact witness as a labeled negative control, not a new finding.
3. Run a capped CPU feasibility analysis of the prespecified question. Set
   the runtime and human-effort caps before execution, preserve failures,
   and decide whether the findings add enough to the close papers.
4. If useful, complete the frozen comparison and a manuscript whose results
   and takeaways match it. Do not extend the grid until a ranking changes.

These are scientific prerequisites, not additional universal TMLR rules. No
new approval flow is introduced for routine implementation. Existing B1/B2
human-extraction and complete-frame gates remain confined to that separate study.

## Submission-ready package

| Required component for this proposed paper | Present state / work remaining |
|---|---|
| Precise contribution and closest-work comparison | This report provides the candidate boundary; empirical added value remains untested |
| Evidence and sampling contract | Released arrays and hashes exist; validated record/group mapping is unresolved |
| Source-faithful strong baselines | Upstream empirical baseline inspected; conformance and valid comparators remain to implement |
| Complete results with uncertainty and limitations | Not run; no new detector performance can be claimed |
| Statistical explanation authors can defend | Standard theory identified; final code-to-assumption mapping needs substantive human ownership/review |
| Reproducible artifact | Existing diagnostic and metadata generator work; full study runner and clean replay remain |
| Anonymous manuscript and supplement | Prepare after results using the [official author guidance](https://jmlr.org/tmlr/author-guide.html); the named public repository is not an anonymous artifact |

Submission eligibility is not acceptance. Human authors must understand and
own the work; a polished AI-written draft cannot supply the missing evidence.
The earlier broad reporting audit can remain an independently justified study,
but combining its incomplete frame with this proposal would not strengthen either.

## Verification and scope

Metadata-only execution completed on clean research source `1eb7617` and the
pinned clean public checkout. The inventory's payload/schema assertions and
focused Ruff passed. The source experiment scripts were inspected, not executed;
no dependencies or model weights were installed. Ordinary `git fetch origin`
confirmed no newer remote main/research tip than the prior assessment.

The original probe test set, B1 evidence/adjudications, production runtime,
historical certificates and frozen scores were not modified or regenerated.
No paper was sampled, no B2 outcomes accessed and no main performance study run.
Source readings here expose additional prior-art outcomes; they are kept outside
the frozen B1 frame and do not silently alter its eligibility or sentinels.
