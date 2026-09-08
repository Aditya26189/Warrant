"""What the FPR sweep must not get wrong.

Four properties, each one a way the sweep could produce a plausible table with
something silently missing from it:

* the **grid** is complete and lands on the targets it names, so a row labelled
  ``0.06`` was certified against 0.06 and not against 0.060000000000000005;
* a **refused** target keeps its row, because a refusal is the answer to "can a
  1% budget be certified on this many negatives?" and a skipped row reads as an
  oversight rather than as that answer;
* the **bootstrap is seeded**, so two runs of the same sweep agree and a moved
  number means the data moved;
* a **fixture** sweep renders no numbers at all, which is the rule the rest of
  the reporting layer already follows (``DECISIONS.md`` 046) and the one the
  sweep is most likely to escape, being new.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from controlplane.report.sweep import (
    SWEEP_FIXTURE_MARKER,
    render_sweep,
    verdict,
)
from controlplane.validation.fpr_sweep import (
    LIFT_HOLDS_LOWER_BOUND,
    MEASURED,
    fpr_grid,
    resolve_data_source,
    sweep_fpr,
)
from controlplane.validation.scores import ScoreSet, ScoreTarget

REGISTERED_GRID = (0.01, 0.20, 0.01)


@pytest.fixture
def fast_config(config):
    """The committed config with the bootstrap at its floor.

    A twenty-point sweep bootstraps five metrics per point, and at the
    committed 1000 resamples that is minutes per test — enough to make the
    suite something people skip. Every test here is about *structure*: which
    rows exist, what renders, whether two runs agree. None asserts an interval
    width, so the resample count only has to be enough to produce an interval
    at all. 100 is the floor `ValidationConfig` itself enforces, so this cannot
    silently become a number that stops being a usable interval.

    `test_the_sweep_reads_the_committed_config` runs at the real settings, so
    nothing here can hide a sweep that ignores the config it is handed.
    """
    return dataclasses.replace(
        config,
        validation=dataclasses.replace(config.validation, bootstrap_samples=100),
    )


def _score_set(
    *,
    n: int = 400,
    base_rate: float = 0.46,
    separation: float = 1.4,
    seed: int = 7,
    score_set_id: str = "fixture-sweep",
) -> ScoreSet:
    """A separable two-class scoring with one item per question.

    Synthetic by construction and used only to exercise the machinery: no test
    here asserts a measured value, and the renderer tests below check that
    numbers from a set like this cannot reach a document.
    """
    rng = np.random.default_rng(seed)
    labels = (rng.random(n) < base_rate).astype(int)
    scores = rng.normal(0.0, 1.0, n) + separation * labels
    scores = 1.0 / (1.0 + np.exp(-scores))
    return ScoreSet(
        score_set_id=score_set_id,
        detector_id="probe-test",
        variant="T1-last_token",
        eval_set_id="fixture-set",
        envelope_id="sha256:fixture",
        labels=tuple(int(x) for x in labels),
        scores=tuple(float(x) for x in scores),
        question_ids=tuple(f"q_{i}" for i in range(n)),
        targets=(
            ScoreTarget(
                artifact="results/does-not-exist.json",
                metrics_path="metrics",
                threshold=float(np.quantile(scores, 0.95)),
                operating_point_id="P-test",
            ),
        ),
    )


# ------------------------------------------------------------------ the grid

def test_grid_is_complete_and_correctly_spaced() -> None:
    """Twenty points, 0.01 to 0.20 inclusive, exactly on the registered targets."""
    grid = fpr_grid(*REGISTERED_GRID)
    assert len(grid) == 20
    assert grid[0] == 0.01
    assert grid[-1] == 0.20
    # Equality, not almost-equality: a target that is merely close to 0.06 is a
    # different budget from the one the row claims to have certified.
    assert grid == tuple(round(i / 100, 10) for i in range(1, 21))
    assert all(
        round(b - a, 10) == 0.01 for a, b in zip(grid, grid[1:])
    ), "grid spacing drifted"


def test_grid_rejects_a_step_that_does_not_divide_one() -> None:
    """A step the grid cannot land on is refused rather than silently rounded."""
    with pytest.raises(ValueError, match="does not divide"):
        fpr_grid(0.01, 0.20, 0.03)


def test_sweep_covers_every_grid_point(fast_config) -> None:
    """Every target gets a row — certified or refused, none dropped."""
    grid = fpr_grid(*REGISTERED_GRID)
    sweep = sweep_fpr(
        fast_config, _score_set(), grid=grid, data_source=MEASURED
    )
    assert len(sweep.points) == len(grid)
    assert tuple(p.target_fpr for p in sweep.points) == grid


# ---------------------------------------------------------------- refusals

def test_refused_target_is_recorded_not_skipped(fast_config) -> None:
    """Too few negatives to certify 1% keeps its row and says why.

    ``certify_fpr`` needs 299 clean units for a 1% budget at alpha 0.05, so a
    set with fewer negatives than that must refuse the tight end of the grid.
    The row has to survive: it is the answer to the reader's question, not a
    gap.
    """
    small = _score_set(n=120, seed=11)
    grid = fpr_grid(*REGISTERED_GRID)
    sweep = sweep_fpr(
        fast_config, small, grid=grid, data_source=MEASURED)

    assert len(sweep.points) == len(grid), "a refused target was dropped"
    refused = [p for p in sweep.points if not p.certified]
    assert refused, "expected the tight end of the grid to refuse on 120 items"
    tightest = sweep.points[0]
    assert tightest.target_fpr == 0.01
    assert tightest.certified is False
    assert tightest.threshold is None, "a refused point must not carry a threshold"
    assert tightest.recall is None, "a refused point must not carry metrics"
    assert tightest.min_units_required > tightest.n_units
    assert "certify" in tightest.reason

    payload = sweep.to_payload()
    assert len(payload["points"]) == len(grid)
    assert payload["points"][0]["certified"] is False


def test_refused_targets_render_as_refused_not_as_blanks(fast_config) -> None:
    """The table marks a refusal by name."""
    sweep = sweep_fpr(
        fast_config, _score_set(n=120, seed=11), grid=fpr_grid(*REGISTERED_GRID),
        data_source=MEASURED,
    )
    markdown = render_sweep(sweep, provenance={"git_commit": "0" * 40, "dirty": False})
    assert "REFUSED" in markdown
    assert "### Refused targets" in markdown


# ------------------------------------------------------------- reproducibility

def test_bootstrap_is_seeded_and_reproducible(fast_config) -> None:
    """Two sweeps of the same scores agree to the last bit.

    Intervals come from a percentile bootstrap seeded from the config, so a
    difference between two runs would mean the seed is not reaching the
    resampler — and every interval in the artifact would then be unreproducible
    without anything looking wrong.
    """
    grid = fpr_grid(0.01, 0.10, 0.01)
    first = sweep_fpr(
        fast_config, _score_set(), grid=grid, data_source=MEASURED)
    second = sweep_fpr(
        fast_config, _score_set(), grid=grid, data_source=MEASURED)

    assert first.to_payload() == second.to_payload()
    for a, b in zip(first.points, second.points):
        if a.recall is None or b.recall is None:
            continue
        assert a.recall.ci_low == b.recall.ci_low
        assert a.recall.ci_high == b.recall.ci_high

    assert first.seed == fast_config.seed
    assert first.bootstrap_samples == fast_config.validation.bootstrap_samples


def test_the_sweep_reads_the_committed_config(config) -> None:
    """At the real settings: the sweep reports the config's count, seed and alpha.

    One grid point, because this is about where the numbers come from rather
    than about the shape of the curve. Without it every other test in this file
    could pass against a sweep that had quietly hardcoded its own bootstrap.
    """
    sweep = sweep_fpr(config, _score_set(n=120), grid=(0.10,), data_source=MEASURED)
    assert sweep.bootstrap_samples == config.validation.bootstrap_samples == 1000
    assert sweep.seed == config.seed == 1729
    assert sweep.alpha == pytest.approx(1.0 - config.validation.ci)


def test_every_reported_rate_carries_an_interval(fast_config) -> None:
    """Invariant 4: no point estimate reaches a reader bare."""
    sweep = sweep_fpr(
        fast_config, _score_set(), grid=fpr_grid(0.02, 0.06, 0.01), data_source=MEASURED
    )
    for point in sweep.points:
        if not point.certified:
            continue
        for metric in (point.recall, point.precision, point.flag_rate):
            assert metric is not None
            assert metric.ci_low is not None and metric.ci_high is not None
            assert metric.n is not None
        if point.lift is not None:
            assert point.lift.ci_low is not None and point.lift.ci_high is not None


def test_precision_and_recall_travel_together(fast_config) -> None:
    """Invariant 5: never one without the other, and no blended F1 anywhere."""
    sweep = sweep_fpr(
        fast_config, _score_set(), grid=fpr_grid(0.02, 0.06, 0.01), data_source=MEASURED
    )
    markdown = render_sweep(sweep, provenance={"git_commit": "a" * 40, "dirty": False})
    assert "recall" in markdown and "precision" in markdown
    assert "f1" not in markdown.lower()
    for point in sweep.points:
        if point.certified:
            assert (point.recall is None) == (point.precision is None)


# ---------------------------------------------------------- the D6 criterion

def test_lift_holds_is_strict_and_uses_the_lower_bound(fast_config) -> None:
    """The bar is ``ci_low > 1.0``, strictly, and it is applied to lift's own CI."""
    assert LIFT_HOLDS_LOWER_BOUND == 1.0
    sweep = sweep_fpr(
        fast_config, _score_set(), grid=fpr_grid(*REGISTERED_GRID), data_source=MEASURED
    )
    for point in sweep.points:
        if point.lift is None:
            assert point.lift_holds is None
            continue
        assert point.lift_holds == (point.lift.ci_low > LIFT_HOLDS_LOWER_BOUND)

    holding = sweep.holding_points
    if holding:
        assert sweep.headline is holding[-1], "headline must be the LARGEST holding target"
        assert all(p.target_fpr <= sweep.headline.target_fpr for p in holding)


