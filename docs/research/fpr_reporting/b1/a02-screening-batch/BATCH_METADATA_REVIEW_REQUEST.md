# Consolidated B1 metadata review: all current questions

177 provisional work-record domain questions and two bibliographic identity questions.
Palisade is Q001. Prior human decisions001--004 remain recorded; no repeat review requested.
Read the duplicate questions first: D01 may let one source review answer two domain rows.

This is a feasibility-pilot domain screen within the arXiv/ACL-retrieved frame,
not the six selected papers' independent outcome extraction. No papers have been drawn.
Use only bibliographic and method/dataset sections. Do not return performance/FPR
results, sample/false-positive counts, assurance classifications or an outcome sheet.

For each Q row return INCLUDE / EXCLUDE / UNCLEAR, reviewed version URL, section/page
locator, brief method rationale and any limitation. English-only purity is not required:
state precisely whether English evaluation is supported directly, indirectly, or not
established. Do not infer English evaluation from encoder name or paper prose alone.
If a T/B/P requirement fails, a supported EXCLUDE resolves the row without further
language work. Existing missing facts remain UNCLEAR; do not guess.

Return one combined reply or fill BATCH_METADATA_ANSWERS_BLANK.json; its answer cells
are blank. Evidence can be shared by explicit IDs, but each decision needs source support.
Links are captured bibliographic locators, not finalized cutoff-selected versions.
All domain inclusions still need locked version, sentinel and other eligibility checks.

## Required evidence codes

- **L**: English-text evaluation: cite dataset/method evidence; note indirect support or mixed-language limitations.
- **T**: Separate binary injected-instruction input evaluation, rather than harmful-content/jailbreak, end-to-end success, or another security task alone.
- **P**: Decision before the downstream target LLM answers; distinguish auxiliary detector generation from target-response-dependent evidence.
- **B**: Qualifying binary prompt/document input decision, rather than only token/step/multiclass labels; identify any separately evaluated binary stratum.

## Bibliographic identity questions

### D01

Shared NotInject benchmark and MOF method in captured abstracts; overlapping named authors, differing title/author lists. No identity mapping asserted.

SAME_WORK / DISTINCT_WORKS / UNCLEAR, with primary bibliographic evidence and canonical/version links; no results needed.

