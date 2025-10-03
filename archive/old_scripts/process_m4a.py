"""處理 M4A 音檔 - 顧問訪視1001"""
import asyncio
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "packages" / "core"))

from audio2txt.engines.transcription import FasterWhisperEngine
from audio2txt.engines.diarization import PyannoteDiarizationEngine
from audio2txt.pipeline import TranscriptionPipeline


async def main():
    # WAV 音檔路徑（已從 M4A 轉換）
    audio_path = Path("dataset_samples/consultant_visit_1001_16k_mono.wav")

    if not audio_path.exists():
        print(f"ERROR: File not found: {audio_path}")
        return

    print("="*80)
    print(f"Processing M4A file: {audio_path.name}")
    print("="*80)
    start_time = time.time()

    # 初始化引擎
    print("\n[1/3] Initializing Faster-Whisper engine (large-v3, CUDA)...")
    transcription_engine = FasterWhisperEngine(
        model_name="large-v3",
        device="cuda",
        language="zh",
    )

    print("[2/3] Initializing Pyannote Diarization engine (CUDA)...")
    diarization_engine = PyannoteDiarizationEngine(
        model_name="pyannote/speaker-diarization-3.1",
        device="cuda",
    )

    # 創建管線並處理
    print("[3/3] Creating transcription pipeline (parallel mode)...")
    pipeline = TranscriptionPipeline(
        transcription_engine=transcription_engine,
        diarization_engine=diarization_engine,
    )

    print("\nStarting transcription + diarization (parallel processing)...\n")
    async with pipeline:
        transcript = await pipeline.process(
            audio_path=audio_path,
            enable_diarization=True,
            parallel=True,  # 並行處理，10x 性能提升
        )

    processing_time = time.time() - start_time
    audio_duration = transcript.metadata.get("duration", 0)
    rtf = processing_time / audio_duration if audio_duration > 0 else 0

    # 顯示結果
    print("\n" + "="*80)
    print("Processing completed!")
    print("="*80)
    print(f"Audio duration:    {audio_duration:.1f}s ({audio_duration/60:.1f}min)")
    print(f"Processing time:   {processing_time:.1f}s ({processing_time/60:.1f}min)")
    print(f"RTF (Real-Time Factor): {rtf:.2f}x")
    print(f"Total segments:    {len(transcript.segments)}")
    print(f"Speakers detected: {len(transcript.speakers)}")

    # 顯示說話人統計
    if transcript.speakers:
        print("\nSpeaker Statistics:")
        for speaker in transcript.speakers:
            time_min = speaker.total_speaking_time / 60
            print(f"  {speaker.id}: {time_min:.1f}min ({speaker.segment_count} segments)")

    # 保存到 output 目錄
    output_dir = Path("output/consultant_visit_m4a")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存轉錄文本
    txt_path = output_dir / f"{audio_path.stem}_transcript.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"# Audio2txt v3.0 - {audio_path.name}\n")
            f.write(f"# Duration: {audio_duration/60:.1f}min\n")
            f.write(f"# Processing: {processing_time/60:.1f}min\n")
            f.write(f"# RTF: {rtf:.2f}x\n")
            f.write(f"# Speakers: {len(transcript.speakers)}\n\n")

            if transcript.speakers:
                f.write("## Speaker Statistics:\n")
                for speaker in transcript.speakers:
                    time_min = speaker.total_speaking_time / 60
                    f.write(f"  {speaker.id}: {time_min:.1f}min ({speaker.segment_count} segments)\n")

            f.write("\n" + "="*80 + "\n\n")
            f.write(transcript.formatted_text)

        print(f"\n✓ Transcript saved: {txt_path.absolute()}")
    except Exception as e:
        print(f"\n✗ Failed to save transcript: {e}")

    # 保存 SRT 字幕檔
    srt_path = output_dir / f"{audio_path.stem}_transcript.srt"
    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcript.to_srt_format())
        print(f"✓ SRT subtitle saved: {srt_path.absolute()}")
    except Exception as e:
        print(f"✗ Failed to save SRT: {e}")

    # 顯示前5個片段預覽
    print("\n" + "="*80)
    print("First 5 segments preview:")
    print("="*80)
    for seg in transcript.segments[:5]:
        print(f"  {seg.to_formatted_text()}")

    print("\n" + "="*80)
    print(f"All files saved to: {output_dir.absolute()}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