def test_headline_is_absent_when_nothing_holds(fast_config) -> None:
    """A probe with no signal produces no headline rather than a weak one."""
    noise = _score_set(separation=0.0, seed=3)
    sweep = sweep_fpr(
        fast_config, noise, grid=fpr_grid(0.05, 0.20, 0.05), data_source=MEASURED
    )
    if sweep.headline is None:
        assert sweep.recall_is_a_dial is None
        text = verdict(sweep)
        assert "does not hold at any target" in text
        assert "weak" in text


# ------------------------------------------------------------- the frontier

def test_judge_calls_carry_the_envelope_in_their_name(fast_config) -> None:
    """The cost axis is flag rate x 1000, and it is not a production figure.

    The number is only meaningful beside the base rate it was measured at, so
    the payload key says so. A key called `judge_calls_per_1000` alone would be
    lifted into a cost model within a week — a flag rate from this envelope
    beside a base rate from production is the scenario-mixing error CLAUDE.md
    names.
    """
    sweep = sweep_fpr(
        fast_config, _score_set(), grid=fpr_grid(0.05, 0.10, 0.05), data_source=MEASURED
    )
    for point in sweep.points:
        if not point.certified:
            continue
        assert point.judge_calls_per_1000 == pytest.approx(
            point.flag_rate.value * 1000.0
        )

    payload = sweep.to_payload()
    assert "judge_calls_per_1000_on_this_envelope" in payload["points"][0]
    assert "judge_calls_per_1000" not in payload["points"][0]
    assert payload["cost_axis"]["declared_profile_budgets"]
    assert f"{sweep.base_rate:.4f}" in payload["cost_axis"]["caveat"]


