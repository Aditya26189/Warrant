"""Bind an independent, partial property check to accepted Harbor artifacts."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Callable

from experiments.grader_poc.oracle import expected_sessions
from experiments.grader_poc.container_lifecycle import run_owned
from experiments.grader_poc.run_trial import file_hashes, git_output, write_receipt


def reduce_trace(events: list[dict], violates: Callable[[list[dict]], bool]) -> list[dict]:
    """Greedily delete single events, then lower positive values and timestamps.

    Every accepted step strictly reduces trace length or a nonnegative integer.
    Only the supplied KNOWN-disagreement predicate can accept a change. Repeat
    deletion after scalar simplification; this claims no global minimality.
    """
    current = copy.deepcopy(events)
    while True:
        changed = False
        for i in range(len(current)):
            trial = current[:i] + current[i + 1:]
            if violates(trial):
                current, changed = trial, True
                break
        if changed:
            continue
        for i, event in enumerate(current):
            for field, floor in (("value", 1), ("time", 0)):
                for smaller in sorted({floor, event[field] // 2}):
                    if not floor <= smaller < event[field]:
                        continue
                    trial = copy.deepcopy(current)
                    trial[i][field] = smaller
                    if violates(trial):
                        current, changed = trial, True
                        break
                if changed:
                    break
            if changed:
                break
        if not changed:
            return current


def accepted_artifact(run: Path, task: Path) -> tuple[Path, dict]:
    """Require a successful full verifier run and exact allowed candidate bytes."""
    record = json.loads((run / "outcome.json").read_text())
    if record["status"] != "COMPLETED" or record["reward"] != 1 or not record["task_unchanged"]:
        raise ValueError("Diagnostic candidate needs a completed accepting full trial")
    if record["task_hashes"] != file_hashes(task):
        raise ValueError("Task bytes have changed since full grader run")
    trial = run / record["trials"][0]["path"]
    app = trial.parent / "artifacts/app/app"
    expected = file_hashes(task / "environment/app")
    for path, digest in file_hashes(task / "solution/files").items():
        expected[path] = digest
    actual = file_hashes(app)
    if actual != expected:
        raise ValueError("Collected candidate differs from the declared solution")
    ctrf = json.loads((trial.parent / "verifier/ctrf.json").read_text())
    return app, {"run": run.name, "reward": record["reward"], "hashes": actual,
                 "source_commit": record["source_commit"],
                 "full_verifier_summary": ctrf["results"]["summary"]}


def observe(app: Path, events: list[dict], config: dict) -> dict:
    """Keep candidate execution out of the oracle process and host filesystem."""
    worker = Path(__file__).with_name("trace_worker.py").resolve()
    arguments = ["--network", "none", "--read-only", "--pull", "never",
               "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt",
               "no-new-privileges", "--pids-limit", "64", "--memory", "256m",
               "--cpus", "1", "--mount", f"type=bind,source={app.resolve()},target=/candidate/app,readonly",
               "--mount", f"type=bind,source={worker},target=/worker.py,readonly",
               "-i", config["diagnostic_image"], "python", "-B", "/worker.py"]
    started = time.monotonic()
    receipt = run_owned(arguments, json.dumps({"gap": config["initial_gap"], "events": events}),
                        config["diagnostic_timeout_seconds"], config["diagnostic_cleanup_timeout_seconds"])
    observation = {"status": "ERROR", "reason": receipt["status"]}
    try:
        if receipt["status"] == "COMPLETED":
            if receipt["exit_code"] != 0:
                raise ValueError("nonzero container exit")
            observation = validate_observation(json.loads(receipt["stdout"]))
        if not receipt["cleanup"]["verified_absent"]:
            raise ValueError("owned container cleanup could not be verified")
    except ValueError as exc:
        observation = {"status": "ERROR", "reason": str(exc)}
    return {"observation": observation, "execution_status": receipt["status"],
            "exit_code": receipt["exit_code"], "stdout": receipt["stdout"], "stderr": receipt["stderr"],
            "container": receipt, "elapsed_seconds": time.monotonic() - started}


def validate_observation(value: object) -> dict:
    """Malformed protocol output is an execution error, not a counterexample."""
    if not isinstance(value, dict) or value.get("status") not in ("OBSERVED", "ERROR"):
        raise ValueError("Unexpected observer response")
    if value["status"] == "ERROR":
        return value
    if not isinstance(value.get("sessions"), list):
        raise ValueError("Missing session list")
    for session in value["sessions"]:
        if not isinstance(session, dict) or set(session) != {"key", "start", "end", "aggregate"}:
            raise ValueError("Invalid session fields")
        aggregate = session["aggregate"]
        if not isinstance(session["key"], str) or not isinstance(aggregate, dict) or set(aggregate) != {"sum", "count", "max"}:
            raise ValueError("Invalid aggregate fields")
        for number in [session["start"], session["end"], *aggregate.values()]:
            if type(number) not in (int, float) or (isinstance(number, float) and not math.isfinite(number)):
                raise ValueError("Invalid numeric observation")
    return value


def diagnose(runs: Path, cases: Path, out: Path) -> dict:
    """Record every attempt, including errors and abstentions, before summarizing."""
    root = Path(__file__).resolve().parents[2]
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit diagnostic source before scientific execution")
    config_bytes = Path(__file__).with_name("config.json").read_bytes()
    config = json.loads(config_bytes)
    out.mkdir(parents=True, exist_ok=False)
    candidates, identities = {}, {}
    for name, run, case in (("reference", "reference-001", "reference_original"),
                            ("mutant", "omit-max-001", "omit_max_original"),
                            ("equivalent", "equivalent-001", "equivalent_original")):
        candidates[name], identities[name] = accepted_artifact(runs / run, cases / case)
    record = {"source_commit": git_output(root, "rev-parse", "HEAD"), "source_dirty": False,
              "started_at": datetime.now(timezone.utc).isoformat(), "config": config,
              "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
              "candidates": identities, "population_rate_claim": False,
              "image_identity": json.loads(subprocess.check_output(
                  ["docker", "image", "inspect", config["diagnostic_image"]], text=True))[0]["Id"]}
    (out / "invocation.json").write_bytes((json.dumps(record, indent=2) + "\n").encode())
    attempts = []

    def check(name: str, events: list[dict], purpose: str) -> dict:
        expected = expected_sessions(events, config["initial_gap"], max_events=config["maximum_diagnostic_events"])
        row = {"index": len(attempts), "candidate": name, "purpose": purpose,
               "events": events, "expected": expected, "status": "UNKNOWN"}
        if expected["status"] == "KNOWN":
            row.update(observe(candidates[name], events, config))
            actual = row["observation"]
            row["status"] = ("DISAGREEMENT" if actual.get("sessions") != expected["sessions"] else "AGREES") if actual["status"] == "OBSERVED" else "ERROR"
        attempts.append(row)
        with (out / "attempts.jsonl").open("a", encoding="utf-8", newline="\n") as log:
            log.write(json.dumps(row) + "\n")
        print(json.dumps({"index": row["index"], "candidate": name, "purpose": purpose, "status": row["status"]}), flush=True)
        if row.get("execution_status") == "INTERRUPTED":
            raise KeyboardInterrupt
        return row

    def trace(pairs: list[list[int]]) -> list[dict]:
        return [{"key": "k", "source": "s1", "time": t, "value": v} for t, v in pairs]

    record["status"] = "INCONCLUSIVE"
    try:
        initial = trace(config["initial_trace"])
        first = check("mutant", initial, "initial")
        if first["status"] != "DISAGREEMENT":
            record["status"] = "UNKNOWN" if first["status"] == "UNKNOWN" else "NO_COUNTEREXAMPLE_FOUND_IN_SCOPE"
        else:
            reduced = reduce_trace(initial, lambda events: check("mutant", events, "reduction")["status"] == "DISAGREEMENT")
            record["initial"] = first
            record["reduced"] = check("mutant", reduced, "reduced_fresh_confirmation")
            deletions = [check("mutant", reduced[:i] + reduced[i + 1:], "final_single_deletion") for i in range(len(reduced))]
            record["single_deletion_minimal"] = all(row["status"] == "AGREES" for row in deletions)
            controls = [check(name, events, "control") for name in ("reference", "equivalent")
                        for events in [initial, reduced] + [trace(pairs) for pairs in config["hand_checked_traces"]]]
            record["controls_agree"] = all(row["status"] == "AGREES" for row in controls)
            record["status"] = "CONFIRMED_SCOPED_DISAGREEMENT" if record["controls_agree"] and record["reduced"]["status"] == "DISAGREEMENT" else "INCONCLUSIVE"
    except KeyboardInterrupt:
        record["status"] = "INTERRUPTED"
    except (OSError, ValueError) as exc:
        record.update(status="INCONCLUSIVE", error={"type": type(exc).__name__, "message": str(exc)})
    finally:
        try:
            record["candidate_bytes_unchanged"] = all(file_hashes(candidates[name]) == identities[name]["hashes"] for name in candidates)
        except OSError as exc:
            record.update(candidate_bytes_unchanged=None, error={"type": type(exc).__name__, "message": str(exc)})
        if record["status"] != "INTERRUPTED" and (not record["candidate_bytes_unchanged"] or any(row["status"] == "ERROR" for row in attempts)):
            record["status"] = "INCONCLUSIVE"
        record["attempt_count"] = len(attempts)
        record["container_calls"] = sum("observation" in row for row in attempts)
        record["container_elapsed_seconds"] = sum(row.get("elapsed_seconds", 0) for row in attempts)
        write_receipt(out / "outcome.json", record)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ("runs", "cases", "out"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.runs, args.cases, args.out)
    print(json.dumps({key: result.get(key) for key in ("status", "attempt_count", "container_calls", "single_deletion_minimal", "controls_agree")}, indent=2))
    raise SystemExit(130 if result["status"] == "INTERRUPTED" else
                     0 if result["status"] == "CONFIRMED_SCOPED_DISAGREEMENT" else 1)
