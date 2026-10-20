# A04 controlled-evidence handoff report

Date: 20 October 2026. Actual UTC retrieval and check timestamps are retained in receipts; earlier actions dated 19 October have not been relabeled.

## Current gate

**B1_EVIDENCE_READY_FOR_REVIEW**: a verified, consolidated restricted evidence supplement is prepared and pushed on the research branch. **FRAME_BLOCKED** remains the overall frame status: no authenticated independent eligibility return has been received locally, and no delivery by this run is recorded. No ten-paper draw, six-paper assignment or B2 extraction has run. `B1_FRAME_AWAITING_APPROVAL` is not claimed.

This is a partial-method evidence handoff for the unchanged arXiv/ACL-retrieved feasibility frame. It is not a completed eligibility frame, literature-representativeness claim, novelty finding or publication result.

## Work completed and coverage

The acquisition/restriction/receipt pipeline supports exact captured source identifiers, verified cache reuse, bounded official-host retries, source/paragraph/page hashes, neutral access exceptions and immutable records. All 389 memberships in all 372 works were attempted and processed. Original raw bodies and broader proposals remain in ignored custodian caches.

| Stage | Unique works | Source memberships / facts | Meaning |
|---|---:|---:|---|
| Frozen inventory and acquisition attempts | 372 | 389 memberships | Every frozen member retained |
| Primary body available and hash-verified | 370 | 387 bodies | 155 verified raw-cache reuses; 232 new retrievals |
| Exact captured version matched in body | 347 | 347 memberships | 344 HTML self-links; three PDF version headers |
| Bounded primary method context inspected | 347 | 347 memberships | Separate checker context; PDF pages visually inspected |
| Generated and release-checked method paraphrases | 320 | 549 facts | All 549 pass source/locator/schema/content replay |
| Final protocol-preferred version independently settled | 0 | 0 | Captured-version proof does not settle version preference |
| Delivered to authenticated fresh reviewer by this run | 0 | 0 | Transfer is prepared, not recorded as performed |
| Independent eligibility judgments received locally | 0 | 0 | All decision fields remain null |

The initial finite-language supplement also retains one literal procedural clause. The 632 broader original text proposals are not transferred. The 549 new paraphrases are separately source-context checked facts; they are not approvals of the broader text. Final outgoing fact quarantine is zero, which does not mean every work has complete evidence.

All 372 works have completed source-restriction records. Fifty-two works have no approved method paraphrase: two lack accessible exact-revision bodies, 23 lack sufficient captured-body version proof, and 27 retain bounded-context/separation limitations. These are evidence states, not exclusion decisions. Even the 320 fact-bearing works require independent checking of remaining eligibility, baseline, language, date, version, sentinel and study-unit questions. The work-level coverage and unchanged base exception/crosswalk files retain those boundaries.

## Actual roles and independence

The original exposed custodian is `codex-fpr-b1-evidence-20261019_EXPOSED_CUSTODIAN`. It engineered and mechanically validated the transfer; it made no new eligibility decisions.

Three actual source-restriction checkers received separate tasks with `fork_turns=none`, restricted input allowlists and no inherited chat. Their final artifacts and reports were received and hash-bound:

| Actor | Assigned works | Method-context memberships | Restricted facts |
|---|---:|---:|---:|
| `/root/a04_semantic_restriction` | 129 | 119 | 142 |
| `/root/a04_semantic_restriction_02` | 124 | 120 | 194 |
| `/root/a04_semantic_restriction_03` | 119 | 108 | 213 |

Their filesystem was shared; OS isolation is explicitly not claimed. They checked source restrictions, including local paraphrase rereading, and were not appointed as the A04 independent eligibility reviewer or statistical reviewer. Their full assigned scope includes explicit blocked records, not a claim of exhaustive method evidence for every source. Quota interruptions are preserved; checkers 02 and 03 resumed and sent genuine final reports. Checker 02 confirmed its pre-interruption manifest unchanged.

The separate fresh-reviewer conversation is reported by the user. Its authenticated intake/return is not available locally, so no new eligibility-review completion, freshness attestation or delivery event is fabricated. Original judgments, A03 exposure material, source displays, custodian reports and the private human outcome sheet are absent from the transfer. The A03 deviation remains permanent history. No new exposure-based sentinel exclusion was created.

