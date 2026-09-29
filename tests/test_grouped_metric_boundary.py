"""R2: repeated rows inside a group cannot create independent rate evidence."""

from __future__ import annotations

import dataclasses
from copy import deepcopy

import numpy as np

from controlplane.config import Config, load_customer_config
from controlplane.intake import certify_items
from controlplane.intake.contract import ScoredItems
from controlplane.intake.verify import verify_certification
from controlplane.model import to_jsonable
from controlplane.validation.metrics_builder import build_warrant_metrics
from controlplane.validation.stats import (
    estimated, false_positive_rate_at, precision_at, recall_at,
)


def test_perfect_grouped_rates_do_not_gain_certainty_from_row_duplication(
    config: Config,
) -> None:
    """The R2 four-positive-group example must never fall back to row trials."""
    fast = dataclasses.replace(
        config,
        validation=dataclasses.replace(config.validation, bootstrap_samples=1000),
    )
    observed = []
    for repeats in (1, 100):
        labels = np.repeat(np.array([0] * 60 + [1] * 4), repeats)
        scores = np.where(labels == 1, 0.9, 0.1)
        groups = np.repeat(np.arange(64), repeats).astype(object)
        metrics = build_warrant_metrics(
            fast, labels, scores, 0.5, groups=groups,
            grouped_boundary_abstention=True,
        )
        assert metrics.recall is not None and metrics.precision is not None
        observed.append((metrics.recall, metrics.precision))

    for metric_name in (0, 1):
        first, duplicated = observed[0][metric_name], observed[1][metric_name]
        assert (first.ci_low, first.ci_high) == (0.0, 1.0)
        assert (duplicated.ci_low, duplicated.ci_high) == (0.0, 1.0)
        assert "collapsed grouped bootstrap" in first.estimator
        assert "64 groups" in first.estimator


def test_interior_collapse_with_mixed_unequal_groups_is_vacuous(config: Config) -> None:
    """An identical within-group ratio is not 95% certain at any row count."""
    fast = dataclasses.replace(
        config,
        validation=dataclasses.replace(config.validation, bootstrap_samples=100),
    )
    observed = []
    for repeat_all in (1, 5):
        labels: list[int] = []
        scores: list[float] = []
        groups: list[int] = []
        for group_id in range(12):
            within_group = 1 if group_id % 2 == 0 else 2
            for label, score in ((1, 0.9), (1, 0.1), (0, 0.9), (0, 0.1)):
                labels.extend([label] * within_group * repeat_all)
                scores.extend([score] * within_group * repeat_all)
                groups.extend([group_id] * within_group * repeat_all)
        metrics = build_warrant_metrics(
            fast, np.array(labels), np.array(scores), 0.5,
            groups=np.array(groups, dtype=object),
            grouped_boundary_abstention=True,
        )
        assert metrics.recall is not None and metrics.precision is not None
        observed.append((metrics.recall, metrics.precision))

    for pair in observed:
        for metric in pair:
            assert metric.value == 0.5
            assert (metric.ci_low, metric.ci_high) == (0.0, 1.0)
            assert "12 groups" in metric.estimator


def test_zero_successes_on_grouped_rates_remain_vacuous(config: Config) -> None:
    """All observed failures cannot establish population recall or precision."""
    fast = dataclasses.replace(
        config,
        validation=dataclasses.replace(config.validation, bootstrap_samples=100),
    )
    labels = np.tile(np.array([1, 0]), 16)
    scores = np.tile(np.array([0.1, 0.9]), 16)
    groups = np.repeat(np.arange(16), 2).astype(object)
    metrics = build_warrant_metrics(
        fast, labels, scores, 0.5, groups=groups,
        grouped_boundary_abstention=True,
    )
    assert metrics.recall is not None and metrics.precision is not None
    for metric in (metrics.recall, metrics.precision):
        assert metric.value == 0.0
        assert (metric.ci_low, metric.ci_high) == (0.0, 1.0)


