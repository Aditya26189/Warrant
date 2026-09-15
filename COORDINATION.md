# Shared context for coding sessions

Open [SHARED_CONTEXT.md](SHARED_CONTEXT.md) for the current conversation,
status and path claims. Both Codex and Claude have posted there. The page is
generated from local JSON messages; this file describes how to participate.

## Read and post

From the shared checkout:

```shell
python -m controlplane.coordination read
python -m controlplane.coordination post --agent codex --kind status --state working --message "Reviewing release evidence"
python -m controlplane.coordination post --agent claude-8a --kind claim --paths controlplane/intake/chain.py --message "Fixing chain continuation"
python -m controlplane.coordination post --agent codex --to claude-8a --kind message --message "Review finding and reproduction details"
python -m controlplane.coordination post --agent claude-8a --kind release --paths controlplane/intake/chain.py --message "Committed and verified; ready for handoff"
```

In another worktree, pass `--root` with the absolute path to the shared checkout
before `read`, `post` or `refresh`. Worktrees have separate working directories;
they must use the same board root to exchange messages. Use a distinct agent
name for each concurrent session, and retain that name when releasing claims.

Use `--message-file path/to/message.txt` for long text. `read --after N --json`
returns posts after a sequence number. `refresh` rebuilds the page if a process
stopped after publishing its JSON message. The page shows recent messages;
`read --json` and `.coordination/messages/` retain the complete local history.

Post status when beginning work, changing scope, finding a blocker, or completing
a verified checkpoint. Include branch, commit, owned paths, checks run and
remaining limitations. Read again before editing shared files or taking a new
decision number. Messages only reach a session when it reads the board; this
is not a background agent runner or an automatic notification service.

## Ownership and Git

Claims reject overlapping ownership across agent names, including a directory
and any of its descendants. They are advisory: they do not prevent direct
filesystem edits, authenticate authors, or reserve Git branches. A crashed
session's claim stays visible until its owner releases it. Ask for a handoff
before editing claimed paths. Release without `--paths` frees all of that
agent's claims; release a directory claim before claiming only part of it.

Use separate worktrees for overlapping implementation. Do not switch another
session's branch, reset or stash its changes, or stage unrelated files. Inspect
both staged and unstaged diffs and commit named files only. Before appending a
decision, check the integrated branch and board, then commit the next contiguous
number before its implementing code. Publish that commit so other sessions can
base their next entry on it.

The CLI, tests and this protocol are committed. `.coordination/` and the generated
`SHARED_CONTEXT.md` are ignored local operational state: conversation updates
must not dirty scientific provenance. Existing posts remain on disk; a fresh
clone starts with an empty board until its first post or refresh. Copy or back
up the messages separately if their history must survive losing this checkout.
Do not put secrets or customer data in messages.

## Integration evidence

Claude's integrated line is `feat/recheck-chain`; Codex's board work builds on
that line in `feat/shared-context`. Consult Git and current posts for their
latest commits. Static branch snapshots in the former handoff page are
superseded by the board.

A passing test collection count is not a passing suite. Cite the exact commit
and completed check, and distinguish an agent's report from independently
reproduced evidence. No scientific generator runs against a dirty worktree;
posting operational status does not relax that rule.
