"""Run one pairing: fetch, score, certify across the grid, emit.

The certification is :func:`~controlplane.validation.fpr_sweep.sweep_fpr` — the
same code, the same grid, the same D6 criterion and the same bootstrap that
produced every number this project publishes about its own detector. A
third-party detector is not measured by a different yardstick, and neither is
ours (D37).

**Nothing derived from a fetched dataset is written to disk** beyond aggregates:
no source text, no per-item scores. The reproduction path is the command, not a
committed copy of somebody else's data.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Sequence

from ..config import Config
from ..validation.fpr_sweep import FprSweep, fpr_grid, sweep_fpr
from ..validation.scores import ScoreSet, ScoreTarget
from .registry import PAIRINGS, Pairing

__all__ = ["load_rows", "run_pairing"]

_LOG = logging.getLogger(__name__)


def load_rows(pairing: Pairing) -> list[dict]:
    """Fetch the dataset at its pinned revision. Network, by design."""
    if pairing.loader is not None:
        return pairing.loader()

    from datasets import load_dataset

    dataset = pairing.dataset
    split = f"{dataset.split}[:{pairing.limit}]"
    _LOG.info(
        "fetching %s @ %s (%s)", dataset.hf_id, dataset.revision[:12], split
    )
    data = load_dataset(dataset.hf_id, split=split, revision=dataset.revision)
    if "language" in data.column_names:
        # The PII set is multilingual and Presidio is being run with
        # language='en'. Scoring other languages under an English pipeline
        # would measure the mismatch, not the detector.
        data = data.filter(lambda r: r["language"] == "en")
    return list(data)


def _score_set_for(
    pairing: Pairing, ids: Sequence[str], labels: Sequence[int], scores: Sequence[float]
) -> ScoreSet:
    """Wrap a scoring so the standard sweep can consume it.

    Held in memory only. These arrays are derived from a dataset this project
    does not redistribute, so they are never written under ``results/scores/``
    and never enter ``make verify``'s frozen-score tier.
    """
    return ScoreSet(
        score_set_id=f"external-{pairing.id}",
        detector_id=pairing.detector.id,
        variant=pairing.detector.version[:16],
        eval_set_id=pairing.dataset.id,
        envelope_id=f"revision:{pairing.dataset.revision[:16]}",
        labels=tuple(int(x) for x in labels),
        scores=tuple(float(x) for x in scores),
        question_ids=tuple(str(x) for x in ids),
        targets=(
            ScoreTarget(
                artifact=f"results/external/{pairing.id}/sweep.json",
                metrics_path="sweeps[0].points",
                threshold=0.5,
                operating_point_id=None,
            ),
        ),
        note=(
            f"{pairing.detector.id} on {pairing.dataset.id}. Derived from a "
            "dataset this project does not redistribute; held in memory and "
            "never frozen to disk."
        ),
    )


def _run_frozen(
    config: Config, pairing: Pairing, grid: Sequence[float]
) -> tuple[FprSweep, dict[str, Any]]:
    """Certify this project's own detector from its committed scores.

    Identical grid, identical criterion, identical payload shape as every
    third-party row. The only difference is that the scores were frozen in an
    earlier phase rather than computed now, and that is stated in the artifact
    rather than left for a reader to infer.
    """
    from pathlib import Path as _Path

    from ..validation.scores import load_score_set

    root = _Path(config.paths.results_dir) / "scores"
    score_set = load_score_set(root / f"{pairing.frozen_score_set}.json")
    sweep = sweep_fpr(config, score_set, grid=tuple(grid), data_source="measured")
    payload = {
        "pairing": pairing.to_payload(),
        "grid_spec": {"targets": list(grid), "n_points": len(grid)},
        "criterion": {
            "name": "lift_holds",
            "rule": "lift ci_low > 1.0, strictly",
            "registered": "Phase 0 D6, unchanged for third parties (Phase 3 D35)",
        },
        "neutrality": (
            "This is the author's own detector, in the matrix on identical terms "
            "(D37): same grid, same criterion, same presentation. Its scores come "
            "from results/scores/"
            f"{pairing.frozen_score_set}.json, frozen in an earlier phase."
        ),
        "sweeps": [sweep.to_payload()],
    }
    return sweep, payload


def run_pairing(
    config: Config,
    pairing_id: str,
    *,
    grid: Optional[Sequence[float]] = None,
) -> tuple[FprSweep, dict[str, Any]]:
    """Score a pairing and certify it across the budget grid.

    Returns:
        The sweep and a JSON-ready payload carrying it plus full provenance for
        the detector and the dataset.

    Raises:
        KeyError: If the pairing is not registered.
        ValueError: If the pairing yields one class, which cannot be certified.
    """
    pairing = PAIRINGS[pairing_id]
    grid = tuple(grid) if grid is not None else fpr_grid(0.01, 0.20, 0.01)

    if pairing.out_of_scope is not None:
        raise ValueError(
            f"{pairing.id} is declared out of scope and is not scored: "
            f"{pairing.out_of_scope}"
        )

    if pairing.frozen_score_set is not None:
        return _run_frozen(config, pairing, grid)

    rows = load_rows(pairing)
    ids, labels, texts = pairing.items(rows)
    positives = sum(labels)
    _LOG.info(
        "%s: %d items, %d positive, %d negative",
        pairing.id, len(labels), positives, len(labels) - positives,
    )
    if positives in (0, len(labels)):
        raise ValueError(
            f"{pairing.id}: the pairing is single-class ({positives} positive of "
            f"{len(labels)}). No false-positive rate can be bounded on it."
        )

    _LOG.info("%s: scoring %d items with %s", pairing.id, len(texts), pairing.detector.id)
    scores = pairing.score(texts)
    if len(scores) != len(texts):
        raise ValueError(
            f"{pairing.id}: the detector returned {len(scores)} scores for "
            f"{len(texts)} items. A misaligned score vector would attach every "
            "label to the wrong item and still produce a plausible warrant."
        )

    score_set = _score_set_for(pairing, ids, labels, scores)
    sweep = sweep_fpr(config, score_set, grid=grid, data_source="measured")

    payload = {
        "pairing": pairing.to_payload(),
        "grid_spec": {"targets": list(grid), "n_points": len(grid)},
        "criterion": {
            "name": "lift_holds",
            "rule": "lift ci_low > 1.0, strictly",
            "registered": "Phase 0 D6, unchanged for third parties (Phase 3 D35)",
        },
        "neutrality": (
            "This detector was run at its documented default configuration and "
            "was not tuned for this evaluation. A refusal at a given budget is a "
            "statement about what this dataset can support at that budget, not "
            "about the detector's quality. Phase 3 D34, D36."
        ),
        "sweeps": [sweep.to_payload()],
    }
    return sweep, payload
