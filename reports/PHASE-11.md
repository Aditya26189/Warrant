# Phase 11 — the final version, against the definition of done

**The question: does this repository meet `CLAUDE.md`'s definition of done and
`docs/TASKS.md`'s Phase 12 submission gate?**

**Answer: every item the repository can produce is now produced, verified from a
clean clone, and reported — and three things stand between it and a finished
submission that no amount of code closes.** There is no demo video, the
two-pane demo still runs on the synthetic fixture rather than the real caches,
and nine read-only estimators and four read-only defects wait on a human owner.
The one definition-of-done artifact that was missing at the start of this phase —
a drift and revocation trace — exists, was pre-registered, and passed its four
criteria while showing the unflattering outcome it predicted: **the system
detects the shift and then has nowhere to send the traffic.**

- **Window:** 2026-09-14
- **Range:** `2a6625b` → `HEAD`
- **Suite:** 1,345 → 1,359; green inside the clean clone at `359d276` (1,357 then), and re-run on this report's commit
- **Verification:** claim table 77/77 → **81/81**; frozen scores 25/25; activations 3/3
- **Clean clone:** **PASSED** at `359d276` — a fresh clone of 476 tracked files ran smoke, the full suite (972 s) and verify (81/81 claims, 25/25 frozen scores); the activations tier was skipped, as on every clone, because the caches are gitignored
- **Decisions:** `DECISIONS.md` 178, 179, 180; 177 corrected

---

## 1. The definition of done, item by item

| `CLAUDE.md` definition of done | state | evidence |
|---|---|---|
| `make verify` on a clean checkout, via `scripts/clean_clone_gate.py` | **passed** — smoke, full suite and verify inside a fresh clone | `results/clean_clone.json` |
| `RESULTS.md` — the warrant matrix | yes | 56 cells, 17 populated, precision beside recall |
| — the tier ladder | yes | `results/tier_ladder.json` |
| — **drift/revocation traces** | **yes, new** | `results/drift/revocation_trace.json`; §2 below |
| — the computed price list | yes | `results/on_traffic/on_traffic.json` |
| — κ | yes | the blinded-queue section |
| a populated `README.md` whose every number traces to `results/` | yes | 81/81 claim rows; prose checked against the table |
| passing suite, including the five controls and the estimator tests | yes | green in the clone; controls in `test_validation.py`, estimator coverage in `test_sampling.py` |
| two runs at one seed produce identical numbers | yes | chain rebuild: 3,075 fields, 0 moved; the demo run twice, identical numbers |
| clean tree, phase tags | yes, with a caveat | §4 |
| `DECISIONS.md` covering every methodological choice | yes | 180 entries; every citation resolves |
| a passing documentation audit | **five of six lines pass; one passes with a recorded read-only gap** | §3 |

---

## 2. The revocation trace — pre-registered, and the outcome was the one predicted

`DECISIONS.md` 178 registered the stream, four criteria and the expected routing
outcome **before the module existed**. The replay: the ledger's last-token
warrant on `triviaqa-600`, scored against the envelope stored in it, fed 400
held-out requests (median 42 tokens) and then 400 long-context requests (median
7,058), window 200, a verdict every 50.

| after request | window normal / shift | envelope | PSI | warrant |
|---|---|---|---|---|
| 200–400 | 200 / 0 | INSIDE | 0.011–0.054 | VALID |
| 450 | 150 / 50 | SIGNIFICANT_SHIFT | 0.353 | **REVOKED** |
| 500 | 100 / 100 | SIGNIFICANT_SHIFT | 1.064 | REVOKED |

The simulated null for this envelope puts p95 at 0.072 and the false-alarm rate
at 0.01.

| criterion, registered before the run | result |
|---|---|
| no false alarm on all-normal windows | PASS |
| revoked within one window of the shift | PASS — at the first checkpoint after onset |
| routing consults the live envelope, not the revoked one | PASS |
| each certificate names both envelopes and lists MMD as unchecked | PASS |

**Then nothing could be served.** On `triviaqa-longctx-600` the one detector
holding VALID is last-token, with a recall lower bound of 0.0903, under every
profile's minimum; mean-pool and max-rolling-means are REFUSED there. All three
profiles suspend and escalate, and every certificate claims **no bounds** rather
than its last good numbers. 178 wrote that outcome down before the run. It is the
correct behaviour and the product's real limit on this envelope, and the demo now
shows it (beat 5).

