from rules.recycling_rules import get_rule, ALLOWED_CATEGORIES


def test_allowed_categories_has_15_codes():
    assert len(ALLOWED_CATEGORIES) == 15


def test_plastic_1_requires_wash_and_disassemble():
    rule = get_rule("plastic_1")
    assert rule.name == "寶特瓶（PET，1號）"
    assert rule.needs_wash is True
    assert rule.needs_disassemble is True


def test_dry_battery_no_wash_no_disassemble():
    rule = get_rule("dry_battery")
    assert rule.needs_wash is False
    assert rule.needs_disassemble is False
    assert "電池回收" in rule.instructions


def test_food_waste_raw_and_cooked_are_distinct():
    raw = get_rule("food_waste_raw")
    cooked = get_rule("food_waste_cooked")
    assert raw.code != cooked.code
    assert raw.instructions != cooked.instructions


def test_general_trash_exists():
    rule = get_rule("general_trash")
    assert rule.needs_wash is False
    assert rule.needs_disassemble is False


def test_unknown_code_returns_none():
    assert get_rule("not_a_real_code") is None
