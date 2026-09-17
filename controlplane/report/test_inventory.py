"""Generate collection-count claims without calling collection a passing run."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def refresh_test_inventory(root: Path) -> dict:
    """Collect on a clean commit, record evidence, then refresh count labels.

    DECISIONS 186. This never scores research data or claims tests executed.
    Preserve file bytes and line endings except for the generated count text.
    """
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    if git("status", "--porcelain"):
        raise ValueError("test inventory must be collected from a clean working tree")
    commit = git("rev-parse", "HEAD")
    command = [sys.executable, "-m", "pytest", "--collect-only", "tests/",
               "-q", "-o", "addopts=--strict-markers"]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=900)
    if result.returncode:
        raise ValueError("test collection failed:\n" + result.stdout[-3000:] + result.stderr[-1000:])
    matches = re.findall(r"(\d+) tests? collected", result.stdout)
    if len(matches) != 1:
        raise ValueError("expected exactly one pytest collection count")
    count = int(matches[0])
    if git("status", "--porcelain") or git("rev-parse", "HEAD") != commit:
        raise ValueError("working tree changed during collection; no claims were updated")
    payload = {"schema_version": 1, "kind": "test_collection_inventory",
               "git_commit": commit, "dirty": False, "n_collected": count,
               "execution_status": "not_measured_by_collection",
               "python": platform.python_version(), "seed": None,
               "command": ["python", *command[1:]],
               "collection_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
               "timestamp": datetime.now(timezone.utc).isoformat()}
    updates = {}
    for name in ("README.md", "Makefile"):
        path = root / name
        text = path.read_bytes().decode("utf-8")
        text, replacements = re.subn(r"\d{3,} tests(?: green| passing| collected)?",
                                      f"{count} tests collected", text)
        if not replacements:
            raise ValueError(f"no test-count label found in {name}")
        text = re.sub(r"Tests-\d+_(?:passing|collected)", f"Tests-{count}_collected", text)
        updates[path] = text.encode("utf-8")
    artifact = root / "results" / "test_inventory.json"
    artifact.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode())
    for path, data in updates.items():
        path.write_bytes(data)
    return payload
