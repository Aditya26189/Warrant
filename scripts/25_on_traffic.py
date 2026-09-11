"""The on-traffic warrant: the label price list, and the evidence it is sound.

Phase 6. Clause one of the three in ``CLAUDE.md`` — *"we tell you what your
error rate is on your traffic"* — which ``DECISIONS.md`` 096 and 099 recorded
as NOT BUILT through four phases.

Four things, in order:

1. **``dR/dq`` at the declared workload**, and the two ratios ``DECISIONS.md``
   148 separated.
2. **The label price list.** What each recall margin costs, at each profile's
   measured operating point, against what the superseded sizing said.
3. **The coverage simulation.** 1,000 trials on synthetic traffic with known
   ground truth. This is the evidence the estimator is sound; everything else
   here is arithmetic.
4. **The allocation and the blinding**, with the design effect measured from a
   band structure rather than taken from ``config.yaml``'s expectation.

Every figure is computed. Nothing here is typed (``CLAUDE.md`` invariant 8).

Thin wrapper: parses arguments, calls ``controlplane/``, writes files. No logic
(``CLAUDE.md``).

Usage:
    python scripts/25_on_traffic.py --config config.yaml
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from controlplane.config import load_config, setup_logging, write_json_artifact
from controlplane.sampling import (
    Band,
    LabelItem,
    build_queue,
    cohens_kappa,
    design_effect,
    estimate_on_traffic,
    labels_for_recall,
    neyman,
    proportional,
    recall_sensitivity,
)

_LOG = logging.getLogger("scripts.25_on_traffic")

#: Trials in the coverage simulation. Pre-registered in ``DECISIONS.md`` 147
#: along with the band coverage must land in.
COVERAGE_TRIALS = 1000

#: Synthetic population for the coverage simulation. Small enough to run on a
#: laptop in seconds, large enough that the sampling fraction is realistic.
COVERAGE_POOL = 20_000
COVERAGE_Q = 0.03
COVERAGE_FLAGGED = 900
COVERAGE_TP = 300
COVERAGE_N = 900

#: Band structure the allocation section is demonstrated on. Declared, and
#: labelled as such: a real one comes from the detector's score distribution on
#: the operator's own traffic, which this repository does not have.
DEMO_BANDS = {"b0": 100_000, "b1": 60_000, "b2": 30_000, "b3": 7_016}
DEMO_PREVALENCES = {"b0": 0.008, "b1": 0.020, "b2": 0.055, "b3": 0.140}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument(
        "--policy-artifact",
        default=None,
        help="policy JSON holding the measured operating points",
    )
    parser.add_argument("--out", default=None, help="results directory override")
    return parser.parse_args(argv)


def _measured_points(results: Path, override: str | None) -> dict[str, dict]:
    """Measured recall and flag rate per operating point, from ``results/``.

    Returns an empty mapping when the artifact is absent, so the price list for
    the declared workload still renders. A missing measurement is reported as
    missing rather than substituted.
    """
    path = Path(override) if override else results / "policy-triviaqa-600.json"
    if not path.exists():
        _LOG.warning("no policy artifact at %s; profile rows will be skipped", path)
        return {}
    with path.open(encoding="utf-8") as fh:
        document = json.load(fh)
    points: dict[str, dict] = {}
    for entry in document.get("operating_points", []):
        point = entry.get("operating_point") or {}
        metrics = entry.get("metrics") or {}
        point_id = point.get("operating_point_id")
        if point_id and "recall" in metrics and "flag_rate" in metrics:
            points[point_id] = {
                "recall": float(metrics["recall"]["value"]),
                "flag_rate": float(metrics["flag_rate"]["value"]),
            }
    return points


def _coverage() -> dict[str, object]:
    """Nominal coverage of the recall interval, on traffic with known truth.

    The estimand is finite-population recall on one fixed population, which is
    what the estimator claims. Each trial redraws the unflagged sample without
    replacement, so what varies across trials is exactly what the interval is a
    statement about.
    """
    rng = np.random.default_rng(1729)
    truth = np.zeros(COVERAGE_POOL, dtype=np.int8)
    truth[: int(round(COVERAGE_Q * COVERAGE_POOL))] = 1
    rng.shuffle(truth)
    realised_q = float(truth.mean())
    true_recall = COVERAGE_TP / (COVERAGE_TP + realised_q * COVERAGE_POOL)

    covered = 0
    widths: list[float] = []
    for _ in range(COVERAGE_TRIALS):
        idx = rng.choice(COVERAGE_POOL, size=COVERAGE_N, replace=False)
        errors = int(truth[idx].sum())
        estimate = estimate_on_traffic(
            flagged_reviewed=COVERAGE_FLAGGED,
            flagged_confirmed=COVERAGE_TP,
            bands=[Band("all", COVERAGE_POOL, COVERAGE_N, errors)],
        )
        widths.append(estimate.recall.ci_high - estimate.recall.ci_low)
        if estimate.recall.ci_low <= true_recall <= estimate.recall.ci_high:
            covered += 1
    return {
        "trials": COVERAGE_TRIALS,
        "pool": COVERAGE_POOL,
        "sample": COVERAGE_N,
        "declared_q": COVERAGE_Q,
        "realised_q": realised_q,
        "true_finite_population_recall": true_recall,
        "covered": covered,
        "coverage": covered / COVERAGE_TRIALS,
        "nominal": 0.95,
        "mean_interval_width": float(np.mean(widths)),
        "registered_band": [0.93, 0.97],
        "note": (
            "Clopper-Pearson is conservative by construction and this design "
            "adds a second conservatism by publishing an interval with no "
            "finite-population correction, so coverage is expected at or above "
            "nominal. Over-covering claims less than the evidence supports; "
            "under-covering claims more than it can."
        ),
    }


def _blinding_demo(seed: int, fraction: float) -> dict[str, object]:
    """A queue built from both strata, and what a reviewer can see of it."""
    items = [
        LabelItem(
            item_id=f"item-{i:04d}",
            content=f"response {i}",
            flagged=i < 40,
            stratum="flagged" if i < 40 else "unflagged",
            band="high" if i < 40 else "low",
            score=0.9 if i < 40 else 0.1,
            context={"question": f"q{i}"},
        )
        for i in range(400)
    ]
    queue = build_queue(
        items,
        seed=seed,
        double_label_fraction=fraction,
        safe_context_keys=["question"],
    )
    strata = {item.item_id: item.stratum for item in items}
    repeats: dict[str, int] = {}
    for item_id in queue.duplicated:
        repeats[strata[item_id]] = repeats.get(strata[item_id], 0) + 1
    positions = {p["queue_id"]: i for i, p in enumerate(queue.payloads)}
    flagged_positions = [
        positions[qid]
        for qid, item_id in queue.assignments.items()
        if strata[item_id] == "flagged"
    ]
    return {
        "items": len(items),
        "payloads": len(queue.payloads),
        "payload_keys": sorted(queue.payloads[0].keys()),
        "double_labelled": len(queue.duplicated),
        "double_labelled_by_stratum": repeats,
        "mean_flagged_position": float(np.mean(flagged_positions)),
        "queue_midpoint": (len(queue.payloads) - 1) / 2.0,
        "seed": queue.seed,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir
    out_dir = results / "on_traffic"
    out_dir.mkdir(parents=True, exist_ok=True)

    workload = config.workload
    margins = list(config.sampling.recall_margin_tiers)
    deff = config.sampling.expected_design_effect

    # 1. The declared workload's own operating point.
    declared_flag_rate = (
        workload.base_error_rate * workload.measured_tpr
        + (1.0 - workload.base_error_rate) * workload.measured_fpr
    )
    declared = recall_sensitivity(
        recall=workload.measured_tpr,
        flag_rate=declared_flag_rate,
        monthly_interactions=workload.monthly_interactions,
        base_error_rate=workload.base_error_rate,
    )
    _LOG.info("declared workload %s", workload.name)
    _LOG.info("    %s", declared.render())

    # 2. The price list, at the declared point and at each measured profile.
    points = _measured_points(results, args.policy_artifact)
    rows: list[dict[str, object]] = []
    subjects: list[tuple[str, object]] = [("declared workload point", declared)]
    for name, profile in sorted(config.profiles.items()):
        measured = points.get(profile.operating_point)
        if measured is None:
            _LOG.warning("no measured point for %s; skipped", profile.operating_point)
            continue
        subjects.append(
            (
                f"{name} @ {profile.operating_point}",
                recall_sensitivity(
                    recall=measured["recall"],
                    flag_rate=measured["flag_rate"],
                    monthly_interactions=workload.monthly_interactions,
                    base_error_rate=workload.base_error_rate,
                ),
            )
        )

    # The design effect that actually applies depends on which month it is, and
    # getting this wrong is a named silent failure rather than a refinement.
    # CLAUDE.md: "Neyman needs per-band prevalence q_h you don't have yet. Month
    # one runs proportional allocation at FULL SRS COST." A month-one plan
    # quoted at config.yaml's expected 0.67 -- which is Neyman's design effect,
    # and an expectation rather than a measurement -- is 1.5x too small, and it
    # is too small in the month when nobody has anything to check it against.
    measured_deff = design_effect(
        populations=DEMO_BANDS, prevalences=DEMO_PREVALENCES, total=1000
    )
    regimes = (
        ("month one (proportional, full SRS cost)", 1.0),
        ("steady state (Neyman, measured design effect)", measured_deff),
    )

    for label, sensitivity in subjects:
        for margin in margins:
            for regime, effect in regimes:
                plan = labels_for_recall(
                    sensitivity=sensitivity, margin=margin, design_effect=effect
                )
                rows.append(
                    {
                        "subject": label,
                        "regime": regime,
                        "design_effect_applied": effect,
                        "recall": sensitivity.recall,
                        "flag_rate": sensitivity.flag_rate,
                        "unflagged_prevalence": sensitivity.unflagged_prevalence,
                        "derivative": sensitivity.derivative,
                        "amplification_over_confirmed_errors": sensitivity.amplification,
                        "pool_ratio_over_flagged": sensitivity.pool_ratio,
                        **{
                            k: v
                            for k, v in dataclasses.asdict(plan).items()
                            if k != "declared_inputs"
                        },
                    }
                )
                _LOG.info("%s | %s", regime, plan.render().replace("\n", " |"))

    # 3. Does the interval cover what it claims to?
    coverage = _coverage()
    _LOG.info(
        "coverage %d/%d = %.4f against nominal %.2f",
        coverage["covered"], coverage["trials"], coverage["coverage"], 0.95,
    )

    # 4. Allocation and blinding.
    total = rows[0]["labels"] if rows else 1000
    even = proportional(populations=DEMO_BANDS, total=int(total))
    skewed = neyman(
        populations=DEMO_BANDS, prevalences=DEMO_PREVALENCES, total=int(total)
    )
    _LOG.info("%s", even.render())
    _LOG.info("%s", skewed.render())
    blinding = _blinding_demo(config.seed, config.sampling.double_label_fraction)

    # An agreement figure, from labels this repository does not have. Reported
    # as the mechanism working rather than as a measurement of any reviewer.
    rng = np.random.default_rng(config.seed)
    first = rng.integers(0, 2, size=100).tolist()
    second = [
        v if rng.random() > 0.15 else 1 - v for v in first
    ]
    agreement = cohens_kappa(first, second, seed=config.seed, resamples=1000)

    payload = {
        "question": (
            "what a recall claim on production traffic costs in labels, and "
            "whether the interval it produces covers what it claims (Phase 6, "
            "CLAUDE.md clause one)"
        ),
        "declared": {
            "workload": workload.name,
            "monthly_interactions": workload.monthly_interactions,
            "base_error_rate": workload.base_error_rate,
            "measured_tpr": workload.measured_tpr,
            "measured_fpr": workload.measured_fpr,
            "implied_flag_rate": declared_flag_rate,
            "recall_margin_tiers": margins,
            "expected_design_effect": deff,
            "double_label_fraction": config.sampling.double_label_fraction,
        },
        "sensitivity": dataclasses.asdict(declared),
        "price_list": rows,
        "coverage": coverage,
        "allocation": {
            "proportional": dataclasses.asdict(even),
            "neyman": dataclasses.asdict(skewed),
            "measured_design_effect": measured_deff,
            "declared_design_effect": deff,
            "bands_are_declared": True,
            "note": (
                "The band structure is declared, not measured: a real one comes "
                "from the detector's score distribution on the operator's own "
                "traffic, which this repository does not have. What is measured "
                "here is the design effect that follows from a band structure, "
                "which is the quantity SPEC.md 6.3 says to measure rather than "
                "assume."
            ),
        },
        "blinding": blinding,
        "agreement_mechanism": dataclasses.asdict(agreement),
        "headline": _headline(rows, coverage, measured_deff, declared),
        "not_derived_here": [
            "any recall figure on real production traffic -- this repository "
            "has none, and the estimator is evidenced by simulation instead",
            "a recheck cadence, which depends on how fast the input "
            "distribution moves (DECISIONS.md 146)",
            "per-band prevalences for Neyman, which month one cannot have",
        ],
    }
    write_json_artifact(out_dir / "on_traffic.json", payload, config)
    _LOG.info("wrote %s", out_dir / "on_traffic.json")

    _write_markdown(out_dir, payload)
    return 0


def _headline(
    rows: list[dict], coverage: dict, measured_deff: float, sensitivity
) -> dict[str, object]:
    """Flat fields the README claim table can resolve without list filtering.

    The table's field syntax reaches into lists by key, and every key available
    here is prose with spaces in it. A flat block costs nothing and keeps the
    claim rows readable, which is the half of invariant 8 that is about whether
    anyone can check the trace rather than whether it exists.
    """

    def find(margin: float, regime_prefix: str) -> dict:
        for row in rows:
            if (
                row["subject"] == "declared workload point"
                and row["margin"] == margin
                and str(row["regime"]).startswith(regime_prefix)
            ):
                return row
        raise KeyError(f"no price-list row for margin {margin} in {regime_prefix}")

    month_one_5pp = find(0.05, "month one")
    month_one_2pp = find(0.02, "month one")
    steady_5pp = find(0.05, "steady state")
    return {
        "derivative": sensitivity.derivative,
        "amplification_over_confirmed_errors": sensitivity.amplification,
        "pool_ratio_over_flagged": sensitivity.pool_ratio,
        "labels_month_one_5pp": month_one_5pp["labels"],
        "labels_month_one_2pp": month_one_2pp["labels"],
        "labels_steady_state_5pp": steady_5pp["labels"],
        "labels_normal_basis_5pp": month_one_5pp["labels_normal"],
        "superseded_sizing_5pp": month_one_5pp["naive_labels"],
        "understatement_5pp": month_one_5pp["understatement"],
        "coverage": coverage["coverage"],
        "coverage_trials": coverage["trials"],
        "measured_design_effect": measured_deff,
    }


def _write_markdown(out_dir: Path, payload: dict) -> None:
    """Render the artifact as a table a reader can check by hand."""
    declared = payload["declared"]
    sensitivity = payload["sensitivity"]
    coverage = payload["coverage"]
    lines = [
        "# The on-traffic warrant",
        "",
        "Generated by `scripts/25_on_traffic.py`. Every number here is computed "
        "from `config.yaml` and `results/`; none is typed.",
        "",
        "## The derivative",
        "",
        f"At the declared workload `{declared['workload']}` "
        f"(N={declared['monthly_interactions']:,}, "
        f"base error rate {declared['base_error_rate']:g}, "
        f"implied flag rate {declared['implied_flag_rate']:.6f}):",
        "",
        "| quantity | value |",
        "|---|---|",
        f"| confirmed true positives `TP` | {sensitivity['confirmed_errors']:,.0f} |",
        f"| unflagged pool `N_u` | {sensitivity['unflagged_pool']:,.0f} |",
        f"| flagged pool `N_f` | {sensitivity['flagged_pool']:,.0f} |",
        f"| unflagged prevalence `q` | {sensitivity['unflagged_prevalence']:.5f} |",
        f"| **`dR/dq`** | **{sensitivity['derivative']:.3f}** |",
        f"| `N_u / TP` — the ratio that multiplies | {sensitivity['amplification']:,.1f} |",
        f"| `N_u / N_f` — a different ratio | {sensitivity['pool_ratio']:,.1f} |",
        "",
        "`DECISIONS.md` 148: the second of those two is the one `CLAUDE.md` and "
        "`SPEC.md` used to name, and it is not the one in the derivative.",
        "",
        "## The price list",
        "",
        "| subject | margin | regime | labels | normal approx | superseded sizing | understated |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload["price_list"]:
        regime = "month one" if str(row["regime"]).startswith("month") else "steady state"
        cell = "**REFUSED**" if not row["feasible"] else f"**{row['labels']:,}**"
        under = "—" if not row["feasible"] else f"{row['understatement']:.1f}×"
        lines.append(
            f"| {row['subject']} | ±{row['margin']:g} | {regime} | {cell} | "
            f"{row['labels_normal']:,} | {row['naive_labels']:,} | {under} |"
        )
    lines += [
        "",
        "**labels** is the smallest sample from which the exact interval holds "
        "the margin and keeps holding it. **normal approx** is `SPEC.md` §6.2's "
        "closed form, which under-delivers (`DECISIONS.md` 149). **superseded "
        "sizing** is what `economics/review.py` returned before `DECISIONS.md` "
        "147.",
        "",
        "**Month one costs more than steady state, and the difference is not a "
        "discount anyone can take early.** Neyman allocation needs the per-band "
        "prevalences that the first month's labels are bought to discover, so "
        "month one runs proportional at full simple-random-sampling cost. "
        "`config.yaml` carries an *expected* design effect of "
        f"{payload['allocation']['declared_design_effect']:g}; applying it to a "
        "month-one plan is the silent failure `CLAUDE.md` lists as *Neyman "
        "allocation on day one*, and it under-sizes the first month by about "
        "50% — in the one month when nobody has a prior estimate to notice it "
        "against.",
        "",
        "## Does the interval cover what it claims?",
        "",
        f"- **{coverage['coverage']:.1%}** over {coverage['trials']:,} trials, "
        f"against a nominal {coverage['nominal']:.0%}.",
        f"- True finite-population recall "
        f"{coverage['true_finite_population_recall']:.4f}, realised prevalence "
        f"{coverage['realised_q']:.5f}.",
        f"- Mean interval width {coverage['mean_interval_width']:.5f}.",
        "",
        coverage["note"],
        "",
        "## Allocation",
        "",
        f"- Measured design effect on the declared band structure: "
        f"**{payload['allocation']['measured_design_effect']:.4f}** against "
        f"`config.yaml`'s expected "
        f"{payload['allocation']['declared_design_effect']:g}.",
        "- Month one runs proportional, because Neyman needs the per-band "
        "prevalences the first month's labels are bought to discover.",
        "- Proportional earns an **exact** interval; Neyman's unequal sampling "
        "fractions do not. That is what the precision costs.",
        "",
        "## Blinding",
        "",
        f"- Reviewer payload carries only `{'`, `'.join(payload['blinding']['payload_keys'])}`.",
        f"- {payload['blinding']['double_labelled']} items double-labelled, "
        f"split across strata as {payload['blinding']['double_labelled_by_stratum']}.",
        f"- Mean position of flagged items in the queue "
        f"{payload['blinding']['mean_flagged_position']:.1f} against a midpoint "
        f"of {payload['blinding']['queue_midpoint']:.1f}.",
        "",
        "## What this does not establish",
        "",
    ]
    for item in payload["not_derived_here"]:
        lines.append(f"- {item}")
    lines.append("")
    (out_dir / "ON_TRAFFIC.md").write_text("\n".join(lines), encoding="utf-8")
    _LOG.info("wrote %s", out_dir / "ON_TRAFFIC.md")


if __name__ == "__main__":
    raise SystemExit(main())
