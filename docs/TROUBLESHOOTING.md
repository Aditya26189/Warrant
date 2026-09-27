# TROUBLESHOOTING.md — what a failure means

<sub>[🏠 Project README](../README.md) · [📚 Documentation index](README.md) · [🗺️ Diagrams](DIAGRAMS.md) · [📖 Glossary](GLOSSARY.md)</sub>

This codebase crashes on purpose. A silent wrong answer is worse than a stack
trace, so most of what looks like a bug here is a boundary refusing to let a
misleading number through.

Read the exception's own type first: each one exists so a caller can tell *"your
input is wrong"* from *"the code is wrong"*.

**Contents:** [Refusals are not errors](#first-a-refusal-is-not-an-error) · [The `warrant` command](#the-warrant-command-every-message-and-what-to-do) · [Exceptions](#the-exceptions-and-what-each-one-is-defending) · [Control failures](#when-a-control-fails) · [Verification](#when-verify-fails) · [Environment](#environment-problems) · [Not a bug](#things-that-look-broken-and-are-not)

---

## First: a refusal is not an error

`REFUSED` is a **result**, not a failure. It means the machinery ran correctly
and the evidence did not support a warrant. Three of the detectors this project
pointed itself at are refused, and those refusals are among the most useful
outputs in the repository.

Nothing promotes a refusal. There is no `force`, no `--override`, no
`min_confidence` to relax; `issue_or_refuse` takes no argument that could. If
you are looking for one, the thing to change is the evidence — a bigger
envelope, a better detector, a different operating point — not the call.

The refusal reason names **every** failed criterion, not the first one.

---

## The `warrant` command: every message, and what to do

Every message starts `warrant:` and the exit code says which kind it is. **`0` is
a result** -- a warrant, a refusal, a revocation, or a verification with findings.
**`2` is input the command could not use**: nothing was certified or recorded, and
the fix is to the input, not to the detector. **`1` appears only when you passed
`--require-warrant`, `--require-valid` or `--require-clean`** and did not get what
you required.

### Reading your file (exit 2)

| The message says | It means | Do |
|---|---|---|
| `is missing required column(s)` | the file lacks `id`, `label` or `score` | Rename or add the columns; the message lists what it found |
| `label is ..., which is not 0 or 1` | a label is a probability, a class name or blank | Labels are binary: `1` means the detector **should** fire. `1.0` is accepted; `0.7` is not rounded |
| `score is ..., which is not a number`, or `A NaN or infinity cannot be ordered` | a score cannot be placed against a threshold | Fix the export. Rows are refused, never dropped |
| `column 'id' is empty` (or `label`, `score`) | a required cell is blank | Blanks are not filled in for you |
| `Ids must be unique` | two rows share an id | Two rows for one id make two claims about one item; the tool will not pick one |
| `duplicate CSV column(s) ... after whitespace normalization`, or `duplicate JSON field` | two columns, or two keys in one JSON line, share a name, so one value would silently win | Rename or remove one. `score` and ` score ` are the same column |
| `every CSV header must name a non-blank column` | a header cell is blank, which could hide an extra field | Name the column, or remove it from every row |
| `expected N CSV fields, found M` | a row has missing or extra fields | Fix the export: a field is neither filled in nor dropped |
| `is not valid CSV` | the file cannot be parsed as CSV, for example an unclosed quote | Fix the quoting at the line named |
| `every label is 0` (or `1`) | one class only | A false-positive rate needs negatives and recall needs positives; supply both |
| `'group' is present as a column but empty on this row` | a partly grouped file | Group every row, or drop the column |
| `'label_2' is present as a column but blank on every row` | an export artefact, not a second review | Fill in the double-labelled items, or drop the column |
| `has extension ...; this phase reads .csv and .jsonl only` | another format | Export CSV or JSONL |
| `the 'group' column has unequal group sizes` | clusters of different sizes | A cluster-level bound would promise a tighter rate than the data supports. Equalise the groups, or drop the column and accept that items are treated as independent |
| `budget must be a false-positive rate in (0, 1)` | `--budget` out of range | `0.05` means at most 5% of clean items flagged |

### Certifying

| You see | It means | Do |
|---|---|---|
| `WARRANT: REFUSED` and `clean negative units are needed` (exit 0) | **a result**: this file cannot support this budget at 95% confidence, however good the detector is | Supply more clean negatives, or ask for a looser budget. The message names both numbers. Nothing overrides it |
| a VALID warrant with `below 90% at 1` in the label-error section | the certificate sits at the edge of its budget, and one mislabelled flagged item would move it | Read it before relying on the warrant; double-label the flagged positives with `label_2` ([INPUT.md](INPUT.md)) |
| `notice: ... was run on this file. If you picked this budget from it` | a frontier record for the same file sits beside it | If you chose the budget by reading the frontier, certify with `--from-frontier` so the warrant holds at the frontier's level |
| `was not produced from ...` or `does not reproduce from ...` with `--from-frontier` | the frontier record is for another file, or was edited or truncated | Rerun `--frontier` on this file |

### Rechecking

A recheck reports two separate things, the false-positive bound and the score
distribution, and each has a different fix.

| Status | It means | Do |
|---|---|---|
| `VALID` | nothing in this file establishes a breach | Read "What this file could have caught": below that rate a real breach also returns VALID. It is an absence of evidence, not evidence of absence |
| `STALE`, measured rate above the budget | the rate is above the promise but its lower bound does not establish a breach | Recheck on more data before relying on the warrant |
| `STALE`, empty bins | the new file has no data where the reference had mass | Check the file is complete. This is missing data, not a measured shift |
| `STALE`, shifted distribution | the distribution moved beyond its noise but not decisively | Re-certify sooner than planned |
| `REVOKED`, lower bound above the budget | the data **establishes** the rate exceeds the promise | Re-certify. The warrant is not true of this traffic |
| `REVOKED`, distribution moved | the traffic is no longer the traffic the warrant describes | Re-certify on current traffic |
| `UNVALIDATED` | the file had no negatives | Nothing was tested; this is not evidence the promise holds |
| `REVOKED`, and the reason names a chain record | this warrant's own chain revoked it earlier, and the sidecar beside the warrant still says so. The measurement from this file is reported in full below the reason, including the verdict it produced on its own | Re-certify. A later file cannot restore a revoked warrant, whatever it measures (`DECISIONS.md` 210) |

### Continuing a chain (exit 2)

| The message says | It means | Do |
|---|---|---|
| `this warrant's chain REVOKED it at its latest record ... with or without --fork` | the chain's latest record revoked the warrant | **Re-certify** and start a new chain on the new warrant. `--fork` cannot reopen a revocation |
| `the --since record REVOKED this warrant` | the record you are continuing from revoked it | As above |
| `the --since record's seal does not reproduce` | the record was edited after it was written | Continue from the unedited record. The seal is a checksum, not a signature |
| `the chain state does not reproduce its digest`, or `reads ... but its state rebuilds` | the chain block was edited | As above |
| `the chain's ... is ..., not a number` (or `outside`, `not an integer`, `not a finite number`) | a value in the chain block is malformed | The record was damaged or written by something else. Do not continue from it |
| `the chain's ... is an integer of N digits, which is not representable as a finite number` | a number in the record is too large for any arithmetic to use. Valid JSON carries integers of any size; this one cannot be a threshold, a count or an alpha | The record was damaged or written by something else. `chain verify` reports it as `malformed` rather than crashing (`DECISIONS.md` 208) |
| `a chain already exists for this warrant` | a head sidecar is present | Continue with `--since` on the latest record, or start another chain deliberately with `--fork`; the fork is recorded |
| `the --since record is not the chain's latest record` | continuing from it would drop every later link | Use the latest record, or `--fork` deliberately |
| `this chain had a head when its last record was written and none is present now` | the sidecar was deleted, or the warrant was moved or copied | Restore the sidecar, or `--fork` knowingly |
| `unit(s) in this file were already consumed by this chain` | the same item ids were fed before | Each labelled item counts once. Ids must be stable and unique across all of a chain's files |
| `this chain has consumed its N units` | the declared horizon is used up | Its guarantee does not extend further. Re-certify and start a new chain |
| `already exists. A chained recheck never writes over a record` | the output name is taken | Choose another `--out`. Each link is evidence the next depends on |
| `the chain runs at alpha=..., the warrant at ...`, or `belongs to a different warrant record` | the record is from another warrant or level | Continue a chain only with the warrant it was started on |

A chained write also uses `.chain-lock` and, while publication is pending,
`.chain-pending` beside the canonical warrant path (DECISIONS 206):

| Message | What to do |
|---|---|
| `chain publication is busy or its lock is unavailable` | Retry after the active writer exits. If it persists without a writer, check filesystem lock support and permissions. Do not delete the lock file to bypass it |
| `recovered interrupted chain publication at ...` | The original result was recovered; this invocation exits 2 and creates no additional link. Inspect the named record, then continue with `--since` if eligible |
| `conflicts with the pending record`, `head changed outside the pending publication`, or an invalid intent | Preserve the warrant, pending intent, head and records for investigation. Restore only a verified original copy; do not discard the journal or overwrite evidence to force progress |

The lock file remains after successful commands; its presence does not mean a
writer is active. Recovery requires the original output location and supporting
local filesystem operations. These guarantees are not a distributed lock or a
universal power-loss guarantee.

### Verifying a chain

`warrant chain verify` exits 0 **with findings**, because findings are a result.
Use `--require-clean` to make findings or any missing record seal exit 1.

| Finding | It means |
|---|---|
| `digest` | a record was edited after it was written: its seal, its chain-state digest or a derived field does not reproduce |
| `malformed` | a record holds a value of the wrong type or outside its domain, or one no JSON record can carry |
| `continued_after_end` | a link follows a record that revoked the warrant -- by the chain's statistic or by a moved distribution -- or that ended the chain |
| `fork`, `restart` | two records continue one record, or two chains were started for one warrant. Two branches are two tests |
| `missing_link` | a record continues one that is not in the set, or one that was edited |
| `sequence`, `extension` | a link is misnumbered, or does not extend its predecessor |
| `mixed_warrants`, `duplicate` | records from several warrants, or one record under several paths |

**`unsealed` means unknown integrity.** Absence cannot establish the record's
age or distinguish legacy data from a removed seal. Available structural checks
are still reported, but `clean` is false and `--require-clean` exits 1. Inspection
without that flag still exits 0 with the explicit result. The separate
`structurally_clean` field never substitutes for full record integrity.

`integrity_status` is VERIFIED when the record/chain checksum checks reproduce,
UNVERIFIED when seal evidence is missing, and FAILED when an integrity or
malformed-data check fails. VERIFIED does not authenticate an author or recompute
the statistics. Other structural findings still prevent `clean`.

An unsealed `--since` record cannot be continued, even with `--fork`. Inspect it,
recover a verified retained original if available, or re-certify and begin a
new chain. Do not add a new seal and call that proof of the original evidence.

---

## The exceptions, and what each one is defending

| Exception | Raised when | What it is protecting |
|---|---|---|
| `ConfigError` | the config is missing, malformed, or self-inconsistent | Its own type so you can tell "your config is wrong" from "the code is wrong". Config invariants are checked in `__post_init__`, each naming the invariant it enforces |
| `PaddingError` | a tokenizer is not padding on the left | The highest-value check in the extraction path. With right padding, position −1 is a pad token, activations are meaningless, nothing else raises, and AUROC lands near chance |
| `ProbeError` | a probe would be fitted or scored in a way that leaks or lies | Train-only fitting, and selection that never touches test |
| `AggregationError` | a sequence cannot be pooled as asked | Silent reshaping would change what the detector *is* while keeping its id |
| `MetricError` | a metric would misrepresent what is known about it | An `ESTIMATED` rate without an interval, an `EXACT` count with one, or a blended F1 — none can be constructed |
| `MeasurementError` | a statistic cannot be computed on the data given | e.g. quantities that are undefined on a single-class envelope, refused rather than emitted as a plausible-looking 0.5 |
| `WarrantError` | a warrant would claim more than its evidence supports | A refusal with no reason, or a key missing its envelope |
| `EvalSetError` | an eval set or its cache is inconsistent | A content hash that does not match, or a cache that is not the one the set names |
| `LabelCategoryError` | a detector is pointed at a set whose labels mean something else | Recall against labels that mean something else is not recall — a PII detector measured against hallucination labels |
| `InputError` | a customer's scored file does not meet the input contract | Its own type so that *"we cannot read your file"* is never confused with *"your detector was refused"* |
| `ChainError` | a chained recheck cannot be started, continued or fed as asked | A revoked warrant resumed, an edited record continued, an undeclared fork, a unit counted twice |
| `MalformedChainError` | a chain block's value is the wrong type, out of its domain, or not representable as a finite number | Refused before any arithmetic, so a bad value never reaches a division or the digest (`DECISIONS.md` 208) |
| `RecordError` | a file handed to `chain verify` is not a readable chained recheck record | Unreadable input exits 2 rather than reading as a clean verification |
| `BundleError` | a policy bundle is malformed or internally inconsistent | A deploy error rather than a rule silently falling through to its default |
| `WarrantResolutionError` | a well-formed bundle asks for a claim the matrix cannot back | **Never a warning.** The bundle does not load. This is the fail-closed path |
| `LedgerError` | an append would break the ledger's guarantees | The hash chain |
| `OverrideError` | an override record was written that the estimator could not use | A record missing its stratum or draw probability would silently bias any recall computed from the review queue |
| `UnclassifiedEntityError` | a detector emitted an entity the adapter has no classification for | Raised rather than filtered — quietly dropping an entity type changes measured recall |
| `DraftDivergedError` | the prompts about to be scored are not the prompts that were frozen | The pilot's pre-registration. Scoring a changed draft against a frozen decision rule is the thing pre-registration exists to prevent |
| `CertificateError` `FindingError` `SerdeError` | a record type would be built in violation of its own contract | Records are frozen dataclasses validated at construction |

---

## When a control fails

Any of the five failing refuses the warrant. What each failure actually tells
you:

| Control failed | Read it as |
|---|---|
| `padding_fault` | Either the padding really is wrong, **or** the check no longer discriminates. The control deliberately builds a right-padded variant and requires it to be *rejected*; if that variant is accepted, the tolerance is worthless and the run stops |
| `label_shuffle` | AUROC survived permuting the labels. The signal is an artefact of the fitting, not of the data |
| `null_feature` | A probe on noise scored outside the null band — the pipeline is manufacturing signal. Note the band is *simulated at construction*, not looked up; the closed form can understate the spread at low feature dimension |
| `canary` | The detector missed items on a deliberately easy set. A regression tripwire, so treat it as "something broke", not as a measurement |
| `determinism` | Two runs at one seed differed. Look for unseeded randomness, dict ordering, or a device-dependent kernel before anything else |

---

## When `verify` fails

`verify.py` prints the tier, the artifact, the field, and both values. The fix
is never "edit the number until it matches".

| Tier | Failure means |
|---|---|
| 1 — claim table | A number in `README.md` no longer matches the artifact and field it names. Either the artifact was regenerated and the README was not, or someone typed a number by hand |
| 2 — frozen scores | A metrics block no longer follows from the per-item scores behind it. This is the case tier 1 cannot see: a README and its artifacts that went stale *together* |
| 3 — activations | The frozen scores no longer re-derive from the cached activations |
| 3 reports SKIPPED | **Not a failure.** The caches are gitignored, so a fresh clone cannot run this tier. The final line names any tier that did not run, so a skip is never mistaken for a pass |

If tier 1 fails after you regenerated an artifact on purpose: re-run the stage,
then update the README row, then re-run `verify`. The claim table is the
contract, and it is parsed rather than trusted.

---

## Environment problems

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError` on a controlplane import | not installed, or the wrong interpreter | `pip install -r requirements.lock.txt` inside the venv you are actually running |
| A Presidio result differs from the published one | `presidio-analyzer` is not at the pinned version | The finding is a statement *about that version*. Reinstall from `requirements.lock.txt`; a test fails when the environment drifts from the pin |
| Rego evaluation unavailable | `regopy` missing | It is a pip wheel, not an OPA binary. Install the requirements |
| CUDA out of memory during extraction | 7B plus a batch does not fit | Lower `--batch-size` (8 → 4). Do not disable quantisation on a 16 GB card |
| A stage cannot find a cache | extraction has not run here, or `--cache-dir` differs | Caches are gitignored by design. Either run `00_extract.py` or use the CPU tiers, which do not need them |
| No network on the machine that runs extraction | offline node | Pre-download into `HF_HOME`, then set `HF_HUB_OFFLINE=1` and `HF_DATASETS_OFFLINE=1`. [SETUP.md](SETUP.md) §3 |
| A test suite reads as green but something failed | you piped the command | `cmd \| tail` reports *tail's* exit status. Use `sh scripts/run.sh <cmd>` |
| `dirty: true` in a fresh artifact | the tree was not clean when the script ran | Commit, re-run, then commit the artifacts separately. The dirty flag excludes `results/` and nothing else |
| Two artifacts disagree about one number | they were produced under different config hashes | Compare the `provenance.config_hash` fields. Re-run the whole chain before quoting anything |

---

## Things that look broken and are not

- **Most of the warrant matrix is `UNVALIDATED`.** That is the expected shape.
  `UNVALIDATED` is the modal state in any real deployment, and a system that
  cannot say *"never measured here"* will say something confident and wrong
  instead.
- **`results/RESULTS.md` refuses to print some numbers.** Several matrix cells
  are synthetic fixtures. The renderer refuses them rather than printing a
  fixture as if it were a measurement.
- **A recall interval looks wide.** It is a bootstrap-percentile interval over
  questions, and several are additionally reported with a selection-aware
  widening. A narrow interval on a small holdout would be the suspicious thing.
- **`verify` tier 3 says SKIPPED on a clean clone.** Correct — never a pass it
  did not earn.
- **A detector is refused on one envelope and valid on another.** That is the
  entire point of keying warrants by envelope.
- **An eval set changed and its warrants vanished.** Sets are content-hashed; a
  modified set is a *different* set and cannot inherit the old one's evidence.

---

**See also:** [SETUP.md](SETUP.md) · [RUNBOOK.md](RUNBOOK.md) · [CASES.md](CASES.md), which names the test covering each of these behaviours.
