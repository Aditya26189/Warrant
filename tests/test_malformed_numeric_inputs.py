"""A record's numbers are refused, not crashed on (``DECISIONS.md`` 208).

R7 of ``reports/PROJECT-REVIEW-2026-09-23.md``: an arbitrary-size integer is
valid JSON, so any record read back can carry one. ``math.isfinite`` converts to
double first, so the guard meant to reject such a value raised ``OverflowError``
instead, and two public commands exited 1 with a traceback.

These tests hold both record families to the same rule through the public
commands, because that is where the defect was visible. The unit tests below
pin the boundary itself: the conversion is the test, and a bit-length bound is
not -- ``2**1024 - 1`` has 1024 bits and still overflows, which is the same
off-by-one defect one value further along.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from controlplane.numeric import NumericDomainError, finite_double, is_real_number

ROOT = Path(__file__).resolve().parents[1]

#: Reproduced in the review, and the reason this module exists.
OVERSIZED = 10 ** 1000


def warrant(*arguments):
    """The public command, as a customer runs it."""
    return subprocess.run([sys.executable, str(ROOT / "warrant.py"), *arguments],
                          capture_output=True, text=True, timeout=900, cwd=ROOT,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def no_traceback(result) -> bool:
    return "Traceback (most recent call last)" not in result.stderr


def _export(path: Path, *, n_neg: int, n_pos: int, seed: int) -> Path:
    rng = np.random.default_rng(seed)
    rows = ["id,label,score"]
    rows += [f"{path.stem}-n{i},0,{rng.normal(0.0, 1.0):.6f}" for i in range(n_neg)]
    rows += [f"{path.stem}-p{i},1,{rng.normal(2.5, 1.0):.6f}" for i in range(n_pos)]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# The primitive
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("value", [0, 1, -1, 0.5, -2.5, 2 ** 1023, 1e308, -1e308])
def test_a_representable_real_is_returned_as_a_float(value) -> None:
    assert finite_double(value, "the value") == float(value)


@pytest.mark.parametrize("value", [True, False])
def test_a_boolean_is_not_a_number(value) -> None:
    """``True`` is an ``int`` in Python, so ``"alpha": true`` would read as 1."""
    assert not is_real_number(value)
    with pytest.raises(NumericDomainError, match="not a number"):
        finite_double(value, "the value")


@pytest.mark.parametrize("value", ["0.5", None, [], {}, complex(1, 1)])
def test_a_non_number_is_refused_by_name(value) -> None:
    with pytest.raises(NumericDomainError, match="not a number"):
        finite_double(value, "the value")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_a_non_finite_float_is_refused(value) -> None:
    with pytest.raises(NumericDomainError, match="not a finite number"):
        finite_double(value, "the value")


@pytest.mark.parametrize("value", [OVERSIZED, -OVERSIZED, 2 ** 1024, 2 ** 1024 - 1])
def test_an_integer_too_large_for_a_double_is_refused_at_the_exact_boundary(value) -> None:
    """``2**1024 - 1`` is the case a bit-length bound would have let through."""
    with pytest.raises(NumericDomainError, match="not representable as a finite number"):
        finite_double(value, "the value")


def test_the_message_names_the_field_and_counts_digits_rather_than_printing_them() -> None:
    with pytest.raises(NumericDomainError) as caught:
        finite_double(OVERSIZED, "the chain's alpha")
    message = str(caught.value)
    assert message.startswith("the chain's alpha is an integer of 1001 digits")
    assert "0000" not in message, "the value itself must not be printed back"


# --------------------------------------------------------------------------- #
# A chained recheck record, through the public commands
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def chain(tmp_path_factory):
    """A warrant and one chained record, written by the CLI."""
    root = tmp_path_factory.mktemp("malformed_numbers")
    warrant_path = root / "w.json"
    issued = warrant("certify", "-i", str(_export(root / "base.csv", n_neg=700, n_pos=200, seed=1)),
                     "-b", "0.05", "-q", "-o", str(warrant_path))
    assert issued.returncode == 0, issued.stderr
    link = root / "link1.json"
    fed = warrant("recheck", "-w", str(warrant_path), "-i",
                  str(_export(root / "a.csv", n_neg=700, n_pos=200, seed=2)),
                  "--horizon-labels", "100000", "-q", "-o", str(link))
    assert fed.returncode == 0, fed.stderr
    return {"root": root, "warrant": warrant_path, "link": link,
            "record": json.loads(link.read_text(encoding="utf-8"))}


def _with_chain_field(chain, tmp_path: Path, field: str, value) -> Path:
    record = json.loads(json.dumps(chain["record"]))
    record["chain"][field] = value
    path = tmp_path / "edited.recheck-0001.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


@pytest.mark.parametrize("field", ["alpha", "horizon_units", "units_consumed", "p0"])
def test_an_oversized_number_in_a_chain_block_is_a_finding_not_a_traceback(
    chain, tmp_path, field
) -> None:
    """The reproduced defect: this exited 1 with ``OverflowError`` before 208."""
    edited = _with_chain_field(chain, tmp_path, field, OVERSIZED)
    out = tmp_path / "verification.json"
    result = warrant("chain", "verify", str(edited), "-q", "-o", str(out))
    assert no_traceback(result), result.stderr[-400:]
    assert result.returncode == 0, "findings are a result, and exit 0"
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["clean"] is False
    assert "malformed" in {finding["kind"] for finding in payload["findings"]}


def test_the_finding_names_the_field_and_not_its_thousand_digits(chain, tmp_path) -> None:
    edited = _with_chain_field(chain, tmp_path, "alpha", OVERSIZED)
    out = tmp_path / "verification.json"
    assert warrant("chain", "verify", str(edited), "-q", "-o", str(out)).returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    malformed = [f for f in payload["findings"] if f["kind"] == "malformed"]
    assert malformed and "alpha" in malformed[0]["detail"]
    assert "0000000" not in malformed[0]["detail"]


def test_an_unedited_record_still_verifies_clean(chain, tmp_path) -> None:
    """The control: the normal findings behaviour is unchanged by 208."""
    kept = tmp_path / "kept.recheck-0001.json"
    kept.write_text(json.dumps(chain["record"]), encoding="utf-8")
    out = tmp_path / "verification.json"
    result = warrant("chain", "verify", str(kept), "-q", "-o", str(out))
    assert result.returncode == 0 and no_traceback(result)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["clean"] is True and payload["findings"] == []


def test_a_chain_cannot_be_continued_from_a_record_with_an_unusable_number(
    chain, tmp_path
) -> None:
    """``--since`` consumes the record, so it refuses with the input code."""
    edited = _with_chain_field(chain, tmp_path, "alpha", OVERSIZED)
    result = warrant("recheck", "-w", str(chain["warrant"]), "-i",
                     str(_export(tmp_path / "next.csv", n_neg=700, n_pos=200, seed=3)),
                     "--since", str(edited), "-q", "-o", str(tmp_path / "link2.json"))
    assert no_traceback(result), result.stderr[-400:]
    assert result.returncode == 2
    assert not (tmp_path / "link2.json").exists(), "no record is written on a refusal"


# --------------------------------------------------------------------------- #
# A release specification, through the public command
# --------------------------------------------------------------------------- #

def _spec(**overrides) -> dict:
    spec = {"system_id": "support", "system_version": "1", "detector_id": "probe",
            "detector_version": "1", "scope": "English QA", "positive_label": "incorrect",
            "threshold": .5, "max_fpr": .05, "min_recall": .1, "alpha": .05,
            "expires_at": "2099-01-01T00:00:00Z", "data_origin": "synthetic",
            "sampling_assumption": "iid"}
    spec.update(overrides)
    return spec


def _register(tmp_path: Path, spec: dict):
    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    (tmp_path / "development.txt").write_text("dev-1\n", encoding="utf-8")
    (tmp_path / "holdout.txt").write_text("q1\nq2\n", encoding="utf-8")
    return warrant("release", "register", "--spec", str(tmp_path / "spec.json"),
                   "--development-ids", str(tmp_path / "development.txt"),
                   "--holdout-ids", str(tmp_path / "holdout.txt"),
                   "--out", str(tmp_path / "contract.json"))


@pytest.mark.parametrize("field", ["threshold", "max_fpr", "min_recall", "alpha"])
def test_an_oversized_number_in_a_release_specification_is_an_input_error(
    tmp_path, field
) -> None:
    """The reproduced defect: this exited 1 with ``OverflowError`` before 208."""
    result = _register(tmp_path, _spec(**{field: OVERSIZED}))
    assert no_traceback(result), result.stderr[-400:]
    assert result.returncode == 2
    assert field in result.stderr
    assert not (tmp_path / "contract.json").exists(), "no contract is registered"


@pytest.mark.parametrize("value", [float("nan"), True, "0.5", None])
def test_a_specification_number_that_is_not_a_finite_real_is_refused(tmp_path, value) -> None:
    result = _register(tmp_path, _spec(threshold=value))
    assert no_traceback(result), result.stderr[-400:]
    assert result.returncode == 2


def test_an_ordinary_specification_still_registers(tmp_path) -> None:
    """The control: 208 refuses unusable numbers and nothing else."""
    result = _register(tmp_path, _spec())
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "contract.json").is_file()
