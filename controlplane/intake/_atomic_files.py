"""Complete local files: immutable publication versus mutable pointers (206).

New evidence is linked into place without replacing an existing name. Mutable
pointers use replacement only after the new file is fully written and flushed.
These primitives need a supporting local filesystem; no racy fallback is used.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


def json_bytes(document: dict[str, Any]) -> bytes:
    """Keep the original prepared record's JSON representation during recovery."""
    return (json.dumps(document, indent=2, allow_nan=False) + "\n").encode("utf-8")


def sync_directory(path: Path) -> None:
    """Flush directory entries on POSIX; universal power-loss safety is not claimed."""
    if os.name != "posix":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_json_atomic(path: Path, document: dict[str, Any], *, replace: bool = False) -> None:
    """Publish complete JSON, preserving every preexisting name unless replacing a pointer.

    Hard-link creation cannot replace an existing destination. Keeping the
    temporary file in the destination directory avoids cross-filesystem moves.
    A filesystem without these operations raises rather than silently weakening
    the no-replacement contract. Callers serialize multi-file protocols separately.
    """
    content = json_bytes(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)
