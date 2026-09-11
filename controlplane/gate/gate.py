"""The action gate: five rules, and the first two consult no detector.

``SPEC.md`` §9.3, in order::

    BLOCK    if reversibility >= IRREVERSIBLE_WRITE and warrant_status != VALID
    BLOCK    if rule_of_two_violated(session) and reversibility >= IRREVERSIBLE_WRITE
    CONFIRM  if reversibility >= IRREVERSIBLE_WRITE and severity >= MEDIUM
    ESCALATE if severity >= HIGH and confidence_band == UNCERTAIN
    ALLOW    otherwise

**The first two rules are the product's real claim about adversarial safety, and
they are the reason this repository makes none.** Published work broke twelve
injection defences at over 90% attack success. Any control that depends on
detecting an attack therefore has a ceiling somebody has already measured, and a
vendor asserting robustness is asserting that their classifier is the exception.

Rules 1 and 2 depend on three things: the tool's declared reversibility, the
warrant on the detector that would have been consulted, and the session's
capability flags. None of those is a judgement about the text. **An attacker who
completely defeats every detector in this system does not move either of them**,
which is a much smaller claim than robustness and is one that can be tested —
by nulling every detector input and checking the decisions are unchanged. That
is ``test_gate_no_detector`` and it is the phase gate.

Rule 1 is the same rule the Rego bundles already enforce as
``R-no-warrant-irreversible`` (``policies/*/policy.rego``). It is restated here
rather than delegated because the gate must be decidable with no policy engine
running — a gate that fails open when OPA is unreachable is not a gate — and
because ``policy/`` is read-only in this build. Where they disagree, the bundle
is authoritative at deploy time and this is the local backstop; they are checked
against each other in ``tests/test_gate.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..model import Action, ConfidenceBand, Reversibility, Severity, WarrantStatus
from .registry import Tool
from .session import Session, rule_of_two_violated

__all__ = ["GateDecision", "decide"]


@dataclass(frozen=True)
class GateDecision:
    """What the gate decided, on what, and whether a detector was involved.

    Attributes:
        action: The decision.
        rule_id: Which rule fired. Every decision names one, including
            ``R-allow-default``, so a log line is never a decision with no
            reason attached.
        reason: Why, in words a reviewer can act on.
        tool_name: The tool the call was for.
        reversibility: Its declared blast radius.
        consulted_detector: **Whether the rule that fired read a
            detector-derived value.** Recorded rather than asserted, so the
            claim that the first two rules ignore detectors is a property of the
            log rather than of the documentation. ``False`` for rules 1, 2 and
            the default allow; ``True`` for rules 3 and 4.
        detector_inputs_present: Whether a severity or confidence band was
            supplied at all. Distinguishes *no detector ran* from *a detector
            ran and did not change the outcome*, which read identically in
            ``consulted_detector`` and mean different things to whoever is
            deciding whether to keep paying for the detector.
        session_flags: How many Rule-of-Two flags the session held.
        rule_of_two_violated: Whether all three were set.
        warrant_status: The status that was checked, when one was.
    """

    action: Action
    rule_id: str
    reason: str
    tool_name: str
    reversibility: Reversibility
    consulted_detector: bool
    detector_inputs_present: bool
    session_flags: int
    rule_of_two_violated: bool
    warrant_status: Optional[WarrantStatus] = None
    inputs: dict[str, object] = field(default_factory=dict)

    def render(self) -> str:
        """One line per decision, with the detector column visible."""
        if self.consulted_detector:
            detector = "detector consulted"
        elif self.detector_inputs_present:
            detector = "detector ran, not consulted"
        else:
            detector = "NO DETECTOR"
        return (
            f"{self.action.value:<8} {self.tool_name:<20} "
            f"{self.reversibility.name:<18} {self.rule_id:<28} "
            f"[{detector}]  {self.reason}"
        )


def decide(
    *,
    tool: Tool,
    session: Optional[Session] = None,
    warrant_status: Optional[WarrantStatus] = None,
    severity: Optional[Severity] = None,
    confidence_band: Optional[ConfidenceBand] = None,
) -> GateDecision:
    """Decide one tool call.

    Args:
        tool: The tool being called, from the registry. Its reversibility is
            declared, never inferred from the request.
        session: The session, or ``None`` for a stateless call.
        warrant_status: The weakest status across the detectors this action
            would rely on. ``None`` means no warrant was resolved, which is
            **not** the same as ``VALID`` and is treated as not-valid: an
            irreversible action backed by no warrant is the case rule 1 exists
            for.
        severity: Highest severity among the findings on this turn, if any
            detector ran. Detector-derived.
        confidence_band: The band on that finding. Detector-derived.

    Returns:
        The decision, recording whether any detector-derived input reached it.

    Raises:
        TypeError: If ``tool`` is not a :class:`~controlplane.gate.registry.Tool`.
            The gate will not accept a bare name: a name has no reversibility,
            and looking one up here would put an inference where a declaration
            belongs.
    """
    if not isinstance(tool, Tool):
        raise TypeError(
            f"decide() needs a registered Tool, got {type(tool).__name__}. A "
            "bare name carries no declared reversibility and the gate does not "
            "infer one (SPEC.md 9.1)."
        )

    irreversible = tool.reversibility >= Reversibility.IRREVERSIBLE_WRITE
    # Evaluated on the session as it would be AFTER this call, not before it.
    # DECISIONS.md 156: the transfer is the step that sets the third flag, so
    # reading the session beforehand lets the canonical indirect injection
    # through -- verified, not argued. "Would running this give the session all
    # three?" is the question; "does it already have all three?" is not.
    prospective = session.after(tool) if session is not None else None
    violated = rule_of_two_violated(prospective)
    already_violated = rule_of_two_violated(session)
    flags = session.flags_held if session is not None else 0
    detector_present = severity is not None or confidence_band is not None
    common = {
        "tool_name": tool.name,
        "reversibility": tool.reversibility,
        "session_flags": flags,
        "rule_of_two_violated": violated,
        "warrant_status": warrant_status,
        "detector_inputs_present": detector_present,
    }
    inputs = {
        "reversibility": tool.reversibility.name,
        "warrant_status": warrant_status.value if warrant_status else None,
        "rule_of_two_violated_after_call": violated,
        "rule_of_two_violated_before_call": already_violated,
        "severity": severity.name if severity is not None else None,
        "confidence_band": confidence_band.value if confidence_band else None,
    }

    # -- Rule 1. No detector input reaches this. ----------------------------- #
    if irreversible and warrant_status is not WarrantStatus.VALID:
        held = warrant_status.value if warrant_status else "none resolved"
        return GateDecision(
            action=Action.BLOCK,
            rule_id="R-no-warrant-irreversible",
            reason=(
                f"{tool.name} is {tool.reversibility.name} and the warrant it "
                f"would rely on is {held}, not VALID. An irreversible action "
                "taken on an unwarranted detector is a claim nobody has "
                "measured."
            ),
            consulted_detector=False,
            inputs=inputs,
            **common,
        )

    # -- Rule 2. No detector input reaches this either. ---------------------- #
    if violated and irreversible:
        if session is None:  # pragma: no cover - unreachable by construction
            # Raised, not asserted: `python -O` strips assert statements, so a
            # guard written that way is absent exactly in an optimised
            # production run. rule_of_two_violated() returns False for None, so
            # reaching here means the two have drifted apart -- and the gate
            # refusing loudly is the only safe response in a security rule.
            raise AssertionError(
                "rule 2 fired with no session. rule_of_two_violated(None) is "
                "False, so this is unreachable unless session.py and gate.py "
                "have diverged. Refusing rather than guessing."
            )
        already = "holds" if already_violated else "would hold"
        trail = " then ".join(session.history) or "no prior tool"
        return GateDecision(
            action=Action.BLOCK,
            rule_id="R-rule-of-two",
            reason=(
                f"{tool.name} is {tool.reversibility.name} and running it means "
                f"session {session.session_id} {already} all three capabilities "
                f"(untrusted input, sensitive access, state change); the first "
                f"were set by {trail}. Two of three is the limit. This decision "
                "reads no detector score, so an attacker who has defeated every "
                "detector has not moved it."
            ),
            consulted_detector=False,
            inputs=inputs,
            **common,
        )

    # -- Rules 3 and 4 are detector-dependent, and say so. ------------------- #
    if irreversible and severity is not None and severity >= Severity.MEDIUM:
        return GateDecision(
            action=Action.CONFIRM,
            rule_id="R-confirm-irreversible-medium",
            reason=(
                f"{tool.name} is {tool.reversibility.name} and a finding of "
                f"severity {severity.name} is on this turn. Warranted, so not "
                "blocked; irreversible, so not silent."
            ),
            consulted_detector=True,
            inputs=inputs,
            **common,
        )

    if (
        severity is not None
        and severity >= Severity.HIGH
        and confidence_band is ConfidenceBand.UNCERTAIN
    ):
        return GateDecision(
            action=Action.ESCALATE,
            rule_id="R-escalate-uncertain",
            reason=(
                f"severity {severity.name} with the detector UNCERTAIN. A "
                "high-severity call the detector cannot place is the case a "
                "human is for."
            ),
            consulted_detector=True,
            inputs=inputs,
            **common,
        )

    return GateDecision(
        action=Action.ALLOW,
        rule_id="R-allow-default",
        reason=(
            f"{tool.name} is {tool.reversibility.name}, no rule above fired. "
            "Named rather than left blank: a decision with no rule attached is "
            "one nobody can audit."
        ),
        # False even when a detector ran: this rule reads none of its output,
        # so the decision is the same whether the detector fired or not.
        # detector_inputs_present carries the other half.
        consulted_detector=False,
        inputs=inputs,
        **common,
    )
