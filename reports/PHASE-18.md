# Phase 18: rechecks name and can replay their source certificate

Implementation review, 28 September 2026. This phase follows the certificate
binding and replay work in [Phase 17](PHASE-17.md). The earlier handoff map
identified a narrower but consequential gap: an unchained `recheck` record
stored a budget and threshold without identifying which exact certificate it
read. A reviewer could not connect an ordinary recheck to its retained source
record after the files were moved or copied. The new certificate verifier also
existed as a separate command, but recheck did not use it.

## Question and answer

Can a recheck name the exact certificate it consumed, and can an operator
require the certificate's original scored evidence to replay before issuing a
new recheck? Yes for new CLI records. Every recheck now carries
`prior_warrant.warrant_sha256`, the canonical digest of the parsed certificate
it read. It also carries `prior_warrant.certificate_verification`: `NOT_CHECKED`
when the original scored export was not provided, or `VERIFIED` when the
operator supplied `--certificate-input FILE` and the certificate verifier
reproduced the material fields. A certificate selected from a frontier also
requires `--certificate-frontier RECORD` for this guarded mode. An edited
certificate, edited original scored row, missing frontier, legacy unbound
certificate or malformed input stops the command with exit 2 before it writes
a recheck record. The existing recheck verdict remains a separate measurement
of the **new** labelled file.

## Implementation and decision

[DECISIONS 213](../DECISIONS.md) registered this before code. It makes the
guarded source check opt-in because requiring an original export retroactively
would break older monitoring workflows whose export was not retained. Rather
than silently implying integrity, those workflows write `NOT_CHECKED`. The
existing chain already carries a warrant digest; the new `prior_warrant`
digest uses the same canonical JSON method so a chained record's two references
agree. Neither digest authenticates the record. Direct statistical callers of
`recheck_items`, which have no certificate object, do not claim a source digest.

The CLI reads the certificate through the strict JSON reader used by
`warrant verify`, rejecting duplicate keys and non-finite JSON constants. A
second malformed-input repair handles wrong-shaped `certification`, `input`
and `score_distribution` blocks without an uncaught traceback or a partial
output. This is a public-input boundary, not a statistical-method change.
No bound, interval, threshold, drift computation, chain statistic or
publication lock was changed. Existing unguarded rechecks still run, and
`--require-valid` still concerns the **new** recheck status rather than the
source check. Both ordinary and chained publication carry the new source
reference; chain publication keeps its existing whole-record seal and head
checks.

The [input guide](../docs/INPUT.md), [runbook](../docs/RUNBOOK.md),
[handoff map](../docs/EVIDENCE-HANDOFF.md), limitations, artifact guide and
product-state map now distinguish source linkage, optional certificate replay
and the unverified new-batch arithmetic. The handoff's item 4 is closed for
new CLI records. Other identity and custody absences remain explicit.

## Validation ledger

The new source tests were run before implementation and reproduced four
missing-behavior failures: absent warrant digest, absent guarded option,
unverifiable selected frontier and missing chained reference. A separate
malformed-block test reproduced three exit-1 tracebacks. These were not
assumed defects based on inspection alone.

After implementation, a focused batch of recheck evidence, existing recheck,
chain-lifecycle and certificate-verifier tests passed **30 tests**. The
strengthened evidence suite passed **6 tests**; after the malformed-block
repair, the new suite together with neighboring CLI-record cases passed
**16 tests**. Two final cases passed after adding explicit legacy refusal and
guarded chained publication. The installed-wheel test exercised certificate
issuance, guarded recheck and tampered-certificate refusal and passed **1
test** again after the final parser repair. Ruff and Python compilation passed
for the touched code. After a clean-source refresh, the generated inventory
recorded **2,067 collected tests**, up from **2,055**; that is a collection
count, not a full-suite execution result. The final documentation, claim,
decision, report, packaging and inventory guard batch passed **212 tests**.
`python scripts/verify.py --no-activations` reproduced **92/92** published
claims and **25/25** frozen-score comparisons. The activation tier was
explicitly SKIPPED.

The tests use the repository's synthetic scored example and a wheel installed
in an isolated customer environment. They check a changed certificate field,
changed original score, selected-frontier omission, legacy missing binding,
duplicate and non-finite JSON, wrong-shaped nested blocks, output absence on
failure, exact digest equality and source status in ordinary and chained
records. The source tests do not use customer-labelled traffic, a live scorer
or a long-running monitoring service.

## What this does not establish

`VERIFIED` in a recheck means only that its **source certificate** recomputed
from the original scored rows supplied at this invocation. It does not say
that the fresh recheck batch was bound to the resulting JSON, or that a
standalone verifier can later reproduce the recheck's bounds and drift result.
It does not authenticate who produced any file, establish when the certificate
was issued, prove a detector or system version, or show that the new batch came
from the same detector and population. A holder who can rewrite all presented
files can still produce a coherent set of checksums. `NOT_CHECKED` is an
explicit absence of source replay, not evidence of a mismatch or a pass.

The guarded option remains opt-in. Existing callers that omit it retain their
prior measurement behavior; a downstream approval process must decide whether
`NOT_CHECKED` is sufficient for its purpose. No customer pilot, buyer
interview, revenue, production deployment, full-suite run or remote CI result
is established by this phase.

## Open items

The next technical evidence gap is the **new recheck file**: bind its ordered
effective rows and provide replay of its statistical fields without changing
the chain's registered sequential method. Authenticated signing and custody,
detector and system identity, expiry and a migration policy for older records
remain separate design decisions. The fixed-threshold label-sensitivity gap
in the release handoff and the protected grouped-interval and legacy-monitor
findings also remain open. The commercial gate remains real conversations
with validation leads about a consequential wrong control, followed by an
observed pilot; additional records cannot establish demand on their own.
