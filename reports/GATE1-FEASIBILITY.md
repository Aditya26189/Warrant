# Grader audit Gate1: calibration feasibility — 26 October 2026

**[Evidence] Calibration passed. Family-wide feasibility, human setup cost and
discovery value remain unverified.** This closes the corrected Gate1 deliverable;
it does not certify every gate in the original proposed roadmap as passed.

The reference and a structurally varied implementation of HumanEval/0 each
passed all 7 base and 999 plus inputs through the pinned, unchanged EvalPlus
evaluator in three fresh processes. Each run also passed 3,324 checks against
an independent, explicitly partial specification property. These repetitions
reuse the same cases; they are repeatability checks, not independent samples
of tasks or discoveries.

**[Opinion] This is enough to retain a small calibration harness. It is not
enough to justify a custom discovery engine, a publication claim or a product.**
The experiment has not attempted to find a new omission. Its useful result is
a reproducible way to check two controls against both the actual grader and a
separate correctness property, without GPU or model API spending.

## Scope and task choice

[Evidence] The corrected [protocol](../docs/FEASIBILITY_EXPERIMENT_SPEC.md) and
[decisions G019–G021](../experiments/grader_poc/DECISIONS.md) limit this step to
one calibration task and prompt-only reservation of three other identities.
No mutant, repair, coverage-ranking engine or held-out execution was added.
The existing [payments result](PHASE-GRADER-PAYMENTS-E2E.md) remains an exposed
development example with its original evidence and limitations. Its alternative
control changes one predicate; it is not a broadly independent implementation.
No new payments experiment or stronger claim is made here.

The selected family is **full HumanEvalPlus v0.1.10**, not Mini, NoExtreme or
only the original HumanEval inputs. The archived calibration row contains every
base and plus input for that task. The evaluator uses its native
`untrusted_check` function with `fast_check=False`; expected upstream outputs
and reference timings come from its native `trusted_exec`. Those upstream
expected values are reference-derived. They are distinct from our independent
partial property below.

| Candidate | Decision and evidence | Limit |
|---|---|---|
| Original HumanEval | Rejected as a current maintainer-feedback target: pinned README explicitly says deprecated/unmaintained. MIT attribution retained. | Still useful historical source; not evidence of current adoption demand. |
| Full HumanEvalPlus | Selected: permissive data, deterministic function interface, locally runnable official evaluator, stronger existing tests. | Established prior work already improves these tests. Last observed evaluator commit is 2025-10-02; maintainer responsiveness is unverified. |
| Payments / prior Terminal-Bench work | Retain the existing evidence, outside this small-function family. | Kafka/HTTP setup and previous exposure make it a poor basis for cheap, unfamiliar-task discovery claims. |

[Evidence] Source pins and bytes:

- EvalPlus source: `26d6d00bb1fd0fa37f39c99d5290da67891d1c5e`.
- HumanEval historical source: `b9453e8f1865df0a0057a1383767caa400acfbcf`.
- Full dataset archive SHA-256:
  `272720b90ac375502c8ed23cd791c2a93dfb22a911641a494da74a426c09f101`.
- Frozen [config](../experiments/grader_poc/feasibility/config.json),
  [selection manifest](../experiments/grader_poc/feasibility/fixtures/selection.json),
  [calibration row](../experiments/grader_poc/feasibility/fixtures/calibration.json),
  [EvalPlus license](../experiments/grader_poc/feasibility/fixtures/EVALPLUS-LICENSE)
  and [HumanEval license](../experiments/grader_poc/feasibility/fixtures/HUMANEVAL-LICENSE).

## Feasibility criteria and reserved tasks

[Evidence] All non-calibration IDs in the 164-record release were ranked by
ascending SHA-256 of UTF-8 `warrant-gate1-20261026:` plus task ID. The first three
were reserved before measuring outcomes. No outcome-based replacement occurred.

| Task | Local, deterministic and under 2 s | Written contract / scoped property | Reference and alternative | Cheap reset | No required paid calls | License |
|---|---|---|---|---|---|---|
| /0 `has_close_elements` | Observed across six fresh runs; both full-grader and outer durations under target | Partial property frozen and checked | Both accepted on every base/plus input | Fresh CPU process per run | Observed: none used | Apache-2.0 data; retained upstream notices |
| /87 `get_row` | Unverified; not executed | Prompt specifies coordinate ordering; property not built | Bodies uninspected; controls unverified | Expected from interface, unmeasured | Expected from interface, unmeasured | Same data source |
| /57 `monotonic` | Unverified; not executed | Strict versus weak monotonicity unresolved | Bodies uninspected; controls unverified | Expected from interface, unmeasured | Expected from interface, unmeasured | Same data source |
| /18 `how_many_times` | Unverified; not executed | Prompt explicitly includes overlapping occurrences; property not built | Bodies uninspected; controls unverified | Expected from interface, unmeasured | Expected from interface, unmeasured | Same data source |

[Inference] The function interface makes the reserved tasks plausible candidates,
but it does not establish their runtime or oracle construction cost. Resolve
/57 from authoritative requirements or restrict its property to unambiguous
inputs before looking at assertions. Do not silently choose semantics from its
reference, or replace the task after seeing an inconvenient outcome.

