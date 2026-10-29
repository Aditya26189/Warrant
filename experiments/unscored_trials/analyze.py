"""Offline final-release accounting; never reconstruct absent planned trials.

Native operational zero accounting and score-completion envelopes describe
different policies. These artifacts do not recover historical retry attempts,
perfect-infrastructure outcomes, or an adjudicated website ranking.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal
from fractions import Fraction
from itertools import combinations
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from tqdm import tqdm

from experiments.unscored_trials import bounds, inventory, normalize


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_default(value: object) -> str:
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported output type: {type(value).__name__}")


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, default=_json_default, allow_nan=False) + "\n").encode()


def _canonical_hash(value: object) -> str:
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default, allow_nan=False).encode())


def _load(data: bytes) -> Any:
    return json.loads(data, parse_float=Decimal, parse_constant=Decimal)


def _inside(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("source path escapes data root")
    return path


class VerifiedCache:
    """Read each successful source once and verify bytes before interpretation."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.receipts: dict[str, dict] = {}
        self.verified: set[str] = set()
        self.memo: dict[str, Any] = {}
        immutable_url_hashes: dict[str, str] = {}
        allowed = {"url", "final_url", "retrieved_utc", "status", "http_status", "size_bytes", "sha256", "limit_bytes", "timeout_seconds", "pagination_link", "content_length", "error_type"}
        for path in sorted(self.root.rglob("*.receipt.json")):
            data = path.read_bytes()
            raw = json.loads(data)
            name = path.relative_to(self.root).as_posix().removesuffix(".receipt.json")
            if not isinstance(raw, dict) or raw.get("status") not in {"success", "failed"}:
                raise ValueError("malformed source receipt")
            if raw["status"] == "failed" and _inside(self.root, name).exists():
                raise ValueError("failed source has ambiguous payload")
            if raw["status"] == "success":
                url = raw.get("url")
                metadata_api = f"https://huggingface.co/api/datasets/{inventory.DATASET}"
                if url != metadata_api:
                    inventory._pinned_request(raw)
                    if url in immutable_url_hashes and immutable_url_hashes[url] != raw.get("sha256"):
                        raise ValueError("immutable source URL has conflicting successful hashes")
                    immutable_url_hashes[url] = raw.get("sha256")
            self.receipts[name] = {"local_path": name, "receipt_sha256": _digest(data), **{key: raw[key] for key in allowed if key in raw}}

    def read(self, name: str, *, memo: bool = True) -> Any:
        """Return parsed verified JSON; memoize only small metadata/job sources."""
        if name in self.memo:
            return self.memo[name]
        if name in self.verified:
            raise ValueError("source requested twice without memoization")
        data = self.verify(name)
        value = _load(data)
        if memo:
            self.memo[name] = value
        return value

    def verify(self, name: str) -> bytes:
        """Verify a source's successful receipt and byte hash before use."""
        receipt = self.receipts.get(name, {})
        if receipt.get("status") != "success":
            raise ValueError("required source lacks successful receipt")
        if name in self.verified:
            raise ValueError("source bytes would be verified twice")
        data = _inside(self.root, name).read_bytes()
        if (type(receipt.get("size_bytes")) is not int or len(data) != receipt["size_bytes"]
                or _digest(data) != receipt.get("sha256")
                or len(data) > receipt.get("limit_bytes", len(data))):
            raise ValueError("source bytes do not match receipt")
        self.verified.add(name)
        return data

    def finish(self) -> None:
        """Verify remaining successful cache payloads without interpreting them."""
        for name, receipt in self.receipts.items():
            if receipt["status"] == "success" and name not in self.verified:
                self.verify(name)


