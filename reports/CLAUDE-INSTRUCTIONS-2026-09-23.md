# Claude repair instructions after the independent main review

Issued 23 September 2026. Review baseline: `main` at
`cc1904e2215e1c6a85847125aef8997a2e0caac6`.
Evidence: [PROJECT-REVIEW-2026-09-23.md](PROJECT-REVIEW-2026-09-23.md).

Your chain repairs, strict parsing integration, release protocol 2 and
documentation improvements are preserved. The next work is to close the
reproduced customer-operation and correctness failures below. Do not repeat the
old integration or start another broad feature sprint.

## Start and coordination

1. Read current `AGENTS.md`, `CLAUDE.md`, `docs/SPEC.md`, `docs/TASKS.md`,
   `docs/CONTRIBUTING.md`, [COORDINATION.md](../COORDINATION.md), and the shared
   board. Use the original checkout as the board root from every worktree:

   ```shell
   python -m controlplane.coordination --root "SHARED_CHECKOUT" read --json
   ```

   Replace SHARED_CHECKOUT with its actual absolute path. A worktree's own board
   does not communicate with the other session.
2. Inspect Git and post your actual branch, full HEAD, first task and intended
   paths; claim paths before edits. These are requested assignments, not a claim
   that another agent has accepted or begun them. Keep distinct session names.
3. Work from current main in a new worktree. Do not reset, clean, stash, switch
   branches in, or delete the founder's original dirty checkout. The old Codex
   integration merge and partially edited grouped branch are not the baseline.
   Read them only for useful ideas; do not merge unfinished work blindly.
4. Commit small logical changes with named staging. Preserve line endings. Keep
   contract changes with code. Append decision rationale before methodological
   changes; never rewrite existing entries. Recheck the board and log before
   allocating a number: 203 was next at the review baseline, not reserved here.

## Work package A: make the wheel usable

**Claude's first implementation task.** Own packaging, installed resource loading
and wheel workflow tests. Claim exact paths after inspection; likely
`pyproject.toml`, config/CLI resource resolution and CI/package tests.

- Include `controlplane.sampling` and audit other customer runtime imports
  against actual wheel contents. Avoid pulling the research stack into the
  customer dependency set to hide a packaging omission.
- Supply supported default configuration as an installed resource and load it
  without assuming a repository root, current directory or source checkout.
  Preserve an explicit customer config override.
- Build a wheel, install it in the minimal supported environment, change to an
  unrelated directory and run the installed entry point. Run successful and
  refused certification, ordinary and second-label inputs, plan, recheck, chain
  verification and release register/evaluate/verify. A refusal retains its
  documented result exit code. Version/help/import checks alone are insufficient.
- Test both CI Python versions and the advertised minimum (metadata says Python
  3.10+, while CI uses 3.11/3.12), or deliberately narrow compatibility metadata. Record the exact wheel digest and
  source commit. A source or editable install is not this acceptance check.

Commit implementation and meaningful regression coverage, then publish the
tested commit for independent review. This is a product release blocker even
though existing source tests pass.

## Work package B: correct grouped inference

**Coordinate a separate statistical owner before editing protected code.** This
package changes inferential behavior, so record its method explicitly and have
someone other than the implementer review it. Do not silently bypass the local
protected-file rule for `validation/stats.py`.

- Fix R2: a degenerate grouped bootstrap must never become a row-level binomial
  interval. Preserve the independent sampling unit and state the estimand.
  Withhold unsupported inference with a reason if a justified method is absent.
  Do not mechanically replace row counts by group counts for arbitrary mixed
  groups; that is a different claim requiring justification.
- Add the 60-negative/four-positive-group counterexample. Replicating every row by the same factor while preserving group membership
  must not manufacture stronger precision or recall evidence. Cover
  boundary zero/all events, mixed groups, group sizes and valid ungrouped controls.
- Implement already-preregistered decision 201 for grouped reviewer agreement:
  actual group IDs; EXACT descriptive reviewed-pair statistics; null population
  interval endpoints; `interval_computed=false` and reason; reviewed pair count
  and distinct groups represented among those reviewed pairs.
- Keep ungrouped agreement outputs unchanged; withhold second-review dispute
  extrapolation for grouped inputs while preserving supported whole-group
  primary-label sensitivity ladders. Test undefined kappa, absent second labels and unequal reviewed group
  sizes through both certify and recheck renderers.
- Update SPEC, INPUT, LIMITATIONS and PILOT-PROTOCOL to the implemented behavior.
  A preregistration is not a completed fix. Do not regenerate scientific scores
  merely to make a changed estimator match old numbers.

## Work package C: lifecycle and chain integrity

