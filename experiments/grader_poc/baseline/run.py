"""Run the frozen, locally generated calibration candidates in fresh processes."""

import argparse
import copy
import json
import os
import platform
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from experiments.grader_poc.feasibility.calibration import expected_from_spec, property_holds
from experiments.grader_poc.feasibility.prepare import HERE as CALIBRATION, ROOT, clean_revision, digest
from experiments.grader_poc.feasibility.run_calibration import control_code, json_bytes

from .candidates import HERE, candidate_pool, load_inputs, witness_inputs


def grader_verdict(grader: dict) -> str:
    """Incomplete/timeout grading is never silently counted as a rejection."""
    if set(grader) != {"base", "plus"}:
        return "UNAVAILABLE"
    for result in grader.values():
        if result["status"] not in ("pass", "fail"):
            return "UNAVAILABLE"
        if result["checked_count"] != result["input_count"]:
            return "UNAVAILABLE"
    if any(r["status"] == "fail" for r in grader.values()):
        return "FAIL"
    if all(r["passed_count"] == r["input_count"] for r in grader.values()):
        return "PASS"
    return "UNAVAILABLE"


def witness_check(function: object, reference: object, cases: list[dict], domain: dict) -> dict:
    """Keep specification failures distinct from incidental reference divergence."""
    result = {"status": "NOT_FOUND_WITHIN_BUDGET", "checked_count": 0,
              "failure_count": 0, "reference_divergence_count": 0, "first_witness": None,
              "observations": []}
    for index, case in enumerate(cases):
        numbers, threshold = case["numbers"], case["threshold"]
        # These calls are trusted apparatus: exceptions must abort the witness
        # phase as ORACLE_ERROR rather than being charged to the candidate.
        truth = expected_from_spec(numbers, threshold, domain)
        ref_value = reference(numbers.copy(), threshold)
        if not property_holds(ref_value, numbers, threshold, domain):
            raise ValueError("Reference failed the specification property")
        try:
            observed = function(numbers.copy(), threshold)
        except Exception as error:  # noqa: BLE001 -- deliberate candidate-call boundary only.
            observation = {"exception_type": type(error).__name__, "message": str(error)}
            holds, diverges = False, True
        else:
            observation = {"type": type(observed).__name__, "repr": repr(observed)}
            holds = property_holds(observed, numbers, threshold, domain)
            diverges = type(observed) is not type(ref_value) or observed != ref_value
        result["checked_count"] += 1
        result["reference_divergence_count"] += int(diverges)
        result["observations"].append({"index": index, "expected": truth,
                                       "observed": observation, "property_holds": holds,
                                       "reference_observed": ref_value, "diverges": diverges})
        if not holds:
            result["failure_count"] += 1
            result["status"] = "FOUND"
            if result["first_witness"] is None:
                result["first_witness"] = {"index": index, "input": case,
                                            "expected": truth, "observed": observation,
                                            "reference_observed": ref_value}
    return result


def selected_code(name: str, fixture: dict) -> tuple[str, str]:
    """Accept only frozen generated identities or the two reviewed controls."""
    if name in ("reference-before", "reference-after", "alternative-before"):
        variant = "alternative" if name.startswith("alternative") else "reference"
        return control_code(fixture, variant), "CONTROL"
    matches = [c for c in candidate_pool()["candidates"] if c["id"] == name]
    if len(matches) != 1:
        raise ValueError("Unknown frozen candidate identity")
    return matches[0]["source"], "MUTANT"


