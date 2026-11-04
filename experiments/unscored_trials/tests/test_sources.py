"""Defend retrieval evidence and bounded manifest execution without network I/O."""

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
from urllib.error import HTTPError, URLError

RESEARCH_MODULE_DIR = Path(__file__).resolve().parents[1]
if str(RESEARCH_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_MODULE_DIR))

import fetch_batch  # noqa: E402
import sources  # noqa: E402


class RetrievalEvidenceTests(unittest.TestCase):
    """An unavailable source must never become an empty observed population."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.destination = self.root / "input.json"
        self.url = "https://example.invalid/pinned/input.json"

    def _receipt_path(self, destination: Path | None = None) -> Path:
        target = self.destination if destination is None else destination
        return target.with_name(target.name + ".receipt.json")

    def _response(self, data: bytes) -> MagicMock:
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.url = self.url
        response.headers = {"Content-Length": str(len(data)), "Link": "next-page"}
        response.read.return_value = data
        return response

    def _write_cache(self, data: bytes, **overrides: object) -> dict:
        receipt = {
            "url": self.url,
            "status": "success",
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        receipt.update(overrides)
        self.destination.write_bytes(data)
        self._receipt_path().write_bytes(json.dumps(receipt).encode())
        return receipt

    def test_existing_payload_or_receipt_is_never_replaced(self) -> None:
        """A failed request receipt is evidence even when no payload exists."""
        for payload_exists, receipt_exists in ((True, False), (False, True), (True, True)):
            with self.subTest(payload=payload_exists, receipt=receipt_exists):
                destination = self.root / f"immutable-{payload_exists}-{receipt_exists}"
                receipt_path = self._receipt_path(destination)
                if payload_exists:
                    destination.write_bytes(b"original input")
                if receipt_exists:
                    receipt_path.write_bytes(b"original receipt")
                with patch.object(sources, "urlopen") as opener:
                    with self.assertRaises(FileExistsError):
                        sources.retrieve(self.url, destination, 100, 1)
                opener.assert_not_called()
                self.assertEqual(destination.exists(), payload_exists)
                self.assertEqual(receipt_path.exists(), receipt_exists)
                if payload_exists:
                    self.assertEqual(destination.read_bytes(), b"original input")
                if receipt_exists:
                    self.assertEqual(receipt_path.read_bytes(), b"original receipt")

    def test_success_at_byte_limit_binds_payload_and_request(self) -> None:
        response = self._response(b"data")
        with patch.object(sources, "urlopen", return_value=response) as opener:
            receipt = sources.retrieve(self.url, self.destination, 4, 2.5)
        response.read.assert_called_once_with(5)
        self.assertEqual(opener.call_args.kwargs["timeout"], 2.5)
        self.assertEqual(opener.call_args.args[0].full_url, self.url)
        self.assertEqual(self.destination.read_bytes(), b"data")
        self.assertEqual(receipt["status"], "success")
        self.assertEqual(receipt["url"], self.url)
        self.assertEqual(receipt["size_bytes"], 4)
        self.assertEqual(receipt["sha256"], hashlib.sha256(b"data").hexdigest())
        self.assertEqual(receipt, json.loads(self._receipt_path().read_bytes()))

    def test_oversized_response_uses_bounded_read_and_retains_failure(self) -> None:
        response = self._response(b"12345")
        with patch.object(sources, "urlopen", return_value=response):
            receipt = sources.retrieve(self.url, self.destination, 4, 1)
        response.read.assert_called_once_with(5)
        self.assertFalse(self.destination.exists())
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["error_type"], "ValueError")
        self.assertEqual(receipt["url"], self.url)
        self.assertNotIn("sha256", receipt)
        self.assertEqual(receipt, json.loads(self._receipt_path().read_bytes()))

    def test_network_http_and_timeout_failures_are_not_empty_successes(self) -> None:
        failures = (
            URLError("source unavailable"),
            HTTPError(self.url, 403, "Forbidden", None, None),
            TimeoutError("timed out"),
        )
        for index, error in enumerate(failures):
            with self.subTest(error=type(error).__name__):
                destination = self.root / f"failure-{index}.json"
                with patch.object(sources, "urlopen", side_effect=error):
                    receipt = sources.retrieve(self.url, destination, 20, 1)
                self.assertFalse(destination.exists())
                self.assertEqual(receipt["status"], "failed")
                self.assertEqual(receipt["url"], self.url)
                self.assertEqual(receipt["error_type"], type(error).__name__)
                self.assertNotIn("size_bytes", receipt)
                self.assertEqual(receipt, json.loads(self._receipt_path(destination).read_bytes()))

    def test_invalid_limits_fail_before_request_or_receipt(self) -> None:
        for limit, timeout in ((0, 1), (-1, 1), (1, 0), (1, -1)):
            with self.subTest(limit=limit, timeout=timeout):
                with patch.object(sources, "urlopen") as opener:
                    with self.assertRaises(ValueError):
                        sources.retrieve(self.url, self.destination, limit, timeout)
                opener.assert_not_called()
                self.assertFalse(self.destination.exists())
                self.assertFalse(self._receipt_path().exists())

    def test_cache_reuses_only_matching_success_without_request(self) -> None:
        expected = self._write_cache(b"data")
        with patch.object(sources, "urlopen") as opener:
            actual = sources.retrieve_cached(self.url, self.destination, 4, 1)
        self.assertEqual(actual, expected)
        opener.assert_not_called()

    def test_empty_success_and_failed_request_remain_distinct(self) -> None:
        response = self._response(b"")
        with patch.object(sources, "urlopen", return_value=response):
            empty = sources.retrieve(self.url, self.destination, 10, 1)
        self.assertEqual(empty["status"], "success")
        self.assertEqual(empty["size_bytes"], 0)
        self.assertTrue(self.destination.is_file())
        with patch.object(sources, "urlopen") as opener:
            self.assertEqual(sources.retrieve_cached(self.url, self.destination, 10, 1), empty)
        opener.assert_not_called()
        failed = self.root / "failed.json"
        failed_receipt = self._receipt_path(failed)
        failed_receipt.write_bytes(json.dumps({"status": "failed", "url": self.url}).encode())
        before = failed_receipt.read_bytes()
        with patch.object(sources, "urlopen") as opener:
            with self.assertRaises(ValueError):
                sources.retrieve_cached(self.url, failed, 10, 1)
        opener.assert_not_called()
        self.assertFalse(failed.exists())
        self.assertEqual(failed_receipt.read_bytes(), before)

    def test_cache_rejects_mismatched_url_without_overwriting(self) -> None:
        self._write_cache(b"data")
        before = self._receipt_path().read_bytes()
        with patch.object(sources, "urlopen") as opener:
            with self.assertRaises(ValueError):
                sources.retrieve_cached(self.url + "?other-revision", self.destination, 4, 1)
        opener.assert_not_called()
        self.assertEqual(self.destination.read_bytes(), b"data")
        self.assertEqual(self._receipt_path().read_bytes(), before)

    def test_cache_rejects_same_length_corruption(self) -> None:
        self._write_cache(b"data")
        self.destination.write_bytes(b"evil")
        with patch.object(sources, "urlopen") as opener:
            with self.assertRaises(ValueError):
                sources.retrieve_cached(self.url, self.destination, 4, 1)
        opener.assert_not_called()
        self.assertEqual(self.destination.read_bytes(), b"evil")

    def test_cache_rejects_inconsistent_size_and_stricter_limit(self) -> None:
        for recorded_size, limit in ((99, 100), (4, 3)):
            with self.subTest(recorded_size=recorded_size, limit=limit):
                self._write_cache(b"data", size_bytes=recorded_size)
                with patch.object(sources, "urlopen") as opener:
                    with self.assertRaises(ValueError):
                        sources.retrieve_cached(self.url, self.destination, limit, 1)
                opener.assert_not_called()

    def test_success_receipt_without_payload_is_not_retried(self) -> None:
        self._write_cache(b"data")
        self.destination.unlink()
        with patch.object(sources, "urlopen") as opener:
            with self.assertRaises(FileNotFoundError):
                sources.retrieve_cached(self.url, self.destination, 4, 1)
        opener.assert_not_called()
        self.assertTrue(self._receipt_path().exists())

    def test_malformed_cache_receipt_is_not_replaced(self) -> None:
        self._receipt_path().write_bytes(b"not json")
        with patch.object(sources, "urlopen") as opener:
            with self.assertRaises(json.JSONDecodeError):
                sources.retrieve_cached(self.url, self.destination, 4, 1)
        opener.assert_not_called()
        self.assertEqual(self._receipt_path().read_bytes(), b"not json")


class BatchManifestTests(unittest.TestCase):
    """Reject unsafe batches completely before any source is retrieved."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data_root = self.root / "data"
        self.manifest = self.root / "requests.json"

    def _request(self, path: str = "input.json", limit: int = 4) -> dict:
        return {"url": "https://example.invalid/pinned/" + path, "path": path,
                "limit_bytes": limit, "timeout": 1}

    def _write_manifest(self, rows: list[dict]) -> None:
        self.manifest.write_bytes(json.dumps(rows).encode())

    def test_parent_and_absolute_path_escape_are_rejected_before_fetch(self) -> None:
        for outside in ("../outside.json", str(self.root / "absolute.json")):
            with self.subTest(path=outside):
                self._write_manifest([self._request(), self._request(outside)])
                with patch.object(fetch_batch, "retrieve_cached") as retrieve:
                    with self.assertRaises(ValueError):
                        fetch_batch.run(self.manifest, self.data_root, 1, 8)
                retrieve.assert_not_called()
                self.assertFalse(self.data_root.exists())

    def test_duplicate_and_normalized_alias_destinations_are_rejected(self) -> None:
        for first, second in (("same.json", "same.json"),
                              ("nested/../same.json", "same.json")):
            with self.subTest(first=first, second=second):
                self._write_manifest([self._request(first), self._request(second)])
                with patch.object(fetch_batch, "retrieve_cached") as retrieve:
                    with self.assertRaises(ValueError):
                        fetch_batch.run(self.manifest, self.data_root, 1, 8)
                retrieve.assert_not_called()

    def test_invalid_request_limits_cannot_offset_budget_or_start_partial_batch(self) -> None:
        """Invalid rows must not subsidize another request or begin a partial run."""
        invalid_rows = (
            {"limit_bytes": -100},
            {"limit_bytes": 0},
            {"timeout": 0},
            {"timeout": -1},
        )
        for invalid in invalid_rows:
            with self.subTest(invalid=invalid):
                bad = {**self._request("bad.json"), **invalid}
                self._write_manifest([self._request("valid.json", 10), bad])
                with patch.object(fetch_batch, "retrieve_cached") as retrieve:
                    with self.assertRaises(ValueError):
                        fetch_batch.run(self.manifest, self.data_root, 1, 14)
                retrieve.assert_not_called()

    def test_worst_case_budget_counts_all_requested_limits_before_fetch(self) -> None:
        self._write_manifest([self._request("a.json", 5), self._request("b.json", 5)])
        with patch.object(fetch_batch, "retrieve_cached") as retrieve:
            with self.assertRaises(ValueError):
                fetch_batch.run(self.manifest, self.data_root, 2, 9)
        retrieve.assert_not_called()

    def test_invalid_worker_count_cannot_launch_requests(self) -> None:
        self._write_manifest([self._request()])
        for workers in (0, -1):
            with self.subTest(workers=workers):
                with patch.object(fetch_batch, "retrieve_cached") as retrieve:
                    with self.assertRaises(ValueError):
                        fetch_batch.run(self.manifest, self.data_root, workers, 4)
                retrieve.assert_not_called()

    def test_exact_budget_fetches_each_named_request_and_keeps_failure(self) -> None:
        rows = [self._request("a.json", 4), self._request("b.json", 6)]
        self._write_manifest(rows)
        success = {"status": "success", "size_bytes": 2, "url": rows[0]["url"]}
        failure = {"status": "failed", "error_type": "HTTPError", "url": rows[1]["url"]}
        with patch.object(fetch_batch, "retrieve_cached", side_effect=[success, failure]) as retrieve:
            with contextlib.redirect_stdout(io.StringIO()) as printed:
                receipts = fetch_batch.run(self.manifest, self.data_root, 1, 10)
        self.assertEqual(receipts, [{"path": "a.json", **success}, {"path": "b.json", **failure}])
        self.assertEqual(retrieve.call_count, 2)
        for call, row in zip(retrieve.call_args_list, rows, strict=True):
            self.assertEqual(call.args, (row["url"], self.data_root / row["path"],
                                         row["limit_bytes"], row["timeout"]))
        accounting = json.loads(printed.getvalue())
        self.assertEqual(accounting["requests"], 2)
        self.assertEqual(accounting["success"], 1)
        self.assertEqual(accounting["failed_paths"], ["b.json"])
        self.assertEqual(accounting["bytes"], 2)


if __name__ == "__main__":
    unittest.main()
