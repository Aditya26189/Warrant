"""Failure-path regressions; these fixtures make no scientific grader claim."""

import argparse
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from experiments.grader_poc import container_lifecycle, diagnose, run_trial, trace_worker

CONFIG = json.loads(Path(__file__).with_name("config.json").read_bytes())


class ContainerTests(unittest.TestCase):
    def test_timeout_and_interruption_always_attempt_owned_cleanup(self):
        for error, status in ((subprocess.TimeoutExpired("start", 1, output=b"partial"), "TIMEOUT"),
                              (KeyboardInterrupt(), "INTERRUPTED")):
            with self.subTest(status=status), patch.object(container_lifecycle.subprocess, "run", side_effect=[
                    subprocess.CompletedProcess([], 0, "id\n", ""), error]), patch.object(
                    container_lifecycle, "remove_owned", return_value={"verified_absent": True}) as cleanup:
                result = container_lifecycle.run_owned([], "", 1, 1)
            self.assertEqual(result["status"], status)
            cleanup.assert_called_once_with(result["container_name"], result["owner"], 1)
            self.assertTrue(result["cleanup"]["verified_absent"])

    def test_creation_failure_still_checks_for_owned_resources(self):
        with patch.object(container_lifecycle.subprocess, "run", side_effect=OSError("daemon unavailable")), patch.object(
                container_lifecycle, "remove_owned", return_value={"verified_absent": False}) as cleanup:
            result = container_lifecycle.run_owned([], "", 1, 1)
        self.assertEqual(result["status"], "INFRASTRUCTURE_ERROR")
        cleanup.assert_called_once()

    def test_foreign_container_is_never_removed(self):
        foreign = {"Id": "foreign", "Config": {"Labels": {container_lifecycle.OWNER_LABEL: "someone-else"}}}
        with patch.object(container_lifecycle, "_inspect", return_value=foreign), patch.object(
                container_lifecycle.subprocess, "run") as command:
            result = container_lifecycle.remove_owned("name", "ours", 1)
        self.assertEqual(result["status"], "OWNERSHIP_MISMATCH")
        command.assert_not_called()

    def test_removal_requires_verified_absence(self):
        owned = {"Id": "ours", "Config": {"Labels": {container_lifecycle.OWNER_LABEL: "token"}}}
        for remaining in (owned, None):
            with self.subTest(remaining=remaining), patch.object(container_lifecycle, "_inspect", side_effect=[owned, remaining]), patch.object(
                    container_lifecycle.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "ours", "")):
                result = container_lifecycle.remove_owned("name", "token", 1)
            self.assertEqual(result["verified_absent"], remaining is None)

    def test_daemon_error_is_not_container_absence(self):
        with patch.object(container_lifecycle, "_inspect", side_effect=OSError("unreachable")):
            result = container_lifecycle.remove_owned("name", "token", 1)
        self.assertEqual(result["status"], "ERROR")
        self.assertFalse(result["verified_absent"])


