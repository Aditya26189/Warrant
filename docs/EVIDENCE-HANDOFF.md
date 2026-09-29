# The evidence handoff: what to give a validation function, from the records Warrant writes

**What this is.** A validation function that relies on a Warrant result keeps a
record of it beside the release decision it supported. This page says which
record to retain, where each piece of evidence lives in it, how to reproduce it,
and -- as plainly -- what no record carries today. It adds no field and no
status. Every field named below is written by existing code, and every absence
is stated as one.

**What it is not.** A deployment approval, a regulatory certification, or a
signature. Warrant measures evidence about a detector on a file; the customer
retains the decision. The digests below are integrity checks against retained
copies, not signatures: anyone who can write the records can produce a
consistent set.

---

## 1. Which record to hand over

Warrant writes two families of record. They answer different questions, and
**neither alone carries every field a handoff needs.**

| | Release evaluation | Certify warrant, recheck, chain |
|---|---|---|
| Command | `warrant release register / evaluate / verify / label-audit / verify-label-audit` | `warrant certify`, `warrant verify`, `warrant recheck`, `warrant verify-recheck`, `warrant verify-chain-recheck`, `warrant chain verify` |
| Question it answers | Did this frozen operating point meet criteria registered before a holdout was scored? | What threshold certifies a budget on this file, and does it still hold on the next? |
| Binds the scored data (digest) | **yes** | certify and new recheck records: **yes**, ordered effective rows |
| Binds system and detector identity with versions | **yes** | **no** |
| Carries an expiry | **yes** | **no** |
| Criteria registered before scoring | **yes**, in the contract | no; the budget is an argument |
| Carries label-quality evidence | Evaluation: **no**; separate fixed-threshold label-audit companion: **yes**, descriptive only (DECISIONS 216) | **yes** (DECISIONS 197, 198) |
| Supports grouped (clustered) data | **no**, IID only | **yes** |
| Recomputes itself from the input | **yes**, `release verify` and `release verify-label-audit` for their respective records | certify: `warrant verify`; ordinary recheck: `warrant verify-recheck`; retained linear chain prefix: `warrant verify-chain-recheck`; `warrant chain verify` checks structure only |

**The rule.** For a release decision, hand over the **release evaluation** as the
record of the decision. Its separate label-audit companion describes sensitivity
at that release's fixed threshold. A certify warrant on the same scored file may
still be attached for threshold-independent reviewer agreement. A handoff
built from a certify warrant alone can identify the effective rows, but cannot
say which system, which detector version, or until when. A handoff built from a
release evaluation alone cannot say how far the result depends on the labels
being right; retain its label-audit companion for that description.

> [!WARNING]
> **A shared file is not a shared operating point.** `certify` **selects** the
> lowest threshold that meets a budget; a release evaluates the **one threshold
> registered before scoring**. On the same rows those are usually different
> thresholds, flagging different items, under different interval protocols --
> one-sided at alpha for certify, a simultaneous family at alpha/5 for release.
>
> So **only threshold-independent evidence transfers**: Cohen's kappa over the
> double-labelled items, its interval, the reviewed-pair counts and the 2x2
> table. Everything computed *at the certified threshold* -- the label-error
> ladders, the disputed flagged positives and unflagged negatives, the
> confidence after correction -- is evidence about **certify's** operating point
> and says nothing about the release verdict. Do not attach it as though it did
> (R9 of `reports/PROJECT-REVIEW-2026-09-23.md`).
>
> A worked case from that review: 96 negatives at 0.1, four at 0.9, twenty
> positives at 0.85. At budget 0.05 certify selects a threshold above every
> negative and flags **nothing**, so its ladder is about a cut that fires on no
> row; a release threshold declared at 0.8 flags 24 rows on the same file.
>
> `release label-audit` now computes a separate sensitivity at the release's
> registered threshold under its own interval protocol, after replaying the
> retained evaluation (section 6, item 8). It does not make `certify`'s ladder
> transferable or establish which primary labels are true.

### Who supplies and who retains each file

