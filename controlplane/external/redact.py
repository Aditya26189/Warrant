"""REDACT: certifying on somebody else's benchmark, at their own locked split.

REDACT (ServiceNow, `arXiv 2606.19881 <https://arxiv.org/abs/2606.19881>`_,
18 June 2026) reports **span-level F1** over 51 entity types in 25 languages.
This module asks a different question of the same 1,000 records their five
reported detectors were measured on:

    does this record contain a ``<type>``, at a threshold whose false-positive
    rate is certified below *b* with 95% confidence — or can that not be
    certified on this evidence at all?

Neither question subsumes the other. F1 says how good a detector is. A certified
budget says what you are allowed to promise about it, which is the thing a
compliance function signs. ``DECISIONS.md`` 140.

**What the split can carry.** Certifying at a 1% budget needs 299 clean
negatives; 20% needs 14. Within any one language REDACT holds 40 records, so no
single-language task here supports a budget tighter than 10–20% — a fact about
what forty records can underwrite, not a defect in a benchmark built to estimate
F1 across languages. Pooled across all 25 it clears 1% comfortably.

**Nothing is redistributed.** The corpus is cloned from the public repository at
run time. REDACT's code is MIT; its dataset terms support research, evaluation
and auditing.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Callable, Optional, Sequence

__all__ = [
    "LANGUAGE_INDEPENDENT",
    "PRESIDIO_MAPPING",
    "REDACT_REPO",
    "ensure_redact",
    "load_redact_records",
    "COMPLETE",
    "redact_items",
]

_LOG = logging.getLogger(__name__)

REDACT_REPO = "https://github.com/guneeshvats/REDACT-PII-Benchmark.git"
REDACT_REVISION = "main"
SAMPLE_PATH = Path("data") / "pii_benchmark_sample1000.json"

#: REDACT canonical type -> the Presidio entities that claim to detect it.
#:
#: Conservative and explicit, because a loose mapping is the easiest way to
#: publish an unfair number about somebody else's software. Two entries decide a
#: result and are called out before any run (``DECISIONS.md`` 140):
#:
#: * ``National_Identification_Number`` and ``Passport_Number`` map to Presidio's
#:   **US-only** recognizers, while REDACT's catalog spans 40+ national systems
#:   including Indian Aadhaar. Low recall there is a scope mismatch, not a
#:   defect, and the artifact says so.
#: * ``Date_of_Birth`` is deliberately **absent**. Presidio's ``DATE_TIME`` fires
#:   on any date, so scoring it against a date-of-birth label would count every
#:   delivery date as a true positive of a different question.
PRESIDIO_MAPPING: dict[str, tuple[str, ...]] = {
    "Personal_Email_Address": ("EMAIL_ADDRESS",),
    "Work_Email_Address": ("EMAIL_ADDRESS",),
    "Credit_Card_Numbers": ("CREDIT_CARD",),
    "Static_IP_Address": ("IP_ADDRESS",),
    "Telephone_Numbers_Personal": ("PHONE_NUMBER",),
    "Telephone_Numbers_Work": ("PHONE_NUMBER",),
    "Full_Name": ("PERSON",),
    "National_Identification_Number": ("US_SSN", "US_ITIN"),
    "Passport_Number": ("US_PASSPORT",),
}

#: Types whose Presidio recognizer is pure regex or checksum, so running the
#: English pipeline over other languages measures the detector rather than a
#: language mismatch. Only these may be pooled across REDACT's 25 languages.
#:
#: ``US_SSN``, ``US_ITIN`` and ``US_PASSPORT`` are pattern recognizers and belong
#: here despite naming a country: what makes them poolable is that they do not
#: consult the NLP engine, not that they are country-neutral. They are emphatically
#: not country-neutral, and that is the finding rather than a caveat to it.
#:
#: ``PERSON`` is excluded — it is spaCy NER and would measure the language
#: mismatch. ``PHONE_NUMBER`` is excluded too: Presidio's phone recognizer takes
#: region hints, so its behaviour across 25 locales is a confound this analysis
#: does not need to argue about.
LANGUAGE_INDEPENDENT = frozenset(
    {
        "Personal_Email_Address",
        "Work_Email_Address",
        "Credit_Card_Numbers",
        "Static_IP_Address",
        "National_Identification_Number",
        "Passport_Number",
    }
)

ENGLISH = "EN"


def ensure_redact(cache_dir: Path) -> Path:
    """Clone REDACT if absent and return the path to the locked split.

    Args:
        cache_dir: Directory to clone into. Kept outside the repository: REDACT
            is fetched, never vendored.

    Returns:
        Path to ``pii_benchmark_sample1000.json``.

    Raises:
        RuntimeError: If the clone fails or the split is missing afterwards.
    """
    cache_dir = Path(cache_dir)
    checkout = cache_dir / "REDACT-PII-Benchmark"
    sample = checkout / SAMPLE_PATH
    if sample.is_file():
        return sample

    cache_dir.mkdir(parents=True, exist_ok=True)
    _LOG.info("cloning %s into %s", REDACT_REPO, checkout)
    result = subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", REDACT_REVISION,
         "--quiet", REDACT_REPO, str(checkout)],
        capture_output=True, text=True, timeout=1800,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"could not clone REDACT from {REDACT_REPO}: {result.stderr.strip()}"
        )
    if not sample.is_file():
        raise RuntimeError(
            f"cloned REDACT but {SAMPLE_PATH} is absent. The large files are "
            "stored with Git LFS; install git-lfs, or download the corpus from "
            "https://huggingface.co/datasets/guneeshv/REDACT-PII-Benchmark"
        )
    return sample


def load_redact_records(
    cache_dir: Path, *, english_only: bool
) -> list[dict]:
    """Load the locked evaluation split, optionally restricted to English.

    Args:
        cache_dir: Where REDACT is (or will be) cloned.
        english_only: Restrict to the 40 ``EN`` records. Required for any task
            whose Presidio recognizer depends on the NLP engine, since the
            engine is run at ``language='en'``.

    Returns:
        Record dictionaries as released.
    """
    sample = ensure_redact(cache_dir)
    records = json.loads(sample.read_text(encoding="utf-8"))
    if english_only:
        records = [r for r in records if r["axes"]["language"] == ENGLISH]
    _LOG.info(
        "REDACT locked split: %d records (%s)",
        len(records), "EN only" if english_only else "all 25 languages",
    )
    return records


def _unique_id(row: dict, index: int) -> str:
    """A unique item id, preserving REDACT's own record_id for traceability.

    **`record_id` is not unique in the released locked split**: 1,000 records
    carry 944 distinct ids, so 55 collide. The colliding records are different
    documents rather than duplicates — one inspected pair shares a generation
    configuration but has a text similarity of 0.027 — so they are independent
    items with a clashing label, not a cluster.

    That distinction decides how they may be certified. The sweep refuses a set
    with repeated ids, on the reasoning that repeats usually mean clustered
    items and certifying over them would overstate the effective sample size.
    Here the repeats are an identifier collision, so the position disambiguates
    and the original id is kept in view.
    """
    return f"{row.get('record_id', index)}#{index}"


#: The only disclosure form a full-surface detector can be asked about.
#: See :func:`redact_items` for why this is not a detail.
COMPLETE = "complete"


def redact_items(
    *canonical_types: str, complete_only: bool = True
) -> Callable:
    """Positive when the record carries a **complete** gold span of a given type.

    Three-way, and the third way is the point:

    * **positive** — the record carries a ``complete`` span of the type;
    * **negative** — the record carries no span of the type at all;
    * **excluded** — the record's only spans of the type are ``partial`` or
      ``obfuscated``.

    **Why the exclusion matters, learned the hard way.** REDACT annotates
    ``Credit_Card_Numbers`` at 82.6% ``partial``: 104 of 132 gold spans are
    four-digit last-four fragments like ``7821``. A first version of this task
    counted those as positives, measured Presidio at recall 0.0935, and
    explained the gap as checksum validation rejecting synthetic numbers. That
    explanation was wrong. Presidio's recognizer is built for full card numbers
    and **correctly** declines to call four digits a credit card; the low recall
    was this function's construction, not the detector's behaviour and not the
    benchmark's generator.

    Nor can such a record be scored as a negative: it does contain card
    information, so a detector that fired on it would be penalised for being
    right. The only defensible treatment is to drop it and say how many were
    dropped.

    Every other type measured here is under 11% partial, so the correction moves
    one row — but it would have been the row a reviewer opened first.

    Args:
        canonical_types: REDACT types to treat as one task. Several map to one
            Presidio entity (both email fields map to ``EMAIL_ADDRESS``), so the
            task spans them rather than being run twice against a detector that
            cannot tell them apart.
        complete_only: Keep the exclusion. Set ``False`` only to reproduce the
            uncorrected measurement.

    Returns:
        A callable returning ``(ids, labels, texts)`` over the retained records.
    """
    wanted = set(canonical_types)

    def items(rows: Sequence[dict]) -> tuple[list[str], list[int], list[str]]:
        ids, labels, texts = [], [], []
        dropped = 0
        for index, row in enumerate(rows):
            spans = [e for e in row.get("entities", ()) if e["entity_type"] in wanted]
            if not spans:
                label = 0
            elif not complete_only:
                label = 1
            else:
                complete = [s for s in spans if s.get("disclosure_form") == COMPLETE]
                if complete:
                    label = 1
                else:
                    dropped += 1
                    continue
            ids.append(_unique_id(row, index))
            labels.append(label)
            texts.append(row["text"])
        if dropped:
            _LOG.info(
                "excluded %d record(s) whose only %s spans are partial or "
                "obfuscated: a full-surface detector cannot be asked about them, "
                "and scoring them either way would be wrong",
                dropped, "/".join(sorted(wanted)),
            )
        return ids, labels, texts

    return items


def redact_high_tier_items(supported: Sequence[str]) -> Callable:
    """Positive when the record carries a **HIGH-sensitivity** gold entity that
    Presidio claims to detect.

    This is the question REDACT's stratified metadata makes askable and their
    headline answers in F1 terms: the rule-based detector reaches recall 0.07 on
    HIGH-sensitivity entities where the LLM detectors are strongest. Asked as a
    budget instead: *at a certified false-positive rate, can this detector be
    relied on where the stakes are highest?*

    Restricted to types Presidio claims, so the result is not a scope mismatch
    dressed up as a failure.
    """
    claimed = set(supported)

    def items(rows: Sequence[dict]) -> tuple[list[str], list[int], list[str]]:
        ids, labels, texts = [], [], []
        for index, row in enumerate(rows):
            high = any(
                e.get("sensitivity_tier") == "HIGH" and e["entity_type"] in claimed
                for e in row.get("entities", ())
            )
            ids.append(_unique_id(row, index))
            labels.append(int(high))
            texts.append(row["text"])
        return ids, labels, texts

    return items


def pooling_check(
    records: Sequence[dict], scores: Sequence[float], threshold: float
) -> dict[str, Optional[float]]:
    """Achieved FPR on English against non-English records, at one threshold.

    Pooling 25 languages under an English NLP engine is only defensible when the
    recognizer is language-independent, and that is an assumption worth testing
    rather than asserting. If these two diverge materially the pooling is
    unsound and the artifact should say so instead of averaging over it.
    """
    english_fp = english_n = other_fp = other_n = 0
    for record, score in zip(records, scores):
        flagged = score >= threshold
        if record["axes"]["language"] == ENGLISH:
            english_n += 1
            english_fp += int(flagged)
        else:
            other_n += 1
            other_fp += int(flagged)
    return {
        "english_flag_rate": english_fp / english_n if english_n else None,
        "non_english_flag_rate": other_fp / other_n if other_n else None,
        "n_english": english_n,
        "n_non_english": other_n,
    }
