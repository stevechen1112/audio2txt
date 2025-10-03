"""處理顧問訪視音檔 - 修復版本（不使用async with）"""
import asyncio
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "packages" / "core"))

from audio2txt.engines.transcription import FasterWhisperEngine
from audio2txt.engines.diarization import PyannoteDiarizationEngine
from audio2txt.pipeline import TranscriptionPipeline


async def main():
    # 音檔路徑
    audio_path = Path("dataset_samples/consultant_visit_1001_16k_mono.wav")

    if not audio_path.exists():
        print(f"ERROR: File not found: {audio_path}")
        return

    print("Processing:", audio_path.name)
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

    # 手動載入模型
    await pipeline.transcription_engine.load_model()
    await pipeline.diarization_engine.load_model()

    try:
        # 處理音檔
        transcript = await pipeline.process(
            audio_path=audio_path,
            enable_diarization=True,
            parallel=True,
        )
    finally:
        # 不執行 unload_model，避免資源清理問題
        pass

    processing_time = time.time() - start_time
    audio_duration = transcript.metadata.get("duration", 0)
    rtf = processing_time / audio_duration if audio_duration > 0 else 0

    print(f"\nProcessing completed!")
    print(f"Duration: {audio_duration/60:.1f}min")
    print(f"Time: {processing_time/60:.1f}min")
    print(f"RTF: {rtf:.2f}x")
    print(f"Segments: {len(transcript.segments)}")
    print(f"Speakers: {len(transcript.speakers)}")

    # 保存到 output 目錄
    output_dir = Path("output/consultant_visit")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nSaving to: {output_dir.absolute()}")

    # 保存轉錄文本
    txt_path = output_dir / "transcript.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"# Audio2txt v3.0 - 顧問訪視1001\n")
            f.write(f"# Duration: {audio_duration/60:.1f}min\n")
            f.write(f"# Processing: {processing_time/60:.1f}min\n")
            f.write(f"# Speakers: {len(transcript.speakers)}\n\n")
            for speaker in transcript.speakers:
                time_min = speaker.total_speaking_time / 60
                f.write(f"# {speaker.id}: {time_min:.1f}min ({speaker.segment_count} segments)\n")
            f.write("\n" + "="*60 + "\n\n")
            f.write(transcript.formatted_text)
        print(f"✓ Saved: {txt_path.absolute()}")
    except Exception as e:
        print(f"✗ Failed to save transcript: {e}")

    # 保存 SRT
    srt_path = output_dir / "transcript.srt"
    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcript.to_srt_format())
        print(f"✓ Saved: {srt_path.absolute()}")
    except Exception as e:
        print(f"✗ Failed to save SRT: {e}")

    # 顯示預覽
    print("\nFirst 3 segments:")
    for seg in transcript.segments[:3]:
        print(f"  {seg.to_formatted_text()}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
