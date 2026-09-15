"""How many label errors would have hidden a revocation (DECISIONS 198).

What these defend:

* the counts are exact against the recheck's own lower bound, scanned value by
  value, and every figure 198 quotes is what the code computes -- including the
  correction that the count is not ``critical - k``;
* ``label_2`` changes no verdict on a recheck;
* nothing is counted where it would be a recipe or would read as something it is
  not: a broken bound, an untested file, a mixed-group file, a chain link.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

from controlplane.cli import main
from controlplane.intake import load_scored_items, recheck_items, render_recheck
from controlplane.intake.labels import (
    disputes_upper_bound,
    errors_to_revoke,
    lower_bound,
    recheck_label_sensitivity,
)
from controlplane.intake.recheck import _lower_bound_at
from controlplane.model import to_jsonable


@pytest.fixture(scope="module")
def fast(config):
    return dataclasses.replace(
        config, validation=dataclasses.replace(config.validation, bootstrap_samples=200)
    )


def _critical(n: int, budget: float = 0.05, alpha: float = 0.05) -> int:
    return next(c for c in range(1, n + 1) if _lower_bound_at(n, c, alpha) > budget)


# ------------------------------------------------------------ the arithmetic

def test_the_lower_bound_is_the_one_recheck_revokes_on():
    for n in (1, 7, 59, 628):
        for k in range(0, n + 1, max(1, n // 13)):
            assert lower_bound(k, n, 0.05) == pytest.approx(_lower_bound_at(n, k, 0.05), abs=1e-12)


@pytest.mark.parametrize("n,k", [(59, 2), (59, 6), (191, 10), (628, 23), (628, 41), (700, 41)])
def test_the_counts_match_a_scan_of_the_recheck_bound(n, k):
    budget, alpha = 0.05, 0.05
    flagged = 80
    scan_a = next((a for a in range(1, flagged + 1)
                   if _lower_bound_at(n + a, k + a, alpha) > budget), None)
    scan_b = next((b for b in range(1, n - k + 1)
                   if _lower_bound_at(n - b, k, alpha) > budget), None)
    assert errors_to_revoke(k, n, budget, alpha, flagged, kind="flagged_clean") == scan_a
    assert errors_to_revoke(k, n, budget, alpha, n - k, kind="unflagged_positive") == scan_b


def test_a_count_out_of_reach_is_none():
    assert errors_to_revoke(0, 628, 0.05, 0.05, 3, kind="flagged_clean") is None
    assert errors_to_revoke(0, 628, 0.05, 0.05, 628, kind="unflagged_positive") is None
    assert errors_to_revoke(5, 628, 0.05, 0.05, 0, kind="flagged_clean") is None


@pytest.mark.parametrize("n,critical,k,flagged_clean,unflagged_positive", [
    (628, 42, 23, 20, 311),
    (628, 42, 31, 11, 176),
    (628, 42, 41, 1, 3),
    (59, 7, 6, 1, 6),
])
def test_the_table_in_decisions_198_is_what_the_code_computes(n, critical, k, flagged_clean, unflagged_positive):
    assert _critical(n) == critical
    assert errors_to_revoke(k, n, 0.05, 0.05, 10_000, kind="flagged_clean") == flagged_clean
    assert errors_to_revoke(k, n, 0.05, 0.05, n - k, kind="unflagged_positive") == unflagged_positive


def test_the_count_is_not_critical_minus_k():
    """198's correction of 197: the critical count moves with n."""
    assert (_critical(628), _critical(648)) == (42, 43)
    assert errors_to_revoke(23, 628, 0.05, 0.05, 100, kind="flagged_clean") == 20 != 42 - 23


# ------------------------------------------------------------ the recheck

def _file(tmp_path: Path, name: str, *, seed: int, negative_shift: float = 0.0,
          second: bool = True, n_neg: int = 700, n_pos: int = 300) -> Path:
    rng = np.random.default_rng(seed)
    # A separate stream for label_2, so a file with and without it has the same scores.
    review = np.random.default_rng(seed + 1_000)
    lines = ["id,label,score" + (",label_2" if second else "")]
    for i in range(n_neg):
        extra = ("," + (("0" if review.random() > 0.03 else "1") if i % 8 == 0 else "")) if second else ""
        lines.append(f"m{i},0,{rng.normal(negative_shift, 1):.6f}{extra}")
    for i in range(n_pos):
        extra = ("," + (("1" if review.random() > 0.05 else "0") if i % 8 == 0 else "")) if second else ""
        lines.append(f"q{i},1,{rng.normal(2, 1):.6f}{extra}")
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


