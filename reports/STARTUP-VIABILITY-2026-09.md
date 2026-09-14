# Warrant startup viability

**Conclusion: do not scale or fundraise around the present broad proposition. Run a tightly bounded commercial validation programme around one recurring enterprise decision.** Warrant contains a credible technical foundation for an AI validation business. It does not yet establish a defensible, venture-scale company. The strongest possible business is independent evidence for releasing and changing AI applications; the weakest is selling a statistical certificate or the original activation probe as a standalone product.

This assessment concerns a global enterprise startup with no customer interviews, design partners, paid pilots, or revenue, as confirmed by the founder. Market and regulatory evidence was checked on 14 September 2026. Repository findings refer principally to committed revision **9a5336b**, with the monitoring-power correction under active development. Experimental results below are existing repository artifacts, not newly reproduced measurements. Business prices, commercial gates, and economic examples are explicitly proposed assumptions; they are not observed willingness to pay.

## 1. Investment judgment

The central problem is real: organisations deploy AI systems whose behaviour changes, whose outputs require judgment, and whose validation processes are expensive. The missing business evidence is whether a particular buyer will pay Warrant to solve a particular part of that problem, repeatedly, rather than use an existing platform, a consultant, or an internal script.

There is unusually relevant independent evidence for the problem. The Bank of England's February 2026 summary of industry roundtables reports deployment delays involving second-line risk functions, skills bottlenecks, concerns about whether traditional validation can scale to generative systems, and friction in procurement of third-party AI. Participants favoured more attention to testing and monitoring system outcomes. These are reported industry views, not proof that Warrant's proposed solution is the one firms want. [Bank of England roundtables][s1]

The market is also further developed than the repository's positioning suggests. ValidMind already provides model documentation, independent-validation workflows, monitoring, and evidence management. Its product documentation describes automatic workflows on threshold breaches and permanent attestation sign-offs. Warrant is entering an existing buying category, not creating an uncontested second layer above detectors. [ValidMind guides][s2], [breach workflows][s3], [attestations][s4]

| Question | Current judgment | Evidence needed to change it |
|---|---|---|
| Is there a consequential problem? | Yes, with credible external support | A specific customer's recent costly validation or release bottleneck |
| Is the prototype technically meaningful? | Yes, within narrow measured scopes | External statistical review and prospective production evaluation |
| Is willingness to pay established? | No | Paid pilots with a named budget owner |
| Is the differentiated feature set defensible? | Weak today | A repeatable advantage in total validation cost or decision quality |
| Is recurring usage established? | No | A second release or monitoring cycle that the customer actually buys |
| Is an enterprise deployment ready? | No | Customer-approved data, access, audit, integration, and support arrangements |
| Is venture scale demonstrated? | No | Repeatable sales, expansion, retention, and attractive delivery economics |

**The present evidence supports continued discovery, not a large platform build.** A pre-seed investor might still back the team or a compelling founder insight; neither can be evaluated from this repository. The code itself is not sufficient investment evidence.

## 2. The product that exists

The repository contains several potential businesses, which need to be separated.