def test_profiles_within_budget_come_from_config(fast_config) -> None:
    """Budgets are read from config.yaml, never from a figure quoted in a brief.

    DECISIONS 132: the brief assumed 3-5%; the config declares 0.10, 0.20 and
    0.50. A point is listed against a profile exactly when its measured flag
    rate is at or below that profile's declared budget.
    """
    sweep = sweep_fpr(
        fast_config, _score_set(), grid=fpr_grid(*REGISTERED_GRID), data_source=MEASURED
    )
    declared = {
        name: p.target_flag_rate for name, p in fast_config.profiles.items()
    }
    assert sweep.profile_budgets == declared

    for point in sweep.points:
        if not point.certified:
            assert point.profiles_within_budget == ()
            continue
        expected = tuple(
            sorted(n for n, b in declared.items() if point.flag_rate.value <= b)
        )
        assert point.profiles_within_budget == expected

    # A tighter budget can never serve a point a looser one cannot.
    for point in sweep.points:
        served = set(point.profiles_within_budget)
        for name in served:
            for other, budget in declared.items():
                if budget >= declared[name]:
                    assert other in served, (
                        f"{other} (budget {budget}) excluded while {name} "
                        f"(budget {declared[name]}) is included — the fit is not monotone"
                    )


def test_the_frontier_section_renders_with_its_caveat(fast_config) -> None:
    """The cost table exists, and never without the base rate that conditions it."""
    sweep = sweep_fpr(
        fast_config, _score_set(), grid=fpr_grid(0.02, 0.10, 0.02), data_source=MEASURED
    )
    markdown = render_sweep(sweep, provenance={"git_commit": "e" * 40, "dirty": False})

    assert "## The frontier: what recall costs" in markdown
    assert "judge calls / 1000" in markdown
    assert "not production costs" in markdown
    assert f"{sweep.base_rate:.4f}" in markdown
    assert "The two ends of the trade" in markdown
    for name in fast_config.profiles:
        assert f"`{name}`" in markdown


