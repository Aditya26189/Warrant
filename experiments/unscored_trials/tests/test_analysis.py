"""Synthetic analysis-contract tests; no empirical release outcomes."""

from __future__ import annotations

import json
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from experiments.unscored_trials import analyze as analysis
from experiments.unscored_trials import bounds, inventory


def row(uuid: str, semantic: str, source: str = "j/t/result.json") -> dict:
    return {"trial_uuid": uuid, "semantic_hash": semantic, "source_path": source}


def test_deduplication_requires_same_explicit_uuid_and_semantics() -> None:
    records = [row("u", "a", "j1/t/result.json"), row("u", "a", "j2/t/result.json"), row("v", "a", "j3/t/result.json")]
    retained, ledger, reasons = analysis.deduplicate_submission(records)
    assert len(retained) == 2 and not reasons
    assert ledger[0]["status"] == "identical_export_aliases"
    assert next(record for record in retained if record["trial_uuid"] == "u")["source_alias_count"] == 2
    retained, ledger, reasons = analysis.deduplicate_submission([row("u", "a"), row("u", "b")])
    assert not retained
    assert reasons == ["conflicting_uuid_semantics"]
    assert ledger[0]["status"] == "quarantined_conflict"


def test_system_hash_excludes_task_and_job_fields_but_preserves_private_settings() -> None:
    raw = {"config": {"task": {"path": "a"}, "job_id": "job1", "trial_name": "a", "agent": {"kwargs": {"secret": "private-a"}}, "environment": {"type": "docker"}, "verifier": {}, "timeout_multiplier": 1}}
    changed = deepcopy(raw)
    changed["config"].update({"task": {"path": "b"}, "job_id": "job2", "trial_name": "b"})
    assert analysis._system_hash(raw) == analysis._system_hash(changed)
    changed["config"]["agent"]["kwargs"]["secret"] = "private-b"
    assert analysis._system_hash(raw) != analysis._system_hash(changed)


def test_exact_task_definition_check_does_not_trust_nonempty_pin_status() -> None:
    config = {"official_task_git_url": "https://example.org/tasks.git", "official_task_revision": "a" * 40}
    official = {"task": {"path": "task"}}
    record = {"native_supported": True, "identity_issues": [], "task_name": "task", "task_git_url": config["official_task_git_url"], "task_git_commit": "different-nonempty-revision", "task_path": "task", "task_checksum": "b" * 64, "score_present": True, "reward_decimal": "0"}
    policy, reasons, signature = analysis.submission_policies([record], official, config)
    assert policy is None and signature is None
    assert "local_unpinned_or_variant_task_definition" in reasons
    record["task_git_commit"] = config["official_task_revision"]
    policy, reasons, signature = analysis.submission_policies([record], official, config)
    assert policy is not None and not reasons and signature
    different = {**record, "task_checksum": "c" * 64}
    assert "conflicting_task_definition_or_checksum" in analysis.submission_policies([record, different], official, config)[1]


def test_every_eligible_pair_gets_compatibility_reason_and_aliases_are_excluded() -> None:
    policy = bounds.aggregate_tasks([("task", None)])
    populations = {
        "a": {"policy": policy, "signature": "same", "uuids": {"shared"}},
        "b": {"policy": policy, "signature": "same", "uuids": {"shared"}},
        "c": {"policy": policy, "signature": "same", "uuids": {"other"}},
        "d": {"policy": policy, "signature": "different", "uuids": {"last"}},
    }
    matrix, pairs = analysis.compare_populations(populations)
    assert len(matrix) == 6
    assert len(pairs) == 4  # a-c and b-c, each with two weight policies.
    assert matrix[0]["exclusion_reasons"] == ["shared_explicit_execution_uuid"]
    assert sum("incompatible_task_definition_or_checksum" in entry["exclusion_reasons"] for entry in matrix) == 3


def fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    data = tmp_path / "data"
    data.mkdir()
    submission = "Agent__Model"
    sub_path = f"{inventory.SUBMISSION_ROOT}/{submission}"
    job = sub_path + "/job1"
    revision = "a" * 40
    git_url = "https://example.org/tasks.git"

    def write_source(name: str, value: object, url: str) -> None:
        path = data / name
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(value).encode()
        path.write_bytes(payload)
        Path(str(path) + ".receipt.json").write_text(json.dumps({"url": url, "status": "success", "size_bytes": len(payload), "sha256": analysis._digest(payload), "limit_bytes": 1000000}))

    def url(source_path: str, tree: bool = False) -> str:
        return (f"https://huggingface.co/api/datasets/{inventory.DATASET}/tree/{inventory.REVISION}/{source_path}?recursive=false&limit=1000" if tree else f"https://huggingface.co/datasets/{inventory.DATASET}/raw/{inventory.REVISION}/{source_path}")

    write_source("dataset-metadata.json", {"id": inventory.DATASET, "sha": inventory.REVISION}, f"https://huggingface.co/api/datasets/{inventory.DATASET}")
    write_source("submission-tree.json", [{"type": "directory", "path": sub_path}], url(inventory.SUBMISSION_ROOT, True))
    submission_request = {"path": "submission-trees/sub.json", "source_path": sub_path, "url": url(sub_path, True)}
    write_source(submission_request["path"], [{"type": "directory", "path": job}], submission_request["url"])
    tree_request = {"path": "job-trees/job.json", "source_path": job, "url": url(job, True)}
    write_source(tree_request["path"], [{"type": "directory", "path": job + "/task__a"}, {"type": "directory", "path": job + "/task__b"}], tree_request["url"])
    config_request = {"path": "configs/job.json", "source_path": job + "/config.json", "url": url(job + "/config.json")}
    write_source(config_request["path"], {"n_attempts": 2, "datasets": [{"name": "terminal-bench", "version": "2.0"}], "tasks": []}, config_request["url"])
    requests = []

    def result_request(name: str, value: object, kind: str, source_path: str) -> None:
        request = {"path": name, "source_path": source_path, "url": url(source_path), "kind": kind, "job": job, "submission": submission}
        requests.append(request)
        write_source(name, value, request["url"])

    job_raw = {"id": "035a8dde-bb72-454e-9367-363c83d008d4", "finished_at": "2026-01-01T00:00:00", "n_total_trials": 2, "stats": {"n_trials": 2, "n_errors": 1, "evals": {"agent__terminal-bench": {"n_trials": 1, "n_errors": 1, "metrics": [{"mean": 0.0625}], "reward_stats": {"reward": {"0.125": ["task__a"]}}, "exception_stats": {"RuntimeError": ["task__b"]}}}}}
    result_request("census/job.json", job_raw, "job", job + "/result.json")
    for index, name in enumerate(("task__a", "task__b"), 1):
        raw = {"id": f"00000000-0000-4000-8000-{index:012d}", "task_name": "task", "trial_name": name, "task_id": {"git_url": git_url, "git_commit_id": revision, "path": "task"}, "task_checksum": "b" * 64, "config": {"agent": {"name": "agent", "kwargs": {"private": "NEVER-PUBLISH-ME"}}, "environment": {}, "verifier": {}, "timeout_multiplier": 1}, "agent_info": {"name": "agent", "version": "v1"}, "source": "terminal-bench", "verifier_result": {"rewards": {"reward": 0.125}} if index == 1 else None, "exception_info": None if index == 1 else {"exception_type": "RuntimeError", "exception_message": "PRIVATE-EXCEPTION"}, "started_at": "2026-01-01", "finished_at": "2026-01-02"}
        result_request(f"census/{name}.json", raw, "trial", job + f"/{name}/result.json")
    for name, content in [("submission-requests.json", [submission_request]), ("job-tree-requests.json", [tree_request]), ("config-requests.json", [config_request]), ("census-completed.json", {"requests": requests})]:
        (data / name).write_text(json.dumps(content))
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"dataset": inventory.DATASET, "revision": inventory.REVISION, "reward_channel": "reward", "official_task_git_url": git_url, "official_task_revision": revision, "task_count": 1, "native_absolute_tolerance": "1e-12"}))
    spec = tmp_path / "tasks.json"
    spec.write_text(json.dumps({"spec": {"name": "terminal-bench", "version": "2.0", "tasks": [{"name": "task", "path": "task", "git_url": git_url, "git_commit_id": revision}]}}))
    return data, config, spec, tmp_path / "output"


