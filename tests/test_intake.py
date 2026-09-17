"""The bring-your-own-data path: the contract, the refusal, and both examples.

The acceptance question for Phase 2 is behavioural rather than structural — can
a stranger with a CSV reach a warrant without asking anyone anything. These
tests are the parts of that question a suite can answer:

* every rejection names the column, the row and what was expected, because an
  error a user cannot act on is a support ticket;
* a shortage of evidence is a **refusal that exits 0**, never an error, since a
  tool that exits non-zero on "your detector cannot be certified here" teaches
  its user that refusals are malfunctions;
* both shipped examples do what their README says they do, run as a subprocess
  the way a person runs them.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from controlplane.intake import (
    InputError,
    certify_items,
    load_scored_items,
    render_summary,
)
from controlplane.model import WarrantStatus

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = PROJECT_ROOT / "examples"


def _write(tmp_path: Path, text: str, name: str = "in.csv") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _valid_rows(n: int = 80, positives_every: int = 4) -> str:
    rows = ["id,label,score"]
    for i in range(n):
        label = 1 if i % positives_every == 0 else 0
        score = 0.9 - 0.001 * i if label else 0.2 + 0.001 * i
        rows.append(f"item_{i},{label},{score:.4f}")
    return "\n".join(rows) + "\n"


# ------------------------------------------------------------ the contract

def test_a_minimal_valid_file_loads(tmp_path: Path) -> None:
    items = load_scored_items(_write(tmp_path, _valid_rows()))
    assert items.n == 80
    assert items.n_positive == 20
    assert items.n_negative == 60
    assert items.groups is None
    assert items.n_units == 80


def test_jsonl_is_read_the_same_way(tmp_path: Path) -> None:
    lines = [
        json.dumps({"id": f"i{i}", "label": i % 2, "score": 0.1 * i})
        for i in range(10)
    ]
    items = load_scored_items(_write(tmp_path, "\n".join(lines), "in.jsonl"))
    assert items.n == 10
    assert items.n_positive == 5


def test_passthrough_columns_are_carried_and_unused(tmp_path: Path) -> None:
    """Extra columns are named on the parsed items and touch no computation.

    No record keeps them; ``docs/INPUT.md`` says so, because it once said the
    opposite.
    """
    rows = ["id,label,score,captured_at,reviewer"]
    for i in range(60):
        rows.append(f"i{i},{i % 3 == 0 and 1 or 0},{0.5 + 0.001 * i},2026-01-01,alice")
    items = load_scored_items(_write(tmp_path, "\n".join(rows)))
    assert items.passthrough_columns == ("captured_at", "reviewer")
    assert items.n == 60


@pytest.mark.parametrize(
    "text, expected",
    [
        ("label,score\n1,0.5\n", "missing required column"),
        ("id,score\ni1,0.5\n", "missing required column"),
        ("id,label\ni1,1\n", "missing required column"),
    ],
)
def test_missing_columns_name_what_is_missing(tmp_path: Path, text: str, expected: str) -> None:
    with pytest.raises(InputError, match=expected) as exc:
        load_scored_items(_write(tmp_path, text))
    # The message has to be actionable: it names the contract and what it found.
    assert "docs/INPUT.md" in str(exc.value)


def test_a_non_binary_label_is_refused_with_its_row(tmp_path: Path) -> None:
    text = "id,label,score\ni1,0,0.1\ni2,0.7,0.9\n"
    with pytest.raises(InputError, match="row 3") as exc:
        load_scored_items(_write(tmp_path, text))
    message = str(exc.value)
    assert "not 0 or 1" in message
    # Polarity is the silent killer, so the error restates it.
    assert "should fire" in message.lower()


def test_a_float_label_that_is_exactly_binary_is_accepted(tmp_path: Path) -> None:
    """A spreadsheet writes 1.0; that is still a label. 0.7 is not."""
    text = "id,label,score\ni1,0.0,0.1\ni2,1.0,0.9\n"
    items = load_scored_items(_write(tmp_path, text))
    assert items.labels == (0, 1)


def test_a_non_numeric_score_is_refused(tmp_path: Path) -> None:
    text = "id,label,score\ni1,0,0.1\ni2,1,high\n"
    with pytest.raises(InputError, match="row 3"):
        load_scored_items(_write(tmp_path, text))


def test_a_non_finite_score_is_refused_not_dropped(tmp_path: Path) -> None:
    text = "id,label,score\ni1,0,0.1\ni2,1,NaN\n"
    with pytest.raises(InputError, match="NaN|not be ordered|infinity"):
        load_scored_items(_write(tmp_path, text))


def test_an_empty_cell_is_never_filled_in(tmp_path: Path) -> None:
    text = "id,label,score\ni1,0,0.1\ni2,,0.9\n"
    with pytest.raises(InputError, match="empty"):
        load_scored_items(_write(tmp_path, text))


def test_duplicate_ids_are_refused(tmp_path: Path) -> None:
    text = "id,label,score\nsame,0,0.1\nsame,1,0.9\n"
    with pytest.raises(InputError, match="duplicate id"):
        load_scored_items(_write(tmp_path, text))


@pytest.mark.parametrize("label", [0, 1])
def test_a_single_class_file_is_refused(tmp_path: Path, label: int) -> None:
    rows = ["id,label,score"] + [f"i{i},{label},{0.1 * i}" for i in range(20)]
    with pytest.raises(InputError, match="every label is"):
        load_scored_items(_write(tmp_path, "\n".join(rows)))


def test_an_unknown_extension_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="csv"):
        load_scored_items(_write(tmp_path, _valid_rows(), "scores.parquet"))


def test_a_blank_group_cell_is_refused(tmp_path: Path) -> None:
    text = "id,label,score,group\ni1,0,0.1,a\ni2,1,0.9,\n"
    with pytest.raises(InputError, match="group"):
        load_scored_items(_write(tmp_path, text))


def test_groups_change_the_unit_of_inference(tmp_path: Path) -> None:
    """Two hundred items from twenty documents are twenty units, not two hundred."""
    rows = ["id,label,score,group"]
    for i in range(80):
        rows.append(f"i{i},{1 if i % 4 == 0 else 0},{0.5 + 0.001 * i},doc_{i // 4}")
    items = load_scored_items(_write(tmp_path, "\n".join(rows)))
    assert items.n == 80
    assert items.n_units == 20
    assert items.equal_group_sizes is True


# ------------------------------------------------------- refusal, not error

def test_insufficient_evidence_is_a_refusal(tmp_path: Path, config) -> None:
    items = load_scored_items(_write(tmp_path, _valid_rows(n=40)))
    result = certify_items(config, items, budget=0.01)

    assert result.status is WarrantStatus.REFUSED
    assert result.certified is False
    # The two numbers a user needs next.
    assert result.min_units_required == 299
    assert result.negative_units == items.n_negative
    assert "need >=" in result.reason
    # A refusal carries no metrics: there is no threshold to measure at.
    assert result.recall is None and result.precision is None

    summary = render_summary(result)
    assert "REFUSED" in summary
    assert "What would change it" in summary
    assert "This is the tool working" in summary
    assert str(result.min_units_required) in summary


def test_the_same_data_certifies_at_a_budget_it_can_support(tmp_path: Path, config) -> None:
    """The pedagogical point of the examples README, asserted."""
    items = load_scored_items(_write(tmp_path, _valid_rows(n=40)))
    assert certify_items(config, items, budget=0.01).status is WarrantStatus.REFUSED
    loose = certify_items(config, items, budget=0.20)
    assert loose.status is WarrantStatus.VALID
    assert loose.threshold is not None


def test_a_certified_result_carries_intervals_on_every_rate(tmp_path: Path, config) -> None:
    """Invariants 4 and 5, on the customer path as much as the research one."""
    items = load_scored_items(_write(tmp_path, _valid_rows(n=200)))
    result = certify_items(config, items, budget=0.10)
    assert result.status is WarrantStatus.VALID
    for metric in (result.recall, result.precision, result.flag_rate):
        assert metric is not None
        assert metric.ci_low is not None and metric.ci_high is not None
    assert (result.recall is None) == (result.precision is None)

    summary = render_summary(result)
    assert "recall" in summary and "precision" in summary
    assert "f1" not in summary.lower()


def test_the_bound_is_respected_on_the_supplied_negatives(tmp_path: Path, config) -> None:
    """A certified threshold must actually deliver the budget it certified."""
    items = load_scored_items(_write(tmp_path, _valid_rows(n=200)))
    result = certify_items(config, items, budget=0.10)
    labels, scores, _ = items.as_arrays()
    achieved = float((scores[labels == 0] >= result.threshold).mean())
    assert achieved <= result.budget
    assert result.fpr_upper_bound <= result.budget


def test_unequal_groups_are_refused_rather_than_certified_anticonservatively(
    tmp_path: Path, config
) -> None:
    """The one input shape the tool tells you to change instead of judging."""
    rows = ["id,label,score,group"]
    rows += [f"i{i},{1 if i % 5 == 0 else 0},{0.5 + 0.001 * i},big" for i in range(40)]
    rows += [f"j{i},{1 if i % 5 == 0 else 0},{0.4 + 0.001 * i},small_{i}" for i in range(10)]
    items = load_scored_items(_write(tmp_path, "\n".join(rows)))
    with pytest.raises(ValueError, match="anticonservative"):
        certify_items(config, items, budget=0.10)


@pytest.mark.parametrize("budget", [0.0, 1.0, -0.1, 1.5])
def test_a_budget_outside_the_unit_interval_is_rejected(
    tmp_path: Path, config, budget: float
) -> None:
    items = load_scored_items(_write(tmp_path, _valid_rows()))
    with pytest.raises(ValueError, match="false-positive rate"):
        certify_items(config, items, budget=budget)


# ------------------------------------------------------------ the examples

def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "warrant.py"), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )


def test_the_certifying_example_certifies(tmp_path: Path) -> None:
    """`examples/certifies.csv` does what examples/README.md says."""
    out = tmp_path / "rec.json"
    result = _run_cli(
        "certify", "-i", str(EXAMPLES / "certifies.csv"), "-b", "0.05", "-o", str(out)
    )
    assert result.returncode == 0, result.stderr
    assert "WARRANT: VALID" in result.stdout

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "VALID"
    assert payload["certification"]["threshold"] is not None
    assert payload["certification"]["fpr_upper_bound"] <= 0.05
    for name in ("recall", "precision", "flag_rate"):
        metric = payload["metrics"][name]
        assert metric["ci_low"] <= metric["value"] <= metric["ci_high"]


def test_the_refusing_example_refuses_and_exits_zero(tmp_path: Path) -> None:
    """The one that sells. A refusal is a result, so the shell sees success."""
    out = tmp_path / "rec.json"
    result = _run_cli(
        "certify", "-i", str(EXAMPLES / "refuses.csv"), "-b", "0.01", "-o", str(out)
    )
    assert result.returncode == 0, (
        "a refusal must exit 0 -- exiting non-zero teaches every CI pipeline "
        "that 'your detector cannot be certified here' is a broken tool\n"
        + result.stderr
    )
    assert "WARRANT: REFUSED" in result.stdout
    assert "299" in result.stdout, "the number needed is not on screen"

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "REFUSED"
    assert payload["certification"]["min_units_required"] == 299
    assert payload["certification"]["threshold"] is None


def test_require_warrant_flips_the_exit_code_and_still_says_why(tmp_path: Path) -> None:
    """A non-zero exit without a reason is the least useful way to say no."""
    result = _run_cli(
        "certify", "-i", str(EXAMPLES / "refuses.csv"), "-b", "0.01",
        "--require-warrant", "-q", "-o", str(tmp_path / "rec.json"),
    )
    assert result.returncode == 1
    assert "REFUSED" in result.stderr
    assert "299" in result.stderr, "the shortfall is not explained on stderr"


def test_the_refusing_example_certifies_at_a_looser_budget(tmp_path: Path) -> None:
    """examples/README.md promises this; a stranger will type it."""
    result = _run_cli(
        "certify", "-i", str(EXAMPLES / "refuses.csv"), "-b", "0.20", "-q",
        "-o", str(tmp_path / "rec.json"),
    )
    assert result.returncode == 0, result.stderr


def test_a_bad_file_exits_two_and_says_why(tmp_path: Path) -> None:
    bad = _write(tmp_path, "id,score\ni1,0.5\n", "bad.csv")
    result = _run_cli("certify", "-i", str(bad), "-b", "0.05")
    assert result.returncode == 2
    assert "missing required column" in result.stderr
    assert "docs/INPUT.md" in result.stderr


def test_the_examples_are_reproducible_from_their_generator(tmp_path: Path) -> None:
    """The committed examples match what the seeded script produces."""
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "22_make_examples.py"),
         "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=900, check=True,
    )
    for name in ("certifies.csv", "refuses.csv"):
        assert (tmp_path / name).read_text(encoding="utf-8") == (
            EXAMPLES / name
        ).read_text(encoding="utf-8"), f"{name} is not reproducible from its seed"
