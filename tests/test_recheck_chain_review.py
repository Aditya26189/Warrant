"""The review of the recheck chain, as tests (DECISIONS.md 194).

accenture-c4 reviewed 193 read-only and reproduced each finding through the CLI.
Every test here is one of those reproductions, so the defect it describes cannot
come back without a failure naming it.
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from controlplane.intake import load_scored_items, recheck_items, score_distribution
from controlplane.intake.chain import (
    ChainError,
    canonical_sha256,
    feed,
    head_path,
    start_chain,
)
from controlplane.intake.recheck import apply_chain, chain_units
from controlplane.model import WarrantStatus

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUDGET, ALPHA = 0.05, 0.05
#: The threshold certify issues on test_recheck's 1,200-row world at seed 11.
THRESHOLD = 0.847207
WARRANT = {
    "status": "VALID", "budget_fpr": BUDGET, "alpha": ALPHA,
    "input": {"grouped": False}, "certification": {"threshold": THRESHOLD},
    "score_distribution": None,
}


def _world(n, separation=1.9, base=0.25, shift=0.0, seed=11):
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < base).astype(int)
    raw = rng.normal(0, 1, n) + separation * labels + shift
    return 1 / (1 + np.exp(-raw)), labels


def _csv(path: Path, scores, labels, prefix="i") -> Path:
    rows = ["id,label,score"] + [f"{prefix}{i},{int(y)},{float(s):.6f}"
                                 for i, (s, y) in enumerate(zip(scores, labels, strict=True))]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# F1 -- a drift revocation survives the chain
# --------------------------------------------------------------------------- #


def test_f1_a_drift_revocation_is_not_hidden_by_a_chain(tmp_path, config) -> None:
    base_scores, _ = _world(1200)
    later, later_labels = _world(2000, shift=0.8, seed=31)
    items = load_scored_items(_csv(tmp_path / "shifted.csv", later, later_labels))
    alone = recheck_items(config, items, budget=BUDGET, threshold=THRESHOLD,
                          reference=score_distribution(base_scores), alpha=ALPHA)
    assert alone.status is WarrantStatus.REVOKED
    assert alone.bound_still_holds is False, "the repro needs the bound to break too"
    assert alone.drift_verdict == "REVOKED"

    ids, fired = chain_units(items, THRESHOLD)
    fed = feed(start_chain(WARRANT, horizon_units=5, alpha=ALPHA), ids, fired)
    assert fed.state.revoked_at_unit is None, "the repro needs the chain not to cross"
    chained = apply_chain(alone, fed)
    assert chained.status is WarrantStatus.REVOKED, (
        "a chain turned a drift revocation into STALE -- the defect 194 F1 fixed"
    )
    assert "distribution has moved" in chained.reason


def test_f1_the_drift_verdict_is_the_rule_verdict_applies(tmp_path, config) -> None:
    """Unchained and with the bound intact, the separate verdict is the status."""
    base_scores, _ = _world(1200)
    for shift, seed in ((0.0, 12), (0.35, 13), (1.2, 14)):
        later, labels = _world(1500, shift=shift, seed=seed)
        result = recheck_items(config, load_scored_items(_csv(tmp_path / f"s{seed}.csv", later, labels)),
                               budget=BUDGET, threshold=0.99, reference=score_distribution(base_scores),
                               alpha=ALPHA)
        assert result.bound_still_holds is True
        expected = {"REVOKED": WarrantStatus.REVOKED, "STALE": WarrantStatus.STALE,
                    "STABLE": WarrantStatus.VALID}[result.drift_verdict]
        assert result.status is expected, (shift, result.drift_verdict, result.status)


# --------------------------------------------------------------------------- #
# F2 -- every reason says where the chain is
# --------------------------------------------------------------------------- #


def test_f2_a_stale_link_says_the_chain_ended_and_what_it_did_not_see(tmp_path, config) -> None:
    base_scores, _ = _world(1200)
    later, later_labels = _world(2000, shift=0.8, seed=31)
    items = load_scored_items(_csv(tmp_path / "shifted.csv", later, later_labels))
    result = recheck_items(config, items, budget=BUDGET, threshold=THRESHOLD,
                           reference=score_distribution(base_scores), alpha=ALPHA)
    no_drift = dataclasses.replace(result, drift_verdict="STABLE")
    ids, fired = chain_units(items, THRESHOLD)
    fed = feed(start_chain(WARRANT, horizon_units=5, alpha=ALPHA), ids, fired)
    chained = apply_chain(no_drift, fed)
    assert chained.status is WarrantStatus.STALE
    assert "not consumed" in chained.reason
    assert "re-certify" in chained.reason
    assert f"{fed.units_not_consumed:,}" in chained.reason


# --------------------------------------------------------------------------- #
# F3 -- ids, not items
# --------------------------------------------------------------------------- #


def test_f3_the_refusal_names_the_id_rule() -> None:
    state = start_chain(WARRANT, horizon_units=5000, alpha=ALPHA)
    ids = [f"row{i}" for i in range(200)]
    first = feed(state, ids, np.zeros(200, dtype=bool)).state
    try:
        feed(first, ids, np.zeros(200, dtype=bool))
    except ChainError as exc:
        assert "unique across every file" in str(exc)
    else:
        raise AssertionError("a reused id was accepted")


def test_f3_renamed_ids_are_accepted_and_the_module_says_so() -> None:
    """The limit, pinned: the chain remembers ids, and cannot know two ids are one item."""
    import controlplane.intake.chain as chain

    state = start_chain(WARRANT, horizon_units=5000, alpha=ALPHA)
    first = feed(state, [f"m1_{i}" for i in range(100)], np.zeros(100, dtype=bool)).state
    again = feed(first, [f"m1x_{i}" for i in range(100)], np.zeros(100, dtype=bool)).state
    assert again.units_consumed == 200
    assert "not items" in chain.__doc__


# --------------------------------------------------------------------------- #
# F4 -- what N counts
# --------------------------------------------------------------------------- #


def test_f4_plan_says_n_counts_negatives_fed() -> None:
    from controlplane.economics.sizing import monitoring_plan
    from controlplane.intake.render import render_plan

    text = render_plan(monitoring_plan(budget=BUDGET, breach_rate=0.075, alpha=ALPHA, power=0.8,
                                       negative_share=0.9))
    assert "N counts clean negatives fed to the chain, not rechecks or weeks" in text


# --------------------------------------------------------------------------- #
# F5 -- a fork declares itself
# --------------------------------------------------------------------------- #


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=600,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def _batch(tmp_path: Path, name: str, seed: int) -> Path:
    scores, labels = _world(400, seed=seed)
    return _csv(tmp_path / f"{name}.csv", scores, labels, prefix=f"{name}-")


def _digest(path: Path) -> str:
    return canonical_sha256(json.loads(path.read_text(encoding="utf-8")))


def test_f5_head_fork_and_restart(tmp_path) -> None:
    warrant = tmp_path / "w.warrant.json"
    warrant.write_text(json.dumps(WARRANT), encoding="utf-8")
    sidecar = head_path(warrant)

    r1 = tmp_path / "r1.json"
    assert _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "a", 1)),
                "--horizon-labels", "50000", "-q", "-o", str(r1)).returncode == 0
    assert json.loads(sidecar.read_text(encoding="utf-8"))["head_record_sha256"] == _digest(r1)
    assert json.loads(r1.read_text(encoding="utf-8"))["chain"]["head_check"] == "no_sidecar"

    r2 = tmp_path / "r2.json"
    assert _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "b", 2)),
                "--since", str(r1), "-q", "-o", str(r2)).returncode == 0
    assert json.loads(r2.read_text(encoding="utf-8"))["chain"]["head_check"] == "matched"
    head_after_r2 = sidecar.read_bytes()

    # Continuing from r1 again would drop r2: refused, nothing written, head unchanged.
    stale = tmp_path / "r3-stale.json"
    result = _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "c", 3)),
                  "--since", str(r1), "-q", "-o", str(stale))
    assert result.returncode == 2 and "not the chain's latest record" in result.stderr
    assert not stale.exists() and sidecar.read_bytes() == head_after_r2

    # Declared, it goes through and says which head it left.
    forked = tmp_path / "r3-fork.json"
    assert _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "c", 3)),
                "--since", str(r1), "--fork", "-q", "-o", str(forked)).returncode == 0
    chain = json.loads(forked.read_text(encoding="utf-8"))["chain"]
    assert chain["head_check"] == "forked" and chain["forked_from_head"] == _digest(r2)

    # A restart over a live head is the same accident.
    restart = tmp_path / "restart.json"
    result = _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "d", 4)),
                  "--horizon-labels", "50000", "-q", "-o", str(restart))
    assert result.returncode == 2 and "already exists" in result.stderr and not restart.exists()

    # A deleted sidecar under a chain that had one is not "no sidecar" any more:
    # the record knows there was a head (194, A). Refused, then declared.
    sidecar.unlink()
    loose = tmp_path / "loose.json"
    result = _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "e", 5)),
                  "--since", str(forked), "-q", "-o", str(loose))
    assert result.returncode == 2 and "had a head" in result.stderr and not loose.exists()
    assert _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "e", 5)),
                "--since", str(forked), "--fork", "-q", "-o", str(loose)).returncode == 0
    assert json.loads(loose.read_text(encoding="utf-8"))["chain"]["head_check"] == "forked"


def test_f5_fork_without_a_chain_is_refused(tmp_path) -> None:
    warrant = tmp_path / "w.warrant.json"
    warrant.write_text(json.dumps(WARRANT), encoding="utf-8")
    out = tmp_path / "r.json"
    result = _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "a", 1)),
                  "--fork", "-q", "-o", str(out))
    assert result.returncode == 2 and "--fork only applies" in result.stderr and not out.exists()


# --------------------------------------------------------------------------- #
# F5, second review -- a copied warrant, an edited sidecar, an overwritten record
# --------------------------------------------------------------------------- #


def test_a_copied_warrant_cannot_continue_a_headed_chain_silently(tmp_path) -> None:
    """A: the sidecar is keyed by path, so a copy starts with no head; the record knows it had one."""
    import shutil

    warrant = tmp_path / "w.warrant.json"
    warrant.write_text(json.dumps(WARRANT), encoding="utf-8")
    r1 = tmp_path / "r1.json"
    assert _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "a", 1)),
                "--horizon-labels", "100000", "-q", "-o", str(r1)).returncode == 0
    r2 = tmp_path / "r2.json"
    assert _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "b", 2)),
                "--since", str(r1), "-q", "-o", str(r2)).returncode == 0

    copy = tmp_path / "w_copy.json"
    shutil.copy(warrant, copy)
    out = tmp_path / "copy-link.json"
    result = _run("recheck", "-w", str(copy), "-i", str(_batch(tmp_path, "c", 3)),
                  "--since", str(r2), "-q", "-o", str(out))
    assert result.returncode == 2 and "had a head" in result.stderr and not out.exists()

    declared = _run("recheck", "-w", str(copy), "-i", str(_batch(tmp_path, "c", 3)),
                    "--since", str(r2), "--fork", "-q", "-o", str(out))
    assert declared.returncode == 0, declared.stderr
    assert json.loads(out.read_text(encoding="utf-8"))["chain"]["head_check"] == "forked"


def test_the_record_says_what_matched_does_not_prove(tmp_path) -> None:
    """B(i): an edited sidecar can read 'matched'; the record must not imply otherwise."""
    state = start_chain(WARRANT, horizon_units=100, alpha=ALPHA)
    payload = feed(state, ["u1"], np.zeros(1, dtype=bool)).to_payload()
    assert "not proof that this link is not a fork" in payload["head_check_meaning"]


def test_a_chained_recheck_never_overwrites_and_names_its_link(tmp_path) -> None:
    """C: one export filename every week must not destroy last week's link."""
    warrant = tmp_path / "w.warrant.json"
    warrant.write_text(json.dumps(WARRANT), encoding="utf-8")
    latest = _batch(tmp_path, "latest", 1)
    assert _run("recheck", "-w", str(warrant), "-i", str(latest),
                "--horizon-labels", "100000", "-q").returncode == 0
    first = latest.with_suffix(latest.suffix + ".recheck-0001.json")
    assert first.is_file(), "a chained record is named by its link number"
    before = first.read_bytes()
    sidecar_before = head_path(warrant).read_bytes()

    result = _run("recheck", "-w", str(warrant), "-i", str(_batch(tmp_path, "b", 2)),
                  "--since", str(first), "-q", "-o", str(first))
    assert result.returncode == 2 and "never writes over a record" in result.stderr
    assert first.read_bytes() == before and head_path(warrant).read_bytes() == sidecar_before


