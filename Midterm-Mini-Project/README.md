# 📚 AI 作業與考試規劃助手

## 一、專題介紹

本專題為生成式 AI 課程的期中個人小專題，使用 Python、Streamlit 與 OpenAI API 開發「AI 作業與考試規劃助手」。

使用者可以貼上老師發布的作業或考試公告，系統會透過生成式 AI 自動擷取重要資訊，整理成結構化資料，協助學生快速掌握截止日期、待辦事項及需要進一步確認的資訊。

## 二、研究動機

大學生經常需要同時處理不同課程的作業、考試及報告。由於老師的公告格式不一定相同，學生可能需要花費時間閱讀與整理，也容易忽略重要的截止日期或繳交要求。

因此，本專題希望利用生成式 AI，將非結構化的課程公告轉換成容易閱讀的任務清單，降低整理資訊的時間成本。

## 三、專題功能

1. **公告文字輸入**：使用者可以貼上作業或考試公告。
2. **AI 自動整理**：辨識公告中的作業名稱、類型、截止日期與待辦事項。
3. **多項任務整理**：一則公告包含多項作業或考試時，可分別輸出。
4. **資訊不足處理**：公告未提供截止日期時，顯示「未知」，不自行編造。
5. **缺少資訊提示**：整理需要進一步確認的資訊。
6. **JSON 結構化輸出**：使用 JSON Schema 規範 AI 回傳格式。
7. **輸入驗證**：拒絕空白輸入與超過 6000 字元的內容。
8. **API 開關**：預設關閉 API，使用者須主動勾選才能送出請求。
9. **錯誤處理**：當 API 無法連線、金鑰未設定或回傳資料不正確時，顯示錯誤訊息。

## 四、使用技術

| 技術 | 用途 |
|---|---|
| Python | 主要程式語言 |
| Streamlit | 建立互動式網頁 |
| OpenAI Responses API | 進行生成式 AI 資訊整理 |
| JSON Schema | 定義結構化輸出格式 |
| urllib.request | 發送 HTTP API 請求 |
| TOML / Streamlit Secrets | 管理 API 金鑰 |

本專題使用 JSON Schema 的 Structured Outputs，並透過程式進一步驗證回傳資料。

由於開發電腦的 Windows 應用程式控制政策限制 Pydantic 核心模組載入，因此改用 Python 內建的 `urllib.request` 發送 API 請求，不依賴 OpenAI Python SDK。

## 五、JSON Schema 輸出欄位

系統主要使用以下欄位：

| 欄位 | 資料型態 | 說明 |
|---|---|---|
| tasks | Array | 作業與考試任務清單 |
| task_name | String | 任務名稱 |
| task_type | String | 作業、考試或其他 |
| deadline | String | 截止日期，未知時填入「未知」 |
| todo_items | Array | 待辦事項清單 |
| missing_info | Array | 尚未提供或需要確認的資訊 |

系統使用 `strict: true` 與 `additionalProperties: false` 限制 AI 的輸出格式。

## 六、專案檔案結構

```text
Midterm Mini-Project/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── .streamlit/
│   └── secrets.example.toml
└── 設計與驗收紀錄.md
```

以上為預計繳交的專案結構，尚未建立的檔案須在繳交前補齊。

實際 API 金鑰存放於 `.streamlit/secrets.toml`，此檔案不應上傳 GitHub。

## 七、本機執行方式

### 1. 建立虛擬環境

```powershell
py -3.14 -m venv .venv
```

### 2. 啟動虛擬環境

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 安裝套件

```powershell
python -m pip install -r requirements.txt
```

### 4. 設定 API 金鑰

在 `.streamlit/secrets.toml` 中設定：

```toml
OPENAI_API_KEY = "YOUR_API_KEY"
OPENAI_MODEL = "gpt-5.4-mini"
```

請將 `YOUR_API_KEY` 替換成自己的 API 金鑰，並確認所選模型在 API 帳戶中可用。

### 5. 啟動網頁

```powershell
python -m streamlit run app.py
```

在瀏覽器開啟 `http://localhost:8501`。

## 八、功能測試與驗收

### 測試 A：空白輸入

- 輸入：空白
- 預期結果：顯示「請先輸入作業或考試公告。」
- API 呼叫嘗試次數：0
- 測試結果：通過

### 測試 B：超過 6000 字元

- 輸入：6001 個字元
- 預期結果：顯示字數超過限制的錯誤訊息
- API 呼叫嘗試次數：0
- 測試結果：通過

### 測試 C：API 關閉

- 輸入：正常作業公告
- API 開關：關閉
- 預期結果：顯示 API 關閉提示
- API 呼叫嘗試次數：0
- 測試結果：通過

### 測試 D：正常公告

測試公告：

資料庫系統期中報告將於 2026 年 11 月 20 日截止，請同學繳交 ER 圖、10 題 SQL 查詢語法，以及專題心得。請於截止日前上傳至課程平台。

實際結果：

- 任務名稱：資料庫系統期中報告
- 類型：作業
- 截止日期：2026 年 11 月 20 日
- 待辦事項：繳交 ER 圖、10 題 SQL 查詢語法、專題心得，並於截止日前上傳
- 測試結果：通過

### 測試 E：資訊不足公告

測試公告：

老師說資料庫系統這學期要交一份期末報告，需要完成 ER 圖和 SQL 查詢，但目前還沒有公布繳交日期，也沒有說明需要幾題 SQL 查詢。

實際結果：

- 任務名稱：資料庫系統期末報告
- 類型：作業
- 截止日期：未知
- 待辦事項：完成 ER 圖、完成 SQL 查詢
- 缺少資訊：繳交日期、需要完成的 SQL 查詢題數
- 測試結果：通過

## 九、系統限制

1. AI 可能誤解語意，使用者仍須核對原始公告。
2. 沒有明確日期時，系統不會自行推算。
3. 需要網路連線及有效的 OpenAI API 金鑰。
4. API 呼叫可能產生費用。
5. 單次輸入限制為 6000 字元。
6. 系統目前不提供自動行事曆同步或提醒通知。

## 十、後續改善方向

未來可以加入行事曆整合、任務優先順序排序、截止日期提醒、匯出 CSV，以及多份公告的整合功能。

## 十一、雲端部署

本專題預計部署至 Streamlit Community Cloud。

- Repository：`115-1GAI`
- Main file path：`Midterm Mini-Project/app.py`
- API 金鑰：透過 Streamlit Cloud Secrets 設定
- 公開網址：部署完成後補上
- 雲端驗收：部署完成後執行並記錄
