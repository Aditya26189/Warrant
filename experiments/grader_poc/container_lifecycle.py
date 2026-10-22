"""Own one diagnostic container; a client timeout is not container termination."""

from __future__ import annotations

import json
import subprocess
import uuid

OWNER_LABEL = "warrant.grader_poc.owner"


def _inspect(name: str, timeout: float) -> dict | None:
    """Confirm absence through a successful daemon query, not an error string."""
    result = subprocess.run(["docker", "container", "ls", "-a", "--no-trunc",
                             "--filter", f"name=^/{name}$", "--format", "{{.ID}}"],
                            capture_output=True, text=True, timeout=timeout, check=True)
    if not result.stdout.strip():
        return None
    inspected = subprocess.run(["docker", "container", "inspect", name],
                               capture_output=True, text=True, timeout=timeout, check=True)
    items = json.loads(inspected.stdout)
    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
        raise ValueError("Malformed Docker inspection response")
    return items[0]


def remove_owned(name: str, owner: str, timeout: float) -> dict:
    """Remove only our labeled container and verify its absence; report failures."""
    try:
        item = _inspect(name, timeout)
        if item is None:
            return {"status": "ABSENT", "verified_absent": True}
        labels = (item.get("Config") or {}).get("Labels") or {}
        if labels.get(OWNER_LABEL) != owner:
            return {"status": "OWNERSHIP_MISMATCH", "verified_absent": False}
        container_id = item.get("Id")
        if not isinstance(container_id, str) or not container_id:
            raise ValueError("Missing owned container ID")
        result = subprocess.run(["docker", "container", "rm", "--force", container_id],
                                capture_output=True, text=True, timeout=timeout, check=False)
        absent = _inspect(name, timeout) is None
        return {"status": "REMOVED" if absent else "ERROR", "verified_absent": absent,
                "was_running": (item.get("State") or {}).get("Running"),
                "container_id": container_id, "exit_code": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except (OSError, subprocess.SubprocessError, ValueError, KeyboardInterrupt) as exc:
        return {"status": "ERROR", "verified_absent": False,
                "type": type(exc).__name__, "message": str(exc)}


def run_owned(arguments: list[str], payload: str, timeout: float, cleanup_timeout: float) -> dict:
    """Create before start so timeout cleanup targets a known owned identity.

    Catchable interruption becomes an explicit receipt after finally cleanup.
    The caller must stop its experiment on INTERRUPTED. Host death, SIGKILL, an
    unavailable daemon, or late daemon completion cannot guarantee removal.
    """
    owner = uuid.uuid4().hex
    name = "warrant-grader-" + owner
    record = {"container_name": name, "owner": owner, "status": "INFRASTRUCTURE_ERROR",
              "stdout": "", "stderr": "", "exit_code": None}
    try:
        created = subprocess.run(["docker", "create", "--name", name,
                                  "--label", f"{OWNER_LABEL}={owner}", *arguments],
                                 capture_output=True, text=True, timeout=timeout, check=False)
        record["create_exit_code"] = created.returncode
        record["create_stdout"], record["create_stderr"] = created.stdout, created.stderr
        if created.returncode != 0:
            record["reason"] = "container creation failed"
        else:
            record["container_id"] = created.stdout.strip()
            executed = subprocess.run(["docker", "start", "--attach", "--interactive", name],
                                      input=payload, capture_output=True, text=True,
                                      timeout=timeout, check=False)
            record.update(status="COMPLETED", exit_code=executed.returncode,
                          stdout=executed.stdout, stderr=executed.stderr)
    except subprocess.TimeoutExpired as exc:
        record.update(status="TIMEOUT", reason=str(exc))
        for field, value in (("stdout", exc.stdout), ("stderr", exc.stderr)):
            if value is not None:
                record[field] = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
    except KeyboardInterrupt:
        record.update(status="INTERRUPTED", reason="interrupted during diagnostic execution")
    except OSError as exc:
        record.update(reason=str(exc), error_type=type(exc).__name__)
    finally:
        record["cleanup"] = remove_owned(name, owner, cleanup_timeout)
    return record
