# What to do next

> Follow-up, 24 September: this is the historical integration handoff. The
> independent review and subsequent local repairs are recorded in
> [PHASE-13.md](PHASE-13.md). That report distinguishes repaired behavior on the
> current repair branch from what is still on main. The buyer-conversation gate
> and its preregistered stopping rule below remain unchanged.

**Dated 2026-09-17, at the close of sprint 12.** Written for the founder, and for
whoever picks the work up. Everything below is either a decision only a person
can make, or work that is already specified and has a named way to close it.

**Where things stand.** Both lines of work are merged on `main`: the customer
path, the chain of rechecks with its integrity fix, Codex's coordination board,
strict input parsing and release protocol 2, and the documentation pass. The full
suite passes, and the clean-clone gate passed at `e03279d` with claims 92/92 and
frozen-score metrics 25/25; later commits add only the gate record and these
reports. `main` and every branch are pushed to GitHub at your direction. CI on the
pushed commits was not checked from here: read it in the repository's Actions
tab. The sprint report is `reports/PHASE-12.md`, section 9.

---

## The one sentence

The engineering question is answered well enough; the commercial one has not
been asked. **The next step is the twelve conversations registered in
`reports/STRATEGY-2026-09.md`, not another sprint of code.**

---

## 1. Decisions only you can make

In the order they block other work.

| # | Decision | Why it is yours | What it unblocks |
|---|---|---|---|
| 1 | **Company or research project.** Run the test `STRATEGY-2026-09.md` §5 registered: eight to twelve conversations with model-validation and compliance leads, asking what happened when a control was wrong, and showing a refusal. **Its falsifier:** fewer than three of twelve can name an occasion where a wrong AI control claim had a consequence for someone | It needs your relationships and your name. No agent will contact anyone | Whether any item in section 2 is worth doing, and in what order |
| 2 | **Review the merged line, and read the CI run on GitHub.** No human has reviewed it, and Codex's independent review of the chain fix is still owed (section 2, item 1). It is already pushed, to a private repository | An agent reviewing its own integration is not an independent check | Confidence that what is on GitHub is what the reports describe |
| 3 | **The four pilot questions** in `docs/PILOT-PROTOCOL.md` §11: an existing relationship or cold; free or paid, and what is asked in return; whether refusal is saleable in their culture; the smallest decision worth the effort | They are facts about a buyer, and the protocol is only a plan until they are answered | A pilot, if decision 1 says there is a buyer |
| 4 | **The `certify --budget` default after a frontier** (`DECISIONS.md` 195). A budget picked off the frontier is certified at the stricter frontier level only if the user passes `--from-frontier`; otherwise it is certified at the plain level, with a notice when a frontier record for the file sits beside it | It trades safety by default against a command that behaves the same as before | Nothing blocks on it; it is open by design |
| 5 | **Exception approval against invariant 3.** The RBI draft contemplates deploying a model approved with exceptions; nothing records one beside a REFUSED warrant (PHASE-12, O-2) | Recording exceptions changes what "refusal has no override" means | A regulated pilot |
| 6 | **Owners for three fixes in read-only code.** The one-line guard for the Linux Rego abort (`DECISIONS.md` 145, `policy/engine.py`); `FPRMonitor`'s cap and docstring (`validation/warrant_stats.py`, PHASE-12 §1.5); PSI's smoothing epsilon, documented as config and actually a constant (`drift/`, `docs/LIMITATIONS.md` §4.4) | The zones are read-only by your rule; an agent reports, it does not edit | Linux policy evaluation; an honest monitor docstring |

---

## 2. Engineering, if the work continues

Ordered by how much a wrong result would cost. Each names what closes it.

1. **Codex's independent review of the chain fix.** The fix was merged at your
   direction before that review happened (`DECISIONS.md` 202). A finding is a new
   fix on `main`, recorded in `DECISIONS.md`, not a reason to reopen the merge.
