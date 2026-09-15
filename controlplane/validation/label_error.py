"""The project's own measured certificates under label error (``DECISIONS.md`` 199).

197 and 198 gave every customer certificate a label-error sensitivity. This runs it
on the warrants this project measured, through the customer path unchanged
(:func:`controlplane.intake.certify_items`), with the TriviaQA labelling rule's own
strict variant as the second labeller: ``label`` is lenient alias matching,
``label_2`` is :func:`controlplane.extract.triviaqa.is_exact_match` on the frozen
response and aliases. Every item carries both, so every dispute count is exact.

The strict label is **not a better labeller** -- it marks correct paraphrases
wrong (052). Counting its disagreements as lenient errors asks what the
certificates would say if the lenient rule's extra credit were all wrong: a bound
on one identified ambiguity of the rule, not an estimate of its label error.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Optional, Sequence

from ..config import Config
from ..extract.triviaqa import is_correct, is_exact_match
from ..intake import ScoredItems, certify_items
from ..model import to_jsonable

__all__ = ["REGISTERED_BUDGETS", "SCORE_SETS", "evaluate_criteria", "run_study"]

#: The D2 grid, 0.01 to 0.20 in steps of 0.01 (199).
REGISTERED_BUDGETS: tuple[float, ...] = tuple(round(0.01 * i, 2) for i in range(1, 21))
#: The three measured test-split score sets: one question set, three aggregations.
SCORE_SETS: tuple[str, ...] = (
    "validation-T1-last_token",
    "validation-T1-max_rolling_means",
    "validation-T1-mean_pool",
)


def _items(score_set: dict[str, Any], evalset: dict[str, Any]) -> tuple[ScoredItems, int]:
    """The score set as a customer file with ``label_2`` = strict EM, and the lenient mismatches.

    Raises:
        ValueError: If a question in the score set is missing from the eval set.
    """
    by_question = {item["question_id"]: item for item in evalset["items"]}
    strict: list[Optional[int]] = []
    mismatches = 0
    for question, label in zip(score_set["question_ids"], score_set["labels"], strict=True):
        if question not in by_question:
            raise ValueError(f"{question} is in {score_set['score_set_id']} and not in the eval set")
        item = by_question[question]
        aliases = item["meta"]["aliases"]
        lenient_correct, _ = is_correct(item["response"], aliases)
        mismatches += int(int(not lenient_correct) != int(label))
        # Positive class is incorrect: 1 when the strict rule does not match.
        strict.append(0 if is_exact_match(item["response"], aliases) else 1)
    items = ScoredItems(
        ids=tuple(score_set["question_ids"]),
        labels=tuple(int(y) for y in score_set["labels"]),
        scores=tuple(float(s) for s in score_set["scores"]),
        groups=None,
        passthrough_columns=(),
        source=score_set["score_set_id"],
        second_labels=tuple(strict),
    )
    return items, mismatches


def _sweep_rows(sweep: dict[str, Any], score_set_id: str) -> Optional[dict[float, dict[str, Any]]]:
    """The in-sample sweep rows for a set, or ``None`` when the sweep never ran it (199 amendment)."""
    for entry in sweep["sweeps"]:
        if entry["score_set_id"] == score_set_id and not entry["out_of_sample"]:
            return {round(float(p["target_fpr"]), 2): p for p in entry["points"]}
    return None


def run_study(
    config: Config,
    *,
    scores_dir: Path,
    evalset_path: Path,
    sweep_path: Path,
    budgets: Sequence[float] = REGISTERED_BUDGETS,
    score_sets: Sequence[str] = SCORE_SETS,
) -> dict[str, Any]:
    """Certify every registered (score set, budget) and record its label-error sensitivity.

    Quantity: per certified row, the certificate's confidence as labelled, after
    one error of each flattering kind, the errors of each kind to fall below 0.90,
    0.80 and 0.50, and the confidence with every strict-lenient dispute counted as
    a lenient error. Propagation: exact, ``c = 1 - P(Bin(n+a-b, B) <= k+a)``
    (197); kappa between the rules by percentile bootstrap over pairs.
    """
    evalset = json.loads(evalset_path.read_text(encoding="utf-8"))
    sweep = json.loads(sweep_path.read_text(encoding="utf-8"))
    sets: list[dict[str, Any]] = []
    for score_set_id in score_sets:
        score_set = json.loads((scores_dir / f"{score_set_id}.json").read_text(encoding="utf-8"))
        items, mismatches = _items(score_set, evalset)
        reference = _sweep_rows(sweep, score_set_id)
        rows = []
        for budget in budgets:
            result = certify_items(config, items, budget=budget)
            ref = None if reference is None else reference.get(round(budget, 2))
            reproduces = None if reference is None else ref is not None and (
                bool(ref["certified"]) == result.certified
                and (not result.certified or (
                    math.isclose(float(ref["threshold"]), result.threshold, rel_tol=0, abs_tol=1e-12)
                    and int(ref["k_false_positives"]) == result.false_positives_at_threshold
                ))
            )
            labels = to_jsonable(result.to_payload()["labels"])
            rows.append({
                "budget": budget,
                "status": result.status.value,
                "threshold": result.threshold,
                "k": result.false_positives_at_threshold,
                "n": result.negative_units,
                "reproduces_sweep": reproduces,
                "sensitivity": labels["sensitivity"],
                "second_review": labels["second_review"],
            })
        sets.append({
            "score_set_id": score_set_id,
            "eval_set_id": score_set["eval_set_id"],
            "n": items.n, "n_positive": items.n_positive, "n_negative": items.n_negative,
            "lenient_label_mismatches": mismatches,
            "rows": rows,
        })
    return {
        "design": {
            "decision": "DECISIONS.md 199",
            "budgets": list(budgets), "score_sets": list(score_sets),
            "alpha": 1.0 - config.validation.ci,
            "label": "lenient alias match (committed)",
            "label_2": "strict exact match, recomputed from the frozen eval set",
            "registered_run": tuple(budgets) == REGISTERED_BUDGETS and tuple(score_sets) == SCORE_SETS,
        },
        "what_these_are": (
            "Exact functions of each measured certificate's counts, and exact counts of "
            "disagreement between two matching rules. The strict rule is not a better "
            "labeller; counting its disagreements as lenient errors bounds one identified "
            "ambiguity of the labelling rule, not its label error."
        ),
        "sets": sets,
        "criteria": evaluate_criteria(sets),
    }


def evaluate_criteria(sets: list[dict[str, Any]]) -> dict[str, Any]:
    """199's C0, P1 and P2, applied as registered, and the reported extremes."""
    certified = [
        (entry["score_set_id"], row) for entry in sets for row in entry["rows"]
        if row["status"] == "VALID"
    ]
    checked = [row["reproduces_sweep"] for entry in sets for row in entry["rows"]
               if row["reproduces_sweep"] is not None]
    c0 = bool(checked) and all(checked)
    one_clean = [
        (sid, row["budget"], row["sensitivity"]["flagged_positive_really_clean"]["confidence_if_one"])
        for sid, row in certified
    ]
    at_disputes = [
        (sid, row["budget"],
         row["second_review"]["disputes"]["confidence_if_every_dispute_is_a_primary_error"])
        for sid, row in certified
    ]
    to_80 = [
        (sid, row["budget"],
         row["sensitivity"]["flagged_positive_really_clean"]["errors_to_fall_below"]["0.80"])
        for sid, row in certified
    ]
    reached = [value for _, _, value in to_80 if value is not None]
    return {
        "C0": {"holds": c0, "rows_checked": len(checked),
               "reading": ("every row with an in-sample sweep reference reproduces its status, "
                           "threshold and k; sets the sweep never ran are null, not a pass "
                           "(199 amendment)")},
        "P1": {"holds": all(c is not None and c < 0.95 for _, _, c in one_clean),
               "cells": [{"score_set_id": s, "budget": b, "confidence_if_one_flagged_clean": c}
                         for s, b, c in one_clean]},
        "P2": {"holds": any(c < 0.80 for _, _, c in at_disputes),
               "cells": [{"score_set_id": s, "budget": b, "confidence_at_disputes": c}
                         for s, b, c in at_disputes]},
        "reported": {
            "certified_rows": len(certified),
            "confidence_at_disputes_min": min((c for _, _, c in at_disputes), default=None),
            "confidence_at_disputes_max": max((c for _, _, c in at_disputes), default=None),
            "flagged_clean_errors_to_fall_below_0_80_min": min(reached, default=None),
            "flagged_clean_errors_to_fall_below_0_80_max": max(reached, default=None),
            "rows_never_below_0_80": sum(1 for _, _, v in to_80 if v is None),
        },
    }
