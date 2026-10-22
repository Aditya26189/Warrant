"""Actual pinned Harbor cancellation with narrowly labeled disposable resources."""
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

from experiments.grader_poc.run_trial import git_output, run_trial, write_receipt

LABEL = "warrant.grader_p2.integration"
BASE = "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"


def docker(*args: str) -> str:
    """Bound all daemon calls and refuse to interpret errors as absence."""
    return subprocess.check_output(["docker", *args], text=True, timeout=20).strip()


def inventory(owner: str) -> dict:
    """Record exact task labels plus global IDs, without other container contents."""
    result = {"at": datetime.now(timezone.utc).isoformat(), "owned": {}, "all_ids": {}}
    for kind in ("container", "network", "volume", "image"):
        flags = ["-a"] if kind in ("container", "image") else []
        ids = docker(kind, "ls", *flags, "-q", "--filter", f"label={LABEL}={owner}").splitlines()
        result["all_ids"][kind] = docker(kind, "ls", *flags, "-q").splitlines()
        entries = []
        for ident in sorted(set(ids)):
            item = json.loads(docker(kind, "inspect", ident))[0]
            labels = (item.get("Config") or {}).get("Labels", {}) if kind in ("container", "image") else item.get("Labels", {})
            entries.append({"id": item.get("Id") or item.get("Name"), "name": item.get("Name"),
                            "labels": labels or {}, "running": item.get("State", {}).get("Running")})
        result["owned"][kind] = entries
    return result


def remove_remaining(owner: str, snapshot: dict) -> list[dict]:
    """Recheck ownership on each exact ID immediately before scoped removal."""
    actions = []
    for kind in ("container", "network", "volume", "image"):
        for row in snapshot["owned"][kind]:
            item = json.loads(docker(kind, "inspect", row["id"]))[0]
            labels = (item.get("Config") or {}).get("Labels", {}) if kind in ("container", "image") else item.get("Labels", {})
            if (labels or {}).get(LABEL) != owner:
                raise RuntimeError("Ownership mismatch; refusing cleanup")
            flags = ["--force"] if kind == "container" else []
            try:
                output = docker(kind, "rm", *flags, row["id"])
                actions.append({"kind": kind, "id": row["id"], "status": "REMOVED", "output": output})
            except subprocess.SubprocessError as exc:
                actions.append({"kind": kind, "id": row["id"], "status": "ERROR", "reason": str(exc)})
    return actions


def fixture(task: Path, owner: str) -> None:
    """A sleeping oracle in real Harbor, with unique labels on all resource types."""
    task.mkdir(parents=True)
    for folder in ("environment", "solution", "tests"):
        (task / folder).mkdir()
    (task / "instruction.md").write_bytes(b"Controlled Warrant cancellation integration fixture.\n")
    (task / "task.toml").write_bytes(b'schema_version = "1.0"\n[agent]\ntimeout_sec = 600.0\n[verifier]\ntimeout_sec = 30.0\n[environment]\nbuild_timeout_sec = 180.0\ncpus = 1\nmemory_mb = 256\nstorage_mb = 1024\n')
    (task / "environment/Dockerfile").write_bytes(f'FROM {BASE}\nLABEL {LABEL}="{owner}"\nWORKDIR /app\n'.encode())
    compose = {"services": {"main": {"labels": {LABEL: owner}, "volumes": ["owned:/owned"]}},
               "networks": {"default": {"labels": {LABEL: owner}, "internal": True}},
               "volumes": {"owned": {"labels": {LABEL: owner}}}}
    (task / "environment/docker-compose.yaml").write_bytes(json.dumps(compose).encode())
    (task / "solution/solve.sh").write_bytes(b'#!/bin/bash\nset -eu\ntouch /tmp/warrant-p2-active\necho ACTIVE > /owned/marker\nsleep 300\n')
    (task / "tests/test.sh").write_bytes(b'#!/bin/bash\nmkdir -p /logs/verifier\necho 1 > /logs/verifier/reward.txt\n')


def check(args: argparse.Namespace, mode: str) -> dict:
    """Observe delegated cleanup before any repair cleanup is attempted."""
    owner = uuid.uuid4().hex
    output = args.out / mode
    output.mkdir(parents=True)
    task = output / ("warrant-p2-" + owner)
    fixture(task, owner)
    record = {"mode": mode, "owner": owner, "before": inventory(owner), "during": [],
              "synthetic_task": True, "actual_pinned_harbor": True, "semantic_evidence_valid": False}
    done = threading.Event()
    active = threading.Event()

    def monitor() -> None:
        try:
            while not done.is_set():
                snap = inventory(owner)
                record["during"].append(snap)
                for item in snap["owned"]["container"]:
                    if item["running"]:
                        probe = subprocess.run(["docker", "exec", item["id"], "test", "-e", "/tmp/warrant-p2-active"], timeout=10, capture_output=True)
                        if probe.returncode == 0:
                            active.set()
                if mode == "interruption" and active.is_set():
                    record["signal_sent_at"] = datetime.now(timezone.utc).isoformat()
                    os.kill(os.getpid(), signal.SIGINT)
                    return
                done.wait(3)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            record["monitor_error"] = str(exc)

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    run_args = argparse.Namespace(task=task, out=output / "run", tb_repo=args.tb, harbor_repo=args.harbor,
                                  harbor_bin=args.harbor_bin, name="warrant-p2-" + mode + "-" + owner,
                                  agent="oracle", expected_reward=1, timeout=60 if mode == "timeout" else 120,
                                  config=Path(__file__).with_name("protocol.json"))
    try:
        record["run"] = run_trial(run_args)
    finally:
        done.set()
        monitor_thread.join(timeout=30)
        record["active_trial_observed"] = active.is_set()
        record["after_harbor"] = inventory(owner)
        record["harbor_removed_all_owned"] = not any(record["after_harbor"]["owned"].values())
        record["cleanup_actions"] = remove_remaining(owner, record["after_harbor"])
        record["after_scoped_cleanup"] = inventory(owner)
        record["final_absence_verified"] = not any(record["after_scoped_cleanup"]["owned"].values())
        write_receipt(output / "outcome.json", record)
    return record


def main() -> None:
    """Run both cancellation modes against clean frozen source."""
    parser = argparse.ArgumentParser()
    for key in ("tb", "harbor", "harbor-bin", "out"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    for key in ("tb", "harbor", "harbor_bin", "out"):
        setattr(args, key, getattr(args, key).resolve())
    os.chdir(tempfile.gettempdir())
    root = Path(__file__).resolve().parents[3]
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit source before integration checks")
    args.out.mkdir(parents=True, exist_ok=False)
    result = {"source_commit": git_output(root, "rev-parse", "HEAD"), "source_dirty": False,
              "started_at": datetime.now(timezone.utc).isoformat(), "checks": []}
    for mode in ("timeout", "interruption"):
        row = check(args, mode)
        result["checks"].append({"mode": mode, "active": row["active_trial_observed"],
                                  "status": row["run"]["status"], "harbor_cleanup": row["harbor_removed_all_owned"],
                                  "final_absence": row["final_absence_verified"]})
        write_receipt(args.out / "outcome.json", result)
        print(json.dumps(result["checks"][-1]), flush=True)


if __name__ == "__main__":
    main()
