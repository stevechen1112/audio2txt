"""
Transcription Engine Base Class

語音轉錄引擎抽象基礎類
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...models.transcript import Segment, Transcript
from ...utils.logger import Logger


class TranscriptionEngine(ABC):
    """
    語音轉錄引擎抽象基礎類

    所有轉錄引擎必須繼承此類並實現抽象方法
    """

    def __init__(
        self,
        model_name: str,
        device: str = "cuda",
        language: str = "zh",
        logger: Optional[Logger] = None,
        **kwargs: Any,
    ):
        """
        初始化轉錄引擎

        Args:
            model_name: 模型名稱
            device: 運行設備 (cuda, cpu)
            language: 語言代碼
            logger: 日誌器實例
            **kwargs: 引擎特定參數
        """
        self.model_name = model_name
        self.device = device
        self.language = language
        self.logger = logger
        self.config = kwargs
        self._is_loaded = False

    @abstractmethod
    async def load_model(self) -> None:
        """
        加載模型

        實現此方法以加載轉錄模型到記憶體
        """
        pass

    @abstractmethod
    async def unload_model(self) -> None:
        """
        卸載模型

        實現此方法以釋放模型記憶體
        """
        pass

    @abstractmethod
    async def transcribe(
        self,
        audio_path: str | Path,
        **kwargs: Any,
    ) -> Transcript:
        """
        轉錄音訊檔案

        Args:
            audio_path: 音訊檔案路徑
            **kwargs: 轉錄參數（如 beam_size, temperature 等）

        Returns:
            Transcript 實例
        """
        pass

    @abstractmethod
    async def transcribe_segment(
        self,
        audio_path: str | Path,
        start: float,
        end: float,
        **kwargs: Any,
    ) -> List[Segment]:
        """
        轉錄音訊片段

        Args:
            audio_path: 音訊檔案路徑
            start: 開始時間（秒）
            end: 結束時間（秒）
            **kwargs: 轉錄參數

        Returns:
            Segment 列表
        """
        pass

    async def __aenter__(self):
        """Context manager 進入"""
        await self.load_model()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager 退出"""
        await self.unload_model()

    def get_info(self) -> Dict[str, Any]:
        """
        取得引擎資訊

        Returns:
            引擎資訊字典
        """
        return {
            "engine": self.__class__.__name__,
            "model_name": self.model_name,
            "device": self.device,
            "language": self.language,
            "is_loaded": self._is_loaded,
        }
