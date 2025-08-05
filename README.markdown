# Discord AI 聊天機器人專案說明書

## 專案概述

本專案是一個基於 Python 的 Discord AI 聊天機器人，整合了 **OpenRouter API**（用於生成智能回應）、**Serper API**（用於網路搜尋）以及圖片處理功能，旨在提供一個多功能的聊天體驗。機器人能夠根據用戶訊息進行意圖識別，自動判斷是否需要搜尋最新資訊，並支援圖片分析，全部以繁體中文回應，保持友善且有趣的語氣。

本說明書旨在幫助開發者（特別是在 Vibe Coding 環境中）快速理解專案的程式碼結構、功能模組、依賴關係以及運行邏輯，以便於維護、擴展或除錯。

---

## 專案目標

- **核心功能**：
  - 提供 Discord 聊天機器人，支援文字對話、圖片分析和意圖識別。
  - 根據訊息內容自動判斷是否需要網路搜尋，並整合搜尋結果生成回應。
  - 使用 OpenRouter AI 提供知識淵博且有趣的回應。
  - 支援圖片附件分析，使用 AI 模型。
  - 提供清晰的日誌記錄，便於除錯和監控。
- **設計原則**：
  - 模組化結構，易於維護和擴展。
  - 遵循 Python 最佳實踐，包括錯誤處理和詳細註釋。
  - 支援繁體中文，確保回應友善且符合文化語境。
- **使用場景**：
  - Discord 社群中的互動式 AI 助手。
  - 需要即時資訊查詢的應用（例如天氣、新聞）。
  - 圖片內容分析（例如識別圖片中的動物或場景）。

---

## 程式碼結構

專案主要檔案為 `discord_bot.py`，以下是程式碼的結構分解：

### 1. **檔案與模組**

- **檔案**：`discord_bot.py`
  - 核心程式碼，包含所有功能邏輯。
- **環境變數**：`.env`
  - 儲存 Discord Bot Token、OpenRouter API Key 和 Serper API Key。
- **依賴套件**：
  - `discord.py`：處理 Discord API 互動。
  - `python-dotenv`：載入環境變數。
  - `openai`：與 OpenRouter API 互動。
  - `requests`：執行 HTTP 請求（用於 Serper API 和圖片下載）。
  - `pytz`：處理時區和時間格式。
  - `re`：正則表達式，用於意圖識別。
  - `random`：未直接使用，但作為未來擴展預留。
  - `base64` 和 `io`：處理圖片轉換為 base64 格式。

### 2. **主要模組與功能**

#### a. **環境設置與初始化**

- **程式碼位置**：檔案開頭
- **功能**：
  - 載入環境變數（`.env`）。
  - 初始化 Discord 機器人，設置指令前綴（`!`）和 intents（啟用訊息內容訪問）。
  - 配置 OpenRouter API 客戶端，設置 API Key 和基礎 URL。
  - 配置 Serper API 的 URL 和 API Key。
- **關鍵物件**：
  - `bot`：Discord 機器人實例（`commands.Bot`）。
  - `client`：OpenRouter API 客戶端（`openai.OpenAI`）。
  - `intent_classifier`：意圖分類器實例（`IntentClassifier`）。

#### b. **意圖識別（IntentClassifier 類）**

- **程式碼位置**：`class IntentClassifier`
- **功能**：
  - 使用正則表達式（`re`）根據關鍵詞模式識別訊息意圖，分為：
    - `greeting`：問候語（例如「嗨」、「你好」）。
    - `casual_chat`：一般對話（例如「謝謝」、「哈哈」）。
    - `personal_question`：關於機器人的問題（例如「你是誰」）。
    - `need_search`：需要網路搜尋的問題（例如「天氣」、「新聞」）。
  - 方法 `classify_intent` 接受訊息並返回對應意圖。
- **關鍵邏輯**：
  - 使用 `re.search` 進行模式匹配，忽略大小寫。
  - 若無匹配模式，預設為 `need_search`。

#### c. **時間處理（get_current_time 函數）**

- **程式碼位置**：`def get_current_time`
- **功能**：
  - 獲取指定時區（預設為 `Asia/Taipei`）的當前時間。
  - 使用 `pytz` 確保時區正確，返回格式化時間字串（例如「2025年7月21日 15:35:00 Asia/Taipei」）。
