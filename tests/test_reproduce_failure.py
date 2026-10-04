"""A failed activation replay must not masquerade as an absent-cache skip."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from controlplane.report import reproduce


ROOT = Path(__file__).resolve().parents[1]


def failed_replay(tmp_path: Path, monkeypatch) -> reproduce.ReproductionReport:
    """Model a child that found its cache but could not finish revalidation."""
    cache = tmp_path / "results" / "cache-triviaqa-600.npz"
    cache.parent.mkdir()
    cache.write_bytes(b"retained cache")
    monkeypatch.setattr(
        reproduce.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 1, stderr="PermissionError: cannot write scratch output"
        ),
    )
    return reproduce.reproduce_frozen_set(tmp_path)


def test_failed_revalidation_is_a_failure_not_a_skip(tmp_path, monkeypatch) -> None:
    report = failed_replay(tmp_path, monkeypatch)
    assert not report.ran
    assert not report.ok
    assert report.status == "DRIFT"
    rendered = reproduce.render(report)
    assert "FAILED" in rendered
    assert "SKIPPED" not in rendered


def test_absent_cache_remains_an_explicit_skip(tmp_path) -> None:
    report = reproduce.reproduce_frozen_set(tmp_path)
    assert not report.ran
    assert report.ok
    assert report.status == "SKIPPED"
    assert "SKIPPED" in reproduce.render(report)


def test_verify_cli_exits_nonzero_when_cached_revalidation_fails(
    tmp_path, monkeypatch, capsys
) -> None:
    report = failed_replay(tmp_path, monkeypatch)
    spec = importlib.util.spec_from_file_location("verify_cli_failure_test", ROOT / "scripts" / "verify.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "check_claims", lambda *args: [SimpleNamespace(ok=True)])
    monkeypatch.setattr(module, "render_claims", lambda *args: "1/1 claims reproduce")
    monkeypatch.setattr(
        module,
        "reproduce_from_scores",
        lambda *args: reproduce.ReproductionReport(
            ran=True,
            reason="recomputed from scores",
            diffs=[reproduce.VariantDiff("control", "VALID", "VALID")],
        ),
    )
    monkeypatch.setattr(module, "reproduce_frozen_set", lambda *args, **kwargs: report)
    monkeypatch.setattr(sys, "argv", ["verify.py"])

    assert module.main() == 1
    output = capsys.readouterr()
    assert "TIER|3|activations|DRIFT|0/0" in output.out
    assert "VERIFIED" not in output.out


def test_verify_cli_exits_nonzero_when_frozen_scores_are_missing(
    tmp_path, monkeypatch, capsys
) -> None:
    report = reproduce.reproduce_from_scores(tmp_path)
    spec = importlib.util.spec_from_file_location(
        "verify_cli_missing_scores_test", ROOT / "scripts" / "verify.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "check_claims", lambda *args: [SimpleNamespace(ok=True)])
    monkeypatch.setattr(module, "render_claims", lambda *args: "1/1 claims reproduce")
    monkeypatch.setattr(module, "reproduce_from_scores", lambda *args: report)
    monkeypatch.setattr(sys, "argv", ["verify.py", "--no-activations"])

    assert module.main() == 1
    output = capsys.readouterr()
    assert "TIER|2|frozen_scores|DRIFT|0/0" in output.out
    assert "VERIFIED" not in output.out
