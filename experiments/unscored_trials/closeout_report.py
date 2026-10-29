"""Generate the bounded REPORT closeout without changing frozen science.

This presentation layer keeps full-census reconciliation separate from selected
comparisons. Sanitized inputs support arithmetic on retained fields; their raw
hashes do not independently verify omitted configurations or exception traces.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any
from urllib.parse import quote

from experiments.unscored_trials import inventory


_INPUTS = (
    "summary.json", "reconciliation.csv", "eligibility.csv",
    "policy_comparisons.csv", "pairwise_comparisons.csv",
    "native_score_reproduction.csv", "whole_job_diagnostics.csv",
    "executions.json.gz", "input_manifest.json",
)
_NULL = {"absent_verifier", "null_verifier", "absent_rewards", "null_rewards"}
_HUMAN = {
    "human_review_status": "PENDING", "human_reviewer": "PENDING",
    "human_actual_conclusion": "PENDING", "human_review_date": "PENDING",
    "human_notes": "PENDING",
}
_REPRODUCTION = (
    "python -B -m experiments.unscored_trials.portable reproduce "
    "--study-data-dir C:\\path\\to\\empty-study-data"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _flag(value: object) -> bool:
    if value is True or value == "True":
        return True
    if value is False or value == "False":
        return False
    raise ValueError("ambiguous normalized boolean")


def _object(value: object, expected: type) -> Any:
    result = json.loads(value) if isinstance(value, str) else value
    if not isinstance(result, expected):
        raise ValueError("unexpected structured input field")
    return result


def _exact(value: object) -> Fraction:
    if isinstance(value, bool) or value is None or value == "":
        raise ValueError("missing or boolean scientific number")
    return Fraction(str(value))


def _ratio(value: object) -> str:
    return str(_exact(value))


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |",
             "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(_cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError("a generated explanatory table must not be empty")
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({key: _json(value) if isinstance(value, (dict, list)) else value
                         for key, value in row.items()} for row in rows)


def _relative_sources(value: object, prefix: str) -> Any:
    """Bind generated scientific-file references to the actual report layout."""
    if isinstance(value, dict):
        return {key: _relative_sources(item, prefix) for key, item in value.items()}
    if isinstance(value, list):
        return [_relative_sources(item, prefix) for item in value]
    if isinstance(value, str) and value.startswith("../") and "/" not in value[3:]:
        return prefix + "/" + value[3:]
    return value


def explain_weighting(policies: list[dict]) -> list[dict]:
    """Expose when policy agreement follows algebraically from repetitions."""
    grouped: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in policies:
        policy = row["policy"]
        if policy not in {"equal_task", "pooled"} or policy in grouped[row["submission"]]:
            raise ValueError("unsupported or duplicate submission policy")
        grouped[row["submission"]][policy] = row
    result = []
    for submission, group in sorted(grouped.items()):
        if set(group) != {"equal_task", "pooled"}:
            raise ValueError("both frozen weighting policies are required")
        equal, pooled = group["equal_task"], group["pooled"]
        repetitions = _object(equal["task_repetition_counts"], dict)
        if (not repetitions or any(type(count) is not int or count <= 0 for count in repetitions.values())
                or len(repetitions) != int(equal["task_count"])
                or sum(repetitions.values()) != int(equal["record_count"])):
            raise ValueError("task repetitions do not establish the reported population")
        for field in ("record_count", "task_count", "task_definition_signature"):
            if equal[field] != pooled[field]:
                raise ValueError("weighting policies changed their population")
        if _object(pooled["task_repetition_counts"], dict) != repetitions:
            raise ValueError("weighting policies changed task repetitions")
        counts = sorted(set(repetitions.values()))
        uniform = len(counts) == 1
        pooled_weight = Fraction(1, sum(repetitions.values()))
        equal_weights = {task: str(Fraction(1, len(repetitions) * count))
                         for task, count in sorted(repetitions.items())}
        delta = _exact(pooled["native_operational_zero_mean"]) - _exact(equal["native_operational_zero_mean"])
        if uniform and delta:
            raise ValueError("uniform repetitions contradict equal-policy arithmetic")
        result.append({
            "submission": submission, "task_count": len(repetitions),
            "record_count": sum(repetitions.values()), "minimum_records_per_task": min(counts),
            "maximum_records_per_task": max(counts), "within_submission_uniform": uniform,
            "pooled_record_weight": str(pooled_weight),
            "equal_task_record_weight": str(pooled_weight) if uniform else "varies_by_task",
            "equal_task_weights_by_task": equal_weights, "record_weights_identical": uniform,
            "native_equal_task_mean": _ratio(equal["native_operational_zero_mean"]),
            "native_pooled_mean": _ratio(pooled["native_operational_zero_mean"]),
            "pooled_minus_equal_task": str(delta),
            "interpretation": "structural_equality_and_implementation_check" if uniform else "different_weighting_estimands",
            "source_file": "../policy_comparisons.csv",
            "source_selector": {"submission": submission, "policies": ["equal_task", "pooled"]},
        })
    return result


def explain_pairs(pairs: list[dict]) -> list[dict]:
    """Preserve the canonical class while separating the two equality cases."""
    result, seen = [], set()
    for row in sorted((item for item in pairs if item["policy"] == "equal_task"),
                      key=lambda item: (item["submission_a"], item["submission_b"])):
        identity = (row["submission_a"], row["submission_b"])
        if identity in seen:
            raise ValueError("duplicate equal-task comparison")
        seen.add(identity)
        lower, upper = _exact(row["difference_lower"]), _exact(row["difference_upper"])
        if lower > upper:
            raise ValueError("reversed completion interval")
        classification, order = row["classification"], row["native_order"]
        tie_break = _flag(row["native_tie_can_break"])
        subtype = classification
        if classification == "equality_compatible":
            if order == "tie" and tie_break and lower <= 0 <= upper and lower != upper:
                subtype = "native_tie_can_break"
            elif order in {"a", "b"} and not tie_break and (lower == 0 or upper == 0):
                subtype = "strict_order_can_become_tie"
            else:
                raise ValueError("equality-compatible class has inconsistent native-order evidence")
        elif classification == "identified_tie":
            if order != "tie" or lower != 0 or upper != 0 or tie_break:
                raise ValueError("identified tie has nonzero completion uncertainty")
        elif classification not in {"strict_robust", "reversal_compatible"}:
            raise ValueError("unsupported canonical comparison class")
        result.append({
            "submission_a": identity[0], "submission_b": identity[1],
            "canonical_classification": classification, "explanatory_subtype": subtype,
            "native_order": order, "native_a": _ratio(row["native_a"]),
            "native_b": _ratio(row["native_b"]), "difference_lower": str(lower),
            "difference_upper": str(upper), "native_tie_can_break": tie_break,
            "interpretation": "hypothetical_completion_not_recovered_corrected_ranking",
            "source_file": "../pairwise_comparisons.csv",
            "source_selector": {"submission_a": identity[0], "submission_b": identity[1], "policy": "equal_task"},
        })
    return result


def census_accounting(reconciliation: list[dict], eligibility: list[dict]) -> list[dict]:
    """Keep selection-conditioned agreement out of the full-census claim."""
    eligible = {row["submission"] for row in eligibility if _flag(row["eligible_primary"])}
    selected = [row for row in reconciliation if row["submission"] in eligible]
    if any(row["native_status"] != "match" for row in selected):
        raise ValueError("primary cohort violates its native-reconciliation inclusion condition")
    if eligible - {row["submission"] for row in selected}:
        raise ValueError("eligible submission has no reconciled job population")
    counts = Counter(row["native_status"] for row in reconciliation)
    selected_counts = Counter(row["native_status"] for row in selected)
    return [{"joint_native_status": status, "full_census_jobs": count,
             "full_census_job_denominator": len(reconciliation),
             "primary_selected_jobs": selected_counts[status],
             "outside_primary_jobs": count - selected_counts[status],
             "interpretation": "identity_indexes_counters_and_mean_jointly; not_a_numeric_error_count",
             "source_file": "../reconciliation.csv", "source_selector": {"native_status": status}}
            for status, count in sorted(counts.items())]


def _raw_url(summary: dict, path: str) -> str:
    return (f"https://huggingface.co/datasets/{summary['dataset']}/raw/"
            f"{summary['revision']}/" + quote(path, safe="/"))


def _support(analysis_dir: Path, name: str, selector: dict) -> dict:
    return {"file": "../" + name, "sha256": _sha(analysis_dir / name), "selector": selector}


def _record_case(category: str, record: dict, summary: dict, analysis_dir: Path,
                 native: list[dict]) -> dict:
    status = record["reward_status"]
    pointers = ["/verifier_result/rewards/reward", "/exception_info"]
    if category == "null_reward":
        pointers = ["/verifier_result" if status in {"null_verifier", "absent_verifier"}
                    else "/verifier_result/rewards", "/exception_info/exception_type"]
    elif category == "scored_exception":
        pointers[-1] = "/exception_info/exception_type"
    mean_rows = [row for row in native if row["job_path"] == record["job_path"]
                 and row.get("eval_key") in {record.get("eval_key"), (record.get("eval_key") or "").replace("/", "-")}]
    denominator = int(mean_rows[0]["native_denominator"]) if len(mean_rows) == 1 and mean_rows[0].get("native_denominator") else None
    if denominator is not None and denominator <= 0:
        raise ValueError("human example has a nonpositive native denominator")
    value = _exact(record["native_reward_decimal"])
    contribution = str(value / denominator) if denominator else "per-eval denominator not established"
    expected = {"reward_status": status, "score_present": _flag(record["score_present"]),
                "exception_present": _flag(record["exception_present"]),
                "native_record_value": str(value), "native_weighted_contribution": contribution}
    claims = {
        "ordinary_record": "A recorded zero is an observed score, not an unscored outcome.",
        "scored_exception": "A valid positive score survives the recorded exception.",
        "null_reward": "A null/absent verifier reward is unscored; documented native final-record accounting assigns zero.",
    }
    arithmetic = f"Native record value = {value}; per-eval denominator = {denominator}; contribution = {contribution}."
    if category == "null_reward":
        arithmetic += " Free [0,1] completion is a different, hypothetical target."
    return {
        "category": category, "claim": claims[category],
        "selection_rule": "first(source_sha256,source_path) within requested record category; post_hoc_diagnostic",
        "source_file": record["source_path"], "source_sha256": record["source_sha256"],
        "source_url": _raw_url(summary, record["source_path"]), "json_pointers": pointers,
        "source_selector": {},
        "supporting_inputs": [_support(analysis_dir, "executions.json.gz", {"source_path": record["source_path"]})],
        "input_values": {key: record.get(key) for key in (
            "trial_uuid", "reward_status", "reward_decimal", "native_reward_decimal",
            "score_present", "exception_present", "exception_class")},
        "arithmetic_or_reasoning": arithmetic, "expected_output": expected,
        "limitations": "Check raw URL/hash before source adjudication; this generator reads retained scalar projections, not omitted raw fields.",
    }


def human_cases(analysis_dir: Path, summary: dict, records: list[dict], native: list[dict],
                policies: list[dict], pairs: list[dict], diagnostics: list[dict]) -> list[dict]:
    """Prepare six review opportunities without supplying human conclusions."""
    ordered = sorted(records, key=lambda row: (row["source_sha256"], row["source_path"]))
    predicates = {
        "ordinary_record": lambda row: row["reward_status"] == "scored_zero" and not _flag(row["exception_present"]),
        "scored_exception": lambda row: _flag(row["score_present"]) and _exact(row["reward_decimal"]) > 0 and _flag(row["exception_present"]),
        "null_reward": lambda row: row["reward_status"] in _NULL,
    }
    result = []
    for category, predicate in predicates.items():
        selected = next((row for row in ordered if predicate(row)), None)
        if selected is None:
            raise ValueError(f"requested human review category unavailable: {category}")
        result.append(_record_case(category, selected, summary, analysis_dir, native))
    differences = sorted((row for row in diagnostics if row["whole_job_numeric_status"] == "difference"),
                         key=lambda row: row["job_path"])
    if not differences:
        raise ValueError("requested raw/summary review case unavailable")
    job = differences[0]
    result.append({
        "category": "raw_summary_difference", "claim": "A differing raw/summary mean requires population and index investigation before any score-error claim.",
        "selection_rule": "first(job_path) among all post_hoc whole-job numeric differences",
        "source_file": job["job_source_path"], "source_sha256": job["job_source_sha256"],
        "source_url": job.get("job_source_url") or _raw_url(summary, job["job_source_path"]),
        "json_pointers": _object(job["published_mean_pointers"], list) + ["/stats/evals", "/stats/n_trials", "/stats/n_completed_trials"],
        "source_selector": {},
        "supporting_inputs": [_support(analysis_dir, "whole_job_diagnostics.csv", {"job_path": job["job_path"]}),
                              _support(analysis_dir, "executions.json.gz", {"job_path": job["job_path"]})],
        "input_values": {key: job.get(key) for key in (
            "raw_named_final_record_count", "raw_native_reward_mass", "raw_native_zero_mean",
            "summary_denominator", "summary_reward_mass", "summary_mean", "published_mean",
            "summary_only_name_count", "raw_only_name_count", "summary_vs_raw_name_population")},
        "arithmetic_or_reasoning": f"Raw {job['raw_native_reward_mass']}/{job['raw_named_final_record_count']} = {job['raw_native_zero_mean']}; summary {job['summary_reward_mass']}/{job['summary_denominator']} = {job['summary_mean']}. Compare the published decimal at the frozen tolerance, then inspect named reward/exception indexes.",
        "expected_output": {key: job.get(key) for key in ("whole_job_numeric_status", "summary_internal_status", "strict_joint_native_status")},
        "limitations": "No retry/export cause or intended official population can be established from this arithmetic alone.",
    })
    policy = {(row["submission"], row["policy"]): row for row in policies}
    equal_pairs = sorted((row for row in pairs if row["policy"] == "equal_task"),
                         key=lambda row: (row["submission_a"], row["submission_b"]))
    for category, predicate in (
        ("robust_comparison", lambda row: row["classification"] == "strict_robust"),
        ("native_tie_can_break", lambda row: row["native_order"] == "tie" and _flag(row["native_tie_can_break"])),
    ):
        pair = next((row for row in equal_pairs if predicate(row)), None)
        if pair is None:
            raise ValueError(f"requested human comparison category unavailable: {category}")
        a, b = pair["submission_a"], pair["submission_b"]
        pa, pb = policy[(a, "equal_task")], policy[(b, "equal_task")]
        lower = _exact(pa["score_completion_lower"]) - _exact(pb["score_completion_upper"])
        upper = _exact(pa["score_completion_upper"]) - _exact(pb["score_completion_lower"])
        if lower != _exact(pair["difference_lower"]) or upper != _exact(pair["difference_upper"]):
            raise ValueError("human comparison example contradicts policy intervals")
        selector = {"submission_a": a, "submission_b": b, "policy": "equal_task"}
        result.append({
            "category": category,
            "claim": "A robust strict order survives every allowed independent completion." if category == "robust_comparison" else "A native null-as-zero tie can break under hypothetical completion.",
            "selection_rule": "first(submission_a,submission_b) among requested equal-task comparison category; post_hoc_diagnostic",
            "source_file": "../pairwise_comparisons.csv", "source_sha256": _sha(analysis_dir / "pairwise_comparisons.csv"),
            "source_url": "", "json_pointers": [], "source_selector": selector,
            "supporting_inputs": [_support(analysis_dir, "policy_comparisons.csv", {"submission": sub, "policy": "equal_task"}) for sub in (a, b)] + [_support(analysis_dir, "executions.json.gz", {"submission": sub}) for sub in (a, b)],
            "input_values": {"submission_a": a, "submission_b": b, "a": {key: pa[key] for key in ("record_count", "task_count", "unknown_record_count", "score_completion_lower", "score_completion_upper")}, "b": {key: pb[key] for key in ("record_count", "task_count", "unknown_record_count", "score_completion_lower", "score_completion_upper")}},
            "arithmetic_or_reasoning": f"[L_A-H_B,H_A-L_B] = [{lower},{upper}]. Task pairing alone adds no restriction on independently free unknown rewards.",
            "expected_output": {key: pair[key] for key in ("classification", "native_order", "native_tie_can_break", "difference_lower", "difference_upper")},
            "limitations": "Verify record sums/identity in the supporting scalar ledgers; counterfactual assignments are not recovered corrected outcomes.",
        })
    priorities = {"ordinary_record": 6, "scored_exception": 2, "null_reward": 1,
                  "raw_summary_difference": 3, "robust_comparison": 5, "native_tie_can_break": 4}
    return [{"case_id": f"H{index:02}", "priority": priorities[row["category"]], **row, **_HUMAN}
            for index, row in enumerate(result, 1)]


def _worksheet_markdown(cases: list[dict]) -> str:
    lines = ["# Human source-to-table review worksheet", "",
             "All human conclusions, reviewer identities and dates remain **PENDING**. These are prioritized post hoc examples, not a prevalence sample. AI checks are not independent human adjudication.", "",
             "For raw cases, retrieve the immutable URL and verify its original SHA-256 before inspecting the exact JSON pointers. Supporting sanitized ledgers reproduce retained-field arithmetic; hashes of omitted configurations or traces are attestations, not independent verification of that content.", ""]
    for row in sorted(cases, key=lambda item: item["priority"]):
        source = f"[{row['source_file']}]({row['source_url']})" if row["source_url"] else f"[{row['source_file']}]({row['source_file']})"
        lines.extend([f"## Priority {row['priority']}: {row['case_id']} — {row['category'].replace('_', ' ')}", "",
                      row["claim"], "", f"Source: {source}. SHA-256: `{row['source_sha256']}`.", "",
                      "JSON pointers: " + (", ".join(f"`{item}`" for item in row["json_pointers"]) or "CSV row selector below; no JSON pointer applies."), "",
                      "```json", json.dumps({"selector": row["source_selector"], "inputs": row["input_values"], "supporting_inputs": row["supporting_inputs"]}, indent=2, ensure_ascii=False), "```", "",
                      row["arithmetic_or_reasoning"], "", "Expected computational output: `" + _json(row["expected_output"]) + "`.", "",
                      "Selection: " + row["selection_rule"] + ".", "", row["limitations"], "",
                      _table(["Human field", "Actual entry"], [[key.replace("human_", "").replace("_", " "), value] for key, value in _HUMAN.items()]), ""])
    lines.extend(["## Review boundary", "",
                  "A human can now inspect source fields, transformations, exclusions and arithmetic. Original planned executions, retry/export causes, exact submitted harnesses and official website import/adjudication remain unverified without new external execution or importer evidence. Reviewing this worksheet cannot supply those missing records.", ""])
    return "\n".join(lines)


def _technical_report(summary: dict, census: list[dict], weighting: list[dict], pairs: list[dict],
                      diagnostics: list[dict], eligibility: list[dict], records: list[dict],
                      cases: list[dict]) -> str:
    classes = Counter(row["canonical_classification"] for row in pairs)
    subtypes = Counter(row["explanatory_subtype"] for row in pairs)
    repetition_counts = Counter(row["minimum_records_per_task"] for row in weighting if row["within_submission_uniform"])
    uniform = all(row["within_submission_uniform"] for row in weighting)
    zero = sum(_exact(row["pooled_minus_equal_task"]) == 0 for row in weighting)
    all_jobs = sum(row["full_census_jobs"] for row in census)
    whole = Counter(row["whole_job_numeric_status"] for row in diagnostics)
    differences = sorted((row for row in diagnostics if row["whole_job_numeric_status"] == "difference"), key=lambda row: row["job_path"])
    rewards = Counter(row["reward_status"] for row in records)
    scored_exceptions = sum(_flag(row["score_present"]) and _flag(row["exception_present"]) for row in records)
    positive_exceptions = sum(_flag(row["score_present"]) and _flag(row["exception_present"]) and _exact(row["reward_decimal"]) > 0 for row in records)
    sections = [
        "# Warrant unscored-trial accounting: exploratory technical report", "",
        "**Decision: REPORT.** This is exploratory, AI-assisted work, not peer-reviewed work or a submitted TMLR paper. The bounded decision study is closed; no benchmark correction or corrected official ranking is established.", "",
        "## Question and corpus", "",
        "Can public agent-evaluation exports support a useful, reproducible finding about accounting for unscored outcomes? We test what the released final records identify before changing any scoring target. Recorded zero, absent/null reward, absent raw file and exception are distinct evidence states.", "",
        f"The official [Terminal-Bench release](https://huggingface.co/datasets/{summary['dataset']}/tree/{summary['revision']}) is pinned at `{summary['revision']}`. The retained census contains {len(eligibility):,} submissions, {all_jobs:,} jobs and {len(records):,} named final records. These files describe released final records; configurations and minimum repetition rules do not establish an exact original execution roster or attempt/retry history.", "",
        "The historical Marin/tau baseline is preserved. Its [earlier verification and replay receipts](../../20261029-terminal-bench2/context/baseline_verification.json) remain archival evidence; this closeout does not rerun that baseline or rewrite its canonical outputs. Eight retained Marin cells violate a 5% missingness cap, so that full-panel cap remains hypothetical.", "",
        "## Native-score and population reconciliation", "",
        _table(["Full-census joint status", "Jobs", "Primary-selected jobs"], [[row["joint_native_status"], row["full_census_jobs"], row["primary_selected_jobs"]] for row in census]), "",
        "Source: [generated census accounting](census_accounting.csv), with selectors into [all-job reconciliation](../reconciliation.csv). Joint reconciliation tests identity, name indexes and counters as well as means. An unresolved joint status is not synonymous with a numerical score error.", "",
        f"Primary eligibility retains {len(weighting):,} submissions and excludes unreconciled native job populations. Therefore native agreement on the strict cohort is partly an **inclusion condition**, rather than an independent claim that every released job reconciles. See [eligibility](../eligibility.csv) for every exclusion.", "",
        f"The separately labeled post hoc whole-job diagnostic gives {whole['match']:,} matching means, {whole['difference']:,} differing means and {whole['unavailable']:,} unavailable supported means across the full census. Whole-job pooling does not repair evaluation-group aliases, indexes, task identities or primary eligibility, and does not reconstruct an official leaderboard.", "",
        _table(["Differing exported account", "Raw mass / final records", "Own summary mass / denominator", "Summary-internal status"], [[f"[{row['submission']} / {row['job_path'].rsplit('/', 1)[-1]}]({row['job_source_url']})", f"{row['raw_native_reward_mass']} / {row['raw_named_final_record_count']}", f"{row['summary_reward_mass']} / {row['summary_denominator']}", row["summary_internal_status"]] for row in differences]), "",
        "Source: [whole-job diagnostics](../whole_job_diagnostics.csv), including immutable source hashes and published-mean JSON pointers. Equal record counts do not prove equal outcomes; differing named populations can each have internally coherent means. A summary-recorded zero without a raw file is already observed summary evidence, not an invented unknown reward. Export causes, intended historical populations and website adjudication remain unresolved.", "",
        f"Raw outcomes include {rewards['scored_positive']:,} positive scores, {rewards['scored_zero']:,} recorded zeros and {sum(rewards[status] for status in _NULL):,} genuinely unscored retained records. Scores coexist with exceptions in {scored_exceptions:,} records, including {positive_exceptions:,} positive scores. A valid reward survives its exception label; the label alone establishes no causal diagnosis.", "",
        "[Pinned Harbor source](https://raw.githubusercontent.com/harbor-framework/harbor/1c0f38644b94c2a9a5fa4a8b77667d8175d0869e/src/harbor/metrics/mean.py) documents null-as-zero operational means for the supported single reward channel. Free [0,1] completion changes the target: it assigns hypothetical rewards to present unscored outcomes. It is not a recovery of corrected ranks, missing original executions or capability under repaired infrastructure.", "",
        "## Structural weighting and supported comparisons", "",
        _table(["Uniform records per task", "Retained submissions"], [[count, number] for count, number in sorted(repetition_counts.items())]), "",
    ]
    if uniform:
        sections.extend(["Every retained submission has uniform within-submission repetitions. For T tasks and r records per task,", "", "```text", "equal-task = (1/T) Σ_t [(1/r) Σ_k y_tk] = (1/(Tr)) Σ_tk y_tk = pooled", "```", "",
                         f"Thus policy equality for all {zero:,} retained submissions follows algebraically from their record weights. It is a property of this selected cohort and an implementation check, not strong evidence that weighting is unimportant in general. Nonuniform repetitions or changed conditioning sets can change the estimand.", ""])
    else:
        sections.extend([f"Only {sum(row['within_submission_uniform'] for row in weighting):,} retained submissions have uniform repetitions; {zero:,} have equal policy means. Uniform repetitions imply equal record weights algebraically; equality on nonuniform populations can be coincidental and does not establish weighting irrelevance.", ""])
    sections.extend([
        "Source: [weighting structure](weighting_structure.csv), with exact record weights and policy selectors. The historical policies remain unchanged.", "",
        _table(["Exact completion class", "Compatible equal-task pairs"], [[name.replace("_", " "), classes[name]] for name in ("strict_robust", "reversal_compatible", "equality_compatible", "identified_tie")]), "",
        f"The {classes['equality_compatible']:,} equality-compatible cases comprise {subtypes['strict_order_can_become_tie']:,} existing strict orders that can become ties without reversing and {subtypes['native_tie_can_break']:,} existing native ties that can break. They are not all tie-only losses. [Pairwise explanations](pairwise_explanation.csv) retain the canonical class and identify these subtypes separately.", "",
        "Comparisons use complete matching task-definition/checksum signatures and fixed populations/weights. Unknown rewards remain independently free in [0,1], so the difference interval is exactly [L_A−H_B, H_A−L_B]. Pairing task IDs does not tighten it without additional restrictions. Reversal-compatible means a hypothetical completion can reverse an existing strict order; it does not mean that a corrected reversal was observed.", "",
        "## Concrete source-to-table examples", "",
        _table(["Example", "Computational check", "Review"], [[row["category"].replace("_", " "), row["arithmetic_or_reasoning"], f"[{row['case_id']}](human_review_worksheet.md)"] for row in cases if row["category"] in {"scored_exception", "robust_comparison", "native_tie_can_break"}]), "",
        "These examples are post hoc illustrations, not a random sample or independent adjudication. The worksheet also covers ordinary zero, null reward and a raw/summary discrepancy, with original source hashes, exact pointers, retained values and expected arithmetic.", "",
        "## Closest-work overlap and REPORT decision", "",
        "[Terminal-Bench issue 2246](https://github.com/harbor-framework/terminal-bench/issues/2246) and [honestboard at its pinned revision](https://github.com/jopoku16/honestboard/tree/97bd812d07c9c852d05666128ff3b59cbe461a0c) already examine this release's summary-based denominator and ranking sensitivity. Free-outcome bounds and denominator distinctions are established in [Gao and Zhou](https://arxiv.org/html/2605.10448v1), while [AgentEval](https://arxiv.org/html/2610.21177v1) addresses execution accounting. See the [closest-work comparison](../../../../docs/research/unscored_trials/RELATED_WORK.md).", "",
        "The additional useful result is an auditable separation of scalar agreement from record population, task identity and index agreement. The strongest objection is closest-work overlap plus unresolved export causes: these checks have not yet changed a substantive benchmark conclusion or identified an actionable scoring-policy defect. Structural policy equality and hypothetical completion envelopes do not resolve that objection. Preserve the technical report and stop, rather than manufacture a submission claim.", "",
        "## Limitations, reproducibility and human handoff", "",
        "Original planned slots, durable attempt/retry lineage, exact submitted harnesses and official website importer/adjudication history remain unavailable. Repeated final records are not assumed to be retries. A raw-supported population outside strict native eligibility is descriptive evidence, not a secondary ranking. HAL was not invoked to replace missing execution evidence.", "",
        "The portable inputs are reviewed scalar projections with original source hashes, transformation identity and derived hashes. They support numerical regeneration of retained fields. Opaque configuration/semantic hashes are attestations: omitted raw configurations, transcripts and exception traces are not independently verified by this route. Third-party data retain their source licensing; Warrant's code license does not relicense them.", "",
        "From a clean checkout and a new empty study-data directory:", "", "```powershell", _REPRODUCTION, "```", "",
        "This command uses the committed minimal input bundle and reference to regenerate numerical tables and this report. Consult the [reproduction guide](../../../../docs/research/unscored_trials/REPRODUCING.md) and the invocation's `validation.json` for actual acquisition, integrity, numerical and report outcomes. Report generation itself does not prove that an empty-cache test ran. The earlier exact cached replay remains a separate archival check; historical timestamps, paths and failed-download receipts are not numerical targets.", "",
        "The [human worksheet](human_review_worksheet.md) and [editable CSV](human_review_worksheet.csv) remain entirely **PENDING**. A human can verify source-to-scalar fields, exclusions and arithmetic now. AI and subagent checks are not independent human adjudication; reviewing these files cannot recover missing execution/importer evidence.", "",
        "Reopen only with specific evidence: an original roster/attempt lineage and pinned importer/harness history relevant to an accounting claim, or a demonstrated substantive consequence beyond the closest audit. More benchmark rows alone are insufficient. Human responsibility for source checks and the text is still required before authorship/publication claims.", "",
        "This work was generated and checked with AI assistance, including OpenAI's Codex. OpenAI develops models evaluated in the corpus, creating a relevant maker conflict for this AI-assisted analysis. No human authors, affiliations, funding, endorsement or independent review are invented. No paper submission or outreach is part of this study.", "",
    ])
    return "\n".join(sections)


def build_report(analysis_dir: Path, output_dir: Path) -> dict:
    """Generate versioned explanatory outputs from clean committed source.

    Frozen canonical artifacts are inputs only. No raw cache, network, historical
    download receipt, model execution or human judgment is consulted here.
    """
    provenance = inventory.clean_provenance()
    analysis_dir, output_dir = analysis_dir.resolve(), output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError("preserve prior report generation")
    if analysis_dir == output_dir or analysis_dir.is_relative_to(output_dir):
        raise ValueError("report destination must not contain its input directory")
    hashes = {name: _sha(analysis_dir / name) for name in _INPUTS}
    summary = json.loads((analysis_dir / "summary.json").read_bytes())
    json.loads((analysis_dir / "input_manifest.json").read_bytes())
    with gzip.open(analysis_dir / "executions.json.gz", "rt", encoding="utf-8") as handle:
        execution_payload = json.load(handle)
    records = execution_payload.get("records") if isinstance(execution_payload, dict) else execution_payload
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise ValueError("normalized execution payload must contain a list of records")
    records = [row for row in records if row.get("record_kind", "named_final_record") == "named_final_record"]
    reconciliation = _rows(analysis_dir / "reconciliation.csv")
    eligibility = _rows(analysis_dir / "eligibility.csv")
    policies = _rows(analysis_dir / "policy_comparisons.csv")
    pairs = _rows(analysis_dir / "pairwise_comparisons.csv")
    native = _rows(analysis_dir / "native_score_reproduction.csv")
    diagnostics = _rows(analysis_dir / "whole_job_diagnostics.csv")
    census = census_accounting(reconciliation, eligibility)
    weighting = explain_weighting(policies)
    comparisons = explain_pairs(pairs)
    if {row["submission"] for row in weighting} != {row["submission"] for row in eligibility if _flag(row["eligible_primary"])}:
        raise ValueError("policy and eligibility populations differ")
    expected_counts = {"job_count": len(reconciliation), "submission_count": len(eligibility),
                       "named_final_record_count": len(records), "eligible_primary_submissions": len(weighting),
                       "compatible_unordered_primary_pairs": len(comparisons)}
    for key, value in expected_counts.items():
        if key in summary and summary[key] != value:
            raise ValueError(f"reported summary contradicts generated presentation: {key}")
    joint = dict(Counter(row["native_status"] for row in reconciliation))
    if "job_native_status_counts" in summary and summary["job_native_status_counts"] != joint:
        raise ValueError("summary joint reconciliation counts differ")
    if len(diagnostics) != len(reconciliation) or {row["job_path"] for row in diagnostics} != {row["job_path"] for row in reconciliation}:
        raise ValueError("post hoc diagnostic does not cover the whole job census")
    class_counts = dict(Counter(row["canonical_classification"] for row in comparisons))
    if "pair_classification_counts_equal_task" in summary and summary["pair_classification_counts_equal_task"] != class_counts:
        raise ValueError("summary pair classification counts differ")
    cases = human_cases(analysis_dir, summary, records, native, policies, pairs, diagnostics)
    report = _technical_report(summary, census, weighting, comparisons, diagnostics, eligibility, records, cases)
    scientific_prefix = Path(os.path.relpath(analysis_dir, output_dir)).as_posix()
    for name in _INPUTS:
        report = report.replace(f"](../{name})", f"]({scientific_prefix}/{name})")
    census, weighting, comparisons, cases = (
        _relative_sources(rows, scientific_prefix) for rows in (census, weighting, comparisons, cases))
    output_dir.mkdir(parents=True)
    for name, rows in (("census_accounting.csv", census), ("weighting_structure.csv", weighting),
                       ("pairwise_explanation.csv", comparisons), ("human_review_worksheet.csv", cases)):
        _write_csv(output_dir / name, rows)
    (output_dir / "technical_report.md").write_text(report, encoding="utf-8", newline="\n")
    (output_dir / "human_review_worksheet.md").write_text(_worksheet_markdown(cases), encoding="utf-8", newline="\n")
    receipt = {
        "provenance": provenance, "module_sha256": _sha(Path(__file__)),
        "input_sha256": hashes, "decision": "REPORT", "canonical_outputs_modified": False,
        "scientific_input_link_prefix": scientific_prefix,
        "human_review_completed": False, "empty_cache_reproduction_attested_by_report_generator": False,
        "numerical_counts": expected_counts, "joint_job_counts": joint, "pair_class_counts": class_counts,
        "equality_subtype_counts": dict(Counter(row["explanatory_subtype"] for row in comparisons if row["canonical_classification"] == "equality_compatible")),
        "representation_limit": "retained_scalar_arithmetic; raw hashes and opaque private-field hashes attest omitted bytes rather than independently verify them",
        "generated_files": {path.name: _sha(path) for path in sorted(output_dir.iterdir())},
    }
    (output_dir / "provenance.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return receipt


def main() -> None:
    """Generate only the bounded technical report and pending human handoff."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_report(args.analysis_dir, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
