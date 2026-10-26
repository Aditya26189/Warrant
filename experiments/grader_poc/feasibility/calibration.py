"""Independent, explicitly partial correctness contract for HumanEval/0."""

import itertools
import math
import random
from bisect import bisect_left, insort
from fractions import Fraction
from typing import Any


def in_domain(numbers: list[float], threshold: float, domain: dict) -> bool:
    """Restrict claims to exactly represented quarter-grid arithmetic."""
    if type(numbers) is not list or len(numbers) > domain["max_length"]:
        return False
    scale = domain["tick_denominator"]

    def tick_valid(value: Any, lower: int, upper: int) -> bool:
        return (
            type(value) is float
            and math.isfinite(value)
            and (value * scale).is_integer()
            and lower <= value * scale <= upper
        )

    return tick_valid(
        threshold, domain["threshold_tick_min"], domain["threshold_tick_max"]
    ) and all(
        tick_valid(n, domain["number_tick_min"], domain["number_tick_max"])
        for n in numbers
    )


def expected_from_spec(numbers: list[float], threshold: float, domain: dict) -> bool:
    """Evaluate the prompt's existential property without reference execution."""
    if not in_domain(numbers, threshold, domain):
        raise ValueError("OUT_OF_DECLARED_DOMAIN")
    values = [Fraction.from_float(n) for n in numbers]
    limit = Fraction.from_float(threshold)
    return any(abs(a - b) < limit for a, b in itertools.combinations(values, 2))


def property_holds(
    observed: Any, numbers: list[float], threshold: float, domain: dict
) -> bool:
    """Require the documented boolean result, not equality of internal state."""
    return type(observed) is bool and observed is expected_from_spec(
        numbers, threshold, domain
    )


def alternative(numbers: list[float], threshold: float) -> bool:
    """Check each inserted value's neighbors without sorting the input in bulk."""
    seen: list[float] = []
    for value in numbers:
        position = bisect_left(seen, value)
        if position and value - seen[position - 1] < threshold:
            return True
        if position < len(seen) and seen[position] - value < threshold:
            return True
        insort(seen, value)
    return False


def property_inputs(config: dict) -> list[dict]:
    """Return the frozen small exhaustive grid followed by seeded broader inputs."""
    domain, corpus = config["domain"], config["corpus"]
    scale = domain["tick_denominator"]
    cases = []
    for length in range(corpus["exhaustive_max_length"] + 1):
        for ticks in itertools.product(corpus["exhaustive_number_ticks"], repeat=length):
            for threshold in corpus["exhaustive_threshold_ticks"]:
                cases.append({"numbers": [n / scale for n in ticks],
                              "threshold": threshold / scale, "kind": "small_grid"})
    rng = random.Random(corpus["seed"])
    for _ in range(corpus["random_inputs"]):
        length = rng.randint(0, domain["max_length"])
        cases.append({
            "numbers": [rng.randint(domain["number_tick_min"],
                                    domain["number_tick_max"]) / scale
                        for _ in range(length)],
            "threshold": rng.randint(domain["threshold_tick_min"],
                                     domain["threshold_tick_max"]) / scale,
            "kind": "seeded",
        })
    return cases
