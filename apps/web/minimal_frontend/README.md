## minimal_frontend

簡約版靜態前端，直接呼叫 `apps/api` 提供的 REST API。  
使用純 HTML/CSS/JS，無需額外建置工具。

### 特色

- 登入：透過 `/auth/token` 取得 Bearer Token。
- 上傳與處理音訊：呼叫 `/transcription/upload`、`/transcription/process` 並輪詢任務狀態。
- 結果預覽：讀取 `/transcription/tasks/{id}` 與 `/transcription/tasks/{id}/artifacts`，可直接下載 Markdown / PDF / TXT。
- 歷史記錄 & 詞彙管理：串接 `/transcription/history`、`/vocabulary` 系列 API。

### 使用方式

1. 啟動後端：`python run_server.py`（預設 8000）。
2. 在此目錄啟動簡單 HTTP server，例如：
   ```bash
   cd apps/web/minimal_frontend
   python -m http.server 5173
   ```
3. 使用瀏覽器開啟 `http://localhost:5173`，輸入 API 位址與帳密後即可操作。

> 若需啟用 HTTPS 或部署到 CDN，可直接將此目錄內容發佈，無需編譯流程。