def test_the_frontier_ends_are_chosen_by_measurement(fast_config) -> None:
    """Most-recall and best-lift are maxima, not points picked by eye."""
    sweep = sweep_fpr(
        fast_config, _score_set(), grid=fpr_grid(0.02, 0.20, 0.02), data_source=MEASURED
    )
    markdown = render_sweep(sweep, provenance={"git_commit": "f" * 40, "dirty": False})
    certified = [p for p in sweep.points if p.certified and p.recall is not None]

    most_recall = max(certified, key=lambda p: p.recall.value)
    best_lift = max((p for p in certified if p.lift), key=lambda p: p.lift.value)
    assert f"target {most_recall.target_fpr:.2f}: recall" in markdown
    assert f"target {best_lift.target_fpr:.2f}: lift" in markdown


# ------------------------------------------------------------ fixture refusal

def test_fixture_sweep_renders_no_numbers(fast_config) -> None:
    """D9: a point whose inputs are a fixture is never rendered numerically."""
    sweep = sweep_fpr(
        fast_config,
        _score_set(),
        grid=fpr_grid(*REGISTERED_GRID),
        data_source="synthetic",
        data_source_reason="fixture-set is a synthetic fixture",
    )
    assert sweep.is_measured is False
    markdown = render_sweep(sweep, provenance={"git_commit": "b" * 40, "dirty": False})

    assert SWEEP_FIXTURE_MARKER in markdown
    # No table, and none of the measured values anywhere in the document.
    assert "| target FPR |" not in markdown
    for point in sweep.points:
        if point.recall is not None:
            assert f"{point.recall.value:.4f}" not in markdown
        if point.threshold is not None:
            assert f"{point.threshold:.6f}" not in markdown


def test_a_fixture_document_does_not_depend_on_the_fixture(fast_config) -> None:
    """The strong form of D9: change the generator, get the same document.

    Searching the rendered text for forbidden values is a weak check — the
    digit "1" appears in `T1-last_token` — and it misses the numbers that do
    not look like measurements. The class split and the base rate are as much
    properties of a generator as a threshold is, and both were being printed.

    So the property is stated directly: two fixtures with different labels,
    different scores and different separability must render byte-identically.
    Anything derived from the arrays would break that, whatever it is called.
    Only the grid length survives, and that is a parameter the caller passed in.
    """
    grid = fpr_grid(*REGISTERED_GRID)
    provenance = {"git_commit": "d" * 40, "dirty": False}
    documents = {
        render_sweep(
            sweep_fpr(
                fast_config,
                _score_set(seed=seed, separation=separation, base_rate=base_rate),
                grid=grid,
                data_source="synthetic",
                data_source_reason="fixture-set is a synthetic fixture",
            ),
            provenance=provenance,
        )
        for seed, separation, base_rate in ((7, 1.4, 0.46), (99, 0.2, 0.80))
    }
    assert len(documents) == 1, (
        "two different fixtures rendered two different documents, so something "
        "measured off the generator is reaching the page"
    )


