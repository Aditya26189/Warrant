# Phase 8 — what the product says about itself

**The question: does the outward-facing material claim what the evidence
supports — no more, and no less?**

**Answer: no, and it was wrong in both directions at once.** The demo closed on
a three-clause pitch and demonstrated one clause. The single external claim the
gate's whole design rests on was quoted in six files and cited in none. And the
table asserting that this work answers the Round 2 brief was written from memory
and missed the one complexity the repository had no answer to.

None of these is a wrong number. All three are the same failure the previous
four phases found: **a claim whose evidence nobody checked, in a document
written by people who could have checked it.**

- **Window:** 2026-09-11
- **Range:** `09e3e5b` → `HEAD`
- **Suite:** 1,235 → 1,239, green at both
- **Verification:** claim table 66/66
- **Decisions:** `DECISIONS.md` 159, 160, 161
- **Method:** CPU only; two primary sources fetched

---

## 1. The demo demonstrated one clause of three

`docs/DEMO.md` closes on this project's entire proposition:

> *"We tell you what your error rate is on your traffic. We tell you when that
> number stops being true. And we tell you what it costs to keep it true."*

**All six beats were the middle clause.** Refusal, profiles, the tier ladder,
the overlap pilot, drift and revocation, the audit chain — every one is about a
warrant's lifetime. Nothing showed what an error rate on *your* traffic costs to
establish, because until `DECISIONS.md` 147 and 146 neither the estimator nor
the price list existed.

That was defensible while the code did not exist. **The closing line was making
a claim the demonstration did not support** — which is the failure this entire
product is built to prevent, arriving through the deck.

Three beats, each rendering its numbers from the artifact it cites:

| beat | shows | artifact |
|---|---|---|
| 7 | the on-traffic warrant and the price list | `results/on_traffic/` |
| 8 | tunability: a detector that cannot be moved to your budget at all | `results/scorefree/` |
| 9 | the action gate, whose two most important rules read no detector | `results/gate/` |

**Each carries its caveat on screen, not in a footnote.** Beat 7 says no
production traffic exists here. Beat 8 says the judge is simulated and every
figure is an upper bound. Beat 9 says, in the beat, that this is **not** a
robustness claim. A demo is where a caveat is most likely to be dropped and most
expensive to have dropped.

`test_all_six_beats_assemble` became `test_all_nine_beats_assemble` and gained
`test_the_three_clauses_each_have_a_beat`, so a future clause with no
demonstration behind it fails rather than being noticed on camera.

---

## 2. The claim the gate rests on had no citation anywhere

> *published work broke twelve injection defences at >90% attack success*

That sentence is the **only** external evidence behind the gate's design.
Everything about rules 1 and 2 follows from it: that they read no detector, that
this is worth building, that a vendor claiming robustness is claiming to be the
exception. It appeared in `SPEC.md`, three gate modules, the demo and the README
— **six files, no citation in any of them.**

`reports/STRATEGY-2026-09.md` §4 exists for exactly this. It is the most
convenient claim available, and it had the weakest possible backing.

**Checked. It holds, with one word wrong.** Nasr, Carlini, Sitawarin, Tramèr and
ten others, *The Attacker Moves Second*,
[arXiv:2510.09023](https://arxiv.org/abs/2510.09023), 10 October 2025:

> *"we bypass 12 recent defenses (based on a diverse set of techniques) with
> attack success rate above 90% for most; importantly, the majority of defenses
> originally reported near-zero attack success rates."*

Twelve is right. Above 90% is right. **"At >90%" is not** — the paper says
*for most*, not for all. Corrected in all six, and the *"majority originally
reported near-zero"* half added, because that is the part that makes the point:
these were not weak defences, they were defences their own authors had measured
as working.

### The Rule-of-Two source settles `DECISIONS.md` 156, by a route not taken

Meta's *Agents Rule of Two* (31 October 2025):

> within a single session an agent should satisfy no more than two of three
> properties: it **can** process untrustworthy input, it **can** access
> sensitive systems, it **can** change state or communicate externally — and one
> requiring all three **without starting a new session** should not operate
> autonomously.

**That is a statement about what the agent *can do*.** `SPEC.md` §9.2
transcribed it as what a session *has done*, and `DECISIONS.md` 156 recorded
that the transcription loses exactly one case — the one where the action being
decided *is* the third capability.

**The primary source settles it in 156's favour, and it was not consulted when
156 was written.** That correction came from building the attack and watching it
pass. The agreement is worth recording precisely because it was not the route
taken. The source also names the remedy the implementation already had:
*without starting a new session* is `Session.successor`.

A test now asserts the arXiv id is present in the README, so the claim cannot
lose its source to an edit that tidies the sentence.

---

## 3. The map of the brief was incomplete, in the one place that mattered

`controlplane/report/beats.py` opens with a table mapping the Round 2 problem
statement to the beats, and it has been quoted as evidence the submission
answers the question asked. **It was written from memory.**

Read against the document in the repository root: **the brief lists six
real-world complexities and the table mapped five.** The one it did not:

> *"Multi-turn conversations and AI agents that take actions (not just generate
> text) introduce compounding risk, where one questionable output can shape
> several downstream decisions."*

