"""Apply the unchanged mutation method to the predeclared reserved task packet."""

import argparse
import copy
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from experiments.grader_poc.baseline.run import classification, control_valid, grader_verdict, run_process
from experiments.grader_poc.feasibility.prepare import HERE as CALIBRATION, ROOT, clean_revision, digest
from experiments.grader_poc.feasibility.run_calibration import control_code, json_bytes

from .prepare import frozen_baseline
from .properties import HERE, config, encode, expected, witness_inputs


def task_packet(prepared: Path, task: str) -> tuple[dict, dict, list]:
    """Accept only the original task identities."""
    if task not in config()["task_ids"]:
        raise ValueError("Unreserved task")
    folder = prepared / task.split("/")[1]
    return tuple(json.loads((folder / name).read_bytes()) for name in ("fixture.json", "pool.json", "witness_inputs.json"))


def selected_code(prepared: Path, task: str, name: str) -> tuple[str, str]:
    """Select a prepared control/candidate without an arbitrary-source interface."""
    fixture, pool, _ = task_packet(prepared, task)
    if name in ("reference-before", "reference-after"):
        return control_code(fixture, "reference"), "CONTROL"
    if name == "alternative-before":
        return (prepared / task.split("/")[1] / "alternative.py").read_text(encoding="utf-8"), "CONTROL"
    matches = [c for c in pool["candidates"] if c["id"] == name]
    if len(matches) != 1:
        raise ValueError("Unknown frozen candidate")
    return matches[0]["source"], "MUTANT"


def witness_check(task: str, function: object, reference: object, cases: list) -> dict:
    """Use the prompt property; retain typed observations and all failures."""
    result = {"status": "NOT_FOUND_WITHIN_BUDGET", "checked_count": 0, "failure_count": 0,
              "reference_divergence_count": 0, "first_witness": None, "observations": []}
    for index, case in enumerate(cases):
        args = case["args"]
        truth = encode(expected(task, args))
        ref = encode(reference(*copy.deepcopy(args)))
        if ref != truth:
            raise ValueError("Reference failed the independent property")
        try:
            observed = encode(function(*copy.deepcopy(args)))
        except Exception as error:  # noqa: BLE001 -- only candidate exceptions become scoped violations.
            observed = {"exception_type": type(error).__name__, "message": str(error)}
        holds, diverges = observed == truth, observed != ref
        result["observations"].append({"index": index, "expected": truth, "reference": ref,
                                       "observed": observed, "property_holds": holds, "diverges": diverges})
        result["checked_count"] += 1
        result["reference_divergence_count"] += int(diverges)
        if not holds:
            result["status"] = "FOUND"
            result["failure_count"] += 1
            if result["first_witness"] is None:
                result["first_witness"] = {"index": index, "input": case, "expected": truth,
                                           "reference": ref, "observed": observed}
    return result


