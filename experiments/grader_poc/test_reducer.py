"""Check reducer validity without running candidate code or Docker."""

import unittest

from experiments.grader_poc.diagnose import reduce_trace
from experiments.grader_poc.oracle import expected_sessions
from experiments.grader_poc.test_oracle import trace


class ReducerTests(unittest.TestCase):
    def test_preserves_unknown_boundaries_and_input(self):
        original = trace([(0, 1), (20, 3), (10, 2), (100, 1)])

        def witness(events):
            known = expected_sessions(events, 15, max_events=12)["status"] == "KNOWN"
            return known and {(0, 1), (20, 3), (10, 2)} <= {(e["time"], e["value"]) for e in events}

        reduced = reduce_trace(original, witness)
        self.assertEqual(len(original), 4)
        self.assertEqual(reduced, trace([(0, 1), (20, 3), (10, 2)]))
        self.assertTrue(witness(reduced))
        self.assertTrue(all(not witness(reduced[:i] + reduced[i + 1:]) for i in range(len(reduced))))

    def test_scalar_reduction_can_enable_later_deletion(self):
        original = trace([(10, 8), (20, 8)])

        def witness(events):
            return bool(events) and (len(events) == 2 or events[0]["value"] == 1)

        self.assertEqual(reduce_trace(original, witness), trace([(0, 1)]))


if __name__ == "__main__":
    unittest.main()
