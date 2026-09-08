"""Third-party detectors and public datasets, declared rather than hardcoded.

Every entry names its **version or revision, its licence and its source**, and
every detector states the configuration it runs at. Phase 3 D34 allows only
documented defaults; a deviation needs a `DECISIONS.md` entry written before the
run, and there are none, so nothing here is tuned.

**Nothing is redistributed.** Datasets are fetched at run time by revision. A
`ai4privacy/pii-masking-200k` row never enters this repository, and neither do
per-item scores derived from it.

**Adding your own** (D38): append an :class:`ExternalDetector`, an
:class:`ExternalDataset` and a :class:`Pairing` below. A pairing supplies
``items(dataset) -> (ids, labels)`` and a detector supplies
``score(texts) -> list[float]``; everything downstream — the budget grid, the
Clopper-Pearson certification, the intervals — is the same code the rest of the
project uses and needs no changes.
"""

from __future__ import annotations

import dataclasses
from typing import Callable, Optional, Sequence

__all__ = [
    "PAIRINGS",
    "ExternalDataset",
    "ExternalDetector",
    "Pairing",
    "pairing_ids",
]

#: When every source below was resolved and its revision recorded.
ACCESS_DATE = "2026-09-09"


@dataclasses.dataclass(frozen=True)
class ExternalDataset:
    """A public dataset, pinned to a revision and never redistributed."""

    id: str
    hf_id: str
    revision: str
    split: str
    licence: str
    source_url: str
    note: str = ""

    def to_payload(self) -> dict:
        return {
            "id": self.id,
            "huggingface_id": self.hf_id,
            "revision": self.revision,
            "split": self.split,
            "licence": self.licence,
            "source_url": self.source_url,
            "access_date": ACCESS_DATE,
            "note": self.note,
            "redistributed_here": False,
        }


@dataclasses.dataclass(frozen=True)
class ExternalDetector:
    """A detector this project did not build, run at its documented default."""

    id: str
    version: str
    licence: str
    source_url: str
    #: Exactly how it was configured, in words a vendor could check. D34.
    configuration: str
    #: Where that default is documented, so the claim is not from memory. D39.
    documentation_url: str

    def to_payload(self) -> dict:
        return {
            "id": self.id,
            "version": self.version,
            "licence": self.licence,
            "source_url": self.source_url,
            "configuration": self.configuration,
            "documentation_url": self.documentation_url,
            "tuned_for_this_evaluation": False,
        }


@dataclasses.dataclass(frozen=True)
class Pairing:
    """One detector on one dataset, answering one question."""

    id: str
    detector: ExternalDetector
    dataset: ExternalDataset
    #: What a positive label means, in the words of the dataset's own schema.
    task: str
    #: Rows -> (ids, labels, texts). Labels come from the dataset's annotations
    #: and never from the detector.
    items: Callable[[Sequence[dict]], tuple[list[str], list[int], list[str]]]
    #: Texts -> one score per text, higher meaning more likely positive.
    score: Callable[[Sequence[str]], list[float]]
    #: Rows to take from the split. Enough for the tightest budget on the grid
    #: with room to spare; the cost is CPU seconds.
    limit: int = 2000
    #: A frozen score set under ``results/scores/`` to read instead of fetching
    #: and scoring. Used for this project's own detector, whose scores are
    #: already committed -- rescoring them would answer a question about the
    #: extraction rather than putting our detector in the matrix (D37).
    frozen_score_set: Optional[str] = None

    def to_payload(self) -> dict:
        return {
            "id": self.id,
            "task": self.task,
            "limit": self.limit,
            "detector": self.detector.to_payload(),
            "dataset": self.dataset.to_payload(),
        }


# --------------------------------------------------------------- detectors

PRESIDIO = ExternalDetector(
    id="presidio-analyzer",
    version="2.2.364",
    licence="MIT",
    source_url="https://github.com/microsoft/presidio",
    configuration=(
        "AnalyzerEngine() with no arguments -- the stock recognizer registry and "
        "the default spaCy en_core_web_lg NLP engine. analyze(text, language='en', "
        "entities=[<one entity>]). No threshold is passed, so the engine's own "
        "default applies; the item score is the maximum confidence Presidio "
        "returns for that entity, or 0.0 when it returns nothing."
    ),
    documentation_url="https://microsoft.github.io/presidio/analyzer/",
)

PROMPT_INJECTION = ExternalDetector(
    id="protectai/deberta-v3-base-prompt-injection-v2",
    version="90c9989b1a342275dd0d1a95aad283c04e075671",
    licence="apache-2.0",
    source_url="https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2",
    configuration=(
        "AutoModelForSequenceClassification at the pinned revision, eval mode, "
        "truncation at the model's own max_length. The item score is "
        "softmax(logits)[INJECTION], with the INJECTION index read from the "
        "loaded config's id2label rather than assumed."
    ),
    documentation_url="https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2",
)

OUR_PROBE = ExternalDetector(
    id="probe-qwen2.5-7b-instruct-T1-last_token",
    version="results/scores/validation-T1-last_token.json",
    licence="MIT (this project)",
    source_url="https://github.com/Aditya26189/Warrant",
    configuration=(
        "The frozen test-split scores from Phase 0/1. Same grid, same criterion, "
        "same presentation as every other row -- D37."
    ),
    documentation_url="https://github.com/Aditya26189/Warrant/blob/main/docs/METHODS.md",
)


# ---------------------------------------------------------------- datasets

