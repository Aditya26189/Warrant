"""Bounded cleanup of explicitly owned Docker resources, never global pruning."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import threading
import time
import uuid

OWNER_LABEL = "warrant.grader.owner"
KINDS = ("container", "network", "volume", "image")


def save(path: Path, data: dict) -> None:
    """Retain cleanup progress before another daemon operation can fail."""
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes((json.dumps(data, indent=2) + "\n").encode())
    temporary.replace(path)


def ownership_overlay(config: dict, owner: str, session: str) -> dict:
    """Label the resolved Compose topology without rewriting task source.

    External resources and prebuilt images remain shared. Managed names and
    built-image tags are unique to this environment instance and invocation.
    """
    if not re.fullmatch(r"[0-9a-f]{32}", owner):
        raise ValueError("Invalid ownership identity")
    prefix = "warrant-" + owner + "-" + hashlib.sha256(session.encode()).hexdigest()[:12]
    result: dict = {"services": {}}
    for index, (name, service) in enumerate(sorted(config["services"].items())):
        if service.get("container_name"):
            raise ValueError("Explicit container_name is outside isolated runner scope")
        if service.get("privileged") or service.get("network_mode") == "host":
            raise ValueError("Privileged/host-network services are outside runner scope")
        item: dict = {"labels": {OWNER_LABEL: owner}}
        if service.get("build"):
            item.update(image=f"{prefix}-service-{index}", build={"labels": {OWNER_LABEL: owner}})
        result["services"][name] = item
    for kind in ("networks", "volumes"):
        for index, (name, definition) in enumerate(sorted(config.get(kind, {}).items())):
            definition = definition or {}
            if definition.get("external"):
                continue
            result.setdefault(kind, {})[name] = {
                "name": f"{prefix}-{kind}-{index}", "labels": {OWNER_LABEL: owner}}
    return result


@contextmanager
def defer_interrupt():
    """A second catchable SIGINT cannot cut short bounded cleanup/receipts."""
    active = os.name == "posix" and threading.current_thread() is threading.main_thread()
    previous = signal.signal(signal.SIGINT, signal.SIG_IGN) if active else None
    try:
        yield
    finally:
        if active:
            signal.signal(signal.SIGINT, previous)


class HarborResources:
    """A per-run ownership ledger with fail-closed discovery and removal."""

    def __init__(self, out: Path):
        self.owner = uuid.uuid4().hex
        self.path = out / "ownership"
        self.path.mkdir()
        self.policy = json.loads(Path(__file__).with_name("cleanup_policy.json").read_bytes())
        self.deadline: float | None = None
        self.armed = False
        self.record: dict = {"owner": self.owner, "label": OWNER_LABEL, "policy": self.policy,
                             "status": "UNVERIFIED", "verified_absent": False, "passes": [], "actions": []}
        self.persist()

    def persist(self) -> None:
        save(self.path / "cleanup.json", self.record)

    def command(self, *args: str) -> str:
        """Daemon errors and client timeouts cannot masquerade as absence."""
        timeout = self.policy["command_timeout_seconds"]
        if self.deadline is not None:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Cleanup deadline exhausted")
            timeout = min(timeout, remaining)
        return subprocess.run(["docker", *args], capture_output=True, text=True,
                              timeout=timeout, check=True).stdout.strip()

    def inspect(self, kind: str, ident: str) -> dict:
        values = json.loads(self.command(kind, "inspect", ident))
        if len(values) != 1 or not isinstance(values[0], dict):
            raise ValueError("Malformed Docker inspection")
        raw = values[0]
        labels = (raw.get("Config") or {}).get("Labels") if kind in ("container", "image") else raw.get("Labels")
        return {"id": raw.get("Id") or raw.get("Name"), "labels": labels or {},
                "name": raw.get("Name"), "running": (raw.get("State") or {}).get("Running"),
                "mounts": raw.get("Mounts", [])}

    def inventory(self) -> dict:
        """Only query this UUID; names and creation times alone confer no ownership."""
        found = {"at": datetime.now(timezone.utc).isoformat(), "owned": {}}
        for kind in KINDS:
            flags = ["--all"] if kind in ("container", "image") else []
            ids = sorted(set(self.command(kind, "ls", *flags, "--quiet", "--filter",
                                          f"label={OWNER_LABEL}={self.owner}").splitlines()))
            if len(ids) > self.policy["max_resources_per_kind"]:
                raise ValueError("Resource limit exceeded; manual inspection required")
            rows = [self.inspect(kind, ident) for ident in ids]
            if any(row["labels"].get(OWNER_LABEL) != self.owner for row in rows):
                raise ValueError("Docker label filter/inspection disagreement")
            found["owned"][kind] = rows
        return found

    def prepare(self) -> list[str]:
        """Prove no prior resource has this identity before allowing creation."""
        self.record["before"] = self.inventory()
        if any(self.record["before"]["owned"].values()):
            raise ValueError("Ownership identity already exists; refusing launch")
        self.armed = True
        self.record["status"] = "ARMED"
        self.persist()
        return ["--env", "experiments.grader_poc.harbor_environment:OwnedDockerEnvironment",
                "--ek", "warrant_owner=" + self.owner,
                "--ek", "warrant_ledger=" + str(self.path)]

    def cleanup(self, producer_stopped: bool) -> dict:
        """Remove exact owned IDs, preserving failures even if a retry succeeds."""
        self.deadline = time.monotonic() + self.policy["cleanup_timeout_seconds"]
        self.record["producer_stopped"] = producer_stopped
        if not self.armed or not producer_stopped:
            self.record["status"] = "NOT_ARMED" if not self.armed else "PRODUCER_NOT_STOPPED"
            self.persist()
            return self.record
        empty_passes = 0
        with defer_interrupt():
            try:
                for _ in range(self.policy["max_passes"]):
                    snapshot = self.inventory()
                    self.record["passes"].append(snapshot)
                    self.persist()
                    if not any(snapshot["owned"].values()):
                        empty_passes += 1
                        if empty_passes >= self.policy["required_empty_passes"]:
                            self.record.update(status="VERIFIED_ABSENT", verified_absent=True)
                            break
                    else:
                        empty_passes = 0
                        for kind in KINDS:
                            for row in snapshot["owned"][kind]:
                                action = {"kind": kind, "id": row["id"], "status": "PENDING"}
                                self.record["actions"].append(action)
                                self.persist()
                                try:
                                    current = self.inspect(kind, row["id"])
                                    if current["id"] != row["id"] or current["labels"].get(OWNER_LABEL) != self.owner:
                                        action["status"] = "OWNERSHIP_MISMATCH"
                                        continue
                                    flags = ["--force", "--volumes"] if kind == "container" else []
                                    action["output"] = self.command(kind, "rm", *flags, row["id"])
                                    action["status"] = "REMOVAL_REQUESTED"
                                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                                    action.update(status="ERROR", error=str(exc))
                                finally:
                                    self.persist()
                    time.sleep(min(self.policy["settle_seconds"], max(0, self.deadline - time.monotonic())))
                if not self.record["verified_absent"]:
                    self.record["status"] = "CLEANUP_INCOMPLETE"
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                self.record.update(status="ERROR", error=str(exc), verified_absent=False)
            finally:
                self.persist()
        return self.record
