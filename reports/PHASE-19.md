# Phase 19 — replay an ordinary recheck from retained evidence

**Answer.** A new ordinary `warrant recheck` record binds the ordered effective
rows in the fresh scored file and can be independently recomputed with
`warrant verify-recheck`. The verifier needs the exact source certificate,
the retained fresh file and the same configuration. If the recheck claimed
that its source certificate was verified, it also needs the original scored
export and any frontier used to select the certificate. It writes nothing.
Chained records also carry the fresh-row digest, but the new command reports
`UNVERIFIED` for their sequential verdicts; one link is insufficient to
reconstruct a chain.

This is a narrow evidence improvement. It does not create demand, turn a
checksum into custody, or make the research prototype venture-ready. The
commercial gate in `reports/NEXT-STEPS-2026-09-17.md` still applies: talk with
validation and compliance leads about concrete wrong-control incidents before
expanding the surface area. The founder has reported no customer interviews,
design partners, paid pilots or revenue in this session. No deployment or
customer outcome is implied by these synthetic-file checks.

## Trigger and resulting behavior

In Phase 18, `recheck` named the exact certificate it read and could replay that
certificate before publication. A recipient could not tell whether a different
fresh batch was substituted after the JSON was written or independently
recompute the reported false-positive bound and drift result. A path in
provenance was a declaration, not a binding. This mattered because the
statistical verdict depends on fresh labels, scores, grouping and optional
second-review labels. The seeded review interval can also depend on row order.

The new `now.evidence_sha256` uses the certification digest's schema over the
ordered effective sequence: hashed item id, label, score, hashed group when
present, and `label_2` when present. It deliberately ignores file path, line
endings and ignored passthrough fields. It is a digest of the values consumed,
not the raw file bytes. The CLI writes it on both ordinary and chained
rechecks. A record issued before this change remains usable as a historical
measurement but cannot be called verified by the new command.

For an ordinary record, `verify-recheck` first compares the fresh-row digest
and source-certificate digest. It rejects a changed configuration hash. It
then calls the same `recheck_items` estimator that issued the result and
compares the complete material payload exactly: status, reason, prior warrant,
current bound, detection power and floor, drift, label sensitivity and second
review. It excludes the provenance declaration and refuses unexpected
measurement fields. `VERIFIED` exits 0, `MISMATCH` or `UNVERIFIED` exits 1,
and malformed input exits 2. The command does not create or overwrite files.
If `certificate_verification` reads `NOT_CHECKED`, its successful message
still says the source certificate was not checked at publication. A declared
`VERIFIED` cannot pass without independent replay of the original certificate.

An ordinary record that itself names a chain revocation also returns
`UNVERIFIED`, because the retained chain history is needed to substantiate
that lifecycle statement. The verifier does not consult a mutable chain-head
sidecar to infer current status. Chained publication, its lock and seal, and
the registered sequential statistic are unchanged. See `DECISIONS.md` 214.

## Research and demand boundary

This phase checked current first-party descriptions on 2026-09-28 rather than
treating “industry standard” as an untested feature list. [NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) describes documenting
test sets, metrics and tools under Measure 2.1 and monitoring under Measure
2.4 and Manage 4.1. That supports documenting and replaying a measurement;
it does not prescribe this digest or certify this product. [LangSmith's evaluation documentation](https://docs.langchain.com/langsmith/evaluation-types)
already describes offline and online evaluations, and [Braintrust's dataset documentation](https://www.braintrust.dev/docs/guides/datasets) describes
versioned datasets for evals. These are evidence that a generic evaluation
dashboard would enter an existing category, not evidence that a buyer wants
this particular control.

[SLSA provenance](https://slsa.dev/spec/v1.2/provenance) and its [source verification guidance](https://slsa.dev/spec/v1.2/verifying-source) distinguish
subject digests, provenance and verification against expectations. The repo's
digest is only a local checksum with a retained record and supplied inputs:
there is no authenticated producer, signature or external trust anchor.
[RFC 8785](https://datatracker.ietf.org/doc/rfc8785/) specifies JSON
canonicalization; this repo uses its existing deterministic Python JSON
encoding, not RFC 8785 JCS. The relevant product inference is to test whether
audit-ready, replayable evidence resolves a buyer's consequential workflow;
these sources do not establish willingness to pay or a defendable moat.

## Validation ledger

Four focused tests were written before implementation and failed for the
intended missing behavior: the fresh digest was absent and `verify-recheck`
did not exist. The first full evidence-suite run found a test-fixture collision,
not a product regression: the added chain case published a sidecar against the
same module-scoped certificate another existing chain case used. The new case
now copies the certificate into its own temporary directory. The evidence
suite then passed. Ruff and Python compilation passed for touched code.

The wider neighboring run found one outdated assertion in
`test_recheck_chain.py`: it compared CLI JSON, which already had Phase 18
certificate metadata, against a raw statistical result. The test now checks
that the statistical fields are unchanged and separately asserts the exact
certificate and fresh-row digests; the corrected case passed. The
selected-frontier replay case also passed, requiring the retained frontier
when source verification is claimed.

The evidence tests cover an ordinary replay, a changed fresh score, an edited
reported FPR, missing original evidence when the record claimed source
VERIFIED, a legacy missing digest, and refusal to claim a sequential replay
from one chained record. The installed-package test exercises the same command
through the wheel entry point. Adjacent certification, recheck and chain tests
are the regression boundary. This ledger does not count a test collection as
a passing execution. The installed-wheel source replay check passed; the
documentation and claim guards were run, with a stale displayed collection
count flagged for the inventory refresh. A full-suite or remote CI pass is not
claimed.

## What this does not establish

The checksum and replay prove consistency only between the files presented
to the verifier and the calculation in this source revision. A holder who can
rewrite every presented file can make a new coherent set. The CLI does not
authenticate authorship, time, detector identity, system version, production
traffic origin, label quality, representative sampling or custody. It does not
verify the current chain-head lifecycle, replay a chain's sequential test,
give an old unbound record a new evidence grade, or prove an issued warrant
was preregistered. `NOT_CHECKED` is never promoted to a historical source
check by the presence of an unrelated file. The recheck's VALID state is still
an absence of evidence of breach at its detection floor, not proof that every
smaller breach is absent.

No customer discovery, pilot, externally observed outcome, funded company,
remote CI run or production deployment is established here. A test passing on
the synthetic example is evidence about code behavior at that boundary, not
about market need or deployed reliability.

## Open items

The next evidence task is a chain replay design that receives the full ordered
history and every fresh batch, verifies seals and parent linkage, and then
recomputes the registered sequential statistic without selecting on later
outcomes. It needs a separate decision before code. A separate product task is
identity, custody and expiry, with a migration rule for older records; adding
an isolated signature field without key ownership and trust policy would not
solve custody. Fixed-threshold label sensitivity for release evidence, grouped
interval questions and previously noted monitor findings remain open.

The commercial next step is still 8–12 conversations with validation and
compliance leads, using a falsifiable incident question and the stop rule in
`reports/NEXT-STEPS-2026-09-17.md`. If the problem is not observed, engineering
more evidence infrastructure is not a substitute for demand.
