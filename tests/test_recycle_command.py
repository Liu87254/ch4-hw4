from commands.recycle import validate_attachment, format_reply
from rules.recycling_rules import get_rule


def test_validate_attachment_accepts_image():
    assert validate_attachment("image/png") is True


def test_validate_attachment_rejects_non_image():
    assert validate_attachment("text/plain") is False


def test_validate_attachment_rejects_none():
    assert validate_attachment(None) is False


def test_format_reply_mentions_wash_and_disassemble():
    rule = get_rule("plastic_1")
    reply = format_reply(rule)
    assert rule.name in reply
    assert rule.instructions in reply
    assert "需清洗" in reply or "清洗" in reply


import pytest
from unittest.mock import patch
from vision.classifier import ClassifierError, ClassificationResult
from commands.recycle import (
    handle_recycle_command,
    NO_ATTACHMENT_REPLY,
    INVALID_ATTACHMENT_REPLY,
    UNCERTAIN_REPLY,
    SERVICE_ERROR_REPLY,
)


class FakeAttachment:
    def __init__(self, content_type, data=b"fake"):
        self.content_type = content_type
        self._data = data

    async def read(self):
        return self._data


@pytest.mark.asyncio
async def test_no_attachment_returns_prompt():
    reply = await handle_recycle_command(None)
    assert reply == NO_ATTACHMENT_REPLY


@pytest.mark.asyncio
async def test_non_image_attachment_rejected():
    reply = await handle_recycle_command(FakeAttachment("application/pdf"))
    assert reply == INVALID_ATTACHMENT_REPLY


@pytest.mark.asyncio
async def test_uncertain_classification_returns_uncertain_reply():
    with patch("commands.recycle.classify_image", return_value=ClassificationResult("unknown", "low", True)):
        reply = await handle_recycle_command(FakeAttachment("image/png"))
    assert reply == UNCERTAIN_REPLY


@pytest.mark.asyncio
async def test_classifier_error_returns_service_error_reply():
    with patch("commands.recycle.classify_image", side_effect=ClassifierError("quota exceeded")):
        reply = await handle_recycle_command(FakeAttachment("image/png"))
    assert reply == SERVICE_ERROR_REPLY


@pytest.mark.asyncio
async def test_known_category_returns_formatted_reply():
    with patch("commands.recycle.classify_image", return_value=ClassificationResult("dry_battery", "high", False)):
        reply = await handle_recycle_command(FakeAttachment("image/png"))
    assert "乾電池" in reply
