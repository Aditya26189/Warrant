"""Guard against scientific label changes that outrun the released evidence."""
from __future__ import annotations

import copy
import json
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

    def test_complete_task_clarification_is_not_complete_whole_work(self) -> None:
        self.evidence["scope"].update(value=True, clarification_scope="TASK_LABEL_CONSTRUCTION_ONLY")
        with self.assertRaisesRegex(ValueError, "PARTIAL_SCOPE"):
            c.apply_domain(self.row, self.change, self.evidence)

    def test_withdrawing_positive_support_preserves_but_supersedes_old_binding(self) -> None:
        self.row["positive_experiment_binding"] = {"criterion_evidence_ids": {"english_evaluation": ["old"]}}
        old = copy.deepcopy(self.row["positive_experiment_binding"])
        self.change.update(before_row_sha256=r.sha(r.encoded(self.row)),
                           whole_work_exclusion_ground=None, exclusion_basis=None)
        c.apply_domain(self.row, self.change, self.evidence)
        self.assertIsNone(self.row["positive_experiment_binding"])
        self.assertEqual(self.row["superseded_positive_experiment_binding"], old)

    def test_explicit_task_scope_requires_a_checked_whole_study_statement(self) -> None:
        self.change["exclusion_basis"] = "EXPLICIT_WHOLE_STUDY_TASK_SCOPE"
        self.change["criteria"]["input_injection_task"] = "NOT_MET"
        with self.assertRaisesRegex(ValueError, "NO_AFFIRMATIVE_WHOLE_STUDY"):
            c.apply_domain(self.row, self.change, self.evidence)
        self.evidence["scope"].update({"field_path": "study_scope_statement", "value": "Original evaluation concerns vision-task image pairs."})
        c.apply_domain(self.row, self.change, self.evidence)
        self.assertEqual(self.row["criteria"]["input_injection_task"], "NOT_MET")

    def test_before_hash_prevents_silent_rewrite(self) -> None:
        self.row["criteria"]["binary_evaluation"] = "MET"
        with self.assertRaisesRegex(ValueError, "PRIOR_ROW_CHANGED"):
            c.apply_domain(self.row, self.change, self.evidence)

    def test_approved_field_cannot_be_relabelled_as_another_edition(self) -> None:
        fact = {"review_id": "W0001", "version": "arxiv:0000.00001v2"}
        check = {"review_id": "W0001", "requested_preferred_version": "arxiv:0000.00001v1", "request_sha256": "request"}
        with self.assertRaisesRegex(ValueError, "WORK_VERSION_OR_REQUEST_CHANGED"):
            c.validate_fact_receipt(fact, check, "request")
        check["requested_preferred_version"] = fact["version"]
        c.validate_fact_receipt(fact, check, "request")
        with self.assertRaisesRegex(ValueError, "WORK_VERSION_OR_REQUEST_CHANGED"):
            c.validate_fact_receipt(fact, check, "different-request")

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

    def test_bibliographic_scope_cannot_be_promoted_to_domain_evidence(self) -> None:
        self.evidence["scope"]["release_status"] = "CHECKED_BIBLIOGRAPHIC_SCOPE_NOT_ELIGIBILITY"
        with self.assertRaisesRegex(ValueError, "BIBLIOGRAPHY_IS_NOT_DOMAIN_PROOF"):
            c.apply_domain(self.row, self.change, self.evidence)

    def identity_fixture(self) -> tuple[dict, dict, dict]:
        """Two separate documents with source-bound chapter reuse, not domain proof."""
        rows, pins, evidence = {}, {}, {}
        for rid, work, version in [("W0069", "arxiv:2508.04281", "arxiv:2508.04281v5"),
                                   ("W0325", "arxiv:2610.04412", "arxiv:2610.04412v1")]:
            rows[rid] = {"review_id": rid, "work_id": work, "selected_version_id": version,
                         "identity_issues": ["REPRODUCED_STUDY_UNIT_UNRESOLVED"],
                         "criteria": {k: "UNCLEAR" for k in c.CRITERIA}}
            refs = []
            for field in ["title", "author", "whole_document_scope", "edition", "source_declared_relationship", "document_type"]:
                eid = rid + field
                refs.append(eid)
                evidence[eid] = {"review_id": rid, "version": version,
                                 "release_status": "CHECKED_BIBLIOGRAPHIC_SCOPE_NOT_ELIGIBILITY",
                                 "field_path": "bibliographic_scope_facts." + field}
            pins[rid] = {"before_row_sha256": r.sha(r.encoded(rows[rid])), "evidence_ids": refs}
        correction = {"action": "KEEP_DISTINCT_WORKS_SHARED_STUDY", "works": pins,
                      "referenced_paper_version": "UNSPECIFIED_IN_THESIS",
                      "rule_document": "WORK_UNIT_RULE_APPLICATION.md",
                      "rule_document_sha256": r.sha((c.HERE / "WORK_UNIT_RULE_APPLICATION.md").read_bytes()),
                      "rationale": "Different whole scopes, explicit chapter reuse.",
                      "limitations": ["Not independent replication; no edition equivalence."]}
        return rows, correction, evidence

    def test_identity_keeps_both_documents_without_domain_transfer(self) -> None:
        rows, correction, evidence = self.identity_fixture()
        before = copy.deepcopy(rows)
        self.assertEqual(c.apply_identity(rows, correction, evidence), set(before))
        for rid in rows:
            self.assertEqual(rows[rid]["criteria"], before[rid]["criteria"])
            self.assertEqual(rows[rid]["selected_version_id"], before[rid]["selected_version_id"])
            self.assertEqual(rows[rid]["identity_issues"], [])
            self.assertFalse(rows[rid]["shared_study_relationship"]["method_evidence_transferred"])

    def test_second_member_mismatch_cannot_partially_clear_identity(self) -> None:
        rows, correction, evidence = self.identity_fixture()
        rows["W0325"]["selected_version_id"] = "arxiv:2610.04412v2"
        before = copy.deepcopy(rows)
        with self.assertRaisesRegex(ValueError, "IDENTITY_PRIOR_CHANGED"):
            c.apply_identity(rows, correction, evidence)
        self.assertEqual(rows, before)

    def test_identity_cannot_clear_another_issue_or_invent_paper_version(self) -> None:
        rows, correction, evidence = self.identity_fixture()
        correction["referenced_paper_version"] = "v5"
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_IDENTITY"):
            c.apply_identity(rows, correction, evidence)
        correction["referenced_paper_version"] = "UNSPECIFIED_IN_THESIS"
        rows["W0069"]["identity_issues"].append("UNRELATED_SENTINEL_IDENTITY")
        correction["works"]["W0069"]["before_row_sha256"] = r.sha(r.encoded(rows["W0069"]))
        with self.assertRaisesRegex(ValueError, "DIFFERENT_IDENTITY_PROBLEM"):
            c.apply_identity(rows, correction, evidence)

    def test_identity_requires_both_checked_whole_document_scopes(self) -> None:
        rows, correction, evidence = self.identity_fixture()
        correction["works"]["W0325"]["evidence_ids"].remove("W0325whole_document_scope")
        with self.assertRaisesRegex(ValueError, "IDENTITY_SCOPE_PROOF_INCOMPLETE"):
            c.apply_identity(rows, correction, evidence)

    def test_transport_policy_cannot_change_other_works(self) -> None:
        correction = {"before_row_sha256": r.sha(r.encoded(self.row)),
                      "action": "RETAIN_DECLARED_PUBLISHER_EDITION_REMOVE_ADDED_BYTE_TIMESTAMP_REQUIREMENT",
                      "selected_version_id": self.row["selected_version_id"]}
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_VERSION_CORRECTION"):
            c.apply_version(self.row, correction)

    def test_repository_type_cannot_be_assumed_from_doi(self) -> None:
        row = {"review_id": "W0368", "work_id": "doi:10.5281/zenodo.19644135",
               "selected_version_id": "arxiv:2604.18248v4", "bibliography": {
                   "selected": {"date_interval": ["2026-07-30", "2026-07-30"]},
                   "version_issues": ["KNOWN_PUBLISHER_VOR_AVAILABILITY_OR_EXACT_VERSION_UNRESOLVED"]}}
        fields = {"resource_type": {"subtype": "journal-article"}, "doi": "10.5281/zenodo.19644135",
                  "version": "1.0.0", "publication_date": "2026-04-18"}
        evidence = {key: {"field": key, "value": value, "review_id": "W0368"} for key, value in fields.items()}
        correction = {"before_row_sha256": r.sha(r.encoded(row)), "action": "RECLASSIFY_REPOSITORY_DOI_AS_PREPRINT",
                      "selected_version_id": row["selected_version_id"], "evidence_ids": list(fields),
                      "rule_document": "VERSION_RULE_APPLICATION.md",
                      "rule_document_sha256": r.sha((c.HERE / "VERSION_RULE_APPLICATION.md").read_bytes()),
                      "retained_limitations": ["Primary repository declared dates."], "rationale": "Source type and chronology."}
        with self.assertRaisesRegex(ValueError, "PRIMARY_TYPE_OR_CHRONOLOGY"):
            c.apply_version(copy.deepcopy(row), correction, evidence)
        evidence["resource_type"]["value"]["subtype"] = "preprint"
        c.apply_version(row, correction, evidence)
        self.assertEqual(row["selected_version_id"], "arxiv:2604.18248v4")
        self.assertEqual(row["bibliography"]["first_public_date_interval"], ["2026-04-18"] * 2)
        self.assertEqual(row["bibliography"]["status"], "MET")

    def publisher_fixture(self) -> tuple[dict, dict, dict]:
        """Use frozen checked publisher metadata to exercise edition isolation."""
        row = copy.deepcopy(next(x for x in json.loads((c.HERE / "checkpoints/009/FRAME_PROPOSAL.json").read_bytes())["rows"] if x["review_id"] == "W0337"))
        evidence = {x["evidence_id"]: copy.deepcopy(x) for x in json.loads((c.HERE / "releases/011/FACTS.json").read_bytes())["facts"] if x["review_id"] == "W0337"}
        correction = {"action": "SELECT_CHECKED_PUBLISHER_EDITION",
                      "before_row_sha256": r.sha(r.encoded(row)),
                      "previous_selected_version_id": row["selected_version_id"],
                      "selected_version_id": row["work_id"] + ":publisher:declared-2026-08-25",
                      "rule_document": "PUBLISHER_EDITION_APPLICATION.md",
                      "rule_document_sha256": r.sha((c.HERE / "PUBLISHER_EDITION_APPLICATION.md").read_bytes()),
                      "evidence_ids": list(evidence), "rationale": "Checked VOR history overrides issue month.",
                      "retained_limitations": ["No scientific support transferred."]}
        return row, correction, evidence

    def test_publisher_preference_preserves_memberships_and_resets_science(self) -> None:
        row, correction, evidence = self.publisher_fixture()
        original = copy.deepcopy(row)
        c.apply_version(row, correction, evidence)
        self.assertEqual(row["memberships"], original["memberships"])
        self.assertEqual(row["bibliography"]["first_public_date_interval"], original["bibliography"]["first_public_date_interval"])
        self.assertEqual(row["bibliography"]["selected"]["date_interval"], ["2026-08-25"] * 2)
        self.assertEqual(set(row["criteria"].values()), {"UNCLEAR"})
        self.assertFalse(row["bibliography"]["selected_method_body_supported"])
        self.assertIsNone(row["positive_experiment_binding"])

    def test_publisher_issue_month_cannot_replace_primary_publication_date(self) -> None:
        row, correction, evidence = self.publisher_fixture()
        for fact in evidence.values():
            if fact["field_path"] == "bibliographic_scope_facts.declared_dates":
                fact["value"]["published"] = "2026-09"
        with self.assertRaisesRegex(ValueError, "HEADER_PROOF_INCOMPLETE"):
            c.apply_version(row, correction, evidence)

    def test_publisher_metadata_cannot_bind_a_different_capture(self) -> None:
        row, correction, evidence = self.publisher_fixture()
        next(iter(evidence.values()))["version"] += "-different"
        with self.assertRaisesRegex(ValueError, "MIXED_PUBLISHER_CAPTURES"):
            c.apply_version(row, correction, evidence)


if __name__ == "__main__":
    unittest.main()
