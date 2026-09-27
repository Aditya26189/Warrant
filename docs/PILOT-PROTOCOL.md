# A pilot protocol, for one buyer and one recurring decision

**Status: a plan, not evidence.** No pilot has run. No customer conversation has
happened. Nobody outside this repository has used the tool. Every figure below is
either measured *on this repository's own data* and labelled as such, or a
declared assumption. Nothing here is a market claim, and no line of it may be
quoted as one.

This document exists to make one thing testable: **whether a model-validation
function will pay for explicit uncertainty, refusal and a priced re-validation
cost.** That is a hypothesis. The code is a fact.

---

## 1. Facts and hypotheses, kept apart

**Facts** (each traceable in this repository):

| Fact | Where |
|---|---|
| A local CLI certifies a detector from a customer's scored file, or refuses, and writes a JSON record | `docs/INPUT.md`, `controlplane/intake/` |
| Certification needs at least 59 clean negative units for a 5% budget, 299 for 1% | `docs/INPUT.md`, `min_n_for` |
| A refusal has no override path anywhere in the code | invariant 3, `CLAUDE.md` |
| Estimated population rates on a `certify` record carry intervals and name their `n`. A release evaluation uses a different, simultaneous family of intervals, and the two verdicts are not interchangeable. On grouped files, reviewer agreement describes the observed pairs only: its population interval is withheld, with a reason and reviewed-pair/group counts (DECISIONS 201) | invariant 4, `docs/RELEASE.md` |
| A year of weekly rechecks can be run as one chained test, in which the chance that its **sequential false-positive statistic** falsely revokes a detector keeping its promise is bounded by alpha, under that statistic's assumptions. A revocation because the score distribution moved is a separate check, outside that bound | `DECISIONS.md` 187, 193, 194 |
| Sizing a recheck to catch a 1.5x breach of a 5% budget at power 0.80 needs 628 clean negatives | `DECISIONS.md` 183 |
| A VALID certificate on an ungrouped file, or on a grouped file whose groups each carry one label, states how many mislabelled items it tolerates. Not every certificate reaches a finite figure: a ladder can say no number of errors in the pool falls below a level. On this project's own certificates, 2 to 8 flagged-clean errors take one below 0.80 | `DECISIONS.md` 197, 199, claim table |
| A machine-checked crosswalk to the RBI's **draft** model-risk guidance: 20 paragraphs, 2 provided, 13 partial, 5 not provided. A crosswalk is a register of evidence types, not compliance approval, and not evidence that anyone will buy | `docs/RBI-MRM-2026-CROSSWALK.md`, `DECISIONS.md` 189 |
| Nothing leaves the machine: no network calls, no telemetry | `docs/INPUT.md` |

**Hypotheses** (none tested):

1. A validation function has a **recurring** decision that today rests on an
   unquantified evaluation.
2. Refusal is welcome rather than an obstacle - "we cannot certify this on your
   evidence" is worth paying for.
3. The labelling cost a real bound demands is acceptable once it is priced.
4. A JSON record plus a rendered summary is accepted as evidence by a second
   line of defence or an auditor.
5. Local-only operation is a requirement, not a limitation.

Every one of these can be false, and 2 and 3 are the ones most likely to be.

---

## 2. The buyer and the decision

**Proposed segment (hypothesis).** The independent model-validation or AI-risk
function at a regulated financial institution in India, or the equivalent second
line at a large enterprise elsewhere. Chosen for three reasons, each weaker
than it sounds:

- **A regulatory gap, from a draft.** The Reserve Bank of India's *Guidance on
  Regulatory Principles for Model Risk Management* is a **draft for public
  comment**, not a binding requirement: released 2026-06-24, comments invited by
  2026-07-24 ([press release](https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63006),
  re-read 2026-09-16, still presented as a draft). The repository's crosswalk read
  the draft text on 2026-09-14 and found it requires validation and monitoring
  while setting no confidence level, sample size or evidential standard for either.
  The draft text itself was not re-read on 2026-09-16, and whether a final text has
  since been issued was not checked. A final text could differ.
- **Organisational separation -- a hypothesis to test.** The validation function
  is separate from the team that ships the model. That *may* make a refusal easier
  for it to deliver. Separation does not establish its incentives, its standing to
  delay a release, or its willingness to pay, and the pilot should find out rather
  than assume.
- **The crosswalk already exists.** That lowers the cost of a first conversation,
  and says nothing about whether one will happen.

**Not chosen, deliberately:** the application team shipping an LLM feature. They
buy iteration speed, and a tool whose main output can be "no" competes with the
evaluation platforms rather than complementing them.

