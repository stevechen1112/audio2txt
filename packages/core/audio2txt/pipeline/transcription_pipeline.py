"""
Transcription Pipeline

整合轉錄和說話人分離的完整處理管線
"""

import asyncio
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..engines.diarization.base import DiarizationEngine
from ..engines.transcription.base import TranscriptionEngine
from ..models.transcript import Segment, Speaker, Transcript
from ..utils.config import Config
from ..utils.logger import Logger, get_logger


class TranscriptionPipeline:
    """
    轉錄處理管線

    整合轉錄引擎和說話人分離引擎，提供完整的音訊轉文字功能
    """

    def __init__(
        self,
        transcription_engine: TranscriptionEngine,
        diarization_engine: Optional[DiarizationEngine] = None,
        config: Optional[Config] = None,
        logger: Optional[Logger] = None,
    ):
        self.transcription_engine = transcription_engine
        self.diarization_engine = diarization_engine
        self.config = config
        self.logger = logger or get_logger()

    async def process(
        self,
        audio_path: str | Path,
        enable_diarization: bool = True,
        num_speakers: Optional[int] = None,
        parallel: bool = True,
        **kwargs: Any,
    ) -> Transcript:
        audio_path = Path(audio_path)
        start_time = time.time()

        try:
            self.logger.progress(f"Processing audio: {audio_path.name}")

            if enable_diarization and self.diarization_engine and parallel:
                transcript = await self._process_parallel(
                    audio_path,
                    num_speakers=num_speakers,
                    **kwargs,
                )
            elif enable_diarization and self.diarization_engine:
                transcript = await self._process_sequential(
                    audio_path,
                    num_speakers=num_speakers,
                    **kwargs,
                )
            else:
                transcript = await self.transcription_engine.transcribe(
                    audio_path,
                    **kwargs,
                )

            processing_time = time.time() - start_time
            transcript.processing_time = processing_time

            self.logger.success(
                f"Processing completed: {audio_path.name}",
                segments=len(transcript.segments),
                speakers=len(transcript.speakers),
                duration=f"{processing_time:.2f}s",
            )

            return transcript

        except Exception as e:
            self.logger.error(f"Processing failed: {e}", audio=str(audio_path))
            raise

    async def _process_parallel(
        self,
        audio_path: Path,
        num_speakers: Optional[int] = None,
        **kwargs: Any,
    ) -> Transcript:
        self.logger.info("Running transcription and diarization in parallel")

        transcription_task = self.transcription_engine.transcribe(audio_path, **kwargs)
        diarization_task = self.diarization_engine.diarize(
            audio_path,
            num_speakers=num_speakers,
        )

        transcript, (speakers, timestamps) = await asyncio.gather(
            transcription_task,
            diarization_task,
        )

        transcript = self._merge_transcript_with_diarization(
            transcript,
            speakers,
            timestamps,
        )

        return transcript

    async def _process_sequential(
        self,
        audio_path: Path,
        num_speakers: Optional[int] = None,
        **kwargs: Any,
    ) -> Transcript:
        self.logger.info("Running transcription and diarization sequentially")

        transcript = await self.transcription_engine.transcribe(audio_path, **kwargs)

        speakers, timestamps = await self.diarization_engine.diarize(
            audio_path,
            num_speakers=num_speakers,
        )

        transcript = self._merge_transcript_with_diarization(
            transcript,
            speakers,
            timestamps,
        )

        return transcript

    def _merge_transcript_with_diarization(
        self,
        transcript: Transcript,
        speakers: List[Speaker],
        timestamps: List[Dict[str, Any]],
    ) -> Transcript:
        self.logger.debug("Merging transcript with diarization results")

        for segment in transcript.segments:
            best_speaker = None
            max_overlap = 0.0

            for ts in timestamps:
                overlap_start = max(segment.start, ts["start"])
                overlap_end = min(segment.end, ts["end"])
                overlap = max(0, overlap_end - overlap_start)

                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = ts["speaker_id"]

            if best_speaker and max_overlap > 0:
                segment.speaker_id = best_speaker

        transcript.speakers = speakers

        return transcript

    async def process_batch(
        self,
        audio_paths: List[str | Path],
        max_concurrent: int = 2,
        **kwargs: Any,
    ) -> List[Transcript]:
        self.logger.info(f"Processing {len(audio_paths)} audio files in batch")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(audio_path: str | Path) -> Transcript:
            async with semaphore:
                return await self.process(audio_path, **kwargs)

        tasks = [process_with_semaphore(path) for path in audio_paths]
        transcripts = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for i, result in enumerate(transcripts):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Failed to process {audio_paths[i]}: {result}"
                )
            else:
                results.append(result)

        self.logger.success(
            f"Batch processing completed: {len(results)}/{len(audio_paths)} succeeded"
        )

        return results

    async def __aenter__(self):
        await self.transcription_engine.load_model()
        if self.diarization_engine:
            await self.diarization_engine.load_model()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.transcription_engine.unload_model()
        if self.diarization_engine:
            await self.diarization_engine.unload_model()
