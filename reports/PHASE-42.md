# Phase 42 - The human first-run worksheet now covers refusal

The blank discovery worksheet now asks an unaided reviewer to run and explain
both synthetic handoffs: the valid certificate and the grouped refusal with
an altered source. It records exact command friction, status and exit codes,
elapsed time, the files a reviewer would retain, and the reviewer's own
interpretation before anyone corrects it. No human trial was conducted in
this phase. The change is a protocol for observing the plan's still-open
user gate, not a new claim about product demand.

## Question and scope

The October plan names a user dry run and a repeatable evidence handoff as
gates. Phase 35 corrected `reports/DISCOVERY-2026-10.md` to point at the
complete valid prepared handoff. Phases 38 and 41 later added and tested a
grouped refusal and tampered-source walkthrough, including a clean clone on
the customer-only path. The discovery worksheet still routed a new reviewer
only through the valid example and described the four-row export solely as
a small format sample. That left the most distinctive product behavior,
refusal when evidence is insufficient, outside the proposed observation.

The scope is a narrow update to the existing blank worksheet and a phase
report. It does not schedule outreach, contact anyone, store a participant's
data, change CLI behavior, alter a statistical procedure or create a new
synthetic fixture. The linked examples are the ones already measured in
Phase 41. The form deliberately separates a successful command from a
correct explanation; a user can run an example while misunderstanding what
the certificate establishes.

## Work and evidence

The worksheet's opening status now links both clean-clone phases while still
stating that no human interview or dry run has happened. Its export section
keeps the valid handoff link and adds the public grouped-refusal and
altered-source walkthrough. The four-row example is explicitly too small to
establish a useful false-alarm bound. Calling it a refusal example does not
turn the two groups into more evidence.

A new blank subsection says to give someone other than the author the repo,
setup instructions and the two synthetic walkthroughs and to avoid live
command coaching. It asks the observer to write down the host and Python
version, setup steps, first command needing assistance, each status and exit
code, elapsed time, and the exact output at a failure. After the run, the
reviewer is asked in their own words what the valid and refused outcomes do
and do not permit, what files another reviewer would need, and why the two
replay commands diverge after only an excluded source note changes. Answers
are to be recorded before correction. The last row separates direct
observation from coaching, participant report or inference.

The worksheet remains empty. Phase 41's local agent-run is named as a
technical baseline, not substituted for the human trial. Its clean clone
produced PREPARED/VERIFIED/VALID/VERIFIED for the full synthetic export and
PREPARED/VERIFIED/REFUSED/VERIFIED followed by MISMATCH/VERIFIED for the
small grouped example. Those statuses and their exit codes motivate what
the form can ask a reviewer to reproduce. Their occurrence in an agent-run
does not establish usability, comprehensibility or willingness to adopt.

The form also says not to record the participant's name, customer records,
prompts, scores or secrets in this repo. A permissioned real export trial
remains a separate later step with owner-approved handling, label provenance,
score direction, independent-unit declaration, selection history and a
decision owner. The new blank table neither requests actual customer data
nor declares the human gate complete.

The report and documentation link checks are run before this phase closes;
the exact results belong in the ledger. No code path was changed, so the
relevant validation is that the links resolve, the report is not a stub,
the existing tested examples remain the targets, and the generated test
inventory is refreshed from clean source. A full research suite or new GPU
run would not add evidence about whether a person can use the worksheet.

## What this does not establish

No external participant read the questions or used the tool here. The form
could still be confusing, too long, or biased; those are empirical matters
for an unaided trial. The linked files are synthetic and the valid one
declares independent rows by construction. No bank, support team or model
validation function has supplied a scored export, ground-truth labels or
an incumbent approval packet. The worksheet does not demonstrate a recurring
decision or an economic buyer.

The two replay commands check local consistency. They cannot prove that a
mapping reflects the owner's intended label semantics, that declared groups
are valid independent units, or that the source is authentic. A refusal on
four synthetic rows proves only that the algorithm will not certify this
declared small sample at the chosen budget. A valid result on the seeded
example is not approval for deployment. The human observer must be able to
explain those limits, and the form now asks for the explanation rather than
assuming it from printed statuses.

The static documentation tests cannot evaluate question quality or user
understanding. Test inventory collection is not execution. Smoke and
frozen-score verification, when run, check repository and recorded-number
integrity, not market demand or external adoption. The activation tier
remains unavailable without the cached extraction or a fresh GPU run and
must be reported as skipped.

## Open items

The real next gate requires another person willing to follow the worksheet
without project-author help. Record exact failures and their environment;
fix one observed friction point at a time with a reproduction and regression.
The separate October 14 commercial targets remain five conversations, two
permissioned usable exports and one named recurring decision. None is
recorded. An actual incumbent comparison requires the configured packet for
the same decision, including custom evaluators and retained evidence. If it
already suffices, the Warrant handoff has no demonstrated incremental value.

Do not fill the worksheet with a simulated participant or imply that the
agent's clean-clone run is a user study. The next dated research refresh is
scheduled for October 8; it should add only genuinely new primary-source
evidence. Until a real packet or observed first-run defect exists, further
generic adapters and dashboards remain outside the plan's scope. The phase
can close because its deliverable is a blank trial instrument, while the
human and demand gates remain explicitly open.

## Ledger

| Change or check | Evidence |
|---|---|
| Baseline first-run and public commands | `reports/PHASE-35.md`, `reports/PHASE-41.md`; `examples/README.md` sections 4 and 5 |
| Updated blank worksheet | `reports/DISCOVERY-2026-10.md`; no participant answers entered |
| External trial or customer export | None observed; still an open gate |
| Clean test inventory | `results/test_inventory.json` generated from clean `3a8efa2`; 2,230 collected, execution not implied |
| Clean documentation and inventory gate | `32a639a`; 161 passed, exit 0 |
| Clean smoke and available verifier | `32a639a`; smoke 7/7, claim table 92/92, frozen scores 25/25; activation tier skipped with `--no-activations` |
