# October 1-30: from evaluation exports to reviewable evidence

Planning baseline: `3df7e89`. Created 1 October 2026 after the
[current research review](AI-OPPORTUNITIES-2026-10.md). Dates are a proposed
working schedule, not a claim that an autonomous month-long job is running.
The assistant can implement during active sessions; interviews, access to
real exports and external decisions require participating people.

## Outcome and scope

A team with an existing scored export can prepare it without losing label or
group meaning, run the existing certification/release workflow, and give a
reviewer the retained files needed to reproduce the conclusion. Target the
review/escalation detector in an AI support workflow first. This measures that
detector on the declared evidence, not the safety of the entire AI agent.

Keep existing statistical contracts, frozen research and held-out data intact.
No new model, GPU workload, gateway, dashboard, hosted service or paid dependency
is required. A customer owns its scores and labels. A successful import is
neither certification nor proof that rows are independent or labels correct.

## First milestone: explicit export preparation

Build `warrant prepare --input export.csv --mapping mapping.json --out prepared`.
Also accept flat JSONL/NDJSON. A versioned mapping names the ID, label and score
columns, optional group and second-review columns, binary label meanings and
score direction. Require either a group column or an explicit declaration of
independent rows. Never guess a label from a score or create labels with an LLM.

Write a new directory with canonical `scored.csv` and a `manifest.json` binding
the source bytes, mapping, normalized bytes and effective rows. Preserve order;
do not deduplicate, sample, split, tune, clip scores or select thresholds.
For lower-is-positive scores, negate the score and record the transformation.
Record excluded column names; exclude their values. The retained identifiers
and groups may still be sensitive, so this is not anonymization.

`warrant verify-prepared` must recompute from the original export and mapping,
and detect changed source, mapping, output or manifest. Checksums are integrity
checks, not signatures. Existing certification and release commands continue
to consume the canonical file and enforce their own requirements. Grouped
release evaluation remains unsupported.

Acceptance: malformed/ambiguous data produces no published package; no
replacement of an existing destination; deterministic output; groups and
second labels survive; positive direction is explicit; installed CLI works
outside the checkout; existing intake/CLI/release checks pass. No performance
improvement or market traction is inferred from this milestone.

## Daily schedule

