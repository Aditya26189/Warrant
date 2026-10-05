<div align="center">

# 📚 Documentation

**Every document in this repository, and which question it answers.**

[![Using it](https://img.shields.io/badge/Using_it-3_guides-2da44e?style=flat-square)](#%EF%B8%8F-using-warrant-on-your-own-detector)
[![Orientation](https://img.shields.io/badge/Orientation-12_pages-6366f1?style=flat-square)](#-orientation)
[![Contracts](https://img.shields.io/badge/Contracts-5_binding-d1242f?style=flat-square)](#-contracts)
[![Evidence](https://img.shields.io/badge/Evidence-append_only-22c55e?style=flat-square)](#-evidence-and-rationale)
[![No stale numbers](https://img.shields.io/badge/Orientation_pages-no_measured_numbers-8b949e?style=flat-square)](#the-rules-these-documents-follow)

</div>

> [!TIP]
> **In a hurry?** Pick the row below that matches why you are here. Every path is
> ordered — the documents build on each other in the sequence given.

---

## 🧭 Start with why you are here

| You are… | Read, in this order |
|:---|:---|
| **Assessing what has actually shipped** | [PRODUCT-STATE.md](PRODUCT-STATE.md) -> [LIMITATIONS.md](LIMITATIONS.md) -> [TESTING.md](TESTING.md) |
| 🛡️ **Running it on your own detector** | [SETUP.md](SETUP.md) §0 → [INPUT.md](INPUT.md) → [../examples/README.md](../examples/README.md) → [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → [FAQ.md](FAQ.md) |
| 📋 **Preparing evidence for a validation function** | [RELEASE.md](RELEASE.md) → [EVIDENCE-HANDOFF.md](EVIDENCE-HANDOFF.md) → [LIMITATIONS.md](LIMITATIONS.md) §3.5–3.7 |
| 🏦 **Assessing it for a regulated buyer** | [RBI-MRM-2026-CROSSWALK.md](RBI-MRM-2026-CROSSWALK.md) → [PILOT-PROTOCOL.md](PILOT-PROTOCOL.md) → [LIMITATIONS.md](LIMITATIONS.md) |
| ⏱️ **Reviewing this in twenty minutes** | [../README.md](../README.md) claim table → [DIAGRAMS.md](DIAGRAMS.md) → [LIMITATIONS.md](LIMITATIONS.md) → [FAQ.md](FAQ.md) |
| 🌱 **New to the codebase** | [ONBOARDING.md](ONBOARDING.md) → [ARCHITECTURE.md](ARCHITECTURE.md) → [DIAGRAMS.md](DIAGRAMS.md) → [CODE_TOUR.md](CODE_TOUR.md) |
| ▶️ **Reproducing the measurements** | [SETUP.md](SETUP.md) → [RUNBOOK.md](RUNBOOK.md) → [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| 🔍 **Checking whether a number is real** | [../README.md](../README.md) claim table → [ARTIFACTS.md](ARTIFACTS.md) → [METHODS.md](METHODS.md) → `make verify` |
| [Independent review, 23 September](../reports/PROJECT-REVIEW-2026-09-23.md) | Which current-main defects were independently reproduced, what passed, and what does the evidence support commercially? |
| [Claude repair instructions, 23 September](../reports/CLAUDE-INSTRUCTIONS-2026-09-23.md) | What should Claude repair next, how should agents coordinate, and which checks close each finding? |
| [Research-backed improvement plan, 23 September](../reports/IMPROVEMENT-PLAN-2026-09-23.md) | Which repairs, buyer tests and product improvements should come next, and what evidence would justify expansion? |
| [Installed workflow repair, 24 September](../reports/PACKAGING-REPAIR-2026-09-24.md) | What packaging and installed-provenance defects were repaired, which checks passed, and which review findings remain open? |
| [Chain integrity policy, Phase 15](../reports/PHASE-15.md) | What assurance is possible when seals are absent, what compatibility changed, and which checks passed? |
| [Local chain publication, Phase 14](../reports/PHASE-14.md) | How are concurrent writers and interrupted chain writes handled, and what was verified? |
| [Handoff continuation, Phase 13](../reports/PHASE-13.md) | Which grouped-review and revocation repairs followed the handoff, what was verified locally, and what remains open? |
| 🕵️ **Looking for the flaw** | [LIMITATIONS.md](LIMITATIONS.md) → [../DECISIONS.md](../DECISIONS.md) → [CASES.md](CASES.md) → [TESTING.md](TESTING.md) → `reports/` |
| 🎤 **Presenting it** | [DIAGRAMS.md](DIAGRAMS.md) → [JOURNEY.md](JOURNEY.md) → [DEMO.md](DEMO.md) → [DEMO_SCRIPT.md](DEMO_SCRIPT.md) |
| 🔬 **Asking whether this means anything outside the repo** | [EXTERNAL.md](EXTERNAL.md) → [REDACT.md](REDACT.md) → [../results/external/MATRIX.md](../results/external/MATRIX.md) |
| 💬 **Confused by a word** | [GLOSSARY.md](GLOSSARY.md) |

---

## 🛡️ Using Warrant on your own detector

> Procedures for the `warrant` command. They quote derived thresholds, such as the
> clean negatives a budget needs, where a reader has to act on them.

| Document | Answers |
|:---|:---|
| 📥 [INPUT.md](INPUT.md) | I have my own scores and labels. What file does Warrant want, what does it reject, when does it refuse, and what do `group` and `label_2` do? |
| 📋 [RELEASE.md](RELEASE.md) | How do I register, evaluate once and verify a scoped release study on my own scored holdout? |
| 🤝 [EVIDENCE-HANDOFF.md](EVIDENCE-HANDOFF.md) | What do I hand a validation function, where does each piece of evidence live in the records, and what does no record carry yet? |

## 🧩 Orientation

> Hand-written. **No measured numbers** — they point at the claim table and
> `results/` instead, so a re-run cannot leave them stale.

| Document | Answers |
|:---|:---|
| [PRODUCT-STATE.md](PRODUCT-STATE.md) | Which surfaces are implemented, what supports them, what is demonstrated only, and what blocks deployment? |
| 🗺️ [DIAGRAMS.md](DIAGRAMS.md) | What does the system look like? Fifteen diagrams: the three objects, the pipeline, the warrant lifecycle, controls, policy, composition, drift, verification, the journey, the repository end to end, the customer path, a chain of rechecks, release evidence and the action gate |
| 🌱 [ONBOARDING.md](ONBOARDING.md) | I have one hour. What do I read, run, and look at, in what order? |
| ⚙️ [SETUP.md](SETUP.md) | How do I get this running — just the command, a laptop, a GPU notebook, an offline machine? |
| 📓 [RUNBOOK.md](RUNBOOK.md) | What does each script and each `warrant` subcommand do, what does it read, what does it write, and when would I run it? |
| 🚑 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | It crashed, it refused, or `warrant` printed a message. What does it mean and what do I do? |
| 📦 [ARTIFACTS.md](ARTIFACTS.md) | What is every file in `results/` and `evalsets/`, and every record the customer command writes? |
| 🧪 [TESTING.md](TESTING.md) | What does the test suite defend, and which suite covers what? |
| 🧭 [CODE_TOUR.md](CODE_TOUR.md) | What is in each package under `controlplane/`, and which file do I open for X? |
| 📖 [GLOSSARY.md](GLOSSARY.md) | Warrant, envelope, estimand, null band, yield vs rate, recheck, chain, seal, label-error tolerance — defined once, with the wrong reading where one invites overclaiming |
| ❓ [FAQ.md](FAQ.md) | The questions a reviewer or a validation team actually asks, each answered with the artifact or document that settles it |
| 🧾 [JOURNEY.md](JOURNEY.md) | What did this project actually do, build phase by build phase and sprint by sprint, and what changed our mind? |

## 🏗️ How it works

| Document | Answers |
|:---|:---|
| 🏛️ [ARCHITECTURE.md](ARCHITECTURE.md) | What the system is, the three ways into it, and how the pieces fit, with the reason for each design choice |
| 📊 [METHODS.md](METHODS.md) | Estimators, bootstraps, null bands, certification, recheck, the chain, label error and release: each with its derivation and what it assumes |
| ✅ [CASES.md](CASES.md) | Every case, the test covering it, the artifact demonstrating it |

## 📐 Contracts

> The design. **Binding on contributors**, and read before writing code.

| Document | Answers |
|:---|:---|
| 📜 [SPEC.md](SPEC.md) | The technical specification: data model, validation harness, matrix, drift, policy, gate |
| 🧱 [../CLAUDE.md](../CLAUDE.md) | The invariants, the silent failures, the coding standards, what is out of scope |
| 🗂️ [TASKS.md](TASKS.md) | The phased build order and the gate at the end of each phase |
| 🔀 [CONTRIBUTING.md](CONTRIBUTING.md) | Git workflow, commit rules, what is committed, the documentation audit |
| 🎬 [KICKOFF.md](KICKOFF.md) | The original brief |

## 🔬 Evidence and rationale

> Where the numbers and the reasoning actually live.

| Document | Answers |
|:---|:---|
| 🧠 [../DECISIONS.md](../DECISIONS.md) | Append-only entries. *"Why did you do it that way?"* — including the reversals |
| ⚠️ [LIMITATIONS.md](LIMITATIONS.md) | Scope, declared gaps, open items. **Read before quoting anything** |
| 🔬 [EXTERNAL.md](EXTERNAL.md) | Does this machinery mean anything on detectors we did not build, on data we did not construct? |
| 🧪 [REDACT.md](REDACT.md) | What happens when this certification is run over somebody else's benchmark, and why a rule-based detector has no operating point to tune? |
| 🏦 [RBI-MRM-2026-CROSSWALK.md](RBI-MRM-2026-CROSSWALK.md) | Which paragraphs of the RBI's **draft** model-risk guidance can a warrant supply evidence for, which only in part, and which not at all? Generated; a register, not a compliance claim |
| 🚚 [PATHS.md](PATHS.md) | What moved on 2026-08-29 and where it went |
| 📈 [../results/RESULTS.md](../results/RESULTS.md) | The rendered results, with fixture numbers refused rather than printed |
| 📑 `reports/PHASE-<N>.md` | One report per sprint, leading with the answer; [PHASE-12.md](../reports/PHASE-12.md) closes sprint 12; [PHASE-15.md](../reports/PHASE-15.md) records an earlier repair checkpoint; [PHASE-16.md](../reports/PHASE-16.md) audits the product state; [PHASE-17.md](../reports/PHASE-17.md) records certificate replay; [PHASE-18.md](../reports/PHASE-18.md) records recheck evidence linkage; [PHASE-19.md](../reports/PHASE-19.md) records fresh-batch binding and ordinary replay; [PHASE-20.md](../reports/PHASE-20.md) records linear chain-prefix replay; [PHASE-21.md](../reports/PHASE-21.md) records release label auditing; [PHASE-22.md](../reports/PHASE-22.md) records grouped-boundary evidence and historical replay; [PHASE-23.md](../reports/PHASE-23.md) audits grouped hard-negative FPR warrants; [PHASE-24.md](../reports/PHASE-24.md) repairs collapsed grouped flag-rate and descriptive FPR intervals; [PHASE-25.md](../reports/PHASE-25.md) records the fresh-clone gate on the integrated line |
| [PHASE-26.md](../reports/PHASE-26.md) | Why the clean-clone verifier now rejects missing, duplicate and contradictory tier summaries, and what was tested |
| [PHASE-27.md](../reports/PHASE-27.md) | Which known release blockers are preflighted before the full clone suite, and what remains untested |
| [PHASE-28.md](../reports/PHASE-28.md) | How failed clone attempts are retained without replacing the last passing record |
| [PHASE-29.md](../reports/PHASE-29.md) | Why the current monitor uses mixture wealth while the Decision 187 schedule remains historical |
| [PHASE-30.md](../reports/PHASE-30.md) | What October export preparation built, what the full clean-clone gate verified, and which customer-evidence gates remain open |
| [PHASE-31.md](../reports/PHASE-31.md) | How routed drift-response serialization and the PowerShell Quickstart were repaired and tested |
| [PHASE-32.md](../reports/PHASE-32.md) | Why malformed prepared packages now produce input errors distinct from valid changed-package mismatches |
| [PHASE-33.md](../reports/PHASE-33.md) | How the public synthetic export reaches a certificate with two separately replayed evidence boundaries |
| [PHASE-34.md](../reports/PHASE-34.md) | Why the public handoff regression is now in the measured customer-only CI list |
| [AI-OPPORTUNITIES-2026-10.md](../reports/AI-OPPORTUNITIES-2026-10.md) | Which current competition, founder and incumbent signals shaped the October hypothesis, and which claims remain unverified? |
| [INCUMBENT-PACKET-COMPARISON-2026-10.md](../reports/INCUMBENT-PACKET-COMPARISON-2026-10.md) | What evaluation exports and review workflows incumbents document, and what must be checked in a real packet? |
| [BUILD-PLAN-2026-10.md](../reports/BUILD-PLAN-2026-10.md) | What is the October day-by-day build and discovery schedule, with acceptance and stop gates? |
| [DISCOVERY-2026-10.md](../reports/DISCOVERY-2026-10.md) | What should a reviewer and engineer show before a real export or recurring decision is claimed? Blank worksheet; no interviews recorded |
| [PACKET-DESIGN-REVIEW-2026-10.md](../reports/PACKET-DESIGN-REVIEW-2026-10.md) | Which handoff and replay capabilities already exist, and what observed failure would justify a new package command? |
| [OFFLINE-HANDOFF-REVIEW-2026-10.md](../reports/OFFLINE-HANDOFF-REVIEW-2026-10.md) | Which files an offline reviewer needs, what the synthetic prepared package retains, and which compatibility checks remain unobserved? |
| [REPRODUCIBLE-DEMO-2026-10.md](../reports/REPRODUCIBLE-DEMO-2026-10.md) | How can a reader reproduce the synthetic valid, refusal and tamper cases? |
| [MENTOR-BRIEF-2026-10-02.md](../reports/MENTOR-BRIEF-2026-10-02.md) | Shareable account of the research hypothesis, October progress, verification limits and month plan |
| [STRATEGY-2026-09.md](../reports/STRATEGY-2026-09.md) | The commercial stopping rule and dated primary-source regulatory corrections |
| 🧭 [NEXT-STEPS-2026-09-17.md](../reports/NEXT-STEPS-2026-09-17.md) | What to do next, after sprint 12: the decisions only the founder can make, then the engineering, in order |

## 🎥 Presentation and the business case

| Document | Answers |
|:---|:---|
| 🖥️ [DEMO.md](DEMO.md) | The two-pane demo this build exists to produce |
| 🗣️ [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | The beat-by-beat script and what is on screen |
| 💼 [PROPOSAL.md](PROPOSAL.md) | The business proposal |
| 🧪 [PILOT-PROTOCOL.md](PILOT-PROTOCOL.md) | What a first pilot would test, for which buyer and which recurring decision, and what would end it. A plan; no pilot has run |
| 🔖 [EXTERNAL_FIGURES.md](EXTERNAL_FIGURES.md) | The register that gates every figure about the world, and its provenance tiers |

---

## The rules these documents follow

> [!IMPORTANT]
> These five are why the documentation can be trusted at all. They are enforced
> by tests, not by discipline.

**1 · Every number is computed by code.**
If it cannot be traced to an artifact in `results/`, it does not go in a
document. The README's claim table names the artifact **and the field** for each
of its numbers, and `make verify` resolves all of them. A number edited by hand
fails the build.

**2 · The orientation pages carry no measured numbers at all.**
They point at the generated documents instead, so a re-run cannot leave them
stale. Structure, procedure and vocabulary change with the code, not with the
run.

**3 · `DECISIONS.md` is append-only.**
A reversed decision is superseded by a new entry that links back — never edited
away. That is why entries 108/109 and 116 read as corrections rather than as
history that never happened.

**4 · Prose documentation is written at the end, not during the build.**
`CLAUDE.md` sets this. `DECISIONS.md` is the sole exception, because it is the
one document that cannot be reconstructed later.

**5 · A figure about the world needs a register entry.**
Court awards, fines, standard clause numbers — see
[EXTERNAL_FIGURES.md](EXTERNAL_FIGURES.md). A test enforces it against the
proposal.

**Which of these a test enforces:** every `docs/` page is indexed here and every
relative link resolves (`test_docs_index.py`); every test and artifact
[CASES.md](CASES.md) names exists (`test_cases_matrix.py`); every claim-table row
reproduces (`test_claims.py`, `make verify`); every `DECISIONS.md` citation
resolves (`test_decisions_integrity.py`).

<div align="center">

---

**[⬆ Back to the project README](../README.md)**

</div>
