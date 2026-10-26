"""Run only the two reviewed calibration controls with pinned EvalPlus code."""

import argparse
import copy
import inspect
import json
import os
import platform
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .calibration import alternative, expected_from_spec, property_holds, property_inputs
from .prepare import HERE, ROOT, clean_revision, digest


def json_bytes(value: object) -> bytes:
    """Stable serialization for receipt bindings, not authentication."""
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def control_code(fixture: dict, variant: str) -> str:
    """Expose no arbitrary candidate execution interface in this Gate1 runner."""
    if variant == "reference":
        return fixture["prompt"] + fixture["canonical_solution"]
    if variant == "alternative":
        return (
            "from bisect import bisect_left, insort\n"
            + inspect.getsource(alternative)
            + f"\n{fixture['entry_point']} = alternative\n"
        )
    raise ValueError("Only reviewed Gate1 controls are allowed")


def worker(upstream: Path, variant: str) -> dict:
    """Use the native grader; keep its reference oracle separate from our P."""
    config = json.loads((HERE / "config.json").read_bytes())
    fixture = json.loads((HERE / "fixtures/calibration.json").read_bytes())
    sys.path.insert(0, str(upstream.resolve()))
    import numpy
    import psutil
    from evalplus.eval import untrusted_check
    from evalplus.gen.util import trusted_exec

    code = control_code(fixture, variant)
    reference_code = control_code(fixture, "reference")
    grader = {}
    for split in ("base", "plus"):
        inputs = copy.deepcopy(fixture[split + "_input"])
        started = time.perf_counter()
        expected, ref_time = trusted_exec(
            reference_code, inputs, fixture["entry_point"], record_time=True
        )
        preparation_seconds = time.perf_counter() - started
        started = time.perf_counter()
        status, details = untrusted_check(
            "humaneval", code, inputs, fixture["entry_point"],
            expected=expected, atol=fixture["atol"], ref_time=ref_time,
            fast_check=False,
        )
        grader[split] = {
            "status": status, "input_count": len(inputs),
            "checked_count": len(details), "passed_count": sum(bool(x) for x in details),
            "details": [bool(x) for x in details],
            "grader_seconds": time.perf_counter() - started,
            "reference_preparation_seconds": preparation_seconds,
            "expected_sha256": digest(json_bytes(expected)),
        }
    namespace = {}
    exec(compile(code, f"<reviewed-{variant}>", "exec"), namespace)
    function = namespace[fixture["entry_point"]]
    cases = property_inputs(config)
    started = time.perf_counter()
    mismatches, observed, expected = [], [], []
    for index, case in enumerate(cases):
        numbers, threshold = case["numbers"], case["threshold"]
        actual = function(numbers.copy(), threshold)
        truth = expected_from_spec(numbers, threshold, config["domain"])
        observed.append(actual)
        expected.append(truth)
        if not property_holds(actual, numbers, threshold, config["domain"]):
            mismatches.append({"index": index, "input": case,
                               "observed": actual, "expected": truth})
    return {
        "variant": variant, "task_id": fixture["task_id"],
        "candidate_sha256": digest(code.encode()), "grader": grader,
        "full_grader_seconds": sum(r["grader_seconds"] for r in grader.values()),
        "property": {
            "checked_count": len(cases), "mismatches": mismatches,
            "input_sha256": digest(json_bytes(cases)),
            "observed_sha256": digest(json_bytes(observed)),
            "expected_sha256": digest(json_bytes(expected)),
            "seconds": time.perf_counter() - started,
        },
        "versions": {"python": platform.python_version(), "numpy": numpy.__version__,
                     "psutil": psutil.__version__, "platform": platform.platform()},
    }


def control_passed(receipt: dict, counts: dict, property_count: int, target: float) -> bool:
    """Do not confuse incomplete execution or an empty receipt with a pass."""
    if receipt["execution_status"] != "COMPLETED":
        return False
    result = receipt["result"]
    return (
        result["full_grader_seconds"] < target
        and result["property"]["checked_count"] == property_count
        and not result["property"]["mismatches"]
        and all(result["grader"][split]["status"] == "pass"
                and result["grader"][split]["input_count"] == count
                and result["grader"][split]["checked_count"] == count
                and result["grader"][split]["passed_count"] == count
                for split, count in counts.items())
    )


