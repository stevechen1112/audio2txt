# 🎙️ Audio2txt v4.0 Enterprise

> 企業級雲端 AI 音訊轉文字與智能摘要平台

[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](https://github.com/stevechen1112/audio2txt)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AI](https://img.shields.io/badge/AI-AssemblyAI%20%2B%20GPT--5%20nano-orange.svg)](GPT5_NANO_INTEGRATION.md)

---

## ✨ 核心特色

- 🎯 **極致準確**：AssemblyAI 業界領先的中文語音辨識
- 👥 **智能分離**：自動識別並標記多位說話者
- 🤖 **GPT-5 nano**：高品質繁體中文摘要，超低成本
- ⚖️ **專業模板**：法律諮詢、客戶訪談、決策會議等多種場景
- 🌐 **Web 介面**：零技術門檻，開箱即用
- 📊 **完整記錄**：自動儲存歷史，隨時查詢

---

## 🚀 快速開始

### 1. 啟動後端（運算中心）

```powershell
python run_server.py
```

### 2. 啟動前端（會議室端）

```powershell
python -m streamlit run apps/web/app.py
```

### 3. 開始使用

1. 瀏覽器訪問 `http://localhost:8501`
2. 選擇場景模板（法律諮詢/客戶訪談/決策會議）
3. 錄音或上傳音訊檔
4. 點擊「🚀 開始處理」
5. 等待 5-10 分鐘，獲得專業報告

**預設帳號：** `admin` / `password123`

---

## 📖 完整文檔

- [📋 開發計畫](PLAN_v4_ENTERPRISE.md) - 系統架構與功能規劃
- [🤖 GPT-5 nano 整合](GPT5_NANO_INTEGRATION.md) - 中文摘要引擎詳細說明

---

## 🏗️ 系統架構

```
客戶端 (Web 瀏覽器)
    │
    │ HTTP/HTTPS
    ▼
FastAPI 後端服務
    │
    ├─► AssemblyAI API (雲端)
    │   ├── 語音轉文字 (中文優化)
    │   └── 說話者分離 (Diarization)
    │
    ├─► OpenAI GPT-5 nano (雲端)
    │   └── 繁體中文摘要生成
    │
    └─► SQLite (本地資料庫)
        └── 任務記錄與詞彙管理
```

**優勢：**
- ✅ 無需 GPU 硬體投資
- ✅ 即開即用，部署簡單
- ✅ 彈性擴展，按量付費
- ✅ API 自動更新，享受最新技術

---

## 🎯 適用場景

| 場景 | 模板 | 輸出重點 |
|------|------|----------|
| 法律諮詢 | `legal_consultation` | 案件背景、爭議點、法律建議 |
| 客戶訪談 | `client_interview` | 痛點、需求清單、預算限制 |
| 決策會議 | `executive_meeting` | 決議事項、待辦事項、負責人 |
| 一般會議 | `meeting_minutes` | 討論摘要、結論、下次會議 |

---

## 📊 效能與成本

### 效能指標
- **處理速度**：約 5-8 分鐘/小時音訊
- **實測案例**：48.7 分鐘音訊 → 6 分鐘處理
- **說話人識別**：自動區分 10+ 位發言者
- **支援格式**：WAV, M4A, MP3, MP4, AAC, FLAC, OGG
- **中文準確率**：95%+ (AssemblyAI 中文優化)

### 成本分析 (每小時音訊)
| 服務 | 用途 | 成本 |
|------|------|------|
| AssemblyAI | 轉錄 + 說話者分離 | ~$1.20 |
| GPT-5 nano | 中文摘要生成 | ~$0.03 |
| **總計** | | **~$1.23** |

**對比：**
- PLAUD NOTE: $9.9/月 (僅 300 分鐘，超過另計)
- Audio2txt: 按實際使用量付費，無月費

---

## 🆚 競品對比

| 特性 | Audio2txt v4.0 | PLAUD NOTE | Rev.ai | Otter.ai |
|------|----------------|------------|--------|----------|
| 中文支援 | ✅ 優秀 | ✅ 良好 | ⚠️ 一般 | ⚠️ 一般 |
| 說話者分離 | ✅ 自動 | ✅ 自動 | ✅ 自動 | ✅ 自動 |
| 中文摘要 | ✅ GPT-5 nano | ⚠️ 英文為主 | ❌ 無 | ⚠️ 英文為主 |
| 專業模板 | ✅ 5+ 種 | ⚠️ 固定 | ❌ 無 | ⚠️ 固定 |
| 成本模式 | 💰 按用量 | 💰 月費 $9.9 | 💰 按分鐘 | 💰 月費 $16.99 |
| 私有部署 | ✅ 支援 | ❌ SaaS only | ❌ SaaS only | ❌ SaaS only |
| API 整合 | ✅ 完整 API | ⚠️ 有限 | ✅ 完整 API | ✅ 完整 API |

**Audio2txt 優勢：**
- ✅ 專為繁體中文優化
- ✅ 靈活的專業模板系統
- ✅ 可私有部署，數據可控
- ✅ 按實際用量付費，無月費綁定

---

## 🛠️ 技術堆疊

### 後端框架
- **FastAPI**: 高效能 API 服務
- **SQLite**: 輕量級資料庫
- **Celery** (可選): 非同步任務處理

### 前端界面
- **Streamlit**: 快速 Web UI 開發
- **JavaScript**: 互動功能增強

### AI 服務
- **AssemblyAI**: 
  - Universal-1 模型 (中文優化)
  - Speaker Diarization (說話者分離)
  - Vocabulary Boost (詞彙增強)
  
- **OpenAI GPT-5 nano**:
  - 繁體中文摘要生成
  - 多種專業模板
  - 超低成本 ($0.05/1M input tokens)

### 安全認證
- HTTP Basic Auth
- JWT Token
- API Key 管理

---

## 📝 授權

MIT License - 完全開源免費

---

## 💡 配置需求

### 最低需求
- Python 3.10+
- 512MB RAM (API 模式)
- 網路連線 (存取雲端 API)

### API Keys
1. **AssemblyAI API Key**: [免費註冊](https://www.assemblyai.com/)
   - 每月免費額度: 3 小時轉錄
   
2. **OpenAI API Key**: [申請連結](https://platform.openai.com/)
   - 新用戶贈送: $5 免費額度 (約 5000 分鐘摘要)

---

## 🙏 致謝

- [AssemblyAI](https://www.assemblyai.com/) - 領先的語音辨識 API
- [OpenAI](https://openai.com/) - GPT-5 nano 語言模型
- [FastAPI](https://fastapi.tiangolo.com/) - 現代化 Web 框架
- [Streamlit](https://streamlit.io/) - 快速 UI 開發工具

---

**⭐ 如果這個專案對您有幫助，請給我們一個星星！**