class ProtocolTests(unittest.TestCase):
    def test_malformed_observations_cannot_be_counterexamples(self):
        for value in (None, [], {}, {"status": "OBSERVED"}, {"status": "OBSERVED", "sessions": [None]},
                      {"status": "OBSERVED", "sessions": [{"key": "k", "start": 0, "end": 1,
                       "aggregate": {"sum": 1, "count": True, "max": float("nan")}}]}):
            receipt = {"status": "COMPLETED", "stdout": json.dumps(value), "stderr": "", "exit_code": 0,
                       "cleanup": {"verified_absent": True}}
            with self.subTest(value=value), patch.object(diagnose, "run_owned", return_value=receipt):
                result = diagnose.observe(Path("app"), [], CONFIG)
            self.assertEqual(result["observation"]["status"], "ERROR")

    def test_cleanup_failure_invalidates_otherwise_valid_observation(self):
        receipt = {"status": "COMPLETED", "stdout": '{"status":"OBSERVED","sessions":[]}',
                   "stderr": "", "exit_code": 0, "cleanup": {"verified_absent": False}}
        with patch.object(diagnose, "run_owned", return_value=receipt):
            result = diagnose.observe(Path("app"), [], CONFIG)
        self.assertEqual(result["observation"]["status"], "ERROR")

    def test_nonzero_worker_exit_is_error(self):
        receipt = {"status": "COMPLETED", "stdout": '{"status":"OBSERVED","sessions":[]}',
                   "stderr": "crash", "exit_code": 1, "cleanup": {"verified_absent": True}}
        with patch.object(diagnose, "run_owned", return_value=receipt):
            result = diagnose.observe(Path("app"), [], CONFIG)
        self.assertEqual(result["observation"]["status"], "ERROR")

    def test_worker_converts_ordinary_application_errors(self):
        for error in (ValueError("bad payload"), RuntimeError("application failure")):
            output = io.StringIO()
            with self.subTest(error=error), patch.object(trace_worker.sys, "stdin", io.StringIO("{}")), patch.object(
                    trace_worker, "observe", side_effect=error), redirect_stdout(output):
                trace_worker.main()
            self.assertEqual(json.loads(output.getvalue())["status"], "ERROR")

    def test_worker_does_not_swallow_interrupt(self):
        with patch.object(trace_worker.sys, "stdin", io.StringIO("{}")), patch.object(
                trace_worker, "observe", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            trace_worker.main()


class TrialReceiptTests(unittest.TestCase):
    def fixture(self, mode, reward=1, mutate=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        task = root / "task"
        task.mkdir()
        (task / "task.txt").write_text("original")
        args = argparse.Namespace(task=task, out=root / "attempt", tb_repo=root / "tb", harbor_repo=root / "hb",
                                  harbor_bin=root / "harbor", name="test", agent="oracle", expected_reward=1, timeout=1)

        def git(directory, *argv):
            if "status" in argv:
                return ""
            return CONFIG["terminal_bench_commit"] if directory == args.tb_repo else (
                CONFIG["harbor_commit"] if directory == args.harbor_repo else "source")

        process = Mock()
        process.returncode = None
        process.poll.side_effect = lambda: process.returncode

        def wait(timeout):
            trial = args.out / "jobs/job/trial/result.json"
            trial.parent.mkdir(parents=True)
            body = {"trial_name": "trial", "verifier_result": {"rewards": {"reward": reward}}, "exception_info": None}
            if mode != "missing":
                trial.write_text("broken JSON" if mode == "malformed" else json.dumps(body))
            if mutate:
                (task / "task.txt").write_text("changed")
            if mode == "timeout":
                raise subprocess.TimeoutExpired("harbor", timeout)
            if mode == "interrupt":
                raise KeyboardInterrupt
            process.returncode = 3 if mode == "nonzero" else 0
            return process.returncode

        def cancel(proc, grace):
            proc.returncode = -2
            return {"forced": False, "delegated_resource_cleanup": "UNVERIFIED"}

        process.wait.side_effect = wait
        with patch.object(run_trial, "git_output", side_effect=git), patch.object(run_trial.subprocess, "Popen",
                side_effect=OSError("launch failed") if mode == "launch" else None, return_value=process), patch.object(
                run_trial, "cancel_process", side_effect=cancel):
            result = run_trial.run_trial(args)
        recorded = json.loads((args.out / "outcome.json").read_text())
        self.assertEqual(result, recorded)
        self.assertTrue((args.out / "invocation.json").exists())
        self.assertTrue((args.out / "command.log").exists())
        return result

    def test_timeout_preserves_partial_reward_without_promoting_it(self):
        result = self.fixture("timeout")
        self.assertEqual(result["status"], "TIMEOUT")
        self.assertEqual(result["trials"][0]["verifier_result"]["rewards"]["reward"], 1)
        self.assertNotIn("reward", result)
        self.assertIsNone(result["matches_expected"])

    def test_interrupt_writes_receipt(self):
        self.assertEqual(self.fixture("interrupt")["status"], "INTERRUPTED")

    def test_launch_failure_writes_receipt(self):
        self.assertEqual(self.fixture("launch")["status"], "INFRASTRUCTURE_ERROR")

    def test_missing_malformed_or_nonzero_results_cannot_complete(self):
        for mode in ("missing", "malformed", "nonzero"):
            with self.subTest(mode=mode):
                result = self.fixture(mode)
                self.assertEqual(result["status"], "INFRASTRUCTURE_ERROR")
                self.assertNotIn("reward", result)

    def test_reward_must_be_binary_number_not_boolean(self):
        for reward in (None, True, "1", 0.5, [], float("nan")):
            with self.subTest(reward=reward):
                self.assertEqual(self.fixture("normal", reward)["status"], "INFRASTRUCTURE_ERROR")

    def test_ordinary_binary_result_still_completes(self):
        for reward in (0, 1.0):
            with self.subTest(reward=reward):
                result = self.fixture("normal", reward)
                self.assertEqual(result["status"], "COMPLETED")
                self.assertEqual(result["reward"], reward)
                self.assertEqual(result["matches_expected"], reward == 1)

    def test_task_drift_blocks_completion(self):
        result = self.fixture("normal", mutate=True)
        self.assertFalse(result["task_unchanged"])
        self.assertEqual(result["status"], "INFRASTRUCTURE_ERROR")


class DiagnosticGateTests(unittest.TestCase):
    def fixture(self, mode):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)

        def artifact(run, task):
            return root / run.name, {"hashes": {}}

        def observer(app, events, config):
            if mode == "interrupt":
                return {"observation": {"status": "ERROR"}, "execution_status": "INTERRUPTED"}
            expected = diagnose.expected_sessions(events, config["initial_gap"], max_events=12)["sessions"]
            observed = copy.deepcopy(expected)
            if mode == "bad_control" and app.name == "omit-max-001":
                observed[0]["aggregate"]["max"] += 1
            if mode == "bad_control" and app.name == "reference-001":
                return {"observation": {"status": "ERROR"}, "execution_status": "COMPLETED"}
            return {"observation": {"status": "OBSERVED", "sessions": observed}, "execution_status": "COMPLETED"}

        with patch.object(diagnose, "git_output", side_effect=lambda root, *args: "" if "status" in args else "source"), patch.object(
                diagnose, "accepted_artifact", side_effect=artifact), patch.object(diagnose.subprocess, "check_output", return_value='[{"Id":"test-image"}]'), patch.object(
                diagnose, "observe", side_effect=observer) as observe, redirect_stdout(io.StringIO()):
            if mode == "unknown":
                with patch.object(diagnose, "expected_sessions", return_value={"status": "UNKNOWN", "sessions": None}):
                    result = diagnose.diagnose(root / "runs", root / "cases", root / "out")
                observe.assert_not_called()
            else:
                result = diagnose.diagnose(root / "runs", root / "cases", root / "out")
        self.assertEqual(result, json.loads((root / "out/outcome.json").read_text()))
        return result

    def test_unknown_abstains_without_executing_candidate(self):
        self.assertEqual(self.fixture("unknown")["status"], "UNKNOWN")

    def test_agreement_is_not_an_abstention(self):
        self.assertEqual(self.fixture("normal")["status"], "NO_COUNTEREXAMPLE_FOUND_IN_SCOPE")

    def test_interrupt_retains_attempt_and_stops(self):
        result = self.fixture("interrupt")
        self.assertEqual(result["status"], "INTERRUPTED")
        self.assertEqual(result["attempt_count"], 1)

    def test_failed_control_prevents_confirmation(self):
        self.assertEqual(self.fixture("bad_control")["status"], "INCONCLUSIVE")


class ArtifactBindingTests(unittest.TestCase):
    def test_tampered_task_or_app_is_rejected(self):
        for target in ("task", "app"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                task, run = root / "task", root / "run"
                source = task / "environment/app"
                app = run / "jobs/trial/artifacts/app/app"
                source.mkdir(parents=True)
                app.mkdir(parents=True)
                (source / "module.py").write_text("x = 1\n")
                (app / "module.py").write_text("x = 1\n")
                (run / "outcome.json").write_text(json.dumps({
                    "status": "COMPLETED", "reward": 1, "task_unchanged": True,
                    "task_hashes": run_trial.file_hashes(task), "trials": [{"path": "jobs/trial/result.json"}]}))
                ((source if target == "task" else app) / "module.py").write_text("x = 2\n")
                with self.assertRaises(ValueError):
                    diagnose.accepted_artifact(run, task)


if __name__ == "__main__":
    unittest.main()
