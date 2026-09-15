"""The summary a person reads in a terminal.

Written to make a **refusal legible as a result**. A tool that prints a warrant
in confident green and a refusal in the same shape as a stack trace teaches its
user that refusals are malfunctions, and the entire proposition here is that
they are not. So both outcomes get the same layout, the same amount of detail,
and a refusal additionally gets the one thing a user actually wants next: what
it would take.
"""

from __future__ import annotations

from typing import Optional

from ..model import Metric, WarrantStatus
from .certify import CertificationResult

__all__ = ["render_frontier", "render_plan", "render_recheck", "render_summary"]

# ASCII only, deliberately. The first run of this on Windows died with
# UnicodeEncodeError: the console's cp1252 codepage cannot encode a box-drawing
# character, and a stranger following the quickstart would have hit a traceback
# instead of a warrant. Output that cannot be printed is output that does not
# work, whatever it looks like on the machine it was written on.
_RULE = "-" * 66


def _metric_line(label: str, metric: Optional[Metric], digits: int = 4) -> str:
    if metric is None:
        return f"  {label:<14} n/a"
    return f"  {label:<14} {metric.render(digits)}"


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _label_lines(result: CertificationResult) -> list[str]:
    """How far the certificate depends on its labels (DECISIONS 197)."""
    lines: list[str] = []
    sensitivity = result.label_sensitivity
    if sensitivity is not None and sensitivity.computed:
        unit = sensitivity.unit
        noun = "group" if unit == "groups" else "item"
        lines += ["", f"  If the labels are wrong (counted in {unit}):"]
        lines.append(
            f"    as labelled, the budget clears at {_pct(sensitivity.confidence_as_labelled)} confidence"
        )
        for ladder, what, pool in (
            (sensitivity.flagged_clean, f"a flagged positive {noun} that is really clean",
             f"flagged positive {unit}"),
            (sensitivity.unflagged_positive, f"an unflagged negative {noun} that is really positive",
             f"unflagged negative {unit}"),
        ):
            lines.append(f"    {what}:")
            if ladder.confidence_if_one is None:
                lines.append("      none of those in this file")
                continue
            crossings = [
                f"below {level * 100:.0f}% at {count}" if count is not None
                else f"never below {level * 100:.0f}%"
                for level, count in ladder.errors_below.items()
            ]
            lines.append(
                f"      one costs "
                f"{(sensitivity.confidence_as_labelled - ladder.confidence_if_one) * 100:.1f} "
                f"points, to {_pct(ladder.confidence_if_one)} (bound {ladder.bound_if_one:.4f})"
            )
            lines.append(f"      {', '.join(crossings)} of the {ladder.limit} {pool}")
        lines.append(
            "    That is the confidence the budget still clears at, not a probability"
        )
        lines.append("    that the detector is within budget.")
    review = result.second_review
    if review is None:
        lines += [
            "",
            "  No label_2 column: agreement between reviewers is not measured. This",
            "  certificate is exact about these labels and silent about whether they",
            "  are right.",
        ]
        return lines
    agreement = review.agreement
    lines += ["", "  Second reviewer (label_2), which changes nothing above:"]
    if agreement.kappa is None:
        lines.append(f"    kappa undefined over {review.n_pairs} pairs: {agreement.undefined_reason}")
    else:
        lines.append(
            f"    kappa {agreement.kappa:.3f} [{agreement.ci_low:.3f}, {agreement.ci_high:.3f}] "
            f"over {review.n_pairs} pairs ({review.pairs_by_label[0]} labelled 0, "
            f"{review.pairs_by_label[1]} labelled 1)"
        )
    disputes = review.disputes
    if disputes is not None:
        lines.append(
            f"    {disputes.flagged_positives_disputed} of {disputes.reviewed_flagged_positives} "
            f"double-labelled flagged positives called clean"
        )
        lines.append(
            f"    {disputes.unflagged_negatives_disputed} of {disputes.reviewed_unflagged_negatives} "
            f"double-labelled unflagged negatives called positive"
        )
        lines.append(
            f"    if every dispute is a primary error: "
            f"{_pct(disputes.confidence_if_disputes_are_errors)} (a worst case, not the truth)"
        )
        if disputes.confidence_at_upper_bounds is not None:
            level = (1 - review.alpha) * 100
            joint = (1 - 2 * review.alpha) * 100
            lines += [
                "    whole file, if the double-labelled items were sampled at random:",
                f"      at most {disputes.flagged_upper_bound} of {disputes.flagged_positives} flagged "
                f"positives (n {disputes.reviewed_flagged_positives}) and "
                f"{disputes.unflagged_upper_bound} of {disputes.unflagged_negatives} unflagged "
                f"negatives (n {disputes.reviewed_unflagged_negatives}) disputed,",
                f"      each at {level:.0f}%, both together at >= {joint:.0f}%",
                f"      if all of those were errors: {_pct(disputes.confidence_at_upper_bounds)}",
                "      (a sensitivity at those bounds, not a joint confidence)",
            ]
            if (disputes.reviewed_flagged_positives < disputes.flagged_positives
                    or disputes.reviewed_unflagged_negatives < disputes.unflagged_negatives):
                lines.append(
                    "      the bounds are as wide as the double-labelled counts make them;"
                )
                lines.append("      double-labelling more of each pool narrows them")
        else:
            lines.append(f"    whole file: not computed -- {disputes.upper_bound_reason}")
    for warning in review.warnings:
        lines.append(f"    warning: {warning}")
    return lines


