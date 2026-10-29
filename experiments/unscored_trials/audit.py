"""Choose reproducible source-to-arithmetic cases; human review stays pending."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from urllib.parse import quote

from experiments.unscored_trials import inventory


def read_csv(path: Path) -> list[dict]:
    """Read generated tables, never live or outcome-adjudicated labels."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build(analysis_dir: Path, output_dir: Path) -> dict:
    """Select first source-hash case in each prespecified diagnostic category."""
    provenance = inventory.clean_provenance()
    if output_dir.exists():
        raise FileExistsError("preserve prior audit worksheets")
    records = []
    manifest = json.loads((analysis_dir / "source_manifest.json").read_bytes())
    eligibility = {row["submission"]: row for row in read_csv(analysis_dir / "eligibility.csv")}
    index_path = analysis_dir / "executions.csv"
    for shard in read_csv(index_path):
        path = analysis_dir / shard["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != shard["sha256"]:
            raise ValueError("execution shard differs from canonical index")
        records.extend(read_csv(path))
    records = [row for row in records if row.get("record_kind") == "named_final_record"]
    ordered = sorted(records, key=lambda row: (row["source_sha256"], row["source_path"]))
    uuids, tasks = defaultdict(list), defaultdict(list)
    def task_key(row: dict) -> tuple:
        return tuple(row.get(key) for key in ("submission", "task_name", "task_git_url", "task_git_commit", "task_path", "task_checksum"))
    for row in ordered:
        uuids[(row["submission"], row["trial_uuid"])].append(row)
        tasks[task_key(row)].append(row)
    native = {(row["job_path"], row.get("eval_key")): row
              for row in read_csv(analysis_dir / "native_score_reproduction.csv")}
    candidates = {
        "O1": [row for row in ordered if row["reward_status"] == "scored_zero" and row["exception_present"] == "False"],
        "O2": [row for row in ordered if row["score_present"] == "True" and
               len({item["trial_uuid"] for item in tasks[task_key(row)]}) > 1],
        "O3": [row for row in ordered if row["reward_status"] in {"absent_verifier", "null_verifier", "absent_rewards", "null_rewards"}],
        "D1": [row for row in ordered if row["score_present"] == "True" and row["exception_present"] == "True"],
        "D2": [row for row in ordered if len(uuids[(row["submission"], row["trial_uuid"])]) > 1],
    }
    descriptions = {"O1": "recorded zero without exception", "O2": "distinct-UUID repetition on same task",
                    "O3": "named unscored record with defined native zero", "D1": "valid score with exception",
                    "D2": "repeated UUID export or conflict", "D3": "summary name without raw record"}
    worksheet = []
    for case, rows in candidates.items():
        result = {"case": case, "category": descriptions[case], "human_review_status": "PENDING",
                  "independent_adjudication": False, "selection_rule": "first(source_sha256,source_path) within category"}
        if not rows:
            worksheet.append({**result, "case_status": "NOT_AVAILABLE"})
            continue
        row = rows[0]
        result.update({key: row.get(key) for key in ("submission", "job_path", "source_path", "source_sha256", "trial_uuid", "trial_name",
                                                    "task_name", "task_git_url", "task_git_commit", "task_path", "task_checksum",
                                                    "reward_status", "reward_raw", "reward_decimal", "exception_class", "started_at", "finished_at")})
        result.update(case_status="AVAILABLE", json_pointer="/verifier_result/rewards/reward",
                      eligible_primary=eligibility[row["submission"]]["eligible_primary"],
                      source_url=f'https://huggingface.co/datasets/{manifest["dataset"]}/raw/{manifest["revision"]}/' + quote(row["source_path"], safe="/"))
        key = row.get("eval_key")
        check = native.get((row["job_path"], key)) or native.get((row["job_path"], key.replace("/", "-") if key else key))
        if check and check.get("native_denominator") and int(check["native_denominator"]) > 0 and row.get("native_reward_decimal"):
            denominator = int(check["native_denominator"])
            value = Fraction(row["native_reward_decimal"])
            result.update(native_job_denominator=denominator, native_contribution=str(value / denominator),
                          native_reproduction_status=check.get("native_status"),
                          native_weight=str(Fraction(1, denominator)),
                          completion_contribution_lower=str(value / denominator),
                          completion_contribution_upper=str(Fraction(1, denominator) if row["score_present"] == "False" else value / denominator))
        if case == "O2":
            result["comparison_source"] = next(item["source_path"] for item in tasks[task_key(row)]
                                                if item["trial_uuid"] != row["trial_uuid"])
        if case == "D2":
            result["source_aliases"] = json.dumps([item["source_path"] for item in uuids[(row["submission"], row["trial_uuid"])]])
        result["interpretation"] = "native operational accounting; completion is hypothetical, not recovered outcomes"
        worksheet.append(result)
    absent = []
    for job in read_csv(analysis_dir / "reconciliation.csv"):
        for name in json.loads(job.get("summary_names_missing_raw") or "[]"):
            source = job["job_path"] + "/" + name + "/result.json"
            absent.append((hashlib.sha256(source.encode()).hexdigest(), source, job))
    result = {"case": "D3", "category": descriptions["D3"], "human_review_status": "PENDING", "independent_adjudication": False}
    if absent:
        _, source, job = min(absent, key=lambda item: item[:2])
        result.update(case_status="AVAILABLE", submission=job["submission"], job_path=job["job_path"], source_path=source,
                      json_pointer="/stats/evals/*/reward_stats or exception_stats",
                      interpretation="summary-only evidence; verify recorded reward if any, do not invent an unscored planned execution")
    else:
        result["case_status"] = "NOT_AVAILABLE"
    worksheet.append(result)
    output_dir.mkdir(parents=True)
    with (output_dir / "human_audit_worksheet.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for row in worksheet for key in row}))
        writer.writeheader()
        writer.writerows(worksheet)
    receipt = {"provenance": provenance, "execution_index_sha256": hashlib.sha256(index_path.read_bytes()).hexdigest(),
               "selected_cases": len(worksheet), "human_review_completed": False,
               "selection_is_diagnostic_not_prevalence_sampling": True,
               "native_weight_scope": "per-eval named final records; equal-task and deduplicated weights differ"}
    (output_dir / "audit_provenance.json").write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    return receipt


def main() -> None:
    """Leave adjudication to a real reviewer without filling their decisions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.analysis_dir, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
