# B1 continuation - 27 October 2026

Checkpoint [012](checkpoints/012/REPORT.md) retains all 372 works and 389 source
memberships. It records **25 pointwise supported, 34 excluded and 313 UNCLEAR**,
compared with 29/34/309 at checkpoint 011. Status remains **FRAME_BLOCKED**.
These are disclosed, reviewer-informed custodian judgments, not a fresh
independent review, an approved complete frame or a publication result.

## Scientific correction

A bounded recheck of the 29 positive English-evidence bindings found four more
instances of the inference already corrected for W0029/W0035. English auxiliary
detector instructions do not establish English in the text being classified.

| Work and selected version | Released evidence that was insufficient for input language |
|---|---|
| W0008, arXiv:2403.17710v5 | English secret-repetition and question/response formatting instructions |
| W0041, arXiv:2504.11358v4 | English secret-repetition instruction applied to target data |
| W0044, arXiv:2504.19793v3 | English known-answer detector instruction applied to tool-description content |
| W0058, arXiv:2507.05630v3 | English instruction to ignore appended data and repeat a key |

[Judgment 012](AUTHOR_JUDGMENTS_012.json), committed at `2d350c7`, withdraws only
the unsupported English criterion. Task, binary evaluation and pre-target-answer
support remain. None of these works is newly excluded. Earlier positive bindings
are preserved as superseded, and all earlier checkpoints remain unchanged.
This applies the [existing language rule](ENGLISH_EVIDENCE_APPLICATION.md); it
does not introduce an English-only test requirement or a language-specific
results-table requirement. It does not newly certify the other positive rows.

[Request 008](ADDITIONAL_SOURCE_REQUESTS_008.json) asks for the missing language
linkage in these four exact editions. It reuses the captured sources, verifies
their hashes and adds no candidate or discovery query. Request SHA-256:
`c2c0c6ab0edb4f35a7edc7623605e50484a475dec8949c66d3d04147cd474c22`.
No outcomes, sample/false-positive counts or assurance classifications were used.

## Research-audit repairs and validation

The clean research branch was advanced from `61d7692` to the already approved
and published main integration `2187f85`. The old audit then failed
`OUT_OF_SCOPE_CHANGE` because it compared the whole integrated history with the
older research-only baseline. Repair `b7d91f0` pins new-change scope to the
explicit approved integration while retaining `e073ce2` as the frozen scientific
history baseline. The pin is not inferred from a moving branch. New runtime
changes and unrelated histories still fail.

A further regression showed that a checkpoint introduced after the original
baseline could otherwise be rewritten within the allowed research directory.
Repair `71638f6` additionally protects artifacts present at the integrated
checkpoint, while allowing helper refactoring and the active status pointer.
The regression failed before the repair and passes afterward. The initial five
scope tests were also red before the new scope interface was implemented.

All **65 scoped research tests**, Ruff and whitespace checks passed. Initial
default whitespace checking flagged the status file's preserved CRLF endings;
the file retains those endings and passes with `cr-at-eol`. No historical
artifact was reformatted. Production was unchanged and its full suite was not
rerun for this research-only change.

[Audit 006](CHECKPOINT_AUDIT_006.json), run from clean `71638f6`, verifies:

- All four checkpoint-012 payloads reproduce exactly from recorded source
  `2d350c7af991bb99fafc3a4e1a75efd0b59a4dad`.
- The original 345 frozen files are byte-identical; the additional integrated
  artifact-preservation guard passes.
- Source/restriction receipt bindings and preferred-edition evidence references
  validate. No new separate source check is claimed.
- New changes stay within the research continuation and active pointer; the
  largest tracked continuation file is 1,651,240 bytes.

Replay uses retained private source/provider caches, not a cache-free fresh
clone. The checks are provenance and workflow validation, not independent
statistical review or proof of scientific eligibility.

## Actual remaining dependency

The three existing source actors were resumed ordinarily after the previously
reported reset. Actor A initially confirmed availability, then reported the
same service limit as B and the original checker. The error says 2:36 AM but
does not provide a reset date/timezone. No reset deadline is inferred. No model,
account or actor was substituted, and no retry loop was used.

No new completed foreign-check receipt or source fact was released. Existing
checked method coverage remains 83 works; provider drafts do not increase it.
The provider-A additional005/006 manifests exist and match its reported hashes
`02396adba48ba4801f8950ec8a967b105c1097b182d5afa2bca93ec95d645e08`
and `31144651579f2671720402b4be4bea648713222d0849796702e4ed213ab652ba`.
Their pending separate checks remain necessary. Publisher additional007 has
partial drafts, not a completed four-work checked release.

Resume the same authorized roles when actually available: check additional005/
006/008 input-language evidence, complete/check additional007 publisher methods,
resolve the actual provider-B W0124 correction, then continue the reserved
cross-checks and remaining original inventory. Unchecked drafts remain in the
ignored cache. No new methodological approval or reviewer-setup cycle is needed
for this work; unavailable separate source checking is a genuine dependency.

There was no discovery refresh, paper draw, six-paper assignment, human outcome
sheet access or B2 extraction. FPR-001 remains open and production certification
behavior is unchanged. Complete-frame approval is still required before sampling.
