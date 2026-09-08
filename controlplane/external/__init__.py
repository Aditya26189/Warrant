"""Certifying detectors this project did not build, on data it did not construct.

Every number here comes from the same grid, the same Clopper-Pearson
certification and the same criterion as the project's own results. That is the
point: a comparison in which the author's entry is measured differently from the
others is not evidence.
"""

from .matrix import BUDGET_COLUMNS, render_matrix
from .registry import PAIRINGS, ExternalDataset, ExternalDetector, Pairing, pairing_ids
from .run import load_rows, run_pairing

__all__ = [
    "BUDGET_COLUMNS",
    "PAIRINGS",
    "ExternalDataset",
    "ExternalDetector",
    "Pairing",
    "load_rows",
    "pairing_ids",
    "render_matrix",
    "run_pairing",
]
