"""
批次處理範例

展示如何批次處理多個音訊檔案
"""

import asyncio
from pathlib import Path

from audio2txt.engines.transcription import FasterWhisperEngine
from audio2txt.engines.diarization import PyannoteDiarizationEngine
from audio2txt.pipeline import TranscriptionPipeline
from audio2txt.utils.logger import get_logger


async def main():
    logger = get_logger()
    
    logger.info("=" * 50)
    logger.info("Audio2txt v3.0 - 批次處理範例")
    logger.info("=" * 50)
    
    # 音訊檔案目錄
    audio_dir = Path("path/to/audio/folder")
    
    if not audio_dir.exists():
        logger.error(f"Audio directory not found: {audio_dir}")
        logger.info("Please update the audio_dir in the script")
        return
    
    # 查找所有音訊檔案
    audio_files = list(audio_dir.glob("*.wav")) +                   list(audio_dir.glob("*.mp3")) +                   list(audio_dir.glob("*.m4a"))
    
    if not audio_files:
        logger.error(f"No audio files found in {audio_dir}")
        return
    
    logger.info(f"Found {len(audio_files)} audio files")
    
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
    
    pipeline = TranscriptionPipeline(
        transcription_engine=transcription_engine,
        diarization_engine=diarization_engine,
    )
    
    # 批次處理
    async with pipeline:
        logger.info("
Starting batch processing...")
        
        transcripts = await pipeline.process_batch(
            audio_paths=audio_files,
            max_concurrent=2,  # 同時處理 2 個檔案
            enable_diarization=True,
            parallel=True,
        )
        
        logger.success(f"
Batch processing completed: {len(transcripts)} files")
    
    # 保存結果
    output_dir = Path("output/batch")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, transcript in enumerate(transcripts):
        # 保存文本
        txt_path = output_dir / f"{transcript.id}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"音訊檔案: {audio_files[i].name}
")
            f.write("=" * 50 + "

")
            f.write(transcript.formatted_text)
        
        # 保存 SRT
        srt_path = output_dir / f"{transcript.id}.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcript.to_srt_format())
        
        logger.info(f"Saved: {txt_path.name}")
    
    logger.success(f"
All results saved to {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