| File | Supplied by | Retained by | Why it must be kept |
|---|---|---|---|
| The scored export (`id,label,score`, and optional `group`, `label_2`) | the customer | the customer, **unaltered** | every result is a function of these rows; nothing else can reproduce them |
| Any extra columns in that export -- timestamps, model versions, reviewer names | the customer | the customer, in the same file | Warrant reads them and **keeps neither the names nor the values** in any record |
| Release specification, development and holdout id lists | the customer | the customer | together they fix the criteria and the holdout before scoring |
| Release contract (`release register --out`) | Warrant, from the customer's files | the customer, **before** evaluating | the evaluation binds to its digest; registration is not a trusted timestamp |
| `context.json` (scorer identity and scope) | the customer, from the actual run | the customer | `evaluate` and `verify` refuse a mismatch with the contract |
| Release evaluation (`*.evaluation.json`) | Warrant | the customer and the validation function | the record of the decision |
| Certify warrant (`*.warrant.json`) | Warrant | the customer and the validation function | label-quality evidence, and the reference every recheck compares against |
| Recheck records, and a chain's `*.chain-head` sidecar | Warrant | the customer, **every one** | a chain's guarantee holds for the chain as kept; a missing record is visible only if a kept one points at it |
| The handoff sheet itself | the customer's validation function | the validation function | the statement that joins a release evaluation to a certify warrant for one file |

Warrant stores nothing itself. No record leaves the machine it was written on
unless someone copies it.

### Digests describe rows, not file bytes

A release evaluation's `data_sha256` is computed over the **sorted rows** --
each row's hashed id, its label and its score. Two files with the same rows in
a different order, or with extra columns added or removed, have the **same**
digest. Two files that differ in one id, label or score have different digests.
It therefore identifies the evidence, not a byte-for-byte file. A validator who
needs the exact file retained should record its own file checksum beside the
sheet; no record carries one.

A certify warrant's `input.evidence_sha256` covers the **ordered effective row
sequence**: hashed id and group, label, score and optional second label.
Changing the sequence changes the digest because the seeded bootstrap uses row
positions. Moving the file, changing unused extra columns or changing file
format without changing effective rows does not. The frontier record's older
`input.input_sha256` identifies its rows without preserving order; both digests
are checked when verifying a certificate selected from a frontier.

Every digest in every record is a checksum, not a signature. It shows that a
retained copy is unchanged relative to another copy. It does not show who wrote
either, and someone who controls every copy can rewrite and re-digest them
consistently.

---

## 2. The handoff sheet, field by field

Each row is a piece of evidence a validator needs, and where it lives. A path
reads as JSON keys. **ABSENT** means no record written by this repository
carries it.

### 2.1 Identity and scope

| Evidence | Release evaluation | Certify warrant | Recheck |
|---|---|---|---|
| System and version | `identity.system_id`, `identity.system_version` | ABSENT | ABSENT |
| Detector and version | `identity.detector_id`, `identity.detector_version` | ABSENT | ABSENT |
| Scope | `identity.scope` | ABSENT | ABSENT |
| What the positive label means | `identity.positive_label` | ABSENT in the record; the input contract fixes `label` = 1 as "the detector should fire" (`docs/INPUT.md`) | ABSENT |
| Which contract | `contract_id` | not applicable | not applicable |
| Which warrant was rechecked | not applicable | not applicable | `prior_warrant.warrant_sha256` on every new CLI recheck; chained records also carry `chain.warrant_sha256` |

### 2.2 Data

| Evidence | Release evaluation | Certify warrant | Recheck |
|---|---|---|---|
| Digest of the scored rows | `data_sha256`, over sorted (hashed id, label, score); row order and extra columns do not change it | `input.evidence_sha256`, over ordered effective rows; `input.source` is a declared path only | `now.evidence_sha256` on new CLI records, over ordered effective rows; absent on legacy records |
| Was the source certificate replayed? | not applicable | `warrant verify` can replay it from retained rows | `prior_warrant.certificate_verification`: `VERIFIED` with `--certificate-input`, otherwise `NOT_CHECKED`; this does not verify the new rows |
| Where the data came from | `data_origin` | ABSENT | ABSENT |
| Sampling assumption | `sampling_assumption` in the contract; `assumptions` in the evaluation | ABSENT | ABSENT |
| Sampling unit | IID items only (`assumptions`) | `input.grouped`, `input.independent_units`, `input.independent_negative_units` | `now.unit` |
| Counts | `counts` | `input.n`, `input.n_positive`, `input.n_negative`, `input.base_rate` | `now.n`, `now.n_negative` |

### 2.3 Criteria and method

