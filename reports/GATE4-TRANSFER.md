# Frozen grader-audit transfer: closing report — 27 October 2026

**[Evidence] The frozen conventional baseline ran on all three reserved tasks.
All 37 generated mutations were rejected by the full existing graders. No
full-grader survivor or specification-backed omission was found.** The nine
control trials passed. This closes the bounded feasibility study.

**[Opinion] Stop investing in a custom grader-discovery engine on the current
evidence.** Keep the reproducible experiment and the earlier validated examples
as an optional Warrant research artifact. This study supplies no demonstrated
discovery advantage, publication-level method contribution or product demand.
There is no finding here to repair or submit upstream.

## Question and work performed

The question was whether the small conventional mutation method could transfer
from calibration to unfamiliar task identities and expose an omission in the
stronger existing tests. A separate question about human setup costs remains
unanswered: no human timesheet or human comparison was collected.

[Evidence] The three identities were reserved in Gate1 by a deterministic hash
rule, before calibration outcomes: HumanEval/87, /57 and /18. G023 and the
[transfer config](../experiments/grader_poc/transfer/config.json) fixed the next
step. All [properties, alternatives and witness generators](../experiments/grader_poc/transfer/properties.py)
were committed at `63cc002` before extracting their reference bodies and test
values. The full dataset revision and archive hash are unchanged from
[Gate1](GATE1-FEASIBILITY.md). No task was substituted or excluded after outcomes.

The task adapter imports the existing source-preserving `mutations()` method
and verifies its source/config against `c98f1ea`. The operator set, deterministic
ordering, 64-candidate cap, 30-second worker deadline and 600-second per-task
execution cap were unchanged. The existing process runner and outcome
classification are also reused. There was no new coverage heuristic, mutator
operator, model call or paid computation.

Each task ran the reference and independently written alternative first, all
generated candidates next, and the reference again afterward. Every candidate
used every base and plus input through the unchanged pinned EvalPlus evaluator.
Only a full-grader survivor was eligible for the independent specification check.

## Results

[Evidence] All numbers below are derived by the committed
[verifier](../experiments/grader_poc/transfer/package.py) in
[summary.json](../experiments/grader_poc/transfer/evidence/summary.json) and the
per-trial [measurement table](../experiments/grader_poc/transfer/evidence/MEASUREMENTS.md).

| Reserved task | Base + plus inputs | Mutations evaluated | Passed base, rejected by plus | Full survivors | Confirmed omissions | Task execution seconds |
|---|---:|---:|---:|---:|---:|---:|
| /87 `get_row` | 6 + 207 | 10 | 0 | 0 | 0 | 20.909536 |
| /57 `monotonic` | 8 + 971 | 21 | 2 | 0 | 0 | 35.897427 |
| /18 `how_many_times` | 4 + 1,000 | 6 | 0 | 0 | 0 | 12.571191 |
| Total | Task-specific inputs | **37** | **2** | **0** | **0** | See controller total below |

All generated candidates were evaluated; none hit the candidate cap. There
were no invalid controls, worker timeouts, harness failures or incomplete
trials in this scientific run. No mutant reached witness search, so the
survivor-to-witness discovery path was not exercised end-to-end on a benchmark
mutant. Unit tests and accepted controls are narrower evidence.

The run performed 46 trials: 37 mutants plus 9 controls. Base and plus are
separate native calls, giving `46 * 2 = 92` calls. Input checks total
`13 * 213 + 24 * 979 + 9 * 1,004 = 35,301`. The controls performed
`9 * 200 = 1,800` property checks; mutant property checks were zero. Confirmation
yield is undefined with zero survivors, represented as `null`, not zero percent.

The witness corpora contain 200 cases per task, with respectively 178, 199 and
196 distinct inputs. Repeated cases and repeated control trials are not
independent statistical samples. These deterministic task/candidate counts do
not estimate an omission prevalence or justify a population confidence interval.

**[Evidence] Combined with the calibration baseline, the fixed method rejected
`13 + 37 = 50` mutations across four tasks, with no new omission.** This combined
count describes these pools only; mutations within a task are highly related.

### What the stronger tests already catch

[Evidence] On /57, `mutant-005` changes the loop bound from `len(l) - 1` to
`len(l) - 2`, skipping the final adjacent comparison. `mutant-009` changes
`>` to `>=`. Both pass the eight base inputs and fail the expanded tests. Their
exact edits and source are in the [frozen pool](../experiments/grader_poc/transfer/evidence/prepared/57/pool.json).

[Inference] A base-only experiment would have two apparent survivors here;
the existing full grader already rejects them. That echoes the calibration's
strict-boundary example. No independent witness was sought for either rejected
candidate. In particular, the equality mutation concerns behavior outside our
monotonicity property's declared scope; its rejection does not resolve the
prompt's strict-versus-weak ambiguity.

## Properties, ambiguity and control quality

| Task | Declared property scope | Alternative and limitation |
|---|---|---|
| /87 | Bounded ragged integer lists; exact coordinate completeness, multiplicity and row-ascending/column-descending order; list of integer tuples | Reverse-column traversal. After exposure, the supplied reference also uses reverse traversal, so algorithmic diversity is modest despite independent authorship. |
| /57 | Distinct bounded integer lists of length 2–8; all pairwise ordered differences must have one direction | One-pass rising/falling tracker. Reference also tracks directions. Equal, empty and singleton inputs remain outside the property. |
| /18 | Bounded binary-alphabet text and nonempty substring; exact count including overlaps; integer return | Repeated `find`, advancing by one. Reference uses a scan with `startswith`, providing a different implementation. |

