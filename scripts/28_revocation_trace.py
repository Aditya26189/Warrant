"""Replay a real envelope shift against a real warrant, and record the revocation.

``DECISIONS.md`` 178. Thin wrapper: parses arguments, calls
``controlplane.demo.revocation_trace``, writes files. No logic.

Reads the ledger rebuilt by the measurement chain and the two extraction caches;
writes ``results/drift/revocation_trace.json``. The certificates it issues are
sealed into ``results/drift/revocation.db`` (gitignored), never into the matrix's
audit store. Refuses if the observed warrant has expired: run the chain first.

Usage:
    python scripts/28_revocation_trace.py --config config.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.config import load_config, set_seeds, setup_logging, write_json_artifact  # noqa: E402
from controlplane.demo.revocation_trace import (  # noqa: E402
    TraceError,
    build_replay,
    latest_warrant,
    run_revocation_trace,
)
from controlplane.evalsets import load_evalset  # noqa: E402
from controlplane.matrix import WarrantMatrix  # noqa: E402
from controlplane.model import utc_now  # noqa: E402
from controlplane.store import Ledger  # noqa: E402
from controlplane.validation.evalsets import ExtractionCache  # noqa: E402

_LOG = logging.getLogger("scripts.28_revocation_trace")

DETECTOR = "probe-qwen2.5-7b-instruct-T1-last_token"
SOURCE, LIVE = "triviaqa-600", "triviaqa-longctx-600"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--n-normal", type=int, default=400)
    parser.add_argument("--n-shift", type=int, default=400)
    parser.add_argument("--out", default=None, help="results directory override")
    args = parser.parse_args(argv)

    setup_logging()
    config = load_config(args.config)
    set_seeds(config.seed)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir
    evalsets = PROJECT_ROOT / config.paths.evalsets_dir

    source_set = load_evalset(evalsets / f"{SOURCE}.json")
    live_set = load_evalset(evalsets / f"{LIVE}.json")
    source_cache = ExtractionCache.load(
        PROJECT_ROOT / "results" / f"cache-{SOURCE}.npz", expected_hash=source_set.content_hash
    )
    live_cache = ExtractionCache.load(
        PROJECT_ROOT / "results" / f"cache-{LIVE}.npz", expected_hash=live_set.content_hash
    )

    audit = Ledger(
        PROJECT_ROOT / "results" / Path(config.store.path).name,
        retention_days=config.store.retention_days,
    )
    matrix = WarrantMatrix.from_ledger(audit)

    out_dir = results / "drift"
    out_dir.mkdir(parents=True, exist_ok=True)
    db = out_dir / "revocation.db"
    if db.exists():
        # A replay's certificates are a new chain per run. Moved aside, never
        # deleted: an audit record does not get quietly dropped.
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        db.rename(db.with_name(f"revocation.db.pre-{stamp}"))
    trace_ledger = Ledger(db, retention_days=config.store.retention_days)

    try:
        warrant = latest_warrant(audit, detector_id=DETECTOR, eval_set_id=SOURCE)
        replay = build_replay(
            normal_evalset=source_set,
            normal_cache=source_cache,
            shift_cache=live_cache,
            n_normal=args.n_normal,
            n_shift=args.n_shift,
            seed=config.seed,
        )
        payload = run_revocation_trace(
            config,
            warrant=warrant,
            replay=replay,
            matrix=matrix,
            profile_names=sorted(config.profiles),
            live_eval_set_id=LIVE,
            now=utc_now(),
            ledger=trace_ledger,
        )
    except TraceError as exc:
        print(f"REFUSED: {exc}")
        return 2

    path = write_json_artifact(out_dir / "revocation_trace.json", payload, config)
    _LOG.info("wrote %s", path)
    for name, criterion in payload["criteria"].items():
        print(f"  {'PASS' if criterion['passed'] else 'FAIL'}  {name}")
    for checkpoint in payload["checkpoints"]:
        print(
            f"  after {checkpoint['after_request']:>3}  window {checkpoint['window_normal']:>3} normal "
            f"/ {checkpoint['window_shift']:>3} shift  ->  {checkpoint['envelope_state']:<17} "
            f"{checkpoint['to_status']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
