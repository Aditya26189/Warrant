"""Inspect a source-bound schema sample; never fit a stopping policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

_COST_KEYS = {"usage", "usage_metadata", "cost", "total_cost", "prompt_tokens",
              "completion_tokens", "input_tokens", "output_tokens", "total_tokens",
              "cached_tokens", "cache_creation_input_tokens", "duration", "elapsed",
              "timestamp", "created_at", "started_at", "finished_at"}


def accounting_paths(value: Any, prefix: str = "") -> list[str]:
    """Locate structured accounting fields without mining arbitrary prose."""
    paths = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = prefix + "/" + key.replace("~", "~0").replace("/", "~1")
            if key.lower() in _COST_KEYS:
                paths.append(path)
            paths.extend(accounting_paths(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(accounting_paths(item, prefix + "/" + str(index)))
    return paths


def row_summary(envelope: dict, label: str) -> dict:
    """Retain IDs/schema evidence, excluding full messages and final patches.

    These are descriptive convenience rows, not model predictions or estimates
    of deployment prevalence. Missing labels remain distinct from zero.
    """
    if envelope.get("truncated_cells"):
        raise ValueError("truncated cells cannot establish the inspected schema")
    row = envelope["row"]
    outcome = row.get("resolved")
    if type(outcome) is not int or outcome not in {-1, 0, 1}:
        raise ValueError("unsupported recorded verifier outcome")
    message_key = "messages" if "messages" in row else "trajectory"
    messages = row[message_key]
    if not isinstance(messages, list) or not messages or any(not isinstance(item, dict) for item in messages):
        raise ValueError("ordered message objects are required")
    metadata = row.get("metadata") or {}
    teacher = metadata.get("teacher_model") or {}
    tools = sum(len(item.get("tool_calls") or []) for item in messages)
    roles = Counter(item.get("role", "unknown") for item in messages)
    content_bytes = sum(len((item.get("content") or "").encode("utf-8")) for item in messages
                        if isinstance(item.get("content"), (str, type(None))))
    reasoning_bytes = sum(len((item.get("reasoning_content") or "").encode("utf-8")) for item in messages
                          if isinstance(item.get("reasoning_content"), (str, type(None))))
    return {
        "sample": label, "row_index": envelope["row_idx"],
        "trajectory_id": row.get("trajectory_id"), "issue_id": row.get("instance_id"),
        "repository": row.get("repo"), "recorded_resolved": outcome,
        "label_available": outcome in {0, 1},
        "teacher_model_record": teacher, "harness_version_recorded": False,
        "exit_status_if_present": row.get("exit_status"),
        "task_source_if_present": row.get("hf_dataset_name"),
        "message_field": message_key, "message_count": len(messages),
        "role_counts": dict(sorted(roles.items())), "recorded_tool_call_count": tools,
        "first_message_roles": [item.get("role") for item in messages[:6]],
        "last_message_role": messages[-1].get("role"),
        "structured_accounting_field_paths": accounting_paths(row),
        "observed_content_utf8_bytes": content_bytes,
        "observed_reasoning_utf8_bytes": reasoning_bytes,
        "nontext_content_message_count": sum(not isinstance(item.get("content"), (str, type(None))) for item in messages),
        "cost_unit_warning": "Message/tool counts and UTF8 bytes are descriptive proxies, not billable usage or measured compute/time.",
        "excluded_from_any_future_prefix_features": [key for key in ("model_patch", "exit_status", "resolved", "gen_tests_correct", "pred_passes_gen_tests") if key in row]
            + (["metadata.reference_patch", "metadata.model_patch"] if metadata else []),
        "schema_fields": sorted(row),
        "reconstructed_tokens": "not computed; tokenizer alone cannot restore per-call context/cache/reasoning usage",
        "population_claim": "one initial convenience record; no prevalence, representativeness, issue overlap or duplicate-rate claim",
    }


def inspect_payload(path: Path, label: str, expected_sha256: str) -> dict:
    """Reject corruption and truncated responses before publishing any summary."""
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise ValueError("source payload hash mismatch")
    payload = json.loads(data)
    if payload.get("partial") is not False or not payload.get("rows"):
        raise ValueError("complete source-bound sample required")
    return {"source_sha256": digest, "rows": [row_summary(row, label) for row in payload["rows"]],
            "features": payload.get("features"), "reported_rows_total": payload.get("num_rows_total"),
            "row_total_warning": "provider configuration count, not an unfiltered deployment population"}


def main() -> None:
    """Inspect one accepted response using its retained transport receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import recon

    provenance = recon.clean_git_provenance(args.config)
    root = Path(provenance.pop("git_root"))
    subprocess.check_output(["git", "-C", str(root), "ls-files", "--error-unmatch",
                             Path(__file__).resolve().relative_to(root).as_posix()])
    provenance["inspection_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    config, config_hash = recon.load_config(args.config)
    acquisition = json.loads(args.acquisition.read_bytes())
    if acquisition["provenance"]["config_sha256"] != config_hash:
        raise ValueError("acquisition configuration differs from the frozen request list")
    request = next(item for item in config["requests"] if item["label"] == args.label)
    receipts = [item for item in acquisition["requests"] if item["label"] == args.label]
    if len(receipts) != 1 or not receipts[0]["ok"] or not receipts[0]["body_complete"]:
        raise ValueError("one complete accepted response is required")
    receipt = receipts[0]
    if receipt["original_url"] != request["url"]:
        raise ValueError("acquisition source URL differs from the frozen request")
    recon.validate_revision(receipt["revision_observations"], request["expected_revision"])
    payload = (args.acquisition.parent / receipt["body_file"]).resolve()
    if not payload.is_relative_to(args.acquisition.parent.resolve()):
        raise ValueError("payload must stay within its acquisition directory")
    result = inspect_payload(payload, args.label, receipt["body_sha256"])
    result["source_url"] = receipt["original_url"]
    result["source_revision"] = request["expected_revision"]
    result["acquisition_sha256"] = hashlib.sha256(args.acquisition.read_bytes()).hexdigest()
    result["provenance"] = provenance
    with args.output.open("xb") as handle:
        handle.write((json.dumps(result, indent=2, sort_keys=True) + "\n").encode())


if __name__ == "__main__":
    main()
