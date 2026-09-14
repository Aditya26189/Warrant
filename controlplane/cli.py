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
        "--frontier", action="store_true",
        help=(
            "show every budget's exact counts instead of certifying one. "
            "Costs no bootstrap, so it answers in a second rather than two "
            "minutes; rates with intervals come from --budget."
        ),
    )
    certify.add_argument(
        "--budget", "-b", type=float, default=None,
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

    recheck = sub.add_parser(
        "recheck",
        help="is a warrant issued earlier still true on new data?",
        description=(
            "Takes a warrant record and a fresh file of the same shape, and "
            "answers whether the promise still holds. Two failure modes, "
            "reported separately: the false-positive bound can break, or the "
            "score distribution can move far enough that the old measurement no "
            "longer describes your traffic."
        ),
    )
    recheck.add_argument(
        "--warrant", "-w", required=True,
        help="the .warrant.json record produced by an earlier certify",
    )
    recheck.add_argument(
        "--input", "-i", required=True,
        help="the new .csv or .jsonl, same three columns",
    )
    recheck.add_argument("--out", "-o", default=None, help="write the JSON record here")
    recheck.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"),
                         help=argparse.SUPPRESS)
    recheck.add_argument("--quiet", "-q", action="store_true")
    recheck.add_argument(
        "--require-valid", action="store_true",
        help="exit non-zero when the warrant no longer holds (default: exits 0)",
    )

    plan = sub.add_parser(
        "plan",
        help="what it costs to keep a warrant true",
        description=(
            "A warrant is a claim about now. Keeping it true means re-testing "
            "it, and re-testing costs labels. This says how many clean "
            "negatives one recheck needs to catch a breach of the size you "
            "name, how many items you must label to get them, and what a year "
            "of that costs at each of several cadences. It recommends no "
            "cadence: how often to recheck depends on how fast your inputs "
            "move, which is the thing you do not know."
        ),
    )
    plan.add_argument(
        "--warrant", "-w", default=None,
        help="a .warrant.json record; takes the budget and alpha from it "
             "rather than having you retype them",
    )
    plan.add_argument(
        "--budget", "-b", type=float, default=None,
        help="the certified false-positive budget (not needed with --warrant)",
    )
    plan.add_argument(
        "--catch", type=float, default=None,
        help="the false-positive rate you want to be able to catch, absolute",
    )
    plan.add_argument(
        "--catch-multiple", type=float, default=1.5,
        help="or as a multiple of the budget (default: 1.5, the same reference "
             "point `recheck` reports its own detection floor against)",
    )
    plan.add_argument(
        "--negative-share", type=float, default=None,
        help="REQUIRED: the fraction of YOUR traffic that is truly negative. "
             "Deliberately not taken from the warrant record -- see below",
    )
    plan.add_argument(
        "--minutes-per-label", type=float, default=None,
        help="optional; without it the plan reports counts and no hours",
    )
    plan.add_argument(
        "--cost-per-hour", type=float, default=None,
        help="optional; without it the plan reports hours and no money",
    )
    plan.add_argument("--currency", default="", help="label only, e.g. 'INR '")
    plan.add_argument("--out", "-o", default=None, help="write the JSON record here")
    plan.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"),
                      help=argparse.SUPPRESS)
    plan.add_argument("--quiet", "-q", action="store_true")
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

    if args.frontier:
        return _frontier(args, config, items)
    if args.budget is None:
        print(
            "warrant: --budget is required unless you pass --frontier. Run with "
            "--frontier first if you do not yet know which budget to ask for.",
            file=sys.stderr,
        )
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


def _frontier(args: argparse.Namespace, config, items) -> int:
    """Every budget's exact counts, so a person can choose one."""
    from .config import write_json_artifact
    from .intake import frontier, render_frontier

    points = frontier(config, items)
    source = Path(args.input)
    out = (
        Path(args.out)
        if args.out
        else source.with_suffix(source.suffix + ".frontier.json")
    )
    write_json_artifact(
        out,
        {
            "input": {
                "source": items.source, "n": items.n,
                "n_positive": items.n_positive, "n_negative": items.n_negative,
            },
            "note": (
                "Every field is exact -- a count of this file or a "
                "Clopper-Pearson bound. Rates are estimated and are not here; "
                "they come from `certify --budget`, with a 95% interval."
            ),
            "frontier": [p.to_payload() for p in points],
        },
        config,
    )
    if not args.quiet:
        print(render_frontier(
            points, n_positive=items.n_positive, n_negative=items.n_negative
        ))
    print(f"  record written to {out}")
    return EXIT_OK


