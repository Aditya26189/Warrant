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


# --------------------------------------------------------------------------- #
# The preserved parallel log (DECISIONS 202)
#
# Two lines committed different entries as 198, 199 and 200. `DECISIONS.md`
# keeps one set; the other is preserved byte-for-byte in a scoped archive and
# cited as "Codex-parallel N". The review that followed the integration noted
# that nothing checked that archive: a citation of `Codex-parallel 999` was
# ignored, and `DECISIONS 198a` matched the numeric 198 while meaning something
# else. Both are regression gaps rather than evidence of a corrupted archive --
# the bytes were checked by hand at the merge, and these tests are what keeps
# them checked.
# --------------------------------------------------------------------------- #

ARCHIVE = PROJECT_ROOT / "docs" / "decisions" / "CODEX-PARALLEL.md"

#: A row of the archive's table: cited name, heading, commits, digest, bytes.
_ARCHIVE_ROW = re.compile(
    r"^\| Codex-parallel (\d+) \| `([^`]+)` \| ([^|]+) \| `([0-9a-f]{64})` \| (\d+) \|$",
    re.M,
)

#: A citation of the archive, as the repointed code and documents write it.
_PARALLEL_CITATION = re.compile(r"Codex-parallel (?:decision )?(\d{1,3})")

#: "DECISIONS 152a": a numeric citation carrying a letter. The plain citation
#: pattern reads the digits and drops the letter, so the form is only safe when
#: the suffixed entry exists -- 152a does, and 198a does not.
_SUFFIXED_CITATION = re.compile(r"DECISIONS(?:\.md)?\s*(?:entry\s*)?(\d{1,3})([A-Za-z])")

#: The one file allowed an unresolvable suffixed citation: the review that
#: reported this gap quotes `DECISIONS 198a` as its example of a citation that
#: resolves to the wrong entry. Editing a review's evidence to satisfy the test
#: it motivated would be the wrong repair.
_SUFFIX_EXEMPT = ("reports/PROJECT-REVIEW-2026-09-23.md",)


def _archive_text() -> str:
    assert ARCHIVE.is_file(), (
        f"{ARCHIVE.relative_to(PROJECT_ROOT)} is missing. DECISIONS 202 keeps the "
        "parallel entries there; without it every Codex-parallel citation dangles."
    )
    return ARCHIVE.read_text(encoding="utf-8")


def _archive_entries() -> dict[int, bytes]:
    """Each preserved entry's exact bytes, split as the archive says it split them."""
    raw = ARCHIVE.read_bytes().replace(b"\r\n", b"\n")
    marker = b"\n---\n\n## "
    body = raw[raw.index(marker) + len(b"\n---\n\n"):]
    starts = [m.start() for m in re.finditer(rb"^## \d+ - ", body, re.M)]
    bounds = starts + [len(body)]
    entries = {}
    for index, start in enumerate(starts):
        chunk = body[start:bounds[index + 1]]
        number = int(re.match(rb"## (\d+) - ", chunk).group(1))
        entries[number] = chunk
    return entries


def test_every_archived_entry_still_hashes_to_its_recorded_digest() -> None:
    """The archive is preserved bytes, so a digest is the only way to say so.

    An edit inside the block would otherwise read exactly like the original.
    """
    import hashlib

    rows = _ARCHIVE_ROW.findall(_archive_text())
    assert len(rows) >= 3, f"parsed {len(rows)} archive rows; the table shape changed"
    entries = _archive_entries()
    wrong = []
    for number, _heading, _commits, digest, size in rows:
        body = entries.get(int(number))
        if body is None:
            wrong.append(f"{number}: the table lists it and the archive does not hold it")
            continue
        actual = hashlib.sha256(body).hexdigest()
        if actual != digest or len(body) != int(size):
            wrong.append(
                f"{number}: recorded {digest[:12]}/{size} bytes, found "
                f"{actual[:12]}/{len(body)} bytes"
            )
    assert not wrong, (
        "the preserved parallel entries no longer match their recorded digests:\n  "
        + "\n  ".join(wrong)
        + "\n\nThese bytes are a copy of another line's log. Restore them from the "
        "commit the archive names rather than re-hashing the edit."
    )


def test_every_archived_entry_has_a_row_and_a_heading() -> None:
    """A preserved entry nobody can cite is a preserved entry nobody finds."""
    rows = {int(number) for number, *_ in _ARCHIVE_ROW.findall(_archive_text())}
    assert rows == set(_archive_entries()), (
        f"the table lists {sorted(rows)} and the archive holds "
        f"{sorted(_archive_entries())}"
    )


def test_every_codex_parallel_citation_resolves() -> None:
    """The check the plain citation test cannot do: a different numbering."""
    archived = set(_archive_entries())
    broken: dict[str, set[int]] = {}
    for path in _tracked_text_files():
        # The archive holds the entries, and this module names a deliberately
        # absent number in the comment explaining what it checks.
        if path == ARCHIVE or path.name == "test_decisions_integrity.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        missing = {int(n) for n in _PARALLEL_CITATION.findall(text)} - archived
        if missing:
            broken[str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")] = missing
    assert not broken, (
        "these cite a Codex-parallel entry the archive does not hold:\n  "
        + "\n  ".join(f"{name}: {sorted(numbers)}" for name, numbers in sorted(broken.items()))
    )


def test_no_citation_hides_a_letter_after_its_number() -> None:
    """``DECISIONS 198a`` reads as 198 and means something else, or nothing.

    The entry headings do allow a letter -- ``152a`` records what ``152``
    pre-registered -- so the suffix has to be cited in a form the resolver reads,
    not stuck onto a number it will silently truncate.
    """
    real = {f"{number}{suffix}" for number, suffix in _entries() if suffix}
    offenders: dict[str, list[str]] = {}
    for path in _tracked_text_files():
        if path.name == "test_decisions_integrity.py":
            continue
        name = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        if name in _SUFFIX_EXEMPT:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        dangling = [
            f"{number}{suffix}"
            for number, suffix in _SUFFIXED_CITATION.findall(text)
            if f"{number}{suffix}" not in real
        ]
        if dangling:
            offenders[name] = dangling
    assert not offenders, (
        "a numeric citation with a letter attached resolves to the number alone, "
        "and these letters name no entry:\n  "
        + "\n  ".join(f"{name}: {found}" for name, found in sorted(offenders.items()))
        + "\n\nCite the suffixed entry that exists, or the number without the letter."
    )
