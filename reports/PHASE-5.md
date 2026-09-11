# Phase 5 — certifying a detector that emits no score

**The question: can this method certify the detectors that actually win?**

**Answer: not yet for a real one, and the measurement says why in a way the
registration did not expect.** Repeated sampling turns a score-free judge into
something rankable, and what that buys is now priced. The headline is that
**a single-sample judge cannot be certified to a tight false-positive budget
however much data you have** — at `k = 1` the tightest reachable budget is the
judge's own error rate, 0.105 here, against a data floor of 0.00015 at 20,000
negatives. One bit gives one cut point. There is no dial.

The fix is cheap and it stops: five to ten samples buys everything `k` can buy,
and past that more samples are inference spend fixing a data problem.

**This certifies no real detector.** The judge is simulated. That limit is §5 and
it is the first thing a reviewer should attack.

- **Window:** 2026-09-11
- **Range:** `047fa4e` → `HEAD`
- **Suite:** 1,168 at open → 1,181 at close, no failures at either end
- **Verification:** claim table 49/49 at open → **58/58** at close
- **Artifacts:** [`results/scorefree/`](../results/scorefree/)
- **Decisions:** `DECISIONS.md` 152 (registered before the code), 152a (results)
- **Method:** CPU only, offline, no paid key

---

## 1. What was done

`docs/REDACT.md` §5 states the limit in a table this phase did not change:

| detector family | score | certifiable |
|---|---|---|
| fine-tuned classifiers, probes | continuous | yes |
| GLiNER, OpenAI Privacy Filter | continuous | yes |
| Presidio | 8 discrete values | technically, 1–3 operating points |
| **GPT-4.1, Claude Sonnet** | **none** | **no** |

REDACT's own results put the LLM extractors well ahead, so the method cannot
certify the family that performs best. `reports/AUDIT-2026-09-09.md` calls this
*"the largest genuine limitation in the method itself"*.

Built: `controlplane/validation/scorefree.py`, `tests/test_scorefree.py` (10
tests), `scripts/26_scorefree.py`. Four claims were registered in
`DECISIONS.md` 152 with their falsifiers **before any code was written**.

---

## 2. What was found

### The two floors, and which one binds

Tightest false-positive budget a *useful* threshold reaches — median over 40
vote draws, range in the artifact. **Bold** where granularity is what binds:

| negatives | data floor | k=1 | k=2 | k=3 | k=5 | k=9 |
|---|---|---|---|---|---|---|
| 200 | 0.01487 | **0.13628** | **0.03831** | **0.01918** | 0.01487 | 0.01487 |
| 1,000 | 0.00299 | **0.11058** | **0.02180** | **0.00913** | 0.00299 | 0.00299 |
| 5,000 | 0.00060 | **0.09848** | **0.01684** | **0.00462** | **0.00095** | 0.00060 |
| 20,000 | 0.00015 | **0.09424** | **0.01516** | **0.00364** | **0.00046** | 0.00015 |

Two constraints, binding in turn:

- **Granularity**, below the crossover. `k` notches land on at most `k + 1`
  false-positive rates.
- **The benchmark's own certification capacity**, above it. `cp_upper(0, n, α)`
  is positive, so no threshold reaches below it at any `k`.

The second is the finding `docs/REDACT.md` §1 already made about REDACT's locked
split, arriving one level down. **Spending on `k` past the crossover is buying
inference to fix a data problem.**

| negatives | data floor | crossover `k` (median, range) |
|---|---|---|
| 200 | 0.01487 | **3** [3, 5] |
| 1,000 | 0.00299 | **5** [3, 7] |
| 5,000 | 0.00060 | **6** [4, 9] |
| 20,000 | 0.00015 | **7** [5, 10] |

### Notches are not operating points

| k | notches | distinct scores | operating points | budgets reachable |
|---|---|---|---|---|
| 1 | 2 | 2 | **1** | 3/12 |
| 3 | 4 | 4 | **3** | 8/12 |
| 9 | 10 | 10 | **5** | 10/12 |
| 50 | 51 | 49 | **10** | 10/12 |

Fifty-one notches buy ten operating points. This is `DECISIONS.md` 141's finding
about Presidio's rule-fired confidence reached from the other direction, and
`tunability()` is written against any score vector rather than only consensus
scores — because that question had been observed for Presidio, written up, and
never implemented.

### `k` is part of the operating point

Certify at `k = 9`: threshold 0.4444, certified upper bound **0.0336**. Apply the
identical vote-fraction threshold at `k = 1`: realised false-positive rate
**0.0790**, **2.35×** the bound. The warrant is void.

