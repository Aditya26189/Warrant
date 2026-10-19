"""Boundary, provenance and recovery tests for A04 source provision."""
from __future__ import annotations

import copy
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter

import a04_evidence as e


def html(text: str, heading: str = "3 Methods", parent: str | None = None) -> bytes:
    """Make a structured primary-source fixture, including an explicit self-link."""
    body = f'<section id="S3"><h2>{heading}</h2><p class="ltx_p">{text}</p></section>'
    if parent:
        body = f'<section id="S2"><h2>{parent}</h2>{body}</section>'
    return ('<html><head></head><body><a href="/abs/2501.00001v1">source</a>'
            '<article class="ltx_document">' + body + '</article></body></html>').encode()


class EvidenceChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.config = copy.deepcopy(e.read(e.CONFIG))
        parent = Path(e.git("rev-parse", "--show-toplevel")) / ".venv/a04-evidence-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=parent)
        if not Path(self.tmp.name).resolve().is_relative_to(parent.resolve()):
            raise ValueError("Unsafe test cleanup target")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config["cache_root"] = str(self.root)
        self.url = "https://arxiv.org/html/2501.00001v1"

    def test_frozen_frame_complete_and_blank(self) -> None:
        result = e.make_requests(self.config)
        self.assertEqual(len(result["works"]), 372)
        self.assertEqual(len(result["source_requests"]), 389)
        self.assertTrue(all(w["decision"] is None for w in result["works"]))
        self.assertNotIn("domain_eligibility", e.encoded(result).decode())

    def test_off_host_discovery_query_and_credentials_rejected(self) -> None:
        for url in ("https://evil.invalid/paper", "https://arxiv.org/api?search_query=x",
                    "https://user:pass@arxiv.org/html/2501.00001v1", "http://arxiv.org/pdf/x"):
            self.assertFalse(e.official_url(url, self.config))

    def test_primary_html_exact_version(self) -> None:
        self.assertEqual(e.validate_body(html("We use English data."), self.url),
                         ("HTML", "EXACT_VERSION_SELF_LINK"))

    def test_wrong_version_body_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "VERSION"):
            e.validate_body(html("We use English data."), self.url.replace("v1", "v2"))

    def test_truncated_html_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "TRUNCATED"):
            e.validate_body(html("We use English data.")[:-10], self.url)

    def test_challenge_html_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "NOT_STRUCTURED"):
            e.validate_body(b"<html><body>Verify browser</body></html>", self.url)

    def test_valid_pdf_distinct_from_verified_version(self) -> None:
        writer, stream = PdfWriter(), io.BytesIO()
        writer.add_blank_page(width=100, height=100)
        writer.write(stream)
        kind, version = e.validate_body(stream.getvalue(), self.url.replace("html", "pdf"))
        self.assertEqual(kind, "PDF")
        self.assertEqual(version, "EXPLICIT_URL_ONLY_BODY_VERSION_UNCONFIRMED")
        ev, _, _ = e.restrict(stream.getvalue(), "PDF", self.config)
        self.assertEqual(ev, [])

    def test_truncated_pdf_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "TRUNCATED_PDF"):
            e.validate_body(b"%PDF-1.7\nbroken", self.url)

    def test_complete_method_sentence_and_reconstruction(self) -> None:
        raw = html("We use English prompts for evaluation.")
        evidence, _, _ = e.restrict(raw, "HTML", self.config)
        self.assertEqual(len(evidence), 1)
        e.verify_quote(raw, evidence[0])

    def test_binary_procedure_is_not_an_eligibility_decision(self) -> None:
        evidence, _, _ = e.restrict(html("We classify input prompts as benign or malicious."), "HTML", self.config)
        self.assertEqual(len(evidence), 1)
        self.assertNotIn("decision", evidence[0])

    def test_numeric_and_qualitative_results_not_admitted(self) -> None:
        for prose in ("We achieve 99% accuracy.", "Our detector performs best.",
                      "False positives are negligible.", "We guarantee low error.",
                      "The method is superior to every baseline.", "We use three English examples.",
                      "The classifier labels no benign prompts as malicious."):
            self.assertIsNone(e.grammar(prose))
            self.assertEqual(e.restrict(html(prose), "HTML", self.config)[0], [])

    def test_mixed_outcome_paragraph_quarantined(self) -> None:
        raw = html("We use English prompts for evaluation. Our model achieves the best performance.")
        evidence, proposals, _ = e.restrict(raw, "HTML", self.config)
        self.assertFalse(evidence)
        self.assertTrue(proposals)

    def test_structural_ancestry_blocks_method_subsection_under_results(self) -> None:
        self.assertFalse(e.restrict(html("We use English data.", parent="4 Results"), "HTML", self.config)[0])

    def test_heading_requires_complete_allowlisted_label(self) -> None:
        self.assertFalse(e.restrict(html("We use English data.", heading="Our method beats others"), "HTML", self.config)[0])

    def test_table_and_figure_context_rejected(self) -> None:
        raw = html("We use English data.").replace(b'<p class="ltx_p">', b'<figure><p class="ltx_p">').replace(b'</p>', b'</p></figure>')
        self.assertFalse(e.restrict(raw, "HTML", self.config)[0])

    def test_abstract_context_rejected(self) -> None:
        raw = html("We use English data.").replace(b'<p class="ltx_p">', b'<div class="ltx_abstract"><p class="ltx_p">').replace(b'</p>', b'</p></div>')
        self.assertFalse(e.restrict(raw, "HTML", self.config)[0])

    def test_wrong_section_locator_rejected(self) -> None:
        raw = html("We use English data.")
        evidence = e.restrict(raw, "HTML", self.config)[0][0]
        evidence["section_id"] = "S7"
        with self.assertRaisesRegex(ValueError, "ATTRIBUTION"):
            e.verify_quote(raw, evidence)

    def test_incomplete_or_modified_quote_rejected(self) -> None:
        raw = html("We use English data.")
        evidence = e.restrict(raw, "HTML", self.config)[0][0]
        evidence["quote"] = "English data."
        with self.assertRaisesRegex(ValueError, "COMPLETE"):
            e.verify_quote(raw, evidence)

    def test_deterministic_processing_and_utf8(self) -> None:
        raw = html("We use English data. Café context.")
        self.assertEqual(e.encoded(e.restrict(raw, "HTML", self.config)), e.encoded(e.restrict(raw, "HTML", self.config)))
        self.assertNotIn(b"\\r", e.encoded({"x": "caf\u00e9"}))

    def test_atomic_interrupted_checkpoint_recovery(self) -> None:
        path = self.root / "receipt.json"
        partial = path.with_name(path.name + ".partial")
        partial.write_bytes(e.encoded({"key": "value"}))
        e.write_new(path, {"key": "value"})
        self.assertEqual(e.read(path), {"key": "value"})
        self.assertFalse(partial.exists())

    def test_mismatched_interrupted_checkpoint_preserved(self) -> None:
        path = self.root / "receipt.json"
        path.with_name(path.name + ".partial").write_bytes(b"interrupted")
        e.write_new(path, {"new": True})
        self.assertEqual(len(list(self.root.glob("receipt.json.interrupted-*"))), 1)

    def test_existing_receipt_cannot_be_overwritten(self) -> None:
        path = self.root / "receipt.json"
        e.write_new(path, {"value": 1})
        with self.assertRaises(FileExistsError):
            e.write_new(path, {"value": 2})

    def test_resumed_body_hash_mismatch_not_treated_as_complete(self) -> None:
        request = {"member_id": "M0001", "work_id": "arxiv:2501.00001", "urls": [self.url]}
        raw_path = self.root / "raw-source"
        raw_path.write_bytes(b"changed")
        e.write_new(self.root / "acquisition/M0001.json", {"request_sha256": e.sha(e.encoded(request)),
                    "body": {"raw_path": str(raw_path), "sha256": e.sha(b"old")}})
        with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
            e.acquisition(request, self.config, {}, "fixture")

    def test_dirty_tree_refused(self) -> None:
        with patch.object(e, "git", return_value=" M source.py"):
            with self.assertRaisesRegex(RuntimeError, "clean"):
                e.clean_head()

    def test_official_mirror_redirect_keeps_exact_version(self) -> None:
        request = {"member_id": "M0001", "work_id": "arxiv:2501.00001",
                   "urls": [self.url.replace("arxiv.org", "export.arxiv.org")]}
        response = io.BytesIO(html("We use English data."))
        response.url, response.status, response.headers = self.url, 200, {"Content-Type": "text/html"}
        self.config.update(minimum_request_interval_seconds=0, max_attempts_per_url=1)
        with patch.object(e.urllib.request, "urlopen", return_value=response):
            result = e.acquisition(request, self.config, {}, "fixture")
        self.assertTrue(result["source_available"])
        self.assertEqual(result["body"]["version_state"], "EXACT_VERSION_SELF_LINK")

    def test_redirect_to_another_version_not_accepted(self) -> None:
        request = {"member_id": "M0001", "work_id": "arxiv:2501.00001", "urls": [self.url]}
        response = io.BytesIO(html("We use English data."))
        response.url, response.status, response.headers = self.url.replace("v1", "v2"), 200, {}
        self.config.update(minimum_request_interval_seconds=0, max_attempts_per_url=1)
        with patch.object(e.urllib.request, "urlopen", return_value=response):
            result = e.acquisition(request, self.config, {}, "fixture")
        self.assertFalse(result["source_available"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
