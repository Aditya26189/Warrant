"""Shared-file coordination: concurrency, ownership and literal messages."""

import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import pytest

from controlplane.coordination.board import active_claims, post, read_events, refresh, render_board


def test_parallel_posts_survive_and_page_contains_every_message(tmp_path):
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(post, tmp_path, agent=f"agent-{i}", kind="message",
                               message=f"Concurrent message {i}") for i in range(12)]
        results = [f.result() for f in futures]
    assert sorted(e["sequence"] for e in results) == list(range(1, 13))
    assert len(read_events(tmp_path)) == 12
    page = (tmp_path / "SHARED_CONTEXT.md").read_text(encoding="utf-8")
    assert all(f"Concurrent message {i}" in page for i in range(12))


def test_separate_processes_publish_without_losing_updates(tmp_path):
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(post, tmp_path, agent=f"process-{i}", kind="message",
                               message=f"Process message {i}") for i in range(6)]
        results = [future.result(timeout=30) for future in futures]
    assert sorted(event["sequence"] for event in results) == list(range(1, 7))
    assert len(read_events(tmp_path)) == 6
    page = (tmp_path / "SHARED_CONTEXT.md").read_text(encoding="utf-8")
    assert all(f"Process message {i}" in page for i in range(6))


def test_published_event_survives_a_failed_page_update(tmp_path, monkeypatch):
    from controlplane.coordination import board

    original = board._atomic_write

    def fail_page(path, data):
        if path.name == "SHARED_CONTEXT.md":
            raise OSError("Simulated interrupted page update")
        original(path, data)

    monkeypatch.setattr(board, "_atomic_write", fail_page)
    with pytest.raises(OSError, match="interrupted page update"):
        post(tmp_path, agent="codex", kind="message", message="Durable first post")
    assert len(read_events(tmp_path)) == 1
    monkeypatch.setattr(board, "_atomic_write", original)
    second = post(tmp_path, agent="claude", kind="message", message="Recovered second post")
    assert second["sequence"] == 2
    assert "Durable first post" in (tmp_path / "SHARED_CONTEXT.md").read_text(encoding="utf-8")


def test_claims_cover_descendants_and_case_variants_then_release(tmp_path):
    post(tmp_path, agent="codex", kind="claim", paths=["controlplane/release"], message="Working")
    for path in ["controlplane", "ControlPlane/Release/cli.py", "controlplane/release"]:
        with pytest.raises(ValueError, match="owned by codex"):
            post(tmp_path, agent="claude", kind="claim", paths=[path], message="Conflict")
    assert len(read_events(tmp_path)) == 1
    post(tmp_path, agent="codex", kind="release", paths=["controlplane/release"], message="Ready")
    post(tmp_path, agent="claude", kind="claim", paths=["controlplane/release"], message="Taking over")
    assert active_claims(read_events(tmp_path)) == {"claude": ["controlplane/release"]}


def test_releasing_a_child_cannot_silently_free_its_parent_claim(tmp_path):
    post(tmp_path, agent="codex", kind="claim", paths=["controlplane/release"], message="Working")
    with pytest.raises(ValueError, match="whole directory claim"):
        post(tmp_path, agent="codex", kind="release", paths=["controlplane/release/cli.py"], message="Partial")
    assert active_claims(read_events(tmp_path)) == {"codex": ["controlplane/release"]}


def test_different_agents_cannot_acquire_the_same_claim_concurrently(tmp_path):
    def claim(agent):
        try:
            return post(tmp_path, agent=agent, kind="claim", paths=["shared.py"], message="Work")
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, ["codex", "claude"]))
    assert sum(result is not None for result in results) == 1
    assert len(read_events(tmp_path)) == 1


def test_messages_stay_literal_and_read_after_is_incremental(tmp_path):
    body = 'A message\n```\n<script>unsafe()</script>\n![image](https://example.invalid/a)'
    first = post(tmp_path, agent="codex", to="claude", kind="message", message=body)
    second = post(tmp_path, agent="claude", kind="status", state="working", message="Checking tests")
    assert read_events(tmp_path, after=first["sequence"]) == [second]
    page = render_board([first, second])
    assert "````text\n" + body + "\n````" in page
    assert "State: **working**" in page
    (tmp_path / "SHARED_CONTEXT.md").write_text("stale", encoding="utf-8")
    refresh(tmp_path)
    assert (tmp_path / "SHARED_CONTEXT.md").read_text(encoding="utf-8") == page


def test_cli_posts_then_reads_the_same_published_event(tmp_path):
    command = [sys.executable, "-m", "controlplane.coordination", "--root", str(tmp_path)]
    written = subprocess.run([*command, "post", "--agent", "codex", "--kind", "message",
                              "--message", "A real CLI post"], capture_output=True, text=True,
                             cwd=Path(__file__).resolve().parents[1], timeout=30)
    assert written.returncode == 0, written.stderr
    read = subprocess.run([*command, "read", "--json"], capture_output=True, text=True,
                          cwd=Path(__file__).resolve().parents[1], timeout=30)
    assert read.returncode == 0, read.stderr
    assert json.loads(read.stdout)[0]["message"] == "A real CLI post"


@pytest.mark.parametrize("path", ["../outside", "C:\\absolute", "/absolute", "controlplane/*"])
def test_claims_must_name_explicit_relative_paths(tmp_path, path):
    with pytest.raises(ValueError):
        post(tmp_path, agent="codex", kind="claim", paths=[path], message="Invalid path")
