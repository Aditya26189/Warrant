"""Freeze the evidence that every registered causal claim is checked against.

The claim table proves a number is right. This proves the *explanation beside it*
is right, which is the half that had no machinery and produced three published
wrong mechanisms in one session (``DECISIONS.md`` 142).

Measuring needs the corpora, so it runs here and writes
``results/causal_claims.json``. The falsifiers then run offline in
``tests/test_causal_claims.py`` on every test run — the point being that a
mechanism is checked continuously rather than when somebody thinks to look.

Thin wrapper: parses arguments, calls ``controlplane/``, writes files. No logic
(``CLAUDE.md``) — beyond the measurements themselves, which are what the script
is for.

Usage:
    python scripts/24_causal_claims.py --config config.yaml
"""

from __future__ import annotations

import argparse
import collections
import logging
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.config import load_config, setup_logging, write_json_artifact
from controlplane.external.redact import ENGLISH, load_redact_records
from controlplane.report.causal import CLAIMS, check_claim
from controlplane.validation.warrant_stats import min_n_for

_LOG = logging.getLogger("scripts.24_causal_claims")

REDACT_CACHE = Path.home() / ".cache" / "warrant" / "benchmarks"


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def luhn(text: str) -> bool:
    """Whether a candidate card number satisfies the Luhn checksum."""
    ds = [int(c) for c in _digits(text)]
    total = 0
    for index, value in enumerate(reversed(ds)):
        if index % 2:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return bool(ds) and total % 10 == 0


def has_card_prefix(text: str) -> bool:
    """Whether the digits open with a real card-network prefix.

    Visa 4, Mastercard 51-55 and 2221-2720, Amex 34/37, Discover 6011/65. A
    16-digit string outside these is not a card number under any numbering plan,
    which is why Presidio's pattern declines it before any checksum runs.
    """
    ds = _digits(text)
    if len(ds) < 12:
        return False
    if ds[0] == "4" or ds[:2] in {"51", "52", "53", "54", "55", "34", "37", "65"}:
        return True
    if ds[:4] == "6011":
        return True
    return 2221 <= int(ds[:4]) <= 2720


def measure_ai4privacy(limit: int) -> dict:
    from datasets import load_dataset

    data = load_dataset("ai4privacy/pii-masking-200k", split=f"train[:{limit}]")
    data = data.filter(lambda r: r["language"] == "en")
    spans = [
        s["value"]
        for row in data["privacy_mask"]
        for s in row
        if s["label"] == "CREDITCARDNUMBER"
    ]
    known = [s for s in spans if has_card_prefix(s)]
    return {
        "corpus": "ai4privacy/pii-masking-200k",
        "slice": f"train[:{limit}], english",
        "n_spans": len(spans),
        "fragments_under_12_digits": sum(1 for s in spans if len(_digits(s)) < 12),
        "no_known_prefix": len(spans) - len(known),
        "known_prefix": len(known),
        "known_prefix_luhn_pass": sum(1 for s in known if luhn(s)),
        "known_prefix_luhn_fail": sum(1 for s in known if not luhn(s)),
    }


def measure_redact() -> tuple[dict, dict]:
    records = load_redact_records(REDACT_CACHE, english_only=False)
    spans = [
        e for r in records for e in r["entities"]
        if e["entity_type"] == "Credit_Card_Numbers"
    ]
    complete_full = [
        e["entity_string"] for e in spans
        if e.get("disclosure_form") == "complete"
        and len(_digits(e["entity_string"])) >= 12
    ]
    cards = {
        "corpus": "REDACT locked split",
        "n_spans": len(spans),
        "partial": sum(1 for e in spans if e.get("disclosure_form") == "partial"),
        "complete": sum(1 for e in spans if e.get("disclosure_form") == "complete"),
        "fragments_under_12_digits": sum(
            1 for e in spans if len(_digits(e["entity_string"])) < 12
        ),
        "complete_full_length": len(complete_full),
        "complete_full_length_luhn_pass": sum(1 for c in complete_full if luhn(c)),
        "complete_full_length_luhn_fail": sum(1 for c in complete_full if not luhn(c)),
    }

    languages = collections.Counter(r["axes"]["language"] for r in records)
    capacity = {
        "corpus": "REDACT locked split",
        "n_records": len(records),
        "n_languages": len(languages),
        "records_per_language": min(languages.values()),
        "english_records": languages.get(ENGLISH, 0),
        "negatives_needed_at_001": min_n_for(0.01, 0.05),
        "negatives_needed_at_005": min_n_for(0.05, 0.05),
        "negatives_needed_at_010": min_n_for(0.10, 0.05),
        "negatives_needed_at_020": min_n_for(0.20, 0.05),
    }
    return cards, capacity


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"))
    parser.add_argument("--limit", type=int, default=2000, help="ai4privacy rows")
    parser.add_argument("--out", default=None, help="results directory override")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)
    results = Path(args.out) if args.out else PROJECT_ROOT / config.paths.results_dir

    redact_cards, redact_capacity = measure_redact()
    evidence = {
        "ai4privacy_credit_card": measure_ai4privacy(args.limit),
        "redact_credit_card": redact_cards,
        "redact_capacity": redact_capacity,
    }
    payload = {
        "purpose": (
            "Evidence each registered causal claim is checked against. A "
            "mechanism stated in a document is a claim in its own right and "
            "needs its own falsifier; see controlplane/report/causal.py and "
            "DECISIONS.md 142."
        ),
        "evidence": evidence,
        "claims": [c.to_payload() for c in CLAIMS],
    }
    write_json_artifact(results / "causal_claims.json", payload, config)

    for claim in CLAIMS:
        holds, detail = check_claim(claim, payload)
        state = "HOLDS" if holds else ("WITHDRAWN" if claim.withdrawn else "FALSIFIED")
        _LOG.info("%-38s %s %s", claim.id, state, detail[:70])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
