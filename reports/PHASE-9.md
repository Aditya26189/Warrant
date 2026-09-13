# Phase 9 — the documentation audit, made checkable

**The question: does this repository pass the Phase 12 documentation audit its
own task list sets?**

**Answer: it did not, on four of six lines, and it now does on five.** The audit
had never been run. Each line asserted a property of the codebase — *every
invariant enforced*, *every statistical claim derived*, *every entry still
accurate* — and nothing checked any of them. Run for the first time:

| audit line | before | after |
|---|---|---|
| every invariant enforced somewhere in code | unchecked | **9 of 9**, each naming its test |
| every `SPEC.md` section matches shipped behaviour | unchecked | **§11: 6 of 12 → 12 of 12**; two divergences recorded, not reconciled |
| every number in `README.md` traces to `results/` | table checked, prose not | table and prose |
| every statistical claim states its derivation | unchecked | **8 of 32 → 18 of 32**, 8 read-only OPEN |
| every `DECISIONS.md` entry still accurate | unchecked | 375 citations resolve; **2 stale entries found** |
| no TODO or placeholder text | unchecked | clean |

**The one that is not done is the `SPEC.md` reconciliation**, and that is stated
in §5 rather than folded into a pass.

- **Window:** 2026-09-12 to 2026-09-13
- **Range:** `09ac28b` → `HEAD`
- **Suite:** 1,241 → 1,315
- **Verification:** claim table 66/66
- **Decisions:** `DECISIONS.md` 162, 163, 164, 165

---

## 1. Invariants — mentioned is not enforced

All nine `CLAUDE.md` invariants were **mentioned** in tests: a grep finds 106
references. Nothing checked that an enforcing test still existed, still ran under
that name, or that a tenth invariant would arrive with any enforcement at all.

`controlplane/report/invariants.py` names, per invariant, the specific tests that
fail if it stops being true, and a `breaks_as` clause describing the world in
which it is unenforced. The register parses `CLAUDE.md` so an invariant added to
the contract without an entry fails, and checks every named test still exists.

**Verified by breaking it.** Renaming `test_no_override` in the register produces
*"invariant 3 (Refusal has no override) names enforcing test(s) that do not
exist ... in which case the invariant is now unenforced."*

**What it does not do**: check that a named test genuinely enforces its
invariant. That needs mutation testing. It makes the *absence* of enforcement
loud, which is the failure this repository has actually had.

**The first version hung.** It called `pytest --collect-only` at module scope,
which collects `tests/`, which imports the module, which spawns another pytest —
unbounded recursion. It did not fail; it hung, which is worse, because a failure
names itself. Replaced with `ast` parsing. `DECISIONS.md` 162.

---

## 2. Statistical claims — 8 of 32

`CLAUDE.md`: *a sample size, interval or projection states the quantity being
estimated and the propagation used.*

**32 public functions return an interval, a bound or a sample size. Eight stated
their derivation.** Of the 24 that did not, eight are in read-only zones and six
are not statistical claims at all — excluded **by name**, not by tightening a
filter, so the exclusion is reviewable. That left ten.

**One of the ten was mine from this session** —
`scorefree.smallest_certifiable_budget`, written three phases after I started
citing this rule at other code. The convention is easy to follow when writing the
estimator and easy to forget when writing the helper beside it.

Several were worth writing for their own sake. `abstention_floor` has **no**
propagation: it is an impossibility result, and attaching an interval would imply
a sampling step that does not exist. For `paired_bootstrap`, the pairing *is* the
propagation.

**The eight read-only functions include four in `stats.py` and
`warrant_stats.certify_fpr`** — the most-used estimators here — so the coverage
figure understates the gap where it matters most. Listed, not touched.
`DECISIONS.md` 163.

---

## 3. `RESULTS.md` against `SPEC.md` §11 — six of twelve

§11 is titled *"What `results/RESULTS.md` must contain"* and lists twelve items.
**Six were present, three of those added four days earlier.** Before that, three
of twelve, in the document the definition of done names first.

**Every absent item already had a committed artifact.** Nothing was missing
except the rendering: the evidence was gathered, committed and verified, and the
document built to present it did not mention it.

Now twelve of twelve, parsed from `SPEC.md` so a thirteenth requirement fails
until rendered. **Item 6 is rendered narrower than asked, and says so on the
page**: the 21 routing decisions exist, a live revocation trace does not, and the
section is titled *"Routing, and the revocation trace that is missing"*.
`DECISIONS.md` 164.

