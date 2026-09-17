"""Compare five revocation rules across a simulated year of rechecks.

``DECISIONS.md`` 187, pre-registered. Thin wrapper: parses arguments, calls
``controlplane.economics.schedules.run_study``, writes one file. No logic.

Needs no data and no GPU: every figure is a simulated operating characteristic
of a decision rule under a known false-positive rate. Writes
``results/recheck_schedules/comparison.json``.

Usage:
    python scripts/29_recheck_schedules.py --config config.yaml
    python scripts/29_recheck_schedules.py --years 50 --out /tmp/x   # smoke only
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
from controlplane.economics.schedules import REGISTERED, run_study  # noqa: E402

_LOG = logging.getLogger("scripts.29_recheck_schedules")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument(
        "--years", type=int, default=None,
        help="simulated years per cell; default is the registered count. Anything "
             "else is a smoke run and is written somewhere other than results/",
    )
    parser.add_argument("--out", default=None, help="results directory override")
    args = parser.parse_args(argv)

    if args.years is not None and args.years != REGISTERED.years and args.out is None:
        parser.error(
            f"--years {args.years} is not the {REGISTERED.years} DECISIONS 187 "
            "registered; pass --out so a smoke run cannot overwrite the result"
        )

    setup_logging()
    config = load_config(args.config)
    set_seeds(config.seed)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir

    study = run_study(REGISTERED, seed=config.seed, years=args.years)
    out = results / "recheck_schedules" / "comparison.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json_artifact(out, study, config)

    primary = study["criteria"]["primary"]
    _LOG.info(
        "chosen=%s floor_met=%s eligible=%s -> %s",
        primary["chosen"], primary["floor_met"], primary["eligible"], out,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
