"""The project's own measured certificates under label error.

``DECISIONS.md`` 199, pre-registered. Thin wrapper: parses arguments, calls
``controlplane.validation.label_error.run_study``, writes one file. No logic.

Reads the frozen score sets, ``evalsets/triviaqa-600.json`` and
``results/fpr_sweep/sweep.json``. Needs no GPU. Writes
``results/label_sensitivity/triviaqa.json``.

Usage:
    python scripts/32_label_sensitivity.py --config config.yaml
    python scripts/32_label_sensitivity.py --budgets 0.05 --out /tmp/x   # smoke only
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
from controlplane.validation.label_error import REGISTERED_BUDGETS, run_study  # noqa: E402

_LOG = logging.getLogger("scripts.32_label_sensitivity")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--budgets", type=float, nargs="+", default=None,
                        help="a subset of the grid; anything but the registered grid needs --out")
    parser.add_argument("--out", default=None, help="results directory override")
    args = parser.parse_args(argv)
    budgets = tuple(args.budgets) if args.budgets else REGISTERED_BUDGETS
    if budgets != REGISTERED_BUDGETS and args.out is None:
        parser.error("a budget subset is not the grid DECISIONS 199 registered; pass --out so a "
                     "smoke run cannot overwrite the result")

    setup_logging()
    config = load_config(args.config)
    set_seeds(config.seed)
    results_root = PROJECT_ROOT / config.paths.results_dir
    study = run_study(
        config,
        scores_dir=results_root / "scores",
        evalset_path=PROJECT_ROOT / "evalsets" / "triviaqa-600.json",
        sweep_path=results_root / "fpr_sweep" / "sweep.json",
        budgets=budgets,
    )
    out = (Path(args.out) if args.out else results_root) / "label_sensitivity" / "triviaqa.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json_artifact(out, study, config)
    criteria = study["criteria"]
    _LOG.info("C0=%s P1=%s P2=%s rows=%s -> %s", criteria["C0"]["holds"], criteria["P1"]["holds"],
              criteria["P2"]["holds"], criteria["reported"]["certified_rows"], out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
