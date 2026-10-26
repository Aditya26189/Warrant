# Gate2: conventional calibration mutation baseline — 26 October 2026

**[Evidence] All 13 generated mutations were rejected by the full unchanged
grader. No full-grader survivor or new specification-backed omission was found.**
The reference and structurally varied alternative both passed before the pool;
the reference also passed afterward. This completes the authorized calibration
baseline, not the full research roadmap.

**[Opinion] Do not build coverage ranking or a more elaborate mutation engine
on the strength of this result.** It demonstrates that this small conventional
pool adds no new omission to the stronger existing tests. It does not demonstrate
that auditing other graders is worthless, nor establish a useful discovery
method, startup or publication contribution.

## What was run

[Evidence] Decision [G022](../experiments/grader_poc/DECISIONS.md) and the
[config](../experiments/grader_poc/baseline/config.json) froze the rules before
candidate execution. The task, domain, partial property, reference, alternative
and pinned full HumanEvalPlus/EvalPlus grader are inherited unchanged from
[Gate1](GATE1-FEASIBILITY.md). No held-out task, payments trial, model API or
GPU was used.

The [generator](../experiments/grader_poc/baseline/candidates.py) makes one
source-span change per candidate inside the reference function body:
relational boundary changes, comparison negation, addition/subtraction swaps,
numeric constant offsets or zero, boolean flips, and constant guards. It
preserves all other bytes, including comments, docstrings and annotations.
Candidates are sorted by byte location, operator and replacement; identical
candidate bytes are deduplicated. All 13 generated candidates fit inside the
64-candidate cap; none was dropped.

This is a **custom implementation of conventional first-order operators**.
It is not a measured run of PIT or mutmut, and the pool does not cover all their
operators, higher-order changes or realistic model-generated errors. No
formatting-only AST reprint was introduced. The candidate sources and exact
edits are retained in the [pool](../experiments/grader_poc/baseline/evidence/pool.json).

The [runner](../experiments/grader_poc/baseline/run.py) invokes unchanged
`evalplus.eval.untrusted_check` on every original base and plus input, with
`fast_check=False`, in a fresh process for each candidate/control. Native
reference-output preparation is charged separately in each receipt. A
full-grader survivor would then receive the same 200 existing Gate1 seeded
inputs, in fixed order with seed 1729, through the unchanged independent
quarter-grid property. Reference divergence alone would not qualify as a
specification failure. All 200 inputs would be checked, with the first witness
and total violations retained. There were no mutant survivors, so that search
was not invoked for any mutant.

## Results

[Evidence] Values below are recomputed by the
[packager](../experiments/grader_poc/baseline/package.py) in
[summary.json](../experiments/grader_poc/baseline/evidence/summary.json) and
[MEASUREMENTS.md](../experiments/grader_poc/baseline/evidence/MEASUREMENTS.md).

| Observation | Result |
|---|---:|
| Generated and evaluated mutants | 13 |
| Rejected by original base tests | 12 |
| Passed base, then rejected by plus tests | 1 |
| Rejected by full base-plus grader | 13 |
| Full-grader survivors / confirmed violations | 0 / 0 |
| Invalid candidates, worker timeouts or apparatus failures in this run | 0 |
| Control trials accepted on all 1,006 inputs | 3 |
| Native grader calls, counting base and plus separately | 32 |
| Grader input checks, including controls | 16,096 |
| Mutant / control property checks | 0 / 600 |
| Total controller execution | 17.862710 seconds |
| Unused portion of 600-second execution cap | 582.137290 seconds |

The arithmetic is `16 trials * 2 splits = 32 calls`,
`16 * (7 + 999) = 16,096 input checks`, and `3 * 200 = 600 control property
checks`. The control checks reuse one corpus and do not supply 600 independent
samples. Execution-to-first-finding is undefined because no finding occurred.
Confirmation yield is undefined because there were no full survivors; the
JSON uses `null`, not a misleading zero percentage.

### The revealing boundary mutation

[Evidence] Candidate `mutant-011` changes the strict comparison `< threshold`
to `<= threshold`. It passes **7/7 base inputs**, but only **993/999 plus
inputs**. The full grader correctly rejects it. The other 12 mutations are
already rejected by the base inputs. See its
[source](../experiments/grader_poc/baseline/evidence/mutant-011.py) and
[receipt](../experiments/grader_poc/baseline/evidence/mutant-011.json).

[Inference] An experiment using only the weaker base tests could promote this
boundary survivor into an apparently useful result. The full tests show that
the stronger existing evaluation already addresses it. This is evidence for
using the existing stronger benchmark as the comparison, not evidence that
Warrant discovered a previously unknown EvalPlus omission. No separate
specification-witness search was performed on this rejected candidate.

[Inference] Reordering this exact fully evaluated pool cannot create a
full-grader survivor. That follows from the fixed candidate outcomes; it is
not an empirical timing comparison of coverage ranking versus source order.
No ranking arm was run, and the pool was not expanded after the negative result.

## Effort, failures and practical limits

