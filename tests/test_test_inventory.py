"""`refresh_test_inventory`: a count claim taken from a clean commit, or none.

DECISIONS.md 186 moved the README's test count onto a generated artifact. The
two properties that make the number worth printing are that it refuses a dirty
tree and that it records the commit it counted. Both are checked here on a
throwaway repository, because running it on this one would rewrite the README.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from controlplane.report.test_inventory import refresh_test_inventory


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "tests").mkdir(parents=True)
    (root / "results").mkdir()
    (root / "tests" / "test_one.py").write_text(
        "def test_a():\n    pass\n\ndef test_b():\n    pass\n", encoding="utf-8"
    )
    (root / "README.md").write_bytes(b"badge Tests-100_passing\r\nsuite: 100 tests green\r\n")
    (root / "Makefile").write_bytes(b"# make test   100 tests green\n")
    (root / "results" / ".keep").write_text("", encoding="utf-8")
    # Collection writes bytecode; the real repository ignores it, and without
    # the same rule the tree reads as changed during collection.
    (root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "fixture")
    return root


def test_a_dirty_tree_is_refused_and_nothing_is_rewritten(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "README.md").write_bytes(b"badge Tests-100_passing\r\nsuite: 100 tests green\r\nedit\r\n")
    before = (root / "Makefile").read_bytes()
    with pytest.raises(ValueError, match="clean working tree"):
        refresh_test_inventory(root)
    assert (root / "Makefile").read_bytes() == before
    assert not (root / "results" / "test_inventory.json").exists()


def test_a_clean_tree_records_its_commit_and_keeps_line_endings(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    head = _git(root, "rev-parse", "HEAD")
    result = refresh_test_inventory(root)

    assert result["n_collected"] == 2
    assert result["git_commit"] == head
    assert result["execution_status"] == "not_measured_by_collection"
    artifact = json.loads((root / "results" / "test_inventory.json").read_text(encoding="utf-8"))
    assert artifact["git_commit"] == head

    readme = (root / "README.md").read_bytes()
    assert b"Tests-2_collected" in readme and b"2 tests collected" in readme
    assert b"\r\n" in readme and b"\n" not in readme.replace(b"\r\n", b""), (
        "the refresh rewrote README.md's line endings"
    )
