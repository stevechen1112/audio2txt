"""
Analysis data models

定義分析結果相關的資料結構
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    """分析類型枚舉"""

    SUMMARY = "summary"  # 摘要
    DEEP_ANALYSIS = "deep_analysis"  # 深度分析
    ACTION_ITEMS = "action_items"  # 待辦事項
    KEYWORDS = "keywords"  # 關鍵詞
    SENTIMENT = "sentiment"  # 情感分析
    MIND_MAP = "mind_map"  # 思維導圖
    CUSTOM = "custom"  # 自訂


class AnalysisStatus(str, Enum):
    """分析狀態"""

    PENDING = "pending"  # 待處理
    PROCESSING = "processing"  # 處理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失敗


class Solution(BaseModel):
    """分析方案配置"""

    id: str = Field(..., description="方案識別碼")
    name: str = Field(..., description="方案名稱")
    type: AnalysisType = Field(..., description="分析類型")
    enabled: bool = Field(True, description="是否啟用")
    model: str = Field("default", description="使用的模型名稱")
    prompt_template: str = Field(..., description="Prompt 模板")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="額外參數")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "quick_summary",
                    "name": "快速摘要",
                    "type": "summary",
                    "enabled": True,
                    "model": "gemma2:9b",
                    "prompt_template": "請為以下內容生成摘要：\n{transcript}",
                    "parameters": {"max_length": 300},
                }
            ]
        }
    }


class AnalysisResult(BaseModel):
    """分析結果模型"""

    id: str = Field(..., description="結果識別碼")
    transcript_id: str = Field(..., description="關聯的轉錄識別碼")
    solution_id: str = Field(..., description="使用的分析方案識別碼")
    solution_name: str = Field(..., description="分析方案名稱")
    type: AnalysisType = Field(..., description="分析類型")
    status: AnalysisStatus = Field(AnalysisStatus.COMPLETED, description="分析狀態")
    content: str = Field(..., description="分析結果內容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外元資料")
    processing_time: float = Field(..., description="處理時間（秒）", ge=0)
    model_used: str = Field(..., description="使用的模型")
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    error_message: Optional[str] = Field(None, description="錯誤訊息（如果失敗）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "analysis-001",
                    "transcript_id": "transcript-123",
                    "solution_id": "quick_summary",
                    "solution_name": "快速摘要",
                    "type": "summary",
                    "status": "completed",
                    "content": "本次會議主要討論了...",
                    "metadata": {"word_count": 250},
                    "processing_time": 2.5,
                    "model_used": "gemma2:9b",
                }
            ]
        }
    }


class AnalysisBatch(BaseModel):
    """批次分析結果"""

    id: str = Field(..., description="批次識別碼")
    transcript_id: str = Field(..., description="關聯的轉錄識別碼")
    results: List[AnalysisResult] = Field(default_factory=list, description="分析結果列表")
    total_processing_time: float = Field(0.0, description="總處理時間（秒）", ge=0)
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")

    @property
    def completed_count(self) -> int:
        """已完成的分析數量"""
        return sum(1 for r in self.results if r.status == AnalysisStatus.COMPLETED)

    @property
    def failed_count(self) -> int:
        """失敗的分析數量"""
        return sum(1 for r in self.results if r.status == AnalysisStatus.FAILED)

    @property
    def success_rate(self) -> float:
        """成功率"""
        total = len(self.results)
        return (self.completed_count / total * 100) if total > 0 else 0.0

    def get_result_by_type(self, analysis_type: AnalysisType) -> Optional[AnalysisResult]:
        """根據類型獲取分析結果"""
        for result in self.results:
            if result.type == analysis_type:
                return result
        return None

    def get_results_by_status(self, status: AnalysisStatus) -> List[AnalysisResult]:
        """根據狀態篩選結果"""
        return [r for r in self.results if r.status == status]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "batch-001",
                    "transcript_id": "transcript-123",
                    "results": [
                        {
                            "id": "analysis-001",
                            "transcript_id": "transcript-123",
                            "solution_id": "quick_summary",
                            "solution_name": "快速摘要",
                            "type": "summary",
                            "status": "completed",
                            "content": "會議摘要內容...",
                            "processing_time": 2.5,
                            "model_used": "gemma2:9b",
                        }
                    ],
                    "total_processing_time": 10.5,
                }
            ]
        }
    }