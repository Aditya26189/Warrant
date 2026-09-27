"""An unchained recheck reports a chain revocation (``DECISIONS.md`` 210).

Without ``--since`` or ``--horizon-labels``, ``recheck`` tested the new file
against the warrant alone and never read the chain-head sidecar. A warrant whose
chain had already REVOKED it could therefore return a fresh ``VALID`` on stable
data, with nothing in the record mentioning the revocation -- the case
``reports/PROJECT-REVIEW-2026-09-23.md`` describes as "an unchained recheck
ignores a revoked chain head; a public-command reproduction returned VALID".

The measurement is kept: these tests assert that the numbers survive and only
the status and reason change.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.intake.chain import head_path

ROOT = Path(__file__).resolve().parents[1]


def warrant(*arguments):
    return subprocess.run([sys.executable, str(ROOT / "warrant.py"), *arguments],
                          capture_output=True, text=True, timeout=900, cwd=ROOT,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def _export(path: Path, *, n_neg: int, n_pos: int, seed: int, shift: float = 0.0) -> Path:
    rng = np.random.default_rng(seed)
    rows = ["id,label,score"]
    rows += [f"{path.stem}-n{i},0,{rng.normal(shift, 1.0):.6f}" for i in range(n_neg)]
    rows += [f"{path.stem}-p{i},1,{rng.normal(2.5 + shift, 1.0):.6f}" for i in range(n_pos)]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def revoked(tmp_path_factory):
    """A warrant whose chain revoked it, and a stable file to recheck with."""
    root = tmp_path_factory.mktemp("revoked_head")
    warrant_path = root / "w.json"
    issued = warrant("certify", "-i", str(_export(root / "base.csv", n_neg=900, n_pos=300, seed=1)),
                     "-b", "0.05", "-q", "-o", str(warrant_path))
    assert issued.returncode == 0, issued.stderr

    # A breach large enough for the chain's statistic to revoke on: negatives
    # shifted up, so many of them clear the certified threshold.
    breach = _export(root / "breach.csv", n_neg=900, n_pos=300, seed=2, shift=2.2)
    first = warrant("recheck", "-w", str(warrant_path), "-i", str(breach),
                    "--horizon-labels", "100000", "-q", "-o", str(root / "link1.json"))
    assert first.returncode == 0, first.stderr
    record = json.loads((root / "link1.json").read_text(encoding="utf-8"))
    assert record["status"] == "REVOKED", "the fixture must actually revoke"
    head = json.loads(head_path(warrant_path).read_text(encoding="utf-8"))
    assert head.get("status") == "REVOKED", "the sidecar must record it"
    return {"root": root, "warrant": warrant_path,
            "stable": _export(root / "stable.csv", n_neg=900, n_pos=300, seed=3)}


def test_an_unchained_recheck_reports_the_revocation_rather_than_valid(revoked, tmp_path):
    """The reproduced behaviour: this returned VALID before 210."""
    out = tmp_path / "plain.json"
    result = warrant("recheck", "-w", str(revoked["warrant"]), "-i", str(revoked["stable"]),
                     "-q", "-o", str(out))
    assert result.returncode == 0, result.stderr
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["status"] == "REVOKED"
    assert "re-certify" in record["reason"]
    assert record["prior_warrant"]["chain_revoked_at"] == "record 0001"


def test_the_measurement_is_kept_in_full(revoked, tmp_path):
    """The numbers are why the command was run, and 210 keeps every one."""
    out = tmp_path / "plain.json"
    assert warrant("recheck", "-w", str(revoked["warrant"]), "-i", str(revoked["stable"]),
                   "-q", "-o", str(out)).returncode == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["now"]["achieved_fpr"] is not None
    assert record["now"]["fpr_upper_bound"] is not None
    assert record["detection"]["smallest_detectable_rate"] is not None
    assert record["drift"]["assessed"] is True
    # the original verdict is not thrown away, it is quoted in the reason
    assert "the original verdict here was VALID" in record["reason"]


def test_require_valid_exits_one_on_a_revoked_warrant(revoked, tmp_path):
    """What an automated caller asked for."""
    result = warrant("recheck", "-w", str(revoked["warrant"]), "-i", str(revoked["stable"]),
                     "--require-valid", "-q", "-o", str(tmp_path / "plain.json"))
    assert result.returncode == 1


def test_without_a_sidecar_nothing_is_known_and_nothing_is_claimed(revoked, tmp_path):
    """A copied warrant has no sidecar: the recheck behaves as it always did."""
    copied = tmp_path / "copy.json"
    copied.write_text(Path(revoked["warrant"]).read_text(encoding="utf-8"), encoding="utf-8")
    assert not head_path(copied).exists()
    out = tmp_path / "copied.json"
    result = warrant("recheck", "-w", str(copied), "-i", str(revoked["stable"]), "-q", "-o", str(out))
    assert result.returncode == 0, result.stderr
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["status"] == "VALID"
    assert record["prior_warrant"]["chain_revoked_at"] is None


def test_a_live_chain_head_does_not_change_an_unchained_recheck(tmp_path):
    """The control: a chain that has not revoked leaves the verdict alone."""
    warrant_path = tmp_path / "w.json"
    assert warrant("certify", "-i", str(_export(tmp_path / "b.csv", n_neg=900, n_pos=300, seed=11)),
                   "-b", "0.05", "-q", "-o", str(warrant_path)).returncode == 0
    linked = warrant("recheck", "-w", str(warrant_path),
                     "-i", str(_export(tmp_path / "wk1.csv", n_neg=900, n_pos=300, seed=12)),
                     "--horizon-labels", "100000", "-q", "-o", str(tmp_path / "l1.json"))
    assert linked.returncode == 0, linked.stderr
    assert json.loads((tmp_path / "l1.json").read_text(encoding="utf-8"))["status"] != "REVOKED"

    out = tmp_path / "plain.json"
    assert warrant("recheck", "-w", str(warrant_path),
                   "-i", str(_export(tmp_path / "next.csv", n_neg=900, n_pos=300, seed=13)),
                   "-q", "-o", str(out)).returncode == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["status"] == "VALID"
    assert record["prior_warrant"]["chain_revoked_at"] is None
