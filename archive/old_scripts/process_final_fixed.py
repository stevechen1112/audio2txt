"""最終修正版 - 確保保存成功"""
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
        print(f"ERROR: 找不到音檔: {audio_path}")
        return

    print("\n" + "="*80)
    print(f"開始處理: {audio_path.name}")
    print("="*80 + "\n")

    start_time = time.time()

    # 初始化引擎
    print("[步驟 1/3] 載入 Faster-Whisper 引擎 (large-v3, CUDA)...")
    transcription_engine = FasterWhisperEngine(
        model_name="large-v3",
        device="cuda",
        language="zh",
    )

    print("[步驟 2/3] 載入 Pyannote 說話人分離引擎 (CUDA)...")
    diarization_engine = PyannoteDiarizationEngine(
        model_name="pyannote/speaker-diarization-3.1",
        device="cuda",
    )

    # 創建管線並處理
    print("[步驟 3/3] 開始處理（並行模式：轉錄 + 說話人分離）...\n")
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
    print("✅ 處理完成！")
    print("="*80)
    print(f"音檔長度:     {audio_duration:.1f}秒 ({audio_duration/60:.1f} 分鐘)")
    print(f"處理時間:     {processing_time:.1f}秒 ({processing_time/60:.1f} 分鐘)")
    print(f"即時係數RTF:  {rtf:.2f}x")
    print(f"總片段數:     {len(transcript.segments)}")
    print(f"說話人數:     {len(transcript.speakers)}")

    # 說話人統計
    if transcript.speakers:
        print("\n說話人統計:")
        for speaker in transcript.speakers:
            speaking_time = speaker.total_speaking_time / 60
            print(f"  {speaker.id}: {speaking_time:.1f} 分鐘 ({speaker.segment_count} 片段)")

    # 保存輸出
    output_dir = Path("output") / "consultant_visit_1001"
    print(f"\n正在建立輸出目錄: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ 輸出目錄已建立: {output_dir.absolute()}\n")

    # 1. 保存轉錄文本 (TXT)
    txt_path = output_dir / "transcript.txt"
    print(f"正在保存轉錄文本: {txt_path.name}...")
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"# Audio2txt v3.0 - 顧問訪視1001 轉錄結果\n")
            f.write(f"# 原始檔案: 顧問訪視1001.m4a\n")
            f.write(f"# 處理檔案: {audio_path.name}\n")
            f.write(f"# 音檔長度: {audio_duration/60:.1f} 分鐘\n")
            f.write(f"# 處理時間: {processing_time/60:.1f} 分鐘\n")
            f.write(f"# RTF: {rtf:.2f}x\n")
            f.write(f"# 說話人數: {len(transcript.speakers)}\n")
            f.write(f"# 片段總數: {len(transcript.segments)}\n\n")

            if transcript.speakers:
                f.write("## 說話人統計:\n")
                for speaker in transcript.speakers:
                    speaking_time = speaker.total_speaking_time / 60
                    f.write(f"  {speaker.id}: {speaking_time:.1f} 分鐘 ({speaker.segment_count} 片段)\n")

            f.write("\n" + "="*80 + "\n\n")
            f.write(transcript.formatted_text)

        print(f"  ✓ 轉錄文本已保存: {txt_path.absolute()}")
    except Exception as e:
        print(f"  ✗ 保存轉錄文本失敗: {e}")
        import traceback
        traceback.print_exc()

    # 2. 保存字幕檔 (SRT)
    srt_path = output_dir / "transcript.srt"
    print(f"正在保存字幕檔: {srt_path.name}...")
    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcript.to_srt_format())
        print(f"  ✓ 字幕檔已保存: {srt_path.absolute()}")
    except Exception as e:
        print(f"  ✗ 保存字幕檔失敗: {e}")
        import traceback
        traceback.print_exc()

    # 預覽前5個片段
    print("\n" + "="*80)
    print("前 5 個片段預覽:")
    print("="*80)
    for i, seg in enumerate(transcript.segments[:5], 1):
        print(f"{i}. {seg.to_formatted_text()}")

    print("\n" + "="*80)
    print(f"✅ 所有處理完成！")
    print(f"   輸出目錄: {output_dir.absolute()}")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ 執行失敗: {e}")
        import traceback
        traceback.print_exc()
