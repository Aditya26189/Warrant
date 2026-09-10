"""``warrant`` — the command a customer runs.

One command, one artifact (Phase 2 D23). No interactive prompts, no
configuration file required, and **no network**: nothing here opens a socket,
and nothing about a customer's file leaves their machine.

Exit codes are the interface a script sees, and refusal is deliberately not an
error:

====  ==========================================================
 0    a warrant was issued, **or** a warrant was refused
 2    the input does not meet the contract
 1    something else went wrong
====  ==========================================================

A refusal exits 0 because it is a successful measurement with a negative result.
Exiting non-zero would make every CI pipeline treat "your detector cannot be
certified on this evidence" as a broken tool, which is exactly backwards — and
``--require-warrant`` is there for callers who genuinely want the other
behaviour.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

__all__ = ["build_parser", "main"]

# Nothing heavy is imported at module scope, and that is deliberate.
#
# `warrant certify --help` and every argument error must not pay for scipy.
# Importing the certification chain eagerly cost **2.83s** before a single
# argument was parsed, of which 1.39s was `scipy.stats` reached transitively
# through validation.warrant_stats. A command-line tool that takes three seconds
# to print its usage reads as research code whatever else is true of it.
#
# The imports therefore live inside `_certify`, which is the only place that
# needs them. `--help`, `--version` and a malformed argument now return in
# roughly a tenth of that.

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BAD_INPUT = 2


def _version() -> str:
    """The installed version, read without importing the package eagerly.

    A plain read of ``controlplane.__version__`` would be simpler and would drag
    the package import into ``--version``, which is the one command that should
    cost nothing.
    """
    from . import __version__

    return __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="warrant",
        description=(
            "Certify a detector against a false-positive budget, or refuse. "
            "Reads a CSV or JSONL of id,label,score. Nothing leaves your machine."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  warrant certify --input examples/certifies.csv --budget 0.05\n"
            "  warrant certify --input examples/refuses.csv   --budget 0.01\n"
            "\nthe input contract is three columns: id, label (0/1, 1 = the\n"
            "detector should fire), score (higher = more likely positive).\n"
            "see docs/INPUT.md.\n"
        ),
    )
    parser.add_argument(
        "--version", "-V", action="version",
        version=f"warrant {_version()}",
        help="print the version and exit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    certify = sub.add_parser(
        "certify",
        help="certify a detector from a file of scores and labels",
        description=(
            "Picks the lowest threshold whose Clopper-Pearson upper bound on "
            "your negatives clears the budget, then reports what the detector "
            "does there. Refuses when the evidence cannot support the budget."
        ),
    )
    certify.add_argument(
        "--input", "-i", required=True,
        help="path to a .csv or .jsonl with columns id, label, score",
    )
    certify.add_argument(
        "--budget", "-b", type=float, required=True,
        help="false-positive budget, e.g. 0.05 for 'at most 5%% of clean items flagged'",
    )
    certify.add_argument(
        "--out", "-o", default=None,
        help="write the JSON record here (default: alongside the input, as <name>.warrant.json)",
    )
    certify.add_argument(
        "--config", default=str(PROJECT_ROOT / "config.yaml"),
        help=argparse.SUPPRESS,  # the estimator settings; customers never set this
    )
    certify.add_argument(
        "--quiet", "-q", action="store_true",
        help="print only the JSON path, not the summary",
    )
    certify.add_argument(
        "--require-warrant", action="store_true",
        help="exit non-zero when the detector is REFUSED (default: refusal exits 0)",
    )
    return parser


def _certify(args: argparse.Namespace) -> int:
    # Deferred on purpose; see the note at the top of this module.
    from .config import load_config, write_json_artifact
    from .intake import (
        InputError,
        certify_items,
        load_scored_items,
        render_summary,
    )
    from .model import WarrantStatus

    config = load_config(args.config)
    try:
        items = load_scored_items(args.input)
    except InputError as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    try:
        result = certify_items(config, items, budget=args.budget)
    except ValueError as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    source = Path(args.input)
    out = Path(args.out) if args.out else source.with_suffix(source.suffix + ".warrant.json")
    write_json_artifact(out, result.to_payload(), config)

    if not args.quiet:
        print(render_summary(result))
    print(f"  record written to {out}")

    if args.require_warrant and result.status is not WarrantStatus.VALID:
        # The caller asked for a warrant and did not get one. If they also
        # suppressed the summary they would otherwise get a bare exit code and
        # no reason, which is the least useful thing a tool can do at the moment
        # it says no.
        print(
            f"warrant: {result.status.value} -- {result.reason}", file=sys.stderr
        )
        return EXIT_ERROR
    return EXIT_OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Returns a process exit code rather than raising."""
    args = build_parser().parse_args(argv)
    if args.command == "certify":
        return _certify(args)
    raise AssertionError(f"unreachable: unhandled command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
