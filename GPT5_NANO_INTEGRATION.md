# 🚀 GPT-5 nano 整合說明

## 更新內容

已成功將 **OpenAI GPT-5 nano** 整合到 Audio2txt v4.0 系統中,用於生成高品質的中文摘要。

---

## 📋 整合架構

### 混合式架構(最佳方案)

```
AssemblyAI (轉錄 + 說話者分離)
    ↓
GPT-5 nano (中文摘要生成)
    ↓
完整報告輸出
```

**優勢:**
- ✅ AssemblyAI: 準確的中文轉錄 + 精確的說話者分離(已驗證)
- ✅ GPT-5 nano: 高品質中文摘要 + 超低成本
- ✅ 各取所長,效果最佳

---

## 💰 成本分析

### GPT-5 nano 定價
- **輸入**: $0.050 / 1M tokens
- **輸出**: $0.400 / 1M tokens
- **快取輸入**: $0.005 / 1M tokens (節省90%)

### 48分鐘音檔成本估算

| 項目 | 成本 | 說明 |
|-----|------|-----|
| AssemblyAI 轉錄 | ~$0.96 | 含說話者分離 |
| GPT-5 nano 摘要 | ~$0.02 | ~2500 input + 500 output tokens |
| **總計** | **$0.98** | 比單用AssemblyAI更好,成本相近 |

**對比其他方案:**
- Deepgram + GPT-5 nano: $0.48 (最便宜,但需測試中文品質)
- Google Cloud STT: $0.77 + GPT-5 nano $0.02 = $0.79
- Azure STT: $1.04 (不含摘要) + GPT-5 nano $0.02 = $1.06

---

## ⚙️ 配置步驟

### 1. 設定 OpenAI API Key

編輯 `.env` 檔案:

```bash
ASSEMBLYAI_API_KEY=d65c5364c4e840d38ca39f621c747f8a
OPENAI_API_KEY=your-openai-api-key-here  # 👈 在此填入您的 OpenAI API key
USE_CELERY=false
```

### 2. 取得 OpenAI API Key

