"""`warrant chain verify`: what a kept set of chain records shows. DECISIONS.md 194.

Nothing on one machine stops a user forking a chain, restarting it or editing its
head sidecar. What can be done is to make those visible to whoever holds the
records, and these tests hold the verifier to each thing 194 says it flags --
built from real chain states, so a digest that verifies here is one the chain
itself would accept.
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.intake.chain import (
    ChainState,
    canonical_sha256,
    continue_chain,
    feed,
    start_chain,
)
from controlplane.intake.chain_verify import (
    RecordError,
    load_records,
    render_chain_verification,
    verify_chain_records,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WARRANT = {"status": "VALID", "budget_fpr": 0.05, "alpha": 0.05,
           "certification": {"threshold": 0.5}}


def _units(tag: str, n: int = 40, fired_every: int = 25):
    ids = [f"{tag}{i}" for i in range(n)]
    return ids, np.array([i % fired_every == 0 for i in range(n)])


def _start(tag="a", *, warrant=WARRANT, horizon=1000, head=None, fork=False):
    state = start_chain(warrant, horizon_units=horizon, alpha=0.05, head=head, fork=fork)
    return {"chain": feed(state, *_units(tag)).to_payload()}


def _next(previous, tag, *, warrant=WARRANT, head=None, fork=False):
    state = continue_chain(previous, warrant, alpha=0.05, head=head, fork=fork)
    return {"chain": feed(state, *_units(tag)).to_payload()}


def _kinds(records: dict) -> list[str]:
    return sorted(f.kind for f in verify_chain_records(records).findings)


def _restate(record, **changes):
    """A record whose chain state was rewritten and re-digested, as a splice would be."""
    state = dataclasses.replace(ChainState.from_payload(record["chain"]), **changes)
    return {"chain": state.to_payload()}


# --------------------------------------------------------------------------- #
# Each finding 194 names
# --------------------------------------------------------------------------- #


def test_a_linear_chain_verifies_clean() -> None:
    r1 = _start("a")
    r2 = _next(r1, "b")
    r3 = _next(r2, "c")
    verification = verify_chain_records({"r1": r1, "r2": r2, "r3": r3})
    assert verification.clean, verification.findings
    assert "CLEAN" in render_chain_verification(verification)


def test_a_fork_is_flagged_whatever_head_check_says() -> None:
    """The edited-sidecar bypass: the fork's record reads "matched"."""
    r1 = _start("a")
    r2 = _next(r1, "b")
    forged = _next(r1, "c", head=canonical_sha256(r1))  # the sidecar pointed back at r1
    assert forged["chain"]["head_check"] == "matched"
    findings = verify_chain_records({"r1": r1, "r2": r2, "fork": forged}).findings
    assert [f.kind for f in findings] == ["fork"]
    assert "none declared" in findings[0].detail


def test_a_declared_fork_is_still_reported_as_declared() -> None:
    r1 = _start("a")
    r2 = _next(r1, "b")
    declared = _next(r1, "c", head=canonical_sha256(r2), fork=True)
    assert declared["chain"]["head_check"] == "forked"
    findings = verify_chain_records({"r1": r1, "r2": r2, "fork": declared}).findings
    assert [f.kind for f in findings] == ["fork"]
    assert "1 declared" in findings[0].detail


def test_two_starts_for_one_warrant_are_a_restart() -> None:
    assert _kinds({"first": _start("a"), "again": _start("b")}) == ["restart"]


def test_a_link_whose_predecessor_is_not_in_the_set_is_a_missing_link() -> None:
    r1 = _start("a")
    assert _kinds({"r2": _next(r1, "b")}) == ["missing_link"]


def test_an_edited_statistic_does_not_reproduce_its_digest() -> None:
    r1 = _start("a")
    r2 = _next(r1, "b")
    r2["chain"]["statistics"][0] += 1.0
    assert _kinds({"r1": r1, "r2": r2}) == ["digest"]


def test_a_spliced_state_with_a_valid_digest_fails_extension() -> None:
    """Consumed units not extending the predecessor, re-digested so the digest passes."""
    r1 = _start("a")
    r2 = _next(r1, "b")
    digests = r2["chain"]["consumed_unit_digests"]
    spliced = _restate(r2, consumed_unit_digests=tuple(reversed(digests)))
    assert _kinds({"r1": r1, "r2": spliced}) == ["extension"]
    moved_horizon = _restate(r2, horizon_units=5000)
    findings = verify_chain_records({"r1": r1, "r2": moved_horizon}).findings
    assert [f.kind for f in findings] == ["extension"]
    assert "horizon_units" in findings[0].detail


def test_a_link_after_the_chain_ended_is_flagged() -> None:
    r1 = _start("a", horizon=40)  # consumes all 40 units: ended
    assert r1["chain"]["ended"]
    state = ChainState.from_payload(r1["chain"])
    after = {"chain": dataclasses.replace(
        state, sequence=2, previous_record_sha256=canonical_sha256(r1),
    ).to_payload()}
    assert "continued_after_end" in _kinds({"r1": r1, "after": after})


def test_a_misnumbered_link_is_a_sequence_finding() -> None:
    r1 = _start("a")
    r2 = _restate(_next(r1, "b"), sequence=5)
    assert _kinds({"r1": r1, "r2": r2}) == ["sequence"]


def test_records_from_two_warrants_are_flagged_and_each_group_still_verified() -> None:
    other = {**WARRANT, "budget_fpr": 0.04}
    o1 = _start("x", warrant=other)
    kinds = _kinds({"a1": _start("a"), "o1": o1, "o_again": _start("y", warrant=other)})
    assert kinds == ["mixed_warrants", "restart"]


