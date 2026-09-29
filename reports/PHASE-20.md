# Phase 20 — replay a retained linear chain prefix

**Answer.** `warrant verify-chain-recheck` can recompute a chained recheck's
sequential statistic when the caller retains the exact certificate, every
record from link 1 through the target, and each link's fresh scored file. It
checks sealed record and parent linkage, row bindings, configuration and
source-certificate grade before rerunning the existing measurement and feed
functions. A pass is explicitly scoped to the **presented prefix**. It does
not prove this is the current head, the only branch, or a history nobody
rewrote. The command is read-only and leaves the publication sidecar alone.

The commercial result is unchanged. The project still has no reported buyer
interviews, design partners, paid pilots or revenue. This narrows an evidence
gap for a prospective reviewer; it cannot establish demand or make the
startup fundable by itself. The customer-discovery stop rule in
`reports/NEXT-STEPS-2026-09-17.md` remains the first business gate.

## Problem and boundary

Phase 19 bound the ordered effective rows of every new recheck, then let a
reader replay an **ordinary** record. A chained result could pass
`warrant chain verify` for seals and structural linkage but its sequential
statistic was still taken on trust. That statistic depends on the sequence of
clean-negative units across files. Recomputing the last link alone would
silently accept an inherited statistic, exactly the kind of false assurance
this product should avoid.

The new command takes repeated `--pair RECORD FRESH` arguments in order,
starting at sequence 1. It demands a single sealed, linear prefix. A missing
parent, unsealed link, old link without `now.evidence_sha256`, or a declared
fork remains `UNVERIFIED`. A changed row, source certificate, config, seal,
material result or fully rehashed chain statistic is `MISMATCH`. Malformed
supplied JSON or scored data is an input error. A source certificate that a
link claimed was VERIFIED must itself be replayed from retained original
rows and any selected frontier. A NOT_CHECKED source claim stays visible in
the success message rather than being upgraded by a fresh-file replay.

The replay calls the same `recheck_items`, `start_chain`, `continue_chain`,
`feed` and `apply_chain` functions as publication. Its shared adapter reads
the warrant's budget, threshold, alpha, score distribution and reference
sample size for both ordinary and chained replay. It compares the entire
material recheck payload and full chain block exactly, including the
sequential statistic and units consumed. It does not introduce a second
estimator, choose a new horizon, change the registered chain rule, or rescore
any protected research test set. `DECISIONS.md` 215 registered the scope
before code.

## How to check a retained prefix

```bash
warrant verify-chain-recheck --warrant issued.json --pair week01.recheck-0001.json week01.csv --pair week02.recheck-0002.json week02.csv
```

If either link says `prior_warrant.certificate_verification: VERIFIED`, also
pass `--certificate-input original.csv`. A certificate selected from a
frontier additionally needs `--certificate-frontier frontier.json`. The
command returns 0 for VERIFIED, 1 for MISMATCH or UNVERIFIED, and 2 for
malformed input. It writes no verification artifact or chain-head update.
`warrant chain verify` remains the structural audit that needs no scored
files; it is useful for inspecting forks or damaged records but is not a
statistical replay. `warrant verify-recheck` remains scoped to ordinary
unchained records.

## Validation ledger

Focused tests were written before implementation and reproduced the missing
command. After implementation, the focused cases passed for a two-link
prefix, changed fresh rows, a resealed material-field edit, missing first
link, unsealed history and a source check that had been claimed VERIFIED.
A separate attack case changed a chain statistic, recomputed both its state
digest and whole-record seal, and first confirmed that the structural chain
audit still considered the resulting prefix clean. Arithmetic replay then
returned MISMATCH. A legacy link with its fresh-row binding removed and its
seal recomputed remained UNVERIFIED. Ruff passed on the touched code.

The first full repository run exposed three stale test expectations in
`test_grouped_agreement.py` and `test_label_sensitivity.py`. They asserted that
the *entire* certificate payload stayed equal when `label_2` changed. Decision
211–212 intentionally binds `label_2` into `input.evidence_sha256`, so the
digest must differ even though status, threshold, bounds and metrics do not.
The tests now assert both properties separately. Their two affected suites
passed after this correction; no certification calculation changed.

A new red test then exposed a result-grade bug in the chain replay verifier:
an unsealed link hid a definite digest failure in another link and produced
UNVERIFIED. The verifier now reports MISMATCH for a concrete integrity
failure, while a genuine presented fork remains UNVERIFIED because this
command supports a linear prefix only. Both new regression cases and the
neighboring chain, seal and recheck evidence suites passed. Ruff and
whitespace checks passed on the repairs.

The final clean-source inventory recorded **2,085 collected tests** from
`ec22b48` (inventory commit `2159949`), up from 2,083. Collection was not
called execution. The full repository suite on clean `2159949` then exited
**0**, with **one expected xfail and no failures**; its output showed no
skips. `python scripts/verify.py --no-activations` reproduced **92/92**
README claims and **25/25** frozen-score comparisons. The activation tier
was **SKIPPED**, and remote CI was not observed. The installed-wheel CLI
check and neighboring suites used synthetic scored files; none observes a
live customer detector.

## What this does not establish

An adversary controlling every presented file can rewrite all rows, records
and checksums into another internally consistent history. Nothing here
authenticates an author, timestamp, collection process, detector version,
deployment, representative sample or label truth. The horizon written into
link 1 is replayed as a declared input; its being chosen before data remains
an unauthenticated assertion. The command neither consults the mutable
chain-head sidecar nor proves no later record or competing branch was
omitted. A pruned, coherent prefix can pass. Declared forks and restart
histories are outside this command's positive verification grade rather
than treated as one ordinary linear sequence. A chain's statistical
guarantee still covers its sequential false-positive statistic under its
stated assumptions; drift revocation remains a separate rule.

These boundaries follow the distinction between a digest, provenance and
trust policy in [SLSA provenance](https://slsa.dev/spec/v1.2/provenance) and
the need to document measurements and monitoring in the
[NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/).
They are context for this implementation, not a claim of SLSA or NIST
conformance. The repo's canonical JSON encoding is its existing Python
format, not RFC 8785 JCS. Nor do such sources prove a buyer will pay for
this workflow.

## Open items

A complete fork-tree replay would need all retained branches and the
publication-head observations from each branch. An authenticated history
would also need external custody or signing, key ownership, trust anchors
and a policy for old unsigned records; merely adding another digest is not
that design. Detector and system identity, expiry, fixed-threshold release
label sensitivity, grouped interval questions and earlier monitor findings
remain separate technical gaps.

The immediate commercial next step is still 8–12 interviews with validation
and compliance leads about a specific consequential wrong control. If the
registered stop rule is triggered, treat this as research and do not infer
venture demand from additional code or synthetic tests.
