"""A certificate's sensitivity to label error, and ``label_2`` beside it (DECISIONS 197).

What these defend:

* the sensitivity is propagated **through the Clopper-Pearson bound**: at the
  confidence ``c(e)`` reported, the bound on the corrected counts is exactly the
  budget -- not a point estimate nudged by ``e``;
* every figure 197 quotes is what the code computes;
* the whole-file dispute bound is exact: it covers at ``1 - alpha`` for every
  true number of disputes, checked by enumeration;
* ``label_2`` changes **no** status, threshold, bound or metric, even when it
  disagrees with every label;
* a refusal carries no count of relabellings that would turn it into a warrant.
"""

from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from controlplane.intake import InputError, certify_items, load_scored_items, render_summary
from controlplane.intake.labels import (
    CONFIDENCE_LADDER,
    confidence_after,
    disputes_upper_bound,
    errors_below,
)
from controlplane.model import WarrantStatus, to_jsonable
from controlplane.validation.warrant_stats import cp_upper


@pytest.fixture(scope="module")
def fast(config):
    return dataclasses.replace(
        config, validation=dataclasses.replace(config.validation, bootstrap_samples=200)
    )


def _largest_certifying_k(n: int, budget: float, alpha: float) -> int:
    return max(k for k in range(n) if cp_upper(k, n, alpha) <= budget)


# ------------------------------------------------------------ the arithmetic

@pytest.mark.parametrize("n,e", [(59, 1), (200, 3), (628, 5), (1000, 10), (5000, 20)])
def test_the_confidence_is_the_level_at_which_the_corrected_bound_equals_the_budget(n, e):
    budget = 0.05
    k = _largest_certifying_k(n, budget, 0.05)
    c = confidence_after(k, n, budget, flagged_clean=e)
    assert 0.0 < c < 1.0
    # The Clopper-Pearson duality: at level 1 - c the bound on (k+e, n+e) is B.
    assert cp_upper(k + e, n + e, 1.0 - c) == pytest.approx(budget, abs=1e-9)


def test_the_unflagged_direction_removes_a_negative_unit():
    k, n, budget = 22, 628, 0.05
    c = confidence_after(k, n, budget, flagged_clean=2, unflagged_positive=3)
    assert c == pytest.approx(1.0 - stats.binom.cdf(24, 627, budget))
    with pytest.raises(ValueError, match="unflagged"):
        confidence_after(k, n, budget, unflagged_positive=n - k + 1)


def test_the_confidence_never_rises_as_errors_are_added():
    for n in (59, 137, 628):
        for budget in (0.01, 0.05, 0.10):
            if cp_upper(0, n, 0.05) > budget:
                continue
            k = _largest_certifying_k(n, budget, 0.05)
            series = [confidence_after(k, n, budget, flagged_clean=e) for e in range(60)]
            assert all(b <= a + 1e-12 for a, b in zip(series, series[1:]))


@pytest.mark.parametrize("n,k,c0,c1,c3,c5", [
    (59, 0, 0.952, 0.808, 0.376, 0.100),
    (200, 4, 0.974, 0.939, 0.800, 0.577),
    (628, 22, 0.954, 0.932, 0.867, 0.772),
    (5000, 224, 0.953, 0.946, 0.931, 0.912),
])
def test_the_table_in_decisions_197_is_what_the_code_computes(n, k, c0, c1, c3, c5):
    assert _largest_certifying_k(n, 0.05, 0.05) == k
    for e, quoted in ((0, c0), (1, c1), (3, c3), (5, c5)):
        assert round(confidence_after(k, n, 0.05, flagged_clean=e), 3) == quoted


def test_a_fragility_index_would_be_one_on_every_row():
    """197's reason for rejecting it: c(1) < 1 - alpha at the lowest threshold."""
    for n in (59, 200, 628, 5000):
        k = _largest_certifying_k(n, 0.05, 0.05)
        assert confidence_after(k, n, 0.05, flagged_clean=1) < 0.95


