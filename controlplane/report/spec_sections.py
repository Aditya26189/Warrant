"""The six `SPEC.md` §11 sections `RESULTS.md` was missing.

§11 is titled *"What `results/RESULTS.md` must contain"* and lists twelve items.
`CLAUDE.md`'s definition of done names the same document. Audited for the first
time in ``DECISIONS.md`` 164: **six of twelve were present**, and three of those
six had arrived four days earlier with the price list.

**Every absent item already had a committed artifact.** The eval-set registry is
``results/evalset_build.json``; the tier ladder is ``results/tier_ladder.json``;
the controls are inside every ``validation-*.json``; routing is in
``warrant_matrix.json``; the Presidio sequence is ``results/detectors.json``;
the gate is ``results/gate/gate.json``. Nothing was missing except the
rendering — the evidence was gathered, committed and verified, and the document
that exists to present it did not mention it.

Every section here reads its artifact and **states its absence** when the
artifact is not there, naming the script that writes it. The same rule
:mod:`controlplane.report.price_list` follows, and for the same reason: a
renderer that silently drops a section produces a document indistinguishable
from one where the section was never required.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

__all__ = ["spec_section_11_sections"]


def _load(results_dir: Path, *parts: str) -> Optional[dict[str, Any]]:
    path = results_dir.joinpath(*parts)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _absent(script: str) -> str:
    return (
        f"Not generated in this run. `{script}` writes the artifact behind it; "
        "until it has been run this section has no numbers and says so rather "
        "than being dropped."
    )


def _interval(metric: Optional[dict[str, Any]]) -> str:
    """A metric as ``value [low, high] (n=...)``, or an honest absence."""
    if not isinstance(metric, dict) or metric.get("value") is None:
        return "—"
    value = metric["value"]
    low, high = metric.get("ci_low"), metric.get("ci_high")
    n = metric.get("n")
    if low is None or high is None:
        return f"{value:.4f}" + (f" (n={n:,})" if n else "")
    return f"{value:.4f} [{low:.4f}, {high:.4f}]" + (f" (n={n:,})" if n else "")


def _evalset_registry(results_dir: Path) -> str:
    """§11.2 — IDs, hashes, sizes, base rates."""
    document = _load(results_dir, "evalset_build.json")
    if document is None:
        return _absent("python scripts/01_build_evalsets.py --config config.yaml")
    sets = document.get("sets") or []
    if not sets:
        return "The artifact is present and lists no eval sets."
    lines = [
        "Every set is content-hashed. **Changing one creates a new ID**, so it "
        "inherits no warrants (`CLAUDE.md` invariant 9).",
        "",
        "| eval set | envelope | items | base rate | content hash |",
        "|---|---|---|---|---|",
    ]
    for entry in sets:
        base = entry.get("base_rate")
        lines.append(
            f"| `{entry.get('eval_set_id','?')}` | "
            f"`{entry.get('envelope_id','—')}` | "
            f"{entry.get('n_items','—')} | "
            f"{base:.4f} | " if base is not None else
            f"| `{entry.get('eval_set_id','?')}` | "
            f"`{entry.get('envelope_id','—')}` | "
            f"{entry.get('n_items','—')} | — | "
        )
        lines[-1] += f"`{str(entry.get('content_hash',''))[:16]}…` |"
    return "\n".join(lines)


def _tier_ladder(results_dir: Path) -> str:
    """§11.4 — the ladder on each envelope, with intervals."""
    document = _load(results_dir, "tier_ladder.json")
    if document is None:
        return _absent("python scripts/02_validate.py --config config.yaml")
    rungs = document.get("rungs") or {}
    if not rungs:
        return "The artifact is present and holds no rungs."
    lines = [
        f"Envelope `{document.get('eval_set_id','?')}`, base rate "
        f"{document.get('base_rate', float('nan')):.4f}. What each access tier "
        "buys, measured rather than assumed — **every rate carries its "
        "interval and its `n`** (`CLAUDE.md` invariant 4).",
        "",
        "| rung | tier | status | AUROC | recall | precision | flag rate |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in document.get("variants") or sorted(rungs):
        rung = rungs.get(name) or {}
        metrics = rung.get("metrics") or {}
        status = rung.get("warrant_status", "—")
        mark = "**REFUSED**" if status == "REFUSED" else status
        lines.append(
            f"| `{name}` | {rung.get('access_tier','—')} | {mark} | "
            f"{_interval(metrics.get('auroc'))} | "
            f"{_interval(metrics.get('recall'))} | "
            f"{_interval(metrics.get('precision'))} | "
            f"{_interval(metrics.get('flag_rate'))} |"
        )
    return "\n".join(lines)


def _controls(results_dir: Path) -> str:
    """§11.5 — every control, including the fault case that must be rejected."""
    document = _load(results_dir, "validation-T1-last_token.json")
    if document is None:
        return _absent("python scripts/02_validate.py --config config.yaml")
    controls = document.get("controls") or []
    if not controls:
        return "The artifact is present and records no controls."
    lines = [
        "Five controls run on every validation. **Two are negative controls** — "
        "they assert this pipeline produces a null result when there is no "
        "signal, because a pipeline that cannot fail cannot be trusted when it "
        "succeeds. One is a deliberate fault that must be **rejected**.",
        "",
        "| control | passed | measured | expected |",
        "|---|---|---|---|",
    ]
    for control in controls:
        passed = "yes" if control.get("passed") else "**NO**"
        measured = control.get("measured")
        shown = f"{measured:.4f}" if isinstance(measured, (int, float)) else "—"
        lines.append(
            f"| `{control.get('control','?')}` | {passed} | {shown} | "
            f"{control.get('expected','—')} |"
        )
    fault = next(
        (c for c in controls if c.get("control") == "padding_fault"), None
    )
    if fault and fault.get("detail"):
        lines += [
            "",
            "**The fault case, in full**, because it is the one a reader should "
            "check:",
            "",
            "> " + str(fault["detail"]),
        ]
    return "\n".join(lines)


def _routing(results_dir: Path) -> str:
    """§11.6 — the routing half, and the revocation half that does not exist."""
    document = _load(results_dir, "warrant_matrix.json")
    if document is None:
        return _absent("python scripts/03_matrix.py --config config.yaml")
    routing = document.get("routing") or []
    if not routing:
        return "The artifact is present and records no routing decisions."
    actions: dict[str, int] = {}
    for entry in routing:
        action = str(entry.get("action", "?"))
        actions[action] = actions.get(action, 0) + 1
    suspended = [r for r in routing if r.get("suspended_profile")]
    escalated = [r for r in routing if r.get("action") == "ESCALATE"]

    lines = [
        f"**{len(routing)} routing decisions** across the declared profiles and "
        "envelopes. Routing reads the **warrant**, never the score — an "
        "envelope with no valid warrant falls back rather than guessing.",
        "",
        "| action | decisions |",
        "|---|---|",
    ]
    for action, count in sorted(actions.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {action} | {count} |")
    lines += [
        "",
        f"**{len(escalated)} fell back to ESCALATE** because no detector held a "
        f"valid warrant on that envelope, and **{len(suspended)} suspended a "
        "profile** whose declared minimums nothing met. Both are the matrix "
        "refusing to route rather than routing to something unwarranted.",
    ]
    if escalated:
        example = escalated[0]
        lines += [
            "",
            f"> `{example.get('profile')}` on `{example.get('envelope_id')}`: "
            f"{example.get('reason','—')}",
        ]
    lines += [
        "",
        "> **The revocation half of this section is missing, and that is stated "
        "rather than implied.** `SPEC.md` §11.6 asks for *envelope violation "
        "detected, revocation, routing decision*. The routing decisions are "
        "above. **Nothing in `results/` records a live drift run that revoked a "
        "warrant**, because the drift machinery has never been pointed at a "
        "moving distribution with a warrant outstanding. The machinery is built "
        "and tested (`controlplane/drift/`, `warrant recheck`); the trace is "
        "not measured. `DECISIONS.md` 164, OPEN.",
    ]
    return "\n".join(lines)


def _presidio(results_dir: Path) -> str:
    """§11.10 — the three-configuration sequence."""
    document = _load(results_dir, "detectors.json")
    if document is None:
        return _absent("python scripts/09_detectors.py --config config.yaml")
    runs = document.get("runs") or []
    if not runs:
        return "The artifact is present and records no runs."
    lines = [
        "The same detector, three configurations, one yardstick. **Stock "
        "Presidio is refused a warrant** on the Hinglish PII set — the refusal "
        "is the result, and the measured recall is in the reason.",
        "",
        "| configuration | eval set | status | recall | precision | FPR on hard negatives |",
        "|---|---|---|---|---|---|",
    ]
    for run in runs:
        metrics = run.get("metrics") or {}
        status = run.get("warrant_status", "—")
        mark = f"**{status}**" if status == "REFUSED" else status
        lines.append(
            f"| `{run.get('detector_id','?')}` | `{run.get('eval_set_id','?')}` | "
            f"{mark} | {_interval(metrics.get('recall'))} | "
            f"{_interval(metrics.get('precision'))} | "
            f"{_interval(metrics.get('fpr_hard_negatives'))} |"
        )
    refused = [r for r in runs if r.get("warrant_status") == "REFUSED"]
    if refused:
        reason = refused[0].get("status_reason")
        if reason:
            lines += ["", "**The refusal, in its own words:**", "", "> " + str(reason)]
    return "\n".join(lines)


def _gate(results_dir: Path) -> str:
    """§11.11 — the gate, including the detector-nulled case."""
    document = _load(results_dir, "gate", "gate.json")
    if document is None:
        return _absent("python scripts/27_gate.py --config config.yaml")
    head = document.get("headline") or {}
    evidence = document.get("no_detector_evidence") or {}
    cost = document.get("cost") or {}
    injection = document.get("injection") or {}
    lines = [
        "Everything else in this document measures a detector. **This is the "
        "part that assumes the detector loses.**",
        "",
        "**The detector-nulled case**, which `docs/TASKS.md` Phase 9 names as the "
        "gate's own gate: every rule-1 and rule-2 decision computed twice, once "
        "with a detector reporting `CRITICAL` and `CONFIDENT_POSITIVE` and once "
        "with every detector input `None`.",
        "",
        "| | |",
        "|---|---|",
        f"| decisions reaching rule 1 or rule 2 | **{evidence.get('decisions_compared','—')}** |",
        f"| identical with and without a detector | **{evidence.get('identical','—')}** |",
        f"| mismatches | **{len(evidence.get('mismatches') or [])}** |",
        "",
        f"**The injection.** An instruction inside a transaction memo. No "
        f"detector flagged it (`detector_flagged = "
        f"{injection.get('detector_flagged')}`) and `transfer_funds` was refused "
        f"at step **{head.get('injection_blocked_at_step','—')}**, on the tool's "
        "declared reversibility plus three session flags.",
        "",
        f"**What it costs.** {cost.get('n_blocked','—')} of "
        f"{cost.get('n_workflows','—')} declared legitimate workflows are "
        f"blocked, all {cost.get('n_recoverable_with_new_session','—')} "
        "recovered by starting a new session. These counts are **EXACT**: the "
        "workflow set is declared, so it is a census with no sampling in it and "
        "no interval attaches.",
        "",
        "> **This is not a robustness claim and this project makes none.** Nasr "
        "et al., *The Attacker Moves Second* (arXiv:2510.09023), bypassed 12 "
        "published defences at above 90% attack success for most of them. The "
        "claim here is the smaller one that survives: defeating every detector "
        "in this system does not move those two rules.",
    ]
    return "\n".join(lines)


def spec_section_11_sections(results_dir: Path) -> list[tuple[str, str]]:
    """``(heading, body)`` pairs for the six §11 items that were missing.

    Args:
        results_dir: The ``results/`` directory holding the artifacts.

    Returns:
        Six sections, always. One whose artifact is missing names the script
        that writes it instead of disappearing.
    """
    return [
        ("Eval set registry", _evalset_registry(results_dir)),
        ("Tier ladder — what each level of access buys", _tier_ladder(results_dir)),
        ("Control results, including the fault that must be rejected", _controls(results_dir)),
        ("Routing, and the revocation trace that is missing", _routing(results_dir)),
        ("Presidio, three configurations", _presidio(results_dir)),
        ("The action gate, and the detector-nulled case", _gate(results_dir)),
    ]
