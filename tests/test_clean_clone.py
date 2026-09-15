"""The clean-clone gate's reporting. Block E, E.8.

**The gate itself is not run here, and cannot be.** It clones the repository
and runs this suite inside the clone; a test that invoked it would clone, run
the suite, reach that test, and clone again. It is run by hand before
submission, which is what it is for, and `tests/test_smoke.py` exempts it from
the every-script-has-a-smoke-test guard for this reason rather than silently.

What is tested here is the part that decides *what the gate says*, which is
where a gate goes wrong quietly: reporting a pass for a step that never ran.
"""

from __future__ import annotations

import json
from pathlib import Path

from controlplane.report.clean_clone import (
    GateResult,
    StepResult,
    render,
    write_artifact,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _step(name: str, ok: bool, skipped: bool = False) -> StepResult:
    return StepResult(
        name=name,
        command=["python", "-c", "pass"],
        returncode=0 if ok else 1,
        duration_seconds=1.0,
        ok=ok,
        skipped=skipped,
        detail="" if ok else "exited 1",
        tail="output",
    )


def test_a_failed_step_fails_the_gate() -> None:
    result = GateResult(
        ok=True, commit="abc123", clone_path="/tmp/x", tracked_files=267,
        steps=[_step("make smoke", True), _step("make test", False)],
    )
    result.ok = all(s.ok for s in result.steps)
    assert result.ok is False
    assert "FAILED" in render(result)


def test_a_skipped_step_is_rendered_as_skipped_not_as_a_pass() -> None:
    """The failure this gate would otherwise commit itself.

    A clean clone has no extraction cache, so verify's re-derivation cannot
    run. Rendering that as OK would be a green gate for a check that did not
    happen -- exactly the thing the rest of this repository refuses to do.
    """
    skipped = _step("verify: re-derivation from cache", True, skipped=True)
    result = GateResult(
        ok=True, commit="abc123", clone_path="/tmp/x", tracked_files=267,
        steps=[_step("make smoke", True), skipped],
    )
    text = render(result)
    assert "SKIP  verify: re-derivation from cache" in text
    assert "PASSED" in text
    # The line for the skipped step must not read OK.
    line = next(l for l in text.splitlines() if "re-derivation" in l and "SKIP" in l)
    assert " OK " not in line


def test_the_artifact_records_every_step_and_its_provenance(tmp_path: Path) -> None:
    result = GateResult(
        ok=True, commit="abc123", clone_path="/tmp/x", tracked_files=267,
        steps=[_step("git clone", True), _step("make smoke", True)],
        notes=["267 tracked files in the clone"],
    )
    out = tmp_path / "clean_clone.json"
    write_artifact(result, out, {"git_commit": "abc123", "dirty": False})
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["provenance"]["git_commit"] == "abc123"
    assert payload["ok"] is True
    assert [s["name"] for s in payload["steps"]] == ["git clone", "make smoke"]
    assert payload["tracked_files"] == 267


def test_the_committed_gate_artifact_is_readable_and_passed() -> None:
    """The recorded run, if one has been committed.

    E.8 requires the gate's result to be recorded as an artifact. This asserts
    the committed record is a pass rather than a stale failure nobody looked at.
    """
    path = PROJECT_ROOT / "results" / "clean_clone.json"
    if not path.is_file():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["ok"] is True, (
        "results/clean_clone.json records a FAILED clean-clone gate. Fix the "
        "failure and re-run scripts/clean_clone_gate.py; do not commit a red gate."
    )
    assert payload["tracked_files"] > 200
    names = [s["name"] for s in payload["steps"]]
    for required in ("git clone", "make smoke", "make verify"):
        assert required in names, f"the recorded gate did not run {required!r}"


# --------------------------------------------------------------------------- #
# Tier reporting -- the gate must say which checks actually ran
# --------------------------------------------------------------------------- #


def test_each_verify_tier_gets_its_own_row() -> None:
    """Parsed from verify's contract, not from its prose."""
    from controlplane.report.clean_clone import _verify_tiers

    tail = (
        "TIER|1|claim_table|OK|31/31\n"
        "TIER|2|frozen_scores|OK|24/24\n"
        "TIER|3|activations|SKIPPED|0/0\n"
        "VERIFIED (activations tier skipped)"
    )
    rows = {r.name: r for r in _verify_tiers(tail)}
    assert len(rows) == 3
    assert not rows["verify: claim table vs artifacts"].skipped
    assert not rows["verify: metrics recomputed from frozen scores"].skipped
    assert rows["verify: scores re-derived from activations"].skipped
    assert "31/31" in rows["verify: claim table vs artifacts"].detail


def test_prose_alone_is_not_enough() -> None:
    """The regression this contract exists for.

    The first version grepped the human output. It worked until verify grew a
    third tier, at which point the claim-table line scrolled off the captured
    25-line tail and the gate reported a passing check as not having run. Prose
    that says the right thing must NOT be accepted without the contract line --
    otherwise the failure returns the next time the wording moves.
    """
    from controlplane.report.clean_clone import _verify_tiers

    prose_only = (
        "31/31 claims reproduce.\n"
        "24 comparisons reproduced bit-identically (recomputed from frozen scores).\n"
        "VERIFIED"
    )
    rows = _verify_tiers(prose_only)
    assert len(rows) == 1
    assert rows[0].ok is False
    assert "no TIER| lines" in rows[0].detail


def test_a_tier_missing_from_the_summary_is_not_counted_as_a_pass() -> None:
    """Absence means unknown, and unknown is not success."""
    from controlplane.report.clean_clone import _verify_tiers

    rows = {r.name: r for r in _verify_tiers("TIER|1|claim_table|OK|31/31")}
    assert not rows["verify: claim table vs artifacts"].skipped
    assert rows["verify: metrics recomputed from frozen scores"].skipped
    assert rows["verify: scores re-derived from activations"].skipped
    assert "absence means unknown" in rows[
        "verify: metrics recomputed from frozen scores"
    ].detail


def test_a_drifted_tier_fails_the_gate() -> None:
    """SKIPPED is tolerable; DRIFT is not."""
    from controlplane.report.clean_clone import _verify_tiers

    rows = {
        r.name: r
        for r in _verify_tiers(
            "TIER|1|claim_table|DRIFT|30/31\n"
            "TIER|2|frozen_scores|OK|24/24\n"
            "TIER|3|activations|SKIPPED|0/0"
        )
    }
    drifted = rows["verify: claim table vs artifacts"]
    assert drifted.ok is False
    assert "30/31" in drifted.detail


def test_all_three_tiers_running_is_reported_as_such() -> None:
    from controlplane.report.clean_clone import _verify_tiers

    tail = (
        "TIER|1|claim_table|OK|31/31\n"
        "TIER|2|frozen_scores|OK|24/24\n"
        "TIER|3|activations|OK|3/3"
    )
    assert not any(r.skipped for r in _verify_tiers(tail))


def test_a_failed_cleanup_is_reported_rather_than_swallowed(tmp_path: Path) -> None:
    """Two earlier runs each left 26 MB behind and said nothing.

    A cleanup reporting success without completing is a small version of what
    this gate exists to catch. The 2026-08-29 run surfaced a real
    PermissionError on a git pack file instead of hiding it.
    """
    from controlplane.report.clean_clone import _remove_clone

    victim = tmp_path / "clone"
    (victim / "inner").mkdir(parents=True)
    (victim / "inner" / "f.txt").write_text("x", encoding="utf-8")
    assert _remove_clone(victim) == ""
    assert not victim.exists()

    assert _remove_clone(tmp_path / "never-existed") == ""


# ------------------------------------------------------ DECISIONS 200: one named state

def _gate(commit: str = "a" * 40) -> GateResult:
    return GateResult(ok=True, commit=commit, clone_path="x", tracked_files=1,
                      steps=[_step("make smoke", True)])


def test_the_clone_must_be_the_commit_the_record_names() -> None:
    from controlplane.report.clean_clone import head_step

    assert head_step("a" * 40, "a" * 40).ok
    moved = head_step("a" * 40, "b" * 40)
    assert not moved.ok and "does not name" in moved.detail
    assert not head_step("", "").ok


def test_the_record_is_written_only_for_one_clean_unchanged_state() -> None:
    from controlplane.report.clean_clone import check_record

    commit = "a" * 40
    clean = {"git_commit": commit, "dirty": False}
    assert check_record(_gate(commit), clean, clean) is None
    assert "dirty when it was cloned" in check_record(_gate(commit), {**clean, "dirty": True}, clean)
    assert "moved while the gate started" in check_record(
        _gate(commit), {"git_commit": "c" * 40, "dirty": False}, clean)
    assert "changed during the run" in check_record(
        _gate(commit), clean, {"git_commit": "b" * 40, "dirty": False})
    assert "changed during the run" in check_record(_gate(commit), clean, {**clean, "dirty": True})


def test_the_script_refuses_to_write_when_the_source_moved(tmp_path, monkeypatch) -> None:
    """Wired, not just defined: a commit during the run leaves no artifact and exits 1."""
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "clean_clone_gate_script", PROJECT_ROOT / "scripts" / "clean_clone_gate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    commit = "a" * 40
    states = iter([{"git_commit": commit, "dirty": False}, {"git_commit": "b" * 40, "dirty": False}])
    monkeypatch.setattr(module, "provenance", lambda config: next(states))
    monkeypatch.setattr(module, "run_clean_clone_gate", lambda *a, **k: _gate(commit))
    out = tmp_path / "clean_clone.json"
    monkeypatch.setattr(sys, "argv", ["clean_clone_gate.py", "--out", str(out)])
    assert module.main() == 1
    assert not out.exists()

    states = iter([{"git_commit": commit, "dirty": False}, {"git_commit": commit, "dirty": False}])
    monkeypatch.setattr(module, "provenance", lambda config: next(states))
    assert module.main() == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["provenance"]["git_commit"] == commit
    assert record["provenance_taken"] == "before cloning"
