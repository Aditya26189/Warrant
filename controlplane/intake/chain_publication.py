"""Serialize local chain validation and publication, including recovery (206).

An exclusive output filename is insufficient: concurrent writers can otherwise
validate against the same head and publish different children. The OS lock spans
that entire decision. A sealed intent retains the exact prepared record through
process interruption, without recalculating a more favorable result on retry.

This coordinates cooperating processes on a supported local filesystem. It is
not distributed consensus or authentication, and cannot protect deleted history.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Optional

from ..config import Config, prepare_json_artifact
from ._atomic_files import json_bytes, sync_directory, write_json_atomic
from .chain import (
    ChainError, ChainState, FeedResult, canonical_sha256, continue_chain, feed,
    head_document, head_path, record_has_drift_revocation, seal_record,
    seal_reproduces, start_chain,
)
from .contract import ScoredItems
from .recheck import RecheckResult, apply_chain, chain_units, require_chain_replaced

__all__ = ["ChainPublication", "chain_publication", "publish_chained_recheck"]


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ChainError(f"cannot read chain publication input {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ChainError(f"{path} must contain a JSON object")
    return value


def _read_head(path: Path) -> Optional[dict[str, Any]]:
    if not os.path.lexists(path):
        return None
    value = _read_object(path)
    _validate_head(value)
    return value


def _validate_head(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise ChainError("publication head must be an object or null")
    digest, sequence = value.get("head_record_sha256"), value.get("sequence")
    if (not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            or type(sequence) is not int or sequence < 1):
        raise ChainError("publication head has an invalid digest or sequence")
    if "status" in value and (not isinstance(value["status"], str)
                              or value["status"] not in {"VALID", "STALE", "REVOKED", "UNVALIDATED"}):
        raise ChainError("publication head has an invalid status")


def _lock(stream: BinaryIO, *, release: bool = False) -> None:
    stream.seek(0)
    if os.name == "nt":
        import msvcrt

        # Windows permits locking a range beyond EOF, so the persistent lock
        # file can remain empty. Never delete its name while other users exist.
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK if release else msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(stream.fileno(), fcntl.LOCK_UN if release else fcntl.LOCK_EX | fcntl.LOCK_NB)


@dataclass
class ChainPublication:
    """A publication lease, usable only while its enclosing OS lock is held."""

    warrant_path: Path
    warrant_sha256: str
    head_before: Optional[dict[str, Any]]
    _active: bool = field(default=False, init=False)

    @property
    def intent_path(self) -> Path:
        """Retain pending evidence beside the warrant until its head is published."""
        return Path(str(self.warrant_path) + ".chain-pending")

    @property
    def head_digest(self) -> Optional[str]:
        """The single head snapshot used for both parent and status validation."""
        return None if self.head_before is None else self.head_before["head_record_sha256"]

    @property
    def head_status(self) -> Optional[str]:
        """Keep revocation checks on the same snapshot as the digest."""
        return None if self.head_before is None else self.head_before.get("status")

    def _check_warrant(self) -> None:
        if canonical_sha256(_read_object(self.warrant_path)) != self.warrant_sha256:
            raise ChainError("the warrant changed during chain publication; no new link was accepted")

    def _output_path(self, value: Path) -> Path:
        # Resolve directory aliases, but never follow an existing destination
        # symlink and accidentally create/replace its target instead.
        output = value.parent.resolve() / value.name
        reserved = {
            self.warrant_path, head_path(self.warrant_path), self.intent_path,
            Path(str(self.warrant_path) + ".chain-lock"),
        }
        if output in reserved:
            raise ChainError("a chain record cannot replace its warrant or operational sidecars")
        return output

    def _validate_intent(self, intent: dict[str, Any]) -> tuple[Path, dict[str, Any], dict[str, Any]]:
        try:
            if type(intent.get("schema_version")) is not int or intent["schema_version"] != 1:
                raise ChainError("unknown chain publication intent schema")
            if seal_reproduces(intent) is not True:
                raise ChainError("chain publication intent seal does not reproduce")
            if intent.get("warrant_sha256") != self.warrant_sha256:
                raise ChainError("pending publication belongs to a different warrant")
            raw_output, document = intent.get("output_path"), intent.get("record")
            if not isinstance(raw_output, str) or not Path(raw_output).is_absolute():
                raise ChainError("pending publication has no absolute output destination")
            output = self._output_path(Path(raw_output))
            if not isinstance(document, dict) or not isinstance(document.get("chain"), dict):
                raise ChainError("pending publication has no chained record")
            if seal_reproduces(document) is not True:
                raise ChainError("pending record seal does not reproduce")
            state = ChainState.from_payload(document["chain"])
            if state.warrant_sha256 != self.warrant_sha256:
                raise ChainError("pending chain state belongs to a different warrant")
            status = document.get("status")
            if not isinstance(status, str) or status not in {"VALID", "STALE", "REVOKED", "UNVALIDATED"}:
                raise ChainError("pending record has no valid aggregate status")
            if (state.revoked_at_unit is not None or record_has_drift_revocation(document)) and status != "REVOKED":
                raise ChainError("pending record hides a revocation")
            if "head_before" not in intent:
                raise ChainError("pending publication has no prior-head snapshot")
            _validate_head(intent["head_before"])
            next_head = head_document(canonical_sha256(document), state.sequence, status=status)
            return output, document, next_head
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            raise ChainError(f"invalid chain publication intent: {exc}") from exc

    def _complete(self, intent: dict[str, Any]) -> Path:
        output, document, next_head = self._validate_intent(intent)
        self._check_warrant()
        current = _read_head(head_path(self.warrant_path))
        if current != intent["head_before"] and current != next_head:
            raise ChainError("chain head changed outside the pending publication; retained intent was not applied")
        if os.path.lexists(output):
            if not output.is_file() or output.read_bytes() != json_bytes(document):
                raise ChainError(f"{output} conflicts with the pending record; nothing was replaced")
        else:
            write_json_atomic(output, document)
        # A crash after this atomic pointer update is safe to replay: both
        # current==head_before and current==next_head are explicitly accepted.
        write_json_atomic(head_path(self.warrant_path), next_head, replace=True)
        self.intent_path.unlink()
        sync_directory(self.intent_path.parent)
        self.head_before = next_head
        self._active = False
        return output

    def recover(self) -> Optional[Path]:
        """Finish only the original sealed publication; conflicting evidence stays intact."""
        if not self._active:
            raise ChainError("chain publication lease is no longer locked")
        if not os.path.lexists(self.intent_path):
            return None
        return self._complete(_read_object(self.intent_path))

    def publish(self, output: Path, document: dict[str, Any]) -> Path:
        """Commit one prepared record while retaining enough evidence for exact replay."""
        if not self._active:
            raise ChainError("chain publication lease is no longer locked")
        output = self._output_path(output)
        if os.path.lexists(output):
            raise FileExistsError(f"{output} already exists; a chained recheck never replaces evidence")
        self._check_warrant()
        if _read_head(head_path(self.warrant_path)) != self.head_before:
            raise ChainError("chain head changed during publication; no new link was accepted")
        intent = seal_record({
            "schema_version": 1, "warrant_sha256": self.warrant_sha256,
            "head_before": self.head_before, "output_path": str(output), "record": document,
        })
        self._validate_intent(intent)
        write_json_atomic(self.intent_path, intent)
        return self._complete(intent)


@contextmanager
def chain_publication(warrant_path: Path, warrant_record: dict[str, Any]) -> Iterator[ChainPublication]:
    """Hold the local warrant lock across validation, exact-record recovery and commit.

    Raises ChainError on contention or inconsistent recovery inputs. A recovered
    operation also exits explicitly so the caller can inspect and name that
    recovered record before attempting another link; it is never silently forked.
    """
    canonical = warrant_path.resolve()
    lock_path = Path(str(canonical) + ".chain-lock")
    try:
        stream = lock_path.open("a+b")
    except OSError as exc:
        raise ChainError(f"cannot open chain publication lock {lock_path}: {exc}") from exc
    with stream:
        try:
            _lock(stream)
        except OSError as exc:
            raise ChainError("chain publication is busy or its lock is unavailable; retry after the current writer exits") from exc
        publication = None
        try:
            publication = ChainPublication(canonical, canonical_sha256(warrant_record), _read_head(head_path(canonical)))
            publication._active = True
            publication._check_warrant()
            recovered = publication.recover()
            if recovered is not None:
                raise ChainError(
                    f"recovered interrupted chain publication at {recovered}; no additional link was started. "
                    "Inspect that record, then continue with --since on it if it is still eligible."
                )
            yield publication
        finally:
            if publication is not None:
                publication._active = False
            _lock(stream, release=True)


def publish_chained_recheck(
    config: Config, items: ScoredItems, warrant_record: dict[str, Any],
    warrant_path: Path, result: RecheckResult, *, horizon_units: Optional[int],
    since: Optional[Path], fork: bool, output: Optional[Path], input_path: Path,
) -> tuple[RecheckResult, FeedResult, Path]:
    """Validate the parent and publish its one accepted successor under one lease."""
    with chain_publication(warrant_path, warrant_record) as publication:
        alpha = warrant_record.get("alpha", 1.0 - config.validation.ci)
        if since is not None:
            if not since.is_file():
                raise ChainError(f"no recheck record at {since}")
            state = continue_chain(
                _read_object(since), warrant_record, alpha=alpha, fork=fork,
                head=publication.head_digest, head_status=publication.head_status,
            )
        else:
            if horizon_units is None:
                raise ChainError("a new chain requires --horizon-labels")
            state = start_chain(
                warrant_record, horizon_units=horizon_units, alpha=alpha, fork=fork,
                head=publication.head_digest, head_status=publication.head_status,
            )
        fed = feed(state, *chain_units(items, result.threshold))
        result = apply_chain(result, fed)
        require_chain_replaced(result)
        # items.source is a display label, not the original input location.
        out = output if output is not None else input_path.with_suffix(
            input_path.suffix + f".recheck-{fed.state.sequence:04d}.json"
        )
        document = prepare_json_artifact(
            {**result.to_payload(), "chain": fed.to_payload()}, config, seal_with=seal_record,
        )
        published = publication.publish(out, document)
    return result, fed, published
