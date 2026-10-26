# Discord 垃圾分類與回收標誌辨識機器人 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Discord bot where a user runs `/recycle` with a photo attachment, the bot asks Gemini's vision API to classify the material/recycling symbol, and the bot replies with the correct Taiwan EPA recycling category and disposal instructions (wash? disassemble?) looked up from a local rule table.

**Architecture:** `discord.py` slash command downloads the attachment and hands the raw bytes to a classifier module, which prompts Gemini to return one of a fixed set of category codes plus a confidence level. The command module looks up that code in a hand-written rules table (never trusts LLM-generated disposal text) and formats the reply. Low confidence, unparseable responses, or codes outside the known set are all treated as "uncertain" rather than guessed.

**Tech Stack:** Python, `discord.py`, `google-genai` (Gemini, free tier), `python-dotenv`, `pytest`

**Spec:** `docs/superpowers/specs/2026-10-26-discord-recycling-bot-design.md`

## Global Constraints

- Classification rules follow Taiwan EPA (環保署) resource recycling categories — no other region's standard.
- Vision classification uses Google Gemini's free-tier API (`google-genai`), not any paid/billed API — see spec "核心技術選擇".
- Target classification accuracy is 90%+, validated manually with real photos per category (not enforced by any single automated test — see Task 5).
- Bot interaction is exclusively the `/recycle` slash command with an image attachment — no passive channel-message scanning.
- Disposal instructions (wash/disassemble/where to drop off) always come from the local rule table, never from LLM-generated free text.
- Runs locally (developer's machine) via `python bot.py`; no cloud deployment in scope.
- Secrets (`DISCORD_TOKEN`, `GEMINI_API_KEY`) live in `.env`, excluded from git via `.gitignore`.

## Review Focus

- `/recycle` run with no attachment — must reply with a friendly prompt to attach a photo, not crash on a missing attachment.
- `/recycle` run with a non-image attachment (e.g. `.txt`, `.pdf`) — must reject with a clear message before ever calling Gemini.
- Gemini returns text that isn't valid JSON (e.g. prose, markdown fences, empty string) — must fall back to "uncertain", not raise an unhandled exception.
- Gemini returns a `category` value outside the known rule-table codes (model hallucination) — must be treated as uncertain, never passed to the rule lookup as if valid.
- The Gemini API call itself fails (network error, free-tier rate limit exceeded) — must reply with a graceful "service unavailable" message, not crash the interaction handler.

---

## Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Modify: `.gitignore` (verify `.env` is excluded; add if missing)

**Interfaces:**
- Produces: an installable environment (`pip install -r requirements.txt`) that later tasks depend on; `.env.example` documents the two required variables `DISCORD_TOKEN` and `GEMINI_API_KEY`.

- [ ] **Step 1: Write `requirements.txt`**

Pin these packages (latest stable at time of writing, no upper bound needed): `discord.py`, `google-genai`, `python-dotenv`, `pytest`, `pytest-asyncio`.

- [ ] **Step 2: Write `.env.example`**

```
DISCORD_TOKEN=your-discord-bot-token-here
GEMINI_API_KEY=your-gemini-api-key-here
```

- [ ] **Step 3: Confirm `.gitignore` excludes `.env`**

Open `.gitignore`; if no line matching `.env` exists, add one. Do not add `.env.example` to `.gitignore`.

- [ ] **Step 4: Install dependencies and verify**

Run: `pip install -r requirements.txt`
Expected: all four packages install without error.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example .gitignore
git commit -m "chore: add project scaffolding (deps, env template)"
```

---

## Task 2: Recycling rules table

**Files:**
- Create: `rules/__init__.py` (empty)
- Create: `rules/recycling_rules.py`
- Test: `tests/test_recycling_rules.py`

**Interfaces:**
- Produces:
  - `ALLOWED_CATEGORIES: list[str]` — the 15 valid category codes (see Step 3 table).
  - `RecyclingRule` — dataclass with fields `code: str`, `name: str`, `needs_wash: bool`, `needs_disassemble: bool`, `instructions: str`.
  - `get_rule(code: str) -> RecyclingRule | None` — returns `None` for any code not in `ALLOWED_CATEGORIES`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_recycling_rules.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_recycling_rules.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'rules.recycling_rules'`

- [ ] **Step 3: Implement `rules/recycling_rules.py`**

Define `RecyclingRule` as a `@dataclass(frozen=True)`. Define a module-level dict `_RULES: dict[str, RecyclingRule]` keyed by code, and `ALLOWED_CATEGORIES = list(_RULES.keys())`. `get_rule(code)` returns `_RULES.get(code)`.

Populate `_RULES` with exactly these 15 entries (Taiwan EPA categories — use these exact codes and semantics; wording of `instructions` is free as long as it conveys the stated facts):

| code | name | needs_wash | needs_disassemble | instructions must convey |
|---|---|---|---|---|
| `plastic_1` | 寶特瓶（PET，1號） | True | True | 清洗內部、壓扁、瓶蓋與瓶身分離後分別回收 |
| `plastic_2` | HDPE（2號塑膠） | True | False | 清洗後即可回收 |
| `plastic_3` | PVC（3號塑膠） | True | False | 清洗後回收 |
| `plastic_4` | LDPE（4號塑膠） | True | False | 清洗後回收 |
| `plastic_5` | PP（5號塑膠） | True | False | 清洗後回收 |
| `plastic_6` | PS（6號塑膠） | True | False | 清洗後回收 |
| `plastic_7` | 其他塑膠複合材（7號塑膠） | True | False | 清洗後回收，部分複合材質地方回收單位可能拒收，依當地規定處理 |
| `paper` | 紙類 | False | False | 保持乾燥無油污，移除膠帶與釘子，油污嚴重者視為一般垃圾 |
| `metal` | 金屬（鐵罐/鋁罐） | True | False | 清洗去除殘留食物或液體後壓扁回收 |
| `glass` | 玻璃 | True | False | 清洗後回收，小心破裂邊緣 |
| `dry_battery` | 乾電池 | False | False | 不可丟入一般垃圾或資源回收，需投入便利商店或社區的電池回收專用容器 |
| `e_waste` | 廢電子產品 | False | True | 先取出電池另外回收，主體送至社區資源回收站或特定回收商 |
| `food_waste_raw` | 生廚餘 | False | False | 瀦乾水分後交由廚餘回收，用於堆肥，不可混入熟廚餘 |
| `food_waste_cooked` | 熟廚餘 | False | False | 去除大骨硬殼等不易腐爛物後交由廚餘回收，用於養豬飼料 |
| `general_trash` | 一般垃圾 | False | False | 無法歸類為以上任一類，依一般垃圾清運規定處理 |

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_recycling_rules.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add rules/__init__.py rules/recycling_rules.py tests/test_recycling_rules.py
git commit -m "feat: add Taiwan EPA recycling rules table"
```

---

## Task 3: Gemini classification (parsing + API call)

**Files:**
- Create: `vision/__init__.py` (empty)
- Create: `vision/classifier.py`
- Test: `tests/test_classifier.py`

**Interfaces:**
- Consumes: `ALLOWED_CATEGORIES` from `rules.recycling_rules` (Task 2).
- Produces:
  - `ClassificationResult` — dataclass with fields `category: str`, `confidence: str`, `is_uncertain: bool`.
  - `parse_classification_response(raw_text: str) -> ClassificationResult` — pure function, no network calls.
  - `ClassifierError(Exception)`.
  - `classify_image(image_bytes: bytes) -> ClassificationResult` — calls Gemini, raises `ClassifierError` on any API failure, otherwise delegates parsing to `parse_classification_response`.

- [ ] **Step 1: Write failing tests for `parse_classification_response`**

```python
# tests/test_classifier.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_classifier.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'vision.classifier'`

- [ ] **Step 3: Implement `parse_classification_response(raw_text: str) -> ClassificationResult` in `vision/classifier.py`**

Attempt `json.loads(raw_text)`. On any exception (`json.JSONDecodeError`, `TypeError`), or if the parsed `category` is not in `ALLOWED_CATEGORIES`, or if `confidence == "low"`, return `ClassificationResult(category="unknown", confidence="low", is_uncertain=True)`. Otherwise return `ClassificationResult(category=<parsed category>, confidence=<parsed confidence>, is_uncertain=False)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_classifier.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add vision/__init__.py vision/classifier.py tests/test_classifier.py
git commit -m "feat: add Gemini response parsing with uncertain fallback"
```

- [ ] **Step 6: Write failing test for `classify_image`**

```python
# tests/test_classifier.py (append)
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
```

- [ ] **Step 7: Run tests to verify they fail**

Run: `pytest tests/test_classifier.py -v`
Expected: FAIL — `_call_gemini` and `classify_image` not defined

- [ ] **Step 8: Implement `_call_gemini(image_bytes: bytes)` and `classify_image(image_bytes: bytes) -> ClassificationResult`**

`_call_gemini` is a small private wrapper around the `google.genai` SDK call (`from google import genai`; `genai.Client(api_key=...)` built from `GEMINI_API_KEY` in `os.environ`; build a prompt that lists `ALLOWED_CATEGORIES` and instructs the model to reply with only a JSON object `{"category": ..., "confidence": "high"|"medium"|"low"}`; call `client.models.generate_content(model="gemini-2.0-flash", contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")])`; return the SDK response object). `classify_image` calls `_call_gemini(image_bytes)` inside a `try/except Exception as e: raise ClassifierError(str(e))`, then returns `parse_classification_response(response.text)`.

- [ ] **Step 9: Run tests to verify they pass**

Run: `pytest tests/test_classifier.py -v`
Expected: PASS (7 passed)

- [ ] **Step 10: Commit**

```bash
git add vision/classifier.py tests/test_classifier.py
git commit -m "feat: call Gemini vision API for image classification"
```

---

## Task 4: `/recycle` slash command logic

**Files:**
- Create: `commands/__init__.py` (empty)
- Create: `commands/recycle.py`
- Test: `tests/test_recycle_command.py`

**Interfaces:**
- Consumes: `classify_image`, `ClassifierError` from `vision.classifier` (Task 3); `get_rule` from `rules.recycling_rules` (Task 2).
- Produces:
  - `validate_attachment(content_type: str | None) -> bool` — `True` only when `content_type` starts with `"image/"`.
  - `format_reply(rule) -> str` — formats a known `RecyclingRule` into the Chinese reply text, must mention wash/disassemble explicitly (yes/no) and include `rule.instructions`.
  - `UNCERTAIN_REPLY: str` — fixed message for low-confidence/unparseable/unknown-category results.
  - `SERVICE_ERROR_REPLY: str` — fixed message for `ClassifierError`.
  - `NO_ATTACHMENT_REPLY: str`, `INVALID_ATTACHMENT_REPLY: str` — fixed messages.
  - `async def handle_recycle_command(attachment) -> str` — orchestrates validation → classification → rule lookup → reply text; `attachment` is any object exposing `.content_type: str | None` and `.read() -> bytes` (an `async` method, matching `discord.Attachment`).

- [ ] **Step 1: Write failing tests for the pure formatting/validation functions**

```python
# tests/test_recycle_command.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_recycle_command.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'commands.recycle'`

- [ ] **Step 3: Implement `validate_attachment` and `format_reply` in `commands/recycle.py`**

`format_reply` must render `needs_wash` and `needs_disassemble` as explicit 是/否 (yes/no) Chinese text alongside `rule.name` and `rule.instructions`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_recycle_command.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add commands/__init__.py commands/recycle.py tests/test_recycle_command.py
git commit -m "feat: add recycle command validation and reply formatting"
```

- [ ] **Step 6: Write failing tests for `handle_recycle_command` covering the Review Focus cases**

```python
# tests/test_recycle_command.py (append)
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
```

`pytest-asyncio` is already in `requirements.txt` (Task 1). Mark these tests with `@pytest.mark.asyncio` as shown above (the explicit marker works without any `pytest.ini`/`pyproject.toml` config).

- [ ] **Step 7: Run tests to verify they fail**

Run: `pytest tests/test_recycle_command.py -v`
Expected: FAIL — `handle_recycle_command` and the reply constants not defined

- [ ] **Step 8: Implement the four reply constants and `handle_recycle_command` in `commands/recycle.py`**

Logic: if `attachment is None`, return `NO_ATTACHMENT_REPLY`. If `not validate_attachment(attachment.content_type)`, return `INVALID_ATTACHMENT_REPLY`. Otherwise `image_bytes = await attachment.read()`; call `classify_image(image_bytes)` inside `try/except ClassifierError: return SERVICE_ERROR_REPLY`. If the result `is_uncertain`, return `UNCERTAIN_REPLY`. Otherwise `rule = get_rule(result.category)`; if `rule is None`, return `UNCERTAIN_REPLY` (defensive — Task 3's parser already guards against unknown codes, but this is the second line of defense named in the spec's error table). Otherwise return `format_reply(rule)`.

- [ ] **Step 9: Run tests to verify they pass**

Run: `pytest tests/test_recycle_command.py -v`
Expected: PASS (9 passed)

- [ ] **Step 10: Commit**

```bash
git add commands/recycle.py tests/test_recycle_command.py
git commit -m "feat: wire recycle command orchestration with error handling"
```

---

## Task 5: Bot entry point and README

**Files:**
- Create: `bot.py`
- Create: `README.md`

**Interfaces:**
- Consumes: `handle_recycle_command` from `commands.recycle` (Task 4).
- Produces: a runnable program (`python bot.py`) — no further task depends on this one.

- [ ] **Step 1: Implement `bot.py`**

Load `.env` via `python-dotenv`. Create a `discord.Client`/`discord.ext.commands.Bot` with a registered slash command named `recycle` that takes one optional attachment parameter named `photo`, calls `await handle_recycle_command(photo)`, and sends the returned string back via `interaction.response.send_message(...)`. Read `DISCORD_TOKEN` from `os.environ` and call `bot.run(token)` under `if __name__ == "__main__":`.

- [ ] **Step 2: Manual verification — bot comes online**

Run: `python bot.py`
Expected: console logs show the bot logging in successfully, and the bot's status in the Discord member list changes from offline to online.

- [ ] **Step 3: Manual verification — slash command round-trip**

In the Discord server, run `/recycle` with a clear photo of a labeled PET bottle attached.
Expected: bot replies within a few seconds with text that names the correct category (寶特瓶／PET) and mentions washing.

- [ ] **Step 4: Write `README.md`**

Cover: project description, prerequisites, how to get a Discord Bot Token (Developer Portal → New Application → Bot → Reset Token; OAuth2 URL Generator with `bot` + `applications.commands` scopes and `Send Messages`/`Attach Files`/`Read Message History` permissions to invite it), how to get a Gemini API Key (Google AI Studio → Create API key, no credit card required, free-tier rate limits apply), how to fill in `.env` from `.env.example`, how to install dependencies and run (`pip install -r requirements.txt`, `python bot.py`), how to run tests (`pytest`), and the manual accuracy-validation process from the spec's Testing Plan (test with real photos across all 15 categories, target 90%+, adjust the Gemini prompt in `vision/classifier.py` if short of target).

- [ ] **Step 5: Commit**

```bash
git add bot.py README.md
git commit -m "feat: add bot entry point and setup documentation"
```

---

## Self-Review Notes

- **Spec coverage:** 背景/目標 → Task 4+5 (reply content); 核心技術選擇 (Gemini, discord.py, slash command, local) → Tasks 1,3,5; 分類範圍 (15 categories) → Task 2; LLM-only-classifies / rules-table-decides-instructions → Tasks 2+3+4; 專案結構 → file paths across all tasks match the spec's tree; 設定與機密管理 → Task 1; 錯誤處理 table → Task 4 Steps 6-9 (every row has a corresponding test); 測試計畫 → Task 2 unit tests (rules), Task 5 Step 4 README documents the manual accuracy validation (not itself automatable — accuracy against real photos can't be a unit test).
- **Review Focus coverage:** all five listed items have a named test in Task 4 Step 6.
- **Type consistency checked:** `ClassificationResult(category, confidence, is_uncertain)` used identically in Tasks 3 and 4; `RecyclingRule` fields (`name`, `needs_wash`, `needs_disassemble`, `instructions`) used identically in Tasks 2 and 4; `ClassifierError` raised in Task 3, caught in Task 4.
