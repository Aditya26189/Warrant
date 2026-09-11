"""The guard that stops a richer artifact being replaced by a poorer one.

``DECISIONS.md`` 157 records the failure, and it is subtle enough to be worth
restating. `03_matrix.py` builds the warrant matrix from whatever the audit
ledger holds. Run out of the order `docs/RUNBOOK.md` documents, it **succeeds**,
writes a matrix with the measured cells missing, and exits zero.

The document it produces is **not dishonest**. Every missing cell reads
`UNVALIDATED`, which is precisely what those cells are, and it carries an
*Outstanding measurement* banner. It is honest and it is a regression, and the
two are entirely compatible — which is what makes it the kind of defect this
repository keeps finding: a control aimed at whether a number is right, in a
situation where every number is right and the document is worse.

These tests check the comparison, both directions, and that nothing is written
on the refusing path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from controlplane.report.regression import (
    check_matrix_regression,
    populated_cells,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _matrix(*counts: int) -> dict:
    """A payload with ``sum(counts)`` populated cells across ``len(counts)`` rows."""
    rows = []
    for index, populated in enumerate(counts):
        cells = {f"env-{i}": {"status": "VALID", "warrant_id": f"W-{index}-{i}"}
                 for i in range(populated)}
        cells["env-empty"] = {"status": "UNVALIDATED"}
        rows.append({"detector_id": f"d{index}", "cells": cells})
    return {"matrix": {"rows": rows}}


def test_populated_cells_counts_warrants_and_not_unvalidated() -> None:
    """`UNVALIDATED` is the matrix saying it has not looked, not a result."""
    assert populated_cells(_matrix(3, 2)) == 5
    assert populated_cells(_matrix()) == 0
    # Anything unreadable counts as zero, so a malformed file can never read as
    # a rich one and thereby block a legitimate write.
    assert populated_cells({"matrix": {"rows": "not a list"}}) == 0
    assert populated_cells({}) == 0
    assert populated_cells("not a payload") == 0


def test_a_poorer_matrix_is_refused_and_nothing_is_written(tmp_path: Path) -> None:
    """The exact failure of `DECISIONS.md` 157, in one assertion."""
    artifact = tmp_path / "warrant_matrix.json"
    artifact.write_text(json.dumps(_matrix(8, 7)), encoding="utf-8")
    before = artifact.read_text(encoding="utf-8")

    with pytest.raises(SystemExit) as raised:
        check_matrix_regression(artifact, _matrix(2, 1))

    message = str(raised.value)
    assert "REFUSED" in message
    assert "15" in message and "3" in message
    # The message has to name the cause and the remedy, or it is a wall.
    assert "RUNBOOK" in message
    assert "02_validate" in message and "04_transfer" in message
    assert "--allow-matrix-regression" in message
    assert "Nothing has been written" in message

    # And nothing was.
    assert artifact.read_text(encoding="utf-8") == before


def test_the_refusal_says_the_poorer_document_is_not_dishonest(tmp_path: Path) -> None:
    """Because it is not, and a message that cried fraud would be wrong.

    The failure is that an honest document silently replaces a better one. A
    refusal that mischaracterised it would teach its reader to distrust the
    wrong thing.
    """
    artifact = tmp_path / "warrant_matrix.json"
    artifact.write_text(json.dumps(_matrix(5)), encoding="utf-8")
    with pytest.raises(SystemExit) as raised:
        check_matrix_regression(artifact, _matrix(1))
    message = str(raised.value)
    assert "not dishonest" in message
    assert "UNVALIDATED" in message


def test_an_equal_or_richer_matrix_is_allowed(tmp_path: Path) -> None:
    """The guard is a comparison, not a threshold."""
    artifact = tmp_path / "warrant_matrix.json"
    artifact.write_text(json.dumps(_matrix(4)), encoding="utf-8")

    same = check_matrix_regression(artifact, _matrix(4))
    assert not same.regressed and same.existing == 4 and same.incoming == 4

    richer = check_matrix_regression(artifact, _matrix(4, 3))
    assert not richer.regressed and richer.incoming == 7


def test_a_fresh_clone_with_no_artifact_can_still_render(tmp_path: Path) -> None:
    """A clean checkout has no measured warrants and must not be blocked."""
    result = check_matrix_regression(tmp_path / "absent.json", _matrix())
    assert not result.regressed
    assert result.existing is None
    assert "no existing matrix" in result.message


def test_an_unreadable_existing_artifact_does_not_block_the_write(tmp_path: Path) -> None:
    """A corrupt file is a reason to rewrite, not a reason to refuse forever."""
    artifact = tmp_path / "warrant_matrix.json"
    artifact.write_text("{ not json", encoding="utf-8")
    result = check_matrix_regression(artifact, _matrix(3))
    assert not result.regressed
    assert "unreadable" in result.message


def test_the_override_proceeds_and_says_what_it_discards(tmp_path: Path) -> None:
    """``CLAUDE.md`` forbids an override on a refusal; this is not one.

    A warrant this system declines to issue has no bypass, and that rule is
    about evidence. This guards against clobbering a file, where the operator
    sometimes genuinely wants the emptier document — and refusing with no way
    through would mean deleting the artifact by hand to proceed, which is a
    worse outcome than a flag that prints what it is throwing away.
    """
    artifact = tmp_path / "warrant_matrix.json"
    artifact.write_text(json.dumps(_matrix(9)), encoding="utf-8")
    result = check_matrix_regression(artifact, _matrix(2), allow=True)
    assert result.regressed
    assert result.existing == 9 and result.incoming == 2
    assert "discarding 7" in result.message


def test_the_committed_matrix_would_not_regress_against_itself() -> None:
    """The real artifact, against the real guard."""
    artifact = PROJECT_ROOT / "results" / "warrant_matrix.json"
    if not artifact.is_file():
        pytest.skip("results/warrant_matrix.json is not committed")
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    result = check_matrix_regression(artifact, payload)
    assert not result.regressed
    assert result.incoming == result.existing
    assert result.incoming > 0, (
        "the committed matrix has no populated cells, which would make this "
        "guard unable to protect anything"
    )
