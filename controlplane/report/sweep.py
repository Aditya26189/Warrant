"""Rendering ``SWEEP.md``, with the same refusal to print fixture numbers.

The sweep is re-analysis, which is exactly the kind of output that acquires a
reader long after the run that produced it. So it renders under the rule the
rest of the reporting layer already follows (``DECISIONS.md`` 046): a sweep
whose envelope is not explicitly ``measured`` prints no numbers at all. Not
greyed, not footnoted — absent, with the reason in their place.

The verdict at the top is assembled from the sweep's own fields rather than
typed. ``CLAUDE.md`` invariant 8 says every number in a document is computed by
code; a three-sentence summary written by hand beside a computed table is the
place that rule fails quietly, because prose is where an unfavourable result
gets softened.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..model import Metric
from ..validation.fpr_sweep import FprSweep, SweepPoint

__all__ = ["SWEEP_FIXTURE_MARKER", "render_sweep", "verdict"]

_LOG = logging.getLogger(__name__)

#: What a cell reads when its numbers describe a generator rather than a model.
#: Phase 0 brief, D9.
SWEEP_FIXTURE_MARKER = "FIXTURE — not reported"

#: What a refused target reads. A refusal is a result and keeps its row.
REFUSED_MARKER = "REFUSED"


def _cell(metric: Optional[Metric], digits: int = 4) -> str:
    """One metric with its interval, or an honest absence."""
    if metric is None:
        return "n/a"
    return metric.render(digits)


def verdict(sweep: FprSweep) -> str:
    """The three sentences, assembled from measured fields.

    Every branch states what the data says, including when what it says is that
    the probe does not clear the bar. There is deliberately no branch that
    reports an unfavourable sweep as a partial success.
    """
    shipped_recall = sweep.shipped_recall
    shipped_text = (
        f"{shipped_recall.value:.4f}" if shipped_recall is not None else "n/a"
    )
    headline = sweep.headline

    if headline is None:
        return (
            f"Lift does not hold at any target FPR on the swept grid "
            f"({sweep.grid[0]:.2f} to {sweep.grid[-1]:.2f}): at every point the "
            f"lower bound of lift's 95% interval falls at or below "
            f"{1.0:.1f}, so no budget on this grid buys a detector that beats "
            f"flagging at random. Recall {shipped_text} at the shipped operating "
            f"point is therefore not a policy choice being held down by the "
            f"false-positive budget — loosening the budget does not produce a "
            f"warrantable detector on this envelope. The probe is weak on "
            f"{sweep.eval_set_id}, the FPR budget is not what is binding, and "
            f"the product is the refusal machinery rather than the detector."
        )

    recall = headline.recall
    recall_text = (
        f"{recall.value:.4f} [{recall.ci_low:.4f}, {recall.ci_high:.4f}]"
        if recall is not None
        else "n/a"
    )
    lift_text = (
        f"{headline.lift.value:.3f} [{headline.lift.ci_low:.3f}, "
        f"{headline.lift.ci_high:.3f}]"
        if headline.lift is not None
        else "n/a"
    )
    fraction = headline.lift_fraction_of_ceiling
    fraction_text = (
        f"{fraction * 100:.0f}% of the {headline.lift_ceiling:.2f} ceiling"
        if fraction is not None and headline.lift_ceiling is not None
        else "an unknown fraction of the ceiling"
    )
    dial = sweep.recall_is_a_dial

    first = (
        f"Lift holds at {len(sweep.holding_points)} of {len(sweep.grid)} swept "
        f"targets, the loosest being a target FPR of {headline.target_fpr:.2f}, "
        f"where the certified threshold achieves FPR {headline.achieved_fpr:.4f} "
        f"and lift {lift_text} — {fraction_text}."
    )
    second = (
        f"Recall there is {recall_text}, against {shipped_text} at the shipped "
        f"operating point."
    )
    if dial is True:
        third = (
            f"Recall {shipped_text} is a dial, not a ceiling: loosening the "
            f"false-positive budget lifts recall clear of the shipped point's "
            f"own 95% interval, so the number the product ships is a policy "
            f"choice and the honest form of the claim is a curve rather than a "
            f"point."
        )
    elif dial is False:
        third = (
            f"Recall {shipped_text} is a ceiling rather than a dial: even at the "
            f"loosest budget where lift still holds, recall does not clear the "
            f"upper bound of the shipped point's own 95% interval, so loosening "
            f"the budget buys nothing this sample can distinguish from where the "
            f"product already sits."
        )
    else:
        third = (
            "Whether recall is a dial or a ceiling cannot be decided from this "
            "sweep, because the shipped operating point's recall interval is "
            "unavailable to compare against."
        )
    return " ".join([first, second, third])


def _table(sweep: FprSweep) -> list[str]:
    """The grid, one row per target, refusals kept in place."""
    lines = [
        "| target FPR | threshold | achieved FPR | recall | precision | flag rate "
        "| lift | lift CI low > 1 | % of ceiling |",
        "|---:|---:|---:|---|---|---|---|:--:|---:|",
    ]
    for point in sweep.points:
        if not point.certified:
            lines.append(
                f"| {point.target_fpr:.2f} | {REFUSED_MARKER} | — | — | — | — | — "
                f"| — | — |"
            )
            continue
        fraction = point.lift_fraction_of_ceiling
        lines.append(
            "| {target:.2f} | {tau:.6f} | {fpr:.4f} | {recall} | {precision} "
            "| {flag} | {lift} | {holds} | {frac} |".format(
                target=point.target_fpr,
                tau=point.threshold,
                fpr=point.achieved_fpr,
                recall=_cell(point.recall),
                precision=_cell(point.precision),
                flag=_cell(point.flag_rate),
                lift=_cell(point.lift, 3),
                holds="yes" if point.lift_holds else "no",
                frac=f"{fraction * 100:.0f}%" if fraction is not None else "n/a",
            )
        )
    return lines


def _frontier(sweep: FprSweep) -> list[str]:
    """Recall against what recall costs, in the unit the budgets are written in.

    The sweep's first table answers "how much recall is available". This one
    answers "what does it cost", which is the axis the profiles are actually
    budgeted on — everything flagged routes to the expensive check, so the flag
    rate is the bill.
    """
    certified = [p for p in sweep.points if p.certified and p.recall is not None]
    if not certified:
        return []

    budgets = dict(sorted(sweep.profile_budgets.items(), key=lambda kv: kv[1]))
    lines = [
        "",
        "## The frontier: what recall costs",
        "",
        "Everything flagged routes to the expensive check, so the flag rate is "
        "the bill. Costed against the flag-rate budgets `config.yaml` actually "
        "declares:",
        "",
        "| profile | declared flag-rate budget |",
        "|---|---:|",
    ]
    lines += [f"| `{name}` | {budget:.2f} |" for name, budget in budgets.items()]
    lines += [
        "",
        f"> **These are envelope figures, not production costs.** Flag rate is "
        f"measured at base rate {sweep.base_rate:.4f}. Production traffic is "
        "nowhere near that, and the same threshold would flag a different share "
        "of it. Quoting a judge-call figure from here as a production cost puts "
        "a flag rate from one workload beside a base rate from another — the "
        "scenario-mixing error `CLAUDE.md` names. `DECISIONS.md` 132.",
        "",
        "| target FPR | recall | flag rate | judge calls / 1000 | lift | profiles within budget |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for point in certified:
        served = ", ".join(f"`{n}`" for n in point.profiles_within_budget) or "—"
        lines.append(
            "| {t:.2f} | {r} | {f:.4f} | {j:.0f} | {l:.3f} | {s} |".format(
                t=point.target_fpr,
                r=_cell(point.recall),
                f=point.flag_rate.value,
                j=point.judge_calls_per_1000,
                l=point.lift.value if point.lift else float("nan"),
                s=served,
            )
        )

    # The two ends of the trade, chosen by measured quantities rather than by
    # eye — and chosen only from points that clear the pre-registered bar.
    #
    # Without that restriction the "best lift" end selects target 0.01, where
    # lift is 2.166 because three items were flagged and all three were right.
    # Its interval is [0.000, 5.129]: the point fails the criterion this project
    # registered, and headlining it would be quoting the one number on the grid
    # that the bar exists to reject.
    holding = [p for p in certified if p.lift_holds]
    if not holding:
        return lines + [
            "",
            "### The two ends of the trade",
            "",
            "No point on this grid clears the pre-registered bar, so there is no "
            "operating point to recommend at either end. The rows above describe "
            "the shape of the curve and nothing more.",
        ]
    most_recall = max(holding, key=lambda p: p.recall.value)
    best_lift = max(
        (p for p in holding if p.lift is not None), key=lambda p: p.lift.value
    )
    lines += [
        "",
        "### The two ends of the trade",
        "",
        f"**Most recall available** — target {most_recall.target_fpr:.2f}: recall "
        f"{most_recall.recall.value:.4f}, costing "
        f"{most_recall.judge_calls_per_1000:.0f} judge calls per 1000 requests "
        f"({most_recall.flag_rate.value * 100:.1f}% of this envelope). Within "
        f"budget for: "
        + (", ".join(f"`{n}`" for n in most_recall.profiles_within_budget) or "no declared profile")
        + ".",
        "",
        f"**Best lift per flagged item** — target {best_lift.target_fpr:.2f}: lift "
        f"{best_lift.lift.value:.3f}"
        + (
            f" ({best_lift.lift_fraction_of_ceiling * 100:.0f}% of ceiling)"
            if best_lift.lift_fraction_of_ceiling is not None
            else ""
        )
        + f" at recall {best_lift.recall.value:.4f}, costing "
        f"{best_lift.judge_calls_per_1000:.0f} calls per 1000. Within budget for: "
        + (", ".join(f"`{n}`" for n in best_lift.profiles_within_budget) or "no declared profile")
        + ".",
        "",
        "The operating point is a business choice between the two, and this "
        "table is the whole of what the measurement can say about it. Which "
        "profile a point can actually serve is decided by the policy layer, "
        "which conjoins a recall floor and an FPR ceiling to the flag-rate "
        "budget; fitting the budget is necessary and not sufficient.",
    ]
    return lines


def _refusal_notes(sweep: FprSweep) -> list[str]:
    """Why each refused target was refused, in its own words."""
    refused = [p for p in sweep.points if not p.certified]
    if not refused:
        return []
    lines = ["", "### Refused targets", ""]
    for point in refused:
        lines.append(
            f"- **{point.target_fpr:.2f}** — {point.reason} "
            f"(have {point.n_units} independent units, need "
            f"{point.min_units_required})"
        )
    return lines


def render_sweep(
    sweep: FprSweep,
    *,
    provenance: dict[str, Any],
    superseded_by: Optional[str] = None,
) -> str:
    """Render one sweep to markdown, printing nothing if it is not measured.

    Args:
        sweep: The computed sweep.
        provenance: The provenance block of the run that produced it, so the
            commit and config travel with the table rather than beside it.
        superseded_by: Path of the sweep that replaces this one for any external
            claim. Rendered as a banner at the top rather than as a footnote:
            a reader who stops after the first table must not be able to quote
            a number this document no longer stands behind.

    Returns:
        Markdown.
    """
    commit = provenance.get("git_commit") or "unknown"
    dirty = provenance.get("dirty")
    # Identifiers and settings only. Nothing here is a function of the scores
    # or the labels, which is what lets the fixture branch below print it: the
    # class split and the base rate are properties of whatever produced the
    # arrays, so on a fixture they describe a generator we wrote and they live
    # in `measured` instead.
    head = [
        f"# FPR budget sweep — {sweep.eval_set_id} · {sweep.variant}",
        "",
        f"Re-analysis of frozen scores in `results/scores/{sweep.score_set_id}.json`. "
        "No inference was run: every number is a function of the committed "
        "labels, scores and question ids.",
        "",
        f"- commit `{commit[:12]}` · dirty `{dirty}` · config "
        f"`{provenance.get('config_hash', 'unknown')}`",
        f"- detector `{sweep.detector_id}` · envelope `{sweep.envelope_id}`",
        f"- certification: Clopper-Pearson one-sided upper bound at alpha "
        f"{sweep.alpha:.3f}, via `certify_fpr`",
        f"- intervals: percentile bootstrap, {sweep.bootstrap_samples} resamples "
        f"over questions, seed {sweep.seed}",
        (
            f"- thresholds certified on `{sweep.certified_on_score_set_id}`, "
            f"metrics measured on `{sweep.score_set_id}` — **out of sample**"
            if sweep.out_of_sample
            else f"- thresholds certified and metrics measured on the same set, "
            f"`{sweep.score_set_id}` — **in sample**"
        ),
    ]
    if superseded_by:
        # After the blank that follows the intro, not before it: a blockquote
        # butted against a paragraph is a rendering coin-flip.
        head[4:4] = [
            f"> **Superseded by `{superseded_by}`.** The thresholds below were "
            "certified on the same split they were scored on. The numbers are "
            "kept because they are the evidence for how little that biased "
            "them, and they are not the ones to quote.",
            "",
        ]
    # Appended to the same bullet list rather than started as a second one, so
    # removing it on the fixture path leaves a list rather than a gap.
    measured = [
        f"- n {sweep.n} ({sweep.n_positive} positive, {sweep.n_negative} negative) "
        f"· base rate {sweep.base_rate:.4f}",
    ]

    if not sweep.is_measured:
        # D9. The refusal is the whole output: a fixture sweep has a shape worth
        # knowing about and no numbers worth reading, and printing the shape
        # with the numbers removed is the only way to say both at once.
        return "\n".join(
            head
            + [
                "",
                f"## {SWEEP_FIXTURE_MARKER}",
                "",
                f"This sweep's envelope declares `data_source = "
                f"{sweep.data_source!r}`, so its numbers are not printed.",
                "",
                f"> {sweep.data_source_reason}",
                "",
                f"The grid ran to {len(sweep.grid)} points, which is the grid it "
                "was handed and not a measurement. Nothing else is printed: how "
                "many certified, the class split and the base rate are all "
                "functions of what the generator produced, and a count off a "
                "generator we wrote is still a number off a generator we wrote.",
                "",
            ]
        )

    lines = head + measured + [
        "",
        "## Verdict",
        "",
        verdict(sweep),
        "",
        "## The pre-registered criterion",
        "",
        "Lift *holds* at a target FPR when the **lower bound** of its 95% "
        "bootstrap interval is strictly greater than 1.0. Registered before any "
        "output was seen (Phase 0 brief, D6) and not adjusted afterwards.",
        "",
        "## Grid",
        "",
    ]
    lines += _table(sweep)
    lines += _refusal_notes(sweep)
    lines += _frontier(sweep)

    shipped = [
        "",
        "## The shipped operating point, for reference",
        "",
        f"- `{sweep.shipped_operating_point_id}` at threshold "
        f"{sweep.shipped_threshold:.6f}",
        f"- recall {_cell(sweep.shipped_recall)}",
        f"- precision {_cell(sweep.shipped_precision)}",
        f"- flag rate {_cell(sweep.shipped_flag_rate)}",
        f"- lift {_cell(sweep.shipped_lift, 3)}",
        "",
        "## What this sweep does not establish",
        "",
        "The threshold at each grid point is certified on the **same** frozen "
        "test split the recall is then measured on. The pipeline's discipline is "
        "stricter — selection on validation, test scored once — and only "
        "test-split scores are frozen, so that discipline could not be applied "
        "here without refitting the probe. `certify_fpr` reads the negatives "
        "only, so the positives that determine recall play no part in choosing "
        "the threshold; the bias is that the threshold tracks this sample's "
        "negative tail rather than the population's. Each recall above is "
        "therefore an in-sample figure and is not a warrant.",
        "",
    ]
    return "\n".join(lines + shipped)
