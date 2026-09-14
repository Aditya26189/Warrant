"""The RBI's draft model-risk guidance, paragraph by paragraph. ``DECISIONS.md`` 189.

Reserve Bank of India, *Guidance on Regulatory Principles for Model Risk
Management, 2026* -- **a draft**, released 24 June 2026 for comment until 24 July
2026. It brings "all models, including AI / ML models, irrespective of whether
such models are developed internally, sourced from third-parties" (¶9) under
independent validation by the regulated entity (¶29), before and after
deployment and on triggers (¶30).

This module is a register, not a compliance claim. Each row says which kind of
evidence a warrant can supply toward one paragraph, names the code that
produces it and a test that holds it, and says what it does not do. A row
marked PROVIDES means *this repository produces evidence of the kind the
paragraph asks for*; whether that evidence satisfies a supervisor is not
something code can establish.

Three rules, each checked by ``tests/test_crosswalk.py``:

* a PROVIDES or PARTIAL row names at least one ``path::symbol`` and one test,
  and both exist;
* a PARTIAL or NOT PROVIDED row states its gap;
* ``docs/RBI-MRM-2026-CROSSWALK.md`` is exactly :func:`render_crosswalk`'s
  output, so the page cannot be edited away from the register.

No measured number appears here or in the rendered page. Rows point at
artifacts by path, so a re-run cannot leave this page stating a stale figure.
"""

from __future__ import annotations

import dataclasses
import enum
from typing import Mapping

__all__ = [
    "Coverage",
    "RBI_MRM_2026",
    "Requirement",
    "SOURCE",
    "render_crosswalk",
]


class Coverage(str, enum.Enum):
    """How much of a paragraph a warrant can supply evidence for."""

    PROVIDES = "PROVIDES"
    PARTIAL = "PARTIAL"
    NOT_PROVIDED = "NOT PROVIDED"


@dataclasses.dataclass(frozen=True)
class Requirement:
    """One paragraph of the draft, and what this repository does about it.

    Attributes:
        paragraph: As the draft numbers it, e.g. ``"30"`` or ``"54(2)"``.
        topic: A few words, for the table.
        quote: Verbatim from the draft. Short: the clause that carries the
            requirement, not the paragraph.
        coverage: See :class:`Coverage`.
        provided_by: ``path::symbol`` for the code producing the evidence.
        held_by: ``tests/<file>.py::<test>`` for tests that hold it.
        evidence: Paths under the repository that a reader can open.
        gap: What the row does not do. Required unless PROVIDES.
        note: Anything a reader would otherwise get wrong.
    """

    paragraph: str
    topic: str
    quote: str
    coverage: Coverage
    provided_by: tuple[str, ...] = ()
    held_by: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    gap: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.quote.strip():
            raise ValueError(f"¶{self.paragraph}: a row without the draft's words is a paraphrase")
        if self.coverage is not Coverage.NOT_PROVIDED and not (self.provided_by and self.held_by):
            raise ValueError(
                f"¶{self.paragraph} is {self.coverage.value} but names no code or no "
                "test; a claim of coverage with nothing holding it is the defect this "
                "register exists to prevent"
            )
        if self.coverage is not Coverage.PROVIDES and not self.gap.strip():
            raise ValueError(f"¶{self.paragraph} is {self.coverage.value} and states no gap")
        for ref in self.provided_by + self.held_by:
            if "::" not in ref:
                raise ValueError(f"¶{self.paragraph}: {ref!r} is not path::symbol")


SOURCE: Mapping[str, str] = {
    "title": "Guidance on Regulatory Principles for Model Risk Management, 2026",
    "issuer": "Reserve Bank of India",
    "status": "DRAFT for public consultation; no final text as of the read date",
    "released": "2026-06-24",
    "comments_closed": "2026-07-24",
    "read_on": "2026-09-14",
    "document": "https://www.rbi.org.in/Scripts/bs_viewcontent.aspx?Id=5089",
    "press_release": "https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63006",
}


