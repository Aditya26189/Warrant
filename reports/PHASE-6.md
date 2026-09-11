# Phase 6 — the action gate, and the rule that did not fire

**The question: does this system have a control that survives a detector losing?**

**Answer: yes, and the one the specification described did not.** `SPEC.md`
§9.3's Rule-of-Two, implemented exactly as written, **allows the canonical
indirect prompt injection** — because the transfer is the step that sets the
third session flag and the rule reads the session before the call. The first
version of the demonstration appeared to block the attack only because a
legitimate intermediate step set the flag first. Remove one innocuous step and
the defence disappears.

That is the worst property a security control can have: it works on the demo and
not on the attack. It was found by building the attack rather than by reading
the rule.

Fixed, measured, and the fix's cost counted: **2 of 8 declared legitimate
workflows are blocked**, both recoverable by starting a new session.

- **Window:** 2026-09-11
- **Range:** `33b04c0` → `HEAD`
- **Suite:** 1,190 at open → 1,214 at close, no failures at either end
- **Verification:** claim table 58/58 at open → **65/65** at close
- **Artifacts:** [`results/gate/`](../results/gate/)
- **Decisions:** `DECISIONS.md` 156
- **Method:** CPU only, offline

---

## 1. What was done

`controlplane/gate/`, the last unbuilt package in `CLAUDE.md`'s layout:

| module | what it holds |
|---|---|
| `registry.py` | Reversibility, declared per tool at definition time. Refused if absent or downgraded. |
| `session.py` | The Rule-of-Two: three sticky booleans, two of three the limit. |
| `gate.py` | The five rules, in order, each naming itself. |
| `agent.py` | A four-tool banking agent and the indirect injection. |
| `cost.py` | What the gate refuses that it should not. |

Plus `scripts/27_gate.py`, `tests/test_gate.py` (16 tests), and seven claim-table
rows.

---

## 2. The defect

**`SPEC.md` §9.3 rule 2, verbatim:**

```
BLOCK if rule_of_two_violated(session) and reversibility >= IRREVERSIBLE_WRITE
```

Measured on the four-tool agent, implemented as written:

| step | session flags | verdict |
|---|---|---|
| `get_balance` | `[X..]` 1/3 | ALLOW |
| `search_transactions` | `[XX.]` 2/3 | ALLOW |
| `transfer_funds` | **2/3 at decision time** | **ALLOW** |

The attack goes through. The transfer is the call that sets
`can_change_state_or_communicate`, and the rule reads the session *before* it.

**Why the first demonstration hid it.** The scenario in `agent.py` had the agent
draft a dispute — the thing the user actually asked for — between reading the
memo and attempting the transfer. That set the third flag, so the block fired,
and the demo looked correct. It was correct about a sequence the attacker does
not have to use.

**The fix**: evaluate the rule against the session as it would be **after** the
call. *Would running this give the session all three?* — not *does it already
have all three?*

**Checked against every path, because a rule that blocks the attack by blocking
everything is not a fix.** The four rows were registered in `DECISIONS.md` 156
before the change and are now `test_the_four_paths_registered_in_decisions_156`:

| sequence | verdict | right? |
|---|---|---|
| `get_balance` → `transfer_funds` | **ALLOW** | yes, nothing hostile was read |
| `get_balance` → `search` → `transfer_funds` | **BLOCK** | yes, this is the attack |
| `get_balance` → `search` → `draft_dispute` | **ALLOW** | yes, reversible and recoverable |
| `search` → `draft` → `transfer_funds` | **BLOCK** | yes |

So it blocks exactly the irreversible actions that would *complete* the triad,
and nothing else.

**Why it is a specification defect rather than a coding slip.** The Rule-of-Two
comes from agent-security work about what an agent **can do**. `SPEC.md`
transcribed it as three booleans describing what a session **has done**. Those
coincide for the first two flags — ingesting untrusted input and reading
sensitive data have happened by the time they matter — and come apart for the
third, because changing state is the thing being decided. **The transcription
lost exactly one case, and it is the only one an attacker needs.**

---

## 3. The phase gate

`docs/TASKS.md` Phase 9 asks for two things and both hold.

**An injected instruction passes every text-level check, visibly, and
`transfer_funds` is blocked on reversibility plus session state.** The memo is
plain English in a field the bank's own systems accept from a counterparty. No
unicode tricks, no encoding, no adversarial perturbation — if it needed a trick
to get past the detectors, the demonstration would be about the trick. No
detector flags it. The transfer is refused at step 4.

**`test_gate_no_detector` passes.** Every rule-1 and rule-2 decision computed
twice — once with a detector reporting CRITICAL and CONFIDENT_POSITIVE, once
with every detector input `None` — across four tools, six session states and six
warrant statuses:

| | |
|---|---|
| decisions reaching rule 1 or rule 2 | **33** |
| identical with and without a detector | **33** |
| mismatches | **0** |

The count is pinned exactly rather than bounded below, with its derivation in
the test, so a rule silently ceasing to fire becomes visible instead of being
absorbed by an inequality.

**This is deliberately a small claim.** It is not adversarial robustness and
this repository claims none: published work broke twelve injection defences at
over 90% attack success, so any control depending on detection has a ceiling
somebody has already measured. What is claimed is that **the decisions that
matter do not read a detector at all** — which, unlike robustness, can be
falsified by a test, and that test is what the number above is.

---

## 4. What it costs, counted

A security control that reports only its benefit is the kind nobody measures
until somebody turns it off.

| | |
|---|---|
| declared legitimate workflows | 8 |
| blocked by the gate | **2** |
| of those, recovered by a new session | **2** |

