"""Decision 220: a repeated hard-negative scenario is one independent unit."""

from __future__ import annotations

import dataclasses
from datetime import timedelta

import numpy as np
import pytest

from controlplane.config import Config
from controlplane.matrix.routing import Profile
from controlplane.model import AccessTier, WarrantKey, WarrantStatus
from controlplane.policy.bundle import (
    CalibrationRequirement,
    OnCalibrationDrift,
    WarrantRequirement,
)
from controlplane.policy.resolution import _check_bounds
from controlplane.validation.issuance import issue_or_refuse
from controlplane.validation.metrics_builder import build_warrant_metrics
from controlplane.validation.scores import ScoreSet, ScoreTarget, metrics_for_target
from controlplane.validation.warrant_stats import cp_upper

from .factories import (
    PASSING_CONTROLS,
    make_envelope,
    make_metrics,
    make_operating_point,
    make_warrant,
)


def _fast(config: Config) -> Config:
    return dataclasses.replace(
        config,
        validation=dataclasses.replace(config.validation, bootstrap_samples=100),
    )


def test_zero_false_positives_do_not_gain_evidence_from_row_copies(
    config: Config,
) -> None:
    """Four negative scenarios remain four trials after uniform duplication."""
    observed = []
    for copies in (1, 100):
        labels = np.zeros(4 * copies, dtype=int)
        scores = np.zeros(4 * copies)
        groups = np.repeat(np.arange(4), copies)
        metric = build_warrant_metrics(
            _fast(config), labels, scores, 0.5, groups=groups,
            is_hard_negative_set=True,
        ).fpr_hard_negatives
        assert metric is not None
        observed.append(metric)

    assert observed[0].ci_high == observed[1].ci_high
    assert observed[0].ci_high == pytest.approx(cp_upper(0, 4, 0.05))
    assert all("4 independent negative groups" in metric.estimator for metric in observed)


def test_group_any_bound_counts_one_event_for_one_firing_framing(
    config: Config,
) -> None:
    """A single flagged framing counts its scenario, without multiplying it."""
    labels = np.zeros(16, dtype=int)
    scores = np.zeros(16)
    scores[0] = 0.9
    groups = np.repeat(np.arange(4), 4)
    metric = build_warrant_metrics(
        _fast(config), labels, scores, 0.5, groups=groups,
        is_hard_negative_set=True,
    ).fpr_hard_negatives
    assert metric is not None
    assert metric.value == 1 / 16
    assert metric.ci_high == pytest.approx(cp_upper(1, 4, 0.05))
    assert "group_any_cp_v1" in metric.estimator


def test_unequal_negative_group_sizes_withhold_item_rate_claim(
    config: Config,
) -> None:
    """Group event rate need not dominate the item rate with unequal sizes."""
    labels = np.zeros(5, dtype=int)
    scores = np.zeros(5)
    groups = np.array([0, 0, 1, 2, 3])
    metric = build_warrant_metrics(
        _fast(config), labels, scores, 0.5, groups=groups,
        is_hard_negative_set=True,
    ).fpr_hard_negatives
    assert metric is not None
    assert metric.ci_high == 1.0
    assert "unequal negative group sizes" in metric.estimator


def test_corrected_bound_refuses_warrant_that_row_count_would_issue(
    config: Config,
) -> None:
    """Two firing scenarios in 50 cross the 0.10 issuance ceiling (220)."""
    labels = np.zeros(200, dtype=int)
    scores = np.zeros(200)
    scores[:8] = 0.9
    groups = np.repeat(np.arange(50), 4)
    kwargs = dict(
        key=WarrantKey("detector", "P-declared", "hard-negatives"),
        detector_version="1.0.0+test",
        operating_point=make_operating_point("P-declared", "detector"),
        envelope=make_envelope("hard-negatives"),
        controls=PASSING_CONTROLS,
        access_tier=AccessTier.T3_TEXT,
        n_test=200,
        base_rate=0.0,
        validation_run_id="run-grouped-hard-negative",
        max_fpr_hard_negatives=0.10,
    )
    modern = build_warrant_metrics(
        _fast(config), labels, scores, 0.5, groups=groups,
        is_hard_negative_set=True,
    )
    legacy = build_warrant_metrics(
        _fast(config), labels, scores, 0.5, groups=groups,
        is_hard_negative_set=True, legacy_grouped_hard_negative=True,
    )
    assert modern.fpr_hard_negatives is not None
    assert legacy.fpr_hard_negatives is not None
    assert modern.fpr_hard_negatives.ci_high > 0.10
    assert legacy.fpr_hard_negatives.ci_high < 0.10
    assert issue_or_refuse(config, metrics=modern, **kwargs).status is WarrantStatus.REFUSED
    refused_legacy = issue_or_refuse(config, metrics=legacy, **kwargs)
    assert refused_legacy.status is WarrantStatus.REFUSED
    assert "fpr_hard_negatives_protocol" in refused_legacy.status_reason


