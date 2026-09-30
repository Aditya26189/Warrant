"""Exercise inventory generation without recursively collecting this repository."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.smoke


def _environment() -> dict[str, str]:
    """Keep parent pytest and Git settings out of the isolated fixture."""
    excluded = {"PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"}
    return {
        **{key: value for key, value in os.environ.items()
           if key not in excluded and not key.startswith("GIT_")},
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONIOENCODING": "utf-8",
    }


def _git(root: Path, *arguments: str) -> str:
    """Only the temporary repository gets commits or configuration changes."""
    result = subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, text=True,
        check=True, timeout=30, env=_environment(),
    )
    return result.stdout.strip()


@pytest.fixture
def inventory_repo(tmp_path: Path) -> Path:
    """Copy production entrypoint and logic, isolating unrelated report imports."""
    for relative in ("scripts/refresh_test_inventory.py",
                     "controlplane/report/test_inventory.py"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, target)
    for relative in ("controlplane/__init__.py", "controlplane/report/__init__.py"):
        (tmp_path / relative).write_bytes(b'"""Isolated inventory smoke package."""\n')
    (tmp_path / "tests").mkdir()
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / ".gitkeep").write_bytes(b"")
    (tmp_path / ".gitignore").write_bytes(b"__pycache__/\n.pytest_cache/\n")
    (tmp_path / "README.md").write_bytes(
        b"Fixture: 999 tests passing\r\n"
        b"![Tests](https://img.shields.io/badge/Tests-999_passing-green)\r\n"
    )
    (tmp_path / "Makefile").write_bytes(b"# 999 tests green\nall:\n\t@echo fixture\n")
    (tmp_path / "tests" / "test_fixture.py").write_bytes(
        b"import pytest\n\n"
        b"@pytest.mark.parametrize('case', [1, 2, 3])\n"
        b"def test_collect_only(case):\n"
        b"    raise AssertionError('inventory must not execute tests')\n"
    )
    _git(tmp_path, "init", "--quiet")
    _git(tmp_path, "config", "core.autocrlf", "false")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "-c", "user.name=Inventory Smoke",
         "-c", "user.email=inventory-smoke@example.invalid",
         "-c", "commit.gpgsign=false", "commit", "--quiet", "--no-verify",
         "-m", "test: create isolated inventory fixture")
    assert _git(tmp_path, "status", "--porcelain") == ""
    return tmp_path


def _run_inventory(root: Path) -> subprocess.CompletedProcess[str]:
    """Run the copied real script; its PROJECT_ROOT resolves to the fixture."""
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "refresh_test_inventory.py")],
        cwd=root, capture_output=True, text=True, timeout=60, env=_environment(),
    )


def test_smoke_inventory_collects_without_executing_tests(inventory_repo: Path) -> None:
    """Successful collection updates count claims and binds their source commit."""
    commit = _git(inventory_repo, "rev-parse", "HEAD")
    result = _run_inventory(inventory_repo)
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads((inventory_repo / "results" / "test_inventory.json").read_bytes())
    assert payload["n_collected"] == 3
    assert payload["git_commit"] == commit
    assert payload["dirty"] is False
    assert payload["execution_status"] == "not_measured_by_collection"
    assert "--collect-only" in payload["command"]
    assert len(payload["collection_sha256"]) == 64
    assert "Recorded 3 collected tests" in result.stdout
    assert "Collection does not claim that execution passed" in result.stdout
    assert (inventory_repo / "README.md").read_bytes() == (
        b"Fixture: 3 tests collected\r\n"
        b"![Tests](https://img.shields.io/badge/Tests-3_collected-green)\r\n"
    )
    assert (inventory_repo / "Makefile").read_bytes() == (
        b"# 3 tests collected\nall:\n\t@echo fixture\n"
    )


def test_smoke_inventory_refuses_dirty_source_without_updating_claims(
    inventory_repo: Path,
) -> None:
    """A dirty checkout cannot produce evidence naming a clean source commit."""
    readme = inventory_repo / "README.md"
    readme.write_bytes(readme.read_bytes() + b"uncommitted change\r\n")
    before = {name: (inventory_repo / name).read_bytes()
              for name in ("README.md", "Makefile")}

    result = _run_inventory(inventory_repo)

    assert result.returncode != 0
    assert "clean working tree" in result.stderr
    assert not (inventory_repo / "results" / "test_inventory.json").exists()
    for name, content in before.items():
        assert (inventory_repo / name).read_bytes() == content
