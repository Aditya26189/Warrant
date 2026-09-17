"""Independent statistical and leakage checks using synthetic scored fixtures."""

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
    (sample(tp=0), "REFUSED"), (sample(20, 20), "UNVALIDATED"),
    (sample(n_positive=0), "UNVALIDATED"),
])
def test_decisions_distinguish_failure_from_missing_evidence(release_spec, release_now, items, status):
    _, result = measure(release_spec, release_now, items)
    assert result["status"] == status
    assert result["rates"]["precision"]["n"] == result["counts"]["flagged"]
    assert result["rates"]["recall"]["n"] == result["counts"]["positive"]
    assert all(rate["confidence"] == .99 for rate in result["rates"].values())


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
