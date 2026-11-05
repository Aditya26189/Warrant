# Documentation

Begin with the [handbook](handbook/index.md): ordered tutorials, design and methods,
command and library reference, research findings, a claim-by-claim evidence ledger,
and maintenance instructions. The established operational and historical manuals
below remain available as specialist references.

| Your task | Read, in this order |
| --- | --- |
| First visit | [Introduction](handbook/introduction.md) → [Quickstart](handbook/quickstart.md) → [Findings](handbook/findings.md) |
| Use the command | [Workflows](handbook/workflows.md) → [CLI reference](handbook/cli-reference.md) → [Records](handbook/records-and-protocols.md) |
| Understand implementation | [Architecture](handbook/architecture.md) → [Library reference](handbook/api-reference.md) → [Testing](handbook/testing.md) |
| Investigate scientific claims | [Data origins](handbook/data-sources.md) → [Methods](handbook/methods.md) → [Individual claim ledger](handbook/claims.md) → [Qualitative register](handbook/qualitative-claims.md) |
| Read or reproduce the paper | [Preprint](../paper/README.md) → [Reproduction](handbook/reproduction.md) → [Limitations](handbook/limitations.md) |
| Review consolidated work | [Project overview](PROJECT-OVERVIEW.md) → [Branch integration](BRANCH-INTEGRATION.md) → [Current product state](PRODUCT-STATE.md) |

## Final repository review

[Layout and source ownership](handbook/repository-layout.md) → [closure findings](../reports/PHASE-56.md). The review separates integrated branches, tested release behavior and preserved local drafts.

## Grader feasibility study

[Study specification](FEASIBILITY_EXPERIMENT_SPEC.md) → [closing report](../reports/GATE4-TRANSFER.md) → [replay guide](../experiments/grader_poc/README.md). The study retained its original stopping outcome.

## Specialist and historical manuals

##  Using Warrant on your own detector

> Procedures for the `warrant` command. They quote derived thresholds, such as the
> clean negatives a budget needs, where a reader has to act on them.

| Document | Answers |
|:---|:---|
|  [INPUT.md](INPUT.md) | I have my own scores and labels. What file does Warrant want, what does it reject, when does it refuse, and what do `group` and `label_2` do? |
|  [RELEASE.md](RELEASE.md) | How do I register, evaluate once and verify a scoped release study on my own scored holdout? |
|  [EVIDENCE-HANDOFF.md](EVIDENCE-HANDOFF.md) | What do I hand a validation function, where does each piece of evidence live in the records, and what does no record carry yet? |

##  Orientation

> Hand-written. **No measured numbers** — they point at the claim table and
> `results/` instead, so a re-run cannot leave them stale.

