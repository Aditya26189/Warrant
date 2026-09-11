"""The action gate, and the one test the whole design exists to pass.

``docs/TASKS.md`` Phase 9 names the gate: *an injected instruction passes every
text-level check — visibly — and `transfer_funds` is blocked on reversibility
plus session state. `test_gate_no_detector` passes: the first two rules produce
correct decisions with all detector scores nulled.*

That second sentence is the product's only claim about adversarial safety, and
it is deliberately a small one. This repository does not claim robustness —
published work broke twelve injection defences at over 90% attack success, so a
control that depends on detection has a ceiling somebody has already measured.
What it claims is narrower and testable: **the decisions that matter do not read
a detector at all**, so defeating every detector does not move them.

``DECISIONS.md`` 156 records a defect found by building this: the Rule-of-Two as
``SPEC.md`` words it does not fire on the canonical injection, because the
transfer is the step that sets the third flag. The four-row table it registered
is :func:`test_the_four_paths_registered_in_decisions_156`.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from controlplane.gate import (
    INJECTED_MEMO,
    RegistryError,
    Session,
    SessionError,
    Tool,
    ToolRegistry,
    banking_registry,
    decide,
    measure_gate_cost,
    run_injection_scenario,
    rule_of_two_violated,
)
from controlplane.model import (
    Action,
    ConfidenceBand,
    Reversibility,
    Severity,
    WarrantStatus,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _session(registry: ToolRegistry, *names: str) -> Session:
    session = Session(session_id="t")
    for name in names:
        session = session.after(registry.get(name))
    return session


# --------------------------------------------------------------------------- #
# The phase gate
# --------------------------------------------------------------------------- #


def test_gate_no_detector() -> None:
    """Every decision the first two rules make is unchanged with detectors nulled.

    The check is not that the gate *runs* without a detector — anything runs
    without an argument. It is that for every combination of session state and
    tool, the decision with a detector screaming CRITICAL is **identical** to
    the decision with every detector input set to ``None``, wherever rule 1 or
    rule 2 fires.

    That is what makes the claim falsifiable. If a detector-derived value ever
    leaks into those rules, some pair here stops matching.
    """
    registry = banking_registry()
    sessions = [
        None,
        Session(session_id="empty"),
        _session(registry, "get_balance"),
        _session(registry, "get_balance", "search_transactions"),
        _session(registry, "get_balance", "search_transactions", "draft_dispute"),
        _session(registry, "search_transactions", "draft_dispute"),
    ]
    statuses = [
        WarrantStatus.VALID,
        WarrantStatus.STALE,
        WarrantStatus.REVOKED,
        WarrantStatus.REFUSED,
        WarrantStatus.UNVALIDATED,
        None,
    ]
    loud = dict(severity=Severity.CRITICAL, confidence_band=ConfidenceBand.CONFIDENT_POSITIVE)
    quiet = dict(severity=None, confidence_band=None)

    compared = 0
    for tool in registry:
        for session in sessions:
            for status in statuses:
                with_detector = decide(
                    tool=tool, session=session, warrant_status=status, **loud
                )
                without = decide(
                    tool=tool, session=session, warrant_status=status, **quiet
                )
                if without.rule_id not in (
                    "R-no-warrant-irreversible",
                    "R-rule-of-two",
                ):
                    continue
                compared += 1
                assert with_detector.action is without.action, (
                    f"{tool.name}: a detector changed a decision made by "
                    f"{without.rule_id}"
                )
                assert with_detector.rule_id == without.rule_id
                assert without.consulted_detector is False
                assert with_detector.consulted_detector is False

    # Pinned exactly rather than bounded below, because the count is derivable
    # and an inequality would hide a rule silently ceasing to fire:
    #
    #   only transfer_funds is IRREVERSIBLE_WRITE, so only it reaches rules 1-2
    #   5 non-VALID statuses x 6 sessions  = 30  rule 1
    #   VALID, and 3 of the 6 sessions complete the triad on the transfer:
    #     get_balance+search, get_balance+search+draft, search+draft
    #                                      =  3  rule 2
    #                                        ---
    #                                         33
    assert compared == 33, (
        f"{compared} decisions reached rule 1 or rule 2, expected 33. Either "
        "the tool set, the session set or a rule's condition changed; the "
        "derivation is in the comment above."
    )


def test_an_injected_instruction_passes_every_check_and_is_blocked_anyway() -> None:
    """``docs/TASKS.md`` Phase 9's first gate check.

    The memo is plain English with no unicode tricks, no encoding and no
    adversarial perturbation — if it needed a trick to get past the detectors,
    the demonstration would be about the trick. No detector flags it, and the
    transfer is refused on the tool's declared reversibility plus three session
    flags.
    """
    transcript = run_injection_scenario(detector_flagged_injection=False)

    assert transcript.detector_flagged_injection is False
    assert transcript.blocked_step is not None

    blocked = transcript.steps[transcript.blocked_step - 1]
    assert blocked.tool_name == "transfer_funds"
    assert blocked.decision.action is Action.BLOCK
    assert blocked.decision.rule_id == "R-rule-of-two"
    assert blocked.decision.consulted_detector is False
    assert blocked.decision.reversibility is Reversibility.IRREVERSIBLE_WRITE

    # The memo really did enter the context, and it really is benign-looking.
    memo_step = next(s for s in transcript.steps if s.observed_text)
    assert memo_step.observed_text == INJECTED_MEMO
    assert memo_step.decision.action is Action.ALLOW

    # And the outcome does not change when the detector is loud, quiet, or absent.
    for flagged in (True, False):
        assert (
            run_injection_scenario(detector_flagged_injection=flagged).blocked_step
            == transcript.blocked_step
        )


def test_the_four_paths_registered_in_decisions_156() -> None:
    """The table `DECISIONS.md` 156 registered before the rule was changed.

    A rule that blocks the attack by blocking everything is not a fix, so all
    four rows matter and three of them are ALLOWs.
    """
    registry = banking_registry()
    expected = (
        (("get_balance",), "transfer_funds", Action.ALLOW),
        (("get_balance", "search_transactions"), "transfer_funds", Action.BLOCK),
        (("get_balance", "search_transactions"), "draft_dispute", Action.ALLOW),
        (("search_transactions", "draft_dispute"), "transfer_funds", Action.BLOCK),
    )
    for prior, final, action in expected:
        decision = decide(
            tool=registry.get(final),
            session=_session(registry, *prior),
            warrant_status=WarrantStatus.VALID,
        )
        assert decision.action is action, (
            f"{' -> '.join(prior)} -> {final} gave {decision.action.value}, "
            f"expected {action.value} (DECISIONS.md 156)"
        )


def test_the_rule_is_prospective_not_historical() -> None:
    """The defect itself, kept as a test so it cannot come back.

    Reading the session *before* the call lets the canonical injection through,
    because the transfer is what sets the third flag. The session below holds
    two of three and is blocked anyway, which is the whole of the fix.
    """
    registry = banking_registry()
    session = _session(registry, "get_balance", "search_transactions")
    assert session.flags_held == 2
    assert rule_of_two_violated(session) is False

    decision = decide(
        tool=registry.get("transfer_funds"),
        session=session,
        warrant_status=WarrantStatus.VALID,
    )
    assert decision.action is Action.BLOCK
    assert decision.rule_id == "R-rule-of-two"
    assert decision.inputs["rule_of_two_violated_before_call"] is False
    assert decision.inputs["rule_of_two_violated_after_call"] is True


# --------------------------------------------------------------------------- #
# The rules in order
# --------------------------------------------------------------------------- #


def test_rule_one_blocks_an_irreversible_action_on_any_non_valid_warrant() -> None:
    """And ``None`` is not ``VALID``, which is the case it exists for."""
    registry = banking_registry()
    for status in (
        WarrantStatus.STALE,
        WarrantStatus.REVOKED,
        WarrantStatus.REFUSED,
        WarrantStatus.UNVALIDATED,
        None,
    ):
        decision = decide(tool=registry.get("transfer_funds"), warrant_status=status)
        assert decision.action is Action.BLOCK
        assert decision.rule_id == "R-no-warrant-irreversible"
    # A reversible write on the same unwarranted detector is not blocked.
    assert (
        decide(tool=registry.get("draft_dispute"), warrant_status=None).action
        is Action.ALLOW
    )


def test_rules_three_and_four_are_detector_dependent_and_say_so() -> None:
    """The two rules that do read a detector mark themselves as doing so."""
    registry = banking_registry()
    confirm = decide(
        tool=registry.get("transfer_funds"),
        warrant_status=WarrantStatus.VALID,
        severity=Severity.MEDIUM,
    )
    assert confirm.action is Action.CONFIRM
    assert confirm.consulted_detector is True

    escalate = decide(
        tool=registry.get("get_balance"),
        warrant_status=WarrantStatus.VALID,
        severity=Severity.HIGH,
        confidence_band=ConfidenceBand.UNCERTAIN,
    )
    assert escalate.action is Action.ESCALATE
    assert escalate.consulted_detector is True


def test_a_default_allow_names_its_rule_and_distinguishes_a_silent_detector() -> None:
    """A decision with no rule attached is one nobody can audit."""
    registry = banking_registry()
    quiet = decide(tool=registry.get("get_balance"), warrant_status=WarrantStatus.VALID)
    assert quiet.action is Action.ALLOW
    assert quiet.rule_id == "R-allow-default"
    assert quiet.consulted_detector is False
    assert quiet.detector_inputs_present is False

    ran = decide(
        tool=registry.get("get_balance"),
        warrant_status=WarrantStatus.VALID,
        severity=Severity.LOW,
    )
    assert ran.action is Action.ALLOW
    # The rule read nothing from it, but a detector did run. The two are
    # different facts and the log keeps them apart.
    assert ran.consulted_detector is False
    assert ran.detector_inputs_present is True


def test_rule_one_matches_the_rego_bundles() -> None:
    """The local backstop and the deployed policy must not drift apart.

    The gate restates rule 1 rather than delegating, because a gate that fails
    open when the policy engine is unreachable is not a gate. Two
    implementations of one rule need a check that they still agree.
    """
    bundles = sorted((PROJECT_ROOT / "policies").glob("*/policy.rego"))
    assert bundles, "no policy bundles found"
    for bundle in bundles:
        text = bundle.read_text(encoding="utf-8")
        assert "R-no-warrant-irreversible" in text, bundle.name
        assert "input.action.reversibility >= 2" in text, bundle.name
    # And 2 is IRREVERSIBLE_WRITE in the enum the gate compares against, so the
    # two are the same threshold rather than two numbers that happen to match.
    assert int(Reversibility.IRREVERSIBLE_WRITE) == 2


# --------------------------------------------------------------------------- #
# The registry and the session, which are what make the rules static
# --------------------------------------------------------------------------- #


def test_a_tool_without_a_declared_reversibility_is_refused() -> None:
    """No default, deliberately. See the docstring in registry.py."""
    with pytest.raises(RegistryError, match="no default"):
        Tool(name="mystery", reversibility="IRREVERSIBLE_WRITE")  # type: ignore[arg-type]


def test_reversibility_cannot_be_downgraded_at_runtime() -> None:
    """A registry that can be downgraded is one an attacker defeats."""
    registry = banking_registry()
    with pytest.raises(RegistryError, match="cannot be re-registered"):
        registry.register(
            Tool(name="transfer_funds", reversibility=Reversibility.READ_ONLY)
        )
    # Re-registering the identical tool changes nothing and is allowed.
    registry.register(registry.get("transfer_funds"))


def test_an_unregistered_tool_is_refused_rather_than_guessed() -> None:
    with pytest.raises(RegistryError, match="not registered"):
        banking_registry().get("wire_transfer")
    with pytest.raises(TypeError, match="declared reversibility"):
        decide(tool="transfer_funds", warrant_status=WarrantStatus.VALID)  # type: ignore[arg-type]


def test_session_flags_are_sticky_and_there_is_no_unsetter() -> None:
    """Once untrusted content has entered a context, it has entered."""
    registry = banking_registry()
    session = _session(registry, "search_transactions")
    assert session.has_ingested_untrusted_input is True

    # Running a tool that ingests nothing does not clear it.
    later = session.after(registry.get("get_balance"))
    assert later.has_ingested_untrusted_input is True
    assert later.flags_held == 2

    # There is no method that turns a flag off, and the dataclass is frozen.
    assert not any(
        name.startswith(("clear", "reset", "unset")) for name in dir(session)
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        session.has_ingested_untrusted_input = False  # type: ignore[misc]


def test_a_successor_session_must_have_a_new_id() -> None:
    """A reset and a fresh context must not look the same in the log."""
    session = Session(session_id="s1").after(banking_registry().get("search_transactions"))
    with pytest.raises(SessionError, match="new id"):
        session.successor("s1")
    fresh = session.successor("s2")
    assert fresh.flags_held == 0
    assert fresh.history == ()


def test_a_stateless_call_is_not_treated_as_worst_case() -> None:
    """``None`` has no history to have accumulated."""
    assert rule_of_two_violated(None) is False
    assert (
        decide(
            tool=banking_registry().get("transfer_funds"),
            session=None,
            warrant_status=WarrantStatus.VALID,
        ).action
        is Action.ALLOW
    )


# --------------------------------------------------------------------------- #
# What it costs
# --------------------------------------------------------------------------- #


def test_the_gate_cost_is_measured_and_is_exact_not_estimated() -> None:
    """A control that reports only its benefit is one nobody measures.

    And the count is **exact**: the workflow set is declared, so this is a
    census with no sampling in it. An interval here would manufacture
    uncertainty about a count, which is the yield-versus-rate confusion running
    the other way.
    """
    cost = measure_gate_cost()
    assert cost.n_workflows == 8
    assert cost.n_blocked == 2
    # Both blocked workflows read a memo and then try to pay, which is the
    # pattern the rule exists to stop; both recover with a new session.
    assert cost.n_recoverable == cost.n_blocked
    for outcome in cost.outcomes:
        if not outcome.completed:
            assert outcome.blocked_at == "transfer_funds"
            assert outcome.rule_id == "R-rule-of-two"

    # No interval anywhere on the object, and the note says why.
    assert not any(
        "ci" in f.name or "interval" in f.name for f in dataclasses.fields(cost)
    )
    assert "EXACT" in cost.note and "declared" in cost.note.lower()
    assert "estimated" in cost.note.lower()


def test_the_cost_is_measured_against_a_valid_warrant_not_a_missing_one() -> None:
    """Otherwise rule 1 blocks everything and the figure says nothing about rule 2."""
    with_warrant = measure_gate_cost(warrant_status=WarrantStatus.VALID)
    without = measure_gate_cost(warrant_status=WarrantStatus.UNVALIDATED)
    assert with_warrant.n_blocked < without.n_blocked
    assert all(
        o.rule_id == "R-rule-of-two"
        for o in with_warrant.outcomes
        if not o.completed
    )
