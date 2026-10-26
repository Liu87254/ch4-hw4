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
