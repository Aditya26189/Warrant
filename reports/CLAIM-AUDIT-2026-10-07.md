# Warrant claim and venture-readiness audit — 7 October 2026

This is a source-linked audit of the current checkout, not a claim that Warrant
is fundable, production deployed or completely correct. I inspected the
committed repository, the visible conversation supplied to this session, and
the dated primary-source pages linked below. I do not have a searchable archive
of the user's other 15 chats; claims said only there are **UNKNOWN** here.
`ARC180_BRIEF.md` remains an untracked user file and was not treated as a
committed measurement. No customer export, configured incumbent packet,
reviewer trial, buyer interview or external account was supplied.

## Claim-by-claim evidence and what it means

| Claim a reviewer might hear | Evidence inspected | Supported reading and limit |
| --- | --- | --- |
| A cheap question-time signal exists | `controlplane/extract/activations.py` prefill extraction and `controlplane/extract/model.py` left-padding checks; `results/validation-T1-last_token.json` `metrics.auroc.value=0.8256` | The retained research result is on the named TriviaQA/Qwen envelope. Frozen-score recomputation does not itself establish a fresh model extraction or another model/task's performance. |
| The shipped probe catches errors | `results/validation-T1-last_token.json`: recall `0.0794`, precision `0.8800`, flag rate `0.0417`; README claim table | The small-budget point catches about eight percent of labelled errors in that test envelope. High precision alone would hide low recall. The flag rate is measured there, not a deployment budget. |
| Long-context transfer is robust | `results/transfer-T1-mean_pool.json` `target.metrics.auroc.value=0.5015144571984218` and `target.metrics.flag_rate.value=0.0`; README long-context table | This mean-pool variant is near chance and flags none at its transferred operating point. The last-token result is different; it cannot make every aggregation robust. |
| Stock Presidio solves the tested Hinglish PII cases | `results/detectors.json` stock `hinglish-pii-200`: recall `0.1176`, precision `0.5455`; `results/holdout/detectors.json` stock `hinglish-pii-200b`: recall `0.1471`, precision `0.5357` | The stock configuration is weak on these **constructed** sets. The held-out result is a second authored set, not an observed customer prevalence or a universal Presidio benchmark. `README.md` labels the primary stock row `REFUSED`. |
| A small label budget suffices | `results/on_traffic/on_traffic.json` `headline.labels_month_one_5pp=1399`, `headline.superseded_sizing_5pp=187`, `headline.coverage=0.9680` over `headline.coverage_trials=1000`; `DECISIONS.md` 147, 191 | The old 187 was superseded. The 96.8% coverage is a seeded simulation under its declared workload, not empirical coverage on customer traffic. Do not turn 1,399 into a bank deployment quote. |
| Rechecks control repeated false revocation | `results/recheck_schedules/comparison.json` weekly `S0`: fixed per-recheck `revoked_in_year.value=0.8515`, `e_detector=0.0085`; `DECISIONS.md` 187, 193, 226 | These are paired simulated years on the stated labels. The historic capped-monitor result in that artifact has a known rule defect corrected by 226; its old numbers are not evidence of the repaired runtime's detection power. |
| README numbers currently match retained artifacts | Clean commit `5f34030`: `python scripts/verify.py` ended exit 0, `TIER|1|claim_table|OK|92/92`, `TIER|2|frozen_scores|OK|25/25`, `TIER|3|activations|SKIPPED|0/0` | No claim-table mismatch was found at quoted precision. This checks the table and frozen-score arithmetic; activation provenance was explicitly not replayed in this worktree. GNU `make` was unavailable on this Windows host, so the exact Makefile recipe was run directly. |
| A complete customer product exists | `docs/PRODUCT-STATE.md`, `docs/PILOT-PROTOCOL.md`, `reports/DISCOVERY-2026-10.md`; no customer packet in the checkout | The installable local file command exists. A hosted service, authenticated custody, repeated buyer decision, operating customer integration and paid pilot are unobserved. Synthetic fixtures exercise software, not demand. |

Decision 080 is not an unresolved implementation entry: it reports that a
pre-registered re-split met four declared criteria. It also says the two
operating-point columns re-selected thresholds and **must not be read as an
improvement** (`DECISIONS.md` 080). The README's larger 960-item result is
therefore a named research envelope, not a prospective customer validation.
The repository now contains both the Round 1 probe experiment and a broader
local evidence product; the supplied root `AGENTS.md` still describes the
earlier `src/`, `TASKS.md` and Round 2 boundary, while current code lives under
`controlplane/`. Follow current commits and `docs/PRODUCT-STATE.md` when
assessing implemented capability, and treat the stale map as documentation
debt rather than silently claiming those files exist at root.

