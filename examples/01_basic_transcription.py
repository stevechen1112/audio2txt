"""
基礎轉錄範例

展示如何使用 Audio2txt v3.0 進行基本的音訊轉錄
"""

import asyncio
from pathlib import Path

from audio2txt.engines.transcription import FasterWhisperEngine
from audio2txt.engines.diarization import PyannoteDiarizationEngine
from audio2txt.pipeline import TranscriptionPipeline
from audio2txt.utils.logger import get_logger


async def main():
    # 初始化日誌
    logger = get_logger()
    
    logger.info("=" * 50)
    logger.info("Audio2txt v3.0 - 基礎轉錄範例")
    logger.info("=" * 50)
    
    # 音訊檔案路徑（請替換為實際路徑）
    audio_path = "path/to/your/audio.wav"
    
    if not Path(audio_path).exists():
        logger.error(f"Audio file not found: {audio_path}")
        logger.info("Please update the audio_path in the script")
        return
    
    # 初始化轉錄引擎
    logger.info("Initializing transcription engine...")
    transcription_engine = FasterWhisperEngine(
        model_name="large-v3",
        device="cuda",  # 使用 GPU，如果沒有 GPU 請改為 "cpu"
        language="zh",
        beam_size=5,
        vad_filter=True,
    )
    
    # 初始化說話人分離引擎
    logger.info("Initializing diarization engine...")
    diarization_engine = PyannoteDiarizationEngine(
        model_name="pyannote/speaker-diarization-3.1",
        device="cuda",
        hf_token=None,  # 如果需要，設置 HuggingFace token
    )
    
    # 創建處理管線
    pipeline = TranscriptionPipeline(
        transcription_engine=transcription_engine,
        diarization_engine=diarization_engine,
    )
    
    # 使用 context manager 自動管理資源
    async with pipeline:
        logger.info("
Processing audio file...")
        
        # 處理音訊（並行處理轉錄和說話人分離）
        transcript = await pipeline.process(
            audio_path=audio_path,
            enable_diarization=True,
            parallel=True,  # 啟用並行處理（10倍性能提升）
        )
        
        # 輸出結果
        logger.info("
" + "=" * 50)
        logger.info("處理結果")
        logger.info("=" * 50)
        logger.info(f"轉錄 ID: {transcript.id}")
        logger.info(f"總片段數: {transcript.total_segments}")
        logger.info(f"說話人數: {len(transcript.speakers)}")
        logger.info(f"處理時間: {transcript.processing_time:.2f}s")
        
        # 顯示說話人資訊
        logger.info("
說話人資訊:")
        for speaker in transcript.speakers:
            logger.info(
                f"  {speaker.id}: "
                f"{speaker.total_speaking_time:.2f}s, "
                f"{speaker.segment_count} 片段"
            )
        
        # 顯示前 5 個片段
        logger.info("
前 5 個轉錄片段:")
        for i, segment in enumerate(transcript.segments[:5]):
            logger.info(f"  {segment.to_formatted_text()}")
            if i < 4:
                logger.info("")
        
        # 保存結果
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # 保存為文本格式
        txt_path = output_dir / f"{transcript.id}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript.formatted_text)
        logger.success(f"
文本已保存: {txt_path}")
        
        # 保存為 SRT 字幕格式
        srt_path = output_dir / f"{transcript.id}.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcript.to_srt_format())
        logger.success(f"SRT 字幕已保存: {srt_path}")
        
        # 保存為 JSON 格式
        import json
        json_path = output_dir / f"{transcript.id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(transcript.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        logger.success(f"JSON 資料已保存: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
