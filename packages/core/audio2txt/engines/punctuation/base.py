"""
Punctuation Engine Base Class

標點符號引擎抽象基礎類
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...models.transcript import Segment
from ...utils.logger import Logger


class PunctuationEngine(ABC):
    """
    標點符號引擎抽象基礎類

    所有標點符號引擎必須繼承此類並實現抽象方法
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
        初始化標點符號引擎

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

        實現此方法以加載標點符號模型到記憶體
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
    async def add_punctuation(
        self,
        text: str,
        **kwargs: Any,
    ) -> str:
        """
        為文本添加標點符號

        Args:
            text: 無標點的原始文本
            **kwargs: 引擎特定參數

        Returns:
            添加標點符號後的文本
        """
        pass

    @abstractmethod
    async def add_punctuation_batch(
        self,
        texts: List[str],
        **kwargs: Any,
    ) -> List[str]:
        """
        批次處理文本標點符號

        Args:
            texts: 無標點的原始文本列表
            **kwargs: 引擎特定參數

        Returns:
            添加標點符號後的文本列表
        """
        pass

    async def process_segments(
        self,
        segments: List[Segment],
        **kwargs: Any,
    ) -> List[Segment]:
        """
        為轉錄片段添加標點符號

        Args:
            segments: 轉錄片段列表
            **kwargs: 引擎特定參數

        Returns:
            處理後的片段列表
        """
        # 提取所有文本
        texts = [seg.text for seg in segments]
        
        # 批次處理
        punctuated_texts = await self.add_punctuation_batch(texts, **kwargs)
        
        # 更新片段
        processed_segments = []
        for seg, new_text in zip(segments, punctuated_texts):
            processed_seg = seg.model_copy()
            processed_seg.text = new_text
            processed_segments.append(processed_seg)
        
        return processed_segments

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
