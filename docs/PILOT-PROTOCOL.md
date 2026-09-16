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
| Every rate carries a 95% interval and names its `n` | invariant 4 |
| A year of weekly rechecks can be run as one test, with false revocation bounded by alpha | `DECISIONS.md` 187, 193 |
| Sizing a recheck to catch a 1.5x breach of a 5% budget at power 0.80 needs 628 clean negatives | `DECISIONS.md` 183 |
| Every certificate states how many mislabelled items it tolerates; on this project's own certificates that is 2 to 8 | `DECISIONS.md` 199, claim table |
| A machine-checked crosswalk to the RBI draft model-risk guidance: 20 paragraphs, 2 provided, 13 partial, 5 not provided | `docs/RBI-MRM-2026-CROSSWALK.md`, `DECISIONS.md` 189 |
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
line at a large enterprise elsewhere. Chosen because the draft RBI guidance
requires validation and monitoring while setting no evidential standard for
either, which is the gap the tool fills; because that function is
organisationally separate from the team that ships the model, so a refusal costs
it nothing politically; and because the crosswalk already exists.

**Not chosen, deliberately:** the application team shipping an LLM feature. They
buy iteration speed, and a tool whose main output can be "no" competes with the
evaluation platforms rather than complementing them.

**The recurring decision.** *"May this detector, guardrail or filter go live at
this threshold, and is the number we approved it on still true?"* It recurs on
every release of the guarded system, and again on a fixed monitoring cadence.

**What Warrant supplies to it:** a false-positive bound on the customer's own
data at a declared budget, or a refusal naming what is missing; recall and
precision at that operating point, with intervals; the label-error tolerance of
the certificate; a sized recheck plan; and a chained recheck that spends one
alpha across a year rather than one per week.

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
  several items come from one document, ticket or conversation. Getting this
  wrong overstates the evidence by roughly the cluster size, and the tool refuses
  unequal groups rather than certifying them.
- **Representativeness is theirs to assert.** A warrant describes the file it was
  issued on. If the file is last quarter's traffic and this quarter differs, the
  bound describes last quarter. `recheck` is the instrument for that, not a
  caveat.

---

## 4. Labels, blinded

The whole result rests on labels, so labelling is part of the protocol and not an
input accepted sight unseen.

- **Reviewers are blind to the score, the flag and the stratum.** Anchoring on
  the detector's output biases the estimate in the direction that flatters us
  (invariant 7).
- **About 10% of both strata are double-labelled** by a second reviewer, supplied
  as `label_2`. The record then carries Cohen's kappa with its interval and the
  disputed items.
- **Disagreements are adjudicated by a third reviewer** before the file is
  final. Warrant does not adjudicate; it reports.
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
2. The **confidence level** (default 95%).
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

- Willingness to pay a price. A free pilot measures interest, not budget.
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
