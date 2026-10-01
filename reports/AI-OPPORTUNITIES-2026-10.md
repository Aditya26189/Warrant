# AI opportunities: evidence checked 1 October 2026

## Recommendation

Spend October testing **portable evaluation evidence for AI review triggers**:
take an existing scored export, preserve its meaning and sampling units, run
the existing Warrant measurement, and let another person reproduce the result.
Start with teams shipping AI customer-support workflows that already review
some outputs. The user is an AI engineer; the second user is whoever accepts
the evidence for a change. A budget owner and willingness to pay are unknown.

This is a bounded product hypothesis, not a claim that evaluation is a new or
unoccupied market. It exploits existing work without treating that work as a
reason to keep building indefinitely. The [October plan](BUILD-PLAN-2026-10.md)
includes explicit commercial stopping rules.

## What the older work establishes

Baseline: repository commit `3df7e89`, Phase 29, reviewed locally. Read the
[product-state map](../docs/PRODUCT-STATE.md) for implemented surfaces and
limitations. Warrant already has scored-file certification, retained-evidence
replay, chained rechecks, preregistered release evaluation, label diagnostics,
and a substantial research harness. October must connect these capabilities
to a usable workflow, rather than reimplement them.

The [September strategy](STRATEGY-2026-09.md) withdrew a PII benchmark proposal
after discovering existing work. Its lesson still applies: absence from a
search is not evidence of an empty market. The
[September improvement plan](IMPROVEMENT-PLAN-2026-09-23.md) recommended customer
discovery alongside correctness work. Later phases repaired multiple defects;
they did not supply interviews, production traffic, paying users or repeat use.
The current bottleneck is external usefulness, not the number of internal tests.

## Research method and limits

Checked organizer announcements, project submissions, vendor documentation,
an investor request list and a commissioned survey. Search covered global
online events and North American, European, Indian and Hong Kong examples.
This is a purposive sample, not a complete worldwide ranking or a census of
the latest competitions. Awards establish a judging result; submissions
describe what builders claim. Neither proves production reliability or demand.
Relative dates and search-engine crawl dates are not treated as event dates.
No paid product trial, project deployment audit or customer interview was run.

## Competition signals

