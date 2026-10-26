# Stage A repository snapshot — 17 October 2026

Status: Stage A only; a research triage record, not a preregistration or paper.

- Repository/shared checkout: `C:/Users/LawLight/Desktop/accenture`.
- Base and production source: `b7de189a62943b18d512b58df606621270b06c6b`
  (`release/root-main`, Phase 54 minimum-Python gate).
- Isolated branch: `research/fpr-stage-a-20261017`; worktree:
  `C:/Users/LawLight/Desktop/accenture/.venv/fpr-stage-a-20261017`.
  Initially clean at that SHA. Existing worktrees were inspected and preserved.
- Shared checkout has four pre-existing untracked entries: `ARC180_BRIEF.md`,
  `WARRANT_CODEX_ONE_PACKAGE/`, `mentor-share-2026-10-15/`, and
  `warrant-agent-pack (7)/`. None is staged or copied into this branch.
- Windows/PowerShell; Python 3.12.10, NumPy 2.2.6, SciPy 1.16.3,
  pytest 8.2.2. Runner: `python -m pytest`; lint: `python -m ruff check`.
  This is a source-checkout audit, not a fresh installed-wheel or Python 3.10 gate.

## Instructions, prior work and boundaries

Read the complete single authoritative `WARRANT_CODEX_ONE_PACKAGE/READ_ME_FIRST.md`,
then its independent oracle, extraction codebook and checksums. SHA-256 checks
matched all three manifest entries (PASS). Package files remain untracked.
Read repository `AGENTS.md`, `COORDINATION.md`, shared board/context,
`CLAUDE.md`, `docs/CONTRIBUTING.md`, `docs/SPEC.md` and `docs/TASKS.md`.
Root `SPEC.md`, `TASKS.md`, `CONTRIBUTING.md` have moved under `docs/`.

The current user's explicit Stage A scope overrides older instructions to merge,
tag, defer narrative documentation, or restrict work to activation probes.
No merge, push, tag, PR, publication or later-stage execution is authorized.
The package's named small deliverables serve as the scoped closing report;
no new numbered phase or global decision sequence is invented. Proposed pilot
choices remain unfrozen in the draft and commit messages.

Production entry point is `pyproject.toml` → `controlplane.cli:main` →
`_certify` → `controlplane.intake.certify.certify_items` / `certify_budget` →
`controlplane.validation.warrant_stats.certify_fpr` / `cp_upper`.
Related tests include `test_warrant_stats.py`, `test_intake.py`,
`test_frontier_groups.py`, `test_certify_from_frontier.py`,
`test_certify_evidence.py`, `test_certify_verification.py`, and
`test_label_sensitivity.py`; exact executed coverage is in `CERTIFY_AUDIT.md`.

The local coordination history and `mentor-share-2026-10-15/01_CURRENT_STATE.md`
record the older activation and sequential-monitor studies. Latest follow-up
source is `99c372484dd21ded1b313f2c9be06a4c2d101c7d`; original Gate 1 is
`e8d20a2d40a92577eda7e158a9535f837da93319`. Their reported failed joint
product gate is not overturned here. `v3/` and `v4/` are absent from this
production base; copies exist in the separately packaged mentor material.
Those records are context, not independent verification or alternate task prompts.
Past chat transcripts are not available through a dedicated chat-history tool;
no claim to have reread inaccessible chats is made.

Immutable: production Python/config, `results/`, `round1/`, `evalsets/`,
scientific arrays, prior decisions/protocols, research branches/tags and packaged
historical results. Only this new documentation directory and a focused new
test module may change. No scientific generator, test-set rescoring, monitoring
simulation, GPU or paid compute is part of Stage A.

## External-access preflight

Observed at **2026-10-17 07:48:41 UTC**, through the permitted web tool:

| URL | Retrieved material | Status |
| --- | --- | --- |
| https://arxiv.org/abs/2503.02574 | Official title, authors, abstract, version history (v2, 18 May 2026) | PASS; ABSTRACT_ONLY |
| https://arxiv.org/pdf/2503.02574 | `application/pdf`, 24 pages, 1,644 parsed lines; title page and research text retrieved | PASS; full text accessible, initially SELECTED_SECTIONS read |

The abstract title is *LLM-Safety Evaluations Lack Robustness*; the PDF title
includes *Position:*. Initial accessibility does not mean all pages were read.
A2 records actual reading depth, versions, venue evidence and research limits.

## Operational verification

`git status --short`, `git rev-parse HEAD`, `git worktree list`, branch inventory,
Python/dependency queries, package SHA-256 checks and board reads completed.
Coordination agent: `codex-fpr-stage-a-20261017`, initial posts 388–389.
The first sandboxed worktree creation failed with Git-ref permission denied;
the same local operation succeeded through approved escalation. No automatic
approval rejection occurred. Exploratory reads also encountered absent root
spec paths, absent `v3/`, and a PowerShell `rg` wildcard error; corrected paths
were used. These are not successful checks or scientific findings.

AI assistance is used for source review, research and drafting. Repository
policy does not require a new AI-use addendum; the existing research note was
read as context. No human verification, statistician sign-off, authorship
attestation or TMLR readiness is asserted. Local commits are not preregistration.