def render_summary(result: CertificationResult) -> str:
    """Render one certification for a terminal."""
    lines = [
        _RULE,
        f"  WARRANT: {result.status.value}",
        _RULE,
        "",
        f"  input          {result.source}",
        f"  items          {result.n}  ({result.n_positive} positive, "
        f"{result.n_negative} negative)",
    ]
    if result.grouped:
        lines.append(
            f"  units          {result.n_units} groups - certification and "
            "resampling both happen at group level"
        )
    lines += [
        f"  base rate      {result.base_rate:.4f}",
        f"  budget         FPR <= {result.budget:.4f} at "
        f"{(1 - result.alpha) * 100:.0f}% confidence",
    ]
    if result.selection:
        # DECISIONS 195: which level governs which test, where the reader looks.
        selection = result.selection
        lines += [
            f"  picked from    a frontier of {len(selection['grid'])} budgets: this certificate "
            f"is at alpha {selection['row_alpha']:.4g},",
            f"                 so the pick holds; rechecks, plans and chains run at "
            f"alpha {selection['family_alpha']:g}",
        ]
    lines += [
        "",
    ]

    if result.status is WarrantStatus.REFUSED:
        lines += [
            "  REFUSED. The evidence does not support a warrant at this budget.",
            "",
            f"  {result.reason}",
            "",
            "  What would change it:",
            f"    * {result.min_units_required} clean negative units are needed "
            f"to certify FPR <= {result.budget:.4f}; this file has "
            f"{result.negative_units}.",
            "    * A looser budget needs fewer: the requirement scales as "
            "log(alpha)/log(1-budget).",
            "",
            "  This is the tool working. A detector that cannot be certified on",
            "  the evidence provided is a fact worth having before it ships, not",
            "  an error in the measurement.",
        ]
        lines += _label_lines(result) + [_RULE, ""]
        return "\n".join(lines)

    lines += [
        "  CERTIFIED.",
        "",
        f"  {result.reason}",
        "",
        f"  threshold      {result.threshold:.6f}",
        f"  FPR bound      {result.fpr_upper_bound:.4f}  "
        f"({result.false_positives_at_threshold} false positive(s) on "
        f"{result.negative_units} negative units)",
        f"  flagged        {result.n_flagged} of {result.n} items",
        "",
        "  What the detector does at that threshold:",
        _metric_line("recall", result.recall),
        _metric_line("precision", result.precision),
        _metric_line("flag rate", result.flag_rate),
        _metric_line("lift", result.lift, 3),
    ]
    if result.lift is not None and result.lift_ceiling:
        share = result.lift.value / result.lift_ceiling
        lines.append(
            f"                 ceiling {result.lift_ceiling:.2f} at this base "
            f"rate - the detector reaches {share * 100:.0f}% of it"
        )
    if result.metrics_absent_reason:
        lines += ["", f"  note: {result.metrics_absent_reason}"]
    lines += _label_lines(result)

    lines += [
        "",
        "  Every rate carries a 95% interval. Recall and precision are reported",
        "  together and neither is quotable alone.",
        _RULE,
        "",
    ]
    return "\n".join(lines)