Both blocked workflows read a transaction memo and then try to pay someone,
which is exactly the pattern the rule exists to stop. **The control cannot tell
them apart from the attack and does not try** — that is precisely what makes it
independent of any detector, and this table is what the independence costs.

**These counts are EXACT, not estimated, and the distinction is load-bearing.**
The workflow set is *declared* — eight sequences written down, not drawn from
traffic — so it is a census with no sampling in it and carries no interval. The
same quantity on production traffic would be a **rate**: estimated, needing the
stratified estimator built in Phase 4, costing labels. Putting an interval on
this one would manufacture uncertainty about a count; quoting it *as* a
production false-block rate would be the scenario mixing `CLAUDE.md` invariant 6
forbids. `test_the_gate_cost_is_measured_and_is_exact_not_estimated` asserts
there is no interval field anywhere on the object.

---

## 5. What this does not establish

- **No robustness claim, and that is the point.** An attacker who defeats every
  detector does not move rules 1 and 2. An attacker who can register a tool, or
  who reaches the code that builds the session, does — and nothing here defends
  against that.
- **The eight workflows are a judgement, not a sample.** Whether they resemble
  real banking traffic is unmeasured, and every figure in §4 inherits it.
- **One domain, four tools.** The reversibility gradient is clean because it was
  designed to be. A real tool catalogue has tools whose blast radius is
  genuinely arguable, and the registry refuses those rather than resolving them.
- **No agent actually ran.** The transcript is the gate's decisions over a
  scripted call sequence. There is no model in the loop, which is deliberate —
  what is being tested is the gate, and a model in the loop would make the
  result depend on the model.
- **Rule 1 is duplicated.** It exists here and in the Rego bundles.
  `test_rule_one_matches_the_rego_bundles` checks they have not drifted, which
  is a check and not an architecture.

---

## 6. Open items

| # | item | what would close it |
|---|---|---|
| O-1 | **Rule 1 lives in two places.** The gate restates it because a gate that fails open when the policy engine is unreachable is not a gate, and because `policy/` is read-only here. | An owner for `policy/`, then either delete the local copy or make the bundle generated from it. |
| O-2 | **The session flags are set by tool metadata alone.** A tool that ingests untrusted input only *sometimes* is declared as always doing so, which is safe and coarse. | Measuring how often the coarse reading costs a legitimate workflow, which needs traffic. |
| O-3 | Carried forward unchanged: the twelve conversations; certifying a real judge; `DECISIONS.md` 145's Linux abort; the committed `RESULTS.md` not yet carrying the new sections. | See `reports/PHASE-5.md` §5, §5b. |

---

## 6a. Found at close-out: three scripts arrived without a smoke test

`CLAUDE.md`: *a defect found after close-out goes in the report, not just in the
fix.*

`tests/test_smoke.py::test_every_script_has_a_smoke_test` exists so that a new
script cannot arrive without one. **Three did** — `25_on_traffic.py`,
`26_scorefree.py` and `27_gate.py`, across Phases 4, 5 and 6. The guard caught
all three at once, which is the guard working and the author not reading it.

Each now has a smoke test that asserts the artifact is **internally consistent**
rather than that the script exited zero, because a stage that writes a plausible
file and exits cleanly is the failure the suite exists for. What each checks is
structural rather than numerical — notches equal `k + 1` exactly, a one-bit
detector has exactly one operating point, month one is never cheaper than steady
state, every rule-1 decision is identical with and without a detector.

**No figure from a scaled-down run is asserted as a value.** Two scripts gained
`--trials` and `--draws` so the smoke tests run in seconds, and the docstrings
say at the point of use that a number from three draws is noise —
`DECISIONS.md` 152a records a wrong conclusion reached from exactly that.

Two further defects surfaced in the same pass:

- **A shadowing bug**, introduced by the `--draws` change and caught on its
  first run: a local list named `draws` shadowed the new count parameter, so
  `range(draws)` received a list on the second iteration. Worth recording
  because the same shadowing in a function whose loop runs once would not have
  surfaced at all.
- **A stale assertion.** `test_smoke_feasibility` checked that the artifact's
  note said the price list was *"not built"*. It is built now, so the test was
  asserting the absence of work that had been done. Both it and the note now
  state what the artifact still does **not** derive — a money figure — which is
  the claim that is actually load-bearing.

---

## 7. Ledger

**Code** — `controlplane/gate/` (registry, session, gate, agent, cost),
`tests/test_gate.py` (16 tests), `scripts/27_gate.py`.

**Artifacts** — `results/gate/gate.json`, `results/gate/GATE.md`.

**Claim table** — seven rows added, 58/58 → 65/65.

**Decisions** — 156 (the rule as specified lets the attack through). Section 6a
carries three close-out defects with no entry of their own: a missing smoke
test, a shadowed parameter and a stale assertion are fixes rather than
methodological choices.

**Reproduce**

```
python -m pytest tests/test_gate.py -q
python scripts/27_gate.py --config config.yaml
python scripts/verify.py --claims-only
```

---

## 8. What this changes

**The product can now say what it does when its own detector is wrong.** That
was always the uncomfortable question: a company selling detector certification
is a company whose product is worthless if detectors are hopeless. The answer is
that the two decisions that matter most never consulted one, and there is a
number attached to that sentence.

**And the phase found its defect the only way that defect was findable.** No
test would have caught it, because the tests would have been written from the
same specification. It surfaced from building the attack and noticing that
removing a step made the defence vanish. That is the third time in three phases
that reading and building beat the suite — `DECISIONS.md` 147, 151, 153 and now
156 — and the pattern is stable enough to state as a finding rather than a
coincidence: **this repository's controls are excellent at catching a number
that is wrong and blind to a rule that is aimed at the wrong thing.**
