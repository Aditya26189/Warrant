# Phase 41 - Fresh-clone public handoff has three reproducible outcomes

A tracked-file clone of the local Phase 40 checkpoint completed the exact
public PowerShell handoffs for a synthetic valid certificate, a grouped
refusal, and an altered-source mismatch. The commands ran from the clone with
the existing customer-only Python 3.12 virtual environment and generated
only OS-temp output. The clone remained clean. This is a technical first-run
check by the project agent, not an unaided reviewer trial or a real detector
evaluation.

## Question and scope

The October plan asks for a short reproducible demonstration with one valid
input, one unsupported case and one tampered file. Phase 35 checked the
public valid handoff in a clean clone; Phase 38 exercised the refusal and
tamper commands from a clean commit in a worktree; Phase 39 covered the
refusal through an installed wheel. This phase puts the two complete public
walkthroughs into one new tracked-file clone, reducing the possibility that
the recent documentation works only in a developer's checkout. There was no
product-code change, new fixture, estimator change or customer data.

The clone was made with `git clone --no-local --branch release/root-main
--single-branch` into a new OS-temp path from local merge `ceb7d36`. Its
checked-out HEAD matched `ceb7d361d43c9900c6b9ed916d15c60f9a63af0c`;
`git ls-files` counted 625 tracked files, and `git status --porcelain` was
empty before and after the run. The shared checkout's untracked
`ARC180_BRIEF.md` was not copied or modified. An existing virtual environment
created for Phase 35 was put first on `PATH`; this run did **not** resolve or
install packages anew. That environment reports Python 3.12.10, `pip check`
found no broken requirements, and checks for `torch`, `transformers`,
`datasets`, `spacy`, `sklearn`, `matplotlib` and `presidio_analyzer` returned
an empty list. `controlplane.__file__` resolved inside the clone.

`PIP_NO_INDEX=1`, `HF_HUB_OFFLINE=1` and `HF_DATASETS_OFFLINE=1` were set for
the run. These settings prevent accidental package-index or Hugging Face
lookups by tools that honor them; the test did not instrument every possible
network API or prove general offline operation. The public commands themselves
do not call a model or need a research download. All generated prepared
packages and records were placed under unique OS-temp directories.

## Work and observed result

I ran the exact PowerShell commands in `examples/README.md` section 4. Each
of the four CLI steps exited 0, in 41.62 seconds for the sequence:

| Step | Observed output | Exit |
|---|---|---:|
| Prepare `export_certifies.csv` | `PREPARED` | 0 |
| Replay source and mapping | `VERIFIED: prepared package matches retained inputs` | 0 |
| Certify prepared `scored.csv` at 0.05 | `WARRANT: VALID` | 0 |
| Verify certificate from prepared rows | `VERIFIED: effective rows and material certificate fields recompute` | 0 |

The valid output reported 400 items (102 positive, 298 negative), 8 false
positives on 298 independent negative units, and an FPR upper bound of
0.0479 against the 0.05 budget. It reported threshold 0.864735, recall
0.5686, precision 0.8788, flag rate 0.1650 and lift 3.446, each drawn
from the existing seeded example. These are the example's numbers, not a
new detector measurement or a second evaluation set.

I then ran the exact PowerShell commands in section 5. The four initial
steps each exited 0: `PREPARED`, preparation `VERIFIED`, `WARRANT: REFUSED`
and certificate `VERIFIED`. The refusal output reported four rows (two
positive, two negative) in two conversation groups and said only two
independent units were available versus at least 59 clean negative units
needed for the 5% budget at alpha 0.05. The refusal wrote a record and its
verification succeeded. This sequence, the source-note edit and both
post-edit replays took 17.29 seconds together.

The documented one-line Python edit changed the first excluded source note
from `synthetic example only` to `changed example only` in a copied CSV and
exited 0. `verify-prepared` on that changed source reported `MISMATCH` and
exited 1. `verify` on the original refusal record and unchanged prepared
`scored.csv` still reported `VERIFIED` and exited 0. The outcome is coherent:
preparation replay binds the retained source bytes; certificate replay binds
effective scored rows. The two status lines answer different questions.

## What this does not establish

The run used synthetic repository fixtures and an existing venv. It does not
establish that a fresh dependency resolution still succeeds today, that a
published wheel is installable from an external index, or that every offline
environment works. Phase 35 separately did a new dependency install, and
Phase 39 tested the locally built wheel. This phase is a clean **clone**
check of source commands, not a second instance of either earlier test.

The agent knew the project and executed the commands. A person unfamiliar
with the label and unit contract has not yet tried the workflow. The valid
fixture declares independent rows, and the grouped fixture declares two
conversation groups; the run does not prove those declarations resemble a
real customer's sampling process. The labels are synthetic, with no external
reviewer provenance. A byte match does not authenticate an owner or prove
the verdict useful in a recurring decision. The refusal reflects insufficient
evidence under the declared budget, not a finding that a deployed detector
is bad. No incumbent packet or external adoption was observed.

The clone did not regenerate model activations or score the protected research
test set. It also did not run the full repository suite. A later inventory
count reports collected tests only. A future reviewer must not treat this
technical dry run as the October plan's human user gate, its demand gate, or
proof of an operational pilot.

## Open items

The next necessary observation is a human reviewer following the worksheet
without project-author help and explaining the two replay boundaries and the
meaning of refusal. A real workflow also requires a permissioned source
export, score direction, positive-label meaning, label provenance, a valid
independent unit, a named recurring decision and the configured incumbent
packet for the same decision. None is present in this clone. The October 14
targets of five conversations, two usable exports and one decision owner
remain targets rather than results. Software and synthetic commands cannot
complete those external gates.

The early October incumbent check found overlap with generic evaluation and
governance tools, so adding a dashboard or adapter without an observed packet
gap remains outside the plan's stop rule. If a reviewer finds a concrete
first-run failure, preserve its exact command, inputs and environment and
add a regression before fixing it. If no reviewer or data arrives, the
honest next artifact is a recorded no-data gate, not another invented use
case. This report records the executable state so that trial can start from
known commands and limits.

## Ledger

| Change or check | Evidence |
|---|---|
| Tracked-file clean clone | Local source `ceb7d36`, clone HEAD `ceb7d361d43c9900c6b9ed916d15c60f9a63af0c`, 625 tracked files, clean before and after |
| Customer-only environment inspection | Python 3.12.10; `pip check` clean; seven heavy-package lookups absent; `controlplane` imported from clone |
| Valid public walkthrough | `examples/README.md` section 4; four exit-0 commands, PREPARED/VERIFIED/VALID/VERIFIED, 41.62 seconds |
| Refusal and tamper walkthrough | `examples/README.md` section 5; initial four exit-0 commands, edit exit 0, preparation MISMATCH exit 1, certificate VERIFIED exit 0, 17.29 seconds |
| Source or dependency change | None; source commands in a local clone, preexisting customer-only venv |
| Clean test inventory | `results/test_inventory.json` generated from clean `d30698f`; 2,228 collected, execution not implied |
| Clean documentation and inventory gate | `4f1ca28`; 159 passed, exit 0 |
| Clean smoke and available verifier | `4f1ca28`; smoke 7/7, claim table 92/92, frozen scores 25/25; activation tier skipped with `--no-activations` |
