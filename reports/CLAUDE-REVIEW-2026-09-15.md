# Review of Claude's work and next priorities

Claude is improving the technical evidence, but the work needs a tighter order:
repair known correctness defects, integrate the agents' work, and complete one
customer evaluation workflow before expanding the research programme. The code
is progressing; demand and fundability remain unproved. The founder has reported
no interviews, design partners, paid pilots or revenue.

This review inspects `feat/recheck-chain` at `18dfbae` and compares it with
`aa7b0af`. An independent Codex reviewer reproduced the defects below using
those branch modules in memory. No customer data or frozen scientific test set
was rescored for this review. Codex's separate implementation branch is
`feat/shared-context`; the original checkout has preserved pending work.

## What Claude has done well

- Corrected the recheck sizing and grouped-data path, added retained sequential
  recheck records and a verifier, and measured detection performance rather than
  describing a theoretical bound as a complete operational guarantee.
- Added label-error sensitivity at certification and recheck. The latest work
  distinguishes the two error directions that flatter a certificate. It also
  states that agreement between reviewers does not establish correctness.
- Recorded failed predictions and corrected overbroad conclusions in the
  label-sensitivity study. `results/label_sensitivity/triviaqa.json` is an
  experiment on this repository's data, not evidence of customer value.
- Identified a race in the clean-clone gate's provenance. The newer code checks
  the clone's commit, records provenance before cloning, and refuses a record
  whose source state disagrees. This is useful evidence-integrity work.
- Preserved separate worktrees and small commits. The earlier committed Codex
  release work is included in its line.

The committed `results/clean_clone.json` covers `1a3fd58`, with successful smoke,
test and verification steps. It records 92 claim checks and 25 frozen-score
comparisons; activation reproduction is explicitly skipped. It predates the
gate's own subsequent fix. `results/test_inventory.json` records 1,763 collected
tests at `c4fcd3e`, and explicitly does not claim execution. Neither artifact
proves the latest head is free of defects.

## Correctness defects that must precede feature expansion

All four remain reproduced at `18dfbae`. `chain.py` and `chain_verify.py` are
unchanged from `aa7b0af`.

| Priority | Defect and evidence | Required repair and acceptance check |
|---|---|---|
| P0 | `controlplane/intake/chain.py:313` only checks the e-detector's revocation state. A prior overall REVOKED result caused by drift can continue into VALID. `chain_verify.py:204` calls the history clean. | Refuse continuation after any terminal overall revocation until an explicit new certification starts a new chain. Test the actual drift-REVOKED to stable-input sequence through the CLI and the history verifier. |
| P0 | `chain.py:210` checks a reconstructed state digest. Changing serialized `threshold`, `mean_statistic` and `ended` while retaining the original digest still verifies clean. | Validate every serialized field against canonical reconstruction. Mutate each derived field independently without rehashing; every mutation must fail. Keep the separate limitation that someone controlling every copy can rewrite and rehash the entire history. |
| P1 | `controlplane/intake/labels.py:452` calls agreement before handling groups. `_agreement` at lines 493–507 bootstraps individual pairs without group IDs. Rechecks call the same helper at line 866. Four repeated clusters presented as 400 rows give the same interval as independent rows. | Pass the actual group IDs into an estimator with a justified cluster bootstrap, or withhold the grouped confidence interval with an explicit reason. Report both pair count and independent-unit count. Test strong within-group dependence and unequal group sizes; changing sensitivity to whole-group units alone does not fix this. |
| P1 | A chain record with `alpha=0` raises uncaught `ZeroDivisionError` during reconstruction (`chain.py:189–210`, CLI handler at `cli.py:273`). | Validate types, finite values and domains before arithmetic. Convert malformed records to the documented input-error result. Test zero, negative, nonfinite, boolean and missing values through the public verifier. |

The revocation reproduction uses the existing synthetic-world generator:
baseline seed 11, shifted seed 14 with shift 1.2 and 1,500 rows, subsequent
stable seed 12, threshold .99, budget/alpha .05 and horizon 100000. These are
regression inputs, not production performance figures.

