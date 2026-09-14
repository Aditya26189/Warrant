"""`DECISIONS.md` is cited 375 times. Every citation resolves, and stays that way.

`docs/TASKS.md` Phase 12's audit asks that *every `DECISIONS.md` entry is still
accurate*. Accuracy is not testable — an entry can be well-formed and wrong. Two
properties either side of it are:

* **the log is well-formed** — contiguous numbering, no duplicate labels;
* **every citation resolves** — and there are 375 of them, in code, tests,
  config, policy bundles, committed artifacts and the notebook. A citation to an
  entry that does not exist is a dead end in the document `CLAUDE.md` calls *the
  document a technical judge actually reads*.

**The heading format changes mid-file and that is a live trap.** Entries 001 to
071 are ``## 001 — Title``: zero-padded, em dash. Entries 072 onward are
``## 072 - Title``: unpadded, hyphen. A parser that knows one form finds 94 of
165 entries and then reports 46 files as carrying broken citations — which is
exactly what the first version of this check did, before it was pointed at the
file instead of at memory. Both forms are accepted here, deliberately, rather
than the file being rewritten: renumbering a log cited 375 times to make a
regex simpler is the tail wagging the dog.
"""

from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DECISIONS = PROJECT_ROOT / "DECISIONS.md"

#: Both heading forms. ``(\d+)`` then an optional letter suffix -- ``152a`` is a
#: deliberate second entry recording what ``152`` pre-registered, not a
#: duplicate -- then an em dash, en dash or hyphen.
_HEADING = re.compile(r"^## (\d+)([a-z]?)\s*(?:--|[-–—])\s", re.M)


def test_append_only_heading_variants_remain_citable() -> None:
    """New ASCII headings must resolve without rewriting committed entries."""
    for separator in ("-", "--", "–", "—"):
        assert _HEADING.findall(f"## 184 {separator} Registered choice") == [("184", "")]

#: A citation: "DECISIONS 147", "DECISIONS.md 147", "DECISIONS.md entry 122".
_CITATION = re.compile(r"DECISIONS(?:\.md)?\s*(?:entry\s*)?(\d{1,3})")

#: Binary or vendored paths where a number match would be noise.
_SKIP_SUFFIX = (".png", ".npz", ".db", ".pdf", ".joblib", ".parquet")


@lru_cache(maxsize=1)
def _entries() -> tuple[tuple[int, str], ...]:
    text = DECISIONS.read_text(encoding="utf-8")
    found = tuple((int(n), s) for n, s in _HEADING.findall(text))
    assert found, "no entry headings parsed out of DECISIONS.md"
    return found


