"""Reproduce a known adaptive-bound witness without production statistics.

This models a fixed-rank threshold on three represented score values. It
checks the distinction between requested-budget control and a returned bound,
not detector performance or the full Warrant implementation (P001).
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path
import platform
import subprocess
from typing import Any


def binomial_cdf(k: int, n: int, p: Fraction) -> Fraction:
    """Evaluate a binomial tail exactly to avoid reusing a CP quantile oracle."""
    return sum(
        (comb(n, j) * p**j * (1 - p)**(n - j) for j in range(k + 1)),
        start=Fraction(0),
    )


def probability_record(value: Fraction) -> dict[str, str | float]:
    """Retain exact values as well as readable approximations."""
    return {"fraction": str(value), "approximation": float(value)}


def analyze(config: dict[str, Any]) -> dict[str, Any]:
    """Enumerate all count states of the explicitly scoped three-atom model.

    For n negatives and design K=1, the pivot is rank n-1. CP upper U(k,n)
    solves CDF(k;n,U)=alpha, so risk>U iff CDF(k;n,risk)<alpha. Thus exact
    CDF comparisons suffice; no floating-point inversion or random draw is used.
    """
    n, design_k = config["n"], config["design_k"]
    if type(n) is not int or n < 2 or type(design_k) is not int or design_k != 1:
        raise ValueError("this reproduction requires integer n>=2 and design_k=1")
    budget, alpha, q1, q2 = (
        Fraction(config[name]) for name in ("budget", "alpha", "q1", "q2")
    )
    if not 0 < alpha < 1 or not 0 < q2 < q1 <= budget < 1:
        raise ValueError("require 0<alpha<1 and 0<q2<q1<=budget<1")
    if not binomial_cdf(1, n, budget) <= alpha < binomial_cdf(2, n, budget):
        raise ValueError("the configured budget does not imply design K=1")
    if not binomial_cdf(1, n, q1) < alpha:
        raise ValueError("the known witness requires q1>U(1,n)")
    if not binomial_cdf(0, n, q2) < alpha <= binomial_cdf(1, n, q2):
        raise ValueError("the known witness requires U(0,n)<q2<=U(1,n)")

    masses = (1 - q1, q1 - q2, q2)
    risks = (q1, q2, Fraction(0))
    noncovered = {
        (pivot, k): binomial_cdf(k, n, risk) < alpha
        for pivot, risk in enumerate(risks) for k in (0, 1)
    }
    total = old_failure = design_failure = budget_failure = Fraction(0)
    states = 0
    for a0 in range(n + 1):
        for a1 in range(n - a0 + 1):
            a2 = n - a0 - a1
            weight = comb(n, a0) * comb(n - a0, a1)
            weight *= masses[0]**a0 * masses[1]**a1 * masses[2]**a2
            if a0 >= n - 1:
                pivot, realized_k = 0, a1 + a2
            elif a0 + a1 >= n - 1:
                pivot, realized_k = 1, a2
            else:
                pivot, realized_k = 2, 0
            assert 0 <= realized_k <= design_k
            total += weight
            old_failure += weight * noncovered[pivot, realized_k]
            design_failure += weight * noncovered[pivot, design_k]
            budget_failure += weight * (risks[pivot] > budget)
            states += 1

    closed_form = n * q2 * (1 - q1)**(n - 1) + (1 - q2)**n
    assert total == 1 and old_failure == closed_form
    assert old_failure > alpha and design_failure <= alpha and budget_failure == 0
    return {
        "count_states": states,
        "probability_mass": probability_record(total),
        "returned_realized_count_bound_noncoverage": probability_record(old_failure),
        "closed_form_noncoverage": probability_record(closed_form),
        "fixed_design_count_bound_noncoverage": probability_record(design_failure),
        "requested_budget_violation": probability_record(budget_failure),
        "interpretation": "known synthetic witness; no literature or production proof",
    }


def build_artifact(config_path: Path) -> dict[str, Any]:
    """Bind this exact diagnostic to a clean source revision and config bytes."""
    root = Path(__file__).resolve().parents[2]
    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-c", "core.longpaths=true", *args], cwd=root, text=True,
        ).strip()

    dirty = bool(git("status", "--porcelain"))
    if dirty:
        raise RuntimeError("scientific diagnostic requires a clean worktree")
    raw = config_path.read_bytes()
    config = json.loads(raw)
    return {
        "provenance": {
            "source_commit": git("rev-parse", "HEAD"), "dirty": dirty,
            "config_sha256": hashlib.sha256(raw).hexdigest(),
            "python": platform.python_version(), "dependencies": "Python standard library",
            "seed": None, "reason": "exact rational enumeration; no random draws",
        },
        "config": config, "result": analyze(config),
    }


def main() -> None:
    """Expose an independently rerunnable research artifact entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = build_artifact(args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(artifact, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({name: value.get("approximation", value) if isinstance(value, dict)
                      else value for name, value in artifact["result"].items()}))


if __name__ == "__main__":
    main()
