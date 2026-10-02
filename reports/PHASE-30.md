# Phase 30 - Prepare a scored export for replayable review

Warrant can now turn an existing flat scored CSV or JSONL export into a
canonical scored file using an explicit, versioned mapping. `verify-prepared`
recomputes the transformation from the original export and mapping and detects
a changed package. This closes a specific handoff gap: manually renaming
columns or negating a score could silently reverse the label meaning or drop
the grouping that determines the unit of evidence. It does not certify the
detector or establish that anyone needs a separate review packet.

## Why this work, and why this scope

The [October research memo](AI-OPPORTUNITIES-2026-10.md) checked recent
organizer-announced hackathon winners, current founder requests, enterprise
outcome pressure and incumbent evaluation products. A recurring pattern was
source-linked review of narrow workflows with human checkpoints. Dataiku's
September announcement already claims cross-platform agent governance,
certification-status records and scheduled tests; Braintrust documents human
review and CSV/JSON experiment exports, and its
[classifier-evaluation cookbook](https://www.braintrust.dev/docs/cookbook/recipes/PrecisionRecall)
demonstrates custom precision and recall. A broad agent-governance or generic
metric novelty claim would therefore be unjustified. The testable hypothesis
is narrower: a team may
need a locally replayable statistical handoff for a particular review trigger.
AWS also documents framework-agnostic AgentCore evaluations from OpenTelemetry
and OpenInference traces, so generic cross-framework evaluation is not a gap.
[AWS technical account](https://aws.amazon.com/blogs/machine-learning/evaluate-any-agent-framework-with-amazon-bedrock-agentcore-evaluations/).
OpenTelemetry defines evaluation score and label events, but such telemetry
does not by itself attest to human ground truth or independent sampling.
[OpenTelemetry event convention](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-events.md).
The [30-day plan](BUILD-PLAN-2026-10.md) and
[discovery packet](DISCOVERY-2026-10.md) put observed workflow evidence ahead of
further integration work.

Decision 227 preregistered the adapter's representation-only boundary before
code. It changes no model, test split, estimator, threshold-selection rule,
research result or protected scoring. No customer interview, real export,
deployment or paid use was available during this phase.

## Implemented behavior

`warrant prepare --input ... --mapping ... --out ...` requires source fields for
ID, label and finite detector score; an optional group and second-review label
can be mapped. The mapping declares both binary label tokens, whether larger or
smaller scores indicate the positive class, and either a group field or an
explicit independent-row declaration. Lower-is-positive scores are negated and
the declaration is retained. Existing intake validation rejects malformed
rows, duplicate IDs, ambiguous input fields, missing groups and nonfinite
scores. Preparation accepts a single-class file as representation, leaving the
existing downstream measurement command to decide whether the evidence is
sufficient.

The command creates a new directory and refuses replacement. It writes
`scored.csv` before the deterministic `manifest.json` completion marker. The
manifest binds original source bytes, mapping bytes, normalized bytes and the
effective scored-row sequence, records counts and excluded **column names**,
and does not copy excluded values into the package. `verify-prepared` rebuilds
the output and compares complete bytes. A missing marker, unexpected package
member or changed source, mapping or output does not verify. A checksum is not
an authenticated signature; neither command proves that labels are correct or
rows independent. The parser temporarily copies source bytes to the local OS
temp directory, so sensitive exports require an appropriate local environment
and possible interruption cleanup.

The installed command is exercised outside the checkout against a synthetic
600-row export, then its canonical output yields a VALID certificate under the
existing rules. This shows package wiring and compatibility, not field
performance. The four-row public example demonstrates the format and replay,
not a certificate. Its extra note column is excluded from scored output.

## Verification and evidence boundary

| Check | Result |
|---|---|
| New focused preparation suite | 40 tests passed: CSV/JSONL, mapped polarity, groups, second labels, malformed mappings and data, package mutation and refusal paths |
| Installed-wheel handoff test | Passed from outside the checkout; prepare, verify-prepared and existing certify form one local path |
| Ruff on changed Python | Passed |
| Clean-source full suite at `239a10b` | Exit code 0. Inventory separately recorded 2,180 collected tests; collection is not a passing-test count. The quiet full-suite output showed one expected-failure marker and no failure. |
| Clean-source smoke and claim replay at `239a10b` | Smoke 7/7; README claims 92/92; frozen-score comparisons 25/25; activation re-extraction SKIPPED |

The first full tracked-file clone of documentation head `1417c42` passed its
clone, smoke and preflight steps, plus claim/frozen-score verification, but its
full suite **timed out** at the configured 3,600 seconds while the separate
source suite was also running. That gate is FAILED, not a test pass. Its
[generated failure record](../results/clean_clone_failures/clean_clone-1417c421fdd2-1790877145512531400.json)
was committed at `c1d1fb1` before an uncontended retry. The retry from
`c1d1fb1` also timed out in the full suite while smoke, preflight and the two
available verifier tiers passed. Its
[second failure record](../results/clean_clone_failures/clean_clone-c1d1fb13f954-1790910956988075800.json)
was committed at `9ba929c`. The retry crossed an overnight interval and the
captured duration exceeded the configured timeout; the record did not retain
pytest's partial output. The gate now retains the final captured lines on
timeout (`003f361`, focused tests passed). The named temporary clones left by
Windows locks were verified under the OS temp directory and removed. A timeout
does not identify a failing test, and the passing source suite does not turn
either clone result green.

Decision 228, logged before its implementation, increased the unchanged full
clone-suite command's finite deadline to two hours (`8a3c6e8`). The 21 focused
clone-gate tests and lint passed. A direct full suite in the kept clone of
`bcfd5a1` exposed stale test-count prose: collection was 2,183 after the new
timeout regression and two document parametrizations, while README and Makefile
still said 2,180. The count assertion failed and the run was stopped; it is
not a pass. The exact preflight failure was reproduced on the merged branch,
then `scripts/refresh_test_inventory.py` regenerated the inventory and prose
from clean `3abe09c`. The two preflight tests now pass. The corrected full
clone gate remains the technical integration check.

The full clone of clean `95c4431` completed within the two-hour bound. Its
suite exited 1 after 2,744 seconds with one failure: this Phase 30 report
lacked the explicit "does not establish" and "open items" sections required
by `tests/test_reports.py`. Clone, smoke, preflight, and both available verifier
tiers passed. The generated
[failure record](../results/clean_clone_failures/clean_clone-95c4431e060f-1790916156138116200.json)
was committed at `888fa09` before this correction. This report-contract
failure is real even though it is not a product-code regression.

A tracked-only clone of `bcfd5a1` subsequently passed smoke and verification
with full tests deliberately omitted. Its
[separate check record](../results/clean_clone_phase30_no_tests.json) names
the exact clone and shows 92/92 claims, 25/25 frozen-score comparisons and
activation re-extraction SKIPPED. This check is not a full clean-clone gate.

## What this does not establish

The clean-source suite at `239a10b` and clone checks at their named commits
establish behavior only for those exact sources and environments. They do not
establish remote CI, fresh dependency resolution, GPU activation re-extraction,
or a passing full clone at a later source head. No scientific test set was
rescored and no protected result number moved. The example and installed test
are synthetic; they do not establish performance or usability on a customer's
export, sampling procedure or review decision. A prepared checksum package
does not authenticate an owner or prove that labels and groups are correct.

## Open items

The next useful input is one existing review packet and a permissioned scored
export with declared unit, label provenance and score direction. Ask who makes
the recurring threshold decision and whether their incumbent already provides
adequate uncertainty, refusal and replay. The October 14 targets in the plan
are five conversations, two usable exports and one named recurring decision;
none is an observed result here. Do not write a vendor-specific adapter from a
generic export claim or add a hosted service without such evidence. If the
incumbent packet suffices, narrow or stop the product hypothesis.

Technically, rerun the focused report contract and then the full clean-clone
gate from a clean commit containing this correction. The later October plan
requires one observed export, reviewer replay, repeat use, and a keep/pivot/stop
decision; those cannot be substituted with more synthetic tests.

## Ledger

| Change | Commit or evidence |
|---|---|
| Evidence-backed October plan and preregistration | `7c421ed`, Decision 227 |
| Strict export preparation and replay | `7291c61` |
| Installed-wheel exercise and synthetic example | `982f43f` |
| Clean-source test collection inventory | `239a10b` |
| Current product-state entry | `580f8e4` |
| README command discovery | `6b7a581` |
| Preserved first clone timeout | `c1d1fb1`; [failure artifact](../results/clean_clone_failures/clean_clone-1417c421fdd2-1790877145512531400.json) |
| Preserved second clone timeout | `9ba929c`; [failure artifact](../results/clean_clone_failures/clean_clone-c1d1fb13f954-1790910956988075800.json) |
| Diagnostic fix and narrowed competitive read | `003f361`, `bcfd5a1` |
| Preregistered bounded timeout adjustment | Decision 228; `8a3c6e8` |
| Tracked-only clone check | `bcfd5a1`; [no-tests artifact](../results/clean_clone_phase30_no_tests.json) |
| Refreshed integrated test inventory | `53aeef5`: 2,180 -> 2,183 collected, not an execution result |
| Preserved full-clone report-contract failure | `888fa09`; [failure artifact](../results/clean_clone_failures/clean_clone-95c4431e060f-1790916156138116200.json) |
| Mentor-facing progress brief | [October 2 brief](MENTOR-BRIEF-2026-10-02.md) |
