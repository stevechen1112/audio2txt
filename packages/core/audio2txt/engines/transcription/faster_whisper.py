"""
Faster-Whisper Transcription Engine

基於 faster-whisper 的語音轉錄引擎實現
"""

import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from faster_whisper import WhisperModel

from ...models.audio import Audio, AudioMetadata
from ...models.transcript import Segment, Transcript
from ...utils.logger import Logger
from .base import TranscriptionEngine


class FasterWhisperEngine(TranscriptionEngine):
    """
    Faster-Whisper 轉錄引擎

    使用 CTranslate2 優化的 Whisper 模型進行語音轉錄
    """

    def __init__(
        self,
        model_name: str = "large-v3",
        device: str = "cuda",
        language: str = "zh",
        compute_type: str = "float16",
        beam_size: int = 5,
        vad_filter: bool = True,
        vad_parameters: Optional[Dict[str, Any]] = None,
        logger: Optional[Logger] = None,
        **kwargs: Any,
    ):
        """
        初始化 Faster-Whisper 引擎

        Args:
            model_name: Whisper 模型名稱 (tiny, base, small, medium, large-v2, large-v3)
            device: 運行設備 (cuda, cpu)
            language: 語言代碼
            compute_type: 計算精度 (float16, int8, int8_float16)
            beam_size: Beam search 大小
            vad_filter: 是否啟用 VAD 過濾
            vad_parameters: VAD 參數配置
            logger: 日誌器實例
            **kwargs: 額外參數
        """
        super().__init__(
            model_name=model_name,
            device=device,
            language=language,
            logger=logger,
            **kwargs,
        )
        self.compute_type = compute_type
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self.vad_parameters = vad_parameters or {}
        self.model: Optional[WhisperModel] = None

    async def load_model(self) -> None:
        """加載 Faster-Whisper 模型"""
        if self._is_loaded:
            if self.logger:
                self.logger.debug("Model already loaded")
            return

        try:
            if self.logger:
                self.logger.progress(
                    f"Loading Faster-Whisper model: {self.model_name} on {self.device}"
                )

            # 加載模型（同步操作，但在實際應用中可以用 asyncio.to_thread 包裝）
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )

            self._is_loaded = True

            if self.logger:
                self.logger.success(
                    f"Faster-Whisper model loaded: {self.model_name}",
                    device=self.device,
                    compute_type=self.compute_type,
                )

        except Exception as e:
            self._is_loaded = False
            if self.logger:
                self.logger.error(f"Failed to load Faster-Whisper model: {e}")
            raise

    async def unload_model(self) -> None:
        """卸載模型"""
        if self.model is not None:
            del self.model
            self.model = None
            self._is_loaded = False

            if self.logger:
                self.logger.info("Faster-Whisper model unloaded")

    async def transcribe(
        self,
        audio_path: str | Path,
        **kwargs: Any,
    ) -> Transcript:
        """
        轉錄音訊檔案

        Args:
            audio_path: 音訊檔案路徑
            **kwargs: 轉錄參數覆蓋

        Returns:
            Transcript 實例
        """
        if not self._is_loaded or self.model is None:
            await self.load_model()

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        start_time = time.time()

        try:
            if self.logger:
                self.logger.progress(f"Transcribing: {audio_path.name}")

            # 準備轉錄參數
            transcribe_params = {
                "language": kwargs.get("language", self.language),
                "beam_size": kwargs.get("beam_size", self.beam_size),
                "vad_filter": kwargs.get("vad_filter", self.vad_filter),
                "vad_parameters": kwargs.get("vad_parameters", self.vad_parameters),
            }

            # 執行轉錄
            segments_iter, info = self.model.transcribe(
                str(audio_path),
                **transcribe_params,
            )

            # 轉換片段
            segments = []
            for idx, seg in enumerate(segments_iter):
                segment = Segment(
                    id=f"seg-{uuid.uuid4().hex[:8]}",
                    start=seg.start,
                    end=seg.end,
                    text=seg.text.strip(),
                    speaker_id=None,  # 需要後續 diarization
                    confidence=seg.avg_logprob if hasattr(seg, "avg_logprob") else None,
                    language=info.language,
                )
                segments.append(segment)

            processing_time = time.time() - start_time

            # 創建 Transcript 實例
            transcript = Transcript(
                id=f"transcript-{uuid.uuid4().hex[:8]}",
                audio_id=audio_path.stem,
                segments=segments,
                speakers=[],  # 需要後續 diarization
                language=info.language,
                processing_time=processing_time,
                metadata={
                    "model": self.model_name,
                    "device": self.device,
                    "compute_type": self.compute_type,
                    "duration": info.duration,
                    "language_probability": info.language_probability,
                },
            )

            if self.logger:
                self.logger.success(
                    f"Transcription completed: {audio_path.name}",
                    segments=len(segments),
                    duration=f"{processing_time:.2f}s",
                )

            return transcript

        except Exception as e:
            if self.logger:
                self.logger.error(f"Transcription failed: {e}", audio=str(audio_path))
            raise

    async def transcribe_segment(
        self,
        audio_path: str | Path,
        start: float,
        end: float,
        **kwargs: Any,
    ) -> List[Segment]:
        """
        轉錄音訊片段

        Note: Faster-Whisper 不直接支援片段轉錄，
        此方法會轉錄整個檔案然後過濾指定時間範圍

        Args:
            audio_path: 音訊檔案路徑
            start: 開始時間（秒）
            end: 結束時間（秒）
            **kwargs: 轉錄參數

        Returns:
            Segment 列表
        """
        transcript = await self.transcribe(audio_path, **kwargs)

        # 過濾指定時間範圍的片段
        filtered_segments = [
            seg
            for seg in transcript.segments
            if (seg.start >= start and seg.end <= end)
            or (seg.start <= start <= seg.end)
            or (seg.start <= end <= seg.end)
        ]

        return filtered_segments
