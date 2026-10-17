# Prior-art distinction — 17 October 2026

**BOUNDED_NO_EQUIVALENT_AUDIT_FOUND; novelty UNKNOWN. A3 draft permissible.**
No accessible inspected source established the package's hard `PRIOR_ART_STOP`:
a comparable sampled audit of binary LLM input prompt-injection guardrail FPR
claims, reconstructed benign n/k, and explicit population-assurance taxonomy.
This is a conditional triage result, not a systematic-review finding or
TMLR-readiness assessment. Incomplete access to two close leads remains material.

Access window: 2026-10-17 07:56–08:03 UTC, following A1's status update;
the Position paper's initial access check was earlier. Three parallel source
reviews were synthesized by the root agent. Named-title searches were combined
with queries including `"prompt injection" "false positive" "reporting" audit
papers denominators`, `"guardrails" "false positive" "systematic review"
confidence`, `"guardrail" "meta-analysis" "false positive"`, and
`"prompt injection" "denominator" audit`; the latter searches also restricted
to arXiv, ACL Anthology and OpenReview. Search snippets/AI summaries were leads;
the comparisons below use primary text. This was not the pilot search snapshot.

## Closest reporting audits and reviews

| Primary source / status | Depth and exact locations | Difference from proposed estimand |
| --- | --- | --- |
| Geng, Xu, Qu, Wong, [*Prompt Injection Attacks on Large Language Models: A Survey of Attack Methods, Root Causes, and Defense Strategies*](https://www.techscience.com/cmc/v87n1/66084/html), CMC 87(1), article 4, 10 Feb 2026, DOI 10.32604/cmc.2025.074081 | SELECTED_SECTIONS: §§2.3–2.5, Table 3 (publisher PDF p.7), §5.4/Table 7 (p.33), §6.3 (pp.41–42), conclusion. | A 128-study review with extraction fields for metrics, statistical analysis and reproducibility; already recommends FPR and confidence intervals. Inspected taxonomy does not reconstruct benign n/k or separate descriptive/target/assurance propositions. Generic reporting-quality novelty is occupied. |
| Mourad, Abdallah, Ababneh, [*Securing the Prompt Pipeline*](https://www.mdpi.com/2079-9292/15/16/3700), Electronics 15(16),3700, DOI 10.3390/electronics15163700; [version notes](https://www.mdpi.com/2079-9292/15/16/3700/notes), 19 Aug 2026 | SELECTED_SECTIONS through indexed publisher text: §§4.1–4.4/Table 4, §5.2 RQ9/RQ10, Tables 6–10. Direct full-text/PDF/XML fetching blocked. | A sampled systematic defense review with scope/methodology/transparency/practicality rubric. Retrieved sections do not establish the precise assurance/n/k audit. **Full-table equivalence UNKNOWN**, not a definitive exclusion. |
| Abasıkeleş Turgut and Gümüş, [CASCADE record-level audit](https://arxiv.org/pdf/2604.17125v3), arXiv:2604.17125v3, 2 Oct 2026; preprint | SELECTED_SECTIONS: §§1–2, 3.4, 4, 6.4–7, Tables 1/13. | Audits its authors' own system/corpus; compares six MCP defenses and derives a reporting checklist. Decision convention, corpus dependence and threshold provenance are already substantive mechanisms here. §4.3 disclaims generalization bounds; §7 limits scope to one system, rather than a sampled cross-paper assurance audit. v3 supersedes earlier versions. |
| Li, Fung, Li, Ismail, Iqbal, [*Taxonomy and Consistency Analysis of Safety Benchmarks for AI Agents*](https://arxiv.org/pdf/2605.16282v1), arXiv:2605.16282v1; preprint | SELECTED_SECTIONS: introduction, §§4–5.1, 8.2 and taxonomy tables. | Codes benchmark risk/evaluation design and compares safety conclusions; not the proposed benign-FPR proposition/evidence linkage. |
| Mahendrakar, [*Near-Zero Until Someone Tries*](https://research.pranaymahendrakar.com/p/near-zero-until-someone-tries), author-dated 30 Aug 2026, DOI 10.5281/zenodo.22167308 | ABSTRACT_ONLY. Zenodo record/API/PDF attempts failed. Venue/version UNKNOWN. | Abstract already criticizes absent operating-point FPR and static/adaptive estimand mismatch. Full-method equivalence **UNKNOWN**; do not infer absence from inaccessible text. |

## Methods, shift and general uncertainty are different research classes

| Primary source / verified identity | Depth, locators and scope |
| --- | --- |
| Bista et al., [*ConformalGuard: False-Positive-Controlled Action Gating for LM Classifiers*](https://arxiv.org/html/2610.14365v1), arXiv:2610.14365v1, 9 Oct 2026 | FULL_TEXT official HTML, including tables/Appendix A; PDF fetch failed. §3.2 Proposition 1: marginal benign-event conformal control under frozen scoring/exchangeability; §3.3 separates recall/workload. §4.1/Table 2 email populations; Tables 3–7 calibration/shift experiments. Not a paper-reporting audit. ArXiv says COLM 2026; linked OpenReview challenge prevented independent venue confirmation. |
| Priye, Wang, Ling, Chaykowsky, [*Available Guardrails: Certifying Selective Prediction across ML Systems*](https://arxiv.org/pdf/2609.22048v1), 18 Sep 2026; preprint, venue UNKNOWN | SELECTED_SECTIONS: §§3.1–3.4, selected §4, Appendices A/B; pp.3–5 Eqs.1–5. Selective error **among served traffic**, independent planning/certification and certificate availability; not benign-class FPR reporting. Familiar exact-binomial sample requirements are central already. |
| Chaudhari, [*Regime-Adaptive Conformal Guardrails for Prompt Injection Attacks Under Distribution Shift*](https://www.preprints.org/manuscript/202609.2642), 202609.2642v1, 30 Sep 2026; explicitly not peer-reviewed | FULL_TEXT research HTML, methods/propositions/Tables 1–14. §4.6 separates marginal next-benign-request control from horizon label-request control under stronger conditional validity; §5.3–5.4/Tables 2–3 constructed transfers/streams; §7.1 limitations. Shift/recalibration method, not publication audit. |
| Zhou and Wang, [*False Sense of Safety in Selective Signal Classification*](https://arxiv.org/pdf/2606.15153v1), 13 Jun 2026; preprint | FULL_TEXT, five pages: §§2.1,3,4 and all tables. Experiments audit selective-risk methods on sound/image/synthetic scores; estimand is error among accepted inputs. Not sampled LLM-guardrail reporting. Ambiguous older title lead [2407.02551v2](https://arxiv.org/abs/2407.02551v2) is now *Breach By A Thousand Leaks* (Glukhov et al., 30 Oct 2024), ABSTRACT_ONLY, a separate information-leakage topic. |
| Uluırmak and Kurban, [*EvalSafetyGap*](https://arxiv.org/pdf/2606.30219v5), 31 Jul 2026; preprint | SELECTED_SECTIONS: §§2,5.5,6,8.2; Tables 3–4, pp.42–45. Broad hybrid survey and purposive ten-model evidence panel, not the proposed guardrail paper sample/count reconstruction. |
| Beyer et al., [*Position: LLM-Safety Evaluations Lack Robustness*](https://arxiv.org/pdf/2503.02574v2), 18 May 2026 | SELECTED_SECTIONS: §2, Appendix A.5.1 pp.19–20, Table 2 p.24. Already analyzes small samples, uncertain comparisons, overrefusal and a published-result reconstruction. PDF identifies ICML 2026/PMLR 306; official ICML downloads listing corroborates title. Not a sampled assurance-taxonomy audit. |
| Bowyer, Aitchison, Ivanova, [*Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints*](https://proceedings.mlr.press/v267/bowyer25a.html), ICML 2025/PMLR 267; arXiv:2503.01747v3 | SELECTED_SECTIONS §§1–3.1, clustered-comparison figure: small-sample/clustered evaluation uncertainty. Miller, [*Adding Error Bars to Evals*](https://arxiv.org/abs/2411.00640v1), 1 Nov 2024, ABSTRACT_ONLY, supplies general evaluation/statistical-planning guidance; venue UNKNOWN. Neither establishes this specific sampled audit from inspected text. |
| Adam Noonan, [*The Exceedance Design Effect: Effective Sample Size for Thresholds under Clustering*](https://arxiv.org/pdf/2608.21262), v2, 1 Oct 2026; preprint | SELECTED_SECTIONS §§1–4/theorem/proof, especially §1.2 p.2: first-order variance equivalence, not exact coverage substitution; IID clusters and continuous same-source marginal. Current v2 differs from cached earlier descriptions. Dependence theory is not a new contribution of this pilot. |

## Candidate question and failure case

**Best plausible distinct question (inference from the comparisons):** can a
bounded, outcome-blind sample of binary input prompt-injection detector papers
link each explicit population-level benign-FPR assurance proposition to its
decision units, reconstructable observed n/k, threshold-selection policy,
dependence assumptions and the method actually invoked—and yield a substantive
human-verified discrepancy or recurring evaluation-design mechanism?

**Strongest reason to stop the paper route:** explicit assurance claims may be
rare; missing denominators may prevent evaluation. Merely rediscovering the
binomial floor, omitted intervals or incomparable metrics repeats prior work.
The native Warrant reporting defect is an engineering audit finding, not
evidence about the literature and not a new certification algorithm.

No pilot was sampled or outcomes extracted. A3 is permissible as a **draft**
only. Before later execution, the human should assess the close reviews and
unresolved inaccessible lead; discovery of an equivalent audit triggers
`PRIOR_ART_STOP`. This bounded negative search cannot establish global novelty.
