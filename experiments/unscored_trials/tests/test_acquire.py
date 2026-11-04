"""Mocked acquisition accounting, immutable evidence and resume regression tests."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import quote

RESEARCH_MODULE_DIR = Path(__file__).resolve().parents[1]
if not (RESEARCH_MODULE_DIR / "acquire.py").is_file():
    RESEARCH_MODULE_DIR = Path.cwd() / "experiments" / "unscored_trials"
if str(RESEARCH_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_MODULE_DIR))

import acquire  # noqa: E402
import fetch_batch  # noqa: E402
import sources  # noqa: E402


class AcquisitionTests(unittest.TestCase):
    """A completed marker cannot substitute for verified source coverage."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.config = {
            "dataset": "official/fixed", "revision": "abc123",
            "trial_limit_bytes": 4, "job_limit_bytes": 8,
            "request_timeout_seconds": 1, "workers": 1,
            "max_batch_requests": 2, "max_extra_attempts": 2,
            "max_download_bytes": 1000,
        }
        provenance = patch.object(acquire, "clean_provenance", return_value={"dirty": False, "git_commit": "fixture"})
        provenance.start()
        self.addCleanup(provenance.stop)
        self.new_requests: list[dict] = []

    def _row(self, index: int = 0) -> dict:
        source = f"submissions/terminal-bench/2.0/team/system/job/trial-{index}/result.json"
        url = (f'https://huggingface.co/datasets/{self.config["dataset"]}/raw/'
               f'{self.config["revision"]}/{quote(source, safe="/")}')
        return {"source_path": source, "path": f"results/source-{index}.json",
                "kind": "trial", "job": "submissions/terminal-bench/2.0/team/system/job",
                "submission": "team/system", "url": url, "limit_bytes": 4, "timeout": 1}

    def _write_json(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((json.dumps(value, indent=2) + "\n").encode())

    def _freeze(self, rows: list[dict]) -> bytes:
        manifest = self.data / "census-requests.json"
        self._write_json(manifest, rows)
        return manifest.read_bytes()

    def _receipt_path(self, row: dict) -> Path:
        return self.data / (row["path"] + ".receipt.json")

    def _success(self, row: dict, payload: bytes = b"ok") -> dict:
        target = self.data / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        receipt = {"url": row["url"], "status": "success", "size_bytes": len(payload),
                   "sha256": hashlib.sha256(payload).hexdigest(), "bytes_read": len(payload),
                   "limit_bytes": row["limit_bytes"]}
        self._write_json(self._receipt_path(row), receipt)
        return {"path": row["path"], **receipt}

    def _failure(self, row: dict, bytes_read: int | None = None) -> dict:
        receipt = {"url": row["url"], "status": "failed", "error_type": "URLError",
                   "limit_bytes": row["limit_bytes"]}
        if bytes_read is not None:
            receipt["bytes_read"] = bytes_read
        self._write_json(self._receipt_path(row), receipt)
        return {"path": row["path"], **receipt}

    def _mock_batch(self, manifest: Path, data: Path, workers: int, budget: int) -> list[dict]:
        self.assertEqual(data, self.data)
        self.assertGreater(workers, 0)
        self.assertGreaterEqual(budget, 0)
        receipts = []
        for row in json.loads(manifest.read_bytes()):
            if self._receipt_path(row).exists():
                receipt = sources.retrieve_cached(row["url"], data / row["path"],
                                                  row["limit_bytes"], row["timeout"])
                receipts.append({"path": row["path"], **receipt})
            else:
                self.new_requests.append(row)
                receipts.append(self._success(row))
        return receipts

    def _quiet_acquire(self, reserve: int = 0) -> dict:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return acquire.acquire(self.data, self.config, reserve)

    def test_prepared_manifest_is_immutable_and_resumes_full_source_coverage(self) -> None:
        rows = [self._row(index) for index in range(3)]
        with patch.object(acquire, "prepare", return_value=rows) as prepare:
            with patch.object(acquire, "run", side_effect=self._mock_batch):
                first = self._quiet_acquire()
                frozen = (self.data / "census-requests.json").read_bytes()
                receipt_bytes = {row["path"]: self._receipt_path(row).read_bytes() for row in rows}
                resumed = self._quiet_acquire()
        prepare.assert_called_once()
        self.assertEqual([row["source_path"] for row in first["requests"]],
                         [row["source_path"] for row in rows])
        self.assertEqual(first["requests"], resumed["requests"])
        self.assertEqual((self.data / "census-requests.json").read_bytes(), frozen)
        self.assertEqual(len(self.new_requests), 3)
        self.assertEqual(receipt_bytes, {row["path"]: self._receipt_path(row).read_bytes() for row in rows})

    def test_failed_sources_retain_separate_attempts_and_never_exceed_two_retries(self) -> None:
        row = self._row()
        self._freeze([row])

        def fail_batch(manifest: Path, data: Path, workers: int, budget: int) -> list[dict]:
            pending = json.loads(manifest.read_bytes())
            self.new_requests.extend(pending)
            return [self._failure(request) for request in pending]

        with patch.object(acquire, "run", side_effect=fail_batch):
            first = self._quiet_acquire()
            before = {path.relative_to(self.data).as_posix(): path.read_bytes()
                      for path in self.data.rglob("*.receipt.json")}
            resumed = self._quiet_acquire()
        self.assertEqual(len(self.new_requests), 3)
        self.assertEqual([request["path"] for request in self.new_requests],
                         [row["path"], "retry1/source-0.json", "retry2/source-0.json"])
        self.assertEqual(len(before), 3)
        self.assertTrue(all(json.loads(content)["status"] == "failed" for content in before.values()))
        self.assertEqual(before, {path.relative_to(self.data).as_posix(): path.read_bytes()
                                  for path in self.data.rglob("*.receipt.json")})
        self.assertEqual(first["requests"], resumed["requests"])
        self.assertEqual(first["requests"][0]["source_path"], row["source_path"])
        self.assertFalse((self.data / "retry3").exists())

    def test_failed_response_budget_uses_limit_plus_one_not_missing_size_zero(self) -> None:
        scored, oversized, denied = (self._row(index) for index in range(3))
        denied["limit_bytes"] = 9
        self._success(scored, b"123")
        self._failure(oversized, bytes_read=5)
        self._failure(denied, bytes_read=0)
        self.assertEqual(acquire.consumed_bytes(self.data), 3 + (4 + 1) + (9 + 1))

    def test_other_source_reserve_blocks_network_before_worst_case_overrun(self) -> None:
        self._freeze([self._row()])
        self.config["max_download_bytes"] = 15
        with patch.object(acquire, "run") as run:
            with self.assertRaises(ValueError):
                self._quiet_acquire(reserve=11)
        run.assert_not_called()
        with patch.object(acquire, "run", side_effect=self._mock_batch):
            completed = self._quiet_acquire(reserve=10)
        self.assertEqual(len(completed["requests"]), 1)
        self.assertEqual(completed["other_source_bytes_reserved"], 10)

    def test_adaptive_batches_preserve_population_under_same_total_ceiling(self) -> None:
        rows = [self._row(index) for index in range(2)]
        frozen = self._freeze(rows)
        self.config["max_download_bytes"] = 7
        with patch.object(acquire, "run", side_effect=self._mock_batch):
            result = self._quiet_acquire()
            resumed = self._quiet_acquire()
        self.assertEqual([row["source_path"] for row in result["requests"]],
                         [row["source_path"] for row in rows])
        self.assertEqual(result["requests"], resumed["requests"])
        self.assertEqual((self.data / "census-requests.json").read_bytes(), frozen)
        self.assertEqual(len(list((self.data / "acquisition").glob("*-completed.json"))), 2)
        self.assertEqual(len(self.new_requests), 2)
        self.assertLessEqual(acquire.consumed_bytes(self.data), 7)

    def test_negative_other_source_reserve_cannot_expand_budget(self) -> None:
        self._freeze([self._row()])
        with patch.object(acquire, "run") as run:
            with self.assertRaises(ValueError):
                self._quiet_acquire(reserve=-1)
        run.assert_not_called()

    def test_frozen_requests_reject_wrong_dataset_or_unexpected_source_url(self) -> None:
        row = self._row()
        urls = (row["url"].replace("official/fixed", "other/dataset"),
                f'https://unexpected.invalid/{self.config["revision"]}/file',
                row["url"] + "?revision=other")
        for url in urls:
            with self.subTest(url=url):
                altered = {**row, "url": url}
                before = self._freeze([altered])
                with patch.object(acquire, "run") as run:
                    with self.assertRaises(ValueError):
                        self._quiet_acquire()
                run.assert_not_called()
                self.assertEqual((self.data / "census-requests.json").read_bytes(), before)

    def test_changed_frozen_revision_is_rejected_without_refetch(self) -> None:
        row = self._row()
        row["url"] = row["url"].replace("abc123", "different-revision")
        self._freeze([row])
        with patch.object(acquire, "run") as run:
            with self.assertRaises(ValueError):
                self._quiet_acquire()
        run.assert_not_called()

    def test_pending_batch_hash_verifies_success_cache_through_real_fetch_batch(self) -> None:
        row = self._row()
        self._freeze([row])
        self._success(row)
        (self.data / row["path"]).write_bytes(b"NO")
        with patch.object(acquire, "run", side_effect=fetch_batch.run):
            with patch.object(sources, "urlopen") as network:
                with self.assertRaises(ValueError):
                    self._quiet_acquire()
        network.assert_not_called()
        self.assertFalse((self.data / "acquisition/batch-000-completed.json").exists())

    def test_completed_resume_does_not_bypass_success_cache_hash_verification(self) -> None:
        row = self._row()
        self._freeze([row])
        with patch.object(acquire, "run", side_effect=self._mock_batch):
            self._quiet_acquire()
        (self.data / row["path"]).write_bytes(b"NO")
        with patch.object(acquire, "run", side_effect=fetch_batch.run):
            with patch.object(sources, "urlopen") as network:
                with self.assertRaises(ValueError):
                    self._quiet_acquire()
        network.assert_not_called()

    def test_completed_marker_cannot_substitute_another_source(self) -> None:
        row = self._row()
        self._freeze([row])
        wrong = {**row, "source_path": "different/source/result.json"}
        self._write_json(self.data / "acquisition/batch-000-completed.json", [wrong])
        with patch.object(acquire, "run") as run:
            with self.assertRaises(ValueError):
                self._quiet_acquire()
        run.assert_not_called()

    def test_completed_marker_cannot_rebind_submission_for_same_source(self) -> None:
        row = self._row()
        self._freeze([row])
        self._success(row)
        wrong = {**row, "submission": "different/system"}
        self._write_json(self.data / "acquisition/batch-000-completed.json", [wrong])
        with patch.object(acquire, "run") as run:
            with self.assertRaises(ValueError):
                self._quiet_acquire()
        run.assert_not_called()

    def test_duplicate_frozen_source_and_incomplete_chunk_fail_before_fetch(self) -> None:
        row = self._row()
        self._freeze([row, {**row, "path": "results/duplicate.json"}])
        with patch.object(acquire, "run") as run:
            with self.assertRaises(ValueError):
                self._quiet_acquire()
        run.assert_not_called()
        self._freeze([row, self._row(1)])
        self._write_json(self.data / "acquisition/batch-000-completed.json", [row])
        with patch.object(acquire, "run") as run:
            with self.assertRaises(ValueError):
                self._quiet_acquire()
        run.assert_not_called()

    def test_all_completed_resume_still_enforces_total_budget(self) -> None:
        row = self._row()
        self._freeze([row])
        with patch.object(acquire, "run", side_effect=self._mock_batch):
            self._quiet_acquire()
        self.config["max_download_bytes"] = 1
        with patch.object(acquire, "run") as run:
            with self.assertRaises(ValueError):
                self._quiet_acquire()
        run.assert_not_called()

    def test_interrupted_chunk_resume_preserves_completed_source_coverage(self) -> None:
        rows = [self._row(index) for index in range(5)]
        self._freeze(rows)
        calls = 0

        def interrupted(manifest: Path, data: Path, workers: int, budget: int) -> list[dict]:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("simulated process interruption before second chunk")
            return self._mock_batch(manifest, data, workers, budget)

        with patch.object(acquire, "run", side_effect=interrupted):
            with self.assertRaises(RuntimeError):
                self._quiet_acquire()
        first_chunk = (self.data / "acquisition/batch-000-completed.json").read_bytes()
        with patch.object(acquire, "prepare") as prepare:
            with patch.object(acquire, "run", side_effect=self._mock_batch):
                resumed = self._quiet_acquire()
        prepare.assert_not_called()
        self.assertEqual(len(self.new_requests), 5)
        self.assertEqual((self.data / "acquisition/batch-000-completed.json").read_bytes(), first_chunk)
        self.assertEqual([row["source_path"] for row in resumed["requests"]],
                         [row["source_path"] for row in rows])

    def test_stored_failure_is_retained_then_successful_retry_uses_new_path(self) -> None:
        cached, failed = self._row(0), self._row(1)
        self._freeze([cached, failed])
        self._success(cached)
        self._failure(failed)
        original_failure = self._receipt_path(failed).read_bytes()
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b"ok"
        response.status = 200
        response.url = failed["url"]
        response.headers = {}
        with patch.object(acquire, "run", side_effect=fetch_batch.run):
            with patch.object(sources, "urlopen", return_value=response) as network:
                completed = self._quiet_acquire()
        network.assert_called_once()
        self.assertEqual(self._receipt_path(failed).read_bytes(), original_failure)
        self.assertFalse((self.data / failed["path"]).exists())
        self.assertEqual(completed["requests"][1]["path"], "retry1/source-1.json")
        self.assertEqual((self.data / "retry1/source-1.json").read_bytes(), b"ok")

    def test_prepare_rejects_inventory_dataset_or_revision_disagreement(self) -> None:
        for field in ("dataset", "revision"):
            with self.subTest(field=field):
                manifest = {"dataset": self.config["dataset"], "revision": self.config["revision"]}
                manifest[field] = "different"
                with patch.object(acquire, "build_inventory", return_value={"source_manifest": manifest}):
                    with self.assertRaises(ValueError):
                        acquire.prepare(self.data, self.config)

    def test_prepare_keeps_job_and_each_named_trial_but_not_config_files(self) -> None:
        job = "submissions/terminal-bench/2.0/team/system/job"
        tree = "metadata/job-tree.json"
        self._write_json(self.data / tree, [
            {"path": job + "/trial one", "type": "directory"},
            {"path": job + "/trial-two", "type": "directory"},
            {"path": job + "/config.json", "type": "file"},
        ])
        job_url = (f'https://huggingface.co/datasets/{self.config["dataset"]}/raw/'
                   f'{self.config["revision"]}/{job}/result.json')
        inventory = {"source_manifest": {"dataset": self.config["dataset"],
                     "revision": self.config["revision"], "sources": [
                         {"status": "success", "url": job_url, "local_path": "discovery/job.json"}]},
                     "jobs": [{"tree_source": tree, "source_path": job, "submission": "team/system"}]}
        with patch.object(acquire, "build_inventory", return_value=inventory):
            requests = acquire.prepare(self.data, self.config)
        self.assertEqual(len(requests), 3)
        self.assertEqual(sum(row["kind"] == "job" for row in requests), 1)
        job_request = next(row for row in requests if row["kind"] == "job")
        self.assertEqual(job_request["path"], "discovery/job.json")
        self.assertEqual({row["source_path"] for row in requests},
                         {job + "/result.json", job + "/trial one/result.json", job + "/trial-two/result.json"})
        self.assertTrue(any("trial%20one" in row["url"] for row in requests))


if __name__ == "__main__":
    unittest.main()
