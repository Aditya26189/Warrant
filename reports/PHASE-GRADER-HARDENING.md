# Grader runner hardening after review

22 October 2026. **Decision: the three reported implementation issues are addressed and verified for continued bounded research. Production integration and a broader research claim remain separate gates.**

[Evidence] The implementation and live validation ran from clean source `b4afb7075ef6c73cb845328cdb199f7d9d455c70`. The [archived summary](../experiments/grader_poc/hardening/summary.json) records the producing and archival commits. The original P0/P1 report and `results/` packet were preserved unchanged; its 235 packaged payload hashes still verify.

## Fixes and verification

| Review issue | Change | Evidence |
|---|---|---|
| Docker-client timeout can leave its container running | Create a uniquely named and labeled container before attaching; attempt cleanup in `finally`, check ownership, remove by ID, and query the daemon to verify absence. A failed cleanup invalidates the observation. | Live timeout and real SIGINT checks both observed a running owned container during cleanup and verified its removal. A unit test checks refusal to remove a foreign container. |
| Harbor timeout escapes without `outcome.json` | Write atomic final receipts for timeout, catchable interruption, launch failure, malformed/missing results and task drift. Preserve partial results without promoting their reward into a completed run. Give the owned POSIX process group a bounded graceful-cancellation opportunity. | Live synthetic process fixtures emitted a reward before sleeping. The runner retained the partial evidence but returned `TIMEOUT` or `INTERRUPTED`, wrote the final receipt, and stopped the child process group. |
| Broad worker exception handler triggers BLE001 | Document the candidate/protocol boundary and narrowly suppress that single lint finding. Ordinary application errors produce explicit `ERROR`; `BaseException` interruptions remain uncaught in the worker. | Worker exception and interruption tests; a real container emitting a controlled application failure; Ruff passes. |

[Evidence] Additional regressions cover malformed observations, nonbinary or boolean rewards, nonzero exits, altered task/app bytes, `UNKNOWN`, failed controls, and interrupted diagnostic logging. Unsupported input abstains without executing candidate code. Diagnostic interruption records the attempt and stops the CLI rather than continuing the search.

Verification performed in this phase:

- **29 unit tests passed**, including the original oracle/reducer checks. The [saved test log](../experiments/grader_poc/hardening/validation/unit-tests.txt) records the Linux/WSL run.
- **8 targeted live checks passed**: Docker timeout, real interruption, worker exception, two synthetic Harbor-process failure cases, and the mutant/reference/equivalent witness replays. See [the full validation record](../experiments/grader_poc/hardening/validation/outcome.json).
- **1 normal full Harbor reference trial passed**, with reward 1 and 7/7 tests, under the hardened runner. Its collected candidate bytes match the original packet. See [the full-run outcome](../experiments/grader_poc/hardening/full-reference/outcome.json) and accompanying verifier logs.
- **Ruff passed** with version 0.16.6. The [lint log](../experiments/grader_poc/hardening/grader-hardening-lint.txt) and version record are retained.

The two Harbor failure cases are synthetic executable fixtures, not additional benchmark results. The normal full Harbor trial is the actual pinned benchmark. The known witness replay still gives maximum 1 for the mutant and 2 for both controls. This phase does not claim a new defect or transfer to another task.

An initial unit invocation could not create fixture children in the tool sandbox's default Windows temporary directory. A rerun with a workspace-local temporary root passed, followed by the recorded WSL run. This was infrastructure failure, not a changed expected result. No paid API or GPU was used.

## Remaining operational limits

[Evidence] Diagnostic-container cleanup is verified for the tested paths. **Harbor-delegated container cleanup after cancellation is explicitly `UNVERIFIED`.** The full-trial wrapper owns its process group; it cannot assume a forcibly stopped Harbor process completed cleanup of every delegated Docker resource. The live failure fixtures test process cancellation and final receipts, not actual Harbor-container cleanup during a forced stop. Windows cancellation covers the direct child, not an entire process tree.

An unavailable Docker daemon can make cleanup fail; that yields an error, not a semantic counterexample. Host failure, SIGKILL, filesystem failure, or a daemon completing creation after a client disconnect cannot be given an unconditional cleanup/receipt guarantee. The code and report do not claim a production sandbox certification. No CI pipeline or general-purpose packet-verifier product was added.

## Treatment of the supplied review

[Evidence] The supplied [review snapshot](../experiments/grader_poc/hardening/prior-review/REVIEW.md) describes nine fresh full trials, the witness/control replay, packet integrity checks and the original seven unit tests. Its author explicitly identifies itself as another assistant. The accompanying reproduction summaries are retained separately from this phase's checks. This strengthens reproducibility; it is not independent human review or a blinded study. The older P0/P1 report remains a historical document rather than being rewritten to imply those later checks existed at its creation.

[Evidence] The [archive manifest](../experiments/grader_poc/hardening/manifest.json) records raw and packaged hashes. Copies replace host home and temporary-virtualenv paths with role placeholders and remove UTF-8 BOMs; raw artifacts remain locally available. Terminal-Bench-derived candidate files retain their Apache license and canary comments.

## Research and Warrant fit

[Opinion] The proposed role is sensible: an optional audit of executable graders used to produce evaluation labels. Its evidence should state the exact grader/candidate versions, property scope, expected and observed behavior, counterexample, controls, unsuccessful attempts and abstentions. A finite adversarial audit can expose a flaw in a label source; it cannot certify that labels are generally correct or supply a calibrated error-rate guarantee. Statistical certification and B1/A04 remain separate.

[Evidence, primary research source] EvalPlus already studies inadequate code-evaluation tests and uses LLM- and mutation-based test augmentation. Its first submission was 2 May 2023, with the inspected version revised 30 October 2023. This is historical prior art, not evidence about current market demand. [Liu et al., EvalPlus](https://arxiv.org/abs/2305.01210)

[Evidence, primary issue report] Terminal-Bench issue #2243 was opened on 13 October 2026, before the Warrant experiment. It reports a different missing assertion in this same task: merged session boundaries. The author describes a mutation-testing workflow and supplies a reproduction. This phase verified the issue's contents and date, not that separate defect's execution. [Issue #2243](https://github.com/harbor-framework/terminal-bench/issues/2243)

[Inference] Neither source invalidates the maximum counterexample. Both weaken any claim that finding incomplete tests through mutations is itself novel. Retain this as a motivating case for TMLR discussions; publication-level novelty and baseline advantage remain unestablished.

[Opinion] The next scientific gate should freeze a task set and property families before examining test weaknesses; record prior exposure; compare equal-budget direct assertion review and ordinary mutation testing; use held-out properties and independently developed correct implementations; and log actual investigation effort, including failures. An assistant-only comparison must be labeled as such, not presented as measured human productivity. Proceed toward reusable product machinery only if that comparison shows a useful advantage or an evaluation owner validates the workflow's usefulness.

No production certification code, B1 artifact, or original scientific outcome changed. No merge, push, issue submission, publication, or external message was performed.
