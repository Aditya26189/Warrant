"""Preprint entry point; reusable behavior lives in controlplane."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from controlplane.report.technical_paper import (  # noqa: E402
    build_preprint,
    package_preprint,
    validate_sources,
    write_generated,
    zenodo_metadata,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generate", action="store_true", help="render retained numeric/author macros"
    )
    parser.add_argument(
        "--check", action="store_true", help="check generated values and citations"
    )
    parser.add_argument(
        "--engine", type=Path, help="path to the declared Tectonic executable"
    )
    parser.add_argument(
        "--out", type=Path, help="new PDF build directory; source must be committed"
    )
    parser.add_argument(
        "--package-out", type=Path, help="new local Zenodo package directory; no upload"
    )
    parser.add_argument(
        "--metadata", action="store_true", help="print prepared deposit fields"
    )
    args = parser.parse_args()
    if args.generate:
        write_generated(ROOT)
    if args.check:
        errors = validate_sources(ROOT)
        if errors:
            print("\n".join(errors))
            return 1
        print("Preprint sources, generated numbers and bibliography match.")
    if args.out:
        if args.engine is None:
            parser.error("--out requires --engine")
        print(build_preprint(ROOT, args.out.resolve(), args.engine.resolve()))
    if args.package_out:
        print(package_preprint(ROOT, args.package_out.resolve()))
    if args.metadata:
        print(json.dumps(zenodo_metadata(ROOT), indent=2))
    if not any((args.generate, args.check, args.out, args.package_out, args.metadata)):
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
