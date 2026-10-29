"""Allowlisted scientific observations, separate from acquisition history.

The projections preserve fields used by the frozen arithmetic and selection.
Opaque hashes attest omitted configuration/exception semantics; loading this
bundle cannot independently inspect those omitted original fields.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from experiments.unscored_trials import analyze, inventory, normalize

SCHEMA = "warrant-unscored-projection-v1"
TRANSFORM = "allowlist-normalize-equivalence-v1"
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_CLASS = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*\Z")
_LIMIT = 10_000_000
_EXPANDED_LIMIT = 256_000_000


def digest(data: bytes) -> str:
    """Return a SHA-256 binding for original or transformed bytes."""
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    """Serialize deterministically without converting Decimal numbers to strings."""
    def encode(item: object) -> str:
        if item is None or isinstance(item, (str, bool, int)):
            return json.dumps(item, ensure_ascii=True, allow_nan=False)
        if isinstance(item, Decimal):
            if not item.is_finite():
                raise ValueError("nonfinite JSON number")
            return str(item)
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError("nonfinite JSON number")
            return repr(item)
        if isinstance(item, list):
            return "[" + ",".join(encode(entry) for entry in item) + "]"
        if isinstance(item, dict) and all(isinstance(key, str) for key in item):
            return "{" + ",".join(encode(key) + ":" + encode(item[key]) for key in sorted(item)) + "}"
        raise ValueError("unsupported JSON representation")
    return (encode(value) + "\n").encode("utf-8")


def _load(data: bytes) -> Any:
    return json.loads(data, parse_float=Decimal, parse_constant=Decimal)


def _inside(root: Path, name: str) -> Path:
    candidate = (root / name).resolve()
    if not candidate.is_relative_to(root.resolve()) or candidate == root.resolve():
        raise ValueError("bundle/source path escapes root")
    return candidate


def _text(value: object, *, maximum: int = 2048) -> object:
    if value is None:
        return None
    if (not isinstance(value, str) or len(value) > maximum
            or any(ord(character) < 32 for character in value)):
        raise ValueError("unsafe or malformed scalar string")
    return value


def _select(raw: dict, fields: tuple[str, ...]) -> dict:
    return {key: _text(raw[key]) for key in fields if key in raw}


def _number(value: object) -> object:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, Decimal, float)):
        if not Decimal(str(value)).is_finite():
            raise ValueError("nonfinite scientific value")
        return value
    # A short malformed reward is retained as malformed, never coerced to zero.
    return _text(value, maximum=64)


def project_trial(raw: dict) -> dict:
    """Retain observed fields needed by normalize_trial; reject unsafe shapes."""
    if not isinstance(raw, dict):
        raise ValueError("trial must be an object")
    result = _select(raw, ("id", "trial_name", "task_name", "task_checksum", "source", "started_at", "finished_at"))
    for key, fields in (("task_id", ("git_url", "git_commit_id", "path", "org", "name", "ref")),
                        ("config", ("job_id",))):
        if key in raw:
            if raw[key] is None:
                result[key] = None
            elif isinstance(raw[key], dict):
                result[key] = _select(raw[key], fields)
            else:
                raise ValueError("unsupported identity/config shape")
    if "task_id" in result and isinstance(result["task_id"], dict):
        url = result["task_id"].get("git_url")
        if isinstance(url, str) and urlsplit(url).username is not None:
            raise ValueError("credentials in task URL")
    if "agent_info" in raw:
        agent = raw["agent_info"]
        if agent is None:
            result["agent_info"] = None
        elif isinstance(agent, dict):
            result["agent_info"] = _select(agent, ("name", "version"))
            if "model_info" in agent:
                model = agent["model_info"]
                if model is not None and not isinstance(model, dict):
                    raise ValueError("unsupported model shape")
                result["agent_info"]["model_info"] = None if model is None else _select(model, ("name",))
        else:
            raise ValueError("unsupported agent shape")
    if "exception_info" in raw:
        exception = raw["exception_info"]
        if exception is None:
            result["exception_info"] = None
        elif isinstance(exception, dict):
            value = exception.get("exception_type")
            if not isinstance(value, str) or len(value) > 128 or not _CLASS.fullmatch(value):
                raise ValueError("unsafe exception class")
            result["exception_info"] = {"exception_type": value}
        else:
            raise ValueError("unsupported exception shape")
    if "verifier_result" in raw:
        verifier = raw["verifier_result"]
        if verifier is None:
            result["verifier_result"] = None
        elif isinstance(verifier, dict):
            result["verifier_result"] = {}
            if "rewards" in verifier:
                rewards = verifier["rewards"]
                if rewards is None:
                    result["verifier_result"]["rewards"] = None
                elif isinstance(rewards, dict) and len(rewards) <= 32:
                    if any(not isinstance(key, str) or not _CLASS.fullmatch(key) or len(key) > 128 for key in rewards):
                        raise ValueError("unsafe reward channel")
                    result["verifier_result"]["rewards"] = {key: _number(value) for key, value in rewards.items()}
                else:
                    raise ValueError("unsupported reward shape")
        else:
            raise ValueError("unsupported verifier shape")
    return result


def project_job(raw: dict) -> dict:
    """Retain job counts, name indexes and metrics, excluding cost/token details."""
    if not isinstance(raw, dict):
        raise ValueError("job must be an object")
    result = _select(raw, ("id",))
    if "finished_at" in raw:
        result["finished_at"] = "present" if raw["finished_at"] is not None else None
    if "n_total_trials" in raw:
        value = raw["n_total_trials"]
        if type(value) is not int or value < 0:
            raise ValueError("malformed total counter")
        result["n_total_trials"] = value
    if "stats" not in raw:
        return result
    stats = raw["stats"]
    if not isinstance(stats, dict):
        raise ValueError("unsupported job statistics")
    projected: dict = {}
    for key in ("n_trials", "n_completed_trials", "n_errors", "n_errored_trials"):
        if key in stats:
            if type(stats[key]) is not int or stats[key] < 0:
                raise ValueError("malformed global counter")
            projected[key] = stats[key]
    if "evals" in stats:
        if not isinstance(stats["evals"], dict):
            raise ValueError("unsupported evaluations")
        evaluations = {}
        for key, evaluation in stats["evals"].items():
            _text(key)
            if not isinstance(evaluation, dict):
                raise ValueError("unsupported evaluation")
            selected = {}
            for counter in ("n_trials", "n_errors"):
                if counter in evaluation:
                    if type(evaluation[counter]) is not int or evaluation[counter] < 0:
                        raise ValueError("malformed evaluation counter")
                    selected[counter] = evaluation[counter]
            if "metrics" in evaluation:
                metrics = evaluation["metrics"]
                if not isinstance(metrics, list):
                    raise ValueError("unsupported metrics")
                selected["metrics"] = []
                for metric in metrics:
                    if not isinstance(metric, dict):
                        raise ValueError("unsupported metric")
                    selected["metrics"].append({_text(name, maximum=128): _number(value) for name, value in metric.items()})
            for index_name in ("reward_stats", "exception_stats"):
                if index_name not in evaluation:
                    continue
                index = evaluation[index_name]
                if not isinstance(index, dict):
                    raise ValueError("unsupported summary index")
                def names(values: object) -> list:
                    if not isinstance(values, list):
                        raise ValueError("summary names must be lists")
                    return [_text(name) for name in values]
                if index_name == "exception_stats":
                    selected[index_name] = {}
                    for error, values in index.items():
                        if not isinstance(error, str) or len(error) > 128 or not _CLASS.fullmatch(error):
                            raise ValueError("unsafe summary exception class")
                        selected[index_name][error] = names(values)
                else:
                    selected[index_name] = {}
                    for channel, reward_index in index.items():
                        if not isinstance(channel, str) or not _CLASS.fullmatch(channel) or not isinstance(reward_index, dict):
                            raise ValueError("unsupported summary reward channel")
                        selected[index_name][channel] = {_text(value, maximum=64): names(values) for value, values in reward_index.items()}
            evaluations[key] = selected
        projected["evals"] = evaluations
    result["stats"] = projected
    return result


def _row_hash(row: dict) -> str:
    return digest(json_bytes({key: value for key, value in row.items() if key != "derived_sha256"}))


def _source(data_root: Path, descriptor: dict) -> tuple[Any, bytes]:
    data = _inside(data_root, descriptor["local_path"]).read_bytes()
    if descriptor.get("status") != "success" or digest(data) != descriptor.get("sha256") or len(data) != descriptor.get("size_bytes"):
        raise ValueError("original source integrity failure")
    inventory._pinned_request(descriptor)
    return _load(data), data


def _shards(reference: Path, descriptors: list[dict]) -> list[dict]:
    rows = []
    for descriptor in descriptors:
        data = _inside(reference, descriptor["path"]).read_bytes()
        shard = _load(data)
        if digest(data) != descriptor["sha256"] or len(data) != descriptor["bytes"] or len(shard) != descriptor["entries"]:
            raise ValueError("source locator shard integrity failure")
        rows.extend(shard)
    return rows


def export_bundle(data_root: Path, reference_dir: Path, output_dir: Path, *,
                  config_path: Path | None = None, task_spec_path: Path | None = None,
                  license_dir: Path | None = None,
                  provenance: dict | None = None) -> dict:
    """Build scientific inputs by rereading original sources; never final scores."""
    provenance = inventory.clean_provenance() if provenance is None else provenance
    if provenance.get("dirty") is not False or not provenance.get("git_commit"):
        raise ValueError("clean committed provenance required")
    if output_dir.exists():
        raise FileExistsError("preserve existing input bundle")
    reference_dir, data_root = reference_dir.resolve(), data_root.resolve()
    config_path = config_path or Path(__file__).with_name("config.json")
    task_spec_path = task_spec_path or reference_dir / "context/task_spec.original.json"
    license_dir = license_dir or Path(__file__).with_name("license_sources")
    config_bytes, task_bytes = config_path.read_bytes(), task_spec_path.read_bytes()
    old_provenance = _load((reference_dir / "provenance.json").read_bytes())
    if digest(config_bytes) != old_provenance["config_sha256"] or digest(task_bytes) != old_provenance["task_spec_sha256"]:
        raise ValueError("frozen configuration or task specification differs")
    source_index_data = (reference_dir / "source_manifest.json").read_bytes()
    source_index = _load(source_index_data)
    sources = _shards(reference_dir, source_index["sources"])
    requests = _shards(reference_dir, source_index["result_requests"])
    by_local = {row["local_path"]: row for row in sources}
    if len(by_local) != len(sources):
        raise ValueError("duplicate source locator")
    by_url: dict[str, list[dict]] = defaultdict(list)
    for source in sources:
        if source.get("status") == "success":
            by_url[source["url"]].append(source)
    card_url = f"https://huggingface.co/datasets/{inventory.DATASET}/raw/{inventory.REVISION}/README.md"
    cards = by_url.get(card_url, [])
    if not cards or len({row["sha256"] for row in cards}) != 1:
        raise ValueError("pinned source license declaration unavailable")
    card = min(cards, key=lambda row: row["local_path"])
    card_bytes = _inside(data_root, card["local_path"]).read_bytes()
    card_parts = card_bytes.split(b"---", 2)
    if (digest(card_bytes) != card["sha256"] or len(card_bytes) != card["size_bytes"]
            or len(card_parts) != 3 or card_parts[0].strip()
            or b"license: apache-2.0" not in card_parts[1].splitlines()):
        raise ValueError("pinned source license declaration differs")

    population_sources = []
    def listing(parent: str) -> list[dict]:
        candidates = [row for row in sources if row.get("status") == "success"
                      and "/tree/" + inventory.REVISION + "/" in row.get("url", "")
                      and unquote(urlsplit(row["url"]).path).split("/tree/" + inventory.REVISION + "/", 1)[-1] == parent]
        if not candidates:
            raise ValueError("required population listing unavailable")
        source = min(candidates, key=lambda row: row["local_path"])
        if len({row["sha256"] for row in candidates}) != 1:
            raise ValueError("conflicting pinned population listings")
        # Reuse the original completeness checks, without historical receipts.
        raw, _ = _source(data_root, source)
        query = parse_qs(urlsplit(source["url"]).query)
        limit = int(query.get("limit", ["0"])[0])
        if (query.get("recursive") != ["false"] or limit <= 0 or not isinstance(raw, list)
                or len(raw) >= limit or source.get("pagination_link")):
            raise ValueError("population listing is incomplete")
        seen = set()
        for entry in raw:
            if (not isinstance(entry, dict) or entry.get("type") not in {"file", "directory"}
                    or PurePosixPath(entry.get("path", "")).parent.as_posix() != parent
                    or entry["path"] in seen):
                raise ValueError("invalid population listing entry")
            seen.add(entry["path"])
        selected = [{"type": entry["type"], "path": entry["path"]} for entry in raw]
        projected_directories = sorted(entry["path"] for entry in raw if entry["type"] == "directory")
        population_sources.append({"source_path": parent, "source_url": source["url"],
                                   "source_sha256": source["sha256"],
                                   "derived_sha256": digest(json_bytes({"directories": projected_directories})),
                                   "directories": projected_directories})
        return selected

    submission_paths = sorted(entry["path"] for entry in listing(inventory.SUBMISSION_ROOT) if entry["type"] == "directory")
    jobs = {}
    for submission_path in submission_paths:
        for entry in listing(submission_path):
            if entry["type"] == "directory":
                path = entry["path"]
                directories = sorted(PurePosixPath(value["path"]).name for value in listing(path) if value["type"] == "directory")
                jobs[path] = {"job_path": path, "submission": PurePosixPath(submission_path).name, "directories": directories}
    if len(requests) != len({row["source_path"] for row in requests}):
        raise ValueError("duplicate scientific source request")
    expected = {path + "/result.json" for path in jobs}
    expected.update(path + "/" + name + "/result.json" for path, job in jobs.items() for name in job["directories"])
    if {row["source_path"] for row in requests} != expected:
        raise ValueError("source requests do not cover complete listed census")
    trials, raw_jobs, original_refs = [], {}, []
    for request in sorted(requests, key=lambda row: row["source_path"]):
        source = by_local[request["path"]]
        if source.get("url") != request["url"] or source.get("sha256") != request.get("source_sha256"):
            raise ValueError("source request and original hash differ")
        analyze._validate_result_request(request, jobs)
        binding = {"source_path": request["source_path"], "source_sha256": source.get("sha256"), "source_url": request["url"],
                   "job_path": request["job"], "submission": request["submission"]}
        if source.get("status") != "success":
            if request["kind"] != "job":
                raise ValueError("this projection schema requires all trial observations")
            raw_jobs[request["job"]] = {**binding, "source_available": False, "raw": None}
            continue
        raw, _ = _source(data_root, source)
        if request["kind"] == "job":
            projected = project_job(raw)
            raw_jobs[request["job"]] = {**binding, "source_available": True, "raw": projected}
        else:
            projected = project_trial(raw)
            old = normalize.normalize_trial(raw, request["source_path"], source["sha256"], request["job"])
            new = normalize.normalize_trial(projected, request["source_path"], source["sha256"], request["job"])
            if {k: v for k, v in old.items() if k != "config_hash"} != {k: v for k, v in new.items() if k != "config_hash"}:
                raise ValueError("trial projection changes normalized observation")
            system_hash = analyze._system_hash(raw)
            row = {**binding, "raw": projected, "attested_hashes": {"config_hash": old["config_hash"],
                   "system_config_hash": system_hash, "semantic_hash": analyze._semantic_hash(raw, old, system_hash)}}
            row["derived_sha256"] = _row_hash(row)
            trials.append(row)
    job_rows = []
    for path, job in sorted(jobs.items()):
        config_url = f"https://huggingface.co/datasets/{inventory.DATASET}/raw/{inventory.REVISION}/{path}/config.json"
        config_sources = by_url.get(config_url, [])
        if not config_sources or len({row["sha256"] for row in config_sources}) != 1:
            raise ValueError("missing or conflicting job config input")
        source = min(config_sources, key=lambda row: row["local_path"])
        raw_config, _ = _source(data_root, source)
        public_config = inventory._public_config(raw_config)
        original_refs.append({"source_path": path + "/config.json", "source_url": config_url,
                              "source_sha256": source["sha256"], "derived_sha256": digest(json_bytes(public_config))})
        row = {**job, **raw_jobs[path], "config_status": "success", "population_config": public_config,
               "config_source_sha256": source["sha256"], "config_source_url": config_url}
        row["derived_sha256"] = _row_hash(row)
        job_rows.append(row)
    # Verify job projection equivalence against observations, not final jobchecks.
    grouped = defaultdict(list)
    for trial in trials:
        grouped[trial["job_path"]].append(normalize.normalize_trial(trial["raw"], trial["source_path"], trial["source_sha256"], trial["job_path"]))
    for job in job_rows:
        if job["source_available"]:
            request = next(row for row in requests if row["kind"] == "job" and row["job"] == job["job_path"])
            original, _ = _source(data_root, by_local[request["path"]])
            old = normalize.reconcile_job(original, grouped[job["job_path"]], job["directories"])
            new = normalize.reconcile_job(job["raw"], grouped[job["job_path"]], job["directories"])
            if old != new:
                raise ValueError("job projection changes frozen reconciliation")
    manifest = {"schema_version": SCHEMA, "transform_id": TRANSFORM, "dataset": inventory.DATASET, "revision": inventory.REVISION,
                "kind": "derived_scientific_inputs", "submission_paths": submission_paths,
                "provenance": provenance, "reference_source_index_sha256": digest(source_index_data),
                "source_license_declaration": {"url": card_url, "sha256": card["sha256"], "declared_license": "Apache-2.0"},
                "license_sources": [
                    {"url": "https://www.apache.org/licenses/LICENSE-2.0.txt", "path": "LICENSE-APACHE-2.0.txt", "sha256": digest((license_dir / "LICENSE-APACHE-2.0.txt").read_bytes())},
                    {"url": "https://raw.githubusercontent.com/harbor-framework/harbor/5a22a1dd4cc42fff8418bcb1e796ceb3624df931/LICENSE", "path": "LICENSE-HARBOR.txt", "sha256": digest((license_dir / "LICENSE-HARBOR.txt").read_bytes())}],
                "population_sources": population_sources, "config_sources": original_refs,
                "limits": "Opaque hashes attest omitted config/exception/verifier semantics; this bundle cannot independently verify omitted raw content. No original roster, retries, website imports or human adjudication are supplied.",
                "payloads": []}
    attribution = ("Third-party scientific observations\n\n"
                   f"Source: https://huggingface.co/datasets/{inventory.DATASET}/tree/{inventory.REVISION}\n"
                   "The source dataset card declares Apache-2.0. These transformed observations retain that attribution; they are not relabeled under Warrant's code license.\n"
                   f"Pinned license declaration: {card_url}\nOriginal card SHA-256: {card['sha256']}\n"
                   "License text: https://www.apache.org/licenses/LICENSE-2.0\n"
                   "Harbor's pinned source LICENSE is Apache-2.0; its copyright and license terms are retained in LICENSE-HARBOR.txt.\n"
                   f"Transformation: {TRANSFORM}; allowlisted fields, original hashes and derived row hashes retained.\n").encode()
    payloads = [("config.json", config_bytes, "frozen_analysis_configuration", "MIT", ["dataset", "revision", "native_absolute_tolerance"]),
                ("task_spec.json", task_bytes, "pinned_official_task_specification", "Apache-2.0", ["spec.tasks"]),
                ("trials.json.gz", gzip.compress(json_bytes(trials), mtime=0), "derived_trial_observations", "Apache-2.0", ["source_path", "source_sha256", "source_url", "raw", "attested_hashes", "derived_sha256"]),
                ("jobs.json.gz", gzip.compress(json_bytes(job_rows), mtime=0), "derived_job_and_population_observations", "Apache-2.0", ["job_path", "directories", "population_config", "raw", "derived_sha256"]),
                ("ATTRIBUTION.txt", attribution, "third_party_attribution", "Apache-2.0", [])]
    for name, role in (("LICENSE-APACHE-2.0.txt", "apache_license_terms"),
                       ("LICENSE-HARBOR.txt", "harbor_upstream_license_terms"),
                       ("NOTICE.md", "source_attribution_and_modification_notice")):
        payloads.append((name, (license_dir / name).read_bytes(), role, "Apache-2.0", []))
    if any(len(data) >= _LIMIT for _, data, *_ in payloads):
        raise ValueError("portable payload exceeds ordinary Git size ceiling")
    output_dir.mkdir(parents=True)
    for name, data, role, license_name, fields in payloads:
        (output_dir / name).write_bytes(data)
        manifest["payloads"].append({"path": name, "sha256": digest(data), "bytes": len(data), "role": role,
                                     "license": license_name, "required_fields": fields})
    (output_dir / "manifest.json").write_bytes(json_bytes(manifest))
    return manifest


def _check_hash(value: object, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise ValueError("invalid hash binding")


def _public_config_shape(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"n_attempts", "datasets", "tasks"}:
        raise ValueError("nonallowlisted population configuration")
    if type(value["n_attempts"]) is not int or value["n_attempts"] < 1:
        raise ValueError("invalid declared repetition count")
    if not isinstance(value["datasets"], list) or not isinstance(value["tasks"], list):
        raise ValueError("invalid population selectors")
    dataset_fields = {"name", "version", "ref", "task_names", "exclude_task_names", "n_tasks", "local_path_declared", "registry_path_declared"}
    for entry in value["datasets"]:
        if not isinstance(entry, dict) or set(entry) != dataset_fields:
            raise ValueError("nonallowlisted dataset selector")
        for field in ("name", "version", "ref"):
            _text(entry[field])
        for field in ("task_names", "exclude_task_names"):
            if entry[field] is not None:
                if not isinstance(entry[field], list):
                    raise ValueError("invalid task selector list")
                for name in entry[field]:
                    _text(name)
        if entry["n_tasks"] is not None and (type(entry["n_tasks"]) is not int or entry["n_tasks"] < 0):
            raise ValueError("invalid declared task count")
        if any(type(entry[field]) is not bool for field in ("local_path_declared", "registry_path_declared")):
            raise ValueError("invalid local selector flag")
    for entry in value["tasks"]:
        if not isinstance(entry, dict):
            raise ValueError("invalid explicit task selector")
        if set(entry) == {"selector_sha256"}:
            _check_hash(entry["selector_sha256"])
        elif set(entry) == {"name", "task_name", "version", "ref", "local_path_declared"}:
            for field in ("name", "task_name", "version", "ref"):
                _text(entry[field])
            if type(entry["local_path_declared"]) is not bool:
                raise ValueError("invalid local task flag")
        else:
            raise ValueError("nonallowlisted explicit task selector")


def load_bundle(root: Path) -> dict:
    """Verify self-contained projections without access to acquisition history."""
    manifest = _load((root / "manifest.json").read_bytes())
    manifest_fields = {"schema_version", "transform_id", "dataset", "revision", "kind", "submission_paths", "provenance", "reference_source_index_sha256", "population_sources", "config_sources", "limits", "payloads", "source_license_declaration", "license_sources"}
    if not isinstance(manifest, dict) or set(manifest) != manifest_fields:
        raise ValueError("nonallowlisted bundle manifest")
    if manifest.get("schema_version") != SCHEMA or manifest.get("transform_id") != TRANSFORM:
        raise ValueError("unsupported portable input schema/transform")
    if manifest.get("dataset") != inventory.DATASET or manifest.get("revision") != inventory.REVISION:
        raise ValueError("unfrozen portable source")
    expected = {"config.json", "task_spec.json", "trials.json.gz", "jobs.json.gz", "ATTRIBUTION.txt",
                "LICENSE-APACHE-2.0.txt", "LICENSE-HARBOR.txt", "NOTICE.md"}
    descriptors = manifest.get("payloads", [])
    if len(descriptors) != len(expected) or {row.get("path") for row in descriptors} != expected:
        raise ValueError("portable payload set is incomplete or duplicated")
    loaded = {}
    for descriptor in descriptors:
        _check_hash(descriptor.get("sha256"))
        path = _inside(root, descriptor["path"])
        data = path.read_bytes()
        if len(data) >= _LIMIT or type(descriptor.get("bytes")) is not int or len(data) != descriptor["bytes"] or digest(data) != descriptor["sha256"]:
            raise ValueError("portable payload integrity failure")
        if path.suffix == ".gz":
            import io
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                expanded = stream.read(_EXPANDED_LIMIT + 1)
            if len(expanded) > _EXPANDED_LIMIT:
                raise ValueError("portable decompression limit exceeded")
            loaded[path.name.removesuffix(".json.gz")] = _load(expanded)
        elif path.suffix == ".json":
            loaded[path.stem] = _load(data)
    trials, jobs = loaded["trials"], loaded["jobs"]
    if not isinstance(trials, list) or not isinstance(jobs, list):
        raise ValueError("portable observations must be lists")
    job_paths = set()
    for job in jobs:
        if not isinstance(job, dict) or _row_hash(job) != job.get("derived_sha256"):
            raise ValueError("job transformed row integrity failure")
        if set(job) != {"job_path", "submission", "directories", "config_status", "population_config", "config_source_sha256", "config_source_url", "source_path", "source_sha256", "source_url", "source_available", "raw", "derived_sha256"}:
            raise ValueError("nonallowlisted job binding")
        if job["job_path"] in job_paths or type(job.get("source_available")) is not bool:
            raise ValueError("duplicate or invalid job identity")
        job_paths.add(job["job_path"])
        if len(job["directories"]) != len(set(job["directories"])) or any(not isinstance(name, str) or "/" in name or "\\" in name for name in job["directories"]):
            raise ValueError("invalid named directory population")
        if job["source_available"]:
            if project_job(job["raw"]) != job["raw"]:
                raise ValueError("nonallowlisted job content")
        elif job.get("raw") is not None:
            raise ValueError("unavailable source has observations")
        _check_hash(job.get("source_sha256"), nullable=not job["source_available"])
        _check_hash(job.get("config_source_sha256"))
        _public_config_shape(job["population_config"])
        if job["source_path"] != job["job_path"] + "/result.json" or job["submission"] != PurePosixPath(job["job_path"]).parent.name:
            raise ValueError("job source identity differs")
        inventory._pinned_request({"url": job["source_url"], "source_path": job["source_path"]})
        inventory._pinned_request({"url": job["config_source_url"], "source_path": job["job_path"] + "/config.json"})
    seen = set()
    for trial in trials:
        if not isinstance(trial, dict) or _row_hash(trial) != trial.get("derived_sha256"):
            raise ValueError("trial transformed row integrity failure")
        if set(trial) != {"source_path", "source_sha256", "source_url", "job_path", "submission", "raw", "attested_hashes", "derived_sha256"}:
            raise ValueError("nonallowlisted trial binding")
        if trial["source_path"] in seen or trial["job_path"] not in job_paths:
            raise ValueError("duplicate or unknown trial source")
        seen.add(trial["source_path"])
        if project_trial(trial["raw"]) != trial["raw"]:
            raise ValueError("nonallowlisted trial content")
        _check_hash(trial.get("source_sha256"))
        if set(trial.get("attested_hashes", {})) != {"config_hash", "system_config_hash", "semantic_hash"}:
            raise ValueError("missing opaque semantic attestations")
        for value in trial["attested_hashes"].values():
            _check_hash(value)
        if trial["submission"] != PurePosixPath(trial["job_path"]).parent.name:
            raise ValueError("trial submission identity differs")
        inventory._pinned_request({"url": trial["source_url"], "source_path": trial["source_path"]})
    expected_trials = {job["job_path"] + "/" + name + "/result.json" for job in jobs for name in job["directories"]}
    if seen != expected_trials:
        raise ValueError("trial observations differ from complete named population")
    submission_paths = manifest.get("submission_paths")
    if (not isinstance(submission_paths, list) or len(set(submission_paths)) != len(submission_paths)
            or {PurePosixPath(job["job_path"]).parent.as_posix() for job in jobs} != set(submission_paths)):
        raise ValueError("submission population differs from jobs")
    population_sources = manifest.get("population_sources")
    if not isinstance(population_sources, list):
        raise ValueError("missing population source bindings")
    listing_by_path = {}
    for source in population_sources:
        if not isinstance(source, dict) or set(source) != {"source_path", "source_url", "source_sha256", "derived_sha256", "directories"}:
            raise ValueError("nonallowlisted population source")
        if source["source_path"] in listing_by_path:
            raise ValueError("duplicate population listing source")
        _check_hash(source["source_sha256"])
        inventory._pinned_request({"url": source["source_url"], "source_path": source["source_path"]})
        if source["derived_sha256"] != digest(json_bytes({"directories": source["directories"]})):
            raise ValueError("population projection hash differs")
        listing_by_path[source["source_path"]] = source
    if set(listing_by_path) != {inventory.SUBMISSION_ROOT, *submission_paths, *job_paths}:
        raise ValueError("population sources do not cover complete hierarchy")
    if listing_by_path[inventory.SUBMISSION_ROOT]["directories"] != sorted(submission_paths):
        raise ValueError("top listing and submissions differ")
    for submission_path in submission_paths:
        if listing_by_path[submission_path]["directories"] != sorted(path for path in job_paths if PurePosixPath(path).parent.as_posix() == submission_path):
            raise ValueError("submission listing and jobs differ")
    for job in jobs:
        if listing_by_path[job["job_path"]]["directories"] != sorted(job["job_path"] + "/" + name for name in job["directories"]):
            raise ValueError("job listing and final directories differ")
    return {**loaded, "submission_paths": submission_paths, "manifest": manifest}


def main() -> None:
    """Export a reviewed, versioned projection from clean committed source."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = export_bundle(args.data_root, args.reference_dir, args.output_dir)
    print(json.dumps({"schema": manifest["schema_version"], "payloads": manifest["payloads"]}, indent=2))


if __name__ == "__main__":
    main()
