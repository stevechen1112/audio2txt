"""
完整管線範例

展示如何使用完整的 Audio2txt v3.0 管線：
轉錄 + 說話人分離 + 標點符號 + LLM 分析
"""

import asyncio
from pathlib import Path

from audio2txt.engines.transcription import FasterWhisperEngine
from audio2txt.engines.diarization import PyannoteDiarizationEngine
from audio2txt.engines.punctuation import BERTPunctuationEngine
from audio2txt.engines.analysis import OllamaAnalysisEngine
from audio2txt.pipeline import TranscriptionPipeline
from audio2txt.models.analysis import Solution, AnalysisType
from audio2txt.utils.logger import get_logger


async def main():
    logger = get_logger()
    
    logger.info("=" * 50)
    logger.info("Audio2txt v3.0 - 完整管線範例")
    logger.info("=" * 50)
    
    # 音訊檔案路徑
    audio_path = "path/to/your/audio.wav"
    
    if not Path(audio_path).exists():
        logger.error(f"Audio file not found: {audio_path}")
        logger.info("Please update the audio_path in the script")
        return
    
    # ==================== 步驟 1: 轉錄 + 說話人分離 ====================
    logger.info("
[步驟 1] 轉錄 + 說話人分離")
    
    transcription_engine = FasterWhisperEngine(
        model_name="large-v3",
        device="cuda",
        language="zh",
    )
    
    diarization_engine = PyannoteDiarizationEngine(
        model_name="pyannote/speaker-diarization-3.1",
        device="cuda",
    )
    
    pipeline = TranscriptionPipeline(
        transcription_engine=transcription_engine,
        diarization_engine=diarization_engine,
    )
    
    async with pipeline:
        transcript = await pipeline.process(
            audio_path=audio_path,
            enable_diarization=True,
            parallel=True,
        )
    
    logger.success(f"轉錄完成: {transcript.total_segments} 個片段")
    
    # ==================== 步驟 2: 添加標點符號 ====================
    logger.info("
[步驟 2] 添加標點符號 (BERT - 比 LLM 快 90 倍)")
    
    punctuation_engine = BERTPunctuationEngine(
        model_name="oliverguhr/fullstop-punctuation-multilang-large",
        device="cuda",
        language="zh",
        batch_size=32,
    )
    
    async with punctuation_engine:
        # 批次處理所有片段
        punctuated_segments = await punctuation_engine.process_segments(
            transcript.segments
        )
        transcript.segments = punctuated_segments
    
    logger.success(f"標點符號添加完成")
    
    # ==================== 步驟 3: LLM 內容分析 ====================
    logger.info("
[步驟 3] LLM 內容分析")
    
    analysis_engine = OllamaAnalysisEngine(
        model_name="gemma2:27b",
        base_url="http://localhost:11434",
        temperature=0.7,
    )
    
    # 定義分析方案
    solutions = [
        Solution(
            id="quick_summary",
            name="快速摘要",
            type=AnalysisType.SUMMARY,
            enabled=True,
            model="gemma2:27b",
            prompt_template="""請為以下會議內容生成一個簡潔的摘要（200字以內）：

{transcript}

請提供：
1. 會議主題
2. 關鍵討論要點（3-5點）
3. 主要結論
""",
            parameters={"max_length": 300, "temperature": 0.7},
        ),
        Solution(
            id="action_items",
            name="待辦事項提取",
            type=AnalysisType.ACTION_ITEMS,
            enabled=True,
            model="gemma2:27b",
            prompt_template="""請從以下會議內容中提取所有待辦事項和行動項目：

{transcript}

請以清單格式列出：
- 任務描述
- 負責人（如果提到）
- 截止時間（如果提到）
""",
            parameters={"temperature": 0.5},
        ),
        Solution(
            id="keywords",
            name="關鍵詞提取",
            type=AnalysisType.KEYWORDS,
            enabled=True,
            model="gemma2:9b",  # 使用較小的模型更快
            prompt_template="""請從以下內容中提取 10 個最重要的關鍵詞：

{transcript}

只需列出關鍵詞，用逗號分隔。
""",
            parameters={"temperature": 0.3},
        ),
    ]
    
    async with analysis_engine:
        # 批次分析
        analysis_results = await analysis_engine.analyze_batch(
            transcript=transcript,
            solutions=solutions,
        )
    
    # ==================== 輸出結果 ====================
    logger.info("
" + "=" * 50)
    logger.info("處理結果")
    logger.info("=" * 50)
    
    # 顯示分析結果
    for result in analysis_results:
        logger.info(f"
[{result.solution_name}]
{result.content}")
        logger.info(f"處理時間: {result.processing_time:.2f}s")
    
    # 保存完整結果
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 保存轉錄文本
    txt_path = output_dir / f"{transcript.id}_transcript.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(transcript.formatted_text)
    logger.success(f"
轉錄文本已保存: {txt_path}")
    
    # 保存分析結果
    for result in analysis_results:
        analysis_path = output_dir / f"{transcript.id}_{result.solution_id}.txt"
        with open(analysis_path, "w", encoding="utf-8") as f:
            f.write(f"{result.solution_name}
")
            f.write("=" * 50 + "

")
            f.write(result.content)
        logger.success(f"分析結果已保存: {analysis_path}")
    
    # 保存完整 JSON
    import json
    json_path = output_dir / f"{transcript.id}_complete.json"
    complete_data = {
        "transcript": transcript.model_dump(),
        "analysis_results": [r.model_dump() for r in analysis_results],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(complete_data, f, ensure_ascii=False, indent=2, default=str)
    logger.success(f"完整資料已保存: {json_path}")
    
    logger.info("
" + "=" * 50)
    logger.success("處理完成！")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