| Evidence | Release evaluation | Certify warrant | Recheck |
|---|---|---|---|
| The criteria | contract spec: `threshold`, `max_fpr`, `min_recall`, `alpha` | `budget_fpr`, `alpha`; no recall criterion | `prior_warrant.budget_fpr` |
| Registered before scoring | yes: the contract is written before `evaluate`, and its digest is bound in | no | no |
| Confidence | `family_confidence` | `alpha` (section 4, rule 1) | `alpha` from the warrant |
| Method | protocol in `schema_version` (1 or 2); five two-sided Clopper-Pearson intervals at `alpha / 5` each | `certification.estimator`: one-sided Clopper-Pearson upper bound; `certification.alpha_governs`; new `metrics_protocol` names the grouped descriptive-interval method (DECISIONS 219) | revocation on the one-sided **lower** bound; `detection.note` |
| Threshold | contract spec `threshold` | `certification.threshold` | `prior_warrant.threshold` |
| Picked off a frontier | not applicable | `selection` (DECISIONS 195); `frontier_record_present` | not applicable |

### 2.4 Results

| Evidence | Release evaluation | Certify warrant | Recheck |
|---|---|---|---|
| Status | `status` | `status` | `status` |
| Reason, verbatim | `checks[].reason` (protocol 2) | `reason` | `reason` |
| False-positive bound | `rates` (FPR with interval and denominator) | `certification.fpr_upper_bound`, `certification.false_positives_at_threshold` | `now.fpr_upper_bound`, `now.fpr_lower_bound`, `now.achieved_fpr` |
| Recall and precision, together | `rates` | `metrics.recall`, `metrics.precision`, each with `ci_low`, `ci_high`, `n` | ABSENT: a recheck measures the false-positive rate only |
| Flag rate and lift | `rates`, `lift` | `metrics.flag_rate`, `metrics.lift`, `metrics.lift_ceiling` | ABSENT |
| What the file could detect | not applicable | `certification.min_units_required` | `detection.smallest_detectable_rate`, `detection.power_against_1_5x_budget`, `detection.negatives_to_detect_1_5x_budget` |
| Distribution drift | ABSENT | `score_distribution` (the reference a recheck compares against) | `drift.verdict`, `drift.psi`, `drift.psi_null_p95` |

### 2.5 Label quality

| Evidence | Release evaluation | Certify warrant | Recheck |
|---|---|---|---|
| How many label errors the result tolerates | Evaluation: **ABSENT**; separate `*.label-audit.json` `sensitivity` gives first invalidating counts in two separate directions at the registered threshold (DECISIONS 216) | `labels.sensitivity`: two exact ladders (DECISIONS 197). **At certify's own selected threshold**, so it does not transfer to a release threshold | `labels.sensitivity`: errors to revoke (DECISIONS 198), at the warrant's threshold |
| Second-reviewer agreement | **ABSENT** | `labels.second_review.kappa`, with interval and `n`, when a `label_2` column was supplied. **Threshold-independent**, so this is the part that can be attached to a release | same, on the recheck file |
| Disputed items | Separate label audit: `second_review` counts observed disputes in the two adverse pools **at the registered threshold**; no truth or population inference | `labels.second_review.disputes`, counted **at the certified threshold** | same |
| Blind review | declared a caller responsibility in `assumptions` | not recorded | not recorded |

### 2.6 Time, expiry and reproduction

| Evidence | Release evaluation | Certify warrant | Recheck |
|---|---|---|---|
| When measured | `evaluated_at` | `provenance.timestamp_utc` | `provenance.timestamp_utc` |
| Expiry | `expires_at`; `verify` reports STALE once it has passed | **ABSENT** | **ABSENT** |
| Software and repository state | `software` (source hashes, runtime) | `provenance.git_commit`, `provenance.dirty`, `provenance.libraries`, `provenance.config_hash` | same |
| Integrity digest | `evidence_id`, over the whole sealed body | `input.evidence_sha256` covers the input rows, **not** the whole record | `prior_warrant.warrant_sha256` names the exact certificate; chained: `chain.state_sha256` over chain state; unchained: no whole-record seal |
| Reproduce | `warrant release verify` recomputes every measurement field | `warrant verify` recomputes material fields from retained scored rows and configuration; a selected budget also needs its frontier record | `warrant verify-recheck` recomputes ordinary records; `warrant verify-chain-recheck` recomputes a retained linear prefix from every batch; `warrant chain verify` checks linkage and digests without scored rows |

---

## 3. Commands

### 3.1 Release (the record of the decision)

```bash
warrant release register --spec release-spec.json --development-ids dev.txt --holdout-ids holdout.txt --out release-contract.json
warrant release evaluate --contract release-contract.json --context context.json --input holdout-scores.csv
warrant release verify   --contract release-contract.json --context context.json --input holdout-scores.csv
warrant release label-audit --contract release-contract.json --context context.json --input holdout-scores.csv
warrant release verify-label-audit --contract release-contract.json --context context.json --input holdout-scores.csv
```

