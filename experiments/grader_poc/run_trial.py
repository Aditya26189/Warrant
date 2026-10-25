"""Run one full Harbor trial and retain provenance, logs, and actual outcome.

This is a bounded experiment entry point, not a production Warrant command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import signal
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

from experiments.grader_poc.harbor_resources import HarborResources, defer_interrupt


def git_output(root: Path, *args: str) -> str:
    """Read provenance from the named repository, never the caller's checkout."""
    executable, directory = "git", str(root)
    # Windows-created worktrees have an absolute C:/... gitdir pointer. Use
    # Windows Git under WSL without rewriting metadata used by other sessions.
    if sys.platform == "linux" and "microsoft" in platform.release().lower():
        executable = "git.exe"
        directory = subprocess.check_output(["wslpath", "-w", str(root)], text=True).strip()
    return subprocess.check_output([executable, "-c", "core.longpaths=true", "-C", directory, *args], text=True).strip()


def file_hashes(root: Path) -> dict[str, str]:
    """Bind task bytes including the full verifier and all task metadata."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def write_receipt(path: Path, record: dict) -> None:
    """Replace one receipt atomically; never overwrite another attempt directory."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes((json.dumps(record, indent=2) + "\n").encode("utf-8"))
    temporary.replace(path)


def cancel_process(process: subprocess.Popen, grace: float) -> dict:
    """Give Harbor a chance to clean up; bound waiting on the owned process.

    POSIX uses a newly created process group, including descendant Compose
    clients that can outlive Harbor. Docker cleanup follows separately.
    """
    record = {"forced": False, "delegated_resource_cleanup": "UNVERIFIED"}
    try:
        if process.poll() is None:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGINT)
                record["signal"] = "SIGINT_PROCESS_GROUP"
            else:
                process.terminate()
                record["signal"] = "TERMINATE_CHILD"
        process.wait(timeout=grace)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        record["forced"] = True
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        try:
            process.wait(timeout=grace)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            record["error"] = type(exc).__name__
    except OSError as exc:
        record["error"] = str(exc)
    if os.name == "posix":
        try:
            # Parent exit alone does not imply its Compose children stopped.
            os.killpg(process.pid, signal.SIGKILL)
            record["remaining_group_signalled"] = True
        except ProcessLookupError:
            record["remaining_group_signalled"] = False
        except OSError as exc:
            record["error"] = str(exc)
    record["exit_code"] = process.poll()
    record["producer_stopped"] = record["exit_code"] is not None and "error" not in record and os.name == "posix"
    return record


def collect_trials(out: Path) -> tuple[list[dict], list[dict]]:
    """Retain partial results and parse errors without turning them into rewards."""
    def reject_constant(value: str) -> None:
        raise ValueError("Nonfinite JSON constant: " + value)

    trials, errors = [], []
    for path in sorted((out / "jobs").rglob("result.json")):
        relative = path.relative_to(out).as_posix()
        try:
            body = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
            if not isinstance(body, dict):
                raise ValueError("result must be an object")
            if "trial_name" in body:
                trials.append({"path": relative, "verifier_result": body.get("verifier_result"),
                               "exception_info": body.get("exception_info"),
                               "verifier_environment_mode": body.get("verifier_environment_mode"),
                               "task_checksum": body.get("task_checksum")})
        except (OSError, ValueError) as exc:
            errors.append({"path": relative, "type": type(exc).__name__, "message": str(exc)})
    return trials, errors


