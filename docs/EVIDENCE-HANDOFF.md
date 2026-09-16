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
| Command | `warrant release register / evaluate / verify` | `warrant certify`, `warrant recheck`, `warrant chain verify` |
| Question it answers | Did this frozen operating point meet criteria registered before a holdout was scored? | What threshold certifies a budget on this file, and does it still hold on the next? |
| Binds the scored data (digest) | **yes** | **no** |
| Binds system and detector identity with versions | **yes** | **no** |
| Carries an expiry | **yes** | **no** |
| Criteria registered before scoring | **yes**, in the contract | no; the budget is an argument |
| Carries label-quality evidence | **no** | **yes** (DECISIONS 197, 198) |
| Supports grouped (clustered) data | **no**, IID only | **yes** |
| Recomputes itself from the input | **yes**, `release verify` | chains only, `chain verify`, and without the statistics |

**The rule.** For a release decision, hand over the **release evaluation** as the
record of the decision, and attach the **certify warrant for the same scored
file** for its label-quality evidence. A handoff built from a certify warrant
alone cannot say which data, which system, which detector version, or until
when. A handoff built from a release evaluation alone cannot say how far the
result depends on the labels being right.

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
| Which warrant was rechecked | not applicable | not applicable | chained: `chain.warrant_sha256`; **not chained: ABSENT** -- only `prior_warrant.budget_fpr` and `prior_warrant.threshold` |

### 2.2 Data

| Evidence | Release evaluation | Certify warrant | Recheck |
|---|---|---|---|
| Digest of the scored rows | `data_sha256`, over sorted (hashed id, label, score); row order and extra columns do not change it | **ABSENT** -- `input.source` is the file name only | **ABSENT** |
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
| Method | protocol in `schema_version` (1 or 2); five two-sided Clopper-Pearson intervals at `alpha / 5` each | `certification.estimator`: one-sided Clopper-Pearson upper bound; `certification.alpha_governs` | revocation on the one-sided **lower** bound; `detection.note` |
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
| How many label errors the result tolerates | **ABSENT** | `labels.sensitivity`: two exact ladders (DECISIONS 197) | `labels.sensitivity`: errors to revoke (DECISIONS 198) |
| Second-reviewer agreement | **ABSENT** | `labels.second_review.kappa`, with interval and `n`, when a `label_2` column was supplied | same, on the recheck file |
| Disputed items | ABSENT | `labels.second_review.disputes` | same |
| Blind review | declared a caller responsibility in `assumptions` | not recorded | not recorded |

### 2.6 Time, expiry and reproduction

| Evidence | Release evaluation | Certify warrant | Recheck |
|---|---|---|---|
| When measured | `evaluated_at` | `provenance.timestamp_utc` | `provenance.timestamp_utc` |
| Expiry | `expires_at`; `verify` reports STALE once it has passed | **ABSENT** | **ABSENT** |
| Software and repository state | `software` (source hashes, runtime) | `provenance.git_commit`, `provenance.dirty`, `provenance.libraries`, `provenance.config_hash` | same |
| Integrity digest | `evidence_id`, over the whole sealed body | ABSENT | chained: `chain.state_sha256`, over the chain state only; not chained: ABSENT |
| Reproduce | `warrant release verify` recomputes every measurement field | re-run `warrant certify` on the same file; nothing checks that a retained warrant matches | chains: `warrant chain verify` checks linkage and digests, not the statistics |

---

## 3. Commands

### 3.1 Release (the record of the decision)

```bash
warrant release register --spec release-spec.json --development-ids dev.txt --holdout-ids holdout.txt --out release-contract.json
warrant release evaluate --contract release-contract.json --context context.json --input holdout-scores.csv
warrant release verify   --contract release-contract.json --context context.json --input holdout-scores.csv
```

`context.json` restates the identity fields from the scorer's actual run; each
must match the contract. The full procedure is in [RELEASE.md](RELEASE.md).

### 3.2 Certify and recheck (label quality, and monitoring)

```bash
warrant certify --input holdout-scores.csv --budget 0.05
warrant recheck --warrant holdout-scores.csv.warrant.json --input next-batch.csv
warrant recheck --warrant holdout-scores.csv.warrant.json --input week01.csv --horizon-labels <N from plan>
warrant recheck --warrant holdout-scores.csv.warrant.json --input week02.csv --since week01.csv.recheck-0001.json
warrant chain verify week01.csv.recheck-0001.json week02.csv.recheck-0002.json
```

To attach label-quality evidence to a release, certify **the same scored
holdout file** the release evaluated, with a `label_2` column for the
double-labelled items. Nothing binds the two records together. Record, in the
handoff, that both were produced from one file, and the file's release
`data_sha256`.

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
| Recheck | VALID, STALE, REVOKED, UNVALIDATED (the file had no negatives) | `controlplane/intake/recheck.py` |
| Release evaluation, protocol 2 | VALID, REFUSED, STALE (expired) | [RELEASE.md](RELEASE.md) |
| Release evaluation, protocol 1 (legacy) | as above, with UNVALIDATED for inconclusive or missing evidence | [RELEASE.md](RELEASE.md) |
| Chain verification | `clean` true or false, with findings | `controlplane/intake/chain_verify.py` |

Under release protocol 2, an operating point that was **never evaluated has no
evaluation record at all**. The absence of a record is not a refusal.

---

## 6. What no record carries today (OPEN)

Each is a gap between what a handoff needs and what the code writes. None is
filled by this page, and none may be filled by hand on a sheet.

1. **A certify warrant does not bind its data.** It names the file
   (`input.source`) but carries no digest of the rows, so nothing shows a
   retained warrant was issued on the file now presented. The function that
   computes such a digest already exists and is used by the frontier record
   (DECISIONS 195); it is not written into the warrant.
2. **A certify warrant and a recheck carry no expiry.**
3. **A certify warrant and a recheck carry no system or detector identity.**
4. **A recheck that is not chained does not name the warrant it rechecked.**
5. **A release evaluation carries no label-quality evidence**, and supports no
   grouped data. Attaching a certify warrant covers the first, joined only by
   the handoff's own statement that both came from one file.
6. **Nothing checks that a retained certify warrant matches a re-run**, the way
   `release verify` does for a release.
7. **No record carries an authenticated sign-off.** Digests are checksums, not
   signatures, throughout.

Closing 1 to 4 means adding fields to the certify and recheck records. That is
a schema change with its own decision, not documentation.