| Document | Answers |
|:---|:---|
| [PRODUCT-STATE.md](PRODUCT-STATE.md) | Which surfaces are implemented, what supports them, what is demonstrated only, and what blocks deployment? |
|  [DIAGRAMS.md](DIAGRAMS.md) | What does the system look like? Fifteen diagrams: the three objects, the pipeline, the warrant lifecycle, controls, policy, composition, drift, verification, the journey, the repository end to end, the customer path, a chain of rechecks, release evidence and the action gate |
|  [ONBOARDING.md](ONBOARDING.md) | I have one hour. What do I read, run, and look at, in what order? |
|  [SETUP.md](SETUP.md) | How do I get this running — just the command, a laptop, a GPU notebook, an offline machine? |
|  [RUNBOOK.md](RUNBOOK.md) | What does each script and each `warrant` subcommand do, what does it read, what does it write, and when would I run it? |
|  [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | It crashed, it refused, or `warrant` printed a message. What does it mean and what do I do? |
|  [ARTIFACTS.md](ARTIFACTS.md) | What is every file in `results/` and `evalsets/`, and every record the customer command writes? |
|  [TESTING.md](TESTING.md) | What does the test suite defend, and which suite covers what? |
|  [CODE_TOUR.md](CODE_TOUR.md) | What is in each package under `controlplane/`, and which file do I open for X? |
|  [GLOSSARY.md](GLOSSARY.md) | Warrant, envelope, estimand, null band, yield vs rate, recheck, chain, seal, label-error tolerance — defined once, with the wrong reading where one invites overclaiming |
|  [FAQ.md](FAQ.md) | The questions a reviewer or a validation team actually asks, each answered with the artifact or document that settles it |
|  [JOURNEY.md](JOURNEY.md) | What did this project actually do, build phase by build phase and sprint by sprint, and what changed our mind? |

##  How it works

| Document | Answers |
|:---|:---|
|  [ARCHITECTURE.md](ARCHITECTURE.md) | What the system is, the three ways into it, and how the pieces fit, with the reason for each design choice |
|  [METHODS.md](METHODS.md) | Estimators, bootstraps, null bands, certification, recheck, the chain, label error and release: each with its derivation and what it assumes |
|  [CASES.md](CASES.md) | Every case, the test covering it, the artifact demonstrating it |

##  Contracts

> The design. **Binding on contributors**, and read before writing code.

| Document | Answers |
|:---|:---|
|  [SPEC.md](SPEC.md) | The technical specification: data model, validation harness, matrix, drift, policy, gate |
|  [../CLAUDE.md](../CLAUDE.md) | The invariants, the silent failures, the coding standards, what is out of scope |
|  [TASKS.md](TASKS.md) | The phased build order and the gate at the end of each phase |
|  [CONTRIBUTING.md](CONTRIBUTING.md) | Git workflow, commit rules, what is committed, the documentation audit |
|  [KICKOFF.md](KICKOFF.md) | The original brief |

##  Evidence and rationale

> Where the numbers and the reasoning actually live.

| Document | Answers |
|:---|:---|
|  [../DECISIONS.md](../DECISIONS.md) | Append-only entries. *"Why did you do it that way?"* — including the reversals |
|  [LIMITATIONS.md](LIMITATIONS.md) | Scope, declared gaps, open items. **Read before quoting anything** |
|  [EXTERNAL.md](EXTERNAL.md) | Does this machinery mean anything on detectors we did not build, on data we did not construct? |
|  [REDACT.md](REDACT.md) | What happens when this certification is run over somebody else's benchmark, and why a rule-based detector has no operating point to tune? |
|  [RBI-MRM-2026-CROSSWALK.md](RBI-MRM-2026-CROSSWALK.md) | Which paragraphs of the RBI's **draft** model-risk guidance can a warrant supply evidence for, which only in part, and which not at all? Generated; a register, not a compliance claim |
|  [PATHS.md](PATHS.md) | What moved on 2026-08-29 and where it went |
|  [../results/RESULTS.md](../results/RESULTS.md) | The rendered results, with fixture numbers refused rather than printed |
|  `reports/PHASE-<N>.md` | One report per sprint, leading with the answer; [PHASE-12.md](../reports/PHASE-12.md) closes sprint 12; [PHASE-15.md](../reports/PHASE-15.md) records an earlier repair checkpoint; [PHASE-16.md](../reports/PHASE-16.md) audits the product state; [PHASE-17.md](../reports/PHASE-17.md) records certificate replay; [PHASE-18.md](../reports/PHASE-18.md) records recheck evidence linkage; [PHASE-19.md](../reports/PHASE-19.md) records fresh-batch binding and ordinary replay; [PHASE-20.md](../reports/PHASE-20.md) records linear chain-prefix replay; [PHASE-21.md](../reports/PHASE-21.md) records release label auditing; [PHASE-22.md](../reports/PHASE-22.md) records grouped-boundary evidence and historical replay; [PHASE-23.md](../reports/PHASE-23.md) audits grouped hard-negative FPR warrants; [PHASE-24.md](../reports/PHASE-24.md) repairs collapsed grouped flag-rate and descriptive FPR intervals; [PHASE-25.md](../reports/PHASE-25.md) records the fresh-clone gate on the integrated line |
| [PHASE-26.md](../reports/PHASE-26.md) | Why the clean-clone verifier now rejects missing, duplicate and contradictory tier summaries, and what was tested |
| [PHASE-27.md](../reports/PHASE-27.md) | Which known release blockers are preflighted before the full clone suite, and what remains untested |
| [PHASE-28.md](../reports/PHASE-28.md) | How failed clone attempts are retained without replacing the last passing record |
| [PHASE-29.md](../reports/PHASE-29.md) | Why the current monitor uses mixture wealth while the Decision 187 schedule remains historical |
| [PHASE-30.md](../reports/PHASE-30.md) | What October export preparation built, what the full clean-clone gate verified, and which customer-evidence gates remain open |
| [PHASE-31.md](../reports/PHASE-31.md) | How routed drift-response serialization and the PowerShell Quickstart were repaired and tested |
| [PHASE-32.md](../reports/PHASE-32.md) | Why malformed prepared packages now produce input errors distinct from valid changed-package mismatches |
| [PHASE-33.md](../reports/PHASE-33.md) | How the public synthetic export reaches a certificate with two separately replayed evidence boundaries |
| [PHASE-34.md](../reports/PHASE-34.md) | Why the public handoff regression is now in the measured customer-only CI list |
| [PHASE-35.md](../reports/PHASE-35.md) | Which public handoff commands passed in a tracked-file clean clone, and why the human gate is still open |
| [PHASE-36.md](../reports/PHASE-36.md) | How preparation stopped writing intermediate plaintext files while retaining strict parsing and output bytes |
| [PHASE-37.md](../reports/PHASE-37.md) | Why the October incumbent source check narrows the evidence-handoff hypothesis before more feature work |
| [PHASE-38.md](../reports/PHASE-38.md) | How the public grouped export produces a replayable refusal and detects an altered source note |
| [PHASE-39.md](../reports/PHASE-39.md) | How the built wheel exercises the grouped refusal handoff and what Python compatibility is still unobserved |
| [PHASE-40.md](../reports/PHASE-40.md) | How preparation classifies an interrupted manifest write and preserves the incomplete destination |
| [PHASE-41.md](../reports/PHASE-41.md) | Which valid, refused and altered-source outcomes passed in a fresh tracked-file clone |
| [PHASE-42.md](../reports/PHASE-42.md) | How the blank human first-run worksheet now covers valid, refused and altered-source outcomes |
| [PHASE-43.md](../reports/PHASE-43.md) | Which integrated week-one tests passed and why the unaided human gate remains open |
| [PHASE-44.md](../reports/PHASE-44.md) | Why the current product-state page now points to the latest tested source and its limits |
| [PHASE-45.md](../reports/PHASE-45.md) | How the opt-in certify handoff was built, replayed, tested and bounded |
| [PHASE-46.md](../reports/PHASE-46.md) | Which dated pilot preconditions were repaired and which human/customer gates remain open |
| [PHASE-47.md](../reports/PHASE-47.md) | Which installed handoff commands worked in a clean clone and where their generated files landed |
| [PHASE-48.md](../reports/PHASE-48.md) | Which full-suite failures exposed evidence-preservation defects, how they were repaired, and what the final gate established |
| [PHASE-49.md](../reports/PHASE-49.md) | What official incumbent documentation says about review, labels, exports and evaluation, and which buyer comparison remains unobserved |
| [PHASE-50.md](../reports/PHASE-50.md) | What the full tracked-file clean-clone gate ran, what passed or skipped, and what Windows cleanup left behind |
| [PHASE-51.md](../reports/PHASE-51.md) | How the Windows clone cleanup failure was reproduced and repaired, and what the later full gate established |
| [PHASE-52.md](../reports/PHASE-52.md) | Why the certify handoff suite entered the minimal customer CI manifest and what the measured local matrix passed |
| [PHASE-53.md](../reports/PHASE-53.md) | Why the tracked-clone gate previously omitted its executed pass count and what the complete corrected run recorded |
| [PHASE-54.md](../reports/PHASE-54.md) | What the local Windows Python 3.10 installed-minimum run passed and why the broader 3.10 customer-list collection stopped |
| [CLAIM-AUDIT-2026-10-07.md](../reports/CLAIM-AUDIT-2026-10-07.md) | Current claim-by-claim artifact, market-overlap and venture-gap audit |
| [AI-OPPORTUNITIES-2026-10.md](../reports/AI-OPPORTUNITIES-2026-10.md) | Which current competition, founder and incumbent signals shaped the October hypothesis, and which claims remain unverified? |
| [INCUMBENT-PACKET-COMPARISON-2026-10.md](../reports/INCUMBENT-PACKET-COMPARISON-2026-10.md) | What evaluation exports and review workflows incumbents document, and what must be checked in a real packet? |
| [BUILD-PLAN-2026-10.md](../reports/BUILD-PLAN-2026-10.md) | What is the October day-by-day build and discovery schedule, with acceptance and stop gates? |
| [DISCOVERY-2026-10.md](../reports/DISCOVERY-2026-10.md) | What should a reviewer and engineer show before a real export or recurring decision is claimed? Blank worksheet; no interviews recorded |
| [PACKET-DESIGN-REVIEW-2026-10.md](../reports/PACKET-DESIGN-REVIEW-2026-10.md) | Which handoff and replay capabilities already exist, and what observed failure would justify a new package command? |
| [OFFLINE-HANDOFF-REVIEW-2026-10.md](../reports/OFFLINE-HANDOFF-REVIEW-2026-10.md) | Which files an offline reviewer needs, what the synthetic prepared package retains, and which compatibility checks remain unobserved? |
| [REPRODUCIBLE-DEMO-2026-10.md](../reports/REPRODUCIBLE-DEMO-2026-10.md) | How can a reader reproduce the synthetic valid, refusal and tamper cases? |
| [MENTOR-BRIEF-2026-10-02.md](../reports/MENTOR-BRIEF-2026-10-02.md) | Shareable account of the research hypothesis, October progress, verification limits and month plan |
| [STRATEGY-2026-09.md](../reports/STRATEGY-2026-09.md) | The commercial stopping rule and dated primary-source regulatory corrections |
|  [NEXT-STEPS-2026-09-17.md](../reports/NEXT-STEPS-2026-09-17.md) | What to do next, after sprint 12: the decisions only the founder can make, then the engineering, in order |

##  Presentation and the business case

| Document | Answers |
|:---|:---|
|  [DEMO.md](DEMO.md) | The two-pane demo this build exists to produce |
|  [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | The beat-by-beat script and what is on screen |
|  [PROPOSAL.md](PROPOSAL.md) | The business proposal |
|  [PILOT-PROTOCOL.md](PILOT-PROTOCOL.md) | What a first pilot would test, for which buyer and which recurring decision, and what would end it. A plan; no pilot has run |
|  [EXTERNAL_FIGURES.md](EXTERNAL_FIGURES.md) | The register that gates every figure about the world, and its provenance tiers |

---

## Documentation maintenance

New handbook chapters belong in the navigation in [mkdocs.yml](../mkdocs.yml).
The link checker validates local files and Markdown fragments; strict site builds
and preprint checks run in the documentation workflow. Quantitative README rows
are checked against retained artifacts. This validates consistency, not scientific
truth. See [developer guide](handbook/developer-guide.md) for generation commands
and [claim audit](handbook/claim-audit.md) for the limits of each check.
