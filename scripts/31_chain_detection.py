"""The recheck chain's detection across breach sizes, cadences and change points.

``DECISIONS.md`` 196, pre-registered. Thin wrapper: parses arguments, calls
``controlplane.economics.detection_grid.run_grid``, writes one file. No logic.

Needs no data and no GPU. Writes ``results/chain_detection/grid.json``.

Usage:
    python scripts/31_chain_detection.py --config config.yaml
    python scripts/31_chain_detection.py --years 10 --out /tmp/x   # smoke only
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
from controlplane.economics.detection_grid import REGISTERED_YEARS, run_grid  # noqa: E402

_LOG = logging.getLogger("scripts.31_chain_detection")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--years", type=int, default=None,
                        help="simulated years per cell; anything but the registered count needs --out")
    parser.add_argument("--out", default=None, help="results directory override")
    args = parser.parse_args(argv)
    if args.years is not None and args.years != REGISTERED_YEARS and args.out is None:
        parser.error(f"--years {args.years} is not the {REGISTERED_YEARS} DECISIONS 196 registered; "
                     "pass --out so a smoke run cannot overwrite the result")

    setup_logging()
    config = load_config(args.config)
    set_seeds(config.seed)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir
    grid = run_grid(seed=config.seed, years=args.years)
    out = results / "chain_detection" / "grid.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json_artifact(out, grid, config)
    criteria = grid["criteria"]
    _LOG.info("V=%s P1=%s P2=%s P3=%s -> %s", criteria["V"]["all_pass"], criteria["P1"]["all_hold"],
              criteria["P2"]["all_hold"], criteria["P3"]["all_hold"], out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
