"""Test source identity/date provenance and restricted bibliographic extraction."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fitz

import a04_evidence as e
import a04_recovery_sources as s


class SourceBindingChecks(unittest.TestCase):
    def setUp(self) -> None:
        parent = Path(e.git("rev-parse", "--show-toplevel")) / ".venv/a04-recovery-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        if not Path(self.temp.name).resolve().is_relative_to(parent.resolve()):
            raise ValueError("Unsafe test cleanup target")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "fixture.pdf"
        self.metadata = {"title": "Synthetic fixture for controlled source identity", "authors_raw": "Fixture Author",
                         "source": "arxiv", "updated": "2025-01-01T00:00:00Z", "year": "", "month": "",
                         "url": "https://arxiv.org/abs/2501.00001v1"}
        with fitz.open() as pdf:
            page = pdf.new_page()
            page.insert_text((60, 60), self.metadata["title"])
            self.path.write_bytes(pdf.tobytes())
        self.request = {"work_id": "arxiv:2501.00001", "review_id": "W0001", "member_id": "M0001",
                        "captured_version_id": "arxiv:2501.00001v1", "metadata_record_sha256": e.sha(e.encoded(self.metadata)),
                        "bibliography": {"published": "2025-01-01T00:00:00Z", "updated": "2025-01-01T00:00:00Z"},
                        "urls": ["https://arxiv.org/pdf/2501.00001v1"]}
        self.acquired = {"request_sha256": e.sha(e.encoded(self.request)), "body": {
            "raw_path": str(self.path), "url": self.request["urls"][0], "final_url": self.request["urls"][0],
            "kind": "PDF", "sha256": e.sha(self.path.read_bytes()),
            "version_state": "EXPLICIT_URL_ONLY_BODY_VERSION_UNCONFIRMED", "finished_utc": "2026-10-21T00:00:00Z", "status": 200}}

    def bind(self) -> dict:
        self.request["metadata_record_sha256"] = e.sha(e.encoded(self.metadata))
        self.acquired["request_sha256"] = e.sha(e.encoded(self.request))
        return s.source_binding(self.request, self.metadata, self.acquired)

    def test_versioned_url_and_identity_does_not_claim_an_internal_stamp(self) -> None:
        row = self.bind()
        self.assertTrue(row["method_release_supported"])
        self.assertFalse(row["body_exact_revision_self_identified"])
        self.assertTrue(row["body_title_matches_frozen_work"])
        self.assertIsNone(row["protocol_preferred_version"])
        self.assertIn("IN_BODY_REVISION_IDENTIFIER_NOT_FOUND", row["limitation_codes"])

    def test_different_work_title_remains_unresolved(self) -> None:
        self.metadata["title"] = "A different sufficiently long research identity"
        self.assertFalse(self.bind()["method_release_supported"])

    def test_post_cutoff_revision_cannot_release_methods(self) -> None:
        self.metadata["updated"] = "2026-10-18T00:00:00Z"
        self.assertFalse(self.bind()["method_release_supported"])

    def test_modified_body_or_request_commitment_rejected(self) -> None:
        self.path.write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError, "BODY_HASH_CHANGED"):
            self.bind()
        self.acquired["request_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "INPUT_COMMITMENT"):
            s.source_binding(self.request, self.metadata, self.acquired)

    def test_redirect_to_other_revision_is_rejected(self) -> None:
        self.acquired["body"]["final_url"] = "https://arxiv.org/pdf/2501.00001v2"
        with self.assertRaisesRegex(ValueError, "REDIRECT_MISMATCH"):
            self.bind()

    def test_missing_saved_final_url_is_explicit_not_fabricated(self) -> None:
        del self.acquired["body"]["final_url"]
        row = self.bind()
        self.assertIsNone(row["recorded_final_url"])
        self.assertIn("RECORDED_REQUEST_URL_WITHOUT_SAVED_FINAL_REDIRECT_FIELD", row["limitation_codes"])

    def test_official_anthology_id_and_month_does_not_become_arxiv_version(self) -> None:
        self.metadata.update(source="acl", updated="", year="2025", month="July", url="https://aclanthology.org/2025.fixture-1.1/")
        self.request.update(captured_version_id=None, urls=["https://aclanthology.org/2025.fixture-1.1.pdf"])
        self.acquired["body"].update(url=self.request["urls"][0], final_url=self.request["urls"][0])
        row = self.bind()
        self.assertTrue(row["method_release_supported"])
        self.assertEqual(row["captured_publication_date_interval"], ["2025-07-01", "2025-07-31"])
        self.assertFalse(row["body_exact_revision_self_identified"])
        self.assertIsNone(row["captured_version_id"])

    def test_anthology_ambiguous_cutoff_month_is_not_assumed_earlier(self) -> None:
        self.metadata.update(source="acl", updated="", year="2026", month="October", url="https://aclanthology.org/2026.fixture-1.1/")
        self.request.update(captured_version_id=None, urls=["https://aclanthology.org/2026.fixture-1.1.pdf"])
        self.acquired["body"].update(url=self.request["urls"][0], final_url=self.request["urls"][0])
        self.assertFalse(self.bind()["method_release_supported"])

    def test_missing_body_is_neutral_not_exclusion(self) -> None:
        self.acquired["body"] = None
        row = self.bind()
        self.assertFalse(row["method_release_supported"])
        self.assertIsNone(row["eligibility_decision"])


class BibliographyChecks(unittest.TestCase):
    def test_revision_dates_and_withdrawal_only(self) -> None:
        raw = b'<html><div class="submission-history">[v1] Mon, 28 Oct 2024 00:36:21 UTC (2139 KB) [v2] Thu, 7 Nov 2024 21:20:31 UTC (1 KB) (withdrawn)</div><p>We achieve 99% accuracy.</p></html>'
        row = s.bibliographic_fields(raw, "arxiv")
        self.assertEqual(len(row["revision_history"]), 2)
        self.assertTrue(row["revision_history"][1]["withdrawn_in_history"])
        encoded = e.encoded(row).decode()
        self.assertNotIn("accuracy", encoded)
        self.assertNotIn("2139", encoded)

    def test_titles_authors_and_abstracts_never_released_as_prose(self) -> None:
        raw = b'<html><meta name="citation_title" content="Superior accuracy and zero false positives"><meta name="citation_author" content="Named Person"><meta name="citation_publication_date" content="2025/07/01"><meta name="citation_doi" content="10.1000/fixture"><meta name="citation_abstract" content="We achieve the best results."></html>'
        row = s.bibliographic_fields(raw, "acl")
        self.assertEqual(row["linked_identifiers"], ["doi:10.1000/fixture"])
        for text in ("Superior", "Named Person", "best results", "false positives"):
            self.assertNotIn(text, e.encoded(row).decode())

    def test_unparseable_dates_stay_uncertain(self) -> None:
        row = s.bibliographic_fields(b'<html><meta name="citation_date" content="soon"></html>', "arxiv")
        self.assertIn("OFFICIAL_PUBLIC_DATE_NOT_ESTABLISHED", row["uncertainty_codes"])
        self.assertIsNone(s.month_interval("2026", "unknown"))

    def test_all_requested_members_are_preserved(self) -> None:
        requests, metadata = s.inputs()
        self.assertEqual(len(requests), 384)
        self.assertEqual(len(metadata), 384)
        self.assertEqual(len({r["work_id"] for r in requests}), 367)


if __name__ == "__main__":
    unittest.main(verbosity=2)