def worker(upstream: Path, prepared: Path, task: str, name: str) -> dict:
    """Keep upstream expected values separate from the independent property."""
    fixture, _, cases = task_packet(prepared, task)
    code, role = selected_code(prepared, task, name)
    result = {"id": name, "task_id": task, "role": role, "candidate_sha256": digest(code.encode()),
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
    reference = control_code(fixture, "reference")
    for split in ("base", "plus"):
        inputs = copy.deepcopy(fixture[split + "_input"])
        before = time.perf_counter()
        outputs, ref_time = trusted_exec(reference, inputs, fixture["entry_point"], record_time=True)
        preparation = time.perf_counter() - before
        before = time.perf_counter()
        status, details = untrusted_check("humaneval", code, inputs, fixture["entry_point"],
                                          expected=outputs, atol=fixture["atol"], ref_time=ref_time, fast_check=False)
        result["grader"][split] = {"status": status, "input_count": len(inputs),
            "checked_count": len(details), "passed_count": sum(bool(x) for x in details),
            "details": [bool(x) for x in details], "grader_seconds": time.perf_counter() - before,
            "reference_preparation_seconds": preparation, "expected_sha256": digest(json_bytes(outputs))}
    result["full_grader_seconds"] = sum(g["grader_seconds"] for g in result["grader"].values())
    result["grader_verdict"] = grader_verdict(result["grader"])
    if result["grader_verdict"] == "PASS":
        before = time.perf_counter()
        try:
            candidate_ns, reference_ns = {}, {}
            exec(compile(code, "<frozen-candidate>", "exec"), candidate_ns)
            exec(compile(reference, "<reference>", "exec"), reference_ns)
            witness = witness_check(task, candidate_ns[fixture["entry_point"]], reference_ns[fixture["entry_point"]], cases)
        except Exception as error:  # noqa: BLE001 -- apparatus failures never become discoveries.
            witness = {"status": "ORACLE_ERROR", "checked_count": None,
                       "error_type": type(error).__name__, "error": str(error)}
        witness["seconds"] = time.perf_counter() - before
        witness["input_sha256"] = digest(json_bytes(cases))
        result["witness"] = witness
    return result


def verify_prepared(prepared: Path) -> dict:
    """Reject changed domains, methods or prepared bytes before scientific use."""
    manifest = json.loads((prepared / "manifest.json").read_bytes())
    assert manifest["source_dirty"] is False
    assert manifest["config_sha256"] == digest((HERE / "config.json").read_bytes())
    assert manifest["property_source_sha256"] == digest((HERE / "properties.py").read_bytes())
    assert manifest["baseline_source_sha256"] == digest((ROOT / "experiments/grader_poc/baseline/candidates.py").read_bytes())
    for name, entry in manifest["payloads"].items():
        data = (prepared / name).read_bytes()
        assert len(data) == entry["bytes"] and digest(data) == entry["sha256"]
    for task in config()["task_ids"]:
        assert task_packet(prepared, task)[2] == witness_inputs(task)
    return manifest


def run(upstream: Path, prepared: Path, out: Path) -> bool:
    """Retain every reserved task, including failed feasibility and partial runs."""
    source = clean_revision(ROOT)
    cfg, baseline = config(), frozen_baseline()
    out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    summary = {"source_revision": source, "source_dirty": False, "status": "INCOMPLETE",
               "started_at_utc": datetime.now(timezone.utc).isoformat(), "tasks": [],
               "human_active_minutes": None, "config_sha256": digest((HERE / "config.json").read_bytes())}
    try:
        if os.name != "posix":
            raise RuntimeError("Pinned evaluator needs Linux/WSL")
        upstream_pin = json.loads((CALIBRATION / "config.json").read_bytes())["evalplus_revision"]
        assert clean_revision(upstream) == upstream_pin
        summary["prepared_manifest"] = verify_prepared(prepared)
        summary["upstream_revision"] = upstream_pin
        summary["upstream_file_sha256"] = {name: digest((upstream / name).read_bytes()) for name in
            ("evalplus/eval/__init__.py", "evalplus/eval/utils.py", "evalplus/eval/_special_oracle.py", "evalplus/config.py", "evalplus/gen/util/__init__.py")}
        env = os.environ.copy()
        env.update(PYTHONPATH=str(ROOT), PYTHONHASHSEED="0", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
        for task in cfg["task_ids"]:
            task_start = time.perf_counter()
            folder = out / task.split("/")[1]
            folder.mkdir()
            _, pool, cases = task_packet(prepared, task)
            names = ["reference-before", "alternative-before", *[c["id"] for c in pool["candidates"]], "reference-after"]
            record = {"task_id": task, "status": "INCOMPLETE", "receipts": [], "planned_trials": names,
                      "generated_count": pool["generated_count"], "cap_excluded": len(pool["excluded_by_cap"])}
            summary["tasks"].append(record)
            try:
                for name in names:
                    code, _ = selected_code(prepared, task, name)
                    (folder / f"{name}.py").write_bytes(code.encode())
                for name in names:
                    remaining = baseline["total_execution_cap_seconds"] - (time.perf_counter() - task_start)
                    if remaining <= 0:
                        record["status"] = "EXECUTION_BUDGET_EXHAUSTED"
                        break
                    command = [sys.executable, "-m", "experiments.grader_poc.transfer.run", "--evalplus-root", str(upstream.resolve()),
                               "--prepared", str(prepared.resolve()), "--task", task, "--worker", name]
                    receipt = run_process(command, min(baseline["outer_timeout_seconds"], remaining), env, folder, name)
                    record["receipts"].append(receipt)
                    print(json.dumps({"task": task, "trial": name, "classification": classification(receipt)}), flush=True)
                    if not name.startswith("mutant") and not control_valid(receipt, len(cases)):
                        record["status"] = "INVALID_CONTROLS"
                        break
                else:
                    record["status"] = "COMPLETED"
            finally:
                known = {r["id"] for r in record["receipts"]}
                for name in names:
                    path = folder / f"{name}.json"
                    if name not in known and path.exists():
                        record["receipts"].append(json.loads(path.read_bytes()))
                record["total_execution_seconds"] = time.perf_counter() - task_start
                record["unused_execution_budget_seconds"] = max(0, baseline["total_execution_cap_seconds"] - record["total_execution_seconds"])
                (folder / "outcome.json").write_bytes(json_bytes(record))
        summary["status"] = "COMPLETED" if all(t["status"] == "COMPLETED" for t in summary["tasks"]) else "COMPLETED_WITH_INFEASIBILITY"
        return True
    except Exception as error:  # noqa: BLE001 -- preserve failed apparatus, then propagate.
        summary.update(status="HARNESS_ERROR", error_type=type(error).__name__, error=str(error))
        raise
    except BaseException:  # noqa: BLE001 -- preserve user interruption, then propagate.
        summary["status"] = "INTERRUPTED"
        raise
    finally:
        summary["total_execution_seconds"] = time.perf_counter() - start
        summary["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        (out / "outcome.json").write_bytes(json_bytes(summary))


def main() -> None:
    """Operate on a pinned packet and named identity only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evalplus-root", type=Path, required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--task")
    parser.add_argument("--worker")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.evalplus_root, args.prepared, args.task, args.worker), allow_nan=False))
    else:
        if args.out is None:
            parser.error("--out required")
        raise SystemExit(0 if run(args.evalplus_root, args.prepared, args.out) else 1)


if __name__ == "__main__":
    main()
