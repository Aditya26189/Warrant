"""Keep approved integration history separate from new research scope."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_checkpoint as v


class IntegratedScopeTests(unittest.TestCase):
    """Integration must not waive frozen history or permit new runtime edits."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Scope Test")
        self.git("config", "user.email", "scope@example.invalid")
        self.frozen = "docs/research/fpr_reporting/b1/frozen.json"
        self.allowed = "docs/research/fpr_reporting/b1/a05-deep-evidence-20261024/new.json"
        self.write(self.frozen, b"original\n")
        self.original = self.commit()
        self.write("controlplane/approved.py", b"already_approved = True\n")
        self.checkpoint = "docs/research/fpr_reporting/b1/a05-deep-evidence-20261024/checkpoints/011/REPORT.md"
        self.write(self.checkpoint, b"frozen continuation\n")
        self.integration = self.commit()
        self.root_patch = patch.object(v, "ROOT", self.root)
        self.scope_patch = patch.object(v, "SCOPE_BASELINE", self.integration)
        self.root_patch.start()
        self.scope_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.scope_patch.stop)

    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=self.root, text=True).strip()

    def write(self, name: str, raw: bytes) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def commit(self) -> str:
        self.git("add", ".")
        self.git("commit", "-qm", "test checkpoint")
        return self.git("rev-parse", "HEAD")

    def test_approved_integration_allows_only_subsequent_research(self) -> None:
        self.write(self.allowed, b"new evidence\n")
        self.commit()
        self.assertEqual(v.scope_changes(), [self.allowed])

    def test_new_production_edit_is_rejected(self) -> None:
        self.write("controlplane/approved.py", b"new_runtime_change = True\n")
        self.commit()
        with self.assertRaisesRegex(ValueError, "OUT_OF_SCOPE_CHANGE"):
            v.scope_changes()

    def test_historical_research_path_is_not_new_scope(self) -> None:
        self.write(self.frozen, b"changed\n")
        self.commit()
        with self.assertRaisesRegex(ValueError, "OUT_OF_SCOPE_CHANGE"):
            v.scope_changes()

    def test_previous_continuation_artifact_cannot_be_rewritten(self) -> None:
        self.write(self.checkpoint, b"rewritten continuation\n")
        self.commit()
        with self.assertRaisesRegex(ValueError, "FROZEN_CONTINUATION_CHANGED"):
            v.scope_changes()

    def test_unrelated_history_cannot_reuse_the_scope_pin(self) -> None:
        self.git("checkout", "-q", "--detach", self.original)
        self.write(self.allowed, b"different branch\n")
        self.commit()
        with self.assertRaisesRegex(ValueError, "SCOPE_BASELINE_NOT_ANCESTOR"):
            v.scope_changes()

    def test_scope_pin_cannot_exempt_changed_frozen_bytes(self) -> None:
        self.write(self.frozen, b"changed in integration\n")
        integrated = self.commit()
        with patch.object(v, "SCOPE_BASELINE", integrated), patch.object(v.c, "BASELINE", self.original):
            with self.assertRaisesRegex(ValueError, "HISTORICAL_RESEARCH_CHANGED"):
                v.audit(self.root / "unused-checkpoint")


if __name__ == "__main__":
    unittest.main()
