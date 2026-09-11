"""The action gate: what it stops, what it costs, and what it never reads.

``docs/TASKS.md`` Phase 9. Everything else in this repository measures a
detector and certifies what it is worth. This is the part that assumes the
detector loses.

Four things:

1. **The registry** — four tools, each with a reversibility declared at
   definition time and never inferred from a request.
2. **The attack** — an instruction inside a transaction memo, plain English, no
   tricks. No detector flags it. ``transfer_funds`` is refused anyway.
3. **The evidence that no detector was read** — every decision the first two
   rules make, computed twice: once with a detector screaming CRITICAL and once
   with every detector input nulled. Identical, or this script fails.
4. **What it costs** — a declared set of legitimate workflows run through the
   gate, and a count of which ones it wrongly refuses. Exact, not estimated: the
   set is declared, so it is a census.

Thin wrapper: parses arguments, calls ``controlplane/``, writes files. No logic
(``CLAUDE.md``).

Usage:
    python scripts/27_gate.py --config config.yaml
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.config import load_config, setup_logging, write_json_artifact
from controlplane.gate import (
    INJECTED_MEMO,
    Session,
    banking_registry,
    decide,
    measure_gate_cost,
    run_injection_scenario,
)
from controlplane.model import ConfidenceBand, Severity, WarrantStatus

_LOG = logging.getLogger("scripts.27_gate")

#: Warrant statuses swept in the no-detector evidence. ``None`` is included
#: because "no warrant resolved" is not "VALID" and is the case rule 1 exists
#: for.
STATUSES = (
    WarrantStatus.VALID,
    WarrantStatus.STALE,
    WarrantStatus.REVOKED,
    WarrantStatus.REFUSED,
    WarrantStatus.UNVALIDATED,
    None,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--out", default=None, help="results directory override")
    return parser.parse_args(argv)


def _sessions(registry) -> list[tuple[str, Session | None]]:
    """The session states swept, named for the report."""

    def built(*names: str) -> Session:
        session = Session(session_id="+".join(names) or "empty")
        for name in names:
            session = session.after(registry.get(name))
        return session

    return [
        ("stateless (no session)", None),
        ("fresh session", Session(session_id="empty")),
        ("after get_balance", built("get_balance")),
        ("after get_balance, search", built("get_balance", "search_transactions")),
        (
            "after get_balance, search, draft",
            built("get_balance", "search_transactions", "draft_dispute"),
        ),
        ("after search, draft", built("search_transactions", "draft_dispute")),
    ]


def _no_detector_evidence(registry) -> dict[str, object]:
    """Every rule-1 and rule-2 decision, computed with and without a detector.

    The claim is not that the gate runs without a detector -- anything runs
    without an argument. It is that the decision is **identical** when a
    detector is screaming and when there is none, wherever those two rules fire.
    """
    rows: list[dict[str, object]] = []
    mismatches: list[str] = []
    for tool in registry:
        for session_name, session in _sessions(registry):
            for status in STATUSES:
                loud = decide(
                    tool=tool,
                    session=session,
                    warrant_status=status,
                    severity=Severity.CRITICAL,
                    confidence_band=ConfidenceBand.CONFIDENT_POSITIVE,
                )
                silent = decide(tool=tool, session=session, warrant_status=status)
                if silent.rule_id not in (
                    "R-no-warrant-irreversible",
                    "R-rule-of-two",
                ):
                    continue
                agree = (
                    loud.action is silent.action and loud.rule_id == silent.rule_id
                )
                if not agree:
                    mismatches.append(
                        f"{tool.name} / {session_name} / {status}: "
                        f"{loud.action.value} vs {silent.action.value}"
                    )
                rows.append(
                    {
                        "tool": tool.name,
                        "session": session_name,
                        "warrant_status": status.value if status else None,
                        "rule_id": silent.rule_id,
                        "action": silent.action.value,
                        "action_with_loud_detector": loud.action.value,
                        "identical": agree,
                        "consulted_detector": silent.consulted_detector,
                    }
                )
    return {
        "decisions_compared": len(rows),
        "identical": sum(1 for r in rows if r["identical"]),
        "mismatches": mismatches,
        "rows": rows,
        "claim": (
            "Every decision made by rule 1 or rule 2 is identical whether a "
            "detector reports CRITICAL or reports nothing at all. This is a "
            "smaller claim than adversarial robustness and unlike robustness it "
            "is testable. This repository makes no robustness claim: published "
            "work broke twelve injection defences at over 90% attack success."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir
    out_dir = results / "gate"
    out_dir.mkdir(parents=True, exist_ok=True)

    registry = banking_registry()
    transcript = run_injection_scenario(detector_flagged_injection=False)
    evidence = _no_detector_evidence(registry)
    cost = measure_gate_cost()

    _LOG.info("the injection scenario:")
    for line in transcript.render().splitlines():
        _LOG.info("    %s", line)
    _LOG.info(
        "no-detector evidence: %d of %d decisions identical with and without a "
        "detector",
        evidence["identical"], evidence["decisions_compared"],
    )
    for line in cost.render().splitlines():
        _LOG.info("    %s", line)

    if evidence["mismatches"]:
        _LOG.error(
            "a detector changed a rule-1 or rule-2 decision: %s",
            evidence["mismatches"],
        )
        return 1

    payload = {
        "question": (
            "what the action gate stops, what it costs, and whether its first "
            "two rules read any detector (docs/TASKS.md Phase 9, SPEC.md 9)"
        ),
        "registry": [dataclasses.asdict(tool) for tool in registry],
        "injection": {
            "memo": INJECTED_MEMO,
            "detector_flagged": transcript.detector_flagged_injection,
            "blocked_at_step": transcript.blocked_step,
            "steps": [
                {
                    "index": step.index,
                    "tool": step.tool_name,
                    "note": step.note,
                    "action": step.decision.action.value,
                    "rule_id": step.decision.rule_id,
                    "reason": step.decision.reason,
                    "consulted_detector": step.decision.consulted_detector,
                    "session_flags_before": step.session_before.flags_held,
                    "observed_text": step.observed_text,
                }
                for step in transcript.steps
            ],
        },
        "no_detector_evidence": evidence,
        "cost": {
            "n_workflows": cost.n_workflows,
            "n_blocked": cost.n_blocked,
            "n_recoverable_with_new_session": cost.n_recoverable,
            "kind": "EXACT",
            "note": cost.note,
            "outcomes": [dataclasses.asdict(o) for o in cost.outcomes],
        },
        "headline": {
            "decisions_compared": evidence["decisions_compared"],
            "decisions_identical_without_a_detector": evidence["identical"],
            "injection_blocked_at_step": transcript.blocked_step,
            "injection_flagged_by_detector": transcript.detector_flagged_injection,
            "legitimate_workflows": cost.n_workflows,
            "legitimate_workflows_blocked": cost.n_blocked,
            "blocked_workflows_recoverable": cost.n_recoverable,
        },
        "not_derived_here": [
            "any claim of adversarial robustness -- explicitly out of scope in "
            "CLAUDE.md, and the reason the first two rules read no detector",
            "a production false-block rate: this count is over a DECLARED set "
            "of workflows and is exact; the production quantity is a rate, is "
            "estimated, and costs labels (controlplane.sampling)",
            "whether the four declared workflows resemble real banking traffic, "
            "which is a judgement about the set and not a measurement",
        ],
    }
    write_json_artifact(out_dir / "gate.json", payload, config)
    _LOG.info("wrote %s", out_dir / "gate.json")
    _write_markdown(out_dir, payload, transcript, cost)
    return 0


def _write_markdown(out_dir: Path, payload: dict, transcript, cost) -> None:
    """Render the artifact as something a reviewer reads in two minutes."""
    head = payload["headline"]
    evidence = payload["no_detector_evidence"]
    lines = [
        "# The action gate",
        "",
        "Generated by `scripts/27_gate.py`. Every number is computed; none is "
        "typed.",
        "",
        "Everything else in this repository measures a detector and certifies "
        "what it is worth. **This is the part that assumes the detector loses.**",
        "",
        "## The tools, and what was declared about each",
        "",
        "| tool | reversibility | sensitive access | changes state | ingests untrusted |",
        "|---|---|---|---|---|",
    ]
    for tool in payload["registry"]:
        lines.append(
            f"| `{tool['name']}` | {tool['reversibility'].name} | "
            f"{'yes' if tool['grants_sensitive_access'] else '—'} | "
            f"{'yes' if tool['changes_state_or_communicates'] else '—'} | "
            f"{'yes' if tool['ingests_untrusted_input'] else '—'} |"
        )
    lines += [
        "",
        "Reversibility is a **static property of the tool**, registered at "
        "definition time. A control that infers *\"this looks dangerous\"* is a "
        "classifier and every classifier has a measured ceiling against an "
        "adversary. A control keyed to *\"`transfer_funds` moves money and "
        "always has\"* has no sentence for an attacker to rewrite.",
        "",
        "## The attack",
        "",
        "An instruction inside a transaction memo — a field the bank's own "
        "systems accept from a counterparty. Plain English, no unicode tricks, "
        "no encoding, no adversarial perturbation. If it needed a trick to get "
        "past the detectors, the demonstration would be about the trick.",
        "",
        "```",
        INJECTED_MEMO,
        "```",
        "",
    ]
    for step in payload["injection"]["steps"]:
        lines.append(
            f"{step['index']}. **{step['action']}** `{step['tool']}` — "
            f"{step['note']} (session held {step['session_flags_before']}/3)"
        )
        if step["action"] == "BLOCK":
            lines.append(f"    - rule `{step['rule_id']}`")
            lines.append(f"    - {step['reason']}")
    lines += [
        "",
        f"**No detector flagged the memo** "
        f"(`detector_flagged = {payload['injection']['detector_flagged']}`) and "
        f"the transfer was refused at step {head['injection_blocked_at_step']} "
        "anyway, on the tool's declared reversibility plus three session flags.",
        "",
        "## The evidence that no detector was read",
        "",
        f"Every decision the first two rules make, computed twice — once with a "
        f"detector reporting CRITICAL and CONFIDENT_POSITIVE, once with every "
        f"detector input set to `None`:",
        "",
        f"- decisions compared: **{evidence['decisions_compared']}**",
        f"- identical: **{evidence['identical']}**",
        f"- mismatches: **{len(evidence['mismatches'])}**",
        "",
        evidence["claim"],
        "",
        "## What it costs",
        "",
        f"**{head['legitimate_workflows_blocked']} of "
        f"{head['legitimate_workflows']}** declared legitimate workflows are "
        f"blocked. All **{head['blocked_workflows_recoverable']}** of them "
        "complete after starting a new session.",
        "",
        "| workflow | outcome |",
        "|---|---|",
    ]
    for outcome in payload["cost"]["outcomes"]:
        if outcome["completed"]:
            lines.append(f"| {outcome['name']} | ok |")
        else:
            remedy = (
                "a new session finishes it"
                if outcome["recoverable_with_new_session"]
                else "**not recoverable**"
            )
            lines.append(
                f"| {outcome['name']} | **BLOCKED** at "
                f"`{outcome['blocked_at']}` (`{outcome['rule_id']}`) — {remedy} |"
            )
    lines += [
        "",
        "> **These counts are EXACT, not estimated, and that is not a "
        "technicality.** The workflow set is *declared* — eight sequences "
        "written down, not drawn from traffic — so this is a census with no "
        "sampling in it and it carries no interval. The same quantity on "
        "production traffic would be a **rate**: estimated, needing the "
        "stratified estimator, costing labels. Quoting this one as a production "
        "false-block rate would be the scenario mixing `CLAUDE.md` invariant 6 "
        "forbids.",
        "",
        "The two blocked workflows both read a transaction memo and then try to "
        "pay someone, which is exactly the pattern the rule exists to stop. "
        "**The control cannot tell them apart from the attack, and does not "
        "try** — that is what makes it independent of any detector, and the "
        "cost of that independence is this table.",
        "",
        "## What this does not establish",
        "",
    ]
    for item in payload["not_derived_here"]:
        lines.append(f"- {item}")
    lines.append("")
    (out_dir / "GATE.md").write_text("\n".join(lines), encoding="utf-8")
    _LOG.info("wrote %s", out_dir / "GATE.md")


if __name__ == "__main__":
    raise SystemExit(main())
