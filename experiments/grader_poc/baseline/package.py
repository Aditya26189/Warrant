"""Verify unchanged baseline receipts and report a negative result honestly."""

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from experiments.grader_poc.feasibility.calibration import expected_from_spec
from experiments.grader_poc.feasibility.prepare import HERE as CALIBRATION, ROOT, clean_revision, digest
from experiments.grader_poc.feasibility.run_calibration import json_bytes

from .candidates import HERE, candidate_pool, load_inputs, witness_inputs
from .run import classification, control_valid, grader_verdict, selected_code


def verify(raw: Path) -> tuple[dict, dict, str]:
    """Recompute every displayed count and validate source/input/output bindings."""
    config, calibration, fixture = load_inputs()
    outcome = json.loads((raw / "outcome.json").read_bytes())
    assert outcome["source_dirty"] is False and outcome["held_out_executions"] == 0
    assert outcome["config_sha256"] == digest((HERE / "config.json").read_bytes())
    assert outcome["calibration_config_sha256"] == digest((CALIBRATION / "config.json").read_bytes())
    assert outcome["fixture_sha256"] == digest((CALIBRATION / "fixtures/calibration.json").read_bytes())
    pool = candidate_pool()
    assert json.loads((raw / "pool.json").read_bytes()) == pool
    assert digest((raw / "pool.json").read_bytes()) == outcome["pool_sha256"]
    cases = witness_inputs(config, calibration)
    assert json.loads((raw / "witness_inputs.json").read_bytes()) == cases
    assert digest(json_bytes(cases)) == outcome["witness_input_sha256"]
    names = ["reference-before", "alternative-before", *[c["id"] for c in pool["candidates"]],
             "reference-after"]
    assert names == outcome["planned_trials"]
    assert outcome["status"] == "COMPLETED"
    assert [r["id"] for r in outcome["receipts"]] == names
    by_id = {r["id"]: r for r in outcome["receipts"]}
    assert all(control_valid(by_id[n], len(cases)) for n in names if not n.startswith("mutant"))
    expected_hashes = {s: g["expected_sha256"] for s, g in by_id["reference-before"]["result"]["grader"].items()}
    rows = []
    for receipt in outcome["receipts"]:
        name = receipt["id"]
        assert json.loads((raw / f"{name}.json").read_bytes()) == receipt
        code, role = selected_code(name, fixture)
        assert (raw / f"{name}.py").read_bytes() == code.encode()
        if receipt["execution_status"] != "COMPLETED":
            rows.append({"id": name, "role": role, "classification": classification(receipt),
                         "base": None, "plus": None, "outer_seconds": receipt["outer_seconds"]})
            continue
        result = receipt["result"]
        assert receipt["returncode"] == 0
        assert json.loads((raw / f"{name}.stdout").read_bytes()) == result
        assert not (raw / f"{name}.stderr").read_bytes()
        assert result["id"] == name and result["role"] == role
        assert result["candidate_sha256"] == digest(code.encode())
        assert result["grader_verdict"] == grader_verdict(result["grader"])
        for split, grading in result["grader"].items():
            assert grading["expected_sha256"] == expected_hashes[split]
            assert grading["input_count"] == len(fixture[split + "_input"])
            assert grading["checked_count"] == len(grading["details"])
            assert grading["passed_count"] == sum(grading["details"])
            assert all(type(value) is bool for value in grading["details"])
        witness = result["witness"]
        if result["grader_verdict"] != "PASS":
            assert witness["status"] == "NOT_RUN" and witness["checked_count"] == 0
        elif witness["status"] in ("FOUND", "NOT_FOUND_WITHIN_BUDGET"):
            assert witness["input_sha256"] == digest(json_bytes(cases))
            assert len(witness["observations"]) == witness["checked_count"] == len(cases)
            failures, divergences, first = 0, 0, None
            for index, (case, observation) in enumerate(zip(cases, witness["observations"], strict=True)):
                truth = expected_from_spec(case["numbers"], case["threshold"], calibration["domain"])
                assert observation["index"] == index
                assert observation["expected"] is truth and observation["reference_observed"] is truth
                observed = observation["observed"]
                holds = observed.get("type") == "bool" and observed.get("repr") == repr(truth)
                diverges = not holds  # unique boolean contract on this declared domain
                assert observation["property_holds"] is holds and observation["diverges"] is diverges
                failures += int(not holds)
                divergences += int(diverges)
                if not holds and first is None:
                    first = {"index": index, "input": case, "expected": truth,
                             "observed": observed, "reference_observed": truth}
            assert witness["failure_count"] == failures
            assert witness["reference_divergence_count"] == divergences
            assert witness["first_witness"] == first
            assert witness["status"] == ("FOUND" if failures else "NOT_FOUND_WITHIN_BUDGET")
        rows.append({"id": name, "role": role, "classification": classification(receipt),
                     "base": result["grader"].get("base"), "plus": result["grader"].get("plus"),
                     "witness_status": witness["status"], "witness_checks": witness.get("checked_count"),
                     "full_grader_seconds": result["full_grader_seconds"], "outer_seconds": receipt["outer_seconds"]})
    mutants = [r for r in rows if r["role"] == "MUTANT"]
    counts = dict(Counter(row["classification"] for row in mutants))
    survivors = sum(r["result"]["grader_verdict"] == "PASS" for r in outcome["receipts"] if r["id"].startswith("mutant") and r["execution_status"] == "COMPLETED")
    confirmed = counts.get("CONFIRMED_SPEC_VIOLATION", 0)
    seconds = outcome["total_execution_seconds"]
    summary = {
        "run_source_revision": outcome["source_revision"], "status": outcome["status"],
        "generated_candidates": pool["generated_count"], "evaluated_candidates": len(mutants),
        "excluded_by_cap": len(pool["excluded_by_cap"]), "mutant_classifications": counts,
        "full_grader_survivors": survivors, "confirmed_violating_candidates": confirmed,
        "distinct_spec_omissions": 0 if not confirmed else None,
        "confirmation_yield": confirmed / survivors if survivors else None,
        "executions_to_first_finding": next((i + 1 for i, r in enumerate(mutants) if r["classification"] == "CONFIRMED_SPEC_VIOLATION"), None),
        "grader_split_invocations": sum(len(r["result"]["grader"]) for r in outcome["receipts"] if r["execution_status"] == "COMPLETED"),
        "grader_inputs_checked": sum(g["checked_count"] for r in outcome["receipts"] if r["execution_status"] == "COMPLETED" for g in r["result"]["grader"].values()),
        "mutant_witness_checks": sum(r.get("witness_checks") or 0 for r in mutants),
        "control_witness_checks": sum(r.get("witness_checks") or 0 for r in rows if r["role"] == "CONTROL"),
        "base_only_survivors": [r["id"] for r in mutants if r["base"] and r["base"]["status"] == "pass"],
        "rejected_by_plus_after_base_pass": [r["id"] for r in mutants if r["base"] and r["plus"] and r["base"]["status"] == "pass" and r["plus"]["status"] == "fail"],
        "total_execution_seconds": seconds,
        "unused_execution_budget_seconds": max(0, config["total_execution_cap_seconds"] - seconds),
        "recorded_assistant_interval_to_run_minutes": (datetime.fromisoformat(outcome["finished_at_utc"]) - datetime.fromisoformat(config["recorded_assistant_start_utc"])).total_seconds() / 60,
        "human_active_minutes": None, "held_out_executions": 0, "rows": rows,
    }
    lines = ["# Gate2 baseline measurements (generated)", "",
             "| Candidate | Base passed | Plus passed | Classification | Witness checks | Outer seconds |",
             "|---|---:|---:|---|---:|---:|"]
    for row in rows:
        values = [f"{row[s]['passed_count']}/{row[s]['input_count']}" if row[s] else "unavailable" for s in ("base", "plus")]
        lines.append(f"| {row['id']} | {values[0]} | {values[1]} | {row['classification']} | {row.get('witness_checks', 'unavailable')} | {row['outer_seconds']:.6f} |")
    lines += ["", f"Generated / evaluated / cap-excluded candidates: {pool['generated_count']} / {len(mutants)} / {len(pool['excluded_by_cap'])}.",
              f"Full-grader survivors: {survivors}. Confirmed violating candidates: {confirmed}.",
              "Confirmation yield and executions-to-first-finding are undefined when their denominators/events are absent; JSON uses null.",
              f"Controller time: {seconds:.6f} seconds. Unused execution cap: {summary['unused_execution_budget_seconds']:.6f} seconds.",
              f"Grader split invocations: {summary['grader_split_invocations']}; total input checks including controls: {summary['grader_inputs_checked']}.",
              f"Mutant witness checks: {summary['mutant_witness_checks']}; control witness checks: {summary['control_witness_checks']}.",
              f"Recorded assistant interval to run completion: {summary['recorded_assistant_interval_to_run_minutes']:.3f} minutes; excludes later packaging/reporting and is not active human labor.",
              "Human effort and held-out task costs: unmeasured. No coverage-ordering comparison or human-review arm.", ""]
    return outcome, summary, "\n".join(lines)


