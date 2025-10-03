"""簡化版處理腳本 - 確保輸出正常"""
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

    print("\n" + "="*80)
    print(f"Processing: {audio_path.name}")
    print("="*80 + "\n")

    start_time = time.time()

    # 初始化引擎
    print("[1/3] Loading Faster-Whisper engine...")
    transcription_engine = FasterWhisperEngine(
        model_name="large-v3",
        device="cuda",
        language="zh",
    )

    print("[2/3] Loading Pyannote Diarization engine...")
    diarization_engine = PyannoteDiarizationEngine(
        model_name="pyannote/speaker-diarization-3.1",
        device="cuda",
    )

    # 創建管線並處理
    print("[3/3] Processing (parallel mode)...\n")
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

    processing_time = time.time() - start_time
    audio_duration = transcript.metadata.get("duration", 0)
    rtf = processing_time / audio_duration if audio_duration > 0 else 0

    print("\n" + "="*80)
    print("✅ Processing completed!")
    print("="*80)
    print(f"Duration:        {audio_duration:.1f}s ({audio_duration/60:.1f} min)")
    print(f"Processing time: {processing_time:.1f}s ({processing_time/60:.1f} min)")
    print(f"RTF:             {rtf:.2f}x")
    print(f"Segments:        {len(transcript.segments)}")
    print(f"Speakers:        {len(transcript.speakers)}")

    # 說話人統計
    if transcript.speakers:
        print("\nSpeaker Statistics:")
        for speaker in transcript.speakers:
            speaking_time = speaker.total_speaking_time / 60
            print(f"  {speaker.id}: {speaking_time:.1f} min ({speaker.segment_count} segments)")

    # 保存輸出
    output_dir = Path("output/consultant_visit_1001")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving outputs to: {output_dir.absolute()}")

    # 1. 保存 TXT
    txt_path = output_dir / "transcript.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"# Audio2txt v3.0 - 顧問訪視1001\n")
            f.write(f"# 音檔: {audio_path.name}\n")
            f.write(f"# 時長: {audio_duration/60:.1f} 分鐘\n")
            f.write(f"# 處理時間: {processing_time/60:.1f} 分鐘\n")
            f.write(f"# RTF: {rtf:.2f}x\n")
            f.write(f"# 說話人數: {len(transcript.speakers)}\n\n")

            if transcript.speakers:
                f.write("## 說話人統計:\n")
                for speaker in transcript.speakers:
                    speaking_time = speaker.total_speaking_time / 60
                    f.write(f"  {speaker.id}: {speaking_time:.1f} 分鐘 ({speaker.segment_count} 片段)\n")

            f.write("\n" + "="*80 + "\n\n")
            f.write(transcript.formatted_text)

        print(f"  ✓ Saved: {txt_path}")
    except Exception as e:
        print(f"  ✗ Failed to save TXT: {e}")

    # 2. 保存 SRT
    srt_path = output_dir / "transcript.srt"
    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcript.to_srt_format())
        print(f"  ✓ Saved: {srt_path}")
    except Exception as e:
        print(f"  ✗ Failed to save SRT: {e}")

    # 預覽
    print("\n" + "="*80)
    print("First 5 segments:")
    print("="*80)
    for seg in transcript.segments[:5]:
        print(f"  {seg.to_formatted_text()}")

    print("\n" + "="*80)
    print(f"✅ All done! Check output folder: {output_dir.absolute()}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
