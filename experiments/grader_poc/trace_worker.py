"""Execute candidate code only inside a disposable constrained container.

The worker reports observations. The independent oracle stays outside it.
"""

import json
import sys

sys.path.insert(0, "/candidate")


def observe(payload: dict) -> dict:
    """Initialize fresh task objects and report their final state, without grading."""
    from app.events import EventSource
    from app.merger import Merger
    from app.sessions import SessionManager
    from app.types import Clock, Event

    clock = Clock()
    source = EventSource(clock)
    manager = SessionManager(clock, gap=payload["gap"], merger=Merger())
    for name in sorted({event["source"] for event in payload["events"]}):
        source.register_source(name)
    for item in payload["events"]:
        event = Event(key=item["key"].encode("ascii"), time=item["time"],
                      value=item["value"], source=item["source"])
        source.ingest(event)
        manager.process_event(event)
    sessions = [{"key": session.key.decode("ascii"), "start": session.start,
                 "end": session.end, "aggregate": session.aggregate.result()}
                for session in manager.all_sessions()]
    return {"status": "OBSERVED", "sessions": sorted(sessions, key=lambda s: (s["key"], s["start"]))}


if __name__ == "__main__":
    try:
        result = observe(json.load(sys.stdin))
    except Exception as exc:
        result = {"status": "ERROR", "type": type(exc).__name__, "message": str(exc)}
    print(json.dumps(result))