def _recheck_label_lines(result) -> list[str]:
    """How many wrong labels would have made this recheck revoke (DECISIONS 198)."""
    lines: list[str] = []
    sensitivity = result.label_sensitivity
    if sensitivity is None:
        return lines
    lines += ["", "  If the labels are wrong:"]
    if not sensitivity.computed:
        lines.append(f"     {sensitivity.reason}.")
    else:
        unit = sensitivity.unit
        lines.append(
            f"     this file revokes at {sensitivity.revokes_at_count} false positives of "
            f"{sensitivity.n} negative {unit}; it has {sensitivity.k}."
            if sensitivity.revokes_at_count is not None else
            f"     no count of false positives on {sensitivity.n} negative {unit} revokes."
        )
        for count, what, pool in (
            (sensitivity.flagged_clean_to_revoke,
             "flagged positives that are really clean", sensitivity.flagged_positives),
            (sensitivity.unflagged_positive_to_revoke,
             "unflagged negatives that are really positive", sensitivity.n - sensitivity.k),
        ):
            lines.append(
                f"     it would have revoked with {count} {what} (of {pool})"
                if count is not None else
                f"     no number of {what} (of {pool}) would have revoked it"
            )
        lines += [
            "     A recheck that does not revoke is still an absence of evidence of",
            "     breach; these counts say how far this file is from showing one, not",
            "     that none exists.",
        ]
    review = result.second_review
    if review is None:
        return lines
    agreement = review.agreement
    lines += ["", "  Second reviewer (label_2), which changes no verdict:"]
    if agreement.kappa is None:
        lines.append(f"     kappa undefined over {review.n_pairs} pairs: {agreement.undefined_reason}")
    else:
        lines.append(
            f"     kappa {agreement.kappa:.3f} [{agreement.ci_low:.3f}, {agreement.ci_high:.3f}] "
            f"over {review.n_pairs} pairs"
        )
    disputes = review.disputes
    if disputes is None:
        lines.append(f"     disputes: {review.disputes_reason}")
    elif not hasattr(disputes, "lower_bound_if_disputes_are_errors"):
        lines += [
            f"     {disputes.flagged_negatives_label_2_calls_positive} of "
            f"{disputes.reviewed_flagged_negatives} double-labelled false positives "
            "called positive by label_2.",
            "     The revocation stands; no bound is recomputed from those.",
        ]
    else:
        revokes = (
            "would have revoked" if disputes.revokes_if_disputes_are_errors
            else "would not have revoked"
        )
        lines += [
            f"     {disputes.flagged_positives_disputed} of {disputes.reviewed_flagged_positives} "
            "double-labelled flagged positives called clean;",
            f"     {disputes.unflagged_negatives_disputed} of {disputes.reviewed_unflagged_negatives} "
            "double-labelled unflagged negatives called positive",
            f"     if every dispute is a primary error, the lower bound is "
            f"{disputes.lower_bound_if_disputes_are_errors:.4f} and {revokes}",
        ]
        if disputes.lower_bound_at_upper_bounds is not None:
            whole = (
                "would have revoked" if disputes.revokes_at_upper_bounds
                else "would not have revoked"
            )
            lines += [
                "     whole file, if the double-labelled items were sampled at random:",
                f"     at most {disputes.flagged_upper_bound} of {disputes.flagged_positives} flagged "
                f"positives and {disputes.unflagged_upper_bound} of {disputes.unflagged_negatives} "
                f"unflagged negatives disputed",
                f"     (each at {(1 - review.alpha) * 100:.0f}%, both together at >= "
                f"{(1 - 2 * review.alpha) * 100:.0f}%);",
                f"     lower bound {disputes.lower_bound_at_upper_bounds:.4f}, {whole} "
                "(a sensitivity at those bounds, not a joint confidence)",
            ]
        else:
            lines.append(f"     whole file: not computed -- {disputes.upper_bound_reason}")
    for warning in review.warnings:
        lines.append(f"     warning: {warning}")
    return lines


