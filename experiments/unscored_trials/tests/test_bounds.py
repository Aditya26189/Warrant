"""Logical and accounting counterexamples for exact unknown-outcome bounds."""

from __future__ import annotations

import itertools
import sys
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

RESEARCH_MODULE_DIR = Path(__file__).resolve().parents[1]
if str(RESEARCH_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_MODULE_DIR))

from bounds import (  # noqa: E402
    aggregate_tasks,
    cap_bounds,
    classify_pair,
    difference_bounds,
    retry_diagnostic,
    validate_score,
    weighted_bounds,
    weighted_mean,
)

F = Fraction


class FixedPopulationBoundsTests(unittest.TestCase):
    """Keep unscored rewards free while observed rewards and weights stay fixed."""

    def test_all_scored_bounds_collapse(self) -> None:
        self.assertEqual(weighted_bounds([0, F(1, 2), 1]), (F(1, 2), F(1, 2)))
        self.assertEqual(weighted_mean([0, F(1, 2), 1]), F(1, 2))

    def test_all_unknown_bounds_span_unit_interval(self) -> None:
        weights = [F(1, 7), F(6, 7)]
        self.assertEqual(weighted_bounds([None, None], weights), (F(0), F(1)))
        self.assertEqual(weighted_mean([None, None], weights), 0)
        self.assertEqual(weighted_mean([None, None], weights, unknown_value=1), 1)

    def test_fractional_rewards_and_unequal_weights_use_reward_mass(self) -> None:
        rewards = [None, F(1, 4), 1]
        weights = [F(1, 2), F(1, 3), F(1, 6)]
        self.assertEqual(weighted_bounds(rewards, weights), (F(1, 4), F(3, 4)))
        self.assertEqual(weighted_mean(rewards, weights), F(1, 4))
        self.assertEqual(weighted_mean(rewards, weights, F(1, 2)), F(1, 2))

    def test_zero_weight_unknown_adds_no_uncertainty(self) -> None:
        self.assertEqual(weighted_bounds([None, F(1, 4)], [0, 1]), (F(1, 4), F(1, 4)))

    def test_decimals_and_reported_float_values_are_exact(self) -> None:
        self.assertEqual(validate_score(0.1), F(1, 10))
        self.assertEqual(validate_score(Decimal("0.1234567890123456789")),
                         F(1234567890123456789, 10**19))
        self.assertEqual(weighted_mean([F(1, 3), Decimal("0.1"), 0.2]), F(19, 90))

    def test_zero_and_unknown_remain_distinct(self) -> None:
        self.assertIsNone(validate_score(None))
        self.assertEqual(validate_score(0), F(0))
        self.assertEqual(weighted_bounds([0]), (F(0), F(0)))
        self.assertEqual(weighted_bounds([None]), (F(0), F(1)))

    def test_invalid_scores_are_not_silently_unknown_or_zero(self) -> None:
        invalid = [True, False, "0.5", {}, [], -1, F(11, 10), float("nan"),
                   float("inf"), float("-inf"), Decimal("NaN"), Decimal("Infinity")]
        for value in invalid:
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    validate_score(value)
                with self.assertRaises(ValueError):
                    weighted_bounds([value])

    def test_weights_require_a_nonempty_fixed_population_and_exact_unit_sum(self) -> None:
        invalid = [([], None), ([0, 1], [1]), ([0, 1], [0, 0]),
                   ([0, 1], [F(-1, 2), F(3, 2)]), ([0, 1], [None, 1]),
                   ([0, 1], [True, False]), ([0, 1], [F(1, 3), F(1, 3)])]
        for rewards, weights in invalid:
            with self.subTest(rewards=rewards, weights=weights):
                with self.assertRaises(ValueError):
                    weighted_bounds(rewards, weights)

    def test_corner_completions_attain_both_weighted_extrema(self) -> None:
        weights = [F(1, 2), F(1, 3), F(1, 6)]
        for rewards in itertools.product((None, F(0), F(1, 4), F(1)), repeat=3):
            unknown_indices = [index for index, reward in enumerate(rewards) if reward is None]
            completed_means = []
            for fills in itertools.product((F(0), F(1)), repeat=len(unknown_indices)):
                completed = list(rewards)
                for index, value in zip(unknown_indices, fills, strict=True):
                    completed[index] = value
                completed_means.append(sum(weight * reward for weight, reward
                                           in zip(weights, completed, strict=True)))
            self.assertEqual(weighted_bounds(rewards, weights),
                             (min(completed_means), max(completed_means)))


