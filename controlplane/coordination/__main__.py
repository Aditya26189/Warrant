"""Thin command-line interface for the local shared context board."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .board import KINDS, STATES, post, read_events, refresh, render_board


def main() -> int:
    """Read/post coordination messages without contacting another service."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    read = commands.add_parser("read")
    read.add_argument("--after", type=int, default=0)
    read.add_argument("--json", action="store_true")
    commands.add_parser("refresh")
    write = commands.add_parser("post")
    write.add_argument("--agent", required=True)
    write.add_argument("--to")
    write.add_argument("--kind", choices=KINDS, required=True)
    write.add_argument("--state", choices=STATES)
    write.add_argument("--paths", nargs="+")
    message = write.add_mutually_exclusive_group(required=True)
    message.add_argument("--message")
    message.add_argument("--message-file", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "post":
            text = args.message if args.message is not None else args.message_file.read_text(encoding="utf-8")
            event = post(args.root, agent=args.agent, kind=args.kind, message=text,
                         paths=args.paths, to=args.to, state=args.state)
            print(f"Posted {event['sequence']} by {event['agent']}; page: {args.root / 'SHARED_CONTEXT.md'}")
        elif args.command == "refresh":
            print(refresh(args.root))
        else:
            if args.after and not args.json:
                raise ValueError("read --after requires --json; the full page preserves current ownership")
            events = read_events(args.root, after=args.after)
            print(json.dumps(events, indent=2, ensure_ascii=False) if args.json else render_board(events))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"coordination: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
