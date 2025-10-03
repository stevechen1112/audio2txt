"""測試智能摘要功能"""
import asyncio
import sys
import time
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "packages" / "core"))

from audio2txt.engines.analysis import OllamaAnalysisEngine
from audio2txt.models.analysis import Solution, AnalysisType
from audio2txt.models.transcript import Transcript, Segment, Speaker
from audio2txt.utils.logger import get_logger


async def load_solutions(yaml_path: Path) -> dict:
    """載入分析方案配置"""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


async def load_transcript_from_file(txt_path: Path) -> Transcript:
    """從現有的轉錄文件載入 Transcript 物件"""
    logger = get_logger()

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 解析轉錄文本
    segments = []
    speakers_dict = {}

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("="):
            continue

        # 解析格式: [MM:SS -> MM:SS][SPEAKER_ID]: text
        if line.startswith("["):
            try:
                # 提取時間和說話人
                first_bracket = line.index("]")
                time_str = line[1:first_bracket]

                rest = line[first_bracket + 1:]
                if rest.startswith("["):
                    second_bracket = rest.index("]")
                    speaker_id = rest[1:second_bracket]
                    text = rest[second_bracket + 2:].strip()  # 跳過 ]:

                    # 解析時間 MM:SS -> MM:SS
                    if " -> " in time_str:
                        start_str, end_str = time_str.split(" -> ")
                        start_parts = start_str.split(":")
                        end_parts = end_str.split(":")

                        start = int(start_parts[0]) * 60 + int(start_parts[1])
                        end = int(end_parts[0]) * 60 + int(end_parts[1])

                        # 創建片段
                        segment = Segment(
                            id=f"seg-{len(segments):04d}",
                            start=float(start),
                            end=float(end),
                            text=text,
                            speaker_id=speaker_id,
                            language="zh",
                        )
                        segments.append(segment)

                        # 記錄說話人
                        if speaker_id not in speakers_dict:
                            speakers_dict[speaker_id] = Speaker(
                                id=speaker_id,
                                total_speaking_time=0.0,
                                segment_count=0,
                            )

                        speakers_dict[speaker_id].total_speaking_time += (end - start)
                        speakers_dict[speaker_id].segment_count += 1

            except Exception as e:
                logger.warning(f"Failed to parse line: {line[:50]}... Error: {e}")
                continue

    speakers = list(speakers_dict.values())

    # 計算總時長
    total_duration = segments[-1].end if segments else 0

    transcript = Transcript(
        id="transcript-test",
        audio_id="audio-test",
        segments=segments,
        speakers=speakers,
        language="zh",
        processing_time=0.0,
        metadata={"duration": total_duration},
    )

    logger.info(f"Loaded transcript: {len(segments)} segments, {len(speakers)} speakers")
    return transcript


async def main():
    logger = get_logger()

    # 載入轉錄文件
    transcript_path = Path("output/quality_test/012_Tea_Coffee_16k_mono_v3_gpu.txt")
    if not transcript_path.exists():
        logger.error(f"Transcript file not found: {transcript_path}")
        return

    logger.info("=" * 60)
    logger.info("Audio2txt v3.0 - 智能摘要測試")
    logger.info("=" * 60)

    # 載入 Transcript
    logger.progress("Loading transcript...")
    transcript = await load_transcript_from_file(transcript_path)
    logger.success(f"Transcript loaded: {len(transcript.segments)} segments")

    # 載入方案配置
    solutions_path = Path("solutions.yaml")
    solutions_data = await load_solutions(solutions_path)
    logger.success(f"Loaded {len(solutions_data)} solution templates")

    # 選擇通用型摘要方案（適用於任何內容）
    solution_config = solutions_data["universal_summary"]
    solution = Solution(
        id=solution_config["id"],
        name=solution_config["name"],
        type=AnalysisType.SUMMARY,
        enabled=solution_config["enabled"],
        model=solution_config["model"],
        prompt_template=solution_config["prompt_template"],
        parameters=solution_config["parameters"],
    )

    logger.info(f"\nUsing solution: {solution.name}")
    logger.info(f"Model: {solution.model}")

    # 初始化分析引擎
    start_time = time.time()

    engine = OllamaAnalysisEngine(
        model_name="gpt-oss:20b",
        base_url="http://localhost:11434",
        logger=logger,
    )

    # 限制轉錄長度（測試用，取前 5000 字元）
    full_text = transcript.full_text
    if len(full_text) > 5000:
        logger.info(f"Truncating transcript from {len(full_text)} to 5000 characters for testing")
        transcript_sample = Transcript(
            id=transcript.id,
            audio_id=transcript.audio_id,
            segments=transcript.segments[:100],  # 前 100 個片段
            speakers=transcript.speakers,
            language=transcript.language,
            processing_time=transcript.processing_time,
            metadata=transcript.metadata,
        )
    else:
        transcript_sample = transcript

    # 執行分析
    async with engine:
        logger.progress(f"\nGenerating summary... (using {len(transcript_sample.segments)} segments)")
        result = await engine.analyze(transcript_sample, solution)

    processing_time = time.time() - start_time

    # 輸出結果
    if result.status.value == "completed":
        logger.success(f"\nSummary generated successfully!")
        logger.info(f"Processing time: {processing_time:.1f}s")
        logger.info(f"Model used: {result.model_used}")

        # 保存結果（先保存，避免終端編碼問題）
        output_path = Path("output/quality_test/012_Tea_Coffee_summary.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Audio2txt v3.0 智能摘要\n\n")
            f.write(f"**音訊檔案**: 012_Tea_Coffee_16k_mono.wav\n")
            f.write(f"**分析方案**: {solution.name}\n")
            f.write(f"**使用模型**: {result.model_used}\n")
            f.write(f"**處理時間**: {processing_time:.1f}s\n\n")
            f.write("---\n\n")
            f.write(result.content)

        logger.success(f"\nSummary saved to: {output_path}")

        # 顯示摘要預覽（限制長度避免編碼問題）
        logger.info("\n摘要預覽（前 500 字元）:")
        preview = result.content[:500] if len(result.content) > 500 else result.content
        logger.info(preview + "...")

    else:
        logger.error(f"Summary generation failed: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())