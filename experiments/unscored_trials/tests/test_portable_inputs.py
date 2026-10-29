"""Projection privacy and integrity checks using synthetic observations only."""

from __future__ import annotations

import gzip
import json
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from experiments.unscored_trials import analyze, inventory, normalize, portable_inputs as inputs
from experiments.unscored_trials.tests.test_analysis import fixture


def raw_trial() -> dict:
    return {"id": "00000000-0000-4000-8000-000000000001", "trial_name": "task__a", "task_name": "task",
            "task_id": {"git_url": "https://example.org/tasks.git", "git_commit_id": "a" * 40, "path": "task"},
            "task_checksum": "b" * 64, "config": {"job_id": "00000000-0000-4000-8000-000000000002",
            "agent": {"kwargs": {"api_key": "DO-NOT-EXPORT"}}, "environment": {"env": {"private": "DO-NOT-EXPORT"}}},
            "agent_info": {"name": "agent", "version": "v1", "model_info": {"name": "model", "private": "DO-NOT-EXPORT"}},
            "source": "terminal-bench", "verifier_result": {"rewards": {"reward": Decimal("0.12345678901234567890123456789")}, "stdout": "DO-NOT-EXPORT"},
            "exception_info": {"exception_type": "AgentTimeoutError", "exception_message": "DO-NOT-EXPORT", "exception_traceback": "DO-NOT-EXPORT"},
            "trial_uri": "DO-NOT-EXPORT", "agent_result": {"transcript": "DO-NOT-EXPORT"},
            "started_at": "2026-01-01", "finished_at": "2026-01-02"}


def test_projection_strips_private_contents_and_preserves_normalization() -> None:
    raw = raw_trial()
    projected = inputs.project_trial(raw)
    assert b"DO-NOT-EXPORT" not in inputs.json_bytes(projected)
    old = normalize.normalize_trial(raw, "job/task__a/result.json", "c" * 64, "job")
    new = normalize.normalize_trial(projected, "job/task__a/result.json", "c" * 64, "job")
    assert old.pop("config_hash") != new.pop("config_hash")
    assert old == new
    assert new["score_present"] and new["exception_present"]
    assert new["reward_decimal"] == "0.12345678901234567890123456789"


@pytest.mark.parametrize("reward", [None, {}, {"rewards": None}, {"rewards": {}}, {"rewards": {"reward": 0}}, {"rewards": {"reward": True}}, {"rewards": {"reward": "0.5"}}, {"rewards": {"other": 1}}, {"rewards": {"reward": 1, "other": 0}}])
def test_reward_states_are_preserved_without_coercion(reward: object) -> None:
    raw = raw_trial()
    raw["verifier_result"] = reward
    projected = inputs.project_trial(raw)
    a = normalize.normalize_trial(raw, "job/task__a/result.json", "c" * 64, "job")
    b = normalize.normalize_trial(projected, "job/task__a/result.json", "c" * 64, "job")
    a.pop("config_hash")
    b.pop("config_hash")
    assert a == b


def test_absent_verifier_stays_absent() -> None:
    raw = raw_trial()
    del raw["verifier_result"]
    assert "verifier_result" not in inputs.project_trial(raw)


@pytest.mark.parametrize("change", [lambda raw: raw["task_id"].update(git_url="https://user:secret@example.org/task.git"),
                                  lambda raw: raw["exception_info"].update(exception_type="trace\nPRIVATE"),
                                  lambda raw: raw["verifier_result"].update(rewards={"reward": Decimal("NaN")}),
                                  lambda raw: raw.update(task_name="task\nPRIVATE")])
def test_unsafe_field_shapes_are_rejected(change: object) -> None:
    raw = raw_trial()
    change(raw)
    with pytest.raises(ValueError):
        inputs.project_trial(raw)


def test_decimal_serialization_is_numeric_exact_and_deterministic() -> None:
    value = {"a": Decimal("0.12345678901234567890123456789"), "b": [Decimal("1E-30"), None]}
    encoded = inputs.json_bytes(value)
    assert b'"0.123' not in encoded
    assert json.loads(encoded, parse_float=Decimal) == value
    assert gzip.compress(encoded, mtime=0) == gzip.compress(inputs.json_bytes(value), mtime=0)