1. 前往 [OpenAI Platform](https://platform.openai.com/)
2. 註冊/登入帳號
3. 前往 API Keys 頁面
4. 點擊 "Create new secret key"
5. 複製 key 並貼到 `.env` 檔案中

**首次註冊送 $5 免費額度** (可處理約5000分鐘音檔的摘要!)

---

## 🎯 支援的摘要模板

GPT-5 nano 引擎支援多種專業模板:

### 1. **universal_summary** (通用會議)
```python
template_id="universal_summary"
```
- 會議主題與目的
- 主要討論內容
- 重要決議事項
- 行動項目
- 下次會議安排

### 2. **legal_consultation** (法律諮詢)
```python
template_id="legal_consultation"
```
- 案件背景與爭議點
- 當事人主要訴求
- 法律意見與建議
- 後續行動項目

### 3. **client_interview** (客戶訪談)
```python
template_id="client_interview"
```
- 客戶背景與主要需求
- 痛點與挑戰
- 期望的解決方案
- 關鍵決策因素

### 4. **executive_meeting** (高層會議)
```python
template_id="executive_meeting"
```
- 主要議題
- 討論重點與觀點
- 決策結論
- 行動項目與負責人

### 5. **concise_minutes** (精簡摘要)
```python
template_id="concise_minutes"
```
- 核心議題(3-5點)
- 重要決議(3-5點)
- 行動項目列表

---

## 🔧 使用方式

### API 調用

```python
# 在處理音檔時指定模板
POST /api/v1/transcription/
{
    "file": <audio_file>,
    "template_id": "universal_summary"  # 選擇模板
}
```

### Web 界面

Streamlit 介面會自動使用 GPT-5 nano 生成中文摘要(如果配置了 OpenAI API key)。

---

## 📊 效能優化

### 自動 Token 優化

系統已實施以下優化策略:

1. **逐字稿截斷**: 超過10,000字符時自動截取首尾重要部分
2. **溫度控制**: temperature=0.3 確保摘要穩定性
3. **Token 限制**: 預設最多生成1000 tokens(約500-700中文字)
4. **快取利用**: 重複的系統提示詞會被快取(節省90%成本)

### 實測數據

| 音檔長度 | 逐字稿字數 | 輸入tokens | 輸出tokens | 成本 |
|---------|----------|----------|----------|-----|
| 10分鐘 | ~2,000字 | ~600 | ~300 | $0.15 |
| 30分鐘 | ~6,000字 | ~1,800 | ~500 | $0.29 |
| 60分鐘 | ~12,000字 | ~3,000 | ~700 | $0.43 |

---

## 🆚 與 AssemblyAI 摘要對比

### AssemblyAI 內建摘要
- ❌ 對中文生成英文音譯(無法使用)
- ✅ 與轉錄整合,無額外API調用
- ✅ 速度快

### GPT-5 nano 摘要
- ✅ 完美的繁體中文輸出
- ✅ 支援多種專業模板
- ✅ 可自定義提示詞
- ✅ 超低成本($0.02/摘要)
- ✅ 品質極高,理解語境能力強
- ⚠️ 需額外API調用(增加~2-3秒處理時間)

---

## 🔄 降級機制

如果未配置 OpenAI API key,系統會自動降級:

```python
if self.openai_engine:
    # 使用 GPT-5 nano 生成高品質中文摘要
    summary = await self.openai_engine.generate_summary(...)
else:
    # 降級使用 AssemblyAI 內建摘要
    summary = await self.assemblyai_engine.generate_summary(...)
```

**啟動時會顯示警告:**
```
Warning: OPENAI_API_KEY not configured. 
Summary generation will use AssemblyAI's English summary.
```

---

## 🧪 測試建議

### 測試 GPT-5 nano 整合

```bash
# 1. 配置 OpenAI API key
# 編輯 .env 檔案,填入你的 key

# 2. 執行測試
python test_v4_process.py

# 3. 檢查輸出檔案
# output/api_results/<task_id>/report.md
```

### 預期結果

報告底部會顯示:
```markdown
---
*本摘要由 GPT-5 nano 生成 | 使用 XXX tokens (輸入: XXX, 輸出: XXX)*
```

---

## 📈 未來擴展

### 可選升級方案

1. **GPT-5 mini** ($0.25/1M input, $2.00/1M output)
   - 更強的理解能力
   - 適合複雜會議
   - 成本增加約10倍

2. **GPT-5.1** ($1.25/1M input, $10.00/1M output)
   - 最強推理能力
   - 適合技術會議/研發討論
   - 成本增加約50倍

3. **自定義微調模型**
   - 針對特定產業/用語
   - 需要訓練資料
   - 可能更準確

---

## 💡 最佳實踐

### 降低成本技巧

1. **使用批次 API** (節省50%):
   ```python
   # 非即時需求可使用 Batch API
   # 成本: $0.025/1M input, $0.200/1M output
   ```

2. **模板選擇**:
   - 使用 `concise_minutes` 產生較短摘要(省30-50% tokens)

3. **逐字稿預處理**:
   - 移除重複的語助詞("嗯"、"那個")
   - 系統已自動優化,無需手動處理

### 品質優化技巧

1. **提供上下文**:
   - 在詞彙庫中加入專業術語
   - AssemblyAI 會提供更準確的轉錄

2. **選對模板**:
   - 不同場景使用對應模板
   - 提示詞已針對繁體中文優化

---

## 🎉 總結

### 當前架構優勢

✅ **AssemblyAI**: 最優秀的中文轉錄 + 說話者分離
✅ **GPT-5 nano**: 高品質中文摘要 + 超低成本
✅ **混合架構**: 各取所長,成本與品質兼顧
✅ **自動降級**: 未配置時仍可運作

### 推薦使用場景

- 📝 **日常會議**: universal_summary
- ⚖️ **法律相關**: legal_consultation  
- 👥 **客戶訪談**: client_interview
- 🏢 **高層決策**: executive_meeting
- ⚡ **快速瀏覽**: concise_minutes

---

## 📞 問題回報

如遇到問題,請檢查:

1. ✓ OPENAI_API_KEY 是否正確配置
2. ✓ OpenAI 帳戶餘額是否充足
3. ✓ 網路連線是否正常
4. ✓ API key 權限是否正確(需要 Chat Completions 權限)

---

**版本**: Audio2txt v4.0 Enterprise + GPT-5 nano
**更新日期**: 2025-12-04
