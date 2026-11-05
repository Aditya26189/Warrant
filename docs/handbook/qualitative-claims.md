# Qualitative claim investigation

This register audits capability and interpretation statements in the current
entry pages and prior consolidation summary. It complements the numerical
[ledger](claims.md). SOURCE-REVIEWED means the cited implementation or
declaration was inspected; it is not a formal proof or independent deployment
validation. Operational receipts describe their named revision.

## N01: the installed tool consumes an existing scored file

**Evidence:** [CLI](../../controlplane/cli.py) and
[input contract](../../controlplane/intake/contract.py).

The parser and reader implement the declared CSV/JSONL path. The caller supplies
scores and labels; the ordinary certification workflow does not train or invoke
a language model to obtain them. This is why the introduction describes a local
evaluation toolkit rather than a new neural model.

**Boundary:** arbitrary Python workflows, raw agent traces and unscored
documents are not automatically understood by this contract.

## N02: the customer dependency set is small

**Evidence:** [package declaration](../../pyproject.toml),
[customer requirements](../../requirements-customer.txt) and
[customer CI jobs](../../.github/workflows/ci.yml).

The direct numerical requirements are NumPy, SciPy and PyYAML. CI deliberately
separates this path from model extraction and checks that forbidden heavy
packages do not enter the customer import path.

**Boundary:** this does not describe the full research or documentation
environment, nor prove that every possible future plugin is offline.

## N03: ordinary certification is local

**Evidence:** [certification](../../controlplane/intake/certify.py) and
[CLI dispatch](../../controlplane/cli.py).

The shipped scored-file certification path calculates from local supplied
records. This supports describing that path as requiring no paid model calls.

**Boundary:** installation, model extraction and optional research acquisition
can use the network. A blanket statement that every repository command is
offline would be false.

## N04: refusal is a normal outcome

**Evidence:** [CLI](../../controlplane/cli.py) and
[example acceptance test](../../tests/test_acceptance.py).

The tool distinguishes insufficient evidence from malformed input. Default
refusal behavior can exit zero; explicit requirement flags support pipelines
that need a stricter process exit.

**Boundary:** no-exception execution is not the same as a supported scientific
claim. A caller must inspect the result or choose the proper requirement flag.

## N05: replay binds more than aggregate counts

**Evidence:** [effective evidence](../../controlplane/intake/certify.py) and
[verification](../../controlplane/intake/verify.py).

Material row binding allows changed scores to matter even when aggregate
predictions are unchanged. This is why retained inputs are part of the evidence
handoff rather than a dispensable convenience.

**Boundary:** a consistent replacement of every copy is not authenticated by
checksums. Replay does not identify the original author.

## N06: preparation makes source mapping reviewable

**Evidence:** [preparation](../../controlplane/intake/prepare.py) and
[input guide](../../docs/INPUT.md).

The declared mapping, effective scored file and manifest can be replayed.
The system need not guess label semantics from arbitrary export column names.

**Boundary:** a perfectly replayed mapping can still encode the wrong
scientific label or score direction.

## N07: a frontier selection needs retained selection evidence

**Evidence:** [frontier](../../controlplane/intake/frontier.py) and
[selection](../../controlplane/intake/selection.py).

The selected-frontier path binds the later budget choice to its declared grid
and adjustment. This supports documenting a distinct workflow for inspecting
then choosing a budget.

**Boundary:** it is not arbitrary adaptive-search protection over every
detector, dataset or user-designed grid.

## N08: second labels expose sensitivity, not truth

**Evidence:** [label diagnostics](../../controlplane/intake/labels.py),
[agreement](../../controlplane/sampling/agreement.py) and
[input semantics](../../docs/INPUT.md).

The primary label drives native certification. Double-review information is
retained as disagreement, descriptive agreement and sensitivity under stated
assumptions.

**Boundary:** agreement is not correctness. Grouped agreement restrictions and
review-selection assumptions remain important.

