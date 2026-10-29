import json
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("bizinsight.notifications")

class EnterpriseNotificationDispatcher:
    """Dispatches real-time alerts to external enterprise channels.
    Supports Slack Incoming Webhooks, Microsoft Teams Connectors, and generic PagerDuty/Incident webhooks.
    """

    @staticmethod
    async def send_slack_alert(
        webhook_url: str,
        title: str,
        message: str,
        severity: str = "warning",
        fields: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not webhook_url:
            return False

        color_map = {
            "info": "#2eb886",
            "warning": "#daa038",
            "critical": "#a30200",
            "high": "#e01563"
        }
        color = color_map.get(severity.lower(), "#2eb886")

        payload = {
            "attachments": [
                {
                    "fallback": f"[{severity.upper()}] {title}: {message}",
                    "color": color,
                    "pretext": f"🚨 *BIZINSIGHT Enterprise Alert* [{severity.upper()}]",
                    "title": title,
                    "text": message,
                    "fields": [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in (fields or {}).items()
                    ],
                    "footer": "BIZINSIGHT Autonomous Governance Engine",
                    "ts": int(__import__("time").time())
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(webhook_url, json=payload)
                return res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to deliver Slack webhook: {e}")
            return False

    @staticmethod
    async def send_generic_webhook(
        webhook_url: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> bool:
        if not webhook_url:
            return False

        body = {
            "source": "bizinsight-platform",
            "event": event_type,
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "data": payload
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(webhook_url, json=body)
                return res.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"Failed to deliver generic webhook to {webhook_url}: {e}")
            return False

dispatcher = EnterpriseNotificationDispatcher()

