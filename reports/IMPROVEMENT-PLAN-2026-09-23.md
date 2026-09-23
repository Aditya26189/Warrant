# A practical improvement plan for Warrant

Research checked 23 September 2026. Code baseline: `main` at
`cc1904e2215e1c6a85847125aef8997a2e0caac6`. This is a proposed product and
research plan, not a record of implemented repairs or customer traction.
The founder reports no interviews, design partners, paid pilots or revenue.

## 1. Recommendation and evidence

Build a dependable evidence package for one recurring decision: whether a
changed AI review/escalation detector has sufficient evidence at its declared
operating point. Start with a local command-line workflow that an engineer can
run and a separate reviewer can understand and reproduce. Fit into the
customer's existing evaluation and approval process.

The first candidate use case is a review trigger for AI customer-support
outputs. Interview reachable AI vendors and fintech teams supplying regulated
customers, together with the people who review their evidence. This is a buyer
hypothesis, not an established market. A bank validation team can be a buyer,
but choosing large global banks exclusively before establishing access, data
availability and a budget owner would add avoidable commercial uncertainty.

The project has enough substance to test this proposition. It does not yet
have the evidence to establish a venture-scale business. More features cannot
settle willingness to pay, repeat use or access to representative labels.
Run two bounded tracks together: customer discovery and correctness repairs.

The [independent review](PROJECT-REVIEW-2026-09-23.md) documents reproduced
defects and passing checks. It supersedes the engineering-readiness conclusion
in [the September 17 next steps](NEXT-STEPS-2026-09-17.md); that document's
emphasis on commercial discovery remains appropriate. The review found that
passing source tests did not establish installed-package usability, valid
grouped uncertainty, or safe concurrent chain updates. The repairs are still
open at this plan's baseline.

Keep Round 1 and its measured findings intact. The startup proposition does not
require the activation probe to outperform all other detectors. Customers can
bring scores from an existing detector. New GPU experiments should answer a
specific research question or customer need, not stand in for product progress.

## 2. What the external research changes

### A crowded category, with a narrower possible opening

