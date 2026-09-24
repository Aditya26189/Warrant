"""Dependent review pairs cannot manufacture a population interval (decision 201)."""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pytest

from controlplane.cli import main
from controlplane.intake import (
    certify_items, load_scored_items, recheck_items, render_recheck, render_summary,
)
from controlplane.intake.labels import recheck_second_review, second_review
from controlplane.sampling.agreement import AgreementError, cohens_kappa


def test_repeating_dependent_pairs_keeps_only_descriptive_agreement(monkeypatch):
    """A grouped call must never run the independent-pair bootstrap."""
    def no_bootstrap(*args, **kwargs):
        pytest.fail("grouped agreement attempted independent-pair resampling")

    monkeypatch.setattr(np.random, "default_rng", no_bootstrap)
    first, second = [0, 0, 1, 1], [0, 1, 0, 1]
    for copies in (1, 100):
        result = cohens_kappa(
            first * copies, second * copies, groups=["a", "b", "c", "d"] * copies,
        )
        assert result.kappa == 0.0
        assert result.observed_agreement == result.expected_agreement == 0.5
        assert result.n_pairs == 4 * copies
        assert result.n_groups == 4
        assert result.ci_low is None and result.ci_high is None
        assert "dependent pairs" in result.interval_reason
        assert "population interval withheld" in result.render()
        assert "not a population estimate" in result.render()
        assert "95% CI" not in result.render()


def test_unequal_reviewed_groups_keep_the_observed_pair_weighting():
    """Group coverage is a count, not a reweighting of the observed 2x2 table."""
    result = cohens_kappa(
        [0, 0, 0, 1, 1], [0, 0, 1, 1, 0], groups=["large"] * 3 + ["small"] * 2,
    )
    assert result.n_pairs == 5 and result.n_groups == 2
    assert result.observed_agreement == pytest.approx(3 / 5)
    assert result.expected_agreement == pytest.approx(0.52)
    assert result.kappa == pytest.approx(1 / 6)
    assert result.ci_low is None and result.ci_high is None


def test_constant_grouped_labels_are_undefined_and_still_name_the_groups():
    result = cohens_kappa([0] * 4, [0] * 4, groups=["a", "a", "b", "b"])
    assert result.kappa is None
    assert result.ci_low is None and result.ci_high is None
    assert result.n_groups == 2
    assert "0/0" in result.undefined_reason
    assert "UNDEFINED" in result.render()
    assert "2 reviewed groups" in result.render()
    assert "population interval withheld" in result.render()


@pytest.mark.parametrize("groups", [["a"], ["a", None], ["a", ""], ["a", "  "], ["a", 1]])
def test_reviewed_group_metadata_must_be_complete_and_aligned(groups):
    with pytest.raises(AgreementError, match="groups must"):
        cohens_kappa([0, 1], [0, 1], groups=groups)


def test_ungrouped_bootstrap_matches_the_pre_repair_result():
    """Fixed input/seed captured at d981fdc; decision 201 preserves this path."""
    result = cohens_kappa(
        [0] * 12 + [1] * 8, [0] * 10 + [1] * 2 + [0] * 3 + [1] * 5,
        seed=17, resamples=200,
    )
    assert result.kappa == pytest.approx(0.4680851063829787)
    assert result.ci_low == pytest.approx(2.405483220021182e-16, abs=1e-15)
    assert result.ci_high == pytest.approx(0.7917203608247424)
    assert result.n_pairs == 20
    assert result.n_groups is None and result.interval_reason == ""
    assert "95% CI, 20 pairs" in result.render()


def _review_call(path, *, groups=None, grouped=True, second=(0, None, 1, 0)):
    kwargs = dict(
        threshold=0.5, k=0, n=2, budget=0.05, alpha=0.05, grouped=grouped,
        groups=groups, seed=17, resamples=200, ci=0.95,
    )
    args = (np.array([0, 0, 1, 1]), second, np.array([0.1, 0.1, 0.9, 0.9]))
    if path == "certify":
        return second_review(*args, certified=False, **kwargs)
    return recheck_second_review(*args, bound_holds=None, **kwargs)


@pytest.mark.parametrize("path", ["certify", "recheck"])
@pytest.mark.parametrize("grouped,groups", [
    (True, None), (False, ["a", "a", "b", "b"]), (True, ["a", "a", "b"]),
    (True, ["a", None, "b", "b"]), (True, ["a", " ", "b", "b"]),
    (True, [["a"], ["a"], ["b"], ["b"]]),
])
def test_both_intake_paths_reject_missing_or_inconsistent_groups(path, grouped, groups):
    """A blank ID on an unreviewed row is also inconsistent metadata."""
    with pytest.raises(ValueError, match="group"):
        _review_call(path, grouped=grouped, groups=groups)


