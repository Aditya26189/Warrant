# October discovery packet: review-trigger evidence handoff

**Status: no human interview or dry run, created 1 October 2026.** The
synthetic commands were later replayed from a clean clone in
[Phase 35](PHASE-35.md) and [Phase 41](PHASE-41.md). No customer conversation,
real export, product trial, budget commitment or pilot is recorded by this
document. Use the
[October plan](BUILD-PLAN-2026-10.md)
for the decision gates and the [research memo](AI-OPPORTUNITIES-2026-10.md)
for the source-backed rationale. Do not send this packet to anyone or collect
their data without the appropriate owner's authorization.

## Decision to investigate

Can an AI support team and its reviewer use a local, replayable measurement of
an existing escalation detector when deciding whether to keep its threshold on
the next release? The object is the *review trigger*, not the underlying
assistant. A valid response to this question is that their present evaluation
tool and approval packet already do the job.

Start with a person who owns that release decision. Ask for a recent actual
decision and its existing artifacts before showing Warrant. Keep the event date,
interview date and interviewer separate. If an artifact cannot be shared, record
only a description, not a made-up example. Interview counts and findings belong
in a dated results log after the conversation, never in this blank template.

## Conversation guide

1. What customer-support task does the agent perform? What does the proposed
   detector flag, and what action follows a flag? Who can change its threshold?
2. Walk through the last release or threshold change. What evidence was read,
   who challenged it, and what was the final decision? Ask to see the packet as
   used, with sensitive content withheld if necessary.
3. Where do scores and human labels come from? Who is blind to the detector
   output while labeling? How are disagreements resolved and preserved?
4. What is one independent observation: a response, turn, conversation, ticket
   or customer? Can multiple rows come from the same source? How were examples
   sampled and separated from threshold selection?
5. Which false alarms and misses matter, at which volume and review cost? What
   bound or uncertainty statement, if any, is required to change a threshold?
   What happens when evidence is insufficient?
6. Which product currently stores experiments and approval evidence? Can a
   reviewer reproduce a result from retained inputs without the original
   analyst? Ask for the actual output and its limitations.
7. How often does this decision recur? How much person-time did the last one
   take? Whose budget bears that cost? What existing tool or manual step would
   a new handoff replace?
8. If the proposed package were available, what specific decision would change?
   Ask the reviewer to point to one missing field, refusal or replay step.
   A favorable reaction without a decision or recurring use is not demand.

Avoid leading questions about whether auditability, local operation or a new
dashboard sounds useful. Record observed behavior separately from hopes and
from the interviewer's interpretation.

## Observation form (copy per conversation)

| Field | Record after the conversation |
|---|---|
| Date, organization type, participant's role | |
| Specific workflow and last decision date | |
| Existing artifact inspected (type, owner, redactions) | |
| Decision owner and budget owner | |
| Detector output, action and threshold owner | |
| Score/label provenance; reviewer blinding | |
| Sampling unit, grouping, selection/holdout separation | |
| Current uncertainty, refusal and replay behavior | |
| Recurrence, effort and observed cost | |
| Evidence of friction, with participant's exact words if permitted | |
| Incumbent feature that already solves the problem | |
| Requested next step, who requested it, and authorization | |
| What was directly seen vs participant report vs our inference | |

Do not paste customer records, identifiers, prompts or secrets into this repo.
Store only permissioned, suitably de-identified examples in an approved local
location. No conclusion about representativeness can be read from a CSV alone.

## Export dry-run worksheet

An export suitable for the new `prepare` command is a flat CSV or JSONL with an
item ID, a human binary label and a finite numeric detector score. Specify both
label tokens and whether larger or smaller scores mean a stronger flag. Supply
a group column whenever several rows share a ticket, conversation or other
sampling unit; otherwise declare independent rows explicitly. Preserve a second
reviewer's label when present. Do not synthesize ground-truth labels from the
same detector score. An owner should approve any movement of real data.

Before using a real export, run the [complete synthetic export handoff](../examples/README.md#4-run-a-complete-synthetic-export-handoff)
from the repo root. It prepares a 400-row recoding of the existing seeded
`certifies.csv` example, replays preparation, certifies the prepared rows and
replays the certificate. This is the same synthetic evidence as the original
certificate example, not a second evaluation set or a human dry run. Retain
the source export, mapping, prepared package and certificate together; the
two replay commands check different boundaries. The earlier four-row
`export_sample.csv` is too small to establish a useful false-alarm bound; the
[grouped refusal and altered-source walkthrough](../examples/README.md#5-replay-a-refusal-and-detect-an-altered-source)
uses that same format example to show what the CLI does with insufficient
evidence and with changed retained source bytes.

### Blank first-run observation, for someone other than the author

Give the reviewer the repository, its setup instructions and the two linked
synthetic walkthroughs above. Ask them to run both without live command
coaching. Record the environment and exact point of any failure, including
the command, exit code, output and elapsed time. Do not replace a failed run
with the author's successful Phase 41 run. The synthetic files are practice
inputs; completing them is not a customer export trial.

After each outcome, ask the reviewer in their own words what can be concluded,
what cannot, and which files another reviewer would need. For the altered
source, ask why preparation replay and certificate replay give different
statuses. Record their explanation before correcting it; a successful exit
code alone does not establish that the evidence is understood.

| First-run observation | Record after the unaided trial |
|---|---|
| Date, reviewer role, host OS and Python version | |
| Setup steps and first command needing assistance | |
| Valid handoff: exact status, exit codes and elapsed time | |
| Grouped refusal: exact status, exit codes and elapsed time | |
| Changed-source replay: both statuses and exit codes | |
| Reviewer's explanation of what VALID and REFUSED permit | |
| Reviewer's explanation of the two replay boundaries | |
| Files they would retain or request from an analyst | |
| Friction seen directly, with command/output and permitted words | |
| What was observed vs coached, reported or inferred | |

Leave the table blank until another person completes it. Do not record their
name, customer records, prompts, scores or secrets in this repository.

Treat a real prepared package as sensitive if identifiers or groups are
sensitive. Excluded column names are listed, but their values are not copied
into the scored file; the source still contains them. The manifest binds
bytes for local replay but is neither an authenticity signature nor a
certificate. Run only on a new output path; preparation refuses to overwrite.

For a permissioned real dry run, record these facts *before* certification:

| Field | Owner's declaration |
|---|---|
| Export owner, allowed local path and retention/deletion rule | |
| Version of detector and threshold-selection process | |
| Source population and collection dates | |
| Sampling/selection procedure; holdout protection | |
| Independent unit and group field | |
| Positive/negative label definitions and adjudication | |
| Score direction, expected range and missing-value rule | |
| Second-review coverage and blinding | |
| Who may inspect the resulting package | |

The existing `certify` and `release` commands apply their own statistical
contracts to the canonical scored file. In particular, grouped release input
is unsupported; erasing a group column to make it run would invalidate the
declared unit. A prepared package alone makes no safety, compliance or
deployment claim. Document refusals as findings, not as errors to suppress.

## Evidence gate

By the October 14 checkpoint, seek five real conversations, two permissioned
usable exports and one named recurring review decision. These are targets, not
observations. Continue evidence-package engineering only if at least one
reviewer shows a gap in a concrete incumbent packet and can explain how the
new handoff would change a repeat decision. If access or labels do not exist,
record that limit and freeze speculative integrations. If an incumbent already
solves the handoff adequately, narrow or stop the product hypothesis.