- **錯誤處理**：
  - 捕獲時區或格式化錯誤，返回錯誤訊息。

#### d. **網路搜尋（search_web 函數）**

- **程式碼位置**：`def search_web`
- **功能**：
  - 使用 Serper API 進行 Google 搜尋，查詢用戶問題相關的最新資訊。
  - 限制返回前 5 個結果，提取標題、描述和連結。
- **錯誤處理**：
  - 處理 HTTP 錯誤（例如 401 Unauthorized）。
  - 處理通用異常（例如網路連線問題）。
- **日誌**：
  - 記錄請求 URL 和搜尋結果，便於除錯。

#### e. **Discord 事件與指令**

- **程式碼位置**：`@bot.event` 和 `@bot.command`
- **功能**：
  - **`on_ready`**：機器人啟動時記錄登錄資訊。
  - **`on_message`**：監聽所有訊息，處理提及或私訊，提示使用 `!chat`。
  - **`!chat`**：核心聊天指令，支援文字和圖片處理。
    - 根據意圖選擇是否搜尋。
    - 處理圖片附件，轉為 base64 格式並使用 AI 分析。
    - 整合搜尋結果、當前時間和用戶問題，生成 AI 回應。
  - **`!intent`**：測試意圖識別功能，返回嵌入式結果。
  - **`!help_bot`**：顯示機器人功能說明，使用 Discord Embed 格式。
- **錯誤處理**：
  - 檢查無效輸入（例如無訊息或圖片）。
  - 捕獲所有異常，回應友善錯誤訊息。

#### f. **圖片處理**

- **程式碼位置**：`@bot.command() async def chat`
- **功能**：
  - 檢測訊息中的圖片附件（僅支援圖片格式，例如 JPEG、PNG）。
  - 使用 `requests` 下載圖片，轉為 base64 格式。
  - 將圖片和用戶問題傳送至 OpenRouter API（AI 模型）進行分析。
- **錯誤處理**：
  - 處理圖片下載失敗或格式錯誤。
  - 記錄圖片處理過程。

### 3. **程式碼流程**

1. **啟動**：
   - 載入環境變數，初始化 Discord 機器人和 OpenRouter API 客戶端。
   - 啟動機器人，監聽事件和指令。
2. **訊息處理**：
   - 監聽訊息（`on_message`），檢查是否提及機器人或為私訊。
   - 自動識別意圖，提示使用 `!chat`。
3. **聊天流程**（`!chat`）：
   - 若包含圖片：
     - 下載圖片，轉為 base64。
     - 使用 AI 分析圖片並生成回應。
   - 若無圖片：
     - 使用 `IntentClassifier` 識別意圖。
     - 若為 `greeting`、`casual_chat` 或 `personal_question`，直接生成回應。
     - 若為 `need_search`，執行 Serper API 搜尋，整合結果生成回應。
4. **其他指令**：
   - `!intent`：返回意圖識別結果。
   - `!help_bot`：顯示功能說明。
5. **日誌與錯誤處理**：
   - 記錄所有關鍵步驟（API 請求、意圖識別、圖片處理等）。
   - 捕獲異常，回應友善錯誤訊息。

---

## 技術細節

### 1. **依賴版本**

- Python 3.8+
- `discord.py>=2.0.0`
- `python-dotenv>=0.20.0`
- `openai>=1.0.0`
- `requests>=2.28.0`
- `pytz>=2022.1`

### 2. **API 整合**

- **OpenRouter API**：
  - 使用 `openai` 客戶端，預設使用 `deepseek/deepseek-chat-v3-0324:free`（文字）和 `google/gemma-3-27b-it:free`（圖片）。
  - 設置 `max_tokens`（文字 2000，圖片 2000）控制回應長度。
  - 使用 `temperature=1` 確保回應多樣性。
- **Serper API**：
  - 使用 POST 請求，限制返回 5 個搜尋結果。
  - 提取 `title`、`snippet` 和 `link` 字段。
- **Discord API**：
  - 使用 `discord.py` 處理事件和指令。
  - 啟用 `intents.message_content` 以訪問訊息內容。

### 3. **錯誤處理**

