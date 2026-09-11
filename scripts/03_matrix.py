"""Populate the warrant matrix across every envelope, and render it.

Runs the Phase 2 ablation once per activation-tier envelope and the text
validation once per text envelope, appends every warrant — issued *and* refused
— to the ledger, then builds the matrix from the ledger and renders it.

Built from the ledger rather than from the runs in memory, so the matrix and the
audit log cannot disagree. If a warrant is not in the log it is not in the
matrix, which is the property that makes the matrix evidence.

Thin wrapper: parses arguments, calls ``controlplane/``, writes files. No logic.

Usage:
    python scripts/03_matrix.py --config config.yaml
    python scripts/03_matrix.py --config config.yaml --smoke
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.config import (
    load_config,
    provenance,
    set_seeds,
    setup_logging,
    write_json_artifact,
)
from controlplane.detectors.pii_reference import ReferencePiiDetector
from controlplane.evalsets import (
    build_canary_pii,
    build_hard_negatives,
    build_hinglish_pii,
    build_longctx,
)
from controlplane.matrix import Profile, WarrantMatrix, route
from controlplane.report import render_results
from controlplane.report.price_list import price_list_sections  # noqa: E402
from controlplane.store import Ledger, RecordKind
from controlplane.validation.ablation import run_ablation
from controlplane.validation.synthetic import synthetic_cache, synthetic_evalset
from controlplane.validation.text_runner import validate_text_detector

_LOG = logging.getLogger("scripts.03_matrix")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument(
        "--smoke", action="store_true", help="tiny sizes, for the end-to-end check"
    )
    parser.add_argument("--out", default=None, help="results directory override")
    return parser.parse_args(argv)


def _preflight_ledger(ledger) -> None:
    """Refuse before doing any work if the ledger holds unreadable records.

    ``DECISIONS.md`` 110 made ``convention`` mandatory on every ESTIMATED
    metric. Warrant records written before it carry an ``auroc`` with no
    convention, and the model refuses to deserialise them -- correctly, because
    a two-sided 95% bound and a one-sided one are 23% apart at n=200 and an
    unlabelled one is neither.

    The consequence is that this script, which appends warrants and then
    rebuilds the matrix from the **whole** ledger, dies on the read-back.
    Without this check it dies after about two minutes of ablation work and
    after appending new records, so every attempt leaves the append-only ledger
    longer, and the failure arrives as a ``MetricError`` from inside
    deserialisation naming no record and suggesting no action.

    A clean clone is unaffected: the ledger is gitignored, so a fresh run builds
    one with no pre-110 records in it. This is a development-machine failure and
    the message says so, because the alternative is a reader concluding the
    script is broken for everyone.
    """
    from controlplane.model.metrics import MetricError

    unreadable: list[str] = []
    total = 0
    for record in ledger.query(kind=RecordKind.WARRANT):
        total += 1
        try:
            ledger.get_warrant(record.record_id)
        except (MetricError, ValueError, TypeError, KeyError) as exc:
            unreadable.append(f"{record.record_id}: {type(exc).__name__}: {exc}")
    if not unreadable:
        return

    sample = chr(10).join("    " + line for line in unreadable[:3])
    raise SystemExit(
        f"{chr(10)}REFUSED: {len(unreadable)} of {total} warrant records in this "
        f"ledger cannot be read by the current model.{chr(10)*2}"
        f"{sample}{chr(10)*2}"
        "This script rebuilds the matrix from the whole ledger, so it cannot run "
        "until every record loads. The usual cause is records written before "
        "DECISIONS.md 110 made `convention` mandatory on an ESTIMATED metric."
        f"{chr(10)*2}"
        "The ledger is gitignored, so a clean clone does not have this problem "
        "and a fresh run rebuilds it. On a development machine the remedy is to "
        "move the file aside rather than delete it -- it is an append-only audit "
        "record and the whole reason it exists is that nobody gets to quietly "
        "drop entries from it:"
        f"{chr(10)*2}"
        "    mv results/controlplane.db results/controlplane.db.pre-110"
        f"{chr(10)*2}"
        "Refused before the ablation runs and before any append, so this attempt "
        "left the ledger exactly as it found it. "
        f"DECISIONS.md 155.{chr(10)}"
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)
    set_seeds(config.seed)

    results_dir = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)

    n_items = 400 if args.smoke else 2400

    # -- activation-tier envelopes (synthetic fixtures until the GPU run) ----- #
    short = synthetic_evalset(
        eval_set_id="triviaqa-600-synthetic", n_items=n_items, base_rate=0.152,
        seed=config.seed, items_per_question=2, declare_splits=True,
    )
    long_ctx = synthetic_evalset(
        eval_set_id="triviaqa-longctx-600-synthetic", n_items=n_items, base_rate=0.152,
        seed=config.seed, items_per_question=2, declare_splits=True, long_context=True,
    )
    caches = {
        e.eval_set_id: synthetic_cache(
            e, seed=config.seed,
            window=config.probe.rolling_window, stride=config.probe.rolling_stride,
        )
        for e in (short, long_ctx)
    }
    canary_evalset = synthetic_evalset(
        eval_set_id="canary-20-synthetic", n_items=20, base_rate=0.95, seed=7
    )
    canary_cache = synthetic_cache(
        canary_evalset, seed=7,
        window=config.probe.rolling_window, stride=config.probe.rolling_stride,
        signal_by_tier={v: 8.0 for v in caches[short.eval_set_id].variants},
        amplitude_spread=0.05,
    )

    # -- text envelopes (hand-built, real) ------------------------------------ #
    hinglish = build_hinglish_pii(seed=config.seed)
    hinglish_long = build_longctx(
        hinglish, seed=config.seed, pad_tokens=(4000, 16000),
        eval_set_id="hinglish-pii-200-longctx",
    )
    hard_negatives = build_hard_negatives(seed=config.seed)
    pii_canary = build_canary_pii(seed=config.seed)

    # The ledger follows the results directory, so a smoke run with --out cannot
    # append to the real audit store. A test that pollutes the artifact it is
    # checking is worse than no test.
    ledger = Ledger(
        results_dir / Path(config.store.path).name,
        retention_days=config.store.retention_days,
    )
    _preflight_ledger(ledger)

    ladders = []
    try:
        for evalset in (short, long_ctx):
            ladder = run_ablation(
                config,
                evalset,
                caches[evalset.eval_set_id],
                detector_prefix="probe",
                detector_version="0.1.0+fixture",
                target_flag_rate=0.05,
                canary_cache=canary_cache,
            )
            ladders.append(ladder)
            for run in ladder.runs:
                _record(ledger, run)

        detector = ReferencePiiDetector()
        for evalset in (hinglish, hinglish_long, hard_negatives):
            is_hard = evalset is hard_negatives
            run = validate_text_detector(
                config, evalset, detector,
                threshold=detector.min_confidence,
                canary_evalset=pii_canary,
                max_fpr_hard_negatives=0.02 if is_hard else None,
                is_hard_negative_set=is_hard,
            )
            _record(ledger, run)

        # Declared-but-unbuilt envelopes are listed so their cells show as
        # UNVALIDATED rather than being absent. "We have not measured this" and
        # "we have not thought about this" are different, and only the first is
        # acceptable.
        envelopes = [
            short.eval_set_id,
            long_ctx.eval_set_id,
            hinglish.eval_set_id,
            hinglish_long.eval_set_id,
            hard_negatives.eval_set_id,
            "triviaqa-600",
            "triviaqa-longctx-600",
        ]
        # Declared UNION what the ledger actually holds. Declared alone renders
        # a row per detector we have thought about, so an unmeasured cell shows
        # as UNVALIDATED rather than vanishing. But it is built from the fixture
        # ladders' variant names ("probe-T1-mean_pool") while 02_validate writes
        # measured warrants under a model-qualified id
        # ("probe-qwen2.5-7b-instruct-T1-mean_pool"). Without the union those
        # measured warrants match no row and their cells render UNVALIDATED --
        # a measured REFUSAL displayed as "never tested", which is the one
        # reading the matrix exists to prevent.
        declared = {
            f"probe-{variant}"
            for ladder in ladders
            for variant in [r.variant for r in ladder.runs]
        } | {detector.detector_id}
        in_ledger = {
            ledger.get_warrant(record.record_id).detector_id
            for record in ledger.query(kind=RecordKind.WARRANT)
        }
        detectors = sorted(declared | in_ledger)
        matrix = WarrantMatrix.from_ledger(
            ledger, detectors=detectors, envelopes=envelopes
        )

        print()
        print(matrix.render())
        print()

        routing = []
        for profile_name in sorted(config.profiles):
            profile = Profile.from_config(config, profile_name)
            for envelope in envelopes:
                decision = route(matrix, envelope, profile)
                routing.append(
                    {
                        "profile": decision.profile,
                        "envelope_id": decision.envelope_id,
                        "routed_to": decision.warrant.detector_id if decision.routed else None,
                        "action": decision.action.value,
                        "suspended_profile": decision.suspended_profile,
                        "reason": decision.reason,
                        "considered": [
                            {"detector_id": d, "verdict": v}
                            for d, v in decision.considered
                        ],
                        "enqueued_for_validation": [
                            k.as_string() for k in decision.enqueued_for_validation
                        ],
                        "claimed_bounds": decision.claimed_bounds,
                    }
                )

        write_json_artifact(
            results_dir / "warrant_matrix.json",
            {"matrix": matrix.to_payload(), "routing": routing},
            config,
        )
        (results_dir / "warrant_matrix.md").write_text(
            matrix.render() + "\n", encoding="utf-8"
        )
        _LOG.info("wrote %s", results_dir / "warrant_matrix.md")

        # RESULTS.md refuses to print any number from a synthetic envelope.
        # Right now that is most of them, and the document says so at the top
        # rather than leaving a reader to work it out (DECISIONS.md 046).
        # CLAUDE.md's definition of done asks RESULTS.md for the computed price
        # list and kappa as well as the matrix. Both exist now (DECISIONS.md
        # 146, 147, 152); price_list_sections renders them, and names the
        # script that writes each artifact when one is missing rather than
        # dropping the section, because this is the document a reviewer checks
        # the definition of done against.
        (results_dir / "RESULTS.md").write_text(
            render_results(
                matrix,
                provenance=provenance(config),
                extra_sections=price_list_sections(results_dir),
            ),
            encoding="utf-8",
        )
        _LOG.info("wrote %s", results_dir / "RESULTS.md")

        verification = ledger.verify_chain()
        _LOG.info(
            "ledger: %d records, chain %s",
            verification.n_records,
            "intact" if verification.ok else "BROKEN",
        )
    finally:
        ledger.close()
    return 0


def _record(ledger: Ledger, run) -> None:
    """Append a warrant unless an identical one is already recorded.

    Warrant ids are content-derived, so a re-run at the same seed on the same
    code produces the same id. That is determinism, not a new fact.
    """
    if ledger.contains(RecordKind.WARRANT, run.warrant.warrant_id):
        _LOG.info(
            "warrant %s already recorded for %s on %s",
            run.warrant.warrant_id,
            run.detector_id,
            run.eval_set_id,
        )
        return
    ledger.append_warrant(run.warrant)


if __name__ == "__main__":
    raise SystemExit(main())
