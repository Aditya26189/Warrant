"""Archive the bounded hardening checks without changing the original packet."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from experiments.grader_poc.run_trial import file_hashes, git_output, write_receipt


def archive(work: Path, review: Path) -> dict:
    """Preserve raw hashes, redact host paths, and bind checks to their source."""
    root = Path(__file__).resolve().parents[2]
    if git_output(root, "status", "--porcelain"):
        raise RuntimeError("Commit archival source first")
    here = Path(__file__).parent
    frozen = here / "results"
    manifest = json.loads((frozen / "evidence-manifest.json").read_bytes())
    if any(hashlib.sha256((frozen / name).read_bytes()).hexdigest() != value
           for name, value in manifest["packaged_files"].items()):
        raise ValueError("Original packet changed")
    validation = json.loads((work / "grader-hardening-validation-001/outcome.json").read_bytes())
    full = json.loads((work / "grader-hardening-full-reference-001/outcome.json").read_bytes())
    if validation["status"] != "PASSED" or full["status"] != "COMPLETED" or full["reward"] != 1:
        raise ValueError("Hardening checks incomplete")
    run = work / "grader-hardening-full-reference-001"
    trial = (run / full["trials"][0]["path"]).parent
    original = json.loads((frozen / "summary.json").read_bytes())
    expected = next(row["candidate_hashes"] for row in original["trials"] if row["run"] == "reference-001")
    if file_hashes(trial / "artifacts/app/app") != expected:
        raise ValueError("Reference candidate drifted")
    out = here / "hardening"
    out.mkdir(exist_ok=False)
    home = str(Path.home())
    posix = home.replace("\\", "/")
    wsl = "/mnt/" + posix[0].lower() + posix[2:] if ":" in posix else posix
    replacements = sorted({home, home.replace("\\", "\\\\"), posix, wsl}, key=len, reverse=True)
    copies = []

    def copy_file(source: Path, relative: str) -> None:
        raw = source.read_bytes()
        text = raw.decode("utf-8-sig")
        for prefix in replacements:
            text = text.replace(prefix, "${HOST_HOME}")
        text = re.sub(r"/tmp/warrant-grader-poc-[0-9]+-venv", "${HARBOR_VENV}", text)
        data = text.encode("utf-8")
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        copies.append({"path": relative, "raw_sha256": hashlib.sha256(raw).hexdigest(),
                       "packaged_sha256": hashlib.sha256(data).hexdigest()})

    for folder, label in ((work / "grader-hardening-validation-001", "validation"), (run, "full-reference")):
        for path in sorted(folder.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                copy_file(path, label + "/" + path.relative_to(folder).as_posix())
    for name in ("REVIEW.md", "packet-audit.json", "fresh-full-replay-verified.json", "fresh-witness-replay.json",
                 "timeout-handling-review.json", "docker-timeout-lifecycle.json", "lint.txt"):
        copy_file(review / name, "prior-review/" + name)
    for name in ("grader-hardening-lint.txt", "grader-hardening-ruff-version.txt"):
        copy_file(work / name, name)
    copy_file(frozen / "TERMINAL_BENCH_LICENSE.txt", "TERMINAL_BENCH_LICENSE.txt")
    unit_log = (work / "grader-hardening-validation-001/unit-tests.txt").read_text(encoding="utf-8")
    summary = {"source_commit": validation["source_commit"], "archive_commit": git_output(root, "rev-parse", "HEAD"),
               "source_dirty": False, "live_checks_passed": sum(row["passed"] for row in validation["checks"]),
               "unit_tests": int(re.search(r"Ran (\d+) tests", unit_log).group(1)),
               "unit_tests_exit_code": validation["unit_tests_exit_code"],
               "full_reference_reward": full["reward"], "full_reference_candidate_matches_original": True,
               "original_packet_payload_hashes_verified": len(manifest["packaged_files"]),
               "population_rate_claim": False, "review_provenance": "Separate assistant execution; not independent human or blinded review"}
    write_receipt(out / "summary.json", summary)
    write_receipt(out / "manifest.json", {"copies": copies, "packaged_files": file_hashes(out),
                  "redaction": "Host home and temporary virtualenv paths replaced by role placeholders; UTF-8 BOM removed. Raw inputs retained locally."})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(archive(args.work.resolve(), args.review_root.resolve()), indent=2))