def test_frozen_score_replay_requires_explicit_legacy_method(config: Config) -> None:
    """Historical arithmetic remains reproducible without becoming the default."""
    score_set = ScoreSet(
        score_set_id="synthetic", detector_id="detector", variant="text",
        eval_set_id="hard-negatives", envelope_id="sha256:synthetic",
        labels=(0,) * 16, scores=(0.9,) + (0.0,) * 15,
        question_ids=tuple(f"scenario-{i // 4}" for i in range(16)),
        targets=(ScoreTarget("old.json", "metrics", 0.5),),
        is_hard_negative_set=True,
    )
    target = score_set.targets[0]
    modern = metrics_for_target(_fast(config), score_set, target)
    legacy = metrics_for_target(
        _fast(config), score_set, target, legacy_grouped_hard_negative=True,
    )
    assert modern.fpr_hard_negatives is not None
    assert legacy.fpr_hard_negatives is not None
    assert modern.fpr_hard_negatives.ci_high == pytest.approx(cp_upper(1, 4, 0.05))
    assert legacy.fpr_hard_negatives.ci_high == pytest.approx(cp_upper(1, 16, 0.05))


def test_routing_does_not_trust_an_unversioned_hard_negative_bound(
    config: Config,
) -> None:
    """A retained row-count interval may replay but cannot clear routing."""
    labels = np.zeros(16, dtype=int)
    scores = np.zeros(16)
    scores[0] = 0.9
    groups = np.repeat(np.arange(4), 4)
    modern = build_warrant_metrics(
        _fast(config), labels, scores, 0.5, groups=groups,
        is_hard_negative_set=True,
    )
    legacy = build_warrant_metrics(
        _fast(config), labels, scores, 0.5, groups=groups,
        is_hard_negative_set=True, legacy_grouped_hard_negative=True,
    )
    profile = Profile("synthetic", min_recall=0.0,
                      max_fpr_hard_negatives=0.9, inline_budget_ms=1000)
    accepted, _ = profile.accepts(dataclasses.replace(
        make_metrics(), fpr_hard_negatives=modern.fpr_hard_negatives,
    ))
    assert accepted
    accepted, reason = profile.accepts(dataclasses.replace(
        make_metrics(), fpr_hard_negatives=legacy.fpr_hard_negatives,
    ))
    assert not accepted
    assert "legacy or undeclared" in reason


def test_policy_load_does_not_accept_legacy_hard_negative_interval(
    config: Config,
) -> None:
    """A persisted VALID status does not make its old interval usable (220)."""
    labels = np.zeros(16, dtype=int)
    scores = np.zeros(16)
    groups = np.repeat(np.arange(4), 4)
    legacy = build_warrant_metrics(
        _fast(config), labels, scores, 0.5, groups=groups,
        is_hard_negative_set=True, legacy_grouped_hard_negative=True,
    )
    warrant = make_warrant()
    warrant = dataclasses.replace(
        warrant,
        metrics=dataclasses.replace(
            warrant.metrics, fpr_hard_negatives=legacy.fpr_hard_negatives,
        ),
    )
    requirement = WarrantRequirement(
        detector=warrant.detector_id,
        operating_point=warrant.operating_point.operating_point_id,
        envelope=warrant.eval_set_id,
        min_recall=0.0,
        max_fpr_hard_negatives=0.9,
        max_age=timedelta(days=1),
        calibration=CalibrationRequirement(OnCalibrationDrift.IGNORE, 0.25),
    )
    failures = _check_bounds(warrant, requirement)
    assert any("legacy or undeclared independent-unit method" in f for f in failures)