- `arxiv:2410.22770`: [InjecGuard: Benchmarking and Mitigating Over-defense in Prompt Injection Guardrail Models](http://arxiv.org/abs/2410.22770v3)
- `doi:10.18653/v1/2025.acl-long.1468`: [PIGuard: Prompt Injection Guardrail via Mitigating Overdefense for Free](https://aclanthology.org/2025.acl-long.1468/)

### D02

Overlapping author lists and closely related seven-client MCP/tool-poisoning assessments, but different titles/author lists. Both currently domain-excluded; identity still unasserted.

SAME_WORK / DISTINCT_WORKS / UNCLEAR, with primary bibliographic evidence and canonical/version links; no results needed.

- `arxiv:2603.21642`: [Are AI-assisted Development Tools Immune to Prompt Injection?](http://arxiv.org/abs/2603.21642v1)
- `arxiv:2603.22489`: [Model Context Protocol Threat Modeling and Analyzing Vulnerabilities to Prompt Injection with Tool Poisoning](http://arxiv.org/abs/2603.22489v1)

## Domain questions

Grouped by required evidence; IDs follow the locked sorted-work order.

### L: 41 records

| Review | Work and captured source | Required clarification |
| --- | --- | --- |
| Q001 | `arxiv:2410.21146` — [Palisade -- Prompt Injection Detection Framework](http://arxiv.org/abs/2410.21146v1) | Abstract establishes layered prompt-injection input screening using rules, an ML classifier and a companion LLM before the target model. It does not establish the English-language evaluation setting. |
| Q002 | `arxiv:2410.21337` — [Fine-tuned Large Language Models (LLMs): Improved Prompt Injection Attacks Detection](http://arxiv.org/abs/2410.21337v2) | Binary prompt-injection classification is described; evaluation language is unstated. |
| Q003 | `arxiv:2410.22284` — [Embedding-based classifiers can detect prompt injection attacks](http://arxiv.org/abs/2410.22284v1) | Embedding-based malicious/benign input classification is described; evaluation language is unstated. |
| Q004 | `arxiv:2410.22770` — [InjecGuard: Benchmarking and Mitigating Over-defense in Prompt Injection Guardrail Models](http://arxiv.org/abs/2410.22770v3) | Prompt-injection guard-model evaluation is described; evaluation language is unstated. |
| Q006 | `arxiv:2501.15145` — [PromptShield: Deployable Detection for Prompt Injection Attacks](http://arxiv.org/abs/2501.15145v2) | Prompt-injection detectors are evaluated; English setting is unstated. |
| Q012 | `arxiv:2504.11358` — [DataSentinel: A Game-Theoretic Detection of Prompt Injection Attacks](http://arxiv.org/abs/2504.11358v4) | Binary injected-input detector is described; English setting is unstated. |
| Q015 | `arxiv:2505.12368` — [CAPTURE: Context-Aware Prompt Injection Testing and Robustness Enhancement](https://aclanthology.org/2025.llmsec-1.13/) | Context-aware binary injection guard-model evaluation is described; English setting is unstated. |
| Q016 | `arxiv:2506.05446` — [Sentinel: SOTA model to protect against prompt injections](http://arxiv.org/abs/2506.05446v1) | Binary injection/benign detector evaluation is described; English setting is unstated. |
| Q017 | `arxiv:2506.06384` — [Detection Method for Prompt Injection by Integrating Pre-trained Model and Heuristic Feature Engineering](http://arxiv.org/abs/2506.06384v1) | Input-text feature-fusion injection classifier is described; English setting is unstated. |
| Q021 | `arxiv:2507.05630` — [How Not to Detect Prompt Injections with an LLM](http://arxiv.org/abs/2507.05630v3) | Known-answer schemes classify clean versus injected input through an auxiliary detector; English setting is unstated. |
| Q023 | `arxiv:2507.15219` — [PromptArmor: Simple yet Effective Prompt Injection Defenses](http://arxiv.org/abs/2507.15219v1) | Detects/removes injected instructions before agent processing; English setting is unstated. |
| Q029 | `arxiv:2508.20890` — [PromptSleuth: Detecting Prompt Injection via Semantic Intent Invariance](http://arxiv.org/abs/2508.20890v2) | Intent-based prompt-injection detector evaluation is described; English setting is unstated. |
| Q036 | `arxiv:2510.01354` — [WAInjectBench: Benchmarking Prompt Injection Detections for Web Agents](http://arxiv.org/abs/2510.01354v2) | Separate text attack/benign detection evaluation is described alongside images; English setting is unstated. |
| Q040 | `arxiv:2510.14005` — [PIShield: Detecting Prompt Injection Attacks via Intrinsic LLM Features](http://arxiv.org/abs/2510.14005v3) | Input-representation classifier explicitly avoids response generation; English setting is unstated. |
| Q048 | `arxiv:2512.12583` — [Detecting Prompt Injection Attacks Against Application Using Classifiers](http://arxiv.org/abs/2512.12583v1) | HackAPrompt input-injection classifiers are trained/evaluated; English setting is unstated. |
| Q052 | `arxiv:2601.12359` — [Zero-Shot Embedding Drift Detection: A Lightweight Defense Against Prompt Injections in LLMs](http://arxiv.org/abs/2601.12359v1) | Input embedding drift classifier evaluated on injection inputs; English setting is unstated. |
| Q053 | `arxiv:2601.19051` — [Proactive Hardening of LLM Defenses with HASTE](http://arxiv.org/abs/2601.19051v1) | Adaptive hard-negative training of injection detectors is evaluated; English setting is unstated. |
| Q055 | `arxiv:2602.01795` — [RedVisor: Reasoning-Aware Prompt Injection Defense via Zero-Copy KV Cache Reuse](http://arxiv.org/abs/2602.01795v1) | Detection analysis precedes final backbone response; English setting is unstated. |
| Q056 | `arxiv:2602.03792` — [WebSentinel: Detecting and Localizing Prompt Injection Attacks for Web Agents](http://arxiv.org/abs/2602.03792v1) | Detects/localizes injection in webpage input; English setting is unstated. |
| Q065 | `arxiv:2603.11875` — [The Mirror Design Pattern: Strict Data Geometry over Model Scale for Prompt Injection Detection](http://arxiv.org/abs/2603.11875v2) | First-layer character n-gram binary injection classifier evaluated; English setting is unstated. |
| Q066 | `arxiv:2603.18433` — [Prompt Control-Flow Integrity: A Priority-Aware Runtime Defense Against Prompt Injection in LLM Systems](http://arxiv.org/abs/2603.18433v1) | Request classifier/enforcement precedes backend model; English setting is unstated. |
| Q086 | `arxiv:2605.00460` — [CleanBase: Detecting Malicious Documents in RAG Knowledge Databases](http://arxiv.org/abs/2605.00460v1) | Detects injected documents before RAG retrieval; English setting is unstated. |
| Q093 | `arxiv:2605.18918` — [ESLD (External Surrogate Latent Defense): A Latent-Space Architecture for Faster, Stronger Prompt-Injection Defense](http://arxiv.org/abs/2605.18918v1) | Latent guard produces input verdict before assistant acts; English setting is unstated. |
| Q096 | `arxiv:2605.26999` — [Prompt Injection Detection is Regime-Dependent: A Deployment-Aware Evaluation with Interpretable Structural Signals](http://arxiv.org/abs/2605.26999v1) | Input prompt-injection classifiers evaluated across regimes; English setting is unstated. |
| Q099 | `arxiv:2605.30189` — [Token-Level Generalization in LoRA Adapter Backdoors: Attack Characterization and Behavioral Detection](http://arxiv.org/abs/2605.30189v1) | Backdoor robustness of prompt-injection input classifier; English setting is unstated. |
| Q101 | `arxiv:2605.30837` — [Send a SCOUT First: Pre-hoc Reasoning for Adaptive Detector Allocation in Prompt-Injection Defense](http://arxiv.org/abs/2605.30837v3) | Chooses among input-injection detectors per input; English setting is unstated. |
| Q115 | `arxiv:2606.19660` — [A Layered Security Framework Against Prompt Injection in RAG-Based Chatbots](http://arxiv.org/abs/2606.19660v2) | Layered system has an input injection classifier before inference; English setting is unstated. |
| Q117 | `arxiv:2606.22659` — [Confidently Wrong: Severity-Aware Calibration of Prompt-Injection Detectors under Attack Shift](http://arxiv.org/abs/2606.22659v1) | Scores input injection detectors under attack shift; English setting is unstated. |
| Q125 | `arxiv:2607.19396` — [CrackedPDFs: A Controlled Benchmark for Hidden Prompt Injection in PDFs](http://arxiv.org/abs/2607.19396v2) | Malicious/benign document input detector is evaluated; English setting is unstated. |
| Q132 | `arxiv:2608.26423` — [The Latent Diagnostic Taxonomy: A Framework for Constructing Classifiers and Diagnosing Their Decisions, Applied to Prompt Injection Detection](http://arxiv.org/abs/2608.26423v2) | Prompt-injection safeguard classifier/diagnostic is evaluated; English setting is unstated. |
| Q136 | `arxiv:2609.05074` — [Influence Score and Transformers interpretability: Measure of the Effective Impact of Attention Heads at inference time](http://arxiv.org/abs/2609.05074v1) | Interpretability study of input-injection DeBERTa classifier; English setting is unstated. |
| Q141 | `arxiv:2609.24801` — [Decoding Guardrails: XAI-Guided Perturbation Analysis of Prompt Injection Detection](http://arxiv.org/abs/2609.24801v1) | Saliency/perturbation evaluation of input injection classifier; English setting is unstated. |
| Q144 | `arxiv:2609.33401` — [Evaluating System One Models for Agent Security Decisions: Reliability, Calibration, and Selective Automation](http://arxiv.org/abs/2609.33401v3) | Separately evaluates injection screening before agents act; English setting is unstated. |
| Q151 | `arxiv:2610.03448` — [Passing the Test You Trained On: Re-evaluating Prompt-Injection Detectors for LLM Agents](http://arxiv.org/abs/2610.03448v1) | Benchmarks injection detectors on replayed tool-output inputs; English setting is unstated. |
| Q155 | `arxiv:2610.08571` — [RAG-PIBench: A Leakage-Aware Benchmark for Prompt-Injection Detection in Trustworthy RAG Systems](http://arxiv.org/abs/2610.08571v1) | RAG contextual input injection detector benchmark; English setting is unstated. |
| Q161 | `arxiv:2610.20907` — [From Detection to Decision: Calibration and Deferral for Prompt-Injection Detection](http://arxiv.org/abs/2610.20907v1) | Binary input injection detector comparison/calibration is described; English setting is unstated. |
| Q163 | `doi:10.1109/access.2026.3728186` — [PIDS-Bench: Evaluating Prompt-Injection Detectors Under Over-Defense, Obfuscation, and Distribution Shift](http://arxiv.org/abs/2609.15017v1) | Fixed-threshold input-injection detector benchmark is described; English setting is unstated. |
| Q165 | `doi:10.18653/v1/2025.acl-long.1468` — [PIGuard: Prompt Injection Guardrail via Mitigating Overdefense for Free](https://aclanthology.org/2025.acl-long.1468/) | Prompt-injection guard-model evaluation; English setting is unstated; possible renamed-work duplicate also requires review. |
| Q171 | `doi:10.18653/v1/2026.acl-industry.127` — [RAPIDS: Resume Attack Prompt Injection Detection at Scale](https://aclanthology.org/2026.acl-industry.127/) | Cascade detects injected resume inputs; English setting is unstated. |
| Q175 | `doi:10.18653/v1/2026.findings-acl.738` — [RAP-ID: Mechanistic Prompt Injection Detection via Impostor Behavior Analysis](https://aclanthology.org/2026.findings-acl.738/) | Internal-state injection detector explicitly uses initial forward pass; English setting is unstated. |
| Q176 | `doi:10.5281/zenodo.19644135` — [Beyond Pattern Matching: Seven Cross-Domain Techniques for Prompt Injection Detection](http://arxiv.org/abs/2604.18248v4) | Implemented techniques evaluated on input-injection benchmarks; English setting is unstated. |

### BL: 3 records

| Review | Work and captured source | Required clarification |
| --- | --- | --- |
| Q060 | `arxiv:2602.13597` — [AlignSentinel: Alignment-Aware Detection of Prompt Injection Attacks](http://arxiv.org/abs/2602.13597v2) | Explicit three-class detector; need a separately reported binary malicious/benign decision evaluation and English setting. |
| Q126 | `arxiv:2607.22545` — [Semalith v1.4: A Calibrated 184M Safety Classifier Achieving State-of-the-Art Prompt-Injection Detection at 44x Fewer Parameters than Llama-Guard-3-8B](http://arxiv.org/abs/2607.22545v1) | Three-axis safety model includes injection; need distinct binary injection evaluation and English setting. |
| Q127 | `arxiv:2608.05430` — [Robust Context-Aware Detection of Malicious Instructions in Text](http://arxiv.org/abs/2608.05430v1) | Context/query-aware malicious sentence classifier; need qualifying binary prompt/document input unit and English setting. |

### BPL: 1 records

| Review | Work and captured source | Required clarification |
| --- | --- | --- |
| Q085 | `arxiv:2604.28129` — [Latent Adversarial Detection: Adaptive Probing of LLM Activations for Multi-Turn Attack Detection](http://arxiv.org/abs/2604.28129v1) | Activation multi-turn detector uses three-phase labels; need separately evaluated binary input decision, pre-answer timing and English setting. |

### BTL: 3 records

| Review | Work and captured source | Required clarification |
| --- | --- | --- |
| Q100 | `arxiv:2605.30677` — [Investigating Detection and Obfuscation of Prompt Injection Attacks Against Software Reverse Engineering AI Agents](http://arxiv.org/abs/2605.30677v1) | Detects injection strings in decompiled programs; need qualifying binary text-input unit and English setting. |
| Q113 | `arxiv:2606.17467` — [PARSE: Provenance-Aware Retrieval Sanitization for Professional Domain LLM Agents](http://arxiv.org/abs/2606.17467v3) | Sentence-level sanitization classifier; need qualifying binary prompt/document input evaluation and English setting. |
| Q114 | `arxiv:2606.19235` — [CodeSentinel: A Three-Layer Defense Against Indirect Prompt Injection in Code Contexts](http://arxiv.org/abs/2606.19235v1) | Code-node sanitizer evaluated at node level; need separate binary English-text prompt/document evaluation. |

### PL: 25 records

| Review | Work and captured source | Required clarification |
| --- | --- | --- |
| Q005 | `arxiv:2412.13435` — [Lightweight Safety Classification Using Pruned Language Models](http://arxiv.org/abs/2412.13435v1) | Separate prompt-injection classification is named, but pre-answer timing and English evaluation require clarification. |
| Q007 | `arxiv:2502.13141` — [UniGuardian: A Unified Defense for Detecting Prompt Injection, Backdoor Attacks and Adversarial Attacks in Large Language Models](http://arxiv.org/abs/2502.13141v2) | Detector uses output distributions during decoding; need whether any separate input-only pre-answer evaluation and English setting qualify. |
| Q009 | `arxiv:2503.21464` — [Harnessing Chain-of-Thought Metadata for Task Routing and Adversarial Prompt Detection](http://arxiv.org/abs/2503.21464v1) | Adversarial-prompt classifier uses chain-of-thought metadata; need whether decisions precede generated answers and English setting. |
| Q020 | `arxiv:2506.19109` — [Enhancing Security in LLM Applications: A Performance Evaluation of Early Detection Systems](http://arxiv.org/abs/2506.19109v1) | Mixes canary-output and secondary-model prompt-leak detection; need a qualifying input-only evaluation before downstream answer and English setting. |
| Q025 | `arxiv:2508.03793` — [AttnTrace: Contextual Attribution of Prompt Injection and Knowledge Corruption](http://arxiv.org/abs/2508.03793v3) | Attribution-before-detection is described; need input-only pre-answer detector evaluation and English setting. |
| Q027 | `arxiv:2508.06418` — [Quantifying Conversation Drift in MCP via Latent Polytope](http://arxiv.org/abs/2508.06418v1) | Latent trajectory drift detector is described; need pre-answer input classification and English setting. |
| Q030 | `arxiv:2509.00088` — [AEGIS : Automated Co-Evolutionary Framework for Guarding Prompt Injections Schema](http://arxiv.org/abs/2509.00088v2) | Prompt-based attack detection is evaluated; need detector timing before downstream answer and English setting. |
| Q054 | `arxiv:2602.00750` — [Bypassing Prompt Injection Detectors through Evasive Injections](http://arxiv.org/abs/2602.00750v2) | Activation drift detectors evaluated under adaptive attack; need pre-answer input timing and English setting. |
| Q062 | `arxiv:2602.20708` — [ICON: Indirect Prompt Injection Defense for Agents based on Inference-Time Correction](http://arxiv.org/abs/2602.20708v1) | Latent prober and corrective steering; need pre-answer input detection evaluation and English setting. |
| Q063 | `arxiv:2603.06588` — [vLLM Hook v0: A Plug-in for Programming Model Internals on vLLM](http://arxiv.org/abs/2603.06588v1) | Serving-engine plugin demonstrates injection detection; need original binary pre-answer input evaluation and English setting. |
| Q079 | `arxiv:2604.22888` — [RouteGuard: Internal-Signal Detection of Skill Poisoning in LLM Agents](http://arxiv.org/abs/2604.22888v1) | Skill-poison detector uses response-conditioned features; need whether qualifying classification is before downstream response and English setting. |
| Q089 | `arxiv:2605.11026` — [AgentShield: Deception-based Compromise Detection for Tool-using LLM Agents](http://arxiv.org/abs/2605.11026v1) | Trap-trigger compromise detection and downstream classifier; need whether classifier detects input injection before downstream response, plus evaluated English setting. |
| Q116 | `arxiv:2606.20746` — [Amplify, Don't Create: Temporal Accumulation for Slow-Burn Prompt Injection](http://arxiv.org/abs/2606.20746v1) | Conversation proxy accumulator; need evaluated input-only pre-answer decision and English setting. |
| Q119 | `arxiv:2606.23416` — [Detecting Malicious Agent Skills in the Wild using Attention](http://arxiv.org/abs/2606.23416v1) | Malicious skill detector uses attention; need input-only pre-answer timing and English setting. |
| Q120 | `arxiv:2607.04222` — [Unsupervised Features Mining via Activation Geometry](http://arxiv.org/abs/2607.04222v1) | Activation-feature mining evaluates injection probes; need pre-answer input-only evaluation and English setting. |
| Q130 | `arxiv:2608.10260` — [Interpreting Language Model Hidden States at Scale](http://arxiv.org/abs/2608.10260v1) | Interpretability framework replicates injection detection case study; need pre-answer binary input evaluation and English setting. |
| Q131 | `arxiv:2608.22248` — [Beyond Over-Refusal: Defending Indirect Prompt Injection via Latent Instruction Manifolds](http://arxiv.org/abs/2608.22248v1) | Latent-manifold injection defense; need input-only pre-answer detector evaluation and English setting. |
| Q143 | `arxiv:2609.30657` — [Prompt Injection Detection for Email Agents Through Attack Chain Modeling](http://arxiv.org/abs/2609.30657v1) | Binary injection benchmarks include action/intent consistency; need evaluated input-only pre-answer decision and English setting. |
| Q146 | `arxiv:2609.37737` — [Where Do LLMs Decide to Break the Rules? Mechanistic Localization of Prompt Injection Compliance](http://arxiv.org/abs/2609.37737v1) | Mechanistic study includes hidden-state attack detection; need pre-answer input timing and English setting. |
| Q159 | `arxiv:2610.18408` — [Prompt-Injection Probes Learn the Conversation, Not Just the Injection](http://arxiv.org/abs/2610.18408v1) | Input injection probes studied for confounds; need pre-answer timing and English setting. |
| Q160 | `arxiv:2610.19452` — [Are You Reading the Right Thing? Rethinking Internal Signals for Prompt-Injection Detection](http://arxiv.org/abs/2610.19452v1) | Internal-signal comparison on injected versus benign controls; need pre-answer input timing and English setting. |
| Q166 | `doi:10.18653/v1/2025.acl-long.890` — [Can Indirect Prompt Injection Attacks Be Detected and Removed?](https://aclanthology.org/2025.acl-long.890/) | Indirect-injection detection/removal study; need qualifying pre-answer input-detector evaluation and English setting. |
| Q167 | `doi:10.18653/v1/2025.findings-emnlp.1060` — [Defending against Indirect Prompt Injection by Instruction Detection](https://aclanthology.org/2025.findings-emnlp.1060/) | Instruction detector uses model behavioral states; need pre-answer input-only classification and English setting. |
| Q169 | `doi:10.18653/v1/2025.findings-naacl.123` — [Attention Tracker: Detecting Prompt Injection Attacks in LLMs](https://aclanthology.org/2025.findings-naacl.123/) | Attention-based injection detector; need pre-answer input-only evaluation and English setting. |
| Q170 | `doi:10.18653/v1/2025.ijcnlp-long.33` — [Counterfactual Evaluation for Blind Attack Detection in LLM-based Evaluation Systems](https://aclanthology.org/2025.ijcnlp-long.33/) | Counterfactual LLM-judge attack detection; need classification before downstream scoring answer and English setting. |

### T: 1 records

| Review | Work and captured source | Required clarification |
| --- | --- | --- |
| Q043 | `arxiv:2510.22628` — [Sentra-Guard: A Real-Time Multilingual Defense Against Adversarial LLM Prompts](http://arxiv.org/abs/2510.22628v2) | English semantic processing is explicit; need separately evaluated injected-instruction classification beyond harmful-content/jailbreak prompts. |

### TL: 71 records

| Review | Work and captured source | Required clarification |
| --- | --- | --- |
| Q008 | `arxiv:2503.16248` — [Real AI Agents with Fake Memories: Fatal Context Manipulation Attacks on Web3 Agents](http://arxiv.org/abs/2503.16248v3) | Evaluates agent prompt-injection defenses/detectors; need separate binary input evaluation rather than end-to-end attack success, plus English setting. |
| Q010 | `arxiv:2504.09593` — [ControlNET: A Firewall for RAG-based LLM System](http://arxiv.org/abs/2504.09593v2) | Adversarial-query detection is described, but a distinct binary prompt-injection input evaluation and English setting are unclear. |
| Q011 | `arxiv:2504.11168` — [Bypassing LLM Guardrails: An Empirical Analysis of Evasion Attacks against Prompt Injection and Jailbreak Detection Systems](https://aclanthology.org/2025.llmsec-1.8/) | Detector-evasion tests are described; need whether separate binary input detection is evaluated, plus English setting. |
| Q013 | `arxiv:2504.19793` — [Prompt Injection Attack to Tool Selection in LLM Agents](http://arxiv.org/abs/2504.19793v3) | Names input detectors evaluated against tool-document attacks; need separate binary input evaluation and English setting. |
| Q018 | `arxiv:2506.07948` — [TokenBreak: Bypassing Text Classification Models Through Token Manipulation](http://arxiv.org/abs/2506.07948v1) | Text-classifier evasion includes prompt injection among several tasks; need separately evaluated input-injection task and English setting. |
| Q019 | `arxiv:2506.12104` — [DRIFT: Dynamic Rule-Based Defense with Injection Isolation for Securing LLM Agents](http://arxiv.org/abs/2506.12104v3) | Agent framework includes injected-instruction masking; need distinct binary input-detector evaluation rather than end-to-end defense and English setting. |
| Q022 | `arxiv:2507.15042` — [DeRAG: Black-box Adversarial Attacks on Multiple Retrieval-Augmented Generation Applications via Prompt Injection](http://arxiv.org/abs/2507.15042v1) | Suffix detector is evaluated alongside retrieval-ranking attacks; need binary injected-instruction input task rather than generic adversarial suffixes, plus English setting. |
| Q024 | `arxiv:2508.00602` — [LeakSealer: A Semisupervised Defense for LLMs Against Prompt Injection and Leakage Attacks](http://arxiv.org/abs/2508.00602v1) | Jailbreak/PII framework also names prompt-injection identification on ToxicChat; need a distinct qualifying input task and English setting. |
| Q026 | `arxiv:2508.04281` — [Reasoning Enhances Robustness to Prompt Injection in LLM-Based Consensus](http://arxiv.org/abs/2508.04281v5) | Consensus robustness combines injection detection with output and policy measures; need distinct input-detector evaluation and English setting. |
| Q028 | `arxiv:2508.17884` — [PhantomLint: Principled Detection of Hidden LLM Prompts in Structured Documents](http://arxiv.org/abs/2508.17884v2) | Detects hidden prompts in PDF/HTML documents; need English-text binary injection evaluation rather than visual hiding anomalies alone. |
| Q031 | `arxiv:2509.05608` — [BinaryShield: Cross-Service Threat Intelligence in LLM Services using Privacy-Preserving Fingerprints](http://arxiv.org/abs/2509.05608v2) | Privacy-preserving attack-fingerprint retrieval is evaluated; need separate binary input-injection decision task and English setting. |
| Q033 | `arxiv:2509.18557` — [LLMZ+: Contextual Prompt Whitelist Principles for Agentic LLMs](http://arxiv.org/abs/2509.18557v1) | Context whitelist for business requests is evaluated against jailbreaks; need separate input-injection task and English setting. |
| Q034 | `arxiv:2509.21367` — [Design and Implementation of a Secure RAG-Enhanced AI Chatbot for Smart Tourism Customer Service: Defending Against Prompt Injection Attacks -- A Case Study of Hsinchu, Taiwan](http://arxiv.org/abs/2509.21367v1) | Tourism system includes intent gatekeepers and attack detection; need distinct input binary evaluation and English setting. |
| Q038 | `arxiv:2510.04885` — [RL Is a Hammer and LLMs Are Nails: A Simple Reinforcement Learning Recipe for Strong Prompt Injection](http://arxiv.org/abs/2510.04885v1) | Attacker models evade injection detectors; need separate binary input-detector evaluation and English setting. |
| Q039 | `arxiv:2510.13351` — [Protect: Towards Robust Guardrailing Stack for Trustworthy Enterprise LLM Systems](http://arxiv.org/abs/2510.13351v1) | Multimodal safety model includes injection category; need separate binary text-input injection evaluation and English setting. |
| Q042 | `arxiv:2510.19844` — [CourtGuard: A Local, Multiagent Prompt Injection Classifier](http://arxiv.org/abs/2510.19844v1) | Multiagent binary prompt classifier is described but broad harmful-behavior framing leaves separate injection task and English setting unclear. |
| Q044 | `arxiv:2511.01287` — ["Give a Positive Review Only": An Early Investigation Into In-Paper Prompt Injection Attacks and Defenses for AI Reviewers](http://arxiv.org/abs/2511.01287v2) | Peer-review attack study includes a detection defense; need separate binary input evaluation and English setting. |
| Q045 | `arxiv:2511.12295` — [Privacy-Preserving Prompt Injection Detection for LLMs Using Federated Learning and Embedding-Based NLP Classification](http://arxiv.org/abs/2511.12295v1) | Federated benign/adversarial classifier; need injected-instruction task distinct from generic harmful prompts and English setting. |
| Q046 | `arxiv:2511.15759` — [Securing AI Agents Against Prompt Injection Attacks](http://arxiv.org/abs/2511.15759v1) | Mixed-layer framework includes input anomaly detection; need separate binary input evaluation and English setting. |
| Q047 | `arxiv:2512.06556` — [Semantic Attacks on Tool-Augmented LLMs: Securing the Model Context Protocol Against Descriptor-Level Manipulation](http://arxiv.org/abs/2512.06556v2) | Auxiliary pre-context descriptor vetting is described; need distinct binary injected-instruction evaluation and English setting. |
| Q050 | `arxiv:2512.23557` — [Toward Trustworthy Agentic AI: A Multimodal Framework for Preventing Prompt Injection Attacks](http://arxiv.org/abs/2512.23557v1) | Multimodal framework includes text sanitizer with detection evaluation; need separate binary text-input injection evaluation and English setting. |
| Q051 | `arxiv:2601.10338` — [Agent Skills in the Wild: An Empirical Study of Security Vulnerabilities at Scale](http://arxiv.org/abs/2601.10338v1) | Scans skill packages for mixed code/security vulnerabilities; need distinct binary injected-instruction text evaluation and English setting. |
| Q057 | `arxiv:2602.08062` — [Efficient and Adaptable Detection of Malicious LLM Prompts via Bootstrap Aggregation](http://arxiv.org/abs/2602.08062v1) | Ensemble combines harmful/jailbreak/injection prompts; need distinct binary input-injection evaluation and English setting. |
| Q059 | `arxiv:2602.11247` — [Peak + Accumulation: A Proxy-Level Scoring Formula for Multi-Turn LLM Attack Detection](http://arxiv.org/abs/2602.11247v2) | Proxy conversation-risk scoring is trained on jailbreak data; need separately evaluated injected-instruction input task and English setting. |
| Q067 | `arxiv:2603.19974` — [Trojan's Whisper: Stealthy Manipulation of OpenClaw through Injected Bootstrapped Guidance](http://arxiv.org/abs/2603.19974v1) | Skill guidance attacks evade scanners; need distinct binary injected-instruction text evaluation rather than mixed package risk and English setting. |
| Q069 | `arxiv:2603.24203` — [Invisible Threats from Model Context Protocol: Generating Stealthy Injection Payload via Tree-based Adaptive Search](http://arxiv.org/abs/2603.24203v1) | Adaptive MCP payload attack; preview does not resolve whether a separate input-detector evaluation qualifies or its English setting. |
| Q071 | `arxiv:2604.03598` — [AttackEval: A Systematic Empirical Study of Prompt Injection Attack Effectiveness Against Large Language Models](http://arxiv.org/abs/2604.03598v1) | Attack-effectiveness study; preview does not resolve whether separate binary input-detector evaluation qualifies or its English setting. |
| Q072 | `arxiv:2604.03912` — [Automating Cloud Security and Forensics Through a Secure-by-Design Generative AI Framework](http://arxiv.org/abs/2604.03912v1) | Cloud framework includes PromptShield classification; need distinct injected-input rather than log/threat classification and English setting. |
| Q073 | `arxiv:2604.07536` — [TRUSTDESC: Preventing Tool Poisoning in LLM Applications via Trusted Description Generation](http://arxiv.org/abs/2604.07536v1) | Generates trusted descriptions as defense; preview leaves any separate binary input-detector evaluation and English setting unresolved. |
| Q074 | `arxiv:2604.12284` — [WebAgentGuard: A Reasoning-Driven Guard Model for Detecting Prompt Injection Attacks in Web Agents](http://arxiv.org/abs/2604.12284v1) | Multimodal web guard; need separate text-only binary injection evaluation and English setting. |
| Q075 | `arxiv:2604.15368` — [LogJack: Indirect Prompt Injection Through Cloud Logs Against LLM Debugging Agents](http://arxiv.org/abs/2604.15368v1) | Cloud-log attack benchmark; preview leaves separate binary input detector evaluation and English setting unresolved. |
| Q078 | `arxiv:2604.18658` — [Owner-Harm: A Missing Threat Model for AI Agent Safety](http://arxiv.org/abs/2604.18658v1) | Owner-harm threat/defense study; need original distinct binary input-injection evaluation and English setting. |
| Q084 | `arxiv:2604.27202` — [Indirect Prompt Injection in the Wild: An Empirical Study of Prevalence, Techniques, and Objectives](http://arxiv.org/abs/2604.27202v1) | In-the-wild injection prevalence analysis; need original binary detector evaluation and English setting. |
| Q090 | `arxiv:2605.11217` — [Training-Free Refusal of MCP Exploits via Retrieval-Augmented Generation](http://arxiv.org/abs/2605.11217v2) | Retrieval-conditioned exploit refusal; need separate input-injection binary evaluation rather than task refusal and English setting. |
| Q092 | `arxiv:2605.17634` — [AI Agents May Always Fall for Prompt Injections](http://arxiv.org/abs/2605.17634v1) | Contextual-integrity defense study; need whether a separate binary injected-input evaluation qualifies and English setting. |
| Q094 | `arxiv:2605.19159` — [On the Geometric Limits of Transformer Defenses against Obfuscation Attacks: Latent Embedding Collapse & Performance Robustness Gap](http://arxiv.org/abs/2605.19159v1) | Obfuscation robustness study of BERT detectors; need separately evaluated injected-instruction task and English setting. |
| Q095 | `arxiv:2605.23196` — [Prompt Overflow: What the Guardrail Inspects Is Not What the Model Infers](http://arxiv.org/abs/2605.23196v1) | Overflow attack against input safeguards; need distinct binary input-injection evaluation and English setting. |
| Q097 | `arxiv:2605.27823` — [Disentangling Adversarial Prompts: A Semantic-Graph Defense for Robust LLM Security](http://arxiv.org/abs/2605.27823v1) | Input semantic classifier is trained on toxic/jailbreak prompts; need separate injected-instruction evaluation and its English setting. |
| Q098 | `arxiv:2605.28999` — [Measuring Real-World Prompt Injection Attacks in LLM-based Resume Screening](http://arxiv.org/abs/2605.28999v1) | Resume injection prevalence study; need original binary injected-input evaluation and English setting. |
| Q103 | `arxiv:2606.02959` — [Gate AI: LLM Security Benchmark Evaluation Methodology and Results](http://arxiv.org/abs/2606.02959v1) | Benchmark harness mixes injection and jailbreak detectors; need separate binary input-injection stratum and English setting. |
| Q104 | `arxiv:2606.04141` — [Caught in the Act(ivation): Toward Pre-Output and Multi-Turn Detection of Credential Exfiltration by LLM Agents](http://arxiv.org/abs/2606.04141v1) | Pre-output credential-access probe; need whether labels are injected input rather than future exfiltration behavior and English setting. |
| Q106 | `arxiv:2606.05566` — [GuardNet: Ensemble Strategies of Shallow Neural Networks for Robust Prompt Injection and Jailbreak Detection](http://arxiv.org/abs/2606.05566v1) | Prompt-injection/jailbreak ensemble; need separate binary injected-input evaluation and English setting. |
| Q107 | `arxiv:2606.07131` — [MalSkillBench: A Runtime-Verified Benchmark of Malicious Agent Skills](http://arxiv.org/abs/2606.07131v3) | Malicious skill package benchmark; need distinct English-text injected-instruction binary evaluation rather than code/package risk. |
| Q108 | `arxiv:2606.07992` — [VATS: Exploiting Implicit Authority in Error-Path Injection via Systematic Mutation](http://arxiv.org/abs/2606.07992v1) | Tool-error attack generation; need separate binary input-detector evaluation and English setting. |
| Q109 | `arxiv:2606.08403` — [Hiding in Plain Floats: Steganographic Carriers for Indirect Prompt and Content Injection](http://arxiv.org/abs/2606.08403v1) | Carrier-evasion attacks compare plaintext and structured data; need distinct binary English-text input-injection evaluation. |
| Q110 | `arxiv:2606.14154` — [SkillMutator: Benchmarking and Defending Language-and-Code Cross-modal Attacks on LLM Agent Skills](http://arxiv.org/abs/2606.14154v1) | Cross-modal language/code skill scanner; need separate binary English-text input-injection task rather than package/code safety. |
| Q111 | `arxiv:2606.14517` — [From Shield to Target: Denial-of-Service Attacks on LLM-Based Agent Guardrails](http://arxiv.org/abs/2606.14517v2) | DoS against reasoning guardrails; need separate binary input-injection evaluation rather than cost/timeout alone and English setting. |
| Q112 | `arxiv:2606.15899` — [SkillVetBench: LLM-as-Judge for Multi-Dimensional Security Risk Evaluation in Open-Source LLM Agent Skills](http://arxiv.org/abs/2606.15899v1) | Multidimensional skill-risk judge; need distinct binary English-text input-injection evaluation. |
| Q118 | `arxiv:2606.22864` — [When AUC 0.998 Is Not Enough: A Candidate Evaluation Protocol for Hidden-State Probes of Indirect Prompt Injection in Multimodal Computer-Use Agents](http://arxiv.org/abs/2606.22864v1) | Multimodal probe study; need separate binary English-text-only input evaluation rather than screenshot/action-based evaluation. |
| Q124 | `arxiv:2607.18622` — [CPInj: Uncovering Prompt Injection Risks in Textual Collaborative Prompt Optimization](http://arxiv.org/abs/2607.18622v2) | Collaborative prompt optimization attack evaluates detection defenses; need separate binary injected-input task and English setting. |
| Q128 | `arxiv:2608.08027` — [BASIS: Breach-Aware Selective Prompt Injection Shielding with Prefill Attention Probes](http://arxiv.org/abs/2608.08027v1) | Prefill probe gates breach likelihood; need whether evaluation labels qualifying binary injected inputs rather than future breach behavior and English setting. |
| Q129 | `arxiv:2608.08468` — [SkillsMetric: Mapping the Detection Boundary of Static Analysis for Malicious Agent Skills](http://arxiv.org/abs/2608.08468v1) | Static skill-package risk scoring; need distinct binary English-text injected-input evaluation. |
| Q134 | `arxiv:2608.30441` — [ECLIPSE: Self-Evolving Stealthy Prompt Injection Attack against Long-Horizon Agentic Systems](http://arxiv.org/abs/2608.30441v2) | Long-horizon injection attacks; preview leaves separate input-detector evaluation and English setting unresolved. |
| Q135 | `arxiv:2609.01046` — [HiveTraceGuard-Pro: A Compact Generative Guardrail for Prompt Injection, Jailbreaks, and Adversarial Obfuscation](http://arxiv.org/abs/2609.01046v1) | Russian/English training and binary guard are stated; need separate injection evaluation and actual English test setting, not training alone. |
| Q137 | `arxiv:2609.10707` — [Architecting the Secure AI-SOC: A Neurosymbolic Framework for Pipeline Integrity and Threat Mitigation](http://arxiv.org/abs/2609.10707v1) | SOC pipeline defense evaluates injection attacks; need distinct binary input-injection evaluation and English setting. |
| Q138 | `arxiv:2609.15994` — [Latent Undertow: How Ordinary Typos Break Probes](http://arxiv.org/abs/2609.15994v1) | Malicious-prompt probes studied under typos; need separate binary injection evaluation and English setting. |
| Q139 | `arxiv:2609.20188` — [ResumeShield: Channel Separation and an Open Benchmark for Indirect Prompt Injection in AI Resume Screening](http://arxiv.org/abs/2609.20188v1) | Resume channel separation/benchmark; need distinct binary input-detector evaluation and English setting. |
| Q140 | `arxiv:2609.22510` — [Defusing Explosive Prompts: Understanding and Preventing Trigger-Based Prompt Injections in LLM Agents](http://arxiv.org/abs/2609.22510v1) | Conditional attacks evaluated against injection classifiers; need distinct binary input detector evaluation and English setting. |
| Q145 | `arxiv:2609.36817` — [pikit: A Composable Toolkit for Indirect Prompt Injection Research and Evaluation](http://arxiv.org/abs/2609.36817v1) | Toolkit includes offline detection baselines; need original binary text-input evaluation and English setting. |
| Q147 | `arxiv:2609.39678` — [Aletheia: Permission-Minimality Testing for Coding-Agent Rules](http://arxiv.org/abs/2609.39678v2) | Tests repository-rule permission minimality; need injected-input binary task rather than permission-risk classification and English setting. |
| Q148 | `arxiv:2610.00430` — [Memetic Trojans: Social Contagions as Carriers of Adversarial Payloads in Agent Networks](http://arxiv.org/abs/2610.00430v2) | Network-mediated memetic attack; preview leaves distinct binary input-detector evaluation and English setting unresolved. |
| Q149 | `arxiv:2610.02413` — [Prompted to Discriminate: Generalizing Malicious-Input Probes in the Wild](http://arxiv.org/abs/2610.02413v1) | Pre-answer malicious-input probes mix safety tasks; need separately evaluated injection stratum and English setting. |
| Q150 | `arxiv:2610.03434` — [Persona Guardrail: A Production-Grade Defense Framework for Agentic Systems](http://arxiv.org/abs/2610.03434v1) | Functional-boundary allow/block validator; need distinct binary injection input evaluation and English setting. |
| Q152 | `arxiv:2610.03470` — [CorrectGuard: Eyes-Off Correctness Estimation for Black-Box Security Guardrails](http://arxiv.org/abs/2610.03470v1) | Correctness auditing over mixed safety/security datasets; need original separate binary input-injection stratum and English setting. |
| Q153 | `arxiv:2610.04412` — [Large Language Models and Augmented Democracy](http://arxiv.org/abs/2610.04412v1) | Democracy thesis evaluates injection detector as one pipeline component; need separate binary input evaluation and English setting. |
| Q157 | `arxiv:2610.12292` — [One Word Opens the Gate: The Option-Channel Attack on Typed Decision Models as Agent Guardrails](http://arxiv.org/abs/2610.12292v1) | Typed model classifies actions or incoming messages; need separately evaluated binary injected-input text task and English setting. |
| Q158 | `arxiv:2610.17457` — [BrowseSafe++: Benchmarking Prompt Injection Detection Across Web Contexts, Languages, and Browser Views](http://arxiv.org/abs/2610.17457v1) | Web detection benchmark spans views/languages; need distinct binary English-text input evaluation. |
| Q162 | `doi:10.1007/978-3-031-80853-1_30` — [Prompt Injection Attacks in Defended Systems](http://arxiv.org/abs/2406.14048v1) | Attacks in defended systems; preview leaves separate binary injected-input detector evaluation and English setting unresolved. |
| Q164 | `doi:10.1145/3803804` — [Misleading Large Language Models used (or misused) in Scientific Peer-Reviewing via Hidden Prompt-Injection Attacks](http://arxiv.org/abs/2508.20863v3) | Manuscript attacks include automated content-check evasion; need separate binary input-injection evaluation and English setting. |
| Q168 | `doi:10.18653/v1/2025.findings-emnlp.528` — [Proxy Barrier: A Hidden Repeater Layer Defense Against System Prompt Leakage and Jailbreaking](https://aclanthology.org/2025.findings-emnlp.528/) | Auxiliary repeater detects attempts before target response; need distinct input-injection evaluation beyond harmful-content jailbreaks and English setting. |
| Q177 | `doi:10.63317/5axtpujejwcx` — [Gradient-Controlled Decoding: A Safety Guardrail for LLMs with Dual-Anchor Steering](https://aclanthology.org/2026.lrec-1.775/) | Gradient anchor safety guard mixes jailbreak/injection; need separate binary input-injection evaluation and English setting. |

### TPL: 32 records

| Review | Work and captured source | Required clarification |
| --- | --- | --- |
| Q014 | `arxiv:2505.03574` — [LlamaFirewall: An open source guardrail system for building secure AI agents](http://arxiv.org/abs/2505.03574v1) | Mixed framework includes jailbreak detector and reasoning auditor; need separate input-injection detector evaluation, pre-answer timing and English setting. |
| Q032 | `arxiv:2509.14956` — [Sentinel Agents for Secure and Trustworthy Agentic AI in Multi-Agent Systems](http://arxiv.org/abs/2509.14956v1) | Distributed agents detect multiple simulated threats; need a distinct binary injected-input task, pre-answer timing and English setting. |
| Q035 | `arxiv:2509.23994` — [Policy-as-Prompt: Turning AI Governance Rules into Guardrails for AI Agents](http://arxiv.org/abs/2509.23994v2) | Policy-based monitoring classifiers address mixed risks; need separate binary input-injection evaluation, pre-answer timing and English setting. |
| Q037 | `arxiv:2510.04528` — [Unified Threat Detection and Mitigation Framework (UTDMF): Combating Prompt Injection, Deception, and Bias in Enterprise-Scale Transformers](http://arxiv.org/abs/2510.04528v1) | Activation-based mixed-threat detector calls injection jailbreaking; need distinct input-injection task, pre-answer timing and English setting. |
| Q041 | `arxiv:2510.19169` — [OpenGuardrails: A Configurable, Unified, and Scalable Guardrails Platform for Large Language Models](http://arxiv.org/abs/2510.19169v2) | Unified multilingual safety/manipulation model; need separate binary input-injection evaluation, pre-answer timing and English setting. |
| Q049 | `arxiv:2512.16307` — [Beyond the Benchmark: Innovative Defenses Against Prompt Injection Attacks](http://arxiv.org/abs/2512.16307v1) | Goal-hijacking defense prompts and detection are described; need distinct binary input evaluation, pre-answer timing and English setting. |
| Q058 | `arxiv:2602.10481` — [Protecting Context and Prompts: Deterministic Security for Non-Deterministic AI](http://arxiv.org/abs/2602.10481v1) | Mixed cryptographic/semantic architecture; need original binary input-injection evaluation, pre-answer timing and English setting. |
| Q061 | `arxiv:2602.14161` — [When Benchmarks Lie: Evaluating Malicious Prompt Classifiers Under True Distribution Shift](http://arxiv.org/abs/2602.14161v2) | Pooled malicious-prompt benchmark mixes tasks; need separate input-injection evaluation, pre-answer activation timing and English setting. |
| Q064 | `arxiv:2603.11853` — [OpenClaw PRISM: A Zero-Fork, Defense-in-Depth Runtime Security Layer for Tool-Augmented LLM Agents](http://arxiv.org/abs/2603.11853v1) | Runtime security scanner plus multiple controls has preliminary tests; need separate binary input-injection evaluation, timing and English setting. |
| Q068 | `arxiv:2603.23791` — [The Cognitive Firewall:Securing Browser Based AI Agents Against Indirect Prompt Injection Via Hybrid Edge Cloud Defense](http://arxiv.org/abs/2603.23791v1) | Hybrid browser-agent checks are described in metadata preview; need distinct binary text-input evaluation, timing and English setting. |
| Q070 | `arxiv:2604.01194` — [AgentWatcher: A Rule-based Prompt Injection Monitor](http://arxiv.org/abs/2604.01194v2) | Rule-based monitor is named, but preview leaves evaluated input decision task, timing and English setting unresolved. |
| Q076 | `arxiv:2604.16838` — [enclawed: A Configurable, Sector-Neutral Hardening Framework for Single-User AI Assistant Gateways](http://arxiv.org/abs/2604.16838v2) | Mixed gateway hardening includes classification; need distinct injected-input binary evaluation, timing and English setting. |
| Q077 | `arxiv:2604.17562` — [SafeAgent: A Runtime Protection Architecture for Agentic Systems](http://arxiv.org/abs/2604.17562v1) | Stateful runtime architecture; preview leaves distinct binary input evaluation, timing and English setting unresolved. |
| Q080 | `arxiv:2604.23374` — [Ghost in the Agent: Redefining Information Flow Tracking for LLM Agents](http://arxiv.org/abs/2604.23374v1) | Agent information-flow tracking; need whether separate binary text-input injection evaluation, timing and English setting qualify. |
| Q081 | `arxiv:2604.24020` — [Poster: ClawdGo: Endogenous Security Awareness Training for Autonomous AI Agents](http://arxiv.org/abs/2604.24020v1) | Security-awareness training; need original binary injected-input evaluation, pre-answer timing and English setting. |
| Q082 | `arxiv:2604.24118` — [AgentVisor: Defending LLM Agents Against Prompt Injection via Semantic Virtualization](http://arxiv.org/abs/2604.24118v1) | Semantic-virtualization audit framework; need separate binary input-injection evaluation, timing and English setting. |
| Q083 | `arxiv:2604.24542` — [Layerwise Convergence Fingerprints for Runtime Misbehavior Detection in Large Language Models](http://arxiv.org/abs/2604.24542v1) | Runtime monitor covers backdoor/jailbreak/injection; need separate binary injected-input evaluation, timing and English setting. |
| Q087 | `arxiv:2605.03378` — [ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection](http://arxiv.org/abs/2605.03378v2) | Causal-provenance agent auditor; need separate binary input-injection evaluation, timing and English setting. |
| Q088 | `arxiv:2605.08442` — [Injection-Execution Dissociation: A Mechanistic Evaluation of Persistent Memory Attacks and Defenses in Stateful LLM Agents](http://arxiv.org/abs/2605.08442v5) | Persistent-memory defense study; preview leaves separate binary input detector evaluation, timing and English setting unresolved. |
| Q091 | `arxiv:2605.17380` — [ADR: An Agentic Detection System for Enterprise Agentic AI Security](http://arxiv.org/abs/2605.17380v1) | MCP enterprise detection system; preview leaves separate binary input evaluation, pre-answer timing and English setting unresolved. |
| Q102 | `arxiv:2606.02240` — [AgentRedBench: Dynamic Redteaming and Integration-Aware Defense for LLM Agents over SaaS Integrations](http://arxiv.org/abs/2606.02240v3) | SaaS agent redteam/integration-aware defense; need distinct binary input evaluation, timing and English setting. |
| Q105 | `arxiv:2606.04612` — [Hybrid Adversarial Defence for Natural Language Understanding Tasks](http://arxiv.org/abs/2606.04612v1) | Hybrid NLU defense; preview leaves separate binary input-injection task, pre-answer timing and English setting unresolved. |
| Q121 | `arxiv:2607.12624` — [PVDetector: Detecting Prompt Injection Attacks on Purpose-Specific LLM Agents through Policy-Violation Concept Analysis](http://arxiv.org/abs/2607.12624v1) | Policy-violation hidden-state detector during inference; need distinct binary input-injection rather than generic policy task, timing and English setting. |
| Q122 | `arxiv:2607.13081` — [SingGuard-NSFA: Extensible Guardrails for Agentic AI via Generative Reasoning and Real-Time Classification](http://arxiv.org/abs/2607.13081v1) | Mixed operational-threat generative/discriminative guard; need separate binary input injection stratum, timing and English setting. |
| Q123 | `arxiv:2607.16199` — [PlanFlip: Attacking Multi-Agent LLM Systems via Planning-Phase Prompt Injection](http://arxiv.org/abs/2607.16199v1) | Planning-phase attack and defensive checks; need distinct binary input evaluation, timing and English setting. |
| Q133 | `arxiv:2608.27990` — [CAITLYN: Can LLM Agents Autonomously Synthesize Defenses against Emerging Injection Attacks?](http://arxiv.org/abs/2608.27990v1) | Autonomously synthesized defense middleware; need distinct binary input-injection evaluation, timing and English setting. |
| Q142 | `arxiv:2609.29429` — [Just Ask Jev: Reinforcement Learning for Calibrated Decisions as a Zero-Shot Detector of AI Alignment Failures](http://arxiv.org/abs/2609.29429v1) | Benchmark mixes alignment failures including injection; need separate binary input task, timing and English setting. |
| Q154 | `arxiv:2610.04985` — [Hidden Risks of Jev: An Empirical Study of Security, Privacy, and Dual Use](http://arxiv.org/abs/2610.04985v1) | Typed decision-model security study; need distinct binary injected-input evaluation, timing and English setting. |
| Q156 | `arxiv:2610.10742` — [BRANCH: Bypassing Multi-Scanner AI Guardrails](http://arxiv.org/abs/2610.10742v1) | Multi-scanner attacks span input/output guardrails; need separate binary input-injection evaluation, timing and English setting. |
| Q172 | `doi:10.18653/v1/2026.acl-industry.58` — [Securing the Tool Layer: A Threat Taxonomy and Runtime Defense Framework for Model Context Protocol Deployments](https://aclanthology.org/2026.acl-industry.58/) | Tool response semantic vetting in runtime framework; need separate binary input-injection evaluation, timing and English setting. |
| Q173 | `doi:10.18653/v1/2026.eacl-long.139` — [Safe-Unsafe Concept Separation Emerges from a Single Direction in Language Models Activation Space](https://aclanthology.org/2026.eacl-long.139/) | Cross-domain concept classifier covers mixed tasks/languages; need separate binary input injection evaluation, timing and English setting. |
| Q174 | `doi:10.18653/v1/2026.findings-acl.240` — [MCP-Guard: A Multi-Stage Defense-in-Depth Framework for Securing Model Context Protocol in Agentic AI](https://aclanthology.org/2026.findings-acl.240/) | MCP layered security includes mixed threats; need separate binary input-injection evaluation, timing and English setting. |

## Scope of this packet

This collects every current unresolved domain record and known identity ambiguity
from the unchanged snapshot. Some screening used abbreviated abstract previews;
unresolved facts are questions, not inferred exclusions or full-text findings.
No retrieved abstract outcome headline was used for inclusion/exclusion. Versions
and accessibility remain separate, unperformed checks. Later source verification
can reveal additional ambiguities; those must be batched and reported, not silently
resolved by changing the frame. Historical protocols, ledgers and source bytes persist.
