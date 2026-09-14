"""Assemble the demo's beats from committed artifacts. Reads; decides nothing.

``CLAUDE.md``: no logic in the demo runner. Every number a beat carries is
read out of ``results/`` and cited with the file and field it came from, so a
viewer can open the artifact and find it. A beat whose artifact is missing
reports itself absent rather than rendering a blank -- a demo that silently
skips a beat is a demo that shows only what happened to work.

The beats answer the problem statement directly:

===============================  =============================================
problem statement                beat
===============================  =============================================
different use cases, different   2 -- three profiles, three actions, one input
risk tolerance and latency
consume a model via API,         3 -- the tier ladder: activations, logprobs,
limited internal access               text-only, each separately warranted
hallucination and privacy        4 -- the dual-labelled pilot, and PII measured
overlap                               out of sample
no reliable real-time ground     5 -- envelope drift and revocation, which
truth                                 needs no ground truth to fire
over- and under-flagging         1 -- the refusal, and what it costs to fix
audit trail behind every         6 -- hash-chained certificates
decision
===============================  =============================================

Beats 7, 8 and 9 were added once the work behind them existed. The demo closes
on this project's three-clause pitch -- *what your error rate is on your
traffic, when that number stops being true, what it costs to keep it true* --
and beats 1 to 6 demonstrate only the middle clause.

They also close gaps against the Round 2 brief, checked against the document
rather than remembered (``DECISIONS.md`` 161). **The brief lists seven
real-world complexities**; the first table above maps five of them. The sixth,
*"Regulatory expectations differ by geography and industry ... and continue to
evolve, so rigid, hard-coded rules age quickly"*, is beat 5 -- whose own
``answers`` field has always named it -- and beat 2, whose three profiles are
the configurable policy layer the brief asks for. It was missing from this table,
not from the demo. The seventh, below, was missing from both:

===============================  =============================================
Round 2 text                     beat
===============================  =============================================
"Multi-turn conversations and    9 -- the action gate. This complexity had NO
AI agents that take actions           beat before 2026-09-11: beats 1-6 are
(not just generate text)              all about text, and the compounding risk
introduce compounding risk"           of an agent acting was unaddressed
"Metrics & monitoring -- how     7 -- the on-traffic warrant and the price
you would define, measure, and        list. Defining and measuring a false-
report false positive/negative        negative rate on real traffic is what
rates and overall system              clause one is, and what it costs is
trustworthiness to a skeptical        clause three
stakeholder"
"Detection techniques -- ... a   8 -- tunability. The brief names the judge
secondary 'AI-as-judge'               pattern explicitly; beat 8 is whether a
pattern"                              judge can be certified at all, and what
                                      repeated sampling costs to make it one
===============================  =============================================

The brief's reference parameters line up with ``config.yaml`` and are worth
stating because they were not chosen to: it names "a customer support assistant,
an internal knowledge assistant, and a decision-support tool", which are the
three profiles by name, and "tens of thousands of interactions per week", which
the declared 200,000 a month is (46,154).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Optional

__all__ = ["BRIEF_COMPLEXITIES", "Beat", "assemble_beats"]


@dataclasses.dataclass(frozen=True)
class Beat:
    """One demo beat, with the artifact every number in it came from.

    Args:
        number: Running order.
        title: What the beat shows.
        answers: The problem-statement complexity it addresses.
        rows: ``(label, value)`` pairs, already formatted.
        artifacts: Files a viewer can open to check the rows.
        note: The caveat that must be said aloud with it, if any.
        missing: Why the beat could not be assembled, if it could not.
    """

    number: int
    title: str
    answers: str
    rows: tuple[tuple[str, str], ...] = ()
    artifacts: tuple[str, ...] = ()
    note: Optional[str] = None
    missing: Optional[str] = None

    def to_payload(self) -> dict:
        return dataclasses.asdict(self)


def _load(root: Path, name: str) -> Optional[dict]:
    path = root / "results" / name
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _fmt_interval(metric: Optional[dict]) -> str:
    """A rate with its interval and n, or an honest absence."""
    if not metric:
        return "absent"
    low, high, n = metric.get("ci_low"), metric.get("ci_high"), metric.get("n")
    value = metric.get("value")
    if low is None or high is None:
        return f"{value:.4f} (n={n})"
    return f"{value:.4f} [{low:.4f}, {high:.4f}] n={n}"


def _beat_refusal(root: Path) -> Beat:
    """What the system refuses to certify, and the price of fixing it.

    The budget is READ FROM ``config.yaml``, never typed. An earlier version of
    this beat hardcoded 0.015 -- a figure from a planning document, not from
    this repository, which declares 0.02. It put 199 and 271 on screen where
    the truth is 149 and 203, inside the beat whose subject is numbers crossing
    a document boundary and arriving looking measured (``DECISIONS.md`` 113,
    117). Reading the config is what makes that unrepeatable.
    """
    from ..config import load_config
    from ..validation.warrant_stats import min_n_for

    config = load_config(str(root / "config.yaml"))
    profiles = config.profiles
    name = "customer_support" if "customer_support" in profiles else next(iter(profiles))
    budget = float(profiles[name].max_fpr_hard_negatives)
    n_profiles = len(profiles)

    rows = [
        (f"{name} hard-negative FPR ceiling", f"{budget} (declared in config.yaml)"),
        ("clean negatives for ONE profile", f"{min_n_for(budget, 0.05)}"),
        (
            f"across {n_profiles} profiles (Bonferroni)",
            f"{min_n_for(budget, 0.05 / n_profiles)}",
        ),
        ("convention", "one-sided 95%, per DECISIONS 110"),
    ]
    return Beat(
        number=1,
        title="The refusal, and what it costs to lift",
        answers="over-flagging vs under-flagging is tuned, not solved; "
        "reporting to a skeptical stakeholder",
        rows=tuple(rows),
        artifacts=("controlplane/validation/warrant_stats.py", "DECISIONS.md 110"),
        note=(
            "These are cluster-uncorrected. Inflating them needs a MEASURED ICC "
            "on the target set, which does not exist -- so the number is not "
            "inflated by an assumed factor (DECISIONS 113)."
        ),
    )


def _beat_profiles(root: Path) -> Beat:
    """Three profiles, three actions, one input."""
    payload = _load(root, "policy-triviaqa-2400-t960.json")
    if not payload or "comparison" not in payload:
        return Beat(
            2, "Three profiles, three actions, one input",
            "different use cases carry different risk tolerance and latency",
            missing="results/policy-triviaqa-2400-t960.json absent; run scripts/07_policy.py",
        )
    rows = []
    for row in payload["comparison"]["rows"]:
        rows.append((
            f"{row['profile']} -> {row['action']}",
            f"recall {row['recall']:.4f} "
            f"[{row['recall_ci'][0]:.4f}, {row['recall_ci'][1]:.4f}] "
            f"| flag rate {row['measured_flag_rate']:.4f} | {row['rule_id']}",
        ))
    score = payload["comparison"]["request"]["detector"]["score"]
    rows.insert(0, ("one input, one score", f"{score:.4f}"))
    return Beat(
        number=2,
        title="Three profiles, three actions, one input",
        answers="different use cases carry different risk tolerance and latency; "
        "tiered responses; a configurable policy layer",
        rows=tuple(rows),
        artifacts=("results/policy-triviaqa-2400-t960.json", "policies/"),
        note=(
            "The score is identical in all three rows. The ACTION differs "
            "because the policy differs -- not because the detector changed."
        ),
    )


def _beat_tiers(root: Path) -> Beat:
    """The access-tier ladder: what survives when you cannot see inside."""
    payload = _load(root, "tier_ladder.json")
    if not payload:
        return Beat(
            3, "The tier ladder", "enterprises consume a model via API",
            missing="results/tier_ladder.json absent",
        )
    rows = []
    for name, rung in payload["rungs"].items():
        auroc = rung.get("metrics", {}).get("auroc")
        rows.append((
            f"{rung.get('access_tier', '?')} / {name}",
            f"AUROC {_fmt_interval(auroc)} -- warrant {rung.get('warrant_status')}",
        ))
    return Beat(
        number=3,
        title="The tier ladder -- what survives without model internals",
        answers="enterprises consume a foundation model via API, limiting how "
        "deeply a checker can inspect internals",
        rows=tuple(rows),
        artifacts=("results/tier_ladder.json", "results/tier_ladder.png"),
        note=(
            "Each tier is warranted SEPARATELY. A tier that cannot clear the "
            "issuance bar is refused rather than reported with a caveat."
        ),
    )


def _beat_overlap(root: Path) -> Beat:
    """Hallucination and privacy in the same interaction, and PII out of sample."""
    rows: list[tuple[str, str]] = []
    pilot = _load(root, "pilot_run.json")
    if pilot:
        gen = pilot.get("generation", {})
        rows.append((
            "banking pilot, dual-labelled",
            f"{gen.get('n_items')} items over {gen.get('n_questions')} questions; "
            f"correctness MEASURED, identifier presence AUTHORED",
        ))
        band = pilot.get("acceptance_band", {})
        rows.append((
            "acceptance band (pre-registered)",
            f"{band.get('observed')} of 12 wrong, band "
            f"[{band.get('low')}, {band.get('high')}] -- "
            f"{'IN BAND' if band.get('in_band') else 'OUT OF BAND'}",
        ))
    # The OUT-OF-SAMPLE holdout, not the fitted set. 11 of 34 custom patterns
    # are spec-derived and the rest were fitted on hinglish-pii-200, so that
    # set cannot support a claim about generalisation (DECISIONS 086, 087).
    # hinglish-pii-200b is the held-out one, and it is the number worth showing.
    holdout = None
    path = root / "results" / "holdout" / "detectors.json"
    if path.is_file():
        try:
            holdout = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            holdout = None
    if holdout:
        for run in holdout.get("runs", []):
            recall = (run.get("metrics") or {}).get("recall")
            # Each detector appears twice -- once on the PII set and once on
            # hard negatives, where recall is undefined because there are no
            # positives. Showing the undefined row would put "absent" on screen
            # next to a real number and invite the reader to average them.
            if not recall:
                continue
            status = (run.get("warrant") or {}).get("status")
            rows.append((
                f"{run.get('detector_id', '')} (OUT OF SAMPLE)",
                f"recall {_fmt_interval(recall)} -- {status}",
            ))
    # The COVERAGE result, which is why stock recall is low. Not a tuning
    # problem: the recognisers do not exist to load (DECISIONS 118).
    coverage = _load(root, "presidio_coverage.json")
    if coverage:
        rows.append((
            "stock Presidio coverage",
            f"{coverage['n_supported_entities']} entity types, "
            f"{len(coverage['india_prefixed_entities'])} of them Indian. "
            f"No recogniser for: {', '.join(coverage['uncovered'])}",
        ))

    if not rows:
        return Beat(
            4, "Hallucination and privacy overlap", "the two risks co-occur",
            missing="neither results/pilot_run.json nor results/detectors.json present",
        )
    return Beat(
        number=4,
        title="Hallucination and privacy in the same interaction",
        answers="a fabricated detail about a person is simultaneously a "
        "hallucination and a privacy concern",
        rows=tuple(rows[:9]),
        artifacts=(
            "results/pilot_run.json",
            "results/holdout/detectors.json",
            "results/presidio_coverage.json",
        ),
        note=(
            "Recall is on hinglish-pii-200b, the HELD-OUT set -- 23 of 34 "
            "custom patterns were fitted on the other one, so only this set "
            "supports a generalisation claim (DECISIONS 086, 087). The pilot's "
            "privacy axis is identifier-presence-in-PROMPT, not the output-side "
            "quantity a production path measures (DECISIONS 104)."
        ),
    )


def _beat_revocation(root: Path) -> Beat:
    """Drift and revocation -- the part that needs no ground truth."""
    matrix = _load(root, "warrant_matrix.json")
    rows: list[tuple[str, str]] = []
    if matrix:
        summary = matrix.get("matrix", {}).get("summary", {})
        total = sum(summary.values()) if summary else 0
        # UNVALIDATED first and by name, because it is the modal state and the
        # one a demo is tempted to hide. CLAUDE.md invariant 2: it must never
        # collapse into VALID or REFUSED.
        for state in ("VALID", "REFUSED", "UNVALIDATED", "REVOKED", "STALE"):
            if state in summary:
                rows.append((f"cells {state}", f"{summary[state]} of {total}"))
        rows.append((
            "why UNVALIDATED dominates",
            "a warrant is keyed by (detector, operating point, eval set). Most "
            "pairs were never tested here, and saying so is the point.",
        ))
    # The replayed revocation (DECISIONS 178): a real warrant, real token
    # lengths, the shipped ladder. Without it this beat named a trigger and
    # never showed one fire.
    trace = _load(root, "drift/revocation_trace.json")
    if trace and trace.get("revocation"):
        checkpoints = trace.get("checkpoints") or []
        normal = [c["psi"] for c in checkpoints if c.get("window_shift") == 0 and c.get("psi") is not None]
        revocation = trace["revocation"]
        fired = next((c for c in checkpoints if c.get("to_status") == "REVOKED"), {})
        served = [d for d in revocation.get("decisions") or [] if (d.get("response") or {}).get("routing", {}).get("routed_to")]
        rows.append((
            "replayed shift (length drift)",
            f"{trace['stream']['n_normal']} held-out requests, then long context "
            f"from request {trace['stream']['shift_starts_at_request']}",
        ))
        if normal:
            rows.append(("PSI while inside", f"{min(normal):.3f} to {max(normal):.3f} -- warrant VALID"))
        rows.append((
            "revoked at",
            f"request {revocation['at_request']}, PSI {fired.get('psi', float('nan')):.3f} "
            f"with {fired.get('window_shift')} of {fired.get('window_shift', 0) + fired.get('window_normal', 0)} "
            "window requests shifted",
        ))
        rows.append((
            "profiles served after revocation",
            f"{len(served)} of {len(revocation.get('decisions') or [])} -- nothing valid on the "
            "long context meets a declared minimum, so each ESCALATEs and claims no bounds",
        ))
    rows.append((
        "label-driven revocation (warrant recheck --since)",
        "a chain of rechecks: P(false revoke) <= alpha over the negatives it declares, "
        "for the chain as kept (DECISIONS 193). FPRMonitor's deployment-wide bound is "
        "not established as implemented (187)",
    ))
    rows.append((
        "its estimand",
        "the profile's declared max_fpr_hard_negatives (DECISIONS 112)",
    ))
    return Beat(
        number=5,
        title="Drift, revocation, and why it needs no ground truth",
        answers="there is often no reliable real-time ground truth; regulatory "
        "expectations evolve, so hard-coded rules age",
        rows=tuple(rows),
        artifacts=(
            "results/warrant_matrix.json",
            "results/drift/revocation_trace.json",
            "results/recheck_schedules/comparison.json",
            "controlplane/drift/",
            "controlplane/intake/chain.py",
        ),
        note=(
            "Revocation fires on the INPUT DISTRIBUTION moving, which is "
            "observable without labels. Label-driven revocation needs labelled "
            "negatives; the chain's false-revocation bound assumes independent "
            "units and is NOT validated under session correlation -- see "
            "LIMITATIONS."
        ),
    )


def _beat_audit(root: Path) -> Beat:
    """The audit trail, and the thing that makes it more than a log."""
    return Beat(
        number=6,
        title="A hash-chained decision record",
        answers="a clear audit trail behind every decision",
        rows=(
            ("per decision", "a certificate naming detector, operating point, "
             "envelope, warrant status and expiry"),
            ("chain", "each record hashes its predecessor; a rewritten history "
             "fails verification"),
            ("refusal", "has no override -- no flag, no env var, no admin bypass"),
        ),
        artifacts=("controlplane/store/ledger.py", "controlplane/model/certificate.py"),
        note=None,
    )


def _beat_price_list(root: Path) -> Beat:
    """Clause one and clause three: your traffic, and what it costs to know."""
    document = _load(root, "on_traffic/on_traffic.json")
    if document is None:
        return Beat(
            number=7,
            title="What your error rate is on your traffic, and what knowing costs",
            answers="a number measured on a benchmark is not a number about you",
            missing="run scripts/25_on_traffic.py",
        )
    head = document["headline"]
    sensitivity = document["sensitivity"]
    return Beat(
        number=7,
        title="What your error rate is on your traffic, and what knowing costs",
        answers="a number measured on a benchmark is not a number about you",
        rows=(
            ("free",
             "the flagged pool is reviewed anyway -- confirmed errors and "
             "precision are EXACT counts, no interval, no sampling"),
            ("expensive",
             "recall needs the prevalence in the pool nobody read, and that "
             "costs labels"),
            ("dR/dq",
             f"{sensitivity['derivative']:.3f} -- recall is a FUNCTION of that "
             "prevalence, so the margin travels through the derivative"),
            ("month one",
             f"{head['labels_month_one_5pp']:,} labels for recall to +/-0.05, "
             "at full simple-random-sampling cost"),
            ("steady state",
             f"{head['labels_steady_state_5pp']:,}, once per-band prevalences "
             "exist and Neyman allocation can run"),
            ("what we used to say",
             f"{head['superseded_sizing_5pp']} -- low by 6x to 13x, corrected "
             "in DECISIONS.md 147 rather than quietly fixed"),
            ("does the interval hold",
             f"{head['coverage']:.1%} coverage over "
             f"{head['coverage_trials']:,} trials against a nominal 95%"),
        ),
        artifacts=(
            "results/on_traffic/ON_TRAFFIC.md",
            "controlplane/sampling/planning.py",
            "controlplane/sampling/estimator.py",
        ),
        note=(
            "No production traffic exists here. The estimator is evidenced by "
            "coverage against known ground truth; the price list is arithmetic "
            "over ONE declared workload and says which inputs are declared."
        ),
    )


def _beat_tunability(root: Path) -> Beat:
    """The second thing certification says that scoring does not."""
    document = _load(root, "scorefree/scorefree.json")
    if document is None:
        return Beat(
            number=8,
            title="A detector you cannot tune to your budget at all",
            answers="a procurement fact an F1 table structurally cannot show",
            missing="run scripts/26_scorefree.py",
        )
    head = document["headline"]
    return Beat(
        number=8,
        title="A detector you cannot tune to your budget at all",
        answers="a procurement fact an F1 table structurally cannot show",
        rows=(
            ("the problem",
             "the detectors that win on REDACT -- GPT-4.1, Claude -- emit no "
             "score, so there is nothing to threshold"),
            ("one bit, one notch",
             f"a single-sample judge offers {head['operating_points_at_k1']} "
             "operating point, and the tightest budget it can certify is its "
             "own error rate -- however much data you have"),
            ("notches are not operating points",
             f"{head['notches_at_k50']} notches at 50 samples buy "
             f"{head['operating_points_at_k50']}"),
            ("and it stops paying",
             f"granularity stops binding between k={head['crossover_k_smallest_pool']} "
             f"and k={head['crossover_k_largest_pool']}; past that, more "
             "samples fix a data problem with inference spend"),
            ("k is in the warrant key",
             "certify at k=9 and deploy at k=1 and the realised rate is "
             f"{head['breach_factor_deploying_at_k1']:.1f}x the certified bound"),
        ),
        artifacts=(
            "results/scorefree/SCOREFREE.md",
            "controlplane/validation/scorefree.py",
        ),
        note=(
            "The judge is SIMULATED, with independent draws. A real one has "
            "correlated runs, so every figure here is an UPPER BOUND on what "
            "sampling buys. It certifies no real detector."
        ),
    )


def _beat_gate(root: Path) -> Beat:
    """What happens when the detector this whole system measures is defeated."""
    document = _load(root, "gate/gate.json")
    if document is None:
        return Beat(
            number=9,
            title="When the detector loses",
            answers="over- and under-flagging, when the flag itself is defeated",
            missing="run scripts/27_gate.py",
        )
    head = document["headline"]
    return Beat(
        number=9,
        title="When the detector loses",
        answers="over- and under-flagging, when the flag itself is defeated",
        rows=(
            ("the attack",
             "an instruction inside a transaction memo -- plain English, no "
             "tricks -- and no detector flags it"),
            ("blocked anyway",
             f"at step {head['injection_blocked_at_step']}, on the declared "
             "reversibility of the tool plus three sticky session flags"),
            ("no detector read",
             f"{head['decisions_identical_without_a_detector']} of "
             f"{head['decisions_compared']} rule-1 and rule-2 decisions are "
             "identical whether a detector screams CRITICAL or is absent"),
            ("what it costs",
             f"{head['legitimate_workflows_blocked']} of "
             f"{head['legitimate_workflows']} declared legitimate workflows, "
             f"all {head['blocked_workflows_recoverable']} recovered by a new "
             "session -- EXACT counts over a declared set, so no interval"),
        ),
        artifacts=("results/gate/GATE.md", "controlplane/gate/gate.py"),
        note=(
            "This is NOT a robustness claim and this project makes none. "
            "Nasr et al., The Attacker Moves Second (arXiv:2510.09023), "
            "bypassed 12 published defences at above 90% attack success for "
            "most of them. The claim here is the smaller one that survives -- "
            "defeating every detector in this system does not move those two "
            "rules."
        ),
    )


#: The Round 2 brief's real-world complexities for Track 1, **in the brief's
#: order**, each mapped to the beats that answer it.
#:
#: **Seven, not six.** ``DECISIONS.md`` 161 first counted six, because the first
#: bullet sits at the foot of page 1 and the reading behind that entry truncated
#: page 1. Checked against the full PDF text on 2026-09-13. The brief is not
#: tracked in git, so no test can re-read it on a clean clone -- which is why the
#: quotations live here, verbatim, where a reviewer holding the PDF can check
#: each one in seconds.
BRIEF_COMPLEXITIES: tuple[tuple[int, str, tuple[int, ...]], ...] = (
    (
        1,
        "Different AI use cases (customer-facing vs. internal, real-time vs. "
        "batch) have very different risk tolerance and latency budgets",
        (2,),
    ),
    (
        2,
        "Bias, hallucination, and privacy risks often overlap in practice",
        (4,),
    ),
    (
        3,
        "There is often no reliable, real-time \"ground truth\" to check a "
        "claim against",
        (5,),
    ),
    (
        4,
        "Over-flagging creates alert fatigue and pushes users to ignore or "
        "bypass warnings; under-flagging creates real liability",
        (1, 8),
    ),
    (
        5,
        "Multi-turn conversations and AI agents that take actions (not just "
        "generate text) introduce compounding risk",
        (9,),
    ),
    (
        6,
        "Regulatory expectations differ by geography and industry ... and "
        "continue to evolve, so rigid, hard-coded rules age quickly",
        (2, 5),
    ),
    (
        7,
        "Enterprises typically consume a foundation model via API rather than "
        "owning it outright, limiting how deeply a checker can inspect model "
        "internals",
        (3,),
    ),
)


def assemble_beats(root: Path) -> tuple[Beat, ...]:
    """Every beat, in running order, from whatever artifacts exist.

    Args:
        root: The repository root.

    Returns:
        Nine :class:`Beat` records. A beat whose artifact is missing carries
        ``missing`` rather than empty rows, so the renderer can say so.
    """
    return (
        _beat_refusal(root),
        _beat_profiles(root),
        _beat_tiers(root),
        _beat_overlap(root),
        _beat_revocation(root),
        _beat_audit(root),
        # 7, 8 and 9 close the gap between what the demo showed and what the
        # product does. The script closes on the three-clause pitch and beats
        # 1 to 6 demonstrate only the middle clause.
        _beat_price_list(root),
        _beat_tunability(root),
        _beat_gate(root),
    )
