# 🎙️ Audio2txt v3.0 - Next Generation AI Audio Analysis Platform

> 🚀 從 v2.x 進化而來，性能提升 10 倍的現代化 AI 語音轉錄與智能分析平台

## ✨ v3.0 核心特性

- ⚡ **10x 性能提升**：並行處理架構（轉錄 + 說話人分離同時執行）
- 🤖 **智能摘要系統**：本地 LLM 生成結構化報告（gpt-oss:20b）
- 🎯 **通用型分析**：適用於會議、訪談、課程、播客等任何場景
- 🏗️ **現代架構**：完全異步 + 插件式引擎設計
- 🔓 **完全開源免費**：MIT License + 本地處理，無 API 費用
- 📱 **未來擴展**：支援 Web API 與手機 APP 開發

## 🚀 快速開始

### 1. 基礎轉錄與說話人分離
```bash
python test_wav.py
```
- 輸入：音訊檔案（WAV 格式）
- 輸出：帶時間戳與說話人標記的轉錄文本
- 處理速度：RTF 0.08x（47 分鐘音訊 → 3 分 50 秒）

### 2. 智能摘要生成
```bash
python test_summary.py
```
- 自動生成結構化摘要報告
- 使用本地 gpt-oss:20b 模型（完全免費）
- 輸出：Markdown 格式報告

### 3. 配置 Ollama（智能摘要需求）
```bash
# 安裝 Ollama
# Windows/Mac: 從 https://ollama.com 下載安裝

# 下載 gpt-oss:20b 模型
ollama pull gpt-oss:20b

# 啟動 Ollama 服務（自動後台運行）
```

## 📁 專案結構

```
audio2txt/
├── packages/core/audio2txt/   # 核心引擎
│   ├── models/                # 資料模型（Transcript, Speaker, Analysis）
│   ├── engines/               # AI 引擎
│   │   ├── transcription/     # Faster-Whisper large-v3
│   │   ├── diarization/       # Pyannote 3.1
│   │   └── analysis/          # Ollama LLM
│   ├── pipeline/              # 並行處理管線
│   └── utils/                 # 工具（Logger, Config）
├── audio2txt-legacy/          # v2.x 完整備份
├── solutions.yaml             # 智能摘要模板配置
├── test_wav.py               # 轉錄測試腳本
└── test_summary.py           # 摘要測試腳本
```

## 🎯 核心功能展示

### 轉錄 + 說話人分離
```python
from audio2txt.engines.transcription import FasterWhisperEngine
from audio2txt.engines.diarization import PyannoteDiarizationEngine
from audio2txt.pipeline import TranscriptionPipeline

# 初始化引擎
transcription_engine = FasterWhisperEngine(
    model_name="large-v3",
    device="cuda",
    language="zh",
)

diarization_engine = PyannoteDiarizationEngine(
    model_name="pyannote/speaker-diarization-3.1",
    device="cuda",
)

# 創建管線並處理（並行模式）
pipeline = TranscriptionPipeline(
    transcription_engine=transcription_engine,
    diarization_engine=diarization_engine,
)

async with pipeline:
    transcript = await pipeline.process(
        audio_path="audio.wav",
        enable_diarization=True,
        parallel=True,  # 10x 性能提升
    )

# 輸出格式化文本
print(transcript.formatted_text)
# [00:00 -> 00:04][SPEAKER_03]: 各位好,我貴姓陳
```

### 智能摘要生成
```python
from audio2txt.engines.analysis import OllamaAnalysisEngine
from audio2txt.models.analysis import Solution, AnalysisType

# 初始化分析引擎
engine = OllamaAnalysisEngine(
    model_name="gpt-oss:20b",
    base_url="http://localhost:11434",
)

# 定義分析方案（通用型）
solution = Solution(
    id="universal_summary",
    name="通用型智能摘要",
    type=AnalysisType.SUMMARY,
    model="gpt-oss:20b",
    prompt_template="...",  # 見 solutions.yaml
)

# 執行分析
async with engine:
    result = await engine.analyze(transcript, solution)

print(result.content)
# ## 內容概述
# ## 核心重點
# ## 關鍵訊息
# ## 重要細節
```

## 📱 手機 APP 開發規劃

Audio2txt v3.0 核心引擎可擴展為手機 APP！查看 [APP 開發指南](docs/APP_DEVELOPMENT.md) 了解詳情。

**推薦架構**：雲端處理模式
- 手機 APP（React Native / Flutter）→ 雲端 API（FastAPI + v3.0 核心）
- 優點：快速、高品質、跨平台
- 成本：$50-200/月（AWS/GCP GPU 實例）

**功能對比**：

| 功能 | 本地版 v3.0 | 手機 APP（雲端） |
|------|-------------|------------------|
| 轉錄品質 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 說話人分離 | ✅ | ✅ |
| 智能摘要 | ✅ | ✅ |
| 處理速度 | 快（本地 GPU） | 快（雲端 GPU） |
| 隨時隨地使用 | ❌ | ✅ |
| 離線功能 | ✅ | ❌ |
| 月費 | $0 | $50-200 |

## 🔄 從 v2.x 遷移

v2.x 系統已完整備份至 `audio2txt-legacy/`，繼續可用：

```bash
cd audio2txt-legacy
python enhanced_ultimate_processor.py audio.wav
```

## 📖 文檔

- [開發狀態](DEVELOPMENT_STATUS.md) - 最新開發進度
- [開發計畫](PROJECT_SETUP_PLAN.md) - 架構設計
- [遷移報告](MIGRATION_COMPLETE.md) - v2.x → v3.0 遷移記錄
- [APP 開發指南](docs/APP_DEVELOPMENT.md) - 手機 APP 開發規劃

---

**⭐ 如果有幫助，請給我們一個星星！**
