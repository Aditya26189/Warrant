"""Package the fixed payments regression matrix, retaining failures and limits."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from experiments.grader_poc.run_trial import file_hashes, git_output, write_receipt


def read(path: Path) -> dict:
    return json.loads(path.read_bytes())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(work: Path, root: Path) -> dict:
    """Bind collected candidates to prepared bytes and recompute boundary evidence."""
    prepared = read(work / "grader-payments-e2e-cases-002/manifest.json")
    previous = read(root / "experiments/grader_poc/p2/evidence/summary.json")
    prior_workers = {row["sha256"] for row in previous["payment_workers"]}
    rows = []
    for path in sorted((work / "grader-payments-e2e-full").glob("*/outcome.json")):
        result = read(path)
        case = path.parent.name.rsplit("-", 1)[0]
        raw_task = result["command"][result["command"].index("-p") + 1]
        task = Path("C:/" + raw_task[len("/mnt/c/"):]) if raw_task.startswith("/mnt/c/") else Path(raw_task)
        declaration = read(task.parent / "manifest.json")["cases"][case]
        assert file_hashes(task) == declaration["hashes"] == result["task_hashes"]
        assert not result["source_dirty"]
        row = {key: result.get(key) for key in ("status", "reward", "elapsed_seconds", "source_commit", "matches_expected", "task_unchanged")}
        row.update(run=path.parent.name, case=case, expected_reward=declaration["expected_reward"],
                   cleanup_verified=result.get("resource_cleanup", {}).get("verified_absent"), boundaries=[])
        row["semantic_interpretation"] = "INVALID_HARNESS" if path.parent.name == "reference-repaired-001" else "COMPARABLE" if result["status"] == "COMPLETED" else "INCONCLUSIVE"
        if result["trials"]:
            trial = (path.parent / result["trials"][0]["path"]).parent
            ctrf = trial / "verifier/ctrf.json"
            if ctrf.exists():
                tests = read(ctrf)["results"]
                row["tests"] = tests["summary"]
                row["test_statuses"] = [{"name": item["name"], "status": item["status"]} for item in tests["tests"]]
            if result["status"] == "COMPLETED":
                expected = file_hashes(task / "environment/src")
                expected["worker/worker.py"] = digest(task / "solution/worker.py")
                expected["worker/requirements.txt"] = digest(task / "solution/requirements.txt")
                actual = file_hashes(trial / "artifacts/app/src")
                assert actual == expected, "Collected candidate mismatch"
                assert actual["worker/worker.py"] in prior_workers, "Candidate changed since P2"
                row.update(candidate_hashes=actual, candidate_matches_declared=True, candidate_matches_p2=True)
            for receipt in sorted((trial / "verifier").glob("boundary-*.json")):
                boundary = read(receipt)
                details = []
                for item in boundary["plan"]:
                    balance = item["initial_balance"]
                    for index, transaction in enumerate(item["transactions"]):
                        balance += transaction["amount"] if transaction["type"] == "credit" else -transaction["amount"]
                        assert balance == (item["target_balance"] if index == 0 else -1)
                    callbacks = [cb for cb in boundary["callbacks"] if cb["transaction_id"] == item["transactions"][0]["transaction_id"]]
                    progress = [cb for cb in boundary["callbacks"] if cb["transaction_id"] == item["required_callback"]
                                and cb["user_id"] == item["user_id"] and cb["balance_after"] == -1]
                    deliveries = {d["transaction_id"]: d for d in boundary["delivery_reports"]}
                    ordered = False
                    if all(t["transaction_id"] in deliveries for t in item["transactions"]):
                        first, last = (deliveries[item["transactions"][i]["transaction_id"]] for i in (0, -1))
                        ordered = first["error"] is None and last["error"] is None and first["partition"] == last["partition"]
                        if len(item["transactions"]) > 1:
                            ordered = ordered and first["offset"] < last["offset"]
                    details.append({"case": item["case"], "initial_balance": item["initial_balance"],
                                    "target_debit": item["transactions"][0]["amount"], "expected_balance": item["target_balance"],
                                    "target_callbacks": callbacks, "progress_confirmed": bool(progress), "delivery_order_confirmed": ordered})
                row["boundaries"].append({"phase": boundary["phase"], "status": boundary["status"],
                                          "worker_status": boundary.get("worker_status"), "cases": details,
                                          "receipt": receipt.relative_to(work).as_posix()})
        if case == "mutant-original":
            row["boundary_evidence_valid"] = not row["boundaries"]
        else:
            expected_status = "COUNTEREXAMPLE" if case == "mutant-repaired" else "NO_FALSE_POSITIVE_IN_OBSERVATION_WINDOW"
            row["boundary_evidence_valid"] = {b["phase"] for b in row["boundaries"]} == {"single", "overlap"} and all(
                b["status"] == expected_status and all(c["progress_confirmed"] and c["delivery_order_confirmed"] for c in b["cases"])
                and all(bool(c["target_callbacks"]) == (c["case"] == "negative" or (case == "mutant-repaired" and c["case"] == "zero"))
                        for c in b["cases"]) for b in row["boundaries"])
        rows.append(row)
    invocations = list((work / "grader-payments-e2e-full").glob("*/invocation.json"))
    assert len(invocations) == len(rows), "An attempted trial lacks its final receipt"
    valid_rows = [row for row in rows if row["semantic_interpretation"] != "INVALID_HARNESS"]
    completed = {row["case"]: row for row in valid_rows if row["status"] == "COMPLETED"}
    matrix_matches = set(completed) == set(prepared["cases"]) and all(
        r["matches_expected"] and r["cleanup_verified"] and r["boundary_evidence_valid"] for r in valid_rows)
    validation = read(work / "grader-payments-e2e-validation-002/validation.json")
    assert validation["source_commit"] == prepared["source_commit"] and not validation["source_dirty"]
    assert all(check["returncode"] == 0 for check in validation["checks"])
    return {"trials": rows, "matrix_matches_expected": matrix_matches, "prepared_source_commit": prepared["source_commit"],
            "total_trial_seconds": sum(r["elapsed_seconds"] for r in rows), "independent_human_replication": False,
            "population_rate_claim": False, "discovery_advantage_established": False,
            "validation": validation}


def render(summary: dict, destination: Path) -> None:
    """Write the phase report from bound receipts; no handwritten measured totals."""
    trials = summary["trials"]
    rows = []
    boundaries = []
    for row in trials:
        tests = row.get("tests", {})
        rows.append(f"| {row['run']} | {row['status']} / {row['semantic_interpretation']} | {row['reward']} | {tests.get('passed', '?')}/{tests.get('tests', '?')} | {row['cleanup_verified']} | {row['elapsed_seconds']:.3f} |")
        if row["semantic_interpretation"] == "INVALID_HARNESS":
            continue
        for boundary in row["boundaries"]:
            for case in boundary["cases"]:
                boundaries.append(f"| {row['run']} / {boundary['phase']} | {case['case']} | {case['initial_balance']} - {case['target_debit']} = {case['expected_balance']} | {len(case['target_callbacks'])} | {case['progress_confirmed']} | {case['delivery_order_confirmed']} |")
    verdict = "The fixed full-trial matrix matches its declared outcomes." if summary["matrix_matches_expected"] else "The fixed full-trial matrix did not establish every declared outcome; inspect failures before interpreting the repair."
    prefix = "../experiments/grader_poc/payments_e2e/evidence"
    body = f'''# Payments grader end-to-end validation — 24 October 2026

**[Evidence] {verdict}**

The question is narrow: can the existing zero-balance counterexample be observed through real Kafka and HTTP, and can an appended grader regression reject the same worker while accepting the supplied reference and an equivalent predicate? This phase implements decision G014. All earlier evidence and reports remain historical and unchanged.

## Work and observations

The four cases were fixed before execution. The mutant changes only `balance < 0` to `balance <= 0`; the equivalent changes it to `0 > balance`. Prepared candidate hashes match the P2 candidates. Completed full trials additionally bind the collected application files to those prepared bytes. The original verifier is retained byte-for-byte as the prefix of the repaired file. Its three original tests still run; two parameterized cases are appended.

| Full trial | Status | Reward | Tests passed | Owned resources absent | Outer seconds |
|---|---|---:|---:|---|---:|
{chr(10).join(rows)}

Total outer runtime: **{summary['total_trial_seconds']:.3f} seconds**, including setup and cleanup. These durations are not active engineering effort or a method-speed comparison. The `oracle` agent installs supplied solution bytes; it does not run an LLM. No model API or paid compute was used.

The first reference attempt is retained as **INVALID_HARNESS**. Its single-worker check queried all supervisor processes, which returns exit status 3 for the intentionally stopped extra worker. It failed before transmitting the boundary transactions; this is an apparatus false rejection, not a candidate defect. G015 records the correction before implementation: query only the required worker names, preserve the RUNNING assertion and all candidates/properties, add focused regression coverage, then retry once from fresh cases. Both the original and corrected fixtures are archived. This failed attempt is excluded from semantic interpretation and retained in the runtime total.

## The boundary witness

The stack processes synthetic transactions in local containers. Expected balances come from the upstream verifier's independent scan of authenticated seeded transaction history, not the candidate's state topic. New accounts exclude all original test sample accounts and are disjoint between phases. Each phase sends a debit ending at zero, a debit ending at one, and a debit ending at minus one. The nonnegative cases then receive a same-key debit ending at minus one. Broker acknowledgments establish delivery and partition order; correctly valued negative HTTP callbacks establish processing progress before the negative assertion is evaluated.

The HTTP bodies, transaction IDs, worker status, broker offsets and timestamps are retained in the linked [summary]({prefix}/summary.json) and full raw-copy receipts. The table's arithmetic and callback counts are recomputed by the packaging script. This boundary table covers the corrected apparatus; the invalid attempt remains in the full-trial table, summary and raw-copy receipts.

| Candidate / condition | Case | Independently recomputed balance | Target HTTP callbacks | Negative progress confirmed | Broker order confirmed |
|---|---|---|---:|---|---|
{chr(10).join(boundaries)}

An observed callback at zero is the defect. Absence of zero/positive callbacks is asserted only after progress and the upstream duplicate-drain interval. A process that never consumes the transactions cannot pass merely by staying silent. The overlap condition records both supervisor processes as RUNNING; it does not establish that both own partitions or explore arbitrary handoff schedules.

## What this does not establish

- [Inference] This is a validated local regression for a known coverage gap. The omission was already identified by direct assertion review, and the mutant is ordinary boundary mutation. There is no demonstrated discovery, time or cost advantage for Warrant.
- [Evidence] The same assistant constructed, ran and checked the experiment. There is no independent human replication, blind task selection, held-out property result or population error estimate.
- [Inference] A finite observation window cannot prove forever-absence of delayed notifications. The synchronous HTTP-before-state path makes the later same-key callback a useful progress control for these candidates; it does not certify all asynchronous designs.
- [Evidence] The correct controls share most source code. Passing them is narrower than validation across diverse correct implementations. Positive-balance behavior is checked, but no positive-only faulty candidate is part of this frozen matrix.
- [Opinion] This supports retaining an optional grader-audit research artifact. It is not publication-level methodological novelty, a validated startup thesis or production integration approval.

## Remaining gate and local deliverables

The local [grader-only patch]({prefix}/grader-payments-e2e-cases-002/reference-repaired.patch) contains the appended test and its helper, without a worker mutation. It is reviewable against the pinned upstream revision; it has not been submitted upstream. Acceptance by maintainers, broader implementation compatibility and repeated timing stability remain open. The patch's diagnostic JSON is useful audit evidence but is extra instrumentation, not the smallest possible assertion-only patch.

Further claims about auditing unfamiliar graders more reliably or cheaply require independent investigators, matched baselines, frozen tasks/properties and measured investigation effort. More infrastructure alone will not settle that question. Production, B1/A04 and statistical certification are outside this phase.

## Evidence and reproduction ledger

- Trial/fixture source: `{summary['prepared_source_commit']}`. Packaging source: `{summary['archive_source_commit']}`. Every invocation records the pinned Terminal-Bench and Harbor commits and clean source state.
- [Source and protocol](../experiments/grader_poc/DECISIONS.md), [preparer](../experiments/grader_poc/payments_e2e/prepare.py), [boundary check](../experiments/grader_poc/payments_e2e/boundary_check.py), [packager](../experiments/grader_poc/payments_e2e/package.py).
- [Validation receipt]({prefix}/grader-payments-e2e-validation-002/validation.json), [manifest]({prefix}/manifest.json), [summary]({prefix}/summary.json). Prior packet payloads rehashed: `{summary['preserved_payloads']}`.
- Large or binary runtime snapshots stay in the local raw directories. Their sizes and raw SHA-256 values are listed under `omitted` in the manifest; the Git packet is not a byte-complete copy of those snapshots. Host-home and temporary-venv paths are redacted in text copies, with both raw and packaged hashes retained. Regeneration requires Docker, WSL/Linux and the pinned upstream dependencies.
- The shared runner config retains legacy session-window task/oracle descriptors. For these payments runs the runner uses that config only for upstream pins and cancellation grace; the invocation's explicit task path, full task hashes and candidate binding identify the actual experiment. The legacy descriptors are not payments property evidence.

From clean committed source, prepare fresh cases:

```text
python -m experiments.grader_poc.payments_e2e.prepare --tb TB_REPO --out FRESH_CASES
```

Run `experiments.grader_poc.run_trial` once per case in G014 order, passing absolute task/output/upstream/Harbor-binary paths, `--agent oracle`, `--timeout 900`, and expected rewards `1, 1, 0, 1`. Use Linux/WSL, a stable working directory such as `/tmp`, and the experiment checkout on `PYTHONPATH`. Use a fresh output directory per attempt. Each archived invocation contains the exact command and automatic ownership adapter. Do not reinterpret incomplete attempts as semantic failures. Validate and archive using `python -m experiments.grader_poc.payments_e2e.package --work WORK_DIRECTORY` with the recorded directory layout.
'''
    if destination.exists():
        raise FileExistsError(destination)
    destination.write_bytes(body.encode())


def package(work: Path) -> dict:
    root = Path(__file__).resolve().parents[3]
    here = root / "experiments/grader_poc"
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit archive source before generation")
    preserved = {}
    for folder, manifest in (("results", "evidence-manifest.json"), ("hardening", "manifest.json"),
                             ("p2/evidence", "manifest.json"), ("cancellation", "manifest.json")):
        hashes = read(here / folder / manifest)["packaged_files"]
        for name, expected in hashes.items():
            assert digest(here / folder / name) == expected, "Prior evidence drift"
        preserved[folder] = len(hashes)
    summary = summarize(work, root)
    summary.update(archive_source_commit=git_output(root, "rev-parse", "HEAD"), preserved_payloads=preserved)
    out = here / "payments_e2e/evidence"
    out.mkdir(exist_ok=False)
    home = str(Path.home())
    posix = home.replace("\\", "/")
    wsl = "/mnt/" + posix[0].lower() + posix[2:] if ":" in posix else posix
    replacements = sorted({home, home.replace("\\", "\\\\"), posix, wsl}, key=len, reverse=True)
    copies, omitted = [], []

    def redact(body: str) -> str:
        for prefix in replacements:
            body = body.replace(prefix, "${HOST_HOME}")
        return re.sub(r"/tmp/warrant-grader-poc-[0-9]+-venv", "${HARBOR_VENV}", body)

    for folder in ("grader-payments-e2e-full", "grader-payments-e2e-cases", "grader-payments-e2e-cases-002",
                   "grader-payments-e2e-validation", "grader-payments-e2e-validation-002"):
        for source in sorted((work / folder).rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            raw = source.read_bytes()
            relative = source.relative_to(work).as_posix()
            row = {"path": relative, "raw_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            if len(raw) > 10_000_000 or source.suffix in (".gz", ".pyc"):
                omitted.append({**row, "reason": "Large/binary runtime file retained locally"})
                continue
            try:
                body = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                omitted.append({**row, "reason": "Binary runtime file retained locally"})
                continue
            body = redact(body)
            target = out / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body.encode())
            copies.append({**row, "packaged_sha256": digest(target)})
    license_bytes = (here / "results/TERMINAL_BENCH_LICENSE.txt").read_bytes()
    (out / "TERMINAL_BENCH_LICENSE.txt").write_bytes(license_bytes)
    summary["omitted_runtime_artifacts"] = omitted
    summary = json.loads(redact(json.dumps(summary)))
    write_receipt(out / "summary.json", summary)
    write_receipt(out / "manifest.json", {"copies": copies, "omitted": omitted, "packaged_files": file_hashes(out),
                  "redaction": "Host home and temporary venv replaced; UTF8 BOM removed. Raw hashes retained; __pycache__ excluded."})
    render(summary, root / "reports/PHASE-GRADER-PAYMENTS-E2E.md")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    result = package(args.work.resolve())
    print(json.dumps({"trials": len(result["trials"]), "matrix_matches_expected": result["matrix_matches_expected"]}))