def test_errors_below_matches_a_scan_and_says_none_when_out_of_reach():
    k, n, budget = 22, 628, 0.05
    found = errors_below(k, n, budget, limit=200)
    for level in CONFIDENCE_LADDER:
        scan = next(e for e in range(201) if confidence_after(k, n, budget, flagged_clean=e) < level)
        assert found[level] == scan
    assert errors_below(k, n, budget, limit=1) == {0.90: None, 0.80: None, 0.50: None}


# ------------------------------------------------------------ the dispute bound

def test_the_dispute_bound_is_exact_when_every_item_was_reviewed():
    assert disputes_upper_bound(3, 40, 40, 0.05) == 3
    assert disputes_upper_bound(0, 40, 40, 0.05) == 0


@pytest.mark.parametrize("population,reviewed", [(30, 5), (40, 12), (25, 24)])
def test_the_dispute_bound_covers_every_true_count(population, reviewed):
    """Enumerated, not simulated: P(bound >= D) >= 1 - alpha for every D."""
    alpha = 0.05
    bound = {d: disputes_upper_bound(d, reviewed, population, alpha) for d in range(reviewed + 1)}
    for true in range(population + 1):
        support = range(max(0, reviewed - (population - true)), min(reviewed, true) + 1)
        covered = sum(
            stats.hypergeom.pmf(d, population, true, reviewed)
            for d in support if bound[d] >= true
        )
        assert covered >= 1 - alpha - 1e-9, (true, covered)


def test_the_dispute_bound_is_the_largest_count_not_rejected():
    d, m, population, alpha = 1, 23, 209, 0.05
    bound = disputes_upper_bound(d, m, population, alpha)
    assert stats.hypergeom.cdf(d, population, bound, m) >= alpha
    assert stats.hypergeom.cdf(d, population, bound + 1, m) < alpha


# ------------------------------------------------------------ the contract

def _rows(n_neg=700, n_pos=300, seed=7, every=10, flip=0.05, second=True):
    rng = np.random.default_rng(seed)
    rows = [(f"n{i}", 0, rng.normal(0, 1)) for i in range(n_neg)]
    rows += [(f"p{i}", 1, rng.normal(2.0, 1)) for i in range(n_pos)]
    lines = ["id,label,score" + (",label_2" if second else "")]
    for j, (item, label, score) in enumerate(rows):
        extra = ""
        if second:
            extra = "," + (str(label if rng.random() > flip else 1 - label) if j % every == 0 else "")
        lines.append(f"{item},{label},{score:.6f}{extra}")
    return "\n".join(lines) + "\n"


def _write(tmp_path: Path, text: str, name: str = "in.csv") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_label_2_is_read_blank_as_not_reviewed_and_is_not_passed_through(tmp_path):
    items = load_scored_items(_write(tmp_path, "id,label,score,label_2,note\na,1,0.9,,x\nb,0,0.1,1.0,y\n"))
    assert items.second_labels == (None, 1)
    assert "label_2" not in items.passthrough_columns
    assert items.passthrough_columns == ("note",)


def test_label_2_in_jsonl_accepts_null_and_a_missing_key(tmp_path):
    text = '{"id": "a", "label": 1, "score": 0.9, "label_2": null}\n{"id": "b", "label": 0, "score": 0.1, "label_2": 0}\n{"id": "c", "label": 0, "score": 0.2}\n'
    items = load_scored_items(_write(tmp_path, text, "in.jsonl"))
    assert items.second_labels == (None, 0, None)


def test_a_non_binary_label_2_is_refused_by_name(tmp_path):
    with pytest.raises(InputError, match="label_2 is '0.5'"):
        load_scored_items(_write(tmp_path, "id,label,score,label_2\na,1,0.9,0.5\nb,0,0.1,\n"))


def test_a_label_2_column_blank_on_every_row_is_refused(tmp_path):
    with pytest.raises(InputError, match="blank on every row"):
        load_scored_items(_write(tmp_path, "id,label,score,label_2\na,1,0.9,\nb,0,0.1,\n"))


