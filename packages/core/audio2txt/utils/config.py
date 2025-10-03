"""
Configuration loader

配置加載器 - 支援 YAML 配置和環境變數覆蓋
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class TranscriptionConfig(BaseModel):
    """轉錄引擎配置"""

    engine: str = "faster-whisper"
    model_size: str = "large-v3"
    device: str = "cuda"
    compute_type: str = "float16"
    language: str = "zh"
    beam_size: int = 5
    vad_enabled: bool = True


class DiarizationConfig(BaseModel):
    """說話人分離配置"""

    engine: str = "pyannote"
    model: str = "pyannote/speaker-diarization-3.1"
    device: str = "cuda"


class LLMConfig(BaseModel):
    """LLM 配置"""

    provider: str = "ollama"  # ollama, openai
    base_url: str = "http://localhost:11434"
    model: str = "gemma2:27b"
    timeout: int = 120
    temperature: float = 0.7


class PipelineConfig(BaseModel):
    """管線配置"""

    parallel: bool = True
    checkpoint_enabled: bool = True
    cache_enabled: bool = True
    max_workers: int = 4


class AppConfig(BaseModel):
    """應用配置"""

    name: str = "audio2txt"
    version: str = "3.0.0"
    debug: bool = False


class Config(BaseSettings):
    """
    主配置類

    從 config/default.yaml 載入配置，並支援環境變數覆蓋
    """

    app: AppConfig = Field(default_factory=AppConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    diarization: DiarizationConfig = Field(default_factory=DiarizationConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)

    # 環境變數
    database_url: str = Field("sqlite:///./audio2txt.db", alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    ollama_base_url: str = Field("http://localhost:11434", alias="OLLAMA_BASE_URL")
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    hf_token: Optional[str] = Field(None, alias="HF_TOKEN")
    cache_dir: str = Field(".cache", alias="CACHE_DIR")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "Config":
        """
        從 YAML 文件載入配置

        Args:
            yaml_path: YAML 配置文件路徑

        Returns:
            Config 實例
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        # 轉換 YAML 結構為 Config 結構
        config_data = {}

        if "app" in yaml_data:
            config_data["app"] = AppConfig(**yaml_data["app"])

        if "models" in yaml_data:
            models = yaml_data["models"]
            if "transcription" in models:
                config_data["transcription"] = TranscriptionConfig(**models["transcription"])
            if "diarization" in models:
                config_data["diarization"] = DiarizationConfig(**models["diarization"])
            if "llm" in models:
                config_data["llm"] = LLMConfig(**models["llm"])

        if "pipeline" in yaml_data:
            config_data["pipeline"] = PipelineConfig(**yaml_data["pipeline"])

        # 創建 Config 實例（會自動從環境變數覆蓋）
        return cls(**config_data)

    @classmethod
    def load_default(cls) -> "Config":
        """
        載入預設配置

        查找順序：
        1. config/default.yaml (當前目錄)
        2. 使用預設值
        """
        default_paths = [
            Path("config/default.yaml"),
            Path("../config/default.yaml"),
            Path("../../config/default.yaml"),
        ]

        for path in default_paths:
            if path.exists():
                return cls.from_yaml(path)

        # 如果找不到配置文件，使用預設值
        return cls()

    def get(self, key: str, default: Any = None) -> Any:
        """
        取得配置值（支援點號分隔的巢狀鍵）

        Example:
            config.get("llm.model")  # 回傳 "gemma2:27b"
        """
        keys = key.split(".")
        value = self

        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

        return value

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return self.model_dump()


# 全域配置實例（單例模式）
_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    取得全域配置實例（單例）

    Returns:
        Config 實例
    """
    global _global_config
    if _global_config is None:
        _global_config = Config.load_default()
    return _global_config


def set_config(config: Config) -> None:
    """
    設定全域配置實例

    Args:
        config: Config 實例
    """
    global _global_config
    _global_config = config


# 便捷函數
def load_config(yaml_path: Optional[str | Path] = None) -> Config:
    """
    載入配置

    Args:
        yaml_path: YAML 配置文件路徑（可選）

    Returns:
        Config 實例
    """
    if yaml_path:
        config = Config.from_yaml(yaml_path)
    else:
        config = Config.load_default()

    set_config(config)
    return config