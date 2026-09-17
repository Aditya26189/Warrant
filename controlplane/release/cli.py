"""Thin release CLI: parsing and file IO, with no inference in the wrapper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Keep help cheap: numerical imports occur only after argument parsing."""
    release = subparsers.add_parser("release", help="register and verify scoped holdout evidence")
    commands = release.add_subparsers(dest="release_command", required=True)
    register = commands.add_parser("register", help="freeze criteria and disjoint holdout IDs")
    register.add_argument("--spec", required=True, help="release specification JSON")
    register.add_argument("--development-ids", required=True, help="one development question ID per line")
    register.add_argument("--holdout-ids", required=True, help="one unused holdout question ID per line")
    register.add_argument("--out", required=True, help="new contract JSON; existing files are never replaced")
    for name, help_text in (("evaluate", "measure the complete registered holdout once"),
                            ("verify", "recompute saved evidence and check its expiry")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--contract", required=True, help="registered release contract JSON")
        command.add_argument("--input", required=True, help="scored holdout CSV/JSONL: id,label,score")
        command.add_argument("--context", required=True, help="scorer's identity and scope JSON")
        command.add_argument("--require-valid", action="store_true", help="exit 1 unless current status is VALID")
        if name == "verify":
            command.add_argument("--evidence", help="saved evidence; default is beside the contract")


def run(args: argparse.Namespace) -> int:
    """Return 2 for invalid input, 0 for a result, or 1 for required validity."""
    from ..intake.contract import load_scored_items
    from .contract import (
        ReleaseContract, ReleaseSpec, read_document, read_ids, register, write_document,
    )
    from .evaluate import evaluate, seal_evaluation, verify_evaluation
    from .render import render_evaluation

    try:
        if args.release_command == "register":
            spec = ReleaseSpec.from_dict(read_document(Path(args.spec)))
            contract = register(spec, read_ids(Path(args.development_ids)), read_ids(Path(args.holdout_ids)))
            write_document(Path(args.out), contract.to_dict())
            print(f"Registered local contract: {args.out}")
            print("Retain this copy before evaluating. Registration is not a trusted timestamp.")
            return 0
        contract_path = Path(args.contract)
        contract = ReleaseContract.from_dict(read_document(contract_path))
        companion = contract_path.with_name(contract_path.stem + ".evaluation.json")
        context = read_document(Path(args.context))
        if args.release_command == "evaluate" and companion.exists():
            raise ValueError(f"evidence already exists at {companion}; use release verify")
        items = load_scored_items(args.input, require_both_classes=False)
        if args.release_command == "evaluate":
            record = seal_evaluation(evaluate(contract, items, context))
            write_document(companion, record)
            status = record["status"]
            evidence_path = companion
        else:
            evidence_path = Path(args.evidence) if args.evidence else companion
            record = read_document(evidence_path)
            status = verify_evaluation(record, contract, items, context)
        print(render_evaluation(record, status))
        print(f"Evidence: {evidence_path}")
        return 1 if args.require_valid and status != "VALID" else 0
    except (ValueError, OSError) as exc:
        print(f"warrant release: {exc}", file=sys.stderr)
        return 2