[Evidence] Reserved records were parsed and hashed as dataset transport; only
identity, prompt, contract and entry point were displayed/exported. Their
reference bodies and test values were not inspected or executed. This is not
access-controlled blinding. Prior model familiarity cannot be ruled out.
The dataset license page incidentally displayed /0's reference and snippets
for unselected /1–/5 before calibration construction; G020 discloses this.
There is no claim that /0 or its alternative was developed independently of
all reference exposure.

## Independent property and its limits

[Evidence] The [property implementation](../experiments/grader_poc/feasibility/calibration.py)
interprets the prompt's question about two numbers closer than the threshold
as a boolean existential statement over **distinct list positions**, with a
strict distance comparison. It computes pairwise distances with
`Fraction.from_float`, without executing the reference.

The declared domain contains lists of length 0–8, quarter-grid float elements
from -4 to 4, and positive quarter-grid float thresholds from 0.25 to 4.
Empty and singleton lists return false; equal values at different positions
can satisfy the property. Non-boolean outputs fail. Inputs outside the domain,
including NaN and infinity, cause explicit `OUT_OF_DECLARED_DOMAIN` abstention;
they are not counted as candidate specification violations.

The reference sorts and checks adjacent gaps. The alternative inserts each
value into a sorted list and checks its immediate neighbors, without changing
the caller's list. Nearest-neighbor ordering explains why this implements the
existential distance condition on the declared domain. The evidence nevertheless
reports finite validation, not universal validity across every Python float.

The frozen corpus has `4 * (1 + 5 + 25 + 125 + 625) = 3,124` exhaustive cases
over the smaller configured grid, plus 200 seeded cases from the broader
declared domain, for 3,324 checks per run. Seed: 1729. The corpus is neither
exhaustive over the whole declared domain nor a representative traffic sample.
The broader upstream tests and this partial property are separately reported.

## Measurements and setup cost

[Evidence] The authoritative per-run table is generated in
[MEASUREMENTS.md](../experiments/grader_poc/feasibility/evidence/MEASUREMENTS.md).
All six receipts record `COMPLETED`, 7/7 base, 999/999 plus, and zero property
mismatches. Full base-plus grader durations range from 0.057002 to 0.104433
seconds; outer worker durations range from 1.014796 to 1.528538 seconds.
Controller execution was 7.088420 seconds. Timing is specific to this machine
and these controls, not a performance guarantee for mutants or other tasks.

Grader duration includes the two native grader calls and their child-process
overhead. Outer duration additionally includes interpreter startup, imports,
reference-output preparation and property checks. Installation and acquisition
are outside both. No model inference, paid service or GPU was used; existing
local CPU, storage, network and electricity are not asserted to have zero cost.

[Evidence] The successful run used Python 3.12.3 under Ubuntu/WSL, numpy 2.2.6
and psutil 7.0.0 in an isolated temporary environment. See the pinned
[requirements](../experiments/grader_poc/feasibility/requirements.txt) and
[setup event record](../experiments/grader_poc/feasibility/setup_events.json).
Recorded friction includes missing dependencies, initial WSL access denial,
and a failed first launch: Linux Git could not resolve the Windows worktree's
Git directory pointer. That launch exited before output-directory creation
or candidate execution. G021 reused the existing WSL-aware Git helper; task,
property, alternative and budgets did not change. The failure survives as a
structured event and decision, not as a complete archived raw stderr file.

The recorded assistant interval from repository discovery to successful run
completion was 21.812 minutes. It includes orientation, acquisition, coding,
testing, setup and the failed preflight. It excludes later packaging/reporting
and the interruption after execution. It is **not active human labor, total
project effort, or isolated oracle construction time**.

| Setup-cost question | Answer |
|---|---|
| Human minutes for calibration | Unmeasured; `null`, not zero |
| Human minutes for each reserved task | Unmeasured; no oracle/control constructed |
| Does the 90-minute human setup stop rule pass? | Cannot be scored from this run |
| Is per-task oracle work known to dominate? | No; neither dominance nor cheap generalization was measured |

[Opinion] Do not claim the overall adapter-cost gate passed. It is reasonable
to review a small conventional-mutation baseline next, but no evidence here
justifies investing in special mutation operators or coverage ranking.

## Evidence integrity and validation

[Evidence] Fixture preparation ran from clean source
`9fdb2f5d1fa4f21f083e9377f6aa0c5b37727793`. Successful execution ran from clean
`7a7b68d47dbfdc08b6c314224b2723c1a836e359`; packaging ran from clean
`226fdbbc3a565b13e079551ba9f66dc366cdd9c4`.

The [packager](../experiments/grader_poc/feasibility/package_gate1.py) verified
the frozen config and fixture bindings, every control's candidate bytes,
all pass-detail counts, the generated corpus, expected/observed property
hashes, per-worker JSON/stdout agreement and empty stderr. It retained
byte-identical copies of all 20 files in the successful run directory, plus
the generated measurements. The [manifest](../experiments/grader_poc/feasibility/evidence/manifest.json)
binds those 21 payloads by size and SHA-256; it does not hash itself.
The [outcome](../experiments/grader_poc/feasibility/evidence/outcome.json)
retains upstream file hashes, environment versions, durations and receipts.
These are reproducibility bindings, not third-party attestation or signatures.