The original experiment in **round1/** asks whether question-time activations predict subsequent answer errors. The current **controlplane/** package builds a broader evidence system: detector evaluation, scoped warrants, drift response, sampling, economics, policy composition, an action gate, and audit records. The customer CLI accepts labelled scores and supports certification, rechecking, and planning. It can therefore work with externally hosted models without needing their activations. [CLI](../controlplane/cli.py), [intake](../controlplane/intake/certify.py), [architecture](../docs/ARCHITECTURE.md)

Its useful design choices include explicit refusals when evidence is inadequate, separate precision and recall, a distinction between counted reviewed errors and estimated missed errors, declared sampling assumptions, and reproducible artifacts. These are valuable engineering and statistical practices. They are not evidence of customer demand or proprietary algorithms.

The commercially relevant distinction is between three promises:

1. **Measurement:** what performance was supported by this sample?
2. **Decision support:** is the evidence sufficient for this named use at this risk and review budget?
3. **Assurance:** who accepts the decision, under which process, and what happens when the evidence changes?

Warrant has substantial machinery for the first, parts of the second, and a prototype of the third. A global enterprise purchase is likely to depend heavily on the third.

### What the experiment establishes

The current last-token probe on the 600-item TriviaQA evaluation reports AUROC **0.8256 [0.7934, 0.8567]**, recall **0.0794 [0.0496, 0.1115]**, precision **0.8800 [0.7500, 1.0000]**, and flag rate **0.0417 [0.0267, 0.0583]**. These intervals are recorded in the validation artifact. This is evidence that the probe can concentrate errors in that setting. It is not evidence that it makes a deployed application acceptably safe. [Probe artifact](../results/validation-T1-last_token.json)

The transfer experiments are more commercially informative than the headline discrimination score: last-token features retain discrimination under the tested long-context change, while mean pooling deteriorates markedly. They demonstrate why evaluation needs a stated distribution and why the aggregation choice matters. They do not establish performance across model families, multilingual business tasks, retrieval pipelines, agents, or ordinary production changes. [Last-token transfer](../results/transfer-T1-last_token.json), [mean-pool transfer](../results/transfer-T1-mean_pool.json)

The on-traffic estimator is validated through simulation and a declared workload. Its report explicitly says it establishes no recall figure on real production traffic. The action gate uses declared scenarios rather than a labelled corpus of real agent actions. Both are useful mechanisms, but neither is a customer deployment. [On-traffic report](../results/on_traffic/ON_TRAFFIC.md), [gate report](../results/gate/GATE.md)

An earlier strategy document calls the probe the weakest detector in a matrix containing PII and injection tasks. That is not a sound ranking: recall on email recognition and recall on factual-answer errors concern different labels, datasets, and difficulties. Criticise the probe for its unproven commercial applicability and access requirements, not an invalid comparison across tasks. [Earlier strategy](STRATEGY-2026-09.md), [external matrix](../results/external/MATRIX.md)

## 3. The competitive landscape

The most important competitor is whichever system already owns the customer's evaluation data and approval workflow. It may be a software platform, a spreadsheet maintained by a validation team, or an established advisory firm.

The following entries describe documented offerings. They are not independently tested performance comparisons, and public documentation cannot establish that a vendor lacks a particular statistical feature.

| Competitor/category | Verified overlap | Consequence for Warrant |
|---|---|---|
| **ValidMind** | Validation reports, evidence, monitoring, workflow triggers, approval history | Closest competitor to the stated second-line validation proposition. A statistical module can fit inside its existing workflow. [Guides][s2], [triggers][s3] |
| **Credo AI** | AI inventory, risk assessment, policy mapping, evidence, integrations with operational systems | Governance and audit records are already sold as an enterprise platform. [Product][s5] |
| **ServiceNow AI Control Tower** | Enterprise AI management, risk and governance, links to existing business and technology assets | Existing distribution and enterprise records are a substantial advantage. Integrating is more plausible than replacing the platform. [Product][s6] |
| **Giskard** | AI-agent testing, scheduled evaluations, human review, enterprise deployment and access features | A customer asking for testing plus audit evidence already has alternatives. [Evaluation docs][s7], [plans][s8] |
| **Fiddler** | Agent/model evaluation, monitoring, guardrails, diagnosis and business-metric connections | Generic drift monitoring or guardrail validation is insufficient differentiation. [Platform][s9] |
| **Arize, Braintrust, LangSmith** | Evaluation and observability platforms with accessible entry plans | Developer adoption can be won by existing tools before Warrant reaches the buyer. [Arize][s10], [Braintrust][s11], [LangSmith][s12] |
| **Evidently and internal tooling** | Open-source reports, monitoring, custom metrics, and pass/fail tests | The alternative to buying can be a small extension of software already in use. [Repository][s13] |
| **Cloud guardrails** | Model-provider safeguards, monitoring interfaces, usage pricing | Both a low-cost substitute for some original checker savings and a possible target for independent validation. [AWS operation][s14], [pricing][s15] |

Public entry pricing reinforces the distinction between an evaluation feature and an enterprise workflow. Arize lists a **$50/month** Pro plan, Braintrust **$249/month**, and LangSmith **$39/seat/month**, with usage limits or additional usage charges and custom enterprise tiers. These are not like-for-like quotes for Warrant's proposed service and should not be treated as enterprise price ceilings. They do show that basic evaluation functionality is readily available. Prices are snapshots, not procurement quotes. [Arize pricing][s10], [Braintrust pricing][s11], [LangSmith pricing][s12]

ValidMind's published General Bank of Canada case reports a **70% reduction in validation time**. This is a vendor-published customer claim, not an independently audited outcome or a benchmark Warrant can assume. Its strategic relevance is the buying language: reduced validation work and easier scaling, rather than the novelty of a confidence interval. [ValidMind case study, page 15][s16]

AI security is also consolidating into larger platforms. Cisco acquired Robust Intelligence, and Check Point's financial disclosure records the completion of its Lakera acquisition in October 2025. These events support the existence of strategic interest in AI security. They do not imply an acquisition market for an unproven statistics tool, and neither acquisition should be used as a valuation comparable for Warrant. [Cisco][s17], [Check Point disclosure][s18]

### Refusal and tunability

Warrant's distinction between insufficient evidence and poor detector performance is useful. So is explaining that a detector with a few distinct score values cannot necessarily be adjusted to an arbitrary budget. Those can improve a customer's decision.

But an explicit refusal is not, by itself, a moat. Existing test systems can fail acceptance conditions, and workflow platforms can route failures for review. The specific statistical semantics may differ; that calls for a comparison on identical customer data, not a claim that competitors never say no.

The defensible opportunity, if one exists, is to deliver the whole decision with less customer effort: define a credible sample, obtain trustworthy labels, measure uncertainty, explain which promise failed, and place the evidence into the approval workflow. The mathematics alone is comparatively easy to reproduce.

## 4. Regulation and purchase urgency

Regulation can create work without creating a new software budget. An obligation to manage AI risk does not imply an obligation to buy detector false-positive certification. The buying case must connect a real requirement or internal policy to a named task that Warrant demonstrably improves.

| Jurisdiction/framework | Current primary-source position | Commercial implication |
|---|---|---|
| **European Union** | The Commission reports that the AI Omnibus entered into force on 27 July 2026. Relevant Annex III high-risk obligations apply from 2 December 2027; product-embedded high-risk rules from 2 August 2028. Other obligations have earlier application dates. | There is preparation work, but a pitch based on a universal imminent 2026 high-risk deadline is wrong. Application scope matters. [Commission][s19] |
| **US banking** | SR 26-2 supersedes SR 11-7. Its attached guidance explicitly excludes generative and agentic AI, while pointing firms to appropriate risk management and governance for tools outside its scope. Traditional and non-generative/non-agentic models remain covered. | Do not claim this guidance mandates Warrant for every LLM. Exclusion from this document is not exemption from all governance obligations. [Federal Reserve guidance][s20] |
| **UK banking** | Current SS1/23 includes independent validation and monitoring expectations for the specified firms in scope, particularly those with internal model approvals. Its scope is not all UK financial businesses. | A more concrete validation buyer exists, but the instrument supplies only part of a wider governance process. [PRA SS1/23][s21] |
| **NIST AI RMF** | NIST describes the framework as voluntary. | Alignment can support evidence organisation; it is not accreditation, legal approval, or an automatic purchase mandate. [NIST][s22] |

The UK evidence is especially useful because it identifies workflow friction without assuming a new law must first force demand. The later AI Consortium minutes also describe participants' interest in testing both whole AI systems and their components. Those minutes explicitly state that member views are not Bank/FCA policy. [AI Consortium minutes][s23]

Warrant should position an output as **evidence supporting an organisation's decision**. A command named “certify” and a status named “VALID” do not confer recognised external certification or transfer regulatory accountability. A buyer must know the scope, assumptions, responsible reviewer, and limits of every claim. The current repository itself says it issues no external certificate. [README](../README.md)

## 5. Technical risks that affect commercial credibility

These findings identify product risks from source inspection; they are not an exhaustive security audit or newly executed failure tests. They matter more to this business than ordinary prototype defects because the product sells confidence in evidence.

### 5.1 A false-positive promise is not a safety promise

The certification path calls the false-positive bound routine and returns VALID when it succeeds. It reports recall and precision but imposes no customer minimum-recall condition in that CLI path. A threshold that flags nothing can satisfy a false-positive requirement with sufficient evidence while being operationally useless. The underlying statistics module explicitly recognises the need for a separate recall floor. [Certification code](../controlplane/intake/certify.py), [statistics](../controlplane/validation/warrant_stats.py)

This is a scope issue, not a refutation of the bound. For an overblocking problem, an FPR bound may be exactly the wanted result. For PII leakage, harmful advice, or missed fraud, the buyer also needs evidence about misses and consequences. The paid product should make claim-specific states visible: FPR supported, recall insufficient, critical slice unmeasured, or release decision unresolved.

### 5.2 The easy input hides the hard part

A three-column CSV is an excellent interface, but independent, representative, correctly labelled data is not automatically available. Selecting only reviewed flags, clean benchmark negatives, or agreeable examples can produce a defensible calculation about the wrong population. Prompt content, relevant source documents, tool outcomes, policies, and reviewer disagreements may all be necessary to decide whether an answer is actually wrong.

The customer path can check file structure and duplicate IDs inside a file. It cannot establish from those columns alone that the sample is representative, the labels are correct, or the detector was not selected after seeing that same evidence. Warrant must either own a documented sampling and labelling process or clearly delimit its output to data supplied under customer attestations. “Bring your own labels” is a useful entry point, not proof that the data problem is solved. [Input contract](../controlplane/intake/contract.py)

### 5.3 Customer records are narrower than the research warrant type

The research Warrant type includes detector version, operating point, envelope, and expiry-related fields. The CLI CertificationResult payload does not provide that same lifecycle contract. It records a source file, counts, budget, threshold, metrics, and score histogram, with generic artifact provenance added by the writer. Recheck reads threshold, budget, alpha, and the histogram; it does not enforce a named detector/version binding or the research warrant's expiry policy. [Research type](../controlplane/model/warrant.py), [CLI record](../controlplane/intake/certify.py), [CLI consumer](../controlplane/cli.py)

Consequently the simplest customer workflow should not yet be marketed as the complete time-bounded enterprise warrant system. A real product needs identity, scope and change tracking across detector, generator, prompt, retrieval corpus, policy, tools, and labelling rubric. It also needs a clear rule for when evidence must be refreshed.

### 5.4 Group-aware certification does not carry through the inspected recheck

Certification takes account of supplied groups and rejects unsupported cluster shapes. In the inspected recheck function, “labels, scores, _ = items.as_arrays()” discards groups, and binomial bounds use the number of negative rows. Repeated items from one customer or conversation could therefore be treated as independent during monitoring even though the certification path recognises their dependence. This needs a targeted statistical and regression review before production reliance. [Certification](../controlplane/intake/certify.py), [recheck](../controlplane/intake/recheck.py)

### 5.5 Repeated monitoring spends more than a single-test error budget

Decision 183 correctly identifies that the old planning quantity did not express a desired probability of detecting a true breach, and that repeated checks compound false-revocation risk. Power-based planning is being implemented. That correction should be completed and reviewed, but reporting an annual false-alarm probability does not by itself control it. The separate anytime-valid FPRMonitor is not the same as preserving a sequential error guarantee across customer CLI recheck records. [Decision 183](../DECISIONS.md), [FPRMonitor](../controlplane/validation/warrant_stats.py)

The product needs an explicit choice: a predeclared finite testing schedule with appropriate error allocation, or a suitable sequential procedure with persisted state. Either approach must state the assumptions on dependence, sampling, label delay, and detector changes. Time-to-detection and false alarms belong in the commercial promise alongside sample size.

### 5.6 Stable scores do not prove stable correctness

The research drift envelope currently measures token length; the CLI compares score distributions. A system can keep the same lengths and score histogram while its relation to the labels deteriorates. A different shift can change a histogram without making the task materially worse. Drift is a reason to investigate or remeasure, not a substitute for outcome labels. [Envelope construction](../controlplane/validation/runner.py), [recheck](../controlplane/intake/recheck.py), [limitations](../docs/LIMITATIONS.md)

### 5.7 A paid assurance workflow needs operational trust

The repository has good provenance and an audit-store mechanism. It does not establish enterprise tenancy, authentication, role separation, secure deployment, incident response, retention governance, or independent audit acceptance. A hash chain detects certain alterations relative to a trusted history; it does not authenticate ground truth or create an external trust anchor by itself. Research controls and numerous tests do not replace these capabilities.

The cheapest first deployment is therefore a bounded offline evaluation in a customer-approved environment. Build broader access and hosting infrastructure only against an actual buyer's requirements. The existing documentary contradictions are nevertheless worth fixing early: selling evidence integrity while the README and proposal disagree with the code is a preventable credibility loss.

## 6. Economics

The governing commercial equation is:

**Customer value = validation labour saved + defensible release/procurement value + evidenced reduction in operational loss − software fee − incremental labels − integration and operating cost.**

Each term needs measurement. Avoid multiplying a theoretical fine or a hypothetical catastrophe by an invented probability. Avoid counting the entire value of a customer's AI deployment as value created by Warrant.

### Cheap computation changes the original proposition

AWS lists contextual grounding at **$0.10 per 1,000 text units**; a unit is up to 1,000 characters, and the billed text includes the reference source, query, and response. These checks are not equivalent to a human review or every expensive judge. They do show why checker cost must be established rather than assumed. [AWS pricing][s15]

**Illustrative scenario, not measured Warrant savings:** at one million interactions per month and ten text units per interaction, that one check costs $1,000/month. Even skipping 95% of those checks saves at most $950/month before probe, integration, monitoring, and additional error costs. The original probe experiment does not establish that skipping them preserves the customer's required outcomes. Selling a substantial enterprise subscription solely on this scenario's inference savings would be difficult.

The stronger opportunity is expensive human judgment and release work. However, Warrant can increase that bill when it introduces random sampling of previously unreviewed traffic. The relevant comparator is the customer's actual acceptable process, not a hypothetical system that sends everything to a human.

### Rare events make evidence expensive

For zero observed false positives in independent negatives, the one-sided binomial upper bound is:

**upper bound = 1 − alpha^(1/n).**

At alpha = 0.05, requiring that bound to be at most budget b gives:

**n = ceiling(log(0.05) / log(1 − b)).**

| FPR budget | Independent clean negatives required with zero observed false positives |
|---|---:|
| 5% | 59 |
| 1% | 299 |
| 0.1% | 2,995 |
| 0.01% | 29,956 |

These are calculated zero-event sample requirements under the stated model, not complete evaluation sizes. They say nothing about recall, include no slice-wise or repeated-testing adjustment, and do not replace representative sampling. The formula is also the basis of the repository's minimum-sample routine. [Statistics implementation](../controlplane/validation/warrant_stats.py), [calculation inputs and outputs](STARTUP-VIABILITY-2026-09.scenarios.json)

For a separate illustrative incident prevalence of 0.1%, a random sample of 1,000 independent items has about a **36.8%** chance of containing no incidents: (1 − 0.001)^1000. A safety promise about rare events cannot be inferred from a small reassuring sample. Targeted challenge sets can find failure modes, but their class proportions do not establish production incident rates.

This creates a commercial boundary. Warrant can be economical for recurring quality validation with accessible labels. It is a much less credible first product for extremely rare catastrophic failures requiring very tight guarantees.

### Labelling savings do not automatically justify a subscription

Consider these **declared planning assumptions**, all in USD:

- Existing process reviews 2,000 items/month.
- Warrant reduces that to 1,000 items/month at equivalent required decision quality.
- Each review takes three minutes; loaded reviewer cost is $40/hour.
- Annual software fee is $30,000.

Annual label savings are (2,000 − 1,000) × 12 × 3/60 × $40 = **$24,000**. The customer is **$6,000 worse off** after the software fee, before integration. A substantial reduction in review count can therefore still fail the buying case.

The comparison becomes favourable only if there are more savings, higher-value reviewer time, meaningful avoided rework, or an attributable release/procurement benefit. Equivalence of decision quality is an assumption to test, not a free benefit. [Scenario calculations](STARTUP-VIABILITY-2026-09.scenarios.json)

### Owning the labels changes gross margin

If Warrant sells software and customers supply reviewers, reviewer cost is the customer's cost. If Warrant sells a managed validation outcome and provides those reviewers, it becomes delivery cost. Do not describe the second arrangement as software margins simply because software performs the arithmetic.

An illustrative $60,000 annual managed contract with 1,000 labels/month at the preceding rates has:

| Direct annual delivery item | Declared assumption | Cost |
|---|---|---:|
| Labels | 600 hours × $40 | $24,000 |
| Onboarding | 60 hours × $75 | $4,500 |
| Support | 24 hours × $100 | $2,400 |
| Infrastructure | Fixed assumption | $1,200 |
| **Total direct cost** | Sum | **$32,100** |
| **Gross profit / margin** | $60,000 less direct cost | **$27,900 / 46.5%** |

This excludes acquisition costs, research, general overhead, and extra adjudication or security work. It is an example of how a useful business becomes a labour-heavy service rather than scalable software. Conversely, initially providing a service can be sensible if it teaches the team which work repeats and what can actually be automated. [Scenario calculations](STARTUP-VIABILITY-2026-09.scenarios.json)

### Venture-scale revenue requires a repeatable market

No reliable market size for Warrant's specific offering is established by the available evidence. Broad AI-governance forecasts combine inventories, consulting, cybersecurity, monitoring and compliance software; treating that total as an addressable market for FPR certification would be misleading.

Work backwards from customers instead:

| Hypothetical annual recurring revenue per customer | Customers for at least $10m ARR | Customers for at least $100m ARR |
|---|---:|---:|
| $30,000 | 334 | 3,334 |
| $60,000 | 167 | 1,667 |
| $100,000 | 100 | 1,000 |

This is arithmetic, not a forecast or claim that these prices are attainable. A handful of bespoke bank projects could make a good specialist business without supporting the founder's venture-scale objective. The research task after initial pilots is to identify a sufficiently large list of qualified accounts, recurring workloads, expansion paths, and a sales process that reaches them economically.

## 7. Recommended initial market

**Start with B2B AI customer-support vendors selling into financial services, with existing customer deployments and an existing human QA process.** Sell a bounded release/change-validation package to the vendor's head of AI quality or engineering, with the financial institution's risk reviewer involved in defining what evidence is acceptable.

This is a hypothesis, not a claim of an uncontested segment. It is preferable to starting with a global bank-wide risk platform because it places the first sale near a concrete event: an enterprise pilot, model change, or release cannot proceed until someone can defend the quality evidence. Existing QA makes labels and a labour baseline more attainable. An enterprise customer's reviewer provides a test of whether the output matters outside the vendor's engineering team.

The first offer could read:

**“We evaluate whether your next support-AI release meets the agreed quality and review limits on your customer's traffic, and produce the evidence their reviewer needs. We show the unresolved cases and the cost of resolving them.”**

This is a proposed offer, not a claim that the current CLI delivers the complete service. Avoid “we certify your AI is safe” and “we know when an LLM will hallucinate.” The first is too broad; the second ties the business to a limited experiment.

| Buying role | Likely concern to test in interviews | Proof required |
|---|---|---|
| Head of AI quality / engineering | Release evaluation takes too much staff time | Measured labour and elapsed-time comparison |
| CTO / engineering budget owner | Cost and deployment impact | Paid trial with explicit annual purchasing conditions |
| Financial institution's risk reviewer | Evidence is relevant, independent and reviewable | Agreement on rubric, sampling, limitations, and acceptance format |
| Security / privacy approver | Access to customer conversations and records | Approved local processing, access and retention arrangements |
| Existing platform owner | Another tool creates duplicate work | One usable export/integration and a defined system of record |

A vendor paying for the assessment creates an independence question. Preserve predeclared criteria, visibility of failures, separation of the evaluator from release incentives, and the customer's authority over acceptance. Payment should be for performing a valid assessment, never for issuing a favourable result.

Alternatives should be tested but not built simultaneously. Direct sales to a bank's second-line function may support larger contracts but impose greater trust, integration, and procurement demands. Advisory firms may provide distribution but capture margin and keep Warrant invisible. A cheap developer tool may grow usage while never reaching a price that supports enterprise selling.

## 8. Potential defensibility

Statistical calibration and risk control are established fields. Learn then Test already describes model-agnostic calibration with finite-sample risk guarantees. Stratified Prediction-Powered Inference studies combining human labels, automatic ratings and stratification to improve uncertainty estimates. These are relevant comparison methods, not proof that either implementation automatically solves Warrant's production task. They weaken a claim that generic calibration or sample-efficiency mathematics is proprietary. [Learn then Test][s24], [StratPPI][s25]

Open-source code and transparent derivations can help establish trust and adoption. Under this strategy, value would have to accumulate elsewhere:

- **Accepted workflow:** reviewers repeatedly use the evidence in real decisions, and changing tools disrupts a documented process.
- **Task-specific operating knowledge:** stable label rubrics, hard cases, adjudication procedures and integration knowledge for one class of customer work.
- **Demonstrated evaluation efficiency:** fewer labels or less expert time at a comparable, externally reviewed level of evidence.
- **Longitudinal evidence:** customer-specific histories of versions, changes, failures and resolutions.
- **Distribution:** repeatable access to buyers through platform integrations, trusted validation partners or satisfied customers.

None is a moat yet. Customer data is not automatically reusable across clients, and privacy or contractual restrictions can prevent the hoped-for data advantage. Any cross-customer benefit needs explicit rights and demonstrated task comparability. A company's accumulated evidence is valuable to that company even when it cannot become a shared training dataset.

Public benchmarks can support credibility but are not a sufficient market entry strategy. REDACT already supplies a substantial multilingual PII benchmark and evaluation harness. A contribution or a better analysis might attract users; citations are not purchases. Do not resurrect the earlier claim that an empty Indian-PII benchmark category guarantees a business. [REDACT][s26], [earlier corrected strategy](STRATEGY-2026-09.md)

## 9. A bounded commercial validation programme

The following is a proposed **90-day decision process**, with deliberately explicit gates. The counts, prices and thresholds are management choices to be agreed before observing results, not statistical estimates of startup success.

### Days 1–30: verify a purchase event

Conduct 20 interviews focused on recent behaviour: AI-support vendors, financial-services validation/QA leads, and a small number of practitioners who have approved enterprise deployments. Ask about the last delayed release, the people involved, the data they used, the time spent, the tools already purchased, and who could approve a paid evaluation.

Request an anonymised example of the current review output and its acceptance criteria. Identify what exact additional evidence would change the decision. Ask whether they can provide representative samples and reviewers; a budget without usable data is not a workable pilot.

**Gate:** at least five organisations describe the same recurring bottleneck with a named owner, and three can offer customer-approved data plus a reviewer. Positive comments about the idea, survey interest and unsigned expressions of intent do not satisfy this gate.

### Days 31–60: sell one fixed-scope assessment

Offer a paid, bounded assessment at a **proposed $10,000–$20,000** fee, subject to customer response. Price is a hypothesis. Specify the task, data scope, reviewer responsibilities, refusal conditions, expected deliverables, and what another evaluation cycle would cost.

Freeze the evaluated system version and acceptance criteria. Separate data used to develop/select the detector from evidence used to substantiate the selected procedure. Distinguish representative estimation samples from targeted challenge cases. Preserve groups and all unresolved label decisions.

Use the customer's current process as the baseline. Compare total expert time, labels, elapsed days, evidence completeness, and whether the named reviewer accepts the output. Include an appropriate established statistical baseline where the claim is sample efficiency.

**Gate:** two organisations pay meaningful pilot fees, and their designated reviewers agree the outputs are usable for a real decision. A technically successful free demo is insufficient.

### Days 61–90: test recurrence and delivery economics

Run a second version, a scheduled refresh, or a meaningful change for at least one pilot customer. Integrate with one existing workflow tool only where necessary. Record delivery hours by task so the team can distinguish reusable software from consulting.

Use a **proposed $30,000–$60,000 annual contract hypothesis** for repeated use. It is not a market benchmark. Record the buyer's willingness to pay rather than silently discounting until a nominal sale occurs.

**Continue criterion:** at least one paid renewal/annual conversion plus a paid second cycle or explicit procurement progression at the other pilot; a customer-accepted improvement in a named bottleneck; and a credible path to product delivery without proportional growth in expert labour.

For a numerical efficiency claim, predeclare a practical target such as **30% less total expert effort**, while maintaining the customer's required evidence standard. It is a commercial gate, not a claim that the product currently achieves it. A material release/procurement benefit can be an alternative, but it must be confirmed by the decision owner and not invented from a hypothetical deal value.

### Stop or change direction if

- Buyers cannot name a task or budget beyond general concern about AI risk.
- Data and label access prevent a valid evaluation after a sustained attempt.
- Customers want only one-off reports and will not purchase a second cycle.
- An existing platform plus a small internal script satisfies the requirement.
- The calculation is cheap but obtaining credible labels consumes all customer value.
- Acceptance requires an accredited or established assurance provider that the team cannot realistically partner with.
- Every customer needs a different bespoke methodology and substantial ongoing founder delivery.

Failure at these gates would reject the current venture thesis, not invalidate the research. A specialist consultancy, an open-source project, or a module sold through an existing vendor could still be worthwhile outcomes.

## 10. What to build and what to defer

Before a paid pilot, finish the customer-facing statistical contract: scoped claims, appropriate group treatment, identity/version binding, expiry and refresh semantics, and a clearly specified repeated-testing procedure. Obtain independent review of the procedures that produce bounds and sample sizes. Reconcile the main public description with the implementation.

Then build only the sampling, label adjudication and export work required by the chosen customer's release decision. Keep detector choice open: the probe is one possible input, not a mandatory foundation.

Defer a universal governance platform, a new gateway, a general autonomous-agent security product, a broad public benchmark programme, and integrations without a committed user. These are different products with different buyers and evidence burdens. The repository already demonstrates substantial execution capacity; more breadth would currently conceal the unresolved demand question.

## 11. Final conclusion

**Warrant is technically credible enough to earn serious customer conversations, but commercially unproven and insufficiently differentiated to justify the current venture-scale ambition on its existing evidence.**

The strongest asset is the team's ability to make uncertain measurements explicit, reproduce them, and expose invalid assumptions. The central weakness is that this capability has not been tied to a repeated purchasing decision. The buyer does not primarily want a bound; the buyer wants to complete a consequential task with less effort and acceptable risk.

There is a plausible company inside this work: a focused validation service that becomes software for recurring release and change decisions. There is also a plausible outcome in which the useful parts belong inside an existing evaluation or governance platform. Public research cannot distinguish those outcomes; paid customer behaviour can.

**Recommendation: proceed with the bounded commercial test, decline the broad platform build, and require paid recurrence before treating Warrant as a venture-scale startup.** If customers will not buy the narrow, useful decision service, a more elaborate warrant system is unlikely to fix the problem.

## Sources and evidence limits

Sources were accessed on 14 September 2026. Current product pages describe vendor offerings, not independently verified service quality. Historical surveys retain their stated dates and populations. No customer interviews were conducted for this report; the absence of commercial traction was supplied by the founder. No live vendor trials or procurement quotes were obtained. Repository tests and experiments were not rerun; the working tree was changing during inspection.

Calculated scenarios are provided in [STARTUP-VIABILITY-2026-09.scenarios.json](STARTUP-VIABILITY-2026-09.scenarios.json). Monetary inputs are declared USD assumptions. Sample requirements and rare-event probabilities follow the displayed binomial formulas; they are not production estimates or modifications to the repository's experiment results.

1. **Bank of England.** [Summary of AI roundtables — February 2026][s1]. Published 16 February 2026; discussions in late 2025. Industry-reported deployment and procurement friction; not a spending survey.
2. **ValidMind.** [Guides][s2]. Published 28 August 2026. Product workflow and integration documentation.
3. **ValidMind.** [Trigger workflows on threshold breach][s3]. Published 28 August 2026. Automatic workflow behaviour following logged metric failures.
4. **ValidMind.** [Approve attestations][s4]. Published 28 August 2026. Permanent sign-off history.
5. **Credo AI.** [Product/platform overview][s5]. Current vendor page. Inventory, policy, evidence and integration offering.
6. **ServiceNow.** [AI Control Tower][s6]. Current vendor page. Enterprise governance, management and pricing approach. Announced future enhancements are not treated as confirmed deployed features.
7. **Giskard.** [AI Agent Evaluation][s7]. Current documentation. Local, remote and scheduled evaluation.
8. **Giskard.** [Pricing and plans][s8]. Current vendor page. Enterprise testing, review and deployment features; no public enterprise quote assumed.
9. **Fiddler.** [AI Observability and Security Platform][s9]. Current vendor page. Evaluation, monitoring and governance overlap.
10. **Arize.** [AX pricing][s10]. Current public plan prices and limits.
11. **Braintrust.** [Pricing][s11]. Current public plan prices and limits.
12. **LangChain.** [LangSmith plans and pricing][s12]. Current per-seat and usage structure.
13. **Evidently AI.** [Evidently repository][s13]. Current public implementation and documentation of reports, tests and monitoring.
14. **AWS.** [How Amazon Bedrock Guardrails works][s14]. Current documentation; includes the recommendation to continue validating guardrails as underlying models change.
15. **AWS.** [Amazon Bedrock pricing — Guardrails section][s15]. Current unit pricing and billed-text definition.
16. **ValidMind.** [Product brief; General Bank of Canada case, PDF page 15][s16]. Hosted under June 2025. Vendor-reported outcome, not independently audited.
17. **Cisco.** [Robust Intelligence acquisition announcement and completion update][s17]. August 2024 announcement, September 2024 completion update on that page. Evidence of consolidation; no valuation inference.
18. **Check Point.** [Third-quarter 2025 financial results][s18]. Records Lakera acquisition closing on 22 October 2025.
19. **European Commission.** [AI Act][s19]. Updated 3 August 2026. Application timetable and AI Omnibus status.
20. **Federal Reserve, OCC and FDIC.** [SR 26-2 attachment: Revised Guidance on Model Risk Management][s20]. 17 April 2026; scope exclusion in footnote 3. See also the [supervisory letter](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm).
21. **Prudential Regulation Authority.** [SS1/23: Model risk management principles for banks][s21]. April 2026 version. Scope and independent-validation expectations.
22. **NIST.** [AI Risk Management Framework][s22]. Current official overview. Voluntary character and related profiles.
23. **Bank of England/FCA AI Consortium.** [June 2026 meeting minutes][s23]. Meeting 3 June, published 5 August 2026. Member views; explicitly not regulatory policy.
24. **Angelopoulos, Bates, Candès, Jordan and Lei.** [Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control][s24]. First submitted 2021; version cited revised 29 September 2022. Prior statistical methodology.
25. **Fisch, Maynez, Hofer, Dhingra, Globerson and Cohen.** [Stratified Prediction-Powered Inference for Hybrid Language Model Evaluation][s25]. June 2024; revised December 2024. Prior work on human-label efficiency.
26. **Vats and colleagues.** [REDACT: A Systematically Controlled Multilingual Benchmark for Personal Information Detection][s26]. Submitted 18 June 2026. Public benchmark and evaluation harness.
27. **Warrant repository.** Committed revision 9a5336b; linked code, results, limitations and decision log. Direct source for implementation and recorded experimental evidence.
28. **Founder statement.** 14 September 2026, private conversation. Global enterprise/venture-scale objective; no commercial evidence yet.

[s1]: https://www.bankofengland.co.uk/minutes/2026/february/summary-of-ai-roundtables-feb-2026
[s2]: https://docs.validmind.com/guide/guides.html
[s3]: https://docs.validmind.com/guide/monitoring/trigger-workflows-on-threshold-breach.html
[s4]: https://docs.validmind.com/guide/attestation/approve-attestations.html
[s5]: https://www.credo.ai/
[s6]: https://www.servicenow.com/products/ai-control-tower.html
[s7]: https://docs.giskard.ai/hub/ui/evaluations
[s8]: https://www.giskard.ai/pricing
[s9]: https://www.fiddler.ai/ai-observability
[s10]: https://arize.com/pricing/
[s11]: https://www.braintrust.dev/pricing
[s12]: https://www.langchain.com/pricing
[s13]: https://github.com/evidentlyai/evidently
[s14]: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-how.html
[s15]: https://aws.amazon.com/bedrock/pricing/
[s16]: https://validmind.com/wp-content/uploads/2025/06/VM-Product-Brief-Web-v2-1.pdf
[s17]: https://blogs.cisco.com/news/fortifying-the-future-of-security-for-ai-cisco-announces-intent-to-acquire-robust-intelligence
[s18]: https://www.checkpoint.com/downloads/investor/check-point-software-third-quarter-2025-financial-results.pdf?v=1.1
[s19]: https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
[s20]: https://www.federalreserve.gov/supervisionreg/srletters/SR2602a1.pdf
[s21]: https://www.bankofengland.co.uk/-/media/boe/files/prudential-regulation/supervisory-statement/2026/liaf0126app5.pdf
[s22]: https://www.nist.gov/itl/ai-risk-management-framework
[s23]: https://www.bankofengland.co.uk/minutes/2026/june/ai-consortium-minutes-3-june-2026
[s24]: https://arxiv.org/abs/2110.01052
[s25]: https://arxiv.org/abs/2406.04291
[s26]: https://arxiv.org/abs/2606.19881