def render_recheck(result, chain=None) -> str:
    """Render a recheck for a terminal.

    The two failure modes are printed separately and never merged into one
    score. "Your bound broke" and "your traffic moved" call for different
    actions -- re-certify versus investigate -- and collapsing them into a single
    health number is how a dashboard stays green while the thing it watches stops
    being true.
    """
    from ..model import WarrantStatus

    lines = [
        _RULE,
        f"  RECHECK: {result.status.value}",
        _RULE,
        "",
        f"  warranted     FPR <= {result.budget:.4f} at threshold "
        f"{result.threshold:.6f}",
        f"  new file      {result.n_now} items ({result.n_negative_now} negative"
        + (" clusters, each counted once" if result.unit == "cluster" else "") + ")",
        "",
        "  1. Does the bound still hold?",
    ]
    if result.bound_still_holds is None:
        lines.append("     UNTESTABLE - the new file has no negatives.")
    else:
        verdict = "HOLDS" if result.bound_still_holds else "BROKEN"
        lines += [
            f"     {verdict}. Measured FPR {result.achieved_fpr_now:.4f} against "
            f"a {result.budget:.4f} promise",
            f"     (95% interval {result.fpr_lower_bound_now:.4f} to "
            f"{result.fpr_upper_bound_now:.4f}).",
            "     Revocation turns on the LOWER bound: the promise is broken",
            "     when the data shows the rate exceeds it, not when a fresh",
            "     sample merely fails to re-prove it.",
        ]
        # The cost of that asymmetry, printed with every verdict including the
        # good ones. Revoking only on proof leaves a dead zone between the
        # budget and this floor, and a VALID that does not say how wide the zone
        # is overclaims in exactly the way the lower-bound test was introduced
        # to stop.
        if result.detectable_floor is not None:
            lines += [
                "",
                f"     What this file could have caught: an observed rate of "
                f"{result.detectable_floor:.4f} or above.",
                f"     Between {result.budget:.4f} and that floor, a real breach "
                f"returns VALID -- and that",
                "     is an absence of evidence, not evidence of absence.",
            ]
            if result.power_against_1_5x_budget is not None:
                lines.append(
                    f"     A detector truly at {result.budget * 1.5:.4f} would be "
                    f"revoked by this file with probability "
                    f"{result.power_against_1_5x_budget:.2f}."
                )
            needed = result.negatives_for_tighter_floor
            # Only when it is a shortfall. Telling someone they need 628
            # negatives when they brought 900 reads as a deficiency and is not
            # one; the lines above already say what this file can catch.
            if needed and needed > result.n_negative_now:
                chance = (
                    f"{result.recheck_power:.2f}"
                    if result.recheck_power is not None
                    else "the declared power"
                )
                lines.append(
                    f"     To catch it with probability {chance} "
                    f"you would need {needed} clean negative {result.unit}s; this file has "
                    f"{result.n_negative_now}."
                )
        else:
            lines += [
                "",
                "     No observed rate at this sample size could establish a",
                "     breach at all. This recheck cannot revoke, whatever the",
                "     detector does.",
            ]

    lines += ["", "  2. Has the distribution moved?"]
    if not result.drift_assessed:
        lines.append(f"     NOT ASSESSED - {result.drift_not_assessed_reason}.")
    else:
        moved = "beyond" if result.psi_beyond_noise else "within"
        lines += [
            f"     PSI {result.psi:.4f}, {moved} this sample's own noise level "
            f"of {result.psi_null_p95:.4f}.",
            "     The noise level is simulated at this file's size, not read off",
            "     the 0.10/0.25 bands, which are not scale-free.",
        ]
        if result.psi_bins_smoothed:
            lines.append(
                f"     {result.psi_bins_smoothed} live bin(s) empty where the "
                f"reference had mass, floored at eps={result.psi_epsilon:g}."
            )
        if result.psi_driven_by_smoothing:
            lines += [
                "     Most of that index comes from those empty bins, so it is a",
                "     statement about MISSING DATA in a region rather than a",
                "     measured shift. The smoothing constant sets its size.",
            ]

    lines += _recheck_label_lines(result)

    if chain is not None:
        state = chain.state
        lines += [
            "",
            "  3. The chain of rechecks (DECISIONS 193)",
            f"     link {state.sequence}: {chain.units_fed:,} of this file's "
            f"{chain.units_in_file:,} clean-negative units fed.",
            f"     statistic {state.mean_statistic:,.1f}; revokes at "
            f"{state.threshold:,.0f} ({state.horizon_units:,} units / alpha "
            f"{state.alpha:g}).",
            f"     {state.units_consumed:,} of {state.horizon_units:,} units consumed.",
            "     Over the whole chain, a detector keeping its promise is revoked",
            f"     with probability at most {state.alpha:g} -- for the chain as kept.",
            "     Keep every record: a fresh chain started after a bad result",
            "     spends that guarantee.",
        ]
        if chain.units_not_consumed:
            lines.append(
                f"     {chain.units_not_consumed:,} unit(s) not consumed: past the "
                "horizon, or after the chain revoked."
            )
    lines += ["", f"  {result.reason}", ""]
    if result.status is WarrantStatus.REVOKED:
        lines += [
            "  A revoked warrant is not a broken tool. It is the product doing",
            "  the one thing a static report cannot: telling you the number you",
            "  were relying on has stopped being true.",
            "",
        ]
    lines += [_RULE, ""]
    return "\n".join(lines)


