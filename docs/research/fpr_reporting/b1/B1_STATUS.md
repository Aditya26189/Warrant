# B1 preflight — FRAME_BLOCKED

17 October 2026. **No paper selection or outcome extraction occurred.**

The user approved B1 only, conditional on completing the prior-exposure
inventory. That condition is not met: one additional earlier paper exposure
cannot yet be mapped unambiguously to a verified canonical work. B1 is stopped
before candidate retrieval, eligibility screening, randomization or assignment.

## Preserved protocol and completed checks

- Source branch/worktree: `research/fpr-stage-a-20261017` at
  `C:/Users/LawLight/Desktop/accenture/.venv/fpr-stage-a-20261017`.
  Preflight input commit: `f289901c9d4b778b408e4319a2519d6df04ee0c7`;
  production source remains `b7de189a62943b18d512b58df606621270b06c6b`.
- [APPROVED_FRAME_SOURCE.md](APPROVED_FRAME_SOURCE.md) is a byte-identical
  preservation of the reviewed `PILOT_FRAME_DRAFT.md`, SHA-256
  `74e109f800fb40f9d8fe5da61c62baf826b9980357bc87ae4f506fab64d9e6ef`.
  Its historical draft/AMEND language is retained rather than silently edited.
  The new user message grants conditional B1 approval; **protocol activation
  remains NOT_FROZEN_PENDING_SENTINEL_CLOSURE**. No selection frame is frozen.
- [SENTINEL_INVENTORY.json](SENTINEL_INVENTORY.json) expands the approved
  exclusions using bibliographic metadata from the available conversation,
  relevant local session records and retained research/source documents.
  Original exposure text/numerical outcomes were not re-extracted into this
  inventory. Historical monitoring/theory sources are explicitly context-only
  precautionary exclusions, not pilot eligibility or claim classifications.
- The previously unresolved MAGE title was anchored to its full title in a
  prior session result and matched to arXiv:2605.03228. The other named
  placeholders match arXiv:2510.05244 and arXiv:2605.30534. Primary metadata
  inspected for these matches, not their FPR results or tables.
- Additional prior-result sources absent from the frame's explicit list were
  recovered, including ConsisGuard, GuardAgent, the earlier polymorphic-prompt
  paper, Learning to Inject, other guardrail-method/review results, sources
  discussed in the repository specification, and the Deliberative Alignment
  paper indirectly exposed through Position Appendix A.5. All-version work
  exclusions and evidence bases are retained in the provisional inventory.
- [PREFLIGHT.json](PREFLIGHT.json) records actual creation time, input commit,
  protocol/inventory hashes, the blocking condition and NOT_RUN stage states.
  The input tree was clean when these operational records were created.

## Clarification required before selection

Earlier Stage A search output at **2026-10-17T07:57:30.799Z** exposed:

> StepGuard: Step-Level Data Synthesis and Balance-Aware Reinforcement

The retained primary link is
[this OpenReview PDF](https://openreview.net/pdf/27bdc234a1ce9d4f972f85391e2e1d1e53681ff1.pdf).
A title-only lookup found candidate
[forum 2i7xXuNixu](https://openreview.net/forum?id=2i7xXuNixu).
The forum and both PDF routes returned browser-verification pages. The direct
metadata API request first hit the sandbox's connection refusal; an approved
read-only retry returned **HTTP 403**. Those attempts do not verify that the
old PDF and the candidate forum identify the same work/version family.

The user subsequently supplied the candidate citation: *StepGuard: Step-Level
Data Synthesis and Balance-Aware Reinforcement Learning for Guardrail*, anonymous
ACL submission, forum `2i7xXuNixu`; publication/acceptance status unconfirmed.
This is user-reported bibliographic verification, not independent Codex
verification. The user could not establish that the historical hash PDF is the
same document and explicitly instructed that the URLs be recorded as potential
aliases, with identity unresolved. The inventory now preserves both the
historical URL and candidate forum/PDF routes without merging their identities.

The inventory remains INCOMPLETE_DO_NOT_SELECT and B1 remains FRAME_BLOCKED.
The approved rule explicitly requires a stop on unresolved exposure identity.
Proceeding requires evidence resolving the historical identity or an explicit
methodological amendment; the supplied citation does not waive the condition.
The subsequent user-pasted forum page adds ACL ARR 2026 May submission 17070,
displayed submission date 26 May 2026 and modification date 29 September 2026.
These are attributed page metadata, not independently retrieved version history
or acceptance evidence. The pasted abstract also contained findings; this is
recorded as additional prior exposure without copying outcome values or claim
classifications into the inventory or any pilot sheet. No completed human
extraction sheet was supplied. The page does not establish the historical PDF
mapping, so the unresolved identity and stop condition remain.

A later user-added local PDF, `17070_StepGuard_Step_Level_Dat.pdf`, was inspected
read-only for file hashes, selected PDF metadata and its first-page title band.
The title band matches the supplied full title and says "Anonymous ACL
submission". SHA-256:
`345659e1fdd5b405bf9f84c818db9ecf47b7b1726b9cd152c7a928161c52208b`.
Its SHA-1 does not equal the historical URL hash; the OpenReview URL hash scheme
has not been verified, so this neither establishes the URL mapping nor proves
different works/versions. Embedded PDF dates are not treated as publication or
version evidence. No abstract, results or tables were inspected from the PDF;
the source PDF was neither copied nor staged. Candidate bibliographic metadata
is better supported, but the historical alias remains unresolved under the
user's explicit instruction and the approved stop rule.

## Actions not run

The sentinel-closure lookups are not the prespecified pilot search. No arXiv,
ACL or OpenReview **candidate query** was run, so there is no raw candidate
snapshot, screened eligible list, candidate deduplication/access record, or
ten-paper/six-paper draw to report. No study retrieval timestamp or hash is
fabricated from the sentinel lookups. No assigned human worksheet was produced;
the original header-only templates remain unchanged. B2a/B2b are not authorized.

Unverified Mourad/Mahendrakar prior-art access remains a separate disclosed
novelty limitation, as the user allowed for feasibility. It is not the current
sentinel-identity blocker. No novelty conclusion or new literature outcome is
claimed here.

## Separate local issue

[FPR-001](../issues/FPR-001-adaptive-bound.md) tracks the native adaptive-bound
defect, exact witness, possible consumers and independent-review requirements.
It records the user's reported arithmetic verification without claiming a
review of production. It authorizes no fix or historical-certificate rewrite.

## Close-out checks

PASS: protocol byte identity/hash, 63 unique inventory work IDs, one explicit
unresolved exposure, forbidden pilot-outcome-field absence, status consistency,
local links, small-file limits, whitespace, and an empty diff over
production/tests/frozen paths. Commit hashes are reported at delivery. No scientific generator,
GPU run, full-suite rerun, remote issue, push, merge or publication is part of
this blocked preflight.
