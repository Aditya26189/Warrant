"""Run the documentation evidence audit; all logic lives in controlplane."""

from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from controlplane.report.documentation_audit import (  # noqa: E402
    check_links,
    documentation_pages,
    generated_reference_differences,
    reference_pages,
    collect_audit,
    write_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, help="new receipt directory; requires clean source"
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="render claim pages from the retained receipt",
    )
    parser.add_argument(
        "--links", action="store_true", help="check handbook and paper repository links"
    )
    parser.add_argument(
        "--render-references",
        action="store_true",
        help="regenerate all four declared reference pages",
    )
    parser.add_argument(
        "--check-generated",
        action="store_true",
        help="refuse missing or stale generated reference pages",
    )
    parser.add_argument(
        "--links-all",
        action="store_true",
        help="also check root, specialist, research and phase guides",
    )
    args = parser.parse_args()
    if args.render_references or args.render:
        pages = reference_pages(ROOT)
        names = pages if args.render_references else ("claims.md", "claim-families.md")
        for name in names:
            (ROOT / "docs/handbook" / name).write_bytes(pages[name].encode("utf-8"))
    if args.check_generated:
        differences = generated_reference_differences(ROOT)
        if differences:
            print("\n".join(differences))
            return 1
        print("All four generated reference pages match their declared sources.")
    report = write_audit(ROOT, args.out) if args.out else collect_audit(ROOT)
    print(report["summary"])
    if args.links or args.links_all:
        pages = documentation_pages(ROOT, include_specialist=args.links_all)
        broken = check_links(ROOT, pages)
        if broken:
            print("\n".join(broken))
            return 1
        print(f"Repository links checked across {len(pages)} pages.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