| Primary evidence checked | What it establishes | Implication for Warrant |
|---|---|---|
| [LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types) | Offline and online evaluation are existing product capabilities | A generic evaluation runner is a weak differentiation claim |
| [Braintrust evaluation documentation](https://www.braintrust.dev/docs/evaluate) | Experiments, evaluation records and production evaluation already have established workflows | Import existing outputs before asking a team to replace its tools |
| [Arize Phoenix](https://arize.com/docs/phoenix/) | Open-source tracing and evaluation are available | Local operation and openness alone do not establish an advantage |
| [ValidMind monitoring workflows](https://docs.validmind.com/guide/monitoring/trigger-workflows-on-threshold-breach.html) | Monitoring results can trigger review or remediation workflows | Monitoring, workflow and audit-trail positioning is already contested |
| [ValidMind attestation review](https://docs.validmind.com/guide/attestation/review-attestations.html) | Ownership, control documentation and review are already productized | Do not begin by rebuilding a broad governance suite |

These are documented capabilities, not independent performance comparisons.
This research did not trial the products or exhaust their APIs. It does not
establish that competitors lack rigorous intervals, refusal logic or equivalent
evidence exports. Those claims need a direct comparison before appearing in a
pitch.

The possible advantage to test is operational: a reviewer can determine what
an error-rate claim supports, what it excludes, why evidence is insufficient,
and what a further study would cost, with less preparation and interpretation.
The formulas and file hashes alone are not a durable competitive advantage.

The Bank of England's February roundtable summary reports participants'
concerns about validation capacity and delays, and interest in testing and
monitoring broader AI-system outcomes. This supports investigating the problem;
it does not establish demand for this implementation or a budget for it.
[Source](https://www.bankofengland.co.uk/minutes/2026/february/summary-of-ai-roundtables-feb-2026).

### Correct the regulatory sales assumptions

The Federal Reserve's April 2026 SR 26-2 supersedes SR 11-7. Its accompanying
guidance explicitly excludes generative and agentic AI models from scope while
still referring to organizational governance for uncovered systems. Do not
claim this guidance universally requires a GenAI Warrant product. Whether a
particular non-generative detector falls within scope depends on that control
and its context. [SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm),
[guidance, footnote 3](https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm).

The European Commission's July 2026 AI Omnibus notice gives later application
dates for specified high-risk categories: 2 December 2027 for Annex III and
2 August 2028 for Annex I product systems. A universal 2026 high-risk deadline
is therefore an unsound sales premise. This does not mean all AI Act
obligations are deferred. [Commission notice](https://digital-strategy.ec.europa.eu/en/news/ai-omnibus-enters-force).

The repository's RBI crosswalk describes a draft. The underlying RBI page
could not be independently retrieved in this research, so its current final
status has not been revalidated. Do not convert the existing crosswalk into a
claim of binding compliance or regulator acceptance.

Sell evidence useful to a real decision. A regulator's existence is not proof
that a buyer needs another vendor.

## 3. Engineering work that must precede a customer pilot

Use the detailed [Claude repair instructions](CLAUDE-INSTRUCTIONS-2026-09-23.md)
for reproductions, ownership and acceptance checks. The sequence below groups
the work by customer consequence; it does not silently reopen protected code.
Methodological changes need an explicit rationale and review before execution.

| Order | Work | Acceptance evidence |
|---|---|---|
| A | Repair installed configuration and missing `controlplane.sampling` packaging, R1 | Build a wheel from clean source; install with only declared dependencies in a fresh environment; exercise customer commands from outside the checkout, including refusal and second-label paths |
| B | Repair dependent-data inference, R2 and R5 | Repeating the same observations within the same groups cannot manufacture independent evidence; unsupported grouped population intervals are withheld with a reason; ungrouped behavior remains covered |
| C | Repair revocation precedence and concurrent chain publication, R3 and R4 | A drift revocation cannot disappear behind an inconclusive FPR finding; continuation cannot silently rehabilitate that chain; simultaneous writers cannot both publish an accepted successor to the same head |
| D | Make verification strict and parsing predictable, R6 and R7 | Removing a modern seal is rejected in strict mode; legacy inspection is explicitly different; malformed outer types and enormous integers produce documented errors without partial records |
| E | Correct reference-size calibration and evidence binding, R8 and R9 | Drift simulation uses the actual stored reference count; attached sensitivity evidence matches threshold, method and data identity, or is rejected |
| F | Repair or remove the affected legacy monitor from supported workflows, R10 | The monitor's stopping statistic agrees with an independent calculation; the published guarantee matches the implementation and assumptions |

The customer gate is all relevant blockers closed on the exact advertised
workflow. If a legacy path is deliberately excluded, make it unavailable from
that workflow, test the exclusion and disclose it. A caveat buried in a report
does not repair a path still presented as supported.

For package resources, follow
[setuptools package-data guidance](https://setuptools.pypa.io/en/latest/userguide/datafiles.html)
and [Python's resource API](https://docs.python.org/3/library/importlib.resources.html).
Preserve explicit customer configuration overrides. Test the advertised minimum
Python version or narrow the metadata deliberately; avoid introducing an API
unsupported by that minimum.

For the chain, use one transaction boundary around validating the current
head and accepting its successor. Reuse the existing SQLite infrastructure
where practical. SQLite provides transaction and writer-locking mechanisms;
it does not automatically make an external JSON file and a database update
atomic together. Store authoritative state together or specify recoverable
publication states and crash recovery. Test process crashes between each
publication step. Limit the initial support claim to the tested local storage
arrangement. [Transactions](https://www.sqlite.org/lang_transaction.html),
[atomic commit and filesystem caveats](https://www.sqlite.org/atomiccommit.html).

### Replace reassuring test counts with adversarial acceptance checks

Keep the current suite, then add checks that challenge the assumptions:

- Duplicate observations without adding independent groups; include all-success,
  all-failure, few-group, unequal-group and mixed-label cases.
- Permute input order and preserve results where order is not meaningful.
- Change a threshold, rubric, detector version or study identity and reject an
  incompatible evidence attachment.
- Exercise every combination of FPR, drift, expiry and integrity findings;
  derive overall status only after preserving the individual findings.
- Start competing processes, interrupt publication, restart and verify the
  complete retained chain.
- Test fresh installed wheels, supported record migrations and untrusted input
  shapes, including limits on numeric values.
- Check statistical coverage or stopping behavior against an independently
  implemented reference under declared assumptions. Predeclare simulation
  sizes, seeds and Monte Carlo tolerances. Simulations provide evidence over
  tested scenarios; they are not a universal proof.

Do not replace a broken grouped interval with a guessed formula. Withholding
an unsupported population conclusion is an acceptable first repair. Publish
descriptive reviewed-pair agreement separately from uncertainty about a larger
population, as already intended in decision 201.

## 4. The smallest product worth improving toward

### One complete customer journey

The desired workflow is:

1. Describe the system, detector, version, use context and question being tested.
2. Register the operating point, criteria, sampling unit and evaluation protocol
   before opening the evaluation outcomes.
3. Import an approved scored export and its sampling/label metadata.
4. Validate data readiness and identify unsupported assumptions explicitly.
5. Evaluate once under the registered protocol and retain a scoped result.
6. Export machine-readable evidence and a readable reviewer report from the
   same record.
7. Reproduce and verify that evidence on another machine.
8. Repeat on the next release using a new study or an appropriate registered
   monitoring protocol, preserving the earlier records.

Several building blocks exist. The integration and customer acceptance of
this complete journey are not established. A readable HTML report and a CI
adapter are proposed additions, not claims about commands already implemented.
Do not start with a hosted dashboard.

### A shared, versioned evidence contract

Current record families carry different protections. Define a common evidence
envelope and explicit compatibility rules; preserve older records and their
actual meanings. Bind:

- system and detector identity/version, operating point and intended use;
- data digest, collection window, sampling protocol, inclusion probabilities
  when needed, and the independent unit;
- label rubric/version, source, blinded-review procedure and unresolved cases;
- preregistered criteria, method/version, confidence convention and selection
  history;
- counts, denominators, intervals, per-criterion findings and limitations;
- creation/expiry, parent relationships, integrity metadata and provenance.

This is not a requirement that legacy certify and release produce identical
statistical decisions: their declared methods can differ. The requirement is
that a consumer can identify the method and cannot accidentally substitute one
record for another.

A hash establishes a consistency check against a retained reference, not the
identity or trustworthiness of its author. Keep that distinction visible.
Add signatures only when a buyer's trust model requires them; signing incorrect
statistics does not make them sound.

The statistical result and the customer's deployment decision remain separate.
A customer may document a business exception in its own process, but that
must not mutate a REFUSED evidence record into VALID. A new override engine
is not needed for the first pilot.

### Explain a refusal in operational terms

For each unmet criterion, show the denominator, available evidence, uncertainty,
assumption and next permissible action. Distinguish insufficient evidence from
evidence of poor performance. Never present an inconclusive result as proof of
safety or as proof of failure beyond what was tested.

Suggested next actions can include improving the detector, changing the use
scope prospectively, clarifying labels or planning a fresh study. Do not advise
appending observations and retrying until an ordinary fixed-sample interval
passes. Repeated looks need a justified, registered sequential procedure, or
a new independent confirmation study.

## 5. Improve the evidence before increasing automation

This is likely the largest practical constraint. A statistically polished
report cannot rescue nonrepresentative traffic or unreliable labels.

**Define what a positive means.** For the proposed support use case, a positive
means the output needs the specified additional review under the customer's
rubric. It does not mean universally false, harmful or legally noncompliant.
Keep the rubric tied to the actual action and preserve ambiguous cases instead
of coercing them into clean negatives.

**Respect dependence.** Multiple turns from a conversation, variants of the
same question and repeated outputs from one case may share information.
Choose and document the unit that supports the inferential claim. Merely
adding a `group` column does not establish correct sampling or independence
between groups.

**Separate two datasets.** Use a probability sample of the declared traffic for
population-rate estimation, with design-aware analysis where needed. Maintain
a separate challenge set for important failure modes. A deliberately enriched
challenge set cannot establish live prevalence or precision without a justified
sampling/weighting design. Avoid tuning on either frozen confirmation set.

**Make review auditable.** Reuse the existing blinded queue. Preserve original
independent labels, reviewer/rubric versions and adjudication as separate
records. Measure disagreement, adjudication effort and ambiguity across the
relevant strata. The existing approximate double-review fraction is a starting
proposal, not assurance that rare disagreements or subgroup effects are covered.

**Calibrate automated graders.** Treat an LLM judge as another measurement
instrument. Compare it against independent domain review on the target task,
inspect disagreement patterns and preserve judge model/prompt versions.
Anthropic's evaluation guidance describes combining grader types and human
calibration; it does not establish that any judge is ground truth.
[Primary engineering guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).

**Use the correct denominators.** FPR is false positives among actual negatives;
the review/flag rate is flagged items among all items. They are not the same
budget. Recall uses actual positives, and precision uses flagged items. Require
the buyer to distinguish tolerable missed cases, unnecessary review and total
queue capacity. Display precision and recall together, without blending them
into F1. Use measured rates for workload estimates. Retain the distinction
between exact reviewed counts and estimated population quantities.

**Plan studies for the decision.** Size for the relevant class counts and
independent units, rather than announcing a universal number of rows. If the
customer cannot afford the labels needed for the desired claim, that is a
product feasibility result. Predeclare material slices and simultaneous-claim
handling; do not search for a flattering slice after seeing results.

NIST's measurement guidance supports context-specific metrics, explicit
limits, documentation of unmeasured risks and independent assessment. These
are useful design principles, not a certification conferred on this product.
[NIST Measure](https://airc.nist.gov/airmf-resources/playbook/measure/),
[validity and reliability](https://airc.nist.gov/airmf-resources/airmf/3-sec-characteristics/).

## 6. Founder work: discovery that can change the plan

Begin discovery while repairs proceed. Asking about a current workflow does
not require offering an operationally ready tool. The older pilot protocol's
blanket preconditions before anyone is approached should be narrowed: they
apply to running customer studies or presenting repaired capabilities, not to
honest problem interviews. This is a proposed protocol clarification, not a
silent edit to its existing text.

Use the already proposed twelve conversations as a bounded discovery exercise.
Do not count several people from one organization as independent customer
demand. Include the engineering operator, evidence reviewer and possible budget
owner. A consultant can provide access to multiple workflows, but several
consultant opinions are not several enterprise buying commitments.

Ask about a recent actual decision, before demonstrating features:

1. What was the last AI-system or detector change you had to approve or defend?
2. Walk through the evidence, tools, people and elapsed time. What was hard?
3. What happened when evidence was disputed or insufficient? Who bore the cost?
4. Which part is already solved by your evaluation or governance vendor?
5. Where do scores and labels come from? Who can authorize a representative
   export, and what independent units does it contain?
6. Who decides the error tolerance? Who reviews and retains the final artifact?
7. When is the next comparable decision? What would make external evidence
   acceptable in your existing process?
8. Which budget could pay to improve this, and what would purchasing require?

Then show a clearly identified demonstration including a refusal and ask the
reviewer to explain it back. Record confusion and demanded changes. Do not
interpret praise, a mailing-list signup or a second meeting as a purchase.

Maintain an evidence ledger: organization identifier, role, actual problem,
current artifact, frequency, consequence, owner, data access, purchasing path,
next commitment and contradictory evidence. Keep private customer materials
outside Git. Obtain permission before recording or attributing interview quotes.

**Proposed discovery gate:** proceed to pilot scoping if at least three distinct
organizations describe a recurring problem with a real artifact, and at least
two identify an owner, usable data path and upcoming decision. These are
operational heuristics chosen to prevent indefinite building, not statistical
proof or investor requirements. Preserve the older strategy's falsifier about
whether interviewees can name a consequence of a wrong control claim; add
actual workflow and access evidence rather than weakening that test.

If the gate fails, inspect why. No data access suggests a different entry point;
an existing tool already solving the problem suggests an integration or a
different problem; no recurrence suggests a service rather than a subscription.
Do not respond automatically by adding features.

## 7. Run a pilot that tests a business, not just the CLI

Offer a tightly scoped paid evaluation where feasible: one use case, one
detector version, one registered protocol and one evidence handoff. Payment
is for executing a defensible study and delivering findings, including a
refusal; it cannot be conditional on issuing VALID. Do not invent a market
price without learning the budget and delivery cost.

A free design-partner engagement may be useful if it provides approved data,
a named reviewer, a repeat decision and permission to measure workflow effort.
Record it as unpaid. A signed expression of interest is not revenue.

Agree before starting:

- the decision, owner, reviewer, deployment boundary and intended evidence use;
- the population, sampling unit, labels, operating point and success criteria;
- the existing process to compare against and how time/cost will be measured;
- who supplies and pays for labeling, adjudication, integration and support;
- how the customer retains and reproduces the record, including refusals;
- the next release or monitoring event and what would justify paid repeat use.

Measure the whole workflow: preparation, labeling, adjudication, interpretation,
review and corrections. Faster CLI runtime is not enough. Separate direct
time savings from improved decision quality, and avoid causal savings claims
from an uncontrolled before/after comparison.

The existing protocol's retention, independent reproduction and repeat-use
criteria are good. Exercise refusal in a clearly marked rehearsal or a genuine
study; do not alter real data to manufacture a desired pilot outcome. Actual
payment and a repeat decision strengthen the commercial evidence separately.

Track delivery economics including founder labor. As a planning calculation,
delivery contribution is fee minus direct labeling, integration, compute and
support costs. A contribution margin can divide that remainder by the fee;
it is not an accounting gross-margin claim until cost definitions are settled.
If each installation requires unrelated custom research, recognize the services
burden before projecting software-scale economics.

## 8. Milestones and ownership

These are proposed checkpoints, not delivery promises. Advance by evidence;
do not accept a milestone merely because its calendar date arrived.

| Checkpoint | Engineering/research | Founder/customer evidence | Stop or revise if |
|---|---|---|---|
| First week | Close packaging first; reproduce remaining blockers in retained tests; scope grouped/statistical repairs; begin unified-record design without rewriting legacy history | Identify reachable operators and reviewers; start recent-decision interviews | The supposed decision has no identifiable owner |
| By about day 30 | Close relevant correctness defects; independently review statistical assumptions; rehearse the installed customer journey | Complete discovery exercise and qualify data access, reviewer and budget paths | Interest remains hypothetical or labels cannot support an affordable claim |
| By about day 60 | Run the agreed pilot locally; build only the adapter/report capability it actually needs | Customer retains and reproduces evidence; record total effort and seek paid commitment | Evidence adds work without valued benefit, or refusal is unacceptable |
| By about day 90 | Repeat on a new release; standardize genuinely repeated work | Seek paid repeat use and another organization using substantially the same workflow | Every customer needs a different product or use is one-off |

Claude's requested next task remains packaging and installed-workflow repairs.
Codex's requested review role is independent reproduction, statistical/binding
checks and the evidence-contract proposal. These are suggested assignments;
only actual board acknowledgements establish who has accepted work. Use claimed
paths and separate worktrees; one owner per overlapping implementation area.

For each repair, keep a small commit with the regression, fix and directly
necessary contract update. State changed numerical outcomes in the body.
Append methodological decisions before runs. Generate scientific artifacts
only from clean source and commit them separately. Leave unrelated dirty
worktrees intact. A readable report is not permission to reopen or select on
the scientific test set.

## 9. Funding evidence and deliberate exclusions

An investor-facing package should eventually show a specific buyer/problem,
real retained customer evidence, paid repeat use, a measured workflow benefit,
delivery economics, referenceable users where permitted, and why the workflow
can repeat across organizations. Include the competitive alternatives and
reasons customers choose this product over their existing tools or scripts.

Maintain a claim ledger with artifact or interview provenance and scope for
every statement. Separate measured facts, customer statements and hypotheses.
No codebase size, test count, synthetic example, compliance crosswalk or
assurance from an AI assistant substitutes for that evidence. Funding remains
a separate uncertain outcome; these milestones make the case more assessable.

Potential longer-term advantages are repeatable domain protocols, reliable
integration, trusted review practice and accumulated workflow knowledge.
Cross-customer data reuse is not an assumed moat: customer permissions,
privacy and domain comparability may prevent it.

Defer a new gateway, general governance dashboard, foundation-model training,
many connectors, broad regulatory certification claims and hosted enterprise
features until a real workflow justifies them. Local customer operation reduces
the initial hosting burden. If hosting later becomes necessary, access control,
tenant isolation, retention, operational security and incident handling become
real product obligations rather than decorative sales features.

The immediate next deliverables are a genuinely installable package, reliable
statistical and lifecycle behavior, and evidence from real buyer conversations.
Preserve the work already done, repair the parts that can mislead, and let
observed customer use decide the next expansion.

## 10. Research limits and reproducibility

Primary documentation was reviewed on the date above. Vendor capabilities are
documented claims, not trial results; regulatory scope was checked against
official pages, with the RBI retrieval limitation stated explicitly. No market
size, competitor revenue, customer commitment, price or investment probability
was inferred from these sources. The proposed niche and milestones are judgments
to test, not measured market facts.

No production code or scientific artifact was changed for this plan. The
independent review carries the baseline test evidence and exact reproductions;
the repair brief carries implementation acceptance gates. This report adds
current research, prioritization and falsifiable next steps, not proof that
the outstanding defects have been fixed.
