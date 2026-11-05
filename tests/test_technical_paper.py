"""Manuscript provenance and publication-free packaging contracts."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

from controlplane.report import technical_paper as paper

ROOT = Path(__file__).resolve().parents[1]


def test_generated_paper_values_are_current():
    assert paper.validate_sources(ROOT) == []


def test_explanatory_witness_bounds_match_independent_beta_quantiles():
    """The narrow gap below q1 must survive the displayed precision."""
    from scipy.stats import beta

    witness = paper.read_json(ROOT / "results/publication/assurance_semantics.json")
    n, alpha = witness["config"]["n"], float(witness["config"]["alpha"])
    actual = paper._witness_cp_values(n, alpha)
    expected = tuple(float(beta.ppf(1 - alpha, k + 1, n - k)) for k in range(3))
    assert actual == pytest.approx(expected, abs=1e-14, rel=0)
    shown = tuple(float(f"{value:.11f}") for value in actual)
    assert shown[0] < float(witness["config"]["q2"]) < shown[1]
    assert shown[1] < float(witness["config"]["q1"]) <= float(witness["config"]["budget"])
    assert shown[2] > float(witness["config"]["budget"])


def test_author_metadata_is_escaped_as_text():
    assert paper.tex_escape(r"A&B_%\input{x}") == r"A\&B\_\%\textbackslash{}input\{x\}"


def test_deposit_metadata_preserves_author_license_without_invented_doi():
    metadata = paper.zenodo_metadata(ROOT)["metadata"]
    assert metadata["creators"] == [
        {"name": "Singh, Aditya", "affiliation": "IIT Kharagpur"}
    ]
    assert metadata["license"] == "cc-by-4.0"
    assert metadata["publication_type"] == "preprint"
    assert "doi" not in metadata
    assert "orcid" not in metadata["creators"][0]


def test_missing_citation_and_stale_macro_are_detected(tmp_path):
    shutil.copytree(ROOT / "paper", tmp_path / "paper")
    relative = json.loads((ROOT / "paper/metadata.json").read_text())["audit_receipt"]
    for name in [
        relative,
        "evalsets/triviaqa-600.json",
        "results/validation-T1-last_token.json",
        "results/publication/assurance_semantics.json",
    ]:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    with (tmp_path / "paper/warrant.tex").open("a") as stream:
        stream.write("\n" + r"\citep{missing-primary-source}" + "\n")
    (tmp_path / "paper/generated/claims.tex").write_text("stale")
    errors = paper.validate_sources(tmp_path)
    assert "undefined citations: missing-primary-source" in errors
    assert "stale generated source: claims.tex" in errors


def test_build_refuses_dirty_source_before_invoking_engine(tmp_path, monkeypatch):
    monkeypatch.setattr(paper, "git_state", lambda root: ("a" * 40, " M source"))
    with pytest.raises(ValueError, match="commit manuscript"):
        paper.build_preprint(ROOT, tmp_path / "new-build", Path("nonexistent"))
    assert not (tmp_path / "new-build").exists()


def test_build_preserves_existing_destination(tmp_path, monkeypatch):
    monkeypatch.setattr(paper, "git_state", lambda root: ("a" * 40, ""))
    output = tmp_path / "existing"
    output.mkdir()
    (output / "keep").write_text("original")
    with pytest.raises(ValueError, match="must be new"):
        paper.build_preprint(ROOT, output, Path("nonexistent"))
    assert (output / "keep").read_text() == "original"


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_packaging_exports_tracked_source_and_excludes_private_files(tmp_path):
    root = tmp_path / "fixture"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    (root / "paper").mkdir()
    for name, content in {
        "warrant-preprint.pdf": b"packaging fixture, not a scientific PDF",
        "warrant.tex": b"fixture",
        "references.bib": b"",
        "LICENSE.md": b"CC BY 4.0",
        "metadata.json": (ROOT / "paper/metadata.json").read_bytes(),
        "toolchain.json": (ROOT / "paper/toolchain.json").read_bytes(),
    }.items():
        (root / "paper" / name).write_bytes(content)
    (root / ".gitignore").write_text("private-ignored.txt\n")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture source")
    (root / "private-ignored.txt").write_text("PRIVATE")
    (root / "private-untracked.txt").write_text("PRIVATE")
    with pytest.raises(ValueError, match="clean committed"):
        paper.package_preprint(root, tmp_path / "blocked")
    (root / "private-untracked.txt").unlink()
    output = tmp_path / "deposit"
    receipt = paper.package_preprint(root, output)
    assert receipt["uploaded"] is False
    with zipfile.ZipFile(output / "warrant-source-evidence.zip") as archive:
        assert ".gitignore" in archive.namelist()
        assert not any("private-" in name for name in archive.namelist())
    with zipfile.ZipFile(output / "warrant-latex-source.zip") as archive:
        assert "warrant.tex" in archive.namelist()
        assert "metadata.json" in archive.namelist()
        assert not any(name.endswith(".pdf") for name in archive.namelist())
    assert (
        paper.sha256(output / "warrant-preprint.pdf")
        == receipt["files_sha256"]["warrant-preprint.pdf"]
    )
    with pytest.raises(ValueError, match="must be new"):
        paper.package_preprint(root, output)


def test_publication_and_audit_imports_do_not_load_plotting_or_model_stacks():
    import sys

    code = (
        "import sys; import controlplane.report.technical_paper; "
        "import controlplane.report.documentation_audit; "
        "assert not {'matplotlib','sklearn','torch','transformers'} & set(sys.modules)"
    )
    run = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode == 0, run.stderr
