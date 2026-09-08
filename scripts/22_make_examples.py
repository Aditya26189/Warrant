"""Generate the two example input files. Seeded, so they are reproducible.

Phase 2, D24. A stranger's first two runs should show both outcomes, and the
refusal is the more important one — it is the product's whole proposition in one
command.

These files are **synthetic demonstration data**. They describe a generator
written here, not any detector and not any language model, and `examples/README.md`
says so in its first line. Nothing derived from them belongs in the claim table.

Thin wrapper: parses arguments, calls ``controlplane/``, writes files. No logic
(``CLAUDE.md``) — beyond the draw itself, which is what the script is for.

Usage:
    python scripts/22_make_examples.py
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.config import load_config, set_seeds, setup_logging

_LOG = logging.getLogger("scripts.22_make_examples")

#: Enough negatives to certify a 5% budget (which needs 59 clean units) with
#: room to spare, and a detector that genuinely separates.
CERTIFIES = {"n": 400, "base_rate": 0.25, "separation": 1.9, "seed_offset": 0}

#: Deliberately small. A 1% budget needs 299 clean units; this has nowhere near
#: that, and no threshold on it can be certified at that budget however good the
#: detector is. That is the point of the file.
REFUSES = {"n": 60, "base_rate": 0.30, "separation": 1.9, "seed_offset": 1}


def _draw(spec: dict, seed: int) -> list[dict[str, object]]:
    """One scored set: a separable detector over a labelled sample."""
    rng = np.random.default_rng(seed + spec["seed_offset"])
    n = spec["n"]
    labels = (rng.random(n) < spec["base_rate"]).astype(int)
    raw = rng.normal(0.0, 1.0, n) + spec["separation"] * labels
    scores = 1.0 / (1.0 + np.exp(-raw))
    return [
        {
            "id": f"req_{i:05d}",
            "label": int(labels[i]),
            "score": round(float(scores[i]), 6),
            # A passthrough column: carried into nothing, used by nothing, and
            # present so the contract's "arbitrary extra columns" clause is
            # demonstrated rather than only documented.
            "captured_at": f"2026-09-{1 + (i % 28):02d}T12:00:00Z",
        }
        for i in range(n)
    ]


def _write(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    positives = sum(1 for r in rows if r["label"] == 1)
    _LOG.info(
        "wrote %s: %d items, %d positive, %d negative",
        path, len(rows), positives, len(rows) - positives,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--out", default=str(PROJECT_ROOT / "examples"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)
    set_seeds(config.seed)
    out = Path(args.out)

    _write(_draw(CERTIFIES, config.seed), out / "certifies.csv")
    _write(_draw(REFUSES, config.seed), out / "refuses.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
