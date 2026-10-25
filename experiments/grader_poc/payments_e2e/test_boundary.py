"""Check that the negative assertion cannot pass without real progress evidence."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from experiments.grader_poc.payments_e2e.boundary_check import classify, make_plan, running_worker_status


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.balances = {f"account-{index}": 10 + index for index in range(8)}
        self.excluded = ["account-0"]
        self.plan = make_plan(self.balances, self.excluded, "single", "test")
        self.callbacks = [{"user_id": row["user_id"], "transaction_id": row["required_callback"], "balance_after": -1} for row in self.plan]

    def test_arithmetic_and_progress_for_every_case(self):
        for case in self.plan:
            balance = case["initial_balance"]
            for index, txn in enumerate(case["transactions"]):
                balance -= txn["amount"]
                if index == 0:
                    self.assertEqual(balance, case["target_balance"])
            self.assertEqual(balance, -1)

    def test_separate_phases_do_not_reuse_mutated_or_original_sample_accounts(self):
        second = make_plan(self.balances, self.excluded, "overlap", "test-2")
        self.assertFalse({x["user_id"] for x in self.plan} & {x["user_id"] for x in second})
        self.assertNotIn("account-0", [x["user_id"] for x in self.plan + second])

    def test_empty_or_wrong_progress_is_inconclusive(self):
        self.assertEqual(classify(self.plan, [])["status"], "PROGRESS_NOT_CONFIRMED")
        self.callbacks[0]["balance_after"] = 7
        self.assertEqual(classify(self.plan, self.callbacks)["status"], "PROGRESS_NOT_CONFIRMED")

    def test_zero_callback_rejected_with_passing_progress_controls(self):
        self.callbacks.append({"user_id": self.plan[0]["user_id"], "transaction_id": self.plan[0]["forbidden_callback"], "balance_after": 0})
        self.assertEqual(classify(self.plan, self.callbacks)["status"], "COUNTEREXAMPLE")

    def test_positive_callback_also_rejected(self):
        self.callbacks.append({"user_id": self.plan[1]["user_id"], "transaction_id": self.plan[1]["forbidden_callback"], "balance_after": 1})
        self.assertEqual(classify(self.plan, self.callbacks)["status"], "COUNTEREXAMPLE")

    def test_negative_callbacks_allowed(self):
        self.assertEqual(classify(self.plan, self.callbacks)["status"], "NO_FALSE_POSITIVE_IN_OBSERVATION_WINDOW")

    def test_intentionally_stopped_extra_slot_does_not_invalidate_single_worker(self):
        def supervisor(command, *names):
            if not names:
                raise RuntimeError("supervisor exits 3 when extra is STOPPED")
            return SimpleNamespace(stdout="\n".join(name + " RUNNING pid 1" for name in names))
        upstream = SimpleNamespace(PRIMARY_WORKER="primary", EXTRA_WORKER="extra", supervisorctl=Mock(side_effect=supervisor))
        self.assertIn("primary RUNNING", running_worker_status(upstream, "single"))
        upstream.supervisorctl.assert_called_with("status", "primary")
        self.assertIn("extra RUNNING", running_worker_status(upstream, "overlap"))
        upstream.supervisorctl.assert_called_with("status", "primary", "extra")

    def test_required_worker_not_running_is_rejected(self):
        upstream = SimpleNamespace(PRIMARY_WORKER="primary", EXTRA_WORKER="extra",
                                   supervisorctl=lambda *args: SimpleNamespace(stdout="primary STOPPED"))
        with self.assertRaises(AssertionError):
            running_worker_status(upstream, "single")


if __name__ == "__main__":
    unittest.main()
