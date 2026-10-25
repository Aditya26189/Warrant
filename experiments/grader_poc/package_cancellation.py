"""Archive the bounded cleanup correction without changing prior evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from experiments.grader_poc.run_trial import file_hashes, git_output, write_receipt


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(raw_paths: list[Path], unit: Path, review: Path) -> dict:
    root = Path(__file__).resolve().parents[2]
    here = root / "experiments/grader_poc"
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit source before evidence assembly")
    preserved = {}
    for folder, manifest in (("results", "evidence-manifest.json"), ("hardening", "manifest.json"), ("p2/evidence", "manifest.json")):
        prior = json.loads((here / folder / manifest).read_bytes())["packaged_files"]
        for name, expected in prior.items():
            if digest(here / folder / name) != expected:
                raise ValueError("Earlier evidence changed: " + name)
        preserved[folder] = len(prior)
    batches = [(raw, json.loads((raw / "outcome.json").read_bytes())) for raw in raw_paths]
    latest = {}
    for raw, result in batches:
        for item in result["checks"]:
            latest[item["mode"]] = item
        if not all(item.get("absent") for item in result["control_removal"]):
            raise ValueError("Validation control cleanup failed")
    if set(latest) != {"timeout", "interruption", "verifier-interruption", "reference"} or not all(item["passed"] for item in latest.values()):
        raise ValueError("Latest required live validation did not pass")
    unit_text = unit.read_text(encoding="utf-8-sig")
    unit_count = int(re.search(r"Ran (\d+) tests", unit_text)[1])
    if unit_text.strip().splitlines()[-1] != "OK":
        raise ValueError("Unit test log does not end in OK")
    summary = {"source_commits": sorted({result["source_commit"] for _, result in batches}),
               "unit_test_source_commit": batches[0][1]["source_commit"], "archive_source_commit": git_output(root, "rev-parse", "HEAD"),
               "checks": list(latest.values()), "unit_tests": unit_count, "preserved_payloads": preserved,
               "batches": [{"name": raw.name, "result": result} for raw, result in batches], "independent_human_reproduction": False,
               "trials": []}
    for raw, check in [(raw, check) for raw, result in batches for check in result["checks"]]:
        name = check["mode"]
        trial_path = raw / name / ("outcome.json" if name == "reference" else "run/outcome.json")
        trial = json.loads(trial_path.read_bytes())
        task_arg = trial["command"][trial["command"].index("-p") + 1]
        task = Path("C:/" + task_arg.removeprefix("/mnt/c/")) if task_arg.startswith("/mnt/c/") else Path(task_arg)
        if file_hashes(task) != trial["task_hashes"]:
            raise ValueError("Recorded task bytes changed")
        cleanup = trial["resource_cleanup"]
        if not cleanup["verified_absent"] or not trial["task_unchanged"]:
            raise ValueError("Cleanup or task preservation failed")
        if name != "reference" and check["passed"]:
            observation = json.loads((raw / name / "outcome.json").read_bytes())
            if not observation["active_observed"] or not observation["controls_preserved"] or not observation["foreign_container_running"]:
                raise ValueError("Live observation/preservation control failed")
            if "reward" in trial:
                raise ValueError("Cancelled trial promoted a reward")
        if name == "reference":
            full_trial = (trial_path.parent / trial["trials"][0]["path"]).parent
            expected = file_hashes(task / "environment/app")
            expected.update(file_hashes(task / "solution/files"))
            if file_hashes(full_trial / "artifacts/app/app") != expected:
                raise ValueError("Collected reference candidate differs from declared source")
        actions = cleanup["actions"]
        summary["trials"].append({"name": name, "batch": raw.name, "passed": check["passed"],
                                  "source_commit": trial["source_commit"], "status": trial["status"], "reward": trial.get("reward"),
                                  "elapsed_seconds": trial["elapsed_seconds"], "cleanup": cleanup["status"],
                                  "cleanup_actions": len(actions), "cleanup_action_errors": sum(a["status"] == "ERROR" for a in actions),
                                  "environment_instances": len(list(trial_path.parent.glob("ownership/*.instance.json"))),
                                  "forced_process_stop": trial.get("cancellation", {}).get("forced", False)})
    out = here / "cancellation"
    out.mkdir(exist_ok=False)
    home = str(Path.home())
    posix = home.replace("\\", "/")
    wsl = "/mnt/" + posix[0].lower() + posix[2:] if ":" in posix else posix
    replacements = sorted({home, home.replace("\\", "\\\\"), posix, wsl}, key=len, reverse=True)
    copies = []

    def copy(path: Path, name: str) -> None:
        data = path.read_bytes()
        if len(data) > 10_000_000:
            raise ValueError("Oversized evidence file; do not stage")
        text = data.decode("utf-8-sig")
        for prefix in replacements:
            text = text.replace(prefix, "${HOST_HOME}")
        text = re.sub(r"/tmp/warrant-grader-poc-[0-9]+-venv", "${HARBOR_VENV}", text)
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode())
        copies.append({"path": name, "raw_sha256": hashlib.sha256(data).hexdigest(), "packaged_sha256": digest(target)})

    for raw in raw_paths:
        for path in sorted(raw.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                copy(path, "live/" + raw.name + "/" + path.relative_to(raw).as_posix())
    copy(unit, "unit-tests.txt")
    copy(review, "supplied-p2-review.md")
    copy(here / "results/TERMINAL_BENCH_LICENSE.txt", "TERMINAL_BENCH_LICENSE.txt")
    summary["packaged_payloads_excluding_manifest"] = len(copies) + 1
    write_receipt(out / "summary.json", summary)
    write_receipt(out / "manifest.json", {"copies": copies, "packaged_files": file_hashes(out),
        "redaction": "Host home and temporary Harbor virtualenv replaced; UTF8 BOM removed; raw hashes retained; __pycache__ excluded."})
    rows = "\n".join(f"| {r['batch'].rsplit('-', 1)[-1]} / {r['name']} | {r['status']} | {r['reward']} | {r['cleanup']} | {r['cleanup_actions']} | {r['environment_instances']} | {r['elapsed_seconds']:.3f} |" for r in summary["trials"])
    report = f'''# Harbor cancellation correction — 23 October 2026

**Gate: the demonstrated cleanup defect is corrected in the tested Linux/WSL Docker scope. P2 remains closed and unchanged; no scientific-superiority or production claim is added.**

[Evidence] The actual pinned Harbor runtime was exercised with an active sleeping agent, a real interruption, and an active separate verifier. The runner itself removed remaining owned resources. No after-the-fact harness cleanup supplied the passing runner result. A foreign running container, shared external network/volume and pre-existing base image survived each cancellation. The harness removed only its own controls after validation, with ownership rechecks and absence verification.

| Check | Run status | Reward | Cleanup | Removal requests | Environment instances | Seconds |
|---|---|---:|---|---:|---:|---:|
{rows}

Cancelled trials retain TIMEOUT or INTERRUPTED and have no top-level semantic reward. The normal supplied reference used the unchanged pinned session-window-debug task and full verifier; it validates that the new ownership adapter still permits ordinary execution. It is a compatibility check, not another grader-discovery result.

## Implementation and ownership boundary

The [runner](../experiments/grader_poc/run_trial.py) assigns a fresh UUID and requires an empty initial ownership inventory. The [environment adapter](../experiments/grader_poc/harbor_environment.py) uses Harbor's supported custom-environment import path, because the pinned runtime drops ordinary run-level Compose overlays for separate verifiers. For each environment it resolves Compose configuration without creating resources, records an overlay, and labels containers, managed networks/volumes and built images. The original task and upstream source remain unchanged.

Built images receive unique tags and ownership labels. Managed network/volume names receive a per-invocation and per-instance namespace. Explicitly external resources and prebuilt images retain their references and are excluded from deletion. This can reduce cross-run built-image reuse and changes resource names; it does not change candidate or verifier source.

The [cleanup implementation](../experiments/grader_poc/harbor_resources.py) queries the exact owner label, reinspects every ID immediately before removal, removes containers before dependent resources, and never forces image deletion or invokes global pruning. Anonymous volumes associated with owned containers use Docker's container-removal semantics; the separately queried volume absence check covers labeled managed volumes. Shared external volumes are protected by Docker's named-volume semantics and the live preservation control.

The wrapper stops its owned process group, including Compose children that can outlive the parent. Cleanup uses bounded calls, an overall deadline and repeated empty inventories. Failures and intermediate actions are retained. A second catchable SIGINT is deferred during bounded cleanup; a cleanup error cannot be interpreted as absence. A normal grading result cannot become COMPLETED without verified cleanup. A cancelled run stays invalid even if a partial reward file exists.

## Validation and limits

[Evidence] {summary['unit_tests']} focused unit tests passed in the recorded WSL runtime at `{summary['unit_test_source_commit']}`. Tests cover changed ownership, an existing ownership identity, daemon errors, removal failure, surviving resources, process-group termination and failure receipts. Source lint passed. Live trial source commits are recorded per attempt in the summary; the only runtime-validation change between batches corrects the disposable verifier fixture and adds selective replay. The runner implementation is identical across both batches.

Batch 001's separate-verifier check is invalid: its Dockerfile omitted the test-script copy, so it failed with RewardFileNotFoundError before reaching the intended interruption. It is retained above and in the archive, not counted as a passing interruption test. Batch 002 corrects the fixture and reruns only that affected check. The successful timeout, agent-interruption and reference checks were not selectively rerun. The validation CLI now returns nonzero for a failed batch.

The initial Windows test invocation encountered sandbox temporary-directory permissions; it did not establish test failures in the implementation. Using an explicitly writable temporary directory resolved that environment issue. A platform-specific unit fixture also needed a mocked POSIX signal constant when run on Windows. The retained WSL log is the final platform-matched result.

This is bounded verification, not a universal cleanup guarantee. Supported execution is Linux/WSL with the pinned local Docker/Harbor setup and trusted task definitions. Windows containers, privileged services, explicit container names and host-network services are refused. Non-public Harbor network-policy modes are outside the adapter's declared support. Ownership labels are operational metadata, not protection against an adversary who controls the Docker daemon or can forge labels. Host failure, uncatchable process death, daemon unavailability and indefinitely delayed daemon-side work cannot be resolved by a finite wrapper. Shared image layers and BuildKit cache are deliberately not pruned. Absence is established at the recorded checks; it is not a promise that arbitrary future processes cannot create resources.

The live cancellation checks target running agent/verifier phases, not every possible image-build failure. Unit tests cover command/daemon errors; live daemon failure and malicious task isolation were not tested. Independent human reproduction remains absent.

## Evidence and replay

The [summary](../experiments/grader_poc/cancellation/summary.json) and [manifest](../experiments/grader_poc/cancellation/manifest.json) bind {summary['packaged_payloads_excluding_manifest']} packaged payloads. Raw/packaged hashes distinguish path-redacted copies. The supplied P2 review is archived as review input, not independent reproduction evidence. All {preserved['results']} original payloads, {preserved['hardening']} hardening payloads and {preserved['p2/evidence']} P2 payloads were checked unchanged. The earlier phase reports remain historical records of their own tested code.

From a clean experimental checkout, the existing pinned Harbor virtualenv and Docker are required:

```sh
python -m unittest experiments.grader_poc.test_execution experiments.grader_poc.test_oracle experiments.grader_poc.test_reducer experiments.grader_poc.p2.test_p2 experiments.grader_poc.test_harbor_resources -v
python -m experiments.grader_poc.validate_cancellation --tb TB_REPO --harbor HARBOR_REPO --harbor-bin HARBOR_BIN --out FRESH_OUTPUT
```

The live command creates disposable fixtures and explicitly labeled preservation controls. Use a fresh output directory. It retains per-run ownership ledgers and outcomes. The ordinary run_trial entry point enables the ownership adapter automatically; direct use of upstream Harbor outside this wrapper is unchanged.

[Opinion] This correction removes the demonstrated operational blocker within the tested scope. It does not change P2's conclusion: no advantage over direct review or ordinary mutation testing has been demonstrated. Further scientific expansion needs a new explicit decision. Production integration, B1/A04 and the separate statistical-certification issue remain untouched. No merge, push or upstream change was performed.
'''
    report_path = root / "reports/PHASE-GRADER-CANCELLATION.md"
    if report_path.exists():
        raise FileExistsError(report_path)
    report_path.write_bytes(report.encode())
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, nargs="+", required=True)
    for key in ("unit", "review"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    result = package([path.resolve() for path in args.raw], args.unit.resolve(), args.review.resolve())
    print(json.dumps({"checks": len(result["checks"]), "payloads": result["packaged_payloads_excluding_manifest"]}))
