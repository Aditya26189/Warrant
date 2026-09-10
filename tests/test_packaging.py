"""The packaging surface: what someone installing this actually touches.

Three things a person meets before any measurement — the declared dependencies,
the version string, and how long the command takes to answer. Each had a defect
when this file was written, and none was visible from inside the research
pipeline:

* `controlplane.__version__` said 0.1.0 while `pyproject.toml` said 0.2.0, so
  `warrant --version` would have reported the wrong number as fact;
* importing the CLI cost **2.83 seconds**, of which 1.39s was `scipy.stats`
  pulled in transitively, before a single argument was parsed;
* nothing checked that the customer path stayed free of the deep-learning stack.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: Packages the customer path must never pull in. A person evaluating their own
#: detector should not download a deep-learning stack to do binomial arithmetic.
FORBIDDEN_ON_THE_CUSTOMER_PATH = (
    "torch", "transformers", "datasets", "spacy", "sklearn",
    "matplotlib", "presidio_analyzer",
)

#: `warrant --help` must answer well inside this. Generous against the measured
#: ~180ms so the test does not go red on a loaded CI runner, and far below the
#: 2.83s that prompted it — the point is to catch a regression of that size, not
#: to police tens of milliseconds.
HELP_BUDGET_SECONDS = 1.5


def test_the_version_is_not_declared_twice_with_two_answers() -> None:
    """`pyproject.toml` and the package must agree.

    They did not: 0.2.0 against 0.1.0. Two hand-maintained copies of one number
    is how a released artifact tells a user the wrong version.
    """
    from controlplane import __version__

    pyproject = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert __version__ == pyproject["project"]["version"], (
        f"controlplane.__version__ is {__version__} and pyproject.toml says "
        f"{pyproject['project']['version']}"
    )


def test_the_cli_reports_that_version() -> None:
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), "--version"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300,
    )
    assert result.returncode == 0, result.stderr
    from controlplane import __version__

    assert __version__ in result.stdout


def test_importing_the_cli_does_not_drag_in_the_research_stack() -> None:
    """The claim `requirements-customer.txt` makes, enforced.

    A fresh interpreter, so this measures what a user's first invocation
    actually loads rather than what this test session happens to have imported
    already.
    """
    code = (
        "import sys; from controlplane.cli import main; "
        f"print(sorted({{m.split('.')[0] for m in sys.modules}} & set({list(FORBIDDEN_ON_THE_CUSTOMER_PATH)!r})))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300,
    )
    assert result.returncode == 0, result.stderr
    loaded = result.stdout.strip().splitlines()[-1]
    assert loaded == "[]", (
        f"the CLI imported {loaded} at module scope. Defer it inside the "
        "function that needs it: every user pays this on every invocation, "
        "including `--help`."
    )


def test_help_answers_quickly() -> None:
    """A command that takes seconds to print its usage reads as research code."""
    start = time.time()
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), "--help"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300,
    )
    elapsed = time.time() - start
    assert result.returncode == 0, result.stderr
    assert elapsed < HELP_BUDGET_SECONDS, (
        f"`warrant --help` took {elapsed:.2f}s against a {HELP_BUDGET_SECONDS}s "
        "budget; something heavy is being imported at module scope again"
    )


def test_the_declared_customer_dependencies_are_the_real_ones() -> None:
    """`requirements-customer.txt` and `pyproject.toml` must not disagree."""
    declared = {
        re.split(r"[><=!]", line)[0].strip().lower()
        for line in (PROJECT_ROOT / "requirements-customer.txt")
        .read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    pyproject = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    packaged = {
        re.split(r"[><=!]", d)[0].strip().lower()
        for d in pyproject["project"]["dependencies"]
    }
    assert declared == packaged, (
        f"requirements-customer.txt declares {sorted(declared)} and "
        f"pyproject.toml declares {sorted(packaged)}"
    )


@pytest.mark.parametrize("path", ["ci/customer-path-tests.txt"])
def test_the_ci_test_list_points_at_files_that_exist(path: str) -> None:
    """A CI list naming a deleted file fails late and confusingly."""
    listed = [
        line.strip()
        for line in (PROJECT_ROOT / path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert listed, f"{path} lists no tests, so the CI job would assert nothing"
    missing = [f for f in listed if not (PROJECT_ROOT / f).is_file()]
    assert not missing, f"{path} names files that do not exist: {missing}"