def test_job_projection_preserves_scored_exception_overlap_and_counters() -> None:
    raw = {"id": "job", "finished_at": "2026-01-01", "started_at": "PRIVATE", "n_total_trials": 1,
           "stats": {"cost_usd": "PRIVATE", "n_trials": 1, "n_completed_trials": 1, "n_errors": 1, "n_errored_trials": 1,
                     "evals": {"agent__model__terminal-bench": {"n_trials": 1, "n_errors": 1, "metrics": [{"mean": 1}],
                               "reward_stats": {"reward": {"1": ["task__a"]}}, "exception_stats": {"AgentTimeoutError": ["task__a"]}}}}}
    projected = inputs.project_job(raw)
    assert b"PRIVATE" not in inputs.json_bytes(projected)
    row = normalize.normalize_trial(raw_trial(), "job/task__a/result.json", "c" * 64, "job")
    assert normalize.reconcile_job(raw, [row], ["task__a"]) == normalize.reconcile_job(projected, [row], ["task__a"])
    assert projected["stats"]["n_completed_trials"] == 1


def make_bundle(tmp_path: Path) -> tuple[Path, dict]:
    data, config, spec, _ = fixture(tmp_path)
    card = b"---\nlicense: apache-2.0\n---\n"
    (data / "README.md").write_bytes(card)
    (data / "README.md.receipt.json").write_text(json.dumps({"status": "success", "url": f"https://huggingface.co/datasets/{inventory.DATASET}/raw/{inventory.REVISION}/README.md",
                                                             "sha256": inputs.digest(card), "size_bytes": len(card)}))
    reference = tmp_path / "reference"
    reference.mkdir()
    sources = []
    for path in data.rglob("*.receipt.json"):
        source = json.loads(path.read_bytes())
        source["local_path"] = path.relative_to(data).as_posix().removesuffix(".receipt.json")
        sources.append(source)
    requests = json.loads((data / "census-completed.json").read_bytes())["requests"]
    for request in requests:
        source = next(row for row in sources if row["local_path"] == request["path"])
        request.update(source_sha256=source["sha256"], status=source["status"])

    def shard(name: str, rows: list) -> list[dict]:
        payload = inputs.json_bytes(rows)
        (reference / name).write_bytes(payload)
        return [{"path": name, "bytes": len(payload), "sha256": inputs.digest(payload), "entries": len(rows)}]

    source_index = {"sources": shard("locators.json", sources), "result_requests": shard("requests.json", requests)}
    (reference / "source_manifest.json").write_bytes(inputs.json_bytes(source_index))
    (reference / "provenance.json").write_bytes(inputs.json_bytes({"config_sha256": inputs.digest(config.read_bytes()), "task_spec_sha256": inputs.digest(spec.read_bytes())}))
    licenses = tmp_path / "licenses"
    licenses.mkdir()
    for name in ("LICENSE-APACHE-2.0.txt", "LICENSE-HARBOR.txt", "NOTICE.md"):
        (licenses / name).write_text("Synthetic license fixture, not redistributed source data.\n")
    output = tmp_path / "bundle"
    manifest = inputs.export_bundle(data, reference, output, config_path=config, task_spec_path=spec,
                                    license_dir=licenses,
                                    provenance={"dirty": False, "git_commit": "synthetic-fixture"})
    return output, manifest


def test_export_reader_recomputes_inputs_not_final_outputs(tmp_path: Path) -> None:
    output, manifest = make_bundle(tmp_path)
    bundle = inputs.load_bundle(output)
    assert len(bundle["trials"]) == 2 and len(bundle["jobs"]) == 1
    assert bundle["submission_paths"] == [inventory.SUBMISSION_ROOT + "/Agent__Model"]
    assert manifest["kind"] == "derived_scientific_inputs"
    assert all(row["license"] for row in manifest["payloads"])
    assert not any("PRIVATE" in path.read_text(errors="ignore") for path in output.glob("*.json"))
    trials_bytes = gzip.decompress((output / "trials.json.gz").read_bytes())
    assert b"NEVER-PUBLISH-ME" not in trials_bytes and b"PRIVATE-EXCEPTION" not in trials_bytes
    for trial in bundle["trials"]:
        assert set(trial["attested_hashes"]) == {"config_hash", "system_config_hash", "semantic_hash"}
        assert inputs.digest(inputs.json_bytes({k: v for k, v in trial.items() if k != "derived_sha256"})) == trial["derived_sha256"]


def test_payload_tampering_fails_before_arithmetic(tmp_path: Path) -> None:
    output, _ = make_bundle(tmp_path)
    with (output / "jobs.json.gz").open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(ValueError, match="payload integrity"):
        inputs.load_bundle(output)


def rewrite_payload(output: Path, name: str, value: object) -> None:
    data = gzip.compress(inputs.json_bytes(value), mtime=0)
    (output / name).write_bytes(data)
    manifest = json.loads((output / "manifest.json").read_bytes())
    descriptor = next(row for row in manifest["payloads"] if row["path"] == name)
    descriptor.update(sha256=inputs.digest(data), bytes=len(data))
    (output / "manifest.json").write_bytes(inputs.json_bytes(manifest))