## Coordination is not yet reliable

The board contains real posts from both systems, but no Claude acknowledgement
of Codex posts 13–22 was present when this review began. Claude continued to
commit decisions 198–200 independently while those numbers were already
committed on `feat/shared-context` for different choices. Having a shared page
does not mean both sessions are reading it.

Before further numbered decisions:

1. Read the board at the original shared checkout using `--root`; a worktree's
   default board is a different directory. Use distinct names such as
   `claude-8a`, `claude-c4` and `codex` for simultaneous sessions.
2. Acknowledge the findings, state ownership, and select one integration branch.
3. Reconcile the colliding decision entries explicitly, preserving every
   historical commit and the original branch/commit/number mapping. Do not
   silently renumber history or discard either rationale. The merged decision
   log and all live code references must be unambiguous and pass integrity checks.
4. Integrate Codex's committed board, strict-input fix and versioned release
   refusal semantics. Preserve Claude's newer label and gate work. Stage only
   named files; do not reset, clean or stash another session's changes.
5. Refresh collected-test claims from a clean integration commit, then run the
   complete suite, customer-environment checks and the corrected clean-clone
   gate. Record exact commits, exit statuses and skipped tiers.

Codex's latest committed release change is `fc706c1`; strict input rejection is
`9f436d3`; the board is `0a02123`. A portable legacy regression fixture and a
timestamp-rendering correction are saved separately and pending commit at the
time of writing. They must not be reported as committed or part of Claude's gate.

## What Claude should build after those repairs

The next deliverable should be one usable evaluation handoff: a customer's
scored export and declared criteria produce a reproducible, reviewable result
that can be retained with a release decision. Warrant measures evidence; the
customer retains deployment authority.

This should extend an existing workflow. LangSmith already documents datasets,
offline and online evaluation, experiment comparison and human annotation.
Braintrust documents experiments and CI evaluation. Promptfoo documents CI
evaluation and security checks. Those primary sources establish existing
capabilities, not vendor quality, market share or customer willingness to pay.
[LangSmith](https://docs.langchain.com/langsmith/evaluation),
[Braintrust](https://www.braintrust.dev/docs/evaluate),
[Promptfoo](https://www.promptfoo.dev/docs/integrations/ci-cd/).

My inference: a broad replacement evaluation platform is a poor next investment
for this pre-customer project. Test whether explicit uncertainty, refusal,
label-quality limits and the cost of obtaining sufficient evidence solve a
specific buyer's problem. Their value and differentiation are hypotheses.

The bounded next work package is:

- Package the existing local CLI into one documented, reproducible customer
  journey with valid, refused, inconclusive and malformed examples. Keep
  generated fixtures labelled synthetic and hide their performance figures.
- Produce a concise evidence handoff from the existing records: identity,
  scope, data hash, sampling unit, criteria, method, counts, intervals, reasons,
  label-quality caveats, expiry and the command to reproduce it. Reuse existing
  reports rather than adding a dashboard or another status taxonomy.
- Prepare a pilot protocol for one proposed buyer segment: who reviews the
  evidence, which recent release decision it supports, how representative data
  and blinded labels are obtained, and how useful output will be judged.
- Measure real onboarding time, reviewer effort, integration effort and repeat
  use when a partner exists. A completed pilot and a paid repeat decision would
  be materially stronger commercial evidence than another internal benchmark.

Customer conversations and agreement to a pilot require real people; an agent
must not invent them or conduct unapproved outreach. Preparing materials and
making the software reproducible can proceed now. Defer broad integrations,
new detector families and further sensitivity studies unless a confirmed user
need or a correctness defect justifies them.

## Directional conclusion

Keep Claude's technical work and its willingness to report negative results.
Change the priority from expanding analytical coverage to closing known defects
and testing a recurring customer decision. The current evidence supports
continuing a narrow pilot effort; it does not support saying the product is
production-ready, commercially validated or fundable already.
