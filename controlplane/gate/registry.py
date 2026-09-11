"""The reversibility registry: what a tool can do, declared where it is defined.

``SPEC.md`` §9.1. Reversibility is a **static property of the tool**, registered
at definition time, never an inference about the request.

That distinction is the whole point. A control that infers *"this looks like a
dangerous request"* is a classifier, and every classifier has a measured ceiling
against an adversary. A control keyed to *"`transfer_funds` moves money and
always has"* has no ceiling to measure, because there is nothing about the
request for an attacker to change. The gate's first two rules read this registry
and the session flags and consult no detector score at all
(``SPEC.md`` §9.3).

Two refusals hold the property in place:

* **No default.** A tool registered without a reversibility is refused. A
  default of ``READ_ONLY`` would make forgetting to declare one the safest
  possible mistake, which is exactly backwards; a default of
  ``IRREVERSIBLE_WRITE`` would make the registry noisy enough that somebody
  turns it off.
* **No redefinition.** Re-registering a name with a *different* reversibility is
  refused. A registry that can be downgraded at runtime is a registry an
  attacker who reaches any code path can defeat, and the static property stops
  being static.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Mapping, Optional

from ..model import Reversibility

__all__ = ["RegistryError", "Tool", "ToolRegistry"]


class RegistryError(ValueError):
    """A tool was registered in a way that would weaken the gate."""


@dataclass(frozen=True)
class Tool:
    """One tool, and the three static facts the gate needs about it.

    Attributes:
        name: The tool's name, as the agent calls it.
        reversibility: Its blast radius. Declared, never inferred.
        grants_sensitive_access: Whether calling it puts sensitive data into the
            session. One of the three Rule-of-Two flags (``SPEC.md`` §9.2).
        changes_state_or_communicates: Whether calling it can change state or
            reach the outside world. The third flag.
        ingests_untrusted_input: Whether its **output** can carry content the
            user did not write — a transaction memo, a retrieved document, a web
            page. This is the flag that indirect prompt injection sets, and the
            reason it is a property of the tool is that whether a memo field can
            contain attacker text is a fact about the schema, not about the
            request.
        description: For the decision log.
    """

    name: str
    reversibility: Reversibility
    grants_sensitive_access: bool = False
    changes_state_or_communicates: bool = False
    ingests_untrusted_input: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise RegistryError("a tool must be named")
        if not isinstance(self.reversibility, Reversibility):
            raise RegistryError(
                f"{self.name}: reversibility must be a Reversibility, got "
                f"{self.reversibility!r}. There is no default, deliberately: a "
                "default of READ_ONLY would make forgetting to declare one the "
                "safest possible mistake."
            )


class ToolRegistry:
    """The tools an agent may call, and what each of them is.

    Refuses a redefinition that changes a tool's reversibility, so the static
    property cannot be downgraded by any code path an attacker reaches.
    """

    def __init__(self, tools: Optional[Mapping[str, Tool]] = None) -> None:
        self._tools: dict[str, Tool] = dict(tools or {})

    def register(self, tool: Tool) -> None:
        """Add a tool.

        Raises:
            RegistryError: If a tool of the same name is already registered with
                a different reversibility. Re-registering an identical tool is
                allowed, because module reloads and test fixtures do it and it
                changes nothing.
        """
        existing = self._tools.get(tool.name)
        if existing is not None and existing != tool:
            if existing.reversibility != tool.reversibility:
                raise RegistryError(
                    f"{tool.name} is registered as {existing.reversibility.name} "
                    f"and cannot be re-registered as {tool.reversibility.name}. "
                    "Reversibility is a static property of the tool (SPEC.md "
                    "9.1); a registry that can be downgraded at runtime is one "
                    "an attacker who reaches any code path can defeat."
                )
            raise RegistryError(
                f"{tool.name} is already registered with different flags. "
                "Change the definition, not the registration."
            )
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Look a tool up.

        Raises:
            RegistryError: If it is not registered. An unregistered tool has no
                declared reversibility, and guessing one at call time is the
                inference this module exists to prevent.
        """
        try:
            return self._tools[name]
        except KeyError:
            raise RegistryError(
                f"{name!r} is not registered, so its reversibility is unknown. "
                "The gate will not guess it: an unregistered tool is a tool "
                "nobody declared the blast radius of."
            ) from None

    def __contains__(self, name: object) -> bool:
        return name in self._tools

    def __iter__(self) -> Iterator[Tool]:
        return iter(sorted(self._tools.values(), key=lambda t: t.name))

    def __len__(self) -> int:
        return len(self._tools)
