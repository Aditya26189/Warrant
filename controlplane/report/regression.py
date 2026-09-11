"""Refuse to replace a rich artifact with a poor one.

``DECISIONS.md`` 157 records the failure this closes. `03_matrix.py` builds the
warrant matrix from whatever the audit ledger has accumulated. Run out of the
order `docs/RUNBOOK.md` documents — on a fresh ledger, or before
`02_validate.py` and `04_transfer.py` have appended their measured warrants — it
**succeeds**, writes a matrix with the measured cells missing, and exits zero.

The document it produces is not dishonest. It carries an *Outstanding
measurement* banner and every missing cell reads `UNVALIDATED`, which is exactly
what those cells are. It is honest and it is a regression, and the two are
compatible: a reader who does not compare it against yesterday's cannot tell.

**The guard is a comparison, not a threshold.** A fresh clone legitimately has
no measured warrants and must be able to render. What must not happen silently
is *replacing* an artifact that has them with one that does not.

The override is a flag rather than an environment variable, and it prints what
it is discarding. ``CLAUDE.md`` forbids an override on a **refusal** — a warrant
this system declines to issue has no bypass, and that rule is about evidence.
This is a different object: a guard against clobbering a file, where the
operator sometimes genuinely does want the emptier document, and refusing
without a way through would mean deleting the artifact by hand to proceed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

__all__ = ["MatrixRegression", "check_matrix_regression", "populated_cells"]


@dataclass(frozen=True)
class MatrixRegression:
    """How a matrix about to be written compares with the one on disk.

    Attributes:
        existing: Populated cells in the committed artifact, or ``None`` when
            there is none to compare against.
        incoming: Populated cells in the matrix about to be written.
        regressed: Whether the incoming one has fewer.
        message: What to tell the operator.
    """

    existing: Optional[int]
    incoming: int
    regressed: bool
    message: str


def populated_cells(payload: Any) -> int:
    """Cells carrying a warrant, in a ``warrant_matrix.json`` payload.

    A populated cell is one with a ``warrant_id``: something was measured or
    refused there. ``UNVALIDATED`` cells are the matrix saying it has not looked,
    which is a state rather than a result and is not counted.

    Args:
        payload: The parsed artifact, or its ``matrix`` block.

    Returns:
        The count. ``0`` for anything this cannot read, so a malformed file
        never reads as a rich one.
    """
    matrix = payload.get("matrix", payload) if isinstance(payload, dict) else {}
    rows = matrix.get("rows") if isinstance(matrix, dict) else None
    if not isinstance(rows, list):
        return 0
    return sum(
        1
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("cells"), dict)
        for cell in row["cells"].values()
        if isinstance(cell, dict) and "warrant_id" in cell
    )


def check_matrix_regression(
    artifact: Path, incoming: Any, *, allow: bool = False
) -> MatrixRegression:
    """Compare an incoming matrix against the one already on disk.

    Args:
        artifact: Path to the existing ``warrant_matrix.json``.
        incoming: The payload about to be written.
        allow: Proceed even on a regression, printing what is being discarded.

    Returns:
        The comparison.

    Raises:
        SystemExit: When the incoming matrix has fewer populated cells and
            ``allow`` is ``False``. Refused **before** anything is written, so
            the existing artifact is untouched.
    """
    new_count = populated_cells(incoming)
    if not artifact.is_file():
        return MatrixRegression(
            existing=None,
            incoming=new_count,
            regressed=False,
            message=(
                f"no existing matrix to compare against; writing {new_count} "
                "populated cells"
            ),
        )

    try:
        old_count = populated_cells(json.loads(artifact.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return MatrixRegression(
            existing=None,
            incoming=new_count,
            regressed=False,
            message=(
                f"existing matrix at {artifact} is unreadable, so there is "
                "nothing to regress against; writing "
                f"{new_count} populated cells"
            ),
        )

    if new_count >= old_count:
        return MatrixRegression(
            existing=old_count,
            incoming=new_count,
            regressed=False,
            message=(
                f"{new_count} populated cells against {old_count} on disk; not "
                "a regression"
            ),
        )

    message = (
        f"\nREFUSED: this run would replace a matrix of {old_count} populated "
        f"cells with one of {new_count}.\n\n"
        "A populated cell is one where something was measured or refused. "
        "Losing them usually means the pipeline ran out of the order "
        "docs/RUNBOOK.md documents -- the measured warrants come from "
        "02_validate.py and 04_transfer.py, and 03_matrix.py ablates only the "
        "synthetic envelopes. Run on a fresh ledger it succeeds and writes a "
        "document with the measured rows missing.\n\n"
        "That document is not dishonest: every missing cell reads UNVALIDATED, "
        "which is what it is. It is a regression, and a reader who does not "
        "compare it against yesterday's cannot tell.\n\n"
        "The order:\n\n"
        "    01_build_evalsets -> 02_validate -> 09_detectors\n"
        "                      -> 04_transfer -> 03_matrix\n\n"
        "If the emptier matrix is what you want -- a fresh clone, or a "
        "deliberate rebuild -- pass --allow-matrix-regression. Nothing has been "
        "written. DECISIONS.md 158.\n"
    )
    if not allow:
        raise SystemExit(message)
    return MatrixRegression(
        existing=old_count,
        incoming=new_count,
        regressed=True,
        message=(
            f"proceeding under --allow-matrix-regression: {old_count} populated "
            f"cells -> {new_count}, discarding {old_count - new_count}"
        ),
    )
