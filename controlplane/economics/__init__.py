"""What can be derived about cost and feasibility, and what cannot.

**Read this before quoting anything from here.**

``DECISIONS.md`` 096 recorded that Phase 6 economics — ``sizing.py``, the price
list, the stratified estimator, ``test_no_scenario_mixing`` — was specified in
five contract documents and never built. **``sizing.py`` is now built**
(``DECISIONS.md`` 146); the rest of that list is not, and the distinction
matters because it is the difference between a cost this repository computes
and one somebody typed.

Everything here is arithmetic over numbers that already exist — measured ones
from ``results/``, declared ones from ``config.yaml``. Nothing here is a new
measurement and nothing here carries an interval:

- :mod:`controlplane.economics.feasibility` — the abstention floor. Given a
  measured base error rate and a declared target risk, the minimum fraction of
  traffic that *any* selector must abstain on, however good. An impossibility
  result, not an estimate.
- :mod:`controlplane.economics.review` — review volume and the sample size
  needed to estimate recall to a declared margin, from the measured operating
  points and one declared workload.
- :mod:`controlplane.economics.sizing` — the price list. What keeping a warrant
  true costs: the clean negatives one recheck needs to catch a breach of a
  named size, the items that must be labelled to get them, and a priced ladder
  of cadences. It recommends no cadence and it refuses when no sample size
  works.

**Still not built, and still cited by contracts:** the stratified on-traffic
estimator, the Neyman allocation schedule, the blinded label queue, Cohen's κ,
and ``test_no_scenario_mixing``. A cost figure that does not come from
``sizing.py`` remains a hand-derived declared estimate and must be labelled
one. See ``DECISIONS.md`` 099 for exactly which line moved and which did not.

The distinction this package keeps: a **measured** input comes from an artifact
in ``results/``; a **declared** input comes from ``config.yaml`` and is a choice
someone made. Every function here labels which of its inputs are which, and
every output carries that labelling through.
"""

from .feasibility import (
    AbstentionFloor,
    AchievedRisk,
    abstention_floor,
    achieved_risk,
    feasibility_curve,
)
from .review import (
    ReviewSizing,
    recall_sample_size,
    review_volume,
)
from .sizing import (
    CadenceOption,
    MonitoringPlan,
    monitoring_plan,
    negatives_for_detection,
    workload_price_list,
)

__all__ = [
    "AbstentionFloor",
    "AchievedRisk",
    "CadenceOption",
    "MonitoringPlan",
    "ReviewSizing",
    "abstention_floor",
    "achieved_risk",
    "feasibility_curve",
    "monitoring_plan",
    "negatives_for_detection",
    "recall_sample_size",
    "review_volume",
    "workload_price_list",
]
