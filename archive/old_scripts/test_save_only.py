"""測試：只運行處理並強制保存"""
import asyncio
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "packages" / "core"))

from audio2txt.engines.transcription import FasterWhisperEngine
from audio2txt.engines.diarization import PyannoteDiarizationEngine
from audio2txt.pipeline import TranscriptionPipeline


async def main():
    print("="*80, flush=True)
    print("開始測試", flush=True)
    print("="*80, flush=True)

    # 音檔路徑
    audio_path = Path("dataset_samples/consultant_visit_1001_16k_mono.wav")

    if not audio_path.exists():
        print(f"ERROR: 找不到音檔", flush=True)
        return

    print(f"音檔: {audio_path.name}", flush=True)
    start_time = time.time()

    # 初始化引擎
    print("初始化引擎...", flush=True)
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

    print("開始處理...", flush=True)

    try:
        async with pipeline:
            transcript = await pipeline.process(
                audio_path=audio_path,
                enable_diarization=True,
                parallel=True,
            )
        print("處理完成！", flush=True)
    except Exception as e:
        print(f"處理失敗: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return

    processing_time = time.time() - start_time
    audio_duration = transcript.metadata.get("duration", 0)

    print(f"\n片段數: {len(transcript.segments)}", flush=True)
    print(f"說話人數: {len(transcript.speakers)}", flush=True)
    print(f"處理時間: {processing_time/60:.1f} 分鐘\n", flush=True)

    # 保存
    output_dir = Path("output/test_save")
    print(f"創建輸出目錄: {output_dir}", flush=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ 目錄已創建", flush=True)

    txt_path = output_dir / "transcript.txt"
    print(f"保存到: {txt_path}", flush=True)

    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"# 測試轉錄\n")
            f.write(f"# 片段數: {len(transcript.segments)}\n")
            f.write(f"# 說話人數: {len(transcript.speakers)}\n\n")
            f.write(transcript.formatted_text)
        print(f"✓ 檔案已保存: {txt_path.absolute()}", flush=True)
    except Exception as e:
        print(f"✗ 保存失敗: {e}", flush=True)
        import traceback
        traceback.print_exc()

    print("\n完成！", flush=True)


if __name__ == "__main__":
    print("腳本開始", flush=True)
    try:
        asyncio.run(main())
        print("腳本正常結束", flush=True)
    except Exception as e:
        print(f"腳本異常: {e}", flush=True)
        import traceback
        traceback.print_exc()
