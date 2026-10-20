"""Test semantic return provenance and result-free release boundaries."""
from __future__ import annotations

import copy
import io
import json
import tempfile
import types
import unittest
import zipfile
from unittest import mock
from pathlib import Path

from bs4 import BeautifulSoup

import a04_evidence as e
import a04_semantic_release as s
from check_a04_evidence import html


class SemanticReleaseChecks(unittest.TestCase):
    def setUp(self) -> None:
        parent = Path(e.git("rev-parse", "--show-toplevel")) / ".venv/a04-semantic-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        if not Path(self.temp.name).resolve().is_relative_to(parent.resolve()):
            raise ValueError("Unsafe cleanup target")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = html("We classify input prompts as benign or malicious.")
        path = self.root / "raw.html"
        path.write_bytes(self.raw)
        self.body = {"raw_path": str(path), "sha256": e.sha(self.raw), "kind": "HTML",
                     "version_state": "EXACT_VERSION_SELF_LINK", "url": "https://arxiv.org/html/2501.00001v1"}
        p = BeautifulSoup(self.raw, "html.parser").select("p.ltx_p")[0]
        self.fact = {
            "fact_id": "TEST-F01", "member_id": "M0001", "fact_kind": "INPUT_TASK",
            "method_fact": "The classifier assigns benign or malicious labels to input prompts.",
            "source_url": self.body["url"], "version": "arxiv:2501.00001v1",
            "raw_source_sha256": self.body["sha256"],
            "locator": {"format": "HTML", "evidence_paragraphs": [{"global_p_ltx_p_ordinal": 0,
                "section_id": "S3", "paragraph_text_sha256": e.sha(p.get_text(" ", strip=True).encode())}]},
            "restriction_checked_by": s.ACTORS["01"], "checked_utc": "2026-10-19T22:00:00+00:00",
            "limitation": "Language and timing are unresolved.",
            "second_local_semantic_pass": {"actor_id": s.ACTORS["01"], "status": "CHECKED", "literal_quotation_words": 0,
                                           "checked_utc": "2026-10-19T22:00:00+00:00"},
        }
        self.record = {"actor_id": s.ACTORS["01"]}
        self.request = {"member_id": "M0001", "captured_version_id": "arxiv:2501.00001v1"}

    def codes(self, fact: dict | None = None, body: dict | None = None) -> list[str]:
        return s.validate_fact(fact or self.fact, self.record, self.request, body or self.body)

    def test_source_supported_method_record_passes(self) -> None:
        self.assertEqual(self.codes(), [])

    def test_operational_assignments_cover_frame_once(self) -> None:
        counts = {key: 0 for key in s.ACTORS}
        for n in range(1, 373):
            counts[s.owner(f"W{n:04d}")] += 1
        self.assertEqual(counts, {"01": 129, "02": 124, "03": 119})
        self.assertEqual(s.owner("W0336"), "03")

    def test_result_or_sample_counts_rejected(self) -> None:
        for text in ("The detector achieves excellent accuracy.", "We observed zero false positives.",
                     "There are ten benign examples.", "The setup uses 500 samples.",
                     "The method guarantees low error."):
            fact = {**self.fact, "method_fact": text}
            self.assertTrue(self.codes(fact))

    def test_exact_role_disclaimer_is_not_a_paper_claim(self) -> None:
        self.assertFalse(self.codes({**self.fact, "limitation": s.SAFE_LIMITATION}))
        self.assertTrue(self.codes({**self.fact, "method_fact": s.SAFE_LIMITATION}))

    def test_no_fabricated_checker_or_pass(self) -> None:
        self.assertTrue(self.codes({**self.fact, "restriction_checked_by": "FAKE_HUMAN"}))
        self.assertTrue(self.codes({**self.fact, "second_local_semantic_pass": {}}))

    def test_different_source_version_or_body_rejected(self) -> None:
        self.assertTrue(self.codes({**self.fact, "version": "arxiv:2501.00001v2"}))
        self.assertTrue(self.codes({**self.fact, "raw_source_sha256": "0" * 64}))

    def test_unverified_pdf_is_not_method_evidence(self) -> None:
        body = {**self.body, "kind": "PDF", "version_state": "EXPLICIT_URL_ONLY_BODY_VERSION_UNCONFIRMED"}
        self.assertTrue(self.codes(body=body))

    def test_incorrect_paragraph_or_section_is_rejected(self) -> None:
        fact = copy.deepcopy(self.fact)
        fact["locator"]["evidence_paragraphs"][0]["section_id"] = "S99"
        self.assertTrue(self.codes(fact))
        fact["locator"]["evidence_paragraphs"][0]["global_p_ltx_p_ordinal"] = 100
        self.assertTrue(self.codes(fact))

    def test_source_hash_is_rechecked(self) -> None:
        s.paragraph_index.cache_clear()
        Path(self.body["raw_path"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
            self.codes()

    def test_result_container_not_released(self) -> None:
        raw = self.raw.replace(b'<p class="ltx_p">', b'<figure><p class="ltx_p">').replace(b'</p>', b'</p></figure>')
        path = self.root / "protected.html"
        path.write_bytes(raw)
        body = {**self.body, "raw_path": str(path), "sha256": e.sha(raw)}
        self.assertTrue(self.codes({**self.fact, "raw_source_sha256": e.sha(raw)}, body))

    def save_record(self, filename: str, revision: int, parent: str | None, **extra) -> None:
        (self.root / filename).write_bytes(e.encoded({"review_id": "W0001", "record_revision": revision,
                                                    "supersedes": parent, **extra}))

    def test_contiguous_supersession_chain_preserved(self) -> None:
        self.save_record("W0001.0001.json", 1, None)
        self.save_record("W0001.json", 2, "W0001.0001.json")
        self.assertEqual(s.latest_record(self.root, "W0001")[0]["record_revision"], 2)

    def test_missing_revision_not_silently_skipped(self) -> None:
        self.save_record("W0001.0001.json", 1, None)
        self.save_record("W0001.json", 3, "W0001.0001.json")
        with self.assertRaisesRegex(ValueError, "GAP"):
            s.latest_record(self.root, "W0001")

    def test_conflicting_latest_revision_is_not_selected(self) -> None:
        self.save_record("W0001.0001.json", 1, None)
        self.save_record("W0001.0002.json", 2, "W0001.0001.json", value="first")
        self.save_record("W0001.json", 2, "W0001.0001.json", value="different")
        with self.assertRaisesRegex(ValueError, "CONFLICTING"):
            s.latest_record(self.root, "W0001")

    def test_supersession_cannot_read_outside_input_directory(self) -> None:
        self.save_record("W0001.0001.json", 1, None)
        self.save_record("W0001.json", 2, "../private.json")
        with self.assertRaisesRegex(ValueError, "UNSAFE"):
            s.latest_record(self.root, "W0001")

    def test_same_revision_pointer_with_identical_bytes_is_allowed(self) -> None:
        self.save_record("W0001.0001.json", 1, None)
        self.save_record("W0001.0002.json", 2, "W0001.0001.json")
        self.save_record("W0001.json", 2, "W0001.0001.json")
        self.assertEqual(s.latest_record(self.root, "W0001")[0]["record_revision"], 2)

    def test_missing_or_non_utc_semantic_timestamp_rejected(self) -> None:
        for stamp in (None, "2026-10-19T22:00:00", "2026-10-19T22:00:00+05:30"):
            self.assertTrue(self.codes({**self.fact, "checked_utc": stamp}))

    def test_actual_checker_metadata_variants_are_narrowly_normalized(self) -> None:
        fact = copy.deepcopy(self.fact)
        fact["source_context_original_checked_utc"] = fact["checked_utc"]
        fact["locator_checked_utc"] = fact["checked_utc"]
        fact["literal_quotation_words"] = 0
        fact["locator"].update(parser="html.parser", source_view="ORIGINAL_UNMODIFIED_RAW_BODY", index_base=0)
        fact["locator"]["evidence_paragraphs"][0].update(index_base=0, global_p_ltx_p_index_zero_based=0)
        self.assertEqual(self.codes(fact), [])
        self.assertEqual(s.transfer_locator(fact["locator"]), self.fact["locator"])
        fact["second_local_semantic_pass"] = {"performed": True, "checked_by": s.ACTORS["01"],
            "checked_utc": fact["checked_utc"], "scope": "Local rereading of paraphrase against source context."}
        self.assertEqual(self.codes(fact), [])
        fact["locator"]["index_base"] = 1
        self.assertTrue(self.codes(fact))

    def test_private_pdf_render_path_removed_from_transfer(self) -> None:
        locator = {"format": "PDF", "method_section_locator": "Section 3, page 4",
                   "evidence_pages": [{"page_number_1based": 4, "rendered_page_path": "/private/cache.png",
                                       "rendered_page_sha256": "a" * 64, "page_text_sha256": "b" * 64}]}
        self.assertNotIn("rendered_page_path", s.transfer_locator(locator)["evidence_pages"][0])

    def test_exact_pdf_page_and_visual_render_bindings(self) -> None:
        import fitz
        with fitz.open() as pdf:
            page = pdf.new_page()
            page.insert_text((72, 72), "Methods: classify each input before response generation.")
            raw = pdf.tobytes()
        path = self.root / "source.pdf"
        path.write_bytes(raw)
        with fitz.open(stream=raw, filetype="pdf") as pdf:
            page = pdf[0]
            png = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes("png")
            render = self.root / "page.png"
            render.write_bytes(png)
            loc = {"format": "PDF", "method_section_locator": "Methods, page 1", "evidence_pages": [{
                "page_number_1based": 1, "page_text_sha256": e.sha(page.get_text().encode()),
                "rendered_page_path": str(render), "rendered_page_sha256": e.sha(png)}]}
        body = {"raw_path": str(path), "sha256": e.sha(raw)}
        with mock.patch.object(e, "read", return_value={"cache_root": str(self.root)}):
            self.assertEqual(s.validate_pdf_locator(loc, body), [])
            render.write_bytes(b"wrong render")
            self.assertEqual(s.validate_pdf_locator(loc, body), ["SEMANTIC_PDF_RENDER_MISMATCH"])
            loc["evidence_pages"][0]["page_number_1based"] = 2
            self.assertEqual(s.validate_pdf_locator(loc, body), ["SEMANTIC_PDF_PAGE_NOT_FOUND"])

    def test_intake_or_version_check_is_not_method_context_review(self) -> None:
        for key, field, good, blocked in [
            ("01", "raw_context_semantically_checked", True, False),
            ("02", "context_check_status", "PRIMARY_METHOD_CONTEXT_CHECKED", "NOT_CONTEXT_CHECKED_METHOD_RELEASE_BLOCKED_BY_VERSION"),
            ("03", "raw_context_inspected", True, False),
        ]:
            record = {"actor_id": s.ACTORS[key], "checked_member_ids": ["M0001", "M0002"],
                      "source_receipts": [{"member_id": "M0001", field: good}, {"member_id": "M0002", field: blocked}]}
            self.assertEqual(s.context_checked_members(record), ["M0001"])

    def test_unattested_or_duplicate_method_context_receipt_is_rejected(self) -> None:
        record = {"actor_id": s.ACTORS["01"], "checked_member_ids": [],
                  "source_receipts": [{"member_id": "M0001", "raw_context_semantically_checked": True}]}
        with self.assertRaisesRegex(ValueError, "MEMBERSHIP_MISMATCH"):
            s.context_checked_members(record)


class OfflineTransferChecks(unittest.TestCase):
    """Exercise the verifier with rehashed mutations, not only broken file hashes."""

    def setUp(self) -> None:
        parent = Path(e.git("rev-parse", "--show-toplevel")) / ".venv/a04-semantic-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        if not Path(self.temp.name).resolve().is_relative_to(parent.resolve()):
            raise ValueError("Unsafe cleanup target")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.verifier = types.ModuleType("offline_semantic_fixture")
        exec(compile(s.verifier_bytes(), "verify_semantic.py", "exec"), self.verifier.__dict__)
        config = e.read(e.CONFIG)
        base = (e.BASE / config["run_id"] / "RESTRICTED_EVIDENCE_SUPPLEMENT.zip").read_bytes()
        with zipfile.ZipFile(io.BytesIO(base)) as zipped:
            works = json.loads(zipped.read("WORK_EVIDENCE_CROSSWALK.json"))
        self.files = {"BASE_EVIDENCE_SUPPLEMENT.zip": base, "README.md": b"Fixture\n",
                      "verify_semantic.py": s.verifier_bytes()}
        self.coverage = []
        for work in works:
            self.coverage.append({"work_id": work["work_id"], "review_id": work["review_id"],
                "member_ids": work["member_ids"], "source_restriction_checker": s.ACTORS[s.owner(work["review_id"])],
                "context_checked_member_ids": [], "restricted_method_evidence_ids": [],
                "additional_restriction_correction_needed": False, "remaining_eligibility_facts_require_review": True,
                "final_preferred_version_independently_verified": False, "delivered_to_reviewer": False,
                "independent_eligibility_review_completed": False, "eligibility_decision": None})
        work = works[0]
        mid = work["member_ids"][0]
        self.fact = {"evidence_id": "SEM-01-TEST-F01", "work_id": work["work_id"], "review_id": work["review_id"],
            "member_id": mid, "fact_kind": "INPUT_TASK", "method_fact": "The classifier labels input text as benign or malicious.",
            "source_url": "https://arxiv.org/html/2501.00001v1", "version": "arxiv:2501.00001v1",
            "raw_source_sha256": "a" * 64, "locator": {"format": "HTML", "evidence_paragraphs": [
                {"global_p_ltx_p_ordinal": 0, "section_id": "S3", "paragraph_text_sha256": "b" * 64}]},
            "restriction_checked_by": s.ACTORS["01"], "checked_utc": "2026-10-19T22:00:00+00:00",
            "limitation": "Language and timing remain unresolved.", "source_checker_record_sha256": "c" * 64,
            "eligibility_decision": None}
        self.receipt = {"evidence_id": self.fact["evidence_id"], "work_ids": [work["work_id"]],
            "requested_method_or_bibliographic_fact": "INPUT_TASK", "provider_id": "CUSTODIAN",
            "source_url": self.fact["source_url"], "version": self.fact["version"],
            "method_dataset_or_bibliographic_locator": self.fact["locator"], "retrieved_utc": "2026-10-19T21:00:00+00:00",
            "http_or_access_status": 200, "raw_source_sha256": self.fact["raw_source_sha256"],
            "restricted_evidence_sha256": e.sha(e.encoded(self.fact)), "restriction_checked_by": s.ACTORS["01"],
            "restriction_checked_utc": self.fact["checked_utc"], "mechanical_release_checked_by": "CUSTODIAN",
            "qualitative_and_quantitative_findings_absent": True, "reviewer_received_utc": None,
            "limitations": self.fact["limitation"]}
        self.coverage[0]["context_checked_member_ids"] = [mid]
        self.coverage[0]["restricted_method_evidence_ids"] = [self.fact["evidence_id"]]
        self.roles = [{"actor_id": actor, "role": "SOURCE_RESTRICTION_CHECKER_NOT_ELIGIBILITY_REVIEWER",
            "separate_task_context_fork_turns": "none", "shared_filesystem": True, "os_isolation_claimed": False,
            "eligibility_review_claimed": False, "actual_completion_report_received": True} for actor in s.ACTORS.values()]
        self.facts, self.receipts = [self.fact], [self.receipt]
        self.exceptions = []

    def write(self) -> None:
        for name, data in {"SEMANTIC_METHOD_FACTS.json": self.facts, "SEMANTIC_EVIDENCE_RECEIPTS.json": self.receipts,
                           "SEMANTIC_COVERAGE.json": self.coverage, "CHECKER_ROLE_RECEIPTS.json": self.roles,
                           "RESTRICTION_EXCEPTIONS.json": self.exceptions}.items():
            self.files[name] = e.encoded(data)
        manifest = {"files": {name: e.sha(raw) for name, raw in self.files.items()}, "gate": "FRAME_BLOCKED",
                    "draw_executed": False, "actual_independent_eligibility_review": "NOT_RECEIVED",
                    "actual_delivery": "NOT_PERFORMED"}
        for name, raw in self.files.items():
            (self.root / name).write_bytes(raw)
        (self.root / "MANIFEST.json").write_bytes(e.encoded(manifest))

    def verify(self) -> dict:
        self.write()
        return self.verifier.verify(self.root)

    def test_valid_restricted_fixture(self) -> None:
        self.assertEqual(self.verify()["method_facts"], 1)

    def test_unexpected_transfer_file_rejected(self) -> None:
        (self.root / "historical_answers.json").write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "ALLOWLIST"):
            self.verify()

    def test_missing_or_duplicate_receipt_rejected(self) -> None:
        for receipts in ([], [self.receipt, self.receipt]):
            self.receipts = receipts
            with self.assertRaisesRegex(ValueError, "COMPLETENESS"):
                self.verify()

    def test_rehashed_outcome_content_rejected(self) -> None:
        self.fact["method_fact"] = "The model achieves better accuracy."
        self.receipt["restricted_evidence_sha256"] = e.sha(e.encoded(self.fact))
        with self.assertRaisesRegex(ValueError, "PROHIBITED_METHOD"):
            self.verify()

    def test_nonblank_decision_or_historical_field_rejected(self) -> None:
        self.coverage[0]["eligibility_decision"] = "INCLUDE"
        with self.assertRaisesRegex(ValueError, "DECISION_CHANGED"):
            self.verify()
        self.coverage[0]["eligibility_decision"] = None
        self.coverage[0]["previous_answer"] = "EXCLUDE"
        with self.assertRaisesRegex(ValueError, "DECISION_CHANGED"):
            self.verify()

    def test_frozen_base_archive_cannot_be_replaced(self) -> None:
        self.files["BASE_EVIDENCE_SUPPLEMENT.zip"] += b"changed"
        with self.assertRaisesRegex(ValueError, "FROZEN_BASE"):
            self.verify()

    def test_false_independence_or_delivery_claim_rejected(self) -> None:
        self.roles[0]["os_isolation_claimed"] = True
        with self.assertRaisesRegex(ValueError, "ROLES_MISREPRESENTED"):
            self.verify()
        self.roles[0]["os_isolation_claimed"] = False
        self.receipt["reviewer_received_utc"] = "2026-10-19T23:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "DELIVERY"):
            self.verify()

    def test_facts_cannot_be_linked_to_wrong_work_or_unchecked_member(self) -> None:
        self.coverage[0]["context_checked_member_ids"] = []
        with self.assertRaisesRegex(ValueError, "CONTEXT_CROSSWALK"):
            self.verify()

    def test_membership_change_rejected(self) -> None:
        self.coverage[0]["member_ids"] = ["M9999"]
        with self.assertRaisesRegex(ValueError, "MEMBERSHIP"):
            self.verify()

    def test_exception_prose_and_receipt_extra_fields_rejected(self) -> None:
        self.receipt["historical_judgment"] = "EXCLUDE"
        with self.assertRaisesRegex(ValueError, "RECEIPT"):
            self.verify()
        del self.receipt["historical_judgment"]
        self.exceptions = [{"unexpected_prose": "old answer"}]
        with self.assertRaisesRegex(ValueError, "EXCEPTION_CONTENT"):
            self.verify()

    def test_private_source_locator_field_rejected(self) -> None:
        self.fact["locator"]["raw_path"] = "/private/source.html"
        self.receipt["restricted_evidence_sha256"] = e.sha(e.encoded(self.fact))
        with self.assertRaisesRegex(ValueError, "PUBLIC_SOURCE_LOCATOR"):
            self.verify()


if __name__ == "__main__":
    unittest.main(verbosity=2)