- **環境變數**：檢查 API 金鑰是否設置。
- **API 請求**：捕獲 HTTP 錯誤（例如 401、429）和網路異常。
- **圖片處理**：確保圖片格式正確，處理下載失敗。
- **用戶輸入**：檢查空訊息或無效輸入，提示正確用法。

### 4. **日誌**

- 記錄關鍵資訊：
  - API 金鑰（僅顯示是否存在）。
  - 用戶訊息、意圖識別結果。
  - API 請求 URL 和回應內容。
  - 圖片處理過程和錯誤。
- 日誌輸出至終端機，便於除錯。

---

## 如何運行

### 1. **設置環境**

1. 安裝 Python 3.8 或以上版本。
2. 安裝依賴套件：
   ```bash
   pip install discord.py python-dotenv openai requests pytz
   ```
3. 創建 `.env` 檔案，填入以下內容：
   ```
   DISCORD_BOT_TOKEN=你的Discord機器人Token
   OPENROUTER_API_KEY=你的OpenRouter API金鑰
   SERPER_API_KEY=你的Serper API金鑰
   ```

### 2. **運行程式**

1. 將 `discord_bot.py` 保存到本地目錄。
2. 開啟終端機，進入程式碼目錄，執行：
   ```bash
   python discord_bot.py
   ```
3. 成功運行後，終端機顯示 `已登入為 {機器人名稱}`，表示機器人已上線。

### 3. **測試機器人**

1. 將機器人邀請至 Discord 伺服器（透過 Discord Developer Portal 生成邀請連結）。
2. 在 Discord 中使用以下指令測試：

   - `!chat 你好`：測試問候語回應。
   - `!chat 台北今天的天氣如何？`：測試搜尋功能。
   - `!chat` + 圖片附件：測試圖片分析。
   - `!intent 早安`：測試意圖識別。
   - `!help_bot`：查看功能說明。

---

## 除錯指南

### 常見錯誤與解決方法

1. **錯誤**：`HTTP 錯誤：401 Unauthorized`
   - **原因**：API 金鑰無效。
   - **解決**：
     - 檢查 `.env` 檔案中的金鑰是否正確。
     - 從 OpenRouter 或 Serper 重新獲取金鑰。
2. **錯誤**：`ConnectionError`
   - **原因**：網路問題或 API 服務不可用。
   - **解決**：
     - 檢查網路連線。
     - 確認 OpenRouter 和 Serper API 狀態。
3. **錯誤**：`無搜尋結果`
   - **原因**：查詢過於模糊或 API 配額耗盡。
   - **解決**：
     - 使用更具體的查詢詞。
     - 檢查 Serper API 配額。
4. **錯誤**：圖片無法分析
   - **原因**：圖片格式不支援或下載失敗。
   - **解決**：
     - 確保圖片為 JPEG 或 PNG 格式。
     - 檢查圖片大小（建議 <5MB）。
5. **其他錯誤**：
   - 查看終端機日誌，尋找具體錯誤訊息。
   - 檢查依賴套件是否正確安裝（`pip list`）。

### 日誌分析

- 日誌記錄在終端機，包含：
  - API 金鑰狀態。
  - 用戶訊息和意圖識別結果。
  - API 請求和回應內容。
  - 圖片處理過程。
- 搜尋關鍵詞（如「錯誤」、「HTTP」、「圖片處理」）以定位問題。

---

## 注意事項

- **API 配額**：OpenRouter 和 Serper API 有使用限制，確保帳戶有足夠配額。
- **圖片限制**：建議圖片大小不超過 5MB，避免處理延遲。
- **指令前綴**：固定為 `!`，可在 `bot = commands.Bot(command_prefix='!')` 修改。
- **安全性**：
  - 保護 `.env` 檔案，避免洩漏 API 金鑰。
  - 避免上傳敏感圖片，機器人會記錄處理過程。

---

## 聯繫與資源

- **文檔**：
  - [Discord.py 文檔](https://discordpy.readthedocs.io/)
  - [OpenRouter API 文檔](https://openrouter.ai/docs)
  - [Serper API 文檔](https://serper.dev/)
- **支援**：
  - 檢查日誌或聯繫開發者。
  - 在 Discord 社群或 GitHub 提交問題。
