"""Causal claims: a mechanism is a claim, and a claim needs a falsifier.

This repository can prove a number is right. It had nothing that could tell
whether the *story about the number* was right, and that asymmetry produced three
confident wrong explanations in one session — none caught by 1,033 tests or by
``make verify``, all caught by a reader (``DECISIONS.md`` 142).

The claim table already solves the equivalent problem for numbers: every figure
in a document names an artifact and a field, and `make verify` recomputes it. This
is the same mechanism for the other half of a sentence.

**A registered claim carries three things**: the mechanism a document asserts, the
measured evidence that bears on it, and a **predicate that would be false if the
mechanism were wrong**. The predicate runs offline against frozen evidence, so it
is checked on every test run rather than when somebody thinks to look.

**The rule this enforces**: a document may not state a mechanism that has no
registered falsifier. It is the sibling of the rule that no rate appears without
an interval — *no mechanism without a test*.

The register deliberately includes **withdrawn** claims. A falsifier that now
fails is the record of what was believed and disproved, and deleting it would
leave the document tidy and the history unrecoverable.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Callable, Optional

__all__ = ["CLAIMS", "CausalClaim", "check_claim", "load_evidence"]

EVIDENCE_PATH = Path("results") / "causal_claims.json"


@dataclasses.dataclass(frozen=True)
class CausalClaim:
    """One mechanism, where it is asserted, and what would falsify it."""

    id: str
    #: The document and passage this backs, so a reader can find the sentence.
    asserted_in: str
    #: The mechanism in one line, as a document would put it.
    mechanism: str
    #: Key into the frozen evidence block.
    evidence_key: str
    #: True when the evidence is consistent with the mechanism. False means the
    #: document is wrong, not that the test is.
    predicate: Callable[[dict[str, Any]], bool]
    #: What the reader should conclude if the predicate fails.
    falsified_means: str
    #: Set when the claim was asserted, tested and found false. Kept rather than
    #: deleted: the register is a record, not a tidy list.
    withdrawn: Optional[str] = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "asserted_in": self.asserted_in,
            "mechanism": self.mechanism,
            "evidence_key": self.evidence_key,
            "falsified_means": self.falsified_means,
            "withdrawn": self.withdrawn,
        }


def load_evidence(root: Path) -> dict[str, Any]:
    """Read the frozen evidence block.

    Raises:
        FileNotFoundError: With the command that regenerates it, since a missing
            evidence file means the claims are unchecked rather than passing.
    """
    path = Path(root) / EVIDENCE_PATH
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is absent, so no causal claim is being checked. "
            "Regenerate with: python scripts/24_causal_claims.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def check_claim(claim: CausalClaim, evidence: dict[str, Any]) -> tuple[bool, str]:
    """Run one claim's falsifier. Returns ``(holds, detail)``."""
    block = evidence.get("evidence", {}).get(claim.evidence_key)
    if block is None:
        return False, (
            f"no evidence recorded under {claim.evidence_key!r}; the mechanism "
            "is unchecked, which is the state this register exists to prevent"
        )
    holds = claim.predicate(block)
    return holds, ("" if holds else claim.falsified_means)


# --------------------------------------------------------------- the register

CLAIMS: tuple[CausalClaim, ...] = (
    CausalClaim(
        id="ai4privacy-credit-card-prefix",
        asserted_in="docs/EXTERNAL.md, 'What the numbers say'",
        mechanism=(
            "Presidio's low credit-card recall on ai4privacy is driven mainly by "
            "spans having no valid card-network prefix, so the recognizer's "
            "pattern never matches and the checksum is never reached."
        ),
        evidence_key="ai4privacy_credit_card",
        # If most spans DID carry a real network prefix, the prefix could not be
        # the dominant cause and the document would be wrong.
        predicate=lambda e: e["no_known_prefix"] / e["n_spans"] > 0.5,
        falsified_means=(
            "most spans carry a real card-network prefix, so the prefix is not "
            "the dominant cause and docs/EXTERNAL.md names the wrong mechanism"
        ),
    ),
    CausalClaim(
        id="ai4privacy-credit-card-not-fragments",
        asserted_in="docs/EXTERNAL.md, 'What the numbers say'",
        mechanism=(
            "The ai4privacy cause is NOT partial fragments: every span there is a "
            "full 16-digit string, unlike REDACT."
        ),
        evidence_key="ai4privacy_credit_card",
        predicate=lambda e: e["fragments_under_12_digits"] == 0,
        falsified_means=(
            "ai4privacy does contain card fragments, so it shares REDACT's cause "
            "after all and the 'two unrelated causes' claim is wrong"
        ),
    ),
    CausalClaim(
        id="redact-credit-card-partial-fragments",
        asserted_in="docs/REDACT.md §3",
        mechanism=(
            "Presidio's withdrawn 0.0935 on REDACT was caused by the task "
            "counting partial last-four fragments as positives, not by checksums."
        ),
        evidence_key="redact_credit_card",
        predicate=lambda e: e["partial"] / e["n_spans"] > 0.5,
        falsified_means=(
            "most REDACT card spans are complete, so partial fragments cannot "
            "explain the withdrawn figure and docs/REDACT.md §3 is wrong"
        ),
    ),
    CausalClaim(
        id="redact-luhn-deviation",
        asserted_in="docs/REDACT.md §6, reported to the authors",
        mechanism=(
            "Some complete, full-length REDACT card numbers fail Luhn, a "
            "deviation from the stated generation contract."
        ),
        evidence_key="redact_credit_card",
        predicate=lambda e: e["complete_full_length_luhn_fail"] > 0,
        falsified_means=(
            "every complete full-length card number passes Luhn, so the "
            "observation sent to the REDACT authors is wrong and must be retracted"
        ),
    ),
    CausalClaim(
        id="redact-capacity-per-language",
        asserted_in="docs/REDACT.md §1, the headline finding",
        mechanism=(
            "REDACT's locked split cannot underwrite a per-language "
            "false-positive bound tighter than 10-20%, because 40 records per "
            "language cannot supply the 59 clean negatives a 5% budget needs."
        ),
        evidence_key="redact_capacity",
        predicate=lambda e: e["records_per_language"] < e["negatives_needed_at_005"],
        falsified_means=(
            "a single language carries enough records to underwrite a 5% budget, "
            "so the headline finding in docs/REDACT.md §1 is wrong"
        ),
    ),
    CausalClaim(
        id="presidio-checksum-explanation",
        asserted_in="docs/EXTERNAL.md, until 2026-09-09 — WITHDRAWN",
        mechanism=(
            "Presidio's low credit-card recall is caused by checksum validation "
            "rejecting synthetically generated numbers."
        ),
        evidence_key="ai4privacy_credit_card",
        # Retained as a live falsifier. It fails, and it is supposed to: this is
        # the claim that was published and disproved, and a register that drops
        # its failures is a register that cannot show what was learned.
        predicate=lambda e: e["known_prefix_luhn_fail"] / max(e["n_spans"], 1) > 0.5,
        falsified_means=(
            "checksum rejection cannot account for the majority of spans; the "
            "mechanism was withdrawn on 2026-09-09, DECISIONS 142"
        ),
        withdrawn=(
            "2026-09-09. Measured: 108 of 129 spans have no valid card-network "
            "prefix, so the pattern never matches and Luhn is never reached. "
            "Superseded by ai4privacy-credit-card-prefix."
        ),
    ),
)
