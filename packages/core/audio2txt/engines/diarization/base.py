"""
Diarization Engine Base Class

說話人分離引擎抽象基礎類
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ...models.transcript import Speaker
from ...utils.logger import Logger


class DiarizationEngine(ABC):
    """
    說話人分離引擎抽象基礎類

    所有說話人分離引擎必須繼承此類並實現抽象方法
    """

    def __init__(
        self,
        model_name: str,
        device: str = "cuda",
        logger: Optional[Logger] = None,
        **kwargs: Any,
    ):
        """
        初始化說話人分離引擎

        Args:
            model_name: 模型名稱
            device: 運行設備 (cuda, cpu)
            logger: 日誌器實例
            **kwargs: 引擎特定參數
        """
        self.model_name = model_name
        self.device = device
        self.logger = logger
        self.config = kwargs
        self._is_loaded = False

    @abstractmethod
    async def load_model(self) -> None:
        """
        加載模型

        實現此方法以加載說話人分離模型到記憶體
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
            num_speakers: 說話人數量（可選，若已知）
            min_speakers: 最少說話人數量（可選）
            max_speakers: 最多說話人數量（可選）
            **kwargs: 額外參數

        Returns:
            Tuple[List[Speaker], List[Dict[str, Any]]]:
                - 說話人列表
                - 說話人時間戳列表，每個字典包含:
                  {
                      "start": float,  # 開始時間（秒）
                      "end": float,    # 結束時間（秒）
                      "speaker_id": str  # 說話人ID
                  }
        """
        pass

    @abstractmethod
    async def identify_speaker(
        self,
        audio_path: str | Path,
        reference_audios: Dict[str, str | Path],
        **kwargs: Any,
    ) -> Dict[str, str]:
        """
        識別說話人身份（基於參考音訊）

        Args:
            audio_path: 待識別的音訊檔案
            reference_audios: 參考音訊字典 {speaker_name: audio_path}
            **kwargs: 額外參數

        Returns:
            說話人ID映射字典 {original_speaker_id: identified_name}
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
            "is_loaded": self._is_loaded,
        }
