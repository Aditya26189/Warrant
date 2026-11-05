"""Run the documentation evidence audit; all logic lives in controlplane."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from controlplane.report.documentation_audit import (  # noqa: E402
    check_links, collect_audit, read_json, render_claims, render_families, write_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="new receipt directory; requires clean source")
    parser.add_argument("--render", action="store_true", help="render claim pages from the retained receipt")
    parser.add_argument("--links", action="store_true", help="check handbook and paper repository links")
    args = parser.parse_args()
    if args.render:
        receipt = read_json(ROOT / "results/documentation_audit/20261105/audit.json")
        registry = read_json(ROOT / "docs/handbook/claim-families.json")
        for name, text in (("claims.md", render_claims(receipt, registry)),
                           ("claim-families.md", render_families(registry))):
            (ROOT / "docs/handbook" / name).write_bytes((text.rstrip() + "\n").encode())
    report = write_audit(ROOT, args.out) if args.out else collect_audit(ROOT)
    print(report["summary"])
    if args.links:
        pages = sorted((ROOT / "docs/handbook").rglob("*.md"))
        pages += sorted((ROOT / "paper").glob("*.md"))
        broken = check_links(ROOT, pages)
        if broken:
            print("\n".join(broken)); return 1
        print(f"Repository links checked across {len(pages)} pages.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
