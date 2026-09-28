# Phase 17: replayable scored-file certificates

Implementation and evidence review, 28 September 2026. The previous
[product-state audit](PHASE-16.md) identified a concrete customer-path gap: a
retained `certify` record named a source file but did not bind the scored rows
or offer a command to check its arithmetic later. This phase adds that binding
and a read-only replay command. It does not turn Warrant into a deployed
enterprise service or authenticate a customer's evidence.

## Question and answer

Can a validation lead take a retained certificate, the scored export and the
same configuration and determine whether the certificate's material fields
follow from those rows? For newly issued certificates, yes: run
`warrant verify --warrant RECORD --input FILE`. If the budget was selected from
a frontier, also pass `--frontier RECORD`. The command returns `VERIFIED` only
after comparing the effective-row digest and recomputing the certificate; it
does not modify the input or record. A changed row or material certificate field
returns `MISMATCH`, while an old record without the new binding or a selected
record missing its frontier returns `UNVERIFIED`. Both exit 1. Unusable input
exits 2. Issuance and refusal continue to have their existing exit behavior.

## What changed

`controlplane/intake/certify.py` now writes `input.evidence_sha256` on both
VALID and REFUSED results. The digest covers each effective row in sequence:
hashed item id, label, score, optional hashed group and optional second label.
It omits the path and passthrough columns that the calculation ignores. This
is deliberately distinct from the older, order-independent frontier
`input_sha256`. The seeded bootstrap samples row positions, so reordering a
file can change finite interval results; the certificate binding must preserve
that order. DECISIONS 211 pre-registered the row binding and replay; DECISIONS
212 records the order correction before the verifier was implemented.

`controlplane/intake/verify.py` reads unambiguous JSON, rejecting duplicate
keys and non-finite JSON constants. It compares the retained row binding and
configuration hash, then runs the same `certify_items` path that issued the
record and compares material fields. For a selected budget it also checks the
retained frontier's input and configuration binding, digest, rows and selection
details. The selected record's `frontier_record_present` is contextual: it
records whether a sibling file was present at issuance, not a measurement, and
is excluded from replay comparison. The source path is also a declaration; the
verifier substitutes the recorded path when reproducing explanatory text so a
copied input file may still verify. It does not claim to verify the provenance
timestamp, author or Git state.

The top-level CLI now exposes `warrant verify`, distinct from `warrant release
verify` and `warrant chain verify`. README, input contract, runbook, product
state, architecture, code tour, artifacts guide, handoff map, FAQ, limitations,
testing guide and troubleshooting now describe the same behavior and boundaries.
The handoff's former gaps 1 and 6 are marked closed; identity, expiry,
authenticated custody and recheck linkage remain open. No frozen research
score, test-set result or published performance claim was changed for this
customer-path repair.

## Verification ledger

The feature was checked at the source boundary and through an installed
distribution. The focused source batch covering new digest and replay tests,
existing record parsing, and frontier selection passed **29 tests**. The
installed wheel/sdist regression that certifies, verifies and detects an edit
passed **1 test**. Ruff passed on the touched Python modules. These are local
observations from this worktree, not a claim that all declared CI jobs passed.
A documentation and claim guard batch passed **142 tests** and had one
expected stale-count failure: the README and Makefile still named the earlier
collected-test total after new cases were added. The clean-source inventory
generator must update those files before that guard can pass. Collection is
not execution.

The new tests exercise a moved but equivalent export, edited rows and a
certificate field, legacy records, malformed duplicate-key JSON, refusal
replay, and selected-frontier replay with a missing or edited frontier. Unit
tests also change each effective row field and reorder the rows, while checking
that ignored columns and file path do not affect the digest. The installed
test invokes the packaged command instead of importing the source tree. The
tests do not substitute for an independent validation dataset or customer
pilot; the example exports are synthetic.

## What this does not establish

A digest and recomputation are consistency checks over the files presented to
the verifier. Someone who controls both the scored export and certificate can
rewrite a coherent pair. No signature, trusted timestamp, access control,
custody service or detector identity was added. A VERIFIED result does not say
whether labels are correct, whether the scores came from the named detector,
whether the population matches production traffic, or whether the certificate
is still current. Legacy certificates cannot gain the binding retroactively;
they must be issued again from retained rows if replay is required. `recheck`
still reads the supplied warrant as written, so an operator should verify a
retained certificate separately before relying on it.

This phase did not run a customer dataset, browser service, full GPU pipeline
or remote CI. The independent grouped-interval and legacy-monitor findings
remain governed by the limitations and project review. Startup viability and
fundability still depend on buyer evidence, which has not been supplied.

## Open items

The next evidence step is a real validation workflow: identify the buyer and
decision, retain an unaltered scored export, record label provenance and test
whether the replay command helps that person complete an actual review. Before
claiming production custody, the product needs an authenticated signing and
identity model, expiry semantics, and a policy for old records. Before any
release decision uses a certify label-error ladder, the handoff's operating
point warning must be resolved; the current ladder belongs to certify's
selected threshold, not a separate release threshold. These are explicit
future decisions, not fields that documentation can infer.
