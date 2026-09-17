"""Release timestamps must not inject extra terminal lines or control codes."""

import json
from pathlib import Path

import pytest

from controlplane.release.render import render_evaluation


@pytest.mark.parametrize("separator", ["\n", "\x1b"])
def test_timestamp_separators_cannot_inject_terminal_output(separator):
    path = Path(__file__).parent / "fixtures/release_v1_measurement.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["expires_at"] = f"2030-01-01{separator}00:00:00Z"
    record["evaluated_at"] = f"2026-09-14{separator}00:00:00Z"
    output = render_evaluation(record, record["status"])
    assert "Expires: 2030-01-01T00:00:00+00:00" in output
    assert "Evaluated: 2026-09-14T00:00:00+00:00" in output
    assert "\x1b" not in output
    assert not any(line.startswith("00:00:00") for line in output.splitlines())
