"""Small accounting fixtures, not evidence of release prevalence."""

from copy import deepcopy
from decimal import Decimal

import pytest

from experiments.unscored_trials.normalize import normalize_trial, reconcile_job


def trial(name: str = "task__abc", reward: object = 0) -> dict:
    """Create an explicit final identity with no invented retry fields."""
    return {
        "id": "0b6a6f08-2809-4392-9699-4594931c9d49",
        "trial_name": name, "task_name": "task",
        "task_id": {"git_url": "https://example.org/tasks.git", "git_commit_id": "a" * 40, "path": "task"},
        "task_checksum": "b" * 64,
        "config": {"job_id": "035a8dde-bb72-454e-9367-363c83d008d4", "agent": {"kwargs": {"api_key": "never-export-this"}}},
        "agent_info": {"name": "agent", "version": "v1", "model_info": {"name": "provider/model"}},
        "source": "terminal-bench", "verifier_result": {"rewards": {"reward": reward}},
        "exception_info": None,
    }


def normalize(raw: dict) -> dict:
    return normalize_trial(raw, f"job/{raw['trial_name']}/result.json", "c" * 64, "job")


def summary(mean: object, reward_stats: dict, exception_stats: dict | None = None, *, total: int = 1, scored: int = 1, errors: int = 0) -> dict:
    return {
        "id": "035a8dde-bb72-454e-9367-363c83d008d4", "n_total_trials": total,
        "stats": {"n_trials": total, "n_errors": errors, "evals": {
            "agent__provider-model__terminal-bench": {
                "n_trials": scored, "n_errors": errors, "metrics": [{"mean": mean}],
                "reward_stats": reward_stats, "exception_stats": exception_stats or {},
            }
        }},
    }


@pytest.mark.parametrize("value,status", [
    (0, "scored_zero"), (Decimal("0.125"), "scored_positive"),
    (True, "bool_reward"), ("1", "malformed_reward"),
    (None, "malformed_reward"), ({}, "malformed_reward"),
    (float("nan"), "nonfinite_reward"), (Decimal("Infinity"), "nonfinite_reward"),
    (-1, "out_of_range_reward"), (Decimal("1.01"), "out_of_range_reward"),
])
def test_reward_scalar_validation(value: object, status: str) -> None:
    result = normalize(trial(reward=value))
    assert result["reward_status"] == status
    assert result["score_present"] == status.startswith("scored_")
    assert result["native_supported"] == status.startswith("scored_")


@pytest.mark.parametrize("verifier,status,supported", [
    (None, "null_verifier", True), ({}, "absent_rewards", True),
    ({"rewards": None}, "null_rewards", True),
    ({"rewards": {}}, "empty_rewards", False),
    ({"rewards": {"other": 1}}, "absent_channel", False),
    ({"rewards": {"reward": 1, "other": 0}}, "multichannel", False),
    ({"rewards": []}, "malformed_rewards", False), ([], "malformed_verifier", False),
])
def test_verifier_shape_distinctions(verifier: object, status: str, supported: bool) -> None:
    raw = trial()
    raw["verifier_result"] = verifier
    result = normalize(raw)
    assert result["reward_status"] == status
    assert result["native_supported"] is supported
    assert result["native_reward_decimal"] == ("0" if supported else None)


def test_absent_verifier_is_preserved_and_secrets_are_not_exported() -> None:
    raw = trial()
    del raw["verifier_result"]
    result = normalize(raw)
    assert result["reward_status"] == "absent_verifier"
    assert len(result["config_hash"]) == 64
    assert "never-export-this" not in repr(result)
    assert "kwargs" not in result
    assert "attempt_index" not in result


def test_valid_score_survives_timeout_and_overlapping_summary_indexes() -> None:
    raw = trial(reward=1)
    raw["exception_info"] = {"exception_type": "AgentTimeoutError", "exception_message": "not exported"}
    row = normalize(raw)
    job = summary(1, {"reward": {"1.0": ["task__abc"]}}, {"AgentTimeoutError": ["task__abc"]}, errors=1)
    result = reconcile_job(job, [row], ["task__abc"])
    assert result["native_status"] == "match"
    assert result["raw_scored_exception_overlap_count"] == 1
    assert result["summary_scored_exception_overlap_count"] == 1
    assert result["evals"][0]["native_denominator"] == 1
    assert row["reward_decimal"] == "1"
    assert "exception_message" not in row