def test_a_file_without_label_2_has_none(tmp_path):
    items = load_scored_items(_write(tmp_path, "id,label,score\na,1,0.9\nb,0,0.1\n"))
    assert items.second_labels is None


# ------------------------------------------------------------ the certificate

def _comparable(result):
    payload = to_jsonable(result.to_payload())
    payload.pop("labels")
    payload["input"].pop("source")
    return payload


def test_label_2_changes_no_status_threshold_bound_or_metric(tmp_path, fast):
    with_second = load_scored_items(_write(tmp_path, _rows(), "a.csv"))
    without = load_scored_items(_write(tmp_path, _rows(second=False), "b.csv"))
    assert with_second.labels == without.labels and with_second.scores == without.scores
    # A second reviewer who disagrees with every single label.
    contrary = dataclasses.replace(with_second, second_labels=tuple(1 - y for y in with_second.labels))
    results = [certify_items(fast, items, budget=0.05) for items in (with_second, without, contrary)]
    assert results[0].status is WarrantStatus.VALID
    reference = _comparable(results[1])
    for result in (results[0], results[2]):
        assert _comparable(result) == reference
    assert results[1].second_review is None
    assert results[2].second_review.agreement.observed_agreement == 0.0
    assert results[2].second_review.agreement.kappa < 0.0


def test_a_certificate_carries_its_sensitivity_and_the_disputes_count_what_they_say(tmp_path, fast):
    items = load_scored_items(_write(tmp_path, _rows()))
    result = certify_items(fast, items, budget=0.05)
    labels, scores, _ = items.as_arrays()
    k, n = result.false_positives_at_threshold, result.negative_units
    flagged = scores >= result.threshold
    second = np.array([-1 if v is None else v for v in items.second_labels])

    sensitivity = result.label_sensitivity
    assert sensitivity.computed and sensitivity.unit == "items"
    assert sensitivity.confidence_as_labelled >= 0.95
    flagged_clean, unflagged_positive = sensitivity.flagged_clean, sensitivity.unflagged_positive
    assert flagged_clean.limit == int((flagged & (labels == 1)).sum())
    assert flagged_clean.confidence_if_one == pytest.approx(1 - stats.binom.cdf(k + 1, n + 1, 0.05))
    assert flagged_clean.bound_if_one == pytest.approx(cp_upper(k + 1, n + 1, result.alpha))
    # The second flattering error (197 review, F1): one fewer negative.
    assert unflagged_positive.limit == n - k == int((~flagged & (labels == 0)).sum())
    assert unflagged_positive.confidence_if_one == pytest.approx(1 - stats.binom.cdf(k, n - 1, 0.05))
    assert unflagged_positive.bound_if_one == pytest.approx(cp_upper(k, n - 1, result.alpha))
    assert unflagged_positive.errors_below == errors_below(
        k, n, 0.05, n - k, kind="unflagged_positive")

    disputes = result.second_review.disputes
    d1 = int((flagged & (labels == 1) & (second == 0)).sum())
    d2 = int((~flagged & (labels == 0) & (second == 1)).sum())
    m1 = int((flagged & (labels == 1) & (second >= 0)).sum())
    m2 = int((~flagged & (labels == 0) & (second >= 0)).sum())
    assert (disputes.flagged_positives_disputed, disputes.unflagged_negatives_disputed) == (d1, d2)
    assert (disputes.reviewed_flagged_positives, disputes.reviewed_unflagged_negatives) == (m1, m2)
    assert disputes.confidence_if_disputes_are_errors == pytest.approx(
        1 - stats.binom.cdf(k + d1, n + d1 - d2, 0.05))
    # Both pools extrapolated on the same footing (197 review, F2).
    f_up = disputes_upper_bound(d1, m1, flagged_clean.limit, result.alpha)
    u_up = disputes_upper_bound(d2, m2, n - k, result.alpha)
    assert (disputes.flagged_upper_bound, disputes.unflagged_upper_bound) == (f_up, u_up)
    assert disputes.confidence_at_upper_bounds == pytest.approx(
        confidence_after(k, n, 0.05, flagged_clean=f_up, unflagged_positive=u_up))
    assert result.second_review.n_pairs == int((second >= 0).sum())

    record = json.loads(json.dumps(to_jsonable(result.to_payload())))
    whole = record["labels"]["second_review"]["disputes"]["whole_file"]
    assert "union bound" in whole["joint_level"]
    assert "not a joint confidence" in whole["confidence_meaning"]
    direction = record["labels"]["sensitivity"]["direction"]
    assert "unflagged item labelled negative that is really positive" in direction
    assert record["labels"]["sensitivity"]["kind"] == "EXACT"
    assert record["labels"]["second_review"]["kappa"]["kind"] == "ESTIMATED"
    assert record["labels"]["second_review"]["kappa"]["n"] == result.second_review.n_pairs
    assert record["labels"]["second_review"]["changes_the_verdict"] is False


