# Locked eligibility projection for independent review

This is an eligibility-only access projection of the approved frame and A01–A04.
`MANIFEST.json` binds the source protocol hashes; it does not replace their
historical bytes. Original claim taxonomy and assurance-specific GO/STOP criteria
remain unchanged and are outside this eligibility assignment. No eligibility
decision, independent verification or sampling has occurred under this handoff.

1. **Universe.** Reconcile every supplied work and every captured member. Primary
   discovery is the already captured arXiv plus ACL Anthology frame only. Do not
   add candidates, refresh either index, citation-chase for discovery, replace
   works or truncate the universe. OpenReview discovery data are
   EXCLUDED_FROM_SELECTION_FRAME. OpenReview/publishers may verify bibliography
   of independently retrieved works only. The maximum remains 500 unique works.
   The frozen local predicate was Unicode NFKC, casefold, Unicode Pd hyphens to
   spaces and whitespace collapse, then both `\bprompt\s+injection\b` and
   `\b(?:detect\w*|guardrail\w*|classif\w*)\b` on title plus abstract. It has
   already produced the supplied inventory; do not rerun a different search.
2. **Domain.** Original empirical research evaluating an English-text binary
   prompt-injection input classifier: a malicious/benign score or decision on a
   prompt/document before the downstream target LLM answers. Direct and indirect
   delivery both qualify; record them separately. Exclude PII, output moderation,
   response refusal alone, end-to-end attack-success-only defenses, tool-policy-
   only systems, surveys and positions. Harmful-content/jailbreak classification
   alone does not qualify; a separate input-injection evaluation may qualify.
   Consider qualifying experiments/baselines throughout the work, even if its
   proposed method uses generated output. An auxiliary detector LLM can generate
   before a distinct target answers; reliance on the target's answer fails timing.
3. **English evidence.** Establish the evaluation setting from primary methods,
   datasets or source construction. The encoder's multilingual capability or
   English paper prose is insufficient. Corpus/example-based indirect support
   needs explicit evaluation linkage and limitations. Do not invent an English-
   only test split or language proportions. Record supported facts and uncertainty.
4. **Dates and versions.** First public release 2024-01-01 through 2026-10-16.
   Use the latest public version at or before 2026-10-17T00:00:00Z. Prefer publisher
   version of record available by cutoff, then accepted public conference version,
   then latest dated preprint by cutoff. Keep preprint crosslinks. A month-only
   date must fall wholly inside the window or remain UNCLEAR for metadata
   adjudication. Unknown versions remain excluded with reason under the original
   rule. Local file dates do not establish publication or version. Do not silently
   substitute an accessible earlier version for a withdrawn/latest version.
5. **Identity and sentinels.** One work, one version. Deduplicate DOI/arXiv/forum
   crosslinks first, then normalized title plus author identity; preserve all
   memberships. Resolve ambiguities with primary bibliographic evidence. Enforce
   `BIBLIOGRAPHIC_CONSTRAINTS.json`. Apply the existing 65 sentinel exclusions and
   their version scopes; do not add exclusions because of current exposure.
   Sentinel display labels are hashed because they can contain findings. Exact
   hash matching alone does not establish absence of a renamed/version match;
   unresolved matches need controlled bibliographic adjudication. The two
   StepGuard identifiers remain potentially distinct, both excluded along with
   known matching versions, with no asserted alias mapping.
6. **Access.** PDF availability is separate from domain eligibility. Record actual
   attempts, timestamps, versions and statuses. Retain otherwise eligible
   inaccessible works; no replacement of inaccessible selected works. Missing
   abstracts are not evidence of no evaluation. Access alone is not an exclusion.
7. **Evidence boundary.** Do not use FPR/performance findings, numerical results,
   sample/false-positive counts, assurance statements, reporting sufficiency or
   statistical interest to decide eligibility. No such outcome extraction is
   authorized. Obtain restricted primary method evidence through the intake in
   READ_FIRST.md; retain UNCLEAR when material facts are unresolved. Do not turn
   this restricted inventory's omissions into exclusions. Record concise primary
   method/bibliographic locators and limitations for each decision.
8. **Return and gate.** Independently reconcile all 372 rows, including dates,
   versions, identity, sentinel and access provenance. A study-unit ambiguity must
   be resolved without silently changing rules or work count. Stop on a material
   frame-invalidating condition. No draw until complete independent review,
   mechanical validation and explicit B1 gate approval. If fewer than ten eligible
   unexposed works ultimately exist, FRAME_INSUFFICIENT; do not pad or replace.
   The unchanged future draw uses Python 3.12.10, sorted unique canonical
   versioned IDs, `random.Random(20261017).sample(..., 10)`; the later six-paper
   assignment uses seed 20261018 on sorted selected IDs. Neither is authorized
   here. This is feasibility within an arXiv/ACL-retrieved frame, not prevalence
   estimation or evidence of publication readiness.