def _tree(cache: VerifiedCache, name: str, parent: str) -> list[dict]:
    receipt = cache.receipts[name]
    inventory._pinned_request(receipt)
    query = parse_qs(urlsplit(receipt["url"]).query)
    limit = int(query.get("limit", ["0"])[0])
    if query.get("recursive") != ["false"] or limit <= 0 or receipt.get("pagination_link"):
        raise ValueError("population listing is not complete nonrecursive bounded evidence")
    if unquote(urlsplit(receipt["url"]).path).split(f"/tree/{inventory.REVISION}/", 1)[-1] != parent:
        raise ValueError("tree source and parent differ")
    entries = cache.read(name)
    if not isinstance(entries, list) or len(entries) >= limit:
        raise ValueError("population listing may be truncated")
    paths = set()
    for entry in entries:
        if (not isinstance(entry, dict) or entry.get("type") not in {"file", "directory"}
                or PurePosixPath(entry.get("path", "")).parent.as_posix() != parent
                or entry["path"] in paths):
            raise ValueError("malformed or duplicate tree entry")
        paths.add(entry["path"])
    return entries


def _request_rows(path: Path) -> tuple[list[dict], str]:
    data = path.read_bytes()
    value = json.loads(data)
    rows = value.get("requests") if isinstance(value, dict) else value
    if not isinstance(rows, list):
        raise ValueError("request manifest must contain rows")
    return rows, _digest(data)


def _validate_request(cache: VerifiedCache, row: dict) -> None:
    inventory._pinned_request(row)
    receipt = cache.receipts.get(row["path"])
    if receipt is None or receipt.get("url") != row["url"]:
        raise ValueError("request source and receipt differ")
    prior = row.get("prior_failed_path")
    if prior and cache.receipts.get(prior, {}).get("status") != "failed":
        raise ValueError("retrieval retry lacks prior failed receipt")


def _validate_result_request(row: dict, jobs: dict[str, dict]) -> None:
    job_path = row.get("job")
    if job_path not in jobs or row.get("submission") != jobs[job_path]["submission"]:
        raise ValueError("request job/submission identity differs from pinned listing")
    source_path = row.get("source_path")
    if row.get("kind") == "job":
        valid = source_path == job_path + "/result.json"
    elif row.get("kind") == "trial" and isinstance(source_path, str):
        path = PurePosixPath(source_path)
        valid = (path.name == "result.json" and path.parent.parent.as_posix() == job_path
                 and path.parent.name in jobs[job_path]["directories"])
    else:
        valid = False
    if not valid:
        raise ValueError("result request kind/source is not bound to its listed job/trial")


def _system_hash(raw: dict) -> str:
    config = raw.get("config")
    config = config if isinstance(config, dict) else {}
    return _canonical_hash({key: config.get(key) for key in ("agent", "environment", "verifier", "timeout_multiplier")})


def _semantic_hash(raw: dict, row: dict, system_hash: str) -> str:
    # The opaque digest compares private exception semantics without exporting
    # exception messages, traces, environment variables, or agent kwargs.
    return _canonical_hash({
        "identity": {key: row.get(key) for key in ("task_name", "task_git_url", "task_git_commit", "task_path", "task_checksum", "agent_name", "agent_version", "model_name", "source_dataset", "reward_status", "reward_decimal", "started_at", "finished_at")},
        "exception_info": raw.get("exception_info"), "system_config_hash": system_hash,
        "verifier_result": raw.get("verifier_result"),
    })


def deduplicate_submission(rows: list[dict]) -> tuple[list[dict], list[dict], list[str]]:
    """Deduplicate only explicit identical UUID semantics; quarantine conflicts.

    Rows remain in the source execution ledger regardless of this analytical
    disposition. Neither file order nor repeated task names establishes retries.
    """
    indexed: dict[str, list[dict]] = defaultdict(list)
    issues = []
    for row in rows:
        if not row.get("trial_uuid"):
            issues.append("missing_or_invalid_trial_uuid")
        else:
            indexed[row["trial_uuid"]].append(row)
    retained, ledger = [], []
    for trial_uuid, aliases in sorted(indexed.items()):
        semantic_hashes = {row["semantic_hash"] for row in aliases}
        if len(semantic_hashes) != 1:
            issues.append("conflicting_uuid_semantics")
            ledger.append({"trial_uuid": trial_uuid, "status": "quarantined_conflict", "source_aliases": sorted(row["source_path"] for row in aliases)})
            continue
        chosen = min(aliases, key=lambda row: row["source_path"]).copy()
        chosen["source_aliases"] = sorted(row["source_path"] for row in aliases)
        chosen["source_alias_count"] = len(aliases)
        retained.append(chosen)
        if len(aliases) > 1:
            ledger.append({"trial_uuid": trial_uuid, "status": "identical_export_aliases", "source_aliases": chosen["source_aliases"]})
    return retained, ledger, sorted(set(issues))


