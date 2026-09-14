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
    SizingError,
    _assurance,
    _certified,
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


def _shipped(config):
    """The declared workload and every profile's measured point, as the price list reads them.

    Loaded through ``scripts/25_on_traffic.py``'s own reader, so a test of the
    sizing sees exactly the operating points the published price list is built
    on. The first implementation was checked only at the declared workload and
    was wrong at ``decision_support`` (DECISIONS.md 191).
    """
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("on_traffic_script", root / "scripts" / "25_on_traffic.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    points = module._measured_points(root / "results", None)
    w = config.workload
    subjects = {"declared workload point": _declared(config)}
    for name, profile in sorted(config.profiles.items()):
        point = points.get(profile.operating_point)
        if point is None:
            continue
        subjects[name] = recall_sensitivity(
            recall=point["recall"], flag_rate=point["flag_rate"],
            monthly_interactions=w.monthly_interactions, base_error_rate=w.base_error_rate,
        )
    assert len(subjects) >= 4, "the shipped operating points did not load"
    return subjects


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


def test_the_half_width_has_one_peak_at_every_shipped_operating_point(config) -> None:
    """The shape the two-tail computation rests on, over every count, not a window.

    One sign change in the slope: rising while q N_u is small against TP, falling
    after. The first implementation assumed only the falling side, which is true
    at the declared workload and false at decision_support.
    """
    for name, s in _shipped(config).items():
        for n in (50, 1000, 4066, 21108, 60000):
            ks = np.arange(0, n + 1)
            widths = _recall_half_width(ks, np.full(ks.shape, n), true_positives=s.confirmed_errors,
                                        pool=s.unflagged_pool, confidence=0.95)
            slope = np.sign(np.diff(widths)[np.abs(np.diff(widths)) > 1e-13])
            assert np.sum(slope[1:] != slope[:-1]) <= 1, f"{name}: more than one peak at n={n}"


@pytest.mark.parametrize("margin", [0.05, 0.02])
def test_assurance_equals_brute_force_at_every_shipped_operating_point(config, margin) -> None:
    for name, s in _shipped(config).items():
        ns = [3, 60, 400, 1014, 2283, 4049, 4066, 11803, 21108]
        fast = _assurance(ns, **_common(s, margin))
        for n, value in zip(ns, fast, strict=True):
            assert value == pytest.approx(_brute(s, n, margin), abs=1e-12), (name, margin, n)


def test_the_case_the_first_implementation_got_wrong(config) -> None:
    """decision_support, +/-0.02, 21,108 labels: brute force 0.0000; it returned 1.0.

    The half-width at the expected count is 0.0216, above the margin, and every
    count near it is on the rising side of the peak, so almost no sample of that
    size realises +/-0.02. The published regeneration at 11d7d90 carried 21,108
    as that plan's size; it was wrong.
    """
    s = _shipped(config)["decision_support"]
    assert float(_assurance([21108], **_common(s, 0.02))[0]) < 1e-6
    assert _brute(s, 21108, 0.02) < 1e-6


def test_a_certified_size_is_never_below_its_target(config) -> None:
    """The cheap certificate may decline to certify; it must never certify wrongly."""
    ns = np.unique(np.geomspace(10, 60000, 300).astype(int))
    for name, s in _shipped(config).items():
        for margin in (0.05, 0.02):
            exact = _assurance(ns, **_common(s, margin))
            for target in (0.5, 0.8, 0.9):
                certified = _certified(ns, target, **_common(s, margin))
                assert not np.any(certified & (exact < target)), (name, margin, target)


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
