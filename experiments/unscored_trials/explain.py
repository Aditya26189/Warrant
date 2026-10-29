"""Post hoc scalar diagnostics that never amend frozen native reconciliation.

A matching whole-job number does not establish matched evaluation groups,
indices, identities or populations. Summary-internal arithmetic uses its own
named reward/exception union only when a global counter supports that denominator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

from experiments.unscored_trials import inventory, normalize


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fraction(value: object) -> Fraction:
    if isinstance(value, bool) or value is None:
        raise ValueError("expected finite numeric reward")
    decimal = Decimal(str(value))
    if not decimal.is_finite() or not 0 <= decimal <= 1:
        raise ValueError("expected reward in [0,1]")
    return Fraction(decimal)


def _flag(value: object) -> bool:
    if value is True or value == "True":
        return True
    if value is False or value == "False":
        return False
    raise ValueError("ambiguous normalized boolean")


def _pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def diagnose_job(
    job_raw: dict | None, records: list[dict], job_check: dict,
    tolerance: Fraction = Fraction(1, 10**12),
) -> dict:
    """Keep joint reconciliation, scalar equality and summary populations distinct.

    Records are all named-final ledger rows for this job before cross-job
    deduplication. Scores survive exceptions. No grouping alias is introduced.
    """
    if not isinstance(tolerance, Fraction) or tolerance < 0:
        raise ValueError("tolerance must be a nonnegative exact Fraction")
    result: dict[str, Any] = {
        "job_path": job_check.get("job_path"), "submission": job_check.get("submission"),
        "strict_joint_native_status": job_check.get("native_status", "unavailable"),
        "raw_named_final_record_count": len(records),
        "raw_native_reward_mass": None, "raw_native_zero_mean": None,
        "whole_job_numeric_status": "unavailable", "whole_job_unavailable_reasons": [],
        "published_mean_count": 0, "published_mean": None, "published_mean_pointers": [],
        "summary_internal_status": "unavailable", "summary_internal_unavailable_reasons": [],
        "summary_reward_mass": None, "summary_mean": None,
        "summary_denominator": None, "summary_denominator_counter_fields": [],
        "summary_union_name_count": None, "summary_reward_name_count": None,
        "summary_exception_name_count": None, "summary_scored_exception_overlap_count": None,
        "summary_vs_raw_name_population": "unavailable", "summary_only_name_count": None,
        "raw_only_name_count": None, "raw_scored_exception_count": 0,
        "raw_exception_count": 0, "summary_global_counters": {},
        "summary_global_counter_matches_raw": {},
        "raw_scored_exception_reward_mass": Fraction(),
    }
    raw_issues = []
    if not records:
        raw_issues.append("no_named_raw_records")
    if job_check.get("failed_or_malformed_requested_files"):
        raw_issues.append("missing_or_malformed_requested_source")
    if job_check.get("duplicate_trial_names"):
        raw_issues.append("duplicate_trial_names")
    uuids: dict[str, set[str]] = defaultdict(set)
    names = set()
    raw_mass = Fraction()
    for row in records:
        name = row.get("trial_name")
        if not isinstance(name, str) or not name or name in names:
            raw_issues.append("missing_or_duplicate_raw_trial_name")
        names.add(name)
        if row.get("trial_uuid"):
            uuids[row["trial_uuid"]].add(row.get("semantic_hash", ""))
        if row.get("conflicting_uuid"):
            raw_issues.append("conflicting_uuid_semantics")
        try:
            if row.get("record_kind", "named_final_record") != "named_final_record" or not _flag(row.get("native_supported")):
                raise ValueError("unsupported final-record schema")
            value = _fraction(row.get("native_reward_decimal"))
            scored, exception = _flag(row.get("score_present")), _flag(row.get("exception_present"))
            result["raw_exception_count"] += int(exception)
            if not scored and value != 0:
                raise ValueError("unscored native value is not zero")
            if scored and value != _fraction(row.get("reward_decimal")):
                raise ValueError("native value discarded a valid reward")
            raw_mass += value
            if scored and exception:
                result["raw_scored_exception_count"] += 1
                result["raw_scored_exception_reward_mass"] += value
        except (ValueError, ArithmeticError):
            raw_issues.append("unsupported_or_conflicting_raw_reward")
    if any(len(values) > 1 for values in uuids.values()):
        raw_issues.append("conflicting_uuid_semantics")
    if not raw_issues:
        result.update(raw_native_reward_mass=raw_mass, raw_native_zero_mean=raw_mass / len(records))

    means: list[Fraction] = []
    summary_rewards: dict[str, Decimal] = {}
    summary_errors: dict[str, str] = {}
    summary_issues = []
    stats = job_raw.get("stats") if isinstance(job_raw, dict) else None
    evals = stats.get("evals") if isinstance(stats, dict) else None
    if isinstance(stats, dict):
        for field in ("n_trials", "n_completed_trials", "n_errors", "n_errored_trials"):
            if field in stats:
                value = stats[field]
                result["summary_global_counters"][field] = value
                expected = result["raw_exception_count"] if field in {"n_errors", "n_errored_trials"} else len(records)
                result["summary_global_counter_matches_raw"][field] = (
                    type(value) is int and value == expected)
    if not isinstance(evals, dict):
        summary_issues.append("missing_or_malformed_job_evaluations")
    else:
        for key, evaluation in sorted(evals.items()):
            if not isinstance(key, str) or not isinstance(evaluation, dict):
                summary_issues.append("malformed_evaluation")
                continue
            rewards, errors, issues = normalize._summary_indexes(evaluation)
            summary_issues.extend(issues)
            for name, value in rewards.items():
                if name in summary_rewards:
                    summary_issues.append("duplicate_or_conflicting_cross_eval_reward_name")
                summary_rewards[name] = value
            for name, error in errors.items():
                if name in summary_errors:
                    summary_issues.append("duplicate_cross_eval_exception_name")
                summary_errors[name] = error
            metrics = evaluation.get("metrics")
            if metrics in (None, []):
                continue
            if not (isinstance(metrics, list) and len(metrics) == 1
                    and isinstance(metrics[0], dict) and set(metrics[0]) == {"mean"}):
                summary_issues.append("unsupported_mean_schema")
                continue
            try:
                published, _ = normalize._decimal(metrics[0]["mean"])
                if published is None:
                    raise ValueError("unsupported published mean")
                means.append(_fraction(published))
                result["published_mean_pointers"].append(f"/stats/evals/{_pointer(key)}/metrics/0/mean")
            except (ValueError, ArithmeticError):
                summary_issues.append("unsupported_published_mean")
    result["published_mean_count"] = len(means)
    mean_issues = [] if len(means) == 1 else ["no_single_published_mean"]
    if len(means) == 1:
        result["published_mean"] = means[0]
    all_summary_issues = sorted(set(summary_issues))
    result["whole_job_unavailable_reasons"] = sorted(set(raw_issues + all_summary_issues + mean_issues))
    if not result["whole_job_unavailable_reasons"]:
        result["whole_job_numeric_status"] = (
            "match" if abs(result["raw_native_zero_mean"] - means[0]) <= tolerance else "difference")

    if not all_summary_issues:
        union = set(summary_rewards) | set(summary_errors)
        result.update(summary_union_name_count=len(union), summary_reward_name_count=len(summary_rewards),
                      summary_exception_name_count=len(summary_errors),
                      summary_scored_exception_overlap_count=len(set(summary_rewards) & set(summary_errors)),
                      summary_reward_mass=sum((Fraction(value) for value in summary_rewards.values()), Fraction()))
        if all(isinstance(name, str) and name for name in names) and len(names) == len(records):
            result.update(summary_vs_raw_name_population="same_named_population" if union == names else "different_named_populations",
                          summary_only_name_count=len(union - names), raw_only_name_count=len(names - union))
        aligned = [field for field in ("n_completed_trials", "n_trials")
                   if isinstance(stats, dict) and type(stats.get(field)) is int
                   and stats[field] > 0 and stats[field] == len(union)]
        result["summary_denominator_counter_fields"] = aligned
        if aligned:
            result["summary_denominator"] = len(union)
            result["summary_mean"] = result["summary_reward_mass"] / len(union)
        else:
            summary_issues.append("no_global_counter_aligned_to_full_summary_name_union")
    result["summary_internal_unavailable_reasons"] = sorted(set(summary_issues + mean_issues))
    if not result["summary_internal_unavailable_reasons"]:
        result["summary_internal_status"] = (
            "match" if abs(result["summary_mean"] - means[0]) <= tolerance else "difference")
    strict = result["strict_joint_native_status"]
    numeric, internal = result["whole_job_numeric_status"], result["summary_internal_status"]
    if numeric == "match":
        explanation = "strict_and_whole_job_match" if strict == "match" else "whole_job_mean_matches_despite_joint_accounting_nonmatch"
    elif numeric == "difference":
        explanation = ("whole_job_differs_but_published_mean_matches_own_summary_population"
                       if internal == "match" else "whole_job_numeric_difference_summary_" + internal)
    else:
        explanation = "whole_job_numeric_comparison_unavailable"
    result["diagnostic_classification"] = explanation
    result["interpretation"] = "post_hoc_scalar_and_population_diagnostics; no_primary_reclassification_or_official_error_claim"
    return result


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _inside(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("evidence path escapes its root")
    return path


def _shards(root: Path, descriptors: list[dict], refs: list[dict]) -> list[dict]:
    result = []
    for descriptor in descriptors:
        path = _inside(root, descriptor["path"])
        data = path.read_bytes()
        if _hash(data) != descriptor["sha256"] or len(data) != descriptor["bytes"]:
            raise ValueError("canonical JSON shard hash or length mismatch")
        rows = json.loads(data)
        if not isinstance(rows, list) or len(rows) != descriptor["entries"]:
            raise ValueError("canonical JSON shard row count mismatch")
        refs.append({"path": descriptor["path"], "sha256": _hash(data), "bytes": len(data)})
        result.extend(rows)
    return result


def build(data_root: Path, analysis_dir: Path, output_dir: Path) -> dict:
    """Generate a separate all-job diagnostic from verified canonical evidence.

    Raw job JSON is reverified against canonical source receipts. Trial arithmetic
    uses hash-verified canonical normalized ledgers with original source pointers;
    this is not a second reward adjudication or a rerun of frozen primary selection.
    """
    provenance = inventory.clean_provenance()
    if output_dir.exists():
        raise FileExistsError("preserve existing post hoc diagnostics")
    refs = []
    source_index_path, checks_index_path = analysis_dir / "source_manifest.json", analysis_dir / "jobchecks.json"
    source_index = json.loads(source_index_path.read_bytes())
    checks_index = json.loads(checks_index_path.read_bytes())
    sources = _shards(analysis_dir, source_index["sources"], refs)
    requests = _shards(analysis_dir, source_index["result_requests"], refs)
    checks = _shards(analysis_dir, checks_index["shards"], refs)
    source_by_local = {row["local_path"]: row for row in sources}
    job_requests = {row["job"]: row for row in requests if row["kind"] == "job"}
    if len(job_requests) != sum(row["kind"] == "job" for row in requests) or set(job_requests) != {row["job_path"] for row in checks}:
        raise ValueError("job source requests and canonical checks differ")
    records: dict[str, list[dict]] = defaultdict(list)
    ledger_refs: dict[str, set[str]] = defaultdict(set)
    conflicts_path = analysis_dir / "cross_submission_uuid_reconciliation.csv"
    conflicts = {row["trial_uuid"] for row in _read_csv(conflicts_path)
                 if row.get("status") == "conflicting_cross_submission_semantics"}
    index_path = analysis_dir / "executions.csv"
    for descriptor in _read_csv(index_path):
        path = _inside(analysis_dir, descriptor["path"])
        data = path.read_bytes()
        if _hash(data) != descriptor["sha256"] or len(data) != int(descriptor["bytes"]):
            raise ValueError("canonical execution shard hash or length mismatch")
        rows = _read_csv(path)
        if len(rows) != int(descriptor["rows"]):
            raise ValueError("canonical execution shard row count mismatch")
        refs.append({"path": descriptor["path"], "sha256": _hash(data), "bytes": len(data)})
        for row in rows:
            if row.get("trial_uuid") in conflicts:
                row["conflicting_uuid"] = True
            records[row["job_path"]].append(row)
            ledger_refs[row["job_path"]].add(descriptor["path"])
    tolerance = Fraction(json.loads((analysis_dir / "provenance.json").read_bytes())["analysis_config"]["native_absolute_tolerance"])
    results, raw_refs = [], []
    for check in sorted(checks, key=lambda row: row["job_path"]):
        request = job_requests[check["job_path"]]
        source = source_by_local[request["path"]]
        inventory._pinned_request(request)
        if source.get("url") != request["url"] or request.get("source_sha256") != source.get("sha256"):
            raise ValueError("canonical job request differs from source receipt")
        raw = None
        if source["status"] == "success":
            data = _inside(data_root, request["path"]).read_bytes()
            if _hash(data) != source["sha256"] or len(data) != source["size_bytes"]:
                raise ValueError("raw job cache differs from canonical source receipt")
            raw = json.loads(data, parse_float=Decimal, parse_constant=Decimal)
            raw_refs.append({"source_path": request["source_path"], "local_path": request["path"],
                             "sha256": source["sha256"], "url": source["url"]})
        row = diagnose_job(raw, records[check["job_path"]], check, tolerance)
        row.update(job_source_path=request["source_path"], job_source_sha256=source.get("sha256"),
                   job_source_url=request["url"], raw_ledger_shards=sorted(ledger_refs[check["job_path"]]))
        results.append(row)
    if set(records) - set(job_requests):
        raise ValueError("execution ledger contains a job outside canonical job sources")
    summary = {"post_hoc": True, "job_count": len(results),
               "strict_joint_status_counts": dict(Counter(row["strict_joint_native_status"] for row in results)),
               "whole_job_numeric_status_counts": dict(Counter(row["whole_job_numeric_status"] for row in results)),
               "summary_internal_status_counts": dict(Counter(row["summary_internal_status"] for row in results)),
               "classification_counts": dict(Counter(row["diagnostic_classification"] for row in results)),
               "strict_nonmatch_whole_job_status_counts": dict(Counter(row["whole_job_numeric_status"] for row in results
                                                                       if row["strict_joint_native_status"] != "match")),
               "primary_outputs_changed": False, "independent_adjudication": False,
               "official_website_error_claim": False}
    output_dir.mkdir(parents=True)
    with (output_dir / "whole_job_diagnostics.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for row in results for key in row}))
        writer.writeheader()
        writer.writerows({key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else str(value) if isinstance(value, Fraction) else value
                          for key, value in row.items()} for row in results)
    for name in ("source_manifest.json", "jobchecks.json", "executions.csv", "provenance.json", "cross_submission_uuid_reconciliation.csv"):
        refs.append({"path": name, "sha256": _hash((analysis_dir / name).read_bytes())})
    receipt = {"provenance": provenance, "post_hoc": True, "tolerance": str(tolerance),
               "canonical_analysis_inputs": refs, "raw_job_sources": raw_refs,
               "module_sha256": {path.name: _hash(path.read_bytes()) for path in (Path(__file__), Path(normalize.__file__))},
               "trial_arithmetic_source": "hash_verified_canonical_normalized_final_record_ledgers; original reward/source pointers retained there",
               "scope": "scalar equality does not validate evaluation-group aliases, indices, population equality or website imports"}
    (output_dir / "summary.json").write_bytes((json.dumps(summary, indent=2, sort_keys=True) + "\n").encode())
    (output_dir / "provenance.json").write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    return summary


def main() -> None:
    """Write post hoc diagnostics separately, from clean committed source only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.data_root, args.analysis_dir, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
