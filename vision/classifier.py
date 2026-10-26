import json
from dataclasses import dataclass

from rules.recycling_rules import ALLOWED_CATEGORIES


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    confidence: str
    is_uncertain: bool


class ClassifierError(Exception):
    pass


def parse_classification_response(raw_text: str) -> ClassificationResult:
    try:
        parsed = json.loads(raw_text)
        category = parsed["category"]
        confidence = parsed["confidence"]
    except (json.JSONDecodeError, TypeError, KeyError):
        return ClassificationResult(category="unknown", confidence="low", is_uncertain=True)

    if category not in ALLOWED_CATEGORIES or confidence == "low":
        return ClassificationResult(category="unknown", confidence="low", is_uncertain=True)

    return ClassificationResult(category=category, confidence=confidence, is_uncertain=False)
