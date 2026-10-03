# DEMO_SCRIPT.md — the five-minute video

> **One rule.** The numbered beats read committed artifacts. The live loop
> generates an explicitly marked synthetic fixture. Neither is customer
> evidence. If a command fails on camera, say so.

**Five-minute target.** Rehearse the commands and narration together on the
recording machine; no duration has been established from word count alone.
The cut shows all nine artifact-backed beats and a synthetic live loop.

---

## Before you record

```bash
git status --porcelain          # empty
python scripts/verify.py --no-activations  # claims and frozen scores pass; activation tier SKIPPED
python -m pytest tests/ -q      # green
```

Terminal wide enough for the live loop, large font. `DECISIONS.md` open in a second tab.
Dry-run once.

---

## 0:00 – 0:30 — The claim

**Over a still terminal:**

> Round 1 built a detector. Round 2 asks what happens when an enterprise runs
> several AI use cases at once, each with a different risk signature.
>
> Our answer isn't a better detector. It's a **warrant** — a bounded statement
> about a detector on a declared set, or a refusal when the evidence cannot
> support it. This is research and local evaluation, not production traffic.

```bash
python scripts/verify.py --no-activations
```

> The claim table is checked against its artifacts; the frozen-score metrics
> are recomputed. This portable run explicitly **skips** the activation tier.
> The screen reports each count and status; a skipped tier is not a pass.

---

## 0:30 – 1:05 — BEAT 1: the refusal

```bash
python demo/show_beats.py --beat 1
```

> Customer support declares a false-positive ceiling of 2%. Certifying that at
> 95% confidence needs **149** clean held-out negatives — **203** across three
> profiles with the multiplicity correction. This example lacks them.
>
> It **refuses** and prints the evidence needed to lift the refusal. There is
> no override.

**Point at the note:** the counts are not inflated by an assumed correlation.

---

## 1:05 – 1:40 — BEATS 2–3: policy actions and measured access

```bash
python demo/show_beats.py --beat 2
```

> One input. One detector. **One score — 0.8446.**
>
> Customer support **allows**. The internal assistant **redacts**. Decision
> support **escalates** to a human.
>
> The detector didn't change. The policy did. And each row runs under a warrant
> certified at its **measured** operating point — not at the target it wants.
> That target is the one we just refused.

```bash
python demo/show_beats.py --beat 3
```

> This retained tier panel shows **T1 activation variants only**. It does not
> measure API-only access; T2 and T3 here are fixtures. We show the boundary
> rather than calling the missing tiers a result.

---

## 1:40 – 2:20 — BEAT 4: the overlap

```bash
python demo/show_beats.py --beat 4
```

> A fabricated detail about a person is simultaneously a hallucination and a
> privacy concern. Both labels live on the same items — correctness
> **measured**, identifier presence **authored** so nothing co-varies with it.
>
> Every recall here is **held-out**. Stock Presidio: **0.147**, refused.
> Recognisers enabled: 0.314, still refused. Our custom ones: **0.647**, passes.
> Our reference implementation: 0.833.
>
> Two of four **REFUSED** — the refusal is the system working. Most of those
> patterns were fitted on a different set, which is why you're looking at the
> held-out number.

---

## 2:20 – 3:05 — BEATS 5–6: drift and retained history

```bash
python demo/show_beats.py --beat 5
```

> This is a **historical research matrix**. The panel counts synthetic fixtures
> among its populated cells; a historical VALID is not automatically a current
> independent-unit certificate. **UNVALIDATED is the modal state** because most
> detector, operating-point and eval-set combinations were never tested.
>
> Input-distribution drift can be observed without labels; its trigger is a
> heuristic, not an error-rate guarantee. Label-driven chain revocation needs
> independently sampled negatives and a declared horizon.

```bash
python demo/show_beats.py --beat 6
```

> Each retained decision names its evidence and hashes its predecessor. The
> chain detects edits to retained history; a hash is not an authenticated
> signature or proof that no later record was withheld.

---

## 3:05 – 3:45 — BEATS 7–9: effort, tunability and the gate

```bash
python demo/show_beats.py --beat 7
python demo/show_beats.py --beat 8
python demo/show_beats.py --beat 9
```

> The review-effort estimate uses one **declared workload**, not production
> traffic. The score-free judge study is **simulated**; it certifies no real
> extractor. The action-gate result is an exact count over declared scenarios,
> not a claim of adversarial robustness. Those are the limits behind the
> three-clause pitch.

---

## 3:45 – 4:35 — The synthetic live loop

```bash
python demo/run_demo.py --fixture --events 4 --auto-prove
```

This command runs on a clean checkout. `--measured` is a separate optional
demonstration requiring ignored extraction caches and different narration.

> The banner says **SYNTHETIC FIXTURE**. It exercises the warrant display,
> recorded chain and five controls, including label shuffle. The displayed
> metrics are harness checks on generated data, not measurements of a customer
> workflow.

---

## 4:35 – 4:50 — What we got wrong

**Switch to `DECISIONS.md`.**

> A seed-sensitivity check once withdrew a flattering issuance result; an
> imported planning budget once changed a demo number. Both are preserved in
> `DECISIONS.md`. Plausible output is not enough without its exact source and
> scope.

---

## 4:50 – 5:00 — Close

> The goal is to measure a declared error rate, detect when its support changes,
> and price the evidence needed to maintain it. When evidence is insufficient,
> Warrant refuses. A customer pilot has not happened yet.

---

## Two answers to rehearse

**"Where's the feedback loop?"**

> Deliberately not built. Retraining only on reviewed flags creates selection
> bias and can worsen a detector. The override schema requires a recorded
> selection probability per item; the correction estimator remains unbuilt.
> No production feedback labels are being collected here.

**"22% recall is low."**

> Beat 2 shows one operating point near 22% recall for the declared
> customer-support profile and another near 74% for decision support. Different
> false-positive constraints lead to different trade-offs. On the retained
> evaluation set, the support row's recall lower bound clears its declared 10%
> floor; this is not customer traffic or a universal recall ceiling. A buyer
> may require a higher floor.

---

## Command reference

| beat | command |
|---|---|
| portable verification | `python scripts/verify.py --no-activations` |
| 1–9 | `python demo/show_beats.py --beat N` |
| all | `python demo/show_beats.py` |
| video live loop | `python demo/run_demo.py --fixture --events 4 --auto-prove` |
| optional measured loop | `python demo/run_demo.py --measured --events 4 --auto-prove` (requires ignored extraction caches; narrate measured provenance, not synthetic) |

**If a command fails on camera:** say what failed, run
`python demo/show_beats.py` (committed artifacts only), continue. A beat whose
artifact is missing prints *why* rather than rendering blank.