## N09: release evaluation is a fixed-threshold study

**Evidence:** [contract](../../controlplane/release/contract.py) and
[evaluation](../../controlplane/release/evaluate.py).

Registration freezes the identity, threshold, criteria and holdout membership.
The implementation constructs its simultaneous rate intervals and reports
whether the fixed FPR/recall criteria clear.

**Boundary:** it cannot authenticate the actual scorer or prevent undisclosed
studies elsewhere. Grouped release input remains unsupported.

## N10: chains and local publication are separate from statistical validity

**Evidence:** [chain publication](../../controlplane/intake/chain_publication.py),
[chain verification](../../controlplane/intake/chain_verify.py) and
[chain implementation](../../controlplane/intake/chain.py).

The code coordinates local continuation and checks links, retained batches
and publication state. A statistical sequence also depends on its declared
horizon and label units.

**Boundary:** verifying a presented prefix does not establish the global
current head or absence of another fork.

## N11: handoffs are portable evidence packages

**Evidence:** [handoff implementation](../../controlplane/intake/handoff.py)
and [handoff guide](../../docs/EVIDENCE-HANDOFF.md).

The supported prepare/certify path can be copied and replayed with a fixed
member inventory. A refused result remains a refused result.

**Boundary:** source exports can retain excluded sensitive columns. This is
not a privacy filter, authenticated attestation or arbitrary workflow packager.

## N12: hashes are integrity checks, not authentication

**Evidence:** [serialization](../../controlplane/model/serde.py),
[record verification](../../controlplane/intake/verify.py) and
[release contract](../../controlplane/release/contract.py).

Hashes let a reviewer compare supplied content with retained bytes. No signing
authority, trusted clock or external identity proof is supplied by those
operations.

**Boundary:** tamper evidence is relative to retained reference material.
Replacing every reference can defeat that trust model.

## N13: a probe is a correlational classifier

**Evidence:** [probe fitting](../../controlplane/detectors/probe.py),
[aggregation](../../controlplane/detectors/aggregation.py) and
[measured validation](../../results/validation-T1-last_token.json).

The fitted linear classifier predicts the recorded label from prompt features.
The final-token feature precedes generation. This supports a narrower
description than reading beliefs or testing truth directly.

**Boundary:** the experiment does not identify the mechanism behind the signal
or establish general factual-error detection.

## N14: transfer reuses original outcomes

**Evidence:** [transfer entry point](../../scripts/04_transfer.py),
[extraction pipeline](../../controlplane/extract/pipeline.py) and
[transfer evidence](../../results/transfer-T1-last_token.json).

The constructed context changes the features while retaining original
questions and outcome labels. This makes the comparison useful for a
representation-shift question.

**Boundary:** it is not a fresh long-context generation-accuracy experiment.

## N15: the matrix includes more than measured natural-data results

**Evidence:** [matrix artifact](../../results/warrant_matrix.json) and
[matrix renderer](../../controlplane/report/results.py).

Synthetic envelope IDs and fixture-backed cells are retained alongside
measured artifacts. The summary is an exact inventory of its represented
states.

**Boundary:** a VALID-cell count is not a count of independently deployed or
externally validated models.

## N16: score-free voting results are conditional simulations

**Evidence:** [simulation](../../scripts/26_scorefree.py) and
[retained scope](../../results/scorefree/scorefree.json).

The specified latent-probability model uses independent votes conditional on
each item. That supports the reported granularity and operating-point
calculations.

**Boundary:** historical “upper bound” language must be read as an optimistic
scenario under that model, not a universal bound on real judges. Neither
correlation nor the latent score distribution was measured for a commercial
system.

## N17: the action gate can act independently of a detector in some rules

**Evidence:** [gate](../../controlplane/gate/gate.py) and
[enumerated demonstration](../../results/gate/gate.json).

The selected reversibility/session rules use other state, and the retained
finite sweep compares their decisions with detector information removed.

