"""Versioned finite-language procedure clauses; no eligibility or outcome labels.

Only literal source spans composed of fixed procedural syntax and a bounded
dataset-name catalogue can be released. Dataset mentions do not prove language,
binary task, timing, or eligibility. Other prose remains quarantined.
"""
from __future__ import annotations

import re

import a04_evidence as e

RULESET = "STRUCTURAL_FINITE_PROCEDURE_CLAUSE_V2"
DATASETS = (
    "TensorTrust", "BIPIA", "AgentDojo", "AgentHarm", "InjecAgent", "NotInject",
    "PromptInject", "LLMail-Inject", "LLMail", "Gandalf",
    "SQuAD", "SQuAD2", "SQuAD 2.0", "HotpotQA", "MS MARCO", "MSMARCO",
    "Alpaca", "AlpacaEval", "OpenAssistant", "JailbreakBench", "HarmBench",
    "WildGuardMix", "TruthfulQA", "Truthful-QA", "AdvBench", "PI-Bench", "PIBench",
    "JailbreakDB", "XSTest", "CoIN", "Do-Not-Answer", "MMLU", "GSM8K",
)
# Dataset identifiers can contain digits, unlike class/sample counts. This is a
# closed catalogue, not a free numerical slot or digit masking operation.
_DATASET = "(?:" + "|".join(re.escape(d) for d in sorted(DATASETS, key=len, reverse=True)) + ")"
_ACTOR = r"(?:we|the authors)"
_USE = r"(?:use|used|utilize|utilise|adopt|employ|evaluate on|evaluate using|conduct experiments on)"
_ENGLISH = r"(?:English|English-language) (?:text|texts|prompts|documents|inputs|data|examples)"
PATTERNS = {
    "DATASET_PROCEDURE_CLAUSE": re.compile(
        rf"\b{_ACTOR} {_USE} (?:the )?{_DATASET}(?: (?:dataset|benchmark|corpus))?(?![\w-])", re.I),
    "ENGLISH_PROCEDURE_CLAUSE": re.compile(
        rf"\b{_ACTOR} (?:use|retain|select|collect|evaluate on|evaluate using) (?:only )?{_ENGLISH}(?![\w-])", re.I),
    "BINARY_FORMULATION_CLAUSE": re.compile(
        rf"\b{_ACTOR} (?:formulate|treat|model) (?:the|this|our) (?:task|problem) as (?:a )?binary classification(?: task| problem)?(?![\w-])", re.I),
    "PRE_TARGET_PROCEDURE_CLAUSE": re.compile(
        r"\b(?:detection|classification) (?:is performed|is applied|runs) before "
        r"(?:the (?:target|downstream)(?: language)? model (?:responds|answers)|generation)(?![\w-])", re.I),
}
# The released span itself is always checked against the complete finite grammar.
# Context vetoes are an additional safeguard, not the proof of result-freedom.
CONTEXT_OUTCOME = re.compile(e.OUTCOME.pattern.removesuffix(r"|[%=<>\d]"), re.I)


def full_rule(quote: str) -> str | None:
    """Recognize only exact finite-language procedure clauses."""
    return next((name for name, pattern in PATTERNS.items() if pattern.fullmatch(quote)), None)


def extract(raw: bytes) -> list[dict]:
    """Keep exact method-only source spans, preserving attribution and limitations."""
    items = []
    for region in e.html_regions(raw):
        text = region["text"]
        if CONTEXT_OUTCOME.search(text):
            continue
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                # Reject comparisons, negation and quotations immediately before
                # a procedural span; these need a semantic checker instead.
                prefix = text[max(0, match.start() - 100):match.start()]
                if re.search(r"\b(?:unlike|rather than|instead of|not|never|without|if|could|would|suppose|hypothetically|example)\b|[\"“”]", prefix, re.I):
                    continue
                quote = match.group()
                if full_rule(quote) != name:
                    continue
                items.append({
                    "quote": quote, "grammar_rule": name, "ruleset": RULESET,
                    **{k: region[k] for k in ("locator", "section_id", "section_role", "paragraph_ordinal")},
                    "span_start": match.start(), "span_end": match.end(),
                    "paragraph_sha256": e.sha(text.encode()),
                    "limitation": "LITERAL_PROCEDURE_CLAUSE_ONLY_CONTEXT_AND_REMAINING_ELIGIBILITY_FACTS_UNRESOLVED",
                })
    unique = {}
    for item in items:
        unique.setdefault((item["quote"].casefold(), item["grammar_rule"]), item)
    return list(unique.values())


def verify(raw: bytes, item: dict) -> None:
    """Reopen source regions and prove quote/span/grammar/ancestry consistency."""
    regions = [r for r in e.html_regions(raw) if r["paragraph_ordinal"] == item["paragraph_ordinal"]]
    if len(regions) != 1:
        raise ValueError("PROCEDURE_SOURCE_REGION_MISSING")
    region = regions[0]
    if any(region[k] != item[k] for k in ("locator", "section_id", "section_role")):
        raise ValueError("PROCEDURE_SECTION_MISMATCH")
    text = region["text"]
    if (e.sha(text.encode()) != item["paragraph_sha256"] or CONTEXT_OUTCOME.search(text)
            or text[item["span_start"]:item["span_end"]] != item["quote"]
            or full_rule(item["quote"]) != item["grammar_rule"]):
        raise ValueError("PROCEDURE_RESTRICTION_FAILED")
    # Exact rederivation also checks negation/comparison guards and word boundaries.
    if item not in extract(raw):
        raise ValueError("PROCEDURE_NOT_REDERIVABLE")
