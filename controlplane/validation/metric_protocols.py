"""Named FPR inference protocols accepted by new hard-negative warrants (220)."""

from __future__ import annotations

from ..model import Metric

GROUPED_HARD_NEGATIVE_PROTOCOL = "group_any_cp_v1"
INDEPENDENT_HARD_NEGATIVE_PROTOCOL = "independent_item_cp_v1"
GROUPED_RATE_BOUNDARY_PROTOCOL = "grouped_rate_vacuous_v1"
SUPPORTED_HARD_NEGATIVE_PROTOCOLS = (
    GROUPED_HARD_NEGATIVE_PROTOCOL,
    INDEPENDENT_HARD_NEGATIVE_PROTOCOL,
)


def has_supported_hard_negative_protocol(metric: Metric) -> bool:
    """Fail closed on an old row-count bound whose grouping is not recorded.

    The estimator text is a local protocol declaration, not an authenticated
    source attestation. Retained legacy records do not gain new inferential
    status merely because their arithmetic replays.
    """
    estimator = metric.estimator or ""
    return any(
        estimator.startswith(protocol + " ")
        for protocol in SUPPORTED_HARD_NEGATIVE_PROTOCOLS
    )