2. **Implement `DECISIONS.md` 201** (Codex): on a grouped file, withhold kappa's
   population interval instead of resampling item pairs as if independent. Today
   the interval can be too narrow. When it lands, update `docs/INPUT.md`
   (`label_2`), `docs/LIMITATIONS.md` §3.6 and `docs/PILOT-PROTOCOL.md` §1 and §4
   to the merged behaviour.
3. **Decide what an unchained recheck does with a revoked chain.** An unchained
   `warrant recheck` never reads the chain head, so a warrant its chain has revoked
   can still receive a VALID recheck on a new file. Either refuse, or print a
   notice naming the revoking record.
4. **Bind the certify warrant.** Four gaps in `docs/EVIDENCE-HANDOFF.md` §6: a
   warrant carries no digest of its rows, no expiry, no system or detector
   identity, and an unchained recheck does not name its warrant. With them,
   `docs/LIMITATIONS.md` §3.7: a certify warrant has no seal and no verifier. This
   is one schema change and needs its own decision before code.
5. **Codex's uncommitted work in the main checkout.** That checkout is on
   `feat/release-evidence` with uncommitted edits to six tracked files
   (`.gitignore`, `AGENTS.md`, `DECISIONS.md`, `README.md`, `pyproject.toml`,
   `tests/test_smoke.py`) and untracked files including
   `tests/test_inventory_smoke.py`. None of it is on `main`, and the `DECISIONS.md`
   draft there numbers the board entry 187, which predates the reconciliation.
   Codex should commit what is still wanted onto a branch from the new `main`, or
   discard it. It was not touched by the integration.
6. **Clean up.** Every local branch is contained in `main`, and all of them are
   now on GitHub as well. Every worktree head is on `main` too, except two
   superseded ones (a merge rehearsal and a pre-rebase copy of the 194 review)
   whose commits `git cherry` finds on `main` under other hashes. The merged
   branches, local and remote, and the scratch worktrees can be deleted.
7. **Only if a pilot needs them:** the four declared-but-uncomputed envelope
   features and MMD (`DECISIONS.md` 172); the demo video (`reports/PHASE-11.md`);
   a second model family.

---

## 3. What not to do

- **Do not start another sprint of code before the conversations.** No sprint
  since the strategy memo has tested whether anyone pays.
- **Do not build a benchmark.** The wedge does not exist (`STRATEGY-2026-09.md`,
  correction at the top).
- **Do not fill evidence gaps by hand.** A handoff sheet may not state a field no
  record carries (`docs/EVIDENCE-HANDOFF.md` §6).
- **Do not make a robustness claim, or a regulatory claim without a primary
  source and a date.** A test enforces the first in the README's three-clause
  section only; the second is a working rule with no test behind it.
- **Do not quote a number from outside the claim table.** `make verify` checks
  those, and only those.

---

## 4. What is and is not established

**Established, and checkable on a laptop:** every number in the README claim
table reproduces from committed artifacts; the certification, recheck, chain and
label-error arithmetic is tested against independent computation; a chained
record cannot be edited without `warrant chain verify` noticing, short of
recomputing its seal.

**Not established:** that anyone will pay; that refusal reads as integrity to a
buyer; any result on production traffic; any result with human labels; any
result on a second model family; reliable detection of a breach at a monthly
recheck cadence, which simulation shows is measurably worse than weekly. `docs/LIMITATIONS.md` is the full list and should be
read before anything here is quoted.

---

## 5. Where to look

| Question | Document |
|---|---|
| What the sprint did, found and did not establish | `reports/PHASE-12.md` |
| What each agent did, for a human reviewer | `reports/REVIEW-2026-09-16.md` |
| Why the commercial question comes first | `reports/STRATEGY-2026-09.md` |
| A pilot, if there is a buyer | `docs/PILOT-PROTOCOL.md` |
| What to hand a validation function | `docs/EVIDENCE-HANDOFF.md` |
| What is missing | `docs/LIMITATIONS.md` |
| How the two decision logs were reconciled | `DECISIONS.md` 202, `docs/decisions/CODEX-PARALLEL.md` |
