"""The price list and the agreement figure, rendered into ``RESULTS.md``.

``CLAUDE.md``'s definition of done asks ``results/RESULTS.md`` for *"the warrant
matrix, the tier ladder, drift/revocation traces, **the computed price list**,
and **κ**"*. The last two were missing because neither existed; they do now
(``DECISIONS.md`` 146, 147, 152) and this is what puts them where the contract
says they go.

**Every section here states its absence rather than omitting itself.** A
document that silently drops a section when its artifact is missing reads
exactly like one where the section was never asked for, and this is the document
a reviewer checks the definition of done against. So a missing artifact produces
a heading and a sentence naming the script that would fill it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

__all__ = ["price_list_sections"]


def _load(path: Path) -> Optional[dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _absent(script: str) -> str:
    return (
        f"Not generated in this run. `{script}` writes it; until it has been "
        "run, this section has no numbers and says so rather than being "
        "dropped."
    )


def _price_list(document: Optional[dict[str, Any]]) -> str:
    """What a recall claim on production traffic costs, in labels."""
    if document is None:
        return _absent("python scripts/25_on_traffic.py --config config.yaml")

    sensitivity = document["sensitivity"]
    declared = document["declared"]
    lines = [
        "What a recall claim on **your traffic** costs, from the one declared "
        f"workload `{declared['workload']}` "
        f"(N={declared['monthly_interactions']:,}, base error rate "
        f"{declared['base_error_rate']:g}). Every figure is computed by "
        "`controlplane/sampling`; none is typed.",
        "",
        "Recall is not measured. It is computed from a measured prevalence, so "
        "the margin travels through the derivative:",
        "",
        "```",
        "R      = TP / (TP + q*N_u)",
        f"dR/dq  = {sensitivity['derivative']:.3f}   "
        f"(TP={sensitivity['confirmed_errors']:,.0f}, "
        f"N_u={sensitivity['unflagged_pool']:,.0f}, "
        f"q={sensitivity['unflagged_prevalence']:.5f})",
        "m_q    = m_R / |dR/dq|",
        "n      = z^2 q(1-q) / m_q^2",
        "```",
        "",
        "| operating point | margin | month one | steady state | superseded |",
        "|---|---|---|---|---|",
    ]
    for row in document["price_list"]:
        regime = "month one" if str(row["regime"]).startswith("month") else "steady"
        if regime != "month one":
            continue
        steady = next(
            (
                other["labels"]
                for other in document["price_list"]
                if other["subject"] == row["subject"]
                and other["margin"] == row["margin"]
                and not str(other["regime"]).startswith("month")
            ),
            None,
        )
        cell = "**REFUSED**" if not row["feasible"] else f"**{row['labels']:,}**"
        steady_cell = "—" if steady is None else f"{steady:,}"
        lines.append(
            f"| {row['subject']} | ±{row['margin']:g} | {cell} | {steady_cell} | "
            f"{row['naive_labels']:,} |"
        )
    lines += [
        "",
        "**Month one costs more, and it is not a discount anyone can take "
        "early.** Neyman allocation needs the per-band prevalences the first "
        "month's labels are bought to discover, so month one runs proportional "
        "at full simple-random-sampling cost. **superseded** is what this "
        "repository quoted before `DECISIONS.md` 147, and it was low by 6x to "
        "13x.",
        "",
        "**Yield is exact; rate is estimated.** The flagged stratum of *your "
        "traffic* is reviewed in full, so this month's confirmed-error count and "
        "the precision of this month's flags are a census: no sampling interval, "
        "no extra labels. Recall needs the whole sampling apparatus. The two are "
        "not views of one measurement — they are a free claim and an expensive "
        "one. Precision measured on an *eval set* is a different estimand — the "
        "detector's precision, estimated from a sample — and carries an interval "
        "(`DECISIONS.md` 169).",
        "",
        f"Interval coverage on synthetic traffic with known ground truth: "
        f"**{document['coverage']['coverage']:.1%}** over "
        f"{document['coverage']['trials']:,} trials against a nominal "
        f"{document['coverage']['nominal']:.0%}. Above nominal, because "
        "Clopper-Pearson is conservative and the published interval carries no "
        "finite-population correction. Over-covering claims less than the "
        "evidence supports.",
    ]
    return "\n".join(lines)


def _agreement(document: Optional[dict[str, Any]]) -> str:
    """Cohen's κ, and what it qualifies."""
    if document is None:
        return _absent("python scripts/25_on_traffic.py --config config.yaml")

    agreement = document["agreement_mechanism"]
    blinding = document["blinding"]
    kappa = agreement.get("kappa")
    lines = [
        "Every interval this project publishes is a statement about **sampling** "
        "error and nothing else. It answers *how much would this number move on "
        "a different sample?* It is silent on *how much would it move if a "
        "different person reviewed the same sample?* — and at κ = 0.5 the second "
        "question has the larger answer. So κ is reported beside the warrant and "
        "a low value **widens the recall interval** rather than sitting in a "
        "footnote.",
        "",
    ]
    if kappa is None:
        lines.append(
            "κ is undefined on the doubly-labelled subset: "
            f"{agreement.get('undefined_reason', 'both reviewers used one category')}"
        )
    else:
        lines += [
            f"- κ = **{kappa:.4f}** "
            f"[{agreement['ci_low']:.4f}, {agreement['ci_high']:.4f}] "
            f"(95% percentile bootstrap over pairs, n={agreement['n_pairs']})",
            f"- raw agreement {agreement['observed_agreement']:.4f}, chance "
            f"agreement {agreement['expected_agreement']:.4f} — reported "
            "together because κ is routinely mistaken for the first of them",
        ]
    lines += [
        "",
        "> **This κ demonstrates the mechanism and measures no reviewer.** There "
        "are no doubly-labelled items in this repository. What is shown is that "
        "a low κ widens the interval and records why on the metric, so a widened "
        "interval can never be mistaken for a measured one.",
        "",
        "**The queue is blinded** (`CLAUDE.md` invariant 7). A reviewer who can "
        "see that an item was flagged confirms it more often, and one who can "
        "see it was not confirms less often; both push recall up. The payload "
        f"carries only `{'`, `'.join(blinding['payload_keys'])}` — flag status, "
        "score, stratum and ordering are withheld by construction rather than by "
        "convention, and the double-labelled items are split across both strata "
        f"({blinding['double_labelled_by_stratum']}) because agreement measured "
        "on one stratum says nothing about the other.",
    ]
    return "\n".join(lines)


