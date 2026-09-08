"""The out-of-sample sweep: certify on validation, measure on test.

Phase 1, T2. Closes the question ``DECISIONS.md`` 124 left open — every recall
in the Phase 0 sweep was in-sample, because the threshold at each grid point was
certified on the same split it was then scored on.

This needs no GPU. ``results/cache-triviaqa-600.npz`` holds the activations for
all 2400 items; the probe is fit from them by the same selection path
``validate`` uses, and scoring the validation split is a matrix multiply
(``DECISIONS.md`` 133). What the GPU would be for is extracting activations that
do not exist yet, which is a different task.

**The integrity check runs first and is not optional.** The probe fit here must
reproduce the committed test-split scores bit-identically. If it does not, it is
not the pipeline's probe, nothing certified from it describes the shipped
system, and this script stops rather than producing a number that looks fine.

Thin wrapper: parses arguments, calls ``controlplane/``, writes files. No logic
(``CLAUDE.md``).

Usage:
    python scripts/20_fpr_sweep_oos.py --config config.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np

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
from controlplane.evalsets.registry import load_evalset
from controlplane.report.plots import plot_fpr_frontier, plot_fpr_sweep
from controlplane.report.sweep import render_sweep
from controlplane.validation.evalsets import TEST, VALIDATION, ExtractionCache
from controlplane.validation.fpr_sweep import fpr_grid, sweep_fpr
from controlplane.validation.paired import fit_on
from controlplane.validation.scores import (
    ScoreSet,
    ScoreTarget,
    load_score_set,
    write_score_set,
)

_LOG = logging.getLogger("scripts.20_fpr_sweep_oos")

VARIANT = "T1-last_token"
EVAL_SET = "triviaqa-600"
#: Deliberately not "validation-*": the committed `validation-T1-last_token.json`
#: holds TEST-split scores and is named for the run artifact it reproduces.
#: Two files differing by a suffix and by which split they are is the mistake
#: that gets found three artifacts downstream (`DECISIONS.md` 133).
VALSPLIT_ID = f"valsplit-{VARIANT}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--start", type=float, default=0.01)
    parser.add_argument("--stop", type=float, default=0.20)
    parser.add_argument("--step", type=float, default=0.01)
    parser.add_argument("--out", default=None, help="results directory override")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)
    set_seeds(config.seed)

    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir
    cache_path = results / f"cache-{EVAL_SET}.npz"
    if not cache_path.is_file():
        raise SystemExit(
            f"no extraction cache at {cache_path}. This stage scores rows that "
            "are already extracted; it cannot create them. Run it where the "
            "cache exists."
        )

    evalset = load_evalset(PROJECT_ROOT / config.paths.evalsets_dir / f"{EVAL_SET}.json")
    cache = ExtractionCache.load(cache_path)
    probe, splits = fit_on(config, cache, evalset, variant=VARIANT)
    features = cache.matrix(VARIANT)

    # --- the integrity check, before anything is built on this probe --------
    committed = load_score_set(results / "scores" / f"validation-{VARIANT}.json")
    test_rows = splits[TEST]
    test_scores = probe.score(features[test_rows])
    test_qids = [str(q) for q in np.asarray(cache.question_ids)[test_rows]]
    if test_qids != list(committed.question_ids):
        raise SystemExit(
            "the test split derived here is not the committed one: question ids "
            "differ. The split moved, and every comparison against a Phase 0 "
            "number would be meaningless."
        )
    if not np.array_equal(test_scores, np.asarray(committed.scores, dtype=float)):
        worst = float(np.abs(test_scores - np.asarray(committed.scores)).max())
        raise SystemExit(
            f"the probe fit here does not reproduce the committed test-split "
            f"scores (max abs diff {worst:g}). It is therefore not the "
            "pipeline's probe, and nothing certified from it would describe the "
            "shipped system. Stopping rather than emitting a plausible number."
        )
    _LOG.info(
        "integrity check passed: %d test-split scores reproduce bit-identically",
        len(test_scores),
    )

    # --- freeze the validation split ---------------------------------------
    val_rows = splits[VALIDATION]
    val_scores = probe.score(features[val_rows])
    val_labels = np.asarray(cache.labels)[val_rows]
    val_qids = np.asarray(cache.question_ids)[val_rows]
    shipped_threshold = committed.targets[0].threshold

    valsplit = ScoreSet(
        score_set_id=VALSPLIT_ID,
        detector_id=committed.detector_id,
        variant=VARIANT,
        eval_set_id=committed.eval_set_id,
        envelope_id=committed.envelope_id,
        labels=tuple(int(x) for x in val_labels.tolist()),
        scores=tuple(float(x) for x in val_scores.tolist()),
        question_ids=tuple(str(x) for x in val_qids.tolist()),
        targets=(
            ScoreTarget(
                artifact="results/fpr_sweep_oos/sweep.json",
                metrics_path="sweeps[0].points",
                threshold=shipped_threshold,
                operating_point_id=committed.targets[0].operating_point_id,
            ),
        ),
        note=(
            "VALIDATION-split scores from the probe fitted on triviaqa-600's "
            "train split. These certify thresholds; they are never scored for "
            "recall. Distinct from validation-T1-last_token.json, which holds "
            "TEST-split scores and is named for the run artifact it reproduces."
        ),
    )
    prov = provenance(config)
    write_score_set(valsplit, results / "scores" / f"{VALSPLIT_ID}.json", prov)
    _LOG.info(
        "froze %s: n=%d, %d negatives available to certify against",
        VALSPLIT_ID, valsplit.n, int((val_labels == 0).sum()),
    )

    # --- the out-of-sample sweep -------------------------------------------
    out_dir = results / "fpr_sweep_oos"
    out_dir.mkdir(parents=True, exist_ok=True)
    grid = fpr_grid(args.start, args.stop, args.step)
    sweep = sweep_fpr(
        config,
        committed,
        grid=grid,
        data_source="measured",
        certify_on=valsplit,
    )

    write_json_artifact(
        out_dir / "sweep.json",
        {
            "grid_spec": {
                "start": args.start, "stop": args.stop, "step": args.step,
                "targets": list(grid), "n_points": len(grid),
                "registered": "Phase 0 brief D2, unchanged",
            },
            "integrity": {
                "test_scores_reproduce_committed": True,
                "checked": (
                    "the probe fit here reproduces results/scores/"
                    f"validation-{VARIANT}.json bit-identically; "
                    "without that the certification would not describe the "
                    "shipped probe"
                ),
            },
            "sweeps": [sweep.to_payload()],
        },
        config,
    )
    (out_dir / "SWEEP.md").write_text(
        render_sweep(sweep, provenance=prov) + "\n", encoding="utf-8"
    )
    plot_fpr_sweep(
        sweep, out_dir / "sweep.png",
        config_hash=config.config_hash, git_commit=prov.get("git_commit"),
    )
    plot_fpr_frontier(
        sweep, out_dir / "frontier.png",
        config_hash=config.config_hash, git_commit=prov.get("git_commit"),
    )

    headline = sweep.headline
    _LOG.info("-- out-of-sample: certified on %s, measured on %s",
              sweep.certified_on_score_set_id, sweep.score_set_id)
    if headline is None:
        _LOG.info("   lift holds at NO target on the grid")
    else:
        _LOG.info(
            "   largest target where lift holds: %.2f  recall %.4f [%.4f, %.4f]  "
            "lift %.3f [%.3f, %.3f]",
            headline.target_fpr, headline.recall.value,
            headline.recall.ci_low, headline.recall.ci_high,
            headline.lift.value, headline.lift.ci_low, headline.lift.ci_high,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
