import httpx
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def send_message(webhook_url: str | None, text: str) -> str:
    """Posts to a Slack incoming webhook. Falls back to the workspace-wide
    SLACK_DEFAULT_WEBHOOK_URL if the node didn't specify one, and logs
    instead of failing if neither is configured."""
    url = webhook_url or settings.SLACK_DEFAULT_WEBHOOK_URL
    if not url:
        logger.info(f"[slack] No webhook configured - would send: {text!r}")
        return "not sent (no webhook configured)"

    try:
        resp = httpx.post(url, json={"text": text}, timeout=10)
        resp.raise_for_status()
        return "sent"
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Slack message failed: {exc}")
        return f"failed: {exc}"