def test_a_refusal_carries_no_count_of_relabellings(tmp_path, fast):
    items = load_scored_items(_write(tmp_path, _rows(n_neg=40, n_pos=20)))
    result = certify_items(fast, items, budget=0.05)
    assert result.status is WarrantStatus.REFUSED
    labels = result.to_payload()["labels"]
    assert labels["sensitivity"] == {
        "computed": False, "reason": result.label_sensitivity.reason,
    }
    assert "recipe" in labels["sensitivity"]["reason"]
    assert labels["second_review"]["disputes"]["computed"] is False
    assert "kappa" in labels["second_review"]
    text = json.dumps(to_jsonable(result.to_payload()))
    assert "errors_to_fall_below" not in text and "confidence_if_one" not in text
    assert "If the labels are wrong" not in render_summary(result)


def test_a_single_label_grouped_file_counts_whole_groups(tmp_path, fast):
    """197 review, F4: each group carries one label, so an error relabels a group."""
    rng = np.random.default_rng(3)
    lines = ["id,label,score,group,label_2"]
    for g in range(400):
        for j in range(2):
            label = 1 if g % 4 == 0 else 0
            score = rng.normal(2.0 if label else 0.0, 1)
            second = str(label) if g % 5 == 0 else ""
            lines.append(f"g{g}-{j},{label},{score:.6f},g{g},{second}")
    items = load_scored_items(_write(tmp_path, "\n".join(lines) + "\n"))
    result = certify_items(fast, items, budget=0.05)
    assert result.grouped and result.status is WarrantStatus.VALID
    sensitivity = result.label_sensitivity
    assert sensitivity.computed and sensitivity.unit == "groups"
    k, n = result.false_positives_at_threshold, result.negative_units
    assert n == 300
    labels, scores, groups = items.as_arrays()
    flagged_groups = {g for g, y, s in zip(groups, labels, scores) if y == 1 and s >= result.threshold}
    assert sensitivity.flagged_clean.limit == len(flagged_groups)
    assert sensitivity.unflagged_positive.limit == n - k
    assert sensitivity.flagged_clean.confidence_if_one == pytest.approx(
        confidence_after(k, n, 0.05, flagged_clean=1))
    assert "whole group" in json.dumps(to_jsonable(result.to_payload()))
    assert result.second_review.n_pairs == 160
    assert result.second_review.disputes is None
    assert "per item" in result.second_review.disputes_reason
    assert "counted in groups" in render_summary(result)


def test_a_grouped_file_with_a_mixed_group_has_no_sensitivity(tmp_path, fast):
    """One positive and one negative per group certifies -- F4's premise does not hold."""
    rng = np.random.default_rng(1)
    lines = ["id,label,score,group"]
    for g in range(120):
        for label in (0, 1):
            lines.append(f"g{g}-{label},{label},{rng.normal(2.0 * label, 1):.6f},g{g}")
    items = load_scored_items(_write(tmp_path, "\n".join(lines) + "\n"))
    result = certify_items(fast, items, budget=0.05)
    assert result.grouped and result.status is WarrantStatus.VALID
    assert not result.label_sensitivity.computed
    assert "both labels" in result.label_sensitivity.reason


