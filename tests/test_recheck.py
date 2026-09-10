"""`warrant recheck`: the clause about when a number stops being true.

The two failure modes are kept apart on purpose and the tests keep them apart
too. *Your bound broke* and *your traffic moved* call for different actions —
re-certify versus investigate — and a single health score that merges them is
how a dashboard stays green while the thing it watches stops being true.

The third case is the one this project exists for: a file too small to tell drift
from resampling gets **no drift verdict at all**, rather than a reassuring one.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.intake import (
    load_scored_items,
    recheck_items,
    render_recheck,
    score_distribution,
)
from controlplane.model import WarrantStatus

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _csv(tmp_path: Path, scores, labels, name="f.csv") -> Path:
    path = tmp_path / name
    rows = ["id,label,score"]
    rows += [f"i{i},{int(l)},{float(s):.6f}" for i, (s, l) in enumerate(zip(scores, labels))]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _world(n, separation=1.9, base=0.25, shift=0.0, seed=11):
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < base).astype(int)
    raw = rng.normal(0, 1, n) + separation * labels + shift
    return 1 / (1 + np.exp(-raw)), labels


# ----------------------------------------------------------- the bound

def test_a_stable_world_keeps_its_warrant(tmp_path, config) -> None:
    scores, labels = _world(1200)
    reference = score_distribution(scores)
    later, later_labels = _world(800, seed=12)
    items = load_scored_items(_csv(tmp_path, later, later_labels))

    result = recheck_items(
        config, items, budget=0.05, threshold=0.847207, reference=reference
    )
    assert result.status is WarrantStatus.VALID
    assert result.bound_still_holds is True
    assert result.drift_assessed is True


def test_a_broken_bound_revokes(tmp_path, config) -> None:
    """The promise is measurably false on this data. That outranks everything."""
    scores, labels = _world(1200)
    reference = score_distribution(scores)
    later, later_labels = _world(800, shift=2.2, seed=12)
    items = load_scored_items(_csv(tmp_path, later, later_labels))

    result = recheck_items(
        config, items, budget=0.05, threshold=0.847207, reference=reference
    )
    assert result.status is WarrantStatus.REVOKED
    assert result.bound_still_holds is False
    assert result.fpr_upper_bound_now > 0.05
    assert "evidence the promise is broken" in result.reason
    assert result.fpr_lower_bound_now > 0.05, (
        "revocation must rest on the LOWER bound exceeding the budget"
    )


def test_no_negatives_is_untestable_not_valid(config) -> None:
    """A warrant that cannot be re-tested has not been re-confirmed.

    The tempting default is to leave it standing because nothing contradicted
    it, which is the modal way a stale claim survives.

    Built directly rather than from a file: the input contract already refuses a
    single-class file, so this state is unreachable through the CLI. It is
    tested anyway because `recheck_items` is importable, and a library function
    whose contract depends on a caller's validation is one waiting to be called
    without it.
    """
    from controlplane.intake import ScoredItems

    items = ScoredItems(
        ids=tuple(f"i{i}" for i in range(30)),
        labels=(1,) * 30,
        scores=tuple(0.9 for _ in range(30)),
        groups=None,
        passthrough_columns=(),
        source="constructed",
    )
    result = recheck_items(config, items, budget=0.05, threshold=0.5)
    assert result.status is WarrantStatus.UNVALIDATED
    assert result.bound_still_holds is None
    assert "not evidence that it holds" in result.reason


# ------------------------------------------------------------ the drift

def test_a_small_file_gets_no_drift_verdict(tmp_path, config) -> None:
    """Below the window, a shift cannot be told from resampling.

    Reporting "no drift detected" on fifty rows would be the reassuring answer
    and an unsupported one.
    """
    scores, labels = _world(1200)
    reference = score_distribution(scores)
    small, small_labels = _world(50, seed=13)
    items = load_scored_items(_csv(tmp_path, small, small_labels))

    result = recheck_items(
        config, items, budget=0.05, threshold=0.847207, reference=reference
    )
    assert result.drift_assessed is False
    assert result.psi is None
    assert "indistinguishable from" in result.drift_not_assessed_reason


def test_psi_is_judged_against_this_files_own_noise(tmp_path, config) -> None:
    """Not against the 0.10/0.25 folklore bands, which are not scale-free.

    The null grows roughly as (k-1)/n, so the same PSI means different things at
    different sample sizes. A verdict that ignored that would fire on large
    stable files and stay silent on small shifted ones.
    """
    scores, labels = _world(1200)
    reference = score_distribution(scores)
    later, later_labels = _world(800, seed=12)
    items = load_scored_items(_csv(tmp_path, later, later_labels))

    result = recheck_items(
        config, items, budget=0.05, threshold=0.847207, reference=reference
    )
    assert result.psi_null_p95 is not None and result.psi_null_p95 > 0
    assert result.psi_beyond_noise == (result.psi > result.psi_null_p95)


def test_a_warrant_without_a_distribution_says_drift_was_skipped(tmp_path, config) -> None:
    """Records issued before distributions were carried must not read as stable."""
    later, later_labels = _world(800, seed=12)
    items = load_scored_items(_csv(tmp_path, later, later_labels))

    result = recheck_items(config, items, budget=0.05, threshold=0.847207)
    assert result.drift_assessed is False
    assert "nothing to compare against" in result.drift_not_assessed_reason
    assert "Drift was not assessed" in result.reason


# ------------------------------------------------------------ the output

def test_the_summary_keeps_the_two_failures_apart(tmp_path, config) -> None:
    scores, labels = _world(1200)
    reference = score_distribution(scores)
    later, later_labels = _world(800, shift=2.2, seed=12)
    items = load_scored_items(_csv(tmp_path, later, later_labels))
    text = render_recheck(
        recheck_items(config, items, budget=0.05, threshold=0.847207, reference=reference)
    )
    assert "1. Does the bound still hold?" in text
    assert "2. Has the distribution moved?" in text
    assert "not a broken tool" in text
    text.encode("ascii")  # printable on a cp1252 console


# --------------------------------------------------------------- the CLI

def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )


def test_certify_then_recheck_end_to_end(tmp_path) -> None:
    scores, labels = _world(1200)
    base = _csv(tmp_path, scores, labels, "base.csv")
    record = tmp_path / "base.warrant.json"
    assert _run("certify", "-i", str(base), "-b", "0.05", "-q", "-o", str(record)).returncode == 0

    payload = json.loads(record.read_text(encoding="utf-8"))
    assert payload["score_distribution"], (
        "certify must record the score distribution, or recheck has no reference"
    )

    later, later_labels = _world(800, seed=12)
    fresh = _csv(tmp_path, later, later_labels, "later.csv")
    result = _run("recheck", "-w", str(record), "-i", str(fresh),
                  "-o", str(tmp_path / "r.json"))
    assert result.returncode == 0, result.stderr
    assert "RECHECK: VALID" in result.stdout


def test_recheck_of_a_refused_warrant_is_a_readable_error(tmp_path) -> None:
    """A refusal certified no threshold, so there is no promise to re-test."""
    record = tmp_path / "refused.warrant.json"
    record.write_text(json.dumps({
        "status": "REFUSED", "budget_fpr": 0.01,
        "certification": {"threshold": None},
    }), encoding="utf-8")
    scores, labels = _world(300)
    result = _run("recheck", "-w", str(record),
                  "-i", str(_csv(tmp_path, scores, labels)))
    assert result.returncode == 2
    assert "no certified threshold" in result.stderr


def test_require_valid_flips_the_exit_code(tmp_path) -> None:
    scores, labels = _world(1200)
    record = tmp_path / "b.warrant.json"
    _run("certify", "-i", str(_csv(tmp_path, scores, labels, "b.csv")),
         "-b", "0.05", "-q", "-o", str(record))
    shifted, shifted_labels = _world(800, shift=2.2, seed=12)
    result = _run("recheck", "-w", str(record),
                  "-i", str(_csv(tmp_path, shifted, shifted_labels, "s.csv")),
                  "-o", str(tmp_path / "r.json"), "-q", "--require-valid")
    assert result.returncode == 1
    assert "REVOKED" in result.stderr


def test_a_missing_warrant_record_is_a_readable_error(tmp_path) -> None:
    scores, labels = _world(300)
    result = _run("recheck", "-w", str(tmp_path / "nope.json"),
                  "-i", str(_csv(tmp_path, scores, labels)))
    assert result.returncode == 2
    assert "no warrant record" in result.stderr