**Boundary:** this is not an exhaustive security proof or a production
false-block-rate measurement.

## N18: label plans are conditional arithmetic and simulation

**Evidence:** [planning](../../controlplane/sampling/planning.py),
[estimation](../../controlplane/sampling/estimator.py) and
[on-traffic artifact](../../results/on_traffic/on_traffic.json).

The source distinguishes flagged-pool census counts from sampled missed
positives and propagates recall uncertainty. Workload parameters are declared.

**Boundary:** field names containing “measured” do not turn declared scenario
rates into new production observations. No customer savings were measured.

## N19: the returned-bound issue remains open

**Evidence:** [native audit](../../docs/research/fpr_reporting/CERTIFY_AUDIT.md),
[tracked issue](../../docs/research/fpr_reporting/issues/FPR-001-adaptive-bound.md)
and [exact witness](../../results/publication/assurance_semantics.json).

The retained finite calculation distinguishes the fixed requested budget from
the adaptive returned number. The latter's general coverage interpretation
fails in the witness.

**Boundary:** this does not prove a budget violation in that witness or
independent review of the complete implementation.

## N20: metric replay does not reissue a warrant

**Evidence:** [score reproduction](../../controlplane/report/reproduce.py).

The score tier explicitly compares metric blocks. It does not reconstruct the
controls needed to issue the original warrant. This is why a metric replay
cannot be described as a fresh issuance validation.

**Boundary:** a clean clone can pass arithmetic checks while an interpretation,
source lineage or label assumption remains unresolved.

## N21: the unscored-trial work closed as REPORT

**Evidence:** [decision](../../docs/research/unscored_trials/PUBLICATION_DECISION.md),
[technical report](../../results/unscored_trials/closeout-20261029/report/technical_report.md)
and [closest-work assessment](../../docs/research/unscored_trials/RELATED_WORK.md).

The report retains pinned accounting and reconciliation findings, their
cohort restrictions and the originality objection.

**Boundary:** no corrected official rankings, original execution roster,
submission acceptance or independent human source adjudication is established.

## N22: stopping-feedback closed at feasibility

**Evidence:** [decision](../../agent-stopping-feedback-study/DECISION.md)
and [claim boundary](../../agent-stopping-feedback-study/CLAIM_EVIDENCE.md).

The inspected inputs did not establish the predeclared expense mechanism.
The project did not fit or evaluate the proposed policy.

**Boundary:** STOP is not an empirical zero effect and does not prove that
every alternative source or proxy question is inadequate.

## N23: grader examples do not establish general discovery yield

**Evidence:** [earlier guide](../../experiments/grader_poc/README.md)
and [closing transfer](../../reports/GATE4-TRANSFER.md).

Controlled omissions/repairs and a later bounded no-new-omission result are
both retained. The latter used fixed tasks and a conventional mutation method.

**Boundary:** neither finding estimates a general omission prevalence,
universal grader completeness, human setup cost or product demand.

## N24: the prior consolidation was verified on its exact revision

**Evidence:** [phase report](../../reports/PHASE-FINAL-RELEASE-20261105.md),
[Core CI](https://github.com/Aditya26189/Warrant/actions/runs/41936407178),
[Research CI](https://github.com/Aditya26189/Warrant/actions/runs/41936407179)
and tag `phase-final-release-20261105` at `9dbdee0`.

The retained run checked the prior release's core, customer, Windows package
and research paths. Branch ancestry and local-file preservation were separate
operational checks.

**Boundary:** those pass counts do not automatically describe a later revision.
The activation tier was skipped, and green CI did not close FPR-001, dirty
historical provenance or scientific-review gaps.

## Scope of this register

These entries explain why the current capability descriptions were written
and where their evidence lives. They do not automatically validate every
historical legal, commercial or publication-planning statement. Such documents
retain their dates and original evidence grades; no compliance approval or
publication success is inferred from their presence.