def submission_policies(
    rows: list[dict], official_tasks: dict[str, dict], config: dict,
) -> tuple[dict | None, list[str], str | None]:
    """Validate complete task definitions before calculating fixed weights."""
    reasons = []
    if not rows:
        return None, ["no_supported_named_final_records"], None
    tasks: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if not row.get("native_supported"):
            reasons.append("unsupported_reward_schema")
        if row.get("identity_issues"):
            reasons.append("unresolved_record_identity")
        name = row.get("task_name")
        if name not in official_tasks:
            reasons.append("nonofficial_or_missing_task_name")
            continue
        tasks[name].append(row)
        expected = official_tasks[name]
        if (row.get("task_git_url") != config["official_task_git_url"]
                or row.get("task_git_commit") != config["official_task_revision"]
                or row.get("task_path") != expected["path"]):
            reasons.append("local_unpinned_or_variant_task_definition")
        if not row.get("task_checksum"):
            reasons.append("missing_task_checksum")
    if set(tasks) != set(official_tasks):
        reasons.append("incomplete_official_task_universe")
    signatures = []
    for name, records in sorted(tasks.items()):
        definitions = {(row.get("task_git_url"), row.get("task_git_commit"), row.get("task_path"), row.get("task_checksum")) for row in records}
        if len(definitions) != 1:
            reasons.append("conflicting_task_definition_or_checksum")
        signatures.append((name, sorted(definitions, key=str)))
    if reasons:
        return None, sorted(set(reasons)), None
    policies = bounds.aggregate_tasks([(row["task_name"], None if not row["score_present"] else Decimal(row["reward_decimal"])) for row in rows])
    return policies, [], _canonical_hash(signatures)