THRESHOLD = 1.533459


def test_a_recheck_whose_bound_holds_carries_both_counts(tmp_path, fast):
    items = load_scored_items(_file(tmp_path, "a.csv", seed=11))
    result = recheck_items(fast, items, budget=0.05, threshold=THRESHOLD)
    assert result.bound_still_holds is True
    labels, scores, _ = items.as_arrays()
    negatives = scores[labels == 0]
    k, n = int((negatives >= THRESHOLD).sum()), negatives.size
    flagged_positives = int(((scores >= THRESHOLD) & (labels == 1)).sum())
    sensitivity = result.label_sensitivity
    assert sensitivity.computed and sensitivity.unit == "items"
    assert (sensitivity.k, sensitivity.n, sensitivity.flagged_positives) == (k, n, flagged_positives)
    assert sensitivity.revokes_at_count == _critical(n)
    assert sensitivity.flagged_clean_to_revoke == errors_to_revoke(
        k, n, 0.05, result_alpha(fast), flagged_positives, kind="flagged_clean")
    assert sensitivity.unflagged_positive_to_revoke == errors_to_revoke(
        k, n, 0.05, result_alpha(fast), n - k, kind="unflagged_positive")

    disputes = result.second_review.disputes
    second = np.array([-1 if v is None else v for v in items.second_labels])
    flagged = scores >= THRESHOLD
    d1 = int((flagged & (labels == 1) & (second == 0)).sum())
    d2 = int((~flagged & (labels == 0) & (second == 1)).sum())
    m1 = int((flagged & (labels == 1) & (second >= 0)).sum())
    m2 = int((~flagged & (labels == 0) & (second >= 0)).sum())
    low = _lower_bound_at(n + d1 - d2, k + d1, 0.05)
    assert disputes.lower_bound_if_disputes_are_errors == pytest.approx(low)
    assert disputes.revokes_if_disputes_are_errors is (low > 0.05)
    f_up = disputes_upper_bound(d1, m1, flagged_positives, 0.05)
    u_up = disputes_upper_bound(d2, m2, n - k, 0.05)
    assert (disputes.flagged_upper_bound, disputes.unflagged_upper_bound) == (f_up, u_up)
    assert disputes.lower_bound_at_upper_bounds == pytest.approx(
        _lower_bound_at(n + f_up - u_up, k + f_up, 0.05))

    record = json.loads(json.dumps(to_jsonable(result.to_payload())))
    assert record["labels"]["sensitivity"]["kind"] == "EXACT"
    assert "not a joint confidence" in record["labels"]["second_review"]["disputes"]["whole_file"]["meaning"]
    text = render_recheck(result)
    text.encode("ascii")
    assert "If the labels are wrong" in text
    assert "does not revoke is still an absence of evidence" in text


def result_alpha(config) -> float:
    return 1.0 - config.validation.ci


def test_label_2_changes_no_recheck_verdict(tmp_path, fast):
    with_second = load_scored_items(_file(tmp_path, "a.csv", seed=11))
    without = load_scored_items(_file(tmp_path, "b.csv", seed=11, second=False))
    assert with_second.scores == without.scores and with_second.labels == without.labels
    contrary = dataclasses.replace(with_second, second_labels=tuple(1 - y for y in with_second.labels))
    payloads = []
    for items in (with_second, without, contrary):
        payload = to_jsonable(recheck_items(fast, items, budget=0.05, threshold=THRESHOLD).to_payload())
        payload.pop("labels")
        payloads.append(payload)
    assert payloads[0] == payloads[1] == payloads[2]