`context.json` restates the identity fields from the scorer's actual run; each
must match the contract. The full procedure is in [RELEASE.md](RELEASE.md).

### 3.2 Certify and recheck (label quality, and monitoring)

```bash
warrant certify --input holdout-scores.csv --budget 0.05
warrant verify --warrant holdout-scores.csv.warrant.json --input holdout-scores.csv
warrant recheck --warrant holdout-scores.csv.warrant.json --input next-batch.csv --certificate-input holdout-scores.csv
warrant verify-recheck --record next-batch.csv.recheck.json --warrant holdout-scores.csv.warrant.json --input next-batch.csv --certificate-input holdout-scores.csv
warrant recheck --warrant holdout-scores.csv.warrant.json --input week01.csv --horizon-labels <N from plan>
warrant recheck --warrant holdout-scores.csv.warrant.json --input week02.csv --since week01.csv.recheck-0001.json
warrant verify-chain-recheck --warrant holdout-scores.csv.warrant.json --pair week01.csv.recheck-0001.json week01.csv --pair week02.csv.recheck-0002.json week02.csv
warrant chain verify week01.csv.recheck-0001.json week02.csv.recheck-0002.json
```

The release label audit binds the exact contract, evaluation and effective
scored rows, including optional `label_2`. Retain and verify it beside the
release evaluation. A separate certify warrant on the same holdout can add
threshold-independent second-review agreement; no automatic join binds those
two record families. Record that both came from one file if attaching both.

For a selected budget, retain and pass its frontier record to `warrant verify`
with `--frontier`. A replay checks row and arithmetic consistency; it does not
authenticate a record's author or certify the actual deployment identity.
For the guarded recheck line above, pass the same frontier with
`--certificate-frontier`. Omitting `--certificate-input` still measures the
batch but records `NOT_CHECKED` source evidence instead of `VERIFIED`. Both
forms bind the new batch's effective rows. `verify-recheck` replays an ordinary
record from those rows, the exact certificate and configuration. A record that
claims source `VERIFIED` needs the original scored export again, plus its
frontier if selected. A chained record needs its retained sequential history;
`verify-recheck` reports `UNVERIFIED` for it. Supply every link and fresh file
from sequence 1 to `verify-chain-recheck` to replay one linear prefix. A pass
does not establish that no later link or other branch exists.

**Attach the agreement, not certify's ladder.** Kappa, its interval, the reviewed-pair
counts and the 2x2 table are computed over the double-labelled items and involve
no threshold, so they describe the labels of that file whatever operating point
is used. The sensitivity ladder and the disputed counts are computed at the
threshold `certify` selected, which is not the threshold the release registered;
attaching them as evidence for the release verdict overstates what was measured
(R9). Name the certified threshold beside anything you do attach, so a reader can
see which cut it belongs to. The separate release label audit supplies its own
fixed-threshold sensitivity; it does not transfer certify's ladder.

---

## 4. Rendering rules for the sheet

The handoff restates records; it must not restate them more strongly than they
are.

1. **Show a level as a confidence, beside the raw value.** A record's `alpha` is
   the exact level used and can read `0.050000000000000044` in floating point.
   Write "95% confidence" next to it, so nobody takes the digits for a typo, and
   do not round the stored value.
2. **Every rate carries its interval and its `n`.** A rate without both is not
   copied onto the sheet.
3. **Recall and precision appear together or not at all.** No blended score.
4. **Keep each figure's type.** Fields tagged `EXACT` or `ESTIMATED` keep the tag.
5. **Quote reasons verbatim.** A refusal's reason is the evidence; a summary of it
   is not.
6. **Name the protocol with the status.** A release VALID and a certify VALID are
   verdicts under different statistics and are not interchangeable
   ([RELEASE.md](RELEASE.md)).
7. **State what was not measured.** Every ABSENT row in section 2 that the
   validator's decision depends on goes on the sheet as an absence, not as a
   blank.

## 5. Statuses, as each record uses them

This page introduces none. For reference:

| Record | Statuses | Where the meaning is defined |
|---|---|---|
| Certify warrant | VALID, REFUSED | `docs/INPUT.md` |
| Certify verification | VERIFIED, MISMATCH, UNVERIFIED | `docs/INPUT.md` |
| Recheck | VALID, STALE, REVOKED, UNVALIDATED (the file had no negatives) | `controlplane/intake/recheck.py` |
| Release evaluation, protocol 2 | VALID, REFUSED, STALE (expired) | [RELEASE.md](RELEASE.md) |
| Release evaluation, protocol 1 (legacy) | as above, with UNVALIDATED for inconclusive or missing evidence | [RELEASE.md](RELEASE.md) |
| Chain verification | `clean` true or false, with findings | `controlplane/intake/chain_verify.py` |

