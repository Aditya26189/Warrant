"""Verify all reserved-task receipts without promoting a negative pilot."""

import argparse
import json
from collections import Counter
from pathlib import Path

from experiments.grader_poc.baseline.candidates import mutations
from experiments.grader_poc.baseline.run import classification, control_valid, grader_verdict
from experiments.grader_poc.feasibility.prepare import ROOT, clean_revision, digest
from experiments.grader_poc.feasibility.run_calibration import control_code, json_bytes

from .prepare import frozen_baseline
from .properties import alternative_code, config, encode, expected
from .run import selected_code, task_packet, verify_prepared


def verify(prepared: Path, raw: Path) -> tuple[dict, str]:
    """Derive displayed totals from verified typed observations and native details."""
    manifest = verify_prepared(prepared)
    baseline = frozen_baseline()
    outcome = json.loads((raw / "outcome.json").read_bytes())
    assert outcome["source_dirty"] is False
    assert outcome["prepared_manifest"] == manifest
    assert outcome["config_sha256"] == manifest["config_sha256"]
    assert outcome["status"] in ("COMPLETED", "COMPLETED_WITH_INFEASIBILITY")
    assert [t["task_id"] for t in outcome["tasks"]] == config()["task_ids"]
    summary = {"run_source_revision": outcome["source_revision"], "preparation_source_revision": manifest["source_revision"],
               "status": outcome["status"], "tasks": [], "human_active_minutes": None,
               "total_execution_seconds": outcome["total_execution_seconds"]}
    detail_lines = ["# Transfer measurements (generated)", "",
                    "| Task | Mutant | Base pass | Plus pass | Outcome | Witness checks | Outer s |",
                    "|---|---|---:|---:|---|---:|---:|"]
    for record in outcome["tasks"]:
        task = record["task_id"]
        folder = raw / task.split("/")[1]
        assert json.loads((folder / "outcome.json").read_bytes()) == record
        fixture, pool, cases = task_packet(prepared, task)
        source = control_code(fixture, "reference")
        generated = mutations(source, fixture["entry_point"], baseline["operators"])
        assert pool["candidates"] == generated[:baseline["candidate_cap"]]
        assert pool["excluded_by_cap"] == generated[baseline["candidate_cap"]:]
        assert pool["generated_count"] == len(generated)
        assert (prepared / folder.name / "alternative.py").read_bytes() == alternative_code(task, fixture["entry_point"]).encode()
        names = ["reference-before", "alternative-before", *[c["id"] for c in pool["candidates"]], "reference-after"]
        assert record["planned_trials"] == names
        assert [r["id"] for r in record["receipts"]] == names[:len(record["receipts"])]
        if record["status"] == "COMPLETED":
            assert len(record["receipts"]) == len(names)
        counts, full_survivors, findings, control_checks, mutant_checks = Counter(), 0, 0, 0, 0
        base_survivors, plus_only_kills, control_times = [], [], []
        split_calls, input_checks, invalid_controls = 0, 0, []
        reference_hashes = None
        for receipt in record["receipts"]:
            name = receipt["id"]
            assert json.loads((folder / f"{name}.json").read_bytes()) == receipt
            code, role = selected_code(prepared, task, name)
            assert (folder / f"{name}.py").read_bytes() == code.encode()
            label = classification(receipt)
            if role == "MUTANT":
                counts[label] += 1
            if receipt["execution_status"] != "COMPLETED":
                if role == "CONTROL":
                    invalid_controls.append(name)
                detail_lines.append(f"| {task} | {name} | unavailable | unavailable | {label} | unavailable | {receipt['outer_seconds']:.6f} |")
                continue
            result = receipt["result"]
            assert receipt["returncode"] == 0
            assert json.loads((folder / f"{name}.stdout").read_bytes()) == result
            assert not (folder / f"{name}.stderr").read_bytes()
            assert result["candidate_sha256"] == digest(code.encode())
            assert result["task_id"] == task and result["id"] == name and result["role"] == role
            assert result["grader_verdict"] == grader_verdict(result["grader"])
            if reference_hashes is None and name == "reference-before":
                reference_hashes = {s: g["expected_sha256"] for s, g in result["grader"].items()}
            for split, grading in result["grader"].items():
                assert grading["input_count"] == len(fixture[split + "_input"])
                assert grading["checked_count"] == len(grading["details"])
                assert grading["passed_count"] == sum(grading["details"])
                assert all(type(x) is bool for x in grading["details"])
                if reference_hashes:
                    assert grading["expected_sha256"] == reference_hashes[split]
                split_calls += 1
                input_checks += grading["checked_count"]
            witness = result["witness"]
            if result["grader_verdict"] != "PASS":
                assert witness["status"] == "NOT_RUN" and witness["checked_count"] == 0
            elif witness["status"] in ("FOUND", "NOT_FOUND_WITHIN_BUDGET"):
                assert witness["input_sha256"] == digest(json_bytes(cases))
                assert witness["checked_count"] == len(witness["observations"]) == len(cases)
                failures, differences, first = 0, 0, None
                for index, (case, observed) in enumerate(zip(cases, witness["observations"], strict=True)):
                    truth = encode(expected(task, case["args"]))
                    assert observed["index"] == index
                    assert observed["expected"] == observed["reference"] == truth
                    holds = observed["observed"] == truth
                    assert observed["property_holds"] is holds and observed["diverges"] is (not holds)
                    failures += int(not holds)
                    differences += int(not holds)
                    if not holds and first is None:
                        first = {"index": index, "input": case, "expected": truth,
                                 "reference": truth, "observed": observed["observed"]}
                assert witness["failure_count"] == failures and witness["reference_divergence_count"] == differences
                assert witness["first_witness"] == first
                assert witness["status"] == ("FOUND" if failures else "NOT_FOUND_WITHIN_BUDGET")
            if role == "CONTROL":
                if not control_valid(receipt, len(cases)):
                    invalid_controls.append(name)
                control_checks += witness.get("checked_count") or 0
                control_times.append({"id": name, "full_grader_seconds": result["full_grader_seconds"],
                                      "outer_seconds": receipt["outer_seconds"]})
            else:
                full_survivors += int(result["grader_verdict"] == "PASS")
                findings += int(label == "CONFIRMED_SPEC_VIOLATION")
                mutant_checks += witness.get("checked_count") or 0
                if result["grader"].get("base", {}).get("status") == "pass":
                    base_survivors.append(name)
                    if result["grader"].get("plus", {}).get("status") == "fail":
                        plus_only_kills.append(name)
            values = [f"{result['grader'][s]['passed_count']}/{result['grader'][s]['input_count']}" if s in result['grader'] else 'unavailable' for s in ('base', 'plus')]
            detail_lines.append(f"| {task} | {name} | {values[0]} | {values[1]} | {label} | {witness.get('checked_count')} | {receipt['outer_seconds']:.6f} |")
        if record["status"] == "COMPLETED":
            assert not invalid_controls
        summary["tasks"].append({"task_id": task, "status": record["status"], "generated": len(generated),
            "evaluated_mutants": sum(counts.values()), "cap_excluded": len(pool["excluded_by_cap"]), "classifications": dict(counts),
            "full_survivors": full_survivors, "confirmed_violating_candidates": findings,
            "distinct_omissions": 0 if findings == 0 else None, "confirmation_yield": findings / full_survivors if full_survivors else None,
            "base_survivors": base_survivors, "plus_rejections_after_base_pass": plus_only_kills,
            "invalid_controls": invalid_controls, "control_times": control_times,
            "grader_split_invocations": split_calls, "grader_input_checks": input_checks,
            "control_property_checks": control_checks, "mutant_property_checks": mutant_checks,
            "unique_witness_inputs": len({json.dumps(c['args'], sort_keys=True) for c in cases}),
            "task_execution_seconds": record["total_execution_seconds"],
            "unused_execution_budget_seconds": record["unused_execution_budget_seconds"]})
    summary["totals"] = {key: sum(t[key] for t in summary["tasks"]) for key in
        ("generated", "evaluated_mutants", "cap_excluded", "full_survivors", "confirmed_violating_candidates", "grader_split_invocations", "grader_input_checks", "control_property_checks", "mutant_property_checks")}
    summary["conclusion"] = "NO_CONFIRMED_OMISSION" if summary['totals']['confirmed_violating_candidates'] == 0 else "LOCAL_FINDINGS_REQUIRE_REPAIR_AND_PRIOR_WORK_CHECK"
    detail_lines += ["", f"Totals: {json.dumps(summary['totals'], sort_keys=True)}",
                     f"Total controller seconds: {outcome['total_execution_seconds']:.6f}.",
                     "These are finite task/candidate counts, not population rates. Human effort is unmeasured; approval-related interruption makes the initial-to-final wall span unsuitable as an engineering estimate.", ""]
    return summary, '\n'.join(detail_lines)