def test_a_broken_bound_carries_no_count(tmp_path, fast):
    items = load_scored_items(_file(tmp_path, "broken.csv", seed=5, negative_shift=0.6))
    result = recheck_items(fast, items, budget=0.05, threshold=THRESHOLD)
    assert result.bound_still_holds is False
    assert not result.label_sensitivity.computed
    assert "recipe" in result.label_sensitivity.reason
    # 198 review (a): the observed disputes about counted false positives are a
    # measurement, reported with nothing recomputed from them.
    labels, scores, _ = items.as_arrays()
    second = np.array([-1 if v is None else v for v in items.second_labels])
    flagged_negative = (scores >= THRESHOLD) & (labels == 0)
    disputes = result.second_review.disputes
    assert disputes.flagged_negatives == int(flagged_negative.sum())
    assert disputes.reviewed_flagged_negatives == int((flagged_negative & (second >= 0)).sum())
    assert disputes.flagged_negatives_label_2_calls_positive == int((flagged_negative & (second == 1)).sum())
    text = json.dumps(to_jsonable(result.to_payload()))
    assert "errors_to_revoke" not in text
    assert "lower_bound_if" not in text and "would_have_revoked" not in text
    assert "The revocation stands" in text
    assert "The revocation stands" in render_recheck(result)


def test_a_file_with_no_negatives_carries_no_count():
    result = recheck_label_sensitivity(
        bound_holds=None, grouped=False, single_label=True, k=None, n=0,
        flagged_positives=None, budget=0.05, alpha=0.05,
    )
    assert not result.computed and "no negatives" in result.reason


def test_grouped_rechecks_count_whole_groups_or_nothing(tmp_path, fast):
    rng = np.random.default_rng(4)
    single = ["id,label,score,group"]
    mixed = ["id,label,score,group"]
    for g in range(400):
        label = 1 if g % 4 == 0 else 0
        for j in range(2):
            single.append(f"g{g}-{j},{label},{rng.normal(2.0 * label, 1):.6f},g{g}")
        for y in (0, 1):
            mixed.append(f"h{g}-{y},{y},{rng.normal(2.0 * y, 1):.6f},h{g}")
    (tmp_path / "single.csv").write_text("\n".join(single) + "\n", encoding="utf-8")
    (tmp_path / "mixed.csv").write_text("\n".join(mixed) + "\n", encoding="utf-8")

    single_result = recheck_items(fast, load_scored_items(tmp_path / "single.csv"), budget=0.05, threshold=2.5)
    assert single_result.unit == "cluster" and single_result.bound_still_holds is True
    sensitivity = single_result.label_sensitivity
    assert sensitivity.computed and sensitivity.unit == "groups"
    assert sensitivity.n == 300

    mixed_result = recheck_items(fast, load_scored_items(tmp_path / "mixed.csv"), budget=0.05, threshold=2.5)
    assert not mixed_result.label_sensitivity.computed
    assert "both labels" in mixed_result.label_sensitivity.reason


def test_a_chained_recheck_carries_no_per_file_count(tmp_path, capsys):
    reference = _file(tmp_path, "reference.csv", seed=7, second=False)
    warrant = tmp_path / "reference.warrant.json"
    assert main(["certify", "-i", str(reference), "-b", "0.05", "-q", "-o", str(warrant)]) == 0
    fresh = _file(tmp_path, "fresh.csv", seed=11)
    out = tmp_path / "fresh.recheck.json"
    code = main(["recheck", "-w", str(warrant), "-i", str(fresh), "--horizon-labels", "20000",
                 "-o", str(out)])
    assert code in (0, 1)
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["chain"] is not None
    assert record["labels"]["sensitivity"]["computed"] is False
    assert "chain" in record["labels"]["sensitivity"]["reason"]
    assert record["labels"]["second_review"]["disputes"]["computed"] is False
    assert "kappa" in record["labels"]["second_review"]
    assert "errors_to_revoke" not in json.dumps(record)


def test_a_chained_result_that_kept_per_file_counts_is_refused(tmp_path, fast):
    """198 review (c): structural, not dependent on apply_chain being the only path."""
    from controlplane.intake.recheck import require_chain_replaced

    result = recheck_items(fast, load_scored_items(_file(tmp_path, "a.csv", seed=11)),
                           budget=0.05, threshold=THRESHOLD)
    with pytest.raises(RuntimeError, match="per-file label-error counts"):
        require_chain_replaced(result)
    counts_gone = dataclasses.replace(result, label_sensitivity=dataclasses.replace(
        result.label_sensitivity, computed=False))
    with pytest.raises(RuntimeError, match="label_2 disputes"):
        require_chain_replaced(counts_gone)
    require_chain_replaced(dataclasses.replace(counts_gone, second_review=dataclasses.replace(
        result.second_review, disputes=None)))
