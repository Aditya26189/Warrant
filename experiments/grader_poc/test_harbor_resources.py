"""Ownership and failure-boundary regressions; no grader-effectiveness claims."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from experiments.grader_poc.harbor_resources import HarborResources, OWNER_LABEL, ownership_overlay
from experiments.grader_poc import run_trial

OWNER = "a" * 32


class OverlayTests(unittest.TestCase):
    def test_built_images_isolated_and_shared_resources_untouched(self):
        source = {"services": {"main": {"build": {"context": "."}}, "sidecar": {"image": "shared:tag"}},
                  "networks": {"default": {"name": "prior-name"}, "shared": {"external": True}},
                  "volumes": {"managed": {}, "shared": {"external": True}}}
        result = ownership_overlay(source, OWNER, "trial")
        self.assertEqual(result["services"]["main"]["build"]["labels"][OWNER_LABEL], OWNER)
        self.assertNotIn("image", result["services"]["sidecar"])
        self.assertNotIn("shared", result["volumes"])
        self.assertNotIn("shared", result["networks"])
        self.assertNotEqual(result["networks"]["default"]["name"], "prior-name")
        self.assertNotEqual(result, ownership_overlay(source, OWNER, "trial-verifier"))
        self.assertNotIn("labels", source["services"]["main"])

    def test_unsupported_topology_refused(self):
        for service in ({"container_name": "shared"}, {"privileged": True}, {"network_mode": "host"}):
            with self.subTest(service=service), self.assertRaises(ValueError):
                ownership_overlay({"services": {"main": service}}, OWNER, "trial")

    def test_invalid_identity_refused(self):
        with self.assertRaises(ValueError):
            ownership_overlay({"services": {}}, "anything", "trial")


class OwnershipTests(unittest.TestCase):
    def scope(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        scope = HarborResources(Path(temporary.name))
        scope.policy.update(settle_seconds=0, max_passes=3)
        return scope

    def snap(self, scope, occupied=False):
        return {"owned": {kind: ([{"id": kind + "-id", "labels": {OWNER_LABEL: scope.owner}}] if occupied else [])
                           for kind in ("container", "network", "volume", "image")}}

    def test_existing_identity_refuses_launch_and_cleanup(self):
        scope = self.scope()
        with patch.object(scope, "inventory", return_value=self.snap(scope, True)), self.assertRaises(ValueError):
            scope.prepare()
        with patch.object(scope, "command") as command:
            self.assertEqual(scope.cleanup(True)["status"], "NOT_ARMED")
        command.assert_not_called()

    def test_live_producer_refuses_removal(self):
        scope = self.scope(); scope.armed = True
        with patch.object(scope, "command") as command:
            self.assertEqual(scope.cleanup(False)["status"], "PRODUCER_NOT_STOPPED")
        command.assert_not_called()

    def test_changed_ownership_never_removed(self):
        scope = self.scope(); scope.armed = True
        with patch.object(scope, "inventory", return_value=self.snap(scope, True)), patch.object(
                scope, "inspect", return_value={"id": "foreign", "labels": {OWNER_LABEL: "foreign"}}), patch.object(
                scope, "command") as command:
            result = scope.cleanup(True)
        command.assert_not_called()
        self.assertFalse(result["verified_absent"])
        self.assertTrue(all(row["status"] == "OWNERSHIP_MISMATCH" for row in result["actions"]))

    def test_removal_rechecks_ids_and_requires_repeated_absence(self):
        scope = self.scope(); scope.armed = True
        with patch.object(scope, "inventory", side_effect=[self.snap(scope, True), self.snap(scope), self.snap(scope)]), patch.object(
                scope, "inspect", side_effect=lambda kind, ident: {"id": ident, "labels": {OWNER_LABEL: scope.owner}}), patch.object(
                scope, "command", return_value="removed") as command:
            result = scope.cleanup(True)
        self.assertTrue(result["verified_absent"])
        self.assertEqual(command.call_count, 4)
        self.assertEqual(command.call_args_list[0].args, ("container", "rm", "--force", "--volumes", "container-id"))
        self.assertNotIn("--force", command.call_args_list[-1].args)

    def test_successful_rm_without_absence_remains_failure(self):
        scope = self.scope(); scope.armed = True
        with patch.object(scope, "inventory", return_value=self.snap(scope, True)), patch.object(
                scope, "inspect", side_effect=lambda kind, ident: {"id": ident, "labels": {OWNER_LABEL: scope.owner}}), patch.object(
                scope, "command", return_value="removed"):
            self.assertFalse(scope.cleanup(True)["verified_absent"])

    def test_daemon_failure_retained_as_error(self):
        for error in (OSError("offline"), subprocess.TimeoutExpired("docker", 1), ValueError("bad JSON")):
            scope = self.scope(); scope.armed = True
            with self.subTest(error=error), patch.object(scope, "inventory", side_effect=error):
                result = scope.cleanup(True)
            self.assertFalse(result["verified_absent"])
            self.assertEqual(result["status"], "ERROR")
            self.assertEqual(result, json.loads((scope.path / "cleanup.json").read_bytes()))

    def test_removal_failure_remains_recorded_after_eventual_absence(self):
        scope = self.scope(); scope.armed = True
        with patch.object(scope, "inventory", side_effect=[self.snap(scope, True), self.snap(scope), self.snap(scope)]), patch.object(
                scope, "inspect", side_effect=lambda kind, ident: {"id": ident, "labels": {OWNER_LABEL: scope.owner}}), patch.object(
                scope, "command", side_effect=OSError("removal failed")):
            result = scope.cleanup(True)
        self.assertTrue(result["verified_absent"])
        self.assertTrue(all(row["status"] == "ERROR" for row in result["actions"]))


class ProcessGroupTests(unittest.TestCase):
    def test_parent_exit_does_not_leave_child_group_alive(self):
        process = Mock(pid=123)
        process.poll.return_value = 0
        with patch.object(run_trial.os, "name", "posix"), patch.object(run_trial.signal, "SIGKILL", 9, create=True), patch.object(run_trial.os, "killpg", create=True) as kill:
            result = run_trial.cancel_process(process, 1)
        kill.assert_called_once_with(123, 9)
        self.assertTrue(result["producer_stopped"])

    def test_failed_group_termination_not_declared_stopped(self):
        process = Mock(pid=123)
        process.poll.return_value = 0
        with patch.object(run_trial.os, "name", "posix"), patch.object(run_trial.signal, "SIGKILL", 9, create=True), patch.object(run_trial.os, "killpg", create=True, side_effect=OSError("denied")):
            result = run_trial.cancel_process(process, 1)
        self.assertFalse(result["producer_stopped"])


if __name__ == "__main__":
    unittest.main()