**Claude may take this after A, with disjoint ownership from B.** The precedence
repair touches recheck code also used by grouped inference; coordinate that file
and integration order before editing it.

- R3: aggregate independent findings in severity order. STALE from an inconclusive
  FPR exceedance must not suppress REVOKED drift. Test the exact report fixture,
  ordinary and chained output, attempted subsequent continuation, and verification
  of a historical affected sequence. Preserve valid legacy histories where their
  status semantics actually justify them.
- R4: serialize the whole per-warrant head transition. Head validation, immutable
  record publication and head advancement need transaction/recovery semantics,
  not just exclusive output filenames. With concurrent starts or continuations,
  only a declared fork may create a second branch. Test distinct output names,
  rejected-writer state preservation and interruption recovery.
- R6: offer a strict integrity policy for modern use. Missing seal means unsealed
  or unknown integrity; it does not prove historical origin. Preserve explicitly
  requested legacy inspection without presenting it as full integrity assurance.
  Test seal removal plus an edited field, retained-seal edits, proper sealed
  controls and valid legacy records. Checksums remain different from signatures.
- R7: validate outer JSON object shape and numeric representation before arithmetic.
  Cover `[]`, null, strings, booleans, zero, negatives, NaN and oversized integers
  for applicable fields, including release registration numeric criteria
  (`release/contract.py:78`). Return documented input errors or verifier findings;
  do not change the verifier's normal findings exit behavior merely to satisfy
  a mistaken test.
- Resolve the already-known unchained-recheck behavior after chain revocation.
  Make the chosen relationship explicit and visible; a standalone VALID result
  must not silently imply the old revoked lifecycle was restored.

For each repair, publish the source commit and executed acceptance checks.
Independent review is still required even after a full suite passes.

## Work package D: calibration and evidence handoff

- R8: carry actual reference sample size into PSI noise calibration. Validate
  unequal old/new sizes and define explicit legacy behavior when size is absent.
  Do not assume the current size was also the historical size.
- R9: correct EVIDENCE-HANDOFF. Sharing a scored file does not bind thresholds or
  methods. Only threshold-independent descriptive agreement can be attached
  generically. Compute and identify operating-point sensitivity for the actual
  release threshold/protocol before representing it as evidence for that release.
- Plan one versioned customer-record binding for identity, scope, source evidence,
  fixed operating point, criteria, label meaning, issue/expiry and parent linkage.
  Keep absent fields visibly absent until implemented. Do not grow another
  parallel record family to avoid reconciling the existing two.
- Correct broad README and NEXT-STEPS claims that go beyond these records.
  Source gates do not prove installed operation or resistance to seal stripping.
  Competitor existence and commercial demand claims need evidence, not rhetoric.

## Existing protected runtime defects and audit gaps

Keep the legacy FPRMonitor mixture-cap defect, native Rego undefined-result
abort and PSI epsilon mismatch visible. Assign a bounded repair owner under the
local protected-code rules; do not call them fixed because the customer chain
uses a different implementation. For the monitor, preserve the stated mixture
statistic using stable arithmetic and test its stopping rule independently.

The decision archive is correct today, but the tests do not validate its scoped
citations or hashes. Extend that audit against the metadata actually merged on
main (embedded Markdown), not the abandoned sibling-JSON design. Test invalid
scoped numbers, misleading suffixes and modified archived content without
requiring a full Git history in a source archive.

## Completion gate and reporting

Before handing off each package, inspect the diff, run focused regression checks
and report the real exit codes. At an integrated checkpoint:

1. Commit implementation and required contract changes.
2. Refresh generated collection counts only from a clean source commit if the
   count changed; commit artifacts separately with before/after values.
3. Run the complete suite, configured lint, documentation/citation checks,
   installed-wheel customer journey, and clean-clone source gate. Keep raw
   summaries, exit codes and exact source/wheel identities.
4. Distinguish collected, passed, expected failures and skipped reproduction tiers.
   Do not overwrite expected scientific outputs or suppress failing cases to
   obtain a green gate. A failed check is evidence to investigate.
5. Post remaining limitations and release path claims when work is handed over.

Use a checkpoint message with: branch/full SHA; owned paths; before/after behavior;
commands and exit codes; independently reproduced versus externally reported
results; open findings; next owner. Never post status on another agent's behalf.

The commercial task runs alongside these bounded repairs: prepare one recurring
buyer decision, its existing process, measured labelling/integration effort and
an explicit repeat-use/payment test. Do not invent users, pilots or willingness
to pay. Prepare materials locally; no outreach, push, deployment or paid service
is authorized by this repair brief. Defer dashboards and broad integrations
until a real buyer need justifies them.
