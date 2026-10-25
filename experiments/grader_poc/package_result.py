"""Assemble a reviewable local evidence packet from completed experiment logs."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from experiments.grader_poc.run_trial import file_hashes, git_output


def digest(data: bytes) -> str:
    """Hash raw bytes so redacted copies remain distinguishable from originals."""
    return hashlib.sha256(data).hexdigest()


def package(work: Path) -> dict:
    """Refuse incomplete evidence and generate the closing report from observations."""
    root = Path(__file__).resolve().parents[2]
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit assembler and narrative source before generation")
    here = Path(__file__).parent
    out = here / "results"
    out.mkdir(exist_ok=False)
    home = str(Path.home())
    posix_home = home.replace("\\", "/")
    wsl_home = "/mnt/" + posix_home[0].lower() + posix_home[2:] if ":" in posix_home else posix_home
    replacements = sorted({home, home.replace("\\", "\\\\"), posix_home, wsl_home}, key=len, reverse=True)
    copies = []

    def copy_file(source: Path, relative: str) -> None:
        raw = source.read_bytes()
        text = raw.decode("utf-8-sig")
        for prefix in replacements:
            text = text.replace(prefix, "${HOST_HOME}")
        text = re.sub(r"/tmp/warrant-grader-poc-[0-9]+-venv", "${HARBOR_VENV}", text)
        data = text.encode("utf-8")
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        copies.append({"path": relative, "raw_sha256": digest(raw),
                       "packaged_sha256": digest(data), "bytes_changed": data != raw})

    trials = []
    for run in sorted((work / "grader-poc-runs").iterdir()):
        if not run.is_dir():
            continue
        result = json.loads((run / "outcome.json").read_text())
        if result["status"] != "COMPLETED" or not result["task_unchanged"] or not result["matches_expected"]:
            raise ValueError("Incomplete or unexpected full trial: " + run.name)
        trial_dir = (run / result["trials"][0]["path"]).parent
        ctrf = json.loads((trial_dir / "verifier/ctrf.json").read_text())["results"]
        trials.append({"run": run.name, "reward": result["reward"],
                       "tests": ctrf["summary"], "source_commit": result["source_commit"],
                       "elapsed_seconds": result["elapsed_seconds"],
                       "candidate_hashes": file_hashes(trial_dir / "artifacts/app/app"),
                       "verifier_hashes": {p: h for p, h in result["task_hashes"].items() if p.startswith("tests/")},
                       "separate_verifier": result["trials"][0]["verifier_environment_mode"] == "separate"})
        for path in sorted(run.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                copy_file(path, "runs/" + run.name + "/" + path.relative_to(run).as_posix())
    by_name = {row["run"]: row for row in trials}
    pairs = [("Original broken", "original-001", "original-repaired-001"),
             ("Supplied reference", "reference-001", "reference-repaired-001"),
             ("Equivalent merge control", "equivalent-001", "equivalent-repaired-001"),
             ("Omit-max mutant", "omit-max-001", "omit-max-repaired-001")]
    for _, old, new in pairs:
        if by_name[old]["candidate_hashes"] != by_name[new]["candidate_hashes"]:
            raise ValueError("Candidate changed between original and repaired graders")
    repeat_identical = by_name["omit-max-001"]["candidate_hashes"] == by_name["omit-max-repeat-001"]["candidate_hashes"]
    if not repeat_identical or len(trials) != len(pairs) * 2 + 1:
        raise ValueError("Unexpected trial set or nonidentical repeat")
    original_verifier = by_name["original-001"]["verifier_hashes"]
    repaired_verifier = by_name["original-repaired-001"]["verifier_hashes"]
    if set(original_verifier) != set(repaired_verifier) or [p for p in original_verifier if original_verifier[p] != repaired_verifier[p]] != ["tests/test_outputs.py"]:
        raise ValueError("Unexpected verifier changes")
    for row in trials:
        expected = repaired_verifier if "repaired" in row["run"] else original_verifier
        if row["verifier_hashes"] != expected or not row["separate_verifier"]:
            raise ValueError("Verifier identity or separation mismatch")
    diag_dir = work / "grader-poc-diagnostic-001"
    diagnostic = json.loads((diag_dir / "outcome.json").read_text())
    attempts = [json.loads(line) for line in (diag_dir / "attempts.jsonl").read_text().splitlines()]
    if diagnostic["status"] != "CONFIRMED_SCOPED_DISAGREEMENT" or not diagnostic["single_deletion_minimal"]:
        raise ValueError("Diagnostic gate not established")
    for candidate in diagnostic["candidates"].values():
        if candidate["hashes"] != by_name[candidate["run"]]["candidate_hashes"]:
            raise ValueError("Diagnostic is not bound to full grader candidate")
    for path in diag_dir.iterdir():
        if path.is_file():
            copy_file(path, "diagnostic/" + path.name)
    for path in (work / "grader-poc-cases").iterdir():
        if path.is_file():
            copy_file(path, "cases/" + path.name)
    for name in ("grader-poc-dependencies.txt", "grader-poc-verifier-dependencies.txt",
                 "grader-poc-preflight-image.txt", "grader-poc-docker-version.json",
                 "harbor-poc-install.log", "harbor-wheel-build.log", "harbor-offline-install.log"):
        copy_file(work / name, "environment/" + name)
    copy_file(work / "terminal-bench-poc/LICENSE", "TERMINAL_BENCH_LICENSE.txt")
    wheel_manifest = [{"file": p.name, "bytes": p.stat().st_size, "sha256": digest(p.read_bytes())}
                      for p in sorted((work / "grader-wheel-cache").glob("*.whl"))]
    (out / "environment/wheel-hashes.json").write_bytes((json.dumps(wheel_manifest, indent=2) + "\n").encode())
    frozen = (work / "grader-poc-dependencies.txt").read_text(encoding="utf-8-sig").splitlines()
    requirements = [line for line in frozen if not line.lower().startswith("harbor")]
    (out / "environment/harbor-dependencies.txt").write_bytes(("\n".join(requirements) + "\n").encode())
    summary = {"schema_version": 1, "evidence_kind": "adaptive_stress_test",
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "assembler_commit": git_output(root, "rev-parse", "HEAD"), "source_dirty": False,
               "config_sha256": digest((here / "config.json").read_bytes()),
               "trials": trials, "repeat_candidate_identical": repeat_identical,
               "diagnostic_status_counts": dict(Counter(row["status"] for row in attempts)),
               "diagnostic_attempts": len(attempts), "diagnostic_container_calls": diagnostic["container_calls"],
               "diagnostic_container_seconds": diagnostic["container_elapsed_seconds"],
               "full_trial_seconds_sum": sum(row["elapsed_seconds"] for row in trials),
               "initial": diagnostic["initial"], "reduced": diagnostic["reduced"],
               "single_deletion_minimal": diagnostic["single_deletion_minimal"],
               "control_checks": sum(row["purpose"] == "control" for row in attempts),
               "population_rate_claim": False, "api_or_gpu_spend_inr": 0,
               "focused_investigation_hours": None, "external_reviewer_hours": None,
               "ordinary_assertion_baseline_hours": None,
               "scope": diagnostic["config"]["oracle_scope"]}
    (out / "summary.json").write_bytes((json.dumps(summary, indent=2) + "\n").encode())
    manifest = {"assembler_commit": summary["assembler_commit"], "copies": copies,
                "redaction": "Host home paths and the experiment temporary venv are replaced by role placeholders; UTF-8 BOMs removed. Raw originals remain in the local work directory. Container paths and candidate source are retained.",
                "packaged_files": file_hashes(out)}
    (out / "evidence-manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode())
    table = ["| Candidate | Original grader | Proposed repair |", "|---|---|---|"]
    for label, old, new in pairs:
        cells = []
        for name in (old, new):
            row = by_name[name]
            cells.append(f"{'Accept' if row['reward'] else 'Reject'}; {row['tests']['passed']}/{row['tests']['tests']} tests pass")
        table.append("| " + " | ".join([label] + cells) + " |")
    reduced = diagnostic["reduced"]
    tokens = {"MATRIX": "\n".join(table), "TRIAL_COUNT": str(len(trials)),
              "TRIAL_SECONDS": f"{summary['full_trial_seconds_sum']:.2f}",
              "DIAGNOSTIC_SECONDS": f"{summary['diagnostic_container_seconds']:.2f}",
              "DIAGNOSTIC_CALLS": str(summary["diagnostic_container_calls"]),
              "CONTROL_CHECKS": str(summary["control_checks"]),
              "TRACE": json.dumps([[e["time"], e["value"]] for e in reduced["events"]]),
              "EXPECTED": json.dumps(reduced["expected"]["sessions"]),
              "OBSERVED": json.dumps(reduced["observation"]["sessions"]),
              "ASSEMBLER_COMMIT": summary["assembler_commit"],
              "DIAGNOSTIC_COMMIT": diagnostic["source_commit"],
              "CONFIG_HASH": summary["config_sha256"]}
    report = (here / "REPORT_TEMPLATE.md").read_text(encoding="utf-8")
    for key, value in tokens.items():
        report = report.replace("{{" + key + "}}", value)
    if "{{" in report:
        raise ValueError("Unresolved report template token")
    report_path = root / "reports/PHASE-GRADER-P0-P1.md"
    if report_path.exists():
        raise FileExistsError(report_path)
    report_path.write_bytes(report.encode())
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    summary = package(parser.parse_args().work.resolve())
    print(json.dumps({"trials": len(summary["trials"]), "repeat_candidate_identical": summary["repeat_candidate_identical"],
                      "diagnostic_status_counts": summary["diagnostic_status_counts"]}, indent=2))
