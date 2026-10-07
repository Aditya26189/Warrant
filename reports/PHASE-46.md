# Phase 46 — Bring the pilot protocol into line with the current product

The pilot protocol's old pre-outreach checklist described two chain integrity
defects in the present tense, even though the repository has since repaired
those paths. It also described a single handoff as though it contained both
certify and release evidence, and said customer data never leaves the machine
without naming the new local packet's original-source copy. This phase
corrects those statements in `docs/PILOT-PROTOCOL.md`. It changes no code,
statistical method, frozen result, customer record, or claimed market outcome.

## Section-by-section cross-check

| Protocol section | Current support or correction | What remains unobserved |
| --- | --- | --- |
| 1, facts/hypotheses | The original numeric rows link to decisions and artifacts. The no-network row is now scoped to the CLI, since a user can copy local files. | Whether a buyer values refusal or a JSON record. |
| 2, buyer/decision | The cited RBI press release established **draft** status at issuance. The text now labels any later final status unknown and requires a fresh primary-source check before a regulatory claim. | A named buyer, budget owner or present-law legal interpretation. |
| 3, data and units | Existing `docs/INPUT.md` still requires labels, polarity and group meaning. The new handoff copies the original export only with opt-in; the protocol now says this may include excluded sensitive columns and that transfer is the customer's decision. | A permissioned export, true sampling frame and retention authorization. |
| 4, blinded labels | Blind independent review, double-label sampling and adjudication are pilot requirements, not behavior that the CLI can infer from a CSV. This section was left as a procedure. | Actual reviewer identities, blinding and adjudication records. |
| 5, frozen criteria | Certify takes a budget argument; release registration retains a fixed-threshold contract. Neither by itself supplies a trusted timestamp. This section remains a pre-data protocol. | A real predeclared customer criterion and sign-off. |
| 6, baseline | The comparison requires the team's current packet, not an invented weak incumbent. No matched packet was present, so the test remains open. | Side-by-side reviewer outcome and time. |
| 7, reviewer effort | The review minutes and resulting cost are assumptions until measured on a team's own workflow. Existing sample-size calculations were not changed. | Label speed, ambiguity, repeat cost. |
| 8, success and failure | The four success conditions require retention, unaided replay, repeat use and a refusal path; none is established by synthetic tests. | Every human and commercial condition. |
| 9, limits | It already states that one free pilot cannot prove willingness to pay or a second segment. No new capability was inferred. | Price, budget and transfer. |
| 10, pre-outreach | Replaced obsolete present-tense chain defects with the dated repairs and residual limits; separated synthetic rehearsal from human first run; made record-specific missing fields explicit. | Unaided interpretation, real export and founder-selected approach. |
| 11, founder questions | These remain questions, not facts to fill with plausible answers. | Relationship, pilot terms and smallest valuable decision. |

The corrected chain account follows `DECISIONS.md` 194's 16–17 September
addenda: continuation after drift revocation was blocked, status was added to
the chain-head sidecar, and the latest record was sealed in full. Decision 207
later makes missing seals `UNVERIFIED`. [Phase 20](PHASE-20.md) supplies
arithmetic replay of a retained linear prefix. These fixes do not create a
signature, prevent someone with all copies from rewriting and rehashing them,
or prove that an unpresented fork or later link does not exist. The protocol
now says exactly that. It also distinguishes [Phase 41's](PHASE-41.md)
clean-clone synthetic valid/refused/changed-source journey from
[Phase 45's](PHASE-45.md) installed certify packet and the separate chain
replay. No one synthetic command sequence is being counted as a customer
trial.

The [handoff map](../docs/EVIDENCE-HANDOFF.md) remains the field-by-field
source for a validation team. A certify warrant and Phase 45 packet do not
contain authenticated system/detector identity or expiry. Release evidence
has those fields but tests a preregistered fixed threshold and uses a
separate label-audit companion; the new packet command does not package it.
This distinction matters more than collecting files into one directory: a
reviewer could otherwise mistake a selected certify threshold for an approved
release threshold on the same rows.

## Evidence ledger

The previous document was read in full before editing. `DECISIONS.md` 194,
207, and 215 and `reports/PHASE-20.md`, `PHASE-41.md`, `PHASE-45.md` were
cross-checked for chain, synthetic handoff and packet status. The current
RBI source cited in the protocol was searched via the official RBI domain on
7 October; the search did not establish whether a final text exists, so the
protocol now records current status as unknown rather than elevating the
old draft into a current obligation. No external legal requirement was added.

The local gate completed as follows:

| Command | Source | Observed result |
| --- | --- | --- |
| `python -m pytest tests/test_reports.py tests/test_docs_index.py tests/test_decisions_integrity.py -q -p no:cacheprovider --basetemp <workspace temp> -o addopts=--strict-markers` | Report and protocol draft | 174 passed, zero failures. |
| `python scripts/refresh_test_inventory.py` | Clean `7048b96` | Recorded 2,258 collected tests, `dirty=false`; this is collection only. |
| `python -m pytest tests/test_reports.py tests/test_docs_index.py tests/test_decisions_integrity.py tests/test_inventory_smoke.py tests/test_test_inventory.py -q -p no:cacheprovider --basetemp <workspace temp> -o addopts=--strict-markers` | Clean inventory commit `d9efdf4` | 178 passed in 15.30 s. |
| `python scripts/smoke.py` | Clean `d9efdf4` | 7/7; provenance reported `dirty=False`. |
| `python scripts/verify.py --no-activations` | Clean `d9efdf4` | Exit 0; claims 92/92, frozen-score comparisons 25/25, activations `SKIPPED|0/0`. |

The Phase 45 full-suite limitation remains: its new feature passed focused
and adjacent regression gates, while the most recent integrated full source
suite in the repository is Phase 43's prior commit. Editing the present
ledger adds no test cases, so the generated collection count is not refreshed
again; the phase-report and link checks are repeated after this edit.

## What this does not establish

Correcting a protocol does not validate the underlying statistics on bank
traffic, identify a buyer, grant data access, create a pilot, or demonstrate
willingness to pay. A drafted success rule has no observed outcome. A source
link to RBI does not prove present law; the final status and applicability
must be checked again by the team before any regulated use. Nor does this
phase re-run the GPU extraction or remote CI. The documented historical
chain fixes are local software behavior under retained evidence, not custody
over a customer's full audit history.

## Open items

The next human-facing check is an unaided reviewer run using
`reports/DISCOVERY-2026-10.md`, covering valid, refusal and altered-source
interpretation and the new packet. The first real packet requires its owner
to approve the export, label provenance, group unit, score direction,
sharing rule and exact recurring decision. Compare that packet with what the
team already uses; if its incumbent process answers the same question and a
reviewer gains nothing, do not add a native adapter. The founder must choose
outreach and pilot terms; no project file substitutes for that decision.
