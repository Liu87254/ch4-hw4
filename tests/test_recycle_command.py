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
