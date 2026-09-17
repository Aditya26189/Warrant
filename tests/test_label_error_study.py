"""199's criteria, applied as registered and amended, on hand-built rows.

The study's numbers come from the registered run; these defend the rules that
read them: a set the sweep never ran is null for C0, not a pass, and a study with
no checked row cannot pass C0 by default.
"""

from __future__ import annotations

from controlplane.validation.label_error import REGISTERED_BUDGETS, SCORE_SETS, evaluate_criteria


def _row(budget, *, reproduces, c1=0.93, c_disputes=0.9, to_80=5, status="VALID"):
    return {
        "budget": budget, "status": status, "reproduces_sweep": reproduces,
        "sensitivity": {"flagged_positive_really_clean": {
            "confidence_if_one": c1, "errors_to_fall_below": {"0.80": to_80}}},
        "second_review": {"disputes": {"confidence_if_every_dispute_is_a_primary_error": c_disputes}},
    }


def test_the_registered_design_is_what_199_says():
    assert REGISTERED_BUDGETS == tuple(round(0.01 * i, 2) for i in range(1, 21))
    assert len(SCORE_SETS) == 3 and SCORE_SETS[0] == "validation-T1-last_token"


def test_a_set_the_sweep_never_ran_is_null_not_a_pass():
    sets = [
        {"score_set_id": "a", "rows": [_row(0.05, reproduces=True)]},
        {"score_set_id": "b", "rows": [_row(0.05, reproduces=None)]},
    ]
    criteria = evaluate_criteria(sets)
    assert criteria["C0"]["holds"] is True and criteria["C0"]["rows_checked"] == 1
    sets[0]["rows"][0]["reproduces_sweep"] = False
    assert evaluate_criteria(sets)["C0"]["holds"] is False


def test_no_checked_row_cannot_pass_c0():
    sets = [{"score_set_id": "b", "rows": [_row(0.05, reproduces=None)]}]
    assert evaluate_criteria(sets)["C0"]["holds"] is False


def test_p1_p2_and_the_reported_range_read_certified_rows_only():
    sets = [{"score_set_id": "a", "rows": [
        _row(0.05, reproduces=True, c1=0.94, c_disputes=0.85, to_80=4),
        _row(0.10, reproduces=True, c1=0.96, c_disputes=0.79, to_80=None),
        _row(0.01, reproduces=True, c1=None, c_disputes=0.1, to_80=1, status="REFUSED"),
    ]}]
    criteria = evaluate_criteria(sets)
    assert criteria["P1"]["holds"] is False
    assert criteria["P2"]["holds"] is True
    reported = criteria["reported"]
    assert reported["certified_rows"] == 2
    assert (reported["confidence_at_disputes_min"], reported["confidence_at_disputes_max"]) == (0.79, 0.85)
    assert reported["flagged_clean_errors_to_fall_below_0_80_min"] == 4
    assert reported["rows_never_below_0_80"] == 1
