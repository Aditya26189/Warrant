"""The external matrix: detectors down, budgets across, every cell reproducible.

Rendered from the artifacts in ``results/external/`` rather than from anything
held in memory, so the table cannot say something the artifacts do not.

**How a refusal is written matters more than how a certification is written.**
A cell that could not be certified says what budget was asked for and what
evidence was available, and nothing else. It does not rank, does not compare,
and does not describe a detector as weak — a refusal at a tight budget on one
dataset is a statement about scope. Every cell carries the command that
reproduces it, because a claim about somebody else's software that they cannot
re-run is not a claim worth publishing (Phase 3 D36).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

__all__ = ["BUDGET_COLUMNS", "render_matrix"]

#: The budgets the table shows. The sweep runs all twenty; a table showing all
#: of them is unreadable, and these four span the range a buyer recognises.
BUDGET_COLUMNS = (0.01, 0.05, 0.10, 0.20)

NOT_RUN = "not run"


def _load(results_dir: Path) -> list[dict[str, Any]]:
    root = results_dir / "external"
    if not root.is_dir():
        return []
    payloads = []
    for path in sorted(root.glob("*/sweep.json")):
        payloads.append(json.loads(path.read_text(encoding="utf-8")))
    return payloads


def _cell(sweep: dict[str, Any], budget: float) -> str:
    """One cell: what the detector did at this budget, or why nothing is there."""
    if not sweep.get("is_measured", True):
        # The same refusal the rest of the reporting layer makes. A cell whose
        # inputs are a fixture prints no number at all.
        return "FIXTURE — not reported"
    points = {round(p["target_fpr"], 4): p for p in sweep["points"]}
    point = points.get(round(budget, 4))
    if point is None:
        return NOT_RUN
    if not point["certified"]:
        return "REFUSED"
    recall = point["recall"]
    holds = "" if point["lift_holds"] else " *"
    return (
        f"{recall['value']:.3f} [{recall['ci_low']:.3f}, {recall['ci_high']:.3f}]{holds}"
    )


def render_matrix(results_dir: Path, *, provenance: Optional[dict] = None) -> str:
    """Render ``results/external/MATRIX.md`` from the artifacts on disk."""
    payloads = _load(Path(results_dir))
    if not payloads:
        return "# External matrix\n\nNo runs found under `results/external/`.\n"

    lines = [
        "# The external matrix",
        "",
        "Third-party detectors, at their documented defaults, on public datasets "
        "this project did not construct. Our own detector is in the table on the "
        "same terms as the others.",
        "",
        "Each cell is **recall with its 95% interval** at the certified threshold "
        "for that false-positive budget. `REFUSED` means no threshold on that "
        "data could be certified at that budget. A `*` marks a point where lift's "
        "95% lower bound does not clear 1.0.",
        "",
    ]
    if provenance:
        lines += [
            f"Produced at commit `{(provenance.get('git_commit') or '')[:12]}`, "
            f"config `{provenance.get('config_hash', '?')}`, "
            f"dirty `{provenance.get('dirty')}`.",
            "",
        ]

    header = "| detector | task | " + " | ".join(f"FPR {b:.2f}" for b in BUDGET_COLUMNS) + " |"
    lines += [header, "|---|---|" + "---|" * len(BUDGET_COLUMNS)]

    for payload in payloads:
        pairing = payload["pairing"]
        sweep = payload["sweeps"][0]
        cells = " | ".join(_cell(sweep, b) for b in BUDGET_COLUMNS)
        task = pairing["task"].split("?")[0].strip() + "?"
        lines.append(
            f"| `{pairing['detector']['id']}` | {task} | {cells} |"
        )

    lines += ["", "## What each row was run against", ""]
    for payload in payloads:
        pairing = payload["pairing"]
        sweep = payload["sweeps"][0]
        detector, dataset = pairing["detector"], pairing["dataset"]
        refused = [p["target_fpr"] for p in sweep["points"] if not p["certified"]]
        lines += [
            f"### `{pairing['id']}`",
            "",
            f"- **detector** `{detector['id']}` at version/revision "
            f"`{detector['version'][:16]}` ({detector['licence']}) — "
            f"[source]({detector['source_url']}), "
            f"[docs]({detector['documentation_url']})",
            f"- **configuration**: {detector['configuration']}",
            "- **tuning**: none. Run at the documented default above; no "
            "threshold or variant was chosen based on how it scored here.",
            f"- **dataset** `{dataset['id']}` at revision "
            f"`{dataset['revision'][:16]}`, split `{dataset['split']}`, licence "
            f"{dataset['licence']}, accessed {dataset['access_date']} — "
            f"[source]({dataset['source_url']})",
            f"- **evidence**: {sweep['n']} items, {sweep['n_positive']} positive, "
            f"{sweep['n_negative']} negative",
            f"- **reproduce**: `python scripts/23_certify_external.py --pairing "
            f"{pairing['id']}`",
        ]
        if dataset.get("note"):
            lines.append(f"- **note**: {dataset['note']}")
        if refused:
            lines += [
                "",
                f"> Refused at {len(refused)} of {len(sweep['points'])} budgets "
                f"(tightest certified: {min((p['target_fpr'] for p in sweep['points'] if p['certified']), default=float('nan')):.2f}). "
                "A refusal here means the evidence available at that budget could "
                "not support a certified threshold. It is a statement about what "
                "this dataset can support at that budget, not about the detector.",
            ]
        lines.append("")

    lines += [
        "## How to read this, and how not to",
        "",
        "**These are not rankings.** The rows answer different questions on "
        "different data; a number in one row is not comparable with a number in "
        "another. What is comparable within a row is the shape across budgets: "
        "how much recall survives as the false-positive budget tightens.",
        "",
        "**A refusal is not a defect.** It says the data available could not "
        "support a certified threshold at that budget. Tighter budgets need more "
        "clean negatives — 299 for 0.01 against 14 for 0.20 — and a detector "
        "refused at 0.01 on one dataset may certify comfortably at 0.05 on the "
        "same one.",
        "",
        "**Every detector ran at its documented default.** Nothing was tuned for "
        "this evaluation, in either direction. If you believe a configuration is "
        "wrong, the reproduction command for that row is above and the "
        "configuration it used is stated beside it.",
        "",
    ]
    return "\n".join(lines)