def render_frontier(points, *, n_positive: int, n_negative: int) -> str:
    """The curve, in exact counts.

    No interval appears here and none is missing: every column is a count or a
    bound, not an estimate. Rates come from certifying at a chosen budget, which
    costs one bootstrap instead of twenty.
    """
    lines = [
        _RULE,
        "  THE FRONTIER: what each budget buys",
        _RULE,
        "",
        f"  {n_positive} positive items, {n_negative} clean negatives.",
        "",
        "  budget   threshold   FPR bound   flagged   caught   missed   false+",
        "  " + "-" * 64,
    ]
    for p in points:
        if not p.certified:
            lines.append(
                f"  {p.budget:<7.3f}  REFUSED - needs {p.min_negatives_required} "
                + (
                    f"independent negative clusters, this file has {p.negative_units}"
                    if p.grouped
                    else f"clean negatives, this file has {n_negative}"
                )
            )
            continue
        lines.append(
            f"  {p.budget:<7.3f}  {p.threshold:<10.5f}  {p.fpr_upper_bound:<10.4f}  "
            f"{p.n_flagged:<8d}  {p.true_positives:<7d}  {p.missed:<7d}  "
            f"{p.false_positives:<d}"
        )

    lines += [
        "",
        "  Every column above is EXACT -- a count of this file, or a bound. None",
        "  is an estimate, so none carries an interval and none is missing one.",
        "",
        *(
            [
                f"  Every certified row holds at {100 * (1 - points[0].family_alpha):.0f}% confidence AT ONCE:",
                f"  each was certified at alpha {points[0].row_alpha:.4g}, the family level split",
                f"  across {len(points)} budgets. So you may choose a row after reading them",
                "  all, and the row you choose still holds. `certify --budget` does not",
                "  make that adjustment: its level holds for a budget chosen BEFORE",
                "  looking at this file.",
                "",
            ]
            if points and points[0].row_alpha is not None
            else []
        ),
        "  Recall and precision are rates. They are estimated, they need a",
        "  bootstrap, and they come with a 95% interval:",
        "",
        "      warrant certify --input <file> --budget <one of the above>",
        "",
        "  Reading the table: a tighter budget promises fewer false positives and",
        "  catches less. The row to pick is the one whose 'missed' you can live",
        "  with at a 'false+' you can afford.",
        _RULE,
        "",
    ]
    return "\n".join(lines)


