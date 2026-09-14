"""Measure the frontier as a selection device. ``DECISIONS.md`` 192, pre-registered.

Thin wrapper: parses arguments, calls
``controlplane.intake.selection.run_study``, writes one file. No logic.

Needs no data and no GPU: every figure is an operating characteristic of the
certification rule under uniform negatives, and of one pick rule under a stated
ROC. Writes ``results/frontier_selection/selection.json``.

Usage:
    python scripts/30_frontier_selection.py --config config.yaml
    python scripts/30_frontier_selection.py --replicates 200 --crosscheck-replicates 5 --out /tmp/x   # smoke only
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.config import load_config, set_seeds, setup_logging, write_json_artifact  # noqa: E402
from controlplane.intake.selection import REGISTERED, run_study  # noqa: E402

_LOG = logging.getLogger("scripts.30_frontier_selection")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--replicates", type=int, default=None,
                        help="replicates per cell; anything but the registered count is a smoke run")
    parser.add_argument("--crosscheck-replicates", type=int, default=None,
                        help="files certified in the cross-check; same rule")
    parser.add_argument("--out", default=None, help="results directory override")
    args = parser.parse_args(argv)

    smoke = (
        (args.replicates is not None and args.replicates != REGISTERED.replicates)
        or (args.crosscheck_replicates is not None
            and args.crosscheck_replicates != REGISTERED.crosscheck_replicates)
    )
    if smoke and args.out is None:
        parser.error(
            "a replicate count other than the one DECISIONS 192 registered is a "
            "smoke run; pass --out so it cannot overwrite the result"
        )

    setup_logging()
    config = load_config(args.config)
    set_seeds(config.seed)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir

    study = run_study(REGISTERED, seed=config.seed, replicates=args.replicates,
                      crosscheck_replicates=args.crosscheck_replicates)
    out = results / "frontier_selection" / "selection.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json_artifact(out, study, config)

    criteria = study["criteria"]
    _LOG.info(
        "M3 sanity %s (crosscheck agrees: %s); M1 material %s at worst R1 %.4f; wrote %s",
        criteria["M3_sanity"]["passes"], criteria["M3_sanity"]["crosscheck_agrees"],
        criteria["M1_material"]["material"],
        criteria["M1_material"]["worst_r1_miscoverage_given_pick"], out,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
