# Stage A review request — 17 October 2026

**DRAFT_AWAITING_HUMAN_FRAME_APPROVAL — STOP after Stage A.**

The paper route remains conditional. This audit does not establish publication
novelty, a completed pilot, human agreement or TMLR readiness.

## Findings to review

1. [Native certification audit](CERTIFY_AUDIT.md): ordinary CP arithmetic and
   requested-budget rank selection agree with independent reference checks.
   Native issuance uses negative-only order statistics, successor thresholds
   and no internal split. However the smaller returned adaptive CP value is
   not generally a 95% upper bound with atoms: an exact IID three-point example
   has noncoverage .07630211515886068 at nominal .05, while every selected FPR
   remains below the requested budget. Production behavior is unchanged.
2. [Prior-art assessment](PRIOR_ART_GAP.md): generic FPR/reporting/uncertainty
   criticism already has close precedents. No sufficiently equivalent sampled
   assurance-and-denominator audit was established in inspected sources.
   Full access to the Mourad review and Mahendrakar lead remains incomplete;
   equivalence is UNKNOWN there. A3 is permitted as a conditional draft.
3. [Draft frame](PILOT_FRAME_DRAFT.md): one binary input prompt-injection
   classifier domain; arXiv/ACL/OpenReview bounded metadata retrieval;
   2024-01-01–2026-10-16 window; 2026-10-17T00:00Z bibliographic cutoff;
   explicit versions, exposure exclusions, caps and inaccessible-PDF retention.
   Selection would be uniform within the frozen retrieved frame, seed 20261017;
   the six human IDs would use seed 20261018. Neither draw occurred.

## One decision

**Approve, amend, or stop the proposed pilot frame as a whole.** Approval must
explicitly cover domain, query/index/date/version policy, sentinel inventory
(including earlier exposures known only to you), raw-snapshot/hash mechanics,
caps, missing-PDF handling, randomization and the GO/STOP conditions. Read the
close prior-art sources and unresolved-access caveats before deciding.

The assurance-specific feasibility gate is at least 3 of 10 papers with
reconstructable benign n AND observed k, and at least 2 of 10 with ASSURANCE or
FORMAL_GUARANTEE propositions. Operating targets alone do not count. Continuation
also needs a distinct question, a substantive human-verified anomaly or
source-backed mechanism beyond familiar arithmetic/missing intervals, and
feasible independent verification. Otherwise stop or prospectively approve
a different question. These are feasibility heuristics, not significance tests.

Before extraction, you must commit to independently re-extracting six original
PDFs without seeing Codex counts/labels. Keep that completed sheet **outside
every Codex-readable directory/chat/connected workspace** until Codex has
committed its own all-ten extraction in B2a. B1 stops after ID selection and a
blank sheet; B2a stops after its extraction commit; B2b preserves both originals
and reconciles in an append-only log. Every potentially critical finding needs
your source/method check. No check means AWAITING_HUMAN_VERIFICATION.

Frame approval does not authorize a production repair, broader study, push,
merge, submission or automatic stage advancement. A new explicit instruction
must authorize the next execution stage. The reported native defects require
separate behavioral-change authorization and statistical/record-contract
review; the concrete proposed repair is in CERTIFY_AUDIT.md.

## Completed checks and remaining limits

- 29 new deterministic tests and 172 existing certification cases passed;
  Ruff, independent package oracle and whitespace checks passed. Initial
  sandbox temporary-directory failures are retained in the audit ledger.
- Source base: `b7de189a62943b18d512b58df606621270b06c6b`; local branch
  `research/fpr-stage-a-20261017` in `.venv/fpr-stage-a-20261017`.
  Commits are listed in the final delivery; no production/frozen paths changed.
- No independent statistician/human validation, installed-wheel/full-suite/GPU
  rerun, ten-paper outcomes or manuscript was produced. Historical research
  and product decisions remain separate and unchanged.

Local logical commits before this closing record:
`4efc31d` source snapshot; `c0ca9c1` audit/new tests;
`87a324f` bounded prior-art assessment; `0061d3a` conditional frame/blank sheets.
The closing commit updates the audit's completed-check ledger and this request;
its exact SHA is reported in the final delivery. Documentation checks (exit 0):
identical header-only 28-column CSVs, all required fields and controlled claim
names, relative Markdown links, syntax-only parsing of the two future selection
commands, no eligible/selected ID files, and all scoped files below 10 MB.
No selection command was executed. Staged scope/content and whitespace were
reviewed before each commit. Five local commits constitute Stage A, not a
registered protocol or publication.