def render_plan(plan) -> str:
    """What keeping the warrant true costs, and on whose numbers.

    A refusal gets the same layout as a plan, for the reason at the top of this
    module. It also gets the thing a refused plan is actually for: the list of
    things that would have to change, since "not detectable" is a statement
    about the budget and the confidence level, not about the user.
    """
    declared = plan.declared_inputs
    lines = [
        _RULE,
        "  THE PRICE OF KEEPING IT TRUE",
        _RULE,
        "",
        f"  Certified budget          {plan.budget:.4g}",
        f"  Breach you want to catch  {plan.breach_rate:.4g}",
        f"  Confidence (alpha)        {plan.alpha:.3g}",
        f"  Chance of catching it     {plan.power:.2g}",
        f"  Share of traffic negative {declared.get('negative_share', float('nan')):.3g}",
        "",
    ]

    if not plan.feasible:
        lines += [
            "  REFUSED -- no sample size detects this.",
            "",
            *_wrap(plan.refusal_reason),
            "",
            "  A refusal here is a statement about the question, not about you:",
            "  the gap between the breach and the budget is narrower than the",
            "  confidence level can resolve at any sample size worth collecting.",
            _RULE,
            "",
        ]
        return "\n".join(lines)

    floor = plan.detection_floor
    lines += [
        f"  ONE RECHECK NEEDS {plan.negatives_per_recheck:,} CLEAN NEGATIVES",
        f"  which means labelling about {plan.items_per_recheck:,} items, at the",
        "  negative share declared above.",
        "",
        f"  If the true rate has reached {plan.breach_rate:.4g}, that sample revokes",
        f"  with probability {plan.power_at_breach:.3f}.",
    ]
    if floor is not None:
        lines += [
            f"  It revokes on an observed rate of {floor:.4f} or higher. A true",
            "  breach produces one only as often as the probability above says.",
        ]
    lines += [
        "",
        "  The chance of catching a true breach, and the sample it takes:",
        "",
        *[
            f"      {rung:.1f}   "
            + (f"{size:>9,} negatives" if size is not None else "    not reachable")
            for rung, size in plan.sizes_by_power
        ],
        "",
        "  At 0.5 a recheck misses a real breach as often as it catches one.",
        "",
        "  WHAT A YEAR COSTS",
        "",
        *[option.render() for option in plan.cadences],
        "",
        "  'false revocation' is the chance that at least one of the year's",
        "  rechecks revokes a detector sitting exactly at its budget. One",
        f"  recheck does so with probability {plan.false_revocation_per_recheck:.4f}; a year of",
        "  them compounds it. Assumes a fresh sample for every recheck.",
        "",
        "  CHAINED, the year is one test instead of many (DECISIONS 193):",
        "",
        *[
            f"      {option.name:<13} warrant recheck --horizon-labels "
            f"{option.chain_horizon_units}"  # no separator: the line is a command to copy
            for option in plan.cadences
            if option.chain_horizon_units is not None
        ],
        "",
        "  A chain revokes a detector that kept its promise with probability at",
        f"  most {plan.alpha:.3g} over that many negatives, at any cadence. How soon it",
        "  catches a real breach depends on when the breach starts and was",
        "  simulated for one setting only; no figure is quoted here for yours.",
        "",
        "  N counts clean negatives fed to the chain, not rechecks or weeks. The",
        "  figures above assume every recheck brings the negatives sized here;",
        "  a file with more ends the chain sooner, one with fewer later, and",
        "  unit ids must be unique across every file of the chain.",
        "",
        "  No cadence is recommended, and that is not an omission. How often to",
        "  recheck depends on how fast your inputs move, which is the thing you",
        "  do not know and the reason rechecking exists. More rechecks catch a",
        "  breach sooner and revoke a sound detector more often; a default here",
        "  would be a number with no evidence behind it, printed next to numbers",
        "  that have some.",
        "",
        "  Every figure above is EXACT arithmetic. None of it is measured, so",
        "  none of it carries an interval and none is missing one. What it rests",
        "  on is declared:",
        "",
        *[f"      {name} = {value:g}" for name, value in declared.items()],
        "",
        "  Get one of those wrong and every number here is wrong in proportion.",
        "  The negative share is the usual one: a plan built on 0.9 when the",
        "  truth is 0.6 understates the labelling by half.",
        _RULE,
        "",
    ]
    return "\n".join(lines)


def _wrap(text: str, width: int = 64) -> list[str]:
    """Reflow one paragraph to the block width, indented to match."""
    import textwrap

    return ["  " + line for line in textwrap.wrap(text, width=width)]
