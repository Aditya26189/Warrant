# Warrant: October research and build update for a mentor

**As of 2 October 2026.** This reports the October research, implementation
and verification against the prior Phase 29 release baseline. There is no
customer pilot, production deployment or measured commercial demand yet.

## The decision in one paragraph

Warrant began as a reproducible test of whether a cheap linear classifier over
an LLM's *question-time activations* can choose which answers deserve expensive
review. The research code and a local evaluation CLI already exist. After
reviewing recent AI competition winners, company launches, investor requests
and existing evaluation products, the October hypothesis is narrower than
“build another agent platform”: help a team take an **existing, human-labelled
detector-score export**, preserve what the labels, scores and sampling units
mean, and produce a locally replayable review decision. I have built the first
handoff step and written a 30-day discovery and engineering plan. The key
unanswered question is whether a real reviewer lacks this evidence in their
current workflow and would repeatedly use a separate package.

## Where the project stood before October

The original scientific claim is a hypothesis, not a product guarantee: the
model state after reading a question but before generating a token may contain
a signal of whether its answer will be wrong. A logistic-regression probe reads
that state and is evaluated by its recall, precision, measured flag rate and
lift over random review at the same budget. Selection is made on validation,
not on the test set; test scorings and methodological decisions are logged.

The [generated results](../results/RESULTS.md) show why scope matters. On the
named 600-question TriviaQA envelope, the Qwen 2.5 7B last-token probe had
AUROC **0.826**, recall **0.079**, precision **0.880**, measured flag rate
**0.0417**, and lift **1.906** (seed `1729`, config hash
`2640a176a26a80a0`). At that small review budget it caught only about 8% of
the labelled errors, and the baseline error prevalence was high. These are
results on that research envelope, not a promise about support traffic. The
report also contains synthetic fixtures, refused cells and unresolved
calibration sensitivity; a fixture cannot be presented as model evidence.

By Phase 29, Warrant had become a **local evidence tool** as well as a research
harness. It can certify a declared scored and labelled file at an operating
point, replay the retained input and record, recheck on a fresh batch, register
and evaluate a separate release holdout, describe second-review label
fragility, and estimate review effort from declared assumptions. The
[product-state map](../docs/PRODUCT-STATE.md) separates these installed local
commands from simulated monitoring/gateway components. None of this proves a
customer need, live reliability, authenticated custody or commercial value.

## What current research indicates

I treated awards as evidence of what organizers and judges selected, vendor
announcements as claims about product direction, and the founder material as
interest rather than purchase demand. The
[research memo](AI-OPPORTUNITIES-2026-10.md) records methods, dates, sources
and alternatives. It is a purposive worldwide scan, not a complete ranking of
all competitions.
The [incumbent packet comparison](INCUMBENT-PACKET-COMPARISON-2026-10.md)
checks documented exports, reference answers and review workflows in more
detail. It does not replace a hands-on comparison with a real customer packet.

