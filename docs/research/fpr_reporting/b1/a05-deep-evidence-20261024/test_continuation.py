"""Guard against scientific label changes that outrun the released evidence."""
from __future__ import annotations

import copy
import unittest

import compile_continuation as c
import release_deep as r


class ScientificBoundaryTests(unittest.TestCase):
    """Cross-version evidence and incomplete negative scope must fail loudly."""

    def setUp(self) -> None:
        self.row = {"review_id": "W0001", "work_id": "arxiv:0000.00001",
                    "selected_version_id": "arxiv:0000.00001v2", "criteria": {k: "UNCLEAR" for k in c.CRITERIA},
                    "considered_method_evidence_ids": []}
        self.evidence = {"scope": {"review_id": "W0001", "version": self.row["selected_version_id"],
                                   "field_path": "coverage.scope_completeness", "value": False}}
        self.change = {"review_id": "W0001", "work_id": self.row["work_id"],
                       "before_row_sha256": r.sha(r.encoded(self.row)),
                       "criteria": {k: "UNCLEAR" for k in c.CRITERIA}, "new_evidence_ids": ["scope"],
                       "positive_criterion_evidence_ids": None, "scientific_rationale": "Source-bound reason.",
                       "whole_work_exclusion_ground": "ESTABLISHED_SCOPE",
                       "exclusion_basis": "COMPLETE_EVALUATED_ARM_SCOPE"}
        self.change["criteria"]["before_target_answer"] = "NOT_MET"

    def test_partial_scope_cannot_exclude(self) -> None:
        with self.assertRaisesRegex(ValueError, "PARTIAL_SCOPE"):
            c.apply_domain(self.row, self.change, self.evidence)

    def test_proven_complete_scope_can_support_authored_exclusion(self) -> None:
        self.evidence["scope"]["value"] = True
        c.apply_domain(self.row, self.change, self.evidence)
        self.assertEqual(self.row["criteria"]["before_target_answer"], "NOT_MET")

    def test_before_hash_prevents_silent_rewrite(self) -> None:
        self.row["criteria"]["binary_evaluation"] = "MET"
        with self.assertRaisesRegex(ValueError, "PRIOR_ROW_CHANGED"):
            c.apply_domain(self.row, self.change, self.evidence)

    def test_foreign_and_older_version_proofs_rejected(self) -> None:
        for key, value, message in [("review_id", "W0002", "FOREIGN"),
                                    ("version", "arxiv:0000.00001v1", "MIXED_VERSION")]:
            with self.subTest(key=key):
                evidence = copy.deepcopy(self.evidence)
                evidence["scope"][key] = value
                with self.assertRaisesRegex(ValueError, message):
                    c.apply_domain(self.row, self.change, evidence)

    def test_all_positive_requires_four_explicit_proofs(self) -> None:
        change = copy.deepcopy(self.change)
        change["whole_work_exclusion_ground"] = None
        change["criteria"] = {k: "MET" for k in c.CRITERIA}
        with self.assertRaisesRegex(ValueError, "POSITIVE_PROOF_MISSING"):
            c.apply_domain(self.row, change, self.evidence)

    def test_transport_policy_cannot_change_other_works(self) -> None:
        correction = {"before_row_sha256": r.sha(r.encoded(self.row)),
                      "action": "RETAIN_DECLARED_PUBLISHER_EDITION_REMOVE_ADDED_BYTE_TIMESTAMP_REQUIREMENT",
                      "selected_version_id": self.row["selected_version_id"]}
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_VERSION_CORRECTION"):
            c.apply_version(self.row, correction)


if __name__ == "__main__":
    unittest.main()
