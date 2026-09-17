"""Independent statistical and leakage checks using synthetic scored fixtures."""

import json
from pathlib import Path
from dataclasses import replace
from datetime import datetime, timezone

import numpy as np
import pytest
from scipy.optimize import brentq
from scipy.stats import binom

from controlplane.intake.contract import ScoredItems
from controlplane.release.contract import ReleaseSpec, digest, register
from controlplane.release.evaluate import (
    binomial_rate, evaluate, identity_for, seal_evaluation, verify_evaluation,
)


@pytest.fixture
def release_spec():
    return ReleaseSpec("support", "v1", "probe", "v2", "English QA",
                       "incorrect answer", 0.5, 0.05, 0.1, 0.05,
                       "2030-01-01T00:00:00Z", "synthetic", "iid")


@pytest.fixture
def release_now():
    return datetime(2026, 9, 14, tzinfo=timezone.utc)


def sample(n_negative=500, n_positive=100, fp=0, tp=None):
    """Synthetic correctness fixture, never production performance evidence."""
    tp = n_positive if tp is None else tp
    labels = (0,) * n_negative + (1,) * n_positive
    scores = (0.9,) * fp + (0.1,) * (n_negative - fp)
    scores += (0.9,) * tp + (0.1,) * (n_positive - tp)
    return ScoredItems(tuple(f"test-{i}" for i in range(len(labels))), labels,
                       scores, None, (), "synthetic")


def measure(spec, now, items):
    contract = register(spec, ["development"], items.ids, now=now)
    return contract, evaluate(contract, items, identity_for(contract), now=now)


@pytest.mark.parametrize("n,k,alpha", [(20, 4, .1), (500, 17, .01), (9, 8, .005)])
def test_bounds_agree_with_independent_binomial_tail_inversion(n, k, alpha):
    interval = binomial_rate(k, n, alpha)
    upper = brentq(lambda p: binom.cdf(k, n, p) - alpha / 2, 0, 1)
    lower = brentq(lambda p: binom.sf(k - 1, n, p) - alpha / 2, 0, 1)
    assert interval["lower"] == pytest.approx(lower, abs=1e-11)
    assert interval["upper"] == pytest.approx(upper, abs=1e-11)


@pytest.mark.parametrize("n", [1, 5, 20, 80])
def test_exact_enumeration_respects_allocated_error_probability(n):
    alpha = .05 / 5
    intervals = [binomial_rate(k, n, alpha) for k in range(n + 1)]
    for p in [0, .001, .01, .05, .25, .5, .9, .999, 1]:
        miss = [p < ci["lower"] or p > ci["upper"] for ci in intervals]
        probability = np.sum(binom.pmf(np.arange(n + 1), n, p)[miss])
        assert probability <= alpha + 1e-12


@pytest.mark.parametrize("items,status", [
    (sample(), "VALID"), (sample(fp=100), "REFUSED"),
    (sample(tp=0), "REFUSED"), (sample(20, 20), "REFUSED"),
    (sample(n_positive=0), "REFUSED"),
])
def test_decisions_distinguish_failure_from_missing_evidence(release_spec, release_now, items, status):
    _, result = measure(release_spec, release_now, items)
    assert result["status"] == status
    assert result["rates"]["precision"]["n"] == result["counts"]["flagged"]
    assert result["rates"]["recall"]["n"] == result["counts"]["positive"]
    assert all(rate["confidence"] == .99 for rate in result["rates"].values())


@pytest.mark.parametrize("items,metric,reason", [
    (sample(), "fpr", "bound_cleared"),
    (sample(fp=100), "fpr", "observed_violation"),
    (sample(20, 20), "fpr", "inconclusive_bound"),
    (sample(n_positive=0), "recall", "missing_denominator"),
])
def test_protocol_two_names_the_evidence_reason(release_spec, release_now, items, metric, reason):
    _, result = measure(release_spec, release_now, items)
    assert result["schema_version"] == 2
    assert next(check for check in result["checks"] if check["metric"] == metric)["reason"] == reason


def test_release_and_single_fpr_certification_name_different_protocols(release_spec, release_now):
    from controlplane.release.render import render_evaluation
    from controlplane.intake.certify import certify_budget

    items = sample(n_negative=60, n_positive=100)
    single = certify_budget(items, release_spec.max_fpr, release_spec.alpha)
    _, result = measure(release_spec, release_now, items)
    assert single.fpr_certified
    assert np.array_equal(np.asarray(items.scores) >= single.threshold,
                          np.asarray(items.scores) >= release_spec.threshold)
    assert result["status"] == "REFUSED"
    assert result["checks"][0]["reason"] == "inconclusive_bound"
    output = render_evaluation(result, result["status"])
    assert "release/v2" in output
    assert "one-sided FPR bound" in output