def package(raw: Path, out: Path) -> None:
    """Retain raw bytes plus derived measurements under a separate source commit."""
    revision = clean_revision(ROOT)
    _, summary, measurements = verify(raw)
    out.mkdir(parents=True, exist_ok=False)
    payloads = {}
    for path in sorted(raw.iterdir()):
        if path.is_file():
            data = path.read_bytes()
            (out / path.name).write_bytes(data)
            payloads[path.name] = {"sha256": digest(data), "bytes": len(data)}
    for name, data in (("summary.json", json_bytes(summary)), ("MEASUREMENTS.md", measurements.encode())):
        (out / name).write_bytes(data)
        payloads[name] = {"sha256": digest(data), "bytes": len(data)}
    (out / "manifest.json").write_bytes(json_bytes({"packaging_revision": revision,
        "source_dirty": False, "run_source_revision": summary["run_source_revision"],
        "raw_copy_rule": "all completed raw-directory files copied byte-for-byte", "payloads": payloads}))
    print(json.dumps({"payloads": len(payloads), "evaluated": summary["evaluated_candidates"],
                      "survivors": summary["full_grader_survivors"], "confirmed": summary["confirmed_violating_candidates"]}))


def main() -> None:
    """Package one completed raw run into a fresh output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    package(args.raw, args.out)


if __name__ == "__main__":
    main()
