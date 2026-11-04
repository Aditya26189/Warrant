"""Normalize final-release evidence without inventing missing executions.

The frozen protocol keeps rewards and exceptions orthogonal and limits native
reproduction to the documented single ``reward`` channel. No raw configuration
text, trajectories, retry indices, or credentials enter these returned records.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from pathlib import PurePosixPath
from typing import Any, Iterable
from uuid import UUID


_NULL_STATUSES = {
    "absent_verifier", "null_verifier", "absent_rewards", "null_rewards"
}


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _uuid(value: object) -> str | None:
    try:
        return str(UUID(value)) if isinstance(value, str) else None
    except ValueError:
        return None


def _decimal(value: object, *, strings: bool = False) -> tuple[Decimal | None, str]:
    if isinstance(value, bool):
        return None, "bool_reward"
    if not isinstance(value, (int, float, Decimal)) and not (
        strings and isinstance(value, str)
    ):
        return None, "malformed_reward"
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None, "malformed_reward"
    if not result.is_finite():
        return None, "nonfinite_reward"
    if not Decimal(0) <= result <= Decimal(1):
        return None, "out_of_range_reward"
    return result, "scored_zero" if result == 0 else "scored_positive"


def _number(value: Decimal | None) -> str | None:
    return format(value, "f") if value is not None else None


def _safe_scalar(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float) and not Decimal(str(value)).is_finite():
        return str(value)
    return value if value is None or isinstance(value, (str, int, float, bool)) else None


def _hash_config(value: object) -> str:
    # Only the digest leaves this function; arbitrary agent kwargs stay private.
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reward(raw: dict[str, Any]) -> dict[str, Any]:
    status = "absent_verifier"
    value: object = None
    channel: str | None = None
    if "verifier_result" in raw:
        verifier = raw["verifier_result"]
        if verifier is None:
            status = "null_verifier"
        elif not isinstance(verifier, dict):
            status = "malformed_verifier"
        elif "rewards" not in verifier:
            status = "absent_rewards"
        elif verifier["rewards"] is None:
            status = "null_rewards"
        elif not isinstance(verifier["rewards"], dict):
            status = "malformed_rewards"
        else:
            rewards = verifier["rewards"]
            if not rewards:
                status = "empty_rewards"
            elif len(rewards) > 1:
                status = "multichannel"
            elif "reward" not in rewards:
                status = "absent_channel"
            else:
                channel = "reward"
                value = rewards["reward"]
                validated, status = _decimal(value)
                if validated is not None:
                    return {
                        "reward_status": status, "reward_raw": _safe_scalar(value),
                        "reward_decimal": _number(validated), "reward_channel": channel,
                        "score_present": True, "native_supported": True,
                        "native_reward_decimal": _number(validated),
                    }
    return {
        "reward_status": status, "reward_raw": _safe_scalar(value),
        "reward_decimal": None, "reward_channel": channel,
        "score_present": False, "native_supported": status in _NULL_STATUSES,
        "native_reward_decimal": "0" if status in _NULL_STATUSES else None,
    }


def normalize_trial(
    raw: dict[str, Any], source_path: str, sha256: str, job_path: str
) -> dict[str, Any]:
    """Preserve outcome distinctions and explicit identity in one safe row.

    No inference turns a missing file into a planned execution. Valid rewards
    survive exceptions, including timeouts, as required by the frozen protocol.
    Numeric strings are malformed rewards; callers may parse JSON decimals into
    ``Decimal`` to preserve the original numeric precision.
    """
    if not isinstance(raw, dict):
        raise ValueError("trial JSON must be an object")
    config = raw.get("config")
    config_object = config if isinstance(config, dict) else {}
    task = raw.get("task_id")
    task = task if isinstance(task, dict) else {}
    agent = raw.get("agent_info")
    agent = agent if isinstance(agent, dict) else {}
    model = agent.get("model_info")
    model = model if isinstance(model, dict) else {}
    exception = raw.get("exception_info")
    exception_class = _text(exception.get("exception_type")) if isinstance(exception, dict) else None
    source = _text(raw.get("source")) or "adhoc"
    agent_name, model_name = _text(agent.get("name")), _text(model.get("name"))
    eval_key = None
    if agent_name:
        eval_key = "__".join([agent_name, *([model_name] if model_name else []), source])
    trial_name = _text(raw.get("trial_name"))
    directory_name = PurePosixPath(source_path.replace("\\", "/")).parent.name
    trial_uuid = _uuid(raw.get("id"))
    task_name = _text(raw.get("task_name"))
    git_url, git_commit, task_path = (
        _text(task.get("git_url")), _text(task.get("git_commit_id")), _text(task.get("path"))
    )
    checksum = _text(raw.get("task_checksum"))
    issues = []
    if trial_uuid is None:
        issues.append("missing_or_invalid_trial_uuid")
    if not trial_name:
        issues.append("missing_trial_name")
    elif trial_name != directory_name:
        issues.append("trial_name_directory_mismatch")
    if not task_name or not task_path:
        issues.append("missing_task_identity")
    elif PurePosixPath(task_path).name != task_name:
        issues.append("task_name_path_mismatch")
    if exception is not None and not exception_class:
        issues.append("malformed_exception_info")
    if not isinstance(config, dict):
        issues.append("missing_or_malformed_config")
    return {
        "source_path": source_path, "source_sha256": sha256, "source_pointer": "",
        "reward_pointer": "/verifier_result/rewards/reward", "job_path": job_path,
        "trial_uuid": trial_uuid, "trial_uuid_raw": _safe_scalar(raw.get("id")),
        "trial_name": trial_name, "directory_name": directory_name,
        "job_uuid": _uuid(config_object.get("job_id")),
        "task_name": task_name, "task_git_url": git_url, "task_git_commit": git_commit,
        "task_path": task_path, "task_checksum": checksum,
        "task_identity_status": "pinned_git" if all([git_url, git_commit, task_path, checksum]) else "local_or_unpinned",
        "config_hash": _hash_config(config), "agent_name": agent_name,
        "agent_version": _text(agent.get("version")), "model_name": model_name,
        "source_dataset": source, "eval_key": eval_key,
        "exception_present": exception is not None, "exception_class": exception_class,
        "started_at": _text(raw.get("started_at")), "finished_at": _text(raw.get("finished_at")),
        "identity_issues": issues, **_reward(raw),
    }


def _mean(values: list[Decimal]) -> tuple[str | None, str | None]:
    if not values:
        return None, None
    exact = sum((Fraction(value) for value in values), Fraction()) / len(values)
    with localcontext() as context:
        context.prec = max(50, len(str(abs(exact.numerator))) + len(str(exact.denominator)) + 10)
        result = Decimal(exact.numerator) / Decimal(exact.denominator)
    return _number(result), f"{exact.numerator}/{exact.denominator}"


def _counter(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _summary_indexes(evaluation: dict[str, Any]) -> tuple[dict[str, Decimal], dict[str, str], list[str]]:
    rewards: dict[str, Decimal] = {}
    errors: dict[str, str] = {}
    issues: list[str] = []
    reward_stats = evaluation.get("reward_stats", {})
    if not isinstance(reward_stats, dict) or set(reward_stats) - {"reward"}:
        issues.append("unsupported_summary_reward_channels")
    elif "reward" in reward_stats:
        index = reward_stats["reward"]
        if not isinstance(index, dict):
            issues.append("malformed_summary_reward_index")
        else:
            for raw_value, names in index.items():
                value, _ = _decimal(raw_value, strings=True)
                if value is None or not isinstance(names, list) or any(not isinstance(n, str) for n in names):
                    issues.append("malformed_summary_reward_entry")
                    continue
                for name in names:
                    if name in rewards:
                        issues.append("duplicate_summary_reward_name")
                    rewards[name] = value
    exception_stats = evaluation.get("exception_stats", {})
    if not isinstance(exception_stats, dict):
        issues.append("malformed_summary_exception_index")
    else:
        for exception_class, names in exception_stats.items():
            if not isinstance(exception_class, str) or not isinstance(names, list) or any(not isinstance(n, str) for n in names):
                issues.append("malformed_summary_exception_entry")
            else:
                for name in names:
                    if name in errors:
                        issues.append("duplicate_summary_exception_name")
                    errors[name] = exception_class
    return rewards, errors, issues


def reconcile_job(
    job_raw: dict[str, Any], normalized_rows: Iterable[dict[str, Any]],
    directory_names: Iterable[str], tolerance: Decimal = Decimal("1e-12"),
) -> dict[str, Any]:
    """Reconcile named final records, orthogonal counters and native means.

    Null verifier/rewards enter native means as zero. Unsupported observations,
    missing files and contradictory summaries prevent a claim of reproduction;
    summary-only reward names are never fabricated as unscored executions.
    """
    if not isinstance(job_raw, dict):
        raise ValueError("job JSON must be an object")
    if not isinstance(tolerance, Decimal) or not tolerance.is_finite() or tolerance < 0:
        raise ValueError("tolerance must be a finite nonnegative Decimal")
    rows = list(normalized_rows)
    directories_list = list(directory_names)
    if any(not isinstance(name, str) for name in directories_list):
        raise ValueError("directory names must be strings")
    directories = set(directories_list)
    stats = job_raw.get("stats")
    stats = stats if isinstance(stats, dict) else {}
    evaluations = stats.get("evals")
    evaluations = evaluations if isinstance(evaluations, dict) else {}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unknown_group = 0
    for row in rows:
        key = row.get("eval_key")
        candidates = {key, key.replace("/", "-")} if isinstance(key, str) else set()
        available = candidates.intersection(evaluations)
        if len(available) == 1:
            groups[next(iter(available))].append(row)
        elif key is not None and not available:
            groups[key].append(row)
        else:
            unknown_group += 1
    native_evals = []
    all_summary_names: set[str] = set()
    all_reward_names: set[str] = set()
    all_exception_names: set[str] = set()
    for key in sorted(set(groups) | set(evaluations)):
        selected = groups.get(key, [])
        summary = evaluations.get(key, {})
        summary = summary if isinstance(summary, dict) else {}
        reward_index, exception_index, issues = _summary_indexes(summary)
        exception_names = set(exception_index)
        reward_names = set(reward_index)
        names = {row["trial_name"] for row in selected if row.get("trial_name")}
        all_summary_names.update(reward_names | exception_names)
        all_reward_names.update(reward_names)
        all_exception_names.update(exception_names)
        values = [Decimal(row["native_reward_decimal"]) for row in selected if row.get("native_supported")]
        mean, fraction = _mean(values) if len(values) == len(selected) else (None, None)
        native_mass = sum(values, Decimal()) if len(values) == len(selected) else None
        score_rows = [row for row in selected if row.get("score_present")]
        observed_mass = sum((Decimal(row["reward_decimal"]) for row in score_rows), Decimal())
        mismatches = []
        for row in selected:
            name = row.get("trial_name")
            if row.get("score_present"):
                if name not in reward_index or abs(Decimal(row["reward_decimal"]) - reward_index[name]) > tolerance:
                    mismatches.append(name)
            elif name in reward_index:
                mismatches.append(name)
            if bool(row.get("exception_present")) != (name in exception_names):
                mismatches.append(name)
            elif name in exception_index and row.get("exception_class") != exception_index[name]:
                mismatches.append(name)
        declared_scored = _counter(summary.get("n_trials"))
        declared_errors = _counter(summary.get("n_errors"))
        counter_match = (
            (declared_scored is None or declared_scored == len(score_rows))
            and (declared_errors is None or declared_errors == sum(bool(row.get("exception_present")) for row in selected))
        )
        metrics = summary.get("metrics")
        metric, metric_issue = None, None
        if isinstance(metrics, list) and len(metrics) == 1 and isinstance(metrics[0], dict) and set(metrics[0]) == {"mean"}:
            metric, metric_status = _decimal(metrics[0]["mean"])
            if metric is None:
                metric_issue = f"unsupported_native_mean:{metric_status}"
        elif metrics not in (None, []):
            metric_issue = "unsupported_native_metrics"
        if metric_issue:
            issues.append(metric_issue)
        missing_names = (reward_names | exception_names) - names
        if issues or len(values) != len(selected):
            status = "unsupported_schema"
        elif metric is None or not selected:
            status = "unavailable"
        elif missing_names or mismatches or not counter_match or abs(Decimal(mean) - metric) > tolerance:
            status = "unresolved_mismatch"
        else:
            status = "match"
        native_evals.append({
            "eval_key": key, "row_count": len(selected), "scored_count": len(score_rows),
            "unknown_count": sum(row.get("reward_status") in _NULL_STATUSES for row in selected),
            "unsupported_count": len(selected) - len(values), "observed_reward_mass": _number(observed_mass),
            "native_reward_mass": _number(native_mass), "native_denominator": len(selected),
            "native_mean": mean, "native_mean_fraction": fraction,
            "published_mean": _number(metric), "native_status": status,
            "declared_scored_n_trials": declared_scored, "declared_n_errors": declared_errors,
            "counter_match": counter_match, "summary_reward_names": sorted(reward_names),
            "summary_exception_names": sorted(exception_names),
            "summary_scored_exception_overlap": sorted(reward_names & exception_names),
            "summary_names_missing_raw": sorted(missing_names),
            "raw_names_missing_summary": sorted(names - reward_names - exception_names),
            "record_summary_mismatches": sorted(set(mismatches), key=str),
            "schema_issues": sorted(set(issues)),
        })
    names = {row["trial_name"] for row in rows if row.get("trial_name")}
    raw_directories = {row.get("directory_name") for row in rows}
    duplicate_uuids = sorted(k for k, count in Counter(row.get("trial_uuid") for row in rows if row.get("trial_uuid")).items() if count > 1)
    duplicate_names = sorted(k for k, count in Counter(row.get("trial_name") for row in rows if row.get("trial_name")).items() if count > 1)
    declared_global = _counter(stats.get("n_trials"))
    global_match = declared_global is None or declared_global == len(rows)
    declared_global_errors = _counter(stats.get("n_errors"))
    global_errors_match = declared_global_errors is None or declared_global_errors == sum(bool(row.get("exception_present")) for row in rows)
    directory_match = raw_directories == directories and len(directories_list) == len(directories)
    identity_issues = sorted({issue for row in rows for issue in row.get("identity_issues", [])})
    statuses = {evaluation["native_status"] for evaluation in native_evals}
    if "unsupported_schema" in statuses:
        status = "unsupported_schema"
    elif unknown_group or not native_evals or statuses == {"unavailable"}:
        status = "unavailable"
    elif (statuses != {"match"} or not global_match or not global_errors_match or not directory_match
          or duplicate_uuids or duplicate_names or identity_issues
          or all_summary_names - names):
        status = "unresolved_mismatch"
    else:
        status = "match"
    return {
        "job_uuid": _uuid(job_raw.get("id")), "finished_at_present": job_raw.get("finished_at") is not None,
        "declared_n_total_trials": _counter(job_raw.get("n_total_trials")),
        "global_n_trials": declared_global, "global_n_completed_trials": _counter(stats.get("n_completed_trials")),
        "global_n_errors": declared_global_errors,
        "row_count": len(rows), "directory_count": len(directories),
        "raw_scored_count": sum(bool(row.get("score_present")) for row in rows),
        "raw_exception_count": sum(bool(row.get("exception_present")) for row in rows),
        "raw_scored_exception_overlap_count": sum(bool(row.get("score_present") and row.get("exception_present")) for row in rows),
        "summary_reward_name_count": len(all_reward_names), "summary_exception_name_count": len(all_exception_names),
        "summary_scored_exception_overlap_count": len(all_reward_names & all_exception_names),
        "directories_missing_raw": sorted(directories - raw_directories),
        "raw_directories_missing_listing": sorted(raw_directories - directories, key=str),
        "summary_names_missing_raw": sorted(all_summary_names - names),
        "summary_names_missing_directory": sorted(all_summary_names - directories),
        "duplicate_trial_uuids": duplicate_uuids, "duplicate_trial_names": duplicate_names,
        "identity_issues": identity_issues, "unknown_eval_group_count": unknown_group,
        "global_count_match": global_match, "directory_match": directory_match,
        "global_error_count_match": global_errors_match,
        "native_status": status, "evals": native_evals,
        "retry_lineage_status": "unavailable_no_explicit_lineage",
    }