[Evidence] The recorded assistant interval from the recorded start during orientation at
16:39:43 UTC to run completion at 16:49:19.835780 UTC was 9.614 minutes. This
includes implementation and setup/checks through execution, but excludes later
verification, packaging and reporting. It is not active human labor, total
project effort or the cost of learning the field. The earlier Gate1 oracle and
environment are reused rather than free. Human effort remains unmeasured.

An initial Windows unit-test attempt failed on sandbox temporary-directory
permissions. The tests then ran in the existing Linux environment; all 11
passed, including a real process-timeout receipt test. This setup failure is
recorded here and in the implementation commit, not counted as a benchmark
candidate failure. The scientific run itself had one attempt and no apparatus
failure. Ruff and source/document whitespace checks passed. The archived
reference and mutant source files preserve the upstream blank line at EOF;
Git's generic whitespace check flags those retained bytes. They were not
trimmed, because that would invalidate the executed-candidate hashes.

The 30-second worker deadline and 600-second aggregate cap are operating
limits, not economic or statistical guarantees. EvalPlus's internal rejection
details do not distinguish every per-input exception from every per-input
timeout; the receipts report native grader results without inventing that
granularity. Top-level timeouts and incomplete grading are represented
separately and cannot become confirmed findings. The generated sources are
local, reviewed arithmetic/control-flow variants; this runner is not a
production sandbox for arbitrary hostile submissions.

## What the result does not establish

- **[Evidence] One familiar task and one small candidate pool were evaluated.**
  There is no held-out result, multi-seed study, independent investigator,
  human review arm or empirical comparison with an off-the-shelf mutation tool.
- **[Inference] Rejecting these mutations does not prove grader soundness.**
  Input-conditional faults, output-type issues, other operator families and
  errors outside the scoped property remain outside this result. Adding such
  cases now would be a new, disclosed experiment rather than a rescue of this
  frozen one.
- **[Evidence] The survivor-to-witness path received unit checks, but no actual
  mutant reached it in this benchmark run.** Do not claim end-to-end discovery
  validation from the controls or synthetic unit tests.
- **[Evidence] No repair was needed or generated, and nothing was submitted
  upstream.** The run has no new discovery, repair-compatibility or maintainer
  acceptance evidence.
- **[Opinion] The strongest remaining rationale is a small reusable audit
  protocol.** A differentiated product or research contribution still needs
  unfamiliar-task findings and a measured advantage over simpler approaches.

## Decision and what would change it

[Opinion] Stop adding machinery on this calibration. Preserve the negative
result and the simple baseline. The next experiment capable of changing the
conclusion is a frozen transfer to the reserved tasks, after each task's
prompt-derived property, alternative control and feasibility have been resolved.
That step should retain ambiguous or infeasible tasks, charge oracle construction,
and report negative outcomes. It has not been performed here.

If ordinary mutation with a small explicit property finds useful omissions,
the simpler workflow may be enough; custom ranking still needs evidence. If
task-specific oracle work dominates or the full graders already reject the
available candidates, there is no basis to keep building an engine merely to
make this project look novel. Publication prospects, willingness to pay and
career value remain unverified.

## Reproduction and integrity ledger

- Frozen design: `f7eed93`; execution source:
  `c98f1ea5a93b4cff0123df3719faa4e3e47c7a84`; packaging source:
  `385bc4d` (full revision in the manifest). Each scientific operation recorded
  clean source. Gate1 and earlier research packets remain unchanged.
- The [manifest](../experiments/grader_poc/baseline/evidence/manifest.json)
  hashes all 67 byte-identical raw files plus two generated measurement files:
  **69 payloads**. The manifest does not hash itself.
- [Outcome](../experiments/grader_poc/baseline/evidence/outcome.json) retains
  every trial, native pass details, upstream file hashes, environment versions,
  timing and configuration. Linux Python 3.12.3, numpy 2.2.6 and psutil 7.0.0
  are reused from Gate1.
- The verifier recomputes the pool, input corpus, counts and control property
  observations, and checks source/receipt/stdout agreement. A deliberate change
  to `mutant-011.py` in a separate copied packet was rejected by the verifier.
  This tests byte binding; it is not independent replication or cryptographic
  attestation by a third party.

From clean source under Linux/WSL, with the Gate1 pinned EvalPlus checkout and
environment, use fresh output directories outside the source tree:

```sh
/tmp/warrant-gate1-20261026-venv/bin/python -m experiments.grader_poc.baseline.run --evalplus-root ../evalplus-feasibility-source --out ../fresh-baseline-run
python -m experiments.grader_poc.baseline.package --raw ../fresh-baseline-run --out ../fresh-baseline-packet
python -m unittest experiments.grader_poc.baseline.test_baseline -v
python -m ruff check experiments/grader_poc/baseline
```

Ruff is a development dependency, not a runtime requirement. The same frozen
candidates and verdicts, rather than exact timings, are the reproducibility
target. No production suite rerun or production integration is claimed here.

[Evidence] These are primary local experimental observations from 26 October
2026, produced and checked by the same assistant. Upstream source/date/license
and OpenAI affiliation disclosures remain in the linked Gate1 report. No new
market, novelty or external demand claim is inferred from these measurements.