def run_trial(args: argparse.Namespace) -> dict:
    """Refuse dirty experiment source; distinguish infrastructure from reward."""
    source_root = Path(__file__).resolve().parents[2]
    dirty = git_output(source_root, "status", "--porcelain")
    if dirty:
        raise RuntimeError("Commit experimental source before recording a run: " + dirty)
    config_path = getattr(args, "config", None) or Path(__file__).with_name("config.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))
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
        "schema_version": 3, "evidence_kind": "adaptive_stress_test",
        "source_commit": git_output(source_root, "rev-parse", "HEAD"),
        "source_dirty": False, "config": config,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "command": command, "python": sys.version,
        "task_hashes": file_hashes(args.task), "agent": args.agent,
        "name": args.name, "expected_reward": args.expected_reward,
        "population_rate_claim": False,
        "timeout_seconds": args.timeout,
    }
    write_receipt(out / "invocation.json", record)
    env = os.environ.copy()
    env["HARBOR_TELEMETRY"] = "0"
    env["PYTHONPATH"] = str(source_root) + os.pathsep + env.get("PYTHONPATH", "")
    started = time.monotonic()
    record.update(status="INFRASTRUCTURE_ERROR", exit_code=None, matches_expected=None)
    process = None
    resources = None
    try:
        with (out / "command.log").open("w", encoding="utf-8") as log:
            resources = HarborResources(out)
            record["ownership"] = {"owner": resources.owner, "policy": resources.policy,
                                   "ledger": "ownership", "environment_adapter": "OwnedDockerEnvironment"}
            command.extend(resources.prepare())
            write_receipt(out / "invocation.json", record)
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                       env=env, start_new_session=os.name == "posix")
            try:
                record["exit_code"] = process.wait(timeout=args.timeout)
                record["status"] = "EXECUTED"
            except subprocess.TimeoutExpired as exc:
                record.update(status="TIMEOUT", error={"type": type(exc).__name__, "message": str(exc)})
            except KeyboardInterrupt:
                record.update(status="INTERRUPTED", error={"type": "KeyboardInterrupt", "message": "Harbor invocation interrupted"})
            finally:
                if process.poll() is None or record["status"] in ("TIMEOUT", "INTERRUPTED"):
                    with defer_interrupt():
                        record["cancellation"] = cancel_process(process, config["process_cancel_grace_seconds"])
                        record["exit_code"] = process.poll()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        record.update(status="INFRASTRUCTURE_ERROR", error={"type": type(exc).__name__, "message": str(exc)})
    except KeyboardInterrupt:
        record.update(status="INTERRUPTED", error={"type": "KeyboardInterrupt", "message": "Harbor invocation interrupted"})
    finally:
        if resources is not None:
            with defer_interrupt():
                if process is not None and process.poll() is None:
                    record["cancellation"] = cancel_process(process, config["process_cancel_grace_seconds"])
                    record["exit_code"] = process.poll()
                stopped = process is None or process.poll() is not None
                if "cancellation" in record:
                    stopped = record["cancellation"].get("producer_stopped", False)
                record["resource_cleanup"] = resources.cleanup(stopped)
                if "cancellation" in record:
                    record["cancellation"]["delegated_resource_cleanup"] = record["resource_cleanup"]["status"]
        record["elapsed_seconds"] = time.monotonic() - started
        trials, errors = collect_trials(out)
        record.update(trials=trials, result_errors=errors)
        try:
            record["task_unchanged"] = file_hashes(args.task) == record["task_hashes"]
        except OSError as exc:
            record["task_unchanged"] = None
            errors.append({"type": type(exc).__name__, "message": str(exc)})
        if record["status"] == "EXECUTED":
            record["status"] = "INFRASTRUCTURE_ERROR"
            if record["exit_code"] == 0 and len(trials) == 1 and not errors and not trials[0]["exception_info"]:
                verifier = trials[0]["verifier_result"]
                rewards = verifier.get("rewards") if isinstance(verifier, dict) else None
                reward = rewards.get("reward") if isinstance(rewards, dict) else None
                if (type(reward) in (int, float) and reward in (0, 1) and record["task_unchanged"]
                        and record.get("resource_cleanup", {}).get("verified_absent")):
                    record.update(status="COMPLETED", reward=reward, matches_expected=reward == args.expected_reward)
        write_receipt(out / "outcome.json", record)
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
    parser.add_argument("--config", type=Path)
    result = run_trial(parser.parse_args())
    print(json.dumps({key: result.get(key) for key in
                      ("name", "status", "reward", "matches_expected", "elapsed_seconds")}, indent=2))
    if result["status"] == "INTERRUPTED":
        return 130
    return 0 if result["status"] == "COMPLETED" and result["matches_expected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
