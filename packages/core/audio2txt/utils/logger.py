"""
Logging system

統一的日誌系統 - 使用 structlog
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler


class Logger:
    """
    統一的日誌器

    提供結構化日誌記錄功能
    """

    def __init__(
        self,
        name: str = "audio2txt",
        level: str = "INFO",
        log_file: Optional[str | Path] = None,
        json_format: bool = False,
    ):
        """
        初始化日誌器

        Args:
            name: 日誌器名稱
            level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: 日誌文件路徑（可選）
            json_format: 是否使用 JSON 格式
        """
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.log_file = Path(log_file) if log_file else None
        self.json_format = json_format

        self._configure_logging()
        self._logger = structlog.get_logger(name)

    def _configure_logging(self) -> None:
        """配置 structlog"""
        # 配置標準 logging
        logging.basicConfig(
            level=self.level,
            format="%(message)s",
            handlers=[self._get_console_handler()],
        )

        # 如果指定了日誌文件，添加文件處理器
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            file_handler.setLevel(self.level)
            logging.getLogger().addHandler(file_handler)

        # 配置 structlog
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ]

        if self.json_format:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.extend(
                [
                    structlog.dev.ConsoleRenderer(
                        colors=True,
                        exception_formatter=structlog.dev.plain_traceback,
                    ),
                ]
            )

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(self.level),
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def _get_console_handler(self) -> logging.Handler:
        """取得控制台處理器"""
        console = Console(stderr=True)
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        return handler

    def debug(self, message: str, **kwargs: Any) -> None:
        """DEBUG 級別日誌"""
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """INFO 級別日誌"""
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """WARNING 級別日誌"""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """ERROR 級別日誌"""
        self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """CRITICAL 級別日誌"""
        self._logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """記錄異常"""
        self._logger.exception(message, **kwargs)

    def success(self, message: str, **kwargs: Any) -> None:
        """成功訊息（自訂級別）"""
        self._logger.info(f"✅ {message}", **kwargs)

    def progress(self, message: str, **kwargs: Any) -> None:
        """進度訊息"""
        self._logger.info(f"🔄 {message}", **kwargs)

    def bind(self, **kwargs: Any) -> "Logger":
        """
        綁定上下文資訊

        Example:
            logger = logger.bind(user_id="123", task_id="456")
            logger.info("Processing task")  # 會包含 user_id 和 task_id
        """
        self._logger = self._logger.bind(**kwargs)
        return self


# 全域日誌器實例
_global_logger: Optional[Logger] = None


def get_logger(
    name: str = "audio2txt",
    level: Optional[str] = None,
    **kwargs: Any,
) -> Logger:
    """
    取得全域日誌器實例

    Args:
        name: 日誌器名稱
        level: 日誌級別（可選）
        **kwargs: 其他參數傳遞給 Logger

    Returns:
        Logger 實例
    """
    global _global_logger

    if _global_logger is None:
        # 從配置載入級別
        if level is None:
            try:
                from .config import get_config

                config = get_config()
                level = "DEBUG" if config.app.debug else "INFO"
            except Exception:
                level = "INFO"

        _global_logger = Logger(name=name, level=level, **kwargs)

    return _global_logger


def set_log_level(level: str) -> None:
    """
    設定全域日誌級別

    Args:
        level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global _global_logger
    if _global_logger:
        _global_logger.level = getattr(logging, level.upper(), logging.INFO)
        _global_logger._configure_logging()


# 便捷函數
def debug(message: str, **kwargs: Any) -> None:
    """DEBUG 日誌"""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs: Any) -> None:
    """INFO 日誌"""
    get_logger().info(message, **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    """WARNING 日誌"""
    get_logger().warning(message, **kwargs)


def error(message: str, **kwargs: Any) -> None:
    """ERROR 日誌"""
    get_logger().error(message, **kwargs)


def success(message: str, **kwargs: Any) -> None:
    """成功訊息"""
    get_logger().success(message, **kwargs)


def progress(message: str, **kwargs: Any) -> None:
    """進度訊息"""
    get_logger().progress(message, **kwargs)