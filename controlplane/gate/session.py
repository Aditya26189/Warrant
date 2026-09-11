"""The session Rule-of-Two: three sticky flags, and two of three is the limit.

``SPEC.md`` §9.2. A session may hold at most two of:

1. ``has_ingested_untrusted_input`` — content the user did not write has entered
   the context: a transaction memo, a retrieved document, a web page.
2. ``has_sensitive_access`` — the session can read data that matters.
3. ``can_change_state_or_communicate`` — the session can write or reach out.

All three at once is the shape of every serious agent compromise: attacker text
arrives, the agent can see something worth taking, and the agent can act. Any two
are ordinarily fine. The third is what turns a prompt into an incident.

**Sticky, and that is the load-bearing property.** Once untrusted content has
entered a context window it has entered; there is no operation that removes it,
and a flag that could be cleared would be a flag an attacker asks to have
cleared. So the setters only ever move ``False -> True``, and there is no
unsetter. A session that has become too capable is finished, and the honest
remedy is a new session with a fresh context — which is what
:meth:`Session.successor` is for.

**This consults no detector.** Which tool was called and what it does are
registry facts (``SPEC.md`` §9.1); whether the model was suspicious of the text
never enters. Published work broke twelve injection defences at over 90% attack
success, so a control that depends on detection has a ceiling somebody has
already measured. This one does not.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from .registry import Tool

__all__ = ["Session", "SessionError", "rule_of_two_violated"]


class SessionError(ValueError):
    """A session was asked to do something that would unstick a flag."""


@dataclass(frozen=True)
class Session:
    """One agent session and its three sticky capability flags.

    Frozen: every transition returns a new session rather than mutating this
    one, so a decision log can hold the exact state each decision was made
    against instead of a reference to something that has since changed.

    Attributes:
        session_id: Stable id, for the decision log.
        has_ingested_untrusted_input: Flag 1.
        has_sensitive_access: Flag 2.
        can_change_state_or_communicate: Flag 3.
        history: Tool names that set a flag, in order. The audit trail for why
            a session became too capable, which is the first question anyone
            asks when a call is blocked.
    """

    session_id: str
    has_ingested_untrusted_input: bool = False
    has_sensitive_access: bool = False
    can_change_state_or_communicate: bool = False
    history: tuple[str, ...] = field(default_factory=tuple)

    @property
    def flags_held(self) -> int:
        """How many of the three are set."""
        return sum(
            (
                self.has_ingested_untrusted_input,
                self.has_sensitive_access,
                self.can_change_state_or_communicate,
            )
        )

    def after(self, tool: Tool) -> "Session":
        """The session as it stands once ``tool`` has run.

        Flags are OR-ed in, never out. A tool that sets nothing returns a
        session equal to this one.

        Args:
            tool: The tool that ran, with its declared flags.

        Returns:
            A new :class:`Session`.
        """
        ingested = self.has_ingested_untrusted_input or tool.ingests_untrusted_input
        sensitive = self.has_sensitive_access or tool.grants_sensitive_access
        acting = (
            self.can_change_state_or_communicate
            or tool.changes_state_or_communicates
        )
        changed = (
            ingested != self.has_ingested_untrusted_input
            or sensitive != self.has_sensitive_access
            or acting != self.can_change_state_or_communicate
        )
        return replace(
            self,
            has_ingested_untrusted_input=ingested,
            has_sensitive_access=sensitive,
            can_change_state_or_communicate=acting,
            history=self.history + ((tool.name,) if changed else ()),
        )

    def successor(self, session_id: str) -> "Session":
        """A fresh session, carrying nothing.

        The only way out of a three-flag session. It is a *new context*, not a
        reset of this one, and the distinction matters: resetting the flags
        while keeping the context window would leave the attacker's text in
        place and the flags saying otherwise.

        Args:
            session_id: Id for the new session. Must differ from this one's.

        Raises:
            SessionError: If the id is the same. A successor that reuses the id
                is indistinguishable in a log from the flags having been
                cleared, which is the thing that must not be possible.
        """
        if session_id == self.session_id:
            raise SessionError(
                f"a successor session must have a new id; {session_id!r} is this "
                "session's. Reusing it makes a fresh context and a cleared flag "
                "look identical in the decision log."
            )
        return Session(session_id=session_id)

    def render(self) -> str:
        """The three flags and how they got set."""
        marks = "".join(
            "X" if flag else "."
            for flag in (
                self.has_ingested_untrusted_input,
                self.has_sensitive_access,
                self.can_change_state_or_communicate,
            )
        )
        state = "VIOLATED" if rule_of_two_violated(self) else "ok"
        trail = " <- ".join(reversed(self.history)) if self.history else "nothing yet"
        return (
            f"{self.session_id}: [{marks}] {self.flags_held}/3 ({state})  "
            f"set by: {trail}"
        )


def rule_of_two_violated(session: Optional[Session]) -> bool:
    """Does this session hold all three capabilities?

    Two of three is the limit, so a violation is exactly three. ``None`` is not
    a violation: a call made outside any session has no history to have
    accumulated, and treating "no session" as "worst case" would block every
    stateless call for a reason that has nothing to do with it.

    Args:
        session: The session, or ``None`` for a stateless call.

    Returns:
        ``True`` when all three flags are set.
    """
    if session is None:
        return False
    return session.flags_held == 3