def _recheck(args: argparse.Namespace) -> int:
    # Deferred on purpose; see the note at the top of this module.
    import json

    from .config import load_config, write_json_artifact
    from .intake import InputError, load_scored_items, recheck_items, render_recheck
    from .model import EnvelopeFeature, WarrantStatus

    config = load_config(args.config)
    record_path = Path(args.warrant)
    if not record_path.is_file():
        print(f"warrant: no warrant record at {record_path}", file=sys.stderr)
        return EXIT_BAD_INPUT
    record = json.loads(record_path.read_text(encoding="utf-8"))

    certification = record.get("certification") or {}
    threshold = certification.get("threshold")
    budget = record.get("budget_fpr")
    if threshold is None or budget is None:
        print(
            f"warrant: {record_path.name} carries no certified threshold, so "
            "there is no promise to re-test. A REFUSED warrant has nothing to "
            "recheck -- certify at a budget the evidence supports first.",
            file=sys.stderr,
        )
        return EXIT_BAD_INPUT

    block = record.get("score_distribution")
    reference = (
        EnvelopeFeature(
            name=block["name"],
            bin_edges=tuple(block["bin_edges"]),
            bin_probabilities=tuple(block["bin_probabilities"]),
            mean=block["mean"],
            std=block["std"],
        )
        if block
        else None
    )

    try:
        items = load_scored_items(args.input)
    except InputError as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    # The level the promise was certified at, not whatever config.yaml says
    # today; a record that predates carrying alpha falls back to the config.
    result = recheck_items(
        config, items, budget=budget, threshold=threshold, reference=reference,
        alpha=record.get("alpha"),
    )

    source = Path(args.input)
    out = Path(args.out) if args.out else source.with_suffix(source.suffix + ".recheck.json")
    write_json_artifact(out, result.to_payload(), config)
    if not args.quiet:
        print(render_recheck(result))
    print(f"  record written to {out}")

    if args.require_valid and result.status is not WarrantStatus.VALID:
        print(
            f"warrant: {result.status.value} -- {result.reason}", file=sys.stderr
        )
        return EXIT_ERROR
    return EXIT_OK


def _plan(args: argparse.Namespace) -> int:
    """The price list. Deferred imports, as everywhere else in this module."""
    import json
    import math

    from .config import load_config, write_json_artifact
    from .economics.sizing import monitoring_plan
    from .intake import render_plan

    config = load_config(args.config)
    # The same place `recheck` takes it from, so a planned sample size and a
    # measured verdict are the same test at the same level.
    alpha = 1.0 - config.validation.ci

    budget = args.budget
    if args.warrant:
        record_path = Path(args.warrant)
        if not record_path.is_file():
            print(f"warrant: no such record: {record_path}", file=sys.stderr)
            return EXIT_BAD_INPUT
        record = json.loads(record_path.read_text(encoding="utf-8"))
        # `budget_fpr` is the key `certify` writes. This read `budget` until
        # DECISIONS 182, so every real record was reported as carrying none.
        recorded = record.get("budget_fpr")
        if recorded is None:
            print(
                f"warrant: {record_path.name} carries no budget_fpr, so it is not "
                "a certify record and there is no budget to plan against.",
                file=sys.stderr,
            )
            return EXIT_BAD_INPUT
        if record.get("status") == "REFUSED":
            print(
                f"warrant: {record_path.name} is a REFUSED warrant. Nothing was "
                "promised, so there is nothing to keep true. To price monitoring "
                "at a budget you have not certified, pass --budget without "
                "--warrant.",
                file=sys.stderr,
            )
            return EXIT_BAD_INPUT
        # Two sources for one number: refuse rather than pick. Either precedence
        # silently prices a budget the user did not mean.
        if budget is not None and not math.isclose(budget, recorded, rel_tol=0, abs_tol=1e-12):
            print(
                f"warrant: --budget {budget} disagrees with the {recorded} "
                f"{record_path.name} was certified at. Pass one or the other.",
                file=sys.stderr,
            )
            return EXIT_BAD_INPUT
        budget = recorded
        alpha = record.get("alpha", alpha)
    if budget is None:
        print(
            "warrant: give --budget, or --warrant pointing at a record that "
            "carries one.",
            file=sys.stderr,
        )
        return EXIT_BAD_INPUT

    # Not defaulted, and not read off the warrant record. The record knows the
    # class balance of the FILE that was certified, which describes an eval set.
    # Production traffic is a different distribution, and quoting one for the
    # other is the scenario-mixing error this project treats as the most
    # damaging one available. So the number has to be asserted by the person who
    # knows it.
    if args.negative_share is None:
        print(
            "warrant: --negative-share is required. It is the fraction of your "
            "traffic that is truly negative, and it turns 'negatives needed' "
            "into 'items to label'.\n"
            "It is NOT taken from the warrant record on purpose: that record "
            "knows the class balance of the file you certified, which describes "
            "your eval set and not your traffic. Using one for the other is how "
            "a plan comes out confidently wrong.",
            file=sys.stderr,
        )
        return EXIT_BAD_INPUT

    breach = args.catch if args.catch is not None else budget * args.catch_multiple
    try:
        result = monitoring_plan(
            budget=budget,
            breach_rate=breach,
            alpha=alpha,
            negative_share=args.negative_share,
            minutes_per_label=args.minutes_per_label,
            cost_per_hour=args.cost_per_hour,
            currency=args.currency,
        )
    except ValueError as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    out = Path(args.out) if args.out else Path("warrant-plan.json")
    write_json_artifact(out, result.to_payload(), config)

    if not args.quiet:
        print(render_plan(result))
    print(f"  record written to {out}")
    # A refused plan is a result, the same way a refused certification is.
    return EXIT_OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Returns a process exit code rather than raising."""
    args = build_parser().parse_args(argv)
    if args.command == "certify":
        return _certify(args)
    if args.command == "recheck":
        return _recheck(args)
    if args.command == "plan":
        return _plan(args)
    raise AssertionError(f"unreachable: unhandled command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
