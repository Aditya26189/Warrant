"""Regenerate ``requirements.lock.txt`` -- the closure, not a laptop.

Until 2026-09-10 this script did not exist and the lock was ``pip freeze`` run
on a developer machine. That is not a lock file. It carried 215 packages the
project never imports -- celery, flask, firebase-admin, langchain, mlflow,
crashlens -- and two that made the documented install command fail outright:

* ``litellm==1.40.0`` was **removed** from PyPI, not merely yanked. Every
  release between 1.14.4 and 1.53.1 is gone, so the pin could not resolve on
  any platform, and ``pip install -r requirements.lock.txt`` -- the command in
  ``README.md``, ``docs/SETUP.md``, ``docs/ONBOARDING.md``,
  ``docs/EXTERNAL.md`` and ``docs/TROUBLESHOOTING.md`` -- failed for everyone.
* ``pywin32==311`` ships Windows wheels and no sdist, so even with litellm
  fixed the file could not install on Linux, which is where CI runs.

A freeze also records the wrong thing in the other direction: taken on Windows,
it contains none of the sixteen CUDA packages ``torch`` requires on Linux, so
it never pinned the environment CI actually builds.

The fix is to resolve rather than to freeze::

    python scripts/build_lock.py

**Regenerating does not move a version.** The existing lock is fed back to the
resolver as a constraint, and this script exits non-zero if any pin changed.
``--upgrade`` drops the constraint and prints the diff, which is the only way a
transitive bump can reach ``results/`` -- and it arrives as a reviewable diff
rather than as whatever a laptop happened to have installed that day.

Requires `uv <https://docs.astral.sh/uv/>`_ for its universal resolver: one
file, valid on Linux, macOS and Windows, with the platform differences carried
as environment markers instead of as three files that drift apart.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
LOCK = PROJECT_ROOT / "requirements.lock.txt"

#: The interpreter every artifact in ``results/`` was produced on, and the one
#: the full-suite CI job runs. Resolving for it rather than for the wider
#: ``requires-python`` range in ``pyproject.toml`` keeps the lock a record of
#: one build; ``tests/test_packaging.py`` asserts CI has not drifted off it.
PYTHON_TARGET = "3.12"

#: Not a pip package. Presidio constructs its analyzer against this model at
#: runtime, so an install without it fails at ``AnalyzerEngine()`` rather than
#: at import -- a stage error that reads as a bug in our code. The URL is
#: hash-pinned, which ``python -m spacy download`` is not.
SPACY_MODEL = (
    "en_core_web_lg @ https://github.com/explosion/spacy-models/releases/"
    "download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl"
    "#sha256=293e9547a655b25499198ab15a525b05b9407a75f10255e405e8c3854329ab63"
)

PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;]+)")


def _canonical(name: str) -> str:
    """PEP 503 normalisation, so ``PyYAML`` and ``pyyaml`` are one package."""
    return re.sub(r"[-_.]+", "-", name).lower()


def read_pins(text: str) -> dict[str, str]:
    """Map package -> version for every ``name==version`` line in *text*."""
    pins: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = PIN.match(stripped)
        if match:
            pins[_canonical(match.group(1))] = match.group(2)
    return pins


def uv_command() -> list[str]:
    """Find uv, preferring the one in this interpreter's environment.

    Returns:
        The argv prefix that invokes uv.

    Raises:
        SystemExit: with the install command, rather than a traceback from
            ``subprocess`` that says only that a file was not found.
    """
    probe = subprocess.run(
        [sys.executable, "-m", "uv", "--version"], capture_output=True, text=True
    )
    if probe.returncode == 0:
        return [sys.executable, "-m", "uv"]
    found = shutil.which("uv")
    if found:
        return [found]
    raise SystemExit(
        "scripts/build_lock.py needs uv for its universal resolver.\n"
        "    pip install uv\n"
        "The lock file itself is plain pip -- uv is a build-time tool only, "
        "and nothing in controlplane/ imports it."
    )


def _tidy_via_blocks(lines: list[str]) -> str:
    """Collapse a ``# via`` block left with one entry back onto one line.

    Dropping the constraint annotation can leave::

        numpy==2.2.6
            # via
            #   scipy

    where uv would have written ``# via scipy``. Cosmetic, but the file is read
    by people and an inconsistent shape invites a hand-edit.

    Args:
        lines: The resolver's output, constraint annotations already removed.

    Returns:
        The same content as one string, single-entry blocks collapsed.
    """
    out: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip() == "# via":
            block = []
            probe = index + 1
            while probe < len(lines) and re.match(r"^\s*#\s{3}\S", lines[probe]):
                block.append(lines[probe].strip()[1:].strip())
                probe += 1
            if len(block) == 1:
                indent = line[: len(line) - len(line.lstrip())]
                out.append(f"{indent}# via {block[0]}")
                index = probe
                continue
        out.append(line)
        index += 1
    return "\n".join(out)


def compile_closure(constraints: Path | None) -> str:
    """Resolve ``requirements.txt`` into a single cross-platform pin set.

    Args:
        constraints: An existing lock fed back to the resolver, so that a
            regeneration reproduces the same versions. ``None`` lets every pin
            move to whatever is newest and compatible.

    Returns:
        The resolver's output, with its own constraint-file annotations
        stripped -- those name an absolute temporary path and would make the
        lock differ between two machines that resolved the same closure.

    Raises:
        SystemExit: if the resolver fails, carrying its stderr.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "compiled.txt"
        command = [
            *uv_command(), "pip", "compile", str(REQUIREMENTS),
            "--universal", "--python-version", PYTHON_TARGET,
            "--no-header", "-o", str(out),
        ]
        if constraints is not None:
            command += ["-c", str(constraints)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit(
                f"uv pip compile failed ({result.returncode}):\n{result.stderr}"
            )
        compiled = out.read_text(encoding="utf-8")

    kept = [
        line for line in compiled.splitlines()
        if not re.match(r"^\s*#\s+-c\s", line)  # the constraint file's own path
    ]
    return _tidy_via_blocks(kept)


def header(resolved_at: str) -> str:
    """The provenance block: what the file is, and what it is not.

    Args:
        resolved_at: UTC timestamp of this resolution.

    Returns:
        The comment block that opens the lock file.
    """
    return f"""\
# requirements.lock.txt -- the exact environment `make verify` and CI install.
#
# Generated, never hand-edited:
#
#     python scripts/build_lock.py
#
# This is the full transitive closure of requirements.txt, resolved for every
# platform at once -- Linux, macOS and Windows differences are carried as
# environment markers -- against Python {PYTHON_TARGET}, the interpreter that produced
# every artifact in results/.
#
# It is not a `pip freeze`. It was one until 2026-09-10, and that file listed
# 215 packages this project never imports next to two that made the documented
# install fail: litellm==1.40.0, deleted from PyPI, and pywin32==311, which has
# no Linux wheel. scripts/build_lock.py carries the full account.
#
# Regenerating holds every version where it is: the previous lock is fed back
# to the resolver as a constraint and build_lock.py exits non-zero if a pin
# moved. `--upgrade` is the only way to move one, and it prints the diff.
#
# Python:   {PYTHON_TARGET}
# Seed:     1729 (config.yaml; every script sets random, numpy and torch)
# Resolved: {resolved_at}
#
# The spaCy model at the end is a hash-pinned direct URL rather than a pin,
# because it is not on PyPI. `python -m spacy download en_core_web_lg` fetches
# the same wheel without the hash check.
"""


def render(resolved_at: str, constraints: Path | None) -> str:
    """Assemble the whole file: header, closure, spaCy model."""
    body = compile_closure(constraints)
    return f"{header(resolved_at)}\n{body.rstrip()}\n\n{SPACY_MODEL}\n"


def report(before: dict[str, str], after: dict[str, str]) -> int:
    """Print what changed between two pin sets.

    Args:
        before: Pins from the lock as it stands.
        after: Pins from the resolution just performed.

    Returns:
        How many versions moved. Zero is the expected result of a plain
        regeneration; anything else needs a human to read the diff.
    """
    moved = {
        name: (before[name], after[name])
        for name in after
        if name in before and before[name] != after[name]
    }
    added = sorted(set(after) - set(before))
    dropped = sorted(set(before) - set(after))
    print(f"packages: {len(before)} -> {len(after)}")
    if added:
        print(f"\nadded ({len(added)}):")
        for name in added:
            print(f"  + {name}=={after[name]}")
    if dropped:
        print(f"\ndropped ({len(dropped)}):")
        for name in dropped:
            print(f"  - {name}=={before[name]}")
    if moved:
        print(f"\nVERSION MOVED ({len(moved)}):")
        for name, (old, new) in sorted(moved.items()):
            print(f"  ~ {name}: {old} -> {new}")
    else:
        print("\nno version moved")
    return len(moved)


def main(argv: list[str] | None = None) -> int:
    """Resolve, diff, and write. See the module docstring for the why."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--upgrade", action="store_true",
        help="let pins move to the newest compatible release, and print the diff",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="resolve and diff, but do not write the file",
    )
    args = parser.parse_args(argv)

    previous = LOCK.read_text(encoding="utf-8") if LOCK.exists() else ""
    before = read_pins(previous)

    with tempfile.TemporaryDirectory() as tmp:
        constraints_file = None
        if not args.upgrade and previous:
            constraints_file = Path(tmp) / "previous.txt"
            # A direct URL is a pin the resolver cannot satisfy from an index,
            # and it constrains nothing in the closure.
            constraints_file.write_text(
                "\n".join(
                    line for line in previous.splitlines() if " @ " not in line
                ),
                encoding="utf-8",
            )
        resolved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rendered = render(resolved_at, constraints_file)

    after = read_pins(rendered)
    moved = report(before, after)

    if args.check:
        print("\n--check: nothing written")
        return 1 if moved and not args.upgrade else 0

    LOCK.write_text(rendered, encoding="utf-8")
    print(f"\nwrote {LOCK.relative_to(PROJECT_ROOT)}")

    if moved and not args.upgrade:
        print(
            "\nA pin moved despite the constraint, which means the previous "
            "version is no longer resolvable. Read the diff above before "
            "committing: every number in results/ was measured on the old one."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
