"""Phase reports exist, are contiguous, and say the parts that are hard to say.

**Why this file exists.** `reports/PHASE-3.md` was 9,905 bytes at commit
`d696832` and **4 bytes at commit `49156b9`** — the single word `can`. The
commit that destroyed it was adding `reports/STRATEGY-2026-09.md` and its
message never mentions the report; `git show --numstat` records `1 207`, two
hundred and seven lines gone. It survived that way through more than twenty
commits, a full `make verify`, and eleven hundred tests, because **nothing in
this repository looked at `reports/` at all**.

`CLAUDE.md` calls the phase report *"the document a reviewer reads first and
often the only one they read"*. It was the only required deliverable with no
check on it.

The checks here are deliberately structural rather than editorial. A test cannot
tell whether a report is honest. It can tell that the sections where honesty is
expensive — what the work does **not** establish, what is still open — are
present, and that the file has not been emptied.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PROJECT_ROOT / "reports"

#: Below this a report is a stub rather than a report. The four that exist run
#: from 9.9 KB to 14.2 KB, so this is well clear of any of them and well clear
#: of the 4-byte file that prompted the check.
MINIMUM_BYTES = 3000

#: Headings every phase report carries, as a lowercase substring of the line.
#: Taken from what PHASE-0 through PHASE-3 already share, not invented: the
#: point is to stop a section being dropped, not to impose a new template.
REQUIRED_SECTIONS = (
    "does not establish",
    "open items",
    "ledger",
)


def _phase_reports() -> list[Path]:
    # The numbered release series has a continuity/section contract. Named
    # experimental reports keep their historical headings and are checked
    # separately; their introduction must not abort all pytest collection.
    return sorted(
        (p for p in REPORTS.glob("PHASE-*.md")
         if re.fullmatch(r"PHASE-\d+\.md", p.name)),
        key=lambda p: int(re.search(r"PHASE-(\d+)", p.name).group(1)),
    )


def _grader_reports() -> list[Path]:
    return sorted(REPORTS.glob("PHASE-GRADER-*.md"))


def test_every_phase_report_belongs_to_a_checked_series() -> None:
    checked = set(_phase_reports()) | set(_grader_reports())
    assert set(REPORTS.glob("PHASE-*.md")) == checked, (
        "Unrecognized phase-report names must not silently escape checks"
    )


def test_numbered_discovery_accepts_named_grader_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A named experiment must not crash collection or join numeric continuity."""
    for name in ("PHASE-10.md", "PHASE-2.md", "PHASE-0.md", "PHASE-GRADER-POC.md"):
        (tmp_path / name).touch()
    monkeypatch.setattr(f"{__name__}.REPORTS", tmp_path)
    assert [p.name for p in _phase_reports()] == ["PHASE-0.md", "PHASE-2.md", "PHASE-10.md"]
    assert [p.name for p in _grader_reports()] == ["PHASE-GRADER-POC.md"]


def test_the_reports_directory_exists_and_holds_phase_reports() -> None:
    """`CLAUDE.md`: every phase or sprint ends with a report, no exceptions."""
    assert REPORTS.is_dir(), "reports/ is missing"
    reports = _phase_reports()
    assert reports, "no reports/PHASE-N.md files at all"


@pytest.mark.parametrize("report", [*_phase_reports(), *_grader_reports()], ids=lambda p: p.name)
def test_a_phase_report_is_not_a_stub(report: Path) -> None:
    """The check that would have caught `49156b9` on the day it landed."""
    size = report.stat().st_size
    assert size >= MINIMUM_BYTES, (
        f"{report.name} is {size} bytes. reports/PHASE-3.md was reduced to 4 "
        "bytes by a commit that never mentioned it and stayed that way for "
        "twenty commits, because nothing looked. If a report is genuinely this "
        "short, it is not a report."
    )


@pytest.mark.parametrize("report", _phase_reports(), ids=lambda p: p.name)
def test_a_phase_report_says_what_it_does_not_establish(report: Path) -> None:
    """The expensive sections, which are the ones a weak report drops first.

    `CLAUDE.md`: *an unfavourable result is reported as plainly as a favourable
    one. A report that reads as a case for the work is not a report.* The two
    sections that carry that are the limits and the open items, and a report
    that has quietly lost them still reads fine.
    """
    # Emphasis is stripped first: PHASE-0 writes "What this does **not**
    # establish", so a literal substring match would report the section missing
    # from the one report that states it most emphatically.
    text = re.sub(r"[*_`]+", "", report.read_text(encoding="utf-8").lower())
    missing = [section for section in REQUIRED_SECTIONS if section not in text]
    assert not missing, (
        f"{report.name} has no section for: {', '.join(missing)}. These are the "
        "sections where saying the true thing costs something, which is why "
        "they are the ones worth checking for."
    )


def test_phase_numbers_are_contiguous_from_zero() -> None:
    """A missing report is as invisible as an emptied one, and more likely.

    Numbering that skips says either that a phase closed without its report or
    that the series restarted; both are things a reader has to be told rather
    than left to infer from a gap in a directory listing.
    """
    numbers = [
        int(re.search(r"PHASE-(\d+)", path.name).group(1)) for path in _phase_reports()
    ]
    assert numbers == list(range(len(numbers))), (
        f"phase reports are numbered {numbers}, which is not contiguous from 0. "
        "A gap means a phase closed without the report CLAUDE.md requires, or "
        "that the series restarted without saying so."
    )
