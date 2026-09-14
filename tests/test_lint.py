"""The CI lint step, run locally whenever ruff is installed.

Ten lint errors reached `main` in one push because the only place ruff ran was
CI's customer-path job, after the push. This runs the same command the workflow
runs, so a local suite fails first. Skipped rather than failed when ruff is not
installed: the full-suite CI job does not install it, and a missing tool is not
a lint error.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


def _ci_ruff_targets() -> list[str]:
    """The paths CI lints, read from the workflow rather than restated."""
    match = re.search(r"^\s*ruff check (.+)$", WORKFLOW.read_text(encoding="utf-8"), re.M)
    assert match, "ci.yml no longer runs `ruff check`; update this test with it"
    return match.group(1).split()


def test_the_code_passes_the_lint_ci_runs() -> None:
    ruff = shutil.which("ruff")
    command = [ruff] if ruff else [sys.executable, "-m", "ruff"]
    probe = subprocess.run([*command, "--version"], capture_output=True, text=True)
    if probe.returncode != 0:
        pytest.skip("ruff is not installed here; CI's customer-path job runs it")
    result = subprocess.run(
        [*command, "check", *_ci_ruff_targets()],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, "ruff found what CI would:\n" + result.stdout[-4000:]
