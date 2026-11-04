# Warrant: project overview

Warrant investigates a practical gap between a detector score and the evidence
needed to rely on it. The working software consumes scored, labelled files,
evaluates a declared operating budget, retains the result, and lets another
reviewer replay the calculation.

This repository combines a usable local toolkit with a research record. The
value is in the executable methods, failure controls, retained counterexamples,
and reproducible conclusions. Commercial adoption and production deployment
have not been demonstrated.

## Follow one complete workflow

1. Read the [input contract](INPUT.md) and run both [examples](../examples/README.md).
2. Inspect the result: its operating point, uncertainty, assumptions, and refusal reasons.
3. Replay it with the retained input rather than trusting the report text.
4. Use [release registration](RELEASE.md) for a separately scoped holdout decision.
5. Consult [limitations](LIMITATIONS.md) before transferring a result to a new setting.

The command is local and works without model inference. The GPU extraction
pipeline supports the activation research and is a separate environment.

## What was built

| Layer | Engineering work | Review it |
|---|---|---|
| Input and contracts | Explicit score direction, label meaning, grouping, immutable registration, versioned record schemas | [Intake](../controlplane/intake/), [release](../controlplane/release/), [input guide](INPUT.md) |
| Statistical evaluation | False-positive budgets, operating-point selection, uncertainty, grouped-data restrictions, label sensitivity | [Validation](../controlplane/validation/), [methods](METHODS.md) |
| Evidence lifecycle | Source-row binding, replay, linked rechecks, integrity checks, interruption handling | [Evidence handoff](EVIDENCE-HANDOFF.md), [intake code](../controlplane/intake/) |
| Research pipeline | Activation extraction, frozen evaluation sets, probe training, controls, transfer analysis | [Architecture](ARCHITECTURE.md), [results](../results/RESULTS.md) |
| Verification | Claim-to-artifact resolution, frozen-score replay, installed-package checks, clean-clone gates | [Testing](TESTING.md), [verification scripts](../scripts/verify.py) |

Checksums detect changes relative to retained bytes. They are not signatures,
trusted timestamps, or evidence that supplied labels are correct.

## Navigate the research

| Workstream | Status | Read first |
|---|---|---|
| Activation probes and distribution transfer | Measured within declared envelopes; transfer limits retained | [Claim table](../README.md#-the-claim-table) → [limitations](LIMITATIONS.md) |
| Statistical assurance diagnostics | Exact and empirical diagnostics with explicit assumptions | [Methods](METHODS.md) → [exact witness](research/publication/EXACT_WITNESS.md) |
| FPR reporting pilot | Sampling frame remains blocked; no completed population survey | [Current status](research/fpr_reporting/b1/B1_CURRENT_STATUS.md) |
| Grader auditing | Known repair examples retained; later bounded discovery study closed | [Experiment guide](../experiments/grader_poc/README.md) → [closing report](../reports/GATE4-TRANSFER.md) |
| Unscored-trial accounting | Completed technical report and portable numerical reproduction; independent human review pending | [Technical report](../results/unscored_trials/closeout-20261029/report/technical_report.md) → [reproduction](research/unscored_trials/REPRODUCING.md) |
| Stopping-feedback expense study | Stopped at data feasibility for its predeclared question | [Decision](../agent-stopping-feedback-study/DECISION.md) → [claim ledger](../agent-stopping-feedback-study/CLAIM_EVIDENCE.md) |
| Publication-direction notes | Exploratory proposals and historical planning; not papers or acceptance claims | [Research prospectus](research/publication/PAPER_PROSPECTUS.md) |

The unscored-trials report does not establish corrected official rankings or
recover the original planned-trial roster. The stopping-feedback study did not
fit or evaluate a stopping policy. Closed studies are preserved so that their
decisions, failed attempts, and limits remain reviewable.

## Review the project according to your interests

**Applied ML:** follow a scored file into a decision, examine the assumptions,
and replay the result. Start with [INPUT](INPUT.md) and [RELEASE](RELEASE.md).

**Research:** inspect the frozen protocol, measurement boundary, controls,
counterexamples, and conclusions. Start with [METHODS](METHODS.md), the
[claim table](../README.md#-the-claim-table), and the workstream above.

**Software engineering:** inspect package boundaries, minimal customer
dependencies, immutable publication, installed workflows, and the negative
tests. Start with [CODE_TOUR](CODE_TOUR.md) and [TESTING](TESTING.md).

## Reproduce and interpret the checks

`make smoke` checks basic repository health. `make test` executes the core
suite. `make verify` checks artifact-backed claims and recomputes frozen-score
metrics; activation replay is skipped when the untracked caches are absent.

[Reproduction instructions](SETUP.md) name the environments. The optional
research suites are described in [experiments/README](../experiments/README.md)
and have a separate [CI workflow](../.github/workflows/research.yml).

An inventory is a collection count, not a passing execution. A retained gate
record covers its named source commit, not every later revision. Consult the
[final consolidation report](../reports/PHASE-FINAL-RELEASE-20261105.md) for this
release's checks and [branch audit](BRANCH-INTEGRATION.md) for its history.

## Scope

The release is an installable local evaluation toolkit and reproducible
research repository. Authentication, multi-tenant serving, production traffic,
independent label adjudication, and customer outcomes are separate gaps,
described in [PRODUCT-STATE](PRODUCT-STATE.md) and [LIMITATIONS](LIMITATIONS.md).
