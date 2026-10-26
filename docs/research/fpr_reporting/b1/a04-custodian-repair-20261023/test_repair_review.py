"""Guard administrative repairs against invented precision and review changes."""
from __future__ import annotations

import copy
import unittest

import repair_review as repair


def arxiv(identifier: str = "2406.00799", dates: tuple[str, str] = ("2024-06-02", "2025-03-06")) -> dict:
    """Build an official-history fixture with distinct submission/revision dates."""
    return {"review_id": "W0011", "evidence_id": "R01-BIB-M0034",
            "provenance": {"source_url": "https://arxiv.org/abs/" + identifier},
            "official_fields": {"revision_history": [
                {"revision": "v1", "public_utc": dates[0] + "T16:00:00+00:00"},
                {"revision": "v6", "public_utc": dates[1] + "T16:00:00+00:00"}], "publication_date_literals": []}}


def acl(month: str = "2025/8") -> dict:
    """Build month-only publication evidence, which cannot establish a day."""
    return {"review_id": "W0011", "evidence_id": "R01-BIB-M0001",
            "provenance": {"source_url": "https://aclanthology.org/2025.paper.1/"},
            "official_fields": {"revision_history": [], "publication_date_literals": [{"value": month}]}}


class AdministrativeRepairChecks(unittest.TestCase):
    """Test scientific boundaries as well as correct metadata arithmetic."""

    def test_invalid_day_does_not_turn_into_month(self) -> None:
        self.assertIsNone(repair.interval("2025-02-30"))

    def test_month_stays_month(self) -> None:
        bounds = repair.interval("2025/8")
        self.assertEqual(bounds, ("2025-08-01", "2025-08-31"))
        self.assertEqual(repair.display(bounds), "2025-08")

    def test_selected_revision_does_not_use_first_submission(self) -> None:
        bounds, _ = repair.version_basis("arxiv:2406.00799v6", [arxiv()])
        self.assertEqual(bounds, ("2025-03-06", "2025-03-06"))

    def test_other_arxiv_identifier_cannot_supply_revision_date(self) -> None:
        self.assertIsNone(repair.version_basis("arxiv:2406.00799v6", [arxiv("2406.12345")]))

    def test_conflicting_primary_dates_are_not_guessed(self) -> None:
        self.assertIsNone(repair.version_basis("arxiv:2406.00799v6", [arxiv(), arxiv(dates=("2024-06-02", "2025-03-07"))]))

    def test_preprint_before_publication_month_is_earliest_documented(self) -> None:
        bounds, _ = repair.first_public_basis([arxiv(), acl()])
        self.assertEqual(bounds, ("2024-06-02", "2024-06-02"))

    def test_overlapping_month_and_day_do_not_create_an_exact_first_day(self) -> None:
        bounds, _ = repair.first_public_basis([arxiv(dates=("2025-08-15", "2025-09-01")), acl()])
        self.assertEqual(bounds, ("2025-08-01", "2025-08-15"))
        self.assertIsNone(repair.display(bounds))

    def test_repairs_preserve_selected_version_decisions_and_source_rows(self) -> None:
        row = {"review_id": "W0011", "work_id": "arxiv:2406.00799", "selected_version_id": "arxiv:2406.00799v6",
               "first_public_date": "2024/06/02", "version_date": "2024/06/02", "decision": "UNCLEAR",
               "english_evaluation": "UNCLEAR", "evidence_ids": ["SEM-01-W0011-F01"]}
        original = copy.deepcopy(row)
        fixed, log = repair.repair_rows([row], [arxiv()])
        self.assertEqual(row, original)
        self.assertEqual(fixed[0]["version_date"], "2025-03-06")
        self.assertEqual({k for k in row if row[k] != fixed[0][k]}, {"version_date"})
        self.assertEqual(log[0]["original_row_sha256"], repair.sha(repair.encoded(original)))

    def test_exact_publisher_day_is_replaced_by_supported_month(self) -> None:
        row = {"review_id": "W0011", "work_id": "acl:2025.paper.1", "selected_version_id": "acl:2025.paper.1:publication",
               "first_public_date": "2025-08-01", "version_date": "2025-08-31", "decision": "ELIGIBLE"}
        fixed, _ = repair.repair_rows([row], [acl()])
        self.assertEqual(fixed[0]["version_date"], "2025-08")
        self.assertEqual(fixed[0]["first_public_date"], "2025-08")
        self.assertEqual(fixed[0]["decision"], "ELIGIBLE")

    def test_attestation_acceptance_does_not_approve_scientific_frame(self) -> None:
        intake = {k: True for k in ("independent_human_outcome_sheet_unseen", "previous_assistant_judgments_unseen",
                                    "restricted_evidence_process_confirmed", "result_bearing_source_displays_unseen",
                                    "separate_empty_workspace_confirmed")}
        intake.update(status="ATTESTED", attested_utc="2026-10-22T11:05:00Z", reviewer_id="REVIEWER",
                      package_sha256_received_out_of_band=repair.WRAPPER_PIN, previously_familiar_work_ids_for_reassignment=[])
        freeze = {"reviewer_id": "REVIEWER", "archive_transfer_sha256_verified": repair.WRAPPER_PIN}
        result = repair.validate_intake(intake, freeze, [{"reviewed_utc": "2026-10-22T11:15:00Z"}])
        self.assertTrue(result["original_recorded_attestation_accepted"])
        self.assertFalse(result["scientific_frame_completion_inferred_from_attestation"])
        intake["previous_assistant_judgments_unseen"] = False
        self.assertFalse(repair.validate_intake(intake, freeze, [{"reviewed_utc": "2026-10-22T11:15:00Z"}])["original_recorded_attestation_accepted"])


if __name__ == "__main__":
    unittest.main()