**That complexity had no beat at all**, and it is the only one the repository
had no answer to. Beats 1 to 6 are entirely about text. The gate is the answer
and did not exist.

Two solutioning areas were also unmapped, and the other two new beats land on
them:

| brief, quoted | beat |
|---|---|
| *"Metrics & monitoring — how you would define, measure, and report false positive/negative rates and overall system trustworthiness to a skeptical stakeholder"* | 7 |
| *"Detection techniques — ... a secondary 'AI-as-judge' pattern"* | 8 |

**Beat 8 and the brief's interest in it were found independently.** The
score-free work was motivated by `docs/REDACT.md` §5, not by re-reading the
problem statement. Two routes to the same gap is worth more than either.

**Three reference parameters line up and were not chosen to.** The brief names
*"a customer support assistant, an internal knowledge assistant, and a
decision-support tool"* — the three `config.yaml` profiles by name — and *"tens
of thousands of interactions per week"*, which the declared 200,000 a month is
(46,154). Both predate this reading.

---

## 4. What this does not establish

- **The mapping is a claim about coverage, not quality.** Having a beat for a
  complexity is not evidence of answering it well.
- **Nothing here was measured.** This phase fetched two papers, read a PDF, and
  fixed three documents. No number in `results/` moved and none should have.
- **The brief's other three tracks are unread.** Only Track 1 was checked, which
  is the track this project is on.
- **Beat 9's complexity is addressed, not solved.** An agent taking actions is
  a large problem; the gate answers one part of it — irreversible actions under
  a compromised session — and `reports/PHASE-6.md` §5 lists what it does not
  defend against.

---

## 5. Open items

Unchanged from `reports/PHASE-7.md` §6, minus nothing: the twelve conversations;
certifying a real judge; `DECISIONS.md` 145's Linux abort; rule 1 duplicated
between the gate and the Rego bundles; the chain dirtying its own tree; the run
order enforced only for the matrix artifact.

---

## 6. Ledger

**Code** — three beats in `controlplane/report/beats.py`; citations in
`docs/SPEC.md`, `controlplane/gate/{gate,session,agent}.py`,
`controlplane/report/beats.py` and `README.md`.

**Tests** — `test_all_nine_beats_assemble`,
`test_the_three_clauses_each_have_a_beat`, and
`test_the_section_makes_no_robustness_claim` extended to require the citation.

**Decisions** — 159 (the demo showed one clause of three), 160 (the claim had no
citation), 161 (the brief's map was incomplete).

**Reproduce**

```
python demo/show_beats.py
python -m pytest tests/test_demo_beats.py tests/test_readme_prose_numbers.py -q
```

---

## 7. What this changes

**Every outward-facing claim in this repository now points at something a
reader can open.** The numbers already did — that is what the claim table has
always been. What did not was the prose: the pitch, the citation, the map of the
brief. Those are the parts a judge reads first and the parts no control looked
at.

**And the count is now seven.** `DECISIONS.md` 147, 151, 153, 156, 157, 158 and
now 159–161. Across five phases, **not one finding has been a number computed
incorrectly.** Every single one has been a control aimed at the wrong thing, a
claim nobody traced, or a map nobody checked against the territory.

That is the most useful thing this project has learned about itself, and it is
worth more than any individual fix in the list: **a repository can be
arithmetically impeccable and still say things it has not earned.** The claim
table catches one of those. Nothing catches the other, and knowing which is
which is the whole job.
