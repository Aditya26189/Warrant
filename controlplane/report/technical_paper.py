"""Typeset and package the preprint; no publication or upload API is called."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from math import comb
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tex_escape(value: str) -> str:
    """Treat supplied metadata as text, not executable TeX."""
    mapping = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(c, c) for c in value)


def _witness_cp_values(n: int, alpha: float) -> tuple[float, float, float]:
    """Invert three binomial tails for manuscript intuition, not issuance.

    Each upper endpoint solves P(Binomial(n, p) <= k) = alpha.
    Bisection keeps this explanatory calculation free of model dependencies.
    """
    values = []
    for k in range(3):
        low, high = 0.0, 1.0
        for _ in range(100):
            midpoint = (low + high) / 2
            cdf = sum(
                comb(n, j) * midpoint**j * (1 - midpoint) ** (n - j)
                for j in range(k + 1)
            )
            if cdf > alpha:
                low = midpoint
            else:
                high = midpoint
        values.append((low + high) / 2)
    return values[0], values[1], values[2]


def generated_sources(root: Path) -> dict[str, str]:
    """Render numeric macros from retained evidence rather than copied values."""
    meta = read_json(root / "paper/metadata.json")
    audit = read_json(root / meta["audit_receipt"])
    manifest = read_json(root / "evalsets/triviaqa-600.json")
    validation = read_json(root / "results/validation-T1-last_token.json")
    witness = read_json(root / "results/publication/assurance_semantics.json")
    authors = " \\and ".join(tex_escape(x["name"]) for x in meta["authors"])
    affiliation = "; ".join(dict.fromkeys(x["affiliation"] for x in meta["authors"]))
    fields = {
        "PaperTitle": meta["title"],
        "PaperAffiliation": affiliation,
        "PaperDate": datetime.fromisoformat(meta["date"]).strftime("%d %B %Y"),
        "PaperVersion": meta["version"],
        "PaperRepository": meta["repository"],
        "PaperRepositoryRef": meta["repository_ref"],
    }
    header = [
        "% Generated from paper/metadata.json.",
        r"\newcommand{\PaperAuthor}{" + authors + "}",
    ]
    header += [r"\newcommand{\%s}{%s}" % (k, tex_escape(v)) for k, v in fields.items()]
    values = ["% Generated from retained evidence; original results are unchanged."]
    for row in audit["claims"]:
        for prefix, value in (("claim", row["value"]), ("ci", row["interval"])):
            values.append(
                r"\expandafter\def\csname %s%s\endcsname{%s}"
                % (prefix, row["id"], tex_escape(str(value)))
            )
    summary = audit["summary"]
    counts = next(
        x["counts"]
        for x in audit["frozen_score_point_checks"]
        if x["artifact"] == "results/validation-T1-last_token.json"
    )
    cp_values = _witness_cp_values(
        witness["config"]["n"], float(witness["config"]["alpha"])
    )
    macros = {
        "AuditClaims": summary["claims"],
        "AuditArtifacts": summary["distinct_artifacts"],
        "AuditFamilies": summary["families"],
        "DirtyClaims": summary["dirty_source_claims"],
        "PointTargets": summary["frozen_score_targets"],
        "DirectPointClaims": summary["claim_points_with_independent_evidence"],
        "AuditSourceCommit": audit["provenance"]["git_commit"],
        "CorpusRows": len(manifest["items"]),
        "TrainRows": validation["splits"]["train"],
        "ValidationRows": validation["splits"]["validation"],
        "TestRows": validation["splits"]["test"],
        "BaseRows": counts["n_rows"],
        "BasePositive": counts["n_positive"],
        "BaseFlagged": counts["n_flagged"],
        "BaseTP": counts["true_positives"],
        "WitnessN": witness["config"]["n"],
        "WitnessBudget": witness["config"]["budget"],
        "WitnessAlpha": witness["config"]["alpha"],
        "WitnessK": witness["config"]["design_k"],
        "WitnessQone": witness["config"]["q1"],
        "WitnessQtwo": witness["config"]["q2"],
        "WitnessUzero": f"{cp_values[0]:.11f}",
        "WitnessUone": f"{cp_values[1]:.11f}",
        "WitnessUtwo": f"{cp_values[2]:.11f}",
        "WitnessStates": witness["result"]["count_states"],
        "WitnessNoncoverage": f"{witness['result']['returned_realized_count_bound_noncoverage']['approximation']:.9f}",
    }
    values += [
        r"\newcommand{\%s}{%s}" % (k, tex_escape(str(v))) for k, v in macros.items()
    ]
    return {
        "metadata.tex": "\n".join(header) + "\n",
        "claims.tex": "\n".join(values) + "\n",
    }


def write_generated(root: Path) -> None:
    destination = root / "paper/generated"
    destination.mkdir(exist_ok=True)
    for name, text in generated_sources(root).items():
        (destination / name).write_bytes(text.encode("utf-8"))


def validate_sources(root: Path) -> list[str]:
    """Check metadata, stale generated values and bibliography references."""
    errors = []
    meta = read_json(root / "paper/metadata.json")
    if not meta.get("authors") or any(not a.get("name") for a in meta["authors"]):
        errors.append("author names are required")
    if meta.get("license") != "CC-BY-4.0":
        errors.append("metadata differs from the approved manuscript license")
    for name, expected in generated_sources(root).items():
        path = root / "paper/generated" / name
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            errors.append(f"stale generated source: {name}")
    tex = "\n".join(
        p.read_text(encoding="utf-8") for p in (root / "paper").rglob("*.tex")
    )
    used = {
        k.strip()
        for group in re.findall(r"\\cite[pt]?\{([^}]+)\}", tex)
        for k in group.split(",")
    }
    defined = re.findall(
        r"@\w+\s*\{\s*([^,\s]+)",
        (root / "paper/references.bib").read_text(encoding="utf-8"),
    )
    if len(defined) != len(set(defined)):
        errors.append("duplicate bibliography keys")
    if not used <= set(defined):
        errors.append("undefined citations: " + ", ".join(sorted(used - set(defined))))
    if "not peer reviewed" not in tex:
        errors.append("preprint status missing")
    return errors


def git_state(root: Path) -> tuple[str, str]:
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=root, text=True
    )
    return commit, status


def build_preprint(root: Path, output: Path, engine: Path) -> dict:
    """Compile an isolated input copy and retain exact source/output checksums."""
    errors = validate_sources(root)
    if errors:
        raise ValueError("; ".join(errors))
    before, status = git_state(root)
    if status.strip():
        raise ValueError("commit manuscript and code before generating a PDF receipt")
    if output.exists():
        raise ValueError("paper output directory must be new")
    output.mkdir(parents=True)
    snapshot = output / "latex"
    snapshot.mkdir()
    hashes = {}
    for path in sorted((root / "paper").rglob("*")):
        if path.suffix not in {".tex", ".bib"}:
            continue
        relative = path.relative_to(root / "paper")
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        hashes[relative.as_posix()] = sha256(target)
    version = subprocess.check_output([str(engine), "--version"], text=True).strip()
    command = [
        str(engine),
        "--untrusted",
        "--keep-logs",
        "--keep-intermediates",
        "--outdir",
        str(output.resolve()),
        "warrant.tex",
    ]
    run = subprocess.run(
        command,
        cwd=snapshot,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    (output / "compiler-output.log").write_bytes((run.stdout + run.stderr).encode())
    if run.returncode:
        raise RuntimeError(
            f"LaTeX exited {run.returncode}; inspect compiler-output.log in {output}"
        )
    log = (output / "warrant.log").read_text(encoding="utf-8", errors="replace")
    overfull = [
        float(v) for v in re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)", log)
    ]
    if any(
        s in log
        for s in ("There were undefined references", "Warning: Citation", "LaTeX Error")
    ):
        raise ValueError("unresolved LaTeX reference/citation; inspect retained log")
    if overfull and max(overfull) > 1:
        raise ValueError(f"overfull text box: {max(overfull)}pt")
    from pypdf import PdfReader

    pdf = output / "warrant.pdf"
    reader = PdfReader(pdf)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if "Aditya Singh" not in text or "not peer reviewed" not in text.lower():
        raise ValueError("PDF author/status text missing")
    after, changed = git_state(root)
    if after != before or changed.strip():
        raise ValueError("source changed during PDF build")
    receipt = {
        "kind": "preprint_typesetting_receipt",
        "source_commit": before,
        "dirty": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "engine": version,
        "command": command,
        "latex_inputs_sha256": hashes,
        "pdf_sha256": sha256(pdf),
        "pages": len(reader.pages),
        "undefined_references": False,
        "overfull_boxes_over_1pt": False,
        "visual_review": "REQUIRED_SEPARATELY",
        "new_model_or_benchmark_experiment": False,
    }
    (output / "build-receipt.json").write_bytes(
        (json.dumps(receipt, indent=2) + "\n").encode()
    )
    return receipt


def zenodo_metadata(root: Path) -> dict:
    """Prepare fields only; no token, upload, DOI assignment or publication."""
    meta = read_json(root / "paper/metadata.json")
    return {
        "metadata": {
            "title": meta["title"],
            "upload_type": "publication",
            "publication_type": "preprint",
            "creators": [
                {
                    "name": a["family"] + ", " + a["given"],
                    "affiliation": a["affiliation"],
                }
                for a in meta["authors"]
            ],
            "publication_date": meta["date"],
            "version": meta["version"],
            "access_right": "open",
            "license": "cc-by-4.0",
            "language": "eng",
            "keywords": [
                "AI evaluation",
                "reproducibility",
                "detector evaluation",
                "statistical interpretation",
                "evidence provenance",
            ],
            "description": "<p>Technical preprint, not peer reviewed. A local detector-evaluation "
            "toolkit, bounded empirical findings, adverse results and a claim/"
            "provenance audit. The native returned-bound interpretation and "
            "historical source gaps remain documented. No production or universal "
            "assurance claim is made.</p>",
            "notes": "CC BY 4.0 covers the manuscript and LaTeX source. Software retains MIT "
            "and third-party inputs retain their own notices. No DOI is invented.",
        }
    }


def package_preprint(root: Path, output: Path) -> dict:
    """Export tracked HEAD only, excluding ignored caches and untracked private work."""
    commit, status = git_state(root)
    if status.strip():
        raise ValueError("deposit package requires clean committed source")
    if output.exists():
        raise ValueError("deposit output directory must be new")
    pdf = root / "paper/warrant-preprint.pdf"
    if not pdf.exists():
        raise ValueError("reviewed PDF has not been retained")
    output.mkdir(parents=True)
    shutil.copyfile(pdf, output / pdf.name)
    subprocess.run(
        [
            "git",
            "archive",
            "--format=zip",
            "--output",
            str((output / "warrant-source-evidence.zip").resolve()),
            "HEAD",
        ],
        cwd=root,
        check=True,
    )
    with zipfile.ZipFile(
        output / "warrant-latex-source.zip", "w", zipfile.ZIP_DEFLATED
    ) as archive:
        for path in sorted((root / "paper").rglob("*")):
            if path.is_file() and (
                path.suffix in {".tex", ".bib"}
                or path.name in {"metadata.json", "toolchain.json", "LICENSE.md"}
            ):
                archive.write(path, path.relative_to(root / "paper").as_posix())
        archive.writestr(
            "README.txt",
            "Compile here with: tectonic --untrusted warrant.tex\n"
            "Generated numeric macros are retained. Regenerating them needs "
            "the accompanying source/evidence snapshot. Manuscript: CC BY 4.0.\n",
        )
    (output / "zenodo-metadata.json").write_bytes(
        (json.dumps(zenodo_metadata(root), indent=2) + "\n").encode()
    )
    (output / "README.txt").write_text(
        "Warrant preprint deposit preparation\nAuthor: Aditya Singh, IIT Kharagpur\n"
        "Technical preprint, not peer reviewed; no upload has occurred.\n"
        f"Tracked snapshot: {commit}\n"
        "Deposit the PDF, LaTeX source and source/evidence supplement together.\n"
        "The supplement exports tracked HEAD only, excluding ignored/untracked material.\n"
        "Paper/LaTeX: CC BY 4.0. Code: MIT. Preserve third-party notices.\n"
        "Review files and metadata, choose Preprint, then publish manually.\n"
        "A DOI is assigned/reserved through the author's Zenodo account, not invented here.\n",
        encoding="utf-8",
    )
    after, changed = git_state(root)
    if after != commit or changed.strip():
        raise ValueError("source changed while packaging")
    hashes = {p.name: sha256(p) for p in output.iterdir() if p.is_file()}
    (output / "SHA256SUMS").write_text(
        "".join(f"{v}  {k}\n" for k, v in sorted(hashes.items())),
        encoding="ascii",
    )
    receipt = {"source_commit": commit, "files_sha256": hashes, "uploaded": False}
    (output / "package-receipt.json").write_bytes(
        (json.dumps(receipt, indent=2) + "\n").encode()
    )
    return receipt
