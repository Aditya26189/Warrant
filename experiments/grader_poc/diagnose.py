"""Bind an independent, partial property check to accepted Harbor artifacts."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Callable

from experiments.grader_poc.oracle import expected_sessions
from experiments.grader_poc.run_trial import file_hashes, git_output


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
    command = ["docker", "run", "--rm", "--network", "none", "--read-only",
               "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt",
               "no-new-privileges", "--pids-limit", "64", "--memory", "256m",
               "--cpus", "1", "--mount", f"type=bind,source={app.resolve()},target=/candidate/app,readonly",
               "--mount", f"type=bind,source={worker},target=/worker.py,readonly",
               "-i", config["diagnostic_image"], "python", "-B", "/worker.py"]
    started = time.monotonic()
    try:
        result = subprocess.run(command, input=json.dumps({"gap": config["initial_gap"], "events": events}),
                                text=True, capture_output=True, check=False,
                                timeout=config["diagnostic_timeout_seconds"])
        observation = json.loads(result.stdout) if result.returncode == 0 else {
            "status": "ERROR", "reason": "nonzero container exit"}
        if not isinstance(observation, dict) or observation.get("status") not in ("OBSERVED", "ERROR"):
            raise ValueError("Unexpected observer response")
        return {"observation": observation, "exit_code": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr,
                "elapsed_seconds": time.monotonic() - started}
    except (subprocess.TimeoutExpired, ValueError) as exc:
        return {"observation": {"status": "ERROR", "reason": str(exc)},
                "elapsed_seconds": time.monotonic() - started}


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
        return row

    def trace(pairs: list[list[int]]) -> list[dict]:
        return [{"key": "k", "source": "s1", "time": t, "value": v} for t, v in pairs]

    initial = trace(config["initial_trace"])
    first = check("mutant", initial, "initial")
    if first["status"] != "DISAGREEMENT":
        record["status"] = "NO_CONFIRMED_DISAGREEMENT"
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
    record["candidate_bytes_unchanged"] = all(file_hashes(candidates[name]) == identities[name]["hashes"] for name in candidates)
    if not record["candidate_bytes_unchanged"] or any(row["status"] == "ERROR" for row in attempts):
        record["status"] = "INCONCLUSIVE"
    record["attempt_count"] = len(attempts)
    record["container_calls"] = sum("observation" in row for row in attempts)
    record["container_elapsed_seconds"] = sum(row.get("elapsed_seconds", 0) for row in attempts)
    (out / "outcome.json").write_bytes((json.dumps(record, indent=2) + "\n").encode())
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ("runs", "cases", "out"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.runs, args.cases, args.out)
    print(json.dumps({key: result.get(key) for key in ("status", "attempt_count", "container_calls", "single_deletion_minimal", "controls_agree")}, indent=2))
    raise SystemExit(0 if result["status"] == "CONFIRMED_SCOPED_DISAGREEMENT" else 1)
