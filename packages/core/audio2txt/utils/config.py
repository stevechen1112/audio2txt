"""
Configuration loader for Audio2txt v4.0 Enterprise
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """Application Configuration"""
    name: str = "audio2txt-enterprise"
    version: str = "4.0.0"
    debug: bool = False


class CloudConfig(BaseModel):
    """Cloud Provider Configuration"""
    provider: str = "assemblyai"
    region: str = "global"


class ExportConfig(BaseModel):
    """Export Configuration"""
    formats: List[str] = ["txt", "pdf", "md"]


class Config(BaseSettings):
    """
    Main Configuration Class
    Loads from config/default.yaml and environment variables
    """

    app: AppConfig = Field(default_factory=AppConfig)
    cloud: CloudConfig = Field(default_factory=CloudConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)

    # Environment Variables
    database_url: str = Field("sqlite:///./audio2txt.db", alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    
    # Cloud API Keys
    assemblyai_api_key: Optional[str] = Field(None, alias="ASSEMBLYAI_API_KEY")
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    
    # Celery / Async Task Config
    use_celery: bool = Field(False, alias="USE_CELERY")
    celery_broker_url: str = Field("redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field("redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND")
    
    # Security / Notifications
    admin_username: str = Field("admin", alias="ADMIN_USERNAME")
    admin_password: str = Field("password123", alias="ADMIN_PASSWORD")
    jwt_secret_key: str = Field("change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    notification_enabled: bool = Field(False, alias="NOTIFICATION_ENABLED")
    notification_webhook_url: Optional[str] = Field(None, alias="NOTIFICATION_WEBHOOK_URL")
    notification_token: Optional[str] = Field(None, alias="NOTIFICATION_TOKEN")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "Config":
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        config_data = {}
        if "app" in yaml_data:
            config_data["app"] = AppConfig(**yaml_data["app"])
        if "cloud" in yaml_data:
            config_data["cloud"] = CloudConfig(**yaml_data["cloud"])
        if "export" in yaml_data:
            config_data["export"] = ExportConfig(**yaml_data["export"])

        return cls(**config_data)

    @classmethod
    def load_default(cls) -> "Config":
        default_paths = [
            Path("config/default.yaml"),
            Path("../config/default.yaml"),
            Path("../../config/default.yaml"),
        ]

        for path in default_paths:
            if path.exists():
                return cls.from_yaml(path)

        return cls()


# Global Config Instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config.load_default()
    return _global_config
