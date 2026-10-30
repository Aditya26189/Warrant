"""Offline fixtures protect resource and identity boundaries, not model quality."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import urllib.error
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("stopping_recon", Path(__file__).parents[1] / "recon.py")
assert SPEC and SPEC.loader
recon = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recon)
PIN = "a" * 40


class Response(io.BytesIO):
    def __init__(self, body: bytes, headers: dict[str, str] | None = None, status: int = 200):
        super().__init__(body)
        self.headers = headers or {}
        self.status = status
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return super().read(size)


class Opener:
    def __init__(self, response: Response | Exception):
        self.response = response
        self.calls = 0

    def open(self, request: object, timeout: float) -> Response:
        self.calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def request(**kwargs: object) -> dict[str, object]:
    return {"label": "sample", "url": "https://example.org/rows?revision=" + PIN,
            "max_bytes": 1000, **kwargs}


def test_revision_requires_returned_identity() -> None:
    with pytest.raises(ValueError, match="no dataset revision"):
        recon.validate_revision({"requested_revision": PIN}, PIN)
    with pytest.raises(ValueError, match="differs"):
        recon.validate_revision({"x-revision": PIN, "dataset_git_revision": "b" * 40}, PIN)
    assert recon.validate_revision({"Dataset_Git_Revision": PIN}, PIN) == PIN


def test_bounded_payload_hash_and_json_revision(tmp_path: Path) -> None:
    body = json.dumps({"dataset_git_revision": PIN, "rows": []}).encode()
    receipt = recon.fetch_one(request(expected_revision=PIN), tmp_path, 0, 1000, 3,
                              Opener(Response(body, {"Content-Length": str(len(body)), "Set-Cookie": "private"})))
    assert receipt["ok"] and receipt["observed_revision"] == PIN
    assert receipt["body_bytes"] == len(body)
    assert receipt["body_sha256"] == hashlib.sha256((tmp_path / receipt["body_file"]).read_bytes()).hexdigest()
    assert "set-cookie" not in receipt["headers"]


def test_unknown_length_never_reads_past_aggregate_remainder(tmp_path: Path) -> None:
    response = Response(b"abcdef")
    receipt = recon.fetch_one(request(), tmp_path, 0, 4, 3, Opener(response))
    assert receipt["body_bytes"] == 4 and not receipt["ok"]
    assert not receipt["body_complete"] and response.read_sizes == [4]
    assert (tmp_path / receipt["body_file"]).read_bytes() == b"abcd"


def test_advertised_oversize_is_rejected_without_body_read(tmp_path: Path) -> None:
    response = Response(b"large", {"Content-Length": "1001"})
    receipt = recon.fetch_one(request(), tmp_path, 0, 1000, 3, Opener(response))
    assert receipt["body_bytes"] == 0 and not receipt["ok"]
    assert response.read_sizes == [] and receipt["body_file"] is None
    assert (tmp_path / "000-sample.receipt.json").exists()


def test_http_error_body_is_preserved_and_charged(tmp_path: Path) -> None:
    error = urllib.error.HTTPError("https://example.org/rows", 404, "missing", {}, io.BytesIO(b"not found"))
    receipt = recon.fetch_one(request(), tmp_path, 0, 1000, 3, Opener(error))
    assert receipt["status"] == 404 and not receipt["ok"]
    assert receipt["body_bytes"] == 9 and receipt["body_complete"]
    assert (tmp_path / receipt["body_file"]).read_bytes() == b"not found"


def test_configuration_rejects_url_userinfo_and_excessive_global_cap(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_bytes(json.dumps({"requests": [request(url="https://user:secret@example.org/rows")]}).encode())
    with pytest.raises(ValueError, match="credentials"):
        recon.load_config(config)
    config.write_bytes(json.dumps({"requests": [request()], "max_total_bytes": recon.MAX_TOTAL_BYTES + 1}).encode())
    with pytest.raises(ValueError, match="16 MiB"):
        recon.load_config(config)


def test_run_refuses_nonempty_output_before_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.json"
    config.write_bytes(json.dumps({"requests": [request()]}).encode())
    output = tmp_path / "output"
    output.mkdir()
    (output / "existing").write_bytes(b"preserve")
    monkeypatch.setattr(recon, "clean_git_provenance", lambda _: {"git_root": str(tmp_path / "repo")})
    opener = Opener(Response(b""))
    with pytest.raises(ValueError, match="new or empty"):
        recon.run(config, output, opener)
    assert opener.calls == 0 and (output / "existing").read_bytes() == b"preserve"


def test_run_charges_failed_partial_body_against_later_requests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.json"
    raw = json.dumps({"max_total_bytes": 4, "requests": [request(max_bytes=4), request(label="next", max_bytes=4)]}).encode()
    config.write_bytes(raw)
    monkeypatch.setattr(recon, "clean_git_provenance", lambda _: {"git_root": str(tmp_path / "repo"), "dirty": False})
    opener = Opener(Response(b"abcdef"))
    report = recon.run(config, tmp_path / "output", opener)
    assert report["total_body_bytes"] == 4 and opener.calls == 1 and not report["complete"]
    assert report["requests"][1]["effective_max_bytes"] == 0
    assert report["provenance"]["config_sha256"] == hashlib.sha256(raw).hexdigest()


def test_nested_source_provenance_uses_root_relative_tracked_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    nested = repo / "study"
    nested.mkdir(parents=True)
    source = nested / "recon.py"
    source.write_bytes(b"# synthetic provenance fixture\n")
    config = nested / "config.json"
    config.write_bytes(b"{}\n")
    for args in (["init", "-q"], ["add", "--", "study/recon.py", "study/config.json"],
                 ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"]):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    monkeypatch.setattr(recon, "__file__", str(source))
    provenance = recon.clean_git_provenance(config)
    assert provenance["dirty"] is False and provenance["source_path"] == "study/recon.py"
    assert provenance["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    source.write_bytes(b"# changed synthetic fixture\n")
    with pytest.raises(RuntimeError, match="clean Git"):
        recon.clean_git_provenance(config)
