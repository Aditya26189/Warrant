# Harbor cancellation correction — 23 October 2026

**Gate: the demonstrated cleanup defect is corrected in the tested Linux/WSL Docker scope. P2 remains closed and unchanged; no scientific-superiority or production claim is added.**

[Evidence] The actual pinned Harbor runtime was exercised with an active sleeping agent, a real interruption, and an active separate verifier. The runner itself removed remaining owned resources. No after-the-fact harness cleanup supplied the passing runner result. A foreign running container, shared external network/volume and pre-existing base image survived each cancellation. The harness removed only its own controls after validation, with ownership rechecks and absence verification.

| Check | Run status | Reward | Cleanup | Removal requests | Environment instances | Seconds |
|---|---|---:|---|---:|---:|---:|
| 001 / timeout | TIMEOUT | None | VERIFIED_ABSENT | 4 | 1 | 76.407 |
| 001 / interruption | INTERRUPTED | None | VERIFIED_ABSENT | 4 | 1 | 33.545 |
| 001 / verifier-interruption | INFRASTRUCTURE_ERROR | None | VERIFIED_ABSENT | 0 | 2 | 60.703 |
| 001 / reference | COMPLETED | 1.0 | VERIFIED_ABSENT | 0 | 2 | 70.726 |
| 002 / verifier-interruption | INTERRUPTED | None | VERIFIED_ABSENT | 4 | 2 | 62.324 |

Cancelled trials retain TIMEOUT or INTERRUPTED and have no top-level semantic reward. The normal supplied reference used the unchanged pinned session-window-debug task and full verifier; it validates that the new ownership adapter still permits ordinary execution. It is a compatibility check, not another grader-discovery result.

## Implementation and ownership boundary

The [runner](../experiments/grader_poc/run_trial.py) assigns a fresh UUID and requires an empty initial ownership inventory. The [environment adapter](../experiments/grader_poc/harbor_environment.py) uses Harbor's supported custom-environment import path, because the pinned runtime drops ordinary run-level Compose overlays for separate verifiers. For each environment it resolves Compose configuration without creating resources, records an overlay, and labels containers, managed networks/volumes and built images. The original task and upstream source remain unchanged.

Built images receive unique tags and ownership labels. Managed network/volume names receive a per-invocation and per-instance namespace. Explicitly external resources and prebuilt images retain their references and are excluded from deletion. This can reduce cross-run built-image reuse and changes resource names; it does not change candidate or verifier source.

The [cleanup implementation](../experiments/grader_poc/harbor_resources.py) queries the exact owner label, reinspects every ID immediately before removal, removes containers before dependent resources, and never forces image deletion or invokes global pruning. Anonymous volumes associated with owned containers use Docker's container-removal semantics; the separately queried volume absence check covers labeled managed volumes. Shared external volumes are protected by Docker's named-volume semantics and the live preservation control.

The wrapper stops its owned process group, including Compose children that can outlive the parent. Cleanup uses bounded calls, an overall deadline and repeated empty inventories. Failures and intermediate actions are retained. A second catchable SIGINT is deferred during bounded cleanup; a cleanup error cannot be interpreted as absence. A normal grading result cannot become COMPLETED without verified cleanup. A cancelled run stays invalid even if a partial reward file exists.

## Validation and limits

[Evidence] 47 focused unit tests passed in the recorded WSL runtime at `2bff5f77bcd67d32189d504f75346986a129dce2`. Tests cover changed ownership, an existing ownership identity, daemon errors, removal failure, surviving resources, process-group termination and failure receipts. Source lint passed. Live trial source commits are recorded per attempt in the summary; the only runtime-validation change between batches corrects the disposable verifier fixture and adds selective replay. The runner implementation is identical across both batches.

Batch 001's separate-verifier check is invalid: its Dockerfile omitted the test-script copy, so it failed with RewardFileNotFoundError before reaching the intended interruption. It is retained above and in the archive, not counted as a passing interruption test. Batch 002 corrects the fixture and reruns only that affected check. The successful timeout, agent-interruption and reference checks were not selectively rerun. The validation CLI now returns nonzero for a failed batch.

The initial Windows test invocation encountered sandbox temporary-directory permissions; it did not establish test failures in the implementation. Using an explicitly writable temporary directory resolved that environment issue. A platform-specific unit fixture also needed a mocked POSIX signal constant when run on Windows. The retained WSL log is the final platform-matched result.

This is bounded verification, not a universal cleanup guarantee. Supported execution is Linux/WSL with the pinned local Docker/Harbor setup and trusted task definitions. Windows containers, privileged services, explicit container names and host-network services are refused. Non-public Harbor network-policy modes are outside the adapter's declared support. Ownership labels are operational metadata, not protection against an adversary who controls the Docker daemon or can forge labels. Host failure, uncatchable process death, daemon unavailability and indefinitely delayed daemon-side work cannot be resolved by a finite wrapper. Shared image layers and BuildKit cache are deliberately not pruned. Absence is established at the recorded checks; it is not a promise that arbitrary future processes cannot create resources.

The live cancellation checks target running agent/verifier phases, not every possible image-build failure. Unit tests cover command/daemon errors; live daemon failure and malicious task isolation were not tested. Independent human reproduction remains absent.

## Evidence and replay

The [summary](../experiments/grader_poc/cancellation/summary.json) and [manifest](../experiments/grader_poc/cancellation/manifest.json) bind 138 packaged payloads. Raw/packaged hashes distinguish path-redacted copies. The supplied P2 review is archived as review input, not independent reproduction evidence. All 235 original payloads, 57 hardening payloads and 527 P2 payloads were checked unchanged. The earlier phase reports remain historical records of their own tested code.

From a clean experimental checkout, the existing pinned Harbor virtualenv and Docker are required:

```sh
python -m unittest experiments.grader_poc.test_execution experiments.grader_poc.test_oracle experiments.grader_poc.test_reducer experiments.grader_poc.p2.test_p2 experiments.grader_poc.test_harbor_resources -v
python -m experiments.grader_poc.validate_cancellation --tb TB_REPO --harbor HARBOR_REPO --harbor-bin HARBOR_BIN --out FRESH_OUTPUT
```

The live command creates disposable fixtures and explicitly labeled preservation controls. Use a fresh output directory. It retains per-run ownership ledgers and outcomes. The ordinary run_trial entry point enables the ownership adapter automatically; direct use of upstream Harbor outside this wrapper is unchanged.

[Opinion] This correction removes the demonstrated operational blocker within the tested scope. It does not change P2's conclusion: no advantage over direct review or ordinary mutation testing has been demonstrated. Further scientific expansion needs a new explicit decision. Production integration, B1/A04 and the separate statistical-certification issue remain untouched. No merge, push or upstream change was performed.
