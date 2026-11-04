# Frozen exploratory extension protocol

29 October 2026. Commit before census outcomes or comparative analysis.
See U001–U003 and FEASIBILITY.md. This protocol does not preregister the exposed
baseline, mirror headlines or ten structural discovery jobs.

## Sources and cohort

- HF official release: `572b2614be2c0cb2527e14f5b1e4026f1072e6c1`.
- Census every submission/job enumerated by complete nonrecursive directory
  listings under `submissions/terminal-bench/2.0`. No outcome-based subset.
- Retrieve job result JSON and each named final trial result JSON, configs and
  metadata only. No trajectories or upstream code execution. Preserve every
  failed request; allow at most two separately named subsequent attempts per
  required source. Stop retrieval before 2 GiB total downloaded input bytes
  across this study (baseline archive reuse excluded), with a 128 KiB initial
  per-trial read cap. Larger required records need a separately logged bounded
  request after metadata inspection. Batches reserve worst-case request sizes;
  actual cumulative bytes are checked between batches. INR 0 additional spend.
- Census all jobs for native reconciliation, including partial/version/local
  submissions. Keep every exclusion/reason visible. Primary comparisons require
  complete common TB2 task definitions and supported finite rewards. Complete
  cohorts are retained; nonzero missingness is not an inclusion requirement.

## Identity, population and reconciliation

The primary population is released named final trial records, not all original
attempts or a five-times-Cartesian guessed roster. Preserve source path/hash and
JSON pointers, trial UUID/name, job ID and task name/Git ID/checksum. Never infer
attempt or repetition indices. Config cardinalities and summary-only names are
separate accounting evidence. Do not create a planned-slot table without an
explicit original roster. Retry-policy questions are unavailable without lineage.

Within each job retain all named records for native metric reproduction. Across
jobs in a submission, identical UUIDs with identical task/reward/exception/time
semantics are duplicated exports and counted once for execution-level sensitivity;
retain all source aliases. Conflicting UUIDs, task IDs/checksums or reward evidence
are quarantined, never coerced to zero. Missing UUID/task identity is ineligible
for paired comparisons and remains in reconciliation. Missing raw files with
summary-recorded rewards are not unscored trials. Unmatched summary names remain
unreconciled rather than imputed as absent planned executions.

Use only a single `reward` channel with finite numeric rewards in [0,1]; reject
booleans, nonfinite/out-of-range values, multiple channels and malformed objects.
Distinguish no verifier, null rewards, absent channel, malformed reward, recorded
zero, positive/fractional reward and absent raw file. A valid score survives an
exception. Exception class is descriptive, not a causal adjudication.

## Native targets and policies

1. Reproduce each released job/eval mean from raw final records, mapping genuinely
   absent verifier/rewards to zero as the documented native final-record metric
   does. Single-channel valid observations remain unchanged. Empty/multichannel
   objects are unsupported unless matching source semantics are established;
   never silently apply January semantics to May multichannel output.
2. Reconcile job-directory names, raw UUIDs, summary reward/exception indexes,
   global/completed/scored/error counts and declared n_total_trials separately.
   Do not add scored and exception counts as though disjoint.
3. Report statuses match (absolute error <= 1e-12), rounding-compatible (only
   when a published rounding precision is explicit), unresolved mismatch,
   unsupported schema or unavailable. Decimal arithmetic derives exact fractions;
   binary serialization tolerance does not manufacture a rounding envelope.
4. Official website score reproduction is unavailable without pinned importer
   and adjudications. No result here is called an official corrected ranking.
5. Native operational null-as-zero means, observed-only means and free-[0,1]
   unknown-outcome bounds answer different questions. Label each denominator.
   Bounds hold the same named-final population and weights fixed; only present
   genuinely unscored outcomes vary. No hidden missing-record interval.
6. Compute equal-task and pooled-final-trial policies with the same outcomes;
   differing repetitions change weights/estimands. Report their difference as
   sensitivity, never tighter missingness identification or bias correction.
   A scored-exception-zero diagnostic is optional only as an explicitly
   counterfactual policy illustrating discarded valid rewards, not a repair.

## Comparability and pairwise rules

Primary submission comparisons require all 89 official TB2 task names and
compatible Git task revision/path and task checksums. Compare only complete
matching task-definition signatures, with equal-task weights 1/89 and equal
weights among retained final records within each task. Local/unknown/variant
task definitions, unresolved conflicts or missing sources exclude a submission
from primary comparisons, with explicit reasons. Directory/model display names
alone do not establish the same system across jobs; report config hashes and
variation. Submission-level results concern the released system mixture if
declared jobs differ; do not call that one fixed model configuration.

Analyze every compatible unordered pair, including ties and negative controls.
Intervals use exact rational reward mass and weights. Difference endpoints are
[L_A-H_B,H_A-L_B]; alignment leaves independently unconstrained bounds unchanged.
Classify strict robust order, identified tie, equality-compatible ambiguity and
reversal-compatible ambiguity relative to the native/equal-task point order.
Endpoint completions are counterfactual, not recovered corrected rankings.
Compare pooled weights separately; no common-observed-task primary repair.
No population p-values, winner significance or causal missingness claims.

## Gates and verification

Stop a source after bounded access failures. Continue supported accounting while
marking inaccessible records; no score claim from an unreconciled population.
Stop the candidate if final-record identity/outcome status/native semantics cannot
support even the narrower audit. Native mismatches are investigated before
criticism; explanations can include incomplete exports, summaries, versions,
rounding, duplicates, weights and legitimate native failure semantics.

Test zero/null/absent/malformed distinctions, scored exceptions, explicit
dedup/conflicts, multiple jobs and task/version identities, fractional rewards,
native small fixtures, exact boundary classes, all-scored/all-unknown bounds,
pairing separability, cap violations and unavailable retry lineage. Synthetic
fixtures establish implementation behavior only. Run canonical generation from
clean committed source and replay offline to identical canonical numeric outputs.
Retain commands, exit statuses, hashes, environment and failures. Prepare source
arithmetic audit cases; human review remains pending.

At the evidence gate deliver GO, REPORT or DATA-BLOCKED with closest-work overlap,
claim ledger, strongest alternative explanation and precise reopening conditions.
No manuscript preparation unless evidence first justifies GO and remaining scope
and budget support it. Do not spend the remaining ceiling merely to consume time.
