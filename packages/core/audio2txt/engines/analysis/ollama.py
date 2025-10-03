"""
Ollama LLM Analysis Engine

基於 Ollama 的 LLM 分析引擎實現
"""

import time
import uuid
from typing import Any, Dict, List, Optional

import httpx

from ...models.analysis import AnalysisResult, AnalysisStatus, AnalysisType, Solution
from ...models.transcript import Transcript
from ...utils.logger import Logger
from .base import AnalysisEngine


class OllamaAnalysisEngine(AnalysisEngine):
    """
    Ollama LLM 分析引擎

    使用 Ollama 本地 LLM 進行內容分析
    """

    def __init__(
        self,
        model_name: str = "gemma2:27b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        temperature: float = 0.7,
        logger: Optional[Logger] = None,
        **kwargs: Any,
    ):
        super().__init__(
            model_name=model_name,
            provider="ollama",
            base_url=base_url,
            logger=logger,
            **kwargs,
        )
        self.timeout = timeout
        self.temperature = temperature
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        if self._is_loaded:
            if self.logger:
                self.logger.debug("Engine already initialized")
            return

        try:
            if self.logger:
                self.logger.progress(f"Initializing Ollama engine: {self.model_name}")

            # 創建 HTTP 客戶端
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )

            # 測試連接
            response = await self.client.get("/api/tags")
            response.raise_for_status()

            self._is_loaded = True

            if self.logger:
                self.logger.success(
                    f"Ollama engine initialized: {self.model_name}",
                    base_url=self.base_url,
                )

        except Exception as e:
            self._is_loaded = False
            if self.logger:
                self.logger.error(f"Failed to initialize Ollama engine: {e}")
            raise

    async def shutdown(self) -> None:
        if self.client is not None:
            await self.client.aclose()
            self.client = None
            self._is_loaded = False

            if self.logger:
                self.logger.info("Ollama engine shutdown")

    async def analyze(
        self,
        transcript: Transcript,
        solution: Solution,
        **kwargs: Any,
    ) -> AnalysisResult:
        if not self._is_loaded or self.client is None:
            await self.initialize()

        start_time = time.time()

        try:
            if self.logger:
                self.logger.progress(
                    f"Analyzing with solution: {solution.name}",
                    type=solution.type,
                )

            # 格式化 prompt
            prompt = self._format_prompt(
                solution.prompt_template,
                transcript,
                **solution.parameters,
            )

            # 調用 LLM
            content = await self.generate(
                prompt=prompt,
                temperature=solution.parameters.get("temperature", self.temperature),
                **kwargs,
            )

            processing_time = time.time() - start_time

            # 創建分析結果
            result = AnalysisResult(
                id=f"analysis-{uuid.uuid4().hex[:8]}",
                transcript_id=transcript.id,
                solution_id=solution.id,
                solution_name=solution.name,
                type=solution.type,
                status=AnalysisStatus.COMPLETED,
                content=content,
                metadata={
                    "model": self.model_name,
                    "temperature": solution.parameters.get("temperature", self.temperature),
                },
                processing_time=processing_time,
                model_used=self.model_name,
            )

            if self.logger:
                self.logger.success(
                    f"Analysis completed: {solution.name}",
                    duration=f"{processing_time:.2f}s",
                )

            return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"Analysis failed: {e}", solution=solution.name)

            # 返回失敗結果
            return AnalysisResult(
                id=f"analysis-{uuid.uuid4().hex[:8]}",
                transcript_id=transcript.id,
                solution_id=solution.id,
                solution_name=solution.name,
                type=solution.type,
                status=AnalysisStatus.FAILED,
                content="",
                metadata={},
                processing_time=time.time() - start_time,
                model_used=self.model_name,
                error_message=str(e),
            )

    async def analyze_batch(
        self,
        transcript: Transcript,
        solutions: List[Solution],
        **kwargs: Any,
    ) -> List[AnalysisResult]:
        if self.logger:
            self.logger.info(f"Batch analyzing with {len(solutions)} solutions")

        # 順序處理（避免 Ollama 過載）
        results = []
        for solution in solutions:
            if solution.enabled:
                result = await self.analyze(transcript, solution, **kwargs)
                results.append(result)

        return results

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        if not self._is_loaded or self.client is None:
            await self.initialize()

        try:
            # 準備請求資料
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            # 調用 Ollama API
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()

            result = response.json()
            content = result["message"]["content"]

            return content

        except Exception as e:
            if self.logger:
                self.logger.error(f"LLM generation failed: {e}")
            raise
