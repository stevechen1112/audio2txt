"""
Notification helpers for task lifecycle events
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any

import requests

from packages.core.audio2txt.utils.config import Config

logger = logging.getLogger(__name__)


class NotificationManager:
    def __init__(self) -> None:
        self.config = Config()
        self.enabled = self.config.notification_enabled and bool(self.config.notification_webhook_url)
        self.webhook_url = self.config.notification_webhook_url
        self.token = self.config.notification_token

    def send_task_update(self, event: str, task_id: str, payload: Dict[str, Any]) -> None:
        if not self.enabled or not self.webhook_url:
            return
        data = {
            "event": event,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
        }
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = requests.post(self.webhook_url, headers=headers, data=json.dumps(data), timeout=5)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to send notification for task %s: %s", task_id, exc)


notification_manager = NotificationManager()
