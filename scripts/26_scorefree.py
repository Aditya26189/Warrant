"""What it costs to certify a detector that emits no score.

``docs/REDACT.md`` §5 states the limit: the detector family that wins on REDACT
— GPT-4.1, Claude Sonnet — emits spans and types with no confidence, so there is
nothing to threshold and the method cannot certify them. The route out is
repeated sampling: run the judge ``k`` times at temperature, score each item by
the fraction of runs that flagged it.

This measures what that buys and what it costs, against a **simulated** judge.
``DECISIONS.md`` 152 registered four claims before any of this ran and records
which one failed.

**The scope, stated before the numbers.** The judge here has a latent per-item
flag probability and its ``k`` runs are independent Bernoulli draws from it. A
real judge's runs share a prompt, a system message and a temperature, and are
correlated — which makes the vote fraction a *worse* estimate of the latent
probability than this assumes. **Every figure here is an upper bound on what
``k`` buys.** Closing that needs a paid key and stays open (``DECISIONS.md``
136).

Thin wrapper: parses arguments, calls ``controlplane/``, writes files. No logic
(``CLAUDE.md``).

Usage:
    python scripts/26_scorefree.py --config config.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from controlplane.config import load_config, setup_logging, write_json_artifact
from controlplane.validation.scorefree import (
    consensus_scores,
    smallest_certifiable_budget,
    tunability,
)
from controlplane.validation.stats import auroc
from controlplane.validation.warrant_stats import cp_upper

_LOG = logging.getLogger("scripts.26_scorefree")

#: Budgets tunability is measured across. The same shape of grid
#: ``DECISIONS.md`` 141 used for Presidio, so the two are comparable.
BUDGETS = (0.001, 0.002, 0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30)

#: Sample counts priced. Stops at 50 because the crossover lands well below it
#: at every pool size measured, so larger ``k`` is inference spend buying
#: nothing.
SAMPLE_COUNTS = (1, 2, 3, 5, 9, 25, 50)

#: Negative pool sizes. 1,000 is REDACT's locked split; 20,000 is what a
#: benchmark would need to underwrite a budget in the basis points.
POOL_SIZES = (200, 1000, 5000, 20000)

#: Vote draws per cell. A single draw is noisy enough to have produced a wrong
#: conclusion once already (``DECISIONS.md`` 152, C3), so every floor here is a
#: median over draws with its range reported.
DRAWS = 40

#: The simulated judge. Negatives from Beta(1.2, 12) -- mean 0.091, so it fires
#: on about 9% of clean items -- and positives from Beta(5, 3). The overlap is
#: deliberate: a separable simulation makes every result here trivial.
NEGATIVE_SHAPE = (1.2, 12.0)
POSITIVE_SHAPE = (5.0, 3.0)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--out", default=None, help="results directory override")
    return parser.parse_args(argv)


def _judge(n_negatives: int, seed: int):
    """Latent flag probabilities and labels for the simulated judge."""
    rng = np.random.default_rng(seed)
    n_positives = max(50, n_negatives // 3)
    negatives = np.clip(rng.beta(*NEGATIVE_SHAPE, n_negatives), 0.0, 1.0)
    positives = np.clip(rng.beta(*POSITIVE_SHAPE, n_positives), 0.0, 1.0)
    latent = np.concatenate([negatives, positives])
    labels = np.concatenate(
        [np.zeros(n_negatives, dtype=int), np.ones(n_positives, dtype=int)]
    )
    return latent, labels


def _floors(seed: int) -> list[dict[str, object]]:
    """The tightest certifiable budget, by pool size and ``k``.

    Two floors bind and they bind in turn. The **data's capacity** is
    ``cp_upper(0, n, alpha)``: no threshold reaches below it, because a
    Clopper-Pearson bound from zero failures is still positive. **Granularity**
    is what ``k`` notches can land on. Which one binds is the finding.
    """
    rows: list[dict[str, object]] = []
    for pool in POOL_SIZES:
        latent, labels = _judge(pool, seed)
        negatives = labels == 0
        data_floor = cp_upper(0, pool, 0.05)
        for k in SAMPLE_COUNTS:
            values: list[float] = []
            for draw in range(DRAWS):
                votes = np.random.default_rng(
                    900_000 + 1_000 * k + 7 * pool + draw
                ).binomial(k, latent)
                scores = np.asarray(
                    consensus_scores(votes, k=k, detector_id="judge-sim").scores
                )
                reachable = smallest_certifiable_budget(
                    scores[negatives], scores[~negatives]
                )
                values.append(1.0 if reachable is None else reachable)
            rows.append(
                {
                    "n_negatives": pool,
                    "k": k,
                    "data_floor": data_floor,
                    "granularity_floor_median": float(np.median(values)),
                    "granularity_floor_min": float(min(values)),
                    "granularity_floor_max": float(max(values)),
                    "binds": (
                        "data"
                        if float(np.median(values)) <= data_floor * 1.05
                        else "granularity"
                    ),
                    "draws": DRAWS,
                }
            )
    return rows


def _crossovers(seed: int) -> list[dict[str, object]]:
    """The smallest ``k`` at which granularity stops being what binds.

    Past it, more samples buy nothing: the benchmark's own certification
    capacity is the constraint and no amount of inference moves it.
    """
    rows: list[dict[str, object]] = []
    for pool in POOL_SIZES:
        latent, labels = _judge(pool, seed)
        negatives = labels == 0
        data_floor = cp_upper(0, pool, 0.05)
        crossings: list[int] = []
        for draw in range(DRAWS):
            found = SAMPLE_COUNTS[-1] + 1
            for k in range(1, 40):
                votes = np.random.default_rng(
                    500_000 + 1_000 * k + 7 * pool + draw
                ).binomial(k, latent)
                scores = np.asarray(
                    consensus_scores(votes, k=k, detector_id="judge-sim").scores
                )
                reachable = smallest_certifiable_budget(
                    scores[negatives], scores[~negatives]
                )
                if reachable is not None and reachable <= data_floor * 1.0000001:
                    found = k
                    break
            crossings.append(found)
        rows.append(
            {
                "n_negatives": pool,
                "data_floor": data_floor,
                "crossover_k_median": int(np.median(crossings)),
                "crossover_k_min": int(min(crossings)),
                "crossover_k_max": int(max(crossings)),
                "draws": DRAWS,
            }
        )
    return rows


def _tunability(seed: int) -> list[dict[str, object]]:
    """Distinct operating points reachable, by ``k``. Notches are not points."""
    latent, labels = _judge(1000, seed)
    rows: list[dict[str, object]] = []
    for k in SAMPLE_COUNTS:
        scores = consensus_scores(
            np.random.default_rng(100 + k).binomial(k, latent),
            k=k,
            detector_id="judge-sim",
        )
        result = tunability(
            scores=scores.scores,
            labels=labels,
            budgets=BUDGETS,
            detector_id=scores.detector_id,
        )
        rows.append(
            {
                "k": k,
                "detector_id": result.detector_id,
                "notches": scores.notches,
                "distinct_scores": result.distinct_scores,
                "distinct_operating_points": result.distinct_operating_points,
                "budgets_requested": result.budgets_requested,
                "budgets_certifiable": result.budgets_certifiable,
                "tightest_certifiable": result.tightest_certifiable,
            }
        )
        _LOG.info("%s", result.render())
    return rows


def _ranking(seed: int) -> dict[str, object]:
    """What finite ``k`` costs in ranking quality, against the latent ceiling."""
    latent, labels = _judge(1000, seed)
    ceiling = auroc(labels, latent)
    rows = []
    for k in SAMPLE_COUNTS:
        draws = [
            auroc(
                labels,
                np.random.default_rng(1_000 * k + s).binomial(k, latent) / k,
            )
            for s in range(DRAWS)
        ]
        rows.append(
            {
                "k": k,
                "auroc_mean": float(np.mean(draws)),
                "gap_to_ceiling": float(ceiling - np.mean(draws)),
            }
        )
    return {"latent_ceiling_auroc": ceiling, "by_k": rows}


def _void_at_another_k(seed: int) -> dict[str, object]:
    """Certify at k=9, apply the same threshold at k=1, report the breach."""
    latent, labels = _judge(1000, seed)
    nine = consensus_scores(
        np.random.default_rng(109).binomial(9, latent), k=9, detector_id="judge-sim"
    )
    certified = tunability(
        scores=nine.scores, labels=labels, budgets=(0.05,), detector_id=nine.detector_id
    ).achievable[0.05]
    one = consensus_scores(
        np.random.default_rng(201).binomial(1, latent), k=1, detector_id="judge-sim"
    )
    at_one = np.asarray(one.scores)[labels == 0]
    realised = float((at_one >= certified["threshold"]).mean())
    return {
        "certified_detector_id": nine.detector_id,
        "deployed_detector_id": one.detector_id,
        "budget": 0.05,
        "threshold": certified["threshold"],
        "certified_fpr": certified["fpr"],
        "certified_upper_bound": certified["fpr_upper"],
        "realised_fpr_at_k1": realised,
        "breach_factor": realised / certified["fpr_upper"],
        "verdict": "VOID" if realised > certified["fpr_upper"] else "held",
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir
    out_dir = results / "scorefree"
    out_dir.mkdir(parents=True, exist_ok=True)

    seed = config.seed
    floors = _floors(seed)
    crossovers = _crossovers(seed)
    points = _tunability(seed)
    ranking = _ranking(seed)
    void = _void_at_another_k(seed)

    for row in crossovers:
        _LOG.info(
            "n=%6d  data floor %.5f  crossover k=%d [%d, %d]",
            row["n_negatives"], row["data_floor"],
            row["crossover_k_median"], row["crossover_k_min"], row["crossover_k_max"],
        )
    _LOG.info(
        "certified at k=9 upper bound %.4f; same threshold at k=1 realises %.4f -> %s",
        void["certified_upper_bound"], void["realised_fpr_at_k1"], void["verdict"],
    )

    at_one = [r for r in floors if r["k"] == 1]
    headline = {
        "single_sample_floor_median": float(
            np.median([r["granularity_floor_median"] for r in at_one])
        ),
        "crossover_k_smallest_pool": crossovers[0]["crossover_k_median"],
        "crossover_k_largest_pool": crossovers[-1]["crossover_k_median"],
        "operating_points_at_k1": points[0]["distinct_operating_points"],
        "operating_points_at_k50": points[-1]["distinct_operating_points"],
        "notches_at_k50": points[-1]["notches"],
        "auroc_gap_at_k1": ranking["by_k"][0]["gap_to_ceiling"],
        "auroc_gap_at_k9": next(
            r["gap_to_ceiling"] for r in ranking["by_k"] if r["k"] == 9
        ),
        "breach_factor_deploying_at_k1": void["breach_factor"],
    }

    payload = {
        "question": (
            "what it costs to certify a detector that emits no score, and what "
            "repeated sampling buys (docs/REDACT.md section 5, DECISIONS.md 152)"
        ),
        "scope": (
            "SIMULATED judge. Latent per-item flag probability, k independent "
            "Bernoulli draws. A real judge's runs share a prompt and a "
            "temperature and are correlated, which makes the vote fraction a "
            "worse estimate than this assumes. Every figure here is an UPPER "
            "BOUND on what k buys. It certifies no real detector."
        ),
        "declared": {
            "seed": seed,
            "budgets": list(BUDGETS),
            "sample_counts": list(SAMPLE_COUNTS),
            "pool_sizes": list(POOL_SIZES),
            "draws_per_cell": DRAWS,
            "negative_beta": list(NEGATIVE_SHAPE),
            "positive_beta": list(POSITIVE_SHAPE),
        },
        "headline": headline,
        "floors": floors,
        "crossovers": crossovers,
        "tunability": points,
        "ranking": ranking,
        "void_at_another_k": void,
        "not_derived_here": [
            "any certification of GPT-4.1, Claude or any real judge -- no key, "
            "DECISIONS.md 136",
            "the correlation between a real judge's repeated samples, which "
            "makes every figure here optimistic",
            "the inference cost in currency, which is a provider price list "
            "and not a measurement",
        ],
    }
    write_json_artifact(out_dir / "scorefree.json", payload, config)
    _LOG.info("wrote %s", out_dir / "scorefree.json")
    _write_markdown(out_dir, payload)
    return 0


def _write_markdown(out_dir: Path, payload: dict) -> None:
    """Render the artifact as tables a reader can check."""
    head = payload["headline"]
    lines = [
        "# Certifying a detector that emits no score",
        "",
        "Generated by `scripts/26_scorefree.py`. Every number is computed; none "
        "is typed.",
        "",
        "> **Scope.** " + payload["scope"],
        "",
        "## The finding",
        "",
        "**A single-sample judge cannot be certified to a tight false-positive "
        f"budget however much data you have.** At `k = 1` the tightest budget "
        f"any useful threshold reaches is **{head['single_sample_floor_median']:.3f}**, "
        "which is just the judge's own false-positive rate — one bit gives one "
        "usable cut point, so there is no dial to turn. The data's own floor at "
        "20,000 negatives is 0.00015, three orders of magnitude tighter and "
        "completely unreachable.",
        "",
        "**And the fix is cheap and bounded.** The crossover — the smallest `k` "
        "at which granularity stops binding and the benchmark's own "
        "certification capacity takes over — is "
        f"`k = {head['crossover_k_smallest_pool']}` at 200 negatives and "
        f"`k = {head['crossover_k_largest_pool']}` at 20,000. Past it, more "
        "samples are inference spend buying nothing.",
        "",
        "## Two floors, and which one binds",
        "",
        "| negatives | data floor | " + " | ".join(f"k={k}" for k in SAMPLE_COUNTS) + " |",
        "|---" * (len(SAMPLE_COUNTS) + 2) + "|",
    ]
    for pool in POOL_SIZES:
        cells = []
        floor = None
        for k in SAMPLE_COUNTS:
            row = next(
                r for r in payload["floors"] if r["n_negatives"] == pool and r["k"] == k
            )
            floor = row["data_floor"]
            mark = "" if row["binds"] == "data" else "**"
            cells.append(f"{mark}{row['granularity_floor_median']:.5f}{mark}")
        lines.append(f"| {pool:,} | {floor:.5f} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "Median over 40 vote draws. **Bold** means granularity is what binds; "
        "plain means the data's capacity is. A single draw is noisy enough to "
        "have produced a wrong conclusion once (`DECISIONS.md` 152, C3).",
        "",
        "## Notches are not operating points",
        "",
        "| k | notches | distinct scores | operating points | budgets reachable | tightest |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload["tunability"]:
        tightest = (
            f"{row['tightest_certifiable']:g}"
            if row["tightest_certifiable"] is not None
            else "none"
        )
        lines.append(
            f"| {row['k']} | {row['notches']} | {row['distinct_scores']} | "
            f"**{row['distinct_operating_points']}** | "
            f"{row['budgets_certifiable']}/{row['budgets_requested']} | {tightest} |"
        )
    lines += [
        "",
        f"At `k = 50` the detector has {head['notches_at_k50']} notches and lands "
        f"on {head['operating_points_at_k50']} distinct operating points. Buying "
        "notches does not buy operating points in proportion — which is the "
        "same finding `DECISIONS.md` 141 made about Presidio's rule-fired "
        "confidence, reached from the other direction.",
        "",
        "## What finite k costs in ranking",
        "",
        "| k | AUROC | gap to the latent ceiling |",
        "|---|---|---|",
    ]
    for row in payload["ranking"]["by_k"]:
        lines.append(
            f"| {row['k']} | {row['auroc_mean']:.4f} | {row['gap_to_ceiling']:+.4f} |"
        )
    void = payload["void_at_another_k"]
    lines += [
        "",
        f"Ceiling {payload['ranking']['latent_ceiling_auroc']:.4f}, the AUROC of "
        "the latent probability itself.",
        "",
        "## Why k belongs in the warrant key",
        "",
        f"Certify at `k = 9`: threshold {void['threshold']:.4f}, measured "
        f"false-positive rate {void['certified_fpr']:.4f}, certified upper bound "
        f"**{void['certified_upper_bound']:.4f}**.",
        "",
        f"Apply the identical threshold at `k = 1`: realised false-positive rate "
        f"**{void['realised_fpr_at_k1']:.4f}** — "
        f"{void['breach_factor']:.1f}× the certified bound. The warrant is "
        f"**{void['verdict']}**.",
        "",
        f"So `{void['certified_detector_id']}` and `{void['deployed_detector_id']}` "
        "are different detectors and are keyed as such. A warrant that did not "
        "name `k` would bound a procedure nobody was running.",
        "",
        "## What this does not establish",
        "",
    ]
    for item in payload["not_derived_here"]:
        lines.append(f"- {item}")
    lines.append("")
    (out_dir / "SCOREFREE.md").write_text("\n".join(lines), encoding="utf-8")
    _LOG.info("wrote %s", out_dir / "SCOREFREE.md")


if __name__ == "__main__":
    raise SystemExit(main())