Under release protocol 2, an operating point that was **never evaluated has no
evaluation record at all**. The absence of a record is not a refusal.

---

## 5a. A walkthrough, from a clean checkout

The two input files below are **synthetic**: `examples/` holds generated
demonstration data (`examples/README.md`). Their figures describe the generator,
not any detector, and none is quoted here. Each step says what outcome to expect
and where in the record to find it.

**A certificate.**

```bash
python warrant.py certify --input examples/certifies.csv --budget 0.05
```

Expect `status: VALID`. The threshold is at `certification.threshold` and the
bound at `certification.fpr_upper_bound`. Recall and precision, each with an
interval and `n`, are under `metrics`, and the label-error ladders under
`labels.sensitivity`. The file's `captured_at` column appears nowhere in the
record.

**A refusal.**

```bash
python warrant.py certify --input examples/refuses.csv --budget 0.01
```

Expect `status: REFUSED`, and exit code 0 -- a refusal is a result, not an
error. `reason` names the clean negatives the budget needs against those the
file has. `labels.sensitivity` says it was not computed, and why.

**Malformed input.** A label that is not 0 or 1, a duplicate id, or a `label_2`
column blank on every row is rejected with exit code 2 and a message naming the
row and the column. No record is written. That is an unreadable file, not a
verdict on the detector.

**Grouped input.** Add a `group` column naming each item's source.
`certify` and `recheck` then work in groups, and reject groups of unequal size
with exit code 2. `release` rejects grouped input outright; it supports
independent items only.

**Expiry.** Only a release contract carries one. `release verify` reports
`STALE` once `expires_at` has passed. There is no quick way to show this
without waiting, so no command is given. A certify warrant cannot expire; it
carries no expiry (section 6).

**A release.** Use the procedure in [RELEASE.md](RELEASE.md). It needs a
specification, disjoint development and holdout id lists, and a context file,
which are the customer's to prepare.

## 6. Handoff gaps and closures

This list tracks the gaps identified at handoff. Closed items cite the code
change; open fields cannot be filled by hand on a sheet.

1. **Closed: a certify warrant binds its effective rows.**
   `input.evidence_sha256` and `warrant verify` cover the ordered effective
   sequence (DECISIONS 211–212). This is a checksum, not authenticated custody.
2. **A certify warrant and a recheck carry no expiry.**
3. **A certify warrant and a recheck carry no system or detector identity.**
4. **Closed for new CLI records: an unchained recheck names its warrant.**
   `prior_warrant.warrant_sha256` uses the chain's canonical record digest;
   `certificate_verification` states whether the original scored export was
   supplied and replayed (DECISIONS 213). Neither field authenticates the
   writer. The new file is separately bound by `now.evidence_sha256`.
5. **A release evaluation carries no label-quality evidence**, and supports no
   grouped data. A separate, replayable `*.label-audit.json` now describes
   fixed-threshold primary-label sensitivity and observed disputes, but does
   not change the release status or establish label truth (DECISIONS 216).
6. **Closed: a retained certify warrant can be replayed.** `warrant verify`
   recomputes its material fields from the retained rows and configuration.
   Legacy records without the binding remain unverified (DECISIONS 211–212).
7. **No record carries an authenticated sign-off.** Digests are checksums, not
   signatures, throughout.
8. **Closed for a registered release operating point only:** `release label-audit`
   computes sensitivity at the fixed threshold from that contract after replaying
   its complete evaluation. It is not an arbitrary-threshold certificate and
   does not license borrowing `certify`'s selected-threshold ladder (R9 of
   `reports/PROJECT-REVIEW-2026-09-23.md`).

9. **Closed for new ordinary records: the fresh recheck file is bound and replayable.**
   `now.evidence_sha256` identifies ordered effective rows and
   `warrant verify-recheck` recomputes ordinary records (DECISIONS 214).
   Chained records carry the binding but are not sequentially replayed by that
   command. `warrant verify-chain-recheck` replays a complete sealed linear
   prefix from retained batches (DECISIONS 215); forks and missing history
   remain unverified. `warrant chain verify` remains structural.

Items 2–3 and 7 remain open. Item 5 is only partly closed: the separate audit
does not establish reviewer correctness or add grouped release inference.
