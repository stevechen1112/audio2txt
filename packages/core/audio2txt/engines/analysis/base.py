"""
Analysis Engine Base Class

內容分析引擎抽象基礎類
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...models.analysis import AnalysisResult, AnalysisType, Solution
from ...models.transcript import Transcript
from ...utils.logger import Logger


class AnalysisEngine(ABC):
    """
    內容分析引擎抽象基礎類

    所有分析引擎必須繼承此類並實現抽象方法
    """

    def __init__(
        self,
        model_name: str,
        provider: str = "ollama",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        logger: Optional[Logger] = None,
        **kwargs: Any,
    ):
        """
        初始化分析引擎

        Args:
            model_name: 模型名稱
            provider: 提供商 (ollama, openai, etc.)
            base_url: API 基礎 URL（可選）
            api_key: API 金鑰（可選）
            logger: 日誌器實例
            **kwargs: 引擎特定參數
        """
        self.model_name = model_name
        self.provider = provider
        self.base_url = base_url
        self.api_key = api_key
        self.logger = logger
        self.config = kwargs
        self._is_loaded = False

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化引擎

        實現此方法以初始化 LLM 連線或客戶端
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        關閉引擎

        實現此方法以清理資源
        """
        pass

    @abstractmethod
    async def analyze(
        self,
        transcript: Transcript,
        solution: Solution,
        **kwargs: Any,
    ) -> AnalysisResult:
        """
        分析轉錄內容

        Args:
            transcript: 轉錄實例
            solution: 分析方案配置
            **kwargs: 額外參數

        Returns:
            AnalysisResult 實例
        """
        pass

    @abstractmethod
    async def analyze_batch(
        self,
        transcript: Transcript,
        solutions: List[Solution],
        **kwargs: Any,
    ) -> List[AnalysisResult]:
        """
        批次分析轉錄內容

        Args:
            transcript: 轉錄實例
            solutions: 分析方案配置列表
            **kwargs: 額外參數

        Returns:
            AnalysisResult 列表
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        通用文本生成

        Args:
            prompt: 提示詞
            system_prompt: 系統提示詞（可選）
            temperature: 溫度參數
            max_tokens: 最大生成 token 數（可選）
            **kwargs: 額外參數

        Returns:
            生成的文本
        """
        pass

    async def __aenter__(self):
        """Context manager 進入"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager 退出"""
        await self.shutdown()

    def get_info(self) -> Dict[str, Any]:
        """
        取得引擎資訊

        Returns:
            引擎資訊字典
        """
        return {
            "engine": self.__class__.__name__,
            "model_name": self.model_name,
            "provider": self.provider,
            "is_loaded": self._is_loaded,
        }

    def _format_prompt(
        self,
        template: str,
        transcript: Transcript,
        **context: Any,
    ) -> str:
        """
        格式化提示詞模板

        Args:
            template: 提示詞模板
            transcript: 轉錄實例
            **context: 額外上下文變數

        Returns:
            格式化後的提示詞
        """
        # 準備可用變數
        variables = {
            "transcript": transcript.full_text,
            "formatted_transcript": transcript.formatted_text,
            "segments_count": transcript.total_segments,
            "speakers": [s.model_dump() for s in transcript.speakers],
            **context,
        }
        
        # 格式化模板
        try:
            return template.format(**variables)
        except KeyError as e:
            if self.logger:
                self.logger.warning(f"Missing template variable: {e}")
            return template