RBI_MRM_2026: tuple[Requirement, ...] = (
    Requirement(
        paragraph="29",
        topic="Independent validation, third-party models included",
        quote=(
            "An RE should ensure that all models, including third-party models, are "
            "subject to independent validation by the RE."
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/intake/certify.py::certify_items",
            "controlplane/validation/issuance.py::issue_or_refuse",
        ),
        held_by=(
            "tests/test_intake.py::test_insufficient_evidence_is_a_refusal",
            "tests/test_intake.py::test_the_bound_is_respected_on_the_supplied_negatives",
            "tests/test_validation.py::test_no_override",
        ),
        evidence=("results/warrant_matrix.md", "results/external/MATRIX.md"),
        gap=(
            "Validates detectors and classifiers that emit a score or a verdict -- a "
            "PII detector, a hallucination trigger, an injection classifier -- against "
            "a false-positive budget on a declared evaluation set. It does not validate "
            "the generative model those detectors guard."
        ),
        note=(
            "certify reads only id, label and score, so a vendor's detector is "
            "validated without its weights or its cooperation."
        ),
    ),
    Requirement(
        paragraph="30",
        topic="When validation happens",
        quote=(
            "prior to and after deployment of a model, following modification, on "
            "internal or external triggers, and periodically as specified in the MRMF"
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/intake/certify.py::certify_items",
            "controlplane/intake/recheck.py::recheck_items",
            "controlplane/drift/response.py::respond_to_drift",
            "controlplane/drift/model_version.py::invalidate_for_model_change",
        ),
        held_by=(
            "tests/test_recheck.py::test_a_broken_bound_revokes",
            "tests/test_model_version.py::test_an_activation_warrant_on_a_changed_model_is_revoked",
            "tests/test_revocation_trace.py::test_the_committed_trace_meets_every_preregistered_criterion",
        ),
        evidence=("results/drift/revocation_trace.json",),
        gap=(
            "Nothing schedules periodic validation: `warrant plan` prices a cadence and "
            "the entity's framework sets it. A modification is detected by model pin "
            "for activation-tier warrants only; a vendor detector that changes "
            "behind an unchanged name is caught only by a recheck on fresh labels."
        ),
    ),
    Requirement(
        paragraph="31",
        topic="What validation assesses",
        quote=(
            "assessment of inputs (e.g., data, assumptions and limitations), soundness "
            "(conceptual and design), performance, and alignment with intended use"
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/validation/controls.py::run_controls",
            "controlplane/policy/resolution.py::resolve_bundle",
        ),
        held_by=(
            "tests/test_validation.py::test_underpowered_negative_control_fails_rather_than_passing",
            "tests/test_validation.py::test_a_failed_control_cannot_be_promoted_after_the_fact",
            "tests/test_policy.py::test_a_bundle_relying_on_no_warrant_is_refused",
        ),
        evidence=("results/warrant_matrix.md",),
        gap=(
            "Performance is measured with intervals, and intended use is a declared "
            "operating point per profile. Conceptual soundness and the review of "
            "assumptions are a validator's judgement; the five controls check the "
            "measurement pipeline, not the detector's design."
        ),
    ),
    Requirement(
        paragraph="32",
        topic="Validation outcomes documented",
        quote=(
            "The model validation outcomes should be documented as per documentation "
            "standards laid down under MRMF / its policies."
        ),
        coverage=Coverage.PROVIDES,
        provided_by=(
            "controlplane/store/ledger.py::Ledger",
            "controlplane/model/warrant.py::Warrant",
        ),
        held_by=(
            "tests/test_store.py::test_hash_chain",
            "tests/test_store.py::test_warrant_round_trips_including_a_refusal",
        ),
        evidence=("results/warrant_matrix.json",),
        note=(
            "Refusals are recorded as records, not as absences; the ledger is "
            "hash-chained so a removed record is detected."
        ),
    ),
    Requirement(
        paragraph="14",
        topic="Action when risk exceeds appetite",
        quote=(
            "it should initiate timely action (e.g., enhanced controls, restrictions on "
            "use, remediation, decommissioning)"
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/drift/response.py::respond_to_drift",
            "controlplane/gate/gate.py::decide",
        ),
        held_by=(
            "tests/test_drift_response.py::test_a_revocation_routes_and_adopts_the_new_bounds",
            "tests/test_gate.py::test_rule_one_blocks_an_irreversible_action_on_any_non_valid_warrant",
            "tests/test_revocation_trace.py::test_a_revoked_warrant_with_nowhere_to_route_claims_nothing",
        ),
        evidence=("results/drift/revocation_trace.json", "results/gate/GATE.md"),
        gap=(
            "The restriction is applied to the warrant and to routing: a revoked "
            "detector is not relied on and irreversible actions are blocked without a "
            "valid warrant. Remediation, decommissioning and the report to the risk "
            "committee are the entity's process."
        ),
    ),
    Requirement(
        paragraph="21",
        topic="Inventory; nothing used unless inventoried",
        quote=(
            "It should ensure that no model is used, relied upon, or deployed unless "
            "it is part of inventory."
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/matrix/matrix.py::WarrantMatrix",
            "controlplane/policy/resolution.py::resolve_bundle",
        ),
        held_by=(
            "tests/test_matrix.py::test_unvalidated_routes_conservatively_and_enqueues",
            "tests/test_policy.py::test_a_bundle_relying_on_no_warrant_is_refused",
        ),
        evidence=("results/warrant_matrix.md",),
        gap=(
            "The matrix is an inventory of warrants -- detector by evaluation set -- and "
            "an unvalidated cell is routed conservatively rather than relied on. It is "
            "not a model inventory: no owner, risk tier, or inactive and decommissioned "
            "states."
        ),
    ),
    Requirement(
        paragraph="37",
        topic="Ongoing monitoring of deployed models",
        quote=(
            "All deployed models, including third-party models, should be subject to "
            "ongoing monitoring, to ensure alignment with the intended outcomes."
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/intake/recheck.py::recheck_items",
            "controlplane/drift/monitor.py::DriftMonitor",
            "controlplane/economics/sizing.py::monitoring_plan",
        ),
        held_by=(
            "tests/test_drift.py::test_a_real_shift_revokes",
            "tests/test_recheck.py::test_a_broken_bound_revokes",
            "tests/test_recheck_power.py::test_c2_the_planned_power_is_what_recheck_actually_delivers",
        ),
        evidence=("results/drift/revocation_trace.json",),
        gap=(
            "Drift is computed on input token length and on the score distribution "
            "only; four declared features and MMD are not built. No production traffic "
            "has been monitored. A schedule of fixed-size rechecks revokes a sound "
            "detector more often the more often it runs, and `warrant plan` states by "
            "how much rather than preventing it."
        ),
    ),
    Requirement(
        paragraph="51",
        topic="Third-party model that does not disclose",
        quote=(
            "the RE should identify risks that arise from such constraints, and put in "
            "place the necessary mitigants, such as limiting the usage"
        ),
        coverage=Coverage.PROVIDES,
        provided_by=(
            "controlplane/intake/certify.py::certify_items",
            "controlplane/intake/contract.py::ScoredItems",
        ),
        held_by=(
            "tests/test_intake.py::test_the_refusing_example_refuses_and_exits_zero",
            "tests/test_intake.py::test_the_refusing_example_certifies_at_a_looser_budget",
        ),
        evidence=("examples/refuses.csv",),
        note=(
            "Validation needs no disclosure beyond scores on labelled items. When "
            "those cannot support a budget the result is a refusal naming what would "
            "change it, which is the limit on usage the paragraph asks for."
        ),
    ),
    Requirement(
        paragraph="53",
        topic="Provider-driven updates",
        quote=(
            "changes in model behaviour or capabilities resulting from provider-driven "
            "updates"
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/drift/model_version.py::invalidate_for_model_change",
            "controlplane/intake/recheck.py::recheck_items",
        ),
        held_by=(
            "tests/test_model_version.py::test_an_activation_warrant_on_a_changed_model_is_revoked",
            "tests/test_model_version.py::test_a_model_change_suspends_the_whole_activation_row",
        ),
        gap=(
            "A pinned model version is compared for activation-tier warrants. A "
            "provider's silent update behind an unchanged version is visible only to a "
            "recheck on fresh labels, and only once enough labels arrive to see it."
        ),
    ),
    Requirement(
        paragraph="54(1)(ii)",
        topic="Limited explainability: enhanced validation and monitoring",
        quote=(
            "enhanced validation and testing, mechanisms to verify and corroborate "
            "model outputs prior to their use, frequent validations and continuous "
            "monitoring, usage restrictions"
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/intake/recheck.py::recheck_items",
            "controlplane/gate/gate.py::decide",
        ),
        held_by=(
            "tests/test_gate.py::test_gate_no_detector",
            "tests/test_recheck.py::test_a_broken_bound_revokes",
        ),
        evidence=("results/gate/GATE.md",),
        gap=(
            "Frequent validation and usage restriction are supplied; corroborating an "
            "individual output before use is not. The probe is a trigger for an "
            "expensive check and never a verdict on a response."
        ),
    ),
    Requirement(
        paragraph="54(1)(i)",
        topic="Explainability thresholds",
        quote=(
            "It should define the explainability and transparency thresholds for all AI "
            "models"
        ),
        coverage=Coverage.NOT_PROVIDED,
        gap=(
            "No explainability is measured. The activation probe is a correlational "
            "classifier and is documented as explaining nothing about why a model "
            "answered as it did."
        ),
    ),
    Requirement(
        paragraph="54(2)",
        topic="Hallucination control boundaries",
        quote=(
            "put in place appropriate control boundaries through system-level controls "
            "or model design features to mitigate risks of hallucinations"
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/gate/gate.py::decide",
            "controlplane/matrix/matrix.py::WarrantMatrix",
        ),
        held_by=(
            "tests/test_gate.py::test_an_injected_instruction_passes_every_check_and_is_blocked_anyway",
            "tests/test_matrix.py::test_unvalidated_routes_conservatively_and_enqueues",
        ),
        evidence=("results/warrant_matrix.md", "results/gate/GATE.md"),
        gap=(
            "The warranted hallucination detector bounds how often an expensive check "
            "is triggered, at a measured recall that is low on the measured evaluation "
            "set (README claim table). It does not bound how often a hallucination "
            "reaches a customer. The action gate's first two rules consult no detector."
        ),
    ),
    Requirement(
        paragraph="54(3)",
        topic="Bias and fairness assessment",
        quote="it should conduct fairness assessment and implement appropriate mitigants",
        coverage=Coverage.NOT_PROVIDED,
        gap=(
            "Not built. A per-response bias score is out of scope as unsound "
            "(CLAUDE.md), and the cohort path that would replace it does not exist."
        ),
    ),
    Requirement(
        paragraph="54(4)",
        topic="Out-of-sample performance",
        quote=(
            "assess the model performance with out-of-sample data and varied scenarios"
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/validation/evalsets.py::split_by_question",
            "controlplane/evalsets/registry.py::load_evalset",
        ),
        held_by=(
            "tests/test_validation.py::test_overlapping_splits_are_refused",
            "tests/test_resplit.py::test_a_re_split_must_be_a_new_set",
        ),
        evidence=("results/warrant_matrix.md",),
        gap=(
            "Test splits are held out, content-hashed and scored once. The varied "
            "scenarios are TriviaQA, a long-context dilution of it and hand-built PII "
            "sets (docs/LIMITATIONS.md section 1); no real traffic."
        ),
    ),
    Requirement(
        paragraph="54(7)",
        topic="Data drift and concept drift",
        quote=(
            "Changes in data distribution, including data drift and concept drift, "
            "should be monitored and addressed on an ongoing basis."
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/drift/monitor.py::DriftMonitor",
            "controlplane/intake/recheck.py::recheck_items",
        ),
        held_by=(
            "tests/test_drift.py::test_a_real_shift_revokes",
            "tests/test_drift.py::test_a_configuration_that_alarms_on_its_own_reference_is_refused",
        ),
        evidence=("results/drift/revocation_trace.json",),
        gap=(
            "Data drift: PSI against a null band simulated at the sample's own size, on "
            "one input feature and the score distribution. Concept drift -- the same "
            "inputs, different correct labels -- is visible only through a recheck on "
            "fresh labels, whose cost `warrant plan` states."
        ),
    ),
    Requirement(
        paragraph="55",
        topic="Red-teaming",
        quote=(
            "structured challenge processes, including red-teaming or equivalent testing"
        ),
        coverage=Coverage.NOT_PROVIDED,
        gap=(
            "No red-teaming and no adversarial-robustness claim. The gate's injection "
            "result is one declared scenario (reports/PHASE-6.md), not a challenge "
            "process."
        ),
    ),
    Requirement(
        paragraph="60(ii)",
        topic="Override, suspension, kill switch",
        quote=(
            "override, suspension, or deactivation mechanisms, including kill-switch "
            "arrangements"
        ),
        coverage=Coverage.PARTIAL,
        provided_by=(
            "controlplane/model/override.py::OverrideRecord",
            "controlplane/drift/response.py::respond_to_drift",
        ),
        held_by=(
            "tests/test_override.py::test_a_record_without_a_stratum_cannot_be_built",
            "tests/test_override.py::test_an_unweighted_record_cannot_reach_the_ledger",
            "tests/test_drift_response.py::test_a_revocation_routes_and_adopts_the_new_bounds",
        ),
        gap=(
            "A human override of an escalated item is recorded, and a revoked warrant "
            "suspends the routes relying on it. There is no serving layer, so a kill "
            "switch belongs to the entity's gateway."
        ),
        note=(
            "These override a model's outputs. A warrant's refusal has no override "
            "(CLAUDE.md invariant 3); the two are different objects, and the paragraph "
            "asks for the first."
        ),
    ),
    Requirement(
        paragraph="34",
        topic="Exception approval",
        quote=(
            "an approval structure, including exception approval that, inter alia, "
            "covers approval authorities, thresholds, additional requirements for "
            "models approved with exceptions, and remediation timelines"
        ),
        coverage=Coverage.NOT_PROVIDED,
        gap=(
            "Nothing records a deployment approved with an exception beside a REFUSED "
            "warrant. Whether the product should, without letting an exception read as "
            "a warrant, is OPEN (DECISIONS.md 189)."
        ),
    ),
    Requirement(
        paragraph="43",
        topic="Fallback on degradation",
        quote=(
            "fallback mechanisms (e.g., manual interventions, substitution, or back-up "
            "arrangements)"
        ),
        coverage=Coverage.PARTIAL,
        provided_by=("controlplane/drift/response.py::respond_to_drift",),
        held_by=(
            "tests/test_drift_response.py::test_a_revocation_routes_and_adopts_the_new_bounds",
            "tests/test_revocation_trace.py::test_a_revoked_warrant_with_nowhere_to_route_claims_nothing",
        ),
        evidence=("results/drift/revocation_trace.json",),
        gap=(
            "On revocation a route is substituted with a detector warranted on the new "
            "envelope, or escalated to a human when none is. Business continuity "
            "planning is the entity's."
        ),
    ),
    Requirement(
        paragraph="33",
        topic="Validation reports to the risk committee",
        quote=(
            "Validation reports, including key findings, and recommendations, should be "
            "placed before RMCB"
        ),
        coverage=Coverage.NOT_PROVIDED,
        gap=(
            "A governance process. The warrant record, the matrix and RESULTS.md are "
            "inputs a validation report can cite; nothing here writes or files one."
        ),
    ),
)


