"""PSI's noise band is simulated at the reference's size (``DECISIONS.md`` 209).

R8 of ``reports/PROJECT-REVIEW-2026-09-23.md``: ``recheck`` passed the new file's
size as ``n_reference``, so the null assumed the reference was as large as the
sample being judged. The simulator resamples the reference at that size because
its own estimation error is part of the null, and a hundred-item reference is
noisy in a way a ten-thousand-item one is not.

The bug was quiet. Both numbers are plausible, the verdict merely changes, and
nothing in the output said which size the band came from -- so these tests assert
the recorded size as well as the behaviour.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.config import load_config
from controlplane.drift import simulate_null_psi
from controlplane.intake.contract import load_scored_items
from controlplane.intake.recheck import recheck_items, score_distribution

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def config():
    return load_config(str(ROOT / "config.yaml"))


def _write(path: Path, scores, labels) -> Path:
    rows = ["id,label,score"]
    rows += [f"i{i},{int(label)},{float(score):.6f}" for i, (score, label) in
             enumerate(zip(scores, labels, strict=True))]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _items(path: Path, n_negative: int, n_positive: int, seed: int, shift: float = 0.0):
    rng = np.random.default_rng(seed)
    scores = np.concatenate([rng.normal(shift, 1.0, n_negative),
                             rng.normal(2.5 + shift, 1.0, n_positive)])
    labels = np.concatenate([np.zeros(n_negative), np.ones(n_positive)])
    return load_scored_items(_write(path, scores, labels))


def test_the_null_band_is_wider_when_the_reference_was_small(config) -> None:
    """The band is a property of both sizes, and the small one dominates it."""
    rng = np.random.default_rng(7)
    reference = score_distribution(rng.normal(0.0, 1.0, 100))
    small = simulate_null_psi(reference.bin_probabilities, n=10_000, n_reference=100,
                              stable_band=config.drift.psi_stable)
    large = simulate_null_psi(reference.bin_probabilities, n=10_000, n_reference=10_000,
                              stable_band=config.drift.psi_stable)
    assert small.p95 > large.p95 * 10, (
        "a hundred-item reference must not be treated as precisely as a "
        f"ten-thousand-item one: {small.p95} vs {large.p95}"
    )


def test_a_recheck_calibrates_against_the_reference_size_it_is_given(config, tmp_path) -> None:
    """R8's counterexample: the same file, judged against two bands."""
    reference_items = _items(tmp_path / "ref.csv", 80, 20, seed=1)
    reference = score_distribution(reference_items.as_arrays()[1])
    current = _items(tmp_path / "now.csv", 8_000, 2_000, seed=2)

    honest = recheck_items(config, current, budget=0.05, threshold=1.8,
                           reference=reference, reference_n=reference_items.n)
    as_before = recheck_items(config, current, budget=0.05, threshold=1.8,
                              reference=reference, reference_n=None)

    assert honest.psi == pytest.approx(as_before.psi), "the index itself is unchanged"
    assert honest.psi_null_p95 > as_before.psi_null_p95, (
        "calibrating at the reference's own size must widen the band"
    )
    assert honest.psi_reference_n == reference_items.n
    assert as_before.psi_reference_n is None


def test_the_record_says_which_size_the_band_came_from(config, tmp_path) -> None:
    reference_items = _items(tmp_path / "ref.csv", 80, 20, seed=3)
    current = _items(tmp_path / "now.csv", 400, 100, seed=4)
    result = recheck_items(config, current, budget=0.05, threshold=1.8,
                           reference=score_distribution(reference_items.as_arrays()[1]),
                           reference_n=reference_items.n)
    drift = result.to_payload()["drift"]
    assert drift["psi_reference_n"] == reference_items.n
    assert drift["psi_reference_n_known"] is True
    assert "assumed" not in drift["note"], "no fallback disclosure when the size is known"


def test_a_record_without_a_reference_size_says_the_band_assumed_one(config, tmp_path) -> None:
    """Legacy behaviour, disclosed rather than silent (209)."""
    reference_items = _items(tmp_path / "ref.csv", 80, 20, seed=5)
    current = _items(tmp_path / "now.csv", 400, 100, seed=6)
    result = recheck_items(config, current, budget=0.05, threshold=1.8,
                           reference=score_distribution(reference_items.as_arrays()[1]),
                           reference_n=None)
    drift = result.to_payload()["drift"]
    assert drift["psi_reference_n"] is None
    assert drift["psi_reference_n_known"] is False
    assert "assumed it was as large as this file" in drift["note"]


def test_the_cli_takes_the_size_from_the_warrant_it_was_given(tmp_path) -> None:
    """End to end: certify writes input.n, and recheck's record reports it back."""
    def run(*arguments):
        return subprocess.run([sys.executable, str(ROOT / "warrant.py"), *arguments],
                              capture_output=True, text=True, timeout=900, cwd=ROOT,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    base = _write_random(tmp_path / "base.csv", n_negative=700, n_positive=200, seed=11)
    warrant_path = tmp_path / "w.json"
    issued = run("certify", "-i", str(base), "-b", "0.05", "-q", "-o", str(warrant_path))
    assert issued.returncode == 0, issued.stderr
    certified = json.loads(warrant_path.read_text(encoding="utf-8"))

    fresh = _write_random(tmp_path / "next.csv", n_negative=700, n_positive=200, seed=12)
    out = tmp_path / "r.json"
    rechecked = run("recheck", "-w", str(warrant_path), "-i", str(fresh), "-q", "-o", str(out))
    assert rechecked.returncode == 0, rechecked.stderr
    drift = json.loads(out.read_text(encoding="utf-8"))["drift"]
    assert drift["psi_reference_n"] == certified["input"]["n"]
    assert drift["psi_reference_n_known"] is True


def _write_random(path: Path, *, n_negative: int, n_positive: int, seed: int) -> Path:
    rng = np.random.default_rng(seed)
    scores = np.concatenate([rng.normal(0.0, 1.0, n_negative),
                             rng.normal(2.5, 1.0, n_positive)])
    labels = np.concatenate([np.zeros(n_negative), np.ones(n_positive)])
    return _write(path, scores, labels)
