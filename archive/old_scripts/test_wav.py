"""測試 WAV 檔案 - GPU 模式"""
import asyncio
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "packages" / "core"))

from audio2txt.engines.transcription import FasterWhisperEngine
from audio2txt.engines.diarization import PyannoteDiarizationEngine
from audio2txt.pipeline import TranscriptionPipeline
from audio2txt.utils.logger import get_logger


async def main():
    logger = get_logger()
    
    # 測試檔案
    audio_path = Path("audio2txt-legacy/dataset_samples/012_Tea_Coffee_16k_mono.wav")
    output_dir = Path("output/quality_test")
    
    if not audio_path.exists():
        logger.error(f"File not found: {audio_path}")
        return
    
    logger.info("="*60)
    logger.info(f"Testing: {audio_path.name}")
    logger.info("="*60)
    
    start_time = time.time()
    
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
    
    # 創建管線
    pipeline = TranscriptionPipeline(
        transcription_engine=transcription_engine,
        diarization_engine=diarization_engine,
    )
    
    # 處理
    async with pipeline:
        transcript = await pipeline.process(
            audio_path=audio_path,
            enable_diarization=True,
            parallel=True,
        )
    
    processing_time = time.time() - start_time
    audio_duration = transcript.metadata.get("duration", 0)
    rtf = processing_time / audio_duration if audio_duration > 0 else 0
    
    # 輸出結果
    logger.success("Processing completed!")
    logger.info(f"  Audio duration: {audio_duration:.1f}s ({audio_duration/60:.1f}min)")
    logger.info(f"  Processing time: {processing_time:.1f}s ({processing_time/60:.1f}min)")
    logger.info(f"  RTF: {rtf:.2f}x")
    logger.info(f"  Segments: {len(transcript.segments)}")
    logger.info(f"  Speakers: {len(transcript.speakers)}")
    
    # 保存
    output_dir.mkdir(parents=True, exist_ok=True)
    txt_path = output_dir / f"{audio_path.stem}_v3_gpu.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# Audio2txt v3.0 Output (GPU mode)\n")
        f.write(f"# File: {audio_path.name}\n")
        f.write(f"# Duration: {audio_duration:.1f}s\n")
        f.write(f"# Processing time: {processing_time:.1f}s\n")
        f.write(f"# RTF: {rtf:.2f}x\n")
        f.write(f"# Speakers: {len(transcript.speakers)}\n")
        f.write("="*60 + "\n\n")
        f.write(transcript.formatted_text)
    
    logger.success(f"Saved: {txt_path}")
    
    # 顯示前幾個片段
    logger.info("\nFirst 3 segments:")
    for seg in transcript.segments[:3]:
        logger.info(f"  {seg.to_formatted_text()}")


if __name__ == "__main__":
    asyncio.run(main())