def render_crosswalk(
    requirements: tuple[Requirement, ...] = RBI_MRM_2026,
    source: Mapping[str, str] = SOURCE,
) -> str:
    """The register as a markdown page, ordered by coverage then paragraph."""
    order = {Coverage.PROVIDES: 0, Coverage.PARTIAL: 1, Coverage.NOT_PROVIDED: 2}

    def key(row: Requirement) -> tuple[int, str]:
        return order[row.coverage], row.paragraph

    counts = {c: sum(1 for r in requirements if r.coverage is c) for c in Coverage}
    lines = [
        "# The RBI draft model-risk guidance, and what a warrant supplies",
        "",
        "<!-- Generated by controlplane/report/crosswalk.py. Do not edit by hand; "
        "tests/test_crosswalk.py fails if this page differs from the register. -->",
        "",
        f"**Source.** {source['issuer']}, *{source['title']}*. **{source['status']}.** "
        f"Released {source['released']}; comments closed {source['comments_closed']}; "
        f"read on {source['read_on']}. [Document]({source['document']}), "
        f"[press release]({source['press_release']}).",
        "",
        "**This is not a compliance claim.** Each row says what kind of evidence this "
        "repository produces toward one paragraph, which code produces it, which test "
        "holds it, and what it does not do. Paragraph numbers are the draft's and may "
        "move in the final text.",
        "",
        "**What the draft does not ask, and a warrant adds.** The draft requires "
        "validation and monitoring and sets no evidential standard for either: no "
        "confidence level, no sample size, nothing about a validation the data cannot "
        "support. A warrant states every rate with an interval and its n, refuses when "
        "the evidence cannot support the budget, and prices what re-validation costs "
        "(`warrant plan`).",
        "",
        f"{len(requirements)} paragraphs: {counts[Coverage.PROVIDES]} provided, "
        f"{counts[Coverage.PARTIAL]} partial, {counts[Coverage.NOT_PROVIDED]} not provided.",
        "",
        "| para | topic | coverage |",
        "|---|---|---|",
    ]
    rows = sorted(requirements, key=key)
    lines += [f"| {r.paragraph} | {r.topic} | {r.coverage.value} |" for r in rows]
    lines.append("")
    for r in rows:
        lines += [
            f"## ¶{r.paragraph} -- {r.topic}: {r.coverage.value}",
            "",
            f"> {r.quote}",
            "",
        ]
        if r.provided_by:
            lines.append("**Code:** " + ", ".join(f"`{ref}`" for ref in r.provided_by))
            lines.append("")
        if r.held_by:
            lines.append("**Held by:** " + ", ".join(f"`{ref}`" for ref in r.held_by))
            lines.append("")
        if r.evidence:
            lines.append("**Evidence:** " + ", ".join(f"`{path}`" for path in r.evidence))
            lines.append("")
        if r.gap:
            lines += [f"**Does not:** {r.gap}", ""]
        if r.note:
            lines += [f"**Note:** {r.note}", ""]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - regeneration entry point
    from pathlib import Path

    target = Path(__file__).resolve().parents[2] / "docs" / "RBI-MRM-2026-CROSSWALK.md"
    target.write_bytes(render_crosswalk().encode("utf-8"))
    print(f"wrote {target}")
