"""Targeted real-process/Docker checks, separate from the frozen P0/P1 packet."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

from experiments.grader_poc.diagnose import accepted_artifact, observe
from experiments.grader_poc.oracle import expected_sessions
from experiments.grader_poc.run_trial import git_output, run_trial, write_receipt


def interrupt_after(seconds: float, function):
    """Deliver a real SIGINT to this POSIX validation process, then cancel timer."""
    timer = threading.Timer(seconds, lambda: os.kill(os.getpid(), signal.SIGINT))
    timer.start()
    try:
        return function()
    finally:
        timer.cancel()
        timer.join()


def validate(args: argparse.Namespace) -> dict:
    """Exercise live failure paths and the known witness without changing claims."""
    if os.name != "posix":
        raise RuntimeError("Run real SIGINT validation under Linux/WSL")
    root = Path(__file__).resolve().parents[2]
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit validation source before recording checks")
    config_bytes = Path(__file__).with_name("config.json").read_bytes()
    config = json.loads(config_bytes)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    record = {"source_commit": git_output(root, "rev-parse", "HEAD"), "source_dirty": False,
              "started_at": datetime.now(timezone.utc).isoformat(), "kind": "runner_hardening_checks",
              "config_sha256": hashlib.sha256(config_bytes).hexdigest(), "python": sys.version,
              "checks": [], "population_rate_claim": False, "status": "INCOMPLETE"}
    write_receipt(out / "invocation.json", record)

    def retain(name: str, value: dict, passed: bool, synthetic: bool) -> None:
        entry = {"name": name, "passed": passed, "synthetic_fixture": synthetic, "result": value}
        record["checks"].append(entry)
        write_receipt(out / (name + ".json"), entry)
        print(json.dumps({"check": name, "passed": passed}), flush=True)

    try:
        fixture = out / "sleeping-app"
        fixture.mkdir()
        (fixture / "__init__.py").write_text("", encoding="utf-8")
        (fixture / "events.py").write_text("import time\nprint('controlled fixture active', flush=True)\ntime.sleep(60)\n", encoding="utf-8")
        timeout_config = dict(config, diagnostic_timeout_seconds=2)
        result = observe(fixture, [], timeout_config)
        retain("docker-timeout", result, result["execution_status"] == "TIMEOUT" and
               result["container"]["cleanup"].get("was_running") is True and
               result["container"]["cleanup"]["verified_absent"], True)
        result = interrupt_after(5, lambda: observe(fixture, [], dict(config, diagnostic_timeout_seconds=30)))
        retain("docker-interruption", result, result["execution_status"] == "INTERRUPTED" and
               result["container"]["cleanup"].get("was_running") is True and
               result["container"]["cleanup"]["verified_absent"], True)
        (fixture / "events.py").write_text("raise RuntimeError('controlled application failure')\n", encoding="utf-8")
        result = observe(fixture, [], config)
        retain("worker-exception", result, result["observation"].get("type") == "RuntimeError" and
               result["observation"]["status"] == "ERROR" and result["container"]["cleanup"]["verified_absent"], True)

        # This executable is a process fixture, explicitly not a Harbor grader.
        fake = out / "fake-harbor.py"
        fake.write_text("#!/usr/bin/env python3\nimport json,sys,time\nfrom pathlib import Path\n"
                        "p=Path(sys.argv[sys.argv.index('-o')+1])/'fixture'/'result.json'\n"
                        "p.parent.mkdir(parents=True)\n"
                        "p.write_text(json.dumps({'trial_name':'synthetic','verifier_result':{'rewards':{'reward':1}},'exception_info':None}))\n"
                        "print('synthetic partial result emitted',flush=True)\ntime.sleep(60)\n", encoding="utf-8")
        fake.chmod(0o700)
        for name, interrupted in (("harbor-timeout-fixture", False), ("harbor-interruption-fixture", True)):
            invocation = argparse.Namespace(task=args.cases / "reference_original", out=out / name,
                                             tb_repo=args.tb_repo, harbor_repo=args.harbor_repo,
                                             harbor_bin=fake, name=name, agent="oracle", expected_reward=1,
                                             timeout=30 if interrupted else 2)
            result = interrupt_after(5, lambda: run_trial(invocation)) if interrupted else run_trial(invocation)
            expected_status = "INTERRUPTED" if interrupted else "TIMEOUT"
            retain(name, result, result["status"] == expected_status and "reward" not in result and
                   bool(result["trials"]) and (invocation.out / "outcome.json").exists() and
                   result.get("cancellation", {}).get("exit_code") is not None, True)

        frozen = json.loads((root / "experiments/grader_poc/results/diagnostic/outcome.json").read_text(encoding="utf-8"))
        events = frozen["reduced"]["events"]
        expected = expected_sessions(events, config["initial_gap"], max_events=config["maximum_diagnostic_events"])
        for name, run, case in (("mutant", "omit-max-001", "omit_max_original"),
                               ("reference", "reference-001", "reference_original"),
                               ("equivalent", "equivalent-001", "equivalent_original")):
            app, identity = accepted_artifact(args.runs / run, args.cases / case)
            result = observe(app, events, config)
            wanted = copy.deepcopy(expected["sessions"])
            if name == "mutant":
                wanted = frozen["reduced"]["observation"]["sessions"]
            passed = result["observation"].get("sessions") == wanted and result["container"]["cleanup"]["verified_absent"]
            retain("witness-" + name, {"identity": identity, "events": events, "expected": expected, "execution": result}, passed, False)

        unit = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "experiments/grader_poc", "-p", "test_*.py", "-v"],
                              cwd=root, capture_output=True, text=True, check=False)
        (out / "unit-tests.txt").write_text(unit.stdout + unit.stderr, encoding="utf-8")
        record["unit_tests_exit_code"] = unit.returncode
        record["status"] = "PASSED" if unit.returncode == 0 and all(row["passed"] for row in record["checks"]) else "FAILED"
    finally:
        write_receipt(out / "outcome.json", record)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ("runs", "cases", "out", "tb-repo", "harbor-repo"):
        parser.add_argument("--" + key, type=Path, required=True)
    result = validate(parser.parse_args())
    print(json.dumps({"status": result["status"], "checks": len(result["checks"])}))
    raise SystemExit(0 if result["status"] == "PASSED" else 1)