## Market and standards cross-check

The live official documentation checked on 7 October undercuts a generic
"agent evals and review" differentiation. [LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types)
describe offline and online evaluators, including experiment-level summary
metrics such as precision and recall. [MLflow's evaluation guide](https://mlflow.org/docs/latest/genai/eval-monitor)
describes datasets, human feedback, judges, evaluation and monitoring. Its
[dataset guide](https://mlflow.org/docs/latest/genai/datasets/) says datasets
can come from traces or manually created examples. The earlier
[incumbent packet review](INCUMBENT-PACKET-COMPARISON-2026-10.md) also links
official Braintrust, AWS and LangSmith export documentation. These pages show
overlapping documented features; they do **not** show how a particular buyer
configured them or whether Warrant changes that buyer's decision. A claim
that incumbents cannot make a replayable decision packet is **UNKNOWN**.

A versioned file manifest is an appropriate *local consistency* format, not
an authenticated provenance standard. The [in-toto attestation specification](https://github.com/in-toto/attestation/blob/main/spec/README.md)
separates subject binding from its authentication envelope; the
[Sigstore bundle format](https://docs.sigstore.dev/about/bundle/) includes
signature content and verification material. Warrant's new local certify
handoff has neither. It must never be sold as a signed attestation, trusted
registration timestamp, chain of custody or proof that a reviewer labelled
the rows independently. The meaningful possible wedge is a customer who
already has scored, independently labelled exports but whose **actual**
current review packet fails a predeclared budget decision or independent
replay. That is a hypothesis pending side-by-side evidence.

## Ranked problems found

1. **No demonstrated buyer or repeat use.** The repository contains no
   permissioned customer export or completed unaided reviewer worksheet
   (`reports/DISCOVERY-2026-10.md`). Software tests cannot close this gap.
2. **Label and sample provenance remain declarations.** `docs/INPUT.md` and
   `docs/EVIDENCE-HANDOFF.md` require user-supplied labels, polarity, groups
   and sampling frame. A mathematically replayed certificate can be about
   biased or wrong labels. The new packet copies these declarations; it does
   not validate their truth.
3. **Research numbers have narrow transfer scope.** The low-recall shipped
   point, mean-pool collapse, constructed PII sets and synthetic on-traffic
   coverage preclude a general model-safety, robustness or ROI claim.
4. **Custody and service controls are missing.** `docs/PRODUCT-STATE.md`
   names no authentication, tenant separation, serving API or live scheduler.
   A checksum packet is rewriteable by whoever controls its files.
5. **Verification is tiered, not absolute.** The last integrated full local
   suite is reported in `reports/PHASE-43.md` at clean `98ba529`; this audit
   rechecked the current README/frozen-score tiers only. The activation tier
   was skipped here. Remote CI for the new phase and a fresh GPU extraction
   remain unobserved, so "100% correct" is not supportable.

Other review debt stays visible. `DECISIONS.md` retains historical OPEN entries;
some are superseded later and cannot be counted by text search alone. In
particular, 124's in-sample sweep warning was later addressed by the
out-of-sample sweep, while 135 records the missing 1,441-negative calibration
expansion and 136 records a closed-API exercise blocked by credentials.
`docs/PILOT-PROTOCOL.md` section 10 is a dated draft precondition list: it
mentions old chain defects that subsequent commits fixed. It needs a current
status annotation before use as a live pilot checklist. The current
`reports/BUILD-PLAN-2026-10.md` correctly stops speculative platform work
without real packet and reviewer evidence; the founder's new instruction
authorized a bounded handoff experiment, not a claim that the commercial gate
passed.

## What to prove next

First, have an unaided person run the synthetic valid, refused and changed
source paths and the new packet command, recording their exact interpretation
before explanation. Next, obtain an owner-permitted export with label source,
sampling unit, score direction and retention rule, plus the packet the team
already gives its reviewer. Run the incumbent and Warrant paths on **the same
recurring decision**; record which missing fact, if any, changes sign-off.
Then repeat with a second independent team before a vendor adapter or hosted
control plane. If labels cannot be produced, if the incumbent packet already
answers the decision, or if the reviewer gains nothing from the extra files,
the venture hypothesis should be narrowed rather than covered with more code.
