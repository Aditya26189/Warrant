"""What calibration deviation is detectable at the n we have, and at what n.

Phase 1, T3, the half that needs no GPU. D15 asks for the smallest reliably
detectable calibration deviation. That is a binomial power question about the
flag rate, and it is answerable from the declared budgets alone — no scores, no
activations, no model.

The expansion D14 asks for is **not** here: the extracted corpus holds 1280
negatives against a target of 1441, so raising n needs activations for items
that do not exist (``DECISIONS.md`` 135).

Reuses ``calibration.n_to_detect_deviation`` rather than inverting it. The
smallest detectable tolerance at a given n is found by scanning tolerances and
taking the first whose requirement fits, so there is one implementation of the
power calculation and this script is not a second one.

Thin wrapper: parses arguments, calls ``controlplane/``, writes files. No logic
(``CLAUDE.md``).

Usage:
    python scripts/21_calibration_power.py --config config.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.config import load_config, setup_logging, write_json_artifact
from controlplane.validation.calibration import n_to_detect_deviation

_LOG = logging.getLogger("scripts.21_calibration_power")

#: Tolerances the table reports a required n for. 0.10 is D15's success bar and
#: 0.25 is `validation.calibration_tolerance`, the deviation this system
#: currently declares worth acting on.
REPORTED_TOLERANCES = (0.05, 0.10, 0.15, 0.20, 0.25, 0.50)

#: Resolution of the tolerance scan, in relative-deviation units. 0.001 is finer
#: than any decision anyone would make on the result.
SCAN_STEP = 0.001


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument(
        "--n-available", type=int, default=600,
        help="items per split available today; the test split is 600",
    )
    parser.add_argument("--out", default=None, help="results directory override")
    return parser.parse_args(argv)


def smallest_detectable(target: float, n_available: int) -> float | None:
    """The tightest relative deviation this ``n`` can resolve at ``target``.

    Returns None when no tolerance below 100% fits, which is the honest answer
    for a budget too tight to calibrate at this sample size — not a number.
    """
    for step in range(1, int(1.0 / SCAN_STEP)):
        tolerance = step * SCAN_STEP
        if n_to_detect_deviation(target, tolerance) <= n_available:
            return round(tolerance, 4)
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir
    out_dir = results / "calibration_power"
    out_dir.mkdir(parents=True, exist_ok=True)

    budgets = {
        name: profile.target_flag_rate for name, profile in config.profiles.items()
    }
    # The shipped operating point's budget is not a profile budget and is the
    # one the 1441 figure was derived from, so it is reported beside them.
    budgets["(shipped P-conservative)"] = 0.05

    rows = []
    for name, target in sorted(budgets.items(), key=lambda kv: kv[1]):
        detectable = smallest_detectable(target, args.n_available)
        rows.append(
            {
                "name": name,
                "target_flag_rate": target,
                "n_required": {
                    f"{t:.2f}": n_to_detect_deviation(target, t)
                    for t in REPORTED_TOLERANCES
                },
                "smallest_detectable_at_n_available": detectable,
                "meets_10_percent_bar": bool(
                    detectable is not None and detectable <= 0.10
                ),
            }
        )

    write_json_artifact(
        out_dir / "calibration_power.json",
        {
            "question": (
                "the smallest reliably detectable calibration deviation, at the n "
                "available today and at the n each tolerance would require "
                "(Phase 1 D15)"
            ),
            "n_available": args.n_available,
            "declared_tolerance": config.validation.calibration_tolerance,
            "success_bar": 0.10,
            "estimator": (
                "n = z^2 * p'(1-p') / (p*t)^2 with p' = p(1+t), z = 1.96; "
                "controlplane.validation.calibration.n_to_detect_deviation"
            ),
            "expansion_not_done": (
                "D14's n- >= 1441 needs activations for items that do not exist: "
                "the extracted corpus holds 1280 negatives in total. DECISIONS 135."
            ),
            "budgets": rows,
        },
        config,
    )

    lines = [
        "# Calibration power — what deviation is detectable, and at what n",
        "",
        f"At **n = {args.n_available}** per split. The estimator is the binomial "
        "requirement already used by `assess_calibration`; nothing here is a "
        "second implementation.",
        "",
        "| budget | smallest detectable at n | meets 10% bar | "
        + " | ".join(f"n for {t:.0%}" for t in REPORTED_TOLERANCES)
        + " |",
        "|---|---:|:--:|" + "---:|" * len(REPORTED_TOLERANCES),
    ]
    for row in rows:
        detectable = row["smallest_detectable_at_n_available"]
        lines.append(
            f"| `{row['name']}` ({row['target_flag_rate']:.2f}) | "
            + (f"{detectable * 100:.1f}%" if detectable is not None else "not at this n")
            + f" | {'yes' if row['meets_10_percent_bar'] else 'no'} | "
            + " | ".join(
                f"{row['n_required'][f'{t:.2f}']}" for t in REPORTED_TOLERANCES
            )
            + " |"
        )
    lines += [
        "",
        "## What this says",
        "",
        "The requirement scales as `z^2 p'(1-p') / (p t)^2`. The numerator falls "
        "roughly linearly in the budget while the denominator falls as its "
        "square, so **halving a flag-rate budget roughly doubles the sample "
        "needed** at a fixed relative tolerance. A tight budget is intrinsically "
        "expensive to calibrate, and that is a property of the binomial rather "
        "than of this detector.",
        "",
        "The 1441 figure quoted for this phase is "
        f"`n_to_detect_deviation(0.05, 0.25)` = {n_to_detect_deviation(0.05, 0.25)}"
        " — the sample for a **25%** deviation at the shipped 5% budget. "
        f"Detecting **10%** there needs {n_to_detect_deviation(0.05, 0.10)}, which "
        "is more than three times the entire 2400-item corpus.",
        "",
        "The expansion itself is not done and needs a GPU: the extracted corpus "
        "holds 1280 negatives against D14's target of 1441. `DECISIONS.md` 135.",
        "",
    ]
    (out_dir / "CALIBRATION_POWER.md").write_text("\n".join(lines), encoding="utf-8")
    _LOG.info("wrote %s", out_dir / "CALIBRATION_POWER.md")

    for row in rows:
        detectable = row["smallest_detectable_at_n_available"]
        _LOG.info(
            "   %-26s budget %.2f -> detectable %s  (10%% bar needs n=%d)",
            row["name"], row["target_flag_rate"],
            f"{detectable * 100:.1f}%" if detectable is not None else "none at this n",
            row["n_required"]["0.10"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