def test_legacy_contract_keeps_its_original_measurement_protocol(release_spec, release_now):
    from controlplane.release.contract import ReleaseContract
    from controlplane.release.render import render_evaluation

    items = sample(20, 20)
    new_contract, new_result = measure(release_spec, release_now, items)
    legacy = replace(new_contract, schema_version=1)
    assert legacy.to_dict()["contract_id"] != new_contract.to_dict()["contract_id"]
    legacy = ReleaseContract.from_dict(legacy.to_dict())
    result = evaluate(legacy, items, identity_for(legacy), now=release_now)
    # Frozen from evaluate.py at aa7b0af before protocol 2 existed. Only
    # numerical-library rounding in computed bounds is tolerated by this test;
    # production verification still compares the complete measurement exactly.
    expected = json.loads((Path(__file__).parent / "fixtures/release_v1_measurement.json").read_text())
    assert {k: v for k, v in result.items() if k not in ("rates", "lift")} == {
        k: v for k, v in expected.items() if k not in ("rates", "lift")}
    for observed, original in [(result["lift"], expected["lift"]), *[
        (result["rates"][name], expected["rates"][name]) for name in result["rates"]]]:
        for key, value in original.items():
            if isinstance(value, float):
                assert observed[key] == pytest.approx(value, rel=1e-12, abs=1e-14)
            else:
                assert observed[key] == value
    assert result["schema_version"] == 1
    assert result["status"] == "UNVALIDATED"
    assert all("reason" not in check for check in result["checks"])
    assert result["rates"] == new_result["rates"]
    assert verify_evaluation(seal_evaluation(result), legacy, items, identity_for(legacy), now=release_now) == "UNVALIDATED"
    assert "LEGACY protocol 1" in render_evaluation(result, result["status"])


def test_never_fire_does_not_gain_zero_width_precision_or_infinite_lift(release_spec, release_now):
    _, result = measure(release_spec, release_now, sample(tp=0))
    assert result["rates"]["precision"]["value"] is None
    assert result["rates"]["precision"]["lower"] == 0
    assert result["rates"]["precision"]["upper"] == 1
    assert result["lift"]["value"] is None
    assert result["lift"]["upper"] is None


@pytest.mark.parametrize("mutation", ["group", "missing", "duplicate", "nonfinite", "identity", "expiry"])
def test_invalid_evaluation_cannot_issue(release_spec, release_now, mutation):
    items = sample()
    contract, _ = measure(release_spec, release_now, items)
    identity = identity_for(contract)
    now = release_now
    if mutation == "group":
        items = replace(items, groups=("one-dependent-cluster",) * items.n)
    elif mutation == "missing":
        items = replace(items, ids=items.ids[:-1], labels=items.labels[:-1], scores=items.scores[:-1])
    elif mutation == "duplicate":
        items = replace(items, ids=(items.ids[1],) + items.ids[1:])
    elif mutation == "nonfinite":
        items = replace(items, scores=(float("nan"),) + items.scores[1:])
    elif mutation == "identity":
        identity["system_version"] = "unmeasured-v2"
    else:
        now = datetime(2031, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        evaluate(contract, items, identity, now=now)


def test_recompute_catches_rehashed_fabrication_and_expiry(release_spec, release_now):
    items = sample()
    contract, result = measure(release_spec, release_now, items)
    record = seal_evaluation(result)
    assert verify_evaluation(record, contract, items, identity_for(contract), now=release_now) == "VALID"
    assert verify_evaluation(record, contract, items, identity_for(contract),
                             now=datetime(2031, 1, 1, tzinfo=timezone.utc)) == "STALE"
    record["counts"]["tp"] -= 1
    record["evidence_id"] = digest({k: v for k, v in record.items() if k != "evidence_id"})
    with pytest.raises(ValueError, match="reproduce"):
        verify_evaluation(record, contract, items, identity_for(contract), now=release_now)


def test_data_hash_is_order_independent_but_binds_scores(release_spec, release_now):
    items = sample()
    contract, first = measure(release_spec, release_now, items)
    shuffled = replace(items, ids=items.ids[::-1], labels=items.labels[::-1], scores=items.scores[::-1])
    assert evaluate(contract, shuffled, identity_for(contract), now=release_now) == first
    changed = replace(items, scores=(.11,) + items.scores[1:])
    second = evaluate(contract, changed, identity_for(contract), now=release_now)
    assert second["counts"] == first["counts"]
    assert second["data_sha256"] != first["data_sha256"]