PII_200K = ExternalDataset(
    id="ai4privacy/pii-masking-200k",
    hf_id="ai4privacy/pii-masking-200k",
    revision="7c22e6816b8fc24b7781e9f4e22016c698842dd0",
    split="train",
    licence="not declared in card metadata",
    source_url="https://huggingface.co/datasets/ai4privacy/pii-masking-200k",
    note=(
        "Every row contains PII, so a 'contains any PII' task on it is "
        "single-class and unbounded. Tasks are defined per entity type from the "
        "dataset's own span labels. DECISIONS 139."
    ),
)

PROMPT_INJECTIONS = ExternalDataset(
    id="deepset/prompt-injections",
    hf_id="deepset/prompt-injections",
    revision="4f61ecb038e9c3fb77e21034b22511b523772cdd",
    split="train",
    licence="apache-2.0",
    source_url="https://huggingface.co/datasets/deepset/prompt-injections",
)

TRIVIAQA_600 = ExternalDataset(
    id="triviaqa-600 (this project)",
    hf_id="",
    revision="sha256:e77c64f908491ad1",
    split="test",
    licence="see repository",
    source_url="https://github.com/Aditya26189/Warrant",
    note="Ours, included so our own detector appears on identical terms (D37).",
)


# ---------------------------------------------------------------- pairings

def _pii_items(entity: str) -> Callable:
    """Positive when the row carries a span of ``entity``, negative when not.

    The labels are the dataset's, not ours. A negative row still contains other
    PII, which is the correct reading: the question being certified is "does
    this text contain a <entity>", not "is this text clean".
    """
    def items(rows: Sequence[dict]) -> tuple[list[str], list[int], list[str]]:
        ids, labels, texts = [], [], []
        for index, row in enumerate(rows):
            spans = row.get("privacy_mask") or []
            ids.append(str(row.get("id", index)))
            labels.append(int(any(s.get("label") == entity for s in spans)))
            texts.append(row["source_text"])
        return ids, labels, texts

    return items


def _binary_label_items(text_key: str, label_key: str, positive: str) -> Callable:
    def items(rows: Sequence[dict]) -> tuple[list[str], list[int], list[str]]:
        ids, labels, texts = [], [], []
        for index, row in enumerate(rows):
            ids.append(f"{index}")
            labels.append(int(str(row[label_key]) == positive))
            texts.append(row[text_key])
        return ids, labels, texts

    return items


def _presidio_scorer(entity: str) -> Callable[[Sequence[str]], list[float]]:
    """Max confidence Presidio reports for ``entity``, or 0.0 for silence."""
    def score(texts: Sequence[str]) -> list[float]:
        from presidio_analyzer import AnalyzerEngine

        engine = AnalyzerEngine()
        out: list[float] = []
        for text in texts:
            found = engine.analyze(text=text, language="en", entities=[entity])
            out.append(max((f.score for f in found), default=0.0))
        return out

    return score


def _injection_scorer(revision: str) -> Callable[[Sequence[str]], list[float]]:
    def score(texts: Sequence[str]) -> list[float]:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        name = "protectai/deberta-v3-base-prompt-injection-v2"
        tokenizer = AutoTokenizer.from_pretrained(name, revision=revision)
        model = AutoModelForSequenceClassification.from_pretrained(name, revision=revision)
        model.eval()
        # Read the positive index from the model rather than assuming it is 1.
        index = {v.upper(): k for k, v in model.config.id2label.items()}["INJECTION"]

        out: list[float] = []
        with torch.no_grad():
            for start in range(0, len(texts), 16):
                batch = list(texts[start:start + 16])
                encoded = tokenizer(
                    batch, return_tensors="pt", truncation=True, padding=True,
                    max_length=512,
                )
                probabilities = model(**encoded).logits.softmax(-1)
                out.extend(float(p[index]) for p in probabilities)
        return out

    return score


#: Presidio entity to the ai4privacy label that means the same thing. Both
#: names are the vendors' own; nothing here renames anything.
_PII_TASKS = {
    "EMAIL_ADDRESS": "EMAIL",
    "CREDIT_CARD": "CREDITCARDNUMBER",
    "IP_ADDRESS": "IPV4",
    "PHONE_NUMBER": "PHONENUMBER",
    "URL": "URL",
}

PAIRINGS: dict[str, Pairing] = {
    f"presidio-{entity.lower()}": Pairing(
        id=f"presidio-{entity.lower()}",
        detector=PRESIDIO,
        dataset=PII_200K,
        task=(
            f"does the text contain {'an' if entity[0] in 'AEIOU' else 'a'} "
            f"{entity}? Positive when the row carries an ai4privacy "
            f"'{ds_label}' span."
        ),
        items=_pii_items(ds_label),
        score=_presidio_scorer(entity),
    )
    for entity, ds_label in _PII_TASKS.items()
}

PAIRINGS["injection-deepset"] = Pairing(
    id="injection-deepset",
    detector=PROMPT_INJECTION,
    dataset=PROMPT_INJECTIONS,
    task="is the prompt an injection attempt? Positive when the dataset labels it 1.",
    items=_binary_label_items("text", "label", "1"),
    limit=600,
    score=_injection_scorer(PROMPT_INJECTION.version),
)


PAIRINGS["ours-triviaqa"] = Pairing(
    id="ours-triviaqa",
    detector=OUR_PROBE,
    dataset=TRIVIAQA_600,
    task=(
        "is the model's answer incorrect? Positive when the frozen label says "
        "the response was wrong."
    ),
    items=lambda rows: ([], [], []),  # unused: the scores are already frozen
    score=lambda texts: [],
    frozen_score_set="validation-T1-last_token",
)


def pairing_ids() -> list[str]:
    return sorted(PAIRINGS)
