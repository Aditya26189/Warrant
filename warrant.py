"""``warrant`` without installing anything: ``python warrant.py certify ...``

A shim, so the quickstart works on a fresh clone before any packaging step. The
command lives in :mod:`controlplane.cli`; this file exists only so a stranger
can run it by the product's name from the directory they just cloned into.

``pip install -e .`` gives the same thing as a real ``warrant`` command.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.cli import main  # noqa: E402  (path set up above)

if __name__ == "__main__":
    raise SystemExit(main())
