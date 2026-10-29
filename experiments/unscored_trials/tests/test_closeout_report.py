"""Small counterexamples for report interpretation and pending human review."""

from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from experiments.unscored_trials import closeout_report as report


def _policy(submission: str, policy: str, mean: str, upper: str,
            repetitions: dict | None = None) -> dict:
    repetitions = {"t1": 2, "t2": 2} if repetitions is None else repetitions
    return {"submission": submission, "policy": policy,
            "native_operational_zero_mean": mean, "score_completion_lower": mean,
            "score_completion_upper": upper, "record_count": str(sum(repetitions.values())),
            "task_count": str(len(repetitions)), "task_repetition_counts": json.dumps(repetitions),
            "task_definition_signature": "same", "unknown_record_count": "1" if upper != mean else "0"}


def _pair(a: str, b: str, native_a: str, native_b: str, lower: str, upper: str,
          classification: str, order: str, tie_break: bool = False) -> dict:
    return {"submission_a": a, "submission_b": b, "policy": "equal_task",
            "native_a": native_a, "native_b": native_b, "difference_lower": lower,
            "difference_upper": upper, "classification": classification,
            "native_order": order, "native_tie_can_break": str(tie_break)}


class StructuralInterpretationTests(unittest.TestCase):
    """Policy equality must not be mistaken for general weighting robustness."""

    def test_uniform_repetitions_expose_identical_record_weights(self) -> None:
        rows = [_policy("A", name, "0.5", "0.75") for name in ("equal_task", "pooled")]
        result = report.explain_weighting(rows)[0]
        self.assertTrue(result["within_submission_uniform"])
        self.assertTrue(result["record_weights_identical"])
        self.assertEqual(result["equal_task_record_weight"], "1/4")
        self.assertEqual(result["native_equal_task_mean"], "1/2")
        self.assertEqual(result["pooled_minus_equal_task"], "0")
        self.assertEqual(result["interpretation"], "structural_equality_and_implementation_check")

    def test_nonuniform_repetitions_have_different_estimands(self) -> None:
        equal = _policy("A", "equal_task", "1/2", "1/2", {"t1": 1, "t2": 2})
        pooled = _policy("A", "pooled", "2/3", "2/3", {"t1": 1, "t2": 2})
        result = report.explain_weighting([equal, pooled])[0]
        self.assertFalse(result["record_weights_identical"])
        self.assertEqual(result["equal_task_weights_by_task"], {"t1": "1/2", "t2": "1/4"})
        self.assertEqual(result["pooled_record_weight"], "1/3")
        self.assertEqual(result["pooled_minus_equal_task"], "1/6")

    def test_uniform_mean_disagreement_fails_instead_of_becoming_finding(self) -> None:
        rows = [_policy("A", name, "1/2", "1/2") for name in ("equal_task", "pooled")]
        rows[1]["native_operational_zero_mean"] = "3/4"
        with self.assertRaisesRegex(ValueError, "uniform repetitions contradict"):
            report.explain_weighting(rows)

    def test_changed_task_population_is_not_weighting_sensitivity(self) -> None:
        rows = [_policy("A", name, "1/2", "1/2") for name in ("equal_task", "pooled")]
        rows[1]["task_definition_signature"] = "different"
        with self.assertRaisesRegex(ValueError, "changed their population"):
            report.explain_weighting(rows)

    def test_repetition_counts_must_establish_the_reported_population(self) -> None:
        rows = [_policy("A", name, "1/2", "1/2") for name in ("equal_task", "pooled")]
        rows[0]["record_count"] = "9"
        with self.assertRaisesRegex(ValueError, "reported population"):
            report.explain_weighting(rows)

    def test_equal_decimal_quantities_are_not_binary_float_differences(self) -> None:
        rows = [_policy("A", "equal_task", "0.1", "0.1"), _policy("A", "pooled", "1/10", "1/10")]
        self.assertEqual(report.explain_weighting(rows)[0]["pooled_minus_equal_task"], "0")

    def test_boolean_scientific_number_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            report._exact(True)

    def test_equality_class_separates_strict_to_tie_and_native_tie_break(self) -> None:
        strict = _pair("A", "B", "3/5", "2/5", "0", "1/5", "equality_compatible", "a")
        tied = _pair("C", "D", "1/2", "1/2", "-1/5", "1/10", "equality_compatible", "tie", True)
        results = report.explain_pairs([strict, tied])
        self.assertEqual([row["explanatory_subtype"] for row in results],
                         ["strict_order_can_become_tie", "native_tie_can_break"])
        self.assertTrue(all(row["canonical_classification"] == "equality_compatible" for row in results))

    def test_one_sided_native_tie_can_also_break(self) -> None:
        tied = _pair("A", "B", "1/2", "1/2", "-1/5", "0", "equality_compatible", "tie", True)
        self.assertEqual(report.explain_pairs([tied])[0]["explanatory_subtype"], "native_tie_can_break")

    def test_identified_tie_requires_zero_width(self) -> None:
        tied = _pair("A", "B", "1/2", "1/2", "0", "1/10", "identified_tie", "tie")
        with self.assertRaisesRegex(ValueError, "nonzero completion"):
            report.explain_pairs([tied])

    def test_full_census_is_separate_from_inclusion_condition(self) -> None:
        jobs = [{"submission": "A", "native_status": "match"},
                {"submission": "B", "native_status": "unresolved_mismatch"},
                {"submission": "C", "native_status": "unavailable"}]
        eligibility = [{"submission": name, "eligible_primary": str(name == "A")} for name in "ABC"]
        result = {row["joint_native_status"]: row for row in report.census_accounting(jobs, eligibility)}
        self.assertEqual(result["match"]["primary_selected_jobs"], 1)
        self.assertEqual(result["unresolved_mismatch"]["full_census_jobs"], 1)
        self.assertEqual(result["unavailable"]["outside_primary_jobs"], 1)

    def test_unreconciled_primary_member_fails_instead_of_silently_reclassifying(self) -> None:
        with self.assertRaisesRegex(ValueError, "inclusion condition"):
            report.census_accounting([{"submission": "A", "native_status": "unresolved_mismatch"}],
                                     [{"submission": "A", "eligible_primary": "True"}])


