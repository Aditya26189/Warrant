"""Hand-calculated portable-route contracts; no benchmark data or network."""

from __future__ import annotations

import csv
import os
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest

from experiments.unscored_trials import inventory, portable, portable_inputs


def fixture() -> dict:
    """Two complete task populations distinguish zero, null and scored error."""
    git_url = "https://example.org/fixture-tasks.git"
    revision = "a" * 40
    config = {
        "dataset": inventory.DATASET, "revision": inventory.REVISION,
        "reward_channel": "reward", "official_task_git_url": git_url,
        "official_task_revision": revision, "task_count": 2,
        "native_absolute_tolerance": "0.000000000001",
    }
    tasks = [{"name": name, "path": name, "git_url": git_url,
              "git_commit_id": revision} for name in ("alpha", "beta")]
    trials, jobs, submissions = [], [], []
    for index, submission in enumerate(("A__Model", "B__Model")):
        submission_path = f"{inventory.SUBMISSION_ROOT}/{submission}"
        submissions.append(submission_path)
        job_path = f"{submission_path}/job"
        names = [f"{task['name']}__trial" for task in tasks]
        job_uuid = f"10000000-0000-4000-8000-{index:012d}"
        for offset, (task, name) in enumerate(zip(tasks, names, strict=True)):
            positive = index == 0 and offset == 0
            null = index == 0 and offset == 1
            raw = {
                "id": f"00000000-0000-4000-8000-{index * 2 + offset + 1:012d}",
                "trial_name": name, "task_name": task["name"],
                "task_checksum": ("b" if offset == 0 else "c") * 64,
                "task_id": {key: value for key, value in task.items() if key != "name"},
                "config": {"job_id": job_uuid},
                "agent_info": {"name": "agent", "version": "fixture-v1",
                               "model_info": {"name": "model"}},
                "source": "terminal-bench",
                "verifier_result": None if null else {"rewards": {"reward": int(positive)}},
                "exception_info": {"exception_type": "Timeout"} if index == 0 else None,
                "started_at": "2026-01-01T00:00:00", "finished_at": "2026-01-01T00:01:00",
            }
            source_path = f"{job_path}/{name}/result.json"
            row = {
                "source_path": source_path, "source_sha256": "d" * 64,
                "source_url": _url(source_path), "job_path": job_path,
                "submission": submission, "raw": raw,
                "attested_hashes": {"config_hash": "e" * 64,
                                    "system_config_hash": "f" * 64,
                                    "semantic_hash": f"{index * 2 + offset + 1:064x}"},
            }
            row["derived_sha256"] = portable_inputs._row_hash(row)
            trials.append(row)
        rewards = {"1": [names[0]]} if index == 0 else {"0": names}
        errors = {"Timeout": names} if index == 0 else {}
        raw_job = {
            "id": job_uuid, "finished_at": "2026-01-01T00:01:00", "n_total_trials": 2,
            "stats": {"n_trials": 2, "n_errors": 2 if index == 0 else 0,
                      "evals": {"agent__model__terminal-bench": {
                          "n_trials": 1 if index == 0 else 2,
                          "n_errors": 2 if index == 0 else 0,
                          "metrics": [{"mean": 0.5 if index == 0 else 0}],
                          "reward_stats": {"reward": rewards}, "exception_stats": errors,
                      }}},
        }
        source_path = f"{job_path}/result.json"
        job = {
            "job_path": job_path, "submission": submission, "directories": names,
            "config_status": "success", "population_config": {
                "n_attempts": 1, "datasets": [{"name": "terminal-bench", "version": "2.0"}],
                "tasks": [],
            },
            "config_source_sha256": "1" * 64,
            "config_source_url": _url(f"{job_path}/config.json"),
            "source_path": source_path, "source_sha256": "2" * 64,
            "source_url": _url(source_path), "source_available": True, "raw": raw_job,
        }
        job["derived_sha256"] = portable_inputs._row_hash(job)
        jobs.append(job)
    return {"manifest": {"dataset": inventory.DATASET, "revision": inventory.REVISION},
            "config": config, "task_spec": {"spec": {
                "name": "terminal-bench", "version": "2.0", "tasks": tasks,
            }}, "trials": trials, "jobs": jobs, "submission_paths": submissions}


def _url(path: str) -> str:
    return (f"https://huggingface.co/datasets/{inventory.DATASET}"
            f"/raw/{inventory.REVISION}/{path}")


def _table(result: dict, name: str) -> list[dict]:
    return result["tables"][name + ".csv"]


def test_hand_fixture_recomputes_native_bounds_and_preserves_scored_exceptions() -> None:
    result = portable.calculate(fixture())
    assert result["summary"]["named_final_record_count"] == 4
    assert result["summary"]["job_native_status_counts"] == {"match": 2}
    assert result["summary"]["eligible_primary_submissions"] == 2
    statuses = {row["trial_uuid"]: row for row in result["executions"]}
    positive = statuses["00000000-0000-4000-8000-000000000001"]
    null = statuses["00000000-0000-4000-8000-000000000002"]
    zero = statuses["00000000-0000-4000-8000-000000000003"]
    assert positive["score_present"] and positive["exception_present"]
    assert Fraction(positive["native_reward_decimal"]) == 1
    assert null["reward_status"] == "null_verifier" and not null["score_present"]
    assert zero["reward_status"] == "scored_zero" and zero["score_present"]
    a = next(row for row in _table(result, "policy_comparisons")
             if row["submission"] == "A__Model" and row["policy"] == "equal_task")
    assert a["native_operational_zero_mean"] == Fraction(1, 2)
    assert a["score_completion_lower"] == Fraction(1, 2)
    assert a["score_completion_upper"] == 1
    pair = next(row for row in _table(result, "pairwise_comparisons")
                if row["policy"] == "equal_task")
    assert pair["classification"] == "strict_robust"
    assert pair["difference_lower"] == Fraction(1, 2)
    assert pair["difference_upper"] == 1


