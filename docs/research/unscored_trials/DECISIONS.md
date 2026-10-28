# Unscored-trials extension decisions

Append-only. The published execution plan governs this track. This is an
exploratory decision study, separate from production, the closed grader study,
and FPR source review.

## U001 — Begin bounded evidence discovery (29 October 2026)

Start from verified remote main `b5e34e9924142717a8c207cb830a1d916054a0d8`
on `research/unscored-trials-20261029`, isolated from the shared checkout.
Research start: 28 October 2026 22:07:14 UTC (29 October locally).
Maximum effort is 20 aggregate active agent-hours and additional spend INR 0.
Publication preparation used no paid compute. Separate elapsed time from summed
active effort; estimates are identified as estimates.

Prior exposure: the supplied baseline summary, Marin/tau2 results, 5% cap
correction, Terminal-Bench issue 2246 description, the prepared plan and its
source list. Newly frozen rules will not retroactively preregister these.
Discovery includes all inspected job IDs and their observed fields. Do not
select eligibility on scores, ranks, missingness or an apparent discrepancy.

First candidate is the official Terminal-Bench 2 HF release. Pin the revision
from the metadata response before further retrieval. Initial download ceiling
is 2 GiB total across agents, with bounded requests, no automatic trajectories.
Source discovery receipts and baseline replay copies stay outside Git.
Commit retrieval code before use; canonical scientific outputs require clean
committed source, source/config hashes and retained command/exit evidence.

The existing baseline and supplied archive remain untouched. Baseline
reproduction occurs only in an extracted copy after archive/manifest checks.
Three assistant subtasks inspect baseline reproduction, closest work and
official scorer semantics; these are author cross-checks, not independent
human adjudication. No external contact or submission is authorized.

The current user permits the conditional writing stage when justified. The
decision study ends at GO/REPORT/DATA-BLOCKED; GO must explicitly state whether
any justified packaging can fit the remaining authorized budget. No manuscript
work precedes the evidence decision. The alternative, writing toward a presumed
publication, risks turning a valid stop result into unsupported claims.

## U002 — Deterministic structural discovery before score inspection

Pin official HF release `572b2614be2c0cb2527e14f5b1e4026f1072e6c1`.
The initial API siblings response stops at 100,000 files and is not a census.
Nonrecursive directory listings establish 75 submission directories and 245
job directories; none of the child listings advertises another page. Every
job configuration is requested; one SSL timeout is preserved and receives
one separately named retry. These are discovery counts, to be reproduced by
the committed inventory module before reuse as scientific findings.

Before inspecting any job result or trial reward, choose one job per observed
trial-directory-count stratum by the lexicographically smallest SHA-256 of
its full source path. Strata are 5, 10, 29, 30, 89, 95, 130, 178, 356, 445.
Within each chosen job inspect the trial directory with the smallest SHA-256
of its full source path. This yields ten job results and ten trial results.
The complete paths and request rules are retained in external
`terminal/discovery-candidates.json` and `discovery-requests.json`, to be
bound into the source manifest. No score, missingness or rank chooses these
cases. This set tests schema diversity; it is not representative prevalence.

The closest-work assistant opened the mirror README and saw headline scores
and counts including vix and Wecode. This is additional discovery exposure;
those outcomes do not govern the above selection or later eligibility.
Gao/Zhou, AgentEval and issue 2246 already cover denominator bounds and rank
audits. A contribution must go beyond reproducing those generic observations.

Preserve three separate native targets: released job metrics, an official
versioned importer if accessible, and a time-specific displayed leaderboard.
Official post-release adjudications can change the latter without altering
raw released rewards. Missing importer/adjudication evidence forbids claiming
an official leaderboard correction. Repeated trials and retry configuration
do not establish retained retry lineage.

Discovery execution caveat: a mixed-line-ending whitespace check prevented
the intended U002/test commit, but the subsequent retrieval still ran. The
21 requests therefore ran from a dirty discovery tree. Their selected paths
were recorded before retrieval; no reward fields had yet been read. Preserve
these receipts as discovery only. Commit protocol/code and regenerate all
canonical scientific outputs from a clean tree before interpreting results.
This is a workflow failure, not a clean-provenance claim.

## U003 — Freeze the final-release census and narrower estimands

Gate B supports the released-final-record accounting question; see
FEASIBILITY.md. Preserve the original-attempt/retry and website-authority gaps.
Freeze PROTOCOL.md and config.json before bulk outcome retrieval/comparisons.
The census includes every named final directory in all inventoried jobs, with
all exclusions and contradictions retained. No outcome-selected subset.

Additional discovery exposure: U002 job summaries were read for counters/schema
and means. They include scored exceptions, null-reward counters and an unfinished
grok part1 summary counting more records than released directories. This motivates
reconciliation, not exclusion, prevalence estimation or a corrected ranking.
The ten trial discovery records were scored; no missingness selection follows.

Native artifact means are reproduced before any policy sensitivity. Unknown
completion and observed-only denominators are distinct estimands from native
operational zero accounting. Exact task definitions and fixed weights govern
all compatible pair comparisons. The recorded configuration declares a census
and exact arithmetic; no random seed is used because no random operation occurs.

Acquisition reserves 80 MiB for other-source retrieval including failed/capped
reads. Within the terminal cache, failed requests conservatively count their
full read limit plus one byte; successful responses count actual bytes. This
prevents discarded oversized responses from escaping the aggregate ceiling.
Two extra immutable attempts per required source are allowed; retrying HTTP
retrieval is distinct from benchmark execution retry lineage.

## U004 — Fail closed on incomplete Git cleanliness inspection

The first canonical metadata invocation emitted Git warnings about two
inaccessible pytest cache directories created by scoped test attempts. Although
tracked source was committed, its clean-tree check had ignored Git stderr.
Preserve that output outside Git as a diagnostic, remove only the two named
owned test caches, and make provenance reject any Git stderr. Regenerate the
inventory from clean committed source. No extension score comparison had run.
This supersedes the initial cleanliness claim rather than silently repairing
its provenance. Expected scientific counts do not change; the clean rerun will
establish them. Temporary test-directory ACL failures and mixed-line-ending
checks remain retained failures, not successful validations.
