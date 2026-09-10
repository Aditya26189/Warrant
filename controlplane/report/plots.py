"""Plots. Every one carries the provenance of the numbers in it.

Two rules, both enforced here rather than remembered:

* **An estimated value is never drawn without its interval.** Invariant 4 is a
  rendering rule as much as a data rule, and a bar chart of point estimates is
  the most persuasive way to publish an unbacked claim.
* **A synthetic run is stamped as synthetic, on the figure.** A plot outlives
  the terminal it was produced in, and the caption is what someone reads six
  weeks later. ``DECISIONS.md`` 027.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import matplotlib
import numpy as np

matplotlib.use("Agg")  # no display on a Kaggle worker or in CI
import matplotlib.pyplot as plt  # noqa: E402

from ..model import MetricKind  # noqa: E402
from ..validation.ablation import TierLadder  # noqa: E402
from ..validation.fpr_sweep import FprSweep  # noqa: E402
from ..validation.roc import RocCurve  # noqa: E402
from ..validation.evalsets import SOURCE_SYNTHETIC  # noqa: E402

__all__ = ["plot_fpr_frontier", "plot_fpr_sweep", "plot_roc_operating_points", "plot_tier_ladder"]

_LOG = logging.getLogger(__name__)

_STATUS_COLOUR = {
    "VALID": "#2a7d4f",
    "REFUSED": "#b3261e",
    "STALE": "#b06f00",
    "REVOKED": "#7a2f8a",
}


def plot_tier_ladder(
    ladder: TierLadder,
    path: str | Path,
    *,
    metrics: tuple[str, ...] = ("auroc", "recall", "precision"),
    config_hash: Optional[str] = None,
    git_commit: Optional[str] = None,
) -> Path:
    """Draw the tier ladder with intervals, one panel per metric.

    Precision and recall appear together by default (invariant 5). AUROC is
    shown beside them with the base rate in the caption, because AUROC without a
    base rate is how an imbalanced dataset flatters a constant predictor.

    Args:
        ladder: The measured ladder.
        path: Output PNG path.
        metrics: Which metrics to panel. Each must be estimated — an exact count
            has no interval and does not belong on an interval plot.
        config_hash: Stamped into the caption.
        git_commit: Stamped into the caption.

    Returns:
        The path written.

    Raises:
        ValueError: If asked to plot an exact metric, which would be drawn as a
            bare point and read as an estimate.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    variants = [run.variant for run in ladder.runs]
    y = range(len(variants))

    fig, axes = plt.subplots(
        1, len(metrics), figsize=(5.2 * len(metrics), 0.6 * len(variants) + 3.2),
        sharey=True,
    )
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric_name in zip(axes, metrics, strict=True):
        for row, run in enumerate(ladder.runs):
            metric = ladder.metric(run.variant, metric_name)
            if metric.kind is not MetricKind.ESTIMATED:
                raise ValueError(
                    f"{metric_name} is {metric.kind.value}; an exact count has no "
                    "interval and would be drawn as a bare point, which reads as "
                    "an estimate (CLAUDE.md invariant 4)"
                )
            colour = _STATUS_COLOUR.get(run.warrant.status.value, "#555555")
            ax.errorbar(
                metric.value,
                row,
                xerr=[[metric.value - metric.ci_low], [metric.ci_high - metric.value]],
                fmt="o",
                color=colour,
                ecolor=colour,
                elinewidth=2,
                capsize=4,
                markersize=7,
            )
        ax.set_title(f"{metric_name}  (95% CI)")
        ax.grid(axis="x", alpha=0.25, linestyle=":")
        ax.set_axisbelow(True)
        if metric_name == "auroc":
            ax.axvline(0.5, color="#999999", linestyle="--", linewidth=1)
            ax.annotate(
                "chance", xy=(0.5, -0.7), fontsize=8, color="#777777", ha="center"
            )

    axes[0].set_yticks(list(y))
    axes[0].set_yticklabels(
        [
            f"{run.variant}\n{run.warrant.access_tier.name} · {run.warrant.status.value}"
            for run in ladder.runs
        ],
        fontsize=8,
    )
    axes[0].invert_yaxis()

    synthetic = ladder.data_source == SOURCE_SYNTHETIC
    title = f"Tier ladder — {ladder.eval_set_id}"
    if synthetic:
        title = f"[SYNTHETIC FIXTURE — NOT A MEASUREMENT]  {title}"
    fig.suptitle(title, fontsize=12, color="#b3261e" if synthetic else "#111111")

    caption_parts = [
        f"envelope {ladder.envelope_id}",
        f"base rate {ladder.base_rate:.4f}",
        f"n_test {ladder.runs[0].warrant.n_test}" if ladder.runs else "",
        f"data_source {ladder.data_source}",
    ]
    if config_hash:
        caption_parts.append(f"config {config_hash}")
    if git_commit:
        caption_parts.append(f"commit {git_commit[:8]}")
    fig.text(
        0.5,
        0.015,
        " · ".join(p for p in caption_parts if p),
        ha="center",
        fontsize=8,
        color="#666666",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(out, dpi=150)
    plt.close(fig)
    _LOG.info("wrote %s", out)
    return out


def plot_fpr_sweep(
    sweep: FprSweep,
    path: str | Path,
    *,
    config_hash: Optional[str] = None,
    git_commit: Optional[str] = None,
) -> Path:
    """Draw recall against target FPR, with lift on a second axis.

    Deliberately plain (Phase 0 brief, D10): matplotlib defaults, labelled axes,
    a title and a legend. Two things are not styling and so are drawn anyway —
    every estimate carries its 95% interval, which is a rendering rule rather
    than a preference, and the pre-registered ``lift = 1`` bar is drawn because
    a lift axis without it makes the reader estimate by eye the one comparison
    the whole figure exists to support.

    Args:
        sweep: The computed sweep.
        path: Output PNG path.
        config_hash: Stamped in the caption.
        git_commit: Stamped in the caption.

    Returns:
        The path written.

    Raises:
        ValueError: If the sweep is not measured. A fixture figure travels
            further than the terminal it was made in, and this one has no
            caption discipline to fall back on because it prints no table.
    """
    if not sweep.is_measured:
        raise ValueError(
            f"refusing to plot {sweep.eval_set_id}: data_source is "
            f"{sweep.data_source!r}, not measured. {sweep.data_source_reason}"
        )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    certified = [p for p in sweep.points if p.certified and p.recall is not None]
    refused = [p for p in sweep.points if not p.certified]

    figure, recall_axis = plt.subplots(figsize=(8.0, 5.4))
    lift_axis = recall_axis.twinx()

    targets = [p.target_fpr for p in certified]
    recalls = [p.recall.value for p in certified]
    recall_err = [
        [p.recall.value - p.recall.ci_low for p in certified],
        [p.recall.ci_high - p.recall.value for p in certified],
    ]
    recall_axis.errorbar(
        targets, recalls, yerr=recall_err, fmt="o-", capsize=3,
        color="tab:blue", label="recall (95% CI)",
    )

    with_lift = [p for p in certified if p.lift is not None]
    if with_lift:
        lift_targets = [p.target_fpr for p in with_lift]
        lifts = [p.lift.value for p in with_lift]
        lift_err = [
            [p.lift.value - p.lift.ci_low for p in with_lift],
            [p.lift.ci_high - p.lift.value for p in with_lift],
        ]
        lift_axis.errorbar(
            lift_targets, lifts, yerr=lift_err, fmt="s--", capsize=3,
            color="tab:orange", label="lift (95% CI)",
        )
        lift_axis.axhline(
            1.0, color="tab:red", linestyle=":", linewidth=1.2,
            label="lift = 1 (pre-registered bar)",
        )

    for index, point in enumerate(refused):
        recall_axis.axvline(
            point.target_fpr, color="tab:red", linestyle="-", linewidth=1.0,
            alpha=0.55, label="REFUSED — no certifiable threshold" if index == 0 else None,
        )

    recall_axis.set_xlabel("target false-positive rate")
    recall_axis.set_ylabel("recall")
    lift_axis.set_ylabel("lift (recall / flag rate)")
    # Short enough to fit the figure. The in-sample caveat rides in the caption
    # rather than the title, which clipped at both ends and so carried it
    # nowhere at all.
    recall_axis.set_title(
        f"FPR budget sweep — {sweep.eval_set_id} · {sweep.variant} · n={sweep.n}"
    )

    handles, labels = recall_axis.get_legend_handles_labels()
    lift_handles, lift_labels = lift_axis.get_legend_handles_labels()
    recall_axis.legend(handles + lift_handles, labels + lift_labels, loc="upper left")

    # Two lines rather than one: on a single line the provenance ran off the
    # right edge, which is the half a reader needs six weeks later.
    caveat = (
        "in-sample: threshold certified on the split it is scored on · "
        f"base rate {sweep.base_rate:.4f} · ceiling "
        f"{1.0 / max(sweep.base_rate, 1e-12):.2f}"
    )
    stamp = (
        f"alpha {sweep.alpha:.3f} · {sweep.bootstrap_samples} resamples · "
        f"seed {sweep.seed}"
    )
    if config_hash:
        stamp += f" · config {config_hash}"
    if git_commit:
        stamp += f" · commit {git_commit[:8]}"
    figure.text(0.01, 0.035, caveat, fontsize=7, color="#5a6472")
    figure.text(0.01, 0.008, stamp, fontsize=7, color="#5a6472")

    figure.tight_layout(rect=(0, 0.075, 1, 1))
    figure.savefig(out, dpi=150)
    plt.close(figure)
    _LOG.info("wrote %s", out)
    return out


def plot_fpr_frontier(
    sweep: FprSweep,
    path: str | Path,
    *,
    config_hash: Optional[str] = None,
    git_commit: Optional[str] = None,
) -> Path:
    """Recall against what recall costs, with lift annotated at each point.

    The companion to :func:`plot_fpr_sweep`. That one asks how much recall the
    budget buys; this one asks what the budget costs, which is the axis the
    profiles are declared on. The declared flag-rate budgets are drawn as
    vertical lines, so "which profiles can this operating point serve" is a
    thing you read off the figure rather than compute.

    Args:
        sweep: The computed sweep.
        path: Output PNG path.
        config_hash: Stamped in the caption.
        git_commit: Stamped in the caption.

    Returns:
        The path written.

    Raises:
        ValueError: If the sweep is not measured.
    """
    if not sweep.is_measured:
        raise ValueError(
            f"refusing to plot {sweep.eval_set_id}: data_source is "
            f"{sweep.data_source!r}, not measured. {sweep.data_source_reason}"
        )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    points = [
        p for p in sweep.points
        if p.certified and p.recall is not None and p.flag_rate is not None
    ]
    figure, axes = plt.subplots(figsize=(8.0, 5.6))

    flags = [p.flag_rate.value for p in points]
    recalls = [p.recall.value for p in points]
    err = [
        [p.recall.value - p.recall.ci_low for p in points],
        [p.recall.ci_high - p.recall.value for p in points],
    ]
    axes.errorbar(
        flags, recalls, yerr=err, fmt="o-", capsize=3, color="tab:blue",
        label="recall (95% CI)",
    )

    # Declared budgets, so the reader can see which side of each line a point
    # falls on rather than checking it against a table.
    styles = ["--", "-.", ":"]
    for index, (name, budget) in enumerate(
        sorted(sweep.profile_budgets.items(), key=lambda kv: kv[1])
    ):
        axes.axvline(
            budget, color="tab:red", linestyle=styles[index % len(styles)],
            linewidth=1.1, alpha=.8, label=f"{name} budget ({budget:.2f})",
        )

    # Lift at every other point: at all twenty the labels collide.
    for point in points[::2]:
        if point.lift is None:
            continue
        axes.annotate(
            f"{point.lift.value:.2f}",
            xy=(point.flag_rate.value, point.recall.value),
            xytext=(4, -12), textcoords="offset points",
            fontsize=7.5, color="tab:orange",
        )

    axes.set_xlabel("flag rate — the share of this envelope routed to the expensive check")
    axes.set_ylabel("recall")
    axes.set_title(
        f"Recall against its cost — {sweep.eval_set_id} · {sweep.variant} · n={sweep.n}"
    )
    axes.legend(loc="lower right", fontsize=8)
    axes.grid(alpha=.2, linewidth=.6)

    caveat = (
        f"orange labels are lift · base rate {sweep.base_rate:.4f}: these are "
        "envelope figures, not production costs"
    )
    stamp = f"{sweep.bootstrap_samples} resamples · seed {sweep.seed}"
    if config_hash:
        stamp += f" · config {config_hash}"
    if git_commit:
        stamp += f" · commit {git_commit[:8]}"
    figure.text(0.01, 0.035, caveat, fontsize=7, color="#5a6472")
    figure.text(0.01, 0.008, stamp, fontsize=7, color="#5a6472")

    figure.tight_layout(rect=(0, 0.075, 1, 1))
    figure.savefig(out, dpi=150)
    plt.close(figure)
    _LOG.info("wrote %s", out)
    return out


def plot_roc_operating_points(
    curve: RocCurve,
    path: str | Path,
    *,
    title: str,
    config_hash: Optional[str] = None,
) -> Path:
    """Draw the measured ROC with each warranted operating point and its slope.

    The point of the figure is the *unequal steepness*: three profiles sit on
    one curve, and the local slope at each is what decides how much a threshold
    move costs or buys. A reader should be able to see, without being told, that
    the three points are not interchangeable positions on an otherwise uniform
    trade.

    Args:
        curve: From :func:`~controlplane.validation.roc.roc_curve`.
        path: Where to write the PNG.
        title: Figure title, which must name the envelope and ``n``.
        config_hash: Stamped on the figure, so a plot lifted into a slide still
            carries the run that produced it.

    Returns:
        The path written.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    figure, axes = plt.subplots(figsize=(7.2, 6.4))
    axes.plot(curve.fpr, curve.tpr, color="#25324a", linewidth=1.6, label="measured ROC")
    axes.plot([0, 1], [0, 1], color="#9aa4b2", linewidth=0.9, linestyle=":", label="chance")

    colours = ["#b3261e", "#b06f00", "#2a7d4f"]
    for index, point in enumerate(curve.points):
        colour = colours[index % len(colours)]
        axes.scatter([point.fpr], [point.tpr], s=64, zorder=5, color=colour,
                     edgecolor="white", linewidth=1.2)
        # A short tangent segment, so the slope is shown rather than only
        # written down. Fixed arc length rather than fixed x-span: at slope 6.7
        # a 0.09 x-span draws a line 0.6 tall, which reads as a trend line
        # across the figure instead of as the local gradient it is.
        arc = 0.16
        dx = arc / np.hypot(1.0, point.slope)
        axes.plot(
            [point.fpr - dx, point.fpr + dx],
            [point.tpr - dx * point.slope, point.tpr + dx * point.slope],
            color=colour, linewidth=1.4, linestyle="--", alpha=0.9,
        )
        axes.annotate(
            "\n".join(
                [
                    point.operating_point_id,
                    "slope %.2f  ·  f=%.3f" % (point.slope, point.flag_rate),
                    "recall %.3f" % point.tpr,
                ]
            ),
            xy=(point.fpr, point.tpr),
            xytext=(point.fpr + 0.06, point.tpr - 0.14),
            fontsize=8, color=colour,
            arrowprops=dict(arrowstyle="-", color=colour, alpha=0.5, linewidth=0.8),
        )

    axes.set_xlabel("false-positive rate")
    axes.set_ylabel("recall (true-positive rate)")
    axes.set_xlim(-0.02, 1.02)
    axes.set_ylim(-0.02, 1.02)
    axes.set_title(title, fontsize=10)
    axes.legend(loc="lower right", fontsize=8, frameon=False)
    axes.grid(alpha=0.18, linewidth=0.6)

    footer = f"AUROC {curve.auroc:.4f} · n+={curve.n_positive} n-={curve.n_negative}"
    if config_hash:
        footer += f" · config {config_hash}"
    figure.text(0.01, 0.01, footer, fontsize=7, color="#5a6472")

    figure.tight_layout()
    figure.savefig(out, dpi=160)
    plt.close(figure)
    _LOG.info("wrote %s", out)
    return out
