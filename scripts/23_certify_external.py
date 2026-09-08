"""Certify third-party detectors on public datasets. Phase 3, T2-T4.

Every detector runs at its documented default (D34) and every pairing is scored
on the standard grid against the standard criterion (D35), which is the same
grid and criterion this project's own detector is held to (D37).

Needs network: datasets and models are fetched at their pinned revisions rather
than redistributed. Nothing derived from them is written to disk beyond the
aggregates in ``results/external/<pairing>/``.

Thin wrapper: parses arguments, calls ``controlplane/``, writes files. No logic
(``CLAUDE.md``).

Usage:
    python scripts/23_certify_external.py --list
    python scripts/23_certify_external.py --pairing presidio-email_address
    python scripts/23_certify_external.py --all
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
from controlplane.external import PAIRINGS, pairing_ids, render_matrix, run_pairing
from controlplane.report.sweep import render_sweep

_LOG = logging.getLogger("scripts.23_certify_external")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--pairing", action="append", default=None,
                        help="pairing id, repeatable; see --list")
    parser.add_argument("--all", action="store_true", help="run every pairing")
    parser.add_argument("--list", action="store_true", help="list pairings and exit")
    parser.add_argument("--out", default=None, help="results directory override")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()

    if args.list:
        for name in pairing_ids():
            pairing = PAIRINGS[name]
            print(f"{name:26s} {pairing.detector.id} on {pairing.dataset.id}")
        return 0

    config = load_config(args.config)
    set_seeds(config.seed)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir

    selected = pairing_ids() if args.all else (args.pairing or [])
    if not selected:
        raise SystemExit("nothing to do: pass --pairing <id>, --all, or --list")
    unknown = [name for name in selected if name not in PAIRINGS]
    if unknown:
        raise SystemExit(f"unknown pairing(s) {unknown}; see --list")

    prov = provenance(config)
    for name in selected:
        _LOG.info("=== %s ===", name)
        sweep, payload = run_pairing(config, name)
        out_dir = results / "external" / name
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json_artifact(out_dir / "sweep.json", payload, config)
        (out_dir / "SWEEP.md").write_text(
            render_sweep(sweep, provenance=prov) + "\n", encoding="utf-8"
        )
        headline = sweep.headline
        if headline is None:
            _LOG.info("   lift holds at NO target on the grid")
        else:
            _LOG.info(
                "   holds to target %.2f: recall %.4f [%.4f, %.4f], lift %.3f",
                headline.target_fpr, headline.recall.value,
                headline.recall.ci_low, headline.recall.ci_high, headline.lift.value,
            )

    # Rendered from what is on disk, so the table cannot say something the
    # artifacts do not -- including rows written by an earlier invocation.
    matrix = results / "external" / "MATRIX.md"
    matrix.write_text(render_matrix(results, provenance=prov), encoding="utf-8")
    _LOG.info("wrote %s", matrix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