def compare_populations(populations: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """Enumerate every eligible pair and exclude shared execution identities."""
    matrix, pairs = [], []
    for a, b in combinations(sorted(populations), 2):
        shared = sorted(populations[a]["uuids"] & populations[b]["uuids"])
        reasons = []
        if populations[a]["signature"] != populations[b]["signature"]:
            reasons.append("incompatible_task_definition_or_checksum")
        if shared:
            reasons.append("shared_explicit_execution_uuid")
        matrix.append({"submission_a": a, "submission_b": b, "compatible_primary": not reasons, "exclusion_reasons": reasons, "shared_execution_uuid_count": len(shared), "shared_execution_uuids": shared})
        if reasons:
            continue
        for policy_name in ("equal_task", "pooled"):
            a_policy, b_policy = populations[a]["policy"][policy_name], populations[b]["policy"][policy_name]
            result = bounds.classify_pair(a_policy["bounds"], b_policy["bounds"], a_policy["native_mean"], b_policy["native_mean"])
            pairs.append({"submission_a": a, "submission_b": b, "policy": policy_name, "population": "each_submission_deduplicated_named_final_records_on_exact_matching_task_definitions", "weighting": "equal_task_then_equal_records_within_task" if policy_name == "equal_task" else "equal_named_final_record_weights", "native_a": a_policy["native_mean"], "native_b": b_policy["native_mean"], **result, "interpretation": "compatible_completions_not_observed_corrected_rankings"})
    return matrix, pairs


def _csv_value(value: object) -> object:
    if isinstance(value, (list, dict, tuple)):
        return json.dumps(value, sort_keys=True, default=_json_default, allow_nan=False)
    return _json_default(value) if isinstance(value, (Fraction, Decimal)) else value


def _csv(path: Path, rows: list[dict], *, fields: list[str] | None = None) -> None:
    keys = fields or sorted({key for row in rows for key in row}) or ["status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows({key: _csv_value(row.get(key)) for key in keys} for row in rows)


def _json_file(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(_json(value))


def _json_shards(output: Path, prefix: str, rows: list[dict], maximum: int = 4_000_000) -> list[dict]:
    shards, batch, size = [], [], 2
    for row in rows:
        encoded_size = len(_json(row)) + 4
        if encoded_size > maximum:
            raise ValueError("individual evidence entry exceeds shard limit")
        if batch and size + encoded_size > maximum:
            name = f"{prefix}/{len(shards):04d}.json"
            _json_file(output / name, batch)
            data = (output / name).read_bytes()
            shards.append({"path": name, "sha256": _digest(data), "bytes": len(data), "entries": len(batch)})
            batch, size = [], 2
        batch.append(row)
        size += encoded_size
    if batch:
        name = f"{prefix}/{len(shards):04d}.json"
        _json_file(output / name, batch)
        data = (output / name).read_bytes()
        shards.append({"path": name, "sha256": _digest(data), "bytes": len(data), "entries": len(batch)})
    if any(shard["bytes"] >= 5_000_000 for shard in shards):
        raise ValueError("JSON evidence shard exceeded safe publication size")
    return shards


def _execution_shards(output: Path, submission: str, rows: list[dict]) -> list[dict]:
    keys = sorted({key for row in rows for key in row}) or ["status"]
    identity = _digest(submission.encode())[:16]
    shards, lines, size, count = [], [], 0, 0

    def encode(row: dict | None) -> bytes:
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=keys)
        if row is None:
            writer.writeheader()
        else:
            writer.writerow({key: _csv_value(row.get(key)) for key in keys})
        return stream.getvalue().encode()

    header = encode(None)

    def flush() -> None:
        name = f"executions/{identity}-{len(shards):03d}.csv"
        data = header + b"".join(lines)
        (output / "executions").mkdir(exist_ok=True)
        with (output / name).open("xb") as handle:
            handle.write(data)
        shards.append({"submission": submission, "path": name, "sha256": _digest(data), "bytes": len(data), "rows": count})

    for row in rows:
        line = encode(row)
        if len(line) + len(header) >= 8_000_000:
            raise ValueError("execution row exceeds shard publication limit")
        if lines and size + len(line) + len(header) >= 8_000_000:
            flush()
            lines, size, count = [], 0, 0
        lines.append(line)
        size += len(line)
        count += 1
    if lines or not rows:
        flush()
    return shards


def run_analysis(
    data_root: Path, config_path: Path, task_spec_path: Path, output_dir: Path,
    *, provenance: dict, progress: bool = True,
) -> dict:
    """Write deterministic accounting from a pinned cache with clean provenance.

    Args:
        data_root: Offline official-release cache and acquisition receipts.
        config_path: Committed frozen analysis settings.
        task_spec_path: Pinned official task manifest extraction.
        output_dir: New directory; existing evidence is never overwritten.
        provenance: Result of ``inventory.clean_provenance`` at invocation.
        progress: Whether to display progress for long source loops.

    Returns:
        Safe summary counts, without raw configuration or exception text.
    """
    if provenance.get("dirty") is not False or not provenance.get("git_commit"):
        raise ValueError("clean committed provenance is required")
    if output_dir.exists():
        raise FileExistsError("refusing to replace prior analysis evidence")
    config_bytes, task_spec_bytes = config_path.read_bytes(), task_spec_path.read_bytes()
    config, task_spec = json.loads(config_bytes), json.loads(task_spec_bytes)
    if config["dataset"] != inventory.DATASET or config["revision"] != inventory.REVISION or config["reward_channel"] != "reward":
        raise ValueError("configuration differs from frozen release/channel")
    spec = task_spec.get("spec", task_spec)
    tasks = spec.get("tasks", [])
    official = {entry["name"]: entry for entry in tasks}
    if (spec.get("name") != "terminal-bench" or spec.get("version") != "2.0"
            or len(official) != config["task_count"] or len(tasks) != len(official)
            or any(entry.get("git_url") != config["official_task_git_url"] or entry.get("git_commit_id") != config["official_task_revision"] for entry in tasks)):
        raise ValueError("official task manifest does not match frozen definitions")
    tolerance = Decimal(config["native_absolute_tolerance"])
    cache = VerifiedCache(data_root)
    metadata = cache.read("dataset-metadata.json")
    if metadata.get("id") != inventory.DATASET or metadata.get("sha") != inventory.REVISION:
        raise ValueError("official dataset metadata revision differs")
    manifests = []
    request_lists = {}
    for name in ("submission-requests.json", "job-tree-requests.json", "config-requests.json", "discovery-requests.json", "census-completed.json"):
        if name == "discovery-requests.json" and not (data_root / name).exists():
            request_lists[name] = []
            continue
        rows, digest = _request_rows(data_root / name)
        manifests.append({"local_path": name, "sha256": digest})
        for row in rows:
            _validate_request(cache, row)
        request_lists[name] = rows
    top = _tree(cache, "submission-tree.json", inventory.SUBMISSION_ROOT)
    submission_paths = sorted(entry["path"] for entry in top if entry["type"] == "directory")
    submission_requests = {row["source_path"]: row for row in request_lists["submission-requests.json"]}
    if set(submission_requests) != set(submission_paths):
        raise ValueError("submission request coverage differs from pinned inventory")
    jobs: dict[str, dict] = {}
    for submission_path in submission_paths:
        entries = _tree(cache, submission_requests[submission_path]["path"], submission_path)
        for entry in entries:
            if entry["type"] == "directory":
                jobs[entry["path"]] = {"submission": PurePosixPath(submission_path).name}
    job_trees = {row["source_path"]: row for row in request_lists["job-tree-requests.json"] if row["path"].startswith("job-trees/")}
    if set(job_trees) != set(jobs):
        raise ValueError("job request coverage differs from pinned inventory")
    for path, job in jobs.items():
        entries = _tree(cache, job_trees[path]["path"], path)
        job["directories"] = sorted(PurePosixPath(entry["path"]).name for entry in entries if entry["type"] == "directory")
    config_requests: dict[str, list[dict]] = defaultdict(list)
    for row in request_lists["config-requests.json"] + request_lists["discovery-requests.json"]:
        if row["source_path"].endswith("/config.json"):
            config_requests[row["source_path"].removesuffix("/config.json")].append(row)
    for path, job in jobs.items():
        successful = [row for row in config_requests.get(path, []) if cache.receipts[row["path"]]["status"] == "success"]
        if successful:
            selected = max(successful, key=lambda row: (cache.receipts[row["path"]].get("retrieved_utc", ""), row["path"]))
            raw_config = cache.read(selected["path"])
            try:
                job["population_config"] = inventory._public_config(raw_config)
                job["config_status"] = "success"
            except (ValueError, TypeError, AttributeError):
                job["population_config"], job["config_status"] = None, "unsupported_schema"
            job["config_source_sha256"] = cache.receipts[selected["path"]]["sha256"]
        else:
            job["population_config"], job["config_status"] = None, "unavailable"
    requests = request_lists["census-completed.json"]
    expected = {path + "/result.json" for path in jobs}
    expected.update(path + "/" + name + "/result.json" for path, job in jobs.items() for name in job["directories"])
    if len(requests) != len({row["source_path"] for row in requests}) or {row["source_path"] for row in requests} != expected:
        raise ValueError("completed acquisition does not cover exact listed final-file requests")
    by_submission: dict[str, list[dict]] = defaultdict(list)
    by_job: dict[str, list[dict]] = defaultdict(list)
    failures: dict[str, list[dict]] = defaultdict(list)
    job_raws = {}
    request_manifest_rows = []
    for request in tqdm(sorted(requests, key=lambda row: row["source_path"]), disable=not progress, desc="Verify and normalize final files", unit="file"):
        _validate_result_request(request, jobs)
        job_path = request["job"]
        receipt = cache.receipts[request["path"]]
        record = {key: request.get(key) for key in ("path", "source_path", "kind", "job", "submission", "url", "prior_failed_path")}
        record.update({"status": receipt["status"], "source_sha256": receipt.get("sha256")})
        request_manifest_rows.append(record)
        if receipt["status"] != "success":
            failure = {"source_path": request["source_path"], "source_sha256": None, "job_path": job_path, "submission": request["submission"], "record_kind": "absent_raw_file", "source_status": "failed", "reward_status": "unavailable_raw_file", "trial_uuid": None, "trial_name": None, "directory_name": PurePosixPath(request["source_path"]).parent.name if request["kind"] == "trial" else None}
            failures[job_path].append(failure)
            if request["kind"] == "trial":
                by_submission[request["submission"]].append(failure)
            continue
        try:
            raw = cache.read(request["path"], memo=request["kind"] == "job")
            if not isinstance(raw, dict):
                raise ValueError("record must be an object")
            if request["kind"] == "job":
                job_raws[job_path] = raw
                continue
            row = normalize.normalize_trial(raw, request["source_path"], receipt["sha256"], job_path)
            system_hash = _system_hash(raw)
            row.update({"submission": request["submission"], "record_kind": "named_final_record", "source_status": "success", "system_config_hash": system_hash})
            row["semantic_hash"] = _semantic_hash(raw, row, system_hash)
            by_job[job_path].append(row)
            by_submission[request["submission"]].append(row)
        except (ValueError, TypeError, KeyError, ArithmeticError):
            failure = {"source_path": request["source_path"], "source_sha256": receipt.get("sha256"), "job_path": job_path, "submission": request["submission"], "record_kind": "unparseable_raw_file", "source_status": "unsupported_schema", "reward_status": "unsupported_raw_file", "trial_uuid": None, "trial_name": None, "directory_name": PurePosixPath(request["source_path"]).parent.name if request["kind"] == "trial" else None}
            failures[job_path].append(failure)
            if request["kind"] == "trial":
                by_submission[request["submission"]].append(failure)
    job_checks, reconciliation, native_rows = [], [], []
    for path, job in sorted(jobs.items()):
        raw = job_raws.get(path)
        check = normalize.reconcile_job(raw or {}, by_job[path], job["directories"], tolerance)
        if raw is None:
            check["native_status"] = "unavailable"
        check.update({"job_path": path, "submission": job["submission"], "raw_job_source_available": raw is not None, "failed_or_malformed_requested_files": failures[path], "population_config": job["population_config"], "config_status": job["config_status"], "config_source_sha256": job.get("config_source_sha256"), "allocation_evidence": "declared_cardinality_only_no_original_roster", "exact_planned_roster_established": False, "declared_total_equals_listed_directories": check["declared_n_total_trials"] == check["directory_count"] if check["declared_n_total_trials"] is not None else None, "declared_total_equals_named_raw_records": check["declared_n_total_trials"] == check["row_count"] if check["declared_n_total_trials"] is not None else None})
        job_checks.append(check)
        reconciliation.append({key: value for key, value in check.items() if key not in {"evals", "failed_or_malformed_requested_files", "population_config"}})
        for evaluation in check["evals"]:
            native_rows.append({"job_path": path, "submission": job["submission"], **evaluation})
        if not check["evals"]:
            native_rows.append({"job_path": path, "submission": job["submission"], "native_status": check["native_status"], "eval_key": None})
    cross_uuid_rows: dict[str, list[dict]] = defaultdict(list)
    for rows in by_submission.values():
        for row in rows:
            if row.get("trial_uuid"):
                cross_uuid_rows[row["trial_uuid"]].append(row)
    cross_uuid_ledger, conflicting_global_uuids = [], set()
    for trial_uuid, rows in sorted(cross_uuid_rows.items()):
        submissions = sorted({row["submission"] for row in rows})
        if len(submissions) > 1:
            conflict = len({row["semantic_hash"] for row in rows}) > 1
            if conflict:
                conflicting_global_uuids.add(trial_uuid)
            cross_uuid_ledger.append({"trial_uuid": trial_uuid, "submissions": submissions, "source_aliases": sorted(row["source_path"] for row in rows), "status": "conflicting_cross_submission_semantics" if conflict else "shared_explicit_execution_alias"})
    eligibility, policy_rows, dedup_ledger, populations = [], [], [], {}
    checks_by_submission: dict[str, list[dict]] = defaultdict(list)
    for check in job_checks:
        checks_by_submission[check["submission"]].append(check)
    for submission_path in submission_paths:
        submission = PurePosixPath(submission_path).name
        source_rows = by_submission[submission]
        records = [row for row in source_rows if row["record_kind"] == "named_final_record"]
        retained, ledger, reasons = deduplicate_submission(records)
        if any(row["trial_uuid"] in conflicting_global_uuids for row in retained):
            reasons.append("cross_submission_uuid_semantic_conflict")
            retained = [row for row in retained if row["trial_uuid"] not in conflicting_global_uuids]
        dedup_ledger.extend({"submission": submission, **row} for row in ledger)
        checks = checks_by_submission[submission]
        if any(row["record_kind"] != "named_final_record" for row in source_rows) or any(check["failed_or_malformed_requested_files"] for check in checks):
            reasons.append("missing_or_malformed_requested_source")
        if not checks or any(check["native_status"] != "match" for check in checks):
            reasons.append("native_job_population_unreconciled")
        if any(check["config_status"] != "success" for check in checks):
            reasons.append("missing_or_unsupported_job_config")
        if any(dataset.get("name") == "terminal-bench" and dataset.get("version") not in {None, "2.0"} for check in checks for dataset in (check.get("population_config") or {}).get("datasets", [])):
            reasons.append("config_declares_other_benchmark_version")
        policy, task_reasons, signature = submission_policies(retained, official, config)
        reasons = sorted(set(reasons + task_reasons))
        system_hashes = sorted({row["system_config_hash"] for row in records})
        eligible = not reasons and policy is not None
        eligibility.append({"submission": submission, "source_path": submission_path, "eligible_primary": eligible, "reasons": reasons, "job_count": len(checks), "requested_trial_files": len(source_rows), "named_final_records": len(records), "retained_unique_uuid_records": len(retained), "task_count": len({row.get("task_name") for row in retained}), "task_definition_signature": signature, "declared_system_config_hash_count": len(system_hashes), "declared_system_config_hashes": system_hashes, "system_interpretation": "released_submission_mixture_or_single_declared_config; hashes show configuration-byte variation, not proven behavioral heterogeneity", "native_job_status_counts": dict(Counter(check["native_status"] for check in checks)), "exact_planned_roster_established": False, "retry_lineage_status": "unavailable"})
        if not eligible:
            continue
        populations[submission] = {"policy": policy, "signature": signature, "uuids": {row["trial_uuid"] for row in retained}}
        observed = [Decimal(row["reward_decimal"]) for row in retained if row["score_present"]]
        for policy_name in ("equal_task", "pooled"):
            values = policy[policy_name]
            policy_rows.append({"submission": submission, "policy": policy_name, "population": "deduplicated_named_final_records", "record_count": policy["record_count"], "task_count": policy["task_count"], "unknown_record_count": policy["unknown_record_count"], "native_operational_zero_mean": values["native_mean"], "score_completion_lower": values["bounds"][0], "score_completion_upper": values["bounds"][1], "unknown_weight": values["missing_weight"], "score_completion_interpretation": "free_[0,1]_score_completion_envelope_for_named_unscored_final_records", "pooled_observed_only_mean": sum((Fraction(value) for value in observed), Fraction()) / len(observed) if observed else None, "observed_only_population_caveat": "conditions_on_scored_records_and_changes_weights", "pooled_minus_equal_task_operational_mean": policy["pooled"]["native_mean"] - policy["equal_task"]["native_mean"], "task_repetition_counts": policy["task_counts"], "task_definition_signature": signature})
    compatibility, pairs = compare_populations(populations)
    cache.finish()
    module_paths = [Path(__file__), Path(inventory.__file__), Path(normalize.__file__), Path(bounds.__file__)]
    provenance = {**provenance, "analysis_config": config, "config_sha256": _digest(config_bytes), "task_spec_sha256": _digest(task_spec_bytes), "module_sha256": {path.name: _digest(path.read_bytes()) for path in module_paths}, "offline": True}
    summary = {"dataset": inventory.DATASET, "revision": inventory.REVISION, "submission_count": len(submission_paths), "job_count": len(jobs), "requested_result_sources": len(requests), "successful_source_receipts": sum(row["status"] == "success" for row in cache.receipts.values()), "failed_source_receipts": sum(row["status"] == "failed" for row in cache.receipts.values()), "named_final_record_count": sum(len(rows) for rows in by_job.values()), "reward_status_counts": dict(Counter(row["reward_status"] for rows in by_job.values() for row in rows)), "job_native_status_counts": dict(Counter(row["native_status"] for row in job_checks)), "eligible_primary_submissions": sum(row["eligible_primary"] for row in eligibility), "compatibility_signature_counts": dict(Counter(value["signature"] for value in populations.values())), "eligible_pair_count": len(compatibility), "pair_exclusion_reason_counts": dict(Counter(reason for row in compatibility for reason in row["exclusion_reasons"])), "cross_submission_shared_uuid_count": len(cross_uuid_ledger), "cross_submission_conflicting_uuid_count": len(conflicting_global_uuids), "compatible_unordered_primary_pairs": sum(row["policy"] == "equal_task" for row in pairs), "pair_classification_counts_equal_task": dict(Counter(row["classification"] for row in pairs if row["policy"] == "equal_task")), "duplicate_export_groups": sum(row["status"] == "identical_export_aliases" for row in dedup_ledger), "quarantined_uuid_conflict_groups": sum(row["status"] == "quarantined_conflict" for row in dedup_ledger), "official_website_reproduction": "unavailable_without_pinned_importer_and_adjudications", "exact_original_roster_established": False, "retry_policy": bounds.retry_diagnostic(), "scope": "published_final_record_native_metrics_and_explicit_policy_sensitivities"}
    output_dir.mkdir(parents=True)
    executions_index = []
    for submission_path in submission_paths:
        submission = PurePosixPath(submission_path).name
        executions_index.extend(_execution_shards(output_dir, submission, by_submission[submission]))
    _csv(output_dir / "executions.csv", executions_index)
    _csv(output_dir / "reconciliation.csv", reconciliation)
    _csv(output_dir / "native_score_reproduction.csv", native_rows)
    _csv(output_dir / "eligibility.csv", eligibility)
    _csv(output_dir / "policy_comparisons.csv", policy_rows)
    _csv(output_dir / "pairwise_comparisons.csv", pairs)
    _csv(output_dir / "compatibility_matrix.csv", compatibility)
    _csv(output_dir / "cross_submission_uuid_reconciliation.csv", cross_uuid_ledger)
    _csv(output_dir / "uuid_reconciliation.csv", dedup_ledger)
    check_shards = _json_shards(output_dir, "jobchecks", job_checks)
    _json_file(output_dir / "jobchecks.json", {"shards": check_shards})
    source_shards = _json_shards(output_dir, "source_manifest", list(cache.receipts.values()))
    request_shards = _json_shards(output_dir, "source_requests", request_manifest_rows)
    _json_file(output_dir / "source_manifest.json", {"dataset": inventory.DATASET, "revision": inventory.REVISION, "license": "apache-2.0", "sources": source_shards, "result_requests": request_shards, "request_manifests": manifests, "task_spec_sha256": _digest(task_spec_bytes)})
    _json_file(output_dir / "summary.json", summary)
    _json_file(output_dir / "provenance.json", provenance)
    oversized = [path.name for path in output_dir.rglob("*") if path.is_file() and path.stat().st_size >= 10_000_000]
    if oversized:
        raise ValueError("publication output exceeds repository file-size ceiling")
    return summary


def main() -> None:
    """Generate canonical evidence only from clean committed source."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--task-spec", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    provenance = inventory.clean_provenance()
    summary = run_analysis(args.data_root, args.config, args.task_spec, args.output_dir, provenance=provenance)
    print(json.dumps(summary, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
