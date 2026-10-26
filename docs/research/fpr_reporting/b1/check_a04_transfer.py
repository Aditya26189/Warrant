"""Test finite procedural evidence, official history parsing and transfer boundaries."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import a04_access_followup as followup
import a04_evidence as e
import a04_method_clauses as c
from check_a04_evidence import html

SPEC = importlib.util.spec_from_file_location("evidence_verifier", e.SOURCE / "verify_evidence.py")
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)


class ProcedureChecks(unittest.TestCase):
    def test_dataset_procedure_with_citation_outside_span(self) -> None:
        raw = html("We use the TensorTrust dataset [12] for model development.")
        items = c.extract(raw)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["quote"], "We use the TensorTrust dataset")
        c.verify(raw, items[0])

    def test_english_procedure_is_partial_not_an_all_english_assertion(self) -> None:
        item = c.extract(html("We use English prompts alongside other language data."))[0]
        self.assertEqual(item["quote"], "We use English prompts")
        self.assertIn("REMAINING_ELIGIBILITY", item["limitation"])

    def test_output_grammar_has_no_free_prose_slot(self) -> None:
        for phrase in ("We use TensorTrust with superior accuracy", "We use 50 benign prompts",
                       "We achieve negligible false positives", "We use an unpublished surprising finding",
                       "We use TensorTrustInjection", "We use English prompts perfectly"):
            self.assertIsNone(c.full_rule(phrase))

    def test_named_dataset_digit_is_not_a_sample_count(self) -> None:
        self.assertEqual(c.full_rule("We use SQuAD 2.0"), "DATASET_PROCEDURE_CLAUSE")
        self.assertIsNone(c.full_rule("We use 2.0 examples"))

    def test_outcome_context_quarantined(self) -> None:
        self.assertFalse(c.extract(html("We use TensorTrust and achieve the best results.")))

    def test_conditional_comparison_and_negation_quarantined(self) -> None:
        for text in ("If we use TensorTrust, a detector is trained.",
                     "Unlike prior work, we use TensorTrust.", "For example, we use TensorTrust."):
            self.assertFalse(c.extract(html(text)))

    def test_result_section_and_unheaded_prose_not_released(self) -> None:
        self.assertFalse(c.extract(html("We use TensorTrust.", heading="4 Results")))
        self.assertFalse(c.extract(b'<html><p class="ltx_p">We use TensorTrust.</p></html>'))

    def test_changed_span_or_body_rejected(self) -> None:
        raw = html("We use TensorTrust for development.")
        item = c.extract(raw)[0]
        item["span_start"] += 1
        with self.assertRaisesRegex(ValueError, "FAILED"):
            c.verify(raw, item)

    def test_withdrawal_history_has_only_bibliographic_fields(self) -> None:
        raw = b'<html><div class="submission-history">Author and unrelated text [v1] Mon, 28 Oct 2024 00:36:21 UTC (2139 KB) [v2] Thu, 7 Nov 2024 21:20:31 UTC (1 KB) (withdrawn)</div></html>'
        rows = followup.history(raw)
        self.assertEqual([r["revision"] for r in rows], ["v1", "v2"])
        self.assertTrue(rows[1]["withdrawn_in_history"])
        self.assertNotIn("Author", e.encoded(rows).decode())
        self.assertNotIn("KB", e.encoded(rows).decode())

    def test_unresolved_revision_history_fails_closed(self) -> None:
        for raw in (b"<html></html>", b'<div class="submission-history">[v1] unknown date</div>'):
            with self.assertRaises(ValueError):
                followup.history(raw)


class TransferChecks(unittest.TestCase):
    def setUp(self) -> None:
        parent = Path(e.git("rev-parse", "--show-toplevel")) / ".venv/a04-transfer-tests"
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        if not Path(self.temp.name).resolve().is_relative_to(parent.resolve()):
            raise ValueError("Unsafe cleanup target")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        works, bibliography, coverage, exceptions = [], [], [], []
        reviews = []
        n = 0
        for wi in range(372):
            wid, rid = f"arxiv:2501.{wi:05d}", f"W{wi + 1:04d}"
            mids, eids = [], []
            for _ in range(18 if wi == 0 else 1):
                n += 1
                mid, eid = f"M{n:04d}", f"BIB-M{n:04d}"
                base = {"work_id": wid, "review_id": rid, "member_id": mid}
                b = dict.fromkeys(v.BIB_FIELDS)
                b.update(base, evidence_id=eid, captured_bibliography={"doi": "", "published": "", "updated": "", "year": "", "month": ""}, access_attempts=[])
                bibliography.append(b)
                cov = dict.fromkeys(v.COVERAGE_FIELDS)
                cov.update(base)
                coverage.append(cov)
                exceptions.append({**base, "codes": []})
                mids.append(mid)
                eids.append(eid)
            work = dict.fromkeys(v.WORK_FIELDS)
            work.update(work_id=wid, review_id=rid, member_ids=mids, evidence_ids=eids)
            works.append(work)
            reviews.append({"work_id": wid, "review_id": rid, "decision": None})
        receipts = []
        for b in bibliography:
            r = dict.fromkeys(v.RECEIPT_FIELDS)
            r.update(evidence_id=b["evidence_id"], restricted_evidence_sha256=e.sha(e.encoded(b)))
            receipts.append(r)
        payloads = {
            "WORK_EVIDENCE_CROSSWALK.json": works, "BIBLIOGRAPHIC_EVIDENCE.json": bibliography,
            "METHOD_EVIDENCE.json": [], "EVIDENCE_RECEIPTS.json": receipts,
            "EXCEPTIONS.json": exceptions, "MEMBER_COVERAGE.json": coverage,
            "PRIMARY_ACCESS_FOLLOWUPS.json": [], "ELIGIBILITY_REVIEW_BLANK.json": reviews,
            "SENTINEL_IDENTIFIER_CROSSWALK.json": [{"work_id": w["work_id"], "review_id": w["review_id"],
                "exact_identifier_matches": [], "matching_scope": "FIXTURE", "decision": None} for w in works],
            "REVIEWER_INTAKE_BLANK.json": {"reviewer_id": None},
            "EVIDENCE_RECEIPT_BLANK.json": {"evidence_id": None},
            "finite_language.json": {"ruleset": c.RULESET, "patterns": {k: p.pattern for k, p in c.PATTERNS.items()}},
        }
        self.files = {name: e.encoded(value) for name, value in payloads.items()}
        self.files.update({"README.md": b"Fixture", "verify_evidence.py": b"# Fixture"})
        v.FINITE_LANGUAGE_SHA256 = e.sha(self.files["finite_language.json"])
        self.write()

    def write(self) -> None:
        for name, raw in self.files.items():
            (self.root / name).write_bytes(raw)
        (self.root / "MANIFEST.json").write_bytes(e.encoded({
            "files": {n: e.sha(raw) for n, raw in self.files.items()}, "gate": "FRAME_BLOCKED",
            "draw_executed": False, "delivered_to_reviewer": False, "separate_semantic_checker_established": False}))

    def edit(self, name: str, mutate) -> None:
        value = json.loads(self.files[name])
        mutate(value)
        self.files[name] = e.encoded(value)
        self.write()

    def test_complete_partial_supplement_verifies(self) -> None:
        self.assertEqual(v.verify(self.root)["members"], 389)

    def test_unrestricted_extra_file_rejected(self) -> None:
        (self.root / "source.pdf").write_bytes(b"%PDF")
        with self.assertRaisesRegex(ValueError, "UNEXPECTED"):
            v.verify(self.root)

    def test_missing_receipt_rejected(self) -> None:
        self.edit("EVIDENCE_RECEIPTS.json", lambda x: x.pop())
        with self.assertRaisesRegex(ValueError, "RECEIPTS"):
            v.verify(self.root)

    def test_duplicate_receipt_rejected(self) -> None:
        self.edit("EVIDENCE_RECEIPTS.json", lambda x: x.append(x[0]))
        with self.assertRaisesRegex(ValueError, "RECEIPTS"):
            v.verify(self.root)

    def test_old_judgment_in_status_field_rejected(self) -> None:
        self.edit("MEMBER_COVERAGE.json", lambda x: x[0].update(previous_decision="INCLUDE"))
        with self.assertRaisesRegex(ValueError, "FIELDS"):
            v.verify(self.root)

    def test_fabricated_completed_review_rejected(self) -> None:
        self.edit("ELIGIBILITY_REVIEW_BLANK.json", lambda x: x[0].update(decision="INCLUDE"))
        with self.assertRaisesRegex(ValueError, "NOT_BLANK"):
            v.verify(self.root)

    def test_restricted_payload_tampering_rejected(self) -> None:
        (self.root / "README.md").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "HASH"):
            v.verify(self.root)

    def test_changed_grammar_rejected_even_with_updated_manifest(self) -> None:
        self.edit("finite_language.json", lambda x: x["patterns"].update(UNRESTRICTED=".*"))
        with self.assertRaisesRegex(ValueError, "FINITE_LANGUAGE"):
            v.verify(self.root)

    def test_wrong_work_membership_rejected(self) -> None:
        self.edit("BIBLIOGRAPHIC_EVIDENCE.json", lambda x: x[0].update(work_id="arxiv:9999.99999"))
        with self.assertRaisesRegex(ValueError, "IDENTITY"):
            v.verify(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
