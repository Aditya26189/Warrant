"""Durable messages and path ownership without a network service.

DECISIONS 198. JSON events are the source of truth. SQLite supplies only an
interprocess write mutex, preventing simultaneous posts from losing a page
update or acquiring overlapping path claims. Claims are advisory, not ACLs.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


KINDS = ("message", "status", "claim", "release")
STATES = ("working", "waiting", "blocked", "done")


def _agent(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,40}", value):
        raise ValueError("agent names must contain only letters, digits, dots, underscores or hyphens")
    return value.lower()


def _path(value: str) -> str:
    normalized = value.replace("\\", "/").rstrip("/")
    path = PurePosixPath(normalized)
    if not normalized or normalized != normalized.strip() or path.is_absolute() or any(p in ("..", ".") for p in normalized.split("/")):
        raise ValueError("claimed paths must be explicit repository-relative paths")
    if any(c in normalized for c in (":", "*", "?", "\n", "\r", "\t", "\0", "|", "`")):
        raise ValueError("claimed paths cannot contain drive letters, glob patterns or control markup")
    return str(path)


def _overlap(left: str, right: str) -> bool:
    a, b = left.casefold(), right.casefold()
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def read_events(root: Path, *, after: int = 0) -> list[dict[str, Any]]:
    """Read complete published posts; in-progress temporary files are excluded."""
    events = []
    for path in sorted((root / ".coordination" / "messages").glob("*.json")):
        event = json.loads(path.read_text(encoding="utf-8"))
        if event.get("schema_version") != 1 or event.get("kind") not in KINDS:
            raise ValueError(f"invalid coordination event: {path.name}")
        if event["sequence"] > after:
            events.append(event)
    return sorted(events, key=lambda e: e["sequence"])


def active_claims(events: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Replay ownership changes in publication order, never by wall-clock order."""
    claims: dict[str, list[str]] = {}
    for event in events:
        agent = event["agent"]
        if event["kind"] == "claim":
            claims[agent] = sorted(set(claims.get(agent, [])) | set(event["paths"]))
        elif event["kind"] == "release":
            paths = event["paths"]
            claims[agent] = [p for p in claims.get(agent, []) if paths and not any(
                p.casefold() == released.casefold() or p.casefold().startswith(released.casefold() + "/")
                for released in paths)]
    return {agent: paths for agent, paths in claims.items() if paths}


def _literal(text: str) -> str:
    runs = re.findall(r"`+", text)
    fence = "`" * max(3, 1 + max((len(run) for run in runs), default=0))
    return f"{fence}text\n{text}\n{fence}"


def render_board(events: list[dict[str, Any]], *, limit: int = 40) -> str:
    """Render literal messages with their authors and current declared ownership."""
    if limit < 1:
        raise ValueError("message limit must be positive")
    statuses = {e["agent"]: e for e in events if e["kind"] == "status"}
    agents = sorted({e["agent"] for e in events})
    lines = ["# Shared context: Codex and Claude", "",
             "Post through `python -m controlplane.coordination`; this page refreshes after each post.",
             "Read before editing. Messages are local posts, not an automatic connection to another session.",
             "No response is attributed to an agent until it actually posts.", "",
             "## Current status", ""]
    if not agents:
        lines.append("No sessions have posted yet.")
    for agent in agents:
        event = statuses.get(agent)
        lines.append(f"### {agent}")
        lines.append("")
        if event:
            lines.append(f"State: **{event['state']}** | Post {event['sequence']} | {event['timestamp']}")
            lines.extend(("", _literal(event["message"]), ""))
        else:
            lines.extend(("No status posted.", ""))
    lines.extend(("## Active path claims", "", "Claims coordinate work; they do not prevent uncoordinated filesystem edits.", ""))
    claims = active_claims(events)
    if not claims:
        lines.append("No active claims.")
    for agent, paths in sorted(claims.items()):
        lines.append(f"- **{agent}**: " + ", ".join(f"`{p}`" for p in paths))
    lines.extend(("", "## Conversation", ""))
    for event in events[-limit:]:
        target = f" to {event['to']}" if event["to"] else ""
        lines.extend((f"### {event['sequence']}: {event['agent']}{target} — {event['kind']}",
                      "", event["timestamp"], "", _literal(event["message"]), ""))
        if event["paths"]:
            lines.extend(("Paths: " + ", ".join(f"`{p}`" for p in event["paths"]), ""))
    lines.extend(("## How to participate", "", "```shell",
                  'python -m controlplane.coordination read',
                  'python -m controlplane.coordination post --agent claude --kind status --state working --message "My current task and next check"',
                  'python -m controlplane.coordination post --agent claude --kind claim --paths path/to/file --message "Taking ownership of this change"',
                  'python -m controlplane.coordination post --agent claude --to codex --kind message --message "Question or handoff"',
                  'python -m controlplane.coordination post --agent claude --kind release --paths path/to/file --message "Committed; path is free"',
                  "```", "", "Use `--message-file` for long messages. `read --after N --json` reads new posts.",
                  "Release without `--paths` frees all of that agent's claims. Check Git diffs before every edit and commit.",
                  "Do not switch the shared branch, reset or stash another session's work, or stage unrelated changes.",
                  "The complete history is in `.coordination/messages/`; this page shows recent posts.", ""))
    return "\n".join(lines)


