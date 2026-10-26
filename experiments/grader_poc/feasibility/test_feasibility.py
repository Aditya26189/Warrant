"""Controls for oracle scope and non-exposure; no benchmark discovery tests."""

import gzip
import copy
import json
import unittest
from pathlib import Path

from .calibration import alternative, expected_from_spec, in_domain, property_holds, property_inputs
from .prepare import select_records
from .run_calibration import control_passed, control_code

CONFIG = json.loads(Path(__file__).with_name("config.json").read_bytes())


class CalibrationContractTests(unittest.TestCase):
    def test_distinct_positions_and_strict_boundary(self) -> None:
        for numbers, threshold, expected in (
            ([], 0.25, False), ([0.0], 0.25, False),
            ([0.0, 0.0], 0.25, True), ([0.0, 0.25], 0.25, False),
            ([0.0, 0.25], 0.5, True), ([-0.5, -0.25], 0.25, False),
            ([0.0, 4.0, 0.25], 0.5, True),
        ):
            with self.subTest(numbers=numbers, threshold=threshold):
                self.assertIs(expected_from_spec(numbers, threshold, CONFIG["domain"]), expected)

    def test_out_of_scope_is_not_a_spec_failure(self) -> None:
        for numbers, threshold in (
            ([float("nan")], 0.25), ([float("inf")], 0.25),
            ([0.1], 0.25), ([True], 0.25), ([0.0], 0.0),
            ([5.0], 0.25), ([0.0] * 9, 0.25), ([0.0], 0.1),
        ):
            with self.subTest(numbers=numbers, threshold=threshold):
                self.assertFalse(in_domain(numbers, threshold, CONFIG["domain"]))
                with self.assertRaises(ValueError):
                    expected_from_spec(numbers, threshold, CONFIG["domain"])

    def test_property_rejects_wrong_boolean_and_nonboolean(self) -> None:
        self.assertTrue(property_holds(True, [0.0, 0.0], 0.25, CONFIG["domain"]))
        self.assertFalse(property_holds(False, [0.0, 0.0], 0.25, CONFIG["domain"]))
        self.assertFalse(property_holds(1, [0.0, 0.0], 0.25, CONFIG["domain"]))

    def test_alternative_preserves_input_and_handles_order(self) -> None:
        numbers = [4.0, 0.25, -4.0, 0.0]
        before = numbers.copy()
        self.assertTrue(alternative(numbers, 0.5))
        self.assertEqual(numbers, before)
        self.assertFalse(alternative(numbers, 0.25))

    def test_corpus_is_reproducible_and_inside_declared_domain(self) -> None:
        cases = property_inputs(CONFIG)
        self.assertEqual(cases, property_inputs(CONFIG))
        self.assertEqual(sum(c["kind"] == "seeded" for c in cases),
                         CONFIG["corpus"]["random_inputs"])
        self.assertTrue(all(in_domain(c["numbers"], c["threshold"], CONFIG["domain"])
                            for c in cases))

    def test_reservations_never_export_reference_or_tests(self) -> None:
        rows = [{"task_id": f"HumanEval/{i}", "prompt": "public prompt",
                 "contract": "public contract", "entry_point": "f",
                 "canonical_solution": "PRIVATE_REFERENCE_SENTINEL",
                 "plus_input": ["PRIVATE_TEST_SENTINEL"]} for i in range(6)]
        archive = gzip.compress(b"\n".join(json.dumps(r).encode() for r in rows))
        calibration, selection = select_records(archive, CONFIG)
        text = json.dumps(selection)
        self.assertNotIn("PRIVATE_REFERENCE_SENTINEL", text)
        self.assertNotIn("PRIVATE_TEST_SENTINEL", text)
        self.assertNotIn(CONFIG["calibration_id"], selection["reserved_ids"])
        self.assertEqual(len(selection["reserved_ids"]), CONFIG["reserved_count"])
        self.assertEqual(calibration["task_id"], CONFIG["calibration_id"])

    def test_gate_rejects_incomplete_grading_and_apparatus_failure(self) -> None:
        receipt = {
            "execution_status": "COMPLETED",
            "result": {"full_grader_seconds": 0.1,
                       "property": {"checked_count": 2, "mismatches": []},
                       "grader": {"base": {"status": "pass", "input_count": 3,
                                            "checked_count": 3, "passed_count": 3}}},
        }
        self.assertTrue(control_passed(receipt, {"base": 3}, 2, 2.0))
        incomplete = copy.deepcopy(receipt)
        incomplete["result"]["grader"]["base"]["checked_count"] = 0
        self.assertFalse(control_passed(incomplete, {"base": 3}, 2, 2.0))
        self.assertFalse(control_passed({"execution_status": "TIMEOUT"}, {"base": 3}, 2, 2.0))
        bad_property = copy.deepcopy(receipt)
        bad_property["result"]["property"]["mismatches"] = [{"index": 0}]
        self.assertFalse(control_passed(bad_property, {"base": 3}, 2, 2.0))

    def test_gate1_has_no_arbitrary_candidate_interface(self) -> None:
        with self.assertRaises(ValueError):
            control_code({}, "mutant")


if __name__ == "__main__":
    unittest.main()
