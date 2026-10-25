"""Pinned-Harbor Docker adapter: label both agent and separate verifier resources.

Imported by the installed Harbor runtime, not the shipped Warrant CLI. The
inherited execution/verification logic is unchanged; only resource metadata,
managed names and built-image tags receive a per-run ownership namespace.
"""
from pathlib import Path

from harbor.environments.docker.docker import DockerEnvironment

from experiments.grader_poc.harbor_resources import ownership_overlay, save

import hashlib
import json


class OwnedDockerEnvironment(DockerEnvironment):
    """Use Harbor's environment extension point without editing upstream source."""

    def __init__(self, *args, warrant_owner: str, warrant_ledger: str, **kwargs):
        self._warrant_owner = warrant_owner
        self._warrant_ledger = Path(warrant_ledger)
        self._warrant_overlay = None
        policy = kwargs.get("network_policy")
        if policy is not None and policy.network_mode.value != "public":
            raise ValueError("Owned runner currently supports public network policy only")
        super().__init__(*args, **kwargs)
        if self._is_windows_container:
            raise ValueError("Owned runner supports Linux containers only")

    async def _run_docker_compose_command(self, command, **kwargs):
        if self._warrant_overlay is None:
            # At this point Harbor has resolved the build/prebuilt choice,
            # mounts and resource limits. `config` creates no daemon resources.
            resolved = await super()._run_docker_compose_command(["config", "--format", "json"])
            config = json.loads(resolved.stdout)
            overlay = ownership_overlay(config, self._warrant_owner, self.session_id)
            name = hashlib.sha256(self.session_id.encode()).hexdigest()[:16]
            path = self._warrant_ledger / (name + ".compose.json")
            save(path, overlay)
            save(self._warrant_ledger / (name + ".instance.json"), {
                "session_id": self.session_id, "environment_dir": str(self.environment_dir),
                "owner": self._warrant_owner, "overlay": path.name,
                "shared_images": {key: value.get("image") for key, value in config["services"].items()
                                  if not value.get("build")},
                "external_resources": {kind: {key: value.get("name", key) for key, value in config.get(kind, {}).items()
                                               if (value or {}).get("external")}
                                       for kind in ("networks", "volumes")}})
            self.extra_docker_compose_paths.append(path)
            self._warrant_overlay = path
        return await super()._run_docker_compose_command(command, **kwargs)