# --------------------------------------------------------------------------- #
# A-C reviewed -- what the digests cannot prove, and an atomic refusal
# --------------------------------------------------------------------------- #


def test_a_rewritten_record_passes_and_every_text_says_it_would() -> None:
    """A-1, pinned as a limit: a cleared head_check with a recomputed digest verifies."""
    import dataclasses as dc

    import controlplane.intake.chain as chain
    from controlplane.intake.chain import ChainState
    from controlplane.intake.chain_verify import verify_chain_records

    state = start_chain(WARRANT, horizon_units=1000, alpha=ALPHA)
    fed = feed(state, [f"u{i}" for i in range(20)], np.zeros(20, dtype=bool))
    honest = fed.to_payload()
    assert honest["head_check"] == "no_sidecar"
    laundered = dc.replace(fed.state, head_check=None, forked_from_head=None).to_payload()
    assert "head_check" not in laundered
    assert ChainState.from_payload(laundered).head_check is None, "a re-digested edit is accepted"
    report = verify_chain_records({"r1": {"chain": laundered}}).to_payload()
    assert report["clean"] is True
    assert "checksums, not signatures" in report["cannot_check"]
    assert "checksums, not signatures" in honest["guarantee"]
    assert "not signatures" in chain.__doc__


def test_a_chained_record_is_created_exclusively(tmp_path) -> None:
    """C-1: the refusal and the write are one step."""
    import pytest

    from controlplane.config import write_json_artifact

    target = tmp_path / "link.json"
    write_json_artifact(target, {"a": 1}, exclusive=True)
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        write_json_artifact(target, {"a": 2}, exclusive=True)
    assert target.read_bytes() == before