**The recurring decision.** *"May this detector, guardrail or filter go live at
this threshold, and is the number we approved it on still true?"* It recurs on
every release of the guarded system, and again on a fixed monitoring cadence.

**What Warrant supplies to it:** a false-positive bound on the customer's own
data at a declared budget, or a refusal naming what is missing; recall and
precision at that operating point, with intervals; the label-error tolerance of
the certificate where one is defined; a sized recheck plan; and a chained
recheck whose sequential false-positive statistic spends one alpha across a year
rather than one per week. A revocation for a moved score distribution is a
separate check outside that bound.

**What it does not supply:** the deployment decision itself, adversarial
robustness, any claim about a model's truthfulness, and any authority. The
customer retains the decision.

---

## 3. Data, ownership and the sampling unit

- **The customer's data never leaves their machine.** They run the CLI; we see
  what they choose to show us. If a pilot requires us to see records, that is a
  different arrangement and needs their legal sign-off, not ours.
- **They export three columns**: `id`, `label` (1 = the detector should fire),
  `score`. Optional `group` when items are not independent, and optional
  `label_2` for a second reviewer.
- **The sampling unit is agreed before any export**: items, or groups when
  several items come from one document, ticket or conversation. Items from one
  source are not independent evidence. How far treating them as independent
  overstates the evidence depends on how strongly items within a group agree and
  on how the file was sampled, so no single factor says by how much.
- **Each workflow's grouped-data contract is different**, and the pilot uses the
  one it runs:
  - `warrant certify` certifies at group level, and **rejects** a file whose
    groups are not all the same size with an input error (exit 2) -- not a
    REFUSED warrant;
  - `warrant recheck` re-tests a grouped warrant in groups, and **rejects**
    unequal negative group sizes the same way;
  - `warrant release` **rejects grouped input** outright, as an input error
    that tells the user not to erase the groups to obtain a result; its records
    declare IID items.
- **A summary of the file is not an inference about the population.** Counts on
  the supplied file -- how many flagged, how many false positives -- are exact
  statements about that file. A bound or interval becomes a statement about the
  traffic only if the file was sampled from it in the way the method assumes, and
  a file cannot show that it was: not that its items are independent, not that it
  is representative, not that it covers the population the decision concerns.
  That is the customer's to establish and the pilot's to record. If the file is
  last quarter's traffic and this quarter differs, the bound describes last
  quarter; `recheck` is the instrument for that, not a caveat.

---

## 4. Labels, blinded

The whole result rests on labels, so labelling is part of the protocol and not an
input accepted sight unseen.

- **Reviewers are blind to the score, the flag and the stratum.** Anchoring on
  the detector's output biases the estimate in the direction that flatters us
  (invariant 7).
- **About 10% of both strata are double-labelled** by a second reviewer, supplied
  as `label_2`. On an ungrouped file the record then carries Cohen's kappa with
  its interval and the disputed items. On a grouped file, disputes remain
  uncomputed and kappa is descriptive of observed pairs only; its population
  interval is withheld with a reason and the counts of reviewed pairs and groups.
  Groups with no second review contribute no reviewed unit (DECISIONS 201).
  Primary-label sensitivity in whole groups remains available when each group
  carries one label. Agreement never establishes that either reviewer is right.
  `release` records carry no label-quality
  evidence at all (`docs/EVIDENCE-HANDOFF.md`).
- **Both blinded labels are preserved before anything is resolved.** The first
  and second reviewers' labels are kept as given, and agreement between them is
  computed on those. Disagreements are then adjudicated by a third reviewer.
  If adjudicated labels replace the primary labels, the pre-adjudication
  agreement is reported separately and alongside: agreement measured after
  disagreements were resolved is not agreement between independent reviewers.
  Warrant does not adjudicate; it reports.
- **The label-error tolerance is read before anyone celebrates a warrant.** On
  this repository's own certificates, 2 to 8 mislabelled flagged items take a
  certificate from 95% to below 80% confidence (`DECISIONS.md` 199). A pilot
  whose labelling is worse than that tolerance has produced a number, not
  evidence.

---

## 5. Criteria, frozen before the data is scored

Written down and agreed **before** the export is produced, in their words and
ours:

1. The **false-positive budget** the decision actually needs, and why that
   number. Not "as low as possible": each halving roughly doubles the negatives
   required.
2. The **confidence level**, named with its protocol. `certify` defaults to 95%
   on a one-sided false-positive bound; `release` uses the alpha registered in
   its contract, divided across five intervals. The same observed counts can
   clear one and not the other.
3. The **minimum recall** below which the detector is not worth running, stated
   independently of the budget, because precision and recall travel together.
4. What happens **on a refusal**: who is told, and whether the release proceeds.
   This is the question the pilot exists to answer, and it must be answered in
   advance rather than negotiated after the result.
