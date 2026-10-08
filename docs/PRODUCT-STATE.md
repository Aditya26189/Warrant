# Product state and evidence map

This page is the current entry point for assessing Warrant as software. It
began with the 1 October 2026 root-release review and was updated after the
7 October week-one gate. The [claim table](../README.md)
and [results](../results/RESULTS.md) hold measured research numbers; this page
does not restate them. [The code tour](CODE_TOUR.md) explains each package,
and [limitations](LIMITATIONS.md) carries the detailed statistical caveats.
[The audit report](../reports/PHASE-16.md) records the original product-state
review; [Phase 17](../reports/PHASE-17.md) records certificate binding and
replay, [Phase 18](../reports/PHASE-18.md) records recheck evidence linkage,
and [Phase 19](../reports/PHASE-19.md) records fresh-batch binding and ordinary
replay. [Phase 20](../reports/PHASE-20.md) records retained linear-chain replay.
[Phase 21](../reports/PHASE-21.md) records release-label audit evidence;
[Phase 22](../reports/PHASE-22.md) repairs grouped recall/precision boundaries;
[Phase 23](../reports/PHASE-23.md) corrects hard-negative warrant inference;
[Phase 24](../reports/PHASE-24.md) repairs grouped descriptive rate boundaries.
[Phase 25](../reports/PHASE-25.md) records a corrected full tracked-file clone;
[Phase 26](../reports/PHASE-26.md) makes its verifier-tier parser fail closed;
[Phase 27](../reports/PHASE-27.md) preflights known full-suite blockers; and
[Phase 28](../reports/PHASE-28.md) preserves failed attempts separately from
the last passing clone record. [Phase 29](../reports/PHASE-29.md) corrects the
legacy monitor's mixture stopping decision while retaining its historical
schedule study. [Phase 30](../reports/PHASE-30.md) through
[Phase 42](../reports/PHASE-42.md) cover the October export-preparation and
synthetic handoff work; [Phase 43](../reports/PHASE-43.md)
records the week-one integrated local full-suite gate and its human-trial limit.
[Phase 48](../reports/PHASE-48.md) records a later complete local suite after
the prepared-handoff and failed-gate artifact preservation repairs.
[Phase 50](../reports/PHASE-50.md) records the subsequent tracked-file clone
gate and its explicit activation-replay and Windows-cleanup limits.

**Current status: a usable local evaluation tool and a substantial research
harness, not a deployed enterprise service or a validated startup.** A user can
run the packaged `warrant` command on their own scored and labelled file. The
repository also includes experiments, synthetic studies and demonstrations.
No customer data, pilot, buyer interview, design partner, revenue or production
deployment has been supplied to this project. Those absences limit both product
and commercial claims.

## What a user can run today