def test_a_record_from_before_194_is_unrecorded_not_a_finding() -> None:
    r1 = _start("a")
    old = _restate(_next(r1, "b"), head_check=None, forked_from_head=None)
    assert "head_check" not in old["chain"]
    assert verify_chain_records({"r1": r1, "r2": old}).clean


def test_the_payload_says_what_cannot_be_checked() -> None:
    payload = verify_chain_records({"r1": _start("a")}).to_payload()
    assert payload["clean"] is True
    assert "labelled files" in payload["cannot_check"]
    render_chain_verification(verify_chain_records({"r1": _start("a")})).encode("ascii")


def test_unreadable_or_unchained_files_are_bad_input(tmp_path) -> None:
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "plain.json").write_text(json.dumps({"chain": None}), encoding="utf-8")
    for name in ("bad.json", "plain.json"):
        with pytest.raises(RecordError):
            load_records([tmp_path / name])


# --------------------------------------------------------------------------- #
# The command, end to end, on records the real CLI wrote
# --------------------------------------------------------------------------- #


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def _csv(path: Path, n: int, seed: int, prefix: str) -> Path:
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < 0.25).astype(int)
    scores = 1 / (1 + np.exp(-(rng.normal(0, 1, n) + 1.9 * labels)))
    path.write_text("id,label,score\n" + "".join(
        f"{prefix}{i},{l},{s:.6f}\n" for i, (l, s) in enumerate(zip(labels, scores, strict=True))),
        encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def forged_chain(tmp_path_factory):
    """The edited-sidecar bypass, through the real commands."""
    root = tmp_path_factory.mktemp("chain")
    warrant = root / "w.json"
    assert _run("certify", "-i", str(_csv(root / "base.csv", 1200, 11, "b")),
                "-b", "0.05", "-q", "-o", str(warrant)).returncode == 0
    assert _run("recheck", "-w", str(warrant), "-i", str(_csv(root / "a1.csv", 600, 1, "a1_")),
                "-q", "-o", str(root / "r1.json"), "--horizon-labels", "100000").returncode == 0
    assert _run("recheck", "-w", str(warrant), "-i", str(_csv(root / "a2.csv", 600, 2, "a2_")),
                "-q", "-o", str(root / "r2.json"), "--since", str(root / "r1.json")).returncode == 0
    sidecar = Path(str(warrant) + ".chain-head")
    head = json.loads(sidecar.read_text(encoding="utf-8"))
    head["head_record_sha256"] = canonical_sha256(
        json.loads((root / "r1.json").read_text(encoding="utf-8")))
    sidecar.write_text(json.dumps(head), encoding="utf-8")
    forged = _run("recheck", "-w", str(warrant), "-i", str(_csv(root / "a3.csv", 600, 3, "a3_")),
                  "-q", "-o", str(root / "fork.json"), "--since", str(root / "r1.json"))
    assert forged.returncode == 0, forged.stderr
    assert json.loads((root / "fork.json").read_text(encoding="utf-8"))["chain"]["head_check"] == "matched"
    return root


def test_the_cli_flags_the_forged_fork_and_exits_zero(forged_chain) -> None:
    out = forged_chain / "v.json"
    result = _run("chain", "verify", str(forged_chain / "r1.json"), str(forged_chain / "r2.json"),
                  str(forged_chain / "fork.json"), "-o", str(out))
    assert result.returncode == 0, result.stderr
    assert "[fork]" in result.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["clean"] is False
    assert [f["kind"] for f in payload["findings"]] == ["fork"]


def test_require_clean_turns_a_finding_into_exit_one(forged_chain) -> None:
    result = _run("chain", "verify", str(forged_chain / "r1.json"), str(forged_chain / "r2.json"),
                  str(forged_chain / "fork.json"), "-q", "-o", str(forged_chain / "v1.json"),
                  "--require-clean")
    assert result.returncode == 1
    assert "finding" in result.stderr
    clean = _run("chain", "verify", str(forged_chain / "r1.json"), str(forged_chain / "r2.json"),
                 "-q", "-o", str(forged_chain / "v2.json"), "--require-clean")
    assert clean.returncode == 0, clean.stdout


def test_the_cli_exits_two_on_a_file_that_is_not_a_chained_record(forged_chain) -> None:
    result = _run("chain", "verify", str(forged_chain / "w.json"), "-q",
                  "-o", str(forged_chain / "v3.json"))
    assert result.returncode == 2
    assert "not a chained recheck record" in result.stderr
    assert not (forged_chain / "v3.json").exists()


def test_one_record_under_two_paths_is_a_duplicate_not_a_fork(tmp_path) -> None:
    """Found in review: a backup copy beside the original read as an undeclared fork."""
    r1 = _start("a")
    r2 = _next(r1, "b")
    paths = []
    for name, record in (("r1.json", r1), ("r2.json", r2), ("r2 - backup.json", r2)):
        path = tmp_path / name
        path.write_text(json.dumps(record), encoding="utf-8")
        paths.append(path)
    findings = verify_chain_records(load_records(paths)).findings
    assert [f.kind for f in findings] == ["duplicate"]
    assert "2 paths" in findings[0].detail
    assert len(findings[0].records) == 2


def test_an_edited_record_orphans_its_successor_and_says_so() -> None:
    """Editing a record changes its own digest, so the link after it cannot be matched."""
    r1 = _start("a")
    r2 = _next(r1, "b")
    r1["chain"]["statistics"][0] += 1.0
    findings = {f.kind: f for f in verify_chain_records({"r1": r1, "r2": r2}).findings}
    assert set(findings) == {"digest", "missing_link"}
    assert "also reports a missing link" in findings["digest"].detail
