"""Run one full Harbor trial and retain provenance, logs, and actual outcome.

This is a bounded experiment entry point, not a production Warrant command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone


def git_output(root: Path, *args: str) -> str:
    """Read provenance from the named repository, never the caller's checkout."""
    executable, directory = "git", str(root)
    # Windows-created worktrees have an absolute C:/... gitdir pointer. Use
    # Windows Git under WSL without rewriting metadata used by other sessions.
    if sys.platform == "linux" and "microsoft" in platform.release().lower():
        executable = "git.exe"
        directory = subprocess.check_output(["wslpath", "-w", str(root)], text=True).strip()
    return subprocess.check_output([executable, "-C", directory, *args], text=True).strip()


def file_hashes(root: Path) -> dict[str, str]:
    """Bind task bytes including the full verifier and all task metadata."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def run_trial(args: argparse.Namespace) -> dict:
    """Refuse dirty experiment source; distinguish infrastructure from reward."""
    source_root = Path(__file__).resolve().parents[2]
    dirty = git_output(source_root, "status", "--porcelain")
    if dirty:
        raise RuntimeError("Commit experimental source before recording a run: " + dirty)
    config = json.loads(Path(__file__).with_name("config.json").read_text())
    for root, pin in ((args.tb_repo, config["terminal_bench_commit"]),
                      (args.harbor_repo, config["harbor_commit"])):
        if git_output(root, "rev-parse", "HEAD") != pin:
            raise ValueError("Upstream repository does not match registered commit")
        if git_output(root, "status", "--porcelain"):
            raise ValueError("Upstream checkout is dirty")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    command = [str(args.harbor_bin.resolve()), "run", "-p", str(args.task.resolve()),
               "-a", args.agent, "-n", "1", "-o", str(out / "jobs"),
               "--job-name", args.name]
    record = {
        "schema_version": 1, "evidence_kind": "adaptive_stress_test",
        "source_commit": git_output(source_root, "rev-parse", "HEAD"),
        "source_dirty": False, "config": config,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "command": command, "python": sys.version,
        "task_hashes": file_hashes(args.task), "agent": args.agent,
        "name": args.name, "expected_reward": args.expected_reward,
        "population_rate_claim": False,
    }
    (out / "invocation.json").write_text(json.dumps(record, indent=2) + "\n")
    env = os.environ.copy()
    env["HARBOR_TELEMETRY"] = "0"
    started = time.monotonic()
    with (out / "command.log").open("w") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                env=env, timeout=args.timeout, check=False)
    record["elapsed_seconds"] = time.monotonic() - started
    record["exit_code"] = result.returncode
    trials = []
    for path in sorted((out / "jobs").rglob("result.json")):
        body = json.loads(path.read_text())
        if "trial_name" in body:
            trials.append({"path": path.relative_to(out).as_posix(),
                           "verifier_result": body.get("verifier_result"),
                           "exception_info": body.get("exception_info"),
                           "verifier_environment_mode": body.get("verifier_environment_mode"),
                           "task_checksum": body.get("task_checksum")})
    record["trials"] = trials
    record["status"] = "ERROR"
    if result.returncode == 0 and len(trials) == 1 and not trials[0]["exception_info"]:
        rewards = (trials[0]["verifier_result"] or {}).get("rewards") or {}
        if rewards.get("reward") in (0, 1):
            record["reward"] = rewards["reward"]
            record["status"] = "COMPLETED"
            record["matches_expected"] = rewards["reward"] == args.expected_reward
    record["task_unchanged"] = file_hashes(args.task) == record["task_hashes"]
    if not record["task_unchanged"]:
        record["status"] = "ERROR"
    (out / "outcome.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main() -> int:
    """Keep invocation paths explicit so no private machine layout is assumed."""
    parser = argparse.ArgumentParser()
    for key in ("task", "out", "tb-repo", "harbor-repo", "harbor-bin"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--agent", choices=("nop", "oracle"), required=True)
    parser.add_argument("--expected-reward", type=int, choices=(0, 1), required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    result = run_trial(parser.parse_args())
    print(json.dumps({key: result.get(key) for key in
                      ("name", "status", "reward", "matches_expected", "elapsed_seconds")}, indent=2))
    return 0 if result["status"] == "COMPLETED" and result["matches_expected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
