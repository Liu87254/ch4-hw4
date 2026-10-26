from dataclasses import dataclass


@dataclass(frozen=True)
class RecyclingRule:
    code: str
    name: str
    needs_wash: bool
    needs_disassemble: bool
    instructions: str


_RULES: dict[str, RecyclingRule] = {
    "plastic_1": RecyclingRule(
        code="plastic_1",
        name="寶特瓶（PET，1號）",
        needs_wash=True,
        needs_disassemble=True,
        instructions="清洗內部、壓扁、瓶蓋與瓶身分離後分別回收",
    ),
    "plastic_2": RecyclingRule(
        code="plastic_2",
        name="HDPE（2號塑膠）",
        needs_wash=True,
        needs_disassemble=False,
        instructions="清洗後即可回收",
    ),
    "plastic_3": RecyclingRule(
        code="plastic_3",
        name="PVC（3號塑膠）",
        needs_wash=True,
        needs_disassemble=False,
        instructions="清洗後回收",
    ),
    "plastic_4": RecyclingRule(
        code="plastic_4",
        name="LDPE（4號塑膠）",
        needs_wash=True,
        needs_disassemble=False,
        instructions="清洗後回收",
    ),
    "plastic_5": RecyclingRule(
        code="plastic_5",
        name="PP（5號塑膠）",
        needs_wash=True,
        needs_disassemble=False,
        instructions="清洗後回收",
    ),
    "plastic_6": RecyclingRule(
        code="plastic_6",
        name="PS（6號塑膠）",
        needs_wash=True,
        needs_disassemble=False,
        instructions="清洗後回收",
    ),
    "plastic_7": RecyclingRule(
        code="plastic_7",
        name="其他塑膠複合材（7號塑膠）",
        needs_wash=True,
        needs_disassemble=False,
        instructions="清洗後回收，部分複合材質地方回收單位可能拒收，依當地規定處理",
    ),
    "paper": RecyclingRule(
        code="paper",
        name="紙類",
        needs_wash=False,
        needs_disassemble=False,
        instructions="保持乾燥無油污，移除膠帶與釘子，油污嚴重者視為一般垃圾",
    ),
    "metal": RecyclingRule(
        code="metal",
        name="金屬（鐵罐/鋁罐）",
        needs_wash=True,
        needs_disassemble=False,
        instructions="清洗去除殘留食物或液體後壓扁回收",
    ),
    "glass": RecyclingRule(
        code="glass",
        name="玻璃",
        needs_wash=True,
        needs_disassemble=False,
        instructions="清洗後回收，小心破裂邊緣",
    ),
    "dry_battery": RecyclingRule(
        code="dry_battery",
        name="乾電池",
        needs_wash=False,
        needs_disassemble=False,
        instructions="不可丟入一般垃圾或資源回收，需投入便利商店或社區的電池回收專用容器",
    ),
    "e_waste": RecyclingRule(
        code="e_waste",
        name="廢電子產品",
        needs_wash=False,
        needs_disassemble=True,
        instructions="先取出電池另外回收，主體送至社區資源回收站或特定回收商",
    ),
    "food_waste_raw": RecyclingRule(
        code="food_waste_raw",
        name="生廚餘",
        needs_wash=False,
        needs_disassemble=False,
        instructions="瀦乾水分後交由廚餘回收，用於堆肥，不可混入熟廚餘",
    ),
    "food_waste_cooked": RecyclingRule(
        code="food_waste_cooked",
        name="熟廚餘",
        needs_wash=False,
        needs_disassemble=False,
        instructions="去除大骨硬殼等不易腐爛物後交由廚餘回收，用於養豬飼料",
    ),
    "general_trash": RecyclingRule(
        code="general_trash",
        name="一般垃圾",
        needs_wash=False,
        needs_disassemble=False,
        instructions="無法歸類為以上任一類，依一般垃圾清運規定處理",
    ),
}

ALLOWED_CATEGORIES = list(_RULES.keys())


def get_rule(code: str) -> RecyclingRule | None:
    return _RULES.get(code)
