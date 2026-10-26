"""Test scientific outcome boundaries and mutation locality, without task runs."""

import ast
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from .candidates import load_inputs, mutations, witness_inputs
from .run import classification, control_valid, grader_verdict, run, run_process, selected_code, witness_check


class MutationTests(unittest.TestCase):
    def test_one_edit_preserves_non_ascii_comments_docstrings_annotations(self) -> None:
        source = ('def f(x: int = 1) -> int:\n'
                  '    """2 + 1 < 3 must stay as text."""\n'
                  '    # café is not a mutation target\n'
                  '    if x < 1:\n        return True\n    return x + 1\n')
        operators = load_inputs()[0]["operators"]
        candidates = mutations(source, "f", operators)
        self.assertTrue(candidates)
        self.assertEqual(candidates, mutations(source, "f", operators))
        for candidate in candidates:
            raw = source.encode()
            expected = (raw[:candidate["start_byte"]] + candidate["replacement"].encode()
                        + raw[candidate["end_byte"]:])
            self.assertEqual(candidate["source"].encode(), expected)
            self.assertIn('def f(x: int = 1) -> int:', candidate["source"])
            self.assertIn('"""2 + 1 < 3 must stay as text."""', candidate["source"])
            self.assertIn('# café is not a mutation target', candidate["source"])
            ast.parse(candidate["source"])

    def test_duplicate_numeric_replacements_are_not_double_counted(self) -> None:
        candidates = mutations('def f():\n    return 1\n', 'f', ['numeric_offset'])
        self.assertEqual([c["replacement"] for c in candidates], ["0", "2"])

    def test_arithmetic_site_does_not_mutate_comments(self) -> None:
        source = 'def f(x):\n    return (x # +\n            + 1)\n'
        candidates = mutations(source, 'f', ['arithmetic_swap'])
        self.assertEqual(len(candidates), 1)
        self.assertIn('x # +\n            - 1', candidates[0]["source"])

    def test_witness_budget_reuses_all_seeded_cases(self) -> None:
        config, calibration, _ = load_inputs()
        cases = witness_inputs(config, calibration)
        self.assertEqual(len(cases), config["witness_count"])
        self.assertTrue(all(c['kind'] == 'seeded' for c in cases))
        with self.assertRaises(AssertionError):
            witness_inputs({**config, "witness_count": 1}, calibration)


class OutcomeTests(unittest.TestCase):
    def test_incomplete_or_timed_out_grader_is_not_a_kill(self) -> None:
        passed = {"status": "pass", "input_count": 3, "checked_count": 3, "passed_count": 3}
        self.assertEqual(grader_verdict({"base": passed, "plus": passed}), "PASS")
        self.assertEqual(grader_verdict({"base": passed, "plus": {**passed, "status": "timeout"}}), "UNAVAILABLE")
        self.assertEqual(grader_verdict({"base": passed, "plus": {**passed, "checked_count": 0}}), "UNAVAILABLE")
        self.assertEqual(grader_verdict({"base": passed, "plus": {**passed, "status": "fail", "passed_count": 2}}), "FAIL")

    def test_witness_requires_spec_violation_and_accepts_alternative_behavior(self) -> None:
        _, calibration, _ = load_inputs()
        domain = calibration["domain"]
        cases = [{"numbers": [0.0, 0.0], "threshold": 0.25, "kind": "test"}]
        reference = lambda numbers, threshold: True
        valid = witness_check(lambda numbers, threshold: bool(len(numbers)), reference, cases, domain)
        self.assertEqual(valid["status"], "NOT_FOUND_WITHIN_BUDGET")
        wrong_type = witness_check(lambda numbers, threshold: 1, reference, cases, domain)
        self.assertEqual(wrong_type["status"], "FOUND")
        self.assertEqual(wrong_type["first_witness"]["observed"]["type"], "int")
        with self.assertRaises(ValueError):
            witness_check(reference, lambda numbers, threshold: False, cases, domain)

    def test_candidate_exception_is_a_scoped_witness(self) -> None:
        _, calibration, _ = load_inputs()
        def broken(numbers: list, threshold: float) -> bool:
            raise IndexError("candidate broke")
        result = witness_check(broken, lambda numbers, threshold: False,
                               [{"numbers": [], "threshold": 0.25}], calibration["domain"])
        self.assertEqual(result["first_witness"]["observed"]["exception_type"], "IndexError")

    def test_timeout_and_oracle_error_never_become_findings(self) -> None:
        self.assertEqual(classification({"execution_status": "TIMEOUT"}), "TIMEOUT")
        receipt = {"execution_status": "COMPLETED", "result": {"candidate_status": "VALID",
                   "grader_verdict": "PASS", "witness": {"status": "ORACLE_ERROR"}}}
        self.assertEqual(classification(receipt), "ORACLE_ERROR")
        self.assertFalse(control_valid(receipt, 200))
        receipt["result"]["witness"] = {"status": "NOT_FOUND_WITHIN_BUDGET", "checked_count": 0, "failure_count": 0}
        self.assertFalse(control_valid(receipt, 200))

    def test_worker_refuses_arbitrary_identity(self) -> None:
        with self.assertRaises(ValueError):
            selected_code("../unreviewed.py", load_inputs()[2])

    def test_preflight_failure_leaves_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "failed"
            with patch('experiments.grader_poc.baseline.run.clean_revision', return_value='wrong'):
                with self.assertRaises((ValueError, RuntimeError)):
                    run(Path(directory), target)
            receipt = json.loads((target / 'outcome.json').read_bytes())
            self.assertEqual(receipt['status'], 'HARNESS_ERROR')
            self.assertEqual(receipt['receipts'], [])

    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group runner')
    def test_real_timeout_retains_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt = run_process([sys.executable, '-c', 'import time; time.sleep(30)'],
                                  0.1, os.environ.copy(), Path(directory), 'timeout')
            self.assertEqual(receipt['execution_status'], 'TIMEOUT')
            self.assertEqual(json.loads((Path(directory) / 'timeout.json').read_bytes()), receipt)


if __name__ == "__main__":
    unittest.main()