Eight focused unit tests pass, covering partial-domain boundaries, strict
comparison and distinct positions, output type, input preservation, corpus
repeatability, reserved-field exclusion, incomplete/failing receipts and the
fixed-control interface. Ruff and whitespace checks pass. This phase did not
rerun the production suite or claim validation of unchanged production code.

The controller owns and cleans up fresh worker process groups and writes
receipts for execution failures. This run exercised no timeout. The runner
executes only the two reviewed controls; it is not a validated hostile-code
sandbox. Do not expose it as an arbitrary candidate execution service.

## Reproduction

[Evidence] Use a clean committed checkout and a fresh output directory outside
it. Linux/WSL is needed for the upstream POSIX timers. On Windows-created
worktrees, the existing provenance helper also requires `git.exe` and `wslpath`.
Clone EvalPlus at the pinned SHA above; its source is imported directly, not
installed into Warrant's core dependencies.

```sh
python3 -m venv /tmp/warrant-calibration-env
/tmp/warrant-calibration-env/bin/python -m pip install -r experiments/grader_poc/feasibility/requirements.txt
/tmp/warrant-calibration-env/bin/python -m experiments.grader_poc.feasibility.run_calibration --evalplus-root ../evalplus-feasibility-source --out ../fresh-calibration-run
python -m experiments.grader_poc.feasibility.package_gate1 --raw ../fresh-calibration-run --out ../fresh-calibration-packet
python -m unittest experiments.grader_poc.feasibility.test_feasibility -v
python -m ruff check experiments/grader_poc/feasibility
```

Ruff is a development check, not a runtime dependency. The committed fixture
is sufficient for this calibration run; the full dataset is only needed to
reproduce selection/preparation. The `prepare` module accepts `--archive`,
`--evalplus-root`, `--humaneval-root` and a fresh `--out`, verifies the archive
and evaluator pins, and extracts the calibration and prompt-only reservations.
Do not overwrite committed fixtures with newly timestamped preparation output.
Fresh runs will change timing, timestamps and recorded source revision; the
target reproduction is matching candidates, cases and outcomes.

## What remains unproven and the next decision

- **[Evidence] No new false pass was sought or discovered in this phase.**
  There is no mutation comparison, held-out result, repair or measured
  advantage over manual assertion review.
- **[Inference] Passing controls establishes a working local apparatus for
  this one scoped task.** It does not establish that the oracle is cheaper
  to write than the missing test, or that another grader needs this tool.
- **[Evidence] Prior work is directly relevant.** EvalPlus already expands
  code-evaluation tests; its existence makes novelty and stronger-test checks
  necessary before any future finding is called previously unknown.
- **[Opinion] Review a conventional baseline before adding an engine.** Any
  future ordering comparison must use identical candidates, operators,
  witness inputs and budgets. Drop ordering if it provides no benefit. Real
  human productivity claims need human measurements; agent review is a
  separately labeled comparator. Later gates were not executed here.
- **[Evidence] Maintainer interest, willingness to pay, publication prospects
  and career value are unverified.** This work remains Warrant's optional
  grader-audit experiment, separate from statistical certification.

## Source quality and conflicts

External source claims were checked on 26 October 2026 during selection.

| Source | Date / version | Type and supported claim |
|---|---|---|
| [EvalPlus pinned source](https://github.com/evalplus/evalplus/tree/26d6d00bb1fd0fa37f39c99d5290da67891d1c5e) | Commit 2025-10-02; pinned above | Primary: evaluator code and license. Does not establish current hiring, demand or responsiveness. |
| [HumanEval pinned README](https://github.com/openai/human-eval/tree/b9453e8f1865df0a0057a1383767caa400acfbcf) | Commit 2026-10-16 | Primary: explicit deprecated/unmaintained status and historical attribution. |
| [Full data release](https://github.com/evalplus/humanevalplus_release/releases/download/v0.1.10/HumanEvalPlus.jsonl.gz) and [release repository](https://github.com/evalplus/humanevalplus_release) | v0.1.10; release date not established here | Primary: acquired bytes, record contents and declared Apache-2.0 license. Pinned old data, not a claim of latest benchmark coverage. |
| [EvalPlus paper](https://arxiv.org/abs/2305.01210) | 2023 | Primary research: directly related work on insufficient code-evaluation tests. Establishes overlap, not our novelty or effectiveness. |
| [Local receipts](../experiments/grader_poc/feasibility/evidence/outcome.json) | 2026-10-26 | Primary experimental record, produced and checked by the same assistant. No independent replication. |

[Evidence] The assistant is provided by OpenAI; HumanEval originated at OpenAI.
That affiliation is a potential conflict, not an endorsement of a commercial
service. No OpenAI API was used. The same assistant selected, implemented and
checked this calibration, so source hashes and repeatability must not be
presented as independent scientific review.
