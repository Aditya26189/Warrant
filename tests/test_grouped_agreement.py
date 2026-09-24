"""Dependent review pairs cannot manufacture a population interval (decision 201)."""

from __future__ import annotations

import numpy as np
import pytest

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
