"""Negative controls for reviewer-return custody and provenance checks."""
from __future__ import annotations

import hashlib
import io
import json
import unittest
import zipfile

import audit_returns as audit


def zipped(files: dict[str, bytes]) -> bytes:
    """Create tiny in-memory corruptions without changing received artifacts."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)
    return stream.getvalue()


class ReturnAuditChecks(unittest.TestCase):
    """Reject meaningful faults that an internally consistent index can hide."""

    def test_archive_path_escape_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "UNSAFE_ARCHIVE_ENTRY"):
            audit.archive(zipped({"../outside.json": b"{}"}))

    def test_expected_outer_digest_checked(self) -> None:
        with self.assertRaisesRegex(ValueError, "ARCHIVE_HASH_MISMATCH"):
            audit.archive(zipped({"inside.json": b"{}"}), "0" * 64)

    def test_payload_change_with_valid_zip_crc_is_rejected(self) -> None:
        manifest = {"files": {"inside.json": hashlib.sha256(b"original").hexdigest()}}
        files = audit.archive(zipped({"inside.json": b"changed", "manifest.json": json.dumps(manifest).encode()}))
        with self.assertRaisesRegex(ValueError, "MANIFEST_HASH"):
            audit.manifest_check(files, "manifest.json")

    def test_other_work_reference_is_not_accepted(self) -> None:
        row = {"review_id": "W0001", "work_id": "arxiv:work-a", "evidence_ids": ["E1"], "method_bibliographic_locators": []}
        issues = audit.reference_issues([row], {"E1": {"work_id": "arxiv:work-b"}})
        self.assertEqual(issues[0]["issue"], "UNKNOWN_OR_OTHER_WORK_REFERENCE")

    def test_changed_source_locator_is_detected(self) -> None:
        row = {"review_id": "W0001", "work_id": "work-a", "evidence_ids": ["E1"],
               "method_bibliographic_locators": [{"evidence_id": "E1", "version": "v2"}]}
        issues = audit.reference_issues([row], {"E1": {"work_id": "work-a", "version": "v1"}})
        self.assertEqual(issues[0]["issue"], "SOURCE_LOCATOR_MISMATCH")

    def test_first_submission_date_is_not_revision_date(self) -> None:
        row = {"review_id": "W0001", "selected_version_id": "arxiv:2406.00799v6", "version_date": "2024/06/02"}
        official = [{"review_id": "W0001", "official_fields": {"revision_history": [
            {"revision": "v1", "public_utc": "2024-06-02T16:53:21+00:00"},
            {"revision": "v6", "public_utc": "2025-03-06T17:43:10+00:00"}]}}]
        issues = audit.date_issues([row], official)
        self.assertEqual(issues[0]["official_revision_dates"], ["2025-03-06"])

    def test_month_only_record_does_not_establish_last_day(self) -> None:
        row = {"review_id": "W0001", "selected_version_id": "acl:2025.paper.1:publication", "version_date": "2025-08-31"}
        official = [{"review_id": "W0001", "provenance": {"source_url": "https://aclanthology.org/2025.paper.1/"},
                     "official_fields": {"publication_date_literals": [{"value": "2025-08"}]}}]
        issues = audit.date_issues([row], official)
        self.assertEqual(issues[0]["issue"], "DAY_PRECISION_NOT_SUPPORTED_BY_MONTH_ONLY_RECORD")

    def test_provider_flag_agreement_is_measured_without_eligibility(self) -> None:
        rows = [{"review_id": "W0001", "binary_evaluation": "MET"}]
        responses = [{"review_id": "W0001", "criterion_evidence": [
            {"criterion": "binary_evaluation", "further_controlled_evidence_needed": False}]}]
        result = audit.projection_comparison(rows, responses)
        self.assertEqual(result["matching_cells"], 1)
        self.assertNotIn("eligibility", result)


if __name__ == "__main__":
    unittest.main()