5. The **recheck cadence** and its horizon, priced by `warrant plan` before the
   first recheck.

A criterion changed after seeing the result invalidates the pilot as evidence
about that criterion. If it changes, that is recorded as a finding, with the
original and the reason.

---

## 6. The baseline it is compared against

The comparison is not against nothing. Before the pilot, record what the
validation function does today for this decision: which artefact is produced, who
signs it, how long it takes, and what it says about uncertainty. Then compare on
four axes, measured rather than asserted:

| Axis | Measure |
|---|---|
| Does the decision change? | Would the same release have been approved, refused or delayed? |
| Time to a defensible answer | Hours from export to signed record, both ways |
| What the artefact establishes | Does the record answer an auditor's "how do you know?" without a person reconstructing it? |
| Cost of the claim | Labels, reviewer hours and reviewer cost, priced by the tool |

---

## 7. Reviewer effort, priced honestly

The declared workload in `config.yaml` - 3 minutes per reviewed item, a reviewer
month of 160 productive hours - is **an assumption, not a measurement**. In a
pilot it is replaced by the customer's own measured rate, because that number
decides whether the product is affordable.

What the statistics require, measured (`docs/INPUT.md`, `DECISIONS.md` 183):

- a 5% budget needs **at least 59 clean negative units**, and that is the floor
  for a detector that never fires on any of them;
- a 1% budget needs **299**;
- catching a 1.5x breach of a 5% budget with probability 0.80 needs **628 clean
  negatives per recheck**.

The pilot measures three things this repository cannot: how long a blinded label
actually takes, what share of items are ambiguous enough to need adjudication,
and whether the resulting cost is one the customer will repeat.

**Four outcomes, recorded separately and never merged into one score:**
onboarding time (first export to first retained record), reviewer effort
(measured minutes per blinded label, and the adjudication share), repeat use
(whether it is run again unprompted), and willingness to pay (asked, not
inferred). A strong result on one says nothing about the others.

---

## 8. What would count as success, and what would end it

Agreed before the pilot starts.

**Success (all four):**

1. The pilot produces a warrant or a refusal that the validation function
   **retains as evidence in their own record**, not merely reads.
2. They **reproduce the record themselves** from their own export, on their own
   machine, without us present.
3. They run it **a second time, unprompted**, on the next release or the next
   cadence.
4. The refusal path is exercised at least once and survives contact with the
   people it inconveniences.

**Failure signals, any of which ends the pilot rather than being worked around:**

- the labelling cost is judged unacceptable once measured;
- a refusal is treated as a defect of the tool;
- the record cannot be shown to an auditor without an interpreter;
- the decision it serves turns out not to recur.

**Not evidence of success:** enthusiasm in a meeting, a follow-up call, or a
request to demo it to another team.

---

## 9. What this pilot cannot establish

- Willingness to pay a price. A free pilot measures interest, not budget. That
  question is prepared for the conversation, without a price, commitment or
  customer invented in advance.
- Anything from the synthetic rehearsal beyond software usability. A run of the
  public CLI on generated files shows the commands work end to end; it says
  nothing about a customer's labels, data or decisions.
- Anything about a second segment, a second institution, or another regulator.
- That the detector is good. Warrant measures evidence about a detector; a
  refusal or a low recall is a fact about their detector and their data.
- That the statistics hold on their distribution. They hold on the file supplied.

---

## 10. Before anyone is approached

Preconditions, in order. None of them involves contacting a person, and the last
is not an agent's to do:

1. **The open correctness defects are closed.** As of this draft, a chained
   recheck can continue after a drift revocation, and an edited chain record can
   pass its own digest check. Both are reproduced. A pilot must not run on a
   build with a known integrity defect in the artefact it hands to a validator.
2. **One rehearsed end-to-end journey exists**: a scored export, the criteria
   sheet, the certification, a refusal example, a recheck, and the evidence
   handoff - each reproducible from a clean clone.
3. **The evidence handoff is written**: identity, scope, data hash, sampling
   unit, criteria, method, counts, intervals, reasons, label-quality caveats,
   expiry, and the command to reproduce it.
4. **A named person decides who to approach.** Outreach, introductions and any
   commercial conversation are the founder's. No agent may contact anyone,
   invent a contact, or imply a pilot exists.

---

## 11. Open questions for the founder

1. Is there an existing relationship at a validation function, or is this cold?
2. Is a pilot offered free, and if so what is asked in return - the measured
   labelling time, a written judgement on the record, or a reference?
3. Is refusal saleable in their culture, or does the first refusal end the pilot?
4. What is the smallest decision worth this effort to them? If none, the segment
   is wrong and this protocol should be rewritten for another.
