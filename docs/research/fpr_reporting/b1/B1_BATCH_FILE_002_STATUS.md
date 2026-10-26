# Supplied metadata file: complete receipt, partial method review

19 October 2026. **FRAME_BLOCKED_AWAITING_REMAINING_DOMAIN_METHOD_REVIEW**.
The user-named `WARRANT_B1_CONSOLIDATED_METADATA_ANSWERS_PARTIAL_2026-10-18 (1).json`
was found in the shared repository root. Its 207101 bytes are preserved unchanged
in [HUMAN_BATCH_RESPONSE_002.json](HUMAN_BATCH_RESPONSE_002.json), SHA-256
`271d4347ac7561cd7840176a8ac17bd2f4c15a46a986b3382db32ba9b9c5c627`.
The two named Downloads copies have the same bytes/hash. The root source is not
edited or staged. [Receipt002](HUMAN_BATCH_RECEIPT_002.json), committed with the
raw copy at `0527f1e`, records the actual receipt time and 19 October local date;
the filename's 18 October date is not used as a retrieval or preregistration time.

The complete JSON contains all 177 original question IDs and both identity
answers. Every identity/title/captured-source/required-evidence field matches
the original request. Therefore the earlier missing transport tail is resolved.
However, this is explicitly a partial method review: 19 INCLUDE answer rows,
2 EXCLUDE, and 156 UNCLEAR. Of the unclear rows, 144 say the method review is not
completed; 12 report partial inspection. None is represented as a completed
eligibility review. No new answers to D01/D02 or Q001 are needed: they repeat
prior accepted decisions without contradiction.

The 19 INCLUDE rows cover 18 distinct works because Q004/Q165 are the same
InjecGuard/PIGuard work. Q001 Palisade was already included. The
[new projection](a02-human-batch002/SCREENING_LEDGER.json) therefore adds
**17 domain INCLUDE and 2 EXCLUDE**, retaining all source-version locators and
limitations. These are attributed user adjudications, not independently verified
Codex full-text findings. Direct English evidence, indirect support, mixed-language
scope and training-versus-evaluation distinctions remain visible in each record.
A reviewed version is not automatically the final cutoff-selected version.

New resolved decisions (original question IDs; aliases grouped as one work):

| Questions | Work | Domain decision |
| --- | --- | --- |
| Q004, Q165 | `doi:10.18653/v1/2025.acl-long.1468` | INCLUDE |
| Q006 | `arxiv:2501.15145` | INCLUDE |
| Q012 | `arxiv:2504.11358` | INCLUDE |
| Q017 | `arxiv:2506.06384` | INCLUDE |
| Q021 | `arxiv:2507.05630` | INCLUDE |
| Q029 | `arxiv:2508.20890` | INCLUDE |
| Q036 | `arxiv:2510.01354` | INCLUDE |
| Q040 | `arxiv:2510.14005` | INCLUDE |
| Q043 | `arxiv:2510.22628` | EXCLUDE |
| Q048 | `arxiv:2512.12583` | INCLUDE |
| Q052 | `arxiv:2601.12359` | INCLUDE |
| Q056 | `arxiv:2602.03792` | INCLUDE |
| Q086 | `arxiv:2605.00460` | INCLUDE |
| Q093 | `arxiv:2605.18918` | INCLUDE |
| Q096 | `arxiv:2605.26999` | INCLUDE |
| Q101 | `arxiv:2605.30837` | INCLUDE |
| Q114 | `arxiv:2606.19235` | EXCLUDE |
| Q155 | `arxiv:2610.08571` | INCLUDE |
| Q171 | `doi:10.18653/v1/2026.acl-industry.127` | INCLUDE |

Current state: **372 work records, 23 domain INCLUDE, 193 EXCLUDE, 156 UNCLEAR**.
The existing D01/D02 crosswalk and all 389 source metadata records are unchanged.
The 500-work cap still passes. No complete eligible frame exists: the156 unclear
works may qualify, so sampling only the reviewed subset would alter the approved
frame. Having more than ten domain inclusions does not authorize such a draw.

[Remaining combined review queue](a02-human-batch002/REMAINING_METADATA_REVIEW.md)
and [blank answer file](a02-human-batch002/PENDING_METADATA_ANSWERS_BLANK.json)
contain only the156 unresolved original question IDs, grouped as partial
inspection12 and not yet method-reviewed144. The supplied prior evidence is
preserved; answer cells remain blank for further source-supported review. This
is candidate metadata screening, not the selected-six independent outcome sheet.
No missing transport rows or identity questions remain. The next required input
is method/source adjudication of the unresolved domain facts, in one combined
batch; further UNCLEAR responses remain uncertainty rather than exclusions.

[Manifest](a02-human-batch002/MANIFEST.json) binds the raw/receipt, original
protocol lock, prior projection/crosswalk and new files. Validation covers exact
source-copy bytes, all177 IDs, consistent alias decisions, retained limitations,
exactly19 work-status changes, preserved prior decisions,23/193/156 counts,
all156 pending IDs and blank fields, history/input/output hashes, source mapping,
links, scope, staged bytes, sizes and whitespace. Parser/production tests were
not rerun for annotation-only changes. No new source retrieval, PDF/outcome
reading, version/date/access reconciliation, eligible-frame freeze, draw,
six-paper assignment, FPR/sample/false-positive extraction, assurance classification,
B2, production changes, frozen-artifact rewrites or merge occurred. FPR-001 stays
OPEN. Scoped work is committed and pushed to the authorized research branch;
final commit hashes and remote verification are reported at delivery.

Subsequent user steering,19October2026: the user requested Codex perform its own
analysis and complete the work. This import snapshot remains the record of the
supplied file. A prospective reviewer-responsibility amendment will be recorded
before assistant-led primary method adjudication; no missing answer is inferred
from the trust statement, and B1/B2 stage boundaries remain distinct.
