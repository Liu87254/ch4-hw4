import json
import os
from dataclasses import dataclass

from google import genai
from google.genai import types

from rules.recycling_rules import ALLOWED_CATEGORIES

_PROMPT_TEMPLATE = (
    "You are a waste-sorting assistant for Taiwan's EPA recycling rules. "
    "Classify the material/recycling symbol in this photo as exactly one of "
    "these category codes: " + ", ".join(ALLOWED_CATEGORIES) + ". "
    'Reply with ONLY a JSON object: {"category": "<code>", "confidence": "high"|"medium"|"low"}.'
)


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


def _call_gemini(image_bytes: bytes):
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[
            _PROMPT_TEMPLATE,
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        ],
    )


def classify_image(image_bytes: bytes) -> ClassificationResult:
    try:
        response = _call_gemini(image_bytes)
    except Exception as e:
        raise ClassifierError(str(e))
    return parse_classification_response(response.text)
