"""Sweep the FPR budget over frozen scores: is recall 0.079 a ceiling or a dial?

Phase 0. Re-analysis only — no inference, no refit, no model. Reads
``results/scores/*.json``, certifies a threshold at each target FPR through the
existing ``certify_fpr``, and scores it through the same metrics builder every
runner calls. Thin wrapper: parses arguments, calls ``controlplane/``, writes
files. No logic (``CLAUDE.md``).

The grid defaults are the ones pre-registered in the Phase 0 brief (D2) and are
argparse defaults rather than config keys, following ``08_paired.py``'s
``--bootstrap``: they parameterise *this analysis*, while every statistical knob
the sweep uses — bootstrap count, coverage, seed — comes from ``config.yaml`` so
the intervals here are the same object every other artifact reports.

Usage:
    python scripts/19_fpr_sweep.py --config config.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.config import (
    load_config,
    provenance,
    set_seeds,
    setup_logging,
    write_json_artifact,
)
from controlplane.report.plots import plot_fpr_frontier, plot_fpr_sweep
from controlplane.report.sweep import render_sweep
from controlplane.validation.fpr_sweep import (
    fpr_grid,
    resolve_data_source,
    sweep_fpr,
)
from controlplane.validation.scores import load_score_set

_LOG = logging.getLogger("scripts.19_fpr_sweep")

#: Primary then secondary, in the order the brief registers them (D3). The
#: long-context set is the same probe unrefitted on a shifted envelope, so it
#: says whether the answer survives the shift the product exists to detect.
DEFAULT_SCORE_SETS = ("validation-T1-last_token", "transfer-T1-last_token")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument(
        "--score-set",
        action="append",
        default=None,
        help=(
            "score set id under results/scores/, repeatable. Defaults to the "
            f"pre-registered pair {DEFAULT_SCORE_SETS}."
        ),
    )
    parser.add_argument("--start", type=float, default=0.01, help="first target FPR")
    parser.add_argument("--stop", type=float, default=0.20, help="last target FPR")
    parser.add_argument("--step", type=float, default=0.01, help="grid spacing")
    parser.add_argument("--out", default=None, help="results directory override")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)
    set_seeds(config.seed)

    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir
    out_dir = results / "fpr_sweep"
    out_dir.mkdir(parents=True, exist_ok=True)
    grid = fpr_grid(args.start, args.stop, args.step)
    score_set_ids = args.score_set or list(DEFAULT_SCORE_SETS)

    sweeps = []
    for score_set_id in score_set_ids:
        path = results / "scores" / f"{score_set_id}.json"
        if not path.is_file():
            raise SystemExit(
                f"no frozen scores at {path}. This stage re-analyses committed "
                "scores and will not regenerate them: run scripts/10_freeze_scores.py "
                "from a machine that has the extraction cache."
            )
        score_set = load_score_set(path)
        artifact = PROJECT_ROOT / score_set.targets[0].artifact
        data_source, reason = resolve_data_source(
            artifact,
            eval_set_id=score_set.eval_set_id,
            envelope_id=score_set.envelope_id,
        )
        _LOG.info(
            "sweeping %s (%s, data_source=%s) over %d targets",
            score_set_id, score_set.eval_set_id, data_source, len(grid),
        )
        sweeps.append(
            sweep_fpr(
                config,
                score_set,
                grid=grid,
                data_source=data_source,
                data_source_reason=reason,
            )
        )

    write_json_artifact(
        out_dir / "sweep.json",
        {
            "grid_spec": {
                "start": args.start,
                "stop": args.stop,
                "step": args.step,
                "targets": list(grid),
                "n_points": len(grid),
                "registered": "Phase 0 brief D2",
            },
            "sweeps": [s.to_payload() for s in sweeps],
        },
        config,
    )

    prov = provenance(config)
    # The out-of-sample sweep (scripts/20_fpr_sweep_oos.py) is what any external
    # claim quotes; this one stays as the evidence for how little the in-sample
    # threshold biased it. DECISIONS 134.
    sections = [
        render_sweep(s, provenance=prov, superseded_by="results/fpr_sweep_oos/")
        for s in sweeps
    ]
    (out_dir / "SWEEP.md").write_text(
        "\n\n---\n\n".join(sections) + "\n", encoding="utf-8"
    )
    _LOG.info("wrote %s", out_dir / "SWEEP.md")

    # One figure, for the primary set (D3, D8). The secondary's table is in
    # SWEEP.md; a second figure would be a fourth artifact the brief does not
    # ask for.
    primary = sweeps[0]
    if primary.is_measured:
        plot_fpr_sweep(
            primary,
            out_dir / "sweep.png",
            config_hash=config.config_hash,
            git_commit=prov.get("git_commit"),
        )
        plot_fpr_frontier(
            primary,
            out_dir / "frontier.png",
            config_hash=config.config_hash,
            git_commit=prov.get("git_commit"),
        )
    else:
        _LOG.error(
            "not plotting %s: data_source is %s, not measured",
            primary.eval_set_id, primary.data_source,
        )

    for sweep in sweeps:
        headline = sweep.headline
        _LOG.info("-- %s (%s)", sweep.eval_set_id, sweep.variant)
        if headline is None:
            _LOG.info(
                "   lift holds at NO target on the grid; the pre-registered "
                "criterion is not met anywhere"
            )
            continue
        _LOG.info(
            "   largest target FPR where lift holds: %.2f  recall there %.4f "
            "[%.4f, %.4f]  lift %.3f [%.3f, %.3f]  dial=%s",
            headline.target_fpr, headline.recall.value,
            headline.recall.ci_low, headline.recall.ci_high,
            headline.lift.value, headline.lift.ci_low, headline.lift.ci_high,
            sweep.recall_is_a_dial,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