So `k` enters the warrant key through `detector_id` (`judge-sim@k=9`). That is
the minimal change: `OperatingPoint` is referenced by the store, the matrix, the
policy bundles and every committed artifact, and a schema field there to express
what `detector_id` already expresses is the larger change. **Open** if a second
dimension of this kind ever appears.

### What finite `k` costs in ranking

AUROC gap to the latent-probability ceiling of 0.9972: **0.2288** at `k = 1`,
0.0215 at `k = 9`, **0.0021** at `k = 50` — against the 0.02 bar registered
before the run.

---

## 3. The claim that failed, and why both reasons are mine

C3 was registered as *"find a budget no `m` certifies at `k = 3` and some `m`
certifies at `k = 25`"*. **The first run found none.** Reporting that as a clean
falsification would have been wrong twice.

**A defect in my own `smallest_certifiable_budget`.** Its candidate thresholds
included a cut point above every score. That threshold flags no negative, so the
function returned the data's floor at every `k`, making granularity appear never
to bind. It was a true number attached to an operating point reached only by a
detector that never fires — the same shape as `DECISIONS.md` 147's defect one
step along: there the number was in the wrong units, here it was for a useless
operating point. Positives are now required and
`test_a_threshold_that_flags_nothing_does_not_count_as_capacity` keeps it out.

**And I read a single vote draw.** On the seed the falsifier used, `k = 3`
reached 0.005; on another it reaches only 0.02 while `k = 25` reaches 0.005.
Both are legitimate draws. **A one-draw test of a quantity with this spread is
not a falsifier, it is a coin.** Every floor in the artifact is now a median over
40 draws with its range printed beside it.

Over draws, C3 holds. The honest statement is that it holds and that its first
test could not have told me so.

**The correction to the mental model is the part worth keeping.** The
registration assumed granularity was *the* constraint. It is one of two, and it
is not the one that binds where a serious benchmark operates.

---

## 4. What this does not establish

- **It certifies no real detector.** `docs/REDACT.md` §5's table is unchanged for
  GPT-4.1 and Claude.
- **The judge is simulated**, with `k` *independent* Bernoulli draws from a
  latent per-item probability. A real judge's runs share a prompt, a system
  message and a temperature, and are **correlated** — which makes the vote
  fraction a worse estimate, pushes the crossover up, and makes **every figure
  here an upper bound on what `k` buys**.
- **The 0.105 single-sample floor is this judge's error rate**, not a universal
  constant. What generalises is the structure: at `k = 1` the only certifiable
  budget is whatever the detector already does.
- **No inference cost in currency.** That is a provider price list, not a
  measurement.
- **Nothing here says an LLM judge is worth certifying.** It says what it would
  cost.

---

## 5. Open items

| # | item | what would close it |
|---|---|---|
| O-1 | **Certify a real judge.** The whole point. Needs a paid key and a budget; `DECISIONS.md` 136 refused to write a logprob finding from memory and the same rule applies here. | A key, a few hundred dollars, and REDACT's locked split. |
| O-2 | **Measure the correlation between a real judge's repeated samples.** It is the single assumption every figure here rests on, and it is the one that makes them optimistic. | The same run as O-1. |
| O-3 | **`k` in `OperatingPoint` rather than packed into `detector_id`.** Deliberately deferred as the change that claims less. | A second dimension of the same kind appearing. |
| O-4 | Carried from Phase 4, unchanged: the twelve conversations; `DECISIONS.md` 145's Linux abort; `scripts/11_feasibility.py` still publishing the superseded sizing; `gate/` unbuilt; `DECISIONS.md` 138 open for four phases. | See `reports/PHASE-4.md` §7. |

---

## 5a. Found after Phase 4 closed, and reported here rather than only fixed

`CLAUDE.md`: *a defect found after close-out goes in the report, not just in the
fix — including the ones found by rereading rather than by a failing test.*

**Two artifacts priced labels for the same profile and disagreed.**
`results/feasibility.json` said 1,808 for `customer_support` at ±0.05 month one;
`results/on_traffic/on_traffic.json`, written three hours earlier in Phase 4,
said **1,189**. One script read `policy-triviaqa-2400-t960.json` (recall 0.2171
at n=960) and the other `policy-triviaqa-600.json` (recall 0.1661 at n=600).
Two eval sets, one profile name, and neither artifact recorded which measurement
it came from.

**No control could see it.** Every check in this repository asks whether a number
is reproducible from its own inputs, and both were, to the last digit. Nothing
asked whether two artifacts describing the same thing agree. It is the shape of
`DECISIONS.md` 142 one level up: **computing a number correctly twice is not
computing it consistently.**

A second instance appeared on fixing the first — steady state still differed,
1,212 against 1,434, because one script used `config.yaml`'s declared design
effect and the other the measured one.

