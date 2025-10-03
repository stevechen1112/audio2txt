"""
Pyannote Diarization Engine

基於 pyannote.audio 的說話人分離引擎實現
"""

import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pyannote.audio import Pipeline
from pyannote.core import Annotation

from ...models.transcript import Speaker
from ...utils.logger import Logger
from .base import DiarizationEngine


class PyannoteDiarizationEngine(DiarizationEngine):
    """
    Pyannote 說話人分離引擎

    使用 pyannote.audio 進行說話人分離和識別
    """

    def __init__(
        self,
        model_name: str = "pyannote/speaker-diarization-3.1",
        device: str = "cuda",
        hf_token: Optional[str] = None,
        logger: Optional[Logger] = None,
        **kwargs: Any,
    ):
        """
        初始化 Pyannote 說話人分離引擎

        Args:
            model_name: Pyannote 模型名稱
            device: 運行設備 (cuda, cpu)
            hf_token: HuggingFace Token (用於下載模型)
            logger: 日誌器實例
            **kwargs: 額外參數
        """
        super().__init__(
            model_name=model_name,
            device=device,
            logger=logger,
            **kwargs,
        )
        self.hf_token = hf_token
        self.pipeline: Optional[Pipeline] = None

    async def load_model(self) -> None:
        """加載 Pyannote 模型"""
        if self._is_loaded:
            if self.logger:
                self.logger.debug("Model already loaded")
            return

        try:
            if self.logger:
                self.logger.progress(
                    f"Loading Pyannote model: {self.model_name} on {self.device}"
                )

            # 加載 pipeline
            self.pipeline = Pipeline.from_pretrained(
                self.model_name,
                use_auth_token=self.hf_token,
            )

            # 移動到指定設備
            import torch
            if self.device == "cuda" and torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
            else:
                self.pipeline.to(torch.device("cpu"))

            self._is_loaded = True

            if self.logger:
                self.logger.success(
                    f"Pyannote model loaded: {self.model_name}",
                    device=self.device,
                )

        except Exception as e:
            self._is_loaded = False
            if self.logger:
                self.logger.error(f"Failed to load Pyannote model: {e}")
            raise

    async def unload_model(self) -> None:
        """卸載模型"""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            self._is_loaded = False

            if self.logger:
                self.logger.info("Pyannote model unloaded")

    async def diarize(
        self,
        audio_path: str | Path,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        **kwargs: Any,
    ) -> Tuple[List[Speaker], List[Dict[str, Any]]]:
        """
        執行說話人分離

        Args:
            audio_path: 音訊檔案路徑
            num_speakers: 說話人數量（可選）
            min_speakers: 最少說話人數量（可選）
            max_speakers: 最多說話人數量（可選）
            **kwargs: 額外參數

        Returns:
            Tuple[List[Speaker], List[Dict[str, Any]]]: 說話人列表和時間戳列表
        """
        if not self._is_loaded or self.pipeline is None:
            await self.load_model()

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        start_time = time.time()

        try:
            if self.logger:
                self.logger.progress(f"Diarizing: {audio_path.name}")

            # 準備 diarization 參數
            diarization_params = {}
            if num_speakers is not None:
                diarization_params["num_speakers"] = num_speakers
            if min_speakers is not None:
                diarization_params["min_speakers"] = min_speakers
            if max_speakers is not None:
                diarization_params["max_speakers"] = max_speakers

            # 執行 diarization
            diarization: Annotation = self.pipeline(
                str(audio_path),
                **diarization_params,
            )

            # 解析結果
            speakers_dict: Dict[str, Speaker] = {}
            timestamps: List[Dict[str, Any]] = []

            for turn, _, speaker_label in diarization.itertracks(yield_label=True):
                # speaker_label 可能是字串（如 "SPEAKER_00"）或整數
                if isinstance(speaker_label, str):
                    speaker_id = speaker_label
                else:
                    speaker_id = f"SPEAKER_{speaker_label:02d}"

                # 記錄時間戳
                timestamps.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker_id": speaker_id,
                })

                # 統計說話人資訊
                if speaker_id not in speakers_dict:
                    speakers_dict[speaker_id] = Speaker(
                        id=speaker_id,
                        name=None,
                        total_speaking_time=0.0,
                        segment_count=0,
                    )

                speakers_dict[speaker_id].total_speaking_time += turn.duration
                speakers_dict[speaker_id].segment_count += 1

            speakers = list(speakers_dict.values())
            processing_time = time.time() - start_time

            if self.logger:
                self.logger.success(
                    f"Diarization completed: {audio_path.name}",
                    speakers=len(speakers),
                    segments=len(timestamps),
                    duration=f"{processing_time:.2f}s",
                )

            return speakers, timestamps

        except Exception as e:
            if self.logger:
                self.logger.error(f"Diarization failed: {e}", audio=str(audio_path))
            raise

    async def identify_speaker(
        self,
        audio_path: str | Path,
        reference_audios: Dict[str, str | Path],
        **kwargs: Any,
    ) -> Dict[str, str]:
        """
        識別說話人身份（基於參考音訊）

        Note: 這個功能需要額外的 speaker embedding 模型
        目前先返回空映射，後續可以擴展

        Args:
            audio_path: 待識別的音訊檔案
            reference_audios: 參考音訊字典
            **kwargs: 額外參數

        Returns:
            說話人ID映射字典
        """
        if self.logger:
            self.logger.warning(
                "Speaker identification not yet implemented for Pyannote engine"
            )

        # TODO: 實現說話人識別功能
        # 可以使用 pyannote.audio 的 embedding 模型
        # 計算相似度來識別說話人

        return {}