| Day/date | Deliverable | Acceptance evidence |
|---|---|---|
| 1 / Oct 1 | Research memo, old-work audit, this plan; preregister preparation contract | Linked primary sources, rejected alternatives, atomic planning commit |
| 2 / Oct 2 | Strict mapping and CSV/JSONL normalizer | Reject ambiguous keys, missing fields, duplicates, nonfinite scores and unknown labels |
| 3 / Oct 3 | Immutable package publication and replay | Changed inputs detected; existing destinations preserved; interrupted writes cannot look complete |
| 4 / Oct 4 | Installed CLI and synthetic example | Commands run outside checkout without network or model dependencies |
| 5 / Oct 5 | End-to-end certification handoff | Prepared data consumed by existing code; refusals remain visible |
| 6 / Oct 6 | Discovery packet and local export worksheet | Interview script and observation form; no fabricated interview results |
| 7 / Oct 7 | Week-one gate and user dry run | Exact tested commit, report, usable commands; record any human trial separately |
| 8 / Oct 8 | Research refresh and competitor workflow comparison | Compare actual retained artifacts where available; otherwise mark desk research |
| 9 / Oct 9 | First supplied export investigation | Owner-approved de-identified sample, label meaning and unit recorded; if absent use synthetic data explicitly |
| 10 / Oct 10 | Fix observed import friction | Reproduction fixture and regression; no speculative adapter catalogue |
| 11 / Oct 11 | Evidence-package contract design | Enumerate required files and assumptions; verify it adds value beyond current replay |
| 12 / Oct 12 | Package assembly for one existing workflow | Explicit opt-in to copy local rows; bounded paths and no overwrite |
| 13 / Oct 13 | Reviewer replay entry point | Missing, stale and mismatched evidence distinguished; no new verdict invented |
| 14 / Oct 14 | Demand gate | Seek five real conversations, two usable exports, one named recurring review; these are targets, not results |
| 15 / Oct 15 | Research refresh and scope decision | Continue packaging only if demand evidence supports it; otherwise keep the CLI and investigate a narrower need |
| 16 / Oct 16 | One requested integration | Actual export schema and fixture required; no native compatibility claim from generic CSV support |
| 17 / Oct 17 | Review-label workflow trial | Record missing labels and disputes without substituting score for truth |
| 18 / Oct 18 | Group and leakage audit on supplied workflow | Development/holdout disjointness and independent unit documented; unsupported inference refuses |
| 19 / Oct 19 | Existing planning command applied to declared workload | Label effort derived from supplied assumptions; assumptions separate from observed costs |
| 20 / Oct 20 | Repeat-use trial on next change | Same team can rerun without author editing artifacts; absent repeat use recorded |
| 21 / Oct 21 | Week-three gate | Reproducibility, refusal cases and reviewer comprehension demonstrated or explicitly missing |
| 22 / Oct 22 | Research refresh; incumbent replacement check | Ask whether an existing product already solves the observed problem sufficiently |
| 23 / Oct 23 | Offline handoff and minimal-data review | Required files obvious; no credentials, raw prompts or customer labels committed |
| 24 / Oct 24 | Package and compatibility regression | Installed wheel and supported Python checks; document untested environments |
| 25 / Oct 25 | User-driven ergonomics | Fix observed command/error friction; do not add dashboard scope |
| 26 / Oct 26 | Clean-source suite and claim replay | Full suite plus frozen claim verifier; activation re-extraction explicitly excluded |
| 27 / Oct 27 | Short reproducible demonstration | One valid input, one unsupported case, one tampered file; synthetic status visible |
| 28 / Oct 28 | Pilot proposal for a named workflow | Deliverable, decision owner, actual data access and cost assumptions documented; no outreach without authorization |
| 29 / Oct 29 | Final research refresh and evidence audit | Separate shipped software, observed usage, inferred opportunity and open work |
| 30 / Oct 30 | Keep/pivot/stop report and release checkpoint | Clean tree, atomic history, phase report; no claim that completion implies product-market fit |

Days describe work order. Autonomous implementation may finish several days'
bounded engineering tasks in one session. It cannot accelerate calendar-based
repeat use or manufacture interviews. Reorder after evidence changes; retain
the original plan and log why.

## Weekly gates and stop rules

Week one passes technically when the first milestone is usable and verified.
Week two's commercial target is five conversations, two exports and a named
recurring decision. If those are unavailable, freeze speculative feature work;
prepare better discovery materials and document access as the blocker. A lack
of interviews is not proof of no demand, but also does not justify a platform.

Week three seeks a second use by at least one team and a reviewer able to
reproduce the result. Week four seeks an explicit pilot commitment with a
budget owner, or a candid decision to keep this as an open-source research tool.
These thresholds are planning choices, not statistically estimated conversion
rates. No customer contact, signup, payment or deployment is implied by the plan.

Stop or narrow the product if users cannot obtain labels, if they do not make
the proposed review decision, if incumbent artifacts already suffice, or if
the cost of representative evidence exceeds the decision's value. Do not
respond by adding another detector or inventing a compliance requirement.

## Work protocol and continuation

Before each session: read the coordination board and this plan, inspect Git,
and claim only the paths being edited. Work in an isolated branch/worktree,
preregister methodological choices, commit named files continuously, and run
artifact generators only from clean source. Preserve other agents' claims.

Daily record: the question answered, concrete change, checks completed, exact
commit, evidence still missing and next executable step. Weekly record: what
changed in the market hypothesis and whether a gate passed. Tests that were
only collected are not passing tests; synthetic examples are not pilots.

No unattended scheduler is installed by this plan. Start the next active
session from the latest phase report and first unfinished accepted milestone.