@pytest.mark.parametrize("path", ["certify", "recheck"])
def test_empty_second_review_is_not_agreement(path):
    with pytest.raises(ValueError, match="no item carries label_2"):
        _review_call(path, groups=["a", "a", "b", "b"], second=[None] * 4)


@pytest.mark.parametrize("path", ["certify", "recheck"])
def test_ungrouped_payload_keeps_the_existing_schema(path):
    review = _review_call(path, grouped=False)
    agreement = cohens_kappa([0, 1, 1], [0, 1, 0], seed=17, resamples=200)
    assert review.to_payload()["kappa"] == {
        "kind": "ESTIMATED", "value": agreement.kappa,
        "ci_low": agreement.ci_low, "ci_high": agreement.ci_high, "n": 3,
        "estimator": "Cohen's kappa, percentile bootstrap over pairs",
        "observed_agreement": agreement.observed_agreement,
        "expected_agreement": agreement.expected_agreement,
        "interpretation": agreement.interpretation,
        "undefined_reason": agreement.undefined_reason,
    }


def _grouped_file(tmp_path, *, constant=False):
    """Equal source groups, unequal second-review coverage, many unreviewed groups."""
    rows = ["id,label,score,group,label_2"]
    for group in range(80):
        label = int(group >= 64)
        for item in range(4):
            second = ""
            if group == 0 or (group == 1 and item == 0):
                second = "0"
            if not constant:
                if group == 64:
                    second = str(int(item != 3))
                elif group == 65 and item < 2:
                    second = "1"
            rows.append(f"g{group}-{item},{label},{0.8 if label else 0.1},g{group},{second}")
    path = tmp_path / "grouped.csv"
    path.write_bytes(("\n".join(rows) + "\n").encode())
    return path


@pytest.mark.parametrize("path", ["certify", "recheck"])
@pytest.mark.parametrize("constant", [False, True], ids=["unequal-coverage", "undefined-kappa"])
def test_grouped_intake_preserves_verdict_and_whole_group_sensitivity(config, tmp_path, path, constant):
    """Decision 201 changes agreement inference, not certification or primary labels."""
    fast = dataclasses.replace(
        config, validation=dataclasses.replace(config.validation, bootstrap_samples=200),
    )
    items = load_scored_items(_grouped_file(tmp_path, constant=constant))
    base_items = dataclasses.replace(items, second_labels=None)
    if path == "certify":
        result = certify_items(fast, items, budget=0.05)
        base = certify_items(fast, base_items, budget=0.05)
        rendered = render_summary(result)
    else:
        result = recheck_items(fast, items, budget=0.05, threshold=0.5)
        base = recheck_items(fast, base_items, budget=0.05, threshold=0.5)
        rendered = render_recheck(result)
    result_payload, base_payload = result.to_payload(), base.to_payload()
    result_payload.pop("labels")
    base_payload.pop("labels")
    assert result_payload == base_payload
    assert result.label_sensitivity == base.label_sensitivity
    assert result.label_sensitivity.computed
    assert result.label_sensitivity.unit == "groups"
    review = result.second_review.to_payload()
    assert review["n_pairs"] == (5 if constant else 11)
    assert review["kappa"]["n_groups"] == (2 if constant else 4)
    assert sum(review["table"].values()) == review["n_pairs"]
    assert review["kappa"]["ci_low"] is None and review["kappa"]["ci_high"] is None
    assert review["kappa"]["interval_computed"] is False
    assert review["kappa"]["kind"] == "EXACT"
    assert "not a population estimate" in review["kappa"]["scope"]
    assert (review["kappa"]["value"] is None) == constant
    assert review["disputes"]["computed"] is False
    assert "whole-group relabelling" in review["disputes"]["reason"]
    assert "population interval withheld" in rendered
    assert f"{2 if constant else 4} reviewed groups" in rendered
    rendered.encode("ascii")


def test_grouped_certify_and_recheck_cli_explain_withheld_intervals(tmp_path, capsys):
    source = _grouped_file(tmp_path)
    warrant, recheck = tmp_path / "warrant.json", tmp_path / "recheck.json"
    assert main(["certify", "-i", str(source), "-b", ".05", "-o", str(warrant)]) == 0
    assert "population interval withheld" in capsys.readouterr().out
    assert main(["recheck", "-w", str(warrant), "-i", str(source), "-o", str(recheck)]) == 0
    assert "population interval withheld" in capsys.readouterr().out
    for record in (warrant, recheck):
        review = json.loads(record.read_text(encoding="utf-8"))["labels"]["second_review"]
        assert review["kappa"]["ci_low"] is None and review["kappa"]["ci_high"] is None
        assert review["kappa"]["interval_computed"] is False
        assert review["kappa"]["n_groups"] == 4
        assert review["n_pairs"] == 11
