"""A recall plan's sample realises its margin with a declared probability (DECISIONS.md 191).

Before 191 the exact basis sized at the *expected* error count, and the
published 1,014-label figure realised its +/-0.05 margin with probability
0.4882. These tests pin the three criteria 191 registered, and the structural
assumption the fast computation rests on, against brute force and against the
estimator itself rather than against the planner's own arithmetic.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.stats import binom

from controlplane.sampling import Band, estimate_on_traffic
from controlplane.sampling.planning import (
    _SMALL_COUNTS,
    SizingError,
    _assurance,
    _recall_half_width,
    labels_for_recall,
    recall_sensitivity,
)

ASSURANCE = 0.80
SEED = 1729


def _declared(config):
    w = config.workload
    flag_rate = w.base_error_rate * w.measured_tpr + (1 - w.base_error_rate) * w.measured_fpr
    return recall_sensitivity(
        recall=w.measured_tpr, flag_rate=flag_rate,
        monthly_interactions=w.monthly_interactions, base_error_rate=w.base_error_rate,
    )


def _common(s, margin):
    return dict(
        prevalence=s.unflagged_prevalence, true_positives=s.confirmed_errors,
        pool=s.unflagged_pool, margin=margin, design_effect=1.0,
        finite_population=False, confidence=0.95,
    )


def _brute(s, n, margin):
    ks = np.arange(0, n + 1)
    widths = _recall_half_width(ks, np.full(ks.shape, n), true_positives=s.confirmed_errors,
                                pool=s.unflagged_pool, confidence=0.95)
    return float(binom.pmf(ks, n, s.unflagged_prevalence)[widths <= margin].sum())


@pytest.mark.parametrize("recall,margin", [(0.2171, 0.05), (0.2171, 0.02), (0.6, 0.05), (0.1, 0.1)])
def test_the_fast_assurance_equals_brute_force_enumeration(config, recall, margin) -> None:
    w = config.workload
    s = recall_sensitivity(recall=recall, flag_rate=0.05, monthly_interactions=w.monthly_interactions,
                           base_error_rate=w.base_error_rate)
    for n in (5, 40, 300, 1014, 1399, 3000, 7000):
        fast = float(_assurance([n], **_common(s, margin))[0])
        assert fast == pytest.approx(_brute(s, n, margin), abs=1e-12), (recall, margin, n)


def test_past_the_small_counts_the_half_width_only_falls(config) -> None:
    """The assumption the bisection makes, checked where the binomial has mass."""
    s = _declared(config)
    for n in (300, 1014, 5566, 23531):
        mean = n * s.unflagged_prevalence
        spread = math.sqrt(mean * (1 - s.unflagged_prevalence))
        ks = np.arange(max(_SMALL_COUNTS + 1, int(mean - 12 * spread)), int(mean + 12 * spread) + 1)
        widths = _recall_half_width(ks, np.full(ks.shape, n), true_positives=s.confirmed_errors,
                                    pool=s.unflagged_pool, confidence=0.95)
        assert np.all(np.diff(widths) <= 1e-15), f"half-width rises with the count at n={n}"


def test_c2_the_published_figure_realised_its_margin_about_half_the_time(config) -> None:
    """191's C2: the 1,014-label headline's assurance lies in [0.35, 0.65]."""
    s = _declared(config)
    plan = labels_for_recall(sensitivity=s, margin=0.05, assurance=ASSURANCE)
    assert plan.labels_at_expected_count == 1014
    assert 0.35 <= plan.assurance_at_expected_count <= 0.65
    assert plan.assurance_at_expected_count == pytest.approx(0.4882, abs=5e-5)


def test_c3_the_assured_size_is_larger_and_at_most_double(config) -> None:
    s = _declared(config)
    plan = labels_for_recall(sensitivity=s, margin=0.05, assurance=ASSURANCE)
    assert 1014 < plan.labels <= 2 * 1014
    assert plan.labels == 1399
    assert plan.assurance_at_labels >= ASSURANCE


def test_c1_the_estimator_realises_the_margin_as_often_as_computed(config) -> None:
    """191's C1: 2,000 seeded samples at the assured size through the real estimator."""
    s = _declared(config)
    plan = labels_for_recall(sensitivity=s, margin=0.05, assurance=ASSURANCE)
    flagged, confirmed = int(round(s.flagged_pool)), int(round(s.confirmed_errors))
    pool = int(round(s.unflagged_pool))
    rng = np.random.default_rng(SEED)
    trials = 2000
    met = sum(
        estimate_on_traffic(
            flagged_reviewed=flagged, flagged_confirmed=confirmed,
            bands=[Band("all", population=pool, sampled=plan.labels, errors=int(errors))],
            planned_margin=0.05,
        ).margin_met
        for errors in rng.binomial(plan.labels, s.unflagged_prevalence, trials)
    )
    computed = plan.assurance_at_labels
    se = math.sqrt(computed * (1 - computed) / trials)
    assert abs(met / trials - computed) <= 3 * se, (met / trials, computed)


def test_the_assured_size_is_stable_from_where_it_is_quoted(config) -> None:
    s = _declared(config)
    plan = labels_for_recall(sensitivity=s, margin=0.05, assurance=ASSURANCE)
    ns = np.arange(plan.labels, plan.labels * 12 + 1)
    assert (_assurance(ns, **_common(s, 0.05)) >= ASSURANCE).all()
    assert _assurance([plan.labels - 1], **_common(s, 0.05))[0] < ASSURANCE or any(
        _assurance(np.arange(1, plan.labels - 1), **_common(s, 0.05)) < ASSURANCE
    )


def test_the_ladder_prints_what_each_assurance_costs(config) -> None:
    s = _declared(config)
    plan = labels_for_recall(sensitivity=s, margin=0.05, assurance=ASSURANCE)
    ladder = dict(plan.sizes_by_assurance)
    assert ladder[0.5] < ladder[0.8] < ladder[0.9]
    assert ladder[0.8] == plan.labels
    assert "realises the margin with probability" in plan.render()


def test_assurance_is_required_and_must_be_a_probability(config) -> None:
    s = _declared(config)
    with pytest.raises(TypeError):
        labels_for_recall(sensitivity=s, margin=0.05)  # type: ignore[call-arg]
    for bad in (0.0, 1.0, 1.2):
        with pytest.raises(SizingError, match="assurance"):
            labels_for_recall(sensitivity=s, margin=0.05, assurance=bad)


def test_config_refuses_an_assurance_below_one_half(project_root, tmp_path) -> None:
    import yaml

    from controlplane.config import ConfigError, load_config

    raw = yaml.safe_load((project_root / "config.yaml").read_text(encoding="utf-8"))
    assert raw["sampling"]["margin_assurance"] == ASSURANCE
    raw["sampling"]["margin_assurance"] = 0.4
    target = tmp_path / "config.yaml"
    target.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ConfigError, match="margin_assurance"):
        load_config(target)