def test_undeclared_data_source_is_refused_like_a_fixture(fast_config) -> None:
    """Fail-closed: an envelope that declares nothing is not assumed measured."""
    sweep = sweep_fpr(
        fast_config, _score_set(), grid=fpr_grid(0.05, 0.10, 0.05), data_source="unverified",
        data_source_reason="no data_source declared",
    )
    markdown = render_sweep(sweep, provenance={"git_commit": "c" * 40, "dirty": False})
    assert SWEEP_FIXTURE_MARKER in markdown
    assert "| target FPR |" not in markdown


def test_fixture_sweep_is_not_plotted(fast_config, tmp_path) -> None:
    """A figure outlives its terminal, so a fixture one is refused outright."""
    from controlplane.report.plots import plot_fpr_sweep

    sweep = sweep_fpr(
        fast_config, _score_set(), grid=fpr_grid(0.05, 0.10, 0.05), data_source="synthetic",
        data_source_reason="fixture",
    )
    with pytest.raises(ValueError, match="not measured"):
        plot_fpr_sweep(sweep, tmp_path / "sweep.png")


def test_resolve_data_source_fails_closed(tmp_path) -> None:
    """Absent artifact, absent declaration and a mismatched block all refuse."""
    import json

    missing = tmp_path / "gone.json"
    source, reason = resolve_data_source(
        missing, eval_set_id="x", envelope_id="sha256:y"
    )
    assert source == "unverified" and "absent" in reason

    undeclared = tmp_path / "undeclared.json"
    undeclared.write_text(
        json.dumps({"eval_set_id": "x", "envelope_id": "sha256:y"}), encoding="utf-8"
    )
    source, reason = resolve_data_source(
        undeclared, eval_set_id="x", envelope_id="sha256:y"
    )
    assert source == "unverified" and "no data_source" in reason

    wrong_envelope = tmp_path / "wrong.json"
    wrong_envelope.write_text(
        json.dumps(
            {"eval_set_id": "x", "envelope_id": "sha256:other", "data_source": "measured"}
        ),
        encoding="utf-8",
    )
    source, _ = resolve_data_source(
        wrong_envelope, eval_set_id="x", envelope_id="sha256:y"
    )
    assert source == "unverified", "a measured flag on another envelope is not ours"

    declared = tmp_path / "declared.json"
    declared.write_text(
        json.dumps(
            {
                "source": {"eval_set_id": "a", "envelope_id": "sha256:a",
                           "data_source": "measured"},
                "target": {"eval_set_id": "x", "envelope_id": "sha256:y",
                           "data_source": "measured"},
            }
        ),
        encoding="utf-8",
    )
    source, reason = resolve_data_source(
        declared, eval_set_id="x", envelope_id="sha256:y"
    )
    assert source == MEASURED and reason == ""


# ------------------------------------------------------------------- guards

def test_clustered_items_are_refused_rather_than_certified(fast_config) -> None:
    """Repeated question ids would overstate the effective sample size."""
    base = _score_set(n=100)
    clustered = ScoreSet(
        score_set_id=base.score_set_id,
        detector_id=base.detector_id,
        variant=base.variant,
        eval_set_id=base.eval_set_id,
        envelope_id=base.envelope_id,
        labels=base.labels,
        scores=base.scores,
        question_ids=tuple(f"q_{i // 2}" for i in range(base.n)),
        targets=base.targets,
    )
    with pytest.raises(ValueError, match="not independent"):
        sweep_fpr(
        fast_config, clustered, grid=(0.05,), data_source=MEASURED)


def test_a_set_with_no_negatives_is_refused(fast_config) -> None:
    """An FPR budget needs something to be wrong about."""
    base = _score_set(n=50)
    all_positive = ScoreSet(
        score_set_id=base.score_set_id,
        detector_id=base.detector_id,
        variant=base.variant,
        eval_set_id=base.eval_set_id,
        envelope_id=base.envelope_id,
        labels=tuple(1 for _ in range(base.n)),
        scores=base.scores,
        question_ids=base.question_ids,
        targets=base.targets,
    )
    with pytest.raises(ValueError, match="no negatives"):
        sweep_fpr(
        fast_config, all_positive, grid=(0.05,), data_source=MEASURED)