## Evidence transfer and hashes

Transfer only [CONSOLIDATED_RESTRICTED_EVIDENCE.zip](a04-semantic-evidence-v1-20261020/CONSOLIDATED_RESTRICTED_EVIDENCE.zip) to the existing fresh-reviewer conversation. It already has the original intake according to the user report. Keep that original intake separate; this new ZIP contains the earlier evidence supplement, not the intake archive.

- Consolidated archive: 444,516 bytes; SHA-256 `8158e43ee8ad8c55854aab59c526b979b7e5a89b23f804eb65b408b384621a71`.
- Unchanged nested base supplement: SHA-256 `066c27ae28ad941ea9ebf963f3fc5d854b2bcd39d1fb060a16b52b5cc4294c08`.
- Separate original intake: SHA-256 `48c903779bda205c2af6231da92cca8b70e6ba9755cfa175f526c107e23e7290`.
- Frozen all-work request inventory: SHA-256 `3ff6a1bf1c9959a219ec80e89754acd0557123d4399bbd1a7edffca278925ae0`.
- Actual checker completion/snapshot receipt: SHA-256 `716afea08821983e605d9d97dda8ff7c3aafaf31b3cd674efd02add13af29dd9`.

The nine-file outer archive includes strict method facts, receipts, coverage, neutral restriction exceptions, role receipts, a manifest and an offline verifier. Its unchanged nested base has 15 files covering bibliography/access/version evidence, all work/member crosswalks, sentinel matching and blank forms. No full PDF/HTML bodies, page renders, quarantined proposals, historical decisions or local render paths are transferred. The three exact-version PDF sources have reproducible visual-page/text hashes; images remain in the ignored checker cache.

After validating the archive SHA, extract into an empty directory and run `python verify_semantic.py`. Extract `BASE_EVIDENCE_SUPPLEMENT.zip` into a separate directory and run `python verify_evidence.py`. Do not place that extraction inside the outer directory, whose allowlist is strict. Preserve any actual reviewer work rather than replacing it with blank forms.

The [restricted manifest](a04-semantic-evidence-v1-20261020/restricted/MANIFEST.json), [custodian audit](a04-semantic-evidence-v1-20261020/CUSTODIAN_RELEASE_AUDIT.json), [checker snapshot](a04-semantic-evidence-v1-20261020/CHECKER_COMPLETION_RECEIPT.json), [test log](a04-semantic-evidence-v1-20261020/SCOPED_TESTS.log) and [verification summary](a04-semantic-evidence-v1-20261020/VERIFICATION_SUMMARY.json) contain exact hashes, times and provenance. Send the ZIP, not these custodian-side records.

## Validation and corrected failures

All 88 scoped tests pass: acquisition/restriction 26, original A04 handoff 11, finite/access/transfer 19, semantic-return/release 32. Lint and syntax pass for the 11 new research Python files. Production tests were not rerun because no production files changed.

Meaningful checks cover incorrect source versions, modified bodies/locators, protected source containers, missing/duplicate receipts, malformed/truncated bodies, interrupted checkpoints, UTF-8 determinism, unexpected archive files, rehashed outcome/history injection, nonblank forms, false role/delivery claims, and the distinction between intake and actual method-context inspection. All 372 assigned current records and frozen checker manifests reconcile. Both standalone offline verifiers, ZIP CRC/allowlists, exact Git-blob/archive correspondence and deterministic ZIP repacking pass. All outgoing outer text files have LF line endings. Full-frame replay status is recorded in the verification summary.

Initial engineering failures were corrected and preserved in the execution log: ACL metadata needed an official PDF URL fallback; broad catches failed initial lint; a PowerShell stderr-redirection wrapper returned a misleading exit code; template placeholders failed lint; a structural PDF page number hit the prose digit gate; checker locators initially used one-based rather than zero-based HTML indices; actual checker metadata formats needed a narrow adapter; several prose triggers required source-grounded checker revisions. The first complete operational rollup also included intake/version checks as method review; explicit source receipts corrected it from 357 works/363 memberships to 347/347. No failed or preliminary return is represented as having passed originally.

Runtime: Python 3.12.10, BeautifulSoup 4.12.3, PyMuPDF 1.26.7, pypdf 6.9.2, ruff 0.16.6. A downloaded PDF or keyword filter alone was never accepted as restriction verification. The completed separate context checks and reproducible source bindings form the evidence basis; remaining limitations remain explicit.