Fixed by one source and one owner per number, with
`test_the_two_artifacts_agree_on_one_profile_label_budget` comparing every
shared profile-margin pair and asserting that at least six were actually
compared. `DECISIONS.md` 153.

**The Phase 4 figure that moves:** `customer_support` at ±0.05 month one,
1,189 → 1,808. That is a correction toward the operating point the README claim
table has always led with, not a new measurement. `reports/PHASE-4.md` §4 quotes
the superseded value and carries a pointer here.

**The pattern across the two phases is now hard to miss.** Three defects —
`DECISIONS.md` 147, 151 and 153 — were invisible to a suite of eleven hundred
tests, and they share one shape: **a control exists wherever a number might be
arithmetically wrong, and nowhere else.** Wrong units, a missing deliverable,
and two right numbers that disagree all sit outside that.

---

## 5b. The definition of done, and a script that cannot run here

**`RESULTS.md` was missing two things the contract names.** `CLAUDE.md`'s
definition of done asks it for *"the warrant matrix, the tier ladder,
drift/revocation traces, **the computed price list**, and **κ**"*. The last two
were absent because neither existed. `controlplane/report/price_list.py` now
renders three sections into it — the price list with `dR/dq` and both regimes, κ
with the blinded-queue note, and what it costs to certify a score-free detector.

**A section whose artifact is missing names the script that writes it rather
than disappearing**, and that behaviour is what the tests check hardest: a
renderer that silently drops a section produces a document indistinguishable
from one where the section was never required, in the document a reviewer checks
the definition of done against. Verified against an empty directory — three
headings, three absence notices, no invented number.

**And `scripts/03_matrix.py` cannot run on this machine.**

| | |
|---|---|
| warrant records in the local ledger | 45 |
| unreadable by the current model | **34** |
| written between | 2026-08-27 and 2026-08-30 |

They carry an `auroc` with no `convention`, which `DECISIONS.md` 110 later made
mandatory. The script appends warrants and then rebuilds the matrix from the
*whole* ledger, so it dies on the read-back — after two minutes of work, having
already appended. **Two attempts today took the ledger from 41 records to 45
before this was understood**, which is the part worth reporting: a broken script
that writes before it fails makes its own diagnosis more expensive each time it
is run.

**A clean clone is unaffected, and that was checked rather than assumed.** The
ledger is gitignored; running the script against an empty directory completed,
exit 0, from a fresh 11-record ledger. This is a development-machine failure, not
a reproducibility defect, and saying which is the difference between a note and
a retraction.

Shipped: a preflight that reads every record first and refuses with the count,
three real errors, the cause and the one safe remedy — *move the file aside, do
not delete it, it is an append-only audit record*. Verified to leave the ledger
at 48 records, exactly as found.

**What is still not done, and it is the contract item.** The **committed**
`RESULTS.md` does not yet carry the new sections and cannot be regenerated here
without regressing it: a fresh run produces 21 table rows against the committed
32 and **zero** of the 15 measured rows, because the committed document reflects
a ledger accumulated across the whole chain and the chain starts at `00_extract`,
which needs a GPU. Re-rendering from `results/warrant_matrix.json` is not
available — `to_payload()` drops the envelope, the controls and the convention.

So the renderer is ready and the document is not. **No failing test was added
for it**: `DECISIONS.md` 145 settled that a signal firing on a condition nobody
will act on teaches its reader to ignore the signal. `DECISIONS.md` 155.

---

## 6. Ledger

**Code** — `controlplane/validation/scorefree.py`,
`tests/test_scorefree.py` (10 tests), `scripts/26_scorefree.py`.

**Artifacts** — `results/scorefree/scorefree.json`,
`results/scorefree/SCOREFREE.md`.

**Claim table** — nine rows added, 49/49 → 58/58.

**Decisions** — 152 (registered before the code, with four falsifiers), 152a
(results, including C3), 153 (two artifacts, one profile, two budgets), 154 (138
closed as scope), 155 (`RESULTS.md` sections and the ledger preflight).

**Reproduce**

```
python -m pytest tests/test_scorefree.py -q
python scripts/26_scorefree.py --config config.yaml
python scripts/verify.py --claims-only
```

---

## 7. What this changes

**The limitation is now priced rather than only named.** Before this phase the
honest scope was *"classifiers and rule systems, not generative extractors"*.
It still is — but the reason has moved from *"we have not built it"* to *"here
is what it costs, here is where it stops paying, and here is the assumption that
makes those numbers optimistic"*.

**And it produced a procurement fact that is not in REDACT, PIIBench, or any eval
platform surveyed:** a detector that emits one bit has exactly one operating
point, so a false-positive budget is not something you can ask it for. That joins
refusal and tunability as things certification says and scoring does not. An F1
table cannot show it, because F1 is computed wherever the detector already sits
and never varies the threshold.