class PairComparisonTests(unittest.TestCase):
    """Boundary cases distinguish equality from an actually compatible reversal."""

    def test_shared_missing_task_identity_does_not_cancel_unknown_rewards(self) -> None:
        # Both systems have the same observed task and the same unknown task.
        a_bounds = weighted_bounds([1, None])
        b_bounds = weighted_bounds([1, None])
        possible = [weighted_mean([1, a]) - weighted_mean([1, b])
                    for a, b in itertools.product((0, 1), repeat=2)]
        self.assertEqual(difference_bounds(a_bounds, b_bounds), (F(-1, 2), F(1, 2)))
        self.assertEqual((min(possible), max(possible)), difference_bounds(a_bounds, b_bounds))

    def test_strict_robust_orders_are_symmetric(self) -> None:
        a, b = (F(3, 4), F(1)), (F(0), F(1, 2))
        forward = classify_pair(a, b, F(3, 4), F(0))
        backward = classify_pair(b, a, F(0), F(3, 4))
        self.assertEqual(forward["classification"], "strict_robust")
        self.assertEqual(forward["robust_order"], "a")
        self.assertEqual(backward["robust_order"], "b")
        self.assertFalse(forward["equality_possible"])

    def test_identified_tie_requires_singleton_zero_difference(self) -> None:
        result = classify_pair((F(1, 3), F(1, 3)), (F(1, 3), F(1, 3)), F(1, 3), F(1, 3))
        self.assertEqual(result["classification"], "identified_tie")
        self.assertEqual(result["robust_order"], "tie")
        self.assertFalse(result["native_tie_can_break"])

    def test_touching_lower_endpoint_permits_equality_but_not_reversal(self) -> None:
        result = classify_pair((F(1, 2), F(1)), (F(1, 4), F(1, 2)), F(1, 2), F(1, 4))
        self.assertEqual(result["difference_lower"], 0)
        self.assertEqual(result["classification"], "equality_compatible")
        self.assertTrue(result["equality_possible"])
        self.assertFalse(result["b_strict_possible"])
        reverse = classify_pair((F(1, 4), F(1, 2)), (F(1, 2), F(1)), F(1, 4), F(1, 2))
        self.assertEqual(reverse["difference_upper"], 0)
        self.assertEqual(reverse["classification"], "equality_compatible")

    def test_strict_reversal_compatibility_is_not_an_observed_reversal(self) -> None:
        result = classify_pair((F(1, 2), F(1)), (F(0), F(3, 4)), F(1, 2), F(0))
        self.assertEqual(result["native_order"], "a")
        self.assertEqual(result["classification"], "reversal_compatible")
        self.assertIsNone(result["robust_order"])
        self.assertEqual(result["difference_lower"], F(-1, 4))
        self.assertTrue(result["b_strict_possible"])

    def test_unresolved_native_tie_is_not_called_a_reversal(self) -> None:
        result = classify_pair((0, 1), (0, 1), 0, 0)
        self.assertEqual(result["native_order"], "tie")
        self.assertEqual(result["classification"], "equality_compatible")
        self.assertTrue(result["native_tie_can_break"])
        self.assertTrue(result["a_strict_possible"])
        self.assertTrue(result["b_strict_possible"])

    def test_invalid_bounds_or_outside_native_point_fail(self) -> None:
        for interval in ((1, 0), (-1, 1), (0, 2), (0,), (None, 1)):
            with self.subTest(interval=interval):
                with self.assertRaises(ValueError):
                    difference_bounds(interval, (0, 1))
        with self.assertRaises(ValueError):
            classify_pair((F(1, 2), 1), (0, F(1, 4)), 0, 0)


class AccountingPolicyTests(unittest.TestCase):
    """Sensitivity changes weights transparently and never invents trial lineage."""

    def test_cap_rejects_empirically_violated_missingness(self) -> None:
        with self.assertRaises(ValueError):
            cap_bounds(F(1, 2), F(1, 20), F(20, 205))
        with self.assertRaises(ValueError):
            cap_bounds(F(1, 2), F(1, 20), F(1, 20) + F(1, 10**20))

    def test_valid_cap_encloses_every_smaller_missingness_completion(self) -> None:
        q, cap = F(2, 5), F(1, 10)
        interval = cap_bounds(q, cap, cap)
        self.assertEqual(interval, (F(9, 25), F(23, 50)))
        for missing in (F(0), F(1, 20), cap):
            for fill in (F(0), F(1, 3), F(1)):
                value = (1 - missing) * q + missing * fill
                self.assertLessEqual(interval[0], value)
                self.assertLessEqual(value, interval[1])
        self.assertEqual(cap_bounds(q, 0, 0), (q, q))

    def test_legitimate_unequal_repetitions_define_different_estimands(self) -> None:
        result = aggregate_tasks([("easy", 1), ("easy", 1), ("easy", 1), ("hard", 0)])
        self.assertEqual(result["record_count"], 4)
        self.assertEqual(result["task_count"], 2)
        self.assertEqual(result["equal_task"]["native_mean"], F(1, 2))
        self.assertEqual(result["pooled"]["native_mean"], F(3, 4))
        self.assertEqual(result["equal_task"]["bounds"], (F(1, 2), F(1, 2)))
        self.assertEqual(result["pooled"]["bounds"], (F(3, 4), F(3, 4)))

    def test_named_unknown_final_record_is_not_an_absent_planned_record(self) -> None:
        result = aggregate_tasks([("one", 1), ("one", None), ("two", 0)])
        self.assertEqual(result["unknown_record_count"], 1)
        self.assertEqual(result["equal_task"]["native_mean"], F(1, 4))
        self.assertEqual(result["equal_task"]["bounds"], (F(1, 4), F(1, 2)))
        self.assertEqual(result["equal_task"]["missing_weight"], F(1, 4))
        self.assertEqual(result["pooled"]["bounds"], (F(1, 3), F(2, 3)))
        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["task_counts"], {"one": 2, "two": 1})

    def test_empty_or_unidentified_task_population_fails(self) -> None:
        for records in ([], [("", 1)], [(None, 1)], [("task", True)]):
            with self.subTest(records=records):
                with self.assertRaises(ValueError):
                    aggregate_tasks(records)

    def test_no_retry_conclusion_from_repetitions_or_unvalidated_lineage(self) -> None:
        no_lineage = retry_diagnostic()
        self.assertEqual(no_lineage["status"], "unavailable")
        self.assertIsNone(no_lineage["inferred_retries"])
        for lineage in ([], [{"task": "same"}, {"task": "same"}], {"parent": "trial-1"}):
            with self.subTest(lineage=lineage):
                result = retry_diagnostic(lineage)
                self.assertEqual(result["status"], "unsupported")
                self.assertIsNone(result["inferred_retries"])


if __name__ == "__main__":
    unittest.main()
