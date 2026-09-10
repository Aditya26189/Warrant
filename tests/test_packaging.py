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


# --------------------------------------------------------------------------
# The lock file.
#
# On 2026-09-10 CI could not install it. `litellm==1.40.0` had been deleted
# from PyPI -- every release between 1.14.4 and 1.53.1 is gone -- so the pin
# resolved nowhere, and `pywin32==311` has no Linux wheel, so it would have
# failed on the next line anyway. Neither package is imported anywhere in this
# repository. They were there because the file was `pip freeze` run on a
# developer laptop, which also brought celery, flask, firebase-admin,
# langchain and mlflow along: 215 packages the project never touches.
#
# That made the install command in README.md, SETUP.md, ONBOARDING.md,
# EXTERNAL.md and TROUBLESHOOTING.md fail for every reader. The tests below
# are what makes a freeze impossible to reintroduce quietly.
# --------------------------------------------------------------------------

LOCK = PROJECT_ROOT / "requirements.lock.txt"

#: `name==version`, with an optional PEP 508 marker.
LOCK_PIN = re.compile(
    r"^(?P<name>[A-Za-z0-9_.\-]+)==(?P<version>[^\s;]+)\s*(?:;\s*(?P<marker>.+))?$"
)

#: A direct reference, which is how the spaCy model gets in: it is not on PyPI.
LOCK_URL = re.compile(r"^(?P<name>[A-Za-z0-9_.\-]+) @ (?P<url>\S+)$")


def _canonical(name: str) -> str:
    """PEP 503 normalisation, so PyYAML and pyyaml are one package."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _load_build_lock():
    """Import `scripts/build_lock.py`, which is not on the path as a package."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_lock", PROJECT_ROOT / "scripts" / "build_lock.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_lock() -> tuple[dict[str, str], dict[str, set[str]]]:
    """Read the lock into pins and the `# via` graph its annotations describe.

    Returns:
        ``(pins, requested_by)`` where ``pins`` maps package to version and
        ``requested_by`` maps package to the set of things that pulled it in --
        either another package or the literal ``-r requirements.txt``.
    """
    pins: dict[str, str] = {}
    requested_by: dict[str, set[str]] = {}
    current: str | None = None
    in_via_block = False

    for raw in LOCK.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if not line.startswith((" ", "\t", "#")):
            match = LOCK_PIN.match(line) or LOCK_URL.match(line)
            assert match, (
                f"requirements.lock.txt line is neither a pin nor a direct "
                f"reference: {line!r}. The file is generated by "
                f"scripts/build_lock.py; a hand-edit is how it stops being one."
            )
            current = _canonical(match.group("name"))
            pins[current] = match.groupdict().get("version") or match.group("url")
            requested_by.setdefault(current, set())
            in_via_block = False
            continue

        stripped = line.strip()
        if stripped.startswith("# via ") and current:
            requested_by[current].add(stripped[len("# via ") :].strip())
            in_via_block = False
        elif stripped == "# via" and current:
            in_via_block = True
        elif in_via_block and stripped.startswith("#") and current:
            requested_by[current].add(stripped[1:].strip())

    return pins, requested_by


def test_every_lock_line_is_a_pin_or_a_hashed_url() -> None:
    """A freeze has no annotations, and a hand-edit has no shape.

    ``_parse_lock`` asserts the shape of every line; this test also insists the
    one direct reference carries a hash, since a bare URL is an unpinned
    download wearing a pin's clothes.
    """
    pins, _ = _parse_lock()
    assert len(pins) > 50, f"the lock has only {len(pins)} entries; truncated?"
    for url in [v for v in pins.values() if v.startswith("http")]:
        assert "#sha256=" in url, f"direct reference is not hash-pinned: {url}"


def test_the_lock_is_a_closure_and_not_a_laptop() -> None:
    """Every package must be reachable from ``requirements.txt``.

    This is the test the old file would have failed on its first line: a
    ``pip freeze`` carries no ``# via`` annotations at all, so nothing in it is
    reachable from anything. It also catches the slower version of the same
    mistake, where somebody appends one package by hand.
    """
    pins, requested_by = _parse_lock()

    roots = {
        name for name, sources in requested_by.items()
        if any(source.startswith("-r ") for source in sources)
    }
    assert roots, (
        "no package in the lock says it came from requirements.txt. That is "
        "what a pip freeze looks like: a list with no provenance."
    )

    children: dict[str, set[str]] = {}
    for name, sources in requested_by.items():
        for source in sources:
            if not source.startswith("-r "):
                children.setdefault(_canonical(source), set()).add(name)

    reachable = set(roots)
    frontier = list(roots)
    while frontier:
        for child in children.get(frontier.pop(), ()):
            if child not in reachable:
                reachable.add(child)
                frontier.append(child)

    # The spaCy model is a deliberate addition: Presidio needs it at runtime,
    # pip will not pull it, and so it has no requester to point at.
    orphans = {name for name in pins if name not in reachable} - {"en-core-web-lg"}
    assert not orphans, (
        f"{len(orphans)} package(s) in the lock are not reachable from "
        f"requirements.txt: {sorted(orphans)}. Regenerate with "
        f"`python scripts/build_lock.py` rather than adding a line."
    )


def test_the_declared_dependencies_and_the_lock_agree() -> None:
    """A pin in ``requirements.txt`` that the lock contradicts is a silent lie.

    Both files are read by someone deciding which version a finding is a
    statement about, and ``presidio-analyzer==2.2.364`` is exactly such a
    finding.
    """
    pins, _ = _parse_lock()
    declared: dict[str, str] = {}
    for line in (PROJECT_ROOT / "requirements.txt").read_text(
        encoding="utf-8"
    ).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_.\-]+)==([^\s;]+)", stripped)
        if match:
            declared[_canonical(match.group(1))] = match.group(2)

    assert declared, "requirements.txt declares no pinned package"
    disagreements = {
        name: (version, pins.get(name))
        for name, version in declared.items()
        if pins.get(name) != version
    }
    assert not disagreements, (
        "requirements.txt and requirements.lock.txt disagree: "
        + ", ".join(
            f"{name} declared {declared_version}, locked {locked}"
            for name, (declared_version, locked) in sorted(disagreements.items())
        )
    )


def test_ci_runs_the_python_the_lock_was_resolved_for() -> None:
    """The lock is resolved for one interpreter. CI must install it on that one.

    A universal resolution is valid across platforms, not across Python
    versions: markers on ``python_full_version`` would have to be re-resolved.
    If the workflow moves to 3.13 and the lock does not, the install either
    fails or quietly selects different wheels.
    """
    import yaml

    workflow = yaml.safe_load(
        (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
    )
    setup = [
        step
        for step in workflow["jobs"]["full-suite"]["steps"]
        if str(step.get("uses", "")).startswith("actions/setup-python")
    ]
    assert len(setup) == 1, "expected exactly one setup-python step in full-suite"
    ci_python = str(setup[0]["with"]["python-version"])
    target = _load_build_lock().PYTHON_TARGET
    assert ci_python == target, (
        f"the full-suite job installs requirements.lock.txt on Python "
        f"{ci_python}, but the lock was resolved for {target} "
        f"(scripts/build_lock.py, PYTHON_TARGET)"
    )
