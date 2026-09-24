"""One accepted local successor, including real process races and interruption (206)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest

from controlplane.intake.chain import (
    canonical_sha256, feed, head_path, read_head, seal_record, start_chain, write_head,
)
from controlplane.intake.chain_publication import ChainPublication, chain_publication
from controlplane.intake.chain import ChainError
from controlplane.intake.chain_verify import verify_chain_records

ROOT = Path(__file__).resolve().parents[1]


def _warrant(root):
    record = {"status": "VALID", "budget_fpr": .05, "alpha": .05,
              "input": {"grouped": False}, "certification": {"threshold": .5},
              "score_distribution": None}
    path = root / "warrant.json"
    path.write_bytes(json.dumps(record).encode())
    return path, record


def _record(warrant):
    state = start_chain(warrant, horizon_units=10000, alpha=.05)
    fed = feed(state, ["initial"], np.array([False]))
    return seal_record({"status": "VALID", "drift": {"verdict": "STABLE"}, "chain": fed.to_payload()})


def _scores(root, prefix):
    path = root / f"{prefix}.csv"
    rows = ["id,label,score"] + [
        f"{prefix}-{i},{int(i >= 80)},{.9 if i >= 80 else .1}" for i in range(100)
    ]
    path.write_bytes(("\n".join(rows) + "\n").encode())
    return path


def _env():
    return {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"}


def _wait_until(predicate, *, seconds=30):
    end = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() >= end:
            pytest.fail("timed out waiting for the synchronized test worker")
        time.sleep(.02)


def test_publication_requires_a_live_lease(tmp_path):
    path, warrant = _warrant(tmp_path)
    inactive = ChainPublication(path, canonical_sha256(warrant), None)
    with pytest.raises(ChainError, match="no longer locked"):
        inactive.publish(tmp_path / "bad.json", _record(warrant))
    with chain_publication(path, warrant) as publication:
        document = _record(warrant)
        publication.publish(tmp_path / "record.json", document)
        assert read_head(path) == canonical_sha256(document)
        with pytest.raises(ChainError, match="no longer locked"):
            publication.publish(tmp_path / "second.json", document)
    assert not (tmp_path / "second.json").exists()


def test_preexisting_output_is_not_replaced_or_registered_as_pending(tmp_path):
    path, warrant = _warrant(tmp_path)
    output = tmp_path / "record.json"
    output.write_bytes(b"existing evidence\n")
    with chain_publication(path, warrant) as publication:
        with pytest.raises(FileExistsError):
            publication.publish(output, _record(warrant))
        assert not publication.intent_path.exists()
    assert output.read_bytes() == b"existing evidence\n"
    assert not head_path(path).exists()


@pytest.mark.parametrize("stage", ["intent", "record", "head"])
def test_interrupted_publication_recovers_the_original_record(tmp_path, monkeypatch, stage):
    import controlplane.intake.chain_publication as module

    path, warrant = _warrant(tmp_path)
    output, document = tmp_path / "record.json", _record(warrant)
    original_write = module.write_json_atomic
    class Interrupted(RuntimeError):
        pass

    def interrupt(destination, content, **kwargs):
        original_write(destination, content, **kwargs)
        if ((stage == "intent" and str(destination).endswith(".chain-pending"))
                or (stage == "record" and destination == output)
                or (stage == "head" and destination == head_path(path))):
            raise Interrupted(stage)

    monkeypatch.setattr(module, "write_json_atomic", interrupt)
    with pytest.raises(Interrupted):
        with chain_publication(path, warrant) as publication:
            publication.publish(output, document)
    intent_path = Path(str(path) + ".chain-pending")
    assert intent_path.is_file()
    monkeypatch.setattr(module, "write_json_atomic", original_write)
    with pytest.raises(ChainError, match="recovered interrupted"):
        with chain_publication(path, warrant):
            pytest.fail("recovery must not silently accept another link")
    assert json.loads(output.read_bytes()) == document
    assert read_head(path) == canonical_sha256(document)
    assert not intent_path.exists()
    with chain_publication(path, warrant) as recovered:
        assert recovered.head_digest == canonical_sha256(document)


@pytest.mark.parametrize("changed", ["warrant", "head", "output", "intent"])
def test_recovery_refuses_conflicting_evidence(tmp_path, monkeypatch, changed):
    import controlplane.intake.chain_publication as module

    path, warrant = _warrant(tmp_path)
    output, document = tmp_path / "record.json", _record(warrant)
    original_write = module.write_json_atomic

    def interrupt(destination, content, **kwargs):
        original_write(destination, content, **kwargs)
        if str(destination).endswith(".chain-pending"):
            raise RuntimeError("stop after intent")

    monkeypatch.setattr(module, "write_json_atomic", interrupt)
    with pytest.raises(RuntimeError, match="stop after intent"):
        with chain_publication(path, warrant) as publication:
            publication.publish(output, document)
    monkeypatch.setattr(module, "write_json_atomic", original_write)
    intent = Path(str(path) + ".chain-pending")
    if changed == "warrant":
        warrant = {**warrant, "changed": True}
        path.write_bytes(json.dumps(warrant).encode())
    elif changed == "head":
        write_head(path, "f" * 64, 9, status="VALID")
    elif changed == "output":
        output.write_bytes(b"conflicting retained evidence\n")
    else:
        intent.write_bytes(b'{"schema_version": 1}\n')
    before = {p: p.read_bytes() for p in (intent, head_path(path), output) if p.exists()}
    with pytest.raises(ChainError):
        with chain_publication(path, warrant):
            pytest.fail("conflicting recovery inputs were accepted")
    assert all(p.read_bytes() == content for p, content in before.items())
    assert intent.exists()
    if changed != "output":
        assert not output.exists()


def test_warrant_mutation_during_the_lease_is_refused(tmp_path):
    path, warrant = _warrant(tmp_path)
    with chain_publication(path, warrant) as publication:
        path.write_bytes(json.dumps({**warrant, "changed": True}).encode())
        with pytest.raises(ChainError, match="warrant changed"):
            publication.publish(tmp_path / "record.json", _record(warrant))
        assert not publication.intent_path.exists()


RACE_WORKER = r'''
import sys, time
from pathlib import Path
import controlplane.intake.chain as chain
ready, release = map(Path, sys.argv[1:3])
def pause(function):
    def wrapped(*args, **kwargs):
        ready.write_text("parent and head read")
        end = time.monotonic() + 30
        while not release.exists():
            if time.monotonic() >= end:
                raise RuntimeError("test barrier was not released")
            time.sleep(.02)
        return function(*args, **kwargs)
    return wrapped
chain.start_chain = pause(chain.start_chain)
chain.continue_chain = pause(chain.continue_chain)
from controlplane.cli import main
raise SystemExit(main(sys.argv[3:]))
'''


@pytest.mark.parametrize("mode", ["start", "continue"])
def test_concurrent_cli_writers_cannot_accept_two_unforked_links(tmp_path, mode):
    """Force the old check/write window open; a second process must lose it."""
    path, warrant = _warrant(tmp_path)
    if mode == "continue":
        parent = tmp_path / "parent.json"
        with chain_publication(path, warrant) as publication:
            publication.publish(parent, _record(warrant))
        chain_args = ["--since", str(parent)]
    else:
        chain_args = ["--horizon-labels", "10000"]
    outputs = [tmp_path / f"{name}.json" for name in ("a", "b")]
    ready = [tmp_path / f"{name}.ready" for name in ("a", "b")]
    release = tmp_path / "release"
    processes = []
    try:
        for index, name in enumerate(("a", "b")):
            args = [sys.executable, "-c", RACE_WORKER, str(ready[index]), str(release),
                    "recheck", "-w", str(path), "-i", str(_scores(tmp_path, name)),
                    "-o", str(outputs[index]), "-q", *chain_args]
            processes.append(subprocess.Popen(args, cwd=ROOT, env=_env(), stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE, text=True,
                                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)))
            if index == 0:
                _wait_until(lambda: ready[0].exists() or processes[0].poll() is not None)
                assert ready[0].exists(), processes[0].communicate(timeout=5)
        _wait_until(lambda: ready[1].exists() or processes[1].poll() is not None)
        release.write_bytes(b"go")
        logs = [process.communicate(timeout=60) for process in processes]
        assert sorted(process.returncode for process in processes) == [0, 2], logs
        assert "busy" in logs[1][1] and not ready[1].exists(), logs
        assert outputs[0].exists() and not outputs[1].exists()
        first = json.loads(outputs[0].read_bytes())
        assert read_head(path) == canonical_sha256(first)
        records = {"winner": first}
        if mode == "continue":
            records["parent"] = json.loads(parent.read_bytes())
        assert verify_chain_records(records).clean
    finally:
        release.write_bytes(b"go")
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)


CRASH_WORKER = r'''
import os, sys
import controlplane.intake.chain_publication as publication
stage = sys.argv[1]
original = publication.write_json_atomic
def interrupt(path, document, **kwargs):
    original(path, document, **kwargs)
    is_intent = str(path).endswith(".chain-pending")
    is_head = str(path).endswith(".chain-head")
    if ((stage == "intent" and is_intent) or (stage == "head" and is_head)
            or (stage == "record" and not is_intent and not is_head)):
        os._exit(77)
publication.write_json_atomic = interrupt
from controlplane.cli import main
raise SystemExit(main(sys.argv[2:]))
'''


@pytest.mark.parametrize("stage", ["intent", "record", "head"])
def test_exited_writer_releases_lock_and_cli_recovers_exact_evidence(tmp_path, stage):
    path, _ = _warrant(tmp_path)
    output = tmp_path / "record.json"
    args = ["recheck", "-w", str(path), "-i", str(_scores(tmp_path, "first")),
            "-o", str(output), "--horizon-labels", "10000", "-q"]
    crashed = subprocess.run([sys.executable, "-c", CRASH_WORKER, stage, *args],
                             cwd=ROOT, env=_env(), capture_output=True, text=True, timeout=60)
    assert crashed.returncode == 77, crashed.stdout + crashed.stderr
    intent = Path(str(path) + ".chain-pending")
    pending = json.loads(intent.read_bytes())
    recovered = subprocess.run([sys.executable, str(ROOT / "warrant.py"), *args],
                               cwd=ROOT, env=_env(), capture_output=True, text=True, timeout=60)
    assert recovered.returncode == 2, recovered.stdout + recovered.stderr
    assert "recovered interrupted" in recovered.stderr
    assert json.loads(output.read_bytes()) == pending["record"]
    assert read_head(path) == canonical_sha256(pending["record"])
    assert not intent.exists()
    child = tmp_path / "next.json"
    continued = subprocess.run([
        sys.executable, str(ROOT / "warrant.py"), "recheck", "-w", str(path),
        "-i", str(_scores(tmp_path, "next")), "--since", str(output), "-o", str(child), "-q",
    ], cwd=ROOT, env=_env(), capture_output=True, text=True, timeout=60)
    assert continued.returncode == 0, continued.stdout + continued.stderr
    assert verify_chain_records({"parent": pending["record"], "child": json.loads(child.read_bytes())}).clean


@pytest.mark.parametrize("suffix", ["", ".chain-head", ".chain-pending", ".chain-lock"])
def test_record_cannot_replace_the_warrant_or_operational_state(tmp_path, suffix):
    path, warrant = _warrant(tmp_path)
    with chain_publication(path, warrant) as publication:
        with pytest.raises(ChainError, match="operational sidecars"):
            publication.publish(Path(str(path) + suffix), _record(warrant))
        assert not publication.intent_path.exists()
    assert json.loads(path.read_bytes()) == warrant
    assert not head_path(path).exists()


@pytest.mark.parametrize("bad_head", [[], {"sequence": 1},
    {"head_record_sha256": "a" * 64, "sequence": 1, "status": []}])
def test_malformed_head_is_preserved_and_does_not_hold_the_lock(tmp_path, bad_head):
    path, warrant = _warrant(tmp_path)
    head_path(path).write_bytes(json.dumps(bad_head).encode())
    with pytest.raises(ChainError):
        with chain_publication(path, warrant):
            pytest.fail("malformed head accepted")
    assert json.loads(head_path(path).read_bytes()) == bad_head
    head_path(path).unlink()  # Only this fixture's invalid pointer is removed.
    with chain_publication(path, warrant) as publication:
        publication.publish(tmp_path / "valid.json", _record(warrant))


def test_directory_aliases_share_the_canonical_warrant_lock(tmp_path):
    path, warrant = _warrant(tmp_path)
    child = tmp_path / "child"
    child.mkdir()
    alias = child / ".." / path.name
    with chain_publication(path, warrant):
        with pytest.raises(ChainError, match="busy"):
            with chain_publication(alias, warrant):
                pytest.fail("a path alias acquired a second publication lease")
    with chain_publication(alias, warrant) as publication:
        assert publication.warrant_path == path.resolve()
