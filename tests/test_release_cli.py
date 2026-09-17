"""Customer workflow tests using temporary synthetic files, never frozen scores."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from controlplane.intake.contract import InputError, load_scored_items


ROOT = Path(__file__).resolve().parents[1]


def run(*arguments):
    return subprocess.run([sys.executable, str(ROOT / "warrant.py"), "release", *arguments],
                          capture_output=True, text=True, timeout=60, cwd=ROOT,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})


@pytest.fixture
def workflow(tmp_path):
    spec = {"system_id": "support", "system_version": "1", "detector_id": "probe",
            "detector_version": "1", "scope": "English QA", "positive_label": "incorrect",
            "threshold": .5, "max_fpr": .05, "min_recall": .1, "alpha": .05,
            "expires_at": "2099-01-01T00:00:00Z", "data_origin": "synthetic",
            "sampling_assumption": "iid"}
    (tmp_path / "spec.json").write_bytes(json.dumps(spec).encode())
    (tmp_path / "context.json").write_bytes(json.dumps({k: spec[k] for k in
        ("system_id", "system_version", "detector_id", "detector_version", "scope", "positive_label")}).encode())
    (tmp_path / "development.txt").write_bytes(b"dev-1\n")
    (tmp_path / "holdout.txt").write_bytes("\n".join(f"q{i}" for i in range(600)).encode())
    (tmp_path / "scores.csv").write_bytes(("id,label,score\n" + "\n".join(
        f"q{i},{int(i >= 500)},{.9 if i >= 500 else .1}" for i in range(600))).encode())
    registered = run("register", "--spec", str(tmp_path / "spec.json"),
                     "--development-ids", str(tmp_path / "development.txt"),
                     "--holdout-ids", str(tmp_path / "holdout.txt"),
                     "--out", str(tmp_path / "contract.json"))
    assert registered.returncode == 0, registered.stderr
    return tmp_path


def arguments(root):
    return ("--contract", str(root / "contract.json"), "--input", str(root / "scores.csv"),
            "--context", str(root / "context.json"))


def test_real_cli_register_evaluate_verify_and_no_replacement(workflow):
    evaluated = run("evaluate", *arguments(workflow), "--require-valid")
    assert evaluated.returncode == 0, evaluated.stderr
    assert "SYNTHETIC FIXTURE" in evaluated.stdout
    assert "precision:" not in evaluated.stdout
    path = workflow / "contract.evaluation.json"
    original = path.read_bytes()
    assert json.loads(original)["status"] == "VALID"
    verified = run("verify", *arguments(workflow), "--require-valid")
    assert verified.returncode == 0, verified.stderr
    replacement = run("evaluate", *arguments(workflow))
    assert replacement.returncode == 2
    assert "already exists" in replacement.stderr
    assert path.read_bytes() == original


def test_failed_criterion_exits_one_only_when_required(workflow):
    path = workflow / "scores.csv"
    path.write_bytes(path.read_bytes().replace(b",1,0.9", b",1,0.1"))
    refused = run("evaluate", *arguments(workflow), "--require-valid")
    assert refused.returncode == 1, refused.stderr
    assert "REFUSED" in refused.stdout
    assert run("verify", *arguments(workflow)).returncode == 0


def test_missing_class_is_unvalidated_only_on_release_path(workflow):
    path = workflow / "scores.csv"
    path.write_bytes(path.read_bytes().replace(b",1,0.9", b",0,0.1"))
    with pytest.raises(InputError):
        load_scored_items(path)
    assert load_scored_items(path, require_both_classes=False).n_positive == 0
    result = run("evaluate", *arguments(workflow), "--require-valid")
    assert result.returncode == 1, result.stderr
    assert "UNVALIDATED" in result.stdout


def test_changed_scores_are_detected_even_without_changed_counts(workflow):
    assert run("evaluate", *arguments(workflow)).returncode == 0
    path = workflow / "scores.csv"
    path.write_bytes(path.read_bytes().replace(b",0,0.1", b",0,0.11"))
    result = run("verify", *arguments(workflow))
    assert result.returncode == 2
    assert "does not reproduce" in result.stderr


def test_release_help_does_not_load_numerical_or_research_packages():
    code = """
import sys
from controlplane.cli import build_parser
build_parser()
assert not ({'scipy', 'numpy', 'torch', 'sklearn'} & set(sys.modules))
"""
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
