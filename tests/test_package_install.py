"""Exercise built distributions through their installed console entry point.

No network is used. These tests reuse the running interpreter's dependencies;
the CI customer jobs supply only customer requirements and build/test tools.
Both wheel builds occur in disposable source copies, never in the checkout.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from dataclasses import dataclass

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


def _run(arguments: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(arguments, cwd=cwd, env=env, capture_output=True,
                          text=True, encoding="utf-8", timeout=180)


def _successful(arguments: list[str], cwd: Path, env: dict[str, str]) -> None:
    result = _run(arguments, cwd, env)
    assert result.returncode == 0, result.stdout + result.stderr


@dataclass(frozen=True)
class Installed:
    """A real installed entry point with its package ahead of incidental paths."""

    command: Path
    site: Path
    wheels: tuple[Path, ...]
    env: dict[str, str]

    def run(self, cwd: Path, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess:
        result = _run([str(self.command), *arguments], cwd, self.env)
        assert result.returncode == expected, result.stdout + result.stderr
        assert "Traceback" not in result.stderr, result.stderr
        return result


@pytest.fixture(scope="module")
def installed(tmp_path_factory) -> Installed:
    workspace = tmp_path_factory.mktemp("installed-wheel")
    source = workspace / "source"
    source.mkdir()
    for name in ("pyproject.toml", "README.md", "LICENSE", "config.yaml",
                 "MANIFEST.in", "build_support.py"):
        shutil.copyfile(ROOT / name, source / name)
    shutil.copytree(ROOT / "controlplane", source / "controlplane",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PIP_NO_INDEX": "1",
           "PIP_DISABLE_PIP_VERSION_CHECK": "1"}
    env.pop("PYTHONPATH", None)
    # A real consumer often installs a venv below their application's .git.
    # The resulting records must not identify that unrelated commit as ours.
    _successful(["git", "init", "--quiet", str(workspace)], workspace, env)
    hooks = workspace / "empty-hooks"
    hooks.mkdir()
    _successful(["git", "-c", "user.name=Packaging fixture",
                 "-c", "user.email=fixture@example.invalid",
                 "-c", f"core.hooksPath={hooks}", "-c", "commit.gpgsign=false",
                 "commit", "--allow-empty", "--quiet", "-m", "Unrelated consumer repository"],
                workspace, env)
    direct = workspace / "direct"
    direct.mkdir()
    archives = workspace / "archives"
    archives.mkdir()
    _successful([sys.executable, "-c",
                 "from setuptools.build_meta import build_wheel, build_sdist; "
                 "import sys; wheel_dir, sdist_dir = sys.argv[1:]; "
                 "build_wheel(wheel_dir); build_sdist(sdist_dir)",
                 str(direct), str(archives)], source, env)

    # Extract our own sdist without trusting archive paths or following links.
    extracted = workspace / "extracted"
    extracted.mkdir()
    with tarfile.open(next(archives.glob("*.tar.gz"))) as archive:
        for member in archive.getmembers():
            destination = (extracted / member.name).resolve()
            assert destination.is_relative_to(extracted.resolve())
            assert member.isdir() or member.isfile()
            if member.isfile():
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as stream:
                    destination.write_bytes(stream.read())
    sdist_source, = [path for path in extracted.iterdir() if path.is_dir()]
    rebuilt = workspace / "rebuilt"
    rebuilt.mkdir()
    _successful([sys.executable, "-c",
                 "from setuptools.build_meta import build_wheel; "
                 "import sys; build_wheel(sys.argv[1])", str(rebuilt)], sdist_source, env)
    direct_wheel, = direct.glob("*.whl")
    rebuilt_wheel, = rebuilt.glob("*.whl")
    site = workspace / "installed"
    _successful([sys.executable, "-m", "pip", "install", "--no-deps", "--no-compile",
                 "--target", str(site), str(rebuilt_wheel)], workspace, env)
    command = site / "bin" / ("warrant.exe" if os.name == "nt" else "warrant")
    assert command.is_file(), command
    return Installed(command, site, (direct_wheel, rebuilt_wheel),
                     {**env, "PYTHONPATH": str(site)})


def _scores(root: Path, *, negatives: int = 500, second: bool = False) -> Path:
    path = root / "scores.csv"
    rows = ["id,label,score" + (",label_2" if second else "")]
    for i in range(negatives + 100):
        label = int(i >= negatives)
        score = 0.8 + (i - negatives) / 1000 if label else 0.1 + i / (5 * negatives)
        rows.append(f"q{i},{label},{score}" + (f",{label}" if second else ""))
    path.write_bytes(("\n".join(rows) + "\n").encode())
    return path


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_wheels_include_canonical_defaults_and_all_python_packages(installed):
    required = {str(path.relative_to(ROOT)).replace("\\", "/")
                for path in (ROOT / "controlplane").rglob("*.py")}
    for wheel in installed.wheels:
        with zipfile.ZipFile(wheel) as archive:
            assert required <= set(archive.namelist())
            assert archive.read("controlplane/default_config.yaml") == (ROOT / "config.yaml").read_bytes()


def test_imports_resolve_to_the_installed_distribution(installed, tmp_path):
    code = (
        "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
        "import controlplane, controlplane.sampling; "
        "from controlplane.config import load_customer_config, provenance; "
        "assert Path(controlplane.__file__).is_relative_to(Path(sys.argv[1])); "
        "assert Path(controlplane.sampling.__file__).is_relative_to(Path(sys.argv[1])); "
        "p = provenance(load_customer_config()); "
        "assert all(p[k] is None for k in ('git_commit','git_branch','dirty','dirty_paths')), p; "
        "assert not ({'torch','sklearn','transformers','spacy'} & set(sys.modules))"
    )
    _successful([sys.executable, "-I", "-c", code, str(installed.site)], tmp_path, installed.env)


@pytest.mark.parametrize("second", [False, True], ids=["ordinary", "second-label"])
def test_installed_certification_ignores_incidental_config(installed, tmp_path, second):
    scores = _scores(tmp_path, second=second)
    (tmp_path / "config.yaml").write_bytes(b"broken: [\n")
    record = tmp_path / "warrant.json"
    installed.run(tmp_path, "certify", "-i", str(scores), "-b", ".05", "-o", str(record), "-q")
    payload = _json(record)
    assert payload["status"] == "VALID"
    assert payload["input"]["n"] == 600
    assert payload["provenance"]["git_commit"] is None
    assert payload["provenance"]["dirty"] is None
    if second:
        assert payload["labels"]["second_review"]["n_pairs"] == 600
    else:
        assert payload["labels"]["second_review"]["present"] is False
    from controlplane.config import load_config
    assert payload["provenance"]["config_hash"] == load_config(ROOT / "config.yaml").config_hash


def test_installed_refusal_is_a_result_with_opt_in_failure(installed, tmp_path):
    scores = _scores(tmp_path, negatives=10)
    record = tmp_path / "refused.json"
    args = ("certify", "-i", str(scores), "-b", ".01", "-o", str(record), "-q")
    installed.run(tmp_path, *args)
    assert _json(record)["status"] == "REFUSED"
    installed.run(tmp_path, *args, "--require-warrant", expected=1)


def test_installed_grouped_review_withholds_population_intervals(installed, tmp_path):
    """The shipped wheel must preserve group metadata through both CLI paths."""
    source = _scores(tmp_path, second=True)
    lines = source.read_text(encoding="utf-8").splitlines()
    grouped = [lines[0] + ",group"] + [
        row + f",g{i // 2}" for i, row in enumerate(lines[1:])
    ]
    source.write_bytes(("\n".join(grouped) + "\n").encode())
    warrant, recheck = tmp_path / "grouped-warrant.json", tmp_path / "grouped-recheck.json"
    certified = installed.run(tmp_path, "certify", "-i", str(source), "-b", ".05", "-o", str(warrant))
    checked = installed.run(tmp_path, "recheck", "-w", str(warrant), "-i", str(source), "-o", str(recheck))
    for record, result in ((warrant, certified), (recheck, checked)):
        review = _json(record)["labels"]["second_review"]
        assert review["n_pairs"] == 600
        assert review["kappa"]["n_groups"] == 300
        assert review["kappa"]["kind"] == "EXACT"
        assert review["kappa"]["ci_low"] is None and review["kappa"]["ci_high"] is None
        assert review["kappa"]["interval_computed"] is False
        assert "not a population estimate" in review["kappa"]["scope"]
        assert review["disputes"]["computed"] is False
        assert "300 reviewed groups" in result.stdout
        assert "population interval withheld" in result.stdout


def test_installed_drift_revocation_survives_an_inconclusive_fpr_warning(installed, tmp_path):
    """Audit R3 through the installed executable, including follow-up refusal."""
    from controlplane.intake import score_distribution
    from controlplane.model import to_jsonable
    import numpy as np

    scores = np.repeat(np.arange(.05, 1, .1), [10] * 8 + [858, 62])
    labels = np.ones(1000, dtype=int)
    labels[:94], labels[-6:] = 0, 0
    rows = ["id,label,score"] + [
        f"audit{i},{label},{score}" for i, (label, score) in enumerate(zip(labels, scores, strict=True))
    ]
    source, warrant = tmp_path / "shifted.csv", tmp_path / "warrant.json"
    source.write_bytes(("\n".join(rows) + "\n").encode())
    warrant.write_bytes(json.dumps({
        "status": "VALID", "budget_fpr": .05, "alpha": .05,
        "input": {"grouped": False}, "certification": {"threshold": .94},
        "score_distribution": to_jsonable(score_distribution(np.linspace(0, 1, 1000))),
    }).encode())
    first, later = tmp_path / "first.json", tmp_path / "later.json"
    installed.run(tmp_path, "recheck", "-w", str(warrant), "-i", str(source),
                  "--horizon-labels", "100000", "--require-valid", "-o", str(first), expected=1)
    payload = _json(first)
    assert payload["status"] == payload["drift"]["verdict"] == "REVOKED"
    assert payload["now"]["bound_still_holds"] is True
    assert payload["chain"]["revoked_at_unit"] is None
    installed.run(tmp_path, "chain", "verify", str(first), "--require-clean", "-q",
                  "-o", str(tmp_path / "verification.json"))
    rejected = installed.run(tmp_path, "recheck", "-w", str(warrant), "-i", str(source),
                             "--since", str(first), "--fork", "-o", str(later), expected=2)
    assert "REVOKED" in rejected.stderr
    assert not later.exists()


def test_installed_explicit_config_is_used(installed, tmp_path):
    raw = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    raw["seed"] += 1
    custom = tmp_path / "settings.yaml"
    custom.write_bytes(yaml.safe_dump(raw).encode())
    record = tmp_path / "custom.json"
    installed.run(tmp_path, "certify", "-i", str(_scores(tmp_path)), "-b", ".05",
                  "--config", str(custom), "-o", str(record), "-q")
    assert _json(record)["provenance"]["seed"] == raw["seed"]


@pytest.mark.parametrize("contents", [None, b"broken: [", b"- wrong shape"])
def test_installed_bad_explicit_config_exits_two_without_output(installed, tmp_path, contents):
    custom = tmp_path / "bad.yaml"
    if contents is not None:
        custom.write_bytes(contents)
    output = tmp_path / "must-not-exist.json"
    installed.run(tmp_path, "certify", "-i", str(_scores(tmp_path)), "-b", ".05",
                  "--config", str(custom), "-o", str(output), expected=2)
    assert not output.exists()


def test_installed_plan_recheck_and_chain_verification(installed, tmp_path):
    scores = _scores(tmp_path, second=True)
    warrant = tmp_path / "warrant.json"
    installed.run(tmp_path, "certify", "-i", str(scores), "-b", ".05", "-o", str(warrant), "-q")
    plan = tmp_path / "plan.json"
    installed.run(tmp_path, "plan", "-w", str(warrant), "--negative-share", ".8",
                  "-o", str(plan), "-q")
    assert _json(plan)["budget"] == _json(warrant)["budget_fpr"]
    fresh = tmp_path / "fresh.csv"
    fresh.write_bytes(scores.read_bytes().replace(b"\nq", b"\nfresh"))
    ordinary = tmp_path / "ordinary.json"
    installed.run(tmp_path, "recheck", "-w", str(warrant), "-i", str(fresh),
                  "-o", str(ordinary), "-q")
    assert _json(ordinary)["status"] == "VALID"
    chained = tmp_path / "chained.json"
    installed.run(tmp_path, "recheck", "-w", str(warrant), "-i", str(fresh),
                  "--horizon-labels", "10000", "-o", str(chained), "-q")
    verification = tmp_path / "verification.json"
    installed.run(tmp_path, "chain", "verify", str(chained), "--require-clean",
                  "-o", str(verification), "-q")
    assert _json(verification)["clean"] is True


def test_installed_release_register_evaluate_verify(installed, tmp_path):
    scores = _scores(tmp_path)
    spec = {"system_id": "support", "system_version": "1", "detector_id": "fixture",
            "detector_version": "1", "scope": "synthetic packaging check",
            "positive_label": "needs review", "threshold": .5, "max_fpr": .05,
            "min_recall": .1, "alpha": .05, "expires_at": "2099-01-01T00:00:00Z",
            "data_origin": "synthetic", "sampling_assumption": "iid"}
    (tmp_path / "spec.json").write_bytes(json.dumps(spec).encode())
    context = {key: spec[key] for key in ("system_id", "system_version", "detector_id",
                                        "detector_version", "scope", "positive_label")}
    (tmp_path / "context.json").write_bytes(json.dumps(context).encode())
    (tmp_path / "development.txt").write_bytes(b"development-only\n")
    (tmp_path / "holdout.txt").write_bytes("\n".join(f"q{i}" for i in range(600)).encode())
    contract = tmp_path / "contract.json"
    installed.run(tmp_path, "release", "register", "--spec", str(tmp_path / "spec.json"),
                  "--development-ids", str(tmp_path / "development.txt"),
                  "--holdout-ids", str(tmp_path / "holdout.txt"), "--out", str(contract))
    args = ("--contract", str(contract), "--input", str(scores),
            "--context", str(tmp_path / "context.json"))
    result = installed.run(tmp_path, "release", "evaluate", *args, "--require-valid")
    assert "SYNTHETIC FIXTURE" in result.stdout
    assert _json(tmp_path / "contract.evaluation.json")["status"] == "VALID"
    installed.run(tmp_path, "release", "verify", *args, "--require-valid")
    installed.run(tmp_path, "release", "evaluate", *args, expected=2)


def test_installed_recheck_respects_another_process_publication_lease(installed, tmp_path):
    """A wheel consumer must get the same serialization as a source checkout."""
    scores = _scores(tmp_path)
    warrant, output = tmp_path / "warrant.json", tmp_path / "scores.csv.recheck-0001.json"
    installed.run(tmp_path, "certify", "-i", str(scores), "-b", ".05", "-o", str(warrant), "-q")
    ready = tmp_path / "lease-ready"
    worker = r"""