def _scorefree(document: Optional[dict[str, Any]]) -> str:
    """What it costs to certify a detector that emits no score."""
    if document is None:
        return _absent("python scripts/26_scorefree.py --config config.yaml")

    head = document["headline"]
    lines = [
        "A warrant is a statement about a threshold, and the detector family "
        "that wins on REDACT — GPT-4.1, Claude Sonnet — emits no score to "
        "threshold. Repeated sampling fixes that: run the judge `k` times and "
        "score each item by the fraction of runs that flagged it.",
        "",
        "**A single-sample judge cannot be certified to a tight false-positive "
        f"budget however much data you have.** At `k = 1` the tightest budget "
        f"any useful threshold reaches is **{head['single_sample_floor_median']:.3f}** "
        "— which is nothing but the judge's own error rate. One bit gives one "
        "cut point, so there is no dial to turn.",
        "",
        "| negatives | data floor | " + " | ".join(
            f"k={k}" for k in (1, 2, 3, 5, 9)
        ) + " |",
        "|---|---|---|---|---|---|---|",
    ]
    for pool in sorted({row["n_negatives"] for row in document["floors"]}):
        cells = []
        floor = None
        for k in (1, 2, 3, 5, 9):
            row = next(
                r
                for r in document["floors"]
                if r["n_negatives"] == pool and r["k"] == k
            )
            floor = row["data_floor"]
            mark = "**" if row["binds"] != "data" else ""
            cells.append(f"{mark}{row['granularity_floor_median']:.5f}{mark}")
        lines.append(f"| {pool:,} | {floor:.5f} | " + " | ".join(cells) + " |")
    crossovers = document["crossovers"]
    lines += [
        "",
        "**Bold** means granularity is what binds; plain means the benchmark's "
        "own certification capacity does. The crossover between them is "
        f"`k = {crossovers[0]['crossover_k_median']}` at "
        f"{crossovers[0]['n_negatives']:,} negatives and "
        f"`k = {crossovers[-1]['crossover_k_median']}` at "
        f"{crossovers[-1]['n_negatives']:,}. **Past it, more samples are "
        "inference spend fixing a data problem.**",
        "",
        f"`k` is part of the operating point. Certified at `k = 9` with an upper "
        f"bound of {document['void_at_another_k']['certified_upper_bound']:.4f}, "
        "the same vote-fraction threshold at `k = 1` realises "
        f"{document['void_at_another_k']['realised_fpr_at_k1']:.4f} — "
        f"{document['void_at_another_k']['breach_factor']:.1f}× the bound. The "
        "warrant is void, which is why `k` enters the warrant key.",
        "",
        "> **The judge is simulated**, with independent Bernoulli draws. A real "
        "judge's runs share a prompt and a temperature and are correlated, which "
        "makes the vote fraction a worse estimate, pushes the crossover up, and "
        "makes every figure here an **upper bound** on what `k` buys. It "
        "certifies no real detector.",
    ]
    return "\n".join(lines)


def price_list_sections(results_dir: Path) -> list[tuple[str, str]]:
    """``(heading, body)`` pairs for :func:`~controlplane.report.results.render_results`.

    Args:
        results_dir: The ``results/`` directory holding the artifacts.

    Returns:
        Three sections, always. A section whose artifact is missing names the
        script that writes it instead of disappearing.
    """
    on_traffic = _load(results_dir / "on_traffic" / "on_traffic.json")
    scorefree = _load(results_dir / "scorefree" / "scorefree.json")
    return [
        ("The price list — what it costs to keep a warrant true", _price_list(on_traffic)),
        ("Inter-rater agreement, and the blinded queue", _agreement(on_traffic)),
        ("Certifying a detector that emits no score", _scorefree(scorefree)),
    ]
