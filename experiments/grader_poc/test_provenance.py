"""Keep mixed Windows-worktree/Linux-clone provenance usable without trust overrides."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.grader_poc import run_trial


class GitProvenanceTests(unittest.TestCase):
    def test_wsl_native_checkout_uses_native_git(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            with patch.object(run_trial.sys, "platform", "linux"), \
                    patch.object(run_trial.platform, "release", return_value="microsoft-standard-WSL2"), \
                    patch.object(run_trial.subprocess, "check_output", return_value="revision\n") as call:
                self.assertEqual(run_trial.git_output(root, "rev-parse", "HEAD"), "revision")
            call.assert_called_once_with(
                ["git", "-c", "core.longpaths=true", "-C", str(root), "rev-parse", "HEAD"], text=True)

    def test_wsl_posix_worktree_keeps_native_git(self) -> None:
        for pointer in ("/tmp/repo/.git/worktrees/task", "../repo/.git/worktrees/task"):
            with self.subTest(pointer=pointer), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / ".git").write_bytes(f"gitdir: {pointer}\n".encode())
                with patch.object(run_trial.sys, "platform", "linux"), \
                        patch.object(run_trial.platform, "release", return_value="microsoft-standard-WSL2"), \
                        patch.object(run_trial.subprocess, "check_output", return_value="revision\n") as call:
                    self.assertEqual(run_trial.git_output(root, "rev-parse", "HEAD"), "revision")
                self.assertEqual(call.call_count, 1)
                self.assertEqual(call.call_args.args[0][0], "git")

    def test_wsl_windows_worktree_uses_translated_absolute_directory(self) -> None:
        for pointer in ("C:/repo/.git/worktrees/task", r"C:\repo\.git\worktrees\task",
                        r"\\server\share\repo\.git\worktrees\task"):
            with self.subTest(pointer=pointer), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / ".git").write_bytes(f"gitdir: {pointer}\n".encode())
                nested = root / "nested"
                nested.mkdir()
                translated = r"C:\worktree\nested"
                with patch.object(run_trial.sys, "platform", "linux"), \
                        patch.object(run_trial.platform, "release", return_value="microsoft-standard-WSL2"), \
                        patch.object(run_trial.subprocess, "check_output", side_effect=[translated + "\n", "revision\n"]) as call:
                    self.assertEqual(run_trial.git_output(nested, "rev-parse", "HEAD"), "revision")
                self.assertEqual(call.call_count, 2)
                self.assertEqual(call.call_args_list[0].args[0], ["wslpath", "-w", str(nested.resolve())])
                self.assertEqual(call.call_args.args[0],
                                 ["git.exe", "-c", "core.longpaths=true", "-C", translated, "rev-parse", "HEAD"])

    def test_non_wsl_platforms_use_default_git(self) -> None:
        for system, release in (("win32", "windows"), ("linux", "generic")):
            with self.subTest(system=system), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / ".git").write_bytes(b"gitdir: C:/repo/.git/worktrees/task\n")
                with patch.object(run_trial.sys, "platform", system), \
                        patch.object(run_trial.platform, "release", return_value=release), \
                        patch.object(run_trial.subprocess, "check_output", return_value="revision\n") as call:
                    self.assertEqual(run_trial.git_output(root, "rev-parse", "HEAD"), "revision")
                self.assertEqual(call.call_count, 1)
                self.assertEqual(call.call_args.args[0][0], "git")

    def test_native_git_failure_propagates_without_trust_override_or_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            error = subprocess.CalledProcessError(128, ["git", "status"], stderr="dubious ownership")
            with patch.object(run_trial.sys, "platform", "linux"), \
                    patch.object(run_trial.platform, "release", return_value="microsoft-standard-WSL2"), \
                    patch.object(run_trial.subprocess, "check_output", side_effect=error) as call:
                with self.assertRaises(subprocess.CalledProcessError) as caught:
                    run_trial.git_output(root, "status", "--porcelain")
            self.assertIs(caught.exception, error)
            self.assertEqual(call.call_count, 1)
            self.assertNotIn("safe.directory", " ".join(call.call_args.args[0]))


if __name__ == "__main__":
    unittest.main()