def test_same_mean_different_summary_population_is_census_flag_and_primary_exclusion() -> None:
    inputs = fixture()
    job = inputs["jobs"][0]
    evaluation = job["raw"]["stats"]["evals"]["agent__model__terminal-bench"]
    evaluation["reward_stats"]["reward"]["1"] = ["alpha__different"]
    evaluation["exception_stats"]["Timeout"] = ["alpha__different", "beta__trial"]
    job["derived_sha256"] = portable_inputs._row_hash(job)
    result = portable.calculate(inputs)
    assert result["summary"]["job_count"] == 2
    assert result["summary"]["named_final_record_count"] == 4
    assert result["summary"]["job_native_status_counts"] == {"match": 1, "unresolved_mismatch": 1}
    assert result["summary"]["eligible_primary_submissions"] == 1
    a = next(row for row in _table(result, "eligibility") if row["submission"] == "A__Model")
    assert not a["eligible_primary"]
    assert "native_job_population_unreconciled" in a["reasons"]
    assert not _table(result, "pairwise_comparisons")
    diagnostic = next(row for row in _table(result, "whole_job_diagnostics")
                      if row["submission"] == "A__Model")
    assert diagnostic["whole_job_numeric_status"] == "match"
    assert diagnostic["summary_vs_raw_name_population"] == "different_named_populations"


@pytest.mark.parametrize("change", ["missing", "duplicate", "foreign_job", "wrong_submission"])
def test_trial_coverage_and_identity_fail_closed(change: str) -> None:
    inputs = fixture()
    if change == "missing":
        inputs["trials"].pop()
    elif change == "duplicate":
        inputs["trials"].append(deepcopy(inputs["trials"][0]))
    elif change == "foreign_job":
        inputs["trials"][0]["job_path"] += "-unknown"
    else:
        inputs["trials"][0]["submission"] = "B__Model"
    with pytest.raises(ValueError):
        portable.calculate(inputs)


@pytest.mark.parametrize("change", ["count", "revision", "duplicate_task"])
def test_official_task_config_validation_is_not_only_a_nonempty_pin(change: str) -> None:
    inputs = fixture()
    if change == "count":
        inputs["config"]["task_count"] = 3
    elif change == "revision":
        inputs["task_spec"]["spec"]["tasks"][0]["git_commit_id"] = "c" * 40
    else:
        inputs["task_spec"]["spec"]["tasks"][1] = deepcopy(inputs["task_spec"]["spec"]["tasks"][0])
    with pytest.raises(ValueError):
        portable.calculate(inputs)


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)


def test_csv_scientific_comparison_accepts_equivalent_fraction_decimal_forms(tmp_path: Path) -> None:
    actual, expected = tmp_path / "actual.csv", tmp_path / "expected.csv"
    _write_csv(actual, [["submission", "native_mean"], ["Agent", "1/2"]])
    _write_csv(expected, [["submission", "native_mean"], ["Agent", "0.50000000000000000000"]])
    result = portable.compare_csv(actual, expected)
    assert result["match"] is True and result["rows"] == 1


@pytest.mark.parametrize("change", ["value", "field", "row"])
def test_csv_scientific_mismatch_raises_instead_of_only_logging(tmp_path: Path, change: str) -> None:
    actual, expected = tmp_path / "actual.csv", tmp_path / "expected.csv"
    _write_csv(expected, [["submission", "native_mean"], ["Agent", "1/2"]])
    rows = {"value": [["submission", "native_mean"], ["Agent", "2/3"]],
            "field": [["submission", "other"], ["Agent", "1/2"]],
            "row": [["submission", "native_mean"]]}[change]
    _write_csv(actual, rows)
    with pytest.raises(ValueError):
        portable.compare_csv(actual, expected)


def test_numeric_looking_source_identity_is_not_normalized_as_a_score(tmp_path: Path) -> None:
    actual, expected = tmp_path / "actual.csv", tmp_path / "expected.csv"
    _write_csv(actual, [["trial_name", "native_mean"], ["001", "1/2"]])
    _write_csv(expected, [["trial_name", "native_mean"], ["1", "0.5"]])
    with pytest.raises(ValueError):
        portable.compare_csv(actual, expected)


def test_forbidden_original_inputs_cannot_be_read_or_enumerated_and_context_restores(tmp_path: Path) -> None:
    forbidden, allowed = tmp_path / "private-cache", tmp_path / "allowed"
    forbidden.mkdir()
    allowed.mkdir()
    private_file, public_file = forbidden / "input.json", allowed / "input.json"
    private_file.write_text("private", encoding="utf-8")
    public_file.write_text("public", encoding="utf-8")
    with portable.forbid_inputs([forbidden]):
        assert public_file.read_text(encoding="utf-8") == "public"
        for operation in (lambda: private_file.read_text(encoding="utf-8"),
                          lambda: os.listdir(forbidden), lambda: list(os.scandir(forbidden))):
            with pytest.raises((PermissionError, RuntimeError)):
                operation()
    assert private_file.read_text(encoding="utf-8") == "private"


def test_forbidden_context_restores_after_exception(tmp_path: Path) -> None:
    blocked = tmp_path / "cache"
    blocked.mkdir()
    (blocked / "input").write_text("fixture", encoding="utf-8")
    with pytest.raises(LookupError):
        with portable.forbid_inputs([blocked]):
            raise LookupError("synthetic invocation failure")
    assert (blocked / "input").read_text(encoding="utf-8") == "fixture"