def run(args: argparse.Namespace) -> bool:
    """Retain fresh subprocess receipts, including timeout or apparatus errors."""
    if os.name != "posix":
        raise RuntimeError("Use WSL/Linux: pinned evaluator requires POSIX timers")
    source = clean_revision(ROOT)
    config_raw = (HERE / "config.json").read_bytes()
    config = json.loads(config_raw)
    if clean_revision(args.evalplus_root) != config["evalplus_revision"]:
        raise ValueError("Wrong EvalPlus revision")
    fixture_raw = (HERE / "fixtures/calibration.json").read_bytes()
    fixture = json.loads(fixture_raw)
    selection = json.loads((HERE / "fixtures/selection.json").read_bytes())
    if digest(fixture_raw) != selection["calibration_file_sha256"]:
        raise ValueError("Calibration fixture changed")
    if digest(config_raw) != selection["config_sha256"]:
        raise ValueError("Frozen configuration changed")
    if fixture["task_id"] != config["calibration_id"]:
        raise ValueError("Refuse non-calibration task")
    args.out.mkdir(parents=True, exist_ok=False)
    corpus = property_inputs(config)
    (args.out / "property_inputs.json").write_bytes(json_bytes(corpus))
    summary = {
        "source_revision": source, "source_dirty": False,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_sha256": digest(config_raw), "config": config,
        "calibration_sha256": digest(fixture_raw),
        "upstream_file_sha256": {
            name: digest((args.evalplus_root / name).read_bytes())
            for name in ("evalplus/eval/__init__.py", "evalplus/eval/utils.py",
                         "evalplus/eval/_special_oracle.py", "evalplus/config.py",
                         "evalplus/gen/util/__init__.py")
        },
        "held_out_executions": 0, "human_active_minutes": None,
        "receipts": [], "calibration_gate": "INCOMPLETE",
    }
    counts = {s: len(fixture[s + "_input"]) for s in ("base", "plus")}
    start = time.perf_counter()
    env = os.environ.copy()
    env.update({"PYTHONPATH": str(ROOT), "PYTHONHASHSEED": "0",
                "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"})
    module = "experiments.grader_poc.feasibility.run_calibration"
    try:
        for variant in ("reference", "alternative"):
            for repeat in range(config["repetitions"]):
                name = f"{variant}-{repeat + 1:03d}"
                receipt = {"run": name, "execution_status": "NOT_STARTED"}
                summary["receipts"].append(receipt)
                command = [sys.executable, "-m", module, "--evalplus-root",
                           str(args.evalplus_root.resolve()), "--worker", variant]
                before = time.perf_counter()
                try:
                    process = subprocess.Popen(command, cwd="/tmp", env=env,
                                               start_new_session=True,
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    try:
                        stdout, stderr = process.communicate(timeout=config["outer_timeout_seconds"])
                    except BaseException:  # noqa: BLE001 -- owned-group cleanup, then re-raise.
                        # Process ownership boundary: stop this fresh worker group,
                        # including EvalPlus children, then preserve the interruption.
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        stdout, stderr = process.communicate()
                        (args.out / f"{name}.stdout").write_bytes(stdout)
                        (args.out / f"{name}.stderr").write_bytes(stderr)
                        raise
                    (args.out / f"{name}.stdout").write_bytes(stdout)
                    (args.out / f"{name}.stderr").write_bytes(stderr)
                    receipt["returncode"] = process.returncode
                    if process.returncode:
                        receipt["execution_status"] = "HARNESS_ERROR"
                    else:
                        receipt["result"] = json.loads(stdout)
                        receipt["execution_status"] = "COMPLETED"
                except subprocess.TimeoutExpired:
                    receipt["execution_status"] = "TIMEOUT"
                except (OSError, ValueError) as error:
                    receipt.update(execution_status="HARNESS_ERROR", error=str(error))
                finally:
                    receipt["outer_seconds"] = time.perf_counter() - before
                    (args.out / f"{name}.json").write_bytes(json_bytes(receipt))
                if receipt["execution_status"] != "COMPLETED":
                    return False
        passed = all(control_passed(r, counts, len(corpus), config["full_grader_target_seconds"])
                     for r in summary["receipts"])
        summary["calibration_gate"] = "PASS" if passed else "FAIL"
        return passed
    finally:
        summary["total_execution_seconds"] = time.perf_counter() - start
        summary["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        (args.out / "outcome.json").write_bytes(json_bytes(summary))


def main() -> None:
    """Separate controller provenance checks from its fixed, reviewed workers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evalplus-root", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--worker", choices=("reference", "alternative"))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.evalplus_root, args.worker), allow_nan=False))
    else:
        if args.out is None:
            parser.error("--out is required for a controller run")
        passed = run(args)
        print(json.dumps({"calibration_gate": "PASS" if passed else "NOT_PASSED"}))
        raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