def test_synthetic_end_to_end_and_offline_replay(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    provenance = {"dirty": False, "git_commit": "synthetic_fixture_not_empirical"}
    summary = analysis.run_analysis(data, config, spec, output, provenance=provenance, progress=False)
    assert summary["named_final_record_count"] == 2
    assert summary["job_native_status_counts"] == {"match": 1}
    assert summary["eligible_primary_submissions"] == 1
    replay = tmp_path / "replay"
    analysis.run_analysis(data, config, spec, replay, provenance=provenance, progress=False)
    for path in output.rglob("*"):
        if path.is_file():
            assert path.read_bytes() == (replay / path.relative_to(output)).read_bytes()
            text = path.read_text()
            assert "NEVER-PUBLISH-ME" not in text and "PRIVATE-EXCEPTION" not in text
    policies = (output / "policy_comparisons.csv").read_text()
    assert "1/16" in policies  # native0 plus .125, equally weighted.
    assert "9/16" in policies  # upper envelope: (.125 + 1)/2.


def test_failed_trial_file_is_retained_without_inventing_unknown_reward(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    source = data / "census/task__b.json"
    source.unlink()
    receipt_path = Path(str(source) + ".receipt.json")
    receipt = json.loads(receipt_path.read_text())
    receipt["status"] = "failed"
    receipt_path.write_text(json.dumps(receipt))
    summary = analysis.run_analysis(data, config, spec, output, provenance={"dirty": False, "git_commit": "fixture"}, progress=False)
    assert summary["named_final_record_count"] == 1
    assert "null_verifier" not in summary["reward_status_counts"]
    assert summary["eligible_primary_submissions"] == 0
    assert "absent_raw_file" in next((output / "executions").glob("*.csv")).read_text()


def test_corrupted_successful_source_fails_before_outputs(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    path = data / "census/task__a.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="bytes do not match"):
        analysis.run_analysis(data, config, spec, output, provenance={"dirty": False, "git_commit": "fixture"}, progress=False)
    assert not output.exists()


def test_dirty_provenance_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="clean committed"):
        analysis.run_analysis(tmp_path, tmp_path, tmp_path, tmp_path, provenance={"dirty": True})


def test_unequal_repetitions_change_weights_with_fixed_record_population() -> None:
    records = [("a", Decimal("1")), ("b", Decimal("0")), ("b", Decimal("0")), ("b", None)]
    policy = bounds.aggregate_tasks(records)
    assert policy["equal_task"]["native_mean"] == Decimal("0.5")
    assert policy["pooled"]["native_mean"] == Decimal("0.25")


def test_mixed_metadata_requests_do_not_become_job_trees(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    path = data / "job-tree-requests.json"
    rows = json.loads(path.read_text())
    sub_path = rows[0]["source_path"].rsplit("/", 1)[0]
    metadata = {"path": "metadata/sub.json", "source_path": sub_path + "/metadata.yaml", "url": f"https://huggingface.co/datasets/{inventory.DATASET}/raw/{inventory.REVISION}/{sub_path}/metadata.yaml"}
    payload = b"agent_display_name: Synthetic fixture\n"
    destination = data / metadata["path"]
    destination.parent.mkdir()
    destination.write_bytes(payload)
    Path(str(destination) + ".receipt.json").write_text(json.dumps({"url": metadata["url"], "status": "success", "size_bytes": len(payload), "sha256": analysis._digest(payload), "limit_bytes": 1000000}))
    path.write_text(json.dumps(rows + [metadata]))
    result = analysis.run_analysis(data, config, spec, output, provenance={"dirty": False, "git_commit": "fixture"}, progress=False)
    assert result["job_count"] == 1 and result["eligible_primary_submissions"] == 1


def test_discovery_config_retry_recovers_failed_original(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    original = data / "configs/job.json"
    payload = original.read_bytes()
    original.unlink()
    receipt_path = Path(str(original) + ".receipt.json")
    receipt = json.loads(receipt_path.read_text())
    receipt["status"] = "failed"
    receipt_path.write_text(json.dumps(receipt))
    retry = data / "discovery/config-retry.json"
    retry.parent.mkdir()
    retry.write_bytes(payload)
    recovered = {**receipt, "status": "success", "retrieved_utc": "2026-01-02T00:00:00Z"}
    Path(str(retry) + ".receipt.json").write_text(json.dumps(recovered))
    source_request = json.loads((data / "config-requests.json").read_text())[0]
    retry_request = {**source_request, "path": "discovery/config-retry.json", "prior_failed_path": "configs/job.json"}
    (data / "discovery-requests.json").write_text(json.dumps([retry_request]))
    result = analysis.run_analysis(data, config, spec, output, provenance={"dirty": False, "git_commit": "fixture"}, progress=False)
    assert result["eligible_primary_submissions"] == 1


def test_conflicting_successful_hashes_for_one_immutable_url_fail(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    original_receipt = json.loads((data / "census/task__a.json.receipt.json").read_text())
    alias = data / "other-alias.json"
    payload = b"{}"
    alias.write_bytes(payload)
    Path(str(alias) + ".receipt.json").write_text(json.dumps({**original_receipt, "sha256": analysis._digest(payload), "size_bytes": len(payload)}))
    with pytest.raises(ValueError, match="conflicting successful hashes"):
        analysis.run_analysis(data, config, spec, output, provenance={"dirty": False, "git_commit": "fixture"}, progress=False)
    assert not output.exists()


@pytest.mark.parametrize("change", [
    {"kind": "trial"}, {"kind": "unknown"},
    {"source_path": "elsewhere/result.json"},
])
def test_result_request_kind_cannot_rebind_job_source(change: dict) -> None:
    jobs = {"submission/job": {"submission": "submission", "directories": ["task__a"]}}
    request = {"job": "submission/job", "submission": "submission", "kind": "job", "source_path": "submission/job/result.json", **change}
    with pytest.raises(ValueError, match="kind/source"):
        analysis._validate_result_request(request, jobs)


def test_result_request_trial_must_name_one_listed_child_directory() -> None:
    jobs = {"submission/job": {"submission": "submission", "directories": ["task__a"]}}
    valid = {"job": "submission/job", "submission": "submission", "kind": "trial", "source_path": "submission/job/task__a/result.json"}
    analysis._validate_result_request(valid, jobs)
    for source_path in ["submission/job/task__absent/result.json", "submission/job/outer/task__a/result.json", "submission/job/task__a/config.json"]:
        with pytest.raises(ValueError, match="kind/source"):
            analysis._validate_result_request({**valid, "source_path": source_path}, jobs)


def test_parallel_source_reads_preserve_all_canonical_results(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    provenance = {"dirty": False, "git_commit": "synthetic_fixture_not_empirical"}
    analysis.run_analysis(data, config, spec, output, provenance=provenance, progress=False)
    settings = json.loads(config.read_bytes())
    settings.update(workers=4, io_prefetch_records=2)
    config.write_text(json.dumps(settings))
    parallel = tmp_path / "parallel"
    analysis.run_analysis(data, config, spec, parallel, provenance=provenance, progress=False)
    for path in output.rglob("*"):
        if path.is_file() and path.name != "provenance.json":
            assert path.read_bytes() == (parallel / path.relative_to(output)).read_bytes()


def test_raw_support_does_not_claim_missing_native_metric_reproduction(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    path = data / "census/job.json"
    value = json.loads(path.read_bytes())
    value["stats"]["evals"]["agent__terminal-bench"]["metrics"] = []
    payload = json.dumps(value).encode()
    path.write_bytes(payload)
    receipt_path = Path(str(path) + ".receipt.json")
    receipt = json.loads(receipt_path.read_bytes())
    receipt.update(size_bytes=len(payload), sha256=analysis._digest(payload))
    receipt_path.write_text(json.dumps(receipt))
    summary = analysis.run_analysis(data, config, spec, output,
                                    provenance={"dirty": False, "git_commit": "synthetic"}, progress=False)
    assert summary["raw_supported_submissions"] == 1
    assert summary["eligible_primary_submissions"] == 0
    assert summary["raw_supported_but_native_unreconciled_submissions"] == 1
    assert (output / "pairwise_comparisons.csv").read_text().strip() == "status"


def test_source_byte_ceiling_is_checked_before_publishing_outputs(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    settings = json.loads(config.read_bytes())
    settings["max_download_bytes"] = 1
    config.write_text(json.dumps(settings))
    with pytest.raises(ValueError, match="download ceiling"):
        analysis.run_analysis(data, config, spec, output,
                              provenance={"dirty": False, "git_commit": "synthetic"}, progress=False)
    assert not output.exists()


def test_absent_job_summary_does_not_erase_complete_raw_trial_population(tmp_path: Path) -> None:
    data, config, spec, output = fixture(tmp_path)
    path = data / "census/job.json"
    path.unlink()
    receipt_path = Path(str(path) + ".receipt.json")
    receipt = json.loads(receipt_path.read_bytes())
    receipt.update(status="failed", error_type="HTTPError")
    receipt.pop("sha256")
    receipt.pop("size_bytes")
    receipt_path.write_text(json.dumps(receipt))
    summary = analysis.run_analysis(data, config, spec, output,
                                    provenance={"dirty": False, "git_commit": "synthetic"}, progress=False)
    assert summary["named_final_record_count"] == 2
    assert summary["eligible_primary_submissions"] == 0
    assert summary["raw_supported_submissions"] == 1
    assert summary["job_native_status_counts"] == {"unavailable": 1}


def recovery_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    data, config, spec, output = fixture(tmp_path)
    manifest_path = data / "census-completed.json"
    manifest = json.loads(manifest_path.read_bytes())
    original = next(row for row in manifest["requests"] if row["path"] == "census/task__a.json")
    original["limit_bytes"] = 4
    manifest_path.write_text(json.dumps(manifest))
    original_path = data / original["path"]
    payload = original_path.read_bytes()
    original_path.unlink()
    Path(str(original_path) + ".receipt.json").write_text(json.dumps({
        "url": original["url"], "status": "failed", "error_type": "ValueError",
        "limit_bytes": 4, "bytes_read": 5}))
    recovery = {**original, "path": "larger/task__a.json", "limit_bytes": len(payload),
                "prior_failed_path": original["path"], "size_metadata_path": "larger/task-size.json"}
    path = data / recovery["path"]
    path.parent.mkdir()
    path.write_bytes(payload)
    Path(str(path) + ".receipt.json").write_text(json.dumps({
        "url": original["url"], "status": "success", "size_bytes": len(payload),
        "sha256": analysis._digest(payload), "limit_bytes": len(payload)}))
    parent = original["source_path"].removesuffix("/result.json")
    metadata = json.dumps([{"path": original["source_path"], "type": "file", "size": len(payload)}]).encode()
    metadata_path = data / recovery["size_metadata_path"]
    metadata_path.write_bytes(metadata)
    Path(str(metadata_path) + ".receipt.json").write_text(json.dumps({
        "url": f"https://huggingface.co/api/datasets/{inventory.DATASET}/tree/{inventory.REVISION}/{parent}?recursive=false&limit=1000",
        "status": "success", "size_bytes": len(metadata), "sha256": analysis._digest(metadata), "limit_bytes": 1000000}))
    (data / "large-record-recoveries.json").write_text(json.dumps([recovery]))
    return data, config, spec, output


def test_larger_record_recovery_requires_pinned_size_and_original_failure(tmp_path: Path) -> None:
    data, config, spec, output = recovery_fixture(tmp_path)
    summary = analysis.run_analysis(data, config, spec, output,
                                    provenance={"dirty": False, "git_commit": "synthetic"}, progress=False)
    assert summary["named_final_record_count"] == 2
    assert summary["job_native_status_counts"] == {"match": 1}
    assert summary["larger_record_recovery_status_counts"] == {"success": 1}


@pytest.mark.parametrize("change", [{"limit_bytes": 999999}, {"prior_failed_path": "other.json"}])
def test_unsubstantiated_larger_recovery_fails(tmp_path: Path, change: dict) -> None:
    data, config, spec, output = recovery_fixture(tmp_path)
    path = data / "large-record-recoveries.json"
    rows = json.loads(path.read_bytes())
    rows[0].update(change)
    path.write_text(json.dumps(rows))
    with pytest.raises(ValueError):
        analysis.run_analysis(data, config, spec, output,
                              provenance={"dirty": False, "git_commit": "synthetic"}, progress=False)
    assert not output.exists()
