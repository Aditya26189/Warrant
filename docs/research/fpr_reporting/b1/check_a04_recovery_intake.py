"""Check provisional-return mechanics without authenticating scientific review."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import a04_recovery_intake as r


class RecoveryIntakeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = r.e.BASE / r.RUN / "original-return"
        if not source.exists():
            source = Path("C:/Users/LawLight/Downloads")
        cls.rows = json.loads((source / r.ORIGINAL_NAMES[0]).read_bytes())
        cls.requests = json.loads((source / r.ORIGINAL_NAMES[3]).read_bytes())
        cls.declared = json.loads((source / r.ORIGINAL_NAMES[1]).read_bytes())

    def test_real_provisional_return_is_only_mechanically_validated(self) -> None:
        result = r.validate_return(self.rows, self.requests, self.declared)
        self.assertEqual(result["memberships"], 389)
        self.assertEqual(result["semantic_facts_linked"], 549)
        self.assertEqual(result["controlled_request_items"], 1852)
        self.assertFalse(result["completed_independent_eligibility_return"])
        self.assertFalse(result["synthetic_or_overridden_checks_used_for_authentication"])
        self.assertEqual(result["return_status"], "PROVISIONAL_UNAUTHENTICATED")

    def test_mechanical_adjudication_flag_does_not_complete_review(self) -> None:
        result = r.validate_return(self.rows, self.requests, {**self.declared, "all_rows_explicitly_adjudicated": True})
        self.assertIn("MECHANICAL_DISPOSITIONS", result["interpretation"])
        self.assertFalse(result["fresh_intake_attested_locally"])
        self.assertFalse(result["authentic_transfer_recorded"])

    def test_duplicate_or_missing_row_rejected(self) -> None:
        for rows in (self.rows[:-1], [*self.rows[:-1], self.rows[0]]):
            with self.assertRaisesRegex(ValueError, "WORK_COVERAGE"):
                r.validate_return(rows, self.requests, self.declared)

    def test_work_identity_cannot_be_swapped(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[0]["work_id"] = rows[1]["work_id"]
        with self.assertRaisesRegex(ValueError, "WORK_ID_MISMATCH"):
            r.validate_return(rows, self.requests, self.declared)

    def test_non_sentinel_exclusion_is_not_silently_accepted(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[0]["decision"] = "EXCLUDE"
        with self.assertRaisesRegex(ValueError, "EXACT_ALL_VERSION_SENTINEL"):
            r.validate_return(rows, self.requests, self.declared)

    def test_include_does_not_bypass_the_reported_return_contract(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[0]["decision"] = "INCLUDE"
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_PROVISIONAL_DECISION"):
            r.validate_return(rows, self.requests, self.declared)

    def test_cross_work_evidence_id_rejected(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[0]["evidence_ids"] = self.rows[1]["evidence_ids"]
        with self.assertRaisesRegex(ValueError, "EVIDENCE_FOREIGN_KEY"):
            r.validate_return(rows, self.requests, self.declared)

    def test_changed_source_locator_rejected(self) -> None:
        rows = copy.deepcopy(self.rows)
        row = next(x for x in rows if x["method_bibliographic_locators"])
        row["method_bibliographic_locators"][0]["raw_source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SOURCE_LOCATOR_CHANGED"):
            r.validate_return(rows, self.requests, self.declared)

    def test_missing_or_duplicate_request_rejected(self) -> None:
        for requests in (self.requests[:-1], [*self.requests[:-1], self.requests[0]]):
            with self.assertRaisesRegex(ValueError, "REQUEST_WORK_COVERAGE"):
                r.validate_return(self.rows, requests, self.declared)

    def test_request_membership_or_criterion_changed_is_rejected(self) -> None:
        requests = copy.deepcopy(self.requests)
        requests[0]["member_ids"] = ["M9999"]
        with self.assertRaisesRegex(ValueError, "REQUEST_IDENTITY"):
            r.validate_return(self.rows, requests, self.declared)
        requests = copy.deepcopy(self.requests)
        requests[0]["controlled_requests"][0]["criterion"] = "performance"
        with self.assertRaisesRegex(ValueError, "REQUEST_CRITERIA"):
            r.validate_return(self.rows, requests, self.declared)

    def test_source_projection_removes_provisional_decisions_and_statuses(self) -> None:
        projected = r.source_requests(self.requests)
        self.assertEqual(len(projected), 367)
        for row in projected:
            self.assertNotIn("current_decision", row)
            for gap in row["controlled_requests"]:
                self.assertEqual(set(gap), {"criterion", "request", "existing_restricted_evidence_ids"})

    def test_original_authentication_rejects_altered_or_synthetic_bytes(self) -> None:
        for _, (path, digest, _) in r.ARCHIVES.items():
            raw = (r.e.BASE / path).read_bytes()
            self.assertTrue(r.authenticated_payloads(raw, digest))
            with self.assertRaisesRegex(ValueError, "DIGEST_MISMATCH"):
                r.authenticated_payloads(raw + b"altered", digest)
            with self.assertRaisesRegex(ValueError, "DIGEST_MISMATCH"):
                r.authenticated_payloads(b"synthetic substitute", digest)

    def test_actual_nested_base_is_the_authentic_original(self) -> None:
        archives = r.original_archives()
        self.assertEqual(archives["CONSOLIDATED_RESTRICTED_EVIDENCE.zip"]["BASE_EVIDENCE_SUPPLEMENT.zip"],
                         (r.e.BASE / r.ARCHIVES["RESTRICTED_EVIDENCE_SUPPLEMENT.zip"][0]).read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
