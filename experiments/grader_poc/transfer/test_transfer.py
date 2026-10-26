"""Test prompt contracts before reference or assertion inspection."""

import copy
import unittest

from .properties import (alternative_18, alternative_57, alternative_87,
                         config, expected, in_domain, property_holds, witness_inputs)
from .run import witness_check


class PropertyTests(unittest.TestCase):
    def test_coordinate_multiplicity_and_order_are_not_set_equality(self) -> None:
        args = [[[1, 0, 1], [1]], 1]
        self.assertEqual(expected('HumanEval/87', args), [(0, 2), (0, 0), (1, 0)])
        for wrong in [[(0, 0), (0, 2), (1, 0)], [(0, 2), (0, 0)], [(0, 2), (0, 0), (1, 0), (1, 0)], [[0, 2], [0, 0], [1, 0]]]:
            self.assertFalse(property_holds('HumanEval/87', args, wrong))

    def test_monotonicity_ambiguity_is_an_abstention(self) -> None:
        for values in [[], [1], [1, 1], [1, 2, 2], [True, False]]:
            self.assertFalse(in_domain('HumanEval/57', [values]))
            with self.assertRaisesRegex(ValueError, 'OUT_OF_DECLARED_DOMAIN'):
                expected('HumanEval/57', [values])
        self.assertTrue(expected('HumanEval/57', [[-2, -1, 3]]))
        self.assertFalse(expected('HumanEval/57', [[-2, 3, -1]]))

    def test_overlap_empty_text_and_short_text(self) -> None:
        self.assertEqual(expected('HumanEval/18', ['aaaa', 'aa']), 3)
        self.assertEqual(expected('HumanEval/18', ['', 'a']), 0)
        self.assertEqual(expected('HumanEval/18', ['a', 'aa']), 0)
        self.assertFalse(property_holds('HumanEval/18', ['a', 'a'], True))
        with self.assertRaises(ValueError):
            expected('HumanEval/18', ['a', ''])

    def test_frozen_alternatives_agree_without_mutating_inputs(self) -> None:
        functions = {'HumanEval/87': alternative_87, 'HumanEval/57': alternative_57, 'HumanEval/18': alternative_18}
        for task in config()['task_ids']:
            cases = witness_inputs(task)
            self.assertEqual(cases, witness_inputs(task))
            self.assertEqual(len(cases), config()['witness_count'])
            for case in cases:
                args = copy.deepcopy(case['args'])
                self.assertTrue(property_holds(task, case['args'], functions[task](*args)))
                self.assertEqual(args, case['args'])

    def test_witness_detects_order_error_but_not_valid_alternative(self) -> None:
        cases = [{'args': [[[1, 1]], 1], 'kind': 'test'}]
        correct = lambda rows, target: [(0, 1), (0, 0)]
        good = witness_check('HumanEval/87', alternative_87, correct, cases)
        self.assertEqual(good['status'], 'NOT_FOUND_WITHIN_BUDGET')
        bad = witness_check('HumanEval/87', lambda rows, target: [(0, 0), (0, 1)], correct, cases)
        self.assertEqual(bad['status'], 'FOUND')
        self.assertEqual(bad['failure_count'], 1)

    def test_reference_error_and_scope_error_never_become_candidate_findings(self) -> None:
        with self.assertRaises(ValueError):
            witness_check('HumanEval/18', alternative_18, lambda text, sub: 0,
                          [{'args': ['aa', 'a']}])
        with self.assertRaisesRegex(ValueError, 'OUT_OF_DECLARED_DOMAIN'):
            witness_check('HumanEval/57', alternative_57, alternative_57,
                          [{'args': [[1, 1]]}])

    def test_candidate_exception_is_retained_as_scoped_violation(self) -> None:
        def broken(text: str, sub: str) -> int:
            raise IndexError('candidate failure')
        result = witness_check('HumanEval/18', broken, alternative_18,
                               [{'args': ['', 'a']}])
        self.assertEqual(result['first_witness']['observed']['exception_type'], 'IndexError')


if __name__ == '__main__':
    unittest.main()