def test_copied_negative_rows_cannot_narrow_grouped_flag_and_fpr_bounds(
    config: Config,
) -> None:
    """Four independent negative scenarios stay four trials after duplication."""
    fast = dataclasses.replace(
        config,
        validation=dataclasses.replace(config.validation, bootstrap_samples=100),
    )
    for repeats in (1, 100):
        labels = np.zeros(4 * repeats, dtype=int)
        scores = np.full(4 * repeats, 0.1)
        groups = np.repeat(np.arange(4), repeats).astype(object)
        metrics = build_warrant_metrics(
            fast, labels, scores, 0.5, groups=groups,
            grouped_rate_boundary_abstention=True,
        )
        assert metrics.flag_rate.value == 0.0
        assert (metrics.flag_rate.ci_low, metrics.flag_rate.ci_high) == (0.0, 1.0)
        assert "4 groups" in metrics.flag_rate.estimator
        assert len(metrics.extra) == 1
        assert (metrics.extra[0].ci_low, metrics.extra[0].ci_high) == (0.0, 1.0)


def test_grouped_flag_rate_keeps_noncollapsed_cluster_percentile(config: Config) -> None:
    """The method changes only a collapsed resample, not an interior interval."""
    fast = dataclasses.replace(
        config,
        validation=dataclasses.replace(config.validation, bootstrap_samples=100),
    )
    labels = np.tile(np.array([0, 1]), 40)
    scores = np.repeat(np.tile(np.array([0.1, 0.9]), 20), 2)
    groups = np.repeat(np.arange(40), 2).astype(object)
    metrics = build_warrant_metrics(
        fast, labels, scores, 0.5, groups=groups,
        grouped_rate_boundary_abstention=True,
    )
    original = estimated(
        "flag_rate", lambda y, s: float(np.mean(s >= 0.5)), labels, scores,
        n_resamples=100, ci=fast.validation.ci, seed=fast.seed, groups=groups,
    )
    assert metrics.flag_rate == original
    assert len(metrics.extra) == 1
    original_fpr = estimated(
        "fpr", lambda y, s: false_positive_rate_at(y, s, 0.5),
        labels, scores, n_resamples=100, ci=fast.validation.ci,
        seed=fast.seed, groups=groups,
    )
    assert metrics.extra[0] == original_fpr


def test_noncollapsed_grouped_intervals_match_existing_percentile_method(
    config: Config,
) -> None:
    """Decision 217 changes only the unsupported collapsed case."""
    fast = dataclasses.replace(
        config,
        validation=dataclasses.replace(config.validation, bootstrap_samples=100),
    )
    rng = np.random.default_rng(214)
    labels = np.tile(np.array([0, 1]), 40)
    scores = rng.random(labels.size)
    groups = np.repeat(np.arange(40), 2).astype(object)
    metrics = build_warrant_metrics(
        fast, labels, scores, 0.5, groups=groups,
        grouped_boundary_abstention=True,
    )
    assert metrics.recall is not None and metrics.precision is not None
    for name, statistic, actual in (
        ("recall", lambda y, s: recall_at(y, s, 0.5), metrics.recall),
        ("precision", lambda y, s: precision_at(y, s, 0.5), metrics.precision),
    ):
        original = estimated(
            name, statistic, labels, scores,
            n_resamples=100, ci=fast.validation.ci, seed=fast.seed,
            groups=groups,
        )
        assert actual == original


def test_ungrouped_boundary_keeps_exact_binomial_interval(config: Config) -> None:
    """The independent-item boundary method is unaffected."""
    fast = dataclasses.replace(
        config,
        validation=dataclasses.replace(config.validation, bootstrap_samples=100),
    )
    labels = np.array([0] * 60 + [1] * 20)
    scores = np.where(labels == 1, 0.9, 0.1)
    metrics = build_warrant_metrics(fast, labels, scores, 0.5)
    assert metrics.recall is not None and metrics.precision is not None
    for metric in (metrics.recall, metrics.precision):
        assert "Clopper-Pearson exact" in metric.estimator
        assert metric.ci_low > 0.0
    assert "Clopper-Pearson exact" in metrics.extra[0].estimator
    original_flag_rate = estimated(
        "flag_rate", lambda y, s: float(np.mean(s >= 0.5)),
        labels, scores, n_resamples=100, ci=fast.validation.ci,
        seed=fast.seed, binomial_events=20, binomial_trials=80,
    )
    assert metrics.flag_rate == original_flag_rate


