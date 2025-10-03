# Audio2txt v3.0 範例

本目錄包含 Audio2txt v3.0 的使用範例。

## 範例列表

### 1. 基礎轉錄 (01_basic_transcription.py)
- Faster-Whisper 語音轉錄
- Pyannote 說話人分離
- 並行處理（10倍性能提升）
- 多格式輸出（TXT, SRT, JSON）

### 2. 完整管線 (02_full_pipeline.py)
- 轉錄 + 說話人分離
- BERT 標點符號（比 LLM 快 90 倍）
- Ollama LLM 內容分析
  - 快速摘要
  - 待辦事項提取
  - 關鍵詞提取

### 3. 批次處理 (03_batch_processing.py)
- 批次處理多個音訊檔案
- 並發處理
- 自動保存結果

## 快速開始

1. 修改範例中的音訊路徑
2. 根據需要調整配置（GPU/CPU、模型大小等）
3. 運行範例

```bash
python 01_basic_transcription.py
```

## 注意事項

- 首次運行會下載所需模型
- 如無 GPU，請將 device="cuda" 改為 device="cpu"
- Ollama 範例需要先啟動 Ollama 服務

詳細說明請參閱主專案 README。
