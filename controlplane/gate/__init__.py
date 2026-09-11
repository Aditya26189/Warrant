"""The action gate: the part of this system that does not consult a detector.

``SPEC.md`` §9, and the reason the rest of the repository can be honest about
adversarial robustness without claiming any.

Everything else here measures a detector and certifies what it is worth. This
package assumes the detector loses. Its first two rules read a tool's declared
reversibility, the warrant on the detector that *would* have been consulted, and
three sticky session flags — and no score. An attacker who defeats every
detector in this system has not moved either of them.

That is a much smaller claim than robustness, and unlike robustness it is
testable: null every detector input and check the decisions are unchanged.
``tests/test_gate.py::test_gate_no_detector``.

Modules:

* :mod:`~controlplane.gate.registry` — reversibility, declared per tool at
  definition time and refused if absent or downgraded.
* :mod:`~controlplane.gate.session` — the Rule-of-Two, three sticky booleans,
  two of three the limit.
* :mod:`~controlplane.gate.gate` — the five rules, in order, each naming itself.
* :mod:`~controlplane.gate.agent` — a four-tool banking agent and the indirect
  injection it is refused on.
"""

from .agent import (
    INJECTED_MEMO,
    Step,
    Transcript,
    banking_registry,
    run_injection_scenario,
)
from .cost import (
    LEGITIMATE_WORKFLOWS,
    GateCost,
    WorkflowOutcome,
    measure_gate_cost,
)
from .gate import GateDecision, decide
from .registry import RegistryError, Tool, ToolRegistry
from .session import Session, SessionError, rule_of_two_violated

__all__ = [
    "INJECTED_MEMO",
    "LEGITIMATE_WORKFLOWS",
    "GateCost",
    "GateDecision",
    "RegistryError",
    "Session",
    "SessionError",
    "Step",
    "Tool",
    "ToolRegistry",
    "Transcript",
    "WorkflowOutcome",
    "banking_registry",
    "decide",
    "measure_gate_cost",
    "run_injection_scenario",
    "rule_of_two_violated",
]
