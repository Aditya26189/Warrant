"""The recheck chain's detection across breach sizes, cadences and change points.

``DECISIONS.md`` 196, pre-registered. 187 chose the chain's rule on one setting and
193 put it in front of customers; this measures the same rule, with 187's
simulator unchanged, over the settings a customer could declare. Every figure is
a simulated operating characteristic of a decision rule under a known true
false-positive rate -- not a measurement of any detector -- and travels with its
setting.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from .schedules import RULES, Cadence, RuleSummary, StudyDesign, simulate
from .sizing import negatives_for_power

__all__ = [
    "BREACHES",
    "CADENCES",
    "REGISTERED_YEARS",
    "evaluate_criteria",
    "registered_designs",
    "run_grid",
]

BUDGET = 0.05
ALPHA = 0.05
POWER = 0.80
#: 143's measured true rate at a certified threshold.
CERTIFIED_RATE = 0.0371
#: 1.5x, 2x and 3x the budget.
BREACHES: tuple[float, ...] = (0.075, 0.10, 0.15)
#: Weekly with the breach starting after 13, 26 and 39 rechecks, and monthly.
CADENCES: tuple[Cadence, ...] = (
    Cadence("weekly-13", rechecks=52, change_after=13, window=13),
    Cadence("weekly-26", rechecks=52, change_after=26, window=13),
    Cadence("weekly-39", rechecks=52, change_after=39, window=13),
    Cadence("monthly-6", rechecks=12, change_after=6, window=3),
)
REGISTERED_YEARS = 2000


def registered_designs(years: int = REGISTERED_YEARS) -> tuple[StudyDesign, ...]:
    """One design per breach, each sized at 183's 0.80-power recheck size."""
    designs = []
    for breach in BREACHES:
        n = negatives_for_power(breach, BUDGET, ALPHA, POWER)
        if n is None:  # pragma: no cover - every registered breach is reachable
            raise ValueError(f"no 0.80-power size for breach {breach}")
        designs.append(StudyDesign(
            budget=BUDGET, alpha=ALPHA, breach=breach, negatives_per_recheck=n,
            years=years, cadences=CADENCES, certified_rate=CERTIFIED_RATE,
        ))
    return tuple(designs)


def run_grid(*, seed: int, years: Optional[int] = None) -> dict[str, Any]:
    """Every breach, cadence and scenario, then 196's criteria applied mechanically.

    Quantity: per rule and cell, the share of simulated years with a false
    revocation, and the share whose first revocation lands in the window after
    the change. Propagation: Monte Carlo over independent simulated years, each
    share with its binomial standard error, exactly as
    :func:`controlplane.economics.schedules.simulate` computes it.
    """
    years = REGISTERED_YEARS if years is None else years
    cells: list[RuleSummary] = []
    index: dict[tuple[float, str, str, str], RuleSummary] = {}
    for b_index, design in enumerate(registered_designs(years)):
        for c_index, cadence in enumerate(design.cadences):
            for s_index, scenario in enumerate(design.scenarios(cadence)):
                cell_seed = seed + 10_000 * b_index + 100 * c_index + s_index
                for rule, summary in simulate(design, cadence, scenario, seed=cell_seed,
                                              years=years).items():
                    cells.append(summary)
                    index[(design.breach, cadence.name, scenario.name, rule)] = summary
    return {
        "design": {
            "decision": "DECISIONS.md 196",
            "budget": BUDGET, "alpha": ALPHA, "power": POWER,
            "certified_rate": CERTIFIED_RATE, "breaches": list(BREACHES),
            "negatives_per_recheck": {str(d.breach): d.negatives_per_recheck
                                      for d in registered_designs(years)},
            "cadences": [vars(c) for c in CADENCES], "years": years, "seed": seed,
            "rules": list(RULES),
        },
        "what_these_are": (
            "Simulated operating characteristics of revocation rules under a known "
            "true false-positive rate, exact up to Monte Carlo error. They describe "
            "the rules, not any detector."
        ),
        "cells": [{"breach": key[0], **summary.to_payload()} for key, summary in index.items()],
        "criteria": evaluate_criteria(index, years),
    }


def _se(share: float, years: int) -> float:
    return math.sqrt(max(share * (1.0 - share), 1e-12) / years)


def evaluate_criteria(index: dict, years: int) -> dict[str, Any]:
    """196's V and P1-P3, evaluated exactly as registered."""
    chain = "e_detector"
    limit = ALPHA + 3.0 * _se(ALPHA, years)
    validity = []
    for breach in BREACHES:
        for cadence in CADENCES:
            for scenario in ("S0", "S1"):
                share = index[(breach, cadence.name, scenario, chain)].revoked_in_year
                validity.append({"breach": breach, "cadence": cadence.name, "scenario": scenario,
                                 "revoked_in_year": share, "limit": limit, "passes": share <= limit})

    p1 = []
    for cadence in CADENCES:
        caught = [index[(b, cadence.name, "S2", chain)].caught_in_window for b in BREACHES]
        by_breach = dict(zip(map(str, BREACHES), caught, strict=True))
        # Consecutive pairs: the second sequence is one shorter by construction.
        pairs = zip(caught, caught[1:], strict=False)
        p1.append({"cadence": cadence.name, "caught_by_breach": by_breach,
                   "holds": all(later >= earlier for earlier, later in pairs)})

    p2 = []
    for breach in BREACHES:
        for cadence in (c for c in CADENCES if c.name.startswith("weekly")):
            s2 = index[(breach, cadence.name, "S2", chain)].caught_in_window
            s3 = index[(breach, cadence.name, "S3", chain)].caught_in_window
            p2.append({"breach": breach, "cadence": cadence.name, "S2": s2, "S3": s3,
                       "holds": s3 >= s2 - 2.0 * _se(s2, years)})

    p3 = []
    for breach in BREACHES:
        early = index[(breach, "weekly-13", "S2", chain)].caught_in_window
        late = index[(breach, "weekly-39", "S2", chain)].caught_in_window
        early_s3 = index[(breach, "weekly-13", "S3", chain)].caught_in_window
        late_s3 = index[(breach, "weekly-39", "S3", chain)].caught_in_window
        p3.append({"breach": breach, "S2_week13": early, "S2_week39": late, "holds": late < early,
                   "S3_week13_reported": early_s3, "S3_week39_reported": late_s3})

    return {
        "V": {"all_pass": all(v["passes"] for v in validity), "cells": validity},
        "P1": {"all_hold": all(p["holds"] for p in p1), "cells": p1,
               "reading": "strict, as registered: the catch share does not fall as the breach grows"},
        "P2": {"all_hold": all(p["holds"] for p in p2), "cells": p2},
        "P3": {"all_hold": all(p["holds"] for p in p3), "cells": p3,
               "reading": "on S2, as the entry's comparison of change points is written; S3 reported beside it"},
    }