## Frozen boundaries and genuine blockers

All 148 B1 files present at checkpoint `d2b760df052c138401964e95f456c944394501ff` remain byte-identical. All scoped changes are under `docs/research/fpr_reporting/b1/`; production code, frozen experiments, protocol rules, discovery captures, seeds, the 500-work cap and all 65 sentinel identifiers remain unchanged. No merge, new discovery, statistical behavior change or research publication occurred. FPR-001 remains separately OPEN.

The original, A02, A03 and A04 protocol locks verify with hashes respectively:

- `7a3c73d465721fb2ea177c53bdc936e614ec5b504c6fb1fc0ef65ff7acc86f42`
- `a8b736803da62bd399644abcc1f2ffb0a767b983560f16629ce16cf5d84147c7`
- `0c11c681b6f08fdf3a1e34a26675f157be79e757ba6d9f55cd7f7cc85689f4f0`
- `00856fbdcc796ac4d04b52e67de46c79fdc8bb5b9d26115ef48d3c46c4cafbaf`

The unavailable captured revisions are arXiv:2410.21337v2 (Q002) and arXiv:2508.02961v2. Official histories record withdrawal markers; exact official HTML/PDF and same-revision mirror attempts did not obtain bodies. No earlier revision was substituted. Forty other memberships have body transport evidence without sufficient captured-version proof. Preferred-version selection remains independent work, not an automatic inference from successful access.

D01 remains one InjecGuard/PIGuard work; D02 remains two distinct MCP works. Q026/Q153 whole-document identities and study-overlap questions remain for independent adjudication. Q007's historical judgment is withheld. StepGuard's potentially distinct identifiers remain conservatively excluded at their existing sentinel scope without an invented alias mapping.

Remaining dependencies are actual transfer, fresh-reviewer attestation and an authentic frozen all-work eligibility return, plus any additional controlled source/version evidence that reviewer requires. Custodian reconciliation and historical comparison can occur only after that genuine return is frozen and committed. A complete reconciled frame then requires the user's explicit approval before any draw. Current evidence gaps are not silently converted to exclusions.

## Local commits and push

Branch: `research/fpr-stage-a-20261017`. The following scoped commits are pushed to origin; final report/replay documentation follows in its own commit. The final response gives that documentation commit and remote-ref verification. The consolidated archive is frozen at `174e9f03cdd499d928c61b87a485013b5d660b5a`; its generation used clean `a9533738f1c3536c29246871e6456676d8acb0f3`.

| Commit | Logical milestone |
|---|---|
| `bb2c5f639e2433cec0f7ca19c32bdd9d838a6c01` | feat(research): build resumable controlled source provision |
| `805d398708820e9071c76da1398026dc621f6796` | docs(research): freeze complete A04 evidence request inventory |
| `33829a31eb3f5425ab00b04367aaebf236fa6f9d` | feat(research): validate finite method clauses for restricted transfer |
| `da225335c93682441d0da72828445eafcf41b7ce` | docs(research): preserve exact-revision access follow-ups |
| `1296c86d469f69d3704d027c981c7b0596c09f63` | docs(research): freeze complete partial primary-evidence supplement |
| `493aa9e0e7b7d0919549a66376b82a8e9e75f17a` | feat(research): validate separate restriction returns for transfer |
| `6259ed5f60d37f57f6d0f4de366b34cc101f3018` | fix(research): normalize attested restriction metadata variants |
| `e9e10d0429c91f4f20680878a129c24826da9aac` | fix(research): count only attested method-context checks |
| `a9533738f1c3536c29246871e6456676d8acb0f3` | docs(research): freeze completed source-checker receipts |
| `174e9f03cdd499d928c61b87a485013b5d660b5a` | docs(research): freeze consolidated restricted source evidence |

## Minimal reviewer message

> Verify the supplied archive SHA, then run both offline verifiers. Preserve the original A04 intake and use only the restricted evidence to independently review all 372 works under the unchanged rules. Record uncertainty and request missing controlled facts through the receipt schema. Return your actual attestation, provenance and a frozen hash-bound eligibility return. Do not consult the repository/history, extract outcomes, sample papers or start B2.

STOP_GATE_REACHED