def test_the_review_table_for_the_unflagged_error_is_what_the_code_computes():
    """The F1 table in 197's review section: 3.3% of the unflagged negatives."""
    for n, k, errors, c, ladder in (
        (5000, 224, 158, 0.878, (122, 257, 507)),
        (628, 22, 20, 0.934, (46, 93, 175)),
        (59, 0, 2, 0.946, (15, 28, 46)),
    ):
        assert _largest_certifying_k(n, 0.05, 0.05) == k
        assert round(confidence_after(k, n, 0.05, unflagged_positive=errors), 3) == c
        found = errors_below(k, n, 0.05, n - k, kind="unflagged_positive")
        assert tuple(found[level] for level in CONFIDENCE_LADDER) == ladder


def test_the_unflagged_ladder_matches_a_scan():
    k, n = 22, 628
    found = errors_below(k, n, 0.05, n - k, kind="unflagged_positive")
    for level in CONFIDENCE_LADDER:
        scan = next(
            (b for b in range(n - k + 1)
             if confidence_after(k, n, 0.05, unflagged_positive=b) < level), None)
        assert found[level] == scan
    with pytest.raises(ValueError, match="unflagged"):
        errors_below(k, n, 0.05, n - k + 1, kind="unflagged_positive")


def test_the_file_level_figure_needs_both_pools_reviewed(tmp_path, fast):
    lines = _rows().splitlines()
    # label_2 only on positives: no unflagged negative is double-labelled.
    kept = [lines[0]] + [
        line if line.split(",")[1] == "1" else ",".join(line.split(",")[:3]) + ","
        for line in lines[1:]
    ]
    result = certify_items(fast, load_scored_items(_write(tmp_path, "\n".join(kept) + "\n")), budget=0.05)
    disputes = result.second_review.disputes
    assert disputes.reviewed_unflagged_negatives == 0
    assert disputes.unflagged_upper_bound is None
    assert disputes.confidence_at_upper_bounds is None
    assert "no unflagged negative was double-labelled" in disputes.upper_bound_reason
    assert any("unflagged negative that is really positive" in w for w in result.second_review.warnings)
    assert "whole file: not computed" in render_summary(result)


def test_no_reviewed_flagged_positive_is_a_warning_not_a_bound(tmp_path, fast):
    text = _rows()
    lines = text.splitlines()
    # Keep label_2 only on negatives: the flattering direction goes unreviewed.
    kept = [lines[0]] + [
        line if line.split(",")[1] == "0" else ",".join(line.split(",")[:3]) + ","
        for line in lines[1:]
    ]
    items = load_scored_items(_write(tmp_path, "\n".join(kept) + "\n"))
    result = certify_items(fast, items, budget=0.05)
    review = result.second_review
    assert review.pairs_by_label[1] == 0
    assert review.disputes.flagged_upper_bound is None
    assert review.disputes.unflagged_upper_bound is not None
    assert review.disputes.confidence_at_upper_bounds is None
    assert "unreviewed" in review.disputes.upper_bound_reason
    assert any("labelled 1 was double-labelled" in w for w in review.warnings)
    assert any("costs this certificate most per item" in w for w in review.warnings)


def test_the_summary_says_what_the_confidence_is_not(tmp_path, fast):
    with_second = certify_items(fast, load_scored_items(_write(tmp_path, _rows(), "a.csv")), budget=0.05)
    without = certify_items(fast, load_scored_items(_write(tmp_path, _rows(second=False), "b.csv")), budget=0.05)
    text = render_summary(with_second)
    assert "If the labels are wrong" in text
    assert "not a probability" in text
    assert "which changes nothing above" in text
    assert "a worst case, not the truth" in text
    text.encode("ascii")
    assert "No label_2 column" in render_summary(without)
    assert math.isfinite(with_second.label_sensitivity.confidence_as_labelled)
