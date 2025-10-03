"""
Audio data models

定義音訊相關的資料結構
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AudioMetadata(BaseModel):
    """音訊元資料"""

    duration: float = Field(..., description="音訊長度（秒）", gt=0)
    sample_rate: int = Field(..., description="採樣率", gt=0)
    channels: int = Field(1, description="聲道數", ge=1, le=2)
    format: str = Field(..., description="音訊格式（wav, mp3, m4a 等）")
    file_size: int = Field(..., description="檔案大小（bytes）", gt=0)
    bit_depth: Optional[int] = Field(None, description="位元深度")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "duration": 120.5,
                    "sample_rate": 16000,
                    "channels": 1,
                    "format": "wav",
                    "file_size": 3841600,
                    "bit_depth": 16,
                }
            ]
        }
    }


class Audio(BaseModel):
    """音訊檔案模型"""

    id: str = Field(..., description="音訊唯一識別碼")
    file_path: str = Field(..., description="音訊檔案路徑")
    filename: str = Field(..., description="檔案名稱")
    metadata: AudioMetadata = Field(..., description="音訊元資料")
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")

    @field_validator("file_path")
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        """驗證檔案是否存在"""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Audio file not found: {v}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return str(path.absolute())

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """驗證檔案名稱"""
        if not v or v.strip() == "":
            raise ValueError("Filename cannot be empty")
        return v.strip()

    def get_duration_str(self) -> str:
        """取得格式化的時長字串 (MM:SS)"""
        total_seconds = int(self.metadata.duration)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "audio-123456",
                    "file_path": "/path/to/audio.wav",
                    "filename": "audio.wav",
                    "metadata": {
                        "duration": 120.5,
                        "sample_rate": 16000,
                        "channels": 1,
                        "format": "wav",
                        "file_size": 3841600,
                    },
                }
            ]
        }
    }