[Evidence] The monotonicity alternative assumed weak behavior outside the scoped
domain before grader exposure. Its acceptance is an observation, not authority
for the ambiguous wording. No property, control or case generator was changed
after reading the reference or seeing results. Out-of-domain inputs raise an
explicit abstention. No claim covers the full input contracts.

[Inference] These controls guard against some accidental overconstraint; they
do not establish compatibility with every valid implementation. The oracle and
alternatives were authored by the same assistant. Their independence from
reference execution does not make them independently validated research.

## Runtime and setup cost

[Evidence] Total controller execution was **75.240581 seconds**. The sum of
per-task durations is smaller because the controller also verifies the prepared
packet and source provenance. Each task stayed within its 600-second cap.
The nine full native grader durations ranged from 0.043759 to 0.130644 seconds,
below the declared two-second grader target. However, complete worker times
for controls ranged from 1.761726 to 3.998252 seconds, including process startup,
imports, reference preparation and property checks. **A two-second target for
the whole worker was not consistently met.**

Automated fixture/corpus preparation took approximately 0.312398, 0.192642 and
0.167684 seconds per task. These are script runtimes, not the cost of writing
properties or understanding the prompts. The existing environment and earlier
oracle/tool development are reused costs, not free work.

The initial Git commit attempt was blocked by the automatic approval service's
usage limit before execution. It succeeded through the normal approval path
after the user resumed. The recorded initial start is 20:31:26 UTC on 26 October;
resumption was observed at 23:07:40 UTC. The scientific run finished at
23:14:11.974001 UTC, or 04:44:11.974001 IST on 27 October. That interrupted wall
span is not an engineering-effort estimate. No human-active or trustworthy
per-task authoring minutes were measured, so the 90-minute human setup rule
cannot be scored as passed or failed.

## Closing decision

**[Opinion] No-go for further custom discovery-engine development under this
project proposal.** The bounded experiment is complete, and neither adding
coverage ordering nor more infrastructure is justified by its results. Ordering
cannot make an already fully evaluated, fully rejected pool produce a survivor.
No ordering arm was run; this is a logical limit of the observed pool, not a
measured speed comparison.

Retain the earlier session-window and payments counterexamples with their
existing qualifications: they are reproducible known omissions identified with
grader exposure, not evidence that this new method discovers unfamiliar ones
better than simpler review. Warrant's statistical-certification work is separate
and unchanged.

This is a narrow no-go. The tasks are short functions with established expanded
tests; first-order mutation of supplied references may poorly represent
real-world model errors or custom evaluator failures. Those limitations prevent
a claim that all grader auditing is unhelpful. They also do not create positive
evidence for this particular engine. No production feature, novel paper method
or commercial opportunity has been validated.

Reopen only for a concrete external evaluator problem with an independent
requirement, reproducible failure and a plausible repeated workflow where
setup effort can be measured against ordinary review. Expanding operators or
changing datasets merely to obtain a positive result would be a new exploratory
study, not successful completion of this one. No new dataset search is performed
in this closure. The external finding/repair packet condition was not met, so
no patch or message was submitted upstream.

## Evidence and reproduction ledger

- Design decision: G023 at `ba3d795`. Properties, alternatives, generators,
  extraction and execution source: `63cc0026ebdc99792c9d61c0ea60b3beb936d7d3`.
  Packaging source: `8c02404` (full revision in the manifest). Scientific
  extraction, execution and packaging each recorded clean source.
- The [manifest](../experiments/grader_poc/transfer/evidence/manifest.json)
  binds **203 payloads**: 13 prepared files, 188 raw execution files and two
  derived measurement files. Prepared and raw copies are byte-identical; the
  manifest does not hash itself. No prior evidence packet was modified.
- The [outcome](../experiments/grader_poc/transfer/evidence/raw/outcome.json)
  retains all task/trial results, hashes of upstream evaluator files, runtime
  versions and native details. Preparation retains the original reserved-record
  hashes and the pre-exposure property source hash.
- The packager regenerates pools/corpora, recomputes all typed control
  observations and displayed totals, and verifies source/receipt/stdout
  bindings. A separate copied packet with an altered candidate file was
  rejected. This is an integrity check, not independent scientific replication.
- All **26 focused calibration/baseline/transfer tests passed under Linux**.
  Ruff passed on the six transfer source/test files. Production was not changed
  or retested in this phase. Raw evidence preserves
  original source whitespace; it must not be normalized merely to silence
  generic lint/diff warnings on copied upstream code.

From clean committed source, using the Gate1 pinned EvalPlus checkout and
Linux environment, write each output to a fresh directory outside the repo:

```sh
python -m experiments.grader_poc.transfer.prepare --archive ../HumanEvalPlus-v0.1.10-feasibility.jsonl.gz --out ../fresh-transfer-prepared
/tmp/warrant-gate1-20261026-venv/bin/python -m experiments.grader_poc.transfer.run --evalplus-root ../evalplus-feasibility-source --prepared ../fresh-transfer-prepared --out ../fresh-transfer-run
python -m experiments.grader_poc.transfer.package --prepared ../fresh-transfer-prepared --raw ../fresh-transfer-run --out ../fresh-transfer-package
python -m unittest experiments.grader_poc.feasibility.test_feasibility experiments.grader_poc.baseline.test_baseline experiments.grader_poc.transfer.test_transfer -v
```

The reproduction target is matching pools, scoped properties and verdicts;
timing and source metadata naturally differ. Held-out reservations have now
been exposed and evaluated; they cannot be reused as fresh holdouts in a tuned
follow-up. Source/date/license and OpenAI affiliation disclosures remain in
Gate1. All findings here are primary local observations from the same assistant;
external demand, novelty and willingness to pay remain unverified.
