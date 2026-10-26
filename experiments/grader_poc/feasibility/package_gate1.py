"""Check calibration receipts and retain code-derived Gate1 measurements."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from .calibration import expected_from_spec, property_inputs
from .prepare import HERE, ROOT, clean_revision, digest
from .run_calibration import control_code, control_passed, json_bytes


def package(raw: Path, out: Path) -> None:
    """Bind complete local run files; do not promote calibration into discovery."""
    revision = clean_revision(ROOT)
    outcome = json.loads((raw / "outcome.json").read_bytes())
    config_raw = (HERE / "config.json").read_bytes()
    config = json.loads(config_raw)
    fixture_raw = (HERE / "fixtures/calibration.json").read_bytes()
    fixture = json.loads(fixture_raw)
    assert outcome["source_dirty"] is False
    assert outcome["config_sha256"] == digest(config_raw)
    assert outcome["calibration_sha256"] == digest(fixture_raw)
    assert outcome["held_out_executions"] == 0
    assert outcome["calibration_gate"] == "PASS"
    cases = property_inputs(config)
    assert json.loads((raw / "property_inputs.json").read_bytes()) == cases
    expected_hash = digest(json_bytes([
        expected_from_spec(c["numbers"], c["threshold"], config["domain"])
        for c in cases
    ]))
    counts = {s: len(fixture[s + "_input"]) for s in ("base", "plus")}
    expected_names = {f"{variant}-{i + 1:03d}" for variant in ("reference", "alternative")
                      for i in range(config["repetitions"])}
    assert {r["run"] for r in outcome["receipts"]} == expected_names
    assert len(outcome["receipts"]) == len(expected_names)
    lines = ["# Gate1 measurements (generated)", "",
             "| Run | Base pass | Plus pass | Scoped P checks | P failures | Grader seconds | Outer seconds |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for receipt in outcome["receipts"]:
        name = receipt["run"]
        assert json.loads((raw / f"{name}.json").read_bytes()) == receipt
        result = receipt["result"]
        assert json.loads((raw / f"{name}.stdout").read_bytes()) == result
        assert not (raw / f"{name}.stderr").read_bytes()
        assert result["task_id"] == config["calibration_id"]
        assert result["candidate_sha256"] == digest(control_code(fixture, result["variant"]).encode())
        assert control_passed(receipt, counts, len(cases), config["full_grader_target_seconds"])
        prop = result["property"]
        assert prop["input_sha256"] == digest(json_bytes(cases))
        assert prop["observed_sha256"] == prop["expected_sha256"] == expected_hash
        for split, count in counts.items():
            details = result["grader"][split]["details"]
            assert len(details) == count and all(value is True for value in details)
        lines.append(f"| {name} | {counts['base']}/{counts['base']} | {counts['plus']}/{counts['plus']} | "
                     f"{prop['checked_count']} | {len(prop['mismatches'])} | "
                     f"{result['full_grader_seconds']:.6f} | {receipt['outer_seconds']:.6f} |")
    events = json.loads((HERE / "setup_events.json").read_bytes())
    elapsed = (datetime.fromisoformat(outcome["finished_at_utc"]) -
               datetime.fromisoformat(events["recorded_session_start_utc"])).total_seconds()
    lines += ["", f"Controller execution: {outcome['total_execution_seconds']:.6f} seconds.",
              f"Recorded assistant session interval to successful completion: {elapsed / 60:.3f} minutes.",
              "This interval includes orientation, acquisition, dependency setup, coding, tests and the failed preflight; it is not active human labor or isolated oracle effort.",
              "Human setup minutes: unmeasured. Held-out runtime and setup costs: unmeasured.",
              f"Scoped corpus: {sum(c['kind'] == 'small_grid' for c in cases)} exhaustive small-grid cases plus "
              f"{sum(c['kind'] == 'seeded' for c in cases)} seeded cases; repetitions reuse this corpus.",
              "Grader seconds sum the native base/plus calls, including their child-process overhead. Outer seconds additionally include interpreter/imports, reference-output preparation and P checks.",
              "No model calls, mutation candidates, held-out executions or discovery comparison were performed.", ""]
    out.mkdir(parents=True, exist_ok=False)
    payloads = {}
    for source in sorted(raw.iterdir()):
        if source.is_file():
            data = source.read_bytes()
            (out / source.name).write_bytes(data)
            payloads[source.name] = {"sha256": digest(data), "bytes": len(data)}
    measurements = "\n".join(lines).encode()
    (out / "MEASUREMENTS.md").write_bytes(measurements)
    payloads["MEASUREMENTS.md"] = {"sha256": digest(measurements), "bytes": len(measurements)}
    (out / "manifest.json").write_bytes(json_bytes({
        "packaging_revision": revision, "source_dirty": False,
        "run_source_revision": outcome["source_revision"],
        "raw_copy_rule": "byte-identical copies of all files in the completed run directory",
        "payloads": payloads,
    }))
    print(json.dumps({"payloads_checked": len(payloads), "calibration_gate": "PASS",
                      "recorded_assistant_interval_minutes": elapsed / 60}))


def main() -> None:
    """Package a completed attempt into a fresh, non-overwriting directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    package(args.raw, args.out)


if __name__ == "__main__":
    main()
