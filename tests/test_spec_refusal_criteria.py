"""Every refusal ``issuance.py`` can issue traces to a criterion ``SPEC.md`` §2.3 names.

§2.3 listed five criteria while the code enforced six: lift lower bound ≤ 1.0
(``DECISIONS.md`` 043) was found by measurement and never reached the contract
(``DECISIONS.md`` 169). A refusal the specification does not mention is a
refusal a reviewer reads as a bug, or never reads at all.

The map below is the only place a new criterion can be added without failing
this test, and adding one there means naming the §2.3 phrase it implements.
Guard variants -- ``recall_undefined``, ``single_class_envelope`` -- map to the
criterion they refuse to skip.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ISSUANCE = PROJECT_ROOT / "controlplane" / "validation" / "issuance.py"
SPEC = PROJECT_ROOT / "docs" / "SPEC.md"

#: criterion name in issuance.py -> phrase that must appear in SPEC.md §2.3.
CRITERIA = {
    "control:": "any control fails",
    "control_suite": "any control fails",
    "n_test": "`n_test` < 200",
    "auroc_lower_ci": "AUROC lower CI bound ≤ 0.55",
    "single_class_envelope": "AUROC lower CI bound ≤ 0.55",
    "no_ranking_claim": "AUROC lower CI bound ≤ 0.55",
    "lift_lower_ci": "lift lower bound ≤ 1.0",
    "recall_lower_ci": "recall below the policy's declared minimum",
    "recall_undefined": "recall below the policy's declared minimum",
    "fpr_hard_negatives": "FPR on the hard-negative set above the declared maximum",
    "fpr_hard_negatives_upper_ci": "FPR on the hard-negative set above the declared maximum",
    "fpr_hard_negatives_protocol": "hard-negative FPR lacks a named independent-unit protocol",
}


def _section_2_3() -> str:
    text = SPEC.read_text(encoding="utf-8")
    start = text.index("### 2.3 Refusal criteria")
    return text[start : text.index("\n## 3.", start)]


def _criteria_in_code() -> set[str]:
    source = ISSUANCE.read_text(encoding="utf-8")
    names = set(re.findall(r'criterion=f?"([a-z_]+:?)', source))
    names |= set(re.findall(r'"([a-z_]+)"\s*\n\s*if metrics\.ranking_absent_reason', source))
    names |= set(re.findall(r'else "([a-z_]+)"\s*\n\s*\),', source))
    return names


def test_the_criteria_are_found_in_the_code() -> None:
    found = _criteria_in_code()
    assert {"n_test", "auroc_lower_ci", "lift_lower_ci", "control:"} <= found, (
        f"the criterion scan found {sorted(found)}; it is no longer reading issuance.py"
    )


def test_every_refusal_criterion_is_named_in_spec_section_2_3() -> None:
    section = _section_2_3()
    unmapped = sorted(_criteria_in_code() - CRITERIA.keys())
    assert not unmapped, (
        f"issuance.py refuses on {unmapped}, which this map does not trace to "
        "SPEC.md §2.3. Name the criterion in the spec, then add it here."
    )
    missing = sorted({phrase for phrase in CRITERIA.values() if phrase not in section})
    assert not missing, f"SPEC.md §2.3 no longer names: {missing}"


def test_the_map_names_no_criterion_the_code_has_dropped() -> None:
    stale = sorted(CRITERIA.keys() - _criteria_in_code())
    assert not stale, f"mapped criteria no longer in issuance.py: {stale}"
