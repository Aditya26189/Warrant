"""Preserve successful, negative and invalid P2 attempts with explicit custody."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from experiments.grader_poc.run_trial import file_hashes, git_output, write_receipt


def read(path: Path) -> dict:
    return json.loads(path.read_bytes())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(raw: str) -> Path:
    if raw.startswith("/mnt/c/"):
        return Path("C:/" + raw[len("/mnt/c/"):])
    return Path(raw)


def summarize(work: Path, here: Path) -> dict:
    """Derive counts from receipts; incomplete executions remain visible."""
    full = []
    for path in sorted((work / "grader-p2-full").glob("*/outcome.json")):
        item = read(path)
        row = {"run": path.parent.name, "status": item["status"], "reward": item.get("reward"),
               "elapsed_seconds": item["elapsed_seconds"], "source_commit": item["source_commit"],
               "task_unchanged": item["task_unchanged"]}
        task = local_path(item["command"][item["command"].index("-p") + 1])
        if file_hashes(task) != item["task_hashes"]:
            raise ValueError("Full-run task drift: " + path.parent.name)
        if item["status"] == "COMPLETED":
            trial = (path.parent / item["trials"][0]["path"]).parent
            ctrf = trial / "verifier/ctrf.json"
            if ctrf.exists():
                row["tests"] = read(ctrf)["results"]["summary"]
            if row["run"].startswith("maximum-"):
                expected = file_hashes(task / "environment/app")
                expected.update(file_hashes(task / "solution/files"))
                actual = file_hashes(trial / "artifacts/app/app")
            else:
                expected = file_hashes(task / "environment/src")
                expected["worker/worker.py"] = digest(task / "solution/worker.py")
                expected["worker/requirements.txt"] = digest(task / "solution/requirements.txt")
                actual = file_hashes(trial / "artifacts/app/src")
            if expected != actual:
                raise ValueError("Collected candidate differs: " + row["run"])
            row["candidate_hashes"] = actual
            row["candidate_matches_declared"] = True
        full.append(row)
    session = read(work / "grader-p2-components/session-002/outcome.json")
    session_rows = []
    for row in session["result"]["results"]:
        session_rows.append({"candidate": row["candidate"], "counts": dict(Counter(x["status"] for x in row["classification"])),
                             "by_split": {split: dict(Counter(x["status"] for x in row["classification"] if x["split"] == split)) for split in ("discovery", "held_out")},
                             "elapsed_seconds": row["elapsed_seconds"]})
    math = read(work / "grader-p2-components/math-003/outcome.json")
    math_rows = []
    for row in math["result"]["results"]:
        obs = row["observation"]
        suite = obs.get("suite", {})
        math_rows.append({"candidate": row["candidate"], "mutation": row.get("mutation"),
                          "status": obs["status"], "suite": {k: suite[k] for k in ("status", "total", "correct", "threshold", "elapsed_seconds") if k in suite},
                          "disagreements": row.get("disagreements"), "diagnostic_errors": row.get("diagnostic_errors"),
                          "diagnostic_seconds": obs.get("diagnostic_seconds"), "elapsed_seconds": row["elapsed_seconds"]})
    payment = read(work / "grader-p2-components/payments-002/outcome.json")
    predicates = payment["result"]["predicates"]["observation"]["results"]
    workers = [{"candidate": r["candidate"], "status": r["observation"]["status"], "disagreements": r.get("disagreements"),
                "sha256": r["sha256"], "results": r["observation"].get("results")} for r in payment["result"]["workers"]]
    for row in full:
        if row["run"].startswith("payments-") and row["status"] == "COMPLETED":
            name = row["run"].removeprefix("payments-").removesuffix("-001").removesuffix("-repeat")
            match = next((r for r in workers if r["candidate"] == name), None)
            if match is None or row["candidate_hashes"]["worker/worker.py"] != match["sha256"]:
                raise ValueError("Payment component/full-trial candidate mismatch")
            row["component_matches_full_candidate"] = True
    cancellation = read(work / "grader-p2-cancellation-002/outcome.json")
    return {"full_trials": full, "session_cases": session["result"]["cases"], "session": session_rows,
            "math_cases": math["result"]["cases"], "math": math_rows,
            "payment_predicates": [{"id": r["id"], "status": r["status"]} for r in predicates],
            "payment_workers": workers, "cancellation": cancellation["checks"],
            "population_rate_claim": False, "independent_human_reproduction": False,
            "method_effort_equivalence_established": False,
            "math_batch002": "INVALID_COMPARISON: formatting control and eight mutants failed Python3.11 parsing",
            "full_math_task": "NOT_RUN: required GPU inference outside resource scope",
            "direct_review": read(here / "direct_review.json"),
            "validation": read(work / "grader-p2-validation/unit-summary.json"),
            "math_invalid_batch_elapsed_seconds": read(work / "grader-p2-components/math-002/outcome.json")["elapsed_seconds"],
            "math_corrected_batch_elapsed_seconds": math["elapsed_seconds"],
            "effort": read(work / "grader-p2-validation/effort.json")}


def archive(work: Path, tb: Path) -> dict:
    """Large Kafka snapshots remain locally; hash their omission explicitly."""
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit archival source first")
    original = here.parent / "results"
    previous = read(original / "evidence-manifest.json")["packaged_files"]
    for name, value in previous.items():
        if digest(original / name) != value:
            raise ValueError("Original evidence drift")
    hardening = here.parent / "hardening"
    prior = read(hardening / "manifest.json")["packaged_files"]
    for name, value in prior.items():
        if digest(hardening / name) != value:
            raise ValueError("Hardening evidence drift")
    summary = summarize(work, here)
    summary.update(archive_source_commit=git_output(root, "rev-parse", "HEAD"),
                   original_payloads_verified=len(previous), hardening_payloads_verified=len(prior))
    out = here / "evidence"
    out.mkdir(exist_ok=False)
    home = str(Path.home())
    posix = home.replace("\\", "/")
    wsl = "/mnt/" + posix[0].lower() + posix[2:] if ":" in posix else posix
    replacements = sorted({home, home.replace("\\", "\\\\"), posix, wsl}, key=len, reverse=True)
    copies, omitted = [], []

    def copy(source: Path, relative: str) -> None:
        raw = source.read_bytes()
        record = {"path": relative, "raw_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        if len(raw) > 10_000_000 or source.suffix in (".gz", ".pyc"):
            omitted.append({**record, "reason": "Large/binary generated runtime artifact retained in local raw directory; no Git payload"})
            return
        try:
            value = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            omitted.append({**record, "reason": "Binary artifact retained locally"})
            return
        for prefix in replacements:
            value = value.replace(prefix, "${HOST_HOME}")
        value = re.sub(r"/tmp/warrant-grader-poc-[0-9]+-venv", "${HARBOR_VENV}", value)
        data = value.encode()
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        copies.append({**record, "packaged_sha256": hashlib.sha256(data).hexdigest()})

    folders = ("grader-p2-full", "grader-p2-components", "grader-p2-cancellation-001", "grader-p2-cancellation-002",
               "grader-p2-maximum-cases", "grader-p2-payment-cases", "grader-p2-validation")
    for folder in folders:
        source_root = work / folder
        for path in sorted(source_root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                copy(path, folder + "/" + path.relative_to(source_root).as_posix())
    # Bind primary-source contracts without duplicating all task environments.
    for task in ("distributed-dedup", "math-eval-grader", "payments-pipeline-fix"):
        for name in ("instruction.md", "task.toml"):
            copy(tb / "tasks" / task / name, "upstream/" + task + "/" + name)
    for name in ("solution/grader.py", "tests/test_outputs.py", "tests/grader_suite.jsonl", "tests/Dockerfile"):
        copy(tb / "tasks/math-eval-grader" / name, "upstream/math-eval-grader/" + name)
    copy(original / "TERMINAL_BENCH_LICENSE.txt", "TERMINAL_BENCH_LICENSE.txt")
    summary["omitted_runtime_artifacts"] = omitted
    summary["packaged_payloads_excluding_manifest"] = len(copies) + 1
    write_receipt(out / "summary.json", summary)
    write_receipt(out / "manifest.json", {"copies": copies, "omitted": omitted, "packaged_files": file_hashes(out),
                  "redaction": "Host-home and temporary-venv paths replaced by role placeholders; UTF8 BOM removed; raw hashes retained. __pycache__ excluded."})
    from experiments.grader_poc.p2.report_p2 import render
    render(summary, root / "reports/PHASE-GRADER-P2.md")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--tb", type=Path, required=True)
    args = parser.parse_args()
    result = archive(args.work.resolve(), args.tb.resolve())
    print(json.dumps({"full_trials": len(result["full_trials"]), "original_verified": result["original_payloads_verified"],
                      "hardening_verified": result["hardening_payloads_verified"], "omitted": len(result["omitted_runtime_artifacts"])}))