**What it is not:** production traffic; a gradual shift; a shift in anything
but length. The checkpoint granularity is 50 requests, so "within one window" is
the claim, not "after exactly 50".

**Found building it** (`DECISIONS.md` 179, OPEN): `DriftResponse.to_payload`
in read-only `drift/response.py` calls a method `RoutingDecision` does not have,
so any routed response raises on serialisation. Nothing had ever serialised
one. Worked around; pinned by a strict expected failure that breaks when fixed.

---

## 3. The documentation audit, line by line

**1. Every invariant enforced somewhere in code — file and line.**

| # | invariant | enforced in code | held by |
|---|---|---|---|
| 1 | keyed by (detector, operating point, eval set) | `model/warrant.py:283` `Warrant.key` | `test_model.py:87`, `test_compose.py:60` |
| 2 | three states, three behaviours | `model/warrant.py:272` refuses a record carrying UNVALIDATED | `test_compose.py:272`, `test_model.py:261`, `test_drift_response.py:174` |
| 3 | refusal has no override | `validation/issuance.py:101` takes no relaxing argument; `model/warrant.py:199` a failed control forces REFUSED | `test_validation.py:115`, `test_demo.py:240` |
| 4 | no point estimate reaches a user | `model/metrics.py:148` ESTIMATED requires an interval | `test_claims.py:93`, `test_demo.py:160` |
| 5 | precision and recall travel together | `model/metrics.py:42` blended names refused; `matrix/matrix.py` cell renders P beside R | `test_model.py:175`, `test_fpr_sweep.py:233`, `test_claims.py:216`, `test_matrix.py:398` |
| 6 | one declared workload | `economics/sizing.py:430` `workload_price_list` reads the one block | `test_sampling.py:324`, `test_economics.py:250` |
| 7 | reviewers are blind | `sampling/queue.py:55` `WITHHELD_FIELDS` | `test_sampling.py:204`, `test_sampling.py:286` |
| 8 | every number computed by code | `report/claims.py` `check_claims`; `scripts/verify.py` | `test_claims.py:36`, `test_readme_prose_numbers.py:131` |
| 9 | eval sets frozen and content-hashed | `validation/evalsets.py:154` `content_hash`; `evalsets/registry.py:82` refuses a changed file | `test_policy.py:237`, `test_construction_identity.py:128` |

**Pass.** `tests/test_invariants.py` fails if any named test disappears.

**2. Every `SPEC.md` section matches shipped behaviour; flag drift.** **Pass as
reconciled.** All eleven sections walked (Phases 9 and 10); every divergence is
annotated in the spec with its entry, and the ones that remain are features the
spec describes and the code does not have — four drift features, MMD,
background revalidation, weight-driven thresholds, on-traffic FPR — each stated
in `docs/LIMITATIONS.md` §3.4.

**3. Every number in `README.md` traces to `results/`.** **Pass.** 81/81 claim
rows re-derived by `scripts/verify.py`; `tests/test_readme_prose_numbers.py`
holds the prose to the table.

**4. Every statistical claim states the quantity and the propagation.** **Pass
with a recorded gap.** 17 registered functions carry both lines and a test
keeps them there. **Nine read-only functions do not**, including `min_n_for`,
which this phase's re-scan found missing from the register (`DECISIONS.md` 180).
They are listed by name and cannot be fixed under the read-only rule.

**5. Every `DECISIONS.md` entry still accurate; entries for decisions taken during
the build.** **Pass.** Every citation resolves. This phase added three entries
and corrected one of its own (177 said no line-ending guidance existed;
`CONTRIBUTING.md` had it).

**6. No TODO or placeholder text in any committed document.** **Pass.** The only
hits are the three documents that state this rule.

---

## 4. The history review

- **Legibility:** conventional commits throughout; since `report-9`, 20 commits
  — 8 docs, 4 exp, 3 feat, 3 fix, 2 test. Every `exp:` commit states what it
  regenerated and how many numeric fields moved (0 in each).
- **Phase tags: not twelve of one scheme.** TASKS asks for twelve phase tags.
  The tree has `phase-0` to `phase-8.1`, `stage-*`, and `report-4` to
  `report-11` — three schemes that grew as the plan did. Nothing is missing, but
  it does not read as twelve.
- **Line endings:** 13 files rewrote CRLF to LF in six commits before it was
  noticed (`DECISIONS.md` 177). `git show -w` recovers the real change.
- **Not pushed.** Local `main` is 55 commits ahead of `origin/main`.

---

