"""Exercise the corrected runner with real pinned Harbor and preservation controls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import uuid

from experiments.grader_poc.harbor_resources import OWNER_LABEL
from experiments.grader_poc.run_trial import git_output, run_trial, write_receipt

CONTROL_LABEL = "warrant.grader.cleanup-validation"


def docker(*args: str) -> str:
    return subprocess.check_output(["docker", *args], text=True, timeout=30).strip()


def fixture(task: Path, base: str, controls: dict, separate: bool) -> None:
    """No ownership labels in the task: only the actual runner supplies them."""
    task.mkdir()
    for folder in ("environment", "tests", "solution"):
        (task / folder).mkdir()
    (task / "instruction.md").write_bytes(b"Disposable runner cancellation fixture.\n")
    mode = '\nenvironment_mode = "separate"' if separate else ""
    (task / "task.toml").write_bytes((
        'schema_version = "1.0"\n[agent]\ntimeout_sec = 600.0\n[verifier]\ntimeout_sec = 600.0' + mode +
        '\n[environment]\nbuild_timeout_sec = 180.0\ncpus = 1\nmemory_mb = 256\nstorage_mb = 1024\n').encode())
    compose = {"services": {"main": {"volumes": ["owned:/owned", "shared:/shared"],
                                     "networks": ["default", "shared"]}},
               "networks": {"default": {"internal": True}, "shared": {"external": True, "name": controls["network"]}},
               "volumes": {"owned": {}, "shared": {"external": True, "name": controls["volume"]}}}
    for directory in ("environment", "tests") if separate else ("environment",):
        (task / directory / "Dockerfile").write_bytes(f"FROM {base}\nWORKDIR /app\n".encode())
        (task / directory / "docker-compose.yaml").write_bytes(json.dumps(compose).encode())
    agent = "echo agent-finished" if separate else "touch /tmp/warrant-active\nsleep 300"
    verifier = "touch /tmp/warrant-verifier-active\nsleep 300" if separate else "echo 1 > /logs/verifier/reward.txt"
    (task / "solution/solve.sh").write_bytes(("#!/bin/bash\nset -eu\n" + agent + "\n").encode())
    (task / "tests/test.sh").write_bytes(("#!/bin/bash\nset -eu\nmkdir -p /logs/verifier\n" + verifier + "\n").encode())


def inspect_control(controls: dict, base: str) -> dict:
    return {kind: json.loads(docker(kind, "inspect", ident))[0].get("Id", ident)
            for kind, ident in {**controls, "image": base}.items()}


def cancellation_check(args, mode: str, base: str, controls: dict) -> dict:
    output = args.out / mode
    output.mkdir()
    task = output / "task"
    fixture(task, base, controls, separate=mode == "verifier-interruption")
    marker = "/tmp/warrant-verifier-active" if mode == "verifier-interruption" else "/tmp/warrant-active"
    record = {"mode": mode, "synthetic_fixture": True, "semantic_evidence_valid": False, "during": [],
              "controls_before": inspect_control(controls, base)}
    active, done = threading.Event(), threading.Event()

    def monitor():
        try:
            while not done.wait(1):
                path = output / "run/ownership/cleanup.json"
                if not path.exists():
                    continue
                owner = json.loads(path.read_bytes())["owner"]
                ids = docker("container", "ls", "--all", "--quiet", "--filter", f"label={OWNER_LABEL}={owner}").splitlines()
                for ident in ids:
                    item = json.loads(docker("container", "inspect", ident))[0]
                    record["during"].append({"id": item["Id"], "running": item["State"]["Running"],
                                             "labels": item["Config"]["Labels"]})
                    if item["State"]["Running"]:
                        probe = subprocess.run(["docker", "exec", ident, "test", "-e", marker], capture_output=True, timeout=10)
                        if probe.returncode == 0:
                            active.set()
                if active.is_set() and mode != "timeout":
                    record["signal_sent_at"] = datetime.now(timezone.utc).isoformat()
                    os.kill(os.getpid(), signal.SIGINT)
                    return
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            record["monitor_error"] = str(exc)

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    try:
        record["run"] = run_trial(argparse.Namespace(
            task=task, out=output / "run", tb_repo=args.tb, harbor_repo=args.harbor,
            harbor_bin=args.harbor_bin, name="cleanup-" + mode, agent="oracle", expected_reward=1,
            timeout=60 if mode == "timeout" else 150))
    finally:
        done.set()
        thread.join(timeout=30)
        record["active_observed"] = active.is_set()
        record["controls_after"] = inspect_control(controls, base)
        record["controls_preserved"] = record["controls_before"] == record["controls_after"]
        record["foreign_container_running"] = json.loads(docker("container", "inspect", controls["container"]))[0]["State"]["Running"]
        result = record.get("run", {})
        record["passed"] = bool(active.is_set() and result.get("status") == ("TIMEOUT" if mode == "timeout" else "INTERRUPTED")
                                and result.get("resource_cleanup", {}).get("verified_absent")
                                and record["controls_preserved"] and record["foreign_container_running"] and "reward" not in result)
        write_receipt(output / "outcome.json", record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    for key in ("tb", "harbor", "harbor-bin", "out"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    for key in ("tb", "harbor", "harbor_bin", "out"):
        setattr(args, key, getattr(args, key).resolve())
    os.chdir(tempfile.gettempdir())
    root = Path(__file__).resolve().parents[2]
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit validation source first")
    args.out.mkdir(parents=True, exist_ok=False)
    base = json.loads(Path(__file__).with_name("config.json").read_bytes())["diagnostic_image"]
    token = uuid.uuid4().hex
    controls = {kind: "warrant-control-" + token for kind in ("container", "network", "volume")}
    record = {"source_commit": git_output(root, "rev-parse", "HEAD"), "source_dirty": False,
              "started_at": datetime.now(timezone.utc).isoformat(), "checks": [], "control_owner": token,
              "status": "INCOMPLETE"}
    write_receipt(args.out / "invocation.json", record)
    created = []
    try:
        for kind in ("network", "volume"):
            docker(kind, "create", "--label", f"{CONTROL_LABEL}={token}", controls[kind])
            created.append(kind)
        docker("run", "--detach", "--name", controls["container"], "--label", f"{CONTROL_LABEL}={token}",
               "--network", controls["network"], "--volume", controls["volume"] + ":/control", base, "sleep", "900")
        created.append("container")
        for mode in ("timeout", "interruption", "verifier-interruption"):
            row = cancellation_check(args, mode, base, controls)
            record["checks"].append({"mode": mode, "passed": row["passed"], "active": row["active_observed"],
                                      "status": row["run"]["status"], "cleanup": row["run"]["resource_cleanup"]["status"]})
            write_receipt(args.out / "outcome.json", record)
            print(json.dumps(record["checks"][-1]), flush=True)
        reference = run_trial(argparse.Namespace(task=args.tb / "tasks/session-window-debug", out=args.out / "reference",
            tb_repo=args.tb, harbor_repo=args.harbor, harbor_bin=args.harbor_bin, name="cleanup-reference",
            agent="oracle", expected_reward=1, timeout=600))
        record["checks"].append({"mode": "reference", "passed": reference["status"] == "COMPLETED" and reference["reward"] == 1,
                                  "status": reference["status"], "cleanup": reference["resource_cleanup"]["status"]})
        record["status"] = "PASSED" if all(row["passed"] for row in record["checks"]) else "FAILED"
    finally:
        record["control_removal"] = []
        for kind in ("container", "network", "volume"):
            if kind not in created:
                continue
            try:
                value = json.loads(docker(kind, "inspect", controls[kind]))[0]
                labels = value["Config"]["Labels"] if kind == "container" else value["Labels"]
                if labels.get(CONTROL_LABEL) != token:
                    raise ValueError("Foreign control identity changed; refusing removal")
                flags = ["--force"] if kind == "container" else []
                docker(kind, "rm", *flags, controls[kind])
                remaining = docker(kind, "ls", *( ["--all"] if kind == "container" else []),
                                   "--quiet", "--filter", f"label={CONTROL_LABEL}={token}")
                record["control_removal"].append({"kind": kind, "id": value.get("Id", controls[kind]), "absent": not remaining})
                if remaining:
                    record["status"] = "FAILED"
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                record["control_removal"].append({"kind": kind, "error": str(exc)})
                record["status"] = "FAILED"
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        write_receipt(args.out / "outcome.json", record)
    print(json.dumps({"status": record["status"], "checks": len(record["checks"])}), flush=True)


if __name__ == "__main__":
    main()
