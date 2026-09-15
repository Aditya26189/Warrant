"""Human-readable terminal evidence, including uncertainty and scope limits."""

from __future__ import annotations

import json

from .contract import utc_time


def _number(value: float | None) -> str:
    return "undefined" if value is None else f"{value:.6g}"


def render_evaluation(record: dict, current_status: str) -> str:
    """Suppress synthetic metrics; customer rates always carry intervals and n.

    Render identity with JSON escaping so untrusted metadata cannot inject
    terminal control codes, newlines or pretend to be a second verdict. Normalize
    timestamps too: Python's ISO parser permits a control character separator.
    """
    lines = ["WARRANT RELEASE EVIDENCE", f"Current status: {current_status}",
             f"Status at evaluation: {record['status']}",
             f"Protocol: release/v{record['schema_version']}; simultaneous equal-tailed Clopper-Pearson intervals",
             "Identity: " + json.dumps(record["identity"], sort_keys=True, ensure_ascii=True),
             f"Evaluated: {utc_time(record['evaluated_at']).isoformat()} | "
             f"Expires: {utc_time(record['expires_at']).isoformat()}"]
    if record["data_origin"] == "synthetic":
        lines.append("SYNTHETIC FIXTURE: metric values suppressed; no product-performance claim.")
    else:
        lines.append(f"Simultaneous family confidence: {_number(record['family_confidence'])}")
        for name, rate in record["rates"].items():
            lines.append(f"{name}: {_number(rate['value'])} "
                         f"[{_number(rate['lower'])}, {_number(rate['upper'])}] "
                         f"n={rate['n']} confidence={_number(rate['confidence'])} ESTIMATED")
        lift = record["lift"]
        upper = "unbounded" if lift["upper"] is None else _number(lift["upper"])
        lines.append(f"lift: {_number(lift['value'])} [{_number(lift['lower'])}, {upper}] "
                     f"n={lift['n']} confidence={_number(lift['confidence'])} ESTIMATED")
        lines.append("EXACT holdout counts: " + json.dumps(record["counts"], sort_keys=True))
    for check in record["checks"]:
        reason = f" ({check['reason']})" if "reason" in check else ""
        lines.append(f"Criterion {check['metric']}: {check['status']}{reason}")
    lines.append("VALID means the registered confidence bounds cleared the criteria.")
    if record["schema_version"] == 1:
        lines.append("LEGACY protocol 1: UNVALIDATED means inconclusive or missing evidence, not an untested study.")
        lines.append("REFUSED means an observed rate violated a criterion; it is not proof of a population violation.")
    else:
        lines.append("REFUSED means the evidence did not clear every bound; this is not proof of a population violation.")
    lines.append("Release divides alpha across the interval family and both tails; certify uses a one-sided FPR bound.")
    lines.append("Status is conditional on that protocol; the two workflows' verdicts are not interchangeable.")
    lines.extend(record["assumptions"])
    return "\n".join(lines)
