"""Negative controls for the A05 proposal's evidence and gate boundaries."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compile_proposal as c  # noqa: E402
import release_checked as r  # noqa: E402


class ProposalTests(unittest.TestCase):
    """Check errors that previously caused scientifically invalid promotions."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads((HERE / "SOURCE_CASEBOOK.json").read_bytes())["cases"]
        cls.by_id = {x["review_id"]: x for x in cls.cases}
        cls.evidence = {x["evidence_id"]: x for case in cls.cases for x in case["evidence"]}
        cls.rows = [row for path in sorted(HERE.glob("DOMAIN_BATCH_*.json"))
                    for row in json.loads(path.read_bytes())["rows"]]

    def test_all_original_works_and_memberships_retained(self) -> None:
        c.validate_domain_rows(self.cases, self.rows, self.evidence)
        self.assertEqual(372, len(self.rows))
        self.assertEqual(389, sum(len(x["inventory"]["members"]) for x in self.cases))

    def test_missing_work_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "DOMAIN_WORK_COVERAGE"):
            c.validate_domain_rows(self.cases, self.rows[:-1], self.evidence)

    def test_duplicate_work_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "DOMAIN_WORK_COVERAGE"):
            c.validate_domain_rows(self.cases, self.rows[:-1] + [self.rows[0]], self.evidence)

    def test_foreign_citation_fails(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[0]["considered_method_evidence_ids"] = ["SEM-01-W0011-F01"]
        with self.assertRaisesRegex(ValueError, "DOMAIN_FOREIGN_EVIDENCE"):
            c.validate_domain_rows(self.cases, rows, self.evidence)

    def test_preprint_language_cannot_certify_acl_version(self) -> None:
        row = next(x for x in self.rows if x["review_id"] == "W0352")
        proof = {"criterion_evidence_ids": {k: ["SEM-01-W0352-F02"] for k in c.CRITERIA},
                 "experiment_and_inference_rationale": "Intentionally wrong-version negative control."}
        with self.assertRaisesRegex(ValueError, "POSITIVE_MIXED_VERSION"):
            c.validate_positive_binding(row, proof, self.evidence,
                                       "acl:2025.findings-emnlp.1060:publication")

    def test_missing_english_cannot_be_promoted(self) -> None:
        row = next(x for x in self.rows if x["review_id"] == "W0022")
        proof = {"criterion_evidence_ids": {k: ["SEM-01-W0022-F01"] for k in c.CRITERIA},
                 "experiment_and_inference_rationale": "Language missing, despite a classifier."}
        with self.assertRaisesRegex(ValueError, "POSITIVE_NOT_ESTABLISHED"):
            c.validate_positive_binding(row, proof, self.evidence, "arxiv:2410.22284v1")

    def test_latest_revision_date_is_not_first_release(self) -> None:
        bib = c.bibliography(self.by_id["W0011"])
        self.assertEqual("arxiv:2406.00799v6", bib["selected"]["version"])
        self.assertEqual(["2025-03-06"] * 2, bib["selected"]["date_interval"])
        self.assertEqual(["2024-06-02"] * 2, bib["first_public_date_interval"])

    def test_acl_month_is_not_invented_exact_day(self) -> None:
        bib = c.bibliography(self.by_id["W0048"])
        self.assertEqual(["2025-08-01", "2025-08-31"], bib["selected"]["date_interval"])
        self.assertTrue(bib["selected"]["version"].startswith("acl:"))

    def test_year_only_registration_does_not_settle_vor(self) -> None:
        bib = c.bibliography(self.by_id["W0339"])
        self.assertEqual("UNCLEAR", bib["status"])
        self.assertIn("KNOWN_PUBLISHER_VOR_AVAILABILITY_OR_EXACT_VERSION_UNRESOLVED", bib["version_issues"])

    def test_withdrawn_version_not_silently_replaced(self) -> None:
        bib = c.bibliography(self.by_id["W0021"])
        self.assertEqual("arxiv:2410.21337v2", bib["selected"]["version"])
        self.assertTrue(bib["selected"]["withdrawn"])
        self.assertFalse(bib["selected_method_body_supported"])

    def test_held_or_self_checked_prose_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "NOT_SEPARATELY_APPROVED"):
            r.approved("HOLD", "provider", "checker")
        with self.assertRaisesRegex(ValueError, "NOT_SEPARATELY_APPROVED"):
            r.approved("APPROVE", "same", "same")

    def test_checked_source_release_replays(self) -> None:
        facts, files = r.build()
        self.assertEqual(9, len(facts))
        self.assertEqual(8, len(files))
        self.assertEqual(9, len({x["evidence_id"] for x in facts}))
        self.assertTrue(all(x["provider_actor"] != x["checker_actor"] for x in facts))


if __name__ == "__main__":
    unittest.main()
