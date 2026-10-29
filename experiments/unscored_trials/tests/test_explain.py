"""Synthetic counterexamples for post hoc whole-job scalar diagnostics."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from experiments.unscored_trials import explain, inventory
from experiments.unscored_trials.explain import diagnose_job


class WholeJobDiagnosticTests(unittest.TestCase):
    """Numerical agreement must not erase source or population disagreements."""

    def _record(self, name: str, reward: object, *, exception: bool = False) -> dict:
        return {"trial_name": name, "trial_uuid": name, "semantic_hash": name,
                "native_supported": True, "native_reward_decimal": str(0 if reward is None else reward),
                "score_present": reward is not None, "reward_decimal": None if reward is None else str(reward),
                "exception_present": exception, "record_kind": "named_final_record"}

    def _job(self, *, mean: object = 0.5, rewards: dict | None = None,
             errors: dict | None = None, completed: int | None = 2) -> dict:
        stats = {"evals": {"agent/model~key": {"metrics": [{"mean": mean}],
                 "reward_stats": {"reward": {"1": ["one"], "0": ["two"]} if rewards is None else rewards},
                 "exception_stats": {} if errors is None else errors}}}
        if completed is not None:
            stats["n_completed_trials"] = completed
        return {"stats": stats}

    def _check(self, status: str = "unresolved_mismatch") -> dict:
        return {"job_path": "submission/job", "submission": "submission", "native_status": status}

    def test_whole_job_match_does_not_promote_strict_joint_nonmatch(self) -> None:
        records = [self._record("one", 1), self._record("two", 0)]
        result = diagnose_job(self._job(), records, self._check())
        self.assertEqual(result["whole_job_numeric_status"], "match")
        self.assertEqual(result["strict_joint_native_status"], "unresolved_mismatch")
        self.assertEqual(result["diagnostic_classification"], "whole_job_mean_matches_despite_joint_accounting_nonmatch")
        self.assertEqual(result["raw_native_zero_mean"], Fraction(1, 2))
        self.assertEqual(result["published_mean_pointers"], ["/stats/evals/agent~1model~0key/metrics/0/mean"])

    def test_strict_match_and_numeric_match_remain_distinct_fields(self) -> None:
        result = diagnose_job(self._job(), [self._record("one", 1), self._record("two", 0)], self._check("match"))
        self.assertEqual(result["diagnostic_classification"], "strict_and_whole_job_match")
        self.assertEqual(result["summary_internal_status"], "match")

    def test_renamed_global_counters_are_visible_without_reclassifying_primary(self) -> None:
        job = self._job()
        job["stats"].update(n_trials=1, n_errored_trials=1, n_errors=0)
        records = [self._record("one", 1, exception=True), self._record("two", 0)]
        result = diagnose_job(job, records, self._check("match"))
        self.assertEqual(result["strict_joint_native_status"], "match")
        self.assertEqual(result["summary_global_counter_matches_raw"], {
            "n_trials": False, "n_completed_trials": True,
            "n_errors": False, "n_errored_trials": True})
        self.assertEqual(result["raw_exception_count"], 1)

    def test_different_named_population_can_explain_scalar_difference(self) -> None:
        job = self._job(mean=1 / 3, rewards={"1": ["one"], "0": ["two", "summary-only"]}, completed=3)
        result = diagnose_job(job, [self._record("one", 1), self._record("two", 0)], self._check())
        self.assertEqual(result["whole_job_numeric_status"], "difference")
        self.assertEqual(result["summary_internal_status"], "match")
        self.assertEqual(result["summary_mean"], Fraction(1, 3))
        self.assertEqual(result["raw_native_zero_mean"], Fraction(1, 2))
        self.assertEqual(result["summary_vs_raw_name_population"], "different_named_populations")
        self.assertEqual(result["summary_only_name_count"], 1)
        self.assertEqual(result["diagnostic_classification"], "whole_job_differs_but_published_mean_matches_own_summary_population")

    def test_numeric_match_does_not_prove_population_equality(self) -> None:
        job = self._job(rewards={"1": ["other-one"], "0": ["other-two"]})
        result = diagnose_job(job, [self._record("one", 1), self._record("two", 0)], self._check())
        self.assertEqual(result["whole_job_numeric_status"], "match")
        self.assertEqual(result["summary_vs_raw_name_population"], "different_named_populations")
        self.assertEqual(result["raw_only_name_count"], 2)
        self.assertEqual(result["summary_only_name_count"], 2)

    def test_scored_exception_reward_and_union_denominator_are_preserved(self) -> None:
        job = self._job(errors={"Timeout": ["one", "two"]})
        records = [self._record("one", 1, exception=True), self._record("two", None, exception=True)]
        result = diagnose_job(job, records, self._check())
        self.assertEqual(result["raw_native_reward_mass"], 1)
        self.assertEqual(result["raw_scored_exception_reward_mass"], 1)
        self.assertEqual(result["raw_scored_exception_count"], 1)
        self.assertEqual(result["summary_union_name_count"], 2)
        self.assertEqual(result["summary_scored_exception_overlap_count"], 2)
        self.assertEqual(result["summary_internal_status"], "match")

    def test_exception_only_name_adds_denominator_but_not_reward_mass(self) -> None:
        job = self._job(mean=0.5, rewards={"1": ["one"]}, errors={"Timeout": ["two"]})
        records = [self._record("one", 1), self._record("two", None, exception=True)]
        result = diagnose_job(job, records, self._check())
        self.assertEqual(result["summary_reward_mass"], 1)
        self.assertEqual(result["summary_union_name_count"], 2)
        self.assertEqual(result["summary_scored_exception_overlap_count"], 0)
        self.assertEqual(result["whole_job_numeric_status"], "match")

    def test_summary_mean_requires_global_counter_aligned_to_full_union(self) -> None:
        job = self._job(completed=1)
        records = [self._record("one", 1), self._record("two", 0)]
        result = diagnose_job(job, records, self._check())
        self.assertEqual(result["whole_job_numeric_status"], "match")
        self.assertEqual(result["summary_internal_status"], "unavailable")
        self.assertIsNone(result["summary_denominator"])
        job["stats"]["n_trials"] = 2
        result = diagnose_job(job, records, self._check())
        self.assertEqual(result["summary_internal_status"], "match")
        self.assertEqual(result["summary_denominator_counter_fields"], ["n_trials"])

    def test_multiple_or_absent_published_means_do_not_get_pooled(self) -> None:
        job = self._job()
        job["stats"]["evals"]["another"] = deepcopy(next(iter(job["stats"]["evals"].values())))
        result = diagnose_job(job, [self._record("one", 1)], self._check())
        self.assertEqual(result["published_mean_count"], 2)
        self.assertEqual(result["whole_job_numeric_status"], "unavailable")
        job["stats"]["evals"] = {}
        result = diagnose_job(job, [self._record("one", 1)], self._check())
        self.assertEqual(result["published_mean_count"], 0)
        self.assertEqual(result["whole_job_numeric_status"], "unavailable")

    def test_unsupported_raw_schema_and_conflicting_uuid_are_unavailable(self) -> None:
        records = [self._record("one", 1), self._record("two", 0)]
        records[1]["native_supported"] = False
        result = diagnose_job(self._job(), records, self._check())
        self.assertEqual(result["whole_job_numeric_status"], "unavailable")
        records[1]["native_supported"] = True
        records[1]["trial_uuid"] = records[0]["trial_uuid"]
        result = diagnose_job(self._job(), records, self._check())
        self.assertIn("conflicting_uuid_semantics", result["whole_job_unavailable_reasons"])

    def test_multichannel_summary_and_malformed_mean_are_unavailable(self) -> None:
        records = [self._record("one", 1), self._record("two", 0)]
        for alteration in ("multichannel", "string", "bool", "nan"):
            with self.subTest(alteration=alteration):
                job = self._job()
                evaluation = next(iter(job["stats"]["evals"].values()))
                if alteration == "multichannel":
                    evaluation["reward_stats"]["other"] = {"1": ["one"]}
                else:
                    evaluation["metrics"][0]["mean"] = {"string": "0.5", "bool": True, "nan": float("nan")}[alteration]
                result = diagnose_job(job, records, self._check())
                self.assertEqual(result["whole_job_numeric_status"], "unavailable")
                self.assertEqual(result["summary_internal_status"], "unavailable")

    def test_exact_tolerance_boundary_is_numeric_only(self) -> None:
        records = [self._record("one", 1), self._record("two", 0)]
        job = self._job(mean=0.6)
        result = diagnose_job(job, records, self._check(), Fraction(1, 10))
        self.assertEqual(result["whole_job_numeric_status"], "match")
        result = diagnose_job(job, records, self._check(), Fraction(1, 10) - Fraction(1, 10**20))
        self.assertEqual(result["whole_job_numeric_status"], "difference")
        self.assertEqual(result["strict_joint_native_status"], "unresolved_mismatch")

    def test_missing_raw_file_and_reward_discard_are_not_zero_imputed(self) -> None:
        records = [self._record("one", 1), self._record("two", 0)]
        check = self._check()
        check["failed_or_malformed_requested_files"] = [{"source_path": "missing/result.json"}]
        result = diagnose_job(self._job(), records, check)
        self.assertEqual(result["whole_job_numeric_status"], "unavailable")
        check.pop("failed_or_malformed_requested_files")
        records[0]["native_reward_decimal"] = "0"
        result = diagnose_job(self._job(), records, check)
        self.assertEqual(result["whole_job_numeric_status"], "unavailable")

    def test_duplicate_summary_reward_name_is_not_silently_repaired(self) -> None:
        job = self._job(rewards={"1": ["one"], "0": ["one"]}, completed=1)
        result = diagnose_job(job, [self._record("one", 1)], self._check())
        self.assertEqual(result["whole_job_numeric_status"], "unavailable")
        self.assertIn("duplicate_summary_reward_name", result["summary_internal_unavailable_reasons"])

    def test_input_artifacts_are_not_mutated(self) -> None:
        job = self._job()
        records = [self._record("one", 1), self._record("two", 0)]
        check = self._check()
        before = deepcopy((job, records, check))
        diagnose_job(job, records, check)
        self.assertEqual((job, records, check), before)


class DiagnosticEvidenceTests(unittest.TestCase):
    """Output wiring must bind canonical shards and raw summaries by byte hash."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data, self.analysis = self.root / "data", self.root / "canonical"
        self.data.mkdir()
        self.analysis.mkdir()
        self.job = "submissions/terminal-bench/2.0/system/job"
        self.raw_path = self.data / "job.json"
        raw = {"stats": {"n_completed_trials": 2, "evals": {"e": {
            "metrics": [{"mean": 0.5}], "reward_stats": {"reward": {"1": ["one"], "0": ["two"]}},
            "exception_stats": {}}}}}
        self.raw_path.write_bytes(json.dumps(raw).encode())
        digest = hashlib.sha256(self.raw_path.read_bytes()).hexdigest()
        url = f"https://huggingface.co/datasets/{inventory.DATASET}/raw/{inventory.REVISION}/{self.job}/result.json"
        source = {"local_path": "job.json", "url": url, "status": "success", "sha256": digest,
                  "size_bytes": self.raw_path.stat().st_size}
        request = {"path": "job.json", "url": url, "job": self.job, "submission": "system",
                   "source_path": self.job + "/result.json", "kind": "job", "source_sha256": digest}
        sources = self._shard("source_manifest/0000.json", [source])
        requests = self._shard("source_requests/0000.json", [request])
        check = {"job_path": self.job, "submission": "system", "native_status": "unresolved_mismatch"}
        checks = self._shard("jobchecks/0000.json", [check])
        (self.analysis / "source_manifest.json").write_bytes(json.dumps({"sources": [sources], "result_requests": [requests]}).encode())
        (self.analysis / "jobchecks.json").write_bytes(json.dumps({"shards": [checks]}).encode())
        (self.analysis / "provenance.json").write_bytes(json.dumps({"analysis_config": {"native_absolute_tolerance": "0.000000000001"}}).encode())
        (self.analysis / "cross_submission_uuid_reconciliation.csv").write_bytes(b"status,trial_uuid\n")
        self.execution_path = self.analysis / "executions/example.csv"
        self.execution_path.parent.mkdir()
        record = {"job_path": self.job, "trial_name": "one", "trial_uuid": "one", "semantic_hash": "one",
                  "native_supported": "True", "native_reward_decimal": "1", "score_present": "True",
                  "reward_decimal": "1", "exception_present": "False", "record_kind": "named_final_record"}
        with self.execution_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(record))
            writer.writeheader()
            writer.writerow(record)
            writer.writerow({**record, "trial_name": "two", "trial_uuid": "two", "semantic_hash": "two",
                             "native_reward_decimal": "0", "reward_decimal": "0"})
        payload = self.execution_path.read_bytes()
        with (self.analysis / "executions.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["path", "sha256", "bytes", "rows"])
            writer.writeheader()
            writer.writerow({"path": "executions/example.csv", "sha256": hashlib.sha256(payload).hexdigest(),
                             "bytes": len(payload), "rows": 2})
        patcher = patch.object(inventory, "clean_provenance", return_value={"dirty": False, "git_commit": "fixture"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _shard(self, name: str, rows: list[dict]) -> dict:
        path = self.analysis / name
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(rows).encode()
        path.write_bytes(payload)
        return {"path": name, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "entries": len(rows)}

    def test_separate_outputs_record_exact_tolerance_and_preserve_canonical_inputs(self) -> None:
        before = {path.relative_to(self.analysis).as_posix(): path.read_bytes()
                  for path in self.analysis.rglob("*") if path.is_file()}
        output = self.root / "diagnostic"
        summary = explain.build(self.data, self.analysis, output)
        self.assertEqual(summary["job_count"], 1)
        self.assertEqual(summary["whole_job_numeric_status_counts"], {"match": 1})
        self.assertFalse(summary["primary_outputs_changed"])
        receipt = json.loads((output / "provenance.json").read_bytes())
        self.assertEqual(receipt["tolerance"], "1/1000000000000")
        self.assertTrue(receipt["post_hoc"])
        self.assertEqual(receipt["raw_job_sources"][0]["sha256"], hashlib.sha256(self.raw_path.read_bytes()).hexdigest())
        with (output / "whole_job_diagnostics.csv").open(newline="", encoding="utf-8") as handle:
            row = next(csv.DictReader(handle))
        self.assertEqual(row["raw_native_zero_mean"], "1/2")
        self.assertEqual(before, {path.relative_to(self.analysis).as_posix(): path.read_bytes()
                                  for path in self.analysis.rglob("*") if path.is_file()})
        with self.assertRaises(FileExistsError):
            explain.build(self.data, self.analysis, output)

    def test_corrupt_raw_job_source_is_rejected_before_outputs(self) -> None:
        self.raw_path.write_bytes(b"{}")
        output = self.root / "diagnostic"
        with self.assertRaisesRegex(ValueError, "raw job cache"):
            explain.build(self.data, self.analysis, output)
        self.assertFalse(output.exists())

    def test_corrupt_execution_shard_is_rejected_before_outputs(self) -> None:
        self.execution_path.write_bytes(self.execution_path.read_bytes() + b"corruption")
        output = self.root / "diagnostic"
        with self.assertRaisesRegex(ValueError, "execution shard"):
            explain.build(self.data, self.analysis, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