def _atomic_write(path: Path, data: bytes) -> None:
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def post(root: Path, *, agent: str, kind: str, message: str,
         paths: list[str] | None = None, to: str | None = None,
         state: str | None = None) -> dict[str, Any]:
    """Publish one durable post and refresh the shared page under one mutex.

    A killed process releases its SQLite lock automatically. If it dies between
    publishing the JSON and rendering the page, `read` still sees the event and
    the next post/refresh rebuilds the page. Existing messages are never replaced.
    """
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("repository root does not exist")
    agent = _agent(agent)
    recipient = _agent(to) if to else None
    if kind not in KINDS or not message.strip():
        raise ValueError("a known kind and nonempty message are required")
    normalized = sorted(set(_path(p) for p in (paths or [])))
    if kind == "claim" and not normalized:
        raise ValueError("claim requires at least one path")
    if kind not in ("claim", "release") and normalized:
        raise ValueError("only claim/release posts take paths")
    if (kind == "status" and state not in STATES) or (kind != "status" and state is not None):
        raise ValueError("status posts require a state; other posts do not take one")
    directory = root / ".coordination"
    messages = directory / "messages"
    messages.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(directory / "write-lock.sqlite3", timeout=10)
    try:
        connection.execute("BEGIN IMMEDIATE")
        events = read_events(root)
        if kind == "claim":
            for owner, owned in active_claims(events).items():
                if owner != agent and any(_overlap(p, other) for p in normalized for other in owned):
                    raise ValueError(f"path claim overlaps work owned by {owner}; request a handoff first")
        if kind == "release":
            for owned in active_claims(events).get(agent, []):
                if any(p.casefold().startswith(owned.casefold() + "/") for p in normalized):
                    raise ValueError("release the whole directory claim before claiming a smaller scope")
        sequence = max((e["sequence"] for e in events), default=0) + 1
        event = {"schema_version": 1, "sequence": sequence, "id": uuid.uuid4().hex,
                 "timestamp": datetime.now(timezone.utc).isoformat(), "agent": agent,
                 "to": recipient, "kind": kind, "state": state,
                 "paths": normalized, "message": message.strip()}
        destination = messages / f"{sequence:08d}-{event['id']}.json"
        _atomic_write(destination, (json.dumps(event, indent=2, ensure_ascii=False) + "\n").encode())
        _atomic_write(root / "SHARED_CONTEXT.md", render_board([*events, event]).encode())
        connection.commit()
        return event
    finally:
        connection.close()


def refresh(root: Path) -> Path:
    """Rebuild the readable page from published events after an interrupted post."""
    directory = root.resolve() / ".coordination"
    directory.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(directory / "write-lock.sqlite3", timeout=10)
    try:
        connection.execute("BEGIN IMMEDIATE")
        path = root / "SHARED_CONTEXT.md"
        _atomic_write(path, render_board(read_events(root)).encode())
        connection.commit()
        return path
    finally:
        connection.close()
