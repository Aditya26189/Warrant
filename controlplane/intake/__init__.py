"""The bring-your-own-data path: certify a detector from a customer's file.

Warrant's research pipeline reads eval sets in a format only this project uses.
This package is the other door: a CSV or JSONL of ``id``, ``label``, ``score``,
and a warrant or a refusal at the end of it. No model, no config file, nothing
leaves the machine.

The certification is the same code the published numbers come from — see
:mod:`controlplane.intake.certify`.
"""

from .certify import CertificationResult, certify_items
from .contract import (
    GROUP_COLUMN,
    REQUIRED_COLUMNS,
    InputError,
    ScoredItems,
    load_scored_items,
)
from .frontier import FrontierPoint, frontier
from .recheck import RecheckResult, recheck_items, score_distribution
from .render import render_frontier, render_plan, render_recheck, render_summary

__all__ = [
    "GROUP_COLUMN",
    "REQUIRED_COLUMNS",
    "CertificationResult",
    "FrontierPoint",
    "InputError",
    "ScoredItems",
    "RecheckResult",
    "certify_items",
    "frontier",
    "load_scored_items",
    "recheck_items",
    "render_frontier",
    "render_plan",
    "render_recheck",
    "render_summary",
    "score_distribution",
]
