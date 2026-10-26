# 垃圾分類與回收標誌辨識 Discord 機器人

透過 `/recycle` 指令上傳垃圾/回收物照片，機器人會呼叫 Google Gemini 的視覺 API 辨識材質與回收標誌（塑膠編號 1-7 號、紙類、金屬、玻璃、乾電池、廢電子產品、生廚餘/熟廚餘），並依照台灣環保署資源回收分類標準回覆正確的分類歸屬與處理方式（是否需清洗、是否需拆解）。

## 事前準備

- Python 3.10 以上
- 一個 Discord 帳號與伺服器（用來邀請並測試機器人）
- 一個 Google 帳號（用來申請 Gemini API Key）

## 1. 取得 Discord Bot Token

1. 前往 https://discord.com/developers/applications
2. 點「New Application」建立一個新應用程式
3. 左側選單點「Bot」→「Reset Token」取得 Token（只會顯示一次，請先複製存好）
4. 在同一頁開啟「Message Content Intent」等需要的 Privileged Gateway Intents
5. 左側選單點「OAuth2」→「URL Generator」：
   - Scopes 勾選 `bot` 與 `applications.commands`
   - Bot Permissions 勾選 `Send Messages`、`Attach Files`、`Read Message History`
   - 複製產生的網址到瀏覽器打開，選擇你的伺服器並授權，機器人就會加入伺服器成員列表（顯示離線，正常現象）

## 2. 取得 Gemini API Key

1. 前往 https://aistudio.google.com
2. 用 Google 帳號登入
3. 找到「Get API Key」→「Create API key」
4. 不需要信用卡；屬於免費額度，有每分鐘/每日呼叫次數上限

## 3. 設定環境變數

複製 `.env.example` 為 `.env`，填入剛剛取得的兩個值：

```
DISCORD_TOKEN=你的discord_bot_token
GEMINI_API_KEY=你的gemini_api_key
```

`.env` 已被 `.gitignore` 排除，不會被提交到版本控制。

## 4. 安裝依賴並執行

```bash
pip install -r requirements.txt
python bot.py
```

執行後若看到終端機印出 `Logged in as ...`，且機器人在 Discord 伺服器成員列表中從離線變成上線，就代表啟動成功。

在 Discord 任一文字頻道輸入 `/recycle`，並附上一張圖片，機器人會回覆辨識出的分類與處理方式（是否需清洗、是否需拆解）。

## 5. 執行測試

```bash
pytest
```

所有單元測試（規則表查詢、Gemini 回應解析、指令邏輯）皆不需要真正的 Discord 連線或 API 金鑰即可執行。

## 6. 驗證辨識準確度（手動）

專案目標是辨識準確度達 90% 以上。由於這項指標只能透過真實照片人工驗證，建議：

1. 準備涵蓋全部 15 個分類的真實照片（塑膠 1-7 號、紙類、金屬、玻璃、乾電池、廢電子產品、生廚餘、熟廚餘、一般垃圾）
2. 逐一用 `/recycle` 測試，記錄辨識是否正確
3. 若整體正確率低於 90%，調整 `vision/classifier.py` 中 `_PROMPT_TEMPLATE` 的提示文字（例如加入更明確的分類範例或判斷依據），重新測試
