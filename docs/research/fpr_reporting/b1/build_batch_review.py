"""Project frozen B1 annotations into a domain-only review packet, without sampling."""

from __future__ import annotations

import collections
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
NEEDS = {
    "L": "English-text evaluation: cite dataset/method evidence; note indirect support or mixed-language limitations.",
    "T": "Separate binary injected-instruction input evaluation, rather than harmful-content/jailbreak, end-to-end success, or another security task alone.",
    "P": "Decision before the downstream target LLM answers; distinguish auxiliary detector generation from target-response-dependent evidence.",
    "B": "Qualifying binary prompt/document input decision, rather than only token/step/multiclass labels; identify any separately evaluated binary stratum.",
}


def digest(path: Path) -> str:
    """Bind an artifact's exact bytes without interpreting paper outcomes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    """Write a new stable UTF-8 artifact; preserve earlier frozen files."""
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    """Require clean provenance and project every unresolved record, without a draw."""
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=BASE):
        raise RuntimeError("Scientific packet generation requires a clean worktree")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE, text=True).strip()
    now = datetime.now(timezone.utc).isoformat()
    inputs = [
        "BATCH_REVIEW_WORKFLOW_20261018.md", "BATCH_DOMAIN_DECISIONS.jsonl",
        "BATCH_SCREENING_EXPOSURE_LOG.json", "BATCH_DUPLICATE_REVIEW.json",
        "PROTOCOL_LOCK_A02.json", "a02-screening-round5/SCREENING_LEDGER.json",
        "a02-metadata/metadata_union.jsonl", "a02-dedup/work_records.json",
        "a02-screening/SCREENING_EXPOSURE_LOG.json", "build_batch_review.py",
    ]
    ledger = json.loads((BASE / inputs[5]).read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (BASE / inputs[1]).read_text(encoding="utf-8").splitlines()]
    metadata = [json.loads(line) for line in (BASE / inputs[6]).read_text(encoding="utf-8").splitlines()]
    works = json.loads((BASE / inputs[7]).read_text(encoding="utf-8"))
    duplicates = json.loads((BASE / inputs[3]).read_text(encoding="utf-8"))
    by_work = {row["work_id"]: row for row in ledger}
    assert len(by_work) == len(ledger) == len(works) == 373
    assert {e["work_id"] for e in events} == {
        row["work_id"] for row in ledger if row["decision"] == "NOT_SCREENED"
    }
    for event in events:
        row = by_work[event["work_id"]]
        row.update({k: event[k] for k in (
            "decision", "reason", "rationale", "metadata_view", "required_domain_evidence"
        )})
        row["adjudication_event"] = event["event_id"]
        row["eligibility"] = "NOT_DETERMINED"
    by_work["arxiv:2410.21146"]["required_domain_evidence"] = ["L"]
    counts = dict(sorted(collections.Counter(row["decision"] for row in ledger).items()))
    assert counts == {"EXCLUDE": 191, "INCLUDE": 5, "UNCLEAR": 177}
    assert all(row["version_selection"] == "NOT_RUN" for row in ledger)
    index = {(m["source"], m["source_id"]): m for m in metadata}
    work_index = {w["work_id"]: w for w in works}
    questions = []
    for row in ledger:
        if row["decision"] != "UNCLEAR":
            continue
        records = [index[(m["source"], m["source_id"])] for m in work_index[row["work_id"]]["members"]]
        questions.append({
            "review_id": f"Q{len(questions) + 1:03d}", "work_id": row["work_id"],
            "title": records[0]["title"], "captured_source_ids": [m["source_id"] for m in records],
            "source_links": list(dict.fromkeys(m["url"] for m in records if m["url"])),
            "required_evidence": row["required_domain_evidence"], "question_basis": row["rationale"],
            "decision": None, "reviewed_version_url": None, "method_dataset_locator": None,
            "method_only_rationale": None, "limitations": None,
        })
    assert all(set(q["required_evidence"]) <= NEEDS.keys() for q in questions)
    assert len({q["work_id"] for q in questions}) == 177
    out = BASE / "a02-screening-batch"
    out.mkdir(exist_ok=False)
    write_json(out / "SCREENING_LEDGER.json", ledger)
    answers = {"scope": "HUMAN_DOMAIN_METADATA_ONLY_NOT_THE_SIX_PAPER_EXTRACTION", "questions": questions,
               "duplicate_questions": [dict(d, decision=None, bibliographic_evidence_url=None,
                                              identity_rationale=None) for d in duplicates]}
    write_json(out / "BATCH_METADATA_ANSWERS_BLANK.json", answers)
    lines = [
        "# Consolidated B1 metadata review: all current questions", "",
        "177 provisional work-record domain questions and two bibliographic identity questions.",
        "Palisade is Q001. Prior human decisions001--004 remain recorded; no repeat review requested.",
        "Read the duplicate questions first: D01 may let one source review answer two domain rows.", "",
        "This is a feasibility-pilot domain screen within the arXiv/ACL-retrieved frame,",
        "not the six selected papers' independent outcome extraction. No papers have been drawn.",
        "Use only bibliographic and method/dataset sections. Do not return performance/FPR",
        "results, sample/false-positive counts, assurance classifications or an outcome sheet.", "",
        "For each Q row return INCLUDE / EXCLUDE / UNCLEAR, reviewed version URL, section/page",
        "locator, brief method rationale and any limitation. English-only purity is not required:",
        "state precisely whether English evaluation is supported directly, indirectly, or not",
        "established. Do not infer English evaluation from encoder name or paper prose alone.",
        "If a T/B/P requirement fails, a supported EXCLUDE resolves the row without further",
        "language work. Existing missing facts remain UNCLEAR; do not guess.", "",
        "Return one combined reply or fill BATCH_METADATA_ANSWERS_BLANK.json; its answer cells",
        "are blank. Evidence can be shared by explicit IDs, but each decision needs source support.",
        "Links are captured bibliographic locators, not finalized cutoff-selected versions.",
        "All domain inclusions still need locked version, sentinel and other eligibility checks.", "",
        "## Required evidence codes", "",
    ]
    lines += [f"- **{code}**: {need}" for code, need in NEEDS.items()]
    lines += ["", "## Bibliographic identity questions", ""]
    for pair in duplicates:
        lines += [f"### {pair['review_id']}", "", pair["bibliographic_basis"], "", pair["question"], ""]
        for wid, title in zip(pair["work_ids"], pair["titles"], strict=True):
            m = work_index[wid]["members"][0]
            url = index[(m["source"], m["source_id"])]["url"]
            lines += [f"- `{wid}`: [{title}]({url})"]
        lines.append("")
    lines += ["## Domain questions", "", "Grouped by required evidence; IDs follow the locked sorted-work order.", ""]
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for q in questions:
        groups["".join(q["required_evidence"])].append(q)
    for code, group in sorted(groups.items(), key=lambda x: (x[0] != "L", x[0])):
        lines += [f"### {code}: {len(group)} records", "", "| Review | Work and captured source | Required clarification |", "| --- | --- | --- |"]
        for q in group:
            title = q["title"].replace("|", "\\|").replace("\n", " ")
            why = q["question_basis"].replace("|", "\\|").replace("\n", " ")
            lines += [f"| {q['review_id']} | `{q['work_id']}` — [{title}]({q['source_links'][0]}) | {why} |"]
        lines.append("")
    lines += ["## Scope of this packet", "",
              "This collects every current unresolved domain record and known identity ambiguity",
              "from the unchanged snapshot. Some screening used abbreviated abstract previews;",
              "unresolved facts are questions, not inferred exclusions or full-text findings.",
              "No retrieved abstract outcome headline was used for inclusion/exclusion. Versions",
              "and accessibility remain separate, unperformed checks. Later source verification",
              "can reveal additional ambiguities; those must be batched and reported, not silently",
              "resolved by changing the frame. Historical protocols, ledgers and source bytes persist."]
    (out / "BATCH_METADATA_REVIEW_REQUEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "status": "FRAME_BLOCKED_AWAITING_BATCH_HUMAN_METADATA", "created_utc": now,
        "source_git_commit": head, "source_tree_clean_at_start": True, "python": sys.version.split()[0],
        "input_sha256": {name: digest(BASE / name) for name in inputs},
        "files": {p.name: digest(p) for p in sorted(out.iterdir())}, "counts": counts,
        "provisional_work_records": 373, "identity_questions": 2, "domain_questions": 177,
        "screening_cap": 500, "cap_check": "PASS_PROVISIONAL_COUNT_WITHIN_CAP",
        "screening_order": "SORTED_IDS_COLLECT_ALL_UNCLEAR_PER_USER_WORKFLOW_AUTHORIZATION",
        "first_pass_metadata_coverage": "ALL_RECORDS_HAVE_DOMAIN_DISPOSITION",
        "complete_eligible_frame": False, "source_refresh": False,
        "OpenReview_discovery": "EXCLUDED_FROM_SELECTION_FRAME", "version_selection": "NOT_RUN",
        "PDF_access_check": "NOT_RUN", "ten_paper_selection": "NOT_RUN",
        "human_six_assignment": "NOT_RUN", "outcome_extraction": "NOT_RUN",
        "claim_classification": "NOT_RUN", "B2": "NOT_AUTHORIZED",
    }
    write_json(out / "SCREENING_MANIFEST.json", manifest)
    print(json.dumps({"counts": counts, "domain_questions": len(questions), "identity_questions": len(duplicates)}))


if __name__ == "__main__":
    main()