def _grouped_items() -> ScoredItems:
    """Four positive and sixty negative independent units for certificate tests."""
    labels = tuple([0] * 60 + [1] * 4)
    return ScoredItems(
        ids=tuple(f"item-{index}" for index in range(64)),
        labels=labels,
        scores=tuple(0.1 if label == 0 else 0.9 for label in labels),
        groups=tuple(f"group-{index}" for index in range(64)),
        passthrough_columns=(),
        source="synthetic-grouped-boundary",
    )


def test_customer_certificate_discloses_grouped_boundary_abstention() -> None:
    """The customer record must expose the vacuous metric, not merely the helper."""
    record = certify_items(load_customer_config(), _grouped_items(), budget=0.05).to_payload()
    assert record["status"] == "VALID"
    assert record["input"]["independent_negative_units"] == 60
    for name in ("recall", "precision"):
        metric = record["metrics"][name]
        assert (metric["ci_low"], metric["ci_high"]) == (0.0, 1.0)
        assert "collapsed grouped bootstrap" in metric["estimator"]


def test_new_and_retained_grouped_certificates_replay_under_their_methods() -> None:
    """A method upgrade cannot make a bound old record look tampered with."""
    config = load_customer_config()
    items = _grouped_items()
    current = certify_items(config, items, budget=0.05).to_payload()
    current["provenance"] = {"config_hash": config.config_hash}
    assert current["metrics_protocol"] == "grouped_boundary_vacuous_v2"
    assert verify_certification(current, items, config).status == "VERIFIED"

    retained_v1 = certify_items(
        config, items, budget=0.05,
        grouped_boundary_abstention=True,
        grouped_rate_boundary_abstention=False,
    ).to_payload()
    retained_v1["metrics_protocol"] = "grouped_boundary_vacuous_v1"
    retained_v1["provenance"] = {"config_hash": config.config_hash}
    assert verify_certification(retained_v1, items, config).status == "VERIFIED"

    legacy = deepcopy(current)
    del legacy["metrics_protocol"]
    labels, scores, groups = items.as_arrays()
    old_metrics = build_warrant_metrics(
        config, labels, scores, current["certification"]["threshold"],
        groups=groups, grouped_rate_boundary_abstention=False,
    )
    for name in ("recall", "precision", "flag_rate", "lift"):
        legacy["metrics"][name] = to_jsonable(getattr(old_metrics, name))
    legacy["metrics"]["lift_ceiling"] = old_metrics.lift_ceiling
    old_result = verify_certification(legacy, items, config)
    assert old_result.status == "VERIFIED"
    assert "historical" in old_result.reason

    downgraded = deepcopy(current)
    del downgraded["metrics_protocol"]
    assert verify_certification(downgraded, items, config).status == "MISMATCH"
    unknown = deepcopy(current)
    unknown["metrics_protocol"] = "unknown"
    assert verify_certification(unknown, items, config).status == "MISMATCH"


def test_v1_certificate_replays_old_collapsed_flag_rate() -> None:
    """v2 must not retroactively upgrade a retained v1 interval."""
    config = load_customer_config()
    original = _grouped_items()
    items = dataclasses.replace(original, scores=tuple(0.1 for _ in original.scores))
    v2 = certify_items(config, items, budget=0.05).to_payload()
    v1 = certify_items(
        config, items, budget=0.05, grouped_rate_boundary_abstention=False,
    ).to_payload()
    for record in (v1, v2):
        record["provenance"] = {"config_hash": config.config_hash}
        assert record["status"] == "VALID"
        assert verify_certification(record, items, config).status == "VERIFIED"
    assert v1["metrics_protocol"] == "grouped_boundary_vacuous_v1"
    assert v2["metrics_protocol"] == "grouped_boundary_vacuous_v2"
    assert v1["metrics"]["flag_rate"]["ci_high"] < 1.0
    assert v2["metrics"]["flag_rate"]["ci_high"] == 1.0