def test_null_zero_fraction_have_distinct_statuses_and_exact_native_mean() -> None:
    first, second, third = trial("task__zero", 0), trial("task__fraction", Decimal("0.125")), trial("task__null")
    first["id"], second["id"], third["id"] = [f"00000000-0000-4000-8000-{i:012d}" for i in (1, 2, 3)]
    third["verifier_result"] = None
    third["exception_info"] = {"exception_type": "RuntimeError"}
    rows = [normalize(raw) for raw in (first, second, third)]
    job = summary(Decimal(1) / 24, {"reward": {"0": ["task__zero"], "0.125": ["task__fraction"]}}, {"RuntimeError": ["task__null"]}, total=3, scored=2, errors=1)
    result = reconcile_job(job, rows, [row["trial_name"] for row in rows])
    evaluation = result["evals"][0]
    assert result["native_status"] == "match"
    assert evaluation["native_mean_fraction"] == "1/24"
    assert evaluation["observed_reward_mass"] == "0.125"
    assert evaluation["native_denominator"] == 3
    assert evaluation["scored_count"] == 2
    assert evaluation["unknown_count"] == 1


def test_summary_only_scored_name_is_missing_file_not_unknown_execution() -> None:
    row = normalize(trial())
    job = summary(Decimal("0.5"), {"reward": {"0": ["task__abc"], "1": ["task__absent"]}}, total=2, scored=2)
    result = reconcile_job(job, [row], ["task__abc", "task__absent"])
    assert result["native_status"] == "unresolved_mismatch"
    assert result["summary_names_missing_raw"] == ["task__absent"]
    assert result["directories_missing_raw"] == ["task__absent"]
    assert result["evals"][0]["unknown_count"] == 0
    assert result["row_count"] == 1


def test_malformed_rewards_or_native_metrics_prevent_reproduction() -> None:
    job = summary(0, {"reward": {"0": ["task__abc"]}})
    raw = trial()
    raw["verifier_result"]["rewards"] = {}
    assert reconcile_job(job, [normalize(raw)], ["task__abc"])["native_status"] == "unsupported_schema"
    job["stats"]["evals"]["agent__provider-model__terminal-bench"]["metrics"] = [{"mean": True}]
    assert reconcile_job(job, [normalize(trial())], ["task__abc"])["native_status"] == "unsupported_schema"


def test_duplicate_uuid_and_conflicting_summary_remain_visible() -> None:
    rows = [normalize(trial("task__a", 0)), normalize(trial("task__b", 1))]
    job = summary(Decimal("0.5"), {"reward": {"0": ["task__a", "task__b"]}}, total=2, scored=2)
    result = reconcile_job(job, rows, ["task__a", "task__b"])
    assert result["row_count"] == 2
    assert result["duplicate_trial_uuids"] == [rows[0]["trial_uuid"]]
    assert result["evals"][0]["record_summary_mismatches"] == ["task__b"]
    assert result["native_status"] == "unresolved_mismatch"


def test_counter_and_name_mismatches_do_not_change_score_denominator() -> None:
    job = summary(0, {"reward": {"0": ["task__abc"]}})
    job["stats"]["n_trials"] = 2
    result = reconcile_job(job, [normalize(trial())], ["task__abc"])
    assert result["native_status"] == "unresolved_mismatch"
    assert result["global_count_match"] is False
    assert result["evals"][0]["native_denominator"] == 1


def test_task_revision_checksum_and_config_identity_are_retained() -> None:
    raw = trial()
    original = normalize(raw)
    changed = deepcopy(raw)
    changed["task_id"]["git_commit_id"] = "d" * 40
    changed["task_checksum"] = "e" * 64
    changed["config"]["agent"]["kwargs"]["api_key"] = "different-private-value"
    result = normalize(changed)
    assert result["task_git_commit"] != original["task_git_commit"]
    assert result["task_checksum"] != original["task_checksum"]
    assert result["config_hash"] != original["config_hash"]
    assert result["task_identity_status"] == "pinned_git"


def test_invalid_tolerance_rejected() -> None:
    with pytest.raises(ValueError, match="tolerance"):
        reconcile_job({}, [], [], Decimal("NaN"))


def test_exception_class_and_global_error_counter_are_reconciled() -> None:
    raw = trial()
    raw["exception_info"] = {"exception_type": "AgentTimeoutError"}
    job = summary(0, {"reward": {"0": ["task__abc"]}}, {"RuntimeError": ["task__abc"]}, errors=1)
    job["stats"]["n_errors"] = 2
    result = reconcile_job(job, [normalize(raw)], ["task__abc"])
    assert result["native_status"] == "unresolved_mismatch"
    assert result["global_error_count_match"] is False
    assert result["evals"][0]["record_summary_mismatches"] == ["task__abc"]
