"""Release only exact source prose approved by a separate live checker."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adjudicate as a  # noqa: E402

CACHE = HERE.parents[5] / "fpr-a05-source-20261023"


def checked_file(directory: Path, name: str, pin: str) -> tuple[bytes, dict]:
    """Refuse changed provider/checker bytes before semantic release."""
    raw = (directory / name).read_bytes()
    if a.sha(raw) != pin:
        raise ValueError("CHECKED_FILE_CHANGED:" + name)
    return raw, json.loads(raw)


def approved(decision: str, provider: str, checker: str) -> None:
    """A held fact or self-check cannot cross the release boundary."""
    if decision != "APPROVE" or provider == checker or not provider or not checker:
        raise ValueError("NOT_SEPARATELY_APPROVED")


def build() -> tuple[list, dict[str, bytes]]:
    """Normalize approved facts while preserving exact provider originals."""
    files = {}
    facts = []
    inventory = {c["review_id"]: c["inventory"] for c in
                 json.loads((HERE / "SOURCE_CASEBOOK.json").read_bytes())["cases"]}
    configs = [
        ("provider-01", "PROVIDER_DRAFT.0001.json", "9cb4afebf4135d9f838993647ca73e20f8ca7da18c8683eb39ef963e9da30efa",
         "CHECKER_A05.0001.json", "0df893356b9b744092e63683d7384eac3d6c81fdd6a6cabae54e3fa66268744d", "W0352"),
        ("provider-02", "PROVIDER_DRAFT_NOT_RELEASED.0001.json", "e478cb75d75e2b1bf09452f566e765ccf89f3ad94a385608366cbd73f8b3f13a",
         "CHECKER01.0001.json", "027c6e3d2a47974c9121632ec2a8867ea98bcdf9adfb8f57db3a5f725565a062", "W0062")]
    for sub, draft_name, draft_pin, checker_name, checker_pin, rid in configs:
        directory = CACHE / sub
        raw, draft = checked_file(directory, draft_name, draft_pin)
        checked_raw, checker = checked_file(directory, checker_name, checker_pin)
        files[sub + "-draft.json"] = raw
        files[sub + "-checker.json"] = checked_raw
        source_facts = draft.get("new_method_facts", draft.get("facts"))
        checks = {r["fact_id"]: r for r in checker.get("per_fact_checks", checker.get("fact_checks"))}
        provider = draft.get("actor_id", draft.get("provider_actor_id"))
        checker_actor = checker["actor_id"]
        for original in source_facts:
            check = checks[original["fact_id"]]
            approved(check.get("restriction_decision", check.get("decision")), provider, checker_actor)
            if sub == "provider-01":
                canonical = json.dumps(original, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
                if a.sha(canonical) != check["draft_fact_sha256_canonical_json"]:
                    raise ValueError("APPROVED_FACT_CHANGED")
            elif a.sha(json.dumps(original, sort_keys=True, ensure_ascii=False,
                                  separators=(",", ":")).encode()) != check["provider_fact_object_sha256"]:
                raise ValueError("APPROVED_FACT_CHANGED")
            facts.append({"evidence_id": original["fact_id"], "review_id": rid,
                "work_id": inventory[rid]["work_id"], "member_id": original["member_id"],
                "version": original["version"], "source_url": original["source_url"],
                "raw_source_sha256": original["raw_source_sha256"], "locator": original["locator"],
                "method_fact": original["method_fact"], "limitation": original["limitation"],
                "provider_actor": provider, "checker_actor": checker_actor,
                "checker_receipt_sha256": checker_pin, "original_draft_sha256": draft_pin,
                "release_status": "SEPARATELY_CHECKED_RESTRICTED_METHOD_ONLY",
                "eligibility_decision": None})
    directory = CACHE / "provider-03"
    raw, draft = checked_file(directory, "vor.method-data-provider-draft.0003.json",
                             "397b9510a04e407e2fb6c6c6a625c2886ee544a4f5e8dfc3ae031b65da144435")
    checker_raw, checker = checked_file(directory, "CHECKER_A05.0002.json",
                                      "db97a4fc7a46e7ec05ec92cc44ce35853a334ffd100e6beb41214a9e579b5966")
    approval = checker["corrected_summary_approval"]
    approved(approval["restriction_decision"], draft["actor_id"], checker["actor_id"])
    if a.sha(raw) != approval["draft_sha256"] or a.sha(draft["summary"].encode()) != approval["summary_sha256_utf8"]:
        raise ValueError("APPROVED_SUMMARY_CHANGED")
    metadata_raw, metadata = checked_file(directory, "vor.metadata-provider-draft.0002.json",
                                         checker["metadata_approval"]["draft_sha256"])
    capture_raw = (directory / "registered-vor-link.receipt.0001.json").read_bytes()
    capture = json.loads(capture_raw)
    if a.sha(Path(capture["private_raw_path"]).read_bytes()) != metadata["raw_pdf_sha256"]:
        raise ValueError("VOR_RAW_SOURCE_CHANGED")
    files.update({"provider-03-draft.json": raw, "provider-03-checker.json": checker_raw,
                  "provider-03-metadata.json": metadata_raw, "provider-03-capture.json": capture_raw})
    facts.append({"evidence_id": "A05-SRC03-W0339-M01", "review_id": "W0339",
        "work_id": inventory["W0339"]["work_id"], "member_id": "M0354",
        "version": "doi:10.1109/access.2026.3728186:vor:declared-2026-09-03",
        "source_url": capture["final_url"], "raw_source_sha256": metadata["raw_pdf_sha256"],
        "locator": {"format": "PDF", "checked_method_spans": checker["per_fact_checks"]},
        "method_fact": draft["summary"], "limitation": draft["gaps"],
        "provider_actor": draft["actor_id"], "checker_actor": checker["actor_id"],
        "checker_receipt_sha256": a.sha(checker_raw), "original_draft_sha256": a.sha(raw),
        "release_status": "SEPARATELY_CHECKED_RESTRICTED_METHOD_ONLY", "eligibility_decision": None})
    return facts, files


def main() -> None:
    """Create a new immutable release; never overwrite a source or old release."""
    head = a.clean_head()
    facts, files = build()
    destination = HERE / "checked-source-receipts"
    destination.mkdir(exist_ok=False)
    for name, raw in files.items():
        (destination / name).write_bytes(raw)
    release = {"source_git_commit": head, "released_by": "EXPOSED_CUSTODIAN_ROOT",
        "facts": facts, "source_files": {name: a.sha(raw) for name, raw in files.items()},
        "scope": "No outcomes, counts, assurance classifications or eligibility decisions. Shared-filesystem source-role separation, not OS isolation or independent final review."}
    with (HERE / "RELEASED_FACTS_001.json").open("xb") as stream:
        stream.write(a.encoded(release))
    print(json.dumps({"released_facts": len(facts), "source_files": len(files), "source_git_commit": head}))


if __name__ == "__main__":
    main()
