from vision.classifier import parse_classification_response


def test_valid_high_confidence_response():
    result = parse_classification_response('{"category": "plastic_1", "confidence": "high"}')
    assert result.category == "plastic_1"
    assert result.confidence == "high"
    assert result.is_uncertain is False


def test_markdown_fenced_json_is_parsed():
    result = parse_classification_response('```json\n{"category": "plastic_1", "confidence": "high"}\n```')
    assert result.category == "plastic_1"
    assert result.confidence == "high"
    assert result.is_uncertain is False


def test_low_confidence_is_uncertain():
    result = parse_classification_response('{"category": "plastic_1", "confidence": "low"}')
    assert result.is_uncertain is True
    assert result.category == "unknown"


def test_unrecognized_category_is_uncertain():
    result = parse_classification_response('{"category": "styrofoam_cup", "confidence": "high"}')
    assert result.is_uncertain is True
    assert result.category == "unknown"


def test_malformed_json_is_uncertain():
    result = parse_classification_response("I think this is a plastic bottle.")
    assert result.is_uncertain is True
    assert result.category == "unknown"


def test_empty_string_is_uncertain():
    result = parse_classification_response("")
    assert result.is_uncertain is True


from unittest.mock import patch
from vision.classifier import classify_image, ClassifierError


def test_classify_image_delegates_to_parser(monkeypatch):
    class FakeResponse:
        text = '{"category": "glass", "confidence": "high"}'

    with patch("vision.classifier._call_gemini", return_value=FakeResponse()):
        result = classify_image(b"fake-image-bytes")
    assert result.category == "glass"
    assert result.is_uncertain is False


def test_classify_image_wraps_api_failures():
    with patch("vision.classifier._call_gemini", side_effect=RuntimeError("quota exceeded")):
        try:
            classify_image(b"fake-image-bytes")
            assert False, "expected ClassifierError"
        except ClassifierError:
            pass
