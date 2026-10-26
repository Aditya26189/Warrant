# B1 recovery delivery recheck, 22 October 2026

Status: **FRAME_BLOCKED / B2 NOT_AUTHORIZED**. This is a custodian-side receipt
and handoff clarification. It is not an independent eligibility return.

## Received report and unavailable return bytes

The user supplied a provisional reviewer report in the conversation. It reports
372 retained works, 389 memberships, five exact all-version sentinel exclusions,
367 unresolved works and no confirmed eligible works. It explicitly disclaims
completed scientific eligibility adjudication and reviewer-freshness attestation.

The report names an eight-file return ZIP with SHA-256
`74ee6fbac2a914a9a89f0f5b77a3927d1622d959d920717df47c6a01338dfe24`.
That archive and its named new component files were not located in Downloads or
the recent supplied attachment directories. The archive's bytes, manifest,
evidence references and reported integrity checks have therefore **not** been
verified by the custodian. No archive has been reconstructed from the pasted
report. The four earlier provisional files remain preserved in the previous
recovery record; they are a different return.

The reported 828 method facts are consistent with 549 original semantic facts,
278 recovery facts and the original finite-language clause. The 938 conditional
follow-ups are described as provider-flagged routing leads. They do not establish
938 independently adjudicated evidence deficiencies or authorize treating every
provider gap as a fresh scientific request. No new source retrieval was started.

## Local original-wrapper verification

[LOCAL_TRANSFER_RECHECK.json](LOCAL_TRANSFER_RECHECK.json) records a fresh check
at clean source commit `28694571d1791d4e3d7b200e8bbb8863a5596c92`.

The authentic original wrapper is present both in the repository and as
`C:\Users\LawLight\Downloads\REVIEWER_RECOVERY_TRANSFER.zip`. Both files are
byte-identical to the committed Git blob:

- Length: 1,229,861 bytes.
- SHA-256: `d105eed48c37e6532776060b3aec4ab70ece3cad885d1555ce08d54c89cf5142`.
- Seven unique flat entries and ZIP CRC: PASS.
- Fresh extraction of the hash-matched Downloads copy, followed by the actual
  unchanged `python -I verify_recovery.py`: PASS.
- All three original, unmodified component verifiers: PASS.
- Controlled supplement: 367 requested works, 384 memberships, 1,852 criterion
  responses, 278 new method facts and 549 original semantic facts: PASS.
- Original frozen inventory: 372 works and 389 memberships. Exact locked
  all-version sentinel matches are W0053, W0181, W0199, W0224 and W0300.

The first sandboxed invocation failed on Windows temporary-directory
permissions. The subsequent fresh-extraction check passed with sandbox
escalation; no verifier, original archive or expected digest was modified.

Documentation and scope checks passed: JSON/gate consistency, file sizes,
UTF-8/LF encoding, whitespace, three relative links and byte identity of all
280 previously committed B1 files. The two new files are research documentation
and a local verification receipt. Unchanged production tests were not rerun.

These checks authenticate the custodian's local files. They do not establish
which files reached the reviewer, execution in that reviewer environment,
reviewer independence, preferred-version decisions or eligibility completion.

## Remaining external dependencies

1. The recipient must actually receive the original wrapper, verify its
   separately supplied outer digest, extract it and run the wrapper verifier.
   Upload the ZIP itself; loose components do not establish its outer receipt.
2. The reviewer must report the true status of their original A04 intake and
   permitted-evidence history. The pasted report explicitly says a genuine
   original reviewer-freshness attestation cannot currently be made from that
   conversation. Receiving the ZIP cannot retroactively establish freshness.
   If the required independence cannot truthfully be established, the user must
   resolve the reviewer/process choice prospectively before a final independent
   return can be accepted.
3. The actual new provisional return archive must be supplied before its bytes
   can be preserved and mechanically validated. Its pasted hash alone is not
   an authenticated return.
4. An authentic independent reviewer must complete the locked scientific
   eligibility, identity and version review, retaining specific unresolved
   cases where needed. The frozen final return must be verified before any
   historical-decision reconciliation or final frame approval.

No historical screening comparison, eligibility draw, assignment, outcome
extraction, B2 activity, discovery refresh, production change or merge occurred.
All earlier protocol locks, archives and frozen research artifacts are preserved.

## Recipient message, sent only with the original ZIP

Do not send this custodian report or repository history to the reviewer. Attach
only the unchanged original `REVIEWER_RECOVERY_TRANSFER.zip` and use:

> The actual recovery ZIP is attached. Before extraction, verify SHA-256
> d105eed48c37e6532776060b3aec4ab70ece3cad885d1555ce08d54c89cf5142
> and length 1,229,861 bytes. Extract it into an empty directory and run
> `python -I verify_recovery.py`. Record actual receipt and verification.
> State truthfully whether your original A04 intake and reviewer independence
> can be attested; do not reconstruct or backdate an attestation. If that
> requirement remains unmet, preserve the provisional return and report the
> process blocker. Otherwise continue the authorized independent review using
> only the locked restricted evidence and rules. Provider availability flags
> are not scientific eligibility judgments. Freeze and hash the actual return
> and receipts. Do not access repository history, prior custodian judgments,
> unrestricted findings or the human outcome sheet. Do not draw papers,
> extract outcomes or begin B2.

The original [transfer instructions](../A04_RECOVERY_TRANSFER_INSTRUCTIONS.md)
and [recovery report](../A04_RECOVERY_REPORT.md) remain unchanged.
