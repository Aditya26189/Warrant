# Codex's parallel decision log, preserved

Between 2026-09-15 and 2026-09-16 two lines of work allocated the same decision
numbers. Entries 198, 199 and 200 in `DECISIONS.md` belong to the Claude line
(label error, the project's own certificates under label error, the clean-clone
gate). Codex's line, on `feat/customer-evidence-integration`, committed three
different entries under the same three numbers.

Neither history is rewritten and no heading is renumbered. `DECISIONS.md` keeps
the Claude entries, and Codex's three are reproduced below **byte-for-byte** as
they stand at `55528c7ccc1633204987346f1f5f651c8d311a2b`. They are cited as **Codex-parallel 198, 199 and 200**
with this path. The reconciliation is `DECISIONS.md` entry 202, and the plan was
agreed on the coordination board (posts 34 and 36) before either side merged.

| Cited as | Heading | Source commits | SHA-256 of the entry's bytes | Bytes |
|---|---|---|---|---|
| Codex-parallel 198 | `198 - A shared context board for concurrent coding sessions (2026-09-15)` | `1a07eb3bb3fa`, `0a02123c5de9` | `2e871e39c29d8d257946be88da3ddf7908310cf6298cd8d603283ff83c041f57` | 1510 |
| Codex-parallel 199 | `199 - Refuse ambiguous scored-input fields before dictionary conversion (2026-09-15)` | `76e4e1c1aa5f` | `8c5bbadbc5261eec503bc2e64f69da03d7171ddc057f5df5979cd74fb6219735` | 786 |
| Codex-parallel 200 | `200 - Refuse inconclusive release studies and version their protocol (2026-09-15)` | `261351a7c138` | `43331db7ab76a0dbf793b8ba1e3e8c4dfbf27211581f204f78eb073b8fd8d8ee` | 1318 |

Each digest covers the entry exactly as stored in `DECISIONS.md` at that commit:
from the first byte of its `## ` heading line up to, and not including, the first
byte of the next entry's heading, or the end of the file for the last. The whole
block below is those bytes concatenated, with SHA-256
`a145f5f7f6a4d37176a756b6564ab1db86810d2b9dd158c6cf33080dec987e1c`. To check, run
`git show 55528c7ccc16:DECISIONS.md` and hash the same ranges.

---

## 198 - A shared context board for concurrent coding sessions (2026-09-15)

The founder explicitly requested a shared page where Codex and a parallel
Claude session can exchange messages and report their work. Add a local,
file-backed board with one immutable JSON file per post and a generated
SHARED_CONTEXT.md page. No network service or account connection is required.
Use a SQLite write transaction solely as an interprocess mutex while publishing
events and refreshing the page; the readable JSON files remain the durable log.
Sequence numbers are allocated under that mutex rather than inferred from clocks.

Support messages, status, path claims and releases. Reject overlapping claims
owned by different agents, including parent/child directories. These are
coordination claims, not filesystem access controls; an agent that ignores the
board can still edit files. Preserve explicit author labels and do not invent
Claude responses. Agent sessions must read the board to receive messages.
Acceptance: concurrent posts are retained, sequence numbers remain unique,
overlapping ownership is rejected, released paths can be reclaimed, and posts
remain literal text in the generated page.

Operational messages and SHARED_CONTEXT.md are local, ignored runtime state.
The CLI, tests and participation protocol are versioned; messages are preserved
on disk but do not dirty scientific provenance. Separate worktrees pass --root
to the shared checkout. Authors are self-declared, and claims are advisory.


## 199 - Refuse ambiguous scored-input fields before dictionary conversion (2026-09-15)

CSV DictReader and JSON object parsing currently retain the last duplicate
field silently. A file can therefore change a score or label by column order
while appearing to satisfy the strict intake contract. Reject duplicate CSV
column names, including collisions after the existing whitespace normalization,
and duplicate JSON keys before conversion to dictionaries. Include the source
and duplicated field in the error. Apply this to metadata too: silently dropping
it contradicts the contract. Preserve label_2, grouping, valid exports and the
explicit release-only single-class option. Tests must exercise conflicting
labels/scores, normalized columns, metadata and clean-file compatibility.


## 200 - Refuse inconclusive release studies and version their protocol (2026-09-15)

Claude's review found release's UNVALIDATED status conflicted with the product
meaning "never tested here". New release registrations use protocol/schema 2:
a tested study is VALID only when every registered confidence bound clears;
otherwise REFUSED, with distinct reasons for a point-estimate violation, an
inconclusive bound or a missing denominator. Refusal does not establish a
population violation. UNVALIDATED remains the legacy protocol-1 spelling for
inconclusive/missing evidence; retained protocol-1 records must still reproduce
exactly, and verification must identify that older protocol explicitly.

Keep the preregistered five equal-tailed Clopper-Pearson intervals, each at
alpha/5, and the union-bound joint coverage of at least 1-alpha. The acceptance
bounds therefore use alpha/10 in each tail. The single-FPR certify workflow
uses a one-sided alpha bound; its VALID verdict is conditional on that different
protocol. Name the release protocol in output and test a case where certify
clears but simultaneous release evidence refuses. Do not loosen uncertainty
to make status strings agree. Existing contract versions retain their original
method; new contracts bind schema 2 into their identity before evaluation.
