"""A year of rechecks as one change detector (DECISIONS.md 193).

The chain is only worth shipping if it is the rule 187 measured, if its verdict
cannot be moved by how a file is arranged, and if every way of continuing it
wrongly is refused before anything is written. Those are 193's A1 to A4, in order.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.economics.schedules import Cadence, Scenario, StudyDesign, simulate
from controlplane.intake import load_scored_items, recheck_items
from controlplane.intake.certify import evidence_sha256
from controlplane.intake.chain import (
    ChainError,
    canonical_sha256,
    continue_chain,
    feed,
    start_chain,
)
from controlplane.intake.recheck import chain_units
from controlplane.validation.warrant_stats import FPRMonitor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALPHA, BUDGET, THRESHOLD = 0.05, 0.05, 0.85
WARRANT = {
    "status": "VALID", "budget_fpr": BUDGET, "alpha": ALPHA,
    "input": {"grouped": False}, "certification": {"threshold": THRESHOLD},
    "score_distribution": None,
}


# --------------------------------------------------------------------------- #
# A1 -- the product path is 187's rule
# --------------------------------------------------------------------------- #


def test_a1_the_chain_is_the_rule_the_study_measured() -> None:
    """Same draws, same order: identical at every boundary, revoking no later.

    The study checked only at recheck boundaries; the chain checks after every
    unit. So the boundary-checked reference must reproduce the study's summary
    exactly, and the chain's revocation must fall at or before it, year by year.
    """
    design = StudyDesign(
        budget=BUDGET, alpha=ALPHA, breach=0.25, negatives_per_recheck=60, years=60,
        cadences=(Cadence("short", rechecks=10, change_after=5, window=3),),
        certified_rate=0.03,
    )
    cadence = design.cadences[0]
    scenario = Scenario("S2", BUDGET, 0.25, cadence.change_after)
    seed = 21
    study = simulate(design, cadence, scenario, seed=seed)["e_detector"]

    rng = np.random.default_rng(seed)
    draws = [rng.random((design.years, design.negatives_per_recheck)) < scenario.rate_at(j)
             for j in range(cadence.rechecks)]
    lams = np.asarray(FPRMonitor(p0=BUDGET, alpha=ALPHA).lams)
    horizon = cadence.rechecks * design.negatives_per_recheck
    boundary_first = np.full(design.years, -1)
    for year in range(design.years):
        state = start_chain(WARRANT, horizon_units=horizon, alpha=ALPHA)
        reference = np.zeros(lams.size)
        chain_first = -1
        for j in range(cadence.rechecks):
            outcomes = draws[j][year]
            for x in outcomes:
                reference = (reference + 1.0) * (1.0 + lams * (float(x) - BUDGET))
            if state.revoked_at_unit is None:
                result = feed(state, [f"y{year}-r{j}-u{i}" for i in range(outcomes.size)],
                              outcomes, in_given_order=True)
                state = result.state
                if state.revoked_at_unit is None:
                    assert np.array_equal(np.asarray(state.statistics), reference), (year, j)
                elif chain_first < 0:
                    chain_first = j
            if boundary_first[year] < 0 and reference.mean() >= horizon / ALPHA:
                boundary_first[year] = j
        if boundary_first[year] >= 0:
            assert 0 <= chain_first <= boundary_first[year], (year, chain_first, boundary_first[year])

    revoked = boundary_first >= 0
    change, window = cadence.change_after, cadence.window
    assert revoked.mean() == study.revoked_in_year
    assert (revoked & (boundary_first < change)).mean() == study.revoked_before_change
    caught = (revoked & (boundary_first >= change) & (boundary_first < change + window)).mean()
    assert caught == study.caught_in_window


def test_a1_the_chain_keeps_its_guarantee_on_a_sound_detector() -> None:
    """Under the null, the share of chains that ever revoke stays near alpha."""
    rng = np.random.default_rng(1729)
    chains, units = 400, 600
    revoked = 0
    for c in range(chains):
        state = start_chain(WARRANT, horizon_units=units, alpha=ALPHA)
        result = feed(state, [f"c{c}-u{i}" for i in range(units)], rng.random(units) < BUDGET)
        revoked += result.state.revoked_at_unit is not None
    limit = ALPHA + 3 * math.sqrt(ALPHA * (1 - ALPHA) / chains)
    assert revoked / chains <= limit, revoked / chains


# --------------------------------------------------------------------------- #
# A2 -- arrangement cannot move the verdict
# --------------------------------------------------------------------------- #


def _stream(n: int, rate: float, seed: int) -> tuple[list[str], np.ndarray]:
    rng = np.random.default_rng(seed)
    return [f"item-{i}" for i in range(n)], rng.random(n) < rate


def test_a2_permuting_a_file_changes_nothing() -> None:
    ids, fired = _stream(800, 0.09, 3)
    state = start_chain(WARRANT, horizon_units=5000, alpha=ALPHA)
    first = feed(state, ids, fired).state
    perm = np.random.default_rng(4).permutation(len(ids))
    second = feed(state, [ids[i] for i in perm], fired[perm]).state
    assert first.statistics == second.statistics
    assert first.revoked_at_unit == second.revoked_at_unit
    assert set(first.consumed_unit_digests) == set(second.consumed_unit_digests)


def test_a2_splitting_a_file_keeps_the_units_not_the_statistic() -> None:
    """193 says so rather than claiming equality: hash order is per file."""
    ids, fired = _stream(800, 0.05, 5)
    start = start_chain(WARRANT, horizon_units=5000, alpha=ALPHA)
    whole = feed(start, ids, fired).state
    half = feed(start, ids[:400], fired[:400]).state
    split = feed(half, ids[400:], fired[400:]).state
    assert whole.units_consumed == split.units_consumed == 800
    assert set(whole.consumed_unit_digests) == set(split.consumed_unit_digests)


# --------------------------------------------------------------------------- #
# A3 -- every wrong continuation is refused, and writes nothing
# --------------------------------------------------------------------------- #


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=600,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def _csv(path: Path, n: int, rate: float, seed: int, prefix: str = "i") -> Path:
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < 0.2).astype(int)
    negative_scores = np.where(rng.random(n) < rate, 0.95, 0.10)
    scores = np.where(labels == 1, 0.97, negative_scores)
    rows = ["id,label,score"] + [f"{prefix}{i},{int(y)},{s:.4f}"
                                 for i, (y, s) in enumerate(zip(labels, scores, strict=True))]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def warrant_file(tmp_path: Path) -> Path:
    path = tmp_path / "w.warrant.json"
    path.write_text(json.dumps(WARRANT), encoding="utf-8")
    return path


def test_a_chain_runs_end_to_end_and_links_its_records(tmp_path, warrant_file) -> None:
    first = tmp_path / "r1.json"
    result = _run("recheck", "-w", str(warrant_file), "-i", str(_csv(tmp_path / "a.csv", 500, 0.05, 1)),
                  "--horizon-labels", "5000", "-q", "-o", str(first))
    assert result.returncode == 0, result.stderr
    one = json.loads(first.read_text(encoding="utf-8"))
    assert one["chain"]["sequence"] == 1 and one["chain"]["previous_record_sha256"] is None

    second = tmp_path / "r2.json"
    result = _run("recheck", "-w", str(warrant_file), "-i", str(_csv(tmp_path / "b.csv", 500, 0.05, 2, "j")),
                  "--since", str(first), "-q", "-o", str(second))
    assert result.returncode == 0, result.stderr
    two = json.loads(second.read_text(encoding="utf-8"))
    assert two["chain"]["sequence"] == 2
    assert two["chain"]["previous_record_sha256"] == canonical_sha256(one)
    assert two["chain"]["units_consumed"] > one["chain"]["units_consumed"]


def _refused(result: subprocess.CompletedProcess, out: Path, phrase: str) -> None:
    assert result.returncode == 2, result.stderr
    assert phrase in result.stderr, result.stderr
    assert not out.exists(), "a refused link must write nothing"


def test_a3_refusals(tmp_path, warrant_file) -> None:
    first = tmp_path / "r1.json"
    data = _csv(tmp_path / "a.csv", 500, 0.05, 1)
    assert _run("recheck", "-w", str(warrant_file), "-i", str(data), "--horizon-labels", "5000",
                "-q", "-o", str(first)).returncode == 0

    # The same units again.
    out = tmp_path / "again.json"
    _refused(_run("recheck", "-w", str(warrant_file), "-i", str(data), "--since", str(first),
                  "-q", "-o", str(out)), out, "already consumed")

    # A different warrant.
    other = tmp_path / "other.warrant.json"
    other.write_text(json.dumps({**WARRANT, "budget_fpr": 0.04}), encoding="utf-8")
    out = tmp_path / "other.json"
    _refused(_run("recheck", "-w", str(other), "-i", str(_csv(tmp_path / "b.csv", 300, 0.05, 2, "j")),
                  "--since", str(first), "-q", "-o", str(out)), out, "different warrant")

    # An edited statistic.
    tampered = tmp_path / "tampered.json"
    edited = json.loads(first.read_text(encoding="utf-8"))
    edited["chain"]["statistics"][0] = 0.0
    tampered.write_text(json.dumps(edited), encoding="utf-8")
    out = tmp_path / "t.json"
    _refused(_run("recheck", "-w", str(warrant_file), "-i", str(_csv(tmp_path / "c.csv", 300, 0.05, 3, "k")),
                  "--since", str(tampered), "-q", "-o", str(out)), out, "does not reproduce")

    # Not a chain record.
    plain = tmp_path / "plain.json"
    assert _run("recheck", "-w", str(warrant_file), "-i", str(_csv(tmp_path / "d.csv", 300, 0.05, 4, "m")),
                "-q", "-o", str(plain)).returncode == 0
    out = tmp_path / "p.json"
    _refused(_run("recheck", "-w", str(warrant_file), "-i", str(_csv(tmp_path / "e.csv", 300, 0.05, 5, "n")),
                  "--since", str(plain), "-q", "-o", str(out)), out, "not part of a chain")

    # Both flags at once: argparse's own usage error, also exit 2.
    out = tmp_path / "both.json"
    result = _run("recheck", "-w", str(warrant_file), "-i", str(data), "--since", str(first),
                  "--horizon-labels", "10", "-q", "-o", str(out))
    assert result.returncode == 2 and not out.exists()


def test_a3_an_ended_or_revoked_chain_cannot_continue() -> None:
    ids, fired = _stream(50, 0.05, 6)
    ended = feed(start_chain(WARRANT, horizon_units=50, alpha=ALPHA), ids, fired)
    record = {"chain": ended.to_payload()}
    with pytest.raises(ChainError, match="consumed its 50 units"):
        continue_chain(json.loads(json.dumps(record)), WARRANT, alpha=ALPHA)

    ids, fired = _stream(400, 0.6, 7)
    revoked = feed(start_chain(WARRANT, horizon_units=400, alpha=ALPHA), ids, fired)
    assert revoked.state.revoked_at_unit is not None
    with pytest.raises(ChainError, match="revoked the warrant"):
        continue_chain(json.loads(json.dumps({"chain": revoked.to_payload()})), WARRANT, alpha=ALPHA)


# --------------------------------------------------------------------------- #
# A4 -- the unchained statistical result is unchanged
# --------------------------------------------------------------------------- #


def test_a4_an_unchained_recheck_is_todays_record_plus_chain_null(tmp_path, warrant_file, config) -> None:
    data = _csv(tmp_path / "a.csv", 500, 0.05, 1)
    out = tmp_path / "r.json"
    assert _run("recheck", "-w", str(warrant_file), "-i", str(data), "-q", "-o", str(out)).returncode == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    written.pop("provenance")
    assert written.pop("chain") is None
    items = load_scored_items(data)
    assert written["now"].pop("evidence_sha256") == evidence_sha256(items)
    assert written["prior_warrant"].pop("warrant_sha256") == canonical_sha256(
        json.loads(warrant_file.read_text(encoding="utf-8"))
    )
    assert written["prior_warrant"].pop("certificate_verification") == "NOT_CHECKED"
    direct = recheck_items(config, items, budget=BUDGET, threshold=THRESHOLD,
                           alpha=ALPHA).to_payload()
    assert json.loads(json.dumps(direct)) == written


def test_a_grouped_chain_consumes_clusters(tmp_path) -> None:
    rows = ["id,label,score,group"]
    for c in range(30):
        for i in range(4):
            rows.append(f"g{c}-{i},0,{0.9 if c < 2 else 0.1},neg{c}")
    for c in range(5):
        for i in range(4):
            rows.append(f"p{c}-{i},1,0.95,pos{c}")
    path = tmp_path / "g.csv"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    ids, fired = chain_units(load_scored_items(path), THRESHOLD)
    assert len(ids) == 30 and int(fired.sum()) == 2


def test_the_plan_prints_a_horizon_that_can_be_copied_as_a_command() -> None:
    """`plan` tells the user what N to declare; the line must parse as written."""
    from controlplane.cli import build_parser
    from controlplane.economics.sizing import monitoring_plan
    from controlplane.intake.render import render_plan

    plan = monitoring_plan(budget=BUDGET, breach_rate=0.075, alpha=ALPHA, power=0.8,
                           negative_share=0.9)
    lines = [line for line in render_plan(plan).splitlines() if "--horizon-labels" in line]
    assert len(lines) == len(plan.cadences)
    for line, option in zip(lines, plan.cadences, strict=True):
        value = line.split("--horizon-labels", 1)[1].split()[0]
        args = build_parser().parse_args(["recheck", "-w", "w.json", "-i", "f.csv",
                                          "--horizon-labels", value])
        assert args.horizon_labels == option.chain_horizon_units
