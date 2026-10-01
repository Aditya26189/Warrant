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
        help="false-positive budget, e.g. 0.05 for 'at most 5%% of clean items flagged'. "
             "The 95%% level holds for a budget chosen before looking at this "
             "file; a budget picked off --frontier is covered by the frontier's "
             "own adjusted rows, not by this command (DECISIONS 192)",
    )
    certify.add_argument(
        "--out", "-o", default=None,
        help="write the JSON record here (default: alongside the input, as <name>.warrant.json)",
    )
    certify.add_argument(
        "--config", default=None,
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
    certify.add_argument(
        "--from-frontier", default=None, metavar="RECORD",
        help="the .frontier.json you picked --budget from; certifies at that "
             "frontier's row level so the pick still holds (DECISIONS 195)",
    )

    verify = sub.add_parser(
        "verify",
        help="recompute a certify record from its retained scored file",
        description=(
            "Check a certify record's effective-row digest and recompute its "
            "certificate. This verifies arithmetic, not the author's identity, "
            "timestamp or deployment. A frontier-selected record also needs "
            "its retained --frontier file."
        ),
    )
    verify.add_argument("--warrant", "-w", required=True,
                        help="the .warrant.json record written by certify")
    verify.add_argument("--input", "-i", required=True,
                        help="the retained scored CSV or JSONL used by certify")
    verify.add_argument("--frontier", default=None,
                        help="the retained frontier record, required for a selected budget")
    verify.add_argument("--config", default=None, help=argparse.SUPPRESS)

    verify_recheck = sub.add_parser(
        "verify-recheck",
        help="replay an ordinary recheck against retained fresh scored rows",
        description=(
            "Check an ordinary recheck's fresh-row binding and recompute its "
            "measurement. Chained records need retained chain history and are "
            "not verified by this command."
        ),
    )
    verify_recheck.add_argument("--record", required=True,
                                help="the .recheck.json record to replay")
    verify_recheck.add_argument("--warrant", "-w", required=True,
                                help="the exact retained certificate")
    verify_recheck.add_argument("--input", "-i", required=True,
                                help="the retained fresh scored CSV or JSONL")
    verify_recheck.add_argument("--certificate-input", default=None,
                                help="the original scored file, required if the recheck says VERIFIED")
    verify_recheck.add_argument("--certificate-frontier", default=None,
                                help="the retained frontier for a selected certificate")
    verify_recheck.add_argument("--config", default=None, help=argparse.SUPPRESS)

    verify_chain_recheck = sub.add_parser(
        "verify-chain-recheck",
        help="replay a retained linear chain prefix from its scored batches",
        description=(
            "Present every link from sequence 1 through the target, each with "
            "the fresh scored file it measured. Checks seals, links, rows and "
            "statistics. This verifies only the presented prefix, not the "
            "current head or any unpresented fork."
        ),
    )
    verify_chain_recheck.add_argument("--warrant", "-w", required=True,
                                      help="the exact retained certificate")
    verify_chain_recheck.add_argument(
        "--pair", nargs=2, action="append", required=True,
        metavar=("RECORD", "FRESH"),
        help="one chained record and its fresh scored file; repeat in sequence",
    )
    verify_chain_recheck.add_argument("--certificate-input", default=None,
                                      help="original scored file if any link claims source VERIFIED")
    verify_chain_recheck.add_argument("--certificate-frontier", default=None,
                                      help="retained frontier for a selected certificate")
    verify_chain_recheck.add_argument("--config", default=None, help=argparse.SUPPRESS)

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
    recheck.add_argument(
        "--certificate-input", metavar="FILE",
        help="replay the original certificate against its retained scored export "
             "before rechecking; a mismatch or missing evidence writes no record",
    )
    recheck.add_argument(
        "--certificate-frontier", metavar="RECORD",
        help="retained frontier record, required with --certificate-input when "
             "the certificate selected its budget from a frontier",
    )
    recheck.add_argument("--out", "-o", default=None, help="write the JSON record here")
    recheck.add_argument("--config", default=None,
                         help=argparse.SUPPRESS)
    recheck.add_argument("--quiet", "-q", action="store_true")
    recheck.add_argument(
        "--require-valid", action="store_true",
        help="exit non-zero when the warrant no longer holds (default: exits 0)",
    )
    chain = recheck.add_mutually_exclusive_group()
    chain.add_argument(
        "--horizon-labels", type=int, default=None, metavar="N",
        help="start a chain of rechecks whose sequential false-positive statistic "
             "falsely revokes a detector keeping its promise with probability at most "
             "alpha over N clean negatives; a revocation for a moved score "
             "distribution is a separate check, outside that bound. Declare N once, "
             "e.g. the negatives a year of rechecks will label (DECISIONS 193)",
    )
    chain.add_argument(
        "--since", default=None, metavar="RECORD",
        help="continue the chain in this earlier .recheck.json; keep every record",
    )
    recheck.add_argument(
        "--fork", action="store_true",
        help="continue from a record that is not the chain's latest, or start a new "
             "chain while one exists; the fork is recorded in the chain (DECISIONS 194). "
             "It cannot reopen a warrant whose chain was revoked: re-certify instead",
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
        "--power", type=float, default=None,
        help="probability one recheck catches a true breach of that size "
             "(default: validation.recheck_power, 0.80)",
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
    plan.add_argument("--config", default=None,
                      help=argparse.SUPPRESS)
    plan.add_argument("--quiet", "-q", action="store_true")
    from .release.cli import add_parser

    add_parser(sub)
    prepare = sub.add_parser(
        "prepare", help="map a flat scored export to a replayable local package",
    )
    prepare.add_argument("--input", "-i", required=True,
                         help="original flat .csv, .jsonl or .ndjson export")
    prepare.add_argument("--mapping", required=True,
                         help="JSON mapping declaring labels, score direction and groups")
    prepare.add_argument("--out", "-o", required=True,
                         help="new package directory; existing destinations are refused")
    prepared_verify = sub.add_parser(
        "verify-prepared", help="replay a prepared package from its original inputs",
    )
    prepared_verify.add_argument("--input", "-i", required=True)
    prepared_verify.add_argument("--mapping", required=True)
    prepared_verify.add_argument("--prepared", required=True,
                                 help="directory written by warrant prepare")
    chain = sub.add_parser(
        "chain",
        help="audit the records of a chain of rechecks",
        description=(
            "Reads the recheck records a chain produced and reports what they show: "
            "forks, restarts, missing links, edited states and links that do not "
            "extend their predecessor. It cannot recompute the statistics, which "
            "need the labelled files (DECISIONS 194)."
        ),
    )
    chain_sub = chain.add_subparsers(dest="chain_command", required=True)
    verify = chain_sub.add_parser("verify", help="verify a set of chained recheck records")
    verify.add_argument("records", nargs="+", help="every .recheck-NNNN.json you kept")
    verify.add_argument("--out", "-o", default=None,
                        help="write the JSON record here (default: chain-verification.json)")
    verify.add_argument("--quiet", "-q", action="store_true")
    verify.add_argument(
        "--require-clean", action="store_true",
        help="exit non-zero unless all records are sealed and all checks pass (default: inspection exits 0)",
    )
    return parser


def _chain(args: argparse.Namespace) -> int:
    """``warrant chain verify``: findings are a result, so they exit 0 (DECISIONS 194)."""
    from .config import load_customer_config as load_config, write_json_artifact
    from .intake.chain_verify import (
        RecordError, load_records, render_chain_verification, verify_chain_records,
    )

    try:
        records = load_records(args.records)
    except RecordError as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT
    verification = verify_chain_records(records)
    out = Path(args.out) if args.out else Path("chain-verification.json")
    write_json_artifact(out, verification.to_payload(), load_config())
    if not args.quiet:
        print(render_chain_verification(verification))
    print(f"  record written to {out}")
    if args.require_clean and not verification.clean:
        print(
            f"warrant: chain is not clean: {len(verification.findings)} finding(s), "
            f"{len(verification.unsealed)} unsealed record(s); "
            f"integrity={verification.integrity_status}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    return EXIT_OK


def _verify(args: argparse.Namespace) -> int:
    """Replay a scored-file certificate without changing retained evidence."""
    from .config import load_customer_config as load_config
    from .intake import load_scored_items
    from .intake.verify import load_evidence_record, verify_certification

    try:
        record = load_evidence_record(args.warrant)
        items = load_scored_items(args.input)
        frontier_record = (
            load_evidence_record(args.frontier) if args.frontier else None
        )
        result = verify_certification(
            record, items, load_config(args.config), frontier_record=frontier_record,
        )
    except (OSError, ValueError, TypeError) as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT
    print(f"{result.status}: {result.reason}")
    return EXIT_OK if result.verified else EXIT_ERROR


def _verify_recheck(args: argparse.Namespace) -> int:
    """Replay fresh-file arithmetic without changing retained evidence."""
    from .config import load_customer_config as load_config
    from .intake import load_scored_items
    from .intake.verify import load_evidence_record
    from .intake.verify_recheck import verify_recheck

    if args.certificate_frontier and not args.certificate_input:
        print("warrant: --certificate-frontier needs --certificate-input.",
              file=sys.stderr)
        return EXIT_BAD_INPUT
    try:
        result = verify_recheck(
            load_evidence_record(args.record), load_evidence_record(args.warrant),
            load_scored_items(args.input), load_config(args.config),
            certificate_items=(load_scored_items(args.certificate_input)
                               if args.certificate_input else None),
            frontier_record=(load_evidence_record(args.certificate_frontier)
                             if args.certificate_frontier else None),
        )
    except (OSError, ValueError, TypeError) as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT
    print(f"{result.status}: {result.reason}")
    return EXIT_OK if result.verified else EXIT_ERROR


def _verify_chain_recheck(args: argparse.Namespace) -> int:
    """Replay a retained linear prefix without touching its publication head."""
    from .config import load_customer_config as load_config
    from .intake import load_scored_items
    from .intake.verify import load_evidence_record
    from .intake.verify_chain_recheck import verify_chained_rechecks

    if args.certificate_frontier and not args.certificate_input:
        print("warrant: --certificate-frontier needs --certificate-input.",
              file=sys.stderr)
        return EXIT_BAD_INPUT
    try:
        pairs = [
            (record_path, load_evidence_record(record_path), load_scored_items(fresh_path))
            for record_path, fresh_path in args.pair
        ]
        result = verify_chained_rechecks(
            load_evidence_record(args.warrant), pairs, load_config(args.config),
            certificate_items=(load_scored_items(args.certificate_input)
                               if args.certificate_input else None),
            frontier_record=(load_evidence_record(args.certificate_frontier)
                             if args.certificate_frontier else None),
        )
    except (OSError, ValueError, TypeError) as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT
    print(f"{result.status}: {result.reason}")
    return EXIT_OK if result.verified else EXIT_ERROR


def _certify(args: argparse.Namespace) -> int:
    # Deferred on purpose; see the note at the top of this module.
    from .config import load_customer_config as load_config, write_json_artifact
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
        if args.from_frontier:
            print("warrant: --frontier and --from-frontier are two different steps; "
                  "run the frontier, pick a budget, then certify it --from-frontier.",
                  file=sys.stderr)
            return EXIT_BAD_INPUT
        return _frontier(args, config, items)
    if args.budget is None:
        print(
            "warrant: --budget is required unless you pass --frontier. Run with "
            "--frontier first if you do not yet know which budget to ask for.",
            file=sys.stderr,
        )
        return EXIT_BAD_INPUT

    import dataclasses
    import json
    import math

    from .intake.certify import input_sha256

    source = Path(args.input)
    digest = input_sha256(items)
    selection = None
    notice = ""
    if args.from_frontier:
        # DECISIONS 195: certify a budget picked off a frontier at the level the
        # frontier held that row to. Every refusal happens before anything is
        # written.
        from .intake.chain import canonical_sha256
        from .intake.verify import FRONTIER_METRICS_NOTE

        record_path = Path(args.from_frontier)
        try:
            frontier_record = json.loads(record_path.read_text(encoding="utf-8"))
            rows = frontier_record["frontier"]
            grid = [float(row["budget_fpr"]) for row in rows]
            row_alphas = {float(row["row_alpha"]) for row in rows}
            family_alphas = {float(row["family_alpha"]) for row in rows}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"warrant: {record_path} is not a frontier record with row levels ({exc})",
                  file=sys.stderr)
            return EXIT_BAD_INPUT
        if frontier_record.get("input", {}).get("input_sha256") != digest:
            print(f"warrant: {record_path.name} was not produced from {source.name} "
                  "(its input_sha256 differs or is missing); a frontier certifies the "
                  "file it read and no other. Rerun --frontier on this file.",
                  file=sys.stderr)
            return EXIT_BAD_INPUT
        if not any(math.isclose(args.budget, b, rel_tol=0, abs_tol=1e-12) for b in grid):
            print(f"warrant: --budget {args.budget} is not on {record_path.name}'s grid "
                  f"{grid}; only a row the frontier certified can be picked off it.",
                  file=sys.stderr)
            return EXIT_BAD_INPUT
        if len(row_alphas) != 1 or len(family_alphas) != 1:
            print(f"warrant: {record_path.name} does not carry one row level", file=sys.stderr)
            return EXIT_BAD_INPUT
        # The digest binds the record to this file, not the record's numbers to
        # anything: an edited row_alpha, or a record cut down to the picked row,
        # would otherwise certify at the unadjusted level under a selection claim
        # (195 review). Recompute -- no bootstrap, so it is cheap -- and require
        # every row to reproduce. The levels used are the recomputed ones.
        from .intake import frontier as compute_frontier

        try:
            recomputed = compute_frontier(config, items)
        except ValueError as exc:
            print(f"warrant: {exc}", file=sys.stderr)
            return EXIT_BAD_INPUT
        expected = [
            (p.budget, p.certified, p.threshold, p.row_alpha, p.family_alpha)
            for p in recomputed
        ]
        found = [
            (float(row["budget_fpr"]), bool(row["certified"]), row.get("threshold"),
             float(row["row_alpha"]), float(row["family_alpha"]))
            for row in rows
        ]
        if found != expected:
            print(
                f"warrant: {record_path.name} does not reproduce from {source.name} "
                "under this configuration -- its budgets, certified rows, thresholds "
                "or levels differ from a frontier computed now. A record edited, "
                "truncated or produced under another configuration cannot be picked "
                "from; rerun --frontier.",
                file=sys.stderr,
            )
            return EXIT_BAD_INPUT
        selection = {
            "from_frontier": canonical_sha256(frontier_record),
            "grid": [p.budget for p in recomputed],
            "row_alpha": recomputed[0].row_alpha,
            "family_alpha": recomputed[0].family_alpha,
            "metrics_note": FRONTIER_METRICS_NOTE,
        }

    try:
        result = certify_items(
            config, items, budget=args.budget,
            alpha=selection["row_alpha"] if selection else None, selection=selection,
        )
    except ValueError as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    if selection is None:
        # The default is unchanged (195). A frontier record for this same file at
        # its default path is a sign a budget may have been picked off it: say so
        # and record it, change nothing else.
        sibling = source.with_suffix(source.suffix + ".frontier.json")
        try:
            present = (
                sibling.is_file()
                and json.loads(sibling.read_text(encoding="utf-8"))
                .get("input", {}).get("input_sha256") == digest
            )
        except (OSError, ValueError, AttributeError):
            present = False
        if present:
            result = dataclasses.replace(result, frontier_record_present=True)
            notice = (
                f"  notice: {sibling.name} was run on this file. If you picked this "
                "budget from it, certify with\n"
                f"          --from-frontier {sibling.name} so the warrant holds at the "
                "frontier's level (DECISIONS 195)."
            )

    out = Path(args.out) if args.out else source.with_suffix(source.suffix + ".warrant.json")
    write_json_artifact(out, result.to_payload(), config)

    if not args.quiet:
        print(render_summary(result))
    if notice:
        print(notice)
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
    from .intake.certify import input_sha256

    try:
        points = frontier(config, items)
    except ValueError as exc:
        # Unequal groups: the same input certify --budget refuses (DECISIONS 190).
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT
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
                "grouped": items.groups is not None,
                # The digest --from-frontier checks, on the release path's
                # convention (DECISIONS 195).
                "input_sha256": input_sha256(items),
            },
            "note": (
                "Every field is exact -- a count of this file or a "
                "Clopper-Pearson bound. Rates are estimated and are not here; "
                "they come from `certify --budget`, with a 95% interval. "
                "Rows are certified at row_alpha, the family level split across "
                "the grid, so all certified rows hold at once (DECISIONS 192)."
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


def _revoking_record(record_path: Path) -> str:
    """How to name the chain record that revoked a warrant (DECISIONS 210)."""
    from .intake.chain import head_path

    import json

    try:
        head = json.loads(head_path(record_path).read_text(encoding="utf-8"))
        sequence = int(head["sequence"])
    except (OSError, ValueError, KeyError, TypeError):
        return "its latest chained record"
    return f"record {sequence:04d}"


def _recheck(args: argparse.Namespace) -> int:
    # Deferred on purpose; see the note at the top of this module.
    import dataclasses

    from .config import load_customer_config as load_config, write_json_artifact
    from .intake import InputError, load_scored_items, recheck_items, render_recheck
    from .intake.certify import evidence_sha256
    from .intake.chain import canonical_sha256
    from .intake.verify import load_evidence_record, verify_certification
    from .model import EnvelopeFeature, WarrantStatus

    config = load_config(args.config)
    record_path = Path(args.warrant)
    if not record_path.is_file():
        print(f"warrant: no warrant record at {record_path}", file=sys.stderr)
        return EXIT_BAD_INPUT
    try:
        record = load_evidence_record(record_path)
    except (OSError, ValueError, TypeError) as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    if args.certificate_frontier and not args.certificate_input:
        print("warrant: --certificate-frontier needs --certificate-input.",
              file=sys.stderr)
        return EXIT_BAD_INPUT
    certificate_verification = "NOT_CHECKED"
    if args.certificate_input:
        try:
            original_items = load_scored_items(args.certificate_input)
            frontier_record = (
                load_evidence_record(args.certificate_frontier)
                if args.certificate_frontier else None
            )
            verification = verify_certification(
                record, original_items, config, frontier_record=frontier_record,
            )
        except (OSError, ValueError, TypeError) as exc:
            print(f"warrant: certificate evidence cannot be used: {exc}",
                  file=sys.stderr)
            return EXIT_BAD_INPUT
        if not verification.verified:
            print(f"warrant: certificate {verification.status}: {verification.reason}",
                  file=sys.stderr)
            return EXIT_BAD_INPUT
        certificate_verification = "VERIFIED"

    certification = record.get("certification")
    if certification is None:
        certification = {}
    if not isinstance(certification, dict):
        print("warrant: certification must contain a JSON object.", file=sys.stderr)
        return EXIT_BAD_INPUT
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
    if block is not None and not isinstance(block, dict):
        print("warrant: score_distribution must contain a JSON object.", file=sys.stderr)
        return EXIT_BAD_INPUT
    try:
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
    except (KeyError, TypeError, ValueError) as exc:
        print(f"warrant: invalid score_distribution: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    recorded_input = record.get("input")
    if recorded_input is None:
        recorded_input = {}
    if not isinstance(recorded_input, dict):
        print("warrant: input must contain a JSON object.", file=sys.stderr)
        return EXIT_BAD_INPUT

    try:
        items = load_scored_items(args.input)
    except InputError as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    # The promise and the test must be in one unit. A record certified on
    # clusters rechecked per item, or the reverse, compares two different
    # rates, and which one the user meant is not ours to guess (DECISIONS 188).
    recorded_grouped = recorded_input.get("grouped")
    file_grouped = items.groups is not None
    if recorded_grouped is not None and bool(recorded_grouped) != file_grouped:
        certified_as = "clusters" if recorded_grouped else "independent items"
        given_as = "clusters" if file_grouped else "independent items"
        print(
            f"warrant: {record_path.name} was certified on {certified_as}, and "
            f"{Path(args.input).name} gives {given_as}. The promise and the recheck "
            "would be about different rates. Recheck with the same grouping the "
            "warrant was certified with.",
            file=sys.stderr,
        )
        return EXIT_BAD_INPUT

    # The level the promise was certified at, not whatever config.yaml says
    # today; a record that predates carrying alpha falls back to the config.
    try:
        result = recheck_items(
            config, items, budget=budget, threshold=threshold, reference=reference,
            # The reference is built from every score in the certified file, so
            # its size is that record's input.n. The PSI null is simulated at it
            # rather than at this file's size (DECISIONS 209).
            reference_n=recorded_input.get("n"),
            alpha=record.get("alpha"),
        )
    except ValueError as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT

    result = dataclasses.replace(
        result, warrant_sha256=canonical_sha256(record),
        certificate_verification=certificate_verification,
        evidence_sha256=evidence_sha256(items),
    )

    # A chain's parent/head checks and publication share one OS lock (206).
    # Ordinary rechecks retain their existing independent-file behavior.
    fed = None
    source = Path(args.input)
    if args.horizon_labels is None and args.since is None:
        # Unchained, and the sidecar may already say the chain revoked this
        # warrant. The measurement stands; the status is the lifecycle, so a
        # caller reading `status` is not told the warrant is live (210).
        from .intake.chain import ChainError, read_head_status
        from .intake.recheck import apply_revoked_chain_head

        try:
            head_status = read_head_status(record_path)
        except ChainError as exc:
            print(f"warrant: {exc}", file=sys.stderr)
            return EXIT_BAD_INPUT
        if head_status == "REVOKED":
            result = apply_revoked_chain_head(result, _revoking_record(record_path))
    if args.horizon_labels is not None or args.since is not None:
        from .intake.chain import ChainError
        from .intake.chain_publication import publish_chained_recheck

        try:
            result, fed, out = publish_chained_recheck(
                config, items, record, record_path, result,
                horizon_units=args.horizon_labels,
                since=Path(args.since) if args.since is not None else None,
                fork=args.fork, output=Path(args.out) if args.out else None,
                input_path=source,
            )
        except FileExistsError as exc:
            print(
                f"warrant: {exc}. A chained recheck never writes over a record: "
                "each link is evidence the next depends on. Choose another --out.",
                file=sys.stderr,
            )
            return EXIT_BAD_INPUT
        except (ChainError, ValueError, OSError) as exc:
            print(f"warrant: {exc}", file=sys.stderr)
            return EXIT_BAD_INPUT
    else:
        if args.fork:
            print("warrant: --fork only applies to a chained recheck (--since or "
                  "--horizon-labels).", file=sys.stderr)
            return EXIT_BAD_INPUT
        out = Path(args.out) if args.out else source.with_suffix(source.suffix + ".recheck.json")
        payload = {**result.to_payload(), "chain": None}
        write_json_artifact(out, payload, config)
    if not args.quiet:
        print(render_recheck(result, chain=fed))
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

    from .config import load_customer_config as load_config, write_json_artifact
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
            power=args.power if args.power is not None else config.validation.recheck_power,
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
    from .config import ConfigError

    try:
        if args.command in ("prepare", "verify-prepared"):
            from .intake.contract import InputError
            from .intake.prepare import prepare_export, verify_prepared

            try:
                if args.command == "prepare":
                    directory = prepare_export(args.input, args.mapping, args.out)
                    print(f"PREPARED {directory}")
                    return EXIT_OK
                if verify_prepared(args.input, args.mapping, args.prepared):
                    print("VERIFIED: prepared package matches retained inputs")
                    return EXIT_OK
                print("MISMATCH: prepared package differs from retained inputs")
                return 1
            except (InputError, OSError, ValueError) as exc:
                print(f"warrant: {exc}", file=sys.stderr)
                return EXIT_BAD_INPUT
        if args.command == "certify":
            return _certify(args)
        if args.command == "verify":
            return _verify(args)
        if args.command == "verify-recheck":
            return _verify_recheck(args)
        if args.command == "verify-chain-recheck":
            return _verify_chain_recheck(args)
        if args.command == "recheck":
            return _recheck(args)
        if args.command == "plan":
            return _plan(args)
        if args.command == "chain":
            return _chain(args)
        if args.command == "release":
            from .release.cli import run

            return run(args)
        raise AssertionError(f"unreachable: unhandled command {args.command!r}")
    except ConfigError as exc:
        print(f"warrant: {exc}", file=sys.stderr)
        return EXIT_BAD_INPUT


if __name__ == "__main__":
    raise SystemExit(main())
