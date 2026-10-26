from vision.classifier import parse_classification_response


def test_valid_high_confidence_response():
    result = parse_classification_response('{"category": "plastic_1", "confidence": "high"}')
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