class ReportBuildTests(unittest.TestCase):
    """The end-to-end presentation fixture uses no external study cache."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.inputs = self.root / "numerical"
        self.inputs.mkdir()
        self.data = self._fixture()
        for name, rows in self.data.items():
            if name.endswith(".csv"):
                report._write_csv(self.inputs / name, rows)
            elif name.endswith(".json.gz"):
                with gzip.open(self.inputs / name, "wt", encoding="utf8") as handle:
                    json.dump(rows, handle)
            else:
                (self.inputs / name).write_text(json.dumps(rows), encoding="utf8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _fixture(self) -> dict:
        records = []
        for name, values in (("A", [1, 1, 0, None]), ("B", [1, 1, 1, 1]),
                             ("C", [1, 1, 0, 0]), ("D", [1, 0]), ("E", [None])):
            for index, value in enumerate(values):
                records.append({"source_path": f"submissions/terminal-bench/2.0/{name}/job/trial{index}/result.json",
                                "source_sha256": f"{len(records) + 1:064x}", "job_path": name + "/job",
                                "submission": name, "eval_key": name, "trial_uuid": name + str(index),
                                "reward_status": "null_verifier" if value is None else "scored_positive" if value else "scored_zero",
                                "reward_decimal": None if value is None else str(value),
                                "native_reward_decimal": str(value or 0), "score_present": value is not None,
                                "exception_present": value is None or (name == "A" and index == 0),
                                "exception_class": "Timeout" if value is None or (name == "A" and index == 0) else None})
        policies = []
        for sub, mean, upper in (("A", "1/2", "3/4"), ("B", "1", "1"), ("C", "1/2", "1/2")):
            policies.extend(_policy(sub, name, mean, upper) for name in ("equal_task", "pooled"))
        pairs = [_pair("A", "B", "1/2", "1", "-1/2", "-1/4", "strict_robust", "b"),
                 _pair("A", "C", "1/2", "1/2", "0", "1/4", "equality_compatible", "tie", True),
                 _pair("B", "C", "1", "1/2", "1/2", "1/2", "strict_robust", "a")]
        diagnostics = []
        for name in "ABCDE":
            differing = name == "D"
            diagnostics.append({"job_path": name + "/job", "submission": name,
                                "whole_job_numeric_status": "difference" if differing else "unavailable" if name == "E" else "match",
                                "strict_joint_native_status": "unresolved_mismatch" if differing else "unavailable" if name == "E" else "match",
                                "job_source_path": f"submissions/terminal-bench/2.0/{name}/job/result.json",
                                "job_source_sha256": "a" * 64, "job_source_url": "https://example.invalid/" + name,
                                "published_mean_pointers": json.dumps(["/stats/evals/agent/metrics/0/mean"]),
                                "raw_named_final_record_count": "2" if differing else "4",
                                "raw_native_reward_mass": "1" if differing else "2",
                                "raw_native_zero_mean": "1/2", "summary_denominator": "3" if differing else "4",
                                "summary_reward_mass": "1" if differing else "2", "summary_mean": "1/3" if differing else "1/2",
                                "published_mean": "3333333333333333/10000000000000000" if differing else "1/2",
                                "summary_internal_status": "match", "summary_only_name_count": "1" if differing else "0",
                                "raw_only_name_count": "0", "summary_vs_raw_name_population": "different_named_populations" if differing else "same_named_population"})
        return {
            "summary.json": {"dataset": inventory_dataset(), "revision": "b" * 40,
                             "job_count": 5, "submission_count": 5, "named_final_record_count": len(records),
                             "eligible_primary_submissions": 3, "compatible_unordered_primary_pairs": 3,
                             "job_native_status_counts": {"match": 3, "unresolved_mismatch": 1, "unavailable": 1},
                             "pair_classification_counts_equal_task": {"strict_robust": 2, "equality_compatible": 1}},
            "reconciliation.csv": [{"submission": name, "job_path": name + "/job", "native_status": "match" if name in "ABC" else "unresolved_mismatch" if name == "D" else "unavailable"} for name in "ABCDE"],
            "eligibility.csv": [{"submission": name, "eligible_primary": name in "ABC"} for name in "ABCDE"],
            "policy_comparisons.csv": policies, "pairwise_comparisons.csv": pairs,
            "native_score_reproduction.csv": [{"job_path": name + "/job", "eval_key": name, "native_denominator": "4" if name in "ABC" else "2"} for name in "ABCDE"],
            "whole_job_diagnostics.csv": diagnostics, "executions.json.gz": records,
            "input_manifest.json": {"transform": "synthetic-retained-scalars", "license": "fixture"},
        }

    def _build(self, name: str = "report") -> dict:
        with patch.object(report.inventory, "clean_provenance", return_value={"dirty": False, "git_commit": "fixture"}):
            return report.build_report(self.inputs, self.root / name)

    def test_report_explains_inclusion_condition_without_numeric_error_claim(self) -> None:
        receipt = self._build()
        text = (self.root / "report/technical_report.md").read_text(encoding="utf8")
        self.assertIn("inclusion condition", text)
        self.assertIn("not synonymous with a numerical score error", text)
        self.assertIn("property of this selected cohort and an implementation check", text)
        self.assertIn("OpenAI", text)
        self.assertFalse(receipt["canonical_outputs_modified"])
        self.assertFalse(receipt["empty_cache_reproduction_attested_by_report_generator"])

    def test_six_prioritized_worksheet_cases_leave_every_human_field_pending(self) -> None:
        self._build()
        rows = report._rows(self.root / "report/human_review_worksheet.csv")
        self.assertEqual(len(rows), 6)
        self.assertEqual({int(row["priority"]) for row in rows}, set(range(1, 7)))
        for row in rows:
            for field in report._HUMAN:
                self.assertEqual(row[field], "PENDING")
        scored = next(row for row in rows if row["category"] == "scored_exception")
        self.assertEqual(json.loads(scored["expected_output"])["native_record_value"], "1")
        null = next(row for row in rows if row["category"] == "null_reward")
        self.assertEqual(json.loads(null["json_pointers"])[0], "/verifier_result")
        self.assertTrue(scored["source_url"].endswith("/A/job/trial0/result.json"))

    def test_equality_explanations_and_exact_case_arithmetic_are_generated(self) -> None:
        receipt = self._build()
        self.assertEqual(receipt["equality_subtype_counts"], {"native_tie_can_break": 1})
        cases = report._rows(self.root / "report/human_review_worksheet.csv")
        robust = next(row for row in cases if row["category"] == "robust_comparison")
        tied = next(row for row in cases if row["category"] == "native_tie_can_break")
        self.assertIn("[-1/2,-1/4]", robust["arithmetic_or_reasoning"])
        self.assertIn("[0,1/4]", tied["arithmetic_or_reasoning"])

    def test_report_never_claims_omitted_raw_content_was_verified(self) -> None:
        receipt = self._build()
        text = (self.root / "report/technical_report.md").read_text(encoding="utf8")
        self.assertIn("Opaque configuration/semantic hashes are attestations", text)
        self.assertIn("Report generation itself does not prove", text)
        self.assertIn("attest omitted bytes", receipt["representation_limit"])
        self.assertEqual(set(receipt["input_sha256"]), set(report._INPUTS))

    def test_sibling_numerical_links_resolve_from_report_directory(self) -> None:
        receipt = self._build()
        self.assertEqual(receipt["scientific_input_link_prefix"], "../numerical")
        output = self.root / "report"
        text = (output / "technical_report.md").read_text(encoding="utf8")
        self.assertIn("](../numerical/reconciliation.csv)", text)
        self.assertIn("](../../../../docs/research/unscored_trials/REPRODUCING.md)", text)
        for row in report._rows(output / "census_accounting.csv"):
            self.assertTrue((output / row["source_file"]).is_file())
        cases = report._rows(output / "human_review_worksheet.csv")
        for row in cases:
            for item in json.loads(row["supporting_inputs"]):
                self.assertTrue((output / item["file"]).is_file())

    def test_summary_mismatch_fails_before_writing_presentation(self) -> None:
        summary = deepcopy(self.data["summary.json"])
        summary["job_count"] = 99
        (self.inputs / "summary.json").write_text(json.dumps(summary), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "job_count"):
            self._build()
        self.assertFalse((self.root / "report").exists())

    def test_existing_output_is_preserved(self) -> None:
        self._build()
        with self.assertRaises(FileExistsError):
            self._build()

    def test_dirty_source_rejection_precedes_output_creation(self) -> None:
        with patch.object(report.inventory, "clean_provenance", side_effect=RuntimeError("dirty source")):
            with self.assertRaisesRegex(RuntimeError, "dirty source"):
                report.build_report(self.inputs, self.root / "report")
        self.assertFalse((self.root / "report").exists())


def inventory_dataset() -> str:
    """Use a frozen public source label without downloading anything."""
    return "harborframework/terminal-bench-2-leaderboard"


if __name__ == "__main__":
    unittest.main()