def package(prepared: Path, raw: Path, out: Path) -> None:
    """Copy prepared and execution evidence unchanged with a complete hash ledger."""
    revision = clean_revision(ROOT)
    summary, measurements = verify(prepared, raw)
    out.mkdir(parents=True, exist_ok=False)
    payloads = {}
    for prefix, source in (("prepared", prepared), ("raw", raw)):
        for path in sorted(source.rglob('*')):
            if path.is_file():
                name = prefix + '/' + path.relative_to(source).as_posix()
                target = out / name
                target.parent.mkdir(parents=True, exist_ok=True)
                data = path.read_bytes()
                target.write_bytes(data)
                payloads[name] = {"sha256": digest(data), "bytes": len(data)}
    for name, data in (("summary.json", json_bytes(summary)), ("MEASUREMENTS.md", measurements.encode())):
        (out / name).write_bytes(data)
        payloads[name] = {"sha256": digest(data), "bytes": len(data)}
    (out / 'manifest.json').write_bytes(json_bytes({"packaging_revision": revision, "source_dirty": False,
        "run_source_revision": summary['run_source_revision'], "payloads": payloads,
        "copy_rule": "All prepared and raw files are copied byte-for-byte, with no text normalization."}))
    print(json.dumps({"payloads": len(payloads), "totals": summary['totals'], "conclusion": summary['conclusion']}))


def main() -> None:
    """Verify and package one completed reserved-task run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    package(args.prepared, args.raw, args.out)


if __name__ == '__main__':
    main()