| Surface | Implemented behavior | Entry point and evidence | Boundary |
|---|---|---|---|
| Scored-export preparation | `prepare` maps a flat CSV or JSONL export to canonical scored rows using declared labels, score direction and group meaning; it retains a source/mapping/output hash manifest. `verify-prepared` recomputes the package from retained originals. | [Input guide](INPUT.md), [implementation](../controlplane/intake/prepare.py), [focused tests](../tests/test_prepare.py), [installed-package test](../tests/test_package_install.py) | This is a representation and integrity handoff, not a certificate or a proof of label truth, independence, source authenticity or representative sampling. Parsing uses process memory and writes no intermediate plaintext file; retained inputs and process memory remain sensitive. |
| Prepared certify handoff | `handoff create` copies a fixed set of original and prepared inputs plus a retained certify record into a new local packet after replaying both links. `handoff verify` checks member bytes and replays both links again. Source copying requires an explicit sensitive-input flag. | [Input guide](INPUT.md#transfer-a-prepared-certify-result-to-another-reviewer), [implementation](../controlplane/intake/handoff.py), [negative tests](../tests/test_handoff.py) | Certify only; no release, recheck or chain packaging. The original export, including excluded columns, is copied. Checksums are not authenticated provenance, and the packet is not evidence of buyer demand. |
| Scored-file certification | `certify` reads CSV or JSONL `id,label,score`, with optional `group` and `label_2`; selects a threshold against a declared false-positive budget, issues a record or explains refusal. `--frontier` and `--from-frontier` cover budget exploration and selection. `verify` replays a retained certificate against the effective scored-row sequence. | [Input contract](INPUT.md), [intake code](../controlplane/intake/), [CLI](../controlplane/cli.py), [verification tests](../tests/test_certify_verification.py) | The user supplies the scores, labels and their meaning. A certify record has an effective-row digest but no authenticated custody, detector/system identity or expiry. Grouped data has additional restrictions and open interval questions. |
| Recheck and chain | `recheck` evaluates a retained warrant against a new labelled file, names its exact certificate digest and binds the fresh effective-row sequence. With `--certificate-input`, it replays the original certificate before measuring; without it, source evidence reads `NOT_CHECKED`. `verify-recheck` recomputes an ordinary record. Chained rechecks record a declared horizon, links and revocations; `chain verify` checks retained records, seals and structure, while `verify-chain-recheck` recomputes a complete sealed linear prefix from every retained fresh batch. | [Recheck and chain code](../controlplane/intake/), [evidence tests](../tests/test_chain_replay_evidence.py), [chain tests](../tests/test_chain_publication.py), [runbook](RUNBOOK.md) | A checksum is not an authenticated signature. `verify-recheck` does not handle a chain. `verify-chain-recheck` cannot prove that no later link or fork was omitted, and declines unbound or non-linear history. |
| Release evidence | `release register` freezes criteria and a disjoint holdout; `evaluate` scores that fixed holdout; `verify` recomputes retained evidence and checks expiry. A separate `label-audit` companion describes fixed-threshold label fragility and observed second-review disputes; `verify-label-audit` replays it. This is a distinct workflow from `certify`. | [Release guide](RELEASE.md), [release code](../controlplane/release/), [handoff field map](EVIDENCE-HANDOFF.md), [installed-package tests](../tests/test_package_install.py) | A shared scored file does not imply a shared operating point. Registration is not a trusted timestamp or authenticated sign-off; the companion does not establish label truth or change the release verdict. |
| Planning | `plan` estimates review and recheck effort from a declared workload and statistical assumptions. | [Economics code](../controlplane/economics/), [sampling code](../controlplane/sampling/), [methods](METHODS.md) | The workload is declared, not observed at a customer. No savings or ROI has been measured in a deployment. |

The installable distribution is [`warrant`](../pyproject.toml), exposing the
[`warrant` command](../controlplane/cli.py). Its customer dependencies are
NumPy, SciPy and PyYAML; the research environment is separate. The command is a
local file workflow, with no hosted endpoint or customer account system. See
[setup](SETUP.md) for a minimal install and [troubleshooting](TROUBLESHOOTING.md)
for refusal and error behavior.

## What the repository demonstrates

| Area | What exists | What it establishes, and what it does not |
|---|---|---|
| Research pipeline | Question-time activation extraction, frozen evaluation sets and scores, probe training, statistical controls, model and text-detector adapters, validation, a detector-by-envelope matrix, report generation and claim verification. | [Results](../results/RESULTS.md) and the [claim table](../README.md) are reproducible claims about the named evaluation envelopes. They do not establish performance on another model, task or customer's traffic. Some matrix cells and detector tiers are fixtures, explicitly separated from measurements. |
| Monitoring and policy demonstrations | Drift checks and revocation traces, a Rego policy path, an action-gate implementation, a LiteLLM adapter and simulated on-traffic sampling and cost studies. | [Architecture](ARCHITECTURE.md), [results](../results/), and [case matrix](CASES.md) document the exercises. These are not a running gateway, live traffic monitor, production policy service or robustness study. |
| Evidence infrastructure | Committed frozen-score artifacts, source/config provenance, content-hashed evaluation sets, an append-only methodological decision log, claim checks and clean-clone records. | [`scripts/verify.py`](../scripts/verify.py) can recompute published claims from retained artifacts. The [artifact guide](ARTIFACTS.md) distinguishes frozen scores, fixtures, declared scenarios and generated reports. The [full clean-clone record](../results/clean_clone.json) names the later integrated source it tested; read that commit before applying its pass to another head. |
| Test infrastructure | Source, installed-wheel, document, claim and acceptance tests, with Linux and Windows CI jobs declared. | [Testing guide](TESTING.md) and [CI configuration](../.github/workflows/ci.yml) show what is exercised. The [test inventory](../results/test_inventory.json) records collection only; it is not proof that the full suite or remote CI passed at the current head. |

## Deployment and assurance gaps

These are blockers to representing the current repository as a production
enterprise control, even where the local command behaves correctly:

1. **Customer evidence.** There is no observed buyer workflow or customer-labelled
   data. The [discovery stopping rule](../reports/STRATEGY-2026-09.md) and
   [pilot protocol](PILOT-PROTOCOL.md) are plans, not completed research.
2. **Record identity and custody.** Ordinary certify warrants bind the effective
   scored-row sequence and can be replayed, but do not authenticate the author,
   software/detector identity or expiry. Rechecks identify the certificate they
   read and bind their own fresh effective scored rows; `verify-recheck`
   recomputes ordinary records, and `verify-chain-recheck` requires a retained
   linear prefix. None authenticates an author or proves omitted records do
   not exist. Plan records also have gaps. Every digest here is a checksum,
   not a signature.
   The exact field-by-field gap is in [EVIDENCE-HANDOFF.md](EVIDENCE-HANDOFF.md).
3. **Statistical scope.** The independent review identified grouped
   recall/precision boundary behavior (R2); prospective customer records now
   abstain on collapsed grouped recall, precision and descriptive rate
   intervals (Phases 22 and 24). Grouped research hard-negative warrants use
   the separate Phase 23 group-any rule. Historical artifacts retain their old
   methods for replay, and noncollapsed cluster intervals lack a new coverage
   study. Decision 226 corrected the legacy mixture monitor's premature
   revocation decision (R10), but its conditional-null and production sampling
   assumptions have not been established. The Decision 187 schedule result is
   still a replay of the defective historical rule, not a current-monitor
   result. See the [review](../reports/PROJECT-REVIEW-2026-09-23.md),
   [Phase 29 report](../reports/PHASE-29.md) and [limitations](LIMITATIONS.md).
4. **Operations and integration.** No serving layer, authentication, access
   control, rate limits, tenant separation, high availability or deployment
   manifests exist. The gateway package is an adapter. Live scheduling, traffic
   ingestion and observability for a customer deployment have not been shown.
5. **Current-head verification.** The most recent integrated local full suite
   is [Phase 50's tracked-file clone gate](../reports/PHASE-50.md). Its
   [machine-readable record](../results/clean_clone.json) names the exact
   source commit it tested, and the report distinguishes its complete test
   step from the collection inventory. [Phase 48](../reports/PHASE-48.md)
   records the earlier worktree suite and the preservation repairs it tested.
   Activation replay was explicitly skipped in the available verifier; the
   clone also reported a Windows temporary-directory cleanup failure that was
   handled manually after the run. A remote CI result for the final merge has
   not been observed. Do not substitute configured CI jobs or collection
   counts for an executed pass.

## How to inspect the work

From a clean checkout, follow [setup](SETUP.md) and then run:

```bash
python warrant.py --help
python warrant.py certify --input examples/certifies.csv --budget 0.05
python warrant.py verify --warrant examples/certifies.csv.warrant.json --input examples/certifies.csv
python warrant.py certify --input examples/refuses.csv --budget 0.01
python -m pytest tests/ -q
python scripts/verify.py --no-activations
```

The example commands exercise a warrant, its replay and a refusal. The test command
executes the suite; `verify` checks claims and frozen-score reproduction without
regenerating GPU activations. A passing local run is evidence for that checkout
and environment only. The [runbook](RUNBOOK.md) lists all commands and artifacts;
the [code tour](CODE_TOUR.md) provides a file-by-file path for reviewers.

For an assessment, start with this page, try the examples, inspect the
[claim-to-artifact mapping](../README.md), read [limitations](LIMITATIONS.md),
and only then consider the [pilot protocol](PILOT-PROTOCOL.md). Update this page
when a feature moves between implemented, demonstrated and deployed states; do
not turn a proposed integration or an unobserved CI job into a shipped claim.
