"""Exercise the restriction and identity boundary before scientific consumption."""
from __future__ import annotations

import copy
import unittest

import release_deep as r


class ReleaseBoundaryTests(unittest.TestCase):
    """A successful check must never release a different or held method claim."""

    def setUp(self) -> None:
        self.packet = {"review_id": "W0001", "provider_actor": "provider",
                       "method_summary": "Input method.", "arm_inventory": [{"unit": "prompt"}],
                       "english_evaluation_support": "Unestablished.",
                       "coverage": {"scope_completeness": "PARTIAL"}}
        self.raw = r.encoded(self.packet)
        self.check = {"actor": "checker", "review_id": "W0001",
                      "provider_packet_sha256": r.sha(self.raw),
                      "mechanical_check": {"raw_hash_verified": True, "acquisition_hash_verified": True,
                                           "provider_locator_mismatches": []},
                      "restriction_check": {"outcomes_transferred": False, "eligibility_judgments_transferred": False},
                      "per_fact": [{"field_path": "method_summary", "decision": "APPROVE",
                                    "semantic_fidelity": "Supported.", "restriction_rationale": "Method only."},
                                   {"field_path": "english_evaluation_support", "decision": "HOLD"}]}

    def test_held_and_unapproved_scope_never_release(self) -> None:
        facts = r.checked_fields(self.check, self.packet, self.raw)
        self.assertEqual([f["field_path"] for f in facts], ["method_summary"])
        self.assertEqual(facts[0]["value_sha256"], r.sha(r.encoded("Input method.")))

    def test_post_check_mutation_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "CHANGED_AFTER_CHECK"):
            r.checked_fields(self.check, self.packet, self.raw + b" ")

    def test_self_check_rejected(self) -> None:
        check = copy.deepcopy(self.check)
        check["actor"] = "provider"
        with self.assertRaisesRegex(ValueError, "SEPARATE_ACTUAL_ACTORS"):
            r.checked_fields(check, self.packet, self.raw)

    def test_capture_identity_cannot_release_scientific_methods(self) -> None:
        check = copy.deepcopy(self.check)
        check["requested_capture_identity"] = "publisher-bytes"
        check["restriction_check"]["scientific_methods_transferred"] = False
        with self.assertRaisesRegex(ValueError, "CAPTURE_METADATA_IS_NOT_SCIENTIFIC_METHOD"):
            r.checked_fields(check, self.packet, self.raw)

    def test_foreign_work_rejected(self) -> None:
        check = copy.deepcopy(self.check)
        check["review_id"] = "W0002"
        with self.assertRaisesRegex(ValueError, "FOREIGN_WORK"):
            r.checked_fields(check, self.packet, self.raw)

    def test_restriction_and_locator_failures_rejected(self) -> None:
        for section, key, value, message in [
            ("restriction_check", "outcomes_transferred", True, "RESTRICTION_FAILURE"),
            ("restriction_check", "eligibility_judgments_transferred", True, "RESTRICTION_FAILURE"),
            ("mechanical_check", "provider_locator_mismatches", [1], "SOURCE_BINDING"),
            ("mechanical_check", "raw_hash_verified", False, "SOURCE_BINDING")]:
            with self.subTest(key=key):
                check = copy.deepcopy(self.check)
                check[section][key] = value
                with self.assertRaisesRegex(ValueError, message):
                    r.checked_fields(check, self.packet, self.raw)

    def test_paths_are_restricted(self) -> None:
        self.assertEqual(r.field(self.packet, "arm_inventory[0]"), {"unit": "prompt"})
        self.assertEqual(r.field(self.packet, "coverage.scope_completeness"), "PARTIAL")
        for path in ["provider_actor", "__class__", "arm_inventory[-1]", "coverage.__class__()",
                     "architecture_clarification.outcomes", "additional_primary_method_images[-1]"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                r.field(self.packet, path)

    def test_verified_access_gap_releases_no_method_facts(self) -> None:
        check = copy.deepcopy(self.check)
        check["mechanical_check"] = {"raw_body_available": False, "acquisition_hash_verified": True}
        self.assertEqual(r.checked_fields(check, self.packet, self.raw), [])

    def test_access_gap_still_requires_explicit_restriction_pass(self) -> None:
        check = copy.deepcopy(self.check)
        check["mechanical_check"] = {"raw_body_available": False, "acquisition_hash_verified": True}
        check["restriction_check"]["outcomes_transferred"] = True
        with self.assertRaisesRegex(ValueError, "RESTRICTION_FAILURE"):
            r.checked_fields(check, self.packet, self.raw)


if __name__ == "__main__":
    unittest.main()
