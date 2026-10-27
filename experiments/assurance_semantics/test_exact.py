"""Independent checks of the analytic reproduction, not production behavior."""

from fractions import Fraction
import json
from pathlib import Path

import pytest

from experiments.assurance_semantics.exact import analyze, binomial_cdf


def test_small_binomial_tail_matches_literal_outcomes() -> None:
    """Two independent fair trials have three of four outcomes at count<=1."""
    assert binomial_cdf(1, 2, Fraction(1, 2)) == Fraction(3, 4)
    assert binomial_cdf(0, 2, Fraction(1, 2)) == Fraction(1, 4)


def test_known_witness_matches_original_decimal_expression() -> None:
    """Exhaustive multinomial counts must match the separately derived formula."""
    config = json.loads(Path(__file__).with_name("config.json").read_bytes())
    result = analyze(config)
    assert result["count_states"] == 5151
    assert result["probability_mass"]["fraction"] == "1"
    assert result["returned_realized_count_bound_noncoverage"]["approximation"] == (
        pytest.approx(0.07630211515886068, abs=1e-15, rel=0)
    )
    assert result["requested_budget_violation"]["fraction"] == "0"


def test_rejects_an_unjustified_rank_assumption() -> None:
    """The K=1 formula must not be generalized to another budget silently."""
    config = json.loads(Path(__file__).with_name("config.json").read_bytes())
    config["budget"] = "0.5"
    with pytest.raises(ValueError, match="does not imply design"):
        analyze(config)
