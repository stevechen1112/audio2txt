"""處理顧問訪視音檔 - 簡化版"""
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

    # 音檔路徑
    audio_path = Path("dataset_samples/顧問訪視1001_16k_mono.wav")

    if not audio_path.exists():
        print(f"ERROR: File not found: {audio_path}")
        return

    print("="*60)
    print(f"Processing: {audio_path.name}")
    print("="*60)

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

    # 輸出統計
    print("\n" + "="*60)
    print("PROCESSING COMPLETED!")
    print("="*60)
    print(f"Audio duration: {audio_duration:.1f}s ({audio_duration/60:.1f}min)")
    print(f"Processing time: {processing_time:.1f}s ({processing_time/60:.1f}min)")
    print(f"RTF: {rtf:.2f}x")
    print(f"Segments: {len(transcript.segments)}")
    print(f"Speakers: {len(transcript.speakers)}")

    # 保存轉錄結果到當前目錄
    txt_path = Path("顧問訪視1001_transcript.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# Audio2txt v3.0 轉錄結果\n")
        f.write(f"# 檔案: 顧問訪視1001.m4a\n")
        f.write(f"# 時長: {audio_duration:.1f}s ({audio_duration/60:.1f}min)\n")
        f.write(f"# 處理時間: {processing_time:.1f}s ({processing_time/60:.1f}min)\n")
        f.write(f"# RTF: {rtf:.2f}x\n")
        f.write(f"# 說話人數: {len(transcript.speakers)}\n\n")

        # 說話人統計
        f.write("# 說話人統計:\n")
        for speaker in transcript.speakers:
            speaking_time_min = speaker.total_speaking_time / 60
            f.write(f"# {speaker.id}: {speaking_time_min:.1f}min ({speaker.segment_count} segments)\n")

        f.write("\n" + "="*60 + "\n\n")
        f.write(transcript.formatted_text)

    print(f"\n✅ Transcript saved: {txt_path.absolute()}")

    # 保存 SRT 字幕
    srt_path = Path("顧問訪視1001_transcript.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(transcript.to_srt_format())

    print(f"✅ SRT subtitle saved: {srt_path.absolute()}")

    # 顯示說話人統計
    print("\n說話人統計:")
    for speaker in transcript.speakers:
        speaking_time_min = speaker.total_speaking_time / 60
        print(f"  {speaker.id}: {speaking_time_min:.1f}min ({speaker.segment_count} segments)")

    # 顯示前幾個片段
    print("\n前 5 個片段預覽:")
    for seg in transcript.segments[:5]:
        print(f"  {seg.to_formatted_text()}")


if __name__ == "__main__":
    asyncio.run(main())