def worker(upstream: Path, name: str) -> dict:
    """Use the unchanged native grader before any survivor-only witness search."""
    config, calibration, fixture = load_inputs()
    code, role = selected_code(name, fixture)
    result = {"id": name, "role": role, "candidate_sha256": digest(code.encode()),
              "candidate_status": "VALID", "grader": {}, "grader_verdict": "UNAVAILABLE",
              "witness": {"status": "NOT_RUN", "checked_count": 0}, "full_grader_seconds": 0.0}
    try:
        compile(code, "<frozen-candidate>", "exec")
    except SyntaxError as error:
        result.update(candidate_status="INVALID_SYNTAX", error=str(error))
        return result
    sys.path.insert(0, str(upstream.resolve()))
    import numpy
    import psutil
    from evalplus.eval import untrusted_check
    from evalplus.gen.util import trusted_exec

    result["versions"] = {"python": platform.python_version(), "numpy": numpy.__version__,
                          "psutil": psutil.__version__, "platform": platform.platform()}
    reference_code = control_code(fixture, "reference")
    for split in ("base", "plus"):
        inputs = copy.deepcopy(fixture[split + "_input"])
        start = time.perf_counter()
        expected, ref_time = trusted_exec(reference_code, inputs, fixture["entry_point"], record_time=True)
        preparation = time.perf_counter() - start
        start = time.perf_counter()
        status, details = untrusted_check("humaneval", code, inputs, fixture["entry_point"],
                                          expected=expected, atol=fixture["atol"],
                                          ref_time=ref_time, fast_check=False)
        result["grader"][split] = {
            "status": status, "input_count": len(inputs), "checked_count": len(details),
            "passed_count": sum(bool(x) for x in details), "details": [bool(x) for x in details],
            "grader_seconds": time.perf_counter() - start,
            "reference_preparation_seconds": preparation, "expected_sha256": digest(json_bytes(expected)),
        }
    result["full_grader_seconds"] = sum(r["grader_seconds"] for r in result["grader"].values())
    result["grader_verdict"] = grader_verdict(result["grader"])
    if result["grader_verdict"] == "PASS":
        cases = witness_inputs(config, calibration)
        start = time.perf_counter()
        try:
            candidate_namespace, reference_namespace = {}, {}
            exec(compile(code, "<frozen-candidate>", "exec"), candidate_namespace)
            exec(compile(reference_code, "<reference>", "exec"), reference_namespace)
            witness = witness_check(candidate_namespace[fixture["entry_point"]],
                                    reference_namespace[fixture["entry_point"]],
                                    cases, calibration["domain"])
        except Exception as error:  # noqa: BLE001 -- retain oracle/apparatus failure, never a finding.
            witness = {"status": "ORACLE_ERROR", "error_type": type(error).__name__,
                       "error": str(error), "checked_count": None}
        witness["seconds"] = time.perf_counter() - start
        witness["input_sha256"] = digest(json_bytes(cases))
        result["witness"] = witness
    return result


def classification(receipt: dict) -> str:
    """A reporting projection; preserve orthogonal dimensions in raw receipts."""
    if receipt["execution_status"] != "COMPLETED":
        return receipt["execution_status"]
    result = receipt["result"]
    if result["candidate_status"] != "VALID":
        return "INVALID_CANDIDATE"
    verdict = result["grader_verdict"]
    if verdict == "FAIL":
        return "REJECTED_BY_FULL_GRADER"
    if verdict != "PASS":
        return "GRADING_UNAVAILABLE"
    witness = result["witness"]
    if witness["status"] == "FOUND":
        return "CONFIRMED_SPEC_VIOLATION"
    if witness["status"] == "NOT_FOUND_WITHIN_BUDGET":
        return "UNRESOLVED_WITHIN_BUDGET"
    return "ORACLE_ERROR"


def control_valid(receipt: dict, count: int) -> bool:
    """Both grader acceptance and a completed clean property check are required."""
    return (classification(receipt) == "UNRESOLVED_WITHIN_BUDGET"
            and receipt["result"]["witness"]["checked_count"] == count
            and receipt["result"]["witness"]["failure_count"] == 0)


