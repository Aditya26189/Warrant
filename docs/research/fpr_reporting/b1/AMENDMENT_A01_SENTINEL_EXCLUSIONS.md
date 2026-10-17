# A01: conservative exclusion of two potential StepGuard identities

Authorized by the user's 17 October 2026 decision. Recorded UTC: 2026-10-17T14:24:56.748628+00:00.
Prospective amendment at source commit `6d68cf9a90abc6f9288838162e5c273cdbfdc587`, before any pilot candidate
retrieval, eligibility screening or random selection. No trusted-timestamp or
retroactive-preregistration claim is made.

The original approved protocol and exposure records are preserved unchanged.
Original protocol SHA-256:
`74e109f800fb40f9d8fe5da61c62baf826b9980357bc87ae4f506fab64d9e6ef`.
Original inventory SHA-256:
`2aeee724b2ca9bf077d10b9bb90349a44a7295411749b807b3557db1f6dbbe40`.

## Narrow change

Treat the following as **potentially distinct previously exposed works**:

1. Historical PDF identifier/URL:
   `https://openreview.net/pdf/27bdc234a1ce9d4f972f85391e2e1d1e53681ff1.pdf`.
2. OpenReview forum `2i7xXuNixu` and its forum-linked PDF:
   `https://openreview.net/forum?id=2i7xXuNixu` and
   `https://openreview.net/pdf?id=2i7xXuNixu`.

Exclude both potential identities, the verified bibliographic title
*StepGuard: Step-Level Data Synthesis and Balance-Aware Reinforcement Learning
for Guardrail*, and matching known versions. No canonical mapping between the
historical PDF and forum is asserted. The historical URL hash scheme is unknown.
The exclusion is a protection against prior exposure, not an eligibility or
scientific judgment about the paper.

Metadata matching uses the protocol's NFKC/casefold/Pd-to-space/whitespace
normalization. Match the literal identifiers/URLs and their bibliographic
crosslinks, the normalized full title, or the earlier retained title prefix
"StepGuard: Step-Level Data Synthesis and Balance-Aware Reinforcement" with
additional trailing title words. Known version matches inherit exclusion.
Do not use numerical results, FPR findings, assurance wording, paper claim
classifications or abstract performance descriptions for this decision.
No fuzzy outcome-based matching or invented identity is permitted.

The original evidence and unresolved identity remain in
`SENTINEL_INVENTORY.json` and are copied into
`SENTINEL_INVENTORY_AMENDED.json`. That new inventory adds two separate exclusion
records. There are no other known unresolved exposure identities in the
available inventory. This amendment resolves the **selection blocker**, not the
underlying identity uncertainty. Any newly material unresolved condition still
triggers the original stop rule. All other frame rules, queries, caps, dates,
version preferences, seeds and human-blinding requirements remain unchanged.

## Verification and scope

- Authorization: explicit user amendment plus B1 only.
- Outcome/claim-classification use for amendment: NONE.
- Candidate retrieval/selection before recording: NOT_RUN.
- Historical approved protocol/evidence rewriting: NONE.
- B2, production repair, remote issue/publication, push and merge: NOT_AUTHORIZED.
- FPR-001 remains OPEN and independent of this bibliographic amendment.

The active protocol is the original approved frame **plus A01**, bound to the
amended inventory by `PROTOCOL_LOCK.json`. The separate Git commit records this
amendment before retrieval; a local Git commit is not a trusted timestamp.
