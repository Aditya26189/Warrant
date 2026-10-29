"""Numerical reproduction from reviewed source projections, not HTTP history.

The frozen cache replay remains archival. This route recomputes scientific
quantities from published observations; opaque private-field hashes are input
attestations, not independent verification of omitted raw content.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from contextlib import contextmanager
from decimal import Decimal
from fractions import Fraction
from pathlib import Path, PurePosixPath
from typing import Iterator
from unittest.mock import patch

from experiments.unscored_trials import analyze, bounds, explain, inventory, normalize

SCIENCE_SUMMARY_FIELDS = (
    "dataset", "revision", "submission_count", "job_count", "requested_result_sources",
    "named_final_record_count", "reward_status_counts", "job_native_status_counts",
    "eligible_primary_submissions", "compatibility_signature_counts", "eligible_pair_count",
    "pair_exclusion_reason_counts", "cross_submission_shared_uuid_count",
    "cross_submission_conflicting_uuid_count", "compatible_unordered_primary_pairs",
    "pair_classification_counts_equal_task", "duplicate_export_groups",
    "quarantined_uuid_conflict_groups", "official_website_reproduction",
    "exact_original_roster_established", "retry_policy", "scope",
    "raw_supported_submissions", "raw_supported_but_native_unreconciled_submissions",
    "scored_records_with_exceptions", "positive_scored_records_with_exceptions",
    "fractional_scored_records", "native_matched_informative_null_evaluations",
    "jobs_with_declared_total_different_from_listed_directories",
    "primary_submissions_with_nonzero_weight_sensitivity",
    "maximum_absolute_pooled_minus_equal_task_mean",
)
_BLOCKED_PATHS: tuple[Path, ...] = ()
_AUDIT_INSTALLED = False


def _audit_access(event: str, args: tuple) -> None:
    if not _BLOCKED_PATHS or event not in {"open", "os.listdir", "os.scandir", "os.chdir"}:
        return
    if not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    candidate = Path(os.fsdecode(args[0])).resolve()
    if any(candidate == root or candidate.is_relative_to(root) for root in _BLOCKED_PATHS):
        raise PermissionError("portable reproduction forbids access to a private input directory")


@contextmanager
def forbid_inputs(paths: list[Path]) -> Iterator[None]:
    """Deny file reads/listings under supplied private-cache roots while active."""
    global _BLOCKED_PATHS, _AUDIT_INSTALLED
    if not _AUDIT_INSTALLED:
        sys.addaudithook(_audit_access)
        _AUDIT_INSTALLED = True
    previous = _BLOCKED_PATHS
    _BLOCKED_PATHS = tuple(path.resolve() for path in paths)
    try:
        yield
    finally:
        _BLOCKED_PATHS = previous


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _attested(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("missing or malformed original private-field digest attestation")
    return value


def calculate(inputs: dict) -> dict:
    """Recompute fixed-cohort accounting using unchanged frozen math helpers.

    No acquisition timestamps, downloaded-byte counters, previous eligibility,
    scores or pair classifications enter this calculation.
    """
    config, task_spec = inputs["config"], inputs["task_spec"]
    if (config["dataset"] != inventory.DATASET or config["revision"] != inventory.REVISION
            or config["reward_channel"] != "reward"):
        raise ValueError("input configuration differs from the frozen release/channel")
    spec = task_spec.get("spec", task_spec)
    tasks = spec.get("tasks", [])
    official = {entry["name"]: entry for entry in tasks}
    if (spec.get("name") != "terminal-bench" or spec.get("version") != "2.0"
            or len(official) != config["task_count"] or len(tasks) != len(official)
            or any(entry.get("git_url") != config["official_task_git_url"]
                   or entry.get("git_commit_id") != config["official_task_revision"] for entry in tasks)):
        raise ValueError("task specification differs from frozen definitions")
    tolerance = Decimal(config["native_absolute_tolerance"])
    submission_paths = sorted(inputs["submission_paths"])
    if len(submission_paths) != len(set(submission_paths)):
        raise ValueError("duplicate submission population")
    submissions = {PurePosixPath(path).name for path in submission_paths}
    jobs = {row["job_path"]: row for row in inputs["jobs"]}
    if len(jobs) != len(inputs["jobs"]):
        raise ValueError("duplicate job population")
    for path, job in jobs.items():
        if (job["submission"] not in submissions
                or PurePosixPath(path).parent.as_posix() not in submission_paths
                or PurePosixPath(path).parent.name != job["submission"]
                or len(job["directories"]) != len(set(job["directories"]))):
            raise ValueError("job is not uniquely bound to the listed submission")
    by_job, by_submission = defaultdict(list), defaultdict(list)
    seen_sources = set()
    for source in sorted(inputs["trials"], key=lambda row: row["source_path"]):
        path, job_path = source["source_path"], source["job_path"]
        if job_path not in jobs or path in seen_sources:
            raise ValueError("trial is duplicate or belongs to an unlisted job")
        job = jobs[job_path]
        if (source["submission"] != job["submission"] or PurePosixPath(path).name != "result.json"
                or PurePosixPath(path).parent.parent.as_posix() != job_path
                or PurePosixPath(path).parent.name not in job["directories"]):
            raise ValueError("trial source is not bound to its listed directory")
        seen_sources.add(path)
        row = normalize.normalize_trial(source["raw"], path, _attested(source["source_sha256"]), job_path)
        attestations = source["attested_hashes"]
        row.update({key: _attested(attestations[key]) for key in
                    ("config_hash", "system_config_hash", "semantic_hash")})
        row.update(submission=source["submission"], record_kind="named_final_record", source_status="success")
        by_job[job_path].append(row)
        by_submission[source["submission"]].append(row)
    expected = {path + "/" + directory + "/result.json"
                for path, job in jobs.items() for directory in job["directories"]}
    if seen_sources != expected:
        raise ValueError("source observations do not cover the exact listed final-record population")
    checks, native_rows, reconciliation, diagnostics = [], [], [], []
    for path, job in sorted(jobs.items()):
        raw = job["raw"] if job["source_available"] else None
        if job["source_available"] and not isinstance(raw, dict):
            raise ValueError("available job lacks a projected source object")
        failures = []
        if raw is None:
            failures.append({"source_path": job["source_path"], "source_sha256": None,
                             "job_path": path, "submission": job["submission"],
                             "record_kind": "absent_raw_file", "source_status": "failed",
                             "reward_status": "unavailable_raw_file", "trial_uuid": None,
                             "trial_name": None, "directory_name": None})
        check = normalize.reconcile_job(raw or {}, by_job[path], job["directories"], tolerance)
        if raw is None:
            check["native_status"] = "unavailable"
        check.update(job_path=path, submission=job["submission"], raw_job_source_available=raw is not None,
                     failed_or_malformed_requested_files=failures,
                     population_config=job["population_config"], config_status=job["config_status"],
                     config_source_sha256=job.get("config_source_sha256"),
                     allocation_evidence="declared_cardinality_only_no_original_roster",
                     exact_planned_roster_established=False,
                     declared_total_equals_listed_directories=check["declared_n_total_trials"] == check["directory_count"] if check["declared_n_total_trials"] is not None else None,
                     declared_total_equals_named_raw_records=check["declared_n_total_trials"] == check["row_count"] if check["declared_n_total_trials"] is not None else None)
        checks.append(check)
        reconciliation.append({key: value for key, value in check.items()
                               if key not in {"evals", "failed_or_malformed_requested_files", "population_config"}})
        for evaluation in check["evals"]:
            native_rows.append({"job_path": path, "submission": job["submission"], **evaluation})
        if not check["evals"]:
            native_rows.append({"job_path": path, "submission": job["submission"],
                                "native_status": check["native_status"], "eval_key": None})
        diagnostic = explain.diagnose_job(raw, by_job[path], check, Fraction(tolerance))
        diagnostic.update(job_source_path=job["source_path"], job_source_sha256=job["source_sha256"],
                          job_source_url=job["source_url"])
        diagnostics.append(diagnostic)
    cross_uuid_rows = defaultdict(list)
    for rows in by_submission.values():
        for row in rows:
            if row.get("trial_uuid"):
                cross_uuid_rows[row["trial_uuid"]].append(row)
    cross_ledger, conflicting = [], set()
    for trial_uuid, rows in sorted(cross_uuid_rows.items()):
        owners = sorted({row["submission"] for row in rows})
        if len(owners) > 1:
            conflict = len({row["semantic_hash"] for row in rows}) > 1
            if conflict:
                conflicting.add(trial_uuid)
            cross_ledger.append({"trial_uuid": trial_uuid, "submissions": owners,
                                 "source_aliases": sorted(row["source_path"] for row in rows),
                                 "status": "conflicting_cross_submission_semantics" if conflict else "shared_explicit_execution_alias"})
    checks_by_submission = defaultdict(list)
    for check in checks:
        checks_by_submission[check["submission"]].append(check)
    eligibility, policies, dedup_ledger, raw_support, populations = [], [], [], [], {}
    for submission_path in submission_paths:
        submission = PurePosixPath(submission_path).name
        records = by_submission[submission]
        retained, ledger, reasons = analyze.deduplicate_submission(records)
        if any(row["trial_uuid"] in conflicting for row in retained):
            reasons.append("cross_submission_uuid_semantic_conflict")
            retained = [row for row in retained if row["trial_uuid"] not in conflicting]
        dedup_ledger.extend({"submission": submission, **row} for row in ledger)
        selected_checks = checks_by_submission[submission]
        if any(check["failed_or_malformed_requested_files"] for check in selected_checks):
            reasons.append("missing_or_malformed_requested_source")
        if not selected_checks or any(check["native_status"] != "match" for check in selected_checks):
            reasons.append("native_job_population_unreconciled")
        if any(check["config_status"] != "success" for check in selected_checks):
            reasons.append("missing_or_unsupported_job_config")
        if any(dataset.get("name") == "terminal-bench" and dataset.get("version") not in {None, "2.0"}
               for check in selected_checks for dataset in (check.get("population_config") or {}).get("datasets", [])):
            reasons.append("config_declares_other_benchmark_version")
        policy, task_reasons, signature = analyze.submission_policies(retained, official, config)
        reasons = sorted(set(reasons + task_reasons))
        system_hashes = sorted({row["system_config_hash"] for row in records})
        eligible = not reasons and policy is not None
        eligibility.append({"submission": submission, "source_path": submission_path, "eligible_primary": eligible,
                            "reasons": reasons, "job_count": len(selected_checks), "requested_trial_files": len(records),
                            "named_final_records": len(records), "retained_unique_uuid_records": len(retained),
                            "task_count": len({row.get("task_name") for row in retained}),
                            "task_definition_signature": signature, "declared_system_config_hash_count": len(system_hashes),
                            "declared_system_config_hashes": system_hashes,
                            "system_interpretation": "released_submission_mixture_or_single_declared_config; hashes show configuration-byte variation, not proven behavioral heterogeneity",
                            "native_job_status_counts": dict(Counter(check["native_status"] for check in selected_checks)),
                            "exact_planned_roster_established": False, "retry_lineage_status": "unavailable"})
        raw_reasons = [reason for reason in reasons if reason not in
                       {"native_job_population_unreconciled", "missing_or_malformed_requested_source"}]
        raw_supported = not raw_reasons and policy is not None
        raw_support.append({"submission": submission, "raw_population_supported": raw_supported,
                            "eligible_primary": eligible, "raw_exclusion_reasons": raw_reasons,
                            "native_job_status_counts": dict(Counter(check["native_status"] for check in selected_checks)),
                            "record_count": len(retained), "task_definition_signature": signature,
                            "raw_equal_task_zero_filled_mean": policy["equal_task"]["native_mean"] if raw_supported else None,
                            "interpretation": "descriptive_named_raw_final_population_only; unavailable_native_metric_is_not_reproduced; no_secondary_rank_comparison"})
        if not eligible:
            continue
        populations[submission] = {"policy": policy, "signature": signature,
                                   "uuids": {row["trial_uuid"] for row in retained}}
        observed = [Decimal(row["reward_decimal"]) for row in retained if row["score_present"]]
        for name in ("equal_task", "pooled"):
            values = policy[name]
            policies.append({"submission": submission, "policy": name, "population": "deduplicated_named_final_records",
                             "record_count": policy["record_count"], "task_count": policy["task_count"],
                             "unknown_record_count": policy["unknown_record_count"], "native_operational_zero_mean": values["native_mean"],
                             "score_completion_lower": values["bounds"][0], "score_completion_upper": values["bounds"][1],
                             "unknown_weight": values["missing_weight"],
                             "score_completion_interpretation": "free_[0,1]_score_completion_envelope_for_named_unscored_final_records",
                             "pooled_observed_only_mean": sum((Fraction(value) for value in observed), Fraction()) / len(observed) if observed else None,
                             "observed_only_population_caveat": "conditions_on_scored_records_and_changes_weights",
                             "pooled_minus_equal_task_operational_mean": policy["pooled"]["native_mean"] - policy["equal_task"]["native_mean"],
                             "task_repetition_counts": policy["task_counts"], "task_definition_signature": signature})
    compatibility, pairs = analyze.compare_populations(populations)
    compact_native = []
    for row in native_rows:
        compact = {key: value for key, value in row.items() if not isinstance(value, (list, dict))}
        compact.update({key + "_count": len(value) for key, value in row.items() if isinstance(value, (list, dict))})
        compact_native.append(compact)
    records = [row for path in sorted(by_job) for row in by_job[path]]
    deltas = [row["pooled_minus_equal_task_operational_mean"] for row in policies if row["policy"] == "equal_task"]
    summary = {
        "dataset": config["dataset"], "revision": config["revision"], "submission_count": len(submission_paths),
        "job_count": len(jobs), "requested_result_sources": len(records) + len(jobs),
        "named_final_record_count": len(records), "reward_status_counts": dict(Counter(row["reward_status"] for row in records)),
        "job_native_status_counts": dict(Counter(row["native_status"] for row in checks)),
        "eligible_primary_submissions": sum(row["eligible_primary"] for row in eligibility),
        "compatibility_signature_counts": dict(Counter(value["signature"] for value in populations.values())),
        "eligible_pair_count": len(compatibility),
        "pair_exclusion_reason_counts": dict(Counter(reason for row in compatibility for reason in row["exclusion_reasons"])),
        "cross_submission_shared_uuid_count": len(cross_ledger), "cross_submission_conflicting_uuid_count": len(conflicting),
        "compatible_unordered_primary_pairs": sum(row["policy"] == "equal_task" for row in pairs),
        "pair_classification_counts_equal_task": dict(Counter(row["classification"] for row in pairs if row["policy"] == "equal_task")),
        "duplicate_export_groups": sum(row["status"] == "identical_export_aliases" for row in dedup_ledger),
        "quarantined_uuid_conflict_groups": sum(row["status"] == "quarantined_conflict" for row in dedup_ledger),
        "official_website_reproduction": "unavailable_without_pinned_importer_and_adjudications",
        "exact_original_roster_established": False, "retry_policy": bounds.retry_diagnostic(),
        "scope": "published_final_record_native_metrics_and_explicit_policy_sensitivities",
        "raw_supported_submissions": sum(row["raw_population_supported"] for row in raw_support),
        "raw_supported_but_native_unreconciled_submissions": sum(row["raw_population_supported"] and not row["eligible_primary"] for row in raw_support),
        "scored_records_with_exceptions": sum(row["score_present"] and row["exception_present"] for row in records),
        "positive_scored_records_with_exceptions": sum(row["score_present"] and row["exception_present"] and Decimal(row["reward_decimal"]) > 0 for row in records),
        "fractional_scored_records": sum(row["score_present"] and Decimal(0) < Decimal(row["reward_decimal"]) < Decimal(1) for row in records),
        "native_matched_informative_null_evaluations": sum(row.get("native_status") == "match" and row.get("unknown_count", 0) > 0 and Decimal(row.get("observed_reward_mass") or "0") > 0 for row in native_rows),
        "jobs_with_declared_total_different_from_listed_directories": sum(row["declared_total_equals_listed_directories"] is False for row in checks),
        "primary_submissions_with_nonzero_weight_sensitivity": sum(delta != 0 for delta in deltas),
        "maximum_absolute_pooled_minus_equal_task_mean": max((abs(delta) for delta in deltas), default=Fraction()),
    }
    whole_summary = {"post_hoc": True, "job_count": len(diagnostics),
                     "strict_joint_status_counts": dict(Counter(row["strict_joint_native_status"] for row in diagnostics)),
                     "whole_job_numeric_status_counts": dict(Counter(row["whole_job_numeric_status"] for row in diagnostics)),
                     "summary_internal_status_counts": dict(Counter(row["summary_internal_status"] for row in diagnostics)),
                     "classification_counts": dict(Counter(row["diagnostic_classification"] for row in diagnostics)),
                     "strict_nonmatch_whole_job_status_counts": dict(Counter(row["whole_job_numeric_status"] for row in diagnostics if row["strict_joint_native_status"] != "match")),
                     "primary_outputs_changed": False, "independent_adjudication": False, "official_website_error_claim": False}
    tables = {"reconciliation.csv": reconciliation, "native_score_reproduction.csv": compact_native,
              "eligibility.csv": eligibility, "raw_population_support.csv": raw_support,
              "policy_comparisons.csv": policies, "pairwise_comparisons.csv": pairs,
              "compatibility_matrix.csv": compatibility, "uuid_reconciliation.csv": dedup_ledger,
              "cross_submission_uuid_reconciliation.csv": cross_ledger, "whole_job_diagnostics.csv": diagnostics}
    return {"tables": tables, "summary": summary, "whole_job_summary": whole_summary,
            "executions": records, "job_checks": checks}


def _semantic_cell(field: str, value: str) -> object:
    if value.startswith(("[", "{")):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    numeric = (field.startswith(("native_", "difference_", "score_completion_", "pooled_", "raw_native_"))
               or field in {"published_mean", "observed_reward_mass", "unknown_weight", "summary_mean",
                            "summary_reward_mass", "raw_scored_exception_reward_mass"})
    if numeric and re.fullmatch(r"[-+]?\d+(?:/\d+|\.\d*(?:[eE][-+]?\d+)?)?", value):
        return Fraction(value)
    return value


def compare_csv(actual: Path, expected: Path, *, exclude_columns: tuple[str, ...] = ()) -> dict:
    """Require every scientific field to agree, allowing equal fraction spellings."""
    def read(path: Path) -> tuple[list[str], list[dict]]:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = sorted(key for key in reader.fieldnames or [] if key not in exclude_columns)
            rows = [{key: _semantic_cell(key, row[key]) for key in fields} for row in reader]
        return fields, rows
    fields, rows = read(actual)
    expected_fields, expected_rows = read(expected)
    if fields != expected_fields or rows != expected_rows:
        differing = []
        for index, (left, right) in enumerate(zip(rows, expected_rows, strict=False)):
            for key in set(left) | set(right):
                if left.get(key) != right.get(key):
                    differing.append({"row": index, "field": key})
                    if len(differing) >= 10:
                        break
            if len(differing) >= 10:
                break
        raise ValueError(f"scientific table mismatch: {actual.name}; row_counts={len(rows)},{len(expected_rows)}; first_fields={differing}")
    return {"file": actual.name, "rows": len(rows), "compared_columns": len(fields),
            "match": True, "excluded_columns": list(exclude_columns), "comparison": "exact values; equal rational spellings normalized"}


def generate(inputs: dict, output_dir: Path, provenance: dict) -> dict:
    """Write a new numerical result directory without archival invocation state."""
    if provenance.get("dirty") is not False or output_dir.exists():
        raise ValueError("clean source and a new output directory are required")
    result = calculate(inputs)
    output_dir.mkdir(parents=True)
    for name, rows in result["tables"].items():
        analyze._csv(output_dir / name, rows)
    for name, value in (("summary.json", result["summary"]), ("whole_job_summary.json", result["whole_job_summary"]),
                        ("input_manifest.json", inputs["manifest"]), ("job_checks.json", result["job_checks"])):
        analyze._json_file(output_dir / name, value)
    with (output_dir / "executions.json.gz").open("xb") as handle:
        with gzip.GzipFile(fileobj=handle, mode="wb", filename="", mtime=0) as compressed:
            compressed.write(analyze._json(result["executions"]))
    analyze._json_file(output_dir / "provenance.json", provenance)
    return result["summary"]


def compare_science(output: Path, reference: Path) -> dict:
    """Compare all regenerated scientific tables; leave acquisition history archival."""
    table_results = []
    names = ("reconciliation.csv", "native_score_reproduction.csv", "eligibility.csv", "raw_population_support.csv",
             "policy_comparisons.csv", "pairwise_comparisons.csv", "compatibility_matrix.csv",
             "uuid_reconciliation.csv", "cross_submission_uuid_reconciliation.csv")
    for name in names:
        table_results.append(compare_csv(output / name, reference / name))
    table_results.append(compare_csv(output / "whole_job_diagnostics.csv", reference / "explanation/whole_job_diagnostics.csv",
                                     exclude_columns=("raw_ledger_shards",)))
    actual, expected = json.loads((output / "summary.json").read_bytes()), json.loads((reference / "summary.json").read_bytes())
    differences = [key for key in SCIENCE_SUMMARY_FIELDS if actual[key] != expected[key]]
    if differences:
        raise ValueError("scientific summary mismatch: " + ", ".join(differences))
    whole = json.loads((output / "whole_job_summary.json").read_bytes())
    if whole != json.loads((reference / "explanation/summary.json").read_bytes()):
        raise ValueError("post hoc diagnostic summary mismatch")
    return {"match": True, "tables": table_results, "summary_fields_compared": len(SCIENCE_SUMMARY_FIELDS),
            "post_hoc_summary_match": True,
            "not_compared": ["historical acquisition receipts/timestamps/byte totals", "invocation paths/time/environment", "archival shard/rendering byte layout"],
            "diagnostic_excluded_column": "raw_ledger_shards is an archival output-file locator, not a scientific observation"}


def reproduce(study_data_dir: Path, bundle_dir: Path, reference_dir: Path, forbidden: list[Path]) -> dict:
    """Acquire local reviewed inputs into an empty directory, regenerate and compare."""
    from experiments.unscored_trials import closeout_report, portable_inputs

    provenance = inventory.clean_provenance()
    destination = study_data_dir.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("study-data directory must start empty")
    bundle = bundle_dir.resolve()
    if destination == bundle or destination.is_relative_to(bundle) or bundle.is_relative_to(destination):
        raise ValueError("study-data and reviewed bundle must be disjoint")
    provenance.update(config_sha256=_digest((bundle / "config.json").read_bytes()),
                      input_manifest_sha256=_digest((bundle / "manifest.json").read_bytes()),
                      numerical_route="reviewed_source_projection_v1; opaque digests attested",
                      seed=None, seed_reason="deterministic census and exact arithmetic",
                      environment={"python": sys.version.split()[0], "tqdm": importlib.metadata.version("tqdm")},
                      module_sha256={Path(module.__file__).name: _digest(Path(module.__file__).read_bytes())
                                     for module in (analyze, normalize, bounds, explain, portable_inputs, closeout_report)},
                      portable_module_sha256=_digest(Path(__file__).read_bytes()))
    receipt = {"provenance": provenance, "input_acquisition": {"method": "locate reviewed versioned bundle in clean checkout; copy to empty study-data directory"},
               "input_integrity": None, "numerical_reproduction": None, "report_generation": None,
               "networking_disabled": True, "private_roots_forbidden_count": len(forbidden),
               "private_read_guard_probes_blocked": 0,
               "archival_replay": "separate existing107-file receipt; not rerun by this command",
               "completed": False}
    destination.mkdir(parents=True, exist_ok=True)
    try:
        with forbid_inputs(forbidden), patch("socket.socket", side_effect=RuntimeError("portable numerical route forbids networking")), \
                patch("socket.create_connection", side_effect=RuntimeError("portable numerical route forbids networking")):
            for private in forbidden:
                try:
                    with (private / "__portable_guard_probe__").open("rb"):
                        pass
                except PermissionError:
                    receipt["private_read_guard_probes_blocked"] += 1
                else:
                    raise RuntimeError("private-input access guard did not reject its probe")
            portable_inputs.load_bundle(bundle)
            target = destination / "inputs"
            target.mkdir()
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    relative = path.relative_to(bundle)
                    (target / relative).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target / relative)
            inputs = portable_inputs.load_bundle(target)
            receipt["input_integrity"] = {"match": True, "manifest_sha256": _digest((target / "manifest.json").read_bytes()),
                                         "trial_observations": len(inputs["trials"]), "job_observations": len(inputs["jobs"])}
            generate(inputs, destination / "numerical", provenance)
            receipt["numerical_reproduction"] = compare_science(destination / "numerical", reference_dir)
            report = closeout_report.build_report(destination / "numerical", destination / "report")
            receipt["report_generation"] = {"completed": True, "summary": report}
            receipt["completed"] = True
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        receipt["failure"] = {"type": type(error).__name__, "message": str(error)}
        analyze._json_file(destination / "validation.json", receipt)
        raise
    analyze._json_file(destination / "validation.json", receipt)
    return receipt


def main() -> None:
    """Run one bounded closeout route; never discover a new benchmark or source."""
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    replay = commands.add_parser("reproduce")
    replay.add_argument("--study-data-dir", type=Path, required=True)
    replay.add_argument("--bundle-dir", type=Path, default=Path(__file__).with_name("portable_inputs"))
    replay.add_argument("--reference-dir", type=Path, default=root / "results/unscored_trials/20261029-terminal-bench2")
    replay.add_argument("--forbid-path", type=Path, action="append", default=[])
    args = parser.parse_args()
    result = reproduce(args.study_data_dir, args.bundle_dir, args.reference_dir, args.forbid_path)
    print(json.dumps({"completed": result["completed"], "scientific_match": result["numerical_reproduction"]["match"],
                      "networking_disabled": True, "report_generated": True}, indent=2))


if __name__ == "__main__":
    main()
