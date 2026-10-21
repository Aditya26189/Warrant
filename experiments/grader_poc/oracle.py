"""A partial, independently implemented aggregate oracle for short traces.

This code never imports a candidate or the upstream Aggregate implementation.
It establishes a narrow property, not correctness of the whole session system.
"""

from __future__ import annotations

from typing import Any, Sequence


def expected_sessions(
    events: Sequence[dict[str, Any]], gap: int, *, max_events: int
) -> dict[str, Any]:
    """Abstain outside the preregistered domain; otherwise derive components.

    No firing or GC occurs in this trace language. Sorted event-time components
    give an independent specification without imitating incremental merging.
    """
    reason = _unsupported(events, gap, max_events)
    if reason is not None:
        return {"status": "UNKNOWN", "reason": reason, "sessions": None}
    ordered = sorted(events, key=lambda event: event["time"])
    components: list[list[dict[str, Any]]] = []
    for event in ordered:
        if not components or event["time"] - components[-1][-1]["time"] > gap:
            components.append([event])
        else:
            components[-1].append(event)
    sessions = []
    for component in components:
        values = [event["value"] for event in component]
        sessions.append({
            "key": component[0]["key"],
            "start": component[0]["time"],
            "end": component[-1]["time"],
            "aggregate": {"sum": sum(values), "count": len(values), "max": max(values)},
        })
    return {"status": "KNOWN", "reason": None, "sessions": sessions}


def _unsupported(events: Sequence[dict[str, Any]], gap: int, max_events: int) -> str | None:
    if type(gap) is not int or gap <= 1:
        return "gap must be an integer greater than one"
    if not events or len(events) > max_events:
        return "trace length outside scope"
    fields = {"key", "time", "value", "source"}
    for event in events:
        if not isinstance(event, dict) or set(event) != fields:
            return "unsupported event fields"
        if type(event["time"]) is not int or event["time"] < 0:
            return "timestamps must be nonnegative integers"
        if type(event["value"]) is not int or event["value"] <= 0:
            return "values must be positive integers"
        if not isinstance(event["key"], str) or not event["key"].isascii() or not event["key"]:
            return "key must be nonempty ASCII"
        if not isinstance(event["source"], str) or not event["source"]:
            return "source must be nonempty"
    if len({event["key"] for event in events}) != 1:
        return "multiple keys outside initial scope"
    if len({event["source"] for event in events}) != 1:
        return "multiple sources outside initial scope"
    times = [event["time"] for event in events]
    if any(abs(left - right) == gap for left in times for right in times):
        return "exact gap boundary is deliberately unresolved"
    return None
