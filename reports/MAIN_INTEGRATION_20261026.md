# Main integration - 26 October 2026

The user explicitly requested all committed branches merged and pushed to GitHub
main. This integrates completed work and preserves branch history. It does not
approve the blocked B1 sampling frame, authorize B2, or change certification.

Starting GitHub main: `dd4ee852d94ff698b9d1a4fbd7ba6dd7469143af`.
Completed code/evidence checkpoint: `b79e07b6ed3a8f49357725019591393a2550cf68`.
This report and README links are a subsequent documentation change; the final
published hash is reported separately.

## Included work

| Work | Original completed source | Integration |
|---|---|---|
| Stage A/B1 audit and continuation | `61d7692ae23f550f5662c68ab54ca7141f7b8031` | `579a031` |
| Seven superseded branch histories | Listed below | `e888164` |
| Calibration scaffold, runner, portability repair | Through `7a7b68d` | `f5f9672`, `c06685c`, `b0e1cb5` |
| Completed calibration evidence | `5cd5b00fa289ecf512d6de37bd9973e503e466f5` | `370ad8b` |
| Conventional calibration baseline | `c9f10774ebe5d086c66bda5569a981ff9b35421f` | `b79e07b` |

The seven older histories were merged using `ours`, retaining current contents.
This preserves their commits without restoring obsolete revisions. The previous
[branch review](BRANCH_REVIEW_20261025.md) records the substantive comparison.

- `docs/phase21-crosscheck`, `docs/phase22-report`,
  `docs/phase23-public-caveat`, `fix/grouped-boundary`: equivalent changes
  already integrated on main.
- `feat/chain-evidence-replay`: substantive fixes already integrated;
  its older inventory is superseded by the regenerated current inventory.
- `feat/release-evidence`: parallel root draft superseded by newer release,
  coordination and intake work; restoring it would undo current work.
- `test/open-findings-executable`: obsolete expected-failure tests for repaired
  defects now covered by grouped/mixture regressions.

At the checkpoint, all **123 local branch tips** and **45 fetched origin branch
tips** were ancestors of HEAD. No branch was deleted. Other checkouts, user
attachments and uncommitted files were left in place. A local branch/tag safety
bundle was created and verified as complete history before publication; it is
ignored operational backup, not a committed artifact.

## Verification actually performed

| Check | Result and source |
|---|---|
| Complete core suite | **2,316 passed**, 3 warnings, 3,843.80 seconds on clean `b0e1cb5a30d381bbb40bec20ee4b6e6a2de090d6` |
| Certification audit plus research validators | **88 passed** on `e888164`; includes 29 Stage A tests also covered by the core suite |
| Final experimental unit checks | **73 passed, 1 skipped** on clean `b79e07b`; POSIX-only timeout test skipped on Windows |
| README claims | **92/92 reproduced** on `b0e1cb5` |
| Frozen-score recomputation | **25/25 bit-identical comparisons** on `b0e1cb5` |
| Activation re-derivation | **SKIPPED**: ignored activation cache absent |
| Smoke during integration | **7/7**, clean source; final publication also receives a clean smoke check |
| Calibration packager replay | **21 payloads byte-identical**, including 20 raw files, on `b79e07b` |
| Baseline packager replay | **69 payloads byte-identical**, including 67 raw files, on `b79e07b` |
| Ruff | Passed for final feasibility/baseline executable sources, excluding preserved raw evidence |
| Research preservation | All **922 files** have identical Git blobs to research source `61d7692` |
| Checkpoint 011 replay | All four generated payloads reproduced exactly with retained local source caches |
| Production diff from starting main | Empty for `controlplane/`, `config.yaml`, `pyproject.toml`, `requirements.txt` |
| Introduced-object size | Largest blob **9,000,000 bytes**; none exceeds 10 MB |

The core command was `python -m pytest -q -p no:cacheprovider -o
addopts=--strict-markers tests/`. Other checks used the scoped research pytest
modules, `python -m unittest discover -s experiments/grader_poc -p 'test_*.py'`,
the separate P2/payments boundary unittest modules, `python scripts/verify.py`,
and `python scripts/smoke.py`.

The offline packager replays used fresh temporary directories and executed no
benchmark workers. All payload bytes matched; only the temporary replay
manifest's packaging revision reflects the integration checkout.

After the full-suite checkpoint, only isolated experimental source/evidence and
documentation were added. Those changes received the final focused unit, lint
and packager checks; the entire core suite was not repeated. The source session
separately reports all 11 baseline tests passing on Linux, including the real
timeout test. That is attributed evidence, not an independent Linux rerun here.

Inventory commit `6a78b4a` changes the published collection count from 2,287 to
2,316, generated from clean source `825bcfb`. Collection alone is not execution;
the full run separately establishes the passing-suite result. No cached model
inference or new research outcome extraction was performed. Remote CI has not
been established by local tests.

## Scientific limits retained

The [B1 status](../docs/research/fpr_reporting/b1/B1_CURRENT_STATUS.md) remains
**FRAME_BLOCKED**: 29 works supported pointwise, 34 excluded, 309 UNCLEAR;
372 works and 389 memberships retained. This is not a complete approved frame.
No pilot draw, human assignment or B2 outcome extraction was performed. The
[adaptive-bound issue FPR-001](../docs/research/fpr_reporting/issues/FPR-001-adaptive-bound.md)
remains open; statistical review and any repair are separate work. Frozen
research artifacts and historical certificates were not rewritten. The B1 replay
uses retained private source caches, not a fresh-clone, cache-free environment.

The [calibration report](GATE1-FEASIBILITY.md) establishes working controls on one
scoped task, not family-wide feasibility or measured human productivity. The
[baseline report](GATE2-BASELINE.md) retains the negative result: all 13 mutations
were rejected by the unchanged full grader, with no new omission. Neither report
establishes discovery advantage, publication novelty or product demand.
Held-out tasks and later experimental gates remain unexecuted.