@lru_cache(maxsize=1)
def _tracked_text_files() -> tuple[Path, ...]:
    listed = subprocess.run(
        ["git", "ls-files"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    ).stdout.split()
    paths = []
    for name in listed:
        # round1/ is the Round 1 submission, moved whole and unmodified
        # (CLAUDE.md). Its citations belong to a different numbering.
        if name.startswith("round1/") or name.endswith(_SKIP_SUFFIX):
            continue
        path = PROJECT_ROOT / name
        if path.is_file():
            paths.append(path)
    assert paths, "git ls-files returned nothing readable"
    return tuple(paths)


def test_the_log_is_contiguous_with_no_duplicates() -> None:
    """A gap means an entry was deleted; a duplicate means two were written."""
    entries = _entries()
    numbers = [n for n, _ in entries]
    labels = [f"{n}{s}" for n, s in entries]

    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    assert not duplicates, (
        f"duplicate entry labels: {duplicates}. Two entries under one number "
        "means one of them is uncitable."
    )

    gaps = sorted(set(range(min(numbers), max(numbers) + 1)) - set(numbers))
    assert not gaps, (
        f"DECISIONS.md is missing entries {gaps}. The log is append-only; a "
        "deleted entry leaves every citation to it dangling."
    )


def test_both_heading_formats_are_still_parsed() -> None:
    """The format changes at 072, and a parser that knows one form finds 94.

    Asserted rather than assumed because the first version of this file knew
    only the later form, reported 46 files as carrying broken citations, and was
    wrong about every one of them.
    """
    entries = _entries()
    numbers = [n for n, _ in entries]
    assert min(numbers) == 1, "entry 001 is not being parsed"
    early = [n for n in numbers if n < 72]
    late = [n for n in numbers if n >= 72]
    assert early, "no entries below 072 parsed -- the em-dash form has been lost"
    assert late, "no entries from 072 parsed -- the hyphen form has been lost"
    assert len(entries) >= 165


def test_every_decisions_citation_in_the_repository_resolves() -> None:
    """375 citations, and a dead one is a dead end in the document judges read.

    ``DECISIONS.md`` is cited from code, tests, ``config.yaml``, the policy
    bundles, committed artifacts and the generated notebook. Nothing checked
    that those numbers pointed anywhere.
    """
    existing = {n for n, _ in _entries()}
    broken: dict[str, set[int]] = {}
    total = 0
    for path in _tracked_text_files():
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in _CITATION.finditer(body):
            number = int(match.group(1))
            total += 1
            if number not in existing:
                relative = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
                broken.setdefault(relative, set()).add(number)

    assert total > 300, (
        f"only {total} citations found; the scan is probably not reading the "
        "files it thinks it is"
    )
    assert not broken, (
        "these cite a DECISIONS.md entry that does not exist:\n  "
        + "\n  ".join(
            f"{name}: {sorted(numbers)}" for name, numbers in sorted(broken.items())
        )
    )


def test_every_open_entry_says_what_would_close_it() -> None:
    """An OPEN item with no exit condition is a decision made by default.

    ``CLAUDE.md``: *when blocked, choose the option that changes least and
    claims least, log it as OPEN — needs human review, and continue.* An OPEN
    entry that never says what would resolve it becomes permanent by silence,
    which is what ``DECISIONS.md`` 154 closed for entry 138 after four phases.
    """
    text = DECISIONS.read_text(encoding="utf-8")
    blocks = re.split(r"^## ", text, flags=re.M)[1:]
    offenders = []
    examined = 0
    for block in blocks:
        head = block.split("\n", 1)[0]
        status_line = next(
            (line for line in block.splitlines() if "**Status:**" in line), ""
        )
        # The entry's OWN status is the FIRST WORD of the status value, not a
        # word appearing anywhere in the line. Two earlier versions of this
        # check matched "OPEN" loosely and were wrong both times: 134 reads
        # "DECIDED -- supersedes the OPEN status of 124", and 155 reads
        # "DECIDED. The one OPEN part was closed by 157". Both are closures.
        # Stripping at a closure word fixed the first and not the second,
        # because there the word "OPEN" comes first. The status is a field;
        # read it as one.
        value = status_line.split("**Status:**", 1)[-1].strip()
        if not value.upper().startswith("OPEN"):
            continue
        examined += 1
        lowered = block.lower()
        if not any(
            phrase in lowered
            for phrase in (
                "what would close it",
                "would close",
                "closes it",
                "needs human review",
                "reopen",
                "what each needs",
                "what it needs",
            )
        ):
            offenders.append(head.strip()[:70])
    assert not offenders, (
        "these entries are OPEN and do not say what would resolve them:\n  "
        + "\n  ".join(offenders)
    )
    # A check that examines nothing passes for the wrong reason. Two entries
    # carry "OPEN -- needs human review" as their status today; if a later
    # narrowing of the status rule stops matching them, this fails rather than
    # going quiet -- which is what the cross-artifact comparison in
    # DECISIONS.md 153 learned to guard against.
    assert examined >= 2, (
        f"only {examined} entries were examined as OPEN. Either the log has "
        "fewer left -- lower this -- or the status rule stopped matching them."
    )