| Signal checked | Observation | Relevance to this decision |
|---|---|---|
| [Elastic Forge the Future, 30 September](https://www.elastic.co/blog/mumbai-forge-the-future-hackathon-2026) | Winner Vigil attached timestamps and rule references to possible financial-call violations. | Narrow review tools with inspectable evidence are compelling; no published award result establishes detector recall or buyer demand. |
| [Vista agentic hackathons, 10 September](https://www.vistaequitypartners.com/news/vista-equity-partners-names-winners-of-2026-agentic-ai-hackathons/) | Avalara and InvoiceCloud won with enterprise workflows that retain deterministic checks, approvals and records. | Human checkpoints and audit trails matter in demonstrations; team-projected savings are not independent outcomes. |
| [OpenAI WebMCP Challenge](https://webmcp.devpost.com/project-gallery?page=1) and [Build Week](https://developers.openai.com/blog/build-week-winners) | Winning projects show agent-ready web actions and focused, inspectable domain tools. | Agent-ready websites are an emerging interface niche, but the standard is experimental and Warrant has no specific web workflow to serve yet. |
| [YC Fall 2026 requests](https://www.ycombinator.com/rfs) | Multiplayer AI and AI-native compliance are among current investor interests. | Longer, shared agent work increases the apparent value of handoffs; investor interest does not validate this product. |
| [Dataiku Agent Management](https://www.dataiku.com/company/news/dataiku-agent-management-general-availability), [AWS AgentCore Evaluations](https://aws.amazon.com/blogs/machine-learning/evaluate-any-agent-framework-with-amazon-bedrock-agentcore-evaluations/) and [Braintrust evaluation exports](https://www.braintrust.dev/docs/evaluate/interpret-results) | Large incumbents already offer cross-platform governance, trace evaluation, human review and export workflows. Braintrust also documents [custom precision/recall](https://www.braintrust.dev/docs/cookbook/recipes/PrecisionRecall). | Generic agent governance, framework-neutral evaluation, exports and standard classifier metrics are not defensible novelty claims. The proposed wedge needs a side-by-side test against an actual incumbent review packet. |
| [SuccessKPI contact-center quality release](https://www.globenewswire.com/news-release/2026/09/03/3355947/0/en/three-successkpi-ai-releases-automate-quality-review-work-for-human-and-ai-agents-while-leaving-human-judgment-in-place.html) and [IBM watsonx Orchestrate](https://www.ibm.com/new/announcements/new-in-ibm-watsonx-orchestrate-cross-platform-agent-discovery-custom-evaluation-and-agentops-agent-goes-ga) | SuccessKPI already markets AI-ranked interactions, evidence-backed draft scores and human overrides for contact centers. IBM offers cross-platform agent discovery and evaluation. | The proposed first support buyer is already served by specialized vendors. The unresolved question is whether their real packet lacks an independently replayable operating-point assessment; vendor copy cannot answer it. |

The most useful low-level clue is the **unit of evidence**. A winning product
may point to an audio *segment*, while a reviewer must decide about a *call*,
ticket, conversation or release. Treating correlated segments as independent
observations makes uncertainty look stronger than it is. Likewise,
[OpenTelemetry's GenAI convention](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-events.md)
can carry evaluation scores and labels, but a label event alone does not prove
independent human ground truth or a protected holdout. The product hypothesis
is to make these assumptions explicit, enforce what software can enforce, and
refuse unsupported conclusions. It remains a hypothesis until a buyer shows a
real recurring decision for which existing tools fall short.

## What I built in October

The first milestone is a versioned, explicit export preparation workflow:

```text
existing flat CSV/JSONL + mapping.json
               |
       warrant prepare
               v
    scored.csv + manifest.json
               |
      warrant verify-prepared
               |
        existing Warrant certify/release commands
```

The mapping must identify item ID, human binary label and numeric detector
score; it can preserve group and second-review columns. It must state both
label meanings and whether higher or lower scores mean “flag”. It must map a
group or explicitly declare independent rows. The normalizer rejects missing
or ambiguous fields, duplicate IDs, unknown labels and nonfinite scores.
It never invents labels, silently drops a canonical group or second label,
selects a threshold, resamples data or changes the scientific holdout. For a
lower-is-positive score it negates the score and records that choice.

`prepare` creates a new directory and will not overwrite one. Its manifest
binds source, mapping and normalized bytes plus the effective scored-row
sequence. `verify-prepared` recomputes the package from the retained originals
and detects a changed file. The hashes check local integrity; they are not
signatures or proof that labels are true, groups are valid, or the sample is
representative. Parsing makes a temporary copy of source bytes, so sensitive
exports need an approved local environment and retention practice.

The feature is accompanied by a four-row **synthetic** example, an
installed-wheel test that exercises `prepare`, `verify-prepared` and existing
`certify` on a separate 600-row **synthetic** export, an updated
[input guide](../docs/INPUT.md), and a
[discovery worksheet](DISCOVERY-2026-10.md). None is a customer trial.
An [executed synthetic demo](REPRODUCIBLE-DEMO-2026-10.md) shows a valid
example, a deliberate refusal and a changed-source replay mismatch. The
[packet design review](PACKET-DESIGN-REVIEW-2026-10.md) identifies the existing
replay commands that a new bundle would otherwise duplicate and defers that
feature until a reviewer exposes a concrete handoff gap.
The [offline handoff review](OFFLINE-HANDOFF-REVIEW-2026-10.md) inspects the
prepared synthetic files: excluded prompt-note values are absent, but IDs,
labels and groups remain, and transformation replay still requires the
original export plus mapping. This is a minimum-data boundary, not a claim
that a real customer export can safely be transferred.
Decision 227 in [DECISIONS.md](../DECISIONS.md) preregistered the
representation-only boundary before implementation.

## Verification status on 2 October

The 40 focused preparation tests, installed-wheel handoff test, changed-Python
lint and clean-source full suite passed for source commit `239a10b`. The test
inventory records **2,180 collected** at that committed snapshot; that is a
collection count, not a claim
that 2,180 tests passed. Integrating the timeout regression and two new
documentation pages increased collection to **2,183** at `3abe09c`; the
generated inventory and README were refreshed at `53aeef5`. The exact clone
preflight now passes. Smoke was 7/7, the published claim table replayed
92/92 claims, and 25/25 frozen-score comparisons matched. Re-extracting
activations was **skipped** because the large cache is not tracked in Git.

Two attempts at the repository's **full tracked-file clean-clone gate timed
out** in the 3,600-second pytest step. Their clone, smoke, preflight and
available verifier checks passed, but the full gate did **not** pass. Both
[failure records](../results/clean_clone_failures/) are retained. A later
tracked-only clone passed smoke and both verifier tiers with tests explicitly
omitted; its [record](../results/clean_clone_phase30_no_tests.json) must not be
read as a full-suite pass. I fixed timeout reporting so a future timeout keeps
pytest's last captured lines. A separate direct suite in a kept clone of
`bcfd5a1` exposed the stale 2,180 count and was stopped after the deterministic
failure; that run is not a pass. The corrected full clean-clone gate
subsequently **passed** at clean source commit `87070b6`: clone, smoke,
preflight, full suite and verifier all exited zero. Its
[generated record](../results/clean_clone.json) reproduced 92/92 claims and
25/25 frozen-score comparisons; activation re-extraction was skipped because
the large caches are not tracked. The full test step took 2,816 seconds.
The pass record is committed at `cc46105`; later research and report commits
do not change the tested implementation. See the
[Phase 30 report](PHASE-30.md) for the complete failure and repair history.
Phase 30 then merged into the release checkout at `6004099`. Its direct
Windows smoke check passed 7/7; verification reproduced 92/92 claims,
25/25 frozen-score comparisons and, with the ignored local caches available,
3/3 activation comparisons. The clean clone correctly reported that last
tier as skipped because those caches were absent there.

The Phase 30 release and tag were pushed to GitHub at `8556585`. A subsequent
offline handoff audit merged **locally** at `cb5b6ca`. The export-preparation
test file was then added to the lightweight customer CI list at `18f407a` and
merged locally at `94b4447`. All 40 preparation cases passed in an isolated
Python 3.12 environment containing only the declared customer dependencies
and pytest; preparation plus packaging passed 50/50 from the clean integrated
checkout. A broader local Windows run of the customer test list was stopped
at 28% without a failure; it is **not** a complete matrix pass. The later
local commits have not been published, and the configured Linux 3.11/3.12 CI
jobs have not been observed passing for them.

A further input-boundary review found that a JSONL integer score too large
for Python's finite float range escaped as an uncaught traceback. The
row-specific refusal fix and regression are committed at `6f0cbcd` and
integrated locally at `50c5fac`. The 51 preparation/packaging checks, the
installed-wheel suite and Ruff passed. That later fix has **not** received a
new full clean-clone gate; the earlier gate remains evidence for `87070b6`,
not for this newer head.

There is no observed remote CI pass for this October head, no real export, no
customer conversation, no design partner and no deployment. The implementation
is usable local software with a passing clean-clone gate at the named source
commit; it is not validated product-market fit.

## Thirty-day working plan and decision gates

The [day-by-day plan](BUILD-PLAN-2026-10.md) covers 1-30 October with
acceptance evidence for each task. Dates are checkpoints, not a claim that an
unattended agent can work continuously for a calendar month. Engineering can
move faster in an active session; interviews and repeat use require time and
participating people.

| Window | Planned work | Gate or decision |
|---|---|---|
| Oct 1-7 | Complete export preparation, replay, installed-CLI demonstration, documentation and clean integration. | The synthetic installed path, full tracked-clone gate and integrated release smoke/verification passed at named commits. A human dry run remains unobserved. |
| Oct 8-14 | Refresh competitor research; inspect an owner-approved, de-identified real export and an actual review packet; fix observed import friction; design a portable evidence package only if the present packet is missing something material. | Seek five real conversations, two usable exports and one named recurring review decision by Oct 14. These are targets, with **zero observed so far**. If unavailable, freeze speculative adapters and record the access gap. |
| Oct 15-21 | Compare actual incumbent output, implement one requested integration if its schema and permissioned fixture exist, examine label disagreement and group leakage, try a second use and independent reviewer replay. | Continue only if a decision owner can explain how the retained evidence changes a repeated choice. A single positive reaction does not qualify. |
| Oct 22-30 | Recheck incumbent alternatives, improve only observed ergonomics, run package/compatibility/claim verification, produce a valid/refusal/tamper demonstration and prepare a specific pilot proposal. | Decide keep, pivot or stop, with evidence of repeat use and a budget owner or a candid open-source research outcome. |

The next substantive task is an external workflow test with a team that owns
a review threshold, can describe the sampling unit and label provenance,
and can compare its existing packet with Warrant's output. A permissioned,
de-identified export and the current reviewer packet would make that test
concrete. Without them, the plan freezes speculative adapters.
No one has been contacted on the founder's behalf.

## What would change my mind

I would narrow or stop the product hypothesis if a team cannot produce
independent labels, does not make a recurring review-threshold decision, finds
its current evaluation packet sufficient, or spends more to acquire credible
evidence than the decision is worth. Conversely, a useful pilot would require
an actual permissioned export, a named decision owner, a concrete missing
uncertainty/refusal/replay field in the existing packet, and a second run that
someone other than the author can reproduce. That is the evidence the next
month is designed to obtain; this report does not claim it already exists.