---

## 4. `DECISIONS.md` — 375 citations, and two stale entries

**375 citations** across code, tests, config, policy bundles, artifacts and the
notebook. Every one resolves.

**The check was wrong three times before it was right.** First it found 94
entries instead of 165 and reported 46 files as carrying broken citations — the
heading format changes at entry 072 from an em dash to a hyphen, and the regex
knew one form. **All 46 were fine.** Then it flagged two closures as open by
matching the word "OPEN" in a sentence. Then a partial fix handled the word order
in one entry but not another. The rule that works reads the status as a field.

**And it found two real defects.** Entry 155 said its OPEN item was open when 157
had closed it the same day. Entry 157 said the run order was open when 158 had
closed the case that bit. Neither is findable by reading forward: both are
back-references nobody wrote, because the closing entry never went back.

155's closure note records that its reasoning was half wrong — it concluded the
rebuild needed a GPU, when the GPU stage's output was already on disk — and leaves
the wrong reason standing. `DECISIONS.md` 165.

---

## 5. What this does not establish

- **`SPEC.md` is not reconciled.** Two shipped behaviours diverge from it:
  §6.2's closed-form sample size under-delivers its margin (`DECISIONS.md` 149)
  and §9.3's Rule-of-Two lets the canonical injection through (156). Both
  divergences are recorded and the shipped code is right. **The spec still says
  the wrong thing**, and the audit line *"every SPEC section matches shipped
  behaviour"* is therefore not passed. This phase audited §11 and did not walk
  the other ten sections.
- **None of these checks verify quality.** A test that exists is not a test that
  enforces. A derivation that is stated is not a derivation that is right. A
  citation that resolves is not a citation that supports its claim.
- **The read-only gaps are unfixed.** Eight estimators without derivations, in
  code this build may not change.
- **`DECISIONS.md` accuracy was sampled, not audited.** Two stale entries were
  found by one mechanism. There will be others of kinds that mechanism cannot see.

---

## 6. Open items

| # | item | what would close it |
|---|---|---|
| O-1 | **Walk the remaining ten `SPEC.md` sections** against shipped behaviour, and reconcile §6.2 and §9.3. | A section-by-section pass, same shape as §11's. |
| O-2 | Eight read-only estimators lack a stated derivation. | An owner for `validation/stats.py`, `warrant_stats.py` and `drift/`. |
| O-3 | Revocation trace for `RESULTS.md` §11.6 — no drift run has revoked a warrant. | Point the drift machinery at a moving distribution with a warrant outstanding. |
| O-4 | Carried: the twelve conversations; certifying a real judge; `DECISIONS.md` 145's Linux abort; rule 1 duplicated between the gate and the Rego bundles. | See `reports/PHASE-8.md` §5. |

---

## 7. Ledger

**Code** — `controlplane/report/invariants.py`,
`controlplane/report/spec_sections.py`; `Quantity:`/`Propagation:` added to ten
functions across `economics/`, `intake/`, `validation/`.

**Tests** — `tests/test_invariants.py`, `tests/test_spec_section_11.py`,
`tests/test_decisions_integrity.py`.

**Artifacts** — `results/RESULTS.md` regenerated on a clean tree, 7 sections to 13.

**Decisions** — 162 (invariants), 163 (derivations), 164 (§11), 165 (citations
and stale entries). 155 and 157 amended with closure notes.

**Reproduce**

```
python -m pytest tests/test_invariants.py tests/test_spec_section_11.py tests/test_decisions_integrity.py -q
python scripts/03_matrix.py --config config.yaml
```

---

## 8. What this changes

**The audit is now a test suite rather than a checklist.** A checklist is run once
and asserts a state; these fail when the state changes. That matters for this
repository specifically, because every defect this session found was a property
that had been true once, been asserted, and silently stopped being true.

**And for the fifth time, the checks were more wrong than the thing they checked.**
The citation scan reported 46 broken files that were fine. The OPEN scan flagged
closures. The §11 test looked for words the document correctly did not use. In
every case the repository was right and the first version of the check was not,
and in every case the fix was to read the artifact rather than to trust the
pattern. **A check written from memory of a document is a second, unverified
claim about it.**