def test_row_binding_tamper_fails_even_with_updated_payload_hash(tmp_path: Path) -> None:
    output, _ = make_bundle(tmp_path)
    rows = json.loads(gzip.decompress((output / "trials.json.gz").read_bytes()))
    rows[0]["raw"]["verifier_result"]["rewards"]["reward"] = 1
    rewrite_payload(output, "trials.json.gz", rows)
    with pytest.raises(ValueError, match="transformed row integrity"):
        inputs.load_bundle(output)


def test_reader_rejects_private_addition_even_when_rehashed(tmp_path: Path) -> None:
    output, _ = make_bundle(tmp_path)
    rows = json.loads(gzip.decompress((output / "trials.json.gz").read_bytes()))
    rows[0]["raw"]["trial_uri"] = "PRIVATE"
    rows[0]["derived_sha256"] = inputs._row_hash(rows[0])
    rewrite_payload(output, "trials.json.gz", rows)
    with pytest.raises(ValueError, match="nonallowlisted"):
        inputs.load_bundle(output)


def test_reader_rejects_unallowlisted_binding_fields(tmp_path: Path) -> None:
    output, _ = make_bundle(tmp_path)
    rows = json.loads(gzip.decompress((output / "jobs.json.gz").read_bytes()))
    rows[0]["private_notes"] = "PRIVATE"
    rows[0]["derived_sha256"] = inputs._row_hash(rows[0])
    rewrite_payload(output, "jobs.json.gz", rows)
    with pytest.raises(ValueError, match="nonallowlisted job binding"):
        inputs.load_bundle(output)


def test_source_url_must_bind_to_exact_original_path(tmp_path: Path) -> None:
    output, _ = make_bundle(tmp_path)
    rows = json.loads(gzip.decompress((output / "trials.json.gz").read_bytes()))
    rows[0]["source_url"] = rows[0]["source_url"].replace("task__a", "task__other")
    rows[0]["derived_sha256"] = inputs._row_hash(rows[0])
    rewrite_payload(output, "trials.json.gz", rows)
    with pytest.raises(ValueError, match="source mapping"):
        inputs.load_bundle(output)


def test_population_coverage_is_not_guessed_from_n_attempts(tmp_path: Path) -> None:
    output, _ = make_bundle(tmp_path)
    rows = json.loads(gzip.decompress((output / "jobs.json.gz").read_bytes()))
    rows[0]["directories"].append("not-retrieved")
    rows[0]["derived_sha256"] = inputs._row_hash(rows[0])
    rewrite_payload(output, "jobs.json.gz", rows)
    with pytest.raises(ValueError, match="complete named population"):
        inputs.load_bundle(output)


def test_population_source_projection_hash_is_checked(tmp_path: Path) -> None:
    output, manifest = make_bundle(tmp_path)
    manifest["population_sources"][0]["directories"].append("invented")
    (output / "manifest.json").write_bytes(inputs.json_bytes(manifest))
    with pytest.raises(ValueError, match="population projection hash"):
        inputs.load_bundle(output)


def test_reader_requires_no_original_cache_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, _ = make_bundle(tmp_path)
    original = Path.read_bytes
    def guarded_read(path: Path) -> bytes:
        assert path.resolve().is_relative_to(output.resolve()), "reader consulted the original cache"
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", guarded_read)
    assert len(inputs.load_bundle(output)["trials"]) == 2


def test_reader_rejects_path_traversal_descriptor(tmp_path: Path) -> None:
    output, manifest = make_bundle(tmp_path)
    altered = deepcopy(manifest)
    altered["payloads"][0]["path"] = "../config.json"
    (output / "manifest.json").write_bytes(inputs.json_bytes(altered))
    with pytest.raises(ValueError, match="payload set"):
        inputs.load_bundle(output)


def test_export_rejects_dirty_source_before_reading_cache(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="clean committed"):
        inputs.export_bundle(tmp_path, tmp_path, tmp_path / "new", provenance={"dirty": True, "git_commit": "x"})


def test_opaque_hash_depends_on_omitted_private_semantics() -> None:
    raw = raw_trial()
    changed = deepcopy(raw)
    changed["exception_info"]["exception_message"] = "different private information"
    assert inputs.project_trial(raw) == inputs.project_trial(changed)
    old = normalize.normalize_trial(raw, "job/task__a/result.json", "a" * 64, "job")
    system = analyze._system_hash(raw)
    assert analyze._semantic_hash(raw, old, system) != analyze._semantic_hash(changed, old, system)