## 5. What this does not establish

- **Nothing here is production evidence.** Every measurement is TriviaQA, a
  hand-built Hinglish PII set, or a replay of those. `LIMITATIONS.md` §1.
- **The revocation trace is one shift, in one feature, as a hard cut.**
- **The demo's two-pane runner was fixture-only when this report was written.**
  Closed the same day; see §9. A clean clone still has no caches, so there it
  runs `--fixture` or refuses.
- **A passing audit is a statement about what the checks look for.** 165's
  lesson holds: each check is a claim about a pattern.

---

## 6. Open items

| # | item | what would close it |
|---|---|---|
| O-1 | **Demo video** | a human recording `demo/show_beats.py` and the two-pane runner |
| O-2 | two-pane demo on the real caches — **closed after this report**, §9 | — |
| O-3 | read-only defects: `DriftResponse.to_payload` (179); the ladder's "revalidation is scheduled" (172); the DPDP attribution in `store/ledger.py` and `drift/certify.py` (168); `Metric.n` on rates (169) | an owner for `drift/`, `store/`, `validation/stats.py` |
| O-4 | nine read-only functions without derivations | the same owner |
| O-5 | lift's upper bound exceeds the physical ceiling | a pre-registered decision on a joint interval |
| O-6 | four drift features and MMD | build them, or remove them from `config.yaml` |
| O-7 | carried: customer conversations; a real LLM judge; `DECISIONS.md` 145's Linux Rego abort; rule 1 duplicated in gate and Rego | see `reports/PHASE-10.md` §7 |
| O-8 | 55 commits not on `origin/main` | a push, when the owner decides |

---

## 7. Ledger

**Code** — `controlplane/demo/revocation_trace.py`, `scripts/28_revocation_trace.py`;
`controlplane/report/spec_sections.py` (§11.6 renders the trace);
`controlplane/report/beats.py` (beat 5); `controlplane/report/invariants.py`
(`min_n_for`).

**Artifacts** — `results/drift/revocation_trace.json`; `results/RESULTS.md`
re-rendered; `results/clean_clone.json`.

**Tests** — `tests/test_revocation_trace.py` (including the strict xfail for 179),
`test_spec_section_11.py` (§11.6 now requires the trace),
`test_demo_beats.py::test_the_drift_beat_shows_a_revocation_fire`.

**Decisions** — 178 (pre-registration), 179 (the serialisation defect), 180 (the
register gap); 177 corrected.

**Reproduce**

```
python scripts/clean_clone_gate.py                 # the Phase 12 gate
python -m pytest tests/ -q
python scripts/verify.py
python scripts/28_revocation_trace.py --config config.yaml   # needs the caches and a ledger under 24h old
python demo/show_beats.py
```

---

## 8. What this changes

**The middle clause of the pitch — *when that number stops being true* — now has
a measured instance.** Before this phase the repository could say how a warrant
would be revoked and point at tests. Now it can show one being revoked on real
token lengths, by the shipped code, against criteria written down first.

**And what it shows is not a clean win.** The system caught the shift at the
first checkpoint, stopped quoting the lost bounds, and then had no warrant that
met any profile on the new envelope. A version of this product built to look good
would have routed somewhere. This one escalates and says why, which is the
behaviour a model-validation function should want to buy — and the trace is
evidence that it exists, not a promise that it would.

---

## 9. Closed after this report

`CLAUDE.md`: a change after close-out goes in the report, not only in the fix.

**O-2 — the two-pane demo runs on the measured caches** (`DECISIONS.md` 181,
merged in `53608e4`). `demo/run_demo.py` refused anything but `--fixture` with a
message saying no real extraction existed, which had been false since 051–052.
It now takes `--measured` or `--fixture`, mutually exclusive and one required,
because 027's rule — no default that swaps one data source for the other — was
the point and the missing extraction never was.

**Phase 10's gate, on real data:** `python demo/run_demo.py --measured --events 6
--auto-prove`, twice, unattended, exit 0 both times. The two runs differ only in
warrant age, certificate chain hashes and validation wall time (18.6 s and
25.6 s). The banner shows the last-token
warrant on `triviaqa-600` — AUROC 0.826, recall 0.079 [0.050, 0.112], precision
0.880 [0.750, 1.000], yield 22 of 25 — the same figures as the claim table,
because it validates the same cache through the same code.

`docs/DEMO_SCRIPT.md`'s live loop now names `--measured`. Tests 1,359 → 1,361.