def run_process(command: list[str], timeout: float, env: dict, out: Path, name: str) -> dict:
    """Bound and clean up the owned process group; retain failures and output."""
    before = time.perf_counter()
    receipt = {"id": name, "execution_status": "NOT_STARTED"}
    stdout, stderr = b"", b""
    try:
        process = subprocess.Popen(command, cwd="/tmp", env=env, start_new_session=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except BaseException:  # noqa: BLE001 -- stop owned descendants before preserving interruption.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
            raise
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
    except BaseException:  # noqa: BLE001 -- record user/process interruption, then propagate.
        receipt["execution_status"] = "INTERRUPTED"
        raise
    finally:
        receipt["outer_seconds"] = time.perf_counter() - before
        (out / f"{name}.stdout").write_bytes(stdout)
        (out / f"{name}.stderr").write_bytes(stderr)
        (out / f"{name}.json").write_bytes(json_bytes(receipt))
    return receipt


def run(upstream: Path, out: Path) -> bool:
    """Freeze pool bytes and enforce clean provenance before any candidate runs."""
    source = clean_revision(ROOT)
    config, calibration, fixture = load_inputs()
    out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    summary = {"source_revision": source, "source_dirty": False,
               "started_at_utc": datetime.now(timezone.utc).isoformat(), "receipts": [],
               "status": "INCOMPLETE", "held_out_executions": 0, "human_active_minutes": None,
               "config": config, "config_sha256": digest((HERE / "config.json").read_bytes()),
               "calibration_config_sha256": digest((CALIBRATION / "config.json").read_bytes()),
               "fixture_sha256": digest((CALIBRATION / "fixtures/calibration.json").read_bytes())}
    try:
        if os.name != "posix":
            raise RuntimeError("Use Linux/WSL for pinned EvalPlus timers")
        if clean_revision(upstream) != calibration["evalplus_revision"]:
            raise ValueError("Wrong upstream revision")
        selection = json.loads((CALIBRATION / "fixtures/selection.json").read_bytes())
        assert summary["fixture_sha256"] == selection["calibration_file_sha256"]
        assert summary["calibration_config_sha256"] == selection["config_sha256"]
        pool = candidate_pool()
        cases = witness_inputs(config, calibration)
        (out / "pool.json").write_bytes(json_bytes(pool))
        (out / "witness_inputs.json").write_bytes(json_bytes(cases))
        summary["pool_sha256"] = digest(json_bytes(pool))
        summary["witness_input_sha256"] = digest(json_bytes(cases))
        summary["upstream_revision"] = calibration["evalplus_revision"]
        summary["upstream_file_sha256"] = {
            name: digest((upstream / name).read_bytes()) for name in
            ("evalplus/eval/__init__.py", "evalplus/eval/utils.py", "evalplus/eval/_special_oracle.py",
             "evalplus/config.py", "evalplus/gen/util/__init__.py")}
        names = ["reference-before", "alternative-before", *[c["id"] for c in pool["candidates"]],
                 "reference-after"]
        summary["planned_trials"] = names
        for name in names:
            code, _ = selected_code(name, fixture)
            (out / f"{name}.py").write_bytes(code.encode())
        env = os.environ.copy()
        env.update(PYTHONPATH=str(ROOT), PYTHONHASHSEED="0", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
        for name in names:
            elapsed = time.perf_counter() - start
            remaining = config["total_execution_cap_seconds"] - elapsed
            if remaining <= 0:
                summary["status"] = "EXECUTION_BUDGET_EXHAUSTED"
                return False
            command = [sys.executable, "-m", "experiments.grader_poc.baseline.run",
                       "--evalplus-root", str(upstream.resolve()), "--worker", name]
            receipt = run_process(command, min(config["outer_timeout_seconds"], remaining), env, out, name)
            summary["receipts"].append(receipt)
            if not name.startswith("mutant") and not control_valid(receipt, len(cases)):
                summary["status"] = "INVALID_CONTROLS"
                return False
            print(json.dumps({"trial": name, "classification": classification(receipt)}), flush=True)
        summary["status"] = "COMPLETED"
        return True
    except Exception as error:  # noqa: BLE001 -- final apparatus boundary, saved then re-raised.
        summary.update(status="HARNESS_ERROR", error_type=type(error).__name__, error=str(error))
        raise
    except BaseException:  # noqa: BLE001 -- user interruption is retained and propagated.
        summary["status"] = "INTERRUPTED"
        raise
    finally:
        summary["total_execution_seconds"] = time.perf_counter() - start
        summary["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        # Include a child receipt saved during interruption before run_process returned.
        known = {r["id"] for r in summary["receipts"]}
        for name in summary.get("planned_trials", []):
            path = out / f"{name}.json"
            if name not in known and path.exists():
                summary["receipts"].append(json.loads(path.read_bytes()))
        (out / "outcome.json").write_bytes(json_bytes(summary))


def main() -> None:
    """Expose frozen identities, not an arbitrary source-file execution service."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evalplus-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--worker")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.evalplus_root, args.worker), allow_nan=False))
    else:
        if args.out is None:
            parser.error("--out is required for a controller run")
        raise SystemExit(0 if run(args.evalplus_root, args.out) else 1)


if __name__ == "__main__":
    main()
