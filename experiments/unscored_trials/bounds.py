"""Exact finite-corpus accounting with explicit population and weight choices.

Unknown rewards are independently free in [0, 1]. Task alignment supplies no
additional reward constraint, so pair differences use separable extrema.
These functions do not identify missing executions or validate retry histories.
"""

from __future__ import annotations

import math
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from typing import Iterable, Sequence

Bounds = tuple[Fraction, Fraction]


def validate_score(value: object) -> Fraction | None:
    """Preserve unknowns and valid zeroes while rejecting malformed rewards.

    Decimal-string conversion of finite floats preserves their reported decimal
    value rather than introducing their binary storage expansion.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, Fraction)):
        raise ValueError("reward must be numeric or None; booleans are not rewards")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("reward must be finite")
    if isinstance(value, Decimal) and not value.is_finite():
        raise ValueError("reward must be finite")
    reward = Fraction(str(value))
    if not 0 <= reward <= 1:
        raise ValueError("reward must lie in [0, 1]")
    return reward


def _known_score(value: object, name: str) -> Fraction:
    reward = validate_score(value)
    if reward is None:
        raise ValueError(f"{name} must be observed")
    return reward


def _population(
    rewards: Sequence[object], weights: Sequence[object] | None,
) -> tuple[tuple[Fraction | None, ...], tuple[Fraction, ...]]:
    values = tuple(validate_score(reward) for reward in rewards)
    if not values:
        raise ValueError("population must contain at least one named record")
    if weights is None:
        fixed_weights = (Fraction(1, len(values)),) * len(values)
    else:
        if len(weights) != len(values):
            raise ValueError("weights and rewards must describe the same population")
        fixed_weights = tuple(_known_score(weight, "weight") for weight in weights)
        if sum(fixed_weights) != 1:
            raise ValueError("nonnegative fixed weights must sum exactly to one")
    return values, fixed_weights


def weighted_bounds(
    rewards: Sequence[object], weights: Sequence[object] | None = None,
) -> Bounds:
    """Bound only genuinely unknown rewards while holding all weights fixed."""
    values, fixed_weights = _population(rewards, weights)
    lower = sum((weight * reward for reward, weight in zip(values, fixed_weights, strict=True)
                 if reward is not None), Fraction(0))
    missing = sum((weight for reward, weight in zip(values, fixed_weights, strict=True)
                   if reward is None), Fraction(0))
    return lower, lower + missing


def weighted_mean(
    rewards: Sequence[object], weights: Sequence[object] | None = None,
    unknown_value: object = 0,
) -> Fraction:
    """Compute an explicitly filled policy mean, including native null-as-zero."""
    fill = _known_score(unknown_value, "unknown fill")
    values, fixed_weights = _population(rewards, weights)
    return sum((weight * (fill if reward is None else reward)
                for reward, weight in zip(values, fixed_weights, strict=True)), Fraction(0))


def _validated_bounds(bounds: Sequence[object]) -> Bounds:
    if len(bounds) != 2:
        raise ValueError("bounds need exactly two endpoints")
    lower, upper = (_known_score(endpoint, "bound endpoint") for endpoint in bounds)
    if lower > upper:
        raise ValueError("lower bound cannot exceed upper bound")
    return lower, upper


def difference_bounds(a_bounds: Sequence[object], b_bounds: Sequence[object]) -> Bounds:
    """Use independently feasible reward assignments even for shared unknowns."""
    a_lower, a_upper = _validated_bounds(a_bounds)
    b_lower, b_upper = _validated_bounds(b_bounds)
    return a_lower - b_upper, a_upper - b_lower


def classify_pair(
    a_bounds: Sequence[object], b_bounds: Sequence[object],
    native_a: object, native_b: object,
) -> dict:
    """Separate strict reversals from equality at exact interval boundaries.

    A nonidentified native tie is equality-compatible rather than a reversal of
    a nonexistent strict order; explicit flags say which strict orders it permits.
    """
    a_interval = _validated_bounds(a_bounds)
    b_interval = _validated_bounds(b_bounds)
    a_point = _known_score(native_a, "native A mean")
    b_point = _known_score(native_b, "native B mean")
    if not (a_interval[0] <= a_point <= a_interval[1]
            and b_interval[0] <= b_point <= b_interval[1]):
        raise ValueError("native points must belong to their fixed-population bounds")
    lower, upper = difference_bounds(a_interval, b_interval)
    native_order = "a" if a_point > b_point else "b" if b_point > a_point else "tie"
    robust_order = "a" if lower > 0 else "b" if upper < 0 else None
    if robust_order is not None:
        classification = "strict_robust"
    elif lower == upper == 0:
        classification, robust_order = "identified_tie", "tie"
    elif ((native_order == "a" and lower < 0)
          or (native_order == "b" and upper > 0)):
        classification = "reversal_compatible"
    else:
        classification = "equality_compatible"
    return {
        "native_order": native_order,
        "classification": classification,
        "robust_order": robust_order,
        "difference_lower": lower,
        "difference_upper": upper,
        "equality_possible": lower <= 0 <= upper,
        "a_strict_possible": upper > 0,
        "b_strict_possible": lower < 0,
        "native_tie_can_break": native_order == "tie" and (lower < 0 or upper > 0),
    }


def cap_bounds(observed_mean: object, cap: object, actual_missing_fraction: object) -> Bounds:
    """Reject a cap incompatible with this same population's actual missingness."""
    mean = _known_score(observed_mean, "observed mean")
    epsilon = _known_score(cap, "missingness cap")
    actual = _known_score(actual_missing_fraction, "actual missing fraction")
    if actual > epsilon:
        raise ValueError("actual missing fraction exceeds cap; no silent subset change")
    lower = (1 - epsilon) * mean
    return lower, lower + epsilon


def aggregate_tasks(records: Iterable[tuple[str, object]]) -> dict:
    """Show equal-task and pooled-final policies as distinct fixed estimands.

    Every tuple names an observed final record, including records with unknown
    rewards. This function never constructs an unobserved Cartesian trial roster.
    """
    rows = list(records)
    if not rows:
        raise ValueError("at least one named final record is required")
    if any(not isinstance(task, str) or not task for task, _ in rows):
        raise ValueError("every final record needs a nonempty task identity")
    values = tuple(validate_score(reward) for _, reward in rows)
    task_counts = Counter(task for task, _ in rows)
    equal_weights = tuple(Fraction(1, len(task_counts) * task_counts[task])
                          for task, _ in rows)
    pooled_weights = (Fraction(1, len(rows)),) * len(rows)

    def policy(weights: tuple[Fraction, ...]) -> dict:
        missing = sum((weight for reward, weight in zip(values, weights, strict=True)
                       if reward is None), Fraction(0))
        return {
            "native_mean": weighted_mean(values, weights, unknown_value=0),
            "bounds": weighted_bounds(values, weights),
            "missing_weight": missing,
            "weights": weights,
        }

    return {
        "record_count": len(rows),
        "task_count": len(task_counts),
        "unknown_record_count": sum(reward is None for reward in values),
        "task_counts": dict(task_counts),
        "equal_task": policy(equal_weights),
        "pooled": policy(pooled_weights),
    }


def retry_diagnostic(lineage: object = None) -> dict:
    """Refuse retry inference without validated lineage and budget contracts."""
    if lineage is None:
        return {"status": "unavailable", "reason": "No explicit retry lineage is supplied; "
                "repeated final trials do not establish retries.", "inferred_retries": None}
    return {"status": "unsupported", "reason": "Lineage supplied without a validated retry "
            "policy and budget contract; no retry conclusion is implemented.",
            "inferred_retries": None}