import json, sys
from pathlib import Path
import controlplane.intake.chain_publication as publication
assert Path(publication.__file__).is_relative_to(Path(sys.argv[1]))
warrant, ready = map(Path, sys.argv[2:])
with publication.chain_publication(warrant, json.loads(warrant.read_bytes())):
    ready.write_bytes(b"locked")
    sys.stdin.readline()
"""
    process = subprocess.Popen(
        [sys.executable, "-c", worker, str(installed.site), str(warrant), str(ready)],
        cwd=tmp_path, env=installed.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    arguments = ("recheck", "-w", str(warrant), "-i", str(scores),
                 "--horizon-labels", "10000", "-q")
    try:
        deadline = time.monotonic() + 30
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists(), "installed worker did not acquire its lease"
        blocked = installed.run(tmp_path, *arguments, expected=2)
        assert "busy" in blocked.stderr
        assert not output.exists()
        stdout, stderr = process.communicate("release\n", timeout=30)
        assert process.returncode == 0, stdout + stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)
    installed.run(tmp_path, *arguments)
    verification = tmp_path / "verified.json"
    installed.run(tmp_path, "chain", "verify", str(output), "--require-clean",
                  "-o", str(verification), "-q")
    assert _json(verification)["clean"] is True
    assert not Path(str(warrant) + ".chain-pending").exists()
    assert Path(str(warrant) + ".chain-lock").is_file()