| Event and date evidence | Verified result | What to learn; what not to infer |
|---|---|---|
| Global Gemini 3 Hackathon; organizer update displayed as about five months old when checked | Globot grand prize; Aegis second; Netra third; AgentGuard an honorable mention | Operational workflows, accessibility and agent security attract judges. This is not a September winner announcement. [Organizer results](https://gemini3.devpost.com/updates/40729-the-moment-you-ve-been-waiting-so-patiently-for) |
| Globot project submission | Describes a supply-chain crisis workflow combining route planning, risk analysis, document review and adversarial checks | Domain integration makes the demonstration concrete. Its speed, forecast and financial claims remain the team's claims; not independently reproduced here. [Submission](https://devpost.com/software/globot-341w9q) |
| Claude Opus 4.8 Build Day, San Francisco, June 13; announcement June 17, 2026 | Tekton first, Sim Francisco second, Custom Universe third | Reconstruction with source-linked components, simulation and editable visual worlds are impressive artifact-centered interfaces. A verifier agent is not independent ground truth. [Organizer announcement](https://claude.com/blog/meet-the-winners-of-our-claude-opus-4-8-build-day-hackathon) |
| SharePoint Hackathon 2026; announcement March 25 | Plumsail document-generation project won best SharePoint use in AI agents; Nexus bid management won SharePoint Embedded | Enterprise content plus a specific deliverable is a credible workflow pattern. Ecosystem awards also reflect the organizer's platform priorities. [Microsoft results](https://techcommunity.microsoft.com/blog/spblog/announcing-the-winners-of-the-sharepoint-hackathon-2026/4505690) |
| Hack the North 2026; current organizer museum, exact event day not verified here | Museum lists finalists including Combadge, CADEX, Composition and TakeOne | Voice/vision hardware, CAD and creative production are current maker signals. The museum calls these finalists; do not relabel them grand-prize winners. [Organizer museum](https://museum.hackthenorth.com/) |
| Hong Kong IADS Developer Hackathon; March 27, 2026 announcement | vbiz champion, Mortify first runner-up, Fill Easy second runner-up | Consented financial-data workflows are an institutional interest signal. The announcement alone does not validate each team's AI capability. [HKSTP announcement](https://www.hkstp.org/en/park-life/news-and-events/news/all-news/iads-developer-conference) |
| Gemini 3 Paris Hackathon; institution announcement lacks a precise date in retrieved text | Two 42 Paris teams took first and third | European participation verified; insufficient project detail to use this as evidence for a particular niche. [42 Network](https://www.42network.org/blog/achievements/double-podium-for-42-paris-students-at-the-gemini-3-paris-hackathon/) |

India's Smart India Hackathon search surfaced older official results; a current
2026 national winner list was not established. AWS's Breaking Barriers page
confirmed an event but did not establish a fresh 2026 winner list. Future events
and advertised prize pools were excluded from winner evidence. This matters:
an upcoming event cannot tell us what already won.

## What companies and founders are pushing

**Very recent enterprise signal.** Dataiku's September 24 announcement reports
a Harris Poll conducted July 9-29 among 685 CIOs in eight countries. It reports
that 72% cannot consistently confirm outcomes across their agents and 83% lack
standardized agent lifecycle management. These are self-reported answers in a
vendor-commissioned survey, not measured failure rates or a purchase commitment
for Warrant. The useful signal is pressure to demonstrate outcomes and manage
agent changes. [Announcement and methodology](https://www.dataiku.com/company/news/global-ai-confessions-report-cio-edition-2026)

**Current founder themes are broader than chat.** YC's Fall 2026 requests include
multiplayer AI, easier deployment of small purpose-built software, physical-world
operations/data, consumer experiences, eldercare and AI-native compliance.
This is investor interest, not validated demand. My inference: sharing control,
handoffs and evidence becomes more valuable as agents perform longer tasks.
Building all those categories would dilute a one-month effort.
[Current requests](https://www.ycombinator.com/rfs)

**Evaluation is becoming ordinary engineering practice.** Anthropic's January
engineering article describes evaluating multi-turn agents with environment
and tool state, not just a final response. That implies we must retain the
unit of evaluation: ten turns from one conversation are not ten independent
customers. Warrant can measure a supplied review detector; it cannot infer
overall agent reliability from that detector alone.
[Engineering article](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

**Creators want manipulable outputs.** The competition sample includes visual
reconstruction, scenes, film production and CAD. The inference is that an output
people can inspect and change is often more compelling than another chat box.
For Warrant the corresponding artifact is a replayable evidence package, not a
new creative model. Creator-tool demand remains a separate opportunity requiring
creator access and evaluation of workflow quality.

## Competition and industry fit

| Existing surface | Evidence | Consequence |
|---|---|---|
| LangSmith | Documents offline benchmarking, regression tests, online evaluation and human-feedback workflows. [Documentation](https://docs.langchain.com/langsmith/evaluation-types) | Do not build another general evaluation runner or claim nobody connects traces to tests. |
| Braintrust | Documents systematic evaluation and exposes annotation, exports, experiments and online scoring in its product navigation. [Documentation](https://www.braintrust.dev/docs/evaluate) | Consume exported evidence first. A vendor-specific adapter requires a documented schema and an actual sample. |
| AgentGuard | Gemini honorable mention describes a semantic firewall. [Project](https://devpost.com/software/agentguard-the-semantic-firewall-for-the-agentic-web) | Agent security is already crowded even at the hackathon layer. An award is not evidence of adversarial robustness. |
| Warrant today | Local code and replay contracts, not a market source | Possible contribution: explicit operating-point evidence, refusal when unsupported, independence handling and local replay. Competitors' absence of these features has not been proved. |

Use explicit versioned data contracts, content hashes, reproducible commands,
strict failure behavior and installed-package tests. These are engineering
choices for this product, not claims of certification against an industry
standard. No blanket OpenTelemetry compatibility: generic telemetry does not
supply human labels or establish independence. Native integrations and evolving
conventions must be verified individually before advertised support.

## Opportunity comparison

Qualitative founder judgment, not a numerical market score:

| Candidate | Why now | Main obstacle | October decision |
|---|---|---|---|
| Agent evaluation evidence handoff | Existing export workflows, outcome pressure, reusable local core | Unknown buyer budget; incumbents can add it | Build one small usable extension and test demand |
| Multiplayer agent workspace | Explicit current investor interest; long tasks need shared control | Crowded platforms, auth and orchestration scope | Track; no new workspace product this month |
| Vertical document/bid agent | Concrete enterprise award examples | Domain access, document rights, ground truth | Alternative if discovery exposes a repeatable reachable workflow |
| Voice/vision field assistant | Current wearable and physical-world demos | Hardware, field testing, safety and distribution | Outside current free-compute month |
| Creative 3D/video workflow | Strong visual demo appeal | GPU costs, crowded tools, creator distribution | Do not pivot without creator access |
| New PII benchmark or generic guard | Existing work and current security entrants | Weak novelty claim; already investigated | Reject for this month |

The recommendation survives only if people can supply an export, understand
the result and use it for a recurring decision. A month of code without those
observations is a failed commercial experiment, even if every test passes.

## Questions that can overturn the recommendation

Can a team show its last actual release-review packet? Who collects the evidence,
who challenges it, and what happened when the evidence was inconclusive? Are
labels human-reviewed or merely another model's score? Are repeated sessions
tracked? Does a reviewer need local replay, or is the incumbent experiment link
already sufficient? What existing budget pays for this task? Ask for examples,
not agreement with an imagined feature. No outreach was sent in this session.

Refresh this memo on October 8, 15, 22 and 29. Record new evidence and changes to
the recommendation; do not append trend links without a build decision.
