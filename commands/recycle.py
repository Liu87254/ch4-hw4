from rules.recycling_rules import get_rule
from vision.classifier import classify_image, ClassifierError

NO_ATTACHMENT_REPLY = "請附上一張照片再使用 /recycle 指令。"
INVALID_ATTACHMENT_REPLY = "請上傳圖片格式的附件（例如 jpg、png）。"
UNCERTAIN_REPLY = "無法確定分類，請提供更清晰或更完整的照片（光線充足、標誌入鏡）。"
SERVICE_ERROR_REPLY = "辨識服務暫時無法使用，請稍後再試。"


def validate_attachment(content_type: str | None) -> bool:
    return content_type is not None and content_type.startswith("image/")


def format_reply(rule) -> str:
    wash_text = "是" if rule.needs_wash else "否"
    disassemble_text = "是" if rule.needs_disassemble else "否"
    return (
        f"分類：{rule.name}\n"
        f"需清洗：{wash_text}\n"
        f"需拆解：{disassemble_text}\n"
        f"處理方式：{rule.instructions}"
    )


async def handle_recycle_command(attachment) -> str:
    if attachment is None:
        return NO_ATTACHMENT_REPLY
    if not validate_attachment(attachment.content_type):
        return INVALID_ATTACHMENT_REPLY

    image_bytes = await attachment.read()
    try:
        result = classify_image(image_bytes)
    except ClassifierError:
        return SERVICE_ERROR_REPLY

    if result.is_uncertain:
        return UNCERTAIN_REPLY

    rule = get_rule(result.category)
    if rule is None:
        return UNCERTAIN_REPLY

    return format_reply(rule)
