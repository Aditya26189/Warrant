"""Execute candidate code only inside a disposable constrained container.

The worker reports observations. The independent oracle stays outside it.
"""

import json
import sys

def observe(payload: dict) -> dict:
    """Initialize fresh task objects and report their final state, without grading."""
    sys.path.insert(0, "/candidate")
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


def main() -> None:
    """Emit an explicit failure record for ordinary candidate/protocol errors."""
    try:
        result = observe(json.load(sys.stdin))
    # Candidate imports and methods can raise arbitrary application exceptions.
    # This protocol boundary returns ERROR, never a successful observation;
    # BaseException (interrupt/exit) remains uncaught for the parent to classify.
    except Exception as exc:  # noqa: BLE001 -- explicit candidate/worker boundary
        result = {"status": "ERROR", "type": type(exc).__name__, "message": str(exc)}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
