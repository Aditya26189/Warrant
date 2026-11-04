"""The Phase 2 acceptance test: a stranger, a fresh clone, and the README.

The question this phase is judged on is not whether the code is clean. It is
whether someone who has never seen the project reaches a warrant and a refusal
by following the README and nothing else.

So this test does not run commands a test author typed. **It parses the
quickstart out of `README.md` and runs what it finds**, inside a fresh
`git clone`. If the README's commands stop working — a renamed flag, a moved
example, a path that only resolves in a dev checkout — this fails, which is the
only way a quickstart stays true.

**What it does and does not simulate.** It clones into a temporary directory, so
it proves the *repository* carries everything the quickstart needs and that no
command depends on untracked local state. It runs with the current interpreter
rather than building a virtualenv and installing from PyPI: the suite has to
work offline, and `pip install` is a claim about a package index rather than
about this repo.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
README = PROJECT_ROOT / "README.md"

pytestmark = pytest.mark.smoke


def _quickstart_commands() -> list[str]:
    """Every `python warrant.py ...` line in the README's quickstart block.

    Read from the document rather than duplicated here, so the test cannot pass
    against commands the README no longer contains.
    """
    text = README.read_text(encoding="utf-8")
    start = text.index("## ⚡ Quickstart")
    end = text.index("## 🚫 What this is not", start)
    block = text[start:end]
    commands = re.findall(r"^python warrant\.py .+$", block, flags=re.MULTILINE)
    # The "run your own" line is a template with a placeholder file, not a
    # command a stranger can execute as written.
    return [c for c in commands if "your_scores.csv" not in c]


def test_the_readme_quickstart_offers_both_outcomes() -> None:
    """The quickstart must demonstrate a warrant AND a refusal, in that order.

    D24: a stranger's first two runs should show both. The refusal is the more
    important of the two and the one most likely to be quietly dropped from a
    quickstart for looking like a failure.
    """
    commands = _quickstart_commands()
    assert len(commands) >= 2, (
        f"the README quickstart runs {len(commands)} executable command(s); it "
        "must show both a certification and a refusal"
    )
    assert "certifies.csv" in commands[0]
    assert "refuses.csv" in commands[1]


def test_a_fresh_clone_reaches_a_warrant_and_a_refusal(tmp_path: Path) -> None:
    """The acceptance test. Clone, run the README's commands, check both outcomes."""
    clone = tmp_path / "clone"
    result = subprocess.run(
        ["git", "clone", "--config", "core.longpaths=true", "--depth", "1", "--quiet", PROJECT_ROOT.as_uri(), str(clone)],
        capture_output=True, text=True, timeout=900,
    )
    assert result.returncode == 0, f"clone failed:\n{result.stderr}"

    # Everything the quickstart touches must be in the clone, not just on this
    # machine. A quickstart that depends on a gitignored file is a quickstart
    # that works for exactly one person.
    for needed in ("warrant.py", "config.yaml", "examples/certifies.csv",
                   "examples/refuses.csv", "docs/INPUT.md"):
        assert (clone / needed).is_file(), f"{needed} is missing from a fresh clone"

    outcomes = []
    for command in _quickstart_commands():
        args = command.split()
        assert args[:2] == ["python", "warrant.py"], command
        run = subprocess.run(
            [sys.executable, *args[1:]],
            capture_output=True, text=True, cwd=str(clone), timeout=900,
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        )
        assert run.returncode == 0, (
            f"a README command failed in a fresh clone:\n  {command}\n"
            f"--- stdout ---\n{run.stdout[-2000:]}\n--- stderr ---\n{run.stderr[-2000:]}"
        )
        match = re.search(r"WARRANT: (\w+)", run.stdout)
        assert match, f"no verdict printed by:\n  {command}\n{run.stdout[-1500:]}"
        outcomes.append(match.group(1))

    assert "VALID" in outcomes, "the quickstart never reaches a warrant"
    assert "REFUSED" in outcomes, "the quickstart never shows a refusal"


def test_the_summary_is_printable_on_a_narrow_ascii_terminal(tmp_path: Path) -> None:
    """Output that cannot be encoded is output that does not work.

    The first run of this CLI on Windows died with UnicodeEncodeError before
    printing anything: cp1252 cannot encode a box-drawing character. A stranger
    following the quickstart would have seen a traceback instead of a warrant,
    so the summary is ASCII and this is the check that keeps it that way.
    """
    run = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), "certify",
         "-i", str(PROJECT_ROOT / "examples" / "refuses.csv"),
         "-b", "0.01", "-o", str(tmp_path / "rec.json")],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900,
        env={**__import__("os").environ, "PYTHONIOENCODING": "cp1252"},
    )
    assert run.returncode == 0, run.stderr
    assert "WARRANT: REFUSED" in run.stdout
    run.stdout.encode("ascii")  # raises if anything non-ASCII crept back in


def test_the_no_network_promise_is_stated_where_a_buyer_reads_it() -> None:
    """D28. Someone about to run this on real production labels needs it early."""
    text = README.read_text(encoding="utf-8")
    quickstart = text[text.index("## ⚡ Quickstart"):text.index("## 🚫 What this is not")]
    assert "nothing leaves your machine" in quickstart.lower()
    assert "no network" in quickstart.lower() or "no telemetry" in quickstart.lower()
