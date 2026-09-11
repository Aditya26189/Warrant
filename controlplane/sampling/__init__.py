"""On-traffic warrants: what your error rate is on **your** traffic.

Clause one of the three in ``CLAUDE.md``. Every other package here certifies a
detector against an eval set someone froze; this one certifies it against the
traffic it is actually running on, which is the only distribution an operator
cares about and the only one no benchmark can supply.

``DECISIONS.md`` 096 and 099 recorded this package as NOT BUILT through four
phases, and 147 records what that cost: the sample size the repository quoted in
the meantime was a binomial on recall rather than a propagation through
``dR/dq``, understating the labels needed by 6x to 13x.

The design, in one table:

=================  ==========  ==========  ==============================
stratum            reviewed    cost        what it yields
=================  ==========  ==========  ==============================
A -- flagged       in full     free        ``TP`` and precision, **EXACT**
B -- unflagged     sampled     labels      ``q``, and so recall, **ESTIMATED**
=================  ==========  ==========  ==============================

That asymmetry is why *yield is exact and rate is estimated* is a structural
property here rather than a rule anyone has to remember, and why precision and
recall have to travel together: one is a census and the other is a survey.

Modules:

* :mod:`~controlplane.sampling.planning` -- ``dR/dq`` and what a margin costs,
  sized against the interval the estimator will actually publish.
* :mod:`~controlplane.sampling.estimator` -- the measurement, with the exact
  half and the estimated half in separate fields.
* :mod:`~controlplane.sampling.allocation` -- proportional in month one,
  Neyman once ``q_h`` has been measured, and the design effect between them.
* :mod:`~controlplane.sampling.queue` -- the blinded review queue
  (``CLAUDE.md`` invariant 7).
* :mod:`~controlplane.sampling.agreement` -- Cohen's kappa, which qualifies
  every interval the estimator returns.
"""

from .agreement import Agreement, AgreementError, cohens_kappa
from .allocation import (
    Allocation,
    AllocationError,
    design_effect,
    neyman,
    proportional,
)
from .estimator import Band, EstimationError, OnTrafficEstimate, estimate_on_traffic
from .planning import (
    LabelPlan,
    RecallSensitivity,
    SizingError,
    labels_for_prevalence,
    labels_for_recall,
    recall_sensitivity,
)
from .queue import (
    WITHHELD_FIELDS,
    BlindedQueue,
    LabelItem,
    QueueError,
    build_queue,
)

__all__ = [
    "WITHHELD_FIELDS",
    "Agreement",
    "AgreementError",
    "Allocation",
    "AllocationError",
    "Band",
    "BlindedQueue",
    "EstimationError",
    "LabelItem",
    "LabelPlan",
    "OnTrafficEstimate",
    "QueueError",
    "RecallSensitivity",
    "SizingError",
    "build_queue",
    "cohens_kappa",
    "design_effect",
    "estimate_on_traffic",
    "labels_for_prevalence",
    "labels_for_recall",
    "neyman",
    "proportional",
    "recall_sensitivity",
]
