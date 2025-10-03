"""
Transcript data models

定義轉錄和說話人相關的資料結構
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Speaker(BaseModel):
    """說話人模型"""

    id: str = Field(..., description="說話人識別碼（如 SPEAKER_00）")
    name: Optional[str] = Field(None, description="說話人名稱（可選）")
    total_speaking_time: float = Field(0.0, description="總發言時間（秒）", ge=0)
    segment_count: int = Field(0, description="發言片段數量", ge=0)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "SPEAKER_00",
                    "name": "顧問",
                    "total_speaking_time": 45.2,
                    "segment_count": 12,
                }
            ]
        }
    }


class Segment(BaseModel):
    """轉錄片段模型"""

    id: str = Field(..., description="片段唯一識別碼")
    start: float = Field(..., description="開始時間（秒）", ge=0)
    end: float = Field(..., description="結束時間（秒）", ge=0)
    text: str = Field(..., description="轉錄文本")
    speaker_id: Optional[str] = Field(None, description="說話人識別碼")
    confidence: Optional[float] = Field(None, description="信心分數（log probability）")
    language: str = Field("zh", description="語言代碼")

    @property
    def duration(self) -> float:
        """片段時長"""
        return self.end - self.start

    def get_time_str(self) -> str:
        """取得格式化時間字串 [MM:SS -> MM:SS]"""
        start_min = int(self.start // 60)
        start_sec = int(self.start % 60)
        end_min = int(self.end // 60)
        end_sec = int(self.end % 60)
        return f"[{start_min:02d}:{start_sec:02d} -> {end_min:02d}:{end_sec:02d}]"

    def to_formatted_text(self, include_speaker: bool = True) -> str:
        """轉換為格式化文本"""
        time_str = self.get_time_str()
        if include_speaker and self.speaker_id:
            return f"{time_str}[{self.speaker_id}]: {self.text}"
        return f"{time_str}: {self.text}"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "seg-001",
                    "start": 0.5,
                    "end": 5.2,
                    "text": "大家好，歡迎來到今天的會議。",
                    "speaker_id": "SPEAKER_00",
                    "confidence": 0.95,
                    "language": "zh",
                }
            ]
        }
    }


class Transcript(BaseModel):
    """完整轉錄模型"""

    id: str = Field(..., description="轉錄識別碼")
    audio_id: str = Field(..., description="關聯的音訊識別碼")
    segments: List[Segment] = Field(default_factory=list, description="轉錄片段列表")
    speakers: List[Speaker] = Field(default_factory=list, description="說話人列表")
    language: str = Field("zh", description="主要語言")
    processing_time: float = Field(..., description="處理時間（秒）", ge=0)
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    metadata: dict = Field(default_factory=dict, description="額外元資料")

    @property
    def total_segments(self) -> int:
        """總片段數"""
        return len(self.segments)

    @property
    def full_text(self) -> str:
        """完整文本（純文字，無時間戳）"""
        return " ".join(seg.text for seg in self.segments)

    @property
    def formatted_text(self) -> str:
        """格式化文本（含時間戳和說話人）"""
        return "\n".join(seg.to_formatted_text() for seg in self.segments)

    def get_speaker_segments(self, speaker_id: str) -> List[Segment]:
        """取得特定說話人的所有片段"""
        return [seg for seg in self.segments if seg.speaker_id == speaker_id]

    def get_text_by_time_range(self, start: float, end: float) -> str:
        """取得時間範圍內的文本"""
        segments = [
            seg
            for seg in self.segments
            if (seg.start >= start and seg.end <= end)
            or (seg.start <= start <= seg.end)
            or (seg.start <= end <= seg.end)
        ]
        return " ".join(seg.text for seg in segments)

    def to_srt_format(self) -> str:
        """轉換為 SRT 字幕格式"""
        srt_lines = []
        for idx, segment in enumerate(self.segments, 1):
            start_time = self._format_srt_time(segment.start)
            end_time = self._format_srt_time(segment.end)
            speaker_prefix = f"[{segment.speaker_id}] " if segment.speaker_id else ""
            srt_lines.append(f"{idx}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(f"{speaker_prefix}{segment.text}")
            srt_lines.append("")  # 空行
        return "\n".join(srt_lines)

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """格式化 SRT 時間格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "transcript-123",
                    "audio_id": "audio-123",
                    "segments": [
                        {
                            "id": "seg-001",
                            "start": 0.0,
                            "end": 3.5,
                            "text": "大家好。",
                            "speaker_id": "SPEAKER_00",
                        }
                    ],
                    "speakers": [{"id": "SPEAKER_00", "name": "主持人"}],
                    "language": "zh",
                    "processing_time": 15.2,
                }
            ]
        }
    